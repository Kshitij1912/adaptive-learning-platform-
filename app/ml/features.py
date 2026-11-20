"""Single source of truth for feature construction.

The SAME function builds features for OULAD training rows, synthetic learners and live API
requests, so train/serve parity is structural. Demographics are deliberately excluded:
the models see behaviour only (engagement + assessment signals).
"""
from collections.abc import Iterable, Sequence

import numpy as np

CLICK_REF = 50.0  # weekly clicks treated as "fully engaged" when normalising engagement to 0-1

FEATURES = [
    "week", "clicks_cum", "clicks_week", "clicks_trend", "active_ratio", "inactivity_streak",
    "engagement", "n_assessments", "avg_score", "last_score", "score_trend", "score_missing",
]
CLUSTER_FEATURES = ["engagement", "avg_score", "score_trend", "active_ratio", "inactivity_streak"]


def build_features(
    clicks: Sequence[float], assessments: Iterable[tuple[int, float]], week: int
) -> dict[str, float]:
    """clicks[w] = total clicks in week w. assessments = (week, score in 0-1).
    Only data from weeks <= `week` is used (no look-ahead)."""
    week = max(int(week), 0)
    c = np.zeros(week + 1)
    n = min(len(clicks), week + 1)
    if n:
        c[:n] = np.asarray(clicks[:n], dtype=float)

    recent = float(c[-2:].mean())
    prior = float(c[-4:-2].mean()) if week >= 2 else recent
    trend = float(np.clip((recent - prior) / (prior + 1.0), -3.0, 3.0))
    active_ratio = float((c > 0).mean())
    nz = np.flatnonzero(c)
    streak = float(week - nz[-1]) if nz.size else float(week + 1)
    engagement = float(np.clip(0.5 * active_ratio + 0.5 * min(1.0, c.mean() / CLICK_REF), 0.0, 1.0))

    scores = [s for _, s in sorted((int(w), float(s)) for w, s in assessments if int(w) <= week)]
    k = len(scores)
    if k:
        avg, last = float(np.mean(scores)), float(scores[-1])
        if k >= 2:
            x = np.arange(k, dtype=float)
            y = np.asarray(scores)
            slope = float(((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum())
            score_trend = float(np.clip(slope, -0.5, 0.5))
        else:
            score_trend = 0.0
    else:
        avg = last = score_trend = 0.0

    return {
        "week": float(week), "clicks_cum": float(c.sum()), "clicks_week": float(c[-1]),
        "clicks_trend": trend, "active_ratio": active_ratio, "inactivity_streak": streak,
        "engagement": engagement, "n_assessments": float(k), "avg_score": avg,
        "last_score": last, "score_trend": score_trend, "score_missing": 0.0 if k else 1.0,
    }
