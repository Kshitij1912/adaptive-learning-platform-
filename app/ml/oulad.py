"""Load OULAD CSVs (https://analytics.open.ac.uk/oulad) and build leak-free weekly training rows."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.features import FEATURES, build_features

W_MAX = 40  # OULAD presentations run ~39 weeks
KEY = ["code_module", "code_presentation", "id_student"]


@dataclass
class Enrollment:
    key: str
    clicks: np.ndarray                      # weekly clicks, index = week
    assessments: list[tuple[int, float]]    # (week, score 0-1)
    outcome: str                            # Pass | Fail | Withdrawn | Distinction


def is_dev_standin(data_dir: str | Path) -> bool:
    return (Path(data_dir) / "DEV_STANDIN.txt").exists()


def load_oulad(data_dir: str | Path) -> list[Enrollment]:
    d = Path(data_dir)
    info = pd.read_csv(d / "studentInfo.csv", usecols=KEY + ["final_result"])
    vle = pd.read_csv(d / "studentVle.csv", usecols=KEY + ["date", "sum_click"])
    sa = pd.read_csv(d / "studentAssessment.csv", usecols=["id_assessment", "id_student", "date_submitted", "score"])
    asm = pd.read_csv(d / "assessments.csv", usecols=["code_module", "code_presentation", "id_assessment"])

    vle["week"] = (vle["date"].clip(lower=0) // 7).astype(int).clip(upper=W_MAX)
    wk = (
        vle.groupby(KEY + ["week"], sort=False)["sum_click"].sum()
        .unstack("week", fill_value=0).reindex(columns=range(W_MAX + 1), fill_value=0)
    )
    clicks = {k: row for k, row in zip(wk.index, wk.to_numpy(dtype=float))}

    sa = sa.dropna(subset=["score", "date_submitted"]).merge(asm, on="id_assessment")
    sa["week"] = (sa["date_submitted"].clip(lower=0) // 7).astype(int).clip(upper=W_MAX)
    sa["frac"] = (sa["score"] / 100.0).clip(0, 1)
    assess: dict[tuple, list] = {}
    for k, w, f in zip(zip(sa["code_module"], sa["code_presentation"], sa["id_student"]), sa["week"], sa["frac"]):
        assess.setdefault(k, []).append((int(w), float(f)))

    out = []
    for m, p, s, res in zip(info["code_module"], info["code_presentation"], info["id_student"], info["final_result"]):
        k = (m, p, s)
        out.append(Enrollment(f"{m}_{p}_{s}", clicks.get(k, np.zeros(W_MAX + 1)), assess.get(k, []), str(res)))
    return out


def build_training_frame(enrolls: list[Enrollment], weeks) -> pd.DataFrame:
    rows = []
    for e in enrolls:
        for w in weeks:
            f = build_features(e.clicks, e.assessments, w)
            f["student"] = e.key
            f["outcome"] = e.outcome
            rows.append(f)
    return pd.DataFrame(rows, columns=FEATURES + ["student", "outcome"])
