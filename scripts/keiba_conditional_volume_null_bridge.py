#!/usr/bin/env python3
"""Conditional volume/overdispersion identifiability for KEIBA's coupled market.

One causal research chain is retained:
  source-locked old horse records -> PR17 horse ABM with forward K,c,D
  -> PR18 staged source information -> PR19 smooth/fixed/hard bettors
  -> ONE joint ranking-price index -> independently held next WIN quote.

Against those same SIX archived next-quote vectors we examine a sharper
counterfactual: how much of q1-q0 can happen with no *new* horse signal,
solely finite, cumulative pseudo-ballot noise? The null is simulated using
q0 ONLY; q1 and JRA podiums are never inputs to the simulation.

Conditional pseudo-pool accounting:
  qhat=(1-lambda)q0 + lambda * Multinomial(N,p)/N.
Stationary IID null p=q0; overdispersed competitor p~Dirichlet(kappa*q0).
All lambda, N and kappa scenarios are DECLARED, not inferred. The second
model covers unobserved block correlations, NOT direct evidence of imitation.

The max over horses of |log(qhat_i/q0_i)| is explicitly calibrated by its
own null distribution; a raw 0.10/h trigger is not evidence of information.
Identical q0/q1 and simulated ballots with 1-hour or 22-hour denominators
yield identical calibrated max-rate tail area, despite wildly changing
raw 0.10/h crossing frequency.

Exact flow feasibility is conditional on q0,q1 being ACTUAL pool shares,
which is UNVERIFIED: these are normalized reciprocal quoted PAYOUT odds.
JRA net price/takeout rules and display rounding complicate inference.
Assumed ±0.05 decimal display uncertainty is shown ONLY as sensitivity,
NOT as an empirically certified rounding mechanism.

No real JRA stake volumes, bettor identities, true horse GPS, or
prospectively authenticated Oct12 horse histories. Six races/TWO dates.
The output is a conditional sensitivity, NOT a real p-value, discovered
critical threshold, calibrated betting edge, or new prospectively
validated racing event. Original v3.1 and Kikka M0-2 are untouched.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from keiba_coupled_horse_market_pde import ROOT, vector
from keiba_coupled_history_falsification import history_map, form_prior
from keiba_endogenous_threshold_null_bridge import preoutcome_panel
from odds_threshold_regime_bridge import load_source_locked_panels, market_features

STATUS="RETROSPECTIVE_PRICE_PROXY_NULL_VOLUME_NOT_IDENTIFIED"
LAMBDAS=(0.20,0.80)
EFFECTIVE_NEW_VOTE_COUNTS=(100,1000,10000)
CONCENTRATION_SPECS=(("independent_iid",None),("overdispersed_kappa80",80.0))
ROUNDING_HALF_WIDTH_DECIMAL=0.05
QUANTILE_LEVEL=0.95
ASSUMED_HORSE_CROWD_STRENGTH=2.0
HORSE_INFORMATION_ARRIVALS=(1,3,5)
SIGNAL_SOCIAL_RULE="smooth"


def transition_accounting_lower_bound(q0, q1):
    """Exact simplex condition for q1=(1-lambda)q0+lambda*b, b>=0.

    It only becomes a pool-turnover bound IF quoted reciprocals really are
    exact comparable pool shares, which is NOT established for JRA quotes.
    """
    a=vector(q0)
    b=vector(q1)
    if len(a)!=len(b):
        raise ValueError("HOLD_INCOMPARABLE_FULL_HORSE_ROSTER")
    return float(max(0.,np.max(1-b/a)))


def transition_witness(q0,q1,new_fraction):
    """Algebraic simplex flow witness; NEVER actual observed bets."""
    a,b=vector(q0),vector(q1)
    if (len(a)!=len(b) or type(new_fraction) not in (float,int)
            or not 0<new_fraction<=1):
        raise ValueError("HOLD_INVALID_HYPOTHETICAL_POOL_SHARE")
    implied=(b-(1-new_fraction)*a)/new_fraction
    if np.any(implied < -1e-12):
        raise ValueError("HOLD_NEGATIVE_HYPOTHETICAL_NEW_VOTE_SHARE")
    if not np.isclose(implied.sum(),1,atol=1e-11):
        raise ValueError("HOLD_HYPOTHETICAL_TURNOVER_MASS")
    # Exact feasible new-vote compositions may put zero share on a horse.
    # The horse-prior normalization helper requires strictly positive
    # probabilities and is NOT appropriate for simplex boundary witnesses.
    nonnegative=np.maximum(implied,0.)
    total=float(nonnegative.sum())
    if not math.isclose(total,1.,rel_tol=0,abs_tol=1e-9):
        raise ValueError("HOLD_FLOW_WITNESS_SUM")
    return nonnegative/total


def _rounding_marginal_bounds(odds, *, half_width=ROUNDING_HALF_WIDTH_DECIMAL):
    """All feasible one-horse marginals under ±half_width display bins.

    This sensitivity interval doesn't claim JRA uses nearest-0.1 rounding.
    """
    if not isinstance(odds,dict) or len(odds)<5:
        raise ValueError("HOLD_INVALID_QUOTED_ODDS_FOR_DISPLAY_BOUNDS")
    keys=sorted(odds)
    vals=np.asarray([odds[k] for k in keys],dtype=float)
    if (not np.all(np.isfinite(vals)) or
            not 0<half_width<.5 or np.any(vals<=1+half_width)):
        raise ValueError("HOLD_INVALID_DISPLAY_HALF_BIN")
    reciprocal_low=1/(vals+half_width)
    reciprocal_high=1/(vals-half_width)
    lo=reciprocal_low/(reciprocal_low+reciprocal_high.sum()-
                       reciprocal_high)
    hi=reciprocal_high/(reciprocal_high+reciprocal_low.sum()-
                        reciprocal_low)
    return keys,lo,hi


def quotation_TV_rounding_lower_bound(first_odds, later_odds):
    """Rigorous lower bound within *hypothetical* symmetric quote bins."""
    ids,l0,u0=_rounding_marginal_bounds(first_odds)
    ids2,l1,u1=_rounding_marginal_bounds(later_odds)
    if ids!=ids2:
        raise ValueError("HOLD_QUOTE_ROSTER_DIFFERENCE")
    guaranteed=np.maximum(np.maximum(l0-u1,l1-u0),0.)
    return float(50*np.sum(guaranteed))


def _market_shape_statistics(q0,q1):
    q0=vector(q0)
    q1=vector(q1)
    if len(q0)!=len(q1):
        raise ValueError("HOLD_DIFFERENT_MARKET_ROSTER")
    return (float(50*np.abs(q1-q0).sum()),
            float(np.max(np.abs(np.log(q1/q0)))))


def simulate_no_horse_information(q0, *, new_fraction, effective_new_votes,
                                   concentration=None, repetitions=2000,
                                   seed=20261025):
    """Return RAW null arrays, generated WITHOUT later quote or result.

    Dirichlet mixing makes paths correlated/overdispersed conditionally on
    latent p. Neither random p nor votes represents real JRA bettors.
    """
    initial=vector(q0)
    if (type(effective_new_votes) is not int or effective_new_votes<2
            or type(repetitions) is not int or repetitions<50
            or not 0<new_fraction<=1 or not math.isfinite(new_fraction)
            or concentration is not None and (not math.isfinite(concentration)
                                               or concentration<=0)):
        raise ValueError("HOLD_INVALID_PSEUDO_POOL_NULL_SETTINGS")
    rng=np.random.default_rng(seed)
    n=len(initial)
    if concentration is None:
        p=initial
    else:
        p=rng.dirichlet(concentration*initial,size=repetitions)
    drawn=rng.multinomial(effective_new_votes,p,size=repetitions)
    synthetic=(1-new_fraction)*initial[None,:]+(
        new_fraction*drawn/effective_new_votes)
    if synthetic.shape!=(repetitions,n) or not np.allclose(
            synthetic.sum(axis=1),1.,atol=1e-10):
        raise ValueError("HOLD_PSEUDO_POOL_NOT_NORMALIZED")
    abs_change=np.abs(synthetic-initial)
    tv=50*abs_change.sum(axis=1)
    abs_log_rate_numerator=np.max(
        np.abs(np.log(synthetic/initial)),axis=1)
    return {"TV_pp":tv,"max_abs_log_support_change":abs_log_rate_numerator}


def null_calibration(null_samples, q0, q1, *,
                     hours, new_fraction, sample_count, concentration):
    """Conditional Monte Carlo tail areas of two prespecified statistics.

    These are NOT frequentist p-values about the REAL JRA market because
    pool sizes, q0 true shares, source/rounding models are unknown.
    """
    if hours<=0 or not math.isfinite(hours):
        raise ValueError("HOLD_INVALID_RATE_EXPOSURE")
    tv,raw_max=_market_shape_statistics(q0,q1)
    tv_null=np.asarray(null_samples["TV_pp"],dtype=float)
    max_null=np.asarray(null_samples["max_abs_log_support_change"],dtype=float)
    if (len(tv_null)<50 or len(tv_null)!=len(max_null)
            or np.any(tv_null<0) or np.any(max_null<0)):
        raise ValueError("HOLD_BAD_NULL_DISTRIBUTION")
    observed_rate=raw_max/hours
    simulated_rate=max_null/hours
    p_tv=(1+np.sum(tv_null>=tv))/(len(tv_null)+1)
    p_max=(1+np.sum(simulated_rate>=observed_rate))/(len(max_null)+1)
    min_lambda=transition_accounting_lower_bound(q0,q1)
    return {
        "assumed_new_fraction_of_final_pool":float(new_fraction),
        "assumed_effective_new_vote_count":int(sample_count),
        "assumed_latent_dirichlet_concentration":concentration,
        "assumed_vote_mechanism":("independent_iid_at_initial_q0" if
                                 concentration is None else
                                 "exchangeable_overdispersed_no_horse_signal"),
        "observed_price_proxy_TV_pp":tv,
        "observed_max_abs_log_support_per_hour":observed_rate,
        "null_TV_mean_pp":float(np.mean(tv_null)),
        "null_TV_95pct_pp":float(np.quantile(tv_null,QUANTILE_LEVEL)),
        "null_max_rate_95pct_per_hour":float(np.quantile(simulated_rate,
                                                      QUANTILE_LEVEL)),
        "conditional_tail_area_TV_not_real_p_value":float(p_tv),
        "conditional_tail_area_max_search_not_real_p_value":float(p_max),
        "nominal_proxy_exact_cumulative_flow_feasible_at_assumed_lambda":
            bool(new_fraction+1e-12>=min_lambda),
        "nominal_proxy_lower_bound_new_fraction":min_lambda,
        "corrected_for_search_over_all_horses_in_one_race":True,
        "not_evidence_of_social_imitation_or_new_horse_information":True,
    }


def heldout_null_false_alarm_check(q0, *, new_fraction=.5, count=500,
                                   concentration=None, repetitions=2000,
                                   seed=20261025):
    """Toy self-calibration uses disjoint null draws, NOT six real outcomes."""
    training=simulate_no_horse_information(
        q0,new_fraction=new_fraction,effective_new_votes=count,
        concentration=concentration,repetitions=repetitions,seed=seed)
    holdout=simulate_no_horse_information(
        q0,new_fraction=new_fraction,effective_new_votes=count,
        concentration=concentration,repetitions=repetitions,seed=seed+100000)
    q=np.quantile(training["max_abs_log_support_change"],QUANTILE_LEVEL)
    tvq=np.quantile(training["TV_pp"],QUANTILE_LEVEL)
    return {
        "false_alarm_max_statistic_in_independent_null_holdout":float(
            np.mean(holdout["max_abs_log_support_change"]>q)),
        "false_alarm_TV_in_independent_null_holdout":float(
            np.mean(holdout["TV_pp"]>tvq)),
        "nominal_test_fraction":1-QUANTILE_LEVEL,
        "independent_synthetic_null_splits_only":True,
        "not_a_real_market_type_I_error_estimate":True,
    }


def _build_connected_preoutcome(row, history, *, draws, seed):
    """Reuse PR19's whole nonlocal horse -> staged bettor pipeline.

    Simulated crowd+continuous-policy final market indices are candidate
    forecasts only, never trained from observed later q1 or JRA podium.
    """
    early=market_features(row)["early"]
    ids=sorted(row["first_odds"])
    hist=form_prior(row,history)
    arms={"initial_market":early,"past_form":hist["prior"]}
    out={}
    for arm,prior in arms.items():
        model=preoutcome_panel(
            row,prior,distance_m=history["distance_m"],
            draws=draws,seed=seed)
        out[arm]={str(a):model["models"]["2.0"][a]["smooth"]["market"]
                  for a in (1,3,5)}
        if not np.allclose(model["q0"],vector(early)):
            raise ValueError("HOLD_PHYSICAL_AND_BETTOR_MARKET_NOT_CONNECTED")
    return out


def audit(root=ROOT, *, repetitions=2000, horse_draws=80,seed=20261025):
    if repetitions<100 or horse_draws<40:
        raise ValueError("HOLD_NOT_ENOUGH_PSEUDO_MC_DRAWS")
    races=load_source_locked_panels(root)
    historical=history_map(root)
    if len(races)!=6 or set(historical)!={r["race_id"] for r in races}:
        raise ValueError("HOLD_SOURCE_LOCKED_MARKET_HISTORY_UNIVERSE")
    prepared=[]
    for i,row in enumerate(races):
        ids=sorted(row["first_odds"])
        q0=vector([1/row["first_odds"][j] for j in ids])
        # Prepare all hypothesized independent-vote nulls BEFORE reading q1.
        nulls={}
        for li,lamb in enumerate(LAMBDAS):
            for vi,n in enumerate(EFFECTIVE_NEW_VOTE_COUNTS):
                for ci,(label,kappa) in enumerate(CONCENTRATION_SPECS):
                    nulls[(lamb,n,label)]=simulate_no_horse_information(
                        q0,new_fraction=lamb,effective_new_votes=n,
                        concentration=kappa,repetitions=repetitions,
                        seed=seed+10007*i+li*1000+vi*100+ci)
        physical=_build_connected_preoutcome(
            row,historical[row["race_id"]],draws=horse_draws,
            seed=seed+1009*i)
        prepared.append({"row":row,"q0":q0,"nulls":nulls,"physical":physical})
    # No JRA finishing place is read ANYWHERE in this analysis. Only
    # after all null draws and connected market candidates are generated,
    # score later displayed quotes (a proxy, not actual pool shares).
    evidence=[]
    for prepared_row in prepared:
        row=prepared_row["row"]
        ids=sorted(row["last_odds"])
        if ids!=sorted(row["first_odds"]):
            raise ValueError("HOLD_CHANGED_POOLED_HORSE_ROSTER")
        f=market_features(row)
        q1=vector(f["latest"])
        q0=prepared_row["q0"]
        tv,raw_max=_market_shape_statistics(q0,q1)
        scenarios=[]
        for (lamb,n,label),drawn in prepared_row["nulls"].items():
            kappa=dict(CONCENTRATION_SPECS)[label]
            score=null_calibration(
                drawn,q0,q1,hours=f["hours"],new_fraction=lamb,
                sample_count=n,concentration=kappa)
            scenarios.append({
                "label":label,**score,
            })
        connected={
            arm:{
                round_label:{
                    "TV_to_later_price_proxy_pp":_market_shape_statistics(
                        physical_q,q1)[0],
                    "not_an_external_asof_forecast":True,
                } for round_label,physical_q in starts.items()
            } for arm,starts in prepared_row["physical"].items()
        }
        evidence.append({
            "race_id":row["race_id"],"source_meeting_date":row["meeting_day"],
            "n_horse_entries":len(ids),
            "quote_interval_hours":f["hours"],
            "source_comparability":(
                "SAME_YAHOO_PROVIDER_TWO_QUOTE_SOURCE" if
                row["meeting_day"]=="2026-10-12" else
                "SHUKA_MIXED_PROVIDER_TIME_SEMANTICS"),
            "central_observed_quote_proxy_TV_pp":tv,
            "observed_max_abs_log_rate_per_hour":raw_max/f["hours"],
            "display_bin_only_TV_lower_bound_pp":
                quotation_TV_rounding_lower_bound(
                    row["first_odds"],row["last_odds"]),
            "conditional_exact_proxy_minimum_new_share":
                transition_accounting_lower_bound(q0,q1),
            "price_index_null_sensitivity":scenarios,
            "same_ABM_horse_to_bettor_smooth_candidates":connected,
            "no_actual_new_ballots_or_ledger_gps_observed":True,
        })
    # Group by meeting day; nominal pseudo count cases are NOT new races.
    summary={}
    for day in sorted({x["source_meeting_date"] for x in evidence}):
        cohort=[x for x in evidence if x["source_meeting_date"]==day]
        summary[day]={
            "real_races":len(cohort),
            "mean_nominal_quote_TV_pp":mean(
                x["central_observed_quote_proxy_TV_pp"] for x in cohort),
            "mean_rounding_bin_only_TV_lower_bound_pp":mean(
                x["display_bin_only_TV_lower_bound_pp"] for x in cohort),
            "mean_conditional_exact_proxy_minimum_new_share":mean(
                x["conditional_exact_proxy_minimum_new_share"] for x in cohort),
            "condition_sensitivity":[
                {
                    "assumed_lambda":lamb,"effective_N":n,
                    "noise":label,
                    "mean_conditional_TV_tail_area":mean(
                        next(q for q in x["price_index_null_sensitivity"]
                            if (q["assumed_new_fraction_of_final_pool"]==lamb
                                and q["assumed_effective_new_vote_count"]==n
                                and q["label"]==label))[
                                    "conditional_tail_area_TV_not_real_p_value"]
                        for x in cohort),
                    "n_source_races_where_exact_proxy_turnover_would_be_feasible":sum(
                        next(q for q in x["price_index_null_sensitivity"]
                            if q["assumed_new_fraction_of_final_pool"]==lamb
                            and q["assumed_effective_new_vote_count"]==n
                            and q["label"]==label)[
                                "nominal_proxy_exact_cumulative_flow_feasible_at_assumed_lambda"]
                        for x in cohort),
                    "n_source_races_with_nominal_TV_tail_below_0_05":sum(
                        next(q for q in x["price_index_null_sensitivity"]
                            if q["assumed_new_fraction_of_final_pool"]==lamb
                            and q["assumed_effective_new_vote_count"]==n
                            and q["label"]==label)[
                                "conditional_tail_area_TV_not_real_p_value"]<.05
                        for x in cohort),
                    "n_nominal_tail_below_0_05_among_proxy_flow_feasible":sum(
                        (next(q for q in x["price_index_null_sensitivity"]
                              if q["assumed_new_fraction_of_final_pool"]==lamb
                              and q["assumed_effective_new_vote_count"]==n
                              and q["label"]==label)[
                                    "conditional_tail_area_TV_not_real_p_value"]<.05)
                        and (next(q for q in x["price_index_null_sensitivity"]
                              if q["assumed_new_fraction_of_final_pool"]==lamb
                              and q["assumed_effective_new_vote_count"]==n
                              and q["label"]==label)[
                                "nominal_proxy_exact_cumulative_flow_feasible_at_assumed_lambda"])
                        for x in cohort),
                } for lamb in LAMBDAS
                  for n in EFFECTIVE_NEW_VOTE_COUNTS
                  for label,_ in CONCENTRATION_SPECS
            ],
        }
    selfcheck=heldout_null_false_alarm_check(
        prepared[0]["q0"],repetitions=repetitions,seed=seed+900003)
    return {
        "status":STATUS,
        "archived_real_races":len(evidence),
        "distinct_source_meeting_dates":len(summary),
        "horse_race_entries":sum(x["n_horse_entries"] for x in evidence),
        "source_first_quotes_are_intermediate_not_certified_opening_odds":True,
        "prior_horse_form_was_retrieved_postrace_for_some_races":True,
        "observed_exact_JRA_pool_shares_and_stake_flow_available":False,
        "price_indices_are_normalized_inverse_displayed_payout_odds":True,
        "no_horse_outcomes_loaded_even_for_scoring":True,
        "coupled_horse_to_bettor_model_reused_unmodified":True,
        "assumed_new_fraction_grid":list(LAMBDAS),
        "assumed_effective_vote_count_grid":list(EFFECTIVE_NEW_VOTE_COUNTS),
        "assumed_noise_models":[x[0] for x in CONCENTRATION_SPECS],
        "assumed_display_rounding_only_sensitivity_half_bin":
            ROUNDING_HALF_WIDTH_DECIMAL,
        "source_date_summaries":summary,
        "by_real_race_without_raw_prices":evidence,
        "synthetic_holdout_null_calibration":selfcheck,
        "posterior_or_conditional_tail_areas_not_real_market_p_values":True,
        "real_horse_informational_advantage":"HOLD",
        "real_social_contagion_or_market_criticality":"HOLD",
        "prospective_jra_winning_probability_or_bet_EV":"HOLD",
        "prior_Kikka_and_v31_holdouts_unchanged":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--null-draws",type=int,default=2000)
    p.add_argument("--horse-draws",type=int,default=80)
    p.add_argument("--output",type=Path,
        default=Path("tmp/conditional-volume-market-null.json"))
    a=p.parse_args()
    result=audit(repetitions=a.null_draws,horse_draws=a.horse_draws)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "races":result["archived_real_races"],
        "source_dates":result["distinct_source_meeting_dates"],
        "conditional_noise_holdout":result["synthetic_holdout_null_calibration"],
        "empirical_threshold":"HOLD",
    },ensure_ascii=False))


if __name__=="__main__":
    main()
