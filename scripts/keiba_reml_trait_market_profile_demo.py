#!/usr/bin/env python3
"""Pre-market race-fixed REML -> horse ABM/PDE -> 3-type market toy study.

Never reads any actual Racing Queensland GPS, JRA outcome, real votes,
or live prices. All 6 horses and 7 race histories are FABRICATED.
The 3 profile ratios form a NON-INFERENTIAL sensitivity design.
Source timestamps and rights in the toy input are fabricated too.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from keiba_individual_trait_market_demo import toy_data
from keiba_source_race_fixed_reml import (
    estimate_race_fixed_reml, leave_one_source_date_out_reml
)
from keiba_trait_uncertainty_ensemble import propagate_individual_uncertainty

STATUS="FULLY_ARTIFICIAL_RACE_REML_PROFILE_TO_HORSE_ABM_PDE_TO_SOCIAL_MARKET"


def run(*, trait_draws=12, horse_draws=65, seed=20261026):
    if (type(trait_draws) is not int or not (2<=trait_draws<=64)
            or type(horse_draws) is not int or not (40<=horse_draws<=500)
            or type(seed) is not int):
        raise ValueError("HOLD_SYNTHETIC_METHOD_BUDGET_INPUT")
    source,target,first_odds=toy_data()
    reml=estimate_race_fixed_reml(source,target)
    deletion=leave_one_source_date_out_reml(source,target)
    schedule=[
       {"fundamental":.60,"herding":.20,"informed":.20},
       {"fundamental":.45,"herding":.35,"informed":.20},
       {"fundamental":.25,"herding":.50,"informed":.25},
       {"fundamental":.15,"herding":.60,"informed":.25},
    ]
    results={}
    for name in ("low","central","high"):
        params=dict(
            observed_first_odds=first_odds,
            posterior_covariance_mode="race_contrast_covariance",
            source_variance_fit_mode="source_reml",
            reml_profile_scenario=name,
            posterior_draws=trait_draws,
            physical_mc_draws=horse_draws,
            seed=seed,
            voter_shares_by_round=schedule,
            herding_gamma=2.)
        informed=propagate_individual_uncertainty(
            source,target,information_release_round=3,**params)
        no_public=propagate_individual_uncertainty(
            source,target,information_release_round=5,**params)
        if not no_public["never_released_pairs_bitwise_identical"]:
            raise AssertionError("HOLD_FUTURE_HORSE_INFO_LEAK")
        if (informed["race_contrast_covariance_summary"]["hyperparameters"]
            ["source_only_orthogonal_race_contrast_reml"] is not True):
            raise AssertionError("HOLD_NOT_A_SOURCE_RACE_REML_VARIANCE_ESTIMATE")
        if not informed["conditional_race_contrast_covariance_used"]:
            raise AssertionError("HOLD_OFFDIAGONAL_HORSE_COVARIANCE_DROPPED")
        if no_public["scenario_market_difference_TV_pp"]["mean"]>1e-12:
            raise AssertionError("HOLD_NO_NEWS_MARKET_CONTRAST_NONZERO")
        results[name]={
          "source_horse_between_variance_seconds2":
              informed["race_contrast_covariance_summary"]["hyperparameters"]
              ["horse_between_variance_seconds2"],
          "source_absolute_noise_variance_seconds2":
              informed["race_contrast_covariance_summary"]["hyperparameters"]
              ["assumed_absolute_time_residual_variance_seconds2"],
          "max_horse_effect_offdiag_posterior_corr":
              informed["race_contrast_covariance_summary"]
              ["max_absolute_offdiagonal_effect_correlation"],
          "mean_market_crowding_effect_TV_pp":
              informed["scenario_market_difference_TV_pp"]["mean"],
          "effect_TV_q05_pp":
              informed["scenario_market_difference_TV_pp"]
              ["q05_across_scenario_draws"],
          "effect_TV_q95_pp":
              informed["scenario_market_difference_TV_pp"]
              ["q95_across_scenario_draws"],
          "no_public_information_market_effect_TV_pp":
              no_public["scenario_market_difference_TV_pp"]["mean"],
          "no_public_information_bitwise_equal":
              no_public["never_released_pairs_bitwise_identical"],
          "actual_market_predictive_superiority":
              informed["actual_market_predictive_superiority"],
          "probabilities_sum_to_one":
              abs(sum(informed["expected_final_market_with_crowding"])-1)<1e-11,
        }
    return {
      "status":STATUS,
      "n_fabricated_horses":len(target["horse_ids"]),
      "n_fabricated_prior_races":7,
      "fitted_from_only_prior_absolute_GPS_sectional_times":True,
      "original_market_q0_is_already_social_not_a_fundamental_prior":True,
      "fixed_source_variance_hyperparameter_uncertainty_not_integrated":True,
      "profile_range_not_a_population_CI":True,
      "source_race_fixed_REML":{
          "sigma_between_horse_seconds2":
              reml["horse_effect_variance_seconds_squared"],
          "sigma_absolute_noise_seconds2":
              reml["independent_absolute_time_error_variance_seconds_squared"],
          "conditional_icc_point":reml["conditional_icc_point"],
          "profile_gain_vs_no_horse_effect":
              reml["profile_improvement_vs_zero_horse_variance"],
          "horse_contrast_rank":reml["horse_contrast_rank"],
          "n_independent_race_contrasts":
              reml["n_independent_contrast_dimensions"],
      },
      "leave_one_source_date_out":{
          k:v for k,v in deletion.items() if k!="date_deletion_details"},
      "reml_profile_scenarios":results,
      "true_horse_variance_confirmed_from_data":False,
      "JRA_social_feedback_and_critical_odds_found":False,
      "actual_betting_expected_value":"HOLD",
      "real_RQ_and_JRA_horse_ID_mapping":"NONE_VERIFIED",
    }


def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--output",type=Path,required=True)
    arg.add_argument("--draws",type=int,default=12)
    arg.add_argument("--horse-draws",type=int,default=65)
    args=arg.parse_args()
    result=run(trait_draws=args.draws,horse_draws=args.horse_draws)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
