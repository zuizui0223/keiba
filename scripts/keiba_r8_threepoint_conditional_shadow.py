#!/usr/bin/env python3
"""Kyoto R8: a strict SOURCE-TIME next-quote test of the coupled horse market.

2026-10-12 one race, three fully observed same-provider WIN quote vectors:
12:21, 13:26 (55 WIDE pairs), and independently archived 13:44.
Prior scripts analyzed all three retrospectively. This experiment constructs
pre-13:44 fixed forecasts, both market-only and PR17->19 physically coupled
horse->staged bettor ABM, *before it opens the hash-locked 13:44 target*.

The conditional no-horse-information comparison reuses PR20's 12-item
(lambda,new effective N,independent-vs-overdispersed) pseudo-ballot grid.
No assumption is selected based on target; feasibility is tagged only
AFTER q2 is revealed. Market price indices are normalized reciprocal
DISPLAYED payout odds, NOT observed voting shares, book payouts, win
probabilities or transaction records. A mathematically feasible
cumulative-pool share flow is NOT an identified actual JRA stake flow.

Horse history for this R8 was reconstructed AFTER the target race, so the
history ABM is expressly postrace diagnostic; even the honest market-only
13:26 model comparisons are RETROSPECTIVE, not preregistered forecasts.
There is just ONE TARGET market interval and NO official result is read.
Winning predictions, betting ROI, market phase transitions: HOLD.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from odds_r8_next_win_market_forecast import (
    source_only_features,construct_advance_forecast,win_proxy,
    _mid_win_vector,aware,NEXT_HORIZON_MINUTES,SOURCE_RACE,
)
from odds_r8_real_three_time_market import (
    OTHER_SOURCE, _locked, _win_vector,
)
from odds_real_multirace_archive_audit import SOURCE_SHA,read_file
from keiba_coupled_history_falsification import history_map
from keiba_conditional_volume_null_bridge import (
    LAMBDAS,EFFECTIVE_NEW_VOTE_COUNTS,CONCENTRATION_SPECS,
    simulate_no_horse_information,null_calibration,
    _market_shape_statistics,transition_accounting_lower_bound,
    quotation_TV_rounding_lower_bound,
)
from keiba_endogenous_threshold_null_bridge import preoutcome_panel,voter_path
from keiba_nonlocal_horse_pde_bettor_bridge import finish_pair
from keiba_coupled_horse_market_pde import ROOT,vector

STATUS="ONE_ARCHIVED_R8_NEXT_WIN_QUOTE_SHADOW_VOLUME_UNIDENTIFIED"
WIN_FORECASTS=("mid_quote_persistence","last_observed_win_momentum",
               "momentum_plus_mid_WIDE_node_beta025")
PHYSICAL_PRIORS=("mid_market","retrospective_past_form")
ARRIVALS=(1,3,5)
SOCIAL_RULE="smooth"
CROWDING="2.0"


def _vector_from_proxy(proxy,ids):
    if set(proxy)!=set(ids):
        raise ValueError("HOLD_R8_PROXY_ROSTER_CHANGED")
    return vector([proxy[i] for i in ids])


def build_pre_1344_forecasts(root=ROOT, *, horse_draws=120,seed=20261025):
    """Features never fetch later r8_markets_latest.json nor official podium."""
    if horse_draws<40:
        raise ValueError("HOLD_INSUFFICIENT_HORSE_ENSEMBLE")
    features=source_only_features(root)
    if features["race_id"]!=SOURCE_RACE or features["n_horses"]!=11:
        raise ValueError("HOLD_NOT_COMPLETE_R8_MIDFIELD")
    early=read_file(root,SOURCE_SHA[8][0])
    mid=read_file(root,SOURCE_SHA[8][1])
    mid_win=_mid_win_vector(mid)
    ids=sorted(mid_win)
    if set(ids)!=set(features["last_market_q"]):
        raise ValueError("HOLD_R8_CROSSPOOL_AND_WIN_ROSTER")
    signal_cutoff=aware(features["feature_latest_published"])
    mid_received=aware(features["feature_later_market_received"])
    future_nominal=signal_cutoff+__import__("datetime").timedelta(
        minutes=NEXT_HORIZON_MINUTES)
    race_post=aware(early["start_jst"])
    if not (signal_cutoff<=mid_received<future_nominal<race_post):
        raise ValueError("HOLD_R8_NOT_KNOWN_BEFORE_FORECAST_HORIZON")
    historical=history_map(root)[SOURCE_RACE]
    # A synthetic placeholder for the *future* later quote is explicitly
    # the mid WIN quotes themselves: never the genuine 13:44 target.
    # The claimed 18-minute horizon is a retrospective fixed illustration.
    synthetic_row={
        "race_id":SOURCE_RACE,
        "race_no":8,
        "meeting_day":"2026-10-12",
        "first_odds":dict(mid_win),
        "last_odds":dict(mid_win),
        "initial_quote_at":signal_cutoff.isoformat(),
        "latest_quote_at":future_nominal.isoformat(),
        "post_at":race_post.isoformat(),
    }
    physical=preoutcome_panel(
        synthetic_row,_vector_from_proxy(features["last_market_q"],ids),
        distance_m=historical["distance_m"],
        draws=horse_draws,seed=seed)
    from keiba_coupled_history_falsification import form_prior
    h=form_prior(synthetic_row,historical)
    physical_h=preoutcome_panel(
        synthetic_row,h["prior"],
        distance_m=historical["distance_m"],
        draws=horse_draws,seed=seed)
    scenarios={
        "mid_quote_persistence":features["last_market_q"],
        "last_observed_win_momentum":construct_advance_forecast(
            features,beta_momentum=1.,beta_node=0.),
        "momentum_plus_mid_WIDE_node_beta025":construct_advance_forecast(
            features,beta_momentum=1.,beta_node=.25),
    }
    # SOURCE-ALIGNED JOINT CROSSPOOL SIGNAL (an additional hypothetical
    # mechanism, not proof that WIDE's displayed quote was public/atomic).
    # Inject the 13:26 WIDE residual ONCE as a tilt of the physical horse
    # signal, then run the EXACT SAME four-step synthetic bettor ABM.
    # A one-horse cyclic node reassignment is a fixed placebo.
    midmarket=_vector_from_proxy(features["last_market_q"],ids)
    nodes=np.asarray([features["wide_extra_horse_node"][i] for i in ids],
                     dtype=float)
    if not np.all(np.isfinite(nodes)) or np.max(np.abs(nodes))>10:
        raise ValueError("HOLD_R8_NONFINITE_OR_EXPLOSIVE_WIDE_HORSE_NODES")
    candidates=(("mid_market",physical,midmarket),
                ("retrospective_past_form",physical_h,vector(h["prior"])))
    for label,model,initial_prior in candidates:
        # Reuses the same physical nonlocal kernel/D/draws from PR17 as
        # preoutcome_panel; only the subsequent WIDE residual gate differs.
        horse=finish_pair(
            initial_prior,distance_m=historical["distance_m"],
            draws=horse_draws,seed=seed,crowd_coefficient=2.)
        base_signal=vector(
            horse["scenarios"]["nonlocal_crowd"]["win"])
        for arrival in ARRIVALS:
            control=model["models"][CROWDING][arrival][SOCIAL_RULE]["market"]
            scenarios[f"coupled_{label}_smooth_c2_signal_round{arrival}"]=control
            baseline_voter=voter_path(
                midmarket,base_signal,policy=SOCIAL_RULE,
                duration_hours=NEXT_HORIZON_MINUTES/60,
                arrival=arrival,seed=seed+390)["final"]
            if not np.allclose(control,baseline_voter,rtol=0,atol=1e-13):
                raise ValueError("HOLD_CROSSPOOL_CONTROL_CHANGED_UNDER_SAME_HORSE_MODEL")
            for origin,node in (("WIDE_residual",nodes),
                                ("WIDE_node_rotated_placebo",np.roll(nodes,1))):
                modified_signal=vector(base_signal*np.exp(
                    .25*(node-np.max(node))))
                informed=voter_path(
                    midmarket,modified_signal,policy=SOCIAL_RULE,
                    duration_hours=NEXT_HORIZON_MINUTES/60,
                    arrival=arrival,seed=seed+390)["final"]
                scenarios[
                    f"coupled_{label}_smooth_c2_{origin}_beta025_round{arrival}"
                ]=informed
    predictions={
        label:_vector_from_proxy(proxy,ids)
        if isinstance(proxy,dict) else vector(proxy)
        for label,proxy in scenarios.items()}
    if any(len(v)!=len(ids) or not np.isclose(v.sum(),1,atol=1e-12)
           for v in predictions.values()):
        raise ValueError("HOLD_R8_CANDIDATE_INVALID_MASS")
    return {
        "status":"EARLY_AND_MIDDLE_SOURCE_ONLY_BEFORE_TARGET_UNOPENED",
        "ids":ids,"nominal_cutoff":signal_cutoff,
        "mid_received":mid_received,
        "first_source_published":aware(features["feature_first_published"]),
        "nominal_next_market_publication":future_nominal,
        "official_post":race_post,
        "source_price_q0":_vector_from_proxy(
            features["earlier_market_q"],ids),
        "source_price_qmid":_vector_from_proxy(
            features["last_market_q"],ids),
        "mid_original_displayed_win_prices":mid_win,
        "candidate_indices":predictions,
        "mid_wide_full_55_pair_source_already_checked":True,
        "horse_history_source_received_pre_cutoff_proven":False,
        "PR17_horse_to_staged_PR19_social_market_connected":True,
        "mid_WIDE_node_feeds_same_bettor_ABM_after_horse_agent_signal":True,
        "rotated_mid_WIDE_node_negative_control_in_same_ABM":True,
        "no_target_quote_or_winner_used_by_candidate_forecasts":True,
    }


def generate_nulls(prepared, *, repetitions=2000,seed=20261025):
    """Only qmid enters the no-horse-signal pseudo-vote null."""
    q=prepared["source_price_qmid"]
    if not isinstance(q,np.ndarray):
        raise ValueError("HOLD_R8_MID_PRICE_INDEX_MISSING")
    simulations={}
    for j,lam in enumerate(LAMBDAS):
        for k,n in enumerate(EFFECTIVE_NEW_VOTE_COUNTS):
            for z,(label,kappa) in enumerate(CONCENTRATION_SPECS):
                simulations[(lam,n,label)]=simulate_no_horse_information(
                    q,new_fraction=lam,effective_new_votes=n,
                    concentration=kappa,repetitions=repetitions,
                    seed=seed+1009*j+100*k+z)
    return simulations


def validate_later_quote(root=ROOT, *, prepared):
    """Source-locked target opened ONLY after candidate/null generation."""
    later=_locked(*OTHER_SOURCE["late_all"],root=root)
    if (later["race_id"]!=SOURCE_RACE or later["horse_count"]!=11):
        raise ValueError("HOLD_WRONG_THIRD_POINT_R8_RACE")
    quote=later["markets"]["win"]
    pub=aware(quote["updated_at_jst"])
    received=aware(quote["observed_at_utc"])
    if not (prepared["mid_received"]<
            pub==prepared["nominal_next_market_publication"]<=
            received<prepared["official_post"]):
        raise ValueError("HOLD_R8_NEXT_SOURCE_PUBLICATION_OR_RECEIPT_ORDER")
    if not quote["source_url"].startswith(
            "https://sports.yahoo.co.jp/keiba/"):
        raise ValueError("HOLD_R8_FUTURE_QUOTE_DIFFERENT_PROVIDER")
    prices=_win_vector(quote["quotes"])
    if set(prices)!=set(prepared["ids"]):
        raise ValueError("HOLD_R8_FUTURE_QUOTE_RUNNER_DIFFERENCE")
    return prices


def _tail_class(rows):
    """Only a robust descriptive property of a stipulated grid, NOT a p-value.

    Ignore nominal exact-share-INFEASIBLE lambda scenarios *only if* one
    accepts the strong and unverified assumption that 1/quote is a true
    pool share. Do NOT tune a forecast/nominal lambda using this filter.
    """
    eligible=[r for r in rows if r[
        "hypothetical_exact_proxy_new_fraction_is_simplex_feasible"]]
    calls=[r["conditional_tail_TV_not_real_p_value"]<.05 for r in eligible]
    if not calls:
        name="HOLD_NO_FEASIBLE_EXACT_PROXY_GRID_CELL"
    elif all(calls):
        name="ALL_FEASIBLE_ASSUMED_NOISE_MODELS_IN_TOP_FIVE_PERCENT_TAIL"
    elif not any(calls):
        name="NO_FEASIBLE_ASSUMED_NOISE_MODEL_IN_TOP_FIVE_PERCENT_TAIL"
    else:
        name="ASSUMPTION_DEPENDENT"
    return {
        "descriptive_exact_price_proxy_grid_status":name,
        "n_predeclared_noise_models":len(rows),
        "n_nominal_proxy_flow_feasible":len(eligible),
        "n_feasible_conditional_tail_below_005":sum(calls),
        "cannot_infer_real_p_value_or_information_shock":True,
    }


def score_source_only_forecasts(prepared, target_prices, nulls):
    ids=prepared["ids"]
    future_q=_vector_from_proxy(win_proxy(target_prices),ids)
    qmid=prepared["source_price_qmid"]
    qearly=prepared["source_price_q0"]
    score={}
    for name,candidate in prepared["candidate_indices"].items():
        p=vector(candidate)
        score[name]={
            "next_WIN_price_proxy_TV_pp":float(
                50*np.sum(np.abs(p-future_q))),
            "next_WIN_price_proxy_KL_nats":float(
                np.sum(future_q*np.log(future_q/p))),
            "uses_official_finish_label_for_prediction":False,
        }
    null_score=[]
    interval_hours=NEXT_HORIZON_MINUTES/60
    for (lam,n,label),distribution in nulls.items():
        calib=null_calibration(
            distribution,qmid,future_q,hours=interval_hours,
            new_fraction=lam,sample_count=n,
            concentration=dict(CONCENTRATION_SPECS)[label])
        null_score.append({
            "hypothetical_new_fraction":lam,
            "hypothetical_effective_vote_count":n,
            "noise_family":label,
            "conditional_tail_TV_not_real_p_value":calib[
                "conditional_tail_area_TV_not_real_p_value"],
            "conditional_tail_max_statistic_not_real_p_value":calib[
                "conditional_tail_area_max_search_not_real_p_value"],
            "hypothetical_exact_proxy_new_fraction_is_simplex_feasible":
                calib[
                  "nominal_proxy_exact_cumulative_flow_feasible_at_assumed_lambda"],
            "null_TV_95pct_pp":calib["null_TV_95pct_pp"],
        })
    null_score.sort(key=lambda v:(v["hypothetical_new_fraction"],
                                  v["hypothetical_effective_vote_count"],
                                  v["noise_family"]))
    observed_prev_TV=float(50*np.sum(np.abs(qmid-qearly)))
    observed_next_TV=float(50*np.sum(np.abs(future_q-qmid)))
    min_lambda=transition_accounting_lower_bound(qmid,future_q)
    rounding=quotation_TV_rounding_lower_bound(
        prepared["mid_original_displayed_win_prices"],target_prices)
    prev_hr=(prepared["nominal_cutoff"]-
             prepared["first_source_published"]).total_seconds()/3600
    return {
        "status":"RETROSPECTIVE_NEXT_QUOTE_SINGLE_RACE_NOT_HOLDOUT",
        "n_real_races":1,
        "n_horses":len(ids),
        "mid_source_cutoff":prepared["nominal_cutoff"].isoformat(),
        "mid_received_at":prepared["mid_received"].isoformat(),
        "later_quote_update_at":prepared[
            "nominal_next_market_publication"].isoformat(),
        "fixed_retrospective_18min_horizon_NOT_precommitted_externally":True,
        "source_provider_same_all_three_quote_points":True,
        "full_55_WIDE_pair_mid_source_not_atomic_pool_receipt":True,
        "actual_market_votes_or_pool_size_observed":False,
        "previous_65minute_interval_TV_pp":observed_prev_TV,
        "next_18minute_interval_TV_pp":observed_next_TV,
        "previous_65minute_quote_TV_rate_pp_per_hour":
            observed_prev_TV/prev_hr,
        "next_18minute_quote_TV_rate_pp_per_hour":
            observed_next_TV/interval_hours,
        "display_0_05_half_bin_conditional_lower_bound_TV_pp":rounding,
        "next_interval_exact_proxy_minimum_new_fraction":min_lambda,
        "candidate_forecast_scores":score,
        "null_condition_sensitivity":null_score,
        "null_robustness_only_under_unverified_exact_share_proxy":
            _tail_class(null_score),
        "same_source_price_and_horse_bettor_ABM_comparison_only":True,
        "historical_form_was_retrieved_after_2026_target":True,
        "future_race_outcome_or_positive_EV_inferred":False,
        "market_criticality_or_information_arrival_inferred":False,
    }


def audit(root=ROOT, *, repetitions=2000,horse_draws=120,seed=20261025):
    prepared=build_pre_1344_forecasts(root,horse_draws=horse_draws,
                                     seed=seed)
    nulls=generate_nulls(prepared,repetitions=repetitions,seed=seed)
    # Only NOW open the entire archived 13:44 document.
    later_prices=validate_later_quote(root,prepared=prepared)
    return score_source_only_forecasts(prepared,later_prices,nulls)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--null-draws",type=int,default=2000)
    p.add_argument("--horse-draws",type=int,default=120)
    p.add_argument("--output",type=Path,
        default=Path("tmp/kyoto8-conditional-next-market-shadow.json"))
    args=p.parse_args()
    r=audit(repetitions=args.null_draws,horse_draws=args.horse_draws)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":r["status"],"race_count":r["n_real_races"],
        "max_price_movement_last_18min_pp":r[
            "next_18minute_interval_TV_pp"],
        "robustness":r[
            "null_robustness_only_under_unverified_exact_share_proxy"][
                "descriptive_exact_price_proxy_grid_status"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
