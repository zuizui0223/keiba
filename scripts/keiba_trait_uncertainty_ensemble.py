#!/usr/bin/env python3
"""Propagate repeatable-horse uncertainty to SAME horse ABM/PDE -> bettor market.

This is source-gated, synthetic until authorized same-ID GPS and market
histories have both been obtained. The approximate horse posterior comes
from source-conditional peer-relative GPS times, not independently
recovered JRA animal abilities. Its Gaussian posterior ignores residual
correlation created by shared race-relative denominators.

NO outcome labels or realized next quote enter any forecast. This is not
a Bayesian population interval, observed JRA ballot model, payout, or
proof of actual information-driven criticality.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import math

import numpy as np

from keiba_individual_trait_to_market_cascade import (
    _finite_nonnegative,
    initial_market_proxy,
    layered_vote_market,
    objective_horse_prior,
    premarket_context_log_scores,
    repeatable_traits,
    unit_weights,
)
from keiba_nonlocal_horse_pde_bettor_bridge import (
    CROWD_COEFFICIENT_M2_PER_S,
    finish_pair,
    pde_density_and_agent_check,
)

STATUS = "SYNTHETIC_OR_LOCALLY_GATED_TRAIT_UNCERTAINTY_NOT_EMPIRICAL_CALIBRATION"


def _quantiles(values):
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1 or not arr.size or not np.all(np.isfinite(arr)):
        raise ValueError("HOLD_NONFINITE_SYNTHETIC_SCENARIO_SPREAD")
    return {"mean":float(np.mean(arr)),
            "sd_across_scenario_draws":float(np.std(arr, ddof=1)) if len(arr)>1 else 0.,
            "q05_across_scenario_draws":float(np.quantile(arr,.05)),
            "q50_across_scenario_draws":float(np.quantile(arr,.5)),
            "q95_across_scenario_draws":float(np.quantile(arr,.95))}


def _market_tv(a,b):
    x=unit_weights(a)
    y=unit_weights(b)
    if x.shape!=y.shape:
        raise ValueError("HOLD_DIFFERENT_MARKET_FIELDS")
    return float(50*np.abs(x-y).sum())


def _draw_traits(traits: dict, draws: int, seed: int, *,
                 include_posterior_error: bool):
    """Independent Gaussian *approximation* for posterior trait uncertainty.

    Horse random intercept and residual uncertainties use the current
    source-conditional, method-of-moments model. Correlations of
    individual peer-relative outcomes are NOT recovered by that model.
    """
    if type(draws) is not int or not (2 <= draws <= 64):
        raise ValueError("HOLD_TRAIT_DRAW_COUNT")
    if type(seed) is not int:
        raise ValueError("HOLD_TRAIT_SEED")
    ids=traits["horse_ids"]
    p=traits["posterior"]
    if set(p) != set(ids):
        raise ValueError("HOLD_TRAIT_ROSTER_MISMATCH")
    means=[]
    std=[]
    for i in ids:
        m=p[i]["mean_relative_seconds"]
        v=p[i]["variance_seconds_squared"]
        if (not isinstance(m,(int,float)) or not math.isfinite(m) or
                not isinstance(v,(int,float)) or v<0 or not math.isfinite(v)):
            raise ValueError("HOLD_BAD_TRAIT_POSTERIOR_MOMENTS")
        means.append(float(m))
        std.append(math.sqrt(float(v)))
    rng=np.random.default_rng(seed)
    means=np.asarray(means)
    std=np.asarray(std)
    if include_posterior_error:
        samples=rng.normal(size=(draws,len(ids)))*std[None,:]+means[None,:]
    else:
        samples=np.broadcast_to(means,(draws,len(ids))).copy()
    return samples, means, std


def _prior_from_draw(effect, *, seconds_to_logweight, context):
    beta=_finite_nonnegative(seconds_to_logweight,"UNFITTED_SPEED_SCALE")
    logprior=-beta*np.asarray(effect,dtype=float)
    if context is not None:
        logprior+=np.asarray(context,dtype=float)
    if not np.all(np.isfinite(logprior)):
        raise ValueError("HOLD_NONFINITE_OBJECTIVE_HORSE_PRIOR")
    return unit_weights(np.exp(logprior-np.max(logprior)))


def _unit_mass(prior, physics):
    # The same input probability vector must drive the paired
    # crowd/no-crowd first-passage model and any optional PDE closure.
    for scenario in ("no_crowd","nonlocal_crowd"):
        x=unit_weights(physics["scenarios"][scenario]["win"])
        if not math.isclose(x.sum(),1.,abs_tol=1e-12):
            raise AssertionError("HOLD_PHYSICAL_WINS_DONT_SUM_TO_ONE")


def propagate_individual_uncertainty(
    source: dict,
    target: dict,
    *,
    observed_first_odds: Mapping,
    premarket_context_receipt: dict | None = None,
    posterior_draws: int = 16,
    physical_mc_draws: int = 90,
    seed: int = 20261026,
    include_posterior_error: bool = True,
    information_release_round: int = 1,
    prior_scale: float = 3.0,
    vote_rounds: int = 4,
    vote_seed: int | None = None,
    pde_particles: int = 0,
    pde_draws: int = 0,
    voter_shares_by_round=None,
):
    """Uncertainty propagation, fixed source and shared CRNs per arm.

    At each latent-trait draw, both physical counterfactuals share
    Gumbel/Brownian randomness. Both market counterfactuals likewise
    share voter uniforms. Across trait draws the same random seed
    is reused intentionally: the resulting draw-to-draw spread is
    primarily sensitivity to the uncertain horse intercepts rather
    than simulation-seed variation. This does NOT quantify full error.
    """
    if type(include_posterior_error) is not bool:
        raise ValueError("HOLD_INVALID_UNCERTAINTY_SCENARIO_FLAG")
    if type(physical_mc_draws) is not int or physical_mc_draws<40:
        raise ValueError("HOLD_LOW_PHYSICAL_MONTE_CARLO_SUPPORT")
    if (type(vote_rounds) is not int or vote_rounds<1 or
            type(information_release_round) is not int or
            not 1 <= information_release_round <= vote_rounds+1):
        raise ValueError("HOLD_INVALID_PUBLIC_RELEASE_TIME")
    if type(pde_draws) is not int or not 0 <= pde_draws <= 3:
        raise ValueError("HOLD_PDE_AUDIT_DRAW_LIMIT")
    if (pde_draws and (type(pde_particles) is not int or pde_particles<100)
            or pde_particles and not pde_draws):
        raise ValueError("HOLD_INCOMPLETE_PDE_CLOSURE_REQUEST")
    trait=repeatable_traits(source,target)
    ids=trait["horse_ids"]
    prior_means=objective_horse_prior(
        trait,seconds_to_logweight=prior_scale,
        prestart_objective_log_covariates=(
            premarket_context_log_scores(premarket_context_receipt,target)
            if premarket_context_receipt is not None else None))
    q0=initial_market_proxy(observed_first_odds,ids)
    samples,means,sds=_draw_traits(
        trait,posterior_draws,seed+503,
        include_posterior_error=include_posterior_error)
    raw_context=(premarket_context_log_scores(premarket_context_receipt,target)
                 if premarket_context_receipt is not None else None)
    context=(np.asarray([raw_context[i] for i in ids],dtype=float)
             if raw_context is not None else None)
    p0=[]
    sig0=[]
    sig1=[]
    markets0=[]
    markets1=[]
    tvs=[]
    delta_win=[]
    noinfo_checks=0
    pde_diagnostics=[]
    voter_seed=vote_seed if vote_seed is not None else seed+10007
    uniform_gain_trace=None
    for sample_idx,effect in enumerate(samples):
        objective=_prior_from_draw(
            effect,seconds_to_logweight=prior_scale,context=context)
        physics=finish_pair(
            objective,distance_m=target["distance_m"],
            draws=physical_mc_draws,seed=seed+7001,
            crowd_coefficient=CROWD_COEFFICIENT_M2_PER_S)
        _unit_mass(objective,physics)
        uncrowded=unit_weights(physics["scenarios"]["no_crowd"]["win"])
        crowded=unit_weights(physics["scenarios"]["nonlocal_crowd"]["win"])
        # The horse signal is an objective-conditioned full predictive
        # distribution, not an independent likelihood multiplier.
        market_no=layered_vote_market(
            q0,objective,uncrowded,seed=voter_seed,
            rounds=vote_rounds,release_step=information_release_round,
            voter_shares_by_round=voter_shares_by_round)
        market_c=layered_vote_market(
            q0,objective,crowded,seed=voter_seed,
            rounds=vote_rounds,release_step=information_release_round,
            voter_shares_by_round=voter_shares_by_round)
        for t in range(information_release_round):
            if not np.array_equal(market_no["path"][t],market_c["path"][t]):
                raise AssertionError("HOLD_HORSE_SIGNAL_PASSED_BEFORE_RELEASE")
        if information_release_round==vote_rounds+1:
            if not np.array_equal(market_no["final"],market_c["final"]):
                raise AssertionError("HOLD_HORSE_SIGNAL_AFFECTED_NEVER_MARKET")
            noinfo_checks+=1
        if uniform_gain_trace is None:
            uniform_gain_trace=[
                {"round":r["round"],
                 "uniform_null_local_gain":r["uniform_null_local_gain"],
                 "effective_new_pseudo_vote_fraction":
                     r["effective_new_pseudo_vote_fraction"],
                 "herding_fraction_assumed":
                     r["hypothetical_voter_fractions"]["herding"]}
                for r in market_no["rounds"]]
        p0.append(objective)
        sig0.append(uncrowded)
        sig1.append(crowded)
        markets0.append(market_no["final"])
        markets1.append(market_c["final"])
        tvs.append(_market_tv(market_no["final"],market_c["final"]))
        delta_win.append(_market_tv(uncrowded,crowded))
        if sample_idx < pde_draws:
            diagnostic=pde_density_and_agent_check(
                objective,particles=pde_particles,
                strength=CROWD_COEFFICIENT_M2_PER_S,
                duration_s=2.,dx=1.,dt=.05,halfwidth=25.,
                seed=seed+13000)
            pde_diagnostics.append(diagnostic)
    p0=np.asarray(p0)
    sig0=np.asarray(sig0)
    sig1=np.asarray(sig1)
    markets0=np.asarray(markets0)
    markets1=np.asarray(markets1)
    # The law of total probability: first integrate physical/voter
    # mechanisms conditioned on the horse trait, then integrate traits.
    # The statistics describe only this hypothetical approximation.
    out={
      "status":STATUS,
      "scope":"POSTERIOR_ERROR_CONDITIONAL_MODEL_ONLY",
      "animal_source_rights_externally_authenticated":False,
      "true_JRA_bettor_stakes":False,
      "source_match_required_same_horse_same_provider":True,
      "has_outcome_data":False,
      "n_horses":len(ids),
      "n_repeatable_horses":trait["repeated_source_horses"],
      "source_conditional_moment_icc":trait["source_conditional_approx_icc"],
      "posterior_draws":posterior_draws,
      "physical_draws_per_posterior":physical_mc_draws,
      "model_error_not_population_confidence_interval":True,
      "trait_posterior_independence_ignores_shared_peer_denominator":True,
      "posterior_sampling_enabled":include_posterior_error,
      "pre_market_context_used":raw_context is not None,
      "physical_pairing":"same_prior_same_Gumbel_and_Brownian_randomness",
      "voter_pairing":"same_aggregated_pseudo_voter_uniforms",
      "uniform_equilibrium_gain_trace_not_real_criticality":
          uniform_gain_trace,
      "voter_shares_time_schedule_used":voter_shares_by_round is not None,
      "initial_observed_market_not_objective":True,
      "initial_market_proxy":q0.tolist(),
      "plug_in_objective_prior":prior_means.tolist(),
      "expected_objective_prior_under_trait_error":np.mean(p0,axis=0).tolist(),
      "prior_across_trait_sd":np.std(p0,axis=0,ddof=1).tolist(),
      "expected_physical_win_signal_without_crowding":np.mean(sig0,axis=0).tolist(),
      "expected_physical_win_signal_with_crowding":np.mean(sig1,axis=0).tolist(),
      "expected_final_market_no_crowding":np.mean(markets0,axis=0).tolist(),
      "expected_final_market_with_crowding":np.mean(markets1,axis=0).tolist(),
      "market_TV_between_ensemble_mean_scenarios_pp":
          _market_tv(np.mean(markets0,axis=0),np.mean(markets1,axis=0)),
      "scenario_physical_signal_TV_pp":_quantiles(delta_win),
      "scenario_market_difference_TV_pp":_quantiles(tvs),
      "no_signal_before_release_tested_every_draw":True,
      "never_released_pairs_bitwise_identical":
          noinfo_checks==posterior_draws if information_release_round==vote_rounds+1 else None,
      "pde_diagnostic_ensemble_draws":pde_draws,
      "pde_diagnostics":pde_diagnostics,
      "original_main_REML_ICC_not_ported":True,
      "actual_market_predictive_superiority":"HOLD",
      "real_critical_market_odds":"HOLD"
    }
    assert np.isclose(sum(out["expected_objective_prior_under_trait_error"]),1,atol=1e-11)
    assert np.isclose(sum(out["expected_final_market_no_crowding"]),1,atol=1e-11)
    assert np.isclose(sum(out["expected_final_market_with_crowding"]),1,atol=1e-11)
    return out
