"""
Unit and Integration Tests for API Application Logic.
Directly tests the route handlers and state interactions cleanly.
"""

import unittest
from src.api.app import (
    get_health,
    get_historical_stats,
    list_learners,
    create_learner,
    get_learner,
    get_learner_journey,
    simulate_step,
    simulate_all,
    submit_quiz,
    submit_feedback,
    get_courses,
    CreateLearnerRequest,
    FeedbackRequest,
    QuizSubmissionRequest,
    tracker
)


class TestAPIRoutes(unittest.TestCase):
    def test_health_route(self):
        res = get_health()
        self.assertEqual(res["status"], "healthy")
        self.assertTrue(res["models_loaded"]["classifier"])
        self.assertTrue(res["models_loaded"]["clusterer"])

    def test_stats_route(self):
        stats = get_historical_stats()
        self.assertIn("total_students", stats)
        self.assertIn("outcome_distribution", stats)

    def test_list_learners_route(self):
        learners = list_learners()
        self.assertGreaterEqual(len(learners), 3)

    def test_create_and_fetch_learner_route(self):
        req = CreateLearnerRequest(
            name="Alice Wonder",
            archetype="Advanced",
            age=22,
            education="Undergraduate",
            initial_knowledge=75.0,
            learning_speed=0.85,
            engagement_baseline=0.80,
            preferred_learning_method="Practice"
        )
        res = create_learner(req)
        self.assertEqual(res["message"], "Learner successfully created")
        lid = res["learner"]["learner_id"]

        detail = get_learner(lid)
        self.assertEqual(detail["learner"]["name"], "Alice Wonder")

        journey = get_learner_journey(lid)
        self.assertGreaterEqual(len(journey["timeline"]), 1)

    def test_simulate_step_and_all_routes(self):
        lid = "SYN-A-101"
        res_step = simulate_step(lid, adaptation_active=True)
        self.assertIn("new_checkpoint", res_step)

        res_all = simulate_all(lid, adaptation_active=True)
        self.assertEqual(len(res_all["journey"]), 4)

    def test_quiz_and_feedback_routes(self):
        lid = "SYN-B-102"
        quiz_req = QuizSubmissionRequest(topic_id="T2", score=90.0)
        q_res = submit_quiz(lid, quiz_req)
        self.assertEqual(q_res["quiz_result"]["score"], 90.0)

        fb_req = FeedbackRequest(feedback_type="PACE", notes="Optimal pacing", applied=True)
        fb_res = submit_feedback(lid, fb_req)
        self.assertEqual(fb_res["status"], "Feedback recorded")
        self.assertTrue(fb_res["entry"]["applied"])

    def test_courses_route(self):
        courses = get_courses()
        self.assertGreaterEqual(len(courses), 1)
        self.assertEqual(courses[0]["id"], "CS101")


if __name__ == "__main__":
    unittest.main()
