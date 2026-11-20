"""
Learner Clustering Module.
Implements K-Means clustering to discover learner behavioral archetypes.
Groups learners into actionable cohorts:
- Cohort 0: High Achiever / Fast Paced
- Cohort 1: Steady Learner / Consistent
- Cohort 2: Struggling / Guidance Needed
- Cohort 3: At Risk / Withdrawing
"""

import json
from typing import Dict, Any, List, Optional
import numpy as np


class LearnerClusterer:
    CLUSTER_LABELS = {
        0: "High Achiever (Fast Paced)",
        1: "Steady Learner (Consistent)",
        2: "Struggling Learner (Guidance Needed)",
        3: "At-Risk Learner (Disengaging)",
    }

    def __init__(self, k: int = 4, max_iters: int = 100, seed: int = 42):
        self.k = k
        self.max_iters = max_iters
        self.seed = seed
        self.centroids: Optional[np.ndarray] = None
        self.cluster_names: Dict[int, str] = {}
        self.is_fitted = False

    def fit(self, X: np.ndarray):
        rng = np.random.default_rng(self.seed)
        n_samples, n_features = X.shape

        # Initialize centroids with k-means++ scheme
        centroids = [X[rng.integers(n_samples)]]
        for _ in range(1, self.k):
            dists = np.array([min(np.sum((x - c) ** 2) for c in centroids) for x in X])
            probs = dists / np.sum(dists)
            cumprobs = np.cumsum(probs)
            r = rng.random()
            idx = np.searchsorted(cumprobs, r)
            centroids.append(X[min(idx, n_samples - 1)])

        self.centroids = np.array(centroids, dtype=np.float64)

        # Iterative optimization
        for _ in range(self.max_iters):
            # Compute distances to centroids
            # X: (N, D), centroids: (K, D) -> diffs: (N, K, D)
            diffs = X[:, np.newaxis, :] - self.centroids[np.newaxis, :, :]
            dists = np.sum(diffs ** 2, axis=2)  # shape (N, K)
            labels = np.argmin(dists, axis=1)

            # Update centroids
            new_centroids = np.zeros_like(self.centroids)
            for j in range(self.k):
                members = X[labels == j]
                if len(members) > 0:
                    new_centroids[j] = np.mean(members, axis=0)
                else:
                    new_centroids[j] = X[rng.integers(n_samples)]

            if np.allclose(self.centroids, new_centroids, atol=1e-4):
                break
            self.centroids = new_centroids

        self._assign_semantic_cohort_labels(X)
        self.is_fitted = True

    def _assign_semantic_cohort_labels(self, X: np.ndarray):
        """
        Sort clusters by assessment score and engagement to assign consistent archetypes.
        Index 1 in feature vector is avg_assessment; Index 7 is engagement_index.
        """
        diffs = X[:, np.newaxis, :] - self.centroids[np.newaxis, :, :]
        dists = np.sum(diffs ** 2, axis=2)
        labels = np.argmin(dists, axis=1)

        cohort_scores = []
        for j in range(self.k):
            members = X[labels == j]
            if len(members) > 0:
                avg_assess = float(np.mean(members[:, 1]))
                avg_engage = float(np.mean(members[:, 7]))
                inactivity = float(np.mean(members[:, 3]))
            else:
                avg_assess, avg_engage, inactivity = 0.5, 0.5, 0.5
            cohort_scores.append((j, avg_assess, avg_engage, inactivity))

        # Sort: Highest assessment + engagement first
        cohort_scores.sort(key=lambda item: (item[1] + item[2] - item[3]), reverse=True)

        self.cluster_names = {}
        semantic_archetypes = [
            "Advanced Learner (Fast-Paced)",
            "Average Learner (Consistent Track)",
            "Struggling Learner (High Effort, Low Scores)",
            "Disengaged Learner (High Inactivity / At-Risk)",
        ]
        for rank, (cluster_idx, _, _, _) in enumerate(cohort_scores):
            label = semantic_archetypes[rank] if rank < len(semantic_archetypes) else f"Cluster {cluster_idx}"
            self.cluster_names[cluster_idx] = label

    def predict(self, X: Any) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Clusterer has not been fitted yet.")
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        diffs = X[:, np.newaxis, :] - self.centroids[np.newaxis, :, :]
        dists = np.sum(diffs ** 2, axis=2)
        return np.argmin(dists, axis=1)

    def get_cluster_name(self, cluster_id: int) -> str:
        return self.cluster_names.get(cluster_id, f"Cohort {cluster_id}")

    def save(self, filepath: str):
        data = {
            "centroids": self.centroids.tolist() if self.centroids is not None else None,
            "k": self.k,
            "cluster_names": {str(k): v for k, v in self.cluster_names.items()},
            "is_fitted": self.is_fitted,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.centroids = np.array(data["centroids"])
        self.k = data["k"]
        self.cluster_names = {int(k): v for k, v in data["cluster_names"].items()}
        self.is_fitted = data["is_fitted"]
