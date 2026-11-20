import json
from pathlib import Path

import joblib
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.predict import Predictor
from app.models import ModelKind, ModelVersion

_CACHE: dict[tuple, Predictor] = {}


def get_predictor(db: Session) -> Predictor | None:
    """Predictor built from the active classifier + clustering + risk versions, or None."""
    rows = db.scalars(select(ModelVersion).where(ModelVersion.is_active.is_(True)).order_by(ModelVersion.id)).all()
    by_kind = {r.kind: r for r in rows}  # latest active per kind wins
    if not all(k in by_kind for k in ModelKind):
        return None
    key = tuple(sorted((k.value, r.id, r.artifact_path) for k, r in by_kind.items()))
    if key not in _CACHE:
        clf_row = by_kind[ModelKind.CLASSIFIER]
        meta = json.loads((Path(clf_row.artifact_path).parent / "meta.json").read_text())
        _CACHE.clear()
        _CACHE[key] = Predictor(
            joblib.load(clf_row.artifact_path),
            joblib.load(by_kind[ModelKind.CLUSTERING].artifact_path),
            joblib.load(by_kind[ModelKind.RISK].artifact_path),
            meta, clf_row.id,
        )
    return _CACHE[key]
