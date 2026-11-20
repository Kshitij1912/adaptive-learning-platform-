"""
Unit Tests for Adaptive Guidance Layer (CourseCatalog, RecommendationEngine, JourneyTracker).
"""

import os
import unittest

from src.simulation.learner_generator import LearnerGenerator
from src.adaptive.course_catalog import CourseCatalog
from src.adaptive.recommendation_engine import RecommendationEngine
from src.adaptive.journey_tracker import JourneyTracker

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COURSES_PATH = os.path.join(PROJECT_ROOT, "data", "courses.json")


class TestAdaptiveEngine(unittest.TestCase):
    def setUp(self):
        self.catalog = CourseCatalog(COURSES_PATH)
        self.rec_engine = RecommendationEngine(self.catalog)
        self.tracker = JourneyTracker()
        self.canonical = LearnerGenerator.create_canonical_learners()

    def test_course_catalog_structure(self):
        courses = self.catalog.list_courses()
        self.assertGreaterEqual(len(courses), 1)
        c1 = self.catalog.get_course("CS101")
        self.assertIsNotNone(c1)
        self.assertEqual(c1["name"], "Introduction to Python Programming")

        topics = self.catalog.get_topics("CS101")
        self.assertGreaterEqual(len(topics), 5)
        self.assertEqual(topics[0]["title"], "Python Basics")

    def test_recommendation_for_advanced_learner(self):
        learner_a = self.canonical["learner_a"]
        checkpoint_a = {"assessment_score": 92.0, "engagement_pct": 95.0, "risk_score_pct": 2.0}
        recs = self.rec_engine.generate_recommendations(learner_a.to_dict(), checkpoint_a)

        self.assertEqual(recs["pathway_name"], "Accelerated Mastery Pathway")
        self.assertTrue(any("Skip" in r for r in recs["recommendations"]))
        # Verify T1 is marked as Skipped in custom syllabus
        t1 = next(t for t in recs["custom_curriculum"] if t["topic_id"] == "T1")
        self.assertIn("Skipped", t1["status"])

    def test_recommendation_for_struggling_learner(self):
        learner_c = self.canonical["learner_c"]
        checkpoint_c = {"assessment_score": 42.0, "engagement_pct": 48.0, "risk_score_pct": 65.0}
        recs = self.rec_engine.generate_recommendations(learner_c.to_dict(), checkpoint_c)

        self.assertEqual(recs["pathway_name"], "Remedial & Foundational Support Pathway")
        self.assertTrue(any("foundational" in r.lower() for r in recs["recommendations"]))
        t1 = next(t for t in recs["custom_curriculum"] if t["topic_id"] == "T1")
        self.assertIn("Foundational", t1["status"])

    def test_journey_tracker_feedback_loop(self):
        learner_b = self.canonical["learner_b"]
        self.tracker.register_learner(learner_b)

        # Record checkpoint
        self.tracker.record_checkpoint(learner_b.learner_id, {"week": 1, "score": 60.0})
        self.assertEqual(len(self.tracker.get_timeline(learner_b.learner_id)), 1)

        # Submit quiz
        quiz_res = self.tracker.record_quiz_submission(learner_b.learner_id, "T2", 85.0)
        self.assertEqual(quiz_res["score"], 85.0)
        self.assertIn(85.0, learner_b.assessment_history)

        # User feedback
        initial_eng = learner_b.current_engagement
        fb = self.tracker.record_user_feedback(learner_b.learner_id, "PACING", "Adopting recommendations", applied=True)
        self.assertTrue(fb["applied"])
        self.assertGreater(learner_b.current_engagement, initial_eng)


if __name__ == "__main__":
    unittest.main()
