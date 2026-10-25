#!/usr/bin/env python3
"""R8 single next quote: horse ABM Monte Carlo repeatability, NOT new races.

Generate EVERY 13:26-source-only market forecast for five fixed seeds before
opening source-locked 13:44 q2. Market-only, momentum and WIDE-node predictions
must be identical across horse Monte Carlo seeds. The six physically linked
horse-bettor candidates can fluctuate with arbitrary synthetic Gumbel,
Brownian and voter uniforms. The single observed q2 is NOT six/seven new
independent observations. Actual JRA results/returns are never read.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from statistics import mean
import numpy as np

from keiba_r8_threepoint_conditional_shadow import (
    ROOT,WIN_FORECASTS,build_pre_1344_forecasts,validate_later_quote,
    _vector_from_proxy,win_proxy,
)

STATUS="ONE_RACE_REPEATED_SYNTHETIC_HORSE_VOTER_SEEDS_NOT_FORWARD_VALIDATION"


def audit(root=ROOT, *, n_seeds=5,horse_draws=120,seed=20261025):
    if type(n_seeds) is not int or not 2<=n_seeds<=20 or horse_draws<40:
        raise ValueError("HOLD_BAD_R8_SYNTHETIC_REPETITIONS")
    predictions=[
        build_pre_1344_forecasts(root,horse_draws=horse_draws,
                                 seed=seed+1009*k)
        for k in range(n_seeds)
    ]
    ids=predictions[0]["ids"]
    if any(x["ids"]!=ids for x in predictions):
        raise ValueError("HOLD_R8_HORSE_ROSTER_CHANGED_ACROSS_SEEDS")
    for name in WIN_FORECASTS:
        if not all(np.array_equal(x["candidate_indices"][name],
                                  predictions[0]["candidate_indices"][name])
                   for x in predictions):
            raise ValueError("HOLD_PRETARGET_MARKET_BENCHMARK_CHANGED_BY_MC_SEED")
    # Strict firewall: target loaded only after ALL synthetic forecast sets.
    third=validate_later_quote(root,prepared=predictions[0])
    target=_vector_from_proxy(win_proxy(third),ids)
    scores={}
    for name in predictions[0]["candidate_indices"]:
        errors=[
            float(50*np.sum(np.abs(
                x["candidate_indices"][name]-target)))
            for x in predictions
        ]
        scores[name]={
            "single_real_target_5seed_TV_mean_pp":mean(errors),
            "single_real_target_5seed_TV_min_pp":min(errors),
            "single_real_target_5seed_TV_max_pp":max(errors),
            "is_unchanging_market_only_or_WIDE_comparator":
                name in WIN_FORECASTS,
        }
    if any(not np.isclose(
            scores[name]["single_real_target_5seed_TV_max_pp"],
            scores[name]["single_real_target_5seed_TV_min_pp"],atol=1e-12)
           for name in WIN_FORECASTS):
        raise ValueError("HOLD_EXTERNAL_MARKET_TARGET_JITTER_ACROSS_SEEDS")
    return {
        "status":STATUS,
        "independent_real_next_quote_targets":1,
        "source_date":"2026-10-12",
        "target_from_same_provider_full_WIN_11_horses":True,
        "artificial_horse_bettor_seed_repetitions":n_seeds,
        "horse_simulated_draws_per_seed":horse_draws,
        "source_horse_history_was_retrieved_after_2026_target":True,
        "no_independent_future_market_generalization_proven":True,
        "real_bettor_vote_counts_or_JRA_race_outcomes_consumed":False,
        "by_fixed_candidate":scores,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds",type=int,default=5)
    p.add_argument("--horse-draws",type=int,default=120)
    p.add_argument("--output",type=Path,default=Path(
        "tmp/r8-threepoint-seed-only.json"))
    args=p.parse_args()
    r=audit(n_seeds=args.seeds,horse_draws=args.horse_draws)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({"status":r["status"],
                      "actual_next_market_targets":1,
                      "seed_count":r["artificial_horse_bettor_seed_repetitions"]},
                     ensure_ascii=False))


if __name__=="__main__":
    main()
