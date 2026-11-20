"""Learner state: store activity, build features from the DB, profile, checkpoint, recommend."""
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.features import build_features
from app.ml.predict import Predictor
from app.models import (Assessment, Checkpoint, Interaction, Learner, Recommendation)
from app.schemas import ActivityBatch
from app.services.catalogue import load_catalogue
from app.services.recommender import recommend


@dataclass
class Series:
    clicks: list[float]
    assessments: list[tuple[int, float]]
    latest_week: int | None


def series_for(db: Session, learner_id: int) -> Series:
    wk = dict(db.execute(select(Interaction.week, func.sum(Interaction.clicks))
                         .where(Interaction.learner_id == learner_id).group_by(Interaction.week)).all())
    ass = [(w, min(1.0, max(0.0, s / m))) for w, s, m in db.execute(
        select(Assessment.week, Assessment.score, Assessment.max_score).where(Assessment.learner_id == learner_id))]
    weeks = list(wk) + [w for w, _ in ass]
    if not weeks:
        return Series([], [], None)
    latest = max(weeks)
    clicks = [0.0] * (latest + 1)
    for w, c in wk.items():
        clicks[w] = float(c)
    return Series(clicks, ass, latest)


def current_item_id(db: Session, learner_id: int, upto_week: int) -> int | None:
    return db.scalar(select(Interaction.content_item_id)
                     .where(Interaction.learner_id == learner_id, Interaction.week <= upto_week,
                            Interaction.content_item_id.is_not(None))
                     .order_by(Interaction.week.desc(), Interaction.id.desc()).limit(1))


def store_activity(db: Session, learner: Learner, batch: ActivityBatch) -> None:
    for i in batch.interactions:
        db.add(Interaction(learner_id=learner.id, week=batch.week, **i.model_dump()))
    for a in batch.assessments:
        db.add(Assessment(learner_id=learner.id, week=batch.week, **a.model_dump()))
    db.commit()


def profile_learner(db: Session, learner: Learner, week: int, predictor: Predictor) -> tuple[Checkpoint, dict]:
    s = series_for(db, learner.id)
    feats = build_features(s.clicks, s.assessments, week)
    p = predictor.predict_batch([feats])[0]
    cp = db.scalar(select(Checkpoint).where(Checkpoint.learner_id == learner.id, Checkpoint.week == week,
                                            Checkpoint.model_version_id == predictor.classifier_version_id))
    if cp is None:
        cp = Checkpoint(learner_id=learner.id, week=week, model_version_id=predictor.classifier_version_id)
        db.add(cp)
    else:
        cp.recommendations.clear()  # data changed: old recommendations no longer apply
    cp.engagement = feats["engagement"]
    cp.assessment_score = feats["avg_score"] if feats["n_assessments"] else None
    cp.predicted_outcome, cp.outcome_probs = p.outcome, p.probs
    cp.cluster_id, cp.risk = p.cluster_id, p.risk
    db.commit()
    return cp, feats


def ensure_recommendations(db: Session, learner: Learner, cp: Checkpoint) -> list[Recommendation]:
    if cp.recommendations:
        return list(cp.recommendations)
    s = series_for(db, learner.id)
    feats = build_features(s.clicks, s.assessments, cp.week)
    last_a = max((w for w, _ in s.assessments if w <= cp.week), default=None)
    since = cp.week - last_a if last_a is not None else cp.week + 1
    specs = recommend(load_catalogue(db, learner.course_id), learner.preferred_method, feats, cp.risk,
                      current_item_id(db, learner.id, cp.week), since)
    for sp in specs:
        cp.recommendations.append(Recommendation(
            action=sp.action, content_item_id=sp.item.id if sp.item else None,
            rule_id=sp.rule_id, rationale=sp.rationale))
    db.commit()
    return list(cp.recommendations)


def run_step(db: Session, learner: Learner, week: int, predictor: Predictor) -> tuple[Checkpoint, list[Recommendation]]:
    cp, _ = profile_learner(db, learner, week, predictor)
    return cp, ensure_recommendations(db, learner, cp)
