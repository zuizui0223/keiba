#!/usr/bin/env python3
"""Ecological/network research: node vs dyadic market-information decomposition.

Uses nine historical race *cross sections* already archived in keiba.
It does not place bets, request live odds, infer herding from one timestamp,
identify genetic effects, or relabel posthoc outcomes as independent tests.

For the complete wide pair graph, y_ij = log(qwide_ij / pPLwide_ij).
Weighted least squares: y_ij ~= a_i + a_j (horse-level components).
The residual e_ij = y_ij - a_i - a_j is pair-specific *quoted price*
structure, NOT evidence of an actual biological horse-horse interaction.

Descriptive null: permute the edge scores across graph positions, keeping
horse graph and PL-based edge weights fixed. Controls dimensionality and
background nonuniform weights; not an inferential null for pari-mutuel voting.
Optional retrospective log-loss contrasts are for research diagnostics only.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import permutations
import hashlib
import json
import math
from pathlib import Path
import random

try:
    from scripts.ticket_type_models import predict_tickets
    from scripts.ticket_type_historical_audit import (
        ROOT, SOURCE_DATE, TARGET_RACES, market_race, read_json,
        direct_own_market,
    )
    from scripts.ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, OFFICIAL_TOP3_PATH,
        eligible_four_market_only,
    )
except ModuleNotFoundError:
    from ticket_type_models import predict_tickets
    from ticket_type_historical_audit import (
        ROOT, SOURCE_DATE, TARGET_RACES, market_race, read_json,
        direct_own_market,
    )
    from ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, OFFICIAL_TOP3_PATH,
        eligible_four_market_only,
    )

GRAPH_ALPHA = .5  # illustration uses already inspected historical design
PERMUTATIONS_PER_RACE = 199
PROBABILITY_SOURCE = "inverse_geometric_midpoint_wide_quote_PROXY_NOT_TRUTH"


def _solve(mat: list[list[float]], rhs: list[float]) -> list[float]:
    """Small positive-definite least-squares system, partial pivoting."""
    n = len(rhs)
    rows = [list(row) + [rhs[i]] for i, row in enumerate(mat)]
    if any(len(row) != n + 1 for row in rows):
        raise ValueError("bad_node_matrix")
    for j in range(n):
        pivot = max(range(j, n), key=lambda i: abs(rows[i][j]))
        rows[j], rows[pivot] = rows[pivot], rows[j]
        val = rows[j][j]
        if not math.isfinite(val) or abs(val) <= 1e-14:
            raise ValueError("singular_or_invalid_node_design")
        for k in range(j, n + 1):
            rows[j][k] /= val
        for i in range(j + 1, n):
            mul = rows[i][j]
            for k in range(j, n + 1):
                rows[i][k] -= mul * rows[j][k]
    result = [0.] * n
    for i in range(n - 1, -1, -1):
        result[i] = rows[i][n] - math.fsum(
            rows[i][k] * result[k] for k in range(i + 1, n)
        )
    return result


def decompose_edges(values: dict[tuple[int, int], float],
                    weights: dict[tuple[int, int], float]) -> dict:
    if not values or set(values) != set(weights):
        raise ValueError("edge_values_weights_mismatch")
    nodes = sorted(set(n for edge in values for n in edge))
    n = len(nodes)
    if not 8 <= n <= 18 or len(values) != n * (n - 1) // 2:
        raise ValueError("pair_graph_not_complete")
    if set(values) != {
        (i, j) for i in nodes for j in nodes if i < j
    }:
        raise ValueError("unordered_pair_orientation_invalid")
    index = {node: k for k, node in enumerate(nodes)}
    mat = [[0.] * n for _ in nodes]
    vec = [0.] * n
    for (i, j), y in values.items():
        w = weights[(i, j)]
        if (isinstance(y, bool) or isinstance(w, bool) or
                not math.isfinite(y) or not math.isfinite(w) or w <= 0):
            raise ValueError("nonfinite_or_nonpositive_graph_input")
        a, b = index[i], index[j]
        mat[a][a] += w
        mat[b][b] += w
        mat[a][b] += w
        mat[b][a] += w
        vec[a] += w * y
        vec[b] += w * y
    fitted = _solve(mat, vec)
    nodescores = {node: fitted[index[node]] for node in nodes}
    predicted = {
        edge: nodescores[edge[0]] + nodescores[edge[1]]
        for edge in values
    }
    pair_residual = {edge: values[edge] - predicted[edge] for edge in values}
    norm = math.fsum(weights.values())
    mean = math.fsum(weights[edge] * y for edge, y in values.items()) / norm
    sst = math.fsum(weights[e] * (y - mean)**2 for e, y in values.items())
    sse = math.fsum(weights[e] * pair_residual[e]**2 for e in values)
    weighted_r2 = None if sst < 1e-20 else max(0., min(1., 1 - sse / sst))
    return {
        "node_effect": nodescores,
        "node_pred": predicted,
        "dyadic_residual": pair_residual,
        "edge_weighted_mean": mean,
        "R2_node_vs_constant": weighted_r2,
        "weighted_residual_rms": math.sqrt(sse / norm),
        "weighted_original_sd": math.sqrt(sst / norm),
        "residual_weighted_sum_orthogonality": {
            str(node): math.fsum(
                weights[edge] * pair_residual[edge]
                for edge in values if node in edge
            ) for node in nodes
        },
    }


def graph_inputs(strengths: dict[int, float], frames: dict[int, int],
                 quotes: list[dict]) -> tuple[dict, dict, dict]:
    baseline = predict_tickets(strengths, frames)
    if "wide" not in baseline:
        raise ValueError("wide_market_not_supported")
    pl = baseline["wide"]
    own, status = direct_own_market(quotes, "wide", set(pl),
                                     odds_position="geometric")
    if not own:
        raise ValueError("HOLD_" + status["status"])
    residuals = {
        e: math.log(own[e] / pl[e]) for e in pl
    }
    # One physically meaningful weighting: PL's implied wide-pair top3 mass.
    weights = {e: p / 3 for e, p in pl.items()}
    return residuals, weights, baseline


def joint_transferred_logloss(baseline: dict, frames: dict[int, int],
                              edge_adjustments: dict, true_top3: list[int],
                              alpha: float = GRAPH_ALPHA) -> float:
    """Exact joint likelihood, not a stake, payout, or ticket ROI."""
    triplets = baseline["trifecta"]
    true = tuple(true_top3)
    if true not in triplets:
        raise ValueError("wrong_result_top3")
    scores = {}
    for order, prior in triplets.items():
        edges = [
            tuple(sorted((order[0], order[1]))),
            tuple(sorted((order[0], order[2]))),
            tuple(sorted((order[1], order[2]))),
        ]
        if not set(edges) <= set(edge_adjustments):
            raise ValueError("missing_edge_adjustment")
        loglift = (alpha / 3) * math.fsum(edge_adjustments[e] for e in edges)
        scores[order] = prior * math.exp(loglift)
    norm = math.fsum(scores.values())
    if norm <= 0 or not math.isfinite(norm):
        raise ValueError("invalid_joint_tilt")
    probability = scores[true] / norm
    if not 0 < probability <= 1:
        raise ValueError("invalid_joint_probability")
    return -math.log(probability)


def permutation_reference(values: dict, weights: dict, *,
                          seed: int, n_perm: int = PERMUTATIONS_PER_RACE) -> dict:
    if type(n_perm) is not int or n_perm < 19 or n_perm > 999:
        raise ValueError("invalid_permutation_count")
    actual = decompose_edges(values, weights)["R2_node_vs_constant"]
    if actual is None:
        return {"status": "HOLD_CONSTANT_PAIR_RESIDUAL", "repetitions": n_perm}
    rng = random.Random(seed)
    keys = sorted(values)
    original = [values[k] for k in keys]
    nulls = []
    for _ in range(n_perm):
        shuffled = list(original)
        rng.shuffle(shuffled)
        fit = decompose_edges(dict(zip(keys, shuffled)), weights)
        if fit["R2_node_vs_constant"] is None:
            raise ValueError("unexpected_constant_permutation")
        nulls.append(fit["R2_node_vs_constant"])
    nulls.sort()
    return {
        "status": "DESCRIPTIVE_EDGE_LABEL_PERMUTATION_NOT_A_VOTER_NULL",
        "repetitions": n_perm,
        "actual_node_R2": actual,
        "shuffled_median_node_R2": nulls[len(nulls)//2],
        "shuffled_q05_node_R2": nulls[int(.05*(len(nulls)-1))],
        "shuffled_q95_node_R2": nulls[int(.95*(len(nulls)-1))],
        "actual_minus_shuffled_median": actual - nulls[len(nulls)//2],
        "fraction_shuffled_at_least_actual_DESCRIPTIVE":
            sum(x >= actual for x in nulls) / len(nulls),
        "inferential_p_value": None,
    }


def one_race(*, date: str, race_id: str, venue: str,
             strengths: dict[int, float], frames: dict[int, int],
             wide_quotes: list[dict], top3: list[int], seed: int) -> dict:
    residuals, weights, base = graph_inputs(strengths, frames, wide_quotes)
    proj = decompose_edges(residuals, weights)
    eq = decompose_edges(residuals, {edge: 1. for edge in residuals})
    null = permutation_reference(residuals, weights, seed=seed)
    losses = {
        "win_only_PL": -math.log(base["trifecta"][tuple(top3)]),
        "node_only": joint_transferred_logloss(
            base, frames, proj["node_pred"], top3),
        "dyad_only": joint_transferred_logloss(
            base, frames, proj["dyadic_residual"], top3),
        "node_plus_dyad": joint_transferred_logloss(
            base, frames, residuals, top3),
    }
    return {
        "date": date, "race_id": race_id, "venue": venue,
        "horse_count": len(strengths), "pair_count": len(residuals),
        "node_effects_parameter_count": len(strengths),
        "weighted_node_explained_fraction_R2": proj["R2_node_vs_constant"],
        "equal_edge_weight_node_R2_sensitivity": eq["R2_node_vs_constant"],
        "weighted_pair_only_RMS_log_odds_proxy": proj["weighted_residual_rms"],
        "weighted_crossmarket_logratio_SD": proj["weighted_original_sd"],
        "max_abs_node_orthogonality_error": max(
            abs(v) for v in proj["residual_weighted_sum_orthogonality"].values()),
        "edge_label_shuffle_reference": null,
        "retrospective_correct_order_log_losses": losses,
        "delta_loss_node_vs_PL": losses["node_only"] - losses["win_only_PL"],
        "delta_loss_pair_vs_PL": losses["dyad_only"] - losses["win_only_PL"],
        "delta_loss_full_vs_PL": losses["node_plus_dyad"] - losses["win_only_PL"],
        "delta_loss_pair_added_to_node": losses["node_plus_dyad"] - losses["node_only"],
        "not_genetic_kinship": True,
        "not_actual_horse_pair_behavior": True,
    }


def run_analysis() -> dict:
    hashes = {}
    official12 = read_json(ROOT / "data" / SOURCE_DATE / "official-results-final.json", hashes)
    races = []
    for k, race in enumerate(TARGET_RACES):
        x = market_race(race, hashes)
        if official12["races"][str(race)]["source_type"] != "JRA_official":
            raise ValueError("unverified_kyoto_result")
        top3 = official12["races"][str(race)]["positions"]
        races.append(one_race(
            date=SOURCE_DATE, race_id=x["race_id"], venue="京都",
            strengths={i: 1 / v for i, v in x["win_odds"].items()},
            frames=x["frames"], wide_quotes=x["markets"]["wide"],
            top3=top3, seed=20261123 + 100*k,
        ))
    raw18 = read_json(SAVED_SNAPSHOT_PATH, hashes)
    eligible18, summary18 = eligible_four_market_only(raw18)
    official18 = read_json(OFFICIAL_TOP3_PATH, hashes)
    result18 = {r["race_id"]: r for r in official18["official_results"]}
    if set(result18) != {x["race_id"] for x in eligible18}:
        raise ValueError("incomplete_18th_result_sources")
    for k, x in enumerate(eligible18):
        official = result18[x["race_id"]]
        if official["source_type"] != "JRA_official" or official["venue"] != x["venue"]:
            raise ValueError("unverified_other_day_result")
        races.append(one_race(
            date=SECOND_DATE, race_id=x["race_id"], venue=x["venue"],
            strengths=x["strengths"], frames=x["frames"],
            wide_quotes=x["wide_quotes"], top3=official["top3"],
            seed=20261125 + 100*k,
        ))
    if len(races) != 9:
        raise ValueError("wrong_race_count")
    by_date = {}
    keys = [
        "weighted_node_explained_fraction_R2",
        "equal_edge_weight_node_R2_sensitivity",
        "delta_loss_node_vs_PL", "delta_loss_pair_vs_PL",
        "delta_loss_full_vs_PL", "delta_loss_pair_added_to_node",
    ]
    for date in (SOURCE_DATE, SECOND_DATE):
        part = [r for r in races if r["date"] == date]
        by_date[date] = {
            "race_count": len(part),
            "mean_" + key: math.fsum(r[key] for r in part) / len(part)
            for key in keys
        }
        by_date[date]["races_node_R2_above_edge_shuffle_median"] = sum(
            r["edge_label_shuffle_reference"]["actual_minus_shuffled_median"] > 0
            for r in part
        )
        by_date[date]["races_dyad_addition_reduced_order_logloss"] = sum(
            r["delta_loss_pair_added_to_node"] < -1e-12 for r in part
        )
    return {
        "schema_version": 1,
        "status": "EMPIRICAL_QUOTE_NETWORK_DECOMPOSITION_POSTHOC_EXPLORATORY",
        "goal": "Distinguish node/horse-specific price-proxy structure from dyadic remainder within wide vs win PL",
        "source": PROBABILITY_SOURCE,
        "alpha": GRAPH_ALPHA,
        "weights": "win-PL-wide-marginal normalized to sum1; sensitivity equal-edge weights",
        "node_decomposition": "weighted OLS complete undirected pair graph y_ij~a_i+a_j",
        "edge_label_shuffles_per_race": PERMUTATIONS_PER_RACE,
        "outcomes_used_only_for_retrospective_score": True,
        "real_market_time_series_observed": False,
        "biological_pair_interactions_identified": False,
        "genealogical_horse_id_join_identified": False,
        "odds_true_probabilities_identified": False,
        "prospective_validation": False,
        "information_theory_mutual_information_estimated": False,
        "by_date": by_date,
        "races": races,
        "source_file_sha256": dict(sorted(hashes.items())),
        "important_limitation": (
            "A dyadic quote residual may be heterogeneous margins, takeout, favorite-longshot pricing, "
            "market choice, measurement bias or true pair opinions. Neither biological interactions "
            "nor trader social learning/causality can be inferred without repeat prices and IDs."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        data = run_analysis()
    except (KeyError, TypeError, ValueError, OSError, ZeroDivisionError, OverflowError) as exc:
        p.error(str(exc))
    body = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
