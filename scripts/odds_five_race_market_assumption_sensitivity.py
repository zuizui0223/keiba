#!/usr/bin/env python3
"""Five Kyoto races: does hypothetical WIDE outcome scoring survive assumptions?

Sensitivity on exactly the same archived 2026-10-12 five-race podiums:
- Win PL intensity gamma={.75,1,1.25} ONLY in residual construction,
- Complete WIDE payout-range mapping={lower, geometric, upper}.
- The PL baseline of coherent finish probabilities is unchanged.
- Horse and pair coefficients are fixed arbitrary plus/minus 0.5.

All 9 *prestart* forecast families are built before official outcomes
are loaded. This is retrospective diagnostic sensitivity, not nine
independent experiments, market calibration, or a valid test for odds
threshold/positive returns.

Run:
  python scripts/odds_five_race_market_assumption_sensitivity.py \
     --output tmp/odds-five-race-market-sensitivity.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

from odds_five_race_joint_market_score import (
    SCENARIOS, STATUS as BASE_STATUS, METRICS,
    pre_race_forecasts, score_ranking,
)
from odds_six_race_predictive_increment import verify_official_oct12

ROOT=Path(__file__).resolve().parents[1]
STATUS="FIVE_RACE_ONE_DAY_WIN_WIDE_BETA_ASSUMPTION_SENSITIVITY_NOT_VALIDATION"
GAMMAS=(.75,1.0,1.25)
MAPPINGS=("lower","geometric","upper")
CHECK_MODELS=(
    "horse_node_positive_half",
    "pair_specific_positive_half",
    "horse_and_pair_positive_half",
    "horse_node_negative_half",
)
REPORT_METRICS=(
    "win_categorical_log_loss",
    "top3_per_horse_binary_brier",
    "unordered_top3_trio_log_loss",
)


def audit(root=ROOT):
    # Every forecast family must be constructed before looking at ANY actual
    # horse number in the five JRA official postrace podiums.
    forecasts={}
    for gamma in GAMMAS:
        for mapping in MAPPINGS:
            forecast=pre_race_forecasts(
                root,pl_gamma=gamma,wide_mode=mapping)
            if len(forecast)!=5:
                raise ValueError("HOLD_INCOMPLETE_FIVE_PRESTART_MARKET_SETS")
            forecasts[(gamma,mapping)]=forecast

    official,verified_at=verify_official_oct12(root)
    regimes=[]
    for (gamma,mapping),races in forecasts.items():
        entries=[]
        for race in races:
            actual=official["races"][str(race["race_no"])]["positions"]
            if race["date"]!="2026-10-12" or race["n_horses"]<5:
                raise ValueError("HOLD_SOURCE_COHORT_CHANGED")
            scores={
                name:score_ranking(pred,actual)
                for name,pred in race["forecasts"].items()
            }
            entries.append({
                "race":race["race_no"],
                "win_and_wide_page_source_minute_matches":
                    race["page_same_publisher_update_minute"],
                "scores":scores,
            })
        subgroups={
            "all_five":entries,
            "same_publisher_update_minute_three":
                [r for r in entries if r["win_and_wide_page_source_minute_matches"]],
        }
        values={}
        for group,subset in subgroups.items():
            baseline={
                metric:mean(r["scores"]["win_PL_baseline"][metric]
                            for r in subset)
                for metric in REPORT_METRICS
            }
            model_diffs={}
            for model in CHECK_MODELS:
                model_diffs[model]={
                    metric:mean(
                        r["scores"][model][metric]-
                        r["scores"]["win_PL_baseline"][metric]
                        for r in subset)
                    for metric in REPORT_METRICS
                }
            values[group]={
                "real_race_count":len(subset),
                "PL_baseline_scores":baseline,
                "fixed_beta_model_minus_PL_score_deltas":model_diffs,
            }
        regimes.append({
            "residual_PL_popularity_exponent_assumed":gamma,
            "WIDE_conditional_payout_price_mapping_assumed":mapping,
            "cohorts":values,
        })
    spans={}
    for group in ("all_five","same_publisher_update_minute_three"):
        spans[group]={}
        for model in CHECK_MODELS:
            spans[group][model]={}
            for metric in REPORT_METRICS:
                vals=[
                    r["cohorts"][group]
                     ["fixed_beta_model_minus_PL_score_deltas"][model][metric]
                    for r in regimes
                ]
                spans[group][model][metric]={
                    "min_assumption_specific_delta":min(vals),
                    "max_assumption_specific_delta":max(vals),
                    "cases_out_of_nine_model_better_than_PL":sum(v<0 for v in vals),
                    "sign_stable_across_nine_assumptions":
                        all(v<0 for v in vals) or all(v>0 for v in vals),
                }
    return {
        "status":STATUS,
        "actual_independent_races":5,
        "actual_independent_meeting_dates":1,
        "full_WIN_horse_entries":67,
        "full_WIDE_pair_entries":439,
        "assumption_regimes_not_independent_realizations":len(regimes),
        "fixed_coefficients_not_fit_to_podiums":{
            model:SCENARIOS[model] for model in CHECK_MODELS
        },
        "official_results_only_loaded_after_all_prestart_forecasts":True,
        "original_PL_race_outcomes_and_weights_same_in_every_regime":True,
        "WIDE_payout_low_high_are_different_conditional_cases_not_sampling_CI":True,
        "assumption_details":regimes,
        "sign_stability_by_group_model_and_proper_score":spans,
        "limitations":[
            "Five outcomes from one date cannot determine a robust forecasting signal, beta, odds threshold, market efficiency or return.",
            "The nine WIDE mapping/PL gamma regimes reuse identical five observed results and are not independent tests.",
            "The 3 exact-minute comparisons still join separate source pages, not atomically synchronized wager pools.",
            "No coefficient was trained using past independent meeting dates; a good sign here is a postrace description only.",
            "Win categorical log loss, Top3 Brier and unordered trio log loss are distinct scoring targets; no cherry-picking is allowed.",
            "A previous market's WIDE price lower/upper range is conditional on event realization, not measurement uncertainty.",
            "Do not change main, v3.1 formal holdout or previously frozen ticket selection thresholds.",
        ],
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,
                    default=Path("tmp/odds-five-race-market-sensitivity.json"))
    args=ap.parse_args()
    out=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    x=out["sign_stability_by_group_model_and_proper_score"]
    print(json.dumps({
        "status":out["status"],"actual_races":out["actual_independent_races"],
        "independent_meeting_dates":out["actual_independent_meeting_dates"],
        "assumption_regimes":out["assumption_regimes_not_independent_realizations"],
        "all_five_WIN_logloss_deltas":{
            k:v["win_categorical_log_loss"] for k,v in x["all_five"].items()
        },
        "all_five_Top3_Brier_deltas":{
            k:v["top3_per_horse_binary_brier"] for k,v in x["all_five"].items()
        },
        "exact_minute_three_WIN_logloss_deltas":{
            k:v["win_categorical_log_loss"]
            for k,v in x["same_publisher_update_minute_three"].items()
        },
        "no_prospective_horse_prediction_claim":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
