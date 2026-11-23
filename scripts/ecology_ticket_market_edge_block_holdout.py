#!/usr/bin/env python3
"""Horse-indexed price structure: balanced edge-block out-of-sample challenge.

Source: the same 9 observed races on 2 dates with complete win+wide cross
sections. Within a race, mask 40% of wide pairs and estimate horse-node price
offsets ONLY from the 60% training pairs. Compare on the exact same unseen
edges to (i) training-edge mean and (ii) a shared fourth-order smooth
win-popularity curve. A fixed weak ridge node is also examined.

This is a stronger internal edge-graph test than leave-one-pair-out, but still
not repeatability of a named horse across races or market time stamps. Horse
numbers are RACE-LOCAL indices, not longitudinal horse registry IDs. Training
sees other edges involving a test horse, and each random split reuses data.
Races and dates, not edges or splits, are the candidate future independent units.
No race outcome, vote, payout, genotype, pedigree or wagering outcome is used.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random

try:
    from scripts.ecology_ticket_information_graph import _solve, graph_inputs
    from scripts.ecology_ticket_market_smooth_null import feature_map
    from scripts.ticket_type_historical_audit import (
        SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from scripts.ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )
except (ImportError, ModuleNotFoundError):
    from ecology_ticket_information_graph import _solve, graph_inputs
    from ecology_ticket_market_smooth_null import feature_map
    from ticket_type_historical_audit import (
        SOURCE_DATE, TARGET_RACES, market_race, read_json,
    )
    from ticket_wide_second_day import (
        DATE as SECOND_DATE, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    )

STATUS = "OBSERVED_NINE_RACE_DISJOINT_EDGE_BLOCK_HOLDOUT_NOT_HORSE_REPEATS"
SEED = 20261123
N_SPLITS = 80
TRAIN_FRACTION = 0.60
NODE_RIDGE_SCALES = (0., 0.1)
MAX_SPLIT_ATTEMPTS = 200


def fit_weighted(features: dict, y: dict, weights: dict,
                 train: list[tuple[int, int]], *,
                 ridge: float = 0, center_y: bool = False) -> tuple:
    """WLS from training edges only, optional centered-response ridge.

    For node ridge, center the training response and add its training mean back
    to predictions. Thus a global normalization shift in the quoted win/wide
    ratio cannot alter held-out prediction errors.
    """
    if (not train or set(features) != set(y) or set(weights) != set(y) or
            type(ridge) not in (int, float) or not math.isfinite(ridge) or ridge < 0):
        raise ValueError("invalid_weighted_design")
    p = len(next(iter(features.values())))
    if p < 2 or p > 18 or len(train) <= p + 2:
        raise ValueError("train_graph_underidentified")
    train_mass = math.fsum(weights[e] for e in train)
    mean = math.fsum(weights[e] * y[e] for e in train) / train_mass if center_y else 0.
    mat = [[0.] * p for _ in range(p)]
    rhs = [0.] * p
    for edge in train:
        x = features[edge]
        w, z = weights[edge], y[edge] - mean
        if len(x) != p or not math.isfinite(w) or w <= 0 or not math.isfinite(z):
            raise ValueError("invalid_edge_or_weight")
        for a in range(p):
            rhs[a] += w * x[a] * z
            for b in range(p):
                mat[a][b] += w * x[a] * x[b]
    for i in range(p):
        mat[i][i] += ridge * train_mass / p
    coeff = _solve(mat, rhs)
    return coeff, mean


def predict(coeff: tuple, offset: float, feature: tuple) -> float:
    if len(coeff) != len(feature):
        raise ValueError("prediction_feature_mismatch")
    return offset + math.fsum(a * b for a, b in zip(coeff, feature))


def node_features(nodes: list[int]) -> dict[tuple[int, int], tuple]:
    n = len(nodes)
    ix = {i: j for j, i in enumerate(nodes)}
    return {(i, j): tuple(float(k in (ix[i], ix[j])) for k in range(n))
            for i in nodes for j in nodes if i < j}


def partition_edges(values: dict, rng: random.Random,
                    *, frac: float = TRAIN_FRACTION) -> tuple[list, list]:
    """Choose one design-blind split, independent of every observed edge price."""
    if not .3 <= frac <= .8:
        raise ValueError("invalid_train_fraction")
    all_edges = sorted(values)
    pool = list(all_edges)
    rng.shuffle(pool)
    ntrain = round(frac * len(pool))
    train, test = sorted(pool[:ntrain]), sorted(pool[ntrain:])
    if not train or not test or set(train) & set(test):
        raise ValueError("invalid_partition")
    counts = Counter(i for e in train for i in e)
    nodes = set(i for e in all_edges for i in e)
    if any(counts[node] < 3 for node in nodes):
        raise ValueError("insufficient_train_edges_per_horse")
    return train, test


def _sse(y,weights,pred,test):
    return math.fsum(weights[e]*(y[e]-pred[e])**2 for e in test)


def evaluate_partition(values: dict, weights: dict,
                       node_x: dict, global_x: dict,
                       train: list, test: list) -> dict:
    """All models see exactly the same train/test pairs and weights."""
    full = set(values)
    if (set(train) | set(test) != full or set(train) & set(test) or
            set(global_x) != full or set(node_x) != full):
        raise ValueError("wrong_split_support")
    mean_train = (
        math.fsum(weights[e] * values[e] for e in train) /
        math.fsum(weights[e] for e in train)
    )
    predictions = {"mean": {e: mean_train for e in test}}
    smooth_coef, smooth_off = fit_weighted(global_x, values, weights, train)
    predictions["global_polynomial4"] = {
        e: predict(smooth_coef, smooth_off, global_x[e]) for e in test
    }
    for lam in NODE_RIDGE_SCALES:
        node_coef, node_off = fit_weighted(
            node_x, values, weights, train,
            ridge=lam, center_y=(lam>0),
        )
        label = "node" if lam==0 else "node_ridge_0p1"
        predictions[label] = {
            e: predict(node_coef, node_off, node_x[e]) for e in test
        }
    errors = {
        model: _sse(values, weights, prediction, test)
        for model, prediction in predictions.items()
    }
    if errors["mean"] <= 1e-20:
        raise ValueError("test_prices_not_variable")
    return {
        "train_pair_count": len(train),
        "test_pair_count": len(test),
        "weighted_test_squared_error": errors,
        "relative_heldout_R2_vs_train_mean": {
            name: 1. - err/errors["mean"]
            for name, err in errors.items() if name != "mean"
        },
        "node_beats_global_smooth":
            errors["node"] < errors["global_polynomial4"],
        "node_ridge_beats_global_smooth":
            errors["node_ridge_0p1"] < errors["global_polynomial4"],
    }


def evaluate_race(race_id: str, date: str, strength: dict[int,float],
                  frames: dict[int,int], quotes: list[dict], *,
                  n_splits: int = N_SPLITS, seed: int = SEED) -> dict:
    if type(n_splits) is not int or n_splits < 8 or n_splits > 500:
        raise ValueError("invalid_repeated_split_count")
    y, weights, baseline = graph_inputs(strength,frames,quotes)
    horse_numbers = sorted(strength)
    node_x = node_features(horse_numbers)
    global_x = feature_map(strength,4)
    assert set(y) == set(node_x) == set(global_x)
    rng = random.Random(seed)
    reports = []
    retry = 0
    for _ in range(n_splits):
        success = False
        for _retry in range(MAX_SPLIT_ATTEMPTS):
            try:
                train, test = partition_edges(y,rng)
                record = evaluate_partition(y,weights,node_x,global_x,train,test)
            except ValueError:
                retry += 1
                continue
            reports.append(record)
            success = True
            break
        if not success:
            raise ValueError("HOLD_UNIDENTIFIED_GRAPH_SPLIT_NO_SELECTION_BY_PRICE")
    names = ("global_polynomial4","node","node_ridge_0p1")
    aggregate = {
        model: (
            1. -
            math.fsum(r["weighted_test_squared_error"][model] for r in reports) /
            math.fsum(r["weighted_test_squared_error"]["mean"] for r in reports)
        ) for model in names
    }
    pooled_sse = {
        model: math.fsum(r["weighted_test_squared_error"][model] for r in reports)
        for model in ("mean",) + names
    }
    return {
        "race_id":race_id,"date":date,
        "horse_count":len(horse_numbers),"complete_wide_pair_count":len(y),
        "repeated_splits":n_splits,
        "train_fraction":TRAIN_FRACTION,
        "train_pair_count_each_split":reports[0]["train_pair_count"],
        "test_pair_count_each_split":reports[0]["test_pair_count"],
        "extra_draws_to_find_full_identifiable_train_graph":retry,
        "pooled_heldout_R2_vs_train_mean":aggregate,
        "pooled_sse":pooled_sse,
        "fraction_partitions_node_better_than_global_smooth":
            sum(r["node_beats_global_smooth"] for r in reports)/n_splits,
        "fraction_partitions_ridge_node_better_than_global_smooth":
            sum(r["node_ridge_beats_global_smooth"] for r in reports)/n_splits,
        "fraction_partitions_node_ridge_better_than_unregularized_node":
            sum(r["weighted_test_squared_error"]["node_ridge_0p1"] <
                r["weighted_test_squared_error"]["node"] for r in reports)/n_splits,
        "test_pairs_can_share_horses_with_training":True,
        "named_horse_ID_repeatability_across_races_tested":False,
        "actual_odds_temporal_repeatability_tested":False,
        "not_independent_80_new_races":True,
    }


def run_analysis(n_splits: int=N_SPLITS) -> dict:
    sha={}
    results=[]
    for i,number in enumerate(TARGET_RACES):
        market=market_race(number,sha)
        results.append(evaluate_race(
            market["race_id"],SOURCE_DATE,
            {k:1./v for k,v in market["win_odds"].items()},
            market["frames"],market["markets"]["wide"],
            n_splits=n_splits,seed=SEED+1009*i,
        ))
    source18=read_json(SAVED_SNAPSHOT_PATH,sha)
    eligible,coverage=eligible_four_market_only(source18)
    for i,row in enumerate(eligible):
        results.append(evaluate_race(
            row["race_id"],SECOND_DATE,row["strengths"],
            row["frames"],row["wide_quotes"],
            n_splits=n_splits,seed=SEED+1009*(i+5),
        ))
    if len(results)!=9:
        raise ValueError("race_universe_not_nine")
    dates={}
    models=("global_polynomial4","node","node_ridge_0p1")
    for date in (SOURCE_DATE,SECOND_DATE):
        sub=[r for r in results if r["date"]==date]
        # Race, not split or pair, is the descriptive replication unit.
        dates[date]={
            "race_count":len(sub),
            **{f"mean_race_{m}_block_R2":
                math.fsum(r["pooled_heldout_R2_vs_train_mean"][m] for r in sub)/len(sub)
                for m in models},
            "races_node_beats_global4":sum(
                r["pooled_heldout_R2_vs_train_mean"]["node"] >
                r["pooled_heldout_R2_vs_train_mean"]["global_polynomial4"]
                for r in sub),
            "races_ridge_node_beats_global4":sum(
                r["pooled_heldout_R2_vs_train_mean"]["node_ridge_0p1"] >
                r["pooled_heldout_R2_vs_train_mean"]["global_polynomial4"]
                for r in sub),
        }
    return {
        "schema_version":1,"status":STATUS,
        "data_dates":[SOURCE_DATE,SECOND_DATE],
        "races":results,"by_date":dates,
        "data_starts_same_horses_across_dates_not_identifiable":True,
        "horse_number_not_stable_registry_id":True,
        "market_updates_multiple_times_per_race_not_established":True,
        "repetitions_per_race":n_splits,
        "sampling_train_fraction":TRAIN_FRACTION,
        "training_pair_split_blind_to_price_value":True,
        "null_global4_basis":"shared Legendre degree4 on normalized log win strength with common intercept",
        "node_unregularized":"one horse-index coefficient from training edges only",
        "node_ridge_sensitivity":"fixed penalty 0.1 on centered training log price pair deviations, no outcome tuning",
        "outcome_labels_used":False,
        "biological_individuality_identified":False,
        "human_social_feedback_identified":False,
        "new_horse_prediction":False,
        "new_date_or_race_validation":False,
        "source_file_sha256":dict(sorted(sha.items())),
        "limitation":"Repeated splits are strongly dependent. The effect is ability to interpolate unseen pairs involving the SAME race-local horse numbers, not a heritable/repeatable individual trait. Flexible common pricing curves and source-update confounding remain.",
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--splits",type=int,default=N_SPLITS)
    args=parser.parse_args()
    try:
        output=run_analysis(n_splits=args.splits)
    except (ValueError,TypeError,KeyError,OSError,OverflowError) as exc:
        parser.error(str(exc))
    raw=json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw,encoding="utf-8")
    else:
        print(raw,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
