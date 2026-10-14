"""Download and validate the public Cookie Cats A/B test dataset without credentials."""
from __future__ import annotations
import io
import sys
import urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw" / "cookie_cats.csv"
EXPECTED_COLUMNS = {"userid", "version", "sum_gamerounds", "retention_1", "retention_7"}
EXPECTED_ROWS = 90189

# Public mirrors; downloader validates content rather than trusting a URL.
SOURCES = [
    "https://raw.githubusercontent.com/ryanschaub/Mobile-Games-A-B-Testing-with-Cookie-Cats/master/cookie_cats.csv",
    "https://raw.githubusercontent.com/AsiMrz/AB-Testing/master/cookie_cats.csv",
    "https://raw.githubusercontent.com/solClover/AB-Testing/master/cookie_cats.csv",
]

def validate_frame(df: pd.DataFrame) -> None:
    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS:,} rows, found {len(df):,}.")
    if df["userid"].isna().any() or df["userid"].duplicated().any():
        raise ValueError("userid must be present and unique.")
    if not set(df["version"].astype(str).unique()).issubset({"gate_30", "gate_40"}):
        raise ValueError("Unexpected version values.")
    if (pd.to_numeric(df["sum_gamerounds"], errors="coerce").isna()).any():
        raise ValueError("sum_gamerounds contains non-numeric values.")

def download() -> Path:
    errors = []
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Cookie Cat/1.0"})
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read()
            df = pd.read_csv(io.BytesIO(raw))
            validate_frame(df)
            DEST.parent.mkdir(parents=True, exist_ok=True)
            temp = DEST.with_suffix(".csv.tmp")
            temp.write_bytes(raw)
            temp.replace(DEST)
            print(f"Validated {len(df):,} rows from {url}")
            print(f"Saved dataset to: {DEST}")
            return DEST
        except Exception as exc:
            errors.append(f"- {url}: {type(exc).__name__}: {exc}")
    raise RuntimeError(
        "Automatic dataset download failed from all public mirrors.\n"
        "No Kaggle credentials or manual CSV download are required by design, but "
        "network access to the mirrors may be blocked or the mirrors may have changed.\n"
        + "\n".join(errors)
    )

if __name__ == "__main__":
    try:
        download()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
