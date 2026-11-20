"""
Script to train and evaluate ML models on historical OULAD dataset.
Saves model weights and evaluation metrics.
"""

import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.intelligence.oulad_loader import OULADLoader
from src.intelligence.classifier import OutcomeClassifier
from src.intelligence.clusterer import LearnerClusterer


def main():
    data_path = os.path.join(PROJECT_ROOT, "data", "oulad_historical.csv")
    classifier_path = os.path.join(PROJECT_ROOT, "data", "classifier_model.json")
    clusterer_path = os.path.join(PROJECT_ROOT, "data", "clusterer_model.json")

    print("=" * 60)
    print("OULAD Adaptive Learning Platform - ML Training Pipeline")
    print("=" * 60)

    # 1. Load Data & Engineer Features
    print(f"\n[1/4] Loading historical OULAD dataset from:\n  {data_path}")
    loader = OULADLoader(data_path)
    X, y = loader.extract_features()
    stats = loader.compute_summary_stats()
    print(f"  Loaded {len(X)} records across {X.shape[1]} engineered features.")
    print(f"  Summary stats: {stats}")

    # 2. Train Outcome Classifier
    print("\n[2/4] Training Multi-class Outcome Classifier (Softmax Regression with Momentum)...")
    classifier = OutcomeClassifier(learning_rate=0.08, l2_reg=0.0005, epochs=600)
    classifier.fit(X, y)
    eval_metrics = classifier.evaluate(X, y)
    print(f"  Training accuracy: {eval_metrics['accuracy'] * 100:.2f}%")
    classifier.save(classifier_path)
    print(f"  Saved trained classifier model to:\n    {classifier_path}")

    # 3. Fit Learner Clustering
    print("\n[3/4] Fitting K-Means Clustering for Learner Archetypes (K=4)...")
    clusterer = LearnerClusterer(k=4, max_iters=100, seed=42)
    clusterer.fit(X)
    print("  Discovered Behavioral Cohorts:")
    for k_id, label in clusterer.cluster_names.items():
        print(f"    - Cohort {k_id}: {label}")
    clusterer.save(clusterer_path)
    print(f"  Saved clusterer model to:\n    {clusterer_path}")

    # 4. Validation Sample Prediction
    print("\n[4/4] Running Validation Prediction on sample learner profile...")
    sample_features = [0.85, 0.88, 0.12, 0.05, 0.75, 0.5, 0.0, 0.90]
    pred = classifier.predict_learner_profile(sample_features)
    cluster_id = int(clusterer.predict([sample_features])[0])
    cohort = clusterer.get_cluster_name(cluster_id)
    print(f"  Sample Prediction: {pred['predicted_outcome']} (Risk: {pred['risk_score_pct']}%)")
    print(f"  Class Probabilities: {pred['probabilities']}")
    print(f"  Assigned Cohort: {cohort}")

    print("\n" + "=" * 60)
    print("ML Pipeline Training Complete Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
