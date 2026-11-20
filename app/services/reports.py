from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.registry import get_predictor
from app.models import Checkpoint, Learner, LearnerSource, Outcome, RiskFlag
from app.schemas import ClusterSummary, CohortReport, WeeklyTrendPoint


def _zero(enum_cls) -> dict[str, int]:
    return {m.value: 0 for m in enum_cls}


def cohort_report(db: Session, source: LearnerSource | None, sim_run_id: str | None,
                  course_id: int | None) -> CohortReport:
    q = select(Learner.id)
    if source:
        q = q.where(Learner.source == source)
    if sim_run_id:
        q = q.where(Learner.sim_run_id == sim_run_id)
    if course_id:
        q = q.where(Learner.course_id == course_id)
    ids = list(db.scalars(q))

    cps = list(db.scalars(select(Checkpoint).where(Checkpoint.learner_id.in_(ids)).order_by(Checkpoint.week))) if ids else []
    latest: dict[int, Checkpoint] = {}
    by_week: dict[int, list[Checkpoint]] = defaultdict(list)
    for cp in cps:
        by_week[cp.week].append(cp)
        if cp.learner_id not in latest or cp.week >= latest[cp.learner_id].week:
            latest[cp.learner_id] = cp

    outcomes, risks = _zero(Outcome), _zero(RiskFlag)
    clusters: dict[int, list[Checkpoint]] = defaultdict(list)
    for cp in latest.values():
        outcomes[cp.predicted_outcome.value] += 1
        risks[cp.risk.value] += 1
        if cp.cluster_id is not None:
            clusters[cp.cluster_id].append(cp)

    pred = get_predictor(db)
    labels = pred.cluster_labels if pred else {}

    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 4) if xs else None

    cluster_rows = [ClusterSummary(cluster_id=cid, label=labels.get(cid), size=len(v),
                                   avg_engagement=mean(c.engagement for c in v) or 0.0,
                                   avg_assessment_score=mean(c.assessment_score for c in v))
                    for cid, v in sorted(clusters.items())]
    trend = []
    for w in sorted(by_week):
        dist = _zero(Outcome)
        for cp in by_week[w]:
            dist[cp.predicted_outcome.value] += 1
        trend.append(WeeklyTrendPoint(week=w, avg_engagement=mean(c.engagement for c in by_week[w]) or 0.0,
                                      avg_assessment_score=mean(c.assessment_score for c in by_week[w]),
                                      outcome_distribution=dist))
    return CohortReport(source=source, sim_run_id=sim_run_id, course_id=course_id, n_learners=len(ids),
                        latest_outcome_distribution=outcomes, risk_distribution=risks,
                        clusters=cluster_rows, weekly_trend=trend)
