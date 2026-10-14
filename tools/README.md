# Cookie Cat tool integrations

| Tool | Role | Project artifact | Status |
|---|---|---|---|
| DuckDB | Local SQL analytics database | `scripts/build_warehouse.py`, `sql/*.sql` | Implemented; install optional requirements |
| marimo | Reactive Python research lab | `notebooks/cookie_cat_lab.py` | Implemented; install optional requirements |
| GitHub Actions | Automated tests on push/PR | `.github/workflows/tests.yml` | Implemented; activates when pushed to GitHub |
| Evidence.dev | SQL-as-code report framework | Reusable SQL queries under `sql/` | Optional extension, not yet a built Evidence app |
| Penpot | Interface and design-system prototyping | `design/design_tokens.json`, `design/README.md` | Optional manual workspace |
| Rive | State-driven animation | Animation state specification in `design/README.md` | Optional; no .riv asset bundled |

## DuckDB
From the project root, after the dataset has been downloaded:
```powershell
python -m pip install -r requirements-lab.txt
python scripts/build_warehouse.py
```
The local database is written to `data/warehouse/cookie_cat.duckdb`. You can inspect it with a DuckDB-compatible SQL client such as [DBeaver](https://dbeaver.io/). The generated database is ignored by Git because it can be rebuilt from the source CSV.

## marimo
```powershell
python -m pip install -r requirements-lab.txt
marimo edit notebooks/cookie_cat_lab.py
```
It imports the same tested analysis functions as the main application. This is a real reactive companion lab, not a separate implementation of the statistics.

## GitHub Actions
Push the repository to GitHub. The workflow at `.github/workflows/tests.yml` runs tests for pushes and pull requests. GitHub's official guide: https://docs.github.com/en/actions/tutorials/build-and-test-code/python

## Evidence.dev (optional)
Evidence is an open-source BI-as-code tool. The SQL under `sql/` is ready to serve as the basis for a report, but a full Evidence project is not included or claimed as connected in this version. Official site: https://www.evidence.dev/
