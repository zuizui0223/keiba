#!/usr/bin/env python3
"""NO JRA DATA: synthetic race, horse random-effect posterior -> ABM/PDE -> voters.

Publishes only fake aggregate results, not real horse identifiers or
per-ticket odds. The local source clocks are invented; this is
an executable falsification/demo of the model's information hierarchy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from keiba_individual_trait_market_demo import toy_data
from keiba_trait_uncertainty_ensemble import propagate_individual_uncertainty


def toy_experiment(draws=20,physical_draws=80,seed=20261026):
    if draws<2:
        raise ValueError("HOLD_TOO_FEW_SYNTHETIC_UNCERTAINTY_DRAWS")
    source,target,odds=toy_data()
    # Counterfactual social reliance: early stages receive mostly
    # objective information; the assumed herding fraction rises.
    # This is an invented schedule, not a measured JRA fraction.
    mix=[
        {"fundamental":.60,"herding":.20,"informed":.20},
        {"fundamental":.45,"herding":.35,"informed":.20},
        {"fundamental":.25,"herding":.50,"informed":.25},
        {"fundamental":.15,"herding":.60,"informed":.25},
    ]
    def go(release,posterior=True,gamma=2.0):
        return propagate_individual_uncertainty(
            source,target,observed_first_odds=odds,
            posterior_draws=draws,physical_mc_draws=physical_draws,
            seed=seed,include_posterior_error=posterior,
            information_release_round=release,
            voter_shares_by_round=mix,
            herding_gamma=gamma,
        )
    early=go(1)
    late=go(3)
    never=go(5)
    point=go(3,False)
    g=late["uniform_equilibrium_gain_trace_not_real_criticality"]
    if not ([x["uniform_null_local_gain"]<1 for x in g[:2]]
            == [True,True]
            and abs(g[2]["uniform_null_local_gain"]-1)<1e-12
            and g[3]["uniform_null_local_gain"]>1):
        raise AssertionError("HOLD_INCORRECT_SYNTHETIC_GAIN_HIERARCHY")
    if not never["never_released_pairs_bitwise_identical"]:
        raise AssertionError("HOLD_INFORMATION_LEAK")
    if max(point["prior_across_trait_sd"])>1e-12:
        raise AssertionError("HOLD_PLUG_IN_PREDICTIVE_SPREAD")
    return {
        "status":"ARTIFICIAL_HORSE_TRAIT_AND_BETTOR_POPULATION_COHORT_ONLY",
        "real_market_or_animal_population_supported":False,
        "n_artificial_horses":len(target["horse_ids"]),
        "n_fabricated_repeated_races":7,
        "posterior_ensemble_draws":draws,
        "each_physical_ABM_draws":physical_draws,
        "underlying_GPS_trait_moments_ICC":
            late["source_conditional_moment_icc"],
        "reference_prior_market_odds_already_social":True,
        "double_counted_objective_before_fix":False,
        "same_pseudo_ballots_across_synthetic_counterfactuals":True,
        "uncertainty_effect":{
            "max_individual_prior_probability_sd":
                max(late["prior_across_trait_sd"]),
            "plug_in_without_uncertainty_max_probability_sd":
                max(point["prior_across_trait_sd"]),
            "expected_market_TV_pp_posterior":
                late["scenario_market_difference_TV_pp"],
            "expected_market_TV_pp_plug_in":
                point["scenario_market_difference_TV_pp"],
            "mean_objective_distribution_change_due_to_integrating_trait_error_TV_pp":
                50*sum(abs(a-b) for a,b in zip(
                  late["expected_objective_prior_under_trait_error"],
                  late["plug_in_objective_prior"])),
        },
        "social_info_release":{
            "round_1":early["scenario_market_difference_TV_pp"],
            "round_3":late["scenario_market_difference_TV_pp"],
            "never":never["scenario_market_difference_TV_pp"],
            "no_information_final_markets_equal":
                never["never_released_pairs_bitwise_identical"],
        },
        "uniform_FIXED_POINT_ONLY_social_gain_path":g,
        "price_threshold_discovery":None,
        "real_JRA_bettor_type_fractions":"UNKNOWN",
        "real_RQ_and_JRA_shared_horse_ids":"NONE_VERIFIED",
        "source_clock_external_attestation":"NOT_VERIFIED",
        "research_interpretation":"NEGATIVE_CONTROLS_AND_REPRODUCIBLE_SYNTHETIC_METHOD_ONLY"
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--draws",type=int,default=20)
    ap.add_argument("--horse-draws",type=int,default=80)
    ap.add_argument("--seed",type=int,default=20261026)
    a=ap.parse_args()
    o=toy_experiment(draws=a.draws,physical_draws=a.horse_draws,seed=a.seed)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(o,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
