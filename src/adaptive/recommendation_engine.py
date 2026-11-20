"""
Adaptive Guidance and Recommendation Engine.
Dynamically tailors learning pathways based on the learner's evolving profile,
performance patterns, and learning preferences.
Implements the core specifications from PDF Section 4:
- Learner A (Advanced): Skip introductory revision, move to advanced exercises, challenging topics
- Learner B (Average): Planned sequence, additional practice, periodic assessments
- Learner C (Struggling): Revisit foundations, simpler explanations, introductory videos, additional quizzes
"""

from typing import Dict, Any, List
from .course_catalog import CourseCatalog


class RecommendationEngine:
    def __init__(self, course_catalog: CourseCatalog):
        self.catalog = course_catalog

    def generate_recommendations(
        self,
        learner_profile: Dict[str, Any],
        recent_checkpoint: Dict[str, Any],
        course_id: str = "CS101"
    ) -> Dict[str, Any]:
        """
        Synthesizes adaptive guidance from learner metrics and course catalog.
        """
        course = self.catalog.get_course(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found.")

        topics = course.get("topics", [])
        pref_method = learner_profile.get("preferred_learning_method", "Video")
        assessment_score = recent_checkpoint.get("assessment_score", 50.0)
        engagement_pct = recent_checkpoint.get("engagement_pct", 50.0)
        risk_score = recent_checkpoint.get("risk_score_pct", 30.0)
        archetype = learner_profile.get("archetype", "Average")

        recommendations: List[str] = []
        action_items: List[Dict[str, str]] = []
        custom_pathway: List[Dict[str, Any]] = []

        # Decision Logic: Archetype & Metric based adaptive steering
        if archetype == "Advanced" or (assessment_score >= 80.0 and engagement_pct >= 75.0):
            pathway_name = "Accelerated Mastery Pathway"
            recommendations.extend([
                "Skip introductory syntax revision for Python Basics.",
                "Fast-track to advanced recursion, modular design, and OOP challenges.",
                "Unlock high-difficulty capstone mini-project (Student Gradebook System).",
            ])
            action_items.append({"action": "SKIP", "target": "T1: Python Basics (Introductory)", "reason": "Demonstrated mastery"})
            action_items.append({"action": "ENRICH", "target": "T5: Functions (Advanced Recursion)", "reason": "High problem-solving aptitude"})
            action_items.append({"action": "UNLOCK", "target": "T6: OOP Capstone Project", "reason": "Eligible for distinction honors"})

            # Build tailored curriculum sequence
            for t in topics:
                t_copy = dict(t)
                if t["topic_id"] == "T1":
                    t_copy["status"] = "Skipped / Mastered"
                    t_copy["custom_note"] = "Exempted based on diagnostic pre-assessment."
                elif t["topic_id"] in ["T5", "T6"]:
                    t_copy["status"] = "Active Priority"
                    t_copy["custom_note"] = "Enriched with Hard & Capstone algorithmic challenges."
                else:
                    t_copy["status"] = "Accelerated Pace"
                    t_copy["custom_note"] = "Standard self-paced module."
                custom_pathway.append(t_copy)

        elif archetype == "Struggling" or (assessment_score < 50.0 or risk_score >= 50.0):
            pathway_name = "Remedial & Foundational Support Pathway"
            recommendations.extend([
                "Revisit foundational concepts in Variables and Conditionals before moving forward.",
                "Provide bite-sized introductory video explanations and visual trace diagrams.",
                f"Prioritize preferred learning modality: '{pref_method}'.",
                "Offer low-stakes diagnostic practice quizzes with step-by-step hints.",
            ])
            action_items.append({"action": "REINFORCE", "target": "T1 & T2: Foundations & Variables", "reason": "Address core conceptual gaps"})
            action_items.append({"action": "RECOMMEND_FORMAT", "target": f"{pref_method} Walkthroughs", "reason": f"Matches learner profile ({pref_method})"})
            action_items.append({"action": "SCAFFOLD", "target": "T3 & T4: Conditionals & Loops", "reason": "Provide hint scaffolding and extra attempts"})

            for t in topics:
                t_copy = dict(t)
                if t["topic_id"] in ["T1", "T2"]:
                    t_copy["status"] = "Foundational Review"
                    t_copy["custom_note"] = "Review simpler explanations and core building blocks."
                elif t["topic_id"] in ["T3", "T4"]:
                    t_copy["status"] = "Supported Practice"
                    t_copy["custom_note"] = "Guided step-by-step exercises with hints enabled."
                else:
                    t_copy["status"] = "Locked (Pending Foundations)"
                    t_copy["custom_note"] = "Unlocks once conditional and loop checkpoints are passed."
                custom_pathway.append(t_copy)

        else: # Average / Consistent Track
            pathway_name = "Standard Balanced Progression Pathway"
            recommendations.extend([
                "Continue with the planned sequential learning progression.",
                "Provide supplementary interactive practice exercises for medium topics.",
                "Conduct periodic milestone assessments to consolidate retention.",
            ])
            action_items.append({"action": "CONTINUE", "target": "Sequential Course Track", "reason": "Consistent on-track performance"})
            action_items.append({"action": "PRACTICE", "target": "Topic Quizzes and Coding Labs", "reason": "Solidify conceptual mastery"})

            for t in topics:
                t_copy = dict(t)
                t_copy["status"] = "Standard Sequence"
                t_copy["custom_note"] = "Balanced progression of lectures, labs, and quizzes."
                custom_pathway.append(t_copy)

        return {
            "pathway_name": pathway_name,
            "recommendations": recommendations,
            "action_items": action_items,
            "custom_curriculum": custom_pathway,
            "adaptation_rationale": (
                f"Tuned for archetype '{archetype}' with score {assessment_score}% "
                f"and risk level {risk_score}%. Content prioritized for {pref_method} format."
            ),
        }
