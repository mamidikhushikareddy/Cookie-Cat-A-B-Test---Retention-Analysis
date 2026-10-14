"""DuckDB analytical SQL: independent cross-check of the pandas results (parameter-free, fixed queries only)."""
from __future__ import annotations
import re
from pathlib import Path
import duckdb
import pandas as pd

SQL_FILE = Path(__file__).resolve().parents[2] / "sql" / "duckdb" / "crosscheck.sql"


def _queries() -> dict[str, str]:
    parts = re.split(r"^-- name: (\w+)\s*$", SQL_FILE.read_text(), flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def run_all(df: pd.DataFrame) -> dict[str, list[dict]]:
    con = duckdb.connect(":memory:")
    con.register("players", df)
    out = {name: con.execute(q).fetchdf().to_dict("records") for name, q in _queries().items()}
    con.close()
    return out


def crosscheck(df: pd.DataFrame, tol: float = 1e-12) -> dict:
    """Compare DuckDB group counts/rates with pandas. Disagreement is reported, never hidden."""
    sql = {r["version"]: r for r in run_all(df)["group_retention"]}
    diffs = []
    for v, grp in df.groupby("version"):
        for label, a, b in (("n", len(grp), sql[v]["n"]), ("r1", int(grp.retention_1.sum()), sql[v]["r1"]),
                            ("r7", int(grp.retention_7.sum()), sql[v]["r7"])):
            if a != b:
                diffs.append({"group": v, "metric": label, "pandas": a, "duckdb": int(b)})
    return {"status": "AGREE" if not diffs else "DISAGREE", "differences": diffs}
