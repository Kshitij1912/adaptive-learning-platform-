"""
FastAPI Backend Application for the Adaptive Learning Platform.
Provides modular REST endpoints connecting:
- Layer 1: Intelligence (OULAD analytics, outcome prediction, clustering, pattern analysis)
- Layer 2: Simulation (Synthetic learners population, step-by-step & full-journey simulation)
- Layer 3: Application (Adaptive curriculum pathways, user feedback loops, quiz scoring)
"""

import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..intelligence.oulad_loader import OULADLoader
from ..intelligence.classifier import OutcomeClassifier
from ..intelligence.clusterer import LearnerClusterer
from ..intelligence.pattern_analyzer import PatternAnalyzer
from ..simulation.learner_generator import SyntheticLearner, LearnerGenerator
from ..simulation.interaction_simulator import InteractionSimulator
from ..adaptive.course_catalog import CourseCatalog
from ..adaptive.recommendation_engine import RecommendationEngine
from ..adaptive.journey_tracker import JourneyTracker
from app.api import router as backend_v1_router
from app.db import SessionLocal, engine
from app.models import Base
from app.seed_data import ensure_seed_course

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

app = FastAPI(
    title="OULAD Adaptive Learning Platform API",
    description="ML-powered adaptive learning system with 3 distinct architectural layers.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(backend_v1_router, prefix="/api/v1")


@app.on_event("startup")
def initialize_backend_database():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_seed_course(db)

# ----------------- Initialize Shared Application State -----------------
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
WEB_DIR = os.path.join(PROJECT_ROOT, "src", "web")

catalog = CourseCatalog(os.path.join(DATA_DIR, "courses.json"))
rec_engine = RecommendationEngine(catalog)
tracker = JourneyTracker()

classifier = OutcomeClassifier()
clusterer = LearnerClusterer()

# Load models if weights exist, otherwise train them
classifier_file = os.path.join(DATA_DIR, "classifier_model.json")
clusterer_file = os.path.join(DATA_DIR, "clusterer_model.json")
oulad_file = os.path.join(DATA_DIR, "oulad_historical.csv")

oulad_loader = OULADLoader(oulad_file)

if os.path.exists(classifier_file) and os.path.exists(clusterer_file):
    classifier.load(classifier_file)
    clusterer.load(clusterer_file)
else:
    X, y = oulad_loader.extract_features()
    classifier.fit(X, y)
    clusterer.fit(X)
    classifier.save(classifier_file)
    clusterer.save(clusterer_file)

simulator = InteractionSimulator(classifier=classifier, clusterer=clusterer, pattern_analyzer=PatternAnalyzer)

# Initialize canonical learners A, B, C into tracker
canonical_dict = LearnerGenerator.create_canonical_learners()
for l in canonical_dict.values():
    tracker.register_learner(l)
    # Pre-simulate initial week 1 baseline checkpoint
    step1 = simulator.simulate_checkpoint(l, week=1, adaptation_active=True)
    tracker.record_checkpoint(l.learner_id, step1)
    recs = rec_engine.generate_recommendations(l.to_dict(), step1)
    tracker.set_recommendations(l.learner_id, recs)


# ----------------- Request / Response Models -----------------
class CreateLearnerRequest(BaseModel):
    name: str = Field(..., example="John Doe")
    archetype: str = Field("Average", example="Struggling")
    age: int = Field(22, example=22)
    education: str = Field("Undergraduate", example="Undergraduate")
    initial_knowledge: float = Field(50.0, example=50.0)
    learning_speed: float = Field(0.65, example=0.65)
    engagement_baseline: float = Field(0.60, example=0.60)
    preferred_learning_method: str = Field("Video", example="Practice")


class FeedbackRequest(BaseModel):
    feedback_type: str = Field(..., example="Pacing")
    notes: str = Field("", example="Found variables section clear, ready for exercises")
    applied: bool = Field(True, example=True)


class QuizSubmissionRequest(BaseModel):
    topic_id: str = Field(..., example="T2")
    score: float = Field(..., example=85.0)


# ----------------- API Endpoints -----------------
@app.get("/api/health")
def get_health():
    return {
        "status": "healthy",
        "service": "Adaptive Learning Platform",
        "models_loaded": {
            "classifier": classifier.is_trained,
            "clusterer": clusterer.is_fitted
        },
        "registered_learners_count": len(tracker.learners)
    }


@app.get("/api/stats")
def get_historical_stats():
    return oulad_loader.compute_summary_stats()


@app.get("/api/learners")
def list_learners():
    result = []
    for lid, learner in tracker.learners.items():
        latest = tracker.get_latest_checkpoint(lid)
        result.append({
            **learner.to_dict(),
            "latest_checkpoint": latest
        })
    return result


@app.post("/api/learners")
def create_learner(req: CreateLearnerRequest):
    new_learner = SyntheticLearner(
        learner_id=f"SYN-{os.urandom(3).hex().upper()}",
        name=req.name,
        archetype=req.archetype,
        age=req.age,
        education=req.education,
        initial_knowledge=req.initial_knowledge,
        learning_speed=req.learning_speed,
        engagement_baseline=req.engagement_baseline,
        preferred_learning_method=req.preferred_learning_method,
    )
    tracker.register_learner(new_learner)
    step1 = simulator.simulate_checkpoint(new_learner, week=1, adaptation_active=True)
    tracker.record_checkpoint(new_learner.learner_id, step1)
    recs = rec_engine.generate_recommendations(new_learner.to_dict(), step1)
    tracker.set_recommendations(new_learner.learner_id, recs)

    return {
        "message": "Learner successfully created",
        "learner": new_learner.to_dict(),
        "initial_checkpoint": step1,
        "recommendations": recs
    }


@app.get("/api/learners/{learner_id}")
def get_learner(learner_id: str):
    if learner_id not in tracker.learners:
        raise HTTPException(status_code=404, detail="Learner not found")
    learner = tracker.learners[learner_id]
    latest = tracker.get_latest_checkpoint(learner_id)
    recs = tracker.get_recommendations(learner_id)
    return {
        "learner": learner.to_dict(),
        "latest_checkpoint": latest,
        "recommendations": recs,
    }


@app.get("/api/learners/{learner_id}/journey")
def get_learner_journey(learner_id: str):
    if learner_id not in tracker.learners:
        raise HTTPException(status_code=404, detail="Learner not found")
    return {
        "learner_id": learner_id,
        "timeline": tracker.get_timeline(learner_id)
    }


@app.post("/api/learners/{learner_id}/simulate-step")
def simulate_step(learner_id: str, adaptation_active: bool = True):
    if learner_id not in tracker.learners:
        raise HTTPException(status_code=404, detail="Learner not found")

    learner = tracker.learners[learner_id]
    timeline = tracker.get_timeline(learner_id)
    current_week = timeline[-1]["week"] if timeline else 0

    next_week = current_week + 2 if current_week > 0 else 1
    if next_week > 10:
        return {"message": "Learner has completed maximum 10-week trajectory", "timeline": timeline}

    step = simulator.simulate_checkpoint(learner, week=next_week, adaptation_active=adaptation_active)
    tracker.record_checkpoint(learner_id, step)

    # Recalculate adaptive recommendations
    recs = rec_engine.generate_recommendations(learner.to_dict(), step)
    tracker.set_recommendations(learner_id, recs)

    return {
        "new_checkpoint": step,
        "recommendations": recs,
        "total_checkpoints": len(tracker.get_timeline(learner_id))
    }


@app.post("/api/learners/{learner_id}/simulate-all")
def simulate_all(learner_id: str, adaptation_active: bool = True):
    if learner_id not in tracker.learners:
        raise HTTPException(status_code=404, detail="Learner not found")

    learner = tracker.learners[learner_id]
    checkpoints = [1, 3, 5, 8]
    # Reset history
    learner.assessment_history = []
    tracker.timelines[learner_id] = []

    journey = simulator.simulate_full_journey(learner, checkpoints=checkpoints, adaptation_active=adaptation_active)
    for step in journey:
        tracker.record_checkpoint(learner_id, step)

    recs = rec_engine.generate_recommendations(learner.to_dict(), journey[-1])
    tracker.set_recommendations(learner_id, recs)

    return {
        "message": f"Successfully simulated full journey across weeks {checkpoints}",
        "journey": journey,
        "final_recommendations": recs
    }


@app.get("/api/learners/{learner_id}/recommendations")
def get_learner_recommendations(learner_id: str):
    if learner_id not in tracker.learners:
        raise HTTPException(status_code=404, detail="Learner not found")
    recs = tracker.get_recommendations(learner_id)
    if not recs:
        learner = tracker.learners[learner_id]
        latest = tracker.get_latest_checkpoint(learner_id) or {}
        recs = rec_engine.generate_recommendations(learner.to_dict(), latest)
        tracker.set_recommendations(learner_id, recs)
    return recs


@app.post("/api/learners/{learner_id}/feedback")
def submit_feedback(learner_id: str, req: FeedbackRequest):
    if learner_id not in tracker.learners:
        raise HTTPException(status_code=404, detail="Learner not found")
    result = tracker.record_user_feedback(
        learner_id=learner_id,
        feedback_type=req.feedback_type,
        notes=req.notes,
        applied=req.applied
    )
    return {"status": "Feedback recorded", "entry": result}


@app.post("/api/learners/{learner_id}/submit-quiz")
def submit_quiz(learner_id: str, req: QuizSubmissionRequest):
    if learner_id not in tracker.learners:
        raise HTTPException(status_code=404, detail="Learner not found")
    res = tracker.record_quiz_submission(
        learner_id=learner_id,
        topic_id=req.topic_id,
        score=req.score
    )
    # Refresh recommendations based on new score
    learner = tracker.learners[learner_id]
    latest = tracker.get_latest_checkpoint(learner_id) or {"assessment_score": req.score, "engagement_pct": 70.0}
    latest["assessment_score"] = req.score
    recs = rec_engine.generate_recommendations(learner.to_dict(), latest)
    tracker.set_recommendations(learner_id, recs)
    return {"quiz_result": res, "updated_recommendations": recs}


@app.get("/api/courses")
def get_courses():
    return catalog.list_courses()


@app.get("/api/courses/{course_id}")
def get_course_detail(course_id: str):
    course = catalog.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


# Mount web directory if present
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="static")
