#!/usr/bin/env python3
"""Five JRA races: retrospective WIN/WIDE market hierarchy proper scoring.

Source-locked archival prestart snapshots on 2026-10-12 Kyoto races 8–12:
all 67 horses and 439 unique WIDE pairs, complete fields, one data
provider. WIN and WIDE source page update times are the same minute in
3 races, within ONE minute in 2 races. They are NOT atomic tote snapshots.

The PL source-only baseline and four UNFITTED horse-node/pair models
are created in pre_race_forecasts() BEFORE ANY official-result file
is opened. Outcomes are later loaded from official JRA postrace archive.

The coefficients 0.5 and -0.5 are arbitrary sensitivity values, not
estimated. NO claim of improved true win/place probabilities, market
efficiency, prospective skill or positive wagering expected value.
All comparisons are postrace exploratory and must not enter frozen v3.1.

Run:
 python scripts/odds_five_race_joint_market_score.py \
   --output tmp/odds-five-race-win-wide-retrospective.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from itertools import combinations
import json
import math
from pathlib import Path
from statistics import mean

from odds_real_multirace_archive_audit import SOURCE_SHA, read_file, _one_race
from odds_r8_real_three_time_market import _wide_vector, _win_vector
from odds_cross_pool_global_async import relative_pair_indices
from odds_pair_hierarchy_decomposition import complete_graph_decompose
from odds_coherent_hierarchy_rank_bridge import joint_rank_probability
from odds_six_race_predictive_increment import verify_official_oct12

ROOT=Path(__file__).resolve().parents[1]
STATUS="FIVE_RACES_ONE_DATE_POSTRACE_WIN_WIDE_HIERARCHY_NO_PROSPECTIVE_VALIDATION"
WIDE_SOURCE={
    8:("data/2026-10-12/remaining-snapshots/r8_wide.json",
       "10bb0d0bcab6035eceaa4edda8c31999d83dae05"),
    9:("data/2026-10-12/remaining-snapshots/r9_wide.json",
       "9f49f4379537100038111be3b09b671e42e99e44"),
    10:("data/2026-10-12/remaining-snapshots/r10_wide.json",
        "2f169fb146260a26a7d6a5d9a73dd4838c7b82fc"),
    11:("data/2026-10-12/remaining-snapshots/r11_wide.json",
        "c88b4420c1c3d2a3ea5b75e485f46a4eff129203"),
    12:("data/2026-10-12/remaining-snapshots/r12_wide.json",
        "151369b0f392bd10e18530ebbcfea4e701fc4919"),
}
SCENARIOS={
    "win_PL_baseline":(0.0,0.0),
    "horse_node_positive_half":(0.5,0.0),
    "pair_specific_positive_half":(0.0,0.5),
    "horse_and_pair_positive_half":(0.5,0.5),
    "horse_node_negative_half":(-0.5,0.0),
}
METRICS=(
    "win_categorical_log_loss",
    "win_multiclass_brier",
    "top3_per_horse_binary_brier",
    "top3_per_horse_binary_log_loss",
    "unordered_top3_trio_log_loss",
    "wide_per_pair_binary_brier",
)


def _aware(value):
    ts=datetime.fromisoformat(value)
    if ts.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_SOURCE_TIME")
    return ts


def _strict_wide_range(rows, roster):
    for row in rows:
        low,high=row.get("odds_low"),row.get("odds_high")
        if (type(low) not in (float,int) or type(high) not in (float,int)
                or not math.isfinite(low) or not math.isfinite(high)
                or not 1.0<low<=high):
            raise ValueError("HOLD_WIDE_QUOTE_RANGE_INVALID")
    values=_wide_vector(rows)
    all_pairs=set(combinations(sorted(roster),2))
    if set(values)!=all_pairs:
        raise ValueError("HOLD_WIDE_QUOTE_PAIRS_INCOMPLETE_OR_CHANGED")
    return values


def pre_race_forecasts(root=ROOT):
    """Never opens JRA postrace outcomes or any quote later than candidate cutoff."""
    outputs=[]
    for race_no in range(8,13):
        early=read_file(root,SOURCE_SHA[race_no][0])
        win_page=read_file(root,SOURCE_SHA[race_no][1])
        wide_page=read_file(root,WIDE_SOURCE[race_no])
        _one_race(early,win_page,race_no)
        if (wide_page.get("race")!=race_no or wide_page.get("page_code")!="wide"
                or wide_page.get("missing")!=[]
                or not isinstance(wide_page.get("quotes",{}).get("wide"),list)
                or not wide_page.get("url","").startswith(
                    "https://sports.yahoo.co.jp/keiba/") or
                not win_page["url"].startswith("https://sports.yahoo.co.jp/keiba/")):
            raise ValueError("HOLD_WIDE_SNAPSHOT_SOURCE_MISSING_OR_WRONG_RACE")
        odds=_win_vector(win_page["quotes"]["win"])
        if set(odds)!=set(h["number"] for h in early["horses"]):
            raise ValueError("HOLD_WIN_WIDE_RUNNER_UNIVERSE")
        wide=_strict_wide_range(wide_page["quotes"]["wide"],set(odds))
        tw=_aware(win_page["updated_at_jst"])
        tp=_aware(wide_page["updated_at_jst"])
        post=_aware(early["start_jst"])
        win_receipt=_aware(win_page["observed_at_jst"])
        wide_receipt=_aware(wide_page["observed_at_jst"])
        gap_minutes=abs((tw-tp).total_seconds())/60
        if (gap_minutes>1.0 or
            not tw<=win_receipt<post or
            not tp<=wide_receipt<post or
            not _aware(early["odds_updated_at_jst"])<tw or
            max(tw,tp)>post-timedelta(minutes=10)):
            raise ValueError("HOLD_STALE_NONPRESTART_OR_UNMATCHED_SOURCE_MINUTES")
        if not (5<=len(odds)<=30):
            raise ValueError("HOLD_UNSUPPORTED_STARTER_COUNT")
        relative=relative_pair_indices({
            "label":f"prestart_kyoto_{race_no}",
            "win":odds,"wide":wide})
        graph=complete_graph_decompose(relative["pair_residual"])
        if graph["status"]!="COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION":
            raise ValueError("HOLD_BAD_PRE_RACE_GRAPH_DECOMPOSITION")
        predicted={
            key:joint_rank_probability(
                odds,graph["node_effects"],
                graph["pair_model_residuals"],
                beta_horse=coeffs[0],beta_pair=coeffs[1])
            for key,coeffs in SCENARIOS.items()
        }
        output={
            "race_id":early["race_id"],
            "race_no":race_no,
            "date":early["date"],
            "n_horses":len(odds),
            "wide_pair_count":len(wide),
            "win_page_source_updated_at":tw.isoformat(),
            "wide_page_source_updated_at":tp.isoformat(),
            "source_page_update_minute_gap":gap_minutes,
            "page_same_publisher_update_minute":gap_minutes==0,
            "first_page_received_at":min(win_receipt,wide_receipt).isoformat(),
            "last_page_received_at":max(win_receipt,wide_receipt).isoformat(),
            "scheduled_post":post.isoformat(),
            "fit_price_index_R2_not_result_forecasting_R2":
                graph["explained_fraction_of_edge_change_variance"],
            "forecasts":predicted,
        }
        outputs.append(output)
    if len(outputs)!=5 or len({v["race_id"] for v in outputs})!=5:
        raise ValueError("HOLD_NOT_FIVE_DISTINCT_SOURCE_RACES")
    return outputs


def score_ranking(model, official_order):
    """Proper odds-vs-actual outcome scores for coherent PL-like ranking."""
    pwin=model["win"]
    ptop=model["top3"]
    ppair=model["both_top3_pair"]
    ptrio=model["unordered_top3_trio"]
    expected_keys=set(pwin)
    if (len(official_order)!=3 or len(set(official_order))!=3
            or not set(official_order).issubset(expected_keys)):
        raise ValueError("HOLD_OFFICIAL_FINISH_NOT_IN_PRE_RACE_FIELD")
    real_win=official_order[0]
    truth=set(official_order)
    n=len(pwin)
    trio=tuple(sorted(official_order))
    eps=1e-12
    return {
        "win_categorical_log_loss":-math.log(max(pwin[real_win],eps)),
        "win_multiclass_brier":sum(
            (v-(1 if i==real_win else 0))**2
            for i,v in pwin.items()),
        "top3_per_horse_binary_brier":mean(
            (v-(1 if i in truth else 0))**2
            for i,v in ptop.items()),
        "top3_per_horse_binary_log_loss":-mean(
            math.log(max(min(v if i in truth else 1-v,1-eps),eps))
            for i,v in ptop.items()),
        "unordered_top3_trio_log_loss":-math.log(
            max(ptrio[trio],eps)),
        "wide_per_pair_binary_brier":mean(
            (v-(1 if all(h in truth for h in pair) else 0))**2
            for pair,v in ppair.items()),
    }


def aggregate_scored_races(races):
    if not races or set(x["race_no"] for x in races)!=set(range(8,13)):
        raise ValueError("HOLD_INCOMPLETE_RETROSPECTIVE_SCORING")
    model_names=list(SCENARIOS)
    results={}
    for cohort_name, subset in (
        ("all_five_one_meeting_day",races),
        ("same_source_update_minute_three_races",[
            r for r in races if r["page_same_publisher_update_minute"]]),
        ("one_minute_mismatch_two_races",[
            r for r in races if not r["page_same_publisher_update_minute"]]),
    ):
        if not subset:continue
        means={
            name:{metric:mean(r["scores"][name][metric] for r in subset)
                  for metric in METRICS} for name in model_names
        }
        base=means["win_PL_baseline"]
        for name in model_names:
            means[name]["delta_vs_PL_lower_is_better"]={
                metric:means[name][metric]-base[metric] for metric in METRICS
            }
        results[cohort_name]={
            "actual_independent_races":len(subset),
            "mean_scores_by_model":means,
            "race_ids":[r["race_id"] for r in subset],
            "different_races_not_different_meeting_days":True,
        }
    return results


def audit(root=ROOT):
    # ALL forecasts frozen from only pre-race snapshot sources.
    pre=pre_race_forecasts(root)
    # Official results are postrace labels only and loaded only now.
    source,when=verify_official_oct12(root)
    seen=[]
    for pre_race in pre:
        official=source["races"][str(pre_race["race_no"])]
        positions=official["positions"]
        if not (_aware(pre_race["scheduled_post"])<when):
            raise ValueError("HOLD_POSTRACE_OUTCOME_TIMING_INVALID")
        scores={label:score_ranking(m,positions)
                for label,m in pre_race["forecasts"].items()}
        seen.append({
            "race_id":pre_race["race_id"],
            "race_no":pre_race["race_no"],"date":pre_race["date"],
            "n_horses":pre_race["n_horses"],
            "wide_pair_count":pre_race["wide_pair_count"],
            "official_top3":positions,
            "official_jra_source":official["source_url"],
            "win_page_source_updated_at":pre_race["win_page_source_updated_at"],
            "wide_page_source_updated_at":pre_race["wide_page_source_updated_at"],
            "source_page_update_minute_gap":pre_race[
                "source_page_update_minute_gap"],
            "page_same_publisher_update_minute":pre_race[
                "page_same_publisher_update_minute"],
            "price_index_horse_layer_fit_R2_not_outcome_model_R2":
                pre_race["fit_price_index_R2_not_result_forecasting_R2"],
            "scores":scores,
        })
    cohorts=aggregate_scored_races(seen)
    return {
        "status":STATUS,"date":"2026-10-12",
        "venue":"Kyoto",
        "number_of_meeting_dates":1,
        "independent_real_races":len(seen),
        "horse_race_entries":sum(x["n_horses"] for x in seen),
        "full_bet_pairs_not_independent_samples":sum(
            x["wide_pair_count"] for x in seen),
        "same_minute_win_wide_races":sum(
            x["page_same_publisher_update_minute"] for x in seen),
        "one_minute_source_update_gap_races":sum(
            not x["page_same_publisher_update_minute"] for x in seen),
        "coefficients_hypothetical_not_selected_on_outcomes":{
            k:{"horse_node_beta":v[0],"pair_residual_beta":v[1]}
            for k,v in SCENARIOS.items()},
        "market_price_index_not_calibrated_probability":True,
        "outcome_scores_are_retrospective_not_frozen_or_prospective":True,
        "raw_official_result_input_not_part_of_predictor":True,
        "cohort_means":cohorts,
        "per_race":seen,
        "scientific_limitations":[
            "Only one Kyoto meeting date, five races; race-level and meeting-date statistical uncertainty cannot be generalized.",
            "Betting WIDE lower quotes are conditional payouts, not event probabilities, and PL pair probabilities are model assumptions.",
            "Two races have 1-minute difference in win vs WIDE publisher-update minute, and matching minutes in the other three do not prove atomic pool synchronization.",
            "β=+/−0.5 are hypothetical; they were not trained and frozen on distinct earlier meeting dates.",
            "Any row showing a small improvement here does not establish repeatable added information, calibrated probabilities, exploitable value, or bettor feedback.",
            "The same 439 WIDE pairs overlap, and are not 439 independent horse races.",
            "Do not add these historical outcomes to the formal frozen v3.1 20-race holdout ledger or fit thresholds post hoc.",
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=Path("tmp/odds-five-race-win-wide-retrospective.json"))
    args=parser.parse_args()
    result=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    wanted=("win_categorical_log_loss","top3_per_horse_binary_brier",
            "unordered_top3_trio_log_loss")
    def pack(m):
        return {name:{k:val[k] for k in wanted}
                for name,val in m.items()}
    print(json.dumps({
        "status":result["status"],
        "races":result["independent_real_races"],
        "days":result["number_of_meeting_dates"],
        "horse_entries":result["horse_race_entries"],
        "full_WIDE_pairs":result["full_bet_pairs_not_independent_samples"],
        "three_same_minute":{
            "races":result["cohort_means"][
                "same_source_update_minute_three_races"]["actual_independent_races"],
            "scores":pack(result["cohort_means"][
                "same_source_update_minute_three_races"]["mean_scores_by_model"])
        },
        "all_five_scores":pack(result["cohort_means"][
            "all_five_one_meeting_day"]["mean_scores_by_model"]),
        "cohorts_not_independent_dates":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
