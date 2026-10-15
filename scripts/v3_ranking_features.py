#!/usr/bin/env python3
"""Extract leakage-resistant descriptive features for v3 candidate ranking."""
from datetime import date

from scripts.generate_v3_candidates import generate_candidates


def _class_group(label):
    text = str(label)
    if "1勝クラス" in text:
        return "1win"
    if "2勝クラス" in text:
        return "2win"
    if "3勝クラス" in text:
        return "3win"
    if "未勝利" in text:
        return "maiden"
    if text in {"G1", "GI"}:
        return "G1"
    if text in {"G2", "GII"}:
        return "G2"
    if text in {"G3", "GIII"}:
        return "G3"
    if text in {"L", "Listed"}:
        return "L"
    return text


def build_ranking_features(race, as_of):
    generated = generate_candidates(race, as_of)
    if generated["status"] != "PASS":
        return {"race": race.get("race"), "status": "DATA_HOLD", "rows": []}

    feature_map = {row["number"]: row for row in generated["horse_features"]}
    race_day = date.fromisoformat(race["date"])
    rows = []

    for horse in race["horses"]:
        meta = feature_map[horse["number"]]
        if not meta["candidate"]:
            continue

        runs = horse.get("recent_runs", [])
        similar = [
            run for run in runs
            if run.get("surface") == race["surface"]
            and abs(run.get("distance_m", 10**9) - race["distance_m"]) <= 200
        ]
        same_class = [
            run for run in runs
            if _class_group(run.get("class")) == _class_group(race.get("class"))
        ]
        latest = date.fromisoformat(horse["source_latest_run_date"])

        numeric_similar_margins = [
            run.get("beaten_margin_s") for run in similar
            if isinstance(run.get("beaten_margin_s"), (int, float))
        ]
        numeric_class_margins = [
            run.get("beaten_margin_s") for run in same_class
            if isinstance(run.get("beaten_margin_s"), (int, float))
        ]

        rows.append({
            "number": horse["number"],
            "name": horse.get("name"),
            "market_rank": meta.get("market_rank"),
            "career_starts": horse.get("career_starts"),
            "days_since_latest_run": (race_day - latest).days,
            "recent_wins": sum(run.get("finish") == 1 for run in runs),
            "recent_top3": sum(
                isinstance(run.get("finish"), int) and run["finish"] <= 3
                for run in runs
            ),
            "best_similar_finish": min(
                (run.get("finish") for run in similar), default=None
            ),
            "best_similar_margin_s": (
                min(numeric_similar_margins) if numeric_similar_margins else None
            ),
            "best_same_class_finish": min(
                (run.get("finish") for run in same_class), default=None
            ),
            "best_same_class_margin_s": (
                min(numeric_class_margins) if numeric_class_margins else None
            ),
            "latest_surface_match": (
                bool(runs) and runs[0].get("surface") == race["surface"]
            ),
            "latest_distance_delta_m": (
                abs(runs[0].get("distance_m") - race["distance_m"])
                if runs else None
            ),
            "candidate_signal_count": len(meta.get("positive_signals", [])),
            "candidate_signals": meta.get("positive_signals", []),
            "uncertainty_flag_count": len(meta.get("uncertainty_flags", [])),
            "uncertainty_flags": meta.get("uncertainty_flags", []),
        })

    rows.sort(key=lambda row: (
        row["market_rank"] if row["market_rank"] is not None else 10**9,
        row["number"],
    ))

    return {
        "race": race.get("race"),
        "status": "PASS",
        "rows": rows,
        "ranking_produced": False,
        "target_fields_used": False,
    }
