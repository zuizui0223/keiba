#!/usr/bin/env python3
"""Independent, explicitly exploratory 3-gate odds threshold audit.

M0/M1/M2 in the 2026-10-24 PR #10 prestart SHA freeze are immutable.
This NEW M3 is a separate two-quote thought experiment, NOT a replacement.
Original market quotes are loaded only from source-locked research archives;
official outcomes are loaded only after all model forecasts are constructed.
No threshold or coefficient is fitted from the scored six races.

Run from keiba repository root:
 python scripts/odds_threshold_regime_bridge.py --output tmp/threshold-regime.json
 python scripts/odds_threshold_regime_bridge.py --prestart-only
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
BETA = 0.25
POPULARITY_ODDS_CUTOFF = 10.0
SPEED_LOG_PER_HOUR_CUTOFF = 0.10
INFORMATION_KL_STRATUM_CUTOFF = 0.005
INITIAL_ODDS_GRID = (5.0, 10.0, 20.0, 50.0)
SPEED_GRID = (0.05, 0.10, 0.20)
N_RACES_FOR_FORWARD_READINESS = 60
N_DATES_FOR_FORWARD_READINESS = 8
MODEL_NAMES = ("M0_latest", "M1_smooth", "M2_initial10", "M3_initial10_speed010")
STATUS = "EXPLORATORY_SIX_RACE_RETROSPECTIVE_THRESHOLDS_NOT_VALIDATED"


def aware(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("HOLD_MISSING_SOURCE_CLOCK")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_SOURCE_CLOCK")
    return parsed


def normalize(weights):
    if (len(weights) < 5 or any(type(x) not in (int, float)
                               or not math.isfinite(x) or x <= 0 for x in weights)):
        raise ValueError("HOLD_BAD_WEIGHT_VECTOR")
    z = sum(weights)
    return [w/z for w in weights]


def exact_win_top3(weights):
    """Ordered Plackett-Luce triple enumeration, probability masses (1, 3)."""
    q = normalize(weights)
    n = len(q)
    p3 = [0.0]*n
    for i in range(n):
        for j in range(n):
            if j == i:
                continue
            for k in range(n):
                if k in (i, j):
                    continue
                p = q[i]*q[j]/(1-q[i])*q[k]/(1-q[i]-q[j])
                p3[i] += p
                p3[j] += p
                p3[k] += p
    if (not math.isclose(sum(q), 1, abs_tol=1e-9)
            or not math.isclose(sum(p3), 3, abs_tol=1e-9)):
        raise ValueError("HOLD_PL_PROBABILITY_MASS")
    return {"win": q, "top3": p3}


def market_features(row):
    first, last = row["first_odds"], row["last_odds"]
    if (not isinstance(first, dict) or set(first) != set(last)
            or not 5 <= len(first) <= 30
            or any(type(i) is not int or i <= 0 for i in first)
            or any(type(x) not in (float, int) or not math.isfinite(x) or x <= 1
                   for x in list(first.values())+list(last.values()))):
        raise ValueError("HOLD_MISMATCHED_OR_BAD_FULL_FIELD_ODDS")
    initial, latest, post = (aware(row[k]) for k in
                              ("initial_quote_at", "latest_quote_at", "post_at"))
    if not (initial < latest <= post-timedelta(minutes=10)):
        raise ValueError("HOLD_SOURCE_TIME_TRAVEL_OR_TOO_LATE")
    hours = (latest-initial).total_seconds()/3600
    ids = sorted(first)
    q0 = normalize([1/first[i] for i in ids])
    q1 = normalize([1/last[i] for i in ids])
    shift = [math.log(new/old) for old, new in zip(q0, q1)]
    speed = [abs(x)/hours for x in shift]
    return {"horse_numbers": ids, "hours": hours, "early": q0, "latest": q1,
            "initial_odds": [first[i] for i in ids],
            "log_relative_support_change": shift,
            "absolute_log_relative_support_change_per_hour": speed}


def joint_from_features(f, *, beta=0.0, popularity=None, speed=None):
    """M0/M1/M2-compatible weights; M3 adds an *average-rate* threshold.

    Two points cannot reveal a within-path changepoint. When speed is None,
    this formula exactly reproduces PR #10's original M0/M1/M2 weights.
    """
    gates = [(popularity is None or odds >= popularity)
             and (speed is None or rate >= speed)
             for odds, rate in zip(f["initial_odds"],
                                   f["absolute_log_relative_support_change_per_hour"])]
    weights = normalize([q*math.exp(beta*d*int(g))
                         for q, d, g in zip(f["latest"],
                                             f["log_relative_support_change"], gates)])
    forecast = exact_win_top3(weights)
    return forecast, gates


def forecast_prestart(row):
    """Read strictly prestart rows; has no result argument or I/O."""
    f = market_features(row)
    policies = {
        "M0_latest": (0.0, None, None),
        "M1_smooth": (BETA, None, None),
        "M2_initial10": (BETA, POPULARITY_ODDS_CUTOFF, None),
        "M3_initial10_speed010": (BETA, POPULARITY_ODDS_CUTOFF,
                                    SPEED_LOG_PER_HOUR_CUTOFF),
    }
    predictions, gates, kl = {}, {}, {}
    for key, (beta, popularity, speed) in policies.items():
        predictions[key], gates[key] = joint_from_features(
            f, beta=beta, popularity=popularity, speed=speed)
    reference = predictions["M0_latest"]["win"]
    for key in MODEL_NAMES:
        target = predictions[key]["win"]
        kl[key] = sum(p*math.log(p/q) for p, q in zip(reference, target))
        if kl[key] < -1e-10:
            raise ValueError("HOLD_NEGATIVE_KL")
    return {"features": f, "predictions": predictions,
            "gates": gates, "KL_M0_to_model": kl}


def score_forecast(f, prediction, official_top3):
    ids = f["horse_numbers"]
    if (not isinstance(official_top3, list) or len(official_top3) != 3
            or len(set(official_top3)) != 3
            or not set(official_top3).issubset(set(ids))):
        raise ValueError("HOLD_OFFICIAL_FINISH_NOT_IN_SOURCE_ROSTER")
    winner = ids.index(official_top3[0])
    truth = set(official_top3)
    return {"win_log_loss": -math.log(prediction["win"][winner]),
            "top3_brier": mean((p-int(i in truth))**2
                               for i, p in zip(ids, prediction["top3"]))}


def load_source_locked_panels(root=ROOT):
    """Reuses PR #10's immutable Git-blob validation and clock checks."""
    from odds_real_multirace_archive_audit import SOURCE_SHA, read_file, _one_race
    from shuka2026_odds_information_hierarchy import read_locked, load_snapshots

    rows = []
    for race_no, (source0, source1) in SOURCE_SHA.items():
        first, last = read_file(root, source0), read_file(root, source1)
        _one_race(first, last, race_no)
        rows.append({
            "race_id": first["race_id"], "race_no": race_no,
            "meeting_day": "2026-10-12", "source_scope": "SAME_YAHOO_PUBLISHER_MINUTE",
            "first_odds": {h["number"]: h["win_odds"] for h in first["horses"]},
            "last_odds": {q["selection"][0]: q["odds_low"]
                          for q in last["quotes"]["win"]},
            "initial_quote_at": first["odds_updated_at_jst"],
            "latest_quote_at": last["updated_at_jst"],
            "post_at": first["start_jst"],
        })
    snapshots = load_snapshots(read_locked(root))
    first, last = snapshots[0], snapshots[-1]
    rows.append({
        "race_id": "2608040711", "race_no": 11,
        "meeting_day": "2026-10-18", "source_scope": "MIXED_PROVIDER_AND_CLOCK_SEMANTICS",
        "first_odds": first["win"], "last_odds": last["win"],
        "initial_quote_at": first["observed_at"],
        "latest_quote_at": last["observed_at"],
        "post_at": "2026-10-18T15:40:00+09:00",
    })
    if len(rows) != 6 or len({r["race_id"] for r in rows}) != 6:
        raise ValueError("HOLD_WRONG_ARCHIVE_RACE_COHORT")
    return rows


def real_three_point_regime(root=ROOT):
    """One race's two adjacent windows; does NOT establish a changepoint."""
    from odds_r8_real_three_time_market import collect_pre_race_price_panels
    panels, _, _, _, _ = collect_pre_race_price_panels(root)
    if len(panels) != 3:
        raise ValueError("HOLD_NOT_THREE_VERIFIED_REAL_QUOTES")
    segments = []
    for a, b in zip(panels[:-1], panels[1:]):
        first = a["relative_weights"]
        last = b["relative_weights"]
        if set(first) != set(last) or len(first) != 11:
            raise ValueError("HOLD_THREE_TIME_ROSTER_MISMATCH")
        hrs = (aware(b["provider_published_quote_minute"])
               - aware(a["provider_published_quote_minute"])).total_seconds()/3600
        if hrs <= 0:
            raise ValueError("HOLD_THREE_TIME_CLOCK_BAD")
        rates = [abs(math.log(last[i]/first[i]))/hrs for i in first]
        segments.append({"hours": hrs, "mean_abs_log_change_per_hour": mean(rates),
                         "horse_entries_rate_at_least_010":
                             sum(rate >= SPEED_LOG_PER_HOUR_CUTOFF for rate in rates),
                         "horse_entries_rate_at_least_020":
                             sum(rate >= .20 for rate in rates)})
    return {"race_id": "2608040508", "three_complete_market_times": True,
            "prestart_source_quote_minutes_only": True,
            "one_race_is_not_a_statistical_changepoint_test": True,
            "segments": segments}


def _score_history(predicted_rows, root):
    """Postrace labels are requested ONLY after all forecasts are built."""
    from odds_six_race_predictive_increment import (
        verify_official_oct12, verify_official_shuka,
    )
    oct12, verified_at = verify_official_oct12(root)
    shuka = verify_official_shuka(root)
    outputs = []
    for row, computed in predicted_rows:
        if row["meeting_day"] == "2026-10-12":
            outcome = oct12["races"][str(row["race_no"])]["positions"]
            if verified_at <= aware(row["post_at"]):
                raise ValueError("HOLD_JRA_RESULT_PRECEDES_POST")
        else:
            outcome = shuka["top3"]
            if shuka["verified_on_jst"] <= row["meeting_day"]:
                raise ValueError("HOLD_SHUKA_RESULT_TIME")
        outputs.append({"race_id": row["race_id"],
                        "meeting_day": row["meeting_day"],
                        "model_scores": {key: score_forecast(
                            computed["features"], computed["predictions"][key], outcome)
                            for key in MODEL_NAMES}})
    return outputs


def audit(root=ROOT, *, prestart_only=False):
    rows = load_source_locked_panels(root)
    prepared = [(row, forecast_prestart(row)) for row in rows]
    # No official outcomes are read above this line. The third snapshot is
    # strictly archival and is not used to refit or change the six-race M3.
    three_time = real_three_point_regime(root)
    dates = sorted({r["meeting_day"] for r in rows})
    entries = sum(len(v["features"]["horse_numbers"]) for _, v in prepared)
    grids = []
    for odds_cutoff in INITIAL_ODDS_GRID:
        for rate_cutoff in SPEED_GRID:
            count = sum(sum(o >= odds_cutoff and speed >= rate_cutoff
                            for o, speed in zip(v["features"]["initial_odds"],
                                                v["features"]["absolute_log_relative_support_change_per_hour"]))
                        for _, v in prepared)
            grids.append({"initial_odds_at_least": odds_cutoff,
                          "mean_log_change_rate_at_least": rate_cutoff,
                          "gated_horse_entries": count})
    per_race = [{"race_id": row["race_id"], "date": row["meeting_day"],
                 "source_scope": row["source_scope"],
                 "hours_between_quotes": v["features"]["hours"],
                 "runner_entries": len(v["features"]["horse_numbers"]),
                 "M2_gated_entries": sum(v["gates"]["M2_initial10"]),
                 "M3_gated_entries": sum(v["gates"]["M3_initial10_speed010"]),
                 "preoutcome_KL_M0_to_models": v["KL_M0_to_model"]}
                for row, v in prepared]
    result = {"status": STATUS, "model_status": "NEW_EXPLORATORY_M3_NOT_PART_OF_FROZEN_M0_M1_M2",
              "model_params": {"beta": BETA,
                               "initial_odds_cutoff": POPULARITY_ODDS_CUTOFF,
                               "average_abs_log_support_change_per_hour_cutoff": SPEED_LOG_PER_HOUR_CUTOFF,
                               "preoutcome_KL_stratum_cutoff": INFORMATION_KL_STRATUM_CUTOFF},
              "races": len(rows), "meeting_dates": len(dates), "horse_entries": entries,
              "source_dates": dates, "source_time_windows_heterogeneous": True,
              "source_opening_odds_certified": False,
              "high_KL_M1_races": sum(v["KL_M0_to_model"]["M1_smooth"] >= INFORMATION_KL_STRATUM_CUTOFF
                                    for _, v in prepared),
              "min_real_forward_races_design_gate": N_RACES_FOR_FORWARD_READINESS,
              "min_real_forward_dates_design_gate": N_DATES_FOR_FORWARD_READINESS,
              "qualified_for_forward_threshold_inference": False,
              "no_outcome_based_threshold_selection": True,
              "sensitivity_gate_counts_only_no_winner_selection": grids,
              "per_race": per_race, "three_time_single_race": three_time,
              "actual_market_herding_or_horse_PDE_causality": "HOLD",
              "positive_expected_wager_return": "HOLD"}
    if prestart_only:
        result["status"] = "PRESTART_ONLY_NO_OFFICIAL_OUTCOMES_READ"
        result["postrace_scores"] = "NOT_COMPUTED"
        return result
    scores = _score_history(prepared, root)
    if {(x["race_id"], x["meeting_day"]) for x in scores} != {
        (x["race_id"], x["meeting_day"]) for x in per_race}:
        raise ValueError("HOLD_POSTRACE_JOIN_CHANGED")
    score_by_id = {x["race_id"]: x for x in scores}
    for row in per_race:
        outcomes = score_by_id[row["race_id"]]["model_scores"]
        row["postrace_scores"] = outcomes
        row["win_log_loss_difference_vs_M0"] = {
            key: outcomes[key]["win_log_loss"]-outcomes["M0_latest"]["win_log_loss"]
            for key in MODEL_NAMES[1:]}
    result["mean_postrace_scores_race_equal"] = {
        key: {metric: mean(s["model_scores"][key][metric] for s in scores)
              for metric in ("win_log_loss", "top3_brier")}
        for key in MODEL_NAMES}
    result["mean_win_log_loss_difference_vs_M0_meeting_date_equal"] = {
        key: mean(mean(s["model_scores"][key]["win_log_loss"]
                       -s["model_scores"]["M0_latest"]["win_log_loss"]
                       for s in scores if s["meeting_day"] == day)
                  for day in dates)
        for key in MODEL_NAMES[1:]}
    result["race_count_lower_win_log_loss_than_M0"] = {
        key: sum(s["model_scores"][key]["win_log_loss"]
                 < s["model_scores"]["M0_latest"]["win_log_loss"] - 1e-12
                 for s in scores) for key in MODEL_NAMES[1:]}
    result["postrace_scores_are_retrospective_only"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path("tmp/odds-threshold-regime.json"))
    parser.add_argument("--prestart-only", action="store_true")
    a = parser.parse_args()
    report = audit(prestart_only=a.prestart_only)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "races": report["races"],
                      "meeting_dates": report["meeting_dates"],
                      "has_outcomes": not a.prestart_only,
                      "threshold_claim": "HOLD"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
