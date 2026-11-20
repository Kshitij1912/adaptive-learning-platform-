"""SQLAlchemy 2.0 ORM models for the adaptive learning platform."""
import enum
from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, CheckConstraint, Column, DateTime, Enum, Float, ForeignKey,
    Index, Integer, String, Table, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# --------------------------------------------------------------------------
# Enums (stored as VARCHAR for SQLite/Postgres portability and easy Alembic)
# --------------------------------------------------------------------------
class LearnerSource(str, enum.Enum):
    OULAD = "oulad"
    SYNTHETIC = "synthetic"


class Outcome(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    DISTINCTION = "distinction"
    WITHDRAWN = "withdrawn"


class RiskFlag(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContentType(str, enum.Enum):
    VIDEO = "video"
    READING = "reading"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    VIDEO_EXAMPLES = "video_examples"


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class RecommendationAction(str, enum.Enum):
    SKIP_INTRO = "skip_intro"
    ADVANCE = "advance"
    CONTINUE = "continue"
    EXTRA_PRACTICE = "extra_practice"
    REMEDIATE = "remediate"
    ASSESS = "assess"


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ModelKind(str, enum.Enum):
    CLASSIFIER = "classifier"
    CLUSTERING = "clustering"
    RISK = "risk"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


def enum_col(e: type[enum.Enum]) -> Enum:
    """Store enum *values* as VARCHAR (no native PG enum type)."""
    return Enum(
        e, native_enum=False, length=32, validate_strings=True,
        values_callable=lambda x: [m.value for m in x],
    )


class Base(DeclarativeBase):
    pass


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# --------------------------------------------------------------------------
# Application layer: course catalogue (synthetic content)
# --------------------------------------------------------------------------
topic_prerequisites = Table(
    "topic_prerequisites",
    Base.metadata,
    Column("topic_id", ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    Column("prerequisite_id", ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    CheckConstraint("topic_id <> prerequisite_id", name="ck_topic_not_self_prereq"),
)


class Course(CreatedAtMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    topics: Mapped[list["Topic"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="Topic.order_index"
    )
    learners: Mapped[list["Learner"]] = relationship(back_populates="course")


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("course_id", "order_index", name="uq_topic_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    order_index: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[Difficulty] = mapped_column(enum_col(Difficulty))

    course: Mapped["Course"] = relationship(back_populates="topics")
    content_items: Mapped[list["ContentItem"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan", order_by="ContentItem.order_index"
    )
    prerequisites: Mapped[list["Topic"]] = relationship(
        secondary=topic_prerequisites,
        primaryjoin=id == topic_prerequisites.c.topic_id,
        secondaryjoin=id == topic_prerequisites.c.prerequisite_id,
    )


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content_type: Mapped[ContentType] = mapped_column(enum_col(ContentType))
    difficulty: Mapped[Difficulty] = mapped_column(enum_col(Difficulty))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str | None] = mapped_column(String(500))

    topic: Mapped["Topic"] = relationship(back_populates="content_items")


# --------------------------------------------------------------------------
# Learners (real OULAD + synthetic). `source` keeps the layers separated.
# --------------------------------------------------------------------------
class Learner(CreatedAtMixin, Base):
    __tablename__ = "learners"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_learner_source_external"),
        CheckConstraint("initial_knowledge IS NULL OR (initial_knowledge BETWEEN 0 AND 1)", name="ck_knowledge_range"),
        CheckConstraint("learning_speed IS NULL OR (learning_speed BETWEEN 0 AND 1)", name="ck_speed_range"),
        CheckConstraint("engagement_baseline IS NULL OR (engagement_baseline BETWEEN 0 AND 1)", name="ck_engagement_range"),
        Index("ix_learners_sim_run", "sim_run_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[LearnerSource] = mapped_column(enum_col(LearnerSource), index=True)
    external_id: Mapped[str | None] = mapped_column(String(64))  # OULAD id_student
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"), index=True)

    # Demographics
    age: Mapped[int | None] = mapped_column(Integer)          # synthetic
    age_band: Mapped[str | None] = mapped_column(String(20))  # OULAD ("0-35", "35-55", "55<=")
    education: Mapped[str | None] = mapped_column(String(80))

    # Synthetic-only traits (NULL for OULAD learners)
    initial_knowledge: Mapped[float | None] = mapped_column(Float)
    learning_speed: Mapped[float | None] = mapped_column(Float)
    engagement_baseline: Mapped[float | None] = mapped_column(Float)
    preferred_method: Mapped[ContentType | None] = mapped_column(enum_col(ContentType))
    archetype: Mapped[str | None] = mapped_column(String(30))  # advanced / average / struggling
    sim_run_id: Mapped[str | None] = mapped_column(String(36))

    # Observed outcome (OULAD final_result, or simulated ground truth). Not a prediction.
    actual_outcome: Mapped[Outcome | None] = mapped_column(enum_col(Outcome))

    course: Mapped["Course | None"] = relationship(back_populates="learners")
    interactions: Mapped[list["Interaction"]] = relationship(back_populates="learner", cascade="all, delete-orphan")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="learner", cascade="all, delete-orphan")
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan", order_by="Checkpoint.week"
    )


class Interaction(Base):
    __tablename__ = "interactions"
    __table_args__ = (Index("ix_interactions_learner_week", "learner_id", "week"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"))
    content_item_id: Mapped[int | None] = mapped_column(ForeignKey("content_items.id", ondelete="SET NULL"))
    week: Mapped[int] = mapped_column(Integer)
    day: Mapped[int | None] = mapped_column(Integer)           # day offset from course start
    activity_type: Mapped[str] = mapped_column(String(50))     # OULAD activity_type or content type
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    duration_min: Mapped[float | None] = mapped_column(Float)

    learner: Mapped["Learner"] = relationship(back_populates="interactions")


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        Index("ix_assessments_learner_week", "learner_id", "week"),
        CheckConstraint("score >= 0 AND score <= max_score", name="ck_score_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    week: Mapped[int] = mapped_column(Integer)
    assessment_type: Mapped[str | None] = mapped_column(String(30))  # quiz / TMA / CMA / exam
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float, default=100.0)

    learner: Mapped["Learner"] = relationship(back_populates="assessments")


# --------------------------------------------------------------------------
# Intelligence layer: model registry, predictions, recommendations
# --------------------------------------------------------------------------
class ModelVersion(CreatedAtMixin, Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("kind", "version", name="uq_model_kind_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[ModelKind] = mapped_column(enum_col(ModelKind))
    name: Mapped[str] = mapped_column(String(100))             # e.g. "gradient_boosting"
    version: Mapped[str] = mapped_column(String(50))
    artifact_path: Mapped[str] = mapped_column(String(500))
    metrics: Mapped[dict | None] = mapped_column(JSON)         # accuracy, macro-F1, silhouette...
    trained_on: Mapped[str] = mapped_column(String(50), default="oulad")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class Checkpoint(CreatedAtMixin, Base):
    """Weekly snapshot of a learner's profile. All outcome fields are PREDICTIONS."""
    __tablename__ = "checkpoints"
    __table_args__ = (
        UniqueConstraint("learner_id", "week", "model_version_id", name="uq_checkpoint_learner_week_model"),
        CheckConstraint("engagement BETWEEN 0 AND 1", name="ck_cp_engagement"),
        CheckConstraint("assessment_score IS NULL OR (assessment_score BETWEEN 0 AND 1)", name="ck_cp_score"),
        Index("ix_checkpoints_learner_week", "learner_id", "week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id", ondelete="CASCADE"))
    week: Mapped[int] = mapped_column(Integer)
    engagement: Mapped[float] = mapped_column(Float)                   # normalized 0-1
    assessment_score: Mapped[float | None] = mapped_column(Float)      # normalized 0-1
    predicted_outcome: Mapped[Outcome] = mapped_column(enum_col(Outcome))
    outcome_probs: Mapped[dict] = mapped_column(JSON)                  # {"pass": 0.6, ...}
    cluster_id: Mapped[int | None] = mapped_column(Integer)
    risk: Mapped[RiskFlag] = mapped_column(enum_col(RiskFlag))
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))  # classifier version

    learner: Mapped["Learner"] = relationship(back_populates="checkpoints")
    model_version: Mapped["ModelVersion"] = relationship()
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="checkpoint", cascade="all, delete-orphan"
    )


class Recommendation(CreatedAtMixin, Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    checkpoint_id: Mapped[int] = mapped_column(ForeignKey("checkpoints.id", ondelete="CASCADE"), index=True)
    action: Mapped[RecommendationAction] = mapped_column(enum_col(RecommendationAction))
    content_item_id: Mapped[int | None] = mapped_column(ForeignKey("content_items.id", ondelete="SET NULL"))
    rule_id: Mapped[str] = mapped_column(String(50))           # which rule fired (traceability)
    rationale: Mapped[str | None] = mapped_column(Text)
    status: Mapped[RecommendationStatus] = mapped_column(
        enum_col(RecommendationStatus), default=RecommendationStatus.PENDING
    )

    checkpoint: Mapped["Checkpoint"] = relationship(back_populates="recommendations")
    content_item: Mapped["ContentItem | None"] = relationship()


# --------------------------------------------------------------------------
# Simulation runs (background job tracking)
# --------------------------------------------------------------------------
class SimulationRun(CreatedAtMixin, Base):
    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # uuid4
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id", ondelete="SET NULL"))
    n_learners: Mapped[int] = mapped_column(Integer)
    weeks: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int] = mapped_column(Integer)
    archetype_mix: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[JobStatus] = mapped_column(enum_col(JobStatus), default=JobStatus.QUEUED)
    learners_created: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
