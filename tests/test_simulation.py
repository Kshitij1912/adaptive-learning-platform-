"""
Unit Tests for Simulation Layer (LearnerGenerator, InteractionSimulator).
"""

import os
import unittest

from src.simulation.learner_generator import LearnerGenerator, SyntheticLearner
from src.simulation.interaction_simulator import InteractionSimulator
from src.intelligence.classifier import OutcomeClassifier
from src.intelligence.clusterer import LearnerClusterer
from src.intelligence.pattern_analyzer import PatternAnalyzer

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestSimulationLayer(unittest.TestCase):
    def setUp(self):
        self.canonical = LearnerGenerator.create_canonical_learners()
        self.classifier = OutcomeClassifier()
        clf_path = os.path.join(PROJECT_ROOT, "data", "classifier_model.json")
        if os.path.exists(clf_path):
            self.classifier.load(clf_path)

        self.clusterer = LearnerClusterer()
        clu_path = os.path.join(PROJECT_ROOT, "data", "clusterer_model.json")
        if os.path.exists(clu_path):
            self.clusterer.load(clu_path)

        self.sim = InteractionSimulator(
            classifier=self.classifier,
            clusterer=self.clusterer,
            pattern_analyzer=PatternAnalyzer
        )

    def test_canonical_learners_attributes(self):
        self.assertIn("learner_a", self.canonical)
        self.assertIn("learner_b", self.canonical)
        self.assertIn("learner_c", self.canonical)

        learner_a = self.canonical["learner_a"]
        self.assertEqual(learner_a.archetype, "Advanced")
        self.assertGreater(learner_a.initial_knowledge, 70.0)
        self.assertGreater(learner_a.learning_speed, 0.8)

        learner_c = self.canonical["learner_c"]
        self.assertEqual(learner_c.archetype, "Struggling")
        self.assertLess(learner_c.initial_knowledge, 40.0)

    def test_population_generation(self):
        pop = LearnerGenerator.generate_population(size=50)
        self.assertEqual(len(pop), 50)
        for p in pop:
            self.assertIsInstance(p, SyntheticLearner)
            self.assertIn(p.preferred_learning_method, ["Video", "Practice", "Reading"])

    def test_simulate_checkpoint_step(self):
        learner_a = self.canonical["learner_a"]
        res = self.sim.simulate_checkpoint(learner_a, week=1, adaptation_active=True)
        self.assertEqual(res["week"], 1)
        self.assertIn("assessment_score", res)
        self.assertIn("predicted_outcome", res)
        self.assertIn("risk_score_pct", res)

    def test_adaptive_vs_non_adaptive_trajectory(self):
        # Learner C should improve with adaptation, decline or stagnate without
        learner_c_adapt = LearnerGenerator.create_canonical_learners()["learner_c"]
        learner_c_no_adapt = LearnerGenerator.create_canonical_learners()["learner_c"]

        journey_adapt = self.sim.simulate_full_journey(learner_c_adapt, checkpoints=[1, 3, 5, 8], adaptation_active=True)
        journey_no_adapt = self.sim.simulate_full_journey(learner_c_no_adapt, checkpoints=[1, 3, 5, 8], adaptation_active=False)

        final_adapt_score = journey_adapt[-1]["assessment_score"]
        final_no_adapt_score = journey_no_adapt[-1]["assessment_score"]

        self.assertGreater(final_adapt_score, final_no_adapt_score)
        self.assertLess(journey_adapt[-1]["risk_score_pct"], journey_no_adapt[-1]["risk_score_pct"])


if __name__ == "__main__":
    unittest.main()
