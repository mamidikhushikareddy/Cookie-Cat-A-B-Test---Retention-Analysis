"""Dataset loading, approved dataset registry and provenance."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
# Only approved dataset IDs are loadable (no client-supplied paths).
APPROVED = {"cookie_cats": ROOT / "data" / "raw" / "cookie_cats.csv"}


class DatasetNotApproved(KeyError):
    pass


@dataclass(frozen=True)
class Provenance:
    dataset_id: str
    path: str
    size_bytes: int
    sha256: str
    rows: int
    columns: list[str]


def resolve(dataset_id: str) -> Path:
    if dataset_id not in APPROVED:
        raise DatasetNotApproved(f"Unknown dataset id {dataset_id!r}; approved: {sorted(APPROVED)}")
    return APPROVED[dataset_id]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_raw(dataset_id: str = "cookie_cats", path: Path | None = None) -> pd.DataFrame:
    """Load without coercion; validation is the contract's job."""
    return pd.read_csv(path or resolve(dataset_id))


def provenance(dataset_id: str = "cookie_cats", path: Path | None = None) -> Provenance:
    p = path or resolve(dataset_id)
    df = pd.read_csv(p)
    return Provenance(dataset_id, p.name, p.stat().st_size, sha256_file(p), len(df), list(df.columns))
