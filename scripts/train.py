"""Train + register models.   python -m scripts.train --data-dir data/oulad --version v1"""
import argparse
import json

from app.config import settings
from app.db import SessionLocal, engine
from app.ml.train import DEFAULT_WEEKS, register_bundle, train_bundle
from app.models import Base

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="folder with the OULAD CSVs")
    ap.add_argument("--version", required=True)
    ap.add_argument("--weeks", default=",".join(map(str, DEFAULT_WEEKS)))
    ap.add_argument("--estimators", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    meta = train_bundle(a.data_dir, settings.artifact_dir, a.version,
                        weeks=tuple(int(w) for w in a.weeks.split(",")), seed=a.seed, n_estimators=a.estimators)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        register_bundle(db, settings.artifact_dir / a.version)
    print(json.dumps(meta["metrics"], indent=2))
    print(f"trained_on={meta['trained_on']}  registered + activated version {a.version}")
