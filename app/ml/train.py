"""Offline training on OULAD-format data. Never run in the request path."""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, silhouette_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.ml.features import CLUSTER_FEATURES, FEATURES
from app.ml.oulad import build_training_frame, is_dev_standin, load_oulad
from app.models import ModelKind, ModelVersion

DEFAULT_WEEKS = (1, 2, 3, 4, 6, 8, 10, 12, 16, 20, 24)
N_CLUSTERS = 4


def _label_clusters(pipe: Pipeline) -> dict[int, str]:
    centers = pipe.named_steps["scaler"].inverse_transform(pipe.named_steps["km"].cluster_centers_)
    ie, isc = CLUSTER_FEATURES.index("engagement"), CLUSTER_FEATURES.index("avg_score")
    me, ms = np.median(centers[:, ie]), np.median(centers[:, isc])
    labels, seen = {}, {}
    for i, c in enumerate(centers):
        hi_e, hi_s = c[ie] >= me, c[isc] >= ms
        name = ("High engagement, strong scores" if hi_e and hi_s else
                "Engaged, needs guidance" if hi_e else
                "Low engagement, solid scores" if hi_s else "Low engagement, at risk")
        seen[name] = seen.get(name, 0) + 1
        labels[i] = name if seen[name] == 1 else f"{name} ({chr(64 + seen[name])})"
    return labels


def train_bundle(data_dir, out_dir, version: str, weeks=DEFAULT_WEEKS, seed: int = 42,
                 n_estimators: int = 200) -> dict:
    enrolls = load_oulad(data_dir)
    df = build_training_frame(enrolls, weeks)
    X, y = df[FEATURES], df["outcome"]
    y_risk = y.isin(["Fail", "Withdrawn"]).astype(int)

    tr, te = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed).split(X, y, df["student"]))
    clf = RandomForestClassifier(n_estimators=n_estimators, min_samples_leaf=3, class_weight="balanced_subsample",
                                 n_jobs=-1, random_state=seed).fit(X.iloc[tr], y.iloc[tr])
    risk = RandomForestClassifier(n_estimators=n_estimators, min_samples_leaf=3, class_weight="balanced_subsample",
                                  n_jobs=-1, random_state=seed).fit(X.iloc[tr], y_risk.iloc[tr])

    Xte, yte = X.iloc[te], y.iloc[te]
    pred = clf.predict(Xte)
    by_week = {int(w): round(float(accuracy_score(yte[m], pred[m.to_numpy()])), 4)
               for w in sorted(Xte["week"].unique()) if (m := (Xte["week"] == w)).any()}
    clf_metrics = {
        "holdout_accuracy": round(float(accuracy_score(yte, pred)), 4),
        "holdout_macro_f1": round(float(f1_score(yte, pred, average="macro")), 4),
        "majority_baseline_accuracy": round(float(yte.value_counts(normalize=True).iloc[0]), 4),
        "accuracy_by_week": by_week,
    }
    risk_metrics = {"holdout_roc_auc": round(float(roc_auc_score(y_risk.iloc[te], risk.predict_proba(Xte)[:, 1])), 4)}

    ctr = X.iloc[tr]
    ctr = ctr[ctr["week"] >= 4][CLUSTER_FEATURES]
    pipe = Pipeline([("scaler", StandardScaler()),
                     ("km", KMeans(N_CLUSTERS, n_init=10, random_state=seed))]).fit(ctr)
    sample = ctr.sample(min(5000, len(ctr)), random_state=seed)
    sil = float(silhouette_score(pipe.named_steps["scaler"].transform(sample),
                                 pipe.named_steps["km"].predict(pipe.named_steps["scaler"].transform(sample))))
    clus_metrics = {"silhouette": round(sil, 4), "k": N_CLUSTERS}

    bundle = Path(out_dir) / version
    bundle.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, bundle / "classifier.joblib")
    joblib.dump(pipe, bundle / "clusterer.joblib")
    joblib.dump(risk, bundle / "risk.joblib")
    meta = {
        "version": version, "trained_on": "dev_standin" if is_dev_standin(data_dir) else "oulad",
        "features": FEATURES, "cluster_features": CLUSTER_FEATURES, "classes": [str(c) for c in clf.classes_],
        "cluster_labels": _label_clusters(pipe), "weeks": list(weeks),
        "n_enrollments": len(enrolls), "n_rows": len(df), "seed": seed,
        "metrics": {"classifier": clf_metrics, "risk": risk_metrics, "clustering": clus_metrics},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (bundle / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def register_bundle(db: Session, bundle_dir, activate: bool = True) -> list[ModelVersion]:
    bundle = Path(bundle_dir).resolve()
    meta = json.loads((bundle / "meta.json").read_text())
    spec = [
        (ModelKind.CLASSIFIER, "random_forest", "classifier.joblib", meta["metrics"]["classifier"]),
        (ModelKind.CLUSTERING, "kmeans", "clusterer.joblib", meta["metrics"]["clustering"]),
        (ModelKind.RISK, "random_forest_at_risk", "risk.joblib", meta["metrics"]["risk"]),
    ]
    rows = []
    for kind, name, fname, metrics in spec:
        if activate:
            db.execute(update(ModelVersion).where(ModelVersion.kind == kind).values(is_active=False))
        row = ModelVersion(kind=kind, name=name, version=meta["version"], artifact_path=str(bundle / fname),
                           metrics=metrics, trained_on=meta["trained_on"], is_active=activate)
        db.add(row)
        rows.append(row)
    db.commit()
    return rows
