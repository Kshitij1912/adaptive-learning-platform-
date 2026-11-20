from dataclasses import dataclass

import pandas as pd

from app.ml.features import CLUSTER_FEATURES, FEATURES
from app.models import Outcome, RiskFlag

RISK_MEDIUM = 0.35  # P(fail or withdraw) thresholds
RISK_HIGH = 0.60


def risk_flag(p: float) -> RiskFlag:
    return RiskFlag.HIGH if p >= RISK_HIGH else RiskFlag.MEDIUM if p >= RISK_MEDIUM else RiskFlag.LOW


@dataclass(frozen=True)
class Prediction:
    outcome: Outcome
    probs: dict[str, float]
    cluster_id: int
    cluster_label: str
    at_risk_prob: float
    risk: RiskFlag


class Predictor:
    def __init__(self, classifier, clusterer, risk_model, meta: dict, classifier_version_id: int):
        self.classifier, self.clusterer, self.risk_model = classifier, clusterer, risk_model
        self.meta = meta
        self.classifier_version_id = classifier_version_id
        self.cluster_labels: dict[int, str] = {int(k): v for k, v in meta.get("cluster_labels", {}).items()}
        self.trained_on: str = meta.get("trained_on", "unknown")

    def predict_batch(self, feats: list[dict]) -> list[Prediction]:
        if not feats:
            return []
        X = pd.DataFrame(feats, columns=FEATURES)
        proba = self.classifier.predict_proba(X)
        classes = [str(c).lower() for c in self.classifier.classes_]
        risk_p = self.risk_model.predict_proba(X)[:, 1]
        clusters = self.clusterer.predict(X[CLUSTER_FEATURES])
        out = []
        for row, rp, cl in zip(proba, risk_p, clusters):
            probs = {c: float(p) for c, p in zip(classes, row)}
            for o in Outcome:
                probs.setdefault(o.value, 0.0)
            best = max(probs, key=probs.get)
            out.append(Prediction(
                Outcome(best), probs, int(cl), self.cluster_labels.get(int(cl), f"Cluster {int(cl)}"),
                float(rp), risk_flag(float(rp)),
            ))
        return out
