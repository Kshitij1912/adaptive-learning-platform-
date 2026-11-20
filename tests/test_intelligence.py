"""
Unit Tests for Intelligence Layer (OULAD loader, Classifier, Clusterer, Pattern Analyzer).
"""

import os
import unittest
import numpy as np

from src.intelligence.oulad_loader import OULADLoader
from src.intelligence.classifier import OutcomeClassifier
from src.intelligence.clusterer import LearnerClusterer
from src.intelligence.pattern_analyzer import PatternAnalyzer

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "oulad_historical.csv")


class TestIntelligenceLayer(unittest.TestCase):
    def setUp(self):
        self.loader = OULADLoader(DATA_PATH)
        self.X, self.y = self.loader.extract_features()

    def test_oulad_loader_features(self):
        self.assertGreater(len(self.X), 100)
        self.assertEqual(self.X.shape[1], 8)
        self.assertEqual(len(self.X), len(self.y))
        stats = self.loader.compute_summary_stats()
        self.assertIn("outcome_distribution", stats)
        self.assertIn("avg_clicks", stats)

    def test_classifier_fit_and_predict(self):
        clf = OutcomeClassifier(learning_rate=0.1, epochs=100)
        clf.fit(self.X, self.y)
        self.assertTrue(clf.is_trained)

        # Single profile prediction
        sample = self.X[0]
        res = clf.predict_learner_profile(sample.tolist())
        self.assertIn(res["predicted_outcome"], OutcomeClassifier.CLASSES)
        self.assertGreaterEqual(res["risk_score_pct"], 0.0)
        self.assertLessEqual(res["risk_score_pct"], 100.0)

        # Probability sum test
        prob_sum = sum(res["probabilities"].values())
        self.assertAlmostEqual(prob_sum, 1.0, places=2)

    def test_clusterer_fit_and_cohorts(self):
        clusterer = LearnerClusterer(k=4, max_iters=50, seed=42)
        clusterer.fit(self.X)
        self.assertTrue(clusterer.is_fitted)
        self.assertEqual(len(clusterer.cluster_names), 4)

        labels = clusterer.predict(self.X[:10])
        self.assertEqual(len(labels), 10)
        self.assertTrue(all(0 <= lbl < 4 for lbl in labels))

    def test_pattern_analyzer_rules(self):
        # Rule 1: High engagement + good assessment -> High performance
        p1 = PatternAnalyzer.analyze_patterns(engagement_pct=85.0, assessment_pct=88.0, score_trend=0.08, inactivity_pct=5.0)
        self.assertEqual(p1["status_category"], "High Performer")
        self.assertTrue(any("Likely high performance" in s for s in p1["inferences"]))

        # Rule 2: High engagement + poor assessment -> Guidance needed
        p2 = PatternAnalyzer.analyze_patterns(engagement_pct=80.0, assessment_pct=40.0, score_trend=-0.02, inactivity_pct=10.0)
        self.assertEqual(p2["status_category"], "Guidance Needed")
        self.assertTrue(any("Learner needs additional guidance" in s for s in p2["inferences"]))

        # Rule 3: Low engagement + declining scores -> Potentially at risk
        p3 = PatternAnalyzer.analyze_patterns(engagement_pct=30.0, assessment_pct=42.0, score_trend=-0.12, inactivity_pct=25.0)
        self.assertEqual(p3["status_category"], "Academic Risk")
        self.assertTrue(any("Potentially at risk" in s for s in p3["inferences"]))

        # Rule 4: Good engagement + improving scores -> Positive trajectory
        p4 = PatternAnalyzer.analyze_patterns(engagement_pct=65.0, assessment_pct=60.0, score_trend=0.15, inactivity_pct=10.0)
        self.assertTrue(any("Positive learning trajectory" in s for s in p4["inferences"]))

        # Rule 5: Increasing inactivity -> Potential withdrawal risk
        p5 = PatternAnalyzer.analyze_patterns(engagement_pct=40.0, assessment_pct=45.0, score_trend=-0.01, inactivity_pct=45.0)
        self.assertEqual(p5["status_category"], "Withdrawal Risk")
        self.assertTrue(any("Potential withdrawal risk" in s for s in p5["inferences"]))


if __name__ == "__main__":
    unittest.main()
