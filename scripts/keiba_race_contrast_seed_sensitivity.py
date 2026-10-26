#!/usr/bin/env python3
"""Multiple random-seed sensitivity of *artificial* race-contrast covariance.

Controls for a key confounding in the first comparison: using the old
independent individual-effect estimator changes BOTH posterior means
and correlations. Here the same race-contrast posterior mean, same
marginal variances, same synthetic markets, and the same standard-normal
draw seeds are used in two modes:

  A: marginal-independent draws with diagonal covariance only
  B: full joint conditional Gaussian draws with off-diagonal covariance

Thus the difference isolates the conditional covariance assumption
within the fixed synthetic Gaussian model; it does NOT identify a
real effect on market wagers or a critical odds price. Each seed is
a simulation replicate, never an independently observed race.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from keiba_individual_trait_market_demo import toy_data
from keiba_trait_uncertainty_ensemble import propagate_individual_uncertainty


def mean(xs):
    return float(sum(xs)/len(xs))


def run(*, n_seeds=8, posterior_draws=12, horse_draws=60,
        base_seed=20261026):
    if (type(n_seeds) is not int or not 2 <= n_seeds <= 32
            or type(posterior_draws) is not int or not 2 <= posterior_draws <= 64
            or type(horse_draws) is not int or horse_draws < 40
            or type(base_seed) is not int):
        raise ValueError("HOLD_INVALID_ARTIFICIAL_SEED_DESIGN")
    source,target,odds=toy_data()
    schedule=[
      {"fundamental":.60,"herding":.20,"informed":.20},
      {"fundamental":.45,"herding":.35,"informed":.20},
      {"fundamental":.25,"herding":.50,"informed":.25},
      {"fundamental":.15,"herding":.60,"informed":.25},
    ]
    rows=[]
    for idx in range(n_seeds):
        seed=base_seed+173*idx
        opts=dict(
          observed_first_odds=odds,
          posterior_draws=posterior_draws,
          physical_mc_draws=horse_draws,seed=seed,
          information_release_round=3,
          herding_gamma=2.0,
          voter_shares_by_round=schedule)
        diagonal=propagate_individual_uncertainty(
          source,target,posterior_covariance_mode=
          "race_contrast_marginal_independent",**opts)
        correlated=propagate_individual_uncertainty(
          source,target,posterior_covariance_mode=
          "race_contrast_covariance",**opts)
        if diagonal["plug_in_objective_prior"]!=correlated["plug_in_objective_prior"]:
            raise AssertionError("HOLD_POSTERIOR_MOMENTS_CHANGED_WITH_CORRELATION_ONLY")
        if diagonal["race_contrast_covariance_summary"]!=correlated["race_contrast_covariance_summary"]:
            raise AssertionError("HOLD_HYPERPARAMETERS_CHANGED_ACROSS_SIM_ARMS")
        if diagonal["initial_market_proxy"]!=correlated["initial_market_proxy"]:
            raise AssertionError("HOLD_INITIAL_MARKET_CHANGED_ACROSS_SIM_ARMS")
        if not (diagonal["has_outcome_data"] is False
                and correlated["has_outcome_data"] is False):
            raise AssertionError("HOLD_LEAKED_JRA_TARGET_FINISH")
        d=diagonal["scenario_market_difference_TV_pp"]["mean"]
        c=correlated["scenario_market_difference_TV_pp"]["mean"]
        rows.append({
          "seed":seed,
          "market_change_due_to_crowding_pp_diagonal":d,
          "market_change_due_to_crowding_pp_full_covariance":c,
          "full_minus_diagonal_pp":c-d,
          "max_prior_sd_diagonal":max(diagonal["prior_across_trait_sd"]),
          "max_prior_sd_full_covariance":max(correlated["prior_across_trait_sd"]),
          "posterior_horse_effect_max_offdiag_correlation":
              correlated["race_contrast_covariance_summary"]
              ["max_absolute_offdiagonal_effect_correlation"]
        })
    diffs=[r["full_minus_diagonal_pp"] for r in rows]
    base=[r["market_change_due_to_crowding_pp_diagonal"] for r in rows]
    full=[r["market_change_due_to_crowding_pp_full_covariance"] for r in rows]
    return {
      "status":"ARTIFICIAL_SEED_SENSITIVITY_GAUSSIAN_COVARIANCE_ONLY",
      "same_individual_posterior_means":True,
      "same_marginal_variances":True,
      "same_initial_market":True,
      "same_randomness_seed_per_paired_arm":True,
      "distinct_simulation_seeds_not_distinct_real_races":True,
      "n_fabricated_horses":len(target["horse_ids"]),
      "n_fabricated_history_races":7,
      "seeds_tested":n_seeds,
      "posterior_draws_each_seed":posterior_draws,
      "physical_mc_draws_each_posterior":horse_draws,
      "market_difference_diagonal_mean_pp":mean(base),
      "market_difference_full_covariance_mean_pp":mean(full),
      "covariance_only_mean_difference_pp":mean(diffs),
      "covariance_only_min_difference_pp":float(min(diffs)),
      "covariance_only_max_difference_pp":float(max(diffs)),
      "fraction_simulation_seeds_covariance_increased_crowd_effect":
          sum(x>1e-12 for x in diffs)/len(diffs),
      "fraction_simulation_seeds_covariance_decreased_crowd_effect":
          sum(x< -1e-12 for x in diffs)/len(diffs),
      "seed_level_aggregate_summaries":rows,
      "not_a_empirical_significance_test":True,
      "missing_betting_stakes_social_imitation_ground_weather":True,
      "confidence_or_credible_interval_for_actual_horses":"HOLD",
      "real_market_criticality":"HOLD"
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--seeds",type=int,default=8)
    ap.add_argument("--trait-draws",type=int,default=12)
    ap.add_argument("--horse-draws",type=int,default=60)
    args=ap.parse_args()
    report=run(n_seeds=args.seeds,posterior_draws=args.trait_draws,
               horse_draws=args.horse_draws)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
