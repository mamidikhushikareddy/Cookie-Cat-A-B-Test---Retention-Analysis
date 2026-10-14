# Cookie Cat — Experiment Decision Lab

**A compact, interactive product experimentation project.** Cookie Cat reproduces the classic Cookie Cats Day-7 retention analysis and adds a decision stress test: adjust practical-lift and tolerated-loss thresholds, inspect uncertainty and experiment-health signals, and export an evidence-backed decision memo.

> This repository does not hardcode the resume metrics into its analysis. The project calculates them from the public dataset. The reported values below are acceptance criteria to verify after the real-data run, not a claim that the current environment has already reproduced them.

## Resume claim this project is designed to reproduce

> Conducted an A/B test on Cookie Cats' level-gate placement, analyzing 7-day retention across 90,189 players; found significantly lower retention with the level-40 gate (19.02% vs. 18.20%, p=0.0016) and recommended holding the rollout.

**Core stack:** Python, Pandas, SciPy, Matplotlib, Jupyter Notebook.  
**Interactive experience:** Streamlit + Plotly, with a dark arcade-inspired visual system, motion accents, responsive quest track, and interactive decision controls.  
**Testing:** pytest.

## Features

### Quest Arcade gamification
- Animated campaign track with locked, active, and cleared states; high-contrast dark interface, subtle motion, hover feedback, and responsive styling.
- Four evidence-based missions: retention signal, p-value interpretation, randomization alarm, and rollout boss battle.
- XP, rank progression, mission completion, success feedback, and a downloadable investigator badge.
- Scoring rewards correct reasoning; it never alters the dataset or statistical results.
- Progress is session-scoped in the local prototype, not a shared multi-user leaderboard.

### Real tool integrations
- **DuckDB** local warehouse with SQL views and reusable queries (`requirements-lab.txt`, `scripts/build_warehouse.py`, `sql/`).
- **marimo** reactive notebook companion sharing the same tested analysis module (`notebooks/cookie_cat_lab.py`).
- **GitHub Actions** CI workflow to run tests on pushes and pull requests (`.github/workflows/tests.yml`).
- **Evidence.dev**, **Penpot**, and **Rive** are documented optional extensions; they are not falsely presented as connected services in this version.

- Automatic public dataset download with schema and row-count validation; no Kaggle credentials or manual download.
- Data contracts and validation for unique player IDs, group values, retention flags, and game-round values.
- Day-1 and Day-7 retention metrics, two-proportion tests, Wilson/Newcombe-style confidence interval, and Holm adjustment.
- Sample-ratio mismatch diagnostic, explicitly conditional on a 50/50 assignment assumption.
- Mann–Whitney engagement comparison for skewed game-round counts.
- Interactive decision stress test with configurable practical-lift, tolerated-loss, and confidence settings.
- Downloadable decision memo, machine-readable analysis JSON, group metrics CSV, and Matplotlib report figures.
- Notebook companion, methodology documentation, and automated tests.

## Run on Windows PowerShell

From the project folder:

```powershell
conda create -n cookie_cat python=3.11 -y
conda activate cookie_cat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run_all.py
pytest -q
python -m streamlit run app.py
# Optional integrations (DuckDB + marimo)
python -m pip install -r requirements-lab.txt
python scripts/build_warehouse.py
marimo edit notebooks/cookie_cat_lab.py
```

If you already have a working Python environment, you can use it instead of creating a Conda environment.

## Data source
The downloader tries public GitHub mirrors of the widely used Cookie Cats Mobile Games A/B Testing dataset. It validates required columns and the expected 90,189 rows before saving. If every mirror fails, it prints the attempted sources and errors rather than silently fabricating data. Network restrictions or mirror changes may require updating the source list.

Canonical dataset reference: https://www.kaggle.com/datasets/yufengsui/mobile-games-ab-testing

## Screens in the app
1. **Quest Arcade** — four evidence missions, XP, ranks, rewards, and a final rollout boss battle.
2. **Decision room** — retention comparison, confidence interval, p-values, experiment health, initial call, and memo export.
2. **Stress test** — interactive policy sliders and a live decision rule.
3. **Player signals** — skewed game-round distribution and rank-based comparison.
4. **Method & data** — dataset contract, methods, limitations, and quality snapshot.
5. **Toolchain** — launch links and honest status labels for integrated and optional software.

## Important limitations
The source data has one record per player and includes assignment, total game rounds, and Day-1/Day-7 retention. It does not include session-level events, revenue, satisfaction, acquisition channel, or churn reasons. The project therefore does not claim to calculate funnels, lifetime value, or why individual players churn.

## Repository layout

```text
cookie-cat/
├── app.py
├── run_all.py
├── requirements.txt
├── requirements-lab.txt
├── sql/
├── design/
├── tools/
├── .github/workflows/tests.yml
├── scripts/
│   └── download_data.py
├── src/
│   └── cookie_cat.py
├── tests/
│   └── test_cookie_cat.py
├── notebooks/
│   └── 01_cookie_cat_experiment_lab.ipynb
├── docs/
│   ├── methodology.md
│   └── portfolio_case_study.md
├── data/raw/
└── outputs/
```

## Validation status
- The local test suite currently passes: `9 passed`. Run it again in your environment after installing the project requirements.
Run the commands locally and record the actual outputs. Do not describe the resume figures as reproduced until the data download and test results have been verified.


## Toolchain links
- [DuckDB](https://duckdb.org/) — local SQL warehouse
- [marimo](https://marimo.io/) — reactive research lab
- [GitHub Actions](https://docs.github.com/en/actions/tutorials/build-and-test-code/python) — automated test workflow
- [Evidence.dev](https://www.evidence.dev/) — optional SQL-as-code reports
- [Penpot](https://penpot.app/) — optional interface design
- [Rive](https://rive.app/) — optional state-driven motion design
- [DBeaver](https://dbeaver.io/) — inspect the local DuckDB database


## Next.js frontend (new)
The project now includes `web/`, a Next.js/React frontend prototype, and `api/`, a FastAPI bridge that calls the existing Python analysis module. This preserves the current analysis code while replacing Streamlit as the intended user-facing interface. See `docs/NEXTJS_MIGRATION.md` for the staged migration plan and verified status. The Streamlit app remains as a fallback during migration; it is not the new frontend.


## Next.js frontend (new)
The project now includes `web/`, a Next.js/React frontend prototype, and `api/`, a FastAPI bridge that calls the existing Python analysis module. This preserves the current analysis code while replacing Streamlit as the intended user-facing interface. See `docs/NEXTJS_MIGRATION.md` for the staged migration plan and verified status. The Streamlit app remains as a fallback during migration; it is not the new frontend.


## Next.js frontend (new)
The project now includes `web/`, a Next.js/React frontend prototype, and `api/`, a FastAPI bridge that calls the existing Python analysis module. This preserves the current analysis code while replacing Streamlit as the intended user-facing interface. See `docs/NEXTJS_MIGRATION.md` for the staged migration plan and verified status. The Streamlit app remains as a fallback during migration; it is not the new frontend.

## Resume-ready project description

**Cookie Cats A/B Test - Retention Analysis**

- Conducted an A/B test on Cookie Cats' level-gate placement, analyzing 7-day retention across 90,189 players; found significantly lower retention with the level-40 gate (19.02% vs. 18.20%, p=0.0016) and recommended holding the rollout.

**Technologies:** Python, Pandas, SciPy, Matplotlib, Jupyter Notebook

## Verification status (this build)
See `docs/STATUS.md` for what is implemented and verified versus not yet implemented.
