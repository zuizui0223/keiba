#!/usr/bin/env python3
"""Coherent ranking-probability *structure* from horse/pair price indices.

Input is a full, pre-race win quote vector plus previously *computed*
horse-associated and pair-specific price-index terms from two source
clock-matched win/wide panel captures.

Conditional 3-horse ordered rankings are reweighted as
  P_beta(i,j,k) ∝ P_PL(i,j,k) *
    exp[ beta_h*(a_i+a_j+a_k) +
         beta_p*(e_ij+e_ik+e_jk) ].

Since the same boost applies to all six permutations of any unordered
triple, this is a coherent joint-rank distribution. No independent
Top3/pair logits may violate the three-horse constraints.

IMPORTANT: beta_h and beta_p are NEVER estimated here. Examples use
explicitly invented coefficients for sensitivity only. No win, place,
wide or return advantage is established; this is not a validated wager
prediction or fitted horse behavior model.

Run source-gated one-race sensitivity:
  python scripts/odds_coherent_hierarchy_rank_bridge.py \
     --output tmp/coherent-market-hierarchy-bridge.json
"""
from __future__ import annotations

import argparse
from itertools import combinations, permutations
import json
import math
from pathlib import Path

from odds_cross_pool_global_async import relative_pair_indices
from odds_pair_hierarchy_decomposition import complete_graph_decompose
from odds_r8_real_three_time_market import collect_pre_race_price_panels

STATUS = "SYNTHETIC_COEFFICIENT_MARKET_HIERARCHY_COHERENT_RANK_MODEL_NOT_CALIBRATED"
BETA_SCENARIOS = {
    "market_PL_exact": (0.0, 0.0),
    "hypothetical_horse_layer_only": (0.5, 0.0),
    "hypothetical_pair_layer_only": (0.0, 0.5),
    "hypothetical_two_layer": (0.5, 0.5),
}


def joint_rank_probability(odds, horse_node, pair_residual, *,
                           beta_horse=0.0, beta_pair=0.0):
    """Compute exact 1st / Top2 / Top3 / wide pair / trio marginals.

    No outcome data, betting prices other than win odds, or horse GPS.
    All input keys are stable *horse numbers within one single race*.
    """
    if not isinstance(odds, dict) or len(odds)<5:
        raise ValueError("HOLD_INCOMPLETE_MARKET_RUNNER_FIELD")
    ids=sorted(odds)
    n=len(ids)
    if (any(type(k) is not int or k<=0 or
            type(odds[k]) not in (int,float) or
            not math.isfinite(odds[k]) or odds[k]<=1.0
            for k in ids) or
        set(horse_node)!=set(ids) or
        set(pair_residual)!=set(combinations(ids,2))):
        raise ValueError("HOLD_INVALID_ODDS_OR_HIERARCHICAL_TERMS")
    if any(type(v) not in (float,int) or not math.isfinite(v)
           for v in list(horse_node.values())+list(pair_residual.values())):
        raise ValueError("HOLD_NONFINITE_HIERARCHY_TERMS")
    if (not math.isfinite(beta_horse) or not math.isfinite(beta_pair) or
        max(abs(beta_horse),abs(beta_pair))>5):
        raise ValueError("HOLD_UNBOUNDED_HYPOTHETICAL_BETA")
    weights={i:1/odds[i] for i in ids}
    full=sum(weights.values())
    # Stable categorical softmax for all ordered first/second/third outcomes.
    rows=[]
    max_log=-math.inf
    for a in ids:
        wa=weights[a]
        for b in ids:
            if b==a:continue
            wb=weights[b]
            for c in ids:
                if c==a or c==b:continue
                wc=weights[c]
                key1,key2,key3=(
                    tuple(sorted((a,b))),tuple(sorted((a,c))),tuple(sorted((b,c))))
                logw = (math.log(wa/full) +
                        math.log(wb/(full-wa)) +
                        math.log(wc/(full-wa-wb)) +
                        beta_horse*(horse_node[a]+horse_node[b]+horse_node[c]) +
                        beta_pair*(pair_residual[key1]+pair_residual[key2]+
                                   pair_residual[key3]))
                if not math.isfinite(logw):
                    raise ValueError("HOLD_NONFINITE_ORDER_LOG_WEIGHT")
                rows.append((a,b,c,logw))
                max_log=max(max_log,logw)
    norm=sum(math.exp(z-max_log) for *_,z in rows)
    if not math.isfinite(norm) or norm<=0:
        raise ValueError("HOLD_ORDERED_TRIPLE_NORMALIZATION")
    p1={i:0.0 for i in ids}
    p2={i:0.0 for i in ids}
    p3={i:0.0 for i in ids}
    pair={k:0.0 for k in combinations(ids,2)}
    trio={k:0.0 for k in combinations(ids,3)}
    ordered_firsttwo={(a,b):0.0 for a in ids for b in ids if a!=b}
    ordered_top3_trifecta={}
    for a,b,c,z in rows:
        mass=math.exp(z-max_log)/norm
        p1[a]+=mass
        p2[a]+=mass
        p2[b]+=mass
        for i in (a,b,c):p3[i]+=mass
        for e in (tuple(sorted((a,b))),tuple(sorted((a,c))),
                  tuple(sorted((b,c)))):
            pair[e]+=mass
        trio[tuple(sorted((a,b,c)))]+=mass
        ordered_firsttwo[(a,b)]+=mass
        ordered_top3_trifecta[(a,b,c)]=mass
    epsilon=1e-9
    if not (math.isclose(sum(p1.values()),1,abs_tol=epsilon)
            and math.isclose(sum(p2.values()),2,abs_tol=epsilon)
            and math.isclose(sum(p3.values()),3,abs_tol=epsilon)
            and math.isclose(sum(pair.values()),3,abs_tol=epsilon)
            and math.isclose(sum(trio.values()),1,abs_tol=epsilon)
            and math.isclose(sum(ordered_firsttwo.values()),1,abs_tol=epsilon)
            and math.isclose(sum(ordered_top3_trifecta.values()),1,abs_tol=epsilon)):
        raise ValueError("HOLD_COHERENT_RANK_PROBABILITY_MASS")
    return {
        "status": STATUS,
        "horse_numbers":ids,
        "assumed_horse_layer_coefficient_not_fitted":beta_horse,
        "assumed_pair_layer_coefficient_not_fitted":beta_pair,
        "n_ordered_rankings":len(rows),
        "win":p1,
        "top2":p2,
        "top3":p3,
        "both_top3_pair":pair,
        "unordered_top3_trio":trio,
        "ordered_firsttwo_exacta":ordered_firsttwo,
        "ordered_top3_trifecta":ordered_top3_trifecta,
        "probabilities_properly_normalized_and_joint_rank_coherent":True,
    }


def _total_variation(q, r):
    if set(q)!=set(r):
        raise ValueError("HOLD_DIFFERENT_OUTCOME_UNIVERSE")
    return .5*sum(abs(q[i]-r[i]) for i in q)


def audit():
    price_panels, _, _, _, prices = collect_pre_race_price_panels()
    before_win, after_win, before_wide, after_wide=prices
    early=relative_pair_indices({"label":"r8_1326","win":before_win,
                                 "wide":before_wide})
    late=relative_pair_indices({"label":"r8_1344","win":after_win,
                                "wide":after_wide})
    edge_changes={
        k:late["pair_residual"][k]-early["pair_residual"][k]
        for k in early["pair_residual"]
    }
    fit=complete_graph_decompose(edge_changes)
    if (fit["status"]!="COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION"
            or fit["n"]!=11 or fit["m"]!=55):
        raise ValueError("HOLD_CANNOT_LINK_REAL_PRICE_HIERARCHY")
    hypothetical={}
    models={
        name:joint_rank_probability(
            after_win,fit["node_effects"],fit["pair_model_residuals"],
            beta_horse=coeff[0],beta_pair=coeff[1])
        for name,coeff in BETA_SCENARIOS.items()
    }
    baseline=models["market_PL_exact"]
    top_market_favorite=min(after_win,key=lambda i:(after_win[i],i))
    for key,forecasts in models.items():
        hypothetical[key]={
            "chosen_coefficients":{
                "horse":forecasts["assumed_horse_layer_coefficient_not_fitted"],
                "pair":forecasts["assumed_pair_layer_coefficient_not_fitted"],
            },
            "top_win_price_rank_horse_number":top_market_favorite,
            "top_win_price_rank_horse_win_probability":forecasts["win"][top_market_favorite],
            "top_win_price_rank_horse_top3_probability":forecasts["top3"][top_market_favorite],
            "pair_3_11_both_top3_probability":forecasts["both_top3_pair"][(3,11)],
            "market_shift_in_win_probability_distribution_TV":
                _total_variation(forecasts["win"],baseline["win"]),
            "market_shift_in_top3_horse_marginals_TV":
                _total_variation(forecasts["top3"],baseline["top3"]),
            "market_shift_in_both_top3_pair_probabilities_TV":
                _total_variation(forecasts["both_top3_pair"],
                                 baseline["both_top3_pair"]),
            "mass":{
                "one_first_place":sum(forecasts["win"].values()),
                "two_first_two_places":sum(forecasts["top2"].values()),
                "three_top3_inclusions":sum(forecasts["top3"].values()),
                "three_successful_wide_pairs":sum(
                    forecasts["both_top3_pair"].values()),
                "one_unordered_trio":sum(
                    forecasts["unordered_top3_trio"].values()),
                "one_ordered_trifecta":sum(
                    forecasts["ordered_top3_trifecta"].values()),
            },
        }
    return {
        "status":STATUS,
        "observational_source":"2026-10-12 Kyoto 8R source-locked 13:26 and 13:44 Yahoo win+wide public display panels",
        "only_independent_empirical_races":1,
        "market_benchmark":"PL exact ordered-triple ranking from archived later 11 win quotes",
        "observed_graph_price_index_horse_layer_fit_R2":
            fit["explained_fraction_of_edge_change_variance"],
        "top_winner_probability_model_did_not_use_official_result":True,
        "all_two_layer_coefficients_are_hypothetical_not_estimated":True,
        "scenarios":hypothetical,
        "formal_future_win_top3_forecast_skill":"HOLD_NO_PROSPECTIVE_HORSE_PANEL_AND_FREEZE",
        "warnings":[
            "The horse and pair terms are descriptive transformed market prices, not true horse traits or direct betting flows.",
            "The two β coefficients are invented; no horse-ability/crowding parameter or causal effect is estimated.",
            "Marginals of ranked finishes are coherent, but this does not establish real calibration of win, place, pair or trio probabilities.",
            "Comparing all bets for ROI requires separate historical final payouts and external calibration not supplied here.",
            "One source-locked race is insufficient to infer any forecast advantage, dynamic threshold or bookmaker arbitrage.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,
                   default=Path("tmp/coherent-market-hierarchy-bridge.json"))
    a=p.parse_args()
    report=audit()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "horse_additive_source_index_R2":report[
            "observed_graph_price_index_horse_layer_fit_R2"],
        "first_market_favorite_scenario_sensitivity":{
            name:{
                "favorite_win":v["top_win_price_rank_horse_win_probability"],
                "favorite_top3":v["top_win_price_rank_horse_top3_probability"],
                "pair_3_11":v["pair_3_11_both_top3_probability"],
                "ranking_masses":v["mass"],
            } for name,v in report["scenarios"].items()
        },
        "real_calibration":"HOLD",
    },ensure_ascii=False))


if __name__=="__main__":
    main()
