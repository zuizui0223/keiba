#!/usr/bin/env python3
"""Falsify claimed market "critical odds thresholds" with an information-free null.

One linked pathway: PR17 interacting HORSE first-passage ABM -> staged
information (PR18) -> bettor agents and endogenous market shares -> ordered
Plackett-Luce winner/Top3 probabilities. Compare three PREDECLARED social laws:

  fixed:  herd exponent 0.75 (PR14 "mixed")
  hard:   herd exponent 0.75 -> 1.50 if |d log support|/hour >= 0.10
          (PR14 "threshold_mixed": an ASSUMED switching point)
  smooth: herd exponent 0.75 + 0.75 * r/(r+0.10), continuous for r>=0

All three use common horse Brownian/Gumbel draws, common voter uniforms,
the same q0, prior pseudo stakes 3000 and four batches of 250 synthetic
votes. A signal not received during the 4 rounds is NEVER used.

A separate STRICT NULL simulates synthetic independent or herding-only
bets WITHOUT ANY horse signal. If the 0.10/h gate switches in that null,
it cannot be evidence of new public information, informed imitation,
or a phase transition. We also vary the CLOCK DURATION with identical
ballots: rate-based gates may appear solely from time normalization.

All archived real horses and quotes refer to SIX already-observed races on
TWO dates. Oct 12 detailed JRA history was normalized AFTER the targets.
Only historical DESCRIPTION / retrospective JRA podium scores are allowed;
real bettor stakes, actual GPS, independent source receipts and calibrated
win probabilities remain unavailable. NOTHING is fitted from outcomes,
and earlier sealed PR10 M0-M2/v3.1 are untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import math
from statistics import mean

import numpy as np

from keiba_coupled_horse_market_pde import ROOT, vector, vote_market
from keiba_nonlocal_horse_pde_bettor_bridge import finish_pair
from keiba_coupled_history_falsification import history_map, form_prior
from odds_threshold_regime_bridge import (
    load_source_locked_panels, market_features, exact_win_top3,
    score_forecast, aware,
)

STATUS="MARKET_THRESHOLD_SHARP_VS_SMOOTH_VS_NULL_SYNTHETIC_NOT_IDENTIFIED"
STRENGTHS=(0.0,2.0)
ARRIVALS=(1,3,5)
RULES=("fixed","hard","smooth")
NULL_RULES=("independent", "hard_without_horse_information")
HERD_BASE=0.75
HERD_MAX=1.50
INFO_EXPONENT=0.75
RATE_SCALE_LOG_PER_HOUR=0.10
ROUNDS=4
PRIOR_STAKES=3000
VOTES_PER_ROUND=250
PRIOR_ARMS=("initial_market","historical_form")
NULL_CLOCK_HOURS=(1.0,22.0)
DEFAULT_SEEDS=30


def herd_exponent(rate, policy):
    """Hard step is ASSUMED; smooth rule is an explicit no-step competitor."""
    if (not math.isfinite(rate) or rate<0 or policy not in RULES):
        raise ValueError("HOLD_INVALID_SOCIAL_RATE_OR_RULE")
    if policy=="fixed":
        return HERD_BASE
    if policy=="hard":
        return HERD_MAX if rate>=RATE_SCALE_LOG_PER_HOUR else HERD_BASE
    return HERD_BASE+(HERD_MAX-HERD_BASE)*rate/(rate+RATE_SCALE_LOG_PER_HOUR)


def current_rate(current, q0, elapsed_hours):
    """Maximum absolute normalized log-support change per elapsed hour."""
    if elapsed_hours<0 or not math.isfinite(elapsed_hours):
        raise ValueError("HOLD_INVALID_ELAPSED_RATE_CLOCK")
    if elapsed_hours==0:
        return 0.
    p=vector(current)
    q=vector(q0)
    if len(p)!=len(q):
        raise ValueError("HOLD_MISMATCHED_RATE_HORSE_FIELD")
    return float(np.max(np.abs(np.log(p/q)))/elapsed_hours)


def voter_path(q0, signal, *, policy, duration_hours, arrival=1,
               seed=20261025, steps=ROUNDS):
    """Exactly the original synthetic vote accounting with a controlled gate.

    fixed and hard are bit-for-bit compatible with the pre-existing
    'mixed' and 'threshold_mixed' votes for matching seed/duration/arrival.
    """
    if (policy not in RULES or duration_hours<=0 or not
            math.isfinite(duration_hours) or type(arrival) is not int or
            not 1<=arrival<=steps+1 or steps<2):
        raise ValueError("HOLD_INVALID_VOTER_MECHANISM_OR_ARRIVAL")
    q0=vector(q0)
    signal=vector(signal)
    if len(q0)!=len(signal):
        raise ValueError("HOLD_UNALIGNED_HORSE_MARKET_VECTOR")
    rng=np.random.default_rng(seed)
    pool=q0*PRIOR_STAKES
    path=[q0.copy()]
    rates=[]
    exponents=[]
    switches=0
    for step in range(1,steps+1):
        current=vector(pool)
        h=duration_hours*(step-1)/steps
        rate=current_rate(current,q0,h)
        exponent=herd_exponent(rate,policy)
        if policy=="hard" and rate>=RATE_SCALE_LOG_PER_HOUR:
            switches+=1
        visible_signal=signal if step>=arrival else q0
        weights=vector(current**exponent*visible_signal**INFO_EXPONENT)
        uniform=rng.random(VOTES_PER_ROUND)
        votes=np.bincount(np.searchsorted(np.cumsum(weights),uniform,
                            side="right"),minlength=len(q0))
        pool+=votes
        path.append(vector(pool))
        rates.append(rate)
        exponents.append(exponent)
    if not np.isclose(pool.sum(),PRIOR_STAKES+steps*VOTES_PER_ROUND,
                      atol=1e-8):
        raise ValueError("HOLD_MARKET_ACCOUNTING_MASS")
    return {
        "path":path,
        "final":path[-1],
        "pre_round_rate":rates,
        "herding_exponents":exponents,
        "hard_gate_active_round_count":switches,
        "information_available_round_count":max(0,steps-arrival+1),
        "policy_is_imposed_not_learned":True,
    }


def _TV(a,b):
    x,y=vector(a),vector(b)
    if len(x)!=len(y):
        raise ValueError("HOLD_INCONSISTENT_MARKET_COMPARISON")
    return float(50*np.sum(np.abs(x-y)))


def preoutcome_panel(row, horse_prior, *, distance_m,
                     draws=150,seed=20261025):
    """Produce ALL horse/social counterfactual forecasts without results."""
    f=market_features(row)
    q0=vector(f["early"])
    h=vector(horse_prior)
    if len(q0)!=len(h):
        raise ValueError("HOLD_INCOMPLETE_SOURCE_ROSTER")
    physics=finish_pair(h,distance_m=distance_m,draws=draws,
                        seed=seed,crowd_coefficient=2.)
    signal_by_c={
        "0.0":physics["scenarios"]["no_crowd"]["win"],
        "2.0":physics["scenarios"]["nonlocal_crowd"]["win"],
    }
    models={}
    for strength, signal in signal_by_c.items():
        models[strength]={}
        for arrival in ARRIVALS:
            models[strength][arrival]={}
            for policy in RULES:
                market=voter_path(
                    q0,signal,policy=policy,duration_hours=f["hours"],
                    arrival=arrival,seed=seed+390)
                forecast=exact_win_top3(
                    [float(x) for x in market["final"]])
                models[strength][arrival][policy]={
                    "market":market["final"],
                    "path":market["path"],
                    "rank_forecast":forecast,
                    "active_gate_rounds":market["hard_gate_active_round_count"],
                }
    for arrival in ARRIVALS:
        for policy in RULES:
            a=models["0.0"][arrival][policy]
            b=models["2.0"][arrival][policy]
            a["crowd_to_market_TV_pp"]=_TV(a["market"],b["market"])
            b["crowd_to_market_TV_pp"]=a["crowd_to_market_TV_pp"]
            if arrival==5 and not np.array_equal(a["market"],b["market"]):
                raise ValueError("HOLD_UNRELEASED_PHYSICAL_INFORMATION_AFFECTED_VOTES")
    return {
        "q0":q0, "models":models,
        "correct_first_horse_signal_hard_gate_was_imposed":True,
        "no_real_podium_or_later_market_used_by_simulator":True,
        "paired_same_physical_and_voter_draws":True,
    }


def _independent_null_gate_events(q0, hours, *, seed):
    """Count threshold rate crossings in an UNINFORMED random vote market."""
    x=vote_market(q0,q0,mode="independent",duration_hours=hours,
                  seed=seed,steps=ROUNDS)
    rates=[current_rate(x["path"][i],q0,hours*i/ROUNDS)
           for i in range(ROUNDS)]
    return sum(r>=RATE_SCALE_LOG_PER_HOUR for r in rates)


def null_market_scan(q0, duration_h, *, seeds=DEFAULT_SEEDS,
                     seed=20261025):
    """Do synthetic prices cross the hard rate threshold with NO information?

    The very same q0 and vote uniforms are replayed at the observed
    market time window, 1 hour and 22 hours. Real quoted q1 and
    official finish labels never enter this simulation.
    """
    if type(seeds) is not int or not 2<=seeds<=100:
        raise ValueError("HOLD_BAD_NULL_REPEATS")
    out={}
    horizons={"source_quote_window":duration_h,
              "normalized_1h":NULL_CLOCK_HOURS[0],
              "normalized_22h":NULL_CLOCK_HOURS[1]}
    for label,h in horizons.items():
        if h<=0:
            raise ValueError("HOLD_INVALID_NULL_HORIZON")
        scan={policy:[] for policy in NULL_RULES}
        for k in range(seeds):
            s=seed+1009*k
            scan["independent"].append(_independent_null_gate_events(
                q0,h,seed=s))
            # The hard rule is allowed to switch even with zero new
            # information: its own initial sample noise can generate it.
            scan["hard_without_horse_information"].append(
                voter_path(q0,q0,policy="hard",duration_hours=h,
                           arrival=ROUNDS+1,seed=s)[
                    "hard_gate_active_round_count"])
        out[label]={
            policy:{
                "null_runs_with_1plus_gate":sum(x>0 for x in seq),
                "null_gate_rounds_total":sum(seq),
                "mean_hard_gate_rounds_per_path":mean(seq),
                "fraction_null_runs_with_1plus_gate":sum(x>0 for x in seq)/seeds,
            } for policy,seq in scan.items()
        }
    return out


def run_source_locked(root=ROOT, *, draws=150, seeds=30,
                      seed=20261025, include_official=True):
    """Construct six-race physical/market regime models before all outcomes."""
    rows=load_source_locked_panels(root)
    historical=history_map(root)
    if len(rows)!=6 or set(historical)!={x["race_id"] for x in rows}:
        raise ValueError("HOLD_SOURCE_LOCKED_COHORT_DRIFT")
    produced=[]
    for k,row in enumerate(rows):
        f=market_features(row)
        physical_priors={
            "initial_market":f["early"],
            "historical_form":form_prior(
                row,historical[row["race_id"]])["prior"],
        }
        # Build every pre-outcome forecast and every uninformed null.
        variants={arm:preoutcome_panel(
            row,p,distance_m=historical[row["race_id"]]["distance_m"],
            draws=draws,seed=seed+1009*k)
            for arm,p in physical_priors.items()}
        nulls=null_market_scan(f["early"],f["hours"],seeds=seeds,
                               seed=seed+1009*k)
        produced.append({"row":row,"models":variants,"null":nulls})
    # All six target time-window inputs have already been translated into
    # source-locked forecasts. Compute source-null summaries without outcomes.
    bydate={}
    for day in sorted({z["row"]["meeting_day"] for z in produced}):
        selected=[z for z in produced if z["row"]["meeting_day"]==day]
        bydate[day]={
            "n_source_real_races":len(selected),
            "observed_source_window_hours":[
                float(market_features(z["row"])["hours"]) for z in selected],
            "synthetic_null_gate_any_fraction":{
                horizon:{
                    policy:mean(z["null"][horizon][policy][
                        "fraction_null_runs_with_1plus_gate"] for z in selected)
                    for policy in NULL_RULES}
                for horizon in ("source_quote_window","normalized_1h","normalized_22h")
            },
        }
    out={
        "status":STATUS,
        "source_races":6,
        "source_meeting_dates":2,
        "horse_race_entries":sum(
            len(market_features(z["row"])["horse_numbers"])
            for z in produced),
        "null_simulation_repetitions_per_race":seeds,
        "horse_draws_per_counterfactual":draws,
        "same_six_real_races_not_new_independent_observations":True,
        "market_assumed_hard_threshold_log_per_hour":RATE_SCALE_LOG_PER_HOUR,
        "smooth_feedback_is_continuous_without_fixed_change_point":True,
        "null_without_horse_information_can_trigger_imposed_hard_gate":True,
        "null_time_normalization_changes_rates_even_if_ballots_same":True,
        "three_social_laws":list(RULES),
        "voter_information_first_round_options":list(ARRIVALS),
        "by_source_meeting_date_null":bydate,
        "official_or_criticality_evidence":"HOLD",
        "real_JRA_GPS_or_actual_ballot_flow":False,
        "retrospective_history_source_receipt_unverified":True,
        "prior_Kikka_M0_M2_and_v31_unchanged":True,
    }
    if not include_official:
        out["status"]="PREOUTCOME_ONLY_NULL_AND_SYNTHETIC_NO_JRA_RESULTS_LOADED"
        out["official_score"]="NOT_COMPUTED"
        return out

    # SEALED FIREWALL: only below here read official target outcome labels.
    from odds_six_race_predictive_increment import (
        verify_official_oct12, verify_official_shuka)
    oct12,confirmed=verify_official_oct12(root)
    shuka=verify_official_shuka(root)
    perdate={}
    for obj in produced:
        row=obj["row"]
        if row["meeting_day"]=="2026-10-12":
            if confirmed<=aware(row["post_at"]):
                raise ValueError("HOLD_RETROSPECTIVE_RESULT_CLOCK_ORDER")
            top3=oct12["races"][str(row["race_no"])]["positions"]
        else:
            if shuka["verified_on_jst"]<=row["meeting_day"]:
                raise ValueError("HOLD_LATE_RACE_RESULT_ORDER")
            top3=shuka["top3"]
        f=market_features(row)
        for arm in PRIOR_ARMS:
            for crowd in ("0.0","2.0"):
                for arrival in ARRIVALS:
                    for policy in RULES:
                        state=obj["models"][arm]["models"][crowd][arrival][policy]
                        scored=score_forecast(f,state["rank_forecast"],top3)
                        key=(arm,crowd,arrival,policy)
                        d=perdate.setdefault(row["meeting_day"],{})
                        d.setdefault(key,[]).append({
                            "winner_log_loss":scored["win_log_loss"],
                            "top3_brier":scored["top3_brier"],
                            "later_real_price_TV_pp":_TV(
                                state["market"],f["latest"]),
                            "model_counterfactual_crowd_to_market_TV_pp":
                                state["crowd_to_market_TV_pp"],
                            "hard_rule_gate_count":state["active_gate_rounds"],
                        })
    out["historical_scores"]={
        arm:{
            crowd:{
                str(arrival):{
                    policy:{
                        metric:mean(z[metric] for day in perdate for z in
                                    perdate[day][(arm,crowd,arrival,policy)])
                        for metric in ("winner_log_loss","top3_brier",
                            "later_real_price_TV_pp",
                            "model_counterfactual_crowd_to_market_TV_pp",
                            "hard_rule_gate_count")}
                    for policy in RULES}
                for arrival in ARRIVALS}
            for crowd in ("0.0","2.0")}
        for arm in PRIOR_ARMS}
    out["date_equal_scores"]={
        arm:{
            key:mean(
                mean(z["winner_log_loss"] for z in perdate[day][key])
                for day in perdate)
            for key in perdate[next(iter(perdate))]
            if key[0]==arm and key[2] in (1,3)}
        for arm in PRIOR_ARMS}
    # JSON cannot serialize tuple keys; convert date contrast to structured
    # nested statistics rather than promoting them into arbitrary ranks.
    out["date_equal_scores"]={
        arm:{
            crowd:{
                str(arrival):{
                    policy:mean(
                        mean(z["winner_log_loss"] for z in
                             perdate[day][(arm,crowd,arrival,policy)])
                        for day in sorted(perdate))
                    for policy in RULES}
                for arrival in (1,3)}
            for crowd in ("0.0","2.0")}
        for arm in PRIOR_ARMS}
    out["official_outcomes_read_only_after_all_horse_market_and_null_models"]:True
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws",type=int,default=150)
    ap.add_argument("--null-seeds",type=int,default=30)
    ap.add_argument("--preoutcome-only",action="store_true")
    ap.add_argument("--output",type=Path,
                    default=Path("tmp/endogenous-threshold-null.json"))
    args=ap.parse_args()
    report=run_source_locked(draws=args.draws,seeds=args.null_seeds,
                             include_official=not args.preoutcome_only)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "source_races":report["source_races"],
        "synthetic_null_repeats":report["null_simulation_repetitions_per_race"],
        "threshold_claim":"HOLD",
        "official_outcomes_read":not args.preoutcome_only,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
