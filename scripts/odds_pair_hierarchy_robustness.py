#!/usr/bin/env python3
"""Audit price-range / PL-assumption sensitivity of horse/pair hierarchy.

2026-10-12 Kyoto 8R, a SINGLE archived pre-race betting market, 11 horses
and complete 55 wide quotes at 13:26 and 13:44 displayed-source minute.
The lower and upper WIDE payouts are EVENT-CONTINGENT conditional quotes,
not confidence intervals around a single observed price. Geometric mean
is a COUNTERFACTUAL mapping, not an actually obtainable payout. We vary
that mapping solely to assess dependence of the relative-price index.

We also vary PL intensity gamma: market weight_i = (1/win_odds_i)^gamma.
These gamma values are assumptions, NOT empirical confidence intervals.

The decomposition y_ij = intercept+node_i+node_j+pair_specific_ij
is algebraic in this complete graph. Its horse-node R2 is NOT the
percentage of bettor information explained and cannot identify imitation.

Artificial pair-independent and shared-horse Gaussian perturbations
are merely a mechanics reference, NOT formal null tests for JRA market
microstructure.

Command:
 python scripts/odds_pair_hierarchy_robustness.py \
     --synthetic-draws 500 --output tmp/odds-pair-robustness.json
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
import math
from pathlib import Path
import random
from statistics import mean

from odds_pair_hierarchy_decomposition import complete_graph_decompose
from odds_cross_pool_global_async import relative_pair_indices
from odds_r8_real_three_time_market import (
    collect_pre_race_price_panels, _locked, OTHER_SOURCE,
)

STATUS = "ONE_REAL_RACE_PAIR_HIERARCHY_ASSUMPTION_SENSITIVITY_NOT_VALIDATED_FORECAST"
GAMMAS = (0.75, 1.0, 1.25)
QUOTE_MAPPINGS = ("lower", "geometric", "upper")
SYNTHETIC_STATUS = "FICTIONAL_GAUSSIAN_EDGE_VS_NODE_SHOCKS_NOT_MARKET_GENERATIVE_PROOF"


def quote_mode(quote_row, *, mode):
    lo = quote_row["odds_low"]
    hi = quote_row["odds_high"]
    if (type(lo) not in (float,int) or type(hi) not in (float,int)
            or not math.isfinite(lo) or not math.isfinite(hi)
            or not (1.0 < lo <= hi)):
        raise ValueError("HOLD_BAD_WIDE_QUOTE_RANGE")
    if mode == "lower":
        return float(lo)
    if mode == "upper":
        return float(hi)
    if mode == "geometric":
        return math.sqrt(lo*hi)
    raise ValueError("HOLD_UNRECOGNIZED_COUNTERFACTUAL_WIDE_MAPPING")


def _to_full_pair_prices(quotes, n, mode):
    result = {}
    for row in quotes:
        pair = row["selection"]
        if (not isinstance(pair, list) or len(pair)!=2
                or any(type(i) is not int or not (1<=i<=n) for i in pair)
                or pair[0]==pair[1]):
            raise ValueError("HOLD_INVALID_PAIR_SELECTION")
        k = tuple(sorted(pair))
        if k in result:
            raise ValueError("HOLD_DUPLICATE_WIDE_PAIR")
        result[k] = quote_mode(row, mode=mode)
    if set(result)!=set(combinations(range(1,n+1),2)):
        raise ValueError("HOLD_INCOMPLETE_ALL_WIDE_PAIRS")
    return result


def _time_panel_from_immutable_sources():
    _,_,_,_,raw=collect_pre_race_price_panels()
    a_win,b_win,_,_=raw
    a = _locked(*OTHER_SOURCE["mid_wide"])
    b = _locked(*OTHER_SOURCE["late_all"])
    assert a["updated_at_jst"] == "2026-10-12T13:26:00+09:00"
    assert b["markets"]["wide"]["updated_at_jst"] == "2026-10-12T13:44:00+09:00"
    return a_win,b_win,a["quotes"]["wide"],b["markets"]["wide"]["quotes"]


def _delta_log_before_after(before, after):
    if set(before)!=set(after):
        raise ValueError("HOLD_MISMATCHED_PAIR_INDEX_KEYS")
    return {k:math.log(after[k]/before[k]) for k in before}


def _decompose_pair_indices(a, b):
    observed = _delta_log_before_after(
        a["observed_relative_pair_index"],b["observed_relative_pair_index"])
    modeled = _delta_log_before_after(
        a["model_pair_index"],b["model_pair_index"])
    cross = {k:observed[k]-modeled[k] for k in observed}
    return {
        "wide_raw_only":complete_graph_decompose(observed),
        "PL_model_pair_index_only":complete_graph_decompose(modeled),
        "wide_minus_PL_relative_index":complete_graph_decompose(cross),
    }


def _serialize_submodel(result):
    return {
        "horse_node_explained_fraction_of_pair_change_variance":
            result["explained_fraction_of_edge_change_variance"],
        "leave_one_pair_out_sse_reduction_fraction":
            result["leave_one_pair_out_relative_squared_error_reduction"],
        "horse_node_associated_terms_are_not_bettor_information":True,
        "pair_specific_log_index_residuals": {
            "3-11":result["pair_model_residuals"][(3,11)],
            "6-10":result["pair_model_residuals"][(6,10)],
        },
        "largest_abs_pair_residual": [
            list(max(result["pair_model_residuals"],
                     key=lambda edge:abs(result["pair_model_residuals"][edge]))),
            max(abs(z) for z in result["pair_model_residuals"].values())
        ],
    }


def synthetic_node_pair_noise(*, n=11, draws=500, seed=20261023,
                              node_sd=0.12, edge_sd=0.12):
    """Independent per-edge Gaussian vs shared-horse Gaussian-plus-edge.

    These are ad hoc numbers meant to demonstrate the role of
    graph dependency; they are not learned from any actual pool.
    """
    if (n<5 or draws<100 or node_sd<=0 or edge_sd<=0
            or any(not math.isfinite(v) for v in (node_sd,edge_sd))):
        raise ValueError("HOLD_SYNTHETIC_NOISE_ARGUMENTS")
    rng=random.Random(seed)
    pairs=list(combinations(range(1,n+1),2))
    out={}
    for model in ("independent_edge_shocks", "shared_horse_shocks_plus_edges"):
        r2=[]
        for _ in range(draws):
            horse = {
                i:rng.gauss(0,node_sd) if model=="shared_horse_shocks_plus_edges"
                else 0.0 for i in range(1,n+1)
            }
            edge={pair:horse[pair[0]]+horse[pair[1]]+rng.gauss(0,edge_sd)
                  for pair in pairs}
            r2.append(complete_graph_decompose(edge)[
                "explained_fraction_of_edge_change_variance"])
        ordered=sorted(r2)
        out[model]={
            "synthetic_draws":draws,
            "mean_horse_node_R2":mean(r2),
            "median_horse_node_R2":ordered[draws//2],
            "central_05_95_quantiles":[
                ordered[int(draws*.05)],ordered[min(draws-1,int(draws*.95))]],
        }
    return {
        "status":SYNTHETIC_STATUS,
        "source":"invented Gaussian graph-noise distributions, not tote odds",
        "random_seed":seed,
        "node_standard_deviation_arbitrary":node_sd,
        "pair_noise_standard_deviation_arbitrary":edge_sd,
        "results":out,
        "cannot_interpret_as_pvalue_or_empirical_noise_baseline":True,
        "same_graph_edges_share_horse_ids_not_independent_sample":True,
    }


def audit(*, synthetic_draws=500, seed=20261023):
    early_win,late_win,early_quote_rows,late_quote_rows = (
        _time_panel_from_immutable_sources())
    assert len(early_win)==len(late_win)==11
    samples=[]
    for gamma in GAMMAS:
        early_gamma={i:odds**gamma for i,odds in early_win.items()}
        late_gamma={i:odds**gamma for i,odds in late_win.items()}
        for mode in QUOTE_MAPPINGS:
            before=relative_pair_indices({
                "label":"r8_1326","win":early_gamma,
                "wide":_to_full_pair_prices(early_quote_rows,11,mode)})
            after=relative_pair_indices({
                "label":"r8_1344","win":late_gamma,
                "wide":_to_full_pair_prices(late_quote_rows,11,mode)})
            fits=_decompose_pair_indices(before,after)
            samples.append({
                "PL_gamma_hypothetical":gamma,
                "wide_quote_range_mapping_counterfactual":mode,
                "n_overlapping_pairs":55,
                "wide_raw_only":_serialize_submodel(fits["wide_raw_only"]),
                "PL_model_pair_index_only":_serialize_submodel(
                    fits["PL_model_pair_index_only"]),
                "wide_minus_PL_relative_index":_serialize_submodel(
                    fits["wide_minus_PL_relative_index"]),
            })
    keys=("horse_node_explained_fraction_of_pair_change_variance",
          "leave_one_pair_out_sse_reduction_fraction")
    baseline=next(x for x in samples if
                  x["PL_gamma_hypothetical"]==1.0 and
                  x["wide_quote_range_mapping_counterfactual"]=="lower")
    pair_signs = {}
    for pair in ("3-11","6-10"):
        vals=[
            row["wide_minus_PL_relative_index"]["pair_specific_log_index_residuals"][pair]
            for row in samples
        ]
        pair_signs[pair]={
            "all_nine_assumptions_have_same_sign":all(v>0 for v in vals) or all(v<0 for v in vals),
            "minimum_signed_log_pair_residual":min(vals),
            "maximum_signed_log_pair_residual":max(vals),
        }
    main=[r["wide_minus_PL_relative_index"] for r in samples]
    return {
        "status":STATUS,
        "source":"2026-10-12 Kyoto 8R, 13:26 to 13:44, full 11 win prices + 55 WIDE price ranges, source SHA verified",
        "number_of_independent_races":1,
        "scenarios":samples,
        "n_price_mapping_scenarios":len(samples),
        "PL_gamma_values_not_confidence_interval":list(GAMMAS),
        "wide_lower_upper_are_conditioned_payout_bounds_not_measurement_uncertainty":True,
        "geometric_mapping_is_not_observable_actual_wide_payout":True,
        "direct_PL_gamma1_lower_quote_decompositions":{
            key:baseline[key][keys[0]]
            for key in ("wide_raw_only","PL_model_pair_index_only",
                        "wide_minus_PL_relative_index")
        },
        "wide_minus_PL_horse_node_R2_min":min(row[keys[0]] for row in main),
        "wide_minus_PL_horse_node_R2_max":max(row[keys[0]] for row in main),
        "wide_minus_PL_leave_edge_out_R2_min":min(row[keys[1]] for row in main),
        "wide_minus_PL_leave_edge_out_R2_max":max(row[keys[1]] for row in main),
        "pair_residual_sign_stability":pair_signs,
        "invented_noise_reference":synthetic_node_pair_noise(
            draws=synthetic_draws,seed=seed),
        "inference_limits":[
            "Wide low/high conditional payouts are outcomes of an overlapping betting event, not independent measurement errors.",
            "PL gamma values and quote mappings are assumptions, not empirically fitted uncertainty bounds.",
            "Horse-only shared market price movement does not identify actual horse ability, bettor imitation, or information arrival.",
            "The PL pair benchmark itself has highly additive horse-node movement; subtracting it changes the model fit.",
            "Fixed-pair simulations do not turn 55 overlapping bets into 55 independent races.",
            "No forward independent race result score, threshold, causal effect or economic advantage is established.",
        ],
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--synthetic-draws",type=int,default=500)
    ap.add_argument("--seed",type=int,default=20261023)
    ap.add_argument("--output",type=Path,default=Path("tmp/odds-pair-robustness.json"))
    args=ap.parse_args()
    x=audit(synthetic_draws=args.synthetic_draws,seed=args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":x["status"],"real_races":x["number_of_independent_races"],
        "scenarios":x["n_price_mapping_scenarios"],
        "R2_three_components":x["direct_PL_gamma1_lower_quote_decompositions"],
        "R2_min":x["wide_minus_PL_horse_node_R2_min"],
        "R2_max":x["wide_minus_PL_horse_node_R2_max"],
        "signed_pairs":x["pair_residual_sign_stability"],
        "fictional_noise_reference":x["invented_noise_reference"]["results"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
