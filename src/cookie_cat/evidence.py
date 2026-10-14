"""Evidence dependency graph with branch-local invalidation."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque

EDGE_TYPES = {"DERIVED_FROM", "DEPENDS_ON", "VALIDATED_BY", "ASSUMES", "SUPPORTS", "CONTRADICTS", "LIMITS", "REQUIRES_REVIEW"}
# Edge (a -> b, type) semantics: "a <type> b". For invalidation, a is downstream of b for these types:
PROPAGATING = {"DERIVED_FROM", "DEPENDS_ON", "ASSUMES"}
NODE_TYPES = {"dataset", "contract", "diagnostic", "metric", "estimate", "assumption", "policy", "recommendation", "question", "artifact"}


@dataclass
class Node:
    id: str
    type: str
    label: str
    status: str = "current"  # current | invalidated | unverified | failed
    description: str = ""
    evidence_ref: dict = field(default_factory=dict)


class EvidenceGraph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: list[tuple[str, str, str]] = []

    def add_node(self, n: Node):
        if n.type not in NODE_TYPES:
            raise ValueError(f"bad node type {n.type}")
        if n.id in self.nodes:
            raise ValueError(f"duplicate node {n.id}")
        self.nodes[n.id] = n

    def add_edge(self, src: str, dst: str, kind: str):
        if kind not in EDGE_TYPES:
            raise ValueError(f"bad edge type {kind}")
        if src not in self.nodes or dst not in self.nodes:
            raise KeyError("edge references missing node")
        if kind in PROPAGATING and self._reaches(dst, src):
            raise ValueError(f"edge {src}->{dst} would create a dependency cycle")
        self.edges.append((src, dst, kind))

    def _reaches(self, start: str, target: str) -> bool:
        seen, q = {start}, deque([start])
        while q:
            cur = q.popleft()
            if cur == target:
                return True
            for s, d, k in self.edges:
                if s == cur and k in PROPAGATING and d not in seen:
                    seen.add(d); q.append(d)
        return False

    def downstream(self, node_id: str) -> set[str]:
        """Nodes whose validity depends (transitively) on node_id."""
        out, q = set(), deque([node_id])
        while q:
            cur = q.popleft()
            for s, d, k in self.edges:
                if d == cur and k in PROPAGATING and s not in out:
                    out.add(s); q.append(s)
        return out

    def upstream(self, node_id: str) -> set[str]:
        out, q = set(), deque([node_id])
        while q:
            cur = q.popleft()
            for s, d, k in self.edges:
                if s == cur and k in PROPAGATING and d not in out:
                    out.add(d); q.append(d)
        return out

    def invalidate(self, node_id: str) -> set[str]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        hit = self.downstream(node_id) | {node_id}
        for h in hit:
            self.nodes[h].status = "invalidated"
        return hit

    def open_questions(self, node_id: str) -> list[str]:
        return [s for s, d, k in self.edges if d == node_id and k in {"LIMITS", "REQUIRES_REVIEW"}]

    def to_dict(self) -> dict:
        return {"nodes": [n.__dict__ for n in self.nodes.values()],
                "edges": [{"source": s, "target": d, "type": k} for s, d, k in self.edges]}


def build_cookie_cat_graph(fingerprint: str, srm_warning: bool) -> EvidenceGraph:
    g = EvidenceGraph()
    N = lambda i, t, l, **kw: g.add_node(Node(i, t, l, **kw))
    N("dataset", "dataset", "cookie_cats.csv", evidence_ref={"sha256": fingerprint})
    N("contract", "contract", "Data contract v1.0")
    N("groups", "metric", "Group counts")
    N("ret7", "metric", "Day-7 retention by arm")
    N("effect7", "estimate", "Day-7 effect (gate_40 - gate_30) + CI + test")
    N("srm_assumption", "assumption", "Expected allocation 50/50 (not in dataset)", status="unverified")
    N("srm", "diagnostic", "SRM chi-square diagnostic", status="current")
    N("policy", "policy", "Decision policy")
    N("rec", "recommendation", "Gate-40 rollout recommendation")
    N("q_design", "question", "Was 50/50 the planned allocation? Assignment logs?",
      status="unverified" if srm_warning else "current")
    g.add_node(Node("viz_style", "artifact", "Chart styling"))
    for s, d, k in [("contract", "dataset", "VALIDATED_BY"), ("groups", "contract", "DEPENDS_ON"), ("ret7", "groups", "DERIVED_FROM"),
                    ("effect7", "ret7", "DERIVED_FROM"), ("srm", "groups", "DERIVED_FROM"), ("srm", "srm_assumption", "ASSUMES"),
                    ("rec", "effect7", "DEPENDS_ON"), ("rec", "srm", "DEPENDS_ON"), ("rec", "policy", "DEPENDS_ON"),
                    ("q_design", "srm", "LIMITS"), ("q_design", "rec", "LIMITS"), ("effect7", "srm", "SUPPORTS")]:
        if k == "VALIDATED_BY":
            g.edges.append((s, d, k))
        else:
            g.add_edge(s, d, k)
    # 'rec' is limited by an unresolved question
    g.edges = [(s, d, k) for s, d, k in g.edges if not (s == "effect7" and d == "srm")]
    return g
