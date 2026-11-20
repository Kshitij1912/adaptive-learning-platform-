"""
Simulation Layer: Synthetic learners generation and week-by-week interaction simulation.
"""

from .learner_generator import SyntheticLearner, LearnerGenerator
from .interaction_simulator import InteractionSimulator

__all__ = ["SyntheticLearner", "LearnerGenerator", "InteractionSimulator"]
