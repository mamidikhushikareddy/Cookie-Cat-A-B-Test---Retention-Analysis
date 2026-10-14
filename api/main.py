"""FastAPI bridge to the existing, dataset-derived Cookie Cats analysis."""
from pathlib import Path
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.cookie_cat import load_and_validate, analyze
app = FastAPI(title="Cookie Cat Analysis API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])
DATA = ROOT / "data" / "raw" / "cookie_cats.csv"
@app.get("/health")
def health():
    return {"status":"ok", "dataset_present":DATA.exists(), "analysis":"dataset-derived"}
@app.get("/api/analysis")
def get_analysis():
    if not DATA.exists():
        raise HTTPException(status_code=503, detail="Dataset missing. Run python scripts/download_data.py from the project root.")
    try:
        df = load_and_validate(DATA)
        return analyze(df)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dataset analysis failed: {type(exc).__name__}: {exc}") from exc
