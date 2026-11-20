"""HTTP layer: validation + orchestration only. Logic lives in app/services and app/ml."""
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.ml.registry import get_predictor
from app.models import (ContentItem, ContentType, Course, Learner, LearnerSource, ModelVersion, Recommendation,
                        SimulationRun, Topic, Checkpoint)
from app.schemas import (
    ActivityBatch, AdaptiveStepResponse, CheckpointRead, CohortReport, CourseCreate, CourseRead, ErrorResponse,
    HealthResponse, JourneyPoint, JourneyResponse, LearnerCreate, LearnerRead, ModelVersionRead, Page,
    ProfileRequest, ProfileResponse, RecommendationRead, RecommendationStatusUpdate, RecommendResponse,
    SimulateAccepted, SimulateRequest, SimulateStatus,
)
from app.services import journey, reports
from app.services.simulator import run_simulation

NF = {404: {"model": ErrorResponse, "description": "Not found"}}
NO_MODEL = {409: {"model": ErrorResponse, "description": "No active model"}}
LearnerId = Annotated[int, Path(ge=1)]
DB = Annotated[Session, Depends(get_db)]

router = APIRouter()


def _learner(db: Session, learner_id: int) -> Learner:
    learner = db.get(Learner, learner_id)
    if learner is None:
        raise HTTPException(404, "Learner not found")
    return learner


def _predictor(db: Session):
    p = get_predictor(db)
    if p is None:
        raise HTTPException(409, "No active model. Train one: python -m scripts.train --data-dir <oulad> --version v1")
    return p


# ------------------------------------------------------------- health / models
@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(db: DB):
    p = get_predictor(db)
    return HealthResponse(active_model=p is not None, model_trained_on=p.trained_on if p else None)


@router.get("/models", response_model=list[ModelVersionRead], tags=["models"])
def list_models(db: DB, active_only: bool = False):
    q = select(ModelVersion).order_by(ModelVersion.id.desc())
    if active_only:
        q = q.where(ModelVersion.is_active.is_(True))
    return list(db.scalars(q))


# ------------------------------------------------------------- courses
@router.post("/courses", response_model=CourseRead, status_code=201, tags=["courses"],
             responses={409: {"model": ErrorResponse, "description": "Course code exists"},
                        422: {"description": "Invalid topic ordering or prerequisites"}})
def create_course(body: CourseCreate, db: DB):
    orders = [t.order_index for t in body.topics]
    if len(set(orders)) != len(orders):
        raise HTTPException(422, "Duplicate topic order_index")
    course = Course(code=body.code, title=body.title, description=body.description)
    by_order: dict[int, Topic] = {}
    for spec in body.topics:
        t = Topic(name=spec.name, order_index=spec.order_index, difficulty=spec.difficulty)
        t.content_items = [ContentItem(**ci.model_dump()) for ci in spec.content_items]
        by_order[spec.order_index] = t
        course.topics.append(t)
    for spec in body.topics:
        for o in spec.prerequisite_orders:
            if o not in by_order or o == spec.order_index:
                raise HTTPException(422, f"Invalid prerequisite order {o} for topic {spec.order_index}")
            by_order[spec.order_index].prerequisites.append(by_order[o])
    db.add(course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Course code already exists")
    return course


@router.get("/courses", response_model=Page[CourseRead], tags=["courses"])
def list_courses(db: DB, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    total = db.scalar(select(func.count()).select_from(Course))
    items = list(db.scalars(select(Course).order_by(Course.id).limit(limit).offset(offset)))
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/courses/{course_id}", response_model=CourseRead, tags=["courses"], responses=NF)
def get_course(course_id: Annotated[int, Path(ge=1)], db: DB):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "Course not found")
    return course


# ------------------------------------------------------------- learners
@router.post("/learners", response_model=LearnerRead, status_code=201, tags=["learners"],
             responses={**NF, 409: {"model": ErrorResponse, "description": "(source, external_id) exists"}})
def create_learner(body: LearnerCreate, db: DB):
    if body.course_id is not None and db.get(Course, body.course_id) is None:
        raise HTTPException(404, "Course not found")
    learner = Learner(**body.model_dump())
    db.add(learner)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Learner with this source and external_id already exists")
    return learner


@router.get("/learners", response_model=Page[LearnerRead], tags=["learners"])
def list_learners(db: DB, source: LearnerSource | None = None, sim_run_id: str | None = None,
                  course_id: int | None = None, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    q = select(Learner)
    if source:
        q = q.where(Learner.source == source)
    if sim_run_id:
        q = q.where(Learner.sim_run_id == sim_run_id)
    if course_id:
        q = q.where(Learner.course_id == course_id)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = list(db.scalars(q.order_by(Learner.id).limit(limit).offset(offset)))
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/learners/{learner_id}", response_model=LearnerRead, tags=["learners"], responses=NF)
def get_learner(learner_id: LearnerId, db: DB):
    return _learner(db, learner_id)


@router.post("/learners/{learner_id}/interactions", response_model=AdaptiveStepResponse, status_code=201,
             tags=["adaptive loop"], responses={**NF, **NO_MODEL, 422: {"description": "Unknown content/topic id"}})
def post_activity(learner_id: LearnerId, body: ActivityBatch, db: DB):
    """Store activity -> recompute weekly features -> profile -> checkpoint -> recommend."""
    learner = _learner(db, learner_id)
    predictor = _predictor(db)
    item_ids = {i.content_item_id for i in body.interactions if i.content_item_id is not None}
    topic_ids = {a.topic_id for a in body.assessments if a.topic_id is not None}
    if item_ids and db.scalar(select(func.count()).select_from(ContentItem).where(ContentItem.id.in_(item_ids))) != len(item_ids):
        raise HTTPException(422, "Unknown content_item_id")
    if topic_ids and db.scalar(select(func.count()).select_from(Topic).where(Topic.id.in_(topic_ids))) != len(topic_ids):
        raise HTTPException(422, "Unknown topic_id")
    journey.store_activity(db, learner, body)
    cp, recs = journey.run_step(db, learner, body.week, predictor)
    return AdaptiveStepResponse(learner_id=learner.id, checkpoint=cp, recommendations=recs)


# ------------------------------------------------------------- simulation
@router.post("/simulate", response_model=SimulateAccepted, status_code=202, tags=["simulation"],
             responses={**NF, **NO_MODEL, 422: {"description": "Course has no content"}})
def start_simulation(body: SimulateRequest, tasks: BackgroundTasks, db: DB):
    if db.get(Course, body.course_id) is None:
        raise HTTPException(404, "Course not found")
    _predictor(db)
    has_content = db.scalar(select(func.count()).select_from(ContentItem).join(Topic)
                            .where(Topic.course_id == body.course_id))
    if not has_content:
        raise HTTPException(422, "Course has no content items")
    run = SimulationRun(id=str(uuid.uuid4()), course_id=body.course_id, n_learners=body.n_learners,
                        weeks=body.weeks, seed=body.seed, archetype_mix=body.archetype_mix,
                        recommendation_effect=body.recommendation_effect)
    db.add(run)
    db.commit()
    tasks.add_task(run_simulation, run.id)
    return SimulateAccepted(sim_run_id=run.id, status=run.status)


@router.get("/simulate/{sim_run_id}", response_model=SimulateStatus, tags=["simulation"], responses=NF)
def simulation_status(sim_run_id: str, db: DB):
    run = db.get(SimulationRun, sim_run_id)
    if run is None:
        raise HTTPException(404, "Simulation run not found")
    return SimulateStatus(sim_run_id=run.id, status=run.status, n_learners=run.n_learners,
                          learners_created=run.learners_created, weeks=run.weeks, seed=run.seed,
                          recommendation_effect=run.recommendation_effect, error=run.error,
                          created_at=run.created_at)


# ------------------------------------------------------------- profile / recommend / journey
@router.post("/profile/{learner_id}", response_model=ProfileResponse, tags=["adaptive loop"],
             responses={**NF, 409: {"model": ErrorResponse, "description": "No active model, or no activity yet"}})
def profile_learner(learner_id: LearnerId, db: DB, body: ProfileRequest | None = None):
    learner = _learner(db, learner_id)
    predictor = _predictor(db)
    week = body.week if body and body.week is not None else journey.series_for(db, learner.id).latest_week
    if week is None:
        raise HTTPException(409, "No activity recorded for this learner yet")
    cp, _ = journey.profile_learner(db, learner, week, predictor)
    return ProfileResponse(learner_id=learner.id, source=learner.source, checkpoint=cp,
                           cluster_label=predictor.cluster_labels.get(cp.cluster_id))


@router.get("/recommend/{learner_id}", response_model=RecommendResponse, tags=["adaptive loop"],
            responses={**NF, 409: {"model": ErrorResponse, "description": "No checkpoint yet; call /profile first"}})
def get_recommendations(learner_id: LearnerId, db: DB, week: int | None = Query(None, ge=0, le=60)):
    learner = _learner(db, learner_id)
    q = select(Checkpoint).where(Checkpoint.learner_id == learner.id)
    q = q.where(Checkpoint.week == week) if week is not None else q
    cp = db.scalar(q.order_by(Checkpoint.week.desc(), Checkpoint.id.desc()).limit(1))
    if cp is None:
        raise HTTPException(409, "No checkpoint yet; call POST /profile/{id} first")
    recs = journey.ensure_recommendations(db, learner, cp)
    return RecommendResponse(learner_id=learner.id, week=cp.week, risk=cp.risk, recommendations=recs)


@router.patch("/recommendations/{recommendation_id}", response_model=RecommendationRead,
              tags=["adaptive loop"], responses=NF)
def update_recommendation_status(recommendation_id: Annotated[int, Path(ge=1)],
                                 body: RecommendationStatusUpdate, db: DB):
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(404, "Recommendation not found")
    rec.status = body.status
    db.commit()
    return rec


@router.get("/journey/{learner_id}", response_model=JourneyResponse, tags=["adaptive loop"], responses=NF)
def get_journey(learner_id: LearnerId, db: DB):
    learner = _learner(db, learner_id)
    cps = list(db.scalars(select(Checkpoint).where(Checkpoint.learner_id == learner.id)
                          .order_by(Checkpoint.week, Checkpoint.id)))
    return JourneyResponse(learner_id=learner.id, source=learner.source, actual_outcome=learner.actual_outcome,
                           points=[JourneyPoint(checkpoint=cp, recommendations=list(cp.recommendations)) for cp in cps])


# ------------------------------------------------------------- reports
@router.get("/reports/cohort", response_model=CohortReport, tags=["reports"])
def cohort_report(db: DB, source: LearnerSource | None = None, sim_run_id: str | None = None,
                  course_id: int | None = None):
    return reports.cohort_report(db, source, sim_run_id, course_id)
