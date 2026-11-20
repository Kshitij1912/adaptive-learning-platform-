"""Synthetic learners + weekly closed-loop simulation (activity -> profile -> recommend -> response).

SIMULATION ASSUMPTIONS (not measured from real data): the archetype parameters below and how
learners respond to recommendations. Change them in one place (this file) and re-run.
Predictions here come from models trained on OULAD only; simulated learners never train anything.
"""
from dataclasses import dataclass, field

import numpy as np

from app.db import SessionLocal
from app.ml.features import build_features
from app.ml.registry import get_predictor
from app.models import (Assessment, Checkpoint, ContentType, Interaction, JobStatus, Learner, LearnerSource,
                        Outcome, Recommendation, RecommendationAction as A, RecommendationStatus, SimulationRun)
from app.services.catalogue import Catalogue, load_catalogue
from app.services.recommender import recommend

CLICK_SCALE = 100.0
ARCHETYPES = {  # knowledge k, learning speed s, engagement e, weekly engagement decay
    "advanced": dict(k=0.70, s=0.80, e=0.80, decay=1.00),
    "average": dict(k=0.50, s=0.50, e=0.55, decay=0.99),
    "struggling": dict(k=0.30, s=0.30, e=0.40, decay=0.95),
}
EDUCATION = ["No formal qualifications", "A-level", "Undergraduate", "Postgraduate"]
METHODS = [ContentType.VIDEO, ContentType.READING, ContentType.EXERCISE, ContentType.QUIZ]
# (engagement boost, knowledge boost scale) when a learner follows a recommendation
BOOSTS = {A.REMEDIATE: (0.10, 0.04), A.EXTRA_PRACTICE: (0.02, 0.05), A.ADVANCE: (0.04, 0.03),
          A.SKIP_INTRO: (0.04, 0.03), A.CONTINUE: (0.01, 0.0), A.ASSESS: (0.0, 0.0)}
FORMAT_MATCH_BONUS = 1.25


def _clip(x, lo=0.02, hi=1.0):
    return float(min(hi, max(lo, x)))


@dataclass
class _State:
    learner: Learner
    k: float
    s: float
    e: float
    decay: float
    pref: ContentType
    pos: int = 0
    cur_item_id: int | None = None
    clicks: list[float] = field(default_factory=lambda: [0.0])
    assess: list[tuple[int, float]] = field(default_factory=list)


def run_simulation(run_id: str) -> None:
    """Background-job entry point (own DB session)."""
    with SessionLocal() as db:
        run = db.get(SimulationRun, run_id)
        run.status = JobStatus.RUNNING
        db.commit()
        try:
            _simulate(db, run)
            run = db.get(SimulationRun, run_id)
            run.status = JobStatus.DONE
        except Exception as exc:  # noqa: BLE001 - job boundary: record failure on the run
            db.rollback()
            run = db.get(SimulationRun, run_id)
            run.status, run.error = JobStatus.FAILED, f"{type(exc).__name__}: {exc}"[:500]
        db.commit()


def _simulate(db, run: SimulationRun) -> None:
    rng = np.random.default_rng(run.seed)
    cat = load_catalogue(db, run.course_id)
    predictor = get_predictor(db)
    if not cat:
        raise RuntimeError("course has no content items")
    if predictor is None:
        raise RuntimeError("no active model")

    mix = run.archetype_mix or {k: 1 / 3 for k in ARCHETYPES}
    names = list(mix)
    kinds = rng.choice(names, size=run.n_learners, p=[mix[n] for n in names])

    states: list[_State] = []
    for kind in kinds:
        a = ARCHETYPES[kind]
        k, s, e = _clip(rng.normal(a["k"], 0.08)), _clip(rng.normal(a["s"], 0.08)), _clip(rng.normal(a["e"], 0.07))
        pref = METHODS[int(rng.integers(len(METHODS)))]
        learner = Learner(
            source=LearnerSource.SYNTHETIC, course_id=run.course_id, age=int(np.clip(rng.normal(26, 8), 18, 60)),
            education=EDUCATION[int(rng.integers(len(EDUCATION)))], initial_knowledge=k, learning_speed=s,
            engagement_baseline=e, preferred_method=pref, archetype=str(kind), sim_run_id=run.id)
        states.append(_State(learner, k, s, e, a["decay"], pref))
    db.add_all([st.learner for st in states])
    db.flush()
    run.learners_created = len(states)

    for week in range(1, run.weeks + 1):
        _generate_activity(db, rng, cat, states, week)
        feats = [build_features(st.clicks, st.assess, week) for st in states]
        preds = predictor.predict_batch(feats)
        records = []
        for st, f, p in zip(states, feats, preds):
            last_a = max((w for w, _ in st.assess), default=None)
            since = week - last_a if last_a is not None else week + 1
            specs = recommend(cat, st.pref, f, p.risk, st.cur_item_id, since)
            recs = [Recommendation(action=sp.action, content_item_id=sp.item.id if sp.item else None,
                                   rule_id=sp.rule_id, rationale=sp.rationale) for sp in specs]
            cp = Checkpoint(
                learner_id=st.learner.id, week=week, engagement=f["engagement"],
                assessment_score=f["avg_score"] if f["n_assessments"] else None, predicted_outcome=p.outcome,
                outcome_probs=p.probs, cluster_id=p.cluster_id, risk=p.risk,
                model_version_id=predictor.classifier_version_id, recommendations=recs)
            db.add(cp)
            records.append((st, specs, recs))
        for st, specs, recs in records:
            _respond(rng, cat, st, specs, recs, run.recommendation_effect)
        db.flush()
        run.learners_created = len(states)
        db.commit()

    for st in states:  # simulated ground truth: a rule of THIS simulator, not real data
        st.learner.actual_outcome = (Outcome.WITHDRAWN if st.e < 0.15 else Outcome.DISTINCTION if st.k >= 0.80
                                     else Outcome.PASS if st.k >= 0.50 else Outcome.FAIL)
    db.commit()


def _generate_activity(db, rng, cat: Catalogue, states: list[_State], week: int) -> None:
    rows = []
    for st in states:
        item = cat.items[st.pos]
        clicks = 0.0
        if rng.random() < 0.15 + 0.85 * st.e:
            clicks = float(max(1, rng.poisson(st.e * CLICK_SCALE)))
            st.cur_item_id = item.id
            rows.append(Interaction(learner_id=st.learner.id, content_item_id=item.id, week=week,
                                    day=week * 7 + int(rng.integers(0, 7)), activity_type=item.content_type.value,
                                    clicks=int(clicks), duration_min=round(clicks * 0.4, 1)))
        st.clicks.append(clicks)
        if week % 2 == 1 and rng.random() < 0.45 + 0.5 * st.e:
            score = _clip(st.k + rng.normal(0, 0.07), 0.0, 1.0)
            st.assess.append((week, score))
            rows.append(Assessment(learner_id=st.learner.id, topic_id=item.topic_id, week=week,
                                   assessment_type="quiz", score=round(score * 100, 1), max_score=100.0))
    db.add_all(rows)


def _respond(rng, cat: Catalogue, st: _State, specs, recs, effect: float) -> None:
    """Apply one week of drift, then (maybe) the learner's response to the primary recommendation."""
    st.k = _clip(st.k + 0.045 * st.s * st.e, 0.0, 1.0)
    st.e = _clip(st.e * st.decay)
    followed = False
    if specs and specs[0].item and effect > 0:
        followed = bool(rng.random() < effect * (0.4 + 0.6 * st.e))
    if followed:
        sp = specs[0]
        e_b, k_b = BOOSTS[sp.action]
        mult = FORMAT_MATCH_BONUS if sp.item.content_type == st.pref else 1.0
        st.e = _clip(st.e + e_b * mult * effect)
        st.k = _clip(st.k + k_b * (0.5 + st.s) * mult * effect, 0.0, 1.0)
        st.pos = cat.index_of(sp.item.id)
    else:
        st.pos = min(st.pos + 1, len(cat.items) - 1)
    if recs:
        recs[0].status = RecommendationStatus.ACCEPTED if followed else RecommendationStatus.SKIPPED
