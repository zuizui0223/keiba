#!/usr/bin/env python3
"""Decompose *quoted price-index* cross-pool differences by horse vs pair.

For two panels at a single race, define edge (i,j)
 y_ij = Delta log[(inverse observed wide LOWER quote / total across
 all wide pairs) / (P_PL(i and j both Top3 from same win-quote panel)/3)].

For a complete n-horse field, fit the *descriptive algebraic* decomposition
 y_ij = mu + a_i + a_j + epsilon_ij, constrained sum_i a_i=0.

The complete-graph least-squares solution has:
 mu = average edges y_ij
 a_i = sum_{j != i}(y_ij-mu)/(n-2).
The residual is pair-specific *relative to the selected additive price
model* and NOT a horse biological effect, bettor herding, residual trade
arbitrage, calibrated place probability or predictive power.

A leave-one-pair-out measure and a fixed-marginal edge-label-permutation
reference are also reported. Edges share horses, so neither pair holdout
nor label permutation supports a statistically independent 55/136 sample.

Reproduction:
 python scripts/odds_pair_hierarchy_decomposition.py --permutations 999 \
    --output tmp/odds-pair-hierarchy.json
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
import math
from pathlib import Path
import random
from statistics import mean

from odds_cross_pool_global_async import relative_pair_indices
from odds_r8_real_three_time_market import collect_pre_race_price_panels
from shuka2026_odds_information_hierarchy import load_snapshots, read_locked

STATUS = "OBSERVED_SINGLE_RACE_COMPLETE_PAIR_PRICE_DECOMPOSITION_DESCRIPTIVE_ONLY"
NONSAMPLE = "Pair edges share the same horse field; neither 55 nor 136 pairs are independent races."


def complete_graph_decompose(values):
    """Algebraic OLS over a complete undirected edge graph, no numpy."""
    if not isinstance(values, dict) or len(values) < 10:
        raise ValueError("HOLD_INCOMPLETE_OR_INVALID_PAIR_EDGE_MAP")
    keys = list(values)
    if any(not isinstance(k, tuple) or len(k) != 2 or
           not all(type(v) is int and v > 0 for v in k) or k[0] >= k[1]
           for k in keys):
        raise ValueError("HOLD_INVALID_UNORDERED_PAIR_KEY")
    vertices = sorted(set(v for k in keys for v in k))
    n = len(vertices)
    m = n*(n-1)//2
    if n < 5 or set(keys) != set(combinations(vertices, 2)):
        raise ValueError("HOLD_MISSING_COMPLETE_PAIR_GRAPH")
    if any(type(v) not in (float, int) or not math.isfinite(v)
           for v in values.values()):
        raise ValueError("HOLD_NONFINITE_PAIR_DELTAS")
    mu = mean(values.values())
    node = {i: 0.0 for i in vertices}
    for (a, b), y in values.items():
        node[a] += y-mu
        node[b] += y-mu
    for i in node:
        node[i] /= (n-2)
    prediction = {edge: mu + node[edge[0]]+node[edge[1]]
                  for edge in values}
    residual = {edge: values[edge]-prediction[edge] for edge in values}
    sst = sum((v-mu)**2 for v in values.values())
    sse = sum(v*v for v in residual.values())
    if sst < 1e-18:
        return {
            "status": "HOLD_NO_EDGE_LEVEL_VARIANCE_TO_DECOMPOSE",
            "n": n, "m": m,
            "intercept": mu, "node_effects": node,
            "pair_model_residuals": residual,
            "fitted_edge_values": prediction,
            "explained_fraction_of_edge_change_variance": None,
            "leave_one_pair_out_relative_squared_error_reduction": None,
            "total_edge_variance": sst,
            "pair_residual_sum_squared": sse,
        }
    if sse > sst + 1e-9:
        raise ValueError("HOLD_DECOMPOSITION_SSE_EXCEEDS_BASELINE")
    # For K_n, the intercept + n-1 node effects span n dimensions over
    # m edges. Symmetry => constant diagonal leverage h=n/m=2/(n-1).
    # Exact LOO OLS residual e_i/(1-h); intercept-only LOO residual
    # (y_i-mu)/(1-1/m). Compare total held-out squared errors.
    leverage = n/m
    loo_baseline = sst/((1-1/m)**2)
    loo_additive = sse/((1-leverage)**2)
    return {
        "status": "COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION",
        "n": n, "m": m, "intercept": mu,
        "node_effects": node, "pair_model_residuals": residual,
        "fitted_edge_values": prediction,
        "explained_fraction_of_edge_change_variance": 1-sse/sst,
        "pair_residual_fraction_of_edge_change_variance": sse/sst,
        "mean_abs_edge_change": mean(abs(v) for v in values.values()),
        "rmse_centered_raw_edge_changes": math.sqrt(sst/m),
        "rmse_pair_specific_residuals": math.sqrt(sse/m),
        "leave_one_pair_out_linear_model_leverage": leverage,
        "leave_one_pair_out_relative_squared_error_reduction":
            1-loo_additive/loo_baseline,
        "total_edge_variance": sst,
        "pair_residual_sum_squared": sse,
        "node_effects_sum_constraint": sum(node.values()),
        "max_abs_pair_model_residual_sum_per_horse": max(
            abs(sum(v for (a,b),v in residual.items() if i in (a,b)))
            for i in vertices),
        "independent_races_observed": 1,
    }


def permutation_edge_label_reference(observed, *, repetitions=999, seed=20261023):
    """Optional arithmetic reference: shuffle changes between fixed edges.

    The pairing exchangeability assumption is NOT valid for a formal
    empirical test: different pairs share animals, quote rounding and
    market probability dependencies. Only a structural sanity benchmark.
    """
    if repetitions < 99:
        raise ValueError("HOLD_TOO_FEW_PERMUTATION_REFERENCE_DRAW")
    original = complete_graph_decompose(observed)
    if original["explained_fraction_of_edge_change_variance"] is None:
        raise ValueError("HOLD_NO_VARIANCE_PERMUTATION_REFERENCE")
    pairs = sorted(observed)
    numbers = [observed[k] for k in pairs]
    rng = random.Random(seed)
    dist = []
    for _ in range(repetitions):
        rng.shuffle(numbers)
        z = complete_graph_decompose(dict(zip(pairs, numbers)))
        dist.append(z["explained_fraction_of_edge_change_variance"])
    ordered = sorted(dist)
    observed_r2 = original["explained_fraction_of_edge_change_variance"]
    return {
        "status": "ASSUMPTION_HEAVY_FIXED_EDGE_LABEL_PERMUTATION_REFERENCE_NOT_P_VALUE",
        "repetitions": repetitions, "seed": seed,
        "reference_mean_node_fit_fraction": mean(ordered),
        "reference_quantiles_05_50_95": [
            ordered[int((repetitions-1)*q)] for q in (.05,.5,.95)
        ],
        "fraction_shuffled_edge_assignments_with_node_fit_at_least_observed":
            sum(z >= observed_r2-1e-12 for z in dist)/repetitions,
        "no_formal_statistical_significance_or_causal_identification": True,
        "exchangeability_of_edges_not_defensible_without_model": True,
    }


def _paired_delta(before, after):
    a, b = before["pair_residual"], after["pair_residual"]
    if set(a) != set(b):
        raise ValueError("HOLD_DIFFERENT_PAIR_MARKETS")
    return {key:b[key]-a[key] for key in sorted(a)}


def _summarize(name, before, after, *, repetitions, seed,
               providers_and_clocks_comparable=False,
               audited_prices=False):
    edges = _paired_delta(before, after)
    fit = complete_graph_decompose(edges)
    null = permutation_edge_label_reference(edges,
                                             repetitions=repetitions,seed=seed)
    keep = sorted(edges, key=lambda p: -abs(fit["pair_model_residuals"][p]))[:10]
    return {
        "market_window": name,
        "n_horses": fit["n"], "number_of_overlapping_wide_events":fit["m"],
        "full_bet_quote_pages_same_provider_and_reported_update_minute":
            providers_and_clocks_comparable,
        "both_source_quote_panels_pre_race": audited_prices,
        "source_quote_update_minute_not_atomic_tote_transaction_time": True,
        "intercept_shared_market_index_shift": fit["intercept"],
        "observed_mean_abs_cross_pool_log_ratio_change":
            fit["mean_abs_edge_change"],
        "fraction_edge_change_variance_explained_by_additive_horse_terms":
            fit["explained_fraction_of_edge_change_variance"],
        "fraction_variance_remaining_pair_specific_after_horse_terms":
            fit["pair_residual_fraction_of_edge_change_variance"],
        "leave_one_pair_out_relative_squared_error_reduction":
            fit["leave_one_pair_out_relative_squared_error_reduction"],
        "permutation_reference":null,
        "node_effects_are_market_price_associations_not_biological_or_behavioral":
            True,
        "individual_horse_associated_price_index_terms": [
            {"horse_number":i,"additive_node_log_term":x}
            for i,x in sorted(fit["node_effects"].items(),
                              key=lambda z:-abs(z[1]))
        ],
        "largest_pair_specific_residuals_relative_to_additive_model": [
            {"pair":list(p),
             "raw_relative_pair_change":edges[p],
             "expected_from_shared_horse_terms":fit["fitted_edge_values"][p],
             "pair_specific_residual":fit["pair_model_residuals"][p]}
            for p in keep
        ],
        "selected_3_11_decomposition": (
            {"raw_pair_change":edges[(3,11)],
             "fitted_shared_horse_terms":fit["fitted_edge_values"][(3,11)],
             "remaining_pair_change":fit["pair_model_residuals"][(3,11)]}
            if (3,11) in edges else None
        ),
        "numerical_invariants":{
            "node_effects_sum":fit["node_effects_sum_constraint"],
            "largest_absolute_per_horse_sum_of_pair_residuals":
                fit["max_abs_pair_model_residual_sum_per_horse"],
        },
        "scientific_gates":{
            "true_focal_horse_or_pair_causal_effect":"HOLD_NO_WAGER_FLOW_OR_EXOGENOUS_EVENT",
            "independent_edge_replicates":"HOLD_PAIRS_SHARE_HORSES",
            "future_win_top3_additional_predictiveness":
                "HOLD_NO_INDEPENDENT_PROSPECTIVE_RESULT_TEST",
            "market_pair_price_index_is_event_probability":False,
            "cannot_infer_bettor_following_from_an_algebraic_fit":True,
        },
    }


def audit(*, permutations=999,seed=20261023):
    # R8 source-locks pre-race pages and verifies that win and wide pages
    # have matching displayed source UPDATE minute at each of 2 snapshots.
    r8_panels, _, _, _, (before_win, after_win, before_wide, after_wide) = (
        collect_pre_race_price_panels()
    )
    r8_before = relative_pair_indices({
        "label":"r8_1326", "win":before_win, "wide":before_wide})
    r8_after = relative_pair_indices({
        "label":"r8_1344", "win":after_win, "wide":after_wide})
    r8 = _summarize(
        "2026-10-12_KYOTO_08_1326_to_1344",
        r8_before,r8_after,
        repetitions=permutations,seed=seed,
        providers_and_clocks_comparable=True,audited_prices=True)

    # Shuka distinct time/provider caveats: pair pages do NOT have
    # authoritative atomic JRA source times; this is lower-grade evidence.
    snaps = load_snapshots(read_locked())
    if len(snaps)!=4 or any("wide" not in x for x in snaps[1:]):
        raise ValueError("HOLD_ARCHIVED_SHUKA_PRICE_PANEL_INCOMPLETE")
    sh = [relative_pair_indices(s) for s in snaps[1:]]
    sections = [
        _summarize("2026-10-17_1537_to_2026-10-18_1142",
                   sh[0],sh[1],repetitions=permutations,
                   seed=seed+1),
        _summarize("2026-10-18_1142_to_1218",
                   sh[1],sh[2],repetitions=permutations,
                   seed=seed+2),
    ]
    return {
        "status":STATUS,
        "mathematical_decomposition":
            "Delta log(wide normalized inverse lower quote / win-PL both Top3 index)=market_mean+horse_i+horse_j+pair_error",
        "complete_graph_additive_node_estimator":
            "node_i=sum_other_pairs(y_ij-market_mean)/(n_horses-2)",
        "number_of_real_independent_races":2,
        "pair_sample_sizes_are_not_independent_replicates":True,
        "selected_r8":r8,
        "other_shuka_lower_provenance_comparisons":sections,
        "claims_not_supported":[
            NONSAMPLE,
            "Horse-associated price index coefficients are not individual horse abilities, herding or biological phenotypes.",
            "Pair-specific price-index errors are residuals relative to a chosen PL benchmark and additive graph model, not actual measured pair betting interactions.",
            "Permutation of graph edge values destroys dependencies and is only a mathematical reference, not a scientific null p value.",
            "Even leave-one-pair-out prediction measures fit within one observed race, not future race result prediction.",
            "Display update minute equality between two separate market pages does not certify same underlying tote transaction timestamp.",
            "No financial expected-value or positive return is established.",
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permutations",type=int,default=999)
    parser.add_argument("--seed",type=int,default=20261023)
    parser.add_argument("--output",type=Path,
                        default=Path("tmp/odds-pair-hierarchy.json"))
    args=parser.parse_args()
    r=audit(permutations=args.permutations,seed=args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    def short(x):
        return {
            "market_window":x["market_window"],
            "n_horses":x["n_horses"],
            "pairs":x["number_of_overlapping_wide_events"],
            "horse_additive_R2":x["fraction_edge_change_variance_explained_by_additive_horse_terms"],
            "leave_edge_out_R2":x["leave_one_pair_out_relative_squared_error_reduction"],
            "permutation_edge_reference_95":x["permutation_reference"]
                ["reference_quantiles_05_50_95"][2],
            "max_pair_specific_residual":
                x["largest_pair_specific_residuals_relative_to_additive_model"][0],
            "statistical_causal_claim":"HOLD",
        }
    print(json.dumps({
        "status":r["status"],
        "real_race_count":r["number_of_real_independent_races"],
        "r8":short(r["selected_r8"]),
        "shuka":[short(s) for s in r["other_shuka_lower_provenance_comparisons"]],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
