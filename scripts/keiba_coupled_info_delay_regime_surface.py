#!/usr/bin/env python3
"""Coupled HORSE interaction strength x INFORMATION-ARRIVAL regime surface.

Strictly an EXPLORATORY SYNTHETIC mechanism sensitivity on the six source
locked historical race rosters. This asks whether c-induced physical rank
changes propagate through delayed voters. The original odds-market
threshold is imposed, not discovered. No independent pre-target horse
history receipts or original horse GPS trajectories are available.

IMPORTANT:
  - PR17 interacting horse first passage and nonlocal PDE share K, c, D.
  - PR14 voter ABM now optionally delays the FIRST horse-signal round;
    its default=1 is completely backwards compatible.
  - The physical prior and voter q0 remain distinct.
  - All c values and information arrival times are predeclared.
  - SAME latent horse/Wiener draws per c, SAME voter uniforms per policy.
  - No later real quote or official podium can modify any forecast.
  - Finite synthetic rounds, discrete simulated finishes, and a hardcoded
    voter threshold can LOOK discontinuous without a physical phase change.
  - Real outcomes are loaded only after every model scenario exists.

Run:
  python scripts/keiba_coupled_info_delay_regime_surface.py \
      --draws 120 --pde-particles 800 --output tmp/horse-info-delay.json
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from keiba_coupled_horse_market_pde import (
    ROOT, vector, vote_market,
)
from keiba_nonlocal_horse_pde_bettor_bridge import (
    finish_pair, pde_density_and_agent_check, VOTER_TYPES,
)
from keiba_coupled_history_falsification import (
    history_map, form_prior,
)
from odds_threshold_regime_bridge import (
    load_source_locked_panels, market_features,
    exact_win_top3, score_forecast, aware,
)

STATUS = "SYNTHETIC_INTERACTION_INFORMATION_DELAY_SURFACE_NOT_REAL_CRITICALITY"
CROWD_STRENGTH_GRID = (0., .5, 1., 2., 4., 8.)
SIGNAL_START_ROUNDS = (1, 3, 5)  # early, delayed, never, for four voting rounds
N_VOTE_ROUNDS = 4
PDE_STRENGTH_GRID = (0., 2., 8.)
PRIOR_ARMS = ("initial_market", "historical_form")
REF_C = 0.0


def _key(c):
    if c not in CROWD_STRENGTH_GRID:
        raise ValueError("HOLD_UNDECLARED_CROWD_STRENGTH")
    return str(float(c))


def win_top3_from_market(q):
    """The same ordered Plackett-Luce law for WIN and Top3, no extra logits."""
    return exact_win_top3([float(x) for x in vector(q)])


def _tv_percent(q,r):
    q,r=vector(q),vector(r)
    if len(q)!=len(r):
        raise ValueError("HOLD_INCOHERENT_FIELD_FOR_MARKET_TV")
    return float(50*np.sum(np.abs(q-r)))


def prepare_regimes(row, physical_prior, *, distance_m,
                    draws=120,seed=20261025):
    """Entire simulated regime surface calculated without target outcome.

    The row's later odds are validated for source time/roster but NEVER used
    to generate a horse ensemble, simulate votes, or select a c/arrival.
    """
    f=market_features(row)
    ids=f["horse_numbers"]
    q0=vector([1/row["first_odds"][i] for i in ids])
    prior=vector(physical_prior)
    if len(prior)!=len(ids) or draws<40 or not 800<=distance_m<=5000:
        raise ValueError("HOLD_INVALID_PRIOR_OR_RACE_NUMERICS")
    scenarios={}
    unperturbed=None
    for c in CROWD_STRENGTH_GRID:
        physical=finish_pair(prior,distance_m=distance_m,draws=draws,
                             seed=seed,crowd_coefficient=c)
        # Common random numbers make the c=0 potential outcome IDENTICAL
        # in every c-run. Any mismatch means the comparison is unpaired.
        no_crowd=physical["scenarios"]["no_crowd"]
        if unperturbed is None:
            unperturbed=no_crowd
        else:
            for k in ("win","top3","ordered_top3"):
                if not np.array_equal(unperturbed[k],no_crowd[k]):
                    raise ValueError("HOLD_PHYSICAL_COUNTERFACTUAL_RANDOMNESS_UNPAIRED")
        animal=physical["scenarios"]["nonlocal_crowd"]
        rounds={}
        for first_step in SIGNAL_START_ROUNDS:
            cases={}
            for mode in VOTER_TYPES:
                x=vote_market(q0,animal["win"],mode=mode,
                    duration_hours=f["hours"],seed=seed+390,
                    steps=N_VOTE_ROUNDS,signal_start_step=first_step,
                    synthetic_votes_per_step=250)
                p=win_top3_from_market(x["final"])
                if (not math.isclose(sum(p["win"]),1.,abs_tol=1e-9) or
                    not math.isclose(sum(p["top3"]),3.,abs_tol=1e-9)):
                    raise ValueError("HOLD_MARKET_RANK_PROBABILITY_MASS")
                cases[mode]={
                    "market":x["final"],
                    "forecast":p,
                    "threshold_active_rounds":x["triggered_steps"],
                    "visible_information_rounds":x["information_visible_round_count"],
                }
            rounds[first_step]=cases
        scenarios[_key(c)]={
            "animal_WIN":animal["win"],
            "animal_Top3":animal["top3"],
            "paired_winner_change_fraction":
                physical["paired_prob_winner_difference"],
            "first_top3_order_change_fraction":
                physical["paired_prob_any_first_three_order_difference"],
            "market_by_arrival":rounds,
        }
    baseline=scenarios[_key(REF_C)]
    for key,cdata in scenarios.items():
        cdata["horse_win_TV_from_c0_pp"]=_tv_percent(
            cdata["animal_WIN"],baseline["animal_WIN"])
        cdata["horse_top3_relative_TV_from_c0_pp"]=(
            _tv_percent(cdata["animal_Top3"],baseline["animal_Top3"])/3.)
        for first_step in SIGNAL_START_ROUNDS:
            for mode in VOTER_TYPES:
                mkt=cdata["market_by_arrival"][first_step][mode]
                null=baseline["market_by_arrival"][first_step][mode]
                mkt["crowd_to_market_TV_pp"]=_tv_percent(
                    mkt["market"],null["market"])
                mkt["change_in_fixed_voter_threshold_rounds"]=(
                    mkt["threshold_active_rounds"]-
                    null["threshold_active_rounds"])
                # No physical effect can travel without an information edge.
                if ((mode in ("independent","herding") or
                      first_step==N_VOTE_ROUNDS+1) and
                    not np.array_equal(mkt["market"],null["market"])):
                    raise ValueError("HOLD_CAUSAL_BYPASS_OF_INFORMATION_ARRIVAL")
    return {
        "market_horse_numbers":ids,
        "market_initial_index":q0,
        "physical_prior":prior,
        "regimes":scenarios,
        "four_voter_rounds_with_predeclared_information_release":True,
        "no_actual_finish_or_later_price_used_by_agents":True,
        "source_clock_span_hours":f["hours"],
    }


def _score_predictions(produced, row, official_top3):
    f=market_features(row)
    q_late=vector(f["latest"])
    outcomes={}
    for c,cases in produced["regimes"].items():
        line={}
        for arrival,markets in cases["market_by_arrival"].items():
            measurements={}
            for mode,x in markets.items():
                # Target-event outcome and later PRICE proxy are scored
                # separately; price shape is not a proper winner score.
                perf=score_forecast(f,x["forecast"],official_top3)
                measurements[mode]={
                    "win_log_loss":perf["win_log_loss"],
                    "top3_brier":perf["top3_brier"],
                    "later_market_price_index_TV_pp":_tv_percent(
                        x["market"],q_late),
                }
            line[arrival]=measurements
        outcomes[c]=line
    return outcomes


def _summarize_regimes(rows):
    """No horse rows, source quote vectors or private predictions exported."""
    keys=[_key(c) for c in CROWD_STRENGTH_GRID]
    scores={}
    for arm in PRIOR_ARMS:
        scores[arm]={}
        for c in CROWD_STRENGTH_GRID:
            ck=_key(c)
            scores[arm][ck]={}
            for arr in SIGNAL_START_ROUNDS:
                scores[arm][ck][str(arr)]={}
                for mode in VOTER_TYPES:
                    policy=[z["scores"][arm][ck][arr][mode] for z in rows]
                    p=[z["produced"][arm]["regimes"][ck][
                        "market_by_arrival"][arr][mode] for z in rows]
                    null=[z["produced"][arm]["regimes"][_key(REF_C)][
                        "market_by_arrival"][arr][mode] for z in rows]
                    scores[arm][ck][str(arr)][mode]={
                        "winner_log_loss":mean(x["win_log_loss"] for x in policy),
                        "top3_brier":mean(x["top3_brier"] for x in policy),
                        "later_market_price_index_TV_pp":mean(
                            x["later_market_price_index_TV_pp"] for x in policy),
                        "counterfactual_crowd_to_market_TV_pp":mean(
                            x["crowd_to_market_TV_pp"] for x in p),
                        "sum_triggered_threshold_rounds":sum(
                            x["threshold_active_rounds"] for x in p),
                        "sum_gate_step_delta_from_c0":sum(
                            x["change_in_fixed_voter_threshold_rounds"] for x in p),
                    }
    response={}
    for arm in PRIOR_ARMS:
        response[arm]={}
        for c in CROWD_STRENGTH_GRID:
            ck=_key(c)
            q=[z["produced"][arm]["regimes"][ck] for z in rows]
            response[arm][ck]={
                "physical_WIN_TV_vs_c0_pp":mean(x[
                    "horse_win_TV_from_c0_pp"] for x in q),
                "physical_Top3_relative_TV_vs_c0_pp":mean(x[
                    "horse_top3_relative_TV_from_c0_pp"] for x in q),
                "paired_winner_change_fraction_vs_c0":mean(x[
                    "paired_winner_change_fraction"] for x in q),
            }
    date_effects={}
    for arm in PRIOR_ARMS:
        date_effects[arm]={}
        for day in sorted({x["day"] for x in rows}):
            subset=[x for x in rows if x["day"]==day]
            date_effects[arm][day]={
                "n_real_races":len(subset),
                "c_2_info_first_round_market_TV_vs_no_crowd_pp":mean(
                    x["produced"][arm]["regimes"][_key(2.)][
                        "market_by_arrival"][1]["information"][
                            "crowd_to_market_TV_pp"] for x in subset),
                "c_2_info_third_round_market_TV_vs_no_crowd_pp":mean(
                    x["produced"][arm]["regimes"][_key(2.)][
                        "market_by_arrival"][3]["information"][
                            "crowd_to_market_TV_pp"] for x in subset),
            }
    return scores,response,date_effects


def audit(root=ROOT, *, draws=120, pde_particles=800,
          seed=20261025, include_official=True):
    """Full physical/social panel; no later outcome before ALL predictions."""
    if draws<40 or pde_particles<100:
        raise ValueError("HOLD_INSUFFICIENT_SYNTHETIC_DRAW_COUNT")
    snapshots=load_source_locked_panels(root)
    hist=history_map(root)
    if len(snapshots)!=6 or set(hist)!={q["race_id"] for q in snapshots}:
        raise ValueError("HOLD_UNMATCHED_REAL_RACE_PROVENANCE")
    prepared=[]
    for k,row in enumerate(snapshots):
        q0=vector(market_features(row)["early"])
        history=form_prior(row,hist[row["race_id"]])
        priors={"initial_market":q0,"historical_form":history["prior"]}
        cases={
            arm:prepare_regimes(
                row,prior,distance_m=hist[row["race_id"]]["distance_m"],
                draws=draws,seed=seed+1009*k)
            for arm,prior in priors.items()
        }
        prepared.append({"row":row,"prior":priors,"produced":cases})
    # A small source-locked *diagnostic* PDE strength sweep, performed
    # on one fixed race for two prior regimes; NOT a fit to real GPS.
    representative=prepared[0]
    pde={}
    for arm in PRIOR_ARMS:
        pde[arm]={}
        for c in PDE_STRENGTH_GRID:
            pde[arm][_key(c)]=pde_density_and_agent_check(
                representative["prior"][arm],strength=c,
                particles=pde_particles,seed=seed+999,
                duration_s=12.)
    out={
        "status":STATUS,
        "independent_real_races":len(prepared),
        "independent_meeting_dates":len({
            row["row"]["meeting_day"] for row in prepared}),
        "horse_race_entries":sum(
            len(row["produced"]["initial_market"]["market_horse_numbers"])
            for row in prepared),
        "declared_crowd_strength_m2_per_s":list(CROWD_STRENGTH_GRID),
        "declared_signal_first_available_voter_round":list(SIGNAL_START_ROUNDS),
        "number_of_hypothetical_voter_rounds":N_VOTE_ROUNDS,
        "local_history_retrieved_postrace_asof_unverified":True,
        "same_random_numbers_for_horse_and_voter_counterfactuals":True,
        "c0_and_information-never_release_negative_controls":True,
        "PDE_one_representative_race_not_empirical_GPS":pde,
        "PDE_product_marginals_ignore_interhorse_spatial_covariance":True,
        "not_a_discovered_biological_or_market_critical_point":True,
        "not_an_authentic_prospective_or_wagering_result":True,
        "earlier_sealed_Kikka_M0_M2_and_v31_unchanged":True,
    }
    if not include_official:
        out["status"]="PREOUTCOME_COMPUTATION_ONLY_NO_JRA_RESULT_OPENED"
        out["official_scores"]="NOT_COMPUTED"
        return out

    # Strict result firewall: all physical, social and PDE trajectories
    # across SIX races already exist above this line.
    from odds_six_race_predictive_increment import (
        verify_official_oct12, verify_official_shuka,
    )
    oct12,reported_at=verify_official_oct12(root)
    shuka=verify_official_shuka(root)
    recorded=[]
    for z in prepared:
        row=z["row"]
        if row["meeting_day"]=="2026-10-12":
            if reported_at<=aware(row["post_at"]):
                raise ValueError("HOLD_JRA_RESULT_PRECEDES_TARGET_RACE")
            top3=oct12["races"][str(row["race_no"])]["positions"]
        else:
            if shuka["verified_on_jst"]<=row["meeting_day"]:
                raise ValueError("HOLD_SHUKA_RESULT_TIME_INVALID")
            top3=shuka["top3"]
        scores={
            arm:_score_predictions(produced,row,top3)
            for arm,produced in z["produced"].items()
        }
        recorded.append({
            "day":row["meeting_day"],
            "scores":scores,
            "produced":z["produced"],
        })
    s,p,d=_summarize_regimes(recorded)
    if out["independent_real_races"]!=6 or out["horse_race_entries"]!=84:
        raise ValueError("HOLD_UPSTREAM_SOURCE_RACE_UNIVERSE_CHANGED")
    out["mean_equal_race_scores"]=s
    out["physical_crowd_intensity_response"]=p
    out["by_meeting_day"]=d
    out["market_quote_shapes_are_not_winner_probabilities"]=True
    out["official_outcomes_scored_only_after_all_regimes_frozen_in_memory"]=True
    out["market_or_biological_threshold_inference"]="HOLD"
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws",type=int,default=120)
    parser.add_argument("--pde-particles",type=int,default=800)
    parser.add_argument("--preoutcome-only",action="store_true")
    parser.add_argument("--output",type=Path,
                        default=Path("tmp/coupled-regime-surface.json"))
    args=parser.parse_args()
    report=audit(draws=args.draws,pde_particles=args.pde_particles,
                 include_official=not args.preoutcome_only)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "real_races":report["independent_real_races"],
        "meeting_dates":report["independent_meeting_dates"],
        "empirical_threshold":"HOLD",
        "has_official_labels":not args.preoutcome_only,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
