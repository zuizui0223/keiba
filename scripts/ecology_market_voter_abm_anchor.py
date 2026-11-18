#!/usr/bin/env python3
"""Real saved Japanese quote states -> SIMULATED future voting, never real herding.

No pedigree/genotype or actual post-snapshot market information is supplied.
Cumulative fictional tickets evolve with 3 alternate social-feedback laws.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import statistics

from ecology_market_snapshot_structure import audit_snapshot

SCENARIOS={
    "objective_only":(0.0,None,None),
    "proportional_following":(1.0,None,None),
    "smooth_strong_following":(2.0,None,None),
    "threshold_following":(0.0,0.07,2.0),
}


def one_batch(q0, pool, beta, threshold, elevated, seed, n=250):
    if len(q0)!=len(pool) or len(q0)<3 or min(q0)<=0:
        raise ValueError("HOLD_INVALID_VOTING_FIELD")
    if abs(sum(q0)-1)>1e-8 or min(pool)<=0 or n<1:
        raise ValueError("HOLD_BAD_POOL_MASS")
    q=[x/sum(pool) for x in pool]
    offsets=[math.log(x/base) for x,base in zip(q,q0)]
    rho=(elevated if threshold is not None and
         max(abs(x) for x in offsets)>threshold else beta)
    if rho is None:
        raise ValueError("HOLD_MISSING_SOCIAL_FEEDBACK")
    utility=[math.log(base)+rho*x for base,x in zip(q0,offsets)]
    maximum=max(utility)
    weights=[math.exp(x-maximum) for x in utility]
    draws=random.Random(seed).choices(range(len(q0)),weights=weights,k=n)
    after=list(pool)
    for i in draws:
        after[i]+=1
    if sum(after)!=sum(pool)+n:
        raise ValueError("HOLD_TICKET_MASS_NOT_CONSERVED")
    return after


def run_one(q0, scenario, seed, *, steps=20, batch=250, initial_pool=1000):
    if scenario not in SCENARIOS or steps<1 or initial_pool<2*len(q0):
        raise ValueError("HOLD_INVALID_SCENARIO_OR_LENGTH")
    raw=[p*initial_pool for p in q0]
    counts=[int(v) for v in raw]
    for i in sorted(range(len(raw)),
                    key=lambda j:(raw[j]-counts[j],-j),reverse=True)[:
                    initial_pool-sum(counts)]:
        counts[i]+=1
    if min(counts)<1:
        raise ValueError("HOLD_INITIAL_POOL_TOO_SPARSE")
    beta,threshold,elevated=SCENARIOS[scenario]
    for t in range(steps):
        counts=one_batch(q0,counts,beta,threshold,elevated,
                         seed+100000*t,n=batch)
    final=[v/sum(counts) for v in counts]
    first_favorite=max(range(len(q0)),key=lambda i:q0[i])
    return {
        "effective_support_horses":1/sum(p*p for p in final),
        "original_favorite_final_support":final[first_favorite],
        "original_favorite_is_still_first":(
            max(range(len(q0)),key=lambda i:final[i])==first_favorite),
        "simulated_final_pool":sum(counts),
    }


def simulate(snapshot, repetitions=30):
    if repetitions<3 or repetitions>500:
        raise ValueError("HOLD_SIMULATION_REPETITIONS_BOUNDS")
    audit, races=audit_snapshot(snapshot,include_share_vector=True)
    if audit["status"]!="OBSERVED_SINGLE_SNAPSHOT_MARKET_CONCENTRATION_NOT_GENETICS":
        return audit
    result={}
    for scenario in SCENARIOS:
        rows=[]
        for i,source in enumerate(races):
            for repeat in range(repetitions):
                rows.append(run_one(source["initial_relative_support"],
                                    scenario,seed=20261115+i*1000+repeat))
        result[scenario]={
            "fictional_trajectories":len(rows),
            "mean_simulated_effective_support_horses":statistics.mean(
                r["effective_support_horses"] for r in rows),
            "mean_simulated_original_favorite_final_share":statistics.mean(
                r["original_favorite_final_support"] for r in rows),
            "fraction_fictional_trajectories_changing_favorite":statistics.mean(
                not r["original_favorite_is_still_first"] for r in rows),
            "fictional_final_tickets":rows[0]["simulated_final_pool"],
        }
    return {
        "status":"REAL_NINE_INITIAL_SUPPORT_STATES_SYNTHETIC_FUTURE_VOTER_ABM",
        "source_sha256":audit["data_quality"]["source_sha256"],
        "observed_races":len(races),
        "observed_horse_price_rows":audit["data_quality"]["horse_price_rows"],
        "observed_mean_effective_support_horses":
            audit["data_quality"]["effective_horses_simpson_across_races_mean"],
        "repetitions_per_race":repetitions,
        "fictional_steps":20,
        "fictional_tickets_per_batch":250,
        "market_regime_sensitivity":result,
        "no_actual_odds_time_series_or_ticket_counts_observed":True,
        "no_genotype_or_pedigree_information_in_initial_market":True,
        "no_real_market_social_herding_or_critical_threshold_detected":True,
        "not_calibrated_to_actual_outcomes_or_betting_returns":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--repetitions",type=int,default=30)
    args=p.parse_args()
    result=simulate(args.snapshot,repetitions=args.repetitions)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
