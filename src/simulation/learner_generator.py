"""
Synthetic Learner Generator.
Extends the learning platform beyond historical OULAD records.
Generates realistic synthetic learners with attributes specified in the project PDF:
- Age
- Education
- Initial knowledge %
- Learning speed (0.1 - 1.0)
- Engagement level (0.1 - 1.0)
- Preferred learning method (Video, Practice, Reading)
- Canonical Archetypes: Learner A (Advanced), Learner B (Average), Learner C (Struggling)
"""

import random
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class SyntheticLearner:
    learner_id: str
    name: str
    archetype: str
    age: int
    education: str
    initial_knowledge: float       # Percentage 0.0 - 100.0
    learning_speed: float          # Multiplier 0.1 - 1.0
    engagement_baseline: float     # 0.0 - 1.0
    preferred_learning_method: str # 'Video', 'Practice', 'Reading'
    enrolled_course_id: str = "CS101"
    current_knowledge: float = 0.0
    current_engagement: float = 0.0
    inactivity_rate: float = 0.0
    total_clicks: int = 0
    assessment_history: List[float] = None
    active_pathway: str = "Standard"

    def __post_init__(self):
        if self.assessment_history is None:
            self.assessment_history = []
        if self.current_knowledge == 0.0:
            self.current_knowledge = self.initial_knowledge
        if self.current_engagement == 0.0:
            self.current_engagement = self.engagement_baseline

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LearnerGenerator:
    EDUCATION_LEVELS = [
        "Lower Than A Level",
        "A Level or Equivalent",
        "Undergraduate",
        "HE Qualification",
        "Postgraduate",
    ]

    METHODS = ["Video", "Practice", "Reading"]

    @classmethod
    def create_canonical_learners(cls) -> Dict[str, SyntheticLearner]:
        """
        Creates the 3 core reference learners highlighted in PDF Section 3 & 4:
        - Learner A: Advanced Learner (Studies regularly, fast progress, high scores)
        - Learner B: Average Learner (Moderate engagement, planned sequence)
        - Learner C: Struggling Learner (Low performance, repeated difficulty)
        """
        learner_a = SyntheticLearner(
            learner_id="SYN-A-101",
            name="Learner A (Advanced)",
            archetype="Advanced",
            age=22,
            education="Undergraduate",
            initial_knowledge=72.0,
            learning_speed=0.88,
            engagement_baseline=0.85,
            preferred_learning_method="Practice",
            active_pathway="Accelerated",
        )

        learner_b = SyntheticLearner(
            learner_id="SYN-B-102",
            name="Learner B (Average)",
            archetype="Average",
            age=24,
            education="A Level or Equivalent",
            initial_knowledge=52.0,
            learning_speed=0.62,
            engagement_baseline=0.60,
            preferred_learning_method="Video",
            active_pathway="Standard",
        )

        learner_c = SyntheticLearner(
            learner_id="SYN-C-103",
            name="Learner C (Struggling)",
            archetype="Struggling",
            age=26,
            education="Lower Than A Level",
            initial_knowledge=32.0,
            learning_speed=0.38,
            engagement_baseline=0.42,
            preferred_learning_method="Video",
            active_pathway="Remedial / Foundational",
        )

        return {
            "learner_a": learner_a,
            "learner_b": learner_b,
            "learner_c": learner_c,
        }

    @classmethod
    def generate_random_learner(
        cls,
        archetype: Optional[str] = None,
        learner_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> SyntheticLearner:
        if archetype is None:
            archetype = random.choices(
                ["Advanced", "Average", "Struggling", "At-Risk"],
                weights=[0.20, 0.45, 0.25, 0.10]
            )[0]

        lid = learner_id or f"SYN-{uuid.uuid4().hex[:6].upper()}"
        lname = name or f"Learner {lid.split('-')[-1]}"

        if archetype == "Advanced":
            age = random.randint(20, 30)
            edu = random.choice(["Undergraduate", "HE Qualification", "Postgraduate"])
            init_k = round(random.uniform(68.0, 85.0), 1)
            spd = round(random.uniform(0.75, 0.95), 2)
            eng = round(random.uniform(0.75, 0.95), 2)
        elif archetype == "Average":
            age = random.randint(18, 45)
            edu = random.choice(["A Level or Equivalent", "Undergraduate"])
            init_k = round(random.uniform(45.0, 65.0), 1)
            spd = round(random.uniform(0.50, 0.72), 2)
            eng = round(random.uniform(0.50, 0.70), 2)
        elif archetype == "Struggling":
            age = random.randint(19, 50)
            edu = random.choice(["Lower Than A Level", "A Level or Equivalent"])
            init_k = round(random.uniform(25.0, 48.0), 1)
            spd = round(random.uniform(0.30, 0.48), 2)
            eng = round(random.uniform(0.40, 0.65), 2)  # May have moderate engagement but struggles
        else: # At-Risk
            age = random.randint(18, 55)
            edu = random.choice(["Lower Than A Level", "No Formal quals", "A Level or Equivalent"])
            init_k = round(random.uniform(15.0, 38.0), 1)
            spd = round(random.uniform(0.20, 0.40), 2)
            eng = round(random.uniform(0.15, 0.38), 2)

        method = random.choice(cls.METHODS)

        return SyntheticLearner(
            learner_id=lid,
            name=lname,
            archetype=archetype,
            age=age,
            education=edu,
            initial_knowledge=init_k,
            learning_speed=spd,
            engagement_baseline=eng,
            preferred_learning_method=method,
        )

    @classmethod
    def generate_population(cls, size: int = 1000) -> List[SyntheticLearner]:
        """Generates 1,000 synthetic learners as envisioned in PDF Section 3."""
        population = []
        for i in range(1, size + 1):
            lid = f"SYN-{1000 + i}"
            learner = cls.generate_random_learner(learner_id=lid, name=f"Synthetic Student #{i}")
            population.append(learner)
        return population
