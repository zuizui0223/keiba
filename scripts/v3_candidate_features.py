#!/usr/bin/env python3
"""Build a broad v3 candidate set without converting uncertainty into rank penalties."""
from datetime import date


def class_group(label):
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


def build_candidate_features(race, market_top_n=5, close_margin_s=0.5,
                             lightly_raced_max_starts=6,
                             long_layoff_days=120):
    ordered = sorted(race["horses"], key=lambda h: (h["win_odds"], h["number"]))
    market_rank = {h["number"]: i + 1 for i, h in enumerate(ordered)}
    race_day = date.fromisoformat(race["date"])
    rows = []
    candidate_numbers = []

    for horse in sorted(race["horses"], key=lambda h: h["number"]):
        reasons = []
        uncertainty_flags = []
        runs = horse.get("recent_runs", [])

        if market_rank[horse["number"]] <= market_top_n:
            reasons.append("market_top_n")

        if any(
            r.get("surface") == race["surface"]
            and r.get("distance_m") == race["distance_m"]
            and r.get("finish") == 1
            for r in runs
        ):
            reasons.append("recent_same_distance_win")

        race_group = class_group(race.get("class"))
        for run in runs:
            if class_group(run.get("class")) != race_group:
                continue
            margin = run.get("beaten_margin_s")
            close = (
                run.get("finish", 999) <= 4
                or (isinstance(margin, (int, float)) and margin <= close_margin_s)
            )
            if close:
                reasons.append("recent_same_class_close")
                break

        if horse.get("career_starts", 999) <= lightly_raced_max_starts and any(
            r.get("finish") == 1 for r in runs
        ):
            reasons.append("lightly_raced_recent_win")

        latest = horse.get("source_latest_run_date")
        if latest:
            layoff_days = (race_day - date.fromisoformat(latest)).days
            if layoff_days > long_layoff_days:
                uncertainty_flags.append("long_layoff")

        candidate = bool(reasons)
        if candidate:
            candidate_numbers.append(horse["number"])

        rows.append({
            "number": horse["number"],
            "name": horse.get("name"),
            "market_rank": market_rank[horse["number"]],
            "candidate": candidate,
            "candidate_reasons": sorted(set(reasons)),
            "uncertainty_flags": sorted(set(uncertainty_flags)),
        })

    return {
        "race": race.get("race"),
        "candidate_numbers": candidate_numbers,
        "horses": rows,
    }
