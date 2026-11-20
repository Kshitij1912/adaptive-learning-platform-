"""
Learner Journey Tracker Module.
Maintains the persistent state, timeline checkpoints, and feedback loop for learners.
Connects real-time user actions (e.g. submitting quizzes, adopting recommendations)
with dynamic recalibration of the learning trajectory and risk scores.
"""

from typing import Dict, Any, List, Optional
from ..simulation.learner_generator import SyntheticLearner


class JourneyTracker:
    def __init__(self):
        self.learners: Dict[str, SyntheticLearner] = {}
        self.timelines: Dict[str, List[Dict[str, Any]]] = {}
        self.active_recommendations: Dict[str, Dict[str, Any]] = {}
        self.feedback_logs: List[Dict[str, Any]] = []

    def register_learner(self, learner: SyntheticLearner):
        self.learners[learner.learner_id] = learner
        if learner.learner_id not in self.timelines:
            self.timelines[learner.learner_id] = []

    def record_checkpoint(self, learner_id: str, checkpoint_data: Dict[str, Any]):
        if learner_id not in self.timelines:
            self.timelines[learner_id] = []
        self.timelines[learner_id].append(checkpoint_data)

    def get_timeline(self, learner_id: str) -> List[Dict[str, Any]]:
        return self.timelines.get(learner_id, [])

    def get_latest_checkpoint(self, learner_id: str) -> Optional[Dict[str, Any]]:
        timeline = self.get_timeline(learner_id)
        return timeline[-1] if timeline else None

    def set_recommendations(self, learner_id: str, recommendations_data: Dict[str, Any]):
        self.active_recommendations[learner_id] = recommendations_data

    def get_recommendations(self, learner_id: str) -> Optional[Dict[str, Any]]:
        return self.active_recommendations.get(learner_id)

    def record_user_feedback(
        self,
        learner_id: str,
        feedback_type: str,
        notes: str,
        applied: bool
    ) -> Dict[str, Any]:
        """
        Records user/learner feedback on recommendations or pacing.
        Demonstrates continuous testing and user feedback loop.
        """
        entry = {
            "learner_id": learner_id,
            "feedback_type": feedback_type,
            "notes": notes,
            "applied": applied,
        }
        self.feedback_logs.append(entry)

        # If user adopted recommendation, update learner pathway and engagement boost
        if applied and learner_id in self.learners:
            learner = self.learners[learner_id]
            learner.current_engagement = min(0.95, learner.current_engagement + 0.08)
            learner.inactivity_rate = max(0.02, learner.inactivity_rate - 0.05)

        return entry

    def record_quiz_submission(
        self,
        learner_id: str,
        topic_id: str,
        score: float
    ) -> Dict[str, Any]:
        """
        Submits a live quiz or exercise result, immediately updating learner knowledge
        and triggering trajectory evolution.
        """
        if learner_id not in self.learners:
            raise KeyError(f"Learner {learner_id} not registered.")

        learner = self.learners[learner_id]
        learner.assessment_history.append(score)
        learner.current_knowledge = (0.7 * learner.current_knowledge) + (0.3 * score)
        learner.total_clicks += 15

        return {
            "learner_id": learner_id,
            "topic_id": topic_id,
            "score": score,
            "updated_knowledge": round(learner.current_knowledge, 1),
            "total_attempts": len(learner.assessment_history),
        }
