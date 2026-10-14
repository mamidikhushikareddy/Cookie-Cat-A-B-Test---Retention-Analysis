"""Data contract: Pandera schema plus explicit, severity-classified rule results."""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
import pandas as pd
import pandera.pandas as pa

CONTRACT_VERSION = "1.0"
REQUIRED = ["userid", "version", "sum_gamerounds", "retention_1", "retention_7"]
GROUPS = ["gate_30", "gate_40"]

SCHEMA = pa.DataFrameSchema(
    {
        "userid": pa.Column(nullable=False, unique=True),
        "version": pa.Column(str, pa.Check.isin(GROUPS), nullable=False),
        "sum_gamerounds": pa.Column(int, pa.Check.ge(0), nullable=False, coerce=False),
        "retention_1": pa.Column(bool, nullable=False),
        "retention_7": pa.Column(bool, nullable=False),
    },
    strict=False,
)


@dataclass
class RuleResult:
    rule_id: str
    description: str
    severity: str          # error | warning | info
    expected: str
    observed: str
    status: str            # pass | fail
    affected: int
    sample_ids: list = field(default_factory=list)
    next_step: str = ""
    blocks_analysis: bool = False


def _r(rule_id, desc, sev, expected, observed, ok, affected=0, sample=None, step="", blocks=None):
    return RuleResult(rule_id, desc, sev, expected, observed, "pass" if ok else "fail", int(affected),
                      [int(x) if str(x).lstrip("-").isdigit() else str(x) for x in (sample or [])][:5], step,
                      bool(blocks if blocks is not None else (sev == "error" and not ok)))


def audit(df: pd.DataFrame) -> dict:
    """Run every rule. Never mutates or drops rows."""
    rules: list[RuleResult] = []
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    rules.append(_r("C001", "Required columns present", "error", ", ".join(REQUIRED),
                    "missing: " + ", ".join(missing_cols) if missing_cols else "all present",
                    not missing_cols, len(missing_cols), step="Supply a file with the required columns."))
    rules.append(_r("C002", "Dataset is not empty", "error", ">0 rows", f"{len(df)} rows", len(df) > 0,
                    step="Provide a non-empty dataset."))
    if missing_cols or df.empty:
        return _summary(rules)

    ids_missing = df["userid"].isna()
    rules.append(_r("C003", "userid has no missing values", "error", "0 missing", f"{int(ids_missing.sum())} missing",
                    not ids_missing.any(), ids_missing.sum(), step="Remove or repair rows lacking identifiers."))
    dup = df["userid"].duplicated(keep=False) & ~ids_missing
    rules.append(_r("C004", "userid is unique", "error", "0 duplicates", f"{int(dup.sum())} rows share an id",
                    not dup.any(), dup.sum(), df.loc[dup, "userid"].head(5).tolist(),
                    "Investigate duplicate assignment; do not silently deduplicate."))
    bad_ver = ~df["version"].isin(GROUPS)
    rules.append(_r("C005", "version is one of the known arms", "error", "gate_30 | gate_40",
                    f"{int(bad_ver.sum())} unexpected", not bad_ver.any(), bad_ver.sum(),
                    df.loc[bad_ver, "userid"].head(5).tolist(), "Map or remove unknown arm labels explicitly."))
    rules.append(_r("C006", "Both arms present", "error", "2 arms", f"{df['version'].nunique()} arms",
                    set(GROUPS) <= set(df["version"].unique()), step="A two-arm comparison needs both arms."))
    rounds = pd.to_numeric(df["sum_gamerounds"], errors="coerce")
    non_num = rounds.isna()
    rules.append(_r("C007", "sum_gamerounds is numeric", "error", "numeric", f"{int(non_num.sum())} non-numeric",
                    not non_num.any(), non_num.sum()))
    neg = rounds < 0
    rules.append(_r("C008", "sum_gamerounds is non-negative", "error", ">= 0", f"{int(neg.sum())} negative",
                    not neg.any(), neg.sum(), df.loc[neg, "userid"].head(5).tolist()))
    for col, rid in (("retention_1", "C009"), ("retention_7", "C010")):
        ok_vals = df[col].map(lambda x: str(x).strip().lower() in {"true", "false", "1", "0"})
        rules.append(_r(rid, f"{col} is boolean-like", "error", "True/False", f"{int((~ok_vals).sum())} invalid",
                        ok_vals.all(), (~ok_vals).sum(), df.loc[~ok_vals, "userid"].head(5).tolist()))
    miss = int(df[REQUIRED].isna().sum().sum())
    rules.append(_r("C011", "No missing cells in required columns", "warning", "0", str(miss), miss == 0, miss))
    zeros = int((rounds == 0).sum())
    rules.append(_r("C012", "Players with zero game rounds", "info", "informational", f"{zeros} players", True, zeros,
                    step="Zero-round players are retained in the denominator (assignment-based analysis)."))
    q99 = float(rounds.quantile(0.99)); mx = float(rounds.max())
    rules.append(_r("C013", "Extreme game-round outliers", "warning", "max within ~100x p99",
                    f"max={mx:.0f}, p99={q99:.0f}", mx <= 100 * max(q99, 1), int((rounds > 100 * max(q99, 1)).sum()),
                    df.loc[rounds == mx, "userid"].head(3).tolist(),
                    "Use rank-based tests / report medians; extreme values distort means."))
    try:
        SCHEMA.validate(df.assign(version=df["version"].astype(str)), lazy=True)
        schema_ok, n_fail = True, 0
    except pa.errors.SchemaErrors as e:
        schema_ok, n_fail = False, len(e.failure_cases)
    rules.append(_r("C014", "Pandera schema validation (types + constraints)", "error", "schema satisfied",
                    "satisfied" if schema_ok else f"{n_fail} failure cases", schema_ok, n_fail,
                    step="Inspect Pandera failure cases; types must match without silent coercion."))
    return _summary(rules)


def _summary(rules: list[RuleResult]) -> dict:
    blocking = [r for r in rules if r.blocks_analysis]
    return {
        "contract_version": CONTRACT_VERSION,
        "rules": [asdict(r) for r in rules],
        "blocked": bool(blocking),
        "blocking_rules": [r.rule_id for r in blocking],
        "counts": {s: sum(1 for r in rules if r.severity == s and r.status == "fail") for s in ("error", "warning", "info")},
    }


def to_analysis_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Documented transformation: only legal after audit() reports no blocking rule."""
    if audit(df)["blocked"]:
        raise ValueError("Data contract has blocking violations; refusing to analyse.")
    out = df.copy()
    for c in ("retention_1", "retention_7"):
        out[c] = out[c].map(lambda x: str(x).strip().lower() in {"true", "1"})
    out["sum_gamerounds"] = pd.to_numeric(out["sum_gamerounds"]).astype(int)
    return out
