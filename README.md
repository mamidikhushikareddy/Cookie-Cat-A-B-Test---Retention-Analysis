# Cookie Cats A/B Test: Retention Analysis

Analysis of a mobile-game A/B test that moved the first progression gate from level 30 to level 40, measuring the effect on Day-1 and Day-7 player retention.

## Summary

- **Dataset:** 90,189 players (44,700 at gate 30, 45,489 at gate 40).
- **Finding:** Day-7 retention was lower with the level-40 gate (19.02% vs. 18.20%), a difference of -0.82 percentage points (95% CI -1.33 to -0.31, p = 0.0016).
- **Day-1 retention:** no significant difference (44.82% vs. 44.23%, p = 0.074).
- **Data check:** the group split deviates from 50/50 (chi-square p = 0.0086). The planned allocation is not in the dataset, so this is treated as a warning, not proof of a flawed experiment.
- **Recommendation:** hold the rollout and verify the assignment process.

## Methods

- Data validation with Pandera (schema, uniqueness, valid groups, non-negative values).
- Pooled two-proportion z-test and Newcombe confidence interval for retention differences.
- Holm correction across Day-1 and Day-7 tests.
- Sample-ratio mismatch check (chi-square goodness of fit).
- Mann-Whitney test for the skewed game-round counts.
- DuckDB SQL queries used to cross-check pandas results.

## Project structure

```text
src/cookie_cat/   analysis package (data, contract, stats, decision, evidence)
notebooks/        01_cookie_cats_retention_analysis.ipynb
sql/duckdb/       cross-check queries
tests/            pytest suite
scripts/          dataset download
app.py            Streamlit app
```

## Getting started

```bash
conda create -n cookie_cat python=3.11 -y
conda activate cookie_cat
pip install -r requirements.txt
pip install -e .
python scripts/download_data.py
pytest -q
jupyter notebook notebooks/01_cookie_cats_retention_analysis.ipynb
```

Optional interactive app: `python -m streamlit run app.py`

## Data

Public Cookie Cats mobile-game dataset ([Kaggle](https://www.kaggle.com/datasets/yufengsui/mobile-games-ab-testing)), one row per player: `userid`, `version`, `sum_gamerounds`, `retention_1`, `retention_7`. The download script validates columns and row count before saving.

## Limitations

- No experiment design details (planned split, dates, randomization unit).
- No revenue, session, or churn-reason data, so no lifetime-value or funnel analysis.
- Causal conclusions depend on randomization having held.

## Technologies

Python, Pandas, SciPy, Matplotlib, Jupyter Notebook, Pandera, DuckDB, pytest
