#!/usr/bin/env python3
"""One-race rounding/price-display sensitivity for cumulative market memory.

Actual JRA tote shares are not the normalized reciprocals of published odds.
Under a STYLIZED and deliberately unverified display rule
    o_i = floor_0.1(R / q_i), R=0.80, one winning horse,
the unobserved pool share q_i satisfies
    R/(o_i+0.1) <= q_i <= R/o_i, sum(q)=1.
This toy floor rule is NOT certified as the complete JRA live odds
display rule (special payouts, amendments, published timestamps, etc).

For two sets q0, q1 and a simple cumulative flow q1=(1-lambda)*q0+
lambda*b, b>=0, a conservative uniform necessary bound is
    lambda >= max_i(0,1-U1_i/L0_i).
The input is archived win odds only: none of these fractions are the
actual amounts bet or empirically validated behavioral herding.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from shuka2026_odds_information_hierarchy import load_snapshots, read_locked, share
from odds_market_accounting_null import conditional_identification

STATUS = "HYPOTHETICAL_WIN_ODDS_TRUNCATION_SENSITIVITY_NOT_VERIFIED_TOTE_SHARES"
SOURCE_FORMULA_URL = "https://www.jra.go.jp/kouza/baken/index.html"
RATE_SOURCE = "JRA publishes the win-bet nominal payout rate as 80%; exact time-specific odds-to-stakes inverse is not certified."
DISPLAY_MODEL = "HYPOTHESIS_ONLY_o_i_floor_to_0.1_of_R_div_q_i"
FLOOR_TICK = 0.1
RATE = 0.8


def _validate_odds(odds):
    if (not isinstance(odds, dict) or len(odds)<3 or
        any(not isinstance(i, int) or type(o) not in (int,float)
            or not math.isfinite(o) or o <= 1.0 for i,o in odds.items())):
        raise ValueError("HOLD_INVALID_FLOORED_QUOTE_VECTOR")
    if any(abs(o*10-round(o*10))>1e-7 for o in odds.values()):
        raise ValueError("HOLD_QUOTE_IS_NOT_ONE_DECIMAL")
    return odds


def hypothetical_share_intervals(odds, *, rate=RATE, tick=FLOOR_TICK):
    """Rates and quantization are sensitivity assumptions, not source-verified."""
    _validate_odds(odds)
    if not (0 < rate < 1 and tick > 0):
        raise ValueError("HOLD_INVALID_HYPOTHETICAL_PAYOUT_SETTINGS")
    ids=sorted(odds)
    lower={i:rate/(odds[i]+tick) for i in ids}
    upper={i:rate/odds[i] for i in ids}
    sum_lo=sum(lower.values())
    sum_hi=sum(upper.values())
    if sum_lo > 1 + 1e-10 or sum_hi < 1 - 1e-10:
        return {
            "status": "HOLD_DISPLAY_FLOOR_HYPOTHESIS_INCOMPATIBLE_WITH_TOTAL_POOL",
            "n":len(ids), "sum_lower":sum_lo, "sum_upper":sum_hi,
            "source_share_intervals":None,
        }
    # Tight coordinate endpoints from the sum-to-one constraint.
    lo={i:max(lower[i], 1-(sum_hi-upper[i])) for i in ids}
    hi={i:min(upper[i], 1-(sum_lo-lower[i])) for i in ids}
    if any(lo[i]>hi[i]+1e-10 for i in ids):
        raise ValueError("HOLD_HYPOTHETICAL_INTERVAL_INCONSISTENCY")
    qproxy=share(odds)
    inside=sum(lo[i]-1e-12<=qproxy[i]<=hi[i]+1e-12 for i in ids)
    return {
        "status":"HYPOTHETICAL_DISPLAY_FLOOR_SIMPLEX_FEASIBLE",
        "n":len(ids), "sum_lower":sum_lo, "sum_upper":sum_hi,
        "hypothetical_payout_rate":rate,
        "hypothetical_display_tick":tick,
        "source_share_intervals": {
            i:{"lower":lo[i],"upper":hi[i]} for i in ids},
        "direct_normalized_inverse_odds_proxy_coordinates_inside_floor_intervals":
            inside,
        "not_actual_bet_shares_or_certified_jra_inverse":True,
    }


def interval_lower_bound(earlier, later):
    if (earlier["source_share_intervals"] is None or
        later["source_share_intervals"] is None):
        return {"status":"HOLD_ONE_SNAPSHOT_FAILS_HYPOTHETICAL_ROUNDING"}
    a=earlier["source_share_intervals"]
    b=later["source_share_intervals"]
    if set(a)!=set(b):
        raise ValueError("HOLD_DIFFERENT_HORSE_SETS")
    # This is necessary for all valid latent shares, not asserted SHARP:
    # for any true q0 >= lower0, true q1 <= upper1.
    bounds={i:max(0,1-b[i]["upper"]/a[i]["lower"]) for i in a}
    critical=max(bounds,key=lambda i:(bounds[i],-i))
    v=bounds[critical]
    return {
        "status":"CONSERVATIVE_MATHEMATICAL_LOWER_BOUND_IN_STYLIZED_FLOOR_MODEL",
        "necessary_minimum_lambda_regardless_of_unobserved_rounding":v,
        "binding_horse_number":critical,
        "minimum_new_vs_previous_ratio_if_the_model_were_true":v/(1-v),
        "bound_not_proven_sharp":True,
        "not_a_lower_bound_on_real_JRA_wager_turnover":True,
    }


def audit():
    snaps=load_snapshots(read_locked())
    bound=[hypothetical_share_intervals(x["win"]) for x in snaps]
    periods=[]
    for j in range(len(snaps)-1):
        q0,q1=share(snaps[j]["win"]),share(snaps[j+1]["win"])
        previous=conditional_identification(q0,q1)
        assumed=interval_lower_bound(bound[j],bound[j+1])
        periods.append({
            "earlier":snaps[j]["label"], "later":snaps[j+1]["label"],
            "provider_changed":snaps[j]["provider"]!=snaps[j+1]["provider"],
            "proxy_lambda_min_exact_if_proxy_were_true":
                previous["minimum_new_fraction_of_final_pool_conditional_on_exact_share_proxy"],
            "alternative_hypothetical_floor_conservative":assumed,
        })
    return {
        "status":STATUS,
        "data":"ONE RACE, 2026-10-18 Kyoto 11R, four archived 17-horse price vectors",
        "source_formula_url":SOURCE_FORMULA_URL,
        "published_win_payout_rate":RATE,
        "rate_source_disclaimer":RATE_SOURCE,
        "display_rounding_rule_is_NOT_VERIFIED":True,
        "hypothetical_display_model":DISPLAY_MODEL,
        "actual_pool_totals_observed":False,
        "source_publisher_timestamps_fully_aligned":False,
        "snapshots":[
            {"label":s["label"],"provider":s["provider"],
             "sum_share_interval_lower":b["sum_lower"],
             "sum_share_interval_upper":b["sum_upper"],
             "hypothetical_model_status":b["status"],
             "out_of_17_inverse_odds_proxy_coordinates_consistent_with_floor_intervals":
                  b.get("direct_normalized_inverse_odds_proxy_coordinates_inside_floor_intervals"),
            } for s,b in zip(snaps,bound)
        ],
        "transitions":periods,
        "conclusion":"The previous reverse-odds new-vote percentage is proxy conditional, NOT a recovered flow; under a different hypothetical display inverse its necessary bound changes.",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=Path("tmp/odds-rounding-sensitivity.json"))
    args=parser.parse_args()
    report=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "intervals":[
            {"period":v["earlier"]+" -> "+v["later"],
             "proxy_min_pct":round(100*v["proxy_lambda_min_exact_if_proxy_were_true"],5),
             "floor_conservative_min_pct":round(
                100*v["alternative_hypothetical_floor_conservative"]
                   ["necessary_minimum_lambda_regardless_of_unobserved_rounding"],5)}
            for v in report["transitions"]],
        "real_total_wagers_observed":False,
        "display_rounding_rule_verified":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
