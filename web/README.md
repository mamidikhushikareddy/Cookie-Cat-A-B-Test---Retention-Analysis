# Cookie Cat web frontend

Next.js/React frontend for the Cookie Cat Experiment Odyssey. It uses a custom responsive CSS design system, an explorable mission map, and a decision chamber that renders only results returned by the Python API.

## Run locally
1. Start the Python API from the repository root (see `../api/README.md`).
2. In this directory run `npm install`, then `npm run dev`.
3. Open http://localhost:3000.

Set `NEXT_PUBLIC_API_URL` if the API is not at `http://127.0.0.1:8000`. If the dataset is missing or API is offline, the UI intentionally shows a clear empty state instead of fabricated statistics.
