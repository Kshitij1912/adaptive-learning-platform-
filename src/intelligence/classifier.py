"""
Learner Outcome Classifier.
Predicts academic outcome (Distinction, Pass, Fail, Withdrawn) and assesses academic risk.
Implemented with vectorised Softmax Regression and feature standardisation using NumPy.
"""

import json
from typing import Dict, Any, List, Optional
import numpy as np


class OutcomeClassifier:
    CLASSES = ["Withdrawn", "Fail", "Pass", "Distinction"]

    def __init__(self, learning_rate: float = 0.05, l2_reg: float = 0.001, epochs: int = 400):
        self.learning_rate = learning_rate
        self.l2_reg = l2_reg
        self.epochs = epochs
        self.weights: Optional[np.ndarray] = None  # shape (n_features, n_classes)
        self.bias: Optional[np.ndarray] = None     # shape (n_classes,)
        self.mean: Optional[np.ndarray] = None
        self.std: Optional[np.ndarray] = None
        self.is_trained = False

    def _softmax(self, z: np.ndarray) -> np.ndarray:
        exp_z = np.exp(z - np.max(z, axis=-1, keepdims=True))
        return exp_z / np.sum(exp_z, axis=-1, keepdims=True)

    def fit(self, X: np.ndarray, y: np.ndarray):
        n_samples, n_features = X.shape
        n_classes = len(self.CLASSES)

        # Standardise features
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0)
        self.std[self.std == 0] = 1.0
        X_norm = (X - self.mean) / self.std

        # One-hot encode y
        Y_onehot = np.zeros((n_samples, n_classes))
        for i, val in enumerate(y):
            Y_onehot[i, val] = 1.0

        # Initialize weights with Xavier uniform
        rng = np.random.default_rng(42)
        bound = np.sqrt(6.0 / (n_features + n_classes))
        self.weights = rng.uniform(-bound, bound, (n_features, n_classes))
        self.bias = np.zeros(n_classes)

        # Momentum optimizer
        v_w = np.zeros_like(self.weights)
        v_b = np.zeros_like(self.bias)
        beta = 0.9

        for epoch in range(self.epochs):
            # Forward pass
            logits = np.dot(X_norm, self.weights) + self.bias
            probs = self._softmax(logits)

            # Gradient calculation
            error = probs - Y_onehot
            grad_w = (np.dot(X_norm.T, error) / n_samples) + (self.l2_reg * self.weights)
            grad_b = np.mean(error, axis=0)

            # Momentum update
            v_w = beta * v_w + (1 - beta) * grad_w
            v_b = beta * v_b + (1 - beta) * grad_b

            self.weights -= self.learning_rate * v_w
            self.bias -= self.learning_rate * v_b

        self.is_trained = True

    def predict_proba(self, X: Any) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Classifier has not been trained yet.")
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        X_norm = (X - self.mean) / self.std
        logits = np.dot(X_norm, self.weights) + self.bias
        return self._softmax(logits)

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        preds = self.predict(X)
        accuracy = float(np.mean(preds == y))
        return {"accuracy": round(accuracy, 4)}

    def predict_learner_profile(self, features: List[float]) -> Dict[str, Any]:
        """
        Takes raw features of a single learner and returns class probabilities,
        predicted outcome label, and calculated risk score.
        """
        arr = np.array(features, dtype=np.float64)
        probs = self.predict_proba(arr)[0]
        pred_idx = int(np.argmax(probs))
        predicted_outcome = self.CLASSES[pred_idx]

        # Academic risk is probability of Withdrawn or Fail
        risk_score = round(float(probs[0] + probs[1]) * 100, 1)

        return {
            "predicted_outcome": predicted_outcome,
            "probabilities": {self.CLASSES[i]: round(float(probs[i]), 3) for i in range(len(self.CLASSES))},
            "risk_score_pct": risk_score,
            "is_at_risk": risk_score >= 50.0,
        }

    def save(self, filepath: str):
        data = {
            "weights": self.weights.tolist() if self.weights is not None else None,
            "bias": self.bias.tolist() if self.bias is not None else None,
            "mean": self.mean.tolist() if self.mean is not None else None,
            "std": self.std.tolist() if self.std is not None else None,
            "learning_rate": self.learning_rate,
            "is_trained": self.is_trained,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.weights = np.array(data["weights"])
        self.bias = np.array(data["bias"])
        self.mean = np.array(data["mean"])
        self.std = np.array(data["std"])
        self.learning_rate = data["learning_rate"]
        self.is_trained = data["is_trained"]
