# Cookie Cat frontend migration plan

## Product direction
Hybrid cinematic launcher + explorable game world. Visuals take inspiration from game launchers and world maps without copying third-party game assets. The core product loop is: discover a mission → inspect evidence → interact with a real analysis → record a defensible decision → earn a progress marker.

## Architecture
- `web/`: Next.js + React frontend; custom responsive CSS, custom SVG world map, mission state, decision controls.
- `api/`: FastAPI bridge to `src/cookie_cat.py`; existing Pandas/SciPy/statsmodels logic remains the source of truth.
- `src/cookie_cat.py`: existing analysis, validation, stress testing, and outputs.
- `data/raw/cookie_cats.csv`: downloaded dataset, not committed to source control.

## Implementation stages
1. **Foundation (implemented in this archive):** Next.js scaffold, custom launcher/world-map UI, mission progression state, decision room, Python API bridge, truthful missing-data/API states, migration documentation.
2. **Local verification (must be run on the user's machine):** install dependencies, run the existing Python tests, download/validate the actual dataset, start API, inspect `/api/analysis`, start Next.js, inspect desktop and mobile layouts.
3. **Statistical acceptance:** compare computed row count, group retention rates, p-value, confidence interval, and decision with the resume claim. Do not label a result verified until the actual output has been captured.
4. **Product polish:** replace abstract CSS planet art with original licensed/created art if desired; add keyboard/focus states and accessible mission navigation; add persistent progress only if needed; add decision memo export through API.
5. **Deployment:** deploy frontend to Vercel and API to a Python-capable host; configure CORS and `NEXT_PUBLIC_API_URL`; keep data/API deployment limitations documented. GitHub Actions should test Python and add frontend build checks before deployment.

## Current verification boundary
The files have been generated and packaged. This environment has not installed npm packages, run `next build`, started the FastAPI service, downloaded the real dataset, or verified the resume statistics through the new API. These are explicit next checks, not claimed successes.
