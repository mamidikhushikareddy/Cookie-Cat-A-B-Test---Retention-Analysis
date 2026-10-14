"""Deterministic decision policy. Policies change the action, never the measured statistics."""
from __future__ import annotations
from dataclasses import dataclass, asdict

SHIP, HOLD, REJECT = "SHIP", "HOLD / INVESTIGATE", "REJECT"


@dataclass(frozen=True)
class Policy:
    min_improvement_pp: float = 0.5   # SHIP needs CI lower bound >= this (pp)
    max_loss_pp: float = 0.5          # REJECT needs point loss >= this AND CI upper bound < 0 (pp)
    integrity_blocks: bool = True     # unresolved integrity warning forces HOLD

    def validate(self) -> "Policy":
        for name in ("min_improvement_pp", "max_loss_pp"):
            v = getattr(self, name)
            if not isinstance(v, (int, float)) or not 0 <= v <= 20:
                raise ValueError(f"{name} must be within [0, 20] percentage points")
        return self


def decide(effect: dict, integrity_warning: bool, policy: Policy) -> dict:
    """effect: output of stats.retention_effect for the chosen outcome (pp units)."""
    policy.validate()
    lo, hi = effect["ci_newcombe_pp"]
    d = effect["diff_pp"]
    reasons: list[str] = []
    wants_ship = lo >= policy.min_improvement_pp and lo > 0
    wants_reject = d <= -policy.max_loss_pp and hi < 0
    if integrity_warning and policy.integrity_blocks:
        action = HOLD
        reasons.append("Unresolved integrity warning (sample-ratio) blocks a definitive recommendation under this policy.")
        if wants_reject:
            reasons.append("Absent the integrity block the evidence would support REJECT.")
        elif wants_ship:
            reasons.append("Absent the integrity block the evidence would support SHIP.")
    elif wants_ship:
        action, reasons = SHIP, [f"CI lower bound {lo:.2f} pp >= required improvement {policy.min_improvement_pp:.2f} pp."]
    elif wants_reject:
        action, reasons = REJECT, [f"Loss {d:.2f} pp exceeds tolerance {policy.max_loss_pp:.2f} pp and CI upper bound {hi:.2f} pp < 0."]
    else:
        action = HOLD
        reasons.append("Evidence neither clears the improvement bar nor justifies rejection under this policy.")
    return {"action": action, "reasons": reasons, "policy": asdict(policy),
            "invariants": {k: effect[k] for k in ("diff_pp", "ci_newcombe_pp", "z", "p_value")}}


def stability_map(effect: dict, integrity_warning: bool, improvements, losses, integrity_blocks=True) -> dict:
    """Grid over (min_improvement_pp, max_loss_pp). Range examined is recorded; no 'robustness' claim is made."""
    imps, loss = list(improvements), list(losses)
    if len(imps) * len(loss) > 2500:
        raise ValueError("grid too large")
    grid = [[decide(effect, integrity_warning, Policy(i, l, integrity_blocks))["action"] for l in loss] for i in imps]
    flat = [a for row in grid for a in row]
    return {"min_improvement_pp": imps, "max_loss_pp": loss, "grid": grid,
            "share": {a: flat.count(a) / len(flat) for a in set(flat)},
            "range_examined": f"improvement {imps[0]}..{imps[-1]} pp x loss {loss[0]}..{loss[-1]} pp, integrity_blocks={integrity_blocks}"}
