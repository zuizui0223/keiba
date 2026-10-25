#!/usr/bin/env python3
"""Seed-only robustness of nonlocal HORSE -> delayed informed VOTER response.

The same source-locked SIX historical race rosters and both priors are reused
at each seed; increasing seeds does not increase independent real-race N.
This evaluates ONLY synthetic market-index changes when crowd c switches
from 0 to 2 m2/s. It neither reads the target JRA result nor fits c.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from statistics import mean

from keiba_coupled_horse_market_pde import ROOT, vector, vote_market
from keiba_nonlocal_horse_pde_bettor_bridge import finish_pair
from keiba_coupled_history_falsification import history_map, form_prior
from odds_threshold_regime_bridge import load_source_locked_panels, market_features

STATUS = "SAME_SIX_RACES_SYNTHETIC_SEED_NOISE_NOT_EMPIRICAL_DELAY_EVIDENCE"
ARRIVAL=(1,3,5)
CROWD_C=2.
VOTE_MODE="information"


def individual_causal_response(row,prior,*,distance_m,draws=150,seed=20261025):
    """Physical/voter paired randomized comparison, WITHOUT later odds."""
    q0=vector(market_features(row)["early"])
    p=vector(prior)
    if len(p)!=len(q0):
        raise ValueError("HOLD_STAGED_HORSE_MARKET_RUNNER_MISMATCH")
    animal=finish_pair(p,distance_m=distance_m,draws=draws,
                       seed=seed,crowd_coefficient=CROWD_C)
    base=animal["scenarios"]["no_crowd"]["win"]
    crowd=animal["scenarios"]["nonlocal_crowd"]["win"]
    output={}
    for step in ARRIVAL:
        a=vote_market(q0,base,mode=VOTE_MODE,duration_hours=market_features(row)["hours"],
                      seed=seed+390,signal_start_step=step)
        b=vote_market(q0,crowd,mode=VOTE_MODE,duration_hours=market_features(row)["hours"],
                      seed=seed+390,signal_start_step=step)
        output[step]=float(50*sum(abs(x-y) for x,y in zip(a["final"],b["final"])))
        if step==5 and output[step]!=0:
            raise ValueError("HOLD_UNRELEASED_INFORMATION_LEAKAGE")
    return output


def audit(root=ROOT, *, seed_count=5,draws=150,seed=20261025):
    if seed_count<2 or draws<40 or seed_count>30:
        raise ValueError("HOLD_INVALID_SIMULATION_REPEATS")
    rows=load_source_locked_panels(root)
    histories=history_map(root)
    if len(rows)!=6 or set(histories)!={x["race_id"] for x in rows}:
        raise ValueError("HOLD_UNEXPECTED_ARCHIVED_COHORT")
    sample={}
    for arm in ("initial_market","historical_form"):
        runs=[]
        for iteration in range(seed_count):
            vals=[]
            for idx,row in enumerate(rows):
                f=market_features(row)
                history=form_prior(row,histories[row["race_id"]])
                prior=(f["early"] if arm=="initial_market" else history["prior"])
                vals.append(individual_causal_response(
                    row,prior,distance_m=histories[row["race_id"]]["distance_m"],
                    draws=draws,seed=seed+10003*iteration+1009*idx))
            runs.append({
                "seed":seed+10003*iteration,
                "mean_six_races_market_TV_early_info_pp":
                    mean(x[1] for x in vals),
                "mean_six_races_market_TV_late_info_pp":
                    mean(x[3] for x in vals),
                "mean_six_races_market_TV_no_info_pp":
                    mean(x[5] for x in vals),
            })
        measures={}
        for key in (
            "mean_six_races_market_TV_early_info_pp",
            "mean_six_races_market_TV_late_info_pp",
            "mean_six_races_market_TV_no_info_pp",
        ):
            numbers=[x[key] for x in runs]
            measures[key]={
                "mean_across_repeated_synthetic_seeds":mean(numbers),
                "minimum_across_seeds":min(numbers),
                "maximum_across_seeds":max(numbers),
            }
        sample[arm]={
            "ranges":measures,
            "seed_repetitions_early_exceeds_delayed":sum(
                x["mean_six_races_market_TV_early_info_pp"]>
                x["mean_six_races_market_TV_late_info_pp"] for x in runs),
            "seed_repetitions_any_no_info_response":sum(
                x["mean_six_races_market_TV_no_info_pp"]!=0 for x in runs),
        }
    return {
        "status":STATUS,
        "real_races":6,
        "real_meeting_dates":2,
        "same_real_races_reused_for_seed_repetitions":True,
        "not_a_population_CI_or_true_voter_delay_parameter":True,
        "synthetic_seed_repeat_count":seed_count,
        "horse_draws_per_race_per_seed":draws,
        "physical_crowd_coefficient_m2ps":CROWD_C,
        "source_histories_not_authentically_received_before_2026_targets":True,
        "no_official_outcomes_read":True,
        "information_arrival_rounds_list":list(ARRIVAL),
        "by_horse_initial_prior":sample,
        "actual_market_phase_transition_or_profit":"HOLD",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds",type=int,default=5)
    p.add_argument("--draws",type=int,default=150)
    p.add_argument("--output",type=Path,
        default=Path("tmp/coupled-delay-seed-envelope.json"))
    args=p.parse_args()
    result=audit(seed_count=args.seeds,draws=args.draws)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":
    main()
