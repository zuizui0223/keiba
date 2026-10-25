#!/usr/bin/env python3
"""A complete artificial 6-horse race: repeated GPS -> social market.

All numeric horse histories and pseudo-votes are FABRICATED. This demo
reports only synthetic aggregate diagnostics. NOT evidence about real
horse personalities, official JRA odds, winners, or wagering income.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from keiba_individual_trait_to_market_cascade import (
    initial_market_proxy, local_market_gain, run_coupled_repeatability_trial,
    theoretical_gain,
)

IDS=[f"TOY_H{i}" for i in range(1,7)]


def toy_data():
    target={
        "source_system":"TOY_SYNTHETIC_PROVIDER_NOT_JRA",
        "horse_ids":IDS.copy(),
        "asof_jst":"2026-10-26T09:30:00+09:00",
        "initial_market_published_at_jst":"2026-10-26T08:45:00+09:00",
        "initial_market_received_at_jst":"2026-10-26T09:00:00+09:00",
        "first_marker_m":150,"distance_m":1200,"race_class":"TOY_GRADED",
    }
    true_trait=[-.48,-.32,-.14,.12,.33,.47]
    rows=[]
    for day in range(1,8):
        for k,i in enumerate(IDS):
            rows.append({
                "source_system":target["source_system"],
                "horse_id":i,
                "race_id":f"TOY_R{day}",
                "race_day":f"2026-10-0{day}T10:00:00+09:00",
                "received_at":f"2026-10-0{day}T12:00:00+09:00",
                "first_marker_m":150,"distance_m":1200,
                "race_class":"TOY_GRADED",
                "first_section_seconds":10.0+.12*day+true_trait[k]
                    +.08*((day+k*2)%5-2),
            })
    source={
        "schema":"KEIBA_SAME_HORSE_GPS_REPEATABILITY_HISTORY_V1",
        "source_system":target["source_system"],
        "rights_checked_locally":True,
        "authenticated_publisher_clock":True,
        "records":rows,
    }
    first_display_odds=dict(zip(IDS,[10.,7.,5.,3.,2.,1.7]))
    return source,target,first_display_odds


def compare(*,seed=20261026,horse_draws=250):
    source,target,first=toy_data()
    if horse_draws < 40:
        raise ValueError("HOLD_INSUFFICIENT_SYNTHETIC_DRAWS")
    arms={}
    for label,first_round in (("early",1),("delayed",3),("never",5)):
        o=run_coupled_repeatability_trial(
            source,target,observed_first_odds=first,seed=seed,
            horse_draws=horse_draws,info_release_round=first_round)
        arms[label]=o
    base=arms["early"]
    obj=base["independent_horse_objective_prior"]
    q0=base["observed_early_market_proxy"]
    ratios={}
    for name,x in arms.items():
        ratios[name]=round(x["market_crowding_effect_TV_points"],6)
    uniform=np.ones(len(IDS))/len(IDS)
    jac={}
    for social_exponent in (1.,2.,3.):
        val=local_market_gain(
            uniform,uniform,uniform,gamma=social_exponent,
            new_vote_fraction=.2)
        theorem=theoretical_gain(
            herding_fraction=.5,gamma=social_exponent,
            new_vote_fraction=.2)
        if abs(val["local_simplex_spectral_gain"]-theorem["linear_gain"])>1e-7:
            raise AssertionError("HOLD_MISMATCHED_SYNTHETIC_JACOBIAN")
        jac[str(social_exponent)]={"gain":round(theorem["linear_gain"],6),
                                  "regime":theorem["regime"]}
    return {
        "status":"TOY_SYNTHESTIC_ONLY_NOT_JRA_EVIDENCE",
        "experimental_n_horse_ids":len(IDS),
        "experimental_historical_races":7,
        "individual_traits_purposefully_planted":True,
        "source_repeatability_icc_scenario":
            round(base["source_same_horse_repeatability"]
                  ["source_conditional_approx_icc"],6),
        "independent_objective_favorite":IDS[int(np.argmax(obj))],
        "market_first_quote_favorite":IDS[int(np.argmax(q0))],
        "underlying_market_is_observed_like_but_fabricated":True,
        "no_information_reached_market_exactly_identical":
            base["information_never_market_identical"],
        "synthetic_market_TV_due_to_horse_crowding_pp_by_release_round":ratios,
        "stability_at_uniform_fixed_point_for_50pct_social_20pct_new_votes":jac,
        "source_timestamps_only_self_declared_and_not_external_proof":True,
        "real_RQ_to_JRA_id_bridge":"HOLD_NOT_PRESENT",
        "real_individual_reaction_norm_and_bettor_parameters":"HOLD_NOT_FITTED",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261026)
    p.add_argument("--horse-draws",type=int,default=250)
    a=p.parse_args()
    result=compare(seed=a.seed,horse_draws=a.horse_draws)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,
                                   indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
