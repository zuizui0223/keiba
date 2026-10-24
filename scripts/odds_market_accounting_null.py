#!/usr/bin/env python3
"""Partial identification of parimutuel share persistence, and a feedback-negative-control ABM.

One historical race, four archived pre-race quote snapshots. Actual cumulative
pool totals, bookmaker-like display rounding, exact market share, transaction
timing, and real bettor microdata are UNOBSERVED. These are conditional
calculations on *normalized reciprocal displayed win odds* as a proxy only.

For exact q0, q1 on the same fixed horse roster, a cumulative pool mechanism
q1 = (1-lambda) q0 + lambda b, with b any probability simplex vector,
has nonnegative inferred b iff
  lambda >= max_i (1 - q1_i / q0_i).
This is partial identification of a mathematical representation, NOT the
real fraction of wagers inferred from actual JRA quotes.

The mechanical-null simulation puts in independent UNIFORM new votes that
IGNORE displayed popularity; historical odds still predict future odds
mechanically. The herding comparison is fully synthetic, not fitted.

Run:
  python scripts/odds_market_accounting_null.py --paths 300 \
    --output tmp/market-accounting-null.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
from statistics import mean

from shuka2026_odds_information_hierarchy import (
    load_snapshots, read_locked, share, win_snapshot_summary,
)

STATUS = "CONDITIONAL_MARKET_SHARE_IDENTITY_AND_SYNTHETIC_NO_HERDING_COUNTEREXAMPLE"
RELATION = "q_next=(1-lambda)*q_prior+lambda*new_vote_distribution"
DATA_CAVEAT = (
    "Normalized inverse displayed win odds are not verified actual JRA pool "
    "shares; payout rules, truncation, source publication clock and pool total "
    "must be independently reconciled. No realized wager turnover is inferred."
)


def valid_share(q):
    if not isinstance(q, dict) or len(q) < 3:
        raise ValueError("HOLD_INVALID_MARKET_SHARE_VECTOR")
    if any(not isinstance(k, int) or type(v) not in (float, int)
           or not math.isfinite(v) or v <= 0 for k, v in q.items()):
        raise ValueError("HOLD_INVALID_MARKET_SHARE_VECTOR")
    if not math.isclose(sum(q.values()), 1.0, rel_tol=0, abs_tol=1e-10):
        raise ValueError("HOLD_SHARE_NOT_NORMALIZED")


def flow_witness(q0, q1, late_new_share):
    """Exact witness conditional on shares. Does not infer observed votes."""
    valid_share(q0)
    valid_share(q1)
    if set(q0) != set(q1) or not math.isfinite(late_new_share) or not (0 < late_new_share <= 1):
        raise ValueError("HOLD_INVALID_FLOW_WITNESS")
    b = {
        i: (q1[i]-(1-late_new_share)*q0[i])/late_new_share
        for i in q0
    }
    if min(b.values()) < -1e-10:
        raise ValueError("HOLD_FLOW_REQUIRES_NEGATIVE_NEW_VOTES")
    b = {i: max(0.0, v) for i, v in b.items()}
    if not math.isclose(sum(b.values()), 1.0, abs_tol=1e-9):
        raise ValueError("HOLD_IMPLIED_NEW_VOTES_NOT_NORMALIZED")
    return b


def conditional_identification(q0, q1):
    valid_share(q0)
    valid_share(q1)
    if set(q0) != set(q1):
        raise ValueError("HOLD_FIELD_DIFFERENCE")
    losses = {i: max(0.0, 1-q1[i]/q0[i]) for i in q0}
    biggest_drop_id = min(q0, key=lambda i: (q1[i]/q0[i], i))
    least = max(losses.values())
    tv = 0.5*sum(abs(q1[i]-q0[i]) for i in q0)
    if least + 1e-11 < tv:
        raise ValueError("HOLD_IDENTITY_INCONSISTENT_WITH_TV")
    if least >= 1.0:
        raise ValueError("HOLD_UNBOUNDED_FLOW_RATIO")
    witnesses = {}
    for label, w in (("near_minimum", least+1e-7),
                     ("midpoint", (1+least)/2),
                     ("all_new", 1.0)):
        if w > 1:
            w = 1.0
        votes = flow_witness(q0, q1, w)
        witnesses[label] = {
            "new_share_of_final_pool_assumed": w,
            "synthetic_new_share_favorite": votes[max(q0, key=q0.get)],
            "synthetic_new_share_biggest_decliner": votes[biggest_drop_id],
            "all_horses_nonnegative": all(x >= 0 for x in votes.values()),
            "sum_vote_shares": sum(votes.values()),
        }
    return {
        "accounting_identity": RELATION,
        "status": "EXACT_SIMPLEX_RELATION_APPLIED_TO_PRICE_DERIVED_PROXY",
        "total_variation_share_fraction": tv,
        "minimum_new_fraction_of_final_pool_conditional_on_exact_share_proxy": least,
        "minimum_new_to_previous_pool_ratio_conditional": least/(1-least),
        "largest_relative_share_decrease_horse_number": biggest_drop_id,
        "all_fractions_at_or_above_minimum_feasible_without_observing_bettors": True,
        "identifiability": "The observed q0,q1 alone give a LOWER BOUND, not lambda or a unique new-vote profile.",
        "three_distinct_feasible_unobserved_flow_explanations": witnesses,
        "cannot_estimate_actual_sales_or_herding": True,
    }


def _corr(a, b):
    av = mean(a)
    bv = mean(b)
    numerator = sum((x-av)*(y-bv) for x, y in zip(a, b))
    va = sum((x-av)**2 for x in a)
    vb = sum((x-bv)**2 for x in b)
    if va <= 0 or vb <= 0:
        return None
    return numerator/math.sqrt(va*vb)


def negative_control(q0, *, paths=300, seed=20261023,
                     prior_votes=10000, newly_cast_votes=1600,
                     gamma=1.25):
    """Simulate newcomers who pay NO ATTENTION to earlier quotes.

    Every vote is independent uniform in the null mechanism. Past quotes
    persist from *accounting* only. The alternative herding kernel is
    mathematically feedback-based; its strength is arbitrary and artificial.
    """
    valid_share(q0)
    if paths < 10 or prior_votes < 1 or newly_cast_votes < 1 or gamma <= 0:
        raise ValueError("HOLD_INVALID_SYNTHETIC_ABM_PARAMETERS")
    horses = sorted(q0)
    priors = [q0[i] for i in horses]
    prior_top5 = set(sorted(horses, key=lambda h: (-q0[h], h))[:5])
    fav = max(q0, key=q0.get)
    fav_pos = horses.index(fav)
    final_mass = prior_votes+newly_cast_votes
    retained_weight = prior_votes/final_mass
    experiments = {}
    for label in ("independent_uniform_new_votes", "herding_onto_current_popularity"):
        ending_favorite = []
        previous_corrs = []
        unchanged_top5 = 0
        actual_tv = []
        for p in range(paths):
            r = random.Random(seed+977*p)  # paired initial states, independent vote draws
            counts = [prior_votes*x for x in priors]
            if label == "independent_uniform_new_votes":
                for chosen in r.choices(range(len(horses)), k=newly_cast_votes):
                    counts[chosen] += 1
            else:
                for _ in range(newly_cast_votes):
                    probabilities = [x**gamma for x in counts]
                    chosen = r.choices(range(len(horses)), weights=probabilities, k=1)[0]
                    counts[chosen] += 1
            ending = [x/final_mass for x in counts]
            ending_favorite.append(ending[fav_pos])
            previous_corrs.append(_corr(priors, ending))
            top5 = set(horses[j] for j in
                       sorted(range(len(horses)), key=lambda j: (-ending[j], horses[j]))[:5])
            unchanged_top5 += top5 == prior_top5
            actual_tv.append(0.5*sum(abs(ending[j]-priors[j])
                                     for j in range(len(horses))))
        experiments[label] = {
            "mean_favorite_relative_weight_pct": 100*mean(ending_favorite),
            "mean_across_horse_prior_vs_final_share_Pearson": mean(previous_corrs),
            "fraction_final_market_top5_membership_unchanged": unchanged_top5/paths,
            "mean_initial_to_final_market_total_variation_pp": 100*mean(actual_tv),
        }
    independent_prediction = (retained_weight*priors[fav_pos]
                              +(1-retained_weight)/len(horses))
    return {
        "status": "SYNTHETIC_NO_HERDING_NEGATIVE_CONTROL_AND_ARBITRARY_HERDING_COMPARATOR",
        "synthetic_paths_per_mechanism": paths,
        "prior_fictional_total_votes": prior_votes,
        "new_fictional_votes": newly_cast_votes,
        "assumed_fraction_new_in_final": 1-retained_weight,
        "mechanical_fraction_of_initial_votes_retained": retained_weight,
        "assumed_no_herding_uniform_expected_favorite_pct": 100*independent_prediction,
        "independent_uniform_explanation": (
            "Incoming votes are iid uniform and never inspect q(t). "
            "Initial odds still persist in the cumulative denominator."
        ),
        "results": experiments,
        "observed_market_actual_turnover_inferred": False,
    }


def audit(*, paths=300, seed=20261023, root=None):
    snapshots = load_snapshots(read_locked() if root is None else read_locked(root))
    intervals = []
    for earlier, later in zip(snapshots, snapshots[1:]):
        q0, q1 = share(earlier["win"]), share(later["win"])
        intervals.append({
            "early": earlier["label"], "late": later["label"],
            "source_change": earlier["provider"] != later["provider"],
            "early_timestamp_semantics": earlier["timestamp_kind"],
            "late_timestamp_semantics": later["timestamp_kind"],
            **conditional_identification(q0, q1),
        })
    return {
        "status": STATUS,
        "market_data_scope": "2026-10-18 Kyoto 11R, 17 horses × four price vectors = one race",
        "formula_public_reference": "https://own.jra.jp/faq/pop03/1_17.html",
        "source_not_atomic_and_odds_not_actual_pool_shares": DATA_CAVEAT,
        "earliest_capture_is_not_opening_odds": True,
        "observed_intervals_conditional_on_proxy": intervals,
        "mechanical_memory_counterexample": negative_control(
            share(snapshots[0]["win"]), paths=paths, seed=seed),
        "inference_decision": {
            "social_herding_causal_effect": "HOLD_NONIDENTIFIED_FROM_CUMULATIVE_PRICES",
            "actual_new_pool_fraction": "HOLD_TOTAL_SALES_NOT_OBSERVED",
            "true_information_arrival_lag": "HOLD_SOURCE_TIMESTAMP_ALIGNMENT",
            "winner_top3_threshold_predictiveness": "HOLD_SINGLE_RACE_NO_PROSPECTIVE_TEST",
            "jra_direct_accounting_inverted": False,
            "v31_frozen_thresholds_changed": False,
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paths", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--output", type=Path,
                    default=Path("tmp/market-accounting-null.json"))
    args = ap.parse_args()
    report = audit(paths=args.paths, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "interval_bounds": [
            {"from": x["early"], "to": x["late"],
             "min_new_fraction_pct_conditional":
                100*x["minimum_new_fraction_of_final_pool_conditional_on_exact_share_proxy"]}
            for x in report["observed_intervals_conditional_on_proxy"]
        ],
        "synthetic": report["mechanical_memory_counterexample"],
        "actual_money_volume_inferred": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
