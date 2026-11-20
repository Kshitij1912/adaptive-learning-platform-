"""
OULAD Data Preprocessing and Feature Engineering Module.
Extracts behavioral, engagement, and assessment metrics from historical OULAD records.
Emphasizes the core PDF insight: clicks != learning; engagement trajectory and assessment improvement matter.
"""

import csv
from typing import List, Dict, Any, Tuple
import numpy as np


class OULADLoader:
    EDUCATION_MAP = {
        "No Formal quals": 0,
        "Lower Than A Level": 1,
        "A Level or Equivalent": 2,
        "HE Qualification": 3,
        "Post Graduate Qualification": 4,
    }

    RESULT_MAP = {
        "Withdrawn": 0,
        "Fail": 1,
        "Pass": 2,
        "Distinction": 3,
    }
    INV_RESULT_MAP = {v: k for k, v in RESULT_MAP.items()}

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.raw_data: List[Dict[str, Any]] = []
        self.feature_names = [
            "norm_clicks",
            "avg_assessment",
            "score_trend",
            "inactivity_rate",
            "education_level",
            "studied_credits",
            "prev_attempts",
            "engagement_index",
        ]

    def load(self) -> List[Dict[str, Any]]:
        self.raw_data = []
        with open(self.filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.raw_data.append({
                    "id_student": int(row["id_student"]),
                    "code_module": row["code_module"],
                    "gender": row["gender"],
                    "region": row["region"],
                    "highest_education": row["highest_education"],
                    "age_band": row["age_band"],
                    "studied_credits": float(row["studied_credits"]),
                    "num_of_prev_attempts": int(row["num_of_prev_attempts"]),
                    "total_clicks": float(row["total_clicks"]),
                    "avg_assessment_score": float(row["avg_assessment_score"]),
                    "score_trend": float(row["score_trend"]),
                    "inactivity_rate": float(row["inactivity_rate"]),
                    "final_result": row["final_result"],
                })
        return self.raw_data

    def extract_features(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transforms raw records into feature matrix X and target labels y.
        Calculates normalized engagement index that dampens raw clicks and rewards consistency.
        """
        if not self.raw_data:
            self.load()

        X_list = []
        y_list = []

        # Find max clicks for normalization
        max_clicks = max(r["total_clicks"] for r in self.raw_data) or 1.0

        for r in self.raw_data:
            norm_clicks = min(1.0, r["total_clicks"] / max_clicks)
            norm_assessment = r["avg_assessment_score"] / 100.0
            norm_credits = min(1.0, r["studied_credits"] / 240.0)
            edu_level = self.EDUCATION_MAP.get(r["highest_education"], 1) / 4.0
            prev_att = min(1.0, r["num_of_prev_attempts"] / 3.0)

            # Engagement Index: Blend of active interactions and low inactivity
            # Guard against treating pure clicks as learning (PDF Section 2)
            engagement_index = (0.5 * norm_clicks) + (0.5 * (1.0 - r["inactivity_rate"]))

            features = [
                norm_clicks,
                norm_assessment,
                r["score_trend"],
                r["inactivity_rate"],
                edu_level,
                norm_credits,
                prev_att,
                engagement_index,
            ]
            X_list.append(features)
            y_list.append(self.RESULT_MAP.get(r["final_result"], 1))

        return np.array(X_list, dtype=np.float64), np.array(y_list, dtype=np.int64)

    def compute_summary_stats(self) -> Dict[str, Any]:
        if not self.raw_data:
            self.load()

        total = len(self.raw_data)
        outcomes = {}
        for r in self.raw_data:
            res = r["final_result"]
            outcomes[res] = outcomes.get(res, 0) + 1

        avg_clicks = float(np.mean([r["total_clicks"] for r in self.raw_data]))
        avg_score = float(np.mean([r["avg_assessment_score"] for r in self.raw_data]))

        return {
            "total_students": total,
            "outcome_distribution": {k: round(v / total * 100, 1) for k, v in outcomes.items()},
            "avg_clicks": round(avg_clicks, 1),
            "avg_assessment_score": round(avg_score, 1),
        }
