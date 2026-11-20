"""
Simulation CLI Demonstration Script.
Executes multi-checkpoint learning journeys for Learner A, Learner B, and Learner C.
Demonstrates the core PDF concept:
"The same course can produce different learning journeys for different Learners.
Maintain an evolving profile for every Learner across checkpoints: Week 1, 3, 5, 8."
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.intelligence.classifier import OutcomeClassifier
from src.intelligence.clusterer import LearnerClusterer
from src.intelligence.pattern_analyzer import PatternAnalyzer
from src.simulation.learner_generator import LearnerGenerator
from src.simulation.interaction_simulator import InteractionSimulator
from src.adaptive.course_catalog import CourseCatalog
from src.adaptive.recommendation_engine import RecommendationEngine


def run_demo():
    print("=" * 80)
    print("     ADAPTIVE LEARNING SIMULATOR - MULTI-LEARNER JOURNEY DEMO     ")
    print("=" * 80)

    # 1. Load ML models
    classifier = OutcomeClassifier()
    classifier.load(os.path.join(PROJECT_ROOT, "data", "classifier_model.json"))

    clusterer = LearnerClusterer()
    clusterer.load(os.path.join(PROJECT_ROOT, "data", "clusterer_model.json"))

    catalog = CourseCatalog(os.path.join(PROJECT_ROOT, "data", "courses.json"))
    rec_engine = RecommendationEngine(catalog)
    sim = InteractionSimulator(classifier=classifier, clusterer=clusterer, pattern_analyzer=PatternAnalyzer)

    # 2. Get canonical learners
    canonical = LearnerGenerator.create_canonical_learners()

    checkpoints = [1, 3, 5, 8]

    for key, learner in canonical.items():
        print(f"\n" + "-" * 80)
        print(f"PROFILE: {learner.name.upper()} | Base Knowledge: {learner.initial_knowledge}% | Method: {learner.preferred_learning_method}")
        print("-" * 80)

        print(f"{'Checkpoint':<12} | {'Engagement':<12} | {'Assessment':<12} | {'Predicted Outcome':<20} | {'Risk %':<8}")
        print("-" * 72)

        journey = sim.simulate_full_journey(learner, checkpoints=checkpoints, adaptation_active=True)

        for step in journey:
            print(f"Week {step['week']:<7} | {step['engagement_pct']:>6.1f}%     | {step['assessment_score']:>6.1f}%     | {step['predicted_outcome']:<20} | {step['risk_score_pct']:>5.1f}%")

        # Generate Adaptive Guidance for this learner's final state
        final_step = journey[-1]
        guidance = rec_engine.generate_recommendations(learner.to_dict(), final_step)
        print(f"\n  [Adaptive Pathway Generated]: {guidance['pathway_name']}")
        print("  [System Recommendations]:")
        for rec in guidance["recommendations"]:
            print(f"    * {rec}")
        print("  [Action Items in Syllabus]:")
        for act in guidance["action_items"]:
            print(f"    - [{act['action']}] {act['target']} -> {act['reason']}")

    print("\n" + "=" * 80)
    print("DEMO SUMMARY: All three learners took 'Introduction to Python Programming',")
    print("yet received 3 entirely distinct, personalized pathways and dynamic support!")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
