# Build status (honest ledger)

## Implemented and verified (pytest: 25 tests passing = 16 new core tests + 9 pre-existing legacy tests; notebook executed with 0 errors)
- Approved-ID dataset loader + SHA-256 provenance (`src/cookie_cat/data.py`)
- Pandera data contract with severity-classified rule report (`contract.py`)
- Statistics: Wilson/Newcombe/Wald CIs, pooled z-test, Holm, SRM (configurable allocation & alpha), Mann–Whitney (`stats.py`)
- DuckDB SQL cross-check against pandas (`sql/duckdb/crosscheck.sql`, `sqlchecks.py`)
- Deterministic decision policy + stability map with enforced invariants (`decision.py`)
- Evidence dependency graph: cycle rejection, branch-local invalidation (`evidence.py`)
- Executable notebook `notebooks/01_cookie_cats_retention_analysis.ipynb`
- Baseline regression: all reported figures reproduce from the CSV (Day-7 -0.8201 pp, p=0.001554, SRM p=0.008608)

## Implemented, NOT run
- `r/verify_experiment.R` — R is not installed in the build sandbox; **independent verification status: NOT_RUN**.

## NOT implemented yet
FastMCP server, LangGraph agent, SQLite missions/XP, new FastAPI routes (evidence/simulate/integrity/dossier),
Next.js redesign (Data Vault, Integrity Lab, Decision Lab, Evidence Graph, Agent workspace), Quarto report,
frontend tests, CI updates, remaining docs. The existing `api/main.py` and `web/` are unchanged legacy.

## Findings
- Uploaded zip lacked the dataset, git history, store.py, missions and R script described in the brief; the CSV was fetched from a public mirror (sha256 5ab54d76…c46bd).
- SRM flags at alpha=0.05 (p=0.0086) but not at 0.001; default kept at 0.05 to match baseline; sensitivity documented.
- Contract warning C013: extreme game-round outlier (max 49,854 vs p99 493).
