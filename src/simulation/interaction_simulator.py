"""
Interaction Simulator Module.
Simulates week-by-week learning interactions, assessments, and profile evolution.
Implements the multi-checkpoint trajectory envisioned in PDF Section 6:
Tracks:
- Week 1, 3, 5, 8 checkpoints
- Dynamic influence of adaptive recommendations on engagement and scores
- Separation between historical evidence and simulated results (PDF Section 7 & 8)
"""

import random
from typing import Dict, Any, List, Optional
from .learner_generator import SyntheticLearner


class InteractionSimulator:
    CHECKPOINTS = [1, 2, 3, 4, 5, 6, 7, 8]

    def __init__(self, classifier=None, clusterer=None, pattern_analyzer=None):
        self.classifier = classifier
        self.clusterer = clusterer
        self.pattern_analyzer = pattern_analyzer

    def simulate_checkpoint(
        self,
        learner: SyntheticLearner,
        week: int,
        adaptation_active: bool = True,
        applied_recommendations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Simulates learner progress up to a given week.
        Shows how personalized recommendations improve engagement and assessment outcomes over time.
        """
        applied_recommendations = applied_recommendations or []

        # Pacing and impact based on archetype
        if learner.archetype == "Advanced":
            # Advanced learners excel, especially when challenged with advanced exercises
            bonus = 0.08 if adaptation_active else 0.02
            learner.current_engagement = min(0.98, learner.engagement_baseline + (week * 0.02) + bonus)
            knowledge_gain = (learner.learning_speed * 12.0) + (bonus * 20.0)
            learner.current_knowledge = min(98.0, learner.current_knowledge + knowledge_gain)
            learner.inactivity_rate = max(0.02, 0.10 - (week * 0.01))
            learner.total_clicks += int(random.randint(200, 380) * learner.current_engagement)

            score_mean = min(96.0, learner.current_knowledge + random.uniform(-2.0, 4.0))
            score = round(max(60.0, score_mean), 1)

        elif learner.archetype == "Average":
            # Average learners steady climb with standard practice and periodic quizzes
            bonus = 0.05 if adaptation_active else 0.0
            learner.current_engagement = min(0.85, learner.engagement_baseline + (week * 0.025) + bonus)
            knowledge_gain = (learner.learning_speed * 8.5) + (bonus * 10.0)
            learner.current_knowledge = min(88.0, learner.current_knowledge + knowledge_gain)
            learner.inactivity_rate = max(0.05, 0.18 - (week * 0.015))
            learner.total_clicks += int(random.randint(140, 240) * learner.current_engagement)

            score_mean = learner.current_knowledge + random.uniform(-4.0, 3.0)
            score = round(min(88.0, max(45.0, score_mean)), 1)

        elif learner.archetype == "Struggling":
            # PDF specific trajectory: starts at ~40%, but with adaptive remedial videos and quizzes climbs to pass!
            if adaptation_active:
                # With adaptive guidance (remedial videos, simpler steps), trajectory turns positive!
                learner.current_engagement = min(0.80, 0.45 + (week * 0.045))
                knowledge_gain = (learner.learning_speed * 9.0) + (week * 3.5)
                learner.current_knowledge = min(78.0, 35.0 + knowledge_gain)
                learner.inactivity_rate = max(0.08, 0.35 - (week * 0.035))
                learner.total_clicks += int(random.randint(110, 220) * learner.current_engagement)
                score_mean = learner.current_knowledge + random.uniform(-3.0, 3.0)
                score = round(min(80.0, max(38.0, score_mean)), 1)
            else:
                # Without adaptation, struggling learners decline or drop out
                learner.current_engagement = max(0.20, learner.engagement_baseline - (week * 0.03))
                learner.inactivity_rate = min(0.70, 0.35 + (week * 0.04))
                learner.total_clicks += int(random.randint(30, 80))
                score = round(max(25.0, 42.0 - (week * 2.0) + random.uniform(-4.0, 2.0)), 1)

        else: # At-Risk / Disengaged
            if adaptation_active and week >= 2:
                learner.current_engagement = min(0.65, 0.25 + (week * 0.05))
                learner.inactivity_rate = max(0.18, 0.60 - (week * 0.05))
                score = round(min(65.0, 30.0 + (week * 4.0) + random.uniform(-3.0, 3.0)), 1)
            else:
                learner.current_engagement = max(0.10, learner.engagement_baseline - (week * 0.02))
                learner.inactivity_rate = min(0.85, 0.55 + (week * 0.04))
                score = round(max(15.0, 32.0 - (week * 2.5)), 1)

        learner.assessment_history.append(score)

        # Calculate score trend
        if len(learner.assessment_history) >= 2:
            score_trend = (learner.assessment_history[-1] - learner.assessment_history[0]) / (100.0 * len(learner.assessment_history))
        else:
            score_trend = 0.0

        engagement_pct = round(learner.current_engagement * 100, 1)
        inactivity_pct = round(learner.inactivity_rate * 100, 1)

        # ML Predictions (Layer 1 Integration)
        pred_outcome = "Pass"
        risk_score = 30.0
        probabilities = {}
        cluster_name = "Consistent"
        patterns: List[str] = []

        if self.classifier and self.classifier.is_trained:
            # Construct feature vector matching OULADLoader:
            # [norm_clicks, avg_assessment, score_trend, inactivity_rate, edu_level, norm_credits, prev_att, engagement_index]
            max_clicks = 2500.0
            norm_clicks = min(1.0, learner.total_clicks / max_clicks)
            norm_assessment = score / 100.0
            edu_val = {"Undergraduate": 0.5, "A Level or Equivalent": 0.5, "Lower Than A Level": 0.25}.get(learner.education, 0.5)
            engagement_index = (0.5 * norm_clicks) + (0.5 * (1.0 - learner.inactivity_rate))

            features = [
                norm_clicks,
                norm_assessment,
                score_trend,
                learner.inactivity_rate,
                edu_val,
                0.5,  # norm credits
                0.0,  # prev attempts
                engagement_index,
            ]

            pred_res = self.classifier.predict_learner_profile(features)
            pred_outcome = pred_res["predicted_outcome"]
            risk_score = pred_res["risk_score_pct"]
            probabilities = pred_res["probabilities"]

            if self.clusterer and self.clusterer.is_fitted:
                c_id = int(self.clusterer.predict([features])[0])
                cluster_name = self.clusterer.get_cluster_name(c_id)

        if self.pattern_analyzer:
            pat_res = self.pattern_analyzer.analyze_patterns(
                engagement_pct=engagement_pct,
                assessment_pct=score,
                score_trend=score_trend,
                inactivity_pct=inactivity_pct,
            )
            patterns = pat_res["inferences"]

        checkpoint_data = {
            "week": week,
            "learner_id": learner.learner_id,
            "learner_name": learner.name,
            "engagement_pct": engagement_pct,
            "assessment_score": score,
            "score_trend": round(score_trend, 3),
            "inactivity_pct": inactivity_pct,
            "total_clicks": learner.total_clicks,
            "predicted_outcome": pred_outcome,
            "risk_score_pct": risk_score,
            "probabilities": probabilities,
            "cluster_cohort": cluster_name,
            "patterns": patterns,
            "adaptation_active": adaptation_active,
        }

        return checkpoint_data

    def simulate_full_journey(
        self,
        learner: SyntheticLearner,
        checkpoints: Optional[List[int]] = None,
        adaptation_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Runs an entire learning journey through checkpoints (e.g. Weeks 1, 3, 5, 8 as highlighted in PDF).
        """
        if checkpoints is None:
            checkpoints = [1, 3, 5, 8]

        journey = []
        for wk in checkpoints:
            step = self.simulate_checkpoint(learner, week=wk, adaptation_active=adaptation_active)
            journey.append(step)
        return journey
