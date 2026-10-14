# Cookie Cat analysis API

This API calls the existing tested Python analysis module; it does not duplicate or hardcode statistical results.

From the project root, activate the `cookie_cat` environment and install `api/requirements.txt`, then run `python -m uvicorn api.main:app --reload --port 8000`. The dataset must exist at `data/raw/cookie_cats.csv`. If absent, run `python scripts/download_data.py` from the root.

- `GET /health` reports API and dataset presence.
- `GET /api/analysis` validates the dataset and returns computed group metrics, confidence intervals, p-values, quality checks, and recommendation. Returns HTTP 503 when the dataset is missing; no demo numbers are substituted.
