#!/usr/bin/env python3
"""Global win-vs-wide asynchrony index across all 136 pairs, one archived race.

Win odds and wide quotes are different overlapping events. The source
updates are NOT atomic across pools, so residuals are exploratory relative
price-shape differences, neither probability errors nor evidence of
asynchronous bettor information propagation.

The Plackett-Luce win baseline gives P(both horses Top3). Since every
3-horse podium entails exactly three winning wide pairs, divide by 3
to normalize the overlapping events to an index summing to 1.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, median

from shuka2026_odds_information_hierarchy import (
    load_snapshots, read_locked, pl_pair_top3_index,
)

STATUS = "SINGLE_RACE_136_OVERLAPPING_WIDE_PAIR_PRICE_INDEX_ONLY"
LOG25 = math.log(1.25)


def _rank_corr(a, b):
    if set(a) != set(b):
        raise ValueError("HOLD_PAIR_MATCHING_MISMATCH")
    keys = sorted(a)
    n = len(keys)
    r0 = {key:rank for rank, key in enumerate(sorted(keys, key=lambda k:(a[k], k)))}
    r1 = {key:rank for rank, key in enumerate(sorted(keys, key=lambda k:(b[k], k)))}
    return 1-6*sum((r0[k]-r1[k])**2 for k in keys)/(n*(n*n-1))


def relative_pair_indices(s):
    if "wide" not in s or len(s["wide"]) != 136:
        raise ValueError("HOLD_MISSING_FULL_WIDE_GRID")
    raw = {pair: 1/o for pair, o in s["wide"].items()}
    mass = sum(raw.values())
    qwide = {k:v/mass for k,v in raw.items()}
    qwin_pair = pl_pair_top3_index(s["win"])
    if set(qwide) != set(qwin_pair):
        raise ValueError("HOLD_MISMATCHED_WIDE_WIN_PAIR_UNIVERSE")
    residual = {k:math.log(qwide[k]/qwin_pair[k]) for k in qwide}
    return {
        "label":s["label"], "pair_residual":residual,
        "observed_pair_odds":s["wide"], "model_pair_index":qwin_pair,
        "observed_relative_pair_index":qwide,
        "source_pool_time_aligned":False,
    }


def compare(a, b):
    keys = sorted(a["pair_residual"])
    if keys != sorted(b["pair_residual"]):
        raise ValueError("HOLD_UNMATCHED_PAIRS")
    values = []
    for pair in keys:
        delta = b["pair_residual"][pair]-a["pair_residual"][pair]
        observed_quote_move = math.log(
            b["observed_pair_odds"][pair]/a["observed_pair_odds"][pair])
        win_model_quote_move = math.log(
            a["model_pair_index"][pair]/b["model_pair_index"][pair])
        values.append((pair,delta,observed_quote_move,win_model_quote_move))
    magnitudes = [abs(row[1]) for row in values]
    return {
        "from":a["label"], "to":b["label"],
        "pair_count":len(keys),
        "mean_absolute_cross_pool_log_ratio_change":mean(magnitudes),
        "median_absolute_cross_pool_log_ratio_change":median(magnitudes),
        "residual_rank_spearman":_rank_corr(a["pair_residual"],b["pair_residual"]),
        "displayed_wide_quote_rank_spearman":_rank_corr(
            a["observed_pair_odds"],b["observed_pair_odds"]),
        "pairs_with_cross_pool_residual_ratio_change_at_least_25pct":
            sum(x > LOG25 for x in magnitudes),
        "pairs_with_observed_quote_and_winPL_expected_quote_opposite_signed_change":
            sum(observed*expected < 0 for _,_,observed,expected in values),
        "largest_abs_cross_pool_residual_changes":[
            {"pair":list(pair),
             "log_index_change":delta,
             "before_wide_lower_quote":a["observed_pair_odds"][pair],
             "after_wide_lower_quote":b["observed_pair_odds"][pair]}
            for pair,delta,_,_ in sorted(values,key=lambda x:-abs(x[1]))[:8]
        ],
        "pair_observations_are_not_independent_races":True,
        "25pct_log_ratio_cutoff_is_descriptive_not_predictive_threshold":True,
        "contemporaneous_venue_bettor_updating_identified":False,
    }


def audit():
    s=load_snapshots(read_locked())
    panels = [relative_pair_indices(v) for v in s if "wide" in v]
    contrasts=[compare(panels[i],panels[i+1])
               for i in range(len(panels)-1)]
    return {
        "status":STATUS,
        "data":"2026-10-18 Kyoto 11R, 136 overlapping wide pairs × 3 archived quote groups",
        "four_horse_win_snapshots_exist_but_wide_only_at_last_three":True,
        "underlying_per_pool_quote_update_times_verified":False,
        "observed_win_and_wide_pool_capture_times_aligned":False,
        "pair_index_is_not_event_probability":True,
        "normalization":"inverse wide lower quote across 136 pairs vs 1/3 Plackett-Luce both Top3 model probability",
        "cross_pool_pair_contrasts":contrasts,
        "scientific_conclusion":"DESCRIPTIVE_NON_IDENTIFICATION_NOT_FORECAST_ABILITY",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=Path("tmp/odds-cross-pool-index.json"))
    args=parser.parse_args()
    r=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":r["status"],"results":[{
        "from":v["from"],"to":v["to"],
        "pairs_delta_over_25pct":v["pairs_with_cross_pool_residual_ratio_change_at_least_25pct"],
        "rank_corr":v["residual_rank_spearman"]
    } for v in r["cross_pool_pair_contrasts"]]},ensure_ascii=False))


if __name__=="__main__":
    main()
