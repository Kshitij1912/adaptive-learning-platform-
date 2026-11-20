"""
Learner Pattern Analyzer.
Encapsulates the explicit inference rules directly derived from the OULAD project specification:
- High engagement + good assessment scores -> Likely high performance
- High engagement + poor assessment scores -> Learner needs additional guidance
- Low engagement + declining scores -> Potentially at risk
- Good engagement + improving scores -> Positive learning trajectory
- Increasing inactivity -> Potential withdrawal risk
"""

from typing import Dict, Any, List


class PatternAnalyzer:
    @staticmethod
    def analyze_patterns(
        engagement_pct: float,
        assessment_pct: float,
        score_trend: float,
        inactivity_pct: float
    ) -> Dict[str, Any]:
        """
        Analyzes a learner's metrics at a given checkpoint.
        Returns active pattern inferences, warnings, and trajectory velocity.
        """
        inferences: List[str] = []
        status_category = "Neutral"
        urgency = "LOW"

        # Thresholds based on OULAD research distributions
        high_eng = engagement_pct >= 65.0
        low_eng = engagement_pct <= 45.0
        good_scores = assessment_pct >= 65.0
        poor_scores = assessment_pct < 50.0
        improving = score_trend > 0.05
        declining = score_trend < -0.05
        high_inactivity = inactivity_pct >= 35.0

        # Pattern Rule 1: High engagement + good assessment scores
        if high_eng and good_scores:
            inferences.append("High engagement + good assessment scores: Likely high performance")
            status_category = "High Performer"
            urgency = "LOW"

        # Pattern Rule 2: High engagement + poor assessment scores
        if high_eng and poor_scores:
            inferences.append("High engagement + poor assessment scores: Learner needs additional guidance")
            status_category = "Guidance Needed"
            urgency = "HIGH"

        # Pattern Rule 3: Low engagement + declining scores
        if low_eng and declining:
            inferences.append("Low engagement + declining scores: Potentially at risk")
            status_category = "Academic Risk"
            urgency = "CRITICAL"

        # Pattern Rule 4: Good engagement + improving scores
        if engagement_pct >= 55.0 and improving:
            inferences.append("Good engagement + improving scores: Positive learning trajectory")
            if status_category == "Neutral":
                status_category = "Accelerating"

        # Pattern Rule 5: Increasing inactivity
        if high_inactivity:
            inferences.append("Increasing inactivity: Potential withdrawal risk")
            if urgency != "CRITICAL":
                urgency = "HIGH"
            status_category = "Withdrawal Risk"

        if not inferences:
            inferences.append("Moderate engagement and steady progress: Consistent learning track")
            status_category = "Consistent"

        return {
            "status_category": status_category,
            "urgency": urgency,
            "inferences": inferences,
            "metrics": {
                "engagement_pct": engagement_pct,
                "assessment_pct": assessment_pct,
                "score_trend": round(score_trend, 3),
                "inactivity_pct": inactivity_pct,
            }
        }
