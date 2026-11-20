"""FastAPI route contracts. Bodies are stubs: wire services/ and a DB session in."""
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query, status

from models import LearnerSource
from schemas import (
    ActivityBatch, AdaptiveStepResponse, CohortReport, CourseCreate, CourseRead,
    ErrorResponse, JourneyResponse, LearnerCreate, LearnerRead, ModelVersionRead,
    Page, ProfileRequest, ProfileResponse, RecommendationRead,
    RecommendationStatusUpdate, RecommendResponse, SimulateAccepted,
    SimulateRequest, SimulateStatus,
)

NF = {404: {"model": ErrorResponse, "description": "Not found"}}
LearnerId = Annotated[int, Path(ge=1)]


def _todo():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "not implemented")


router = APIRouter()

# ------------------------------------------------------------- courses
@router.post("/courses", response_model=CourseRead, status_code=201, tags=["courses"],
             responses={409: {"model": ErrorResponse, "description": "Course code exists"}})
def create_course(body: CourseCreate):
    _todo()


@router.get("/courses", response_model=Page[CourseRead], tags=["courses"])
def list_courses(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    _todo()


@router.get("/courses/{course_id}", response_model=CourseRead, tags=["courses"], responses=NF)
def get_course(course_id: Annotated[int, Path(ge=1)]):
    _todo()


# ------------------------------------------------------------- learners
@router.post("/learners", response_model=LearnerRead, status_code=201, tags=["learners"],
             responses={409: {"model": ErrorResponse, "description": "(source, external_id) exists"}})
def create_learner(body: LearnerCreate):
    _todo()


@router.get("/learners", response_model=Page[LearnerRead], tags=["learners"])
def list_learners(
    source: LearnerSource | None = None,
    sim_run_id: str | None = None,
    course_id: int | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    _todo()


@router.get("/learners/{learner_id}", response_model=LearnerRead, tags=["learners"], responses=NF)
def get_learner(learner_id: LearnerId):
    _todo()


@router.post("/learners/{learner_id}/interactions", response_model=AdaptiveStepResponse,
             status_code=201, tags=["adaptive loop"], responses=NF)
def post_activity(learner_id: LearnerId, body: ActivityBatch):
    """Store activity -> recompute weekly features -> profile -> checkpoint -> recommend."""
    _todo()


# ------------------------------------------------------------- simulation
@router.post("/simulate", response_model=SimulateAccepted, status_code=202, tags=["simulation"],
             responses={404: {"model": ErrorResponse, "description": "Course not found"}})
def start_simulation(body: SimulateRequest):
    _todo()


@router.get("/simulate/{sim_run_id}", response_model=SimulateStatus, tags=["simulation"], responses=NF)
def simulation_status(sim_run_id: str):
    _todo()


# ------------------------------------------------------------- profile / recommend / journey
@router.post("/profile/{learner_id}", response_model=ProfileResponse, tags=["adaptive loop"],
             responses={**NF, 409: {"model": ErrorResponse, "description": "No active model"}})
def profile_learner(learner_id: LearnerId, body: ProfileRequest | None = None):
    _todo()


@router.get("/recommend/{learner_id}", response_model=RecommendResponse, tags=["adaptive loop"],
            responses={**NF, 409: {"model": ErrorResponse, "description": "No checkpoint yet; call /profile first"}})
def get_recommendations(learner_id: LearnerId, week: int | None = Query(None, ge=0, le=60)):
    _todo()


@router.patch("/recommendations/{recommendation_id}", response_model=RecommendationRead,
              tags=["adaptive loop"], responses=NF)
def update_recommendation_status(recommendation_id: Annotated[int, Path(ge=1)],
                                 body: RecommendationStatusUpdate):
    _todo()


@router.get("/journey/{learner_id}", response_model=JourneyResponse, tags=["adaptive loop"], responses=NF)
def get_journey(learner_id: LearnerId):
    _todo()


# ------------------------------------------------------------- reports / models
@router.get("/reports/cohort", response_model=CohortReport, tags=["reports"])
def cohort_report(source: LearnerSource | None = None, sim_run_id: str | None = None,
                  course_id: int | None = None):
    _todo()


@router.get("/models", response_model=list[ModelVersionRead], tags=["models"])
def list_models(active_only: bool = False):
    _todo()


app = FastAPI(title="Adaptive Learning Platform API", version="0.1.0")
app.include_router(router, prefix="/api/v1")
