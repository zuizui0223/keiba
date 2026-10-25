#!/usr/bin/env python3
"""Historical JRA horse-form -> physical horse ABMs -> bettor ABM -> prices.

The present Kyoto 2026-10-12 history was RETRIEVED AFTER its targets ran.
Only strictly older race records are read, but a later-source reconstruction
IS NOT an authentic event-time available feature panel or prospective test.
The Akikasho/秋華賞 2026-10-18 pre-draw history has a verified NAME->DRAW
crosswalk, without a separately authenticated before-post history receipt.

Absolutely no target finishing place, market quote, past popularity, future
row, or JRA official target outcome is used to construct horse form. Original
PR #14 physical and market ABMs accept this deliberately alternative prior.
No physical skill parameter is fitted to six scored races.
"""
from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha1
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from keiba_coupled_horse_market_pde import (
    couple_prestart, vector, MIXED_MODES, ROOT,
)
from odds_threshold_regime_bridge import (
    aware, market_features, score_forecast, load_source_locked_panels,
)

STATUS = "POSTRACE_HISTORY_RECONSTRUCTION_NOT_AUTHENTIC_ASOF_OR_PROSPECTIVE"
HISTORY_FILE = "data/2026-10-12/v3-normalized-prerace-history.json"
HISTORY_GIT_SHA = "c60f09fc8e84500579482a1d2f1390862403325c"
SHUKA_HISTORY_FILE = "data/2026-10-18/shuka-jra-official-17-pre-draw.json"
SHUKA_HISTORY_SHA = "d0def56091b76a831b1ea4a93aa514017c8c6501"
SHUKA_DRAW_FILE = "data/2026-10-18/shuka-jra-official-17-horse-numbers.json"
SHUKA_DRAW_SHA = "ff787df0ac64f742c56de6a7fb48aaf410ba790e"

# ALL values are method-design assumptions, never fitted on the six labels.
RECENCY_DAYS = 200.
DISTANCE_SCALE_M = 700.
OTHER_SURFACE_WEIGHT = .30
HISTORY_SHRINKAGE = 2.
HORSE_FORM_LOGIT_MULTIPLIER = 2.
MARKET_HISTORY_BLEND = .20
ARMS = ("market_proxy", "history_only", "history_shuffled",
        "market_80_history_20")
CHECKED_SCORE_MODELS = ("horse_SDE_weak", "market_information",
                        "market_mixed", "market_threshold_mixed")


def _read_git_sha(root: Path, filename: str, expected: str):
    raw = (Path(root) / filename).read_bytes()
    got = sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if got != expected:
        raise ValueError("HOLD_HISTORICAL_SOURCE_SHA_DRIFT:" + filename)
    return json.loads(raw.decode("utf-8"))


def history_map(root=ROOT):
    """Only archived features; no official target outcome is opened."""
    history = _read_git_sha(root, HISTORY_FILE, HISTORY_GIT_SHA)
    old_shuka = _read_git_sha(root, SHUKA_HISTORY_FILE, SHUKA_HISTORY_SHA)
    draw = _read_git_sha(root, SHUKA_DRAW_FILE, SHUKA_DRAW_SHA)
    if (history.get("retrieved_postrace_for_retrospective_normalization") is not True
            or history.get("target_date") != "2026-10-12"
            or old_shuka.get("status") !=
               "SOURCE_VERIFIED_PRE_DRAW_PRICE_FREE_NOT_FROZEN_HOLDOUT"
            or old_shuka.get("past_only_history_before_target") is not True
            or draw.get("official_numbers_are_NOT_alphabetic_entry_order") is not True):
        raise ValueError("HOLD_HISTORY_RETRIEVAL_PROVENANCE")
    out = {}
    # This source was normalized postrace, even though all constituent
    # historical starts precede the target date.
    from odds_real_multirace_archive_audit import SOURCE_SHA, read_file
    for race in range(8, 13):
        key = str(race)
        cfg = history["races"].get(key, {})
        card = read_file(root, SOURCE_SHA[race][0])
        names = {x["number"]: x["name"] for x in card["horses"]}
        entries = cfg.get("horses", [])
        if (len(entries) != len(names) or
                {x["number"] for x in entries} != set(names) or
                any(x["name"] != names[x["number"]] for x in entries)):
            raise ValueError("HOLD_HISTORY_CARD_NUMBER_OR_NAME_MISMATCH")
        surface = {"turf": "芝", "dirt": "ダ", "obstacle": "障"}.get(
            card["surface"])
        if surface is None:
            raise ValueError("HOLD_UNSUPPORTED_TARGET_SURFACE")
        out[card["race_id"]] = {
            "target_date": card["date"], "target_surface": surface,
            "distance_m": card["distance_m"],
            "rows": {x["number"]: x for x in entries},
            "source_scope": "POSTRACE_RETRIEVED_PAST_ONLY_JRA_PROFILE",
        }
    runners = old_shuka.get("runners", [])
    lookup = {z["name"]: z for z in runners}
    draw_rows = draw.get("JRA_official_horse_number_by_name", [])
    if len(lookup) != 17 or len(draw_rows) != 17:
        raise ValueError("HOLD_SHUKA_CROSSWALK_COVERAGE")
    if len({x["name"] for x in runners}) != 17:
        raise ValueError("HOLD_SHUKA_HORSE_NAME_DUPLICATES")
    if ({x["horse_name"] for x in draw_rows} != set(lookup)
            or {x["official_horse_number"] for x in draw_rows} != set(range(1,18))):
        raise ValueError("HOLD_SHUKA_DRAW_NAME_IDENTITY")
    out["2608040711"] = {
        "target_date": old_shuka["target"]["date"],
        "target_surface": old_shuka["target"]["surface"],
        "distance_m": old_shuka["target"]["distance_m"],
        "rows": {x["official_horse_number"]: lookup[x["horse_name"]]
                 for x in draw_rows},
        "source_scope": "PRE_DRAW_HISTORY_WITHOUT_INDEPENDENT_ASOF_RECEIPT",
    }
    return out


def form_prior(row, archive):
    """Strictly older finishes/distance/surface/age; NEVER target data/odds.

    Past field sizes are absent from Akikasho JRA archive. We deliberately
    use exp(-(finish-1)/3) in both cohorts rather than impute field sizes.
    This is an *uncalibrated* past-form score, NOT a measured speed/pace.
    """
    ids = sorted(row["first_odds"])
    if (set(ids) != set(archive["rows"]) or
            row["meeting_day"] != archive["target_date"]):
        raise ValueError("HOLD_HORSE_HISTORY_DIFFERENT_TARGET_RACE")
    target_day = date.fromisoformat(archive["target_date"])
    s = []
    count = 0
    no_history = 0
    all_dates_valid = True
    for num in ids:
        x = archive["rows"][num]
        hist = x.get("full_history_before_target")
        if not isinstance(hist, list):
            raise ValueError("HOLD_MISSING_PAST_HISTORY_VECTOR")
        if len(hist) == 0:
            no_history += 1
        wsum = 0.
        vtot = 0.
        for t in hist:
            # Only five keys are read from each historic run.
            event_day = date.fromisoformat(t["date"])
            if event_day >= target_day:
                raise ValueError("HOLD_CURRENT_OR_FUTURE_RUN_LEAKAGE")
            fin, dist, surf = t["finish"], t["distance_m"], t["surface"]
            if (type(fin) is not int or fin < 1 or
                    type(dist) is not int or dist <= 0 or
                    surf not in ("芝", "ダ", "障")):
                raise ValueError("HOLD_INVALID_PAST_RACE_RECORD")
            lag = (target_day - event_day).days
            weight = (math.exp(-lag / RECENCY_DAYS) *
                      math.exp(-abs(dist - archive["distance_m"]) /
                               DISTANCE_SCALE_M) *
                      (1. if surf == archive["target_surface"]
                       else OTHER_SURFACE_WEIGHT))
            # Rank-only common to both source schemas. Do not use market
            # rank, past popularity, past tote odds, or current result.
            score = math.exp(-(fin-1)/3.)
            wsum += weight
            vtot += weight * score
            count += 1
        s.append(vtot / (wsum + HISTORY_SHRINKAGE))
    if not len(s) >= 5:
        raise ValueError("HOLD_TOO_FEW_HISTORICAL_RUNNERS")
    v = np.asarray(s, dtype=float)
    weights = np.exp(HORSE_FORM_LOGIT_MULTIPLIER * (v - np.max(v)))
    prior = vector(weights)
    return {
        "horse_numbers": ids,
        "prior": prior,
        "prior_form_scores": v,
        "past_race_records_examined": count,
        "entrants_without_any_past_run": no_history,
        "all_run_dates_strictly_before_target": all_dates_valid,
        "fields_used_in_past_records":
            ["date", "finish", "distance_m", "surface"],
        "postrace_history_captured_for_one_cohort": True,
        "certified_target_time_history_available": False,
    }


def fixed_priors(row, form):
    q_market = vector(market_features(row)["early"])
    history = vector(form["prior"])
    # Deterministic cyclic horse-label counterfactual, no result selected.
    placebo = np.roll(history, 1)
    blend = vector(q_market**(1-MARKET_HISTORY_BLEND) *
                   history**MARKET_HISTORY_BLEND)
    return {"market_proxy": None,
            "history_only": history,
            "history_shuffled": placebo,
            "market_80_history_20": blend}


def audit(root=ROOT, *, draws=120, seed=20261025,
          historical_source_asof_certified=False, prestart_only=False):
    """Retrospective reconstruction only, even when target results not read."""
    if historical_source_asof_certified:
        raise ValueError("HOLD_NO_AUTHENTIC_TARGET_TIME_HISTORY_SOURCE_RECEIPT")
    if prestart_only:
        raise ValueError("HOLD_POSTRACE_RETRIEVED_HISTORY_NOT_PRESTART_ELIGIBLE")
    if draws < 40:
        raise ValueError("HOLD_TOO_FEW_MC_DRAWS")
    rows = load_source_locked_panels(root)
    archives = history_map(root)
    if len(rows) != 6 or set(archives) != {row["race_id"] for row in rows}:
        raise ValueError("HOLD_UNMATCHED_SIX_RACE_HISTORIES")
    prepared = []
    for k, row in enumerate(rows):
        source = archives[row["race_id"]]
        form = form_prior(row, source)
        variants = fixed_priors(row, form)
        sims = {}
        for arm, external in variants.items():
            sims[arm] = couple_prestart(
                row, distance_m=source["distance_m"], draws=draws,
                seed=seed + 1000*k, votes_per_step=250,
                horse_prior=external)
        prepared.append({"row": row, "form": form, "sim": sims,
                         "source_scope": source["source_scope"]})

    # All six source-locked forecasts and negative controls exist before
    # any official target outcome is opened.
    from odds_six_race_predictive_increment import (
        verify_official_oct12, verify_official_shuka)
    oct12, v_at = verify_official_oct12(root)
    shuka = verify_official_shuka(root)
    results = []
    for item in prepared:
        row = item["row"]
        if row["meeting_day"] == "2026-10-12":
            if v_at <= aware(row["post_at"]):
                raise ValueError("HOLD_OUTCOME_TIMESTAMP_BEFORE_TARGET")
            actual = oct12["races"][str(row["race_no"])]["positions"]
        else:
            if shuka["verified_on_jst"] <= row["meeting_day"]:
                raise ValueError("HOLD_SHUKA_AFTER_RESULT_CLOCK")
            actual = shuka["top3"]
        features = market_features(row)
        models = {}
        for arm in ARMS:
            res = item["sim"][arm]
            models[arm] = {
                "scores": {mod: score_forecast(
                    features, res["predictions"][mod], actual)
                    for mod in CHECKED_SCORE_MODELS},
                "mean_market_TV_pp": {
                    mode: res["market_paths"][mode][
                        "TV_to_archived_later_quote_pp"]
                    for mode in MIXED_MODES}}
        observed_m0 = score_forecast(
            features, item["sim"]["market_proxy"][
                "predictions"]["observed_M0"], actual)
        results.append({"race_id":row["race_id"],
                        "day":row["meeting_day"],
                        "source_scope":item["source_scope"],
                        "history_n":item["form"]["past_race_records_examined"],
                        "unseen_horses":item["form"]["entrants_without_any_past_run"],
                        "arms":models, "observed_M0":observed_m0})
    out = {
        "status": STATUS,
        "real_races": 6, "real_meeting_dates": 2,
        "horse_race_entries": sum(len(x["form"]["horse_numbers"])
                                  for x in prepared),
        "entrants_with_no_past_start": sum(
            x["form"]["entrants_without_any_past_run"] for x in prepared),
        "all_histories_reconstruct_only": True,
        "original_postrace_normalization_not_asof_proven": True,
        "future_target_data_used_to_calculate_form": False,
        "real_JRA_GPS_or_true_speed_from_histories": False,
        "history_horse_identity_placebo_fixed_cyclic_shift": True,
        "fixed_parameters_not_fit_on_actual_six_race_outcomes": {
            "recency_days": RECENCY_DAYS, "distance_scale_m":DISTANCE_SCALE_M,
            "other_surface_weight":OTHER_SURFACE_WEIGHT,
            "pseudo_history_weight":HISTORY_SHRINKAGE,
            "logit_multiplier":HORSE_FORM_LOGIT_MULTIPLIER,
            "market_history_geometric_blend":MARKET_HISTORY_BLEND},
        "per_race_summary": [
            {key:r[key] for key in ("race_id","day","source_scope","history_n",
                                    "unseen_horses")} for r in results],
        "mean_race_equal": {
            arm: {
                mod: {metric: mean(
                    z["arms"][arm]["scores"][mod][metric] for z in results)
                    for metric in ("win_log_loss", "top3_brier")}
                for mod in CHECKED_SCORE_MODELS}
            for arm in ARMS},
        "market_TV_pp_race_equal": {
            arm: {mode: mean(z["arms"][arm]["mean_market_TV_pp"][mode]
                            for z in results) for mode in MIXED_MODES}
            for arm in ARMS},
        "M0_late_market_reference": {
            met: mean(z["observed_M0"][met] for z in results)
            for met in ("win_log_loss", "top3_brier")},
        "history_only_vs_permuted_past_identity_win_log_loss_delta":
            mean(z["arms"]["history_only"]["scores"]["market_information"]
                 ["win_log_loss"] -
                 z["arms"]["history_shuffled"]["scores"]["market_information"]
                 ["win_log_loss"] for z in results),
        "trained_coef_or_empirical_gain_claim": "HOLD",
        "prospective_model_readiness": "HOLD_UNPROVEN_HISTORY_CAPTURE_TIME",
        "separate_cannon_park_GPS_transfer_to_JRA_ability": "NOT_PERMITTED",
        "existing_PR10_Kikka_and_v31_frozen": True,
    }
    if out["horse_race_entries"] != 84 or out["entrants_with_no_past_start"]!=1:
        raise ValueError("HOLD_ARCHIVED_PAST_FORM_SOURCE_COVERAGE_CHANGED")
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,
        default=Path("tmp/coupled-history-identity-falsification.json"))
    p.add_argument("--draws",type=int,default=120)
    p.add_argument("--seed",type=int,default=20261025)
    p.add_argument("--prestart-only",action="store_true")
    a=p.parse_args()
    result=audit(draws=a.draws,seed=a.seed,prestart_only=a.prestart_only)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "races":result["real_races"],
        "horse_rows":result["horse_race_entries"],
        "history_vs_shuffled_winner_log_loss":
            result["history_only_vs_permuted_past_identity_win_log_loss_delta"],
        "prospective":"HOLD"},ensure_ascii=False))


if __name__=="__main__":
    main()
