"""Rule-based recommender (v1). Pure function: profile + catalogue position -> actions.

Rules are evaluated in priority order; the first group that fires wins. Every output carries
a rule_id so a recommendation is always traceable to the rule that produced it.
"""
from dataclasses import dataclass

from app.models import ContentType, Difficulty, RecommendationAction as A, RiskFlag
from app.services.catalogue import Catalogue, Item

ENG_HIGH = 0.60
SCORE_LOW = 0.45
SCORE_HIGH = 0.75
INACTIVE_WEEKS = 2
ASSESS_EVERY = 3


@dataclass(frozen=True)
class Spec:
    action: A
    item: Item | None
    rule_id: str
    rationale: str


def recommend(cat: Catalogue | None, pref: ContentType | None, feats: dict, risk: RiskFlag,
              current_item_id: int | None, weeks_since_assessment: float) -> list[Spec]:
    if not cat:
        return []
    idx = cat.index_of(current_item_id)
    eng, score = feats["engagement"], feats["avg_score"]
    n_a, trend, streak = int(feats["n_assessments"]), feats["score_trend"], feats["inactivity_streak"]

    # R4: disengaging -> restart with something easy in the preferred format
    if streak >= INACTIVE_WEEKS:
        return [Spec(A.REMEDIATE, cat.foundational(idx, pref), "R4_REENGAGE",
                     f"No activity for {int(streak)} weeks; restart with an easy item in your preferred format.")]

    # R3: struggling, or engaged but scoring poorly
    engaged_poor = eng >= ENG_HIGH and n_a >= 1 and score < 0.5
    struggling = (risk == RiskFlag.HIGH or (n_a >= 1 and score < SCORE_LOW)
                  or (n_a >= 2 and trend < -0.05 and score < 0.6))
    if engaged_poor or struggling:
        specs = [Spec(A.REMEDIATE, cat.foundational(idx, pref),
                      "R3B_ENGAGED_POOR" if engaged_poor else "R3A_STRUGGLING",
                      "High engagement but low scores: extra guidance on foundations." if engaged_poor
                      else "Low scores or high risk: revisit foundational concepts with simpler content.")]
        p = cat.practice(idx)
        if p:
            specs.append(Spec(A.EXTRA_PRACTICE, p, "R3_PRACTICE", "Additional easy practice to consolidate."))
        return specs

    # R1: advanced -> skip revision / move to harder material
    if risk == RiskFlag.LOW and eng >= 0.65 and n_a >= 1 and score >= SCORE_HIGH:
        cur = cat.items[max(idx, 0)]
        if cur.difficulty == Difficulty.EASY:
            tgt = cat.first_at_least(idx, Difficulty.MEDIUM)
            if tgt:
                return [Spec(A.SKIP_INTRO, tgt, "R1A_SKIP_INTRO", "Strong results: skip introductory revision.")]
        tgt = cat.harder(idx)
        return [Spec(A.ADVANCE, tgt, "R1B_ADVANCE",
                     "Strong results: move to more challenging material." if tgt else "Course content complete.")]

    # R2: average -> continue plan, add practice, assess periodically
    specs = [Spec(A.CONTINUE, cat.next_item(idx), "R2_CONTINUE",
                  "Continue the planned sequence." if cat.next_item(idx) else "Reached the end of the planned sequence.")]
    p = cat.practice(idx)
    if p:
        specs.append(Spec(A.EXTRA_PRACTICE, p, "R2_PRACTICE", "Additional practice to firm up understanding."))
    q = cat.quiz(idx)
    if q and weeks_since_assessment >= ASSESS_EVERY:
        specs.append(Spec(A.ASSESS, q, "R2_ASSESS", f"{int(weeks_since_assessment)} weeks since your last assessment."))
    return specs
