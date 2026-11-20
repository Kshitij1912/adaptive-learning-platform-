"""Pydantic v2 schemas = API contracts (requests + responses)."""
from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models import (
    ContentType, Difficulty, JobStatus, LearnerSource, ModelKind, Outcome,
    RecommendationAction, RecommendationStatus, RiskFlag,
)

T = TypeVar("T")

PREDICTION_NOTE = (
    "Outcomes are model predictions, not actual results. A change in prediction "
    "does not by itself show that a recommendation caused improvement."
)


class APIModel(BaseModel):
    # protected_namespaces=() allows fields like `model_version`
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ---------------------------------------------------------------- common
class Page(APIModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorResponse(APIModel):
    detail: str
    code: str | None = None


# ---------------------------------------------------------------- catalogue
class ContentItemCreate(APIModel):
    title: str = Field(max_length=200)
    content_type: ContentType
    difficulty: Difficulty
    order_index: int = 0
    url: str | None = None


class ContentItemRead(ContentItemCreate):
    id: int
    topic_id: int


class TopicCreate(APIModel):
    name: str = Field(max_length=200)
    order_index: int
    difficulty: Difficulty
    prerequisite_ids: list[int] = []
    content_items: list[ContentItemCreate] = []


class TopicRead(APIModel):
    id: int
    course_id: int
    name: str
    order_index: int
    difficulty: Difficulty
    prerequisite_ids: list[int] = []
    content_items: list[ContentItemRead] = []

    @model_validator(mode="before")
    @classmethod
    def _prereq_ids(cls, v):
        # Accept ORM Topic: derive prerequisite_ids from the relationship.
        if hasattr(v, "prerequisites"):
            return {
                "id": v.id, "course_id": v.course_id, "name": v.name,
                "order_index": v.order_index, "difficulty": v.difficulty,
                "prerequisite_ids": [p.id for p in v.prerequisites],
                "content_items": v.content_items,
            }
        return v


class CourseCreate(APIModel):
    code: str = Field(max_length=50)
    title: str = Field(max_length=200)
    description: str | None = None
    topics: list[TopicCreate] = []


class CourseRead(APIModel):
    id: int
    code: str
    title: str
    description: str | None
    created_at: datetime
    topics: list[TopicRead] = []


# ---------------------------------------------------------------- learners
class LearnerCreate(APIModel):
    source: LearnerSource = LearnerSource.SYNTHETIC
    external_id: str | None = None
    course_id: int | None = None
    age: int | None = Field(None, ge=10, le=100)
    age_band: str | None = None
    education: str | None = None
    initial_knowledge: float | None = Field(None, ge=0, le=1)
    learning_speed: float | None = Field(None, ge=0, le=1)
    engagement_baseline: float | None = Field(None, ge=0, le=1)
    preferred_method: ContentType | None = None
    archetype: Literal["advanced", "average", "struggling"] | None = None


class LearnerRead(LearnerCreate):
    id: int
    sim_run_id: str | None
    actual_outcome: Outcome | None  # observed / simulated ground truth, NOT a prediction
    created_at: datetime


# ---------------------------------------------------------------- activity ingestion
class InteractionCreate(APIModel):
    content_item_id: int | None = None
    day: int | None = Field(None, ge=0)
    activity_type: str = Field(max_length=50)
    clicks: int = Field(0, ge=0)
    duration_min: float | None = Field(None, ge=0)


class AssessmentCreate(APIModel):
    topic_id: int | None = None
    assessment_type: str | None = None
    score: float = Field(ge=0)
    max_score: float = Field(100.0, gt=0)

    @model_validator(mode="after")
    def _score_le_max(self):
        if self.score > self.max_score:
            raise ValueError("score cannot exceed max_score")
        return self


class ActivityBatch(APIModel):
    """POST /learners/{id}/interactions body: one week of new activity."""
    week: int = Field(ge=0, le=60)
    interactions: list[InteractionCreate] = []
    assessments: list[AssessmentCreate] = []

    @model_validator(mode="after")
    def _not_empty(self):
        if not self.interactions and not self.assessments:
            raise ValueError("provide at least one interaction or assessment")
        return self


# ---------------------------------------------------------------- model registry
class ModelVersionRead(APIModel):
    id: int
    kind: ModelKind
    name: str
    version: str
    metrics: dict | None
    trained_on: str
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------------- profile / checkpoints
class CheckpointRead(APIModel):
    id: int
    learner_id: int
    week: int
    engagement: float = Field(ge=0, le=1)
    assessment_score: float | None = Field(None, ge=0, le=1)
    predicted_outcome: Outcome
    outcome_probs: dict[str, float]
    cluster_id: int | None
    risk: RiskFlag
    model_version_id: int
    created_at: datetime


class ProfileRequest(APIModel):
    week: int | None = Field(None, ge=0, le=60, description="Defaults to the learner's latest week")


class ProfileResponse(APIModel):
    learner_id: int
    source: LearnerSource
    checkpoint: CheckpointRead
    cluster_label: str | None = None
    is_prediction: Literal[True] = True
    note: str = PREDICTION_NOTE


# ---------------------------------------------------------------- recommendations
class RecommendationRead(APIModel):
    id: int
    checkpoint_id: int
    action: RecommendationAction
    content_item: ContentItemRead | None = None
    rule_id: str
    rationale: str | None
    status: RecommendationStatus
    created_at: datetime


class RecommendResponse(APIModel):
    learner_id: int
    week: int
    risk: RiskFlag
    recommendations: list[RecommendationRead]


class RecommendationStatusUpdate(APIModel):
    status: RecommendationStatus


class AdaptiveStepResponse(APIModel):
    """Result of one pass through the adaptive loop (ingest -> profile -> recommend)."""
    learner_id: int
    checkpoint: CheckpointRead
    recommendations: list[RecommendationRead]
    is_prediction: Literal[True] = True
    note: str = PREDICTION_NOTE


# ---------------------------------------------------------------- journey
class JourneyPoint(APIModel):
    checkpoint: CheckpointRead
    recommendations: list[RecommendationRead] = []


class JourneyResponse(APIModel):
    learner_id: int
    source: LearnerSource
    actual_outcome: Outcome | None  # shown separately from predictions
    points: list[JourneyPoint]
    note: str = PREDICTION_NOTE


# ---------------------------------------------------------------- simulation
class SimulateRequest(APIModel):
    n_learners: int = Field(1000, ge=1, le=10000)
    weeks: int = Field(8, ge=1, le=52)
    course_id: int
    seed: int = 42
    archetype_mix: dict[Literal["advanced", "average", "struggling"], float] | None = Field(
        None, description="Fractions summing to 1. Defaults to an even split."
    )

    @model_validator(mode="after")
    def _mix_sums_to_one(self):
        if self.archetype_mix and abs(sum(self.archetype_mix.values()) - 1.0) > 1e-6:
            raise ValueError("archetype_mix must sum to 1")
        return self


class SimulateAccepted(APIModel):
    sim_run_id: str
    status: JobStatus


class SimulateStatus(APIModel):
    sim_run_id: str
    status: JobStatus
    n_learners: int
    learners_created: int
    weeks: int
    seed: int
    error: str | None = None
    created_at: datetime


# ---------------------------------------------------------------- reports
class ClusterSummary(APIModel):
    cluster_id: int
    label: str | None
    size: int
    avg_engagement: float
    avg_assessment_score: float | None


class WeeklyTrendPoint(APIModel):
    week: int
    avg_engagement: float
    avg_assessment_score: float | None
    outcome_distribution: dict[str, int]


class CohortReport(APIModel):
    source: LearnerSource | None
    sim_run_id: str | None
    course_id: int | None
    n_learners: int
    latest_outcome_distribution: dict[str, int]   # predicted
    risk_distribution: dict[str, int]
    clusters: list[ClusterSummary]
    weekly_trend: list[WeeklyTrendPoint]
    note: str = PREDICTION_NOTE
