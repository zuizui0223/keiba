#!/usr/bin/env python3
"""Nonlocal horse ABM <-> finite-horse marginal-density PDE <-> bettor ABM.

For each horse i, the interacting physical law is
 dX_i = [16.8 + 0.10*(log(prior_i)+Gumbel_i)
         - c*(sum_{j != i} K(X_j-X_i))/(n-1)]dt + sqrt(2D)dW_i
 K(d) = exp(-d/ell)/ell for 0 < d <= radius, else 0 (ahead only).
 c is in m²/s; K has units 1/m. The agent ensemble is generated before
 any later real quote or official target result enters the score code.

Finite-horse coupled *marginal* PDE closure in comoving coordinates:
 drho_i/dt = -d_x[(delta_i-c/(n-1)*sum_{j!=i}(K_+*rho_j))rho_i]
             + D d_xx rho_i.
 This discards cross-horse spatial correlations, and conditions on
 deterministic delta_i=0.10 centered log(prior_i), excluding Gumbel. It is
 neither exact at finite n nor an empirically calibrated race-position PDE.
 Both PDE and horse ABM use the *same K, c, D* and self-exclusion law.
 The companion particle check uses fixed delta_i and NO sampled Gumbel.

The finish-time SDE has Gumbel skill uncertainty (not fitted); winner/Top3
ensembles feed the pre-existing vote_market into WIN/Top3/WIDE/trio joint
PL ranking. All voter scenarios use paired uniforms between crowd
counterfactuals. No physical arrow from the quoted odds to actual horses
is asserted; abilities may optionally come from independently sourced
but NOT historically time-attested horse records.

This module is a separate Draft model, never the v3.1 or sealed M0-M2.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from keiba_coupled_horse_market_pde import (
    ROOT, vector, vote_market, _synthetic_odds_row, MIXED_MODES,
)
from keiba_coupled_history_falsification import form_prior, history_map
from odds_threshold_regime_bridge import (
    aware, market_features, forecast_prestart, load_source_locked_panels,
    score_forecast, exact_win_top3,
)

STATUS = "RETROSPECTIVE_SYNTHETIC_FINITE_HORSE_NONLOCAL_PDE_NOT_CALIBRATED"
KERNEL_RADIUS_M = 8.0
KERNEL_DECAY_M = 3.0
CROWD_COEFFICIENT_M2_PER_S = 2.0
DIFFUSION_M2_PER_S = 0.25
START_SD_M = 2.0
SPEED_BASE_MPS = 16.8
ABILITY_LOG_WEIGHT_MPS = 0.10
MONTE_CARLO_PL_PSEUDOCOUNT = 2.0
CROWD_SCENARIOS = ("no_crowd", "nonlocal_crowd")
PRIOR_ARMS = ("initial_market", "historical_form")
VOTER_TYPES = ("independent", "herding", "information",
               "mixed", "threshold_mixed")


def ahead_kernel(gap, *, radius=KERNEL_RADIUS_M, decay=KERNEL_DECAY_M):
    """Nonnegative, ahead-only bounded interaction, K in inverse metres."""
    if radius <= 0 or decay <= 0:
        raise ValueError("HOLD_NONPOSITIVE_KERNEL_GEOMETRY")
    gap=np.asarray(gap,dtype=float)
    if not np.all(np.isfinite(gap)):
        raise ValueError("HOLD_NONFINITE_INTERHORSE_GAP")
    return np.where((gap > 0) & (gap <= radius),
                    np.exp(-np.maximum(gap,0)/decay)/decay, 0.0)


def crowd_density_agent(positions, *, active=None, radius=KERNEL_RADIUS_M,
                        decay=KERNEL_DECAY_M):
    """Ahead-neighbour density per horse; self interactions exactly zero."""
    x=np.asarray(positions,dtype=float)
    if x.ndim!=2 or x.shape[1]<5 or not np.all(np.isfinite(x)):
        raise ValueError("HOLD_BAD_FINITE_AGENT_POSITIONS")
    gap=x[:,None,:]-x[:,:,None]
    inter=ahead_kernel(gap,radius=radius,decay=decay)
    if active is not None:
        a=np.asarray(active,dtype=bool)
        if a.shape!=x.shape:
            raise ValueError("HOLD_BAD_ACTIVE_HORSE_MASK")
        inter=inter*a[:,None,:]
    return inter.sum(axis=2)/(x.shape[1]-1)


def finish_pair(prior, *, distance_m, draws=350, seed=20261025,
                crowd_coefficient=CROWD_COEFFICIENT_M2_PER_S,
                diffusion=DIFFUSION_M2_PER_S, step_s=1.0):
    """Paired no-crowd/crowd first passage with exactly shared randomness."""
    p=vector(prior)
    if not (800 <= distance_m <= 5000 and draws>=40 and step_s>0
            and 0<=diffusion<=10 and 0<=crowd_coefficient<=40):
        raise ValueError("HOLD_UNVALIDATED_FINITE_HORSE_SETTINGS")
    n=len(p)
    max_steps=int(math.ceil(distance_m/(15*step_s)))+50
    rng=np.random.default_rng(seed)
    stochastic_ability=(np.log(p)[None,:]+
                         rng.gumbel(size=(draws,n)))
    start=rng.normal(0,START_SD_M,size=(draws,n))
    brownian=rng.normal(0,math.sqrt(2*diffusion*step_s),
                        size=(max_steps,draws,n))
    speeds_base=SPEED_BASE_MPS+ABILITY_LOG_WEIGHT_MPS*stochastic_ability
    if np.any(speeds_base<=0):
        raise ValueError("HOLD_NONPOSITIVE_SYNTHETIC_SPEED")
    output={}
    for name,strength in (("no_crowd",0.0),
                          ("nonlocal_crowd",crowd_coefficient)):
        x=start.copy()
        times=np.full((draws,n),np.inf)
        for step in range(max_steps):
            active=~np.isfinite(times)
            if not active.any():
                break
            penalty=(crowd_density_agent(x,active=active)
                     if strength>0 else 0.)
            speed=speeds_base-strength*penalty
            if np.any(speed[active]<=0):
                raise ValueError("HOLD_NONPOSITIVE_INTERACTION_SPEED")
            new=x+speed*step_s+brownian[step]
            hit=active&(new>=distance_m)
            move=new[hit]-x[hit]
            if np.any(move<=0):
                raise ValueError("HOLD_INVALID_FIRST_PASSAGE_INTERPOLATION")
            times[hit]=step*step_s+(distance_m-x[hit])*step_s/move
            x[active]=new[active]
        if not np.all(np.isfinite(times)):
            raise ValueError("HOLD_FINITE_HORSE_DID_NOT_FINISH")
        rank=np.argsort(times,axis=1,kind="stable")
        win=np.bincount(rank[:,0],minlength=n)/draws
        top3=np.bincount(rank[:,:3].ravel(),minlength=n)/draws
        # Small, prior-only finite-Monte-Carlo smoothing. h-only can never
        # borrow the market q0 through this numerical safeguard.
        pl=exact_win_top3([float(v) for v in p])
        smooth_win=(draws*win+MONTE_CARLO_PL_PSEUDOCOUNT*np.asarray(pl["win"]))/(draws+MONTE_CARLO_PL_PSEUDOCOUNT)
        smooth_top=(draws*top3+MONTE_CARLO_PL_PSEUDOCOUNT*np.asarray(pl["top3"]))/(draws+MONTE_CARLO_PL_PSEUDOCOUNT)
        output[name]={
            "win":smooth_win,
            "top3":smooth_top,
            "ordered_top3":rank[:,:3],
        }
        if not (np.isclose(smooth_win.sum(),1.0,atol=1e-10)
                and np.isclose(smooth_top.sum(),3.0,atol=1e-10)):
            raise ValueError("HOLD_NONLOCAL_AGENT_PROBABILITY_MASS")
    f=output["no_crowd"]["ordered_top3"]
    g=output["nonlocal_crowd"]["ordered_top3"]
    return {
        "scenarios":output,
        "paired_prob_any_first_three_order_difference":float(
            np.mean(np.any(f!=g,axis=1))),
        "paired_prob_winner_difference":float(np.mean(f[:,0]!=g[:,0])),
        "draws":draws,
        "parameters":{"crowd_coefficient_m2ps":crowd_coefficient,
                      "diffusion_m2ps":diffusion,
                      "start_position_sd_m":START_SD_M,
                      "first_passage_step_s":step_s,
                      "kernel_radius_m":KERNEL_RADIUS_M,
                      "kernel_decay_m":KERNEL_DECAY_M},
    }


def _pde_ahead(density, dx, radius, decay):
    """Per-horse K-convolution, truncated at boundaries, no wraparound."""
    n,nx=density.shape
    max_k=min(nx-1,int(math.floor(radius/dx+1e-9)))
    ahead=np.zeros_like(density)
    for k in range(1,max_k+1):
        gap=k*dx
        weight=math.exp(-gap/decay)/decay*dx
        ahead[:,:-k]+=weight*density[:,k:]
    return ahead


def pde_density_and_agent_check(prior, *, strength=CROWD_COEFFICIENT_M2_PER_S,
                                diffusion=DIFFUSION_M2_PER_S,
                                particles=2400, duration_s=12.0,
                                dx=0.6, dt=0.10, halfwidth=36.,
                                seed=20261025):
    """Matched agent/PDE marginal law with fixed horse-specific drifts.

    PDE factorizes other horses' joint distribution. One horse of each
    species; unlike a true N->infinity limit, correlated finite-race
    interactions can make this closure inaccurate.
    """
    p=vector(prior)
    if (particles<100 or diffusion<0 or strength<0 or
            dx<=0 or dt<=0 or duration_s<=0 or halfwidth<=10 or
            len(p)>30):
        raise ValueError("HOLD_PDE_INVALID_NUMERIC_SETUP")
    steps=round(duration_s/dt)
    if not math.isclose(steps*dt,duration_s,abs_tol=1e-9):
        raise ValueError("HOLD_PDE_NONINTEGER_DURATION")
    x=np.arange(-halfwidth,halfwidth+dx/2,dx)
    if not math.isclose(x[-1],halfwidth,abs_tol=1e-9):
        raise ValueError("HOLD_PDE_INCONSISTENT_GRID_EXTENT")
    v=ABILITY_LOG_WEIGHT_MPS*(np.log(p)-np.mean(np.log(p)))
    # K <= 1/ell pointwise; this bound also applies to average others.
    speed_bound=max(abs(v))+strength/KERNEL_DECAY_M
    cfl=dt*(speed_bound/dx+2*diffusion/(dx*dx))
    if cfl>0.95:
        raise ValueError("HOLD_PDE_UNSTABLE_EXPLICIT_CFL")
    normal=np.exp(-0.5*(x/START_SD_M)**2)
    normal/=normal.sum()*dx
    rho=np.broadcast_to(normal,(len(p),len(x))).copy()
    rng=np.random.default_rng(seed)
    positions=rng.normal(0,START_SD_M,size=(particles,len(p)))
    sd=math.sqrt(2*diffusion*dt)
    for step in range(steps):
        # Physical particle law uses EXACT SAME ahead kernel, no Gumbel.
        crowd=crowd_density_agent(positions)
        positions+=(v[None,:]-strength*crowd)*dt
        if diffusion>0:
            positions+=sd*rng.standard_normal(positions.shape)
        # Mean marginal closure: exclude own horse marginal; no wrapping.
        ahead=_pde_ahead(rho,dx,KERNEL_RADIUS_M,KERNEL_DECAY_M)
        others=(np.sum(ahead,axis=0)[None,:]-ahead)/(len(p)-1)
        b=v[:,None]-strength*others
        interface=.5*(b[:,:-1]+b[:,1:])
        flux=np.zeros((len(p),len(x)+1))
        flux[:,1:-1]=(interface*np.where(interface>=0,rho[:,:-1],rho[:,1:])
                       - diffusion*np.diff(rho,axis=1)/dx)
        rho-=dt*np.diff(flux,axis=1)/dx
        if np.any(rho < -1e-10) or not np.all(np.isfinite(rho)):
            raise ValueError("HOLD_PDE_NEGATIVE_OR_NONFINITE_DENSITY")
    masses=rho.sum(axis=1)*dx
    bins=np.concatenate((x-dx/2,[x[-1]+dx/2]))
    errors=[]
    off_grid=0
    for j in range(len(p)):
        observed,_=np.histogram(positions[:,j],bins=bins)
        off_grid+=particles-int(observed.sum())
        empirical=np.cumsum(observed)/particles
        calculated=np.cumsum(rho[j])*dx
        errors.append(float(np.max(np.abs(empirical-calculated))))
    # A finite horse group builds inter-horse positional dependence. The
    # product-marginal PDE discards all such joint information.
    corr=np.corrcoef(positions,rowvar=False)
    mask=np.triu_indices(len(p),k=1)
    pair_abs_corr=float(np.mean(np.abs(corr[mask])))
    pair_signed_corr=float(np.mean(corr[mask]))
    analytic_no_crowd_cdf_error=None
    if strength==0:
        # No interactions -> each marginal has an analytical Gaussian CDF;
        # isolate PDE discretization error from particle sampling/closure.
        sigma=math.sqrt(START_SD_M**2+2*diffusion*duration_s)
        edge=x+dx/2
        analytic_no_crowd_cdf_error=max(
            float(np.max(np.abs(np.cumsum(rho[j])*dx-
                np.asarray([0.5*(1+math.erf(
                    (position-v[j]*duration_s)/(math.sqrt(2)*sigma)))
                    for position in edge]))))
            for j in range(len(p)))
    return {
        "status":"CORRELATED_FINITE_AGENT_VS_FACTORIZED_NONLOCAL_PDE_CHECK",
        "n_horse_species":len(p), "independent_replica_races":particles,
        "grid_step_m":dx,"time_step_s":dt, "duration_s":duration_s,
        "kernel_radius_m":KERNEL_RADIUS_M,"kernel_decay_m":KERNEL_DECAY_M,
        "crowd_coefficient_m2ps":strength,"diffusion_m2ps":diffusion,
        "CFL_upper_bound":float(cfl),
        "min_horse_probability_mass":float(np.min(masses)),
        "max_horse_probability_mass":float(np.max(masses)),
        "nonnegative_density":bool(np.min(rho)>=-1e-10),
        "particle_outside_grid_total_over_species":off_grid,
        "mean_KS_particle_to_PDE":float(np.mean(errors)),
        "max_KS_particle_to_PDE":float(np.max(errors)),
        "mean_abs_interhorse_position_correlation_particle":pair_abs_corr,
        "mean_signed_interhorse_position_correlation_particle":pair_signed_corr,
        "analytic_no_interaction_PDE_CDF_max_error":analytic_no_crowd_cdf_error,
        "closure_is_not_exact_for_finite_correlated_horses":True,
        "PDE_conditions_on_fixed_logprior_drift_without_Gumbel":True,
        "no_real_GPS_or_fitted_physics":True,
    }


def coupled_prestart(row, prior, *, distance_m, draws=350, seed=20261025):
    """One horse interaction law reaches the voter ABM, then joint ranks."""
    feature=market_features(row)
    ids=feature["horse_numbers"]
    market_q0=vector(feature["early"])
    input_horse_p=vector(prior)
    if len(input_horse_p)!=len(ids):
        raise ValueError("HOLD_HORSE_PRIOR_DIFFERENT_MARKET_FIELD")
    animal=finish_pair(input_horse_p,distance_m=distance_m,
                       draws=draws,seed=seed)
    states={}
    for crowd in CROWD_SCENARIOS:
        pred=animal["scenarios"][crowd]
        signal=vector(pred["win"])
        modes={}
        for mode in VOTER_TYPES:
            simulation=vote_market(market_q0,signal,mode=mode,
                    duration_hours=feature["hours"],seed=seed+390,
                    synthetic_votes_per_step=250)
            synth=_synthetic_odds_row(row,ids,simulation["final"])
            pl=forecast_prestart(synth)["predictions"]["M0_latest"]
            modes[mode]={
                "market":simulation["final"],
                "prediction":pl,
                "triggered_steps":simulation["triggered_steps"],
                "later_market_shape_TV_pp":float(
                    50*np.sum(np.abs(simulation["final"]-feature["latest"]))),
            }
        states[crowd]=modes
    # Fundamental negative controls: if voter rules see only q0, horse
    # crowding cannot change their market path under paired uniforms.
    for null in ("independent","herding"):
        if not np.array_equal(states["no_crowd"][null]["market"],
                              states["nonlocal_crowd"][null]["market"]):
            raise ValueError("HOLD_HORSE_CROWD_CAUSED_MARKET_WITHOUT_INFO_PATH")
    horse_win_shift_pp=float(50*np.sum(np.abs(
        animal["scenarios"]["nonlocal_crowd"]["win"]-
        animal["scenarios"]["no_crowd"]["win"])))
    horse_top3_rel_shift_pp=float((50/3)*np.sum(np.abs(
        animal["scenarios"]["nonlocal_crowd"]["top3"]-
        animal["scenarios"]["no_crowd"]["top3"])))
    vote_signal_market_transfer_pp={
        mode:float(50*np.sum(np.abs(
            states["nonlocal_crowd"][mode]["market"]-
            states["no_crowd"][mode]["market"])))
        for mode in VOTER_TYPES}
    if any(vote_signal_market_transfer_pp[k]!=0
           for k in ("independent","herding")):
        raise ValueError("HOLD_CAUSAL_BYPASS_OF_INFORMATION_FILTER")
    return {
        "horse_scenario":animal,
        "by_crowd_and_vote":states,
        "physical_to_market_transmission": {
            "horse_win_distribution_shift_TV_pp":horse_win_shift_pp,
            "horse_Top3_normalized_shift_TV_pp":horse_top3_rel_shift_pp,
            "market_price_index_shift_TV_pp":vote_signal_market_transfer_pp,
            "synthetic_threshold_gate_step_delta":
                (states["nonlocal_crowd"]["threshold_mixed"]["triggered_steps"]-
                 states["no_crowd"]["threshold_mixed"]["triggered_steps"]),
            "null_information_voter_effect_identically_zero":True,
        },
        "market_q0":market_q0,
        "physical_horse_prior":input_horse_p,
        "later_observed_market_only_for_shape_scoring":True,
        "same_randomness_across_crowd_counterfactuals":True,
        "no_official_outcome_read":True,
    }


def archived_six_race_audit(root=ROOT, *, draws=350, seed=20261025,
                            pde_particles=1500):
    """Source-locked retrospective; all forecasts before outcomes."""
    rows=load_source_locked_panels(root)
    histories=history_map(root)
    if len(rows)!=6 or set(histories)!={z["race_id"] for z in rows}:
        raise ValueError("HOLD_SOURCE_LOCKED_RACES_NOT_SIX")
    produced=[]
    for i,row in enumerate(rows):
        f=market_features(row)
        hs=form_prior(row,histories[row["race_id"]])
        priors={"initial_market":f["early"],
                "historical_form":hs["prior"]}
        cases={}
        for arm,prior in priors.items():
            cases[arm]=coupled_prestart(
                row,prior,distance_m=histories[row["race_id"]]["distance_m"],
                draws=draws,seed=seed+i*1009)
        # For each horse prior, verify actual same interaction kernel
        # against a *factorized*, correlation-neglecting PDE closure.
        pde={arm:pde_density_and_agent_check(
                prior,strength=CROWD_COEFFICIENT_M2_PER_S,
                particles=pde_particles,seed=seed+i*1009)
             for arm,prior in priors.items()}
        produced.append({"row":row,"history":hs,"cases":cases,"pde":pde})
    baseline={}
    for a in produced:
        row=a["row"]
        baseline[row["race_id"]]=forecast_prestart(row)["predictions"][
            "M0_latest"]
    # ONLY BELOW this line do official results enter the code.
    from odds_six_race_predictive_increment import (
        verify_official_oct12,verify_official_shuka)
    official,official_at=verify_official_oct12(root)
    shuka=verify_official_shuka(root)
    scored=[]
    for obj in produced:
        row=obj["row"]
        if row["meeting_day"]=="2026-10-12":
            if official_at <= aware(row["post_at"]):
                raise ValueError("HOLD_OFFICIAL_RESULT_TIME_TRAVEL")
            podium=official["races"][str(row["race_no"])]["positions"]
        else:
            if shuka["verified_on_jst"]<=row["meeting_day"]:
                raise ValueError("HOLD_SHUKA_SOURCE_TIME_TRAVEL")
            podium=shuka["top3"]
        f=market_features(row)
        scores={}
        for arm,res in obj["cases"].items():
            scores[arm]={}
            for crowd in CROWD_SCENARIOS:
                scores[arm][crowd]={
                    mode:score_forecast(
                        f,res["by_crowd_and_vote"][crowd][mode]["prediction"],
                        podium)
                    for mode in VOTER_TYPES}
        scored.append({"race_id":row["race_id"],"day":row["meeting_day"],
                       "baseline":score_forecast(
                           f,baseline[row["race_id"]],podium),
                       "model_scores":scores,
                       "pde":obj["pde"],
                       "cases":obj["cases"]})
    metrics=("win_log_loss","top3_brier")
    scores={arm:{crowd:{mode:{
        k:float(mean(z["model_scores"][arm][crowd][mode][k]
                     for z in scored)) for k in metrics}
        for mode in VOTER_TYPES} for crowd in CROWD_SCENARIOS}
        for arm in PRIOR_ARMS}
    transfer={arm:{
        "mean_horse_WIN_probability_TV_shift_pp":float(mean(
            z["cases"][arm]["physical_to_market_transmission"][
                "horse_win_distribution_shift_TV_pp"] for z in scored)),
        "mean_horse_Top3_relative_TV_shift_pp":float(mean(
            z["cases"][arm]["physical_to_market_transmission"][
                "horse_Top3_normalized_shift_TV_pp"] for z in scored)),
        "voter_market_response_TV_pp":{
            mode:float(mean(z["cases"][arm][
                "physical_to_market_transmission"][
                    "market_price_index_shift_TV_pp"][mode]
                for z in scored)) for mode in VOTER_TYPES},
        "sum_threshold_gate_switch_delta":sum(z["cases"][arm][
            "physical_to_market_transmission"][
                "synthetic_threshold_gate_step_delta"] for z in scored),
        "no_direct_physical_to_quoted_odds_arrow":True,
        } for arm in PRIOR_ARMS}
    physical={arm:{
        "mean_max_KS_particle_to_nonlocal_PDE":float(
            mean(z["pde"][arm]["max_KS_particle_to_PDE"] for z in scored)),
        "max_KS_all_six":max(
            z["pde"][arm]["max_KS_particle_to_PDE"] for z in scored),
        "pde_mass_min":min(
            z["pde"][arm]["min_horse_probability_mass"] for z in scored),
        "pde_mass_max":max(
            z["pde"][arm]["max_horse_probability_mass"] for z in scored),
        "average_paired_top3_order_change":float(
            mean(z["cases"][arm]["horse_scenario"][
                "paired_prob_any_first_three_order_difference"]
                 for z in scored)),
        "average_paired_winner_change":float(
            mean(z["cases"][arm]["horse_scenario"][
                "paired_prob_winner_difference"] for z in scored)),
        } for arm in PRIOR_ARMS}
    tvs={arm:{crowd:{mode:float(mean(
        z["cases"][arm]["by_crowd_and_vote"][crowd][mode][
            "later_market_shape_TV_pp"] for z in scored))
        for mode in VOTER_TYPES} for crowd in CROWD_SCENARIOS}
        for arm in PRIOR_ARMS}
    days=sorted({z["day"] for z in scored})
    date_effects={arm:{day:{
        "real_race_count":sum(z["day"]==day for z in scored),
        "delta_crowd_minus_no_crowd_information_WIN_LL":mean(
            z["model_scores"][arm]["nonlocal_crowd"]["information"][
                "win_log_loss"]-
            z["model_scores"][arm]["no_crowd"]["information"][
                "win_log_loss"]
            for z in scored if z["day"]==day),
        "delta_crowd_minus_no_crowd_information_market_TV_pp":mean(
            z["cases"][arm]["by_crowd_and_vote"]["nonlocal_crowd"][
                "information"]["later_market_shape_TV_pp"]-
            z["cases"][arm]["by_crowd_and_vote"]["no_crowd"][
                "information"]["later_market_shape_TV_pp"]
            for z in scored if z["day"]==day),
        } for day in days} for arm in PRIOR_ARMS}
    return {
        "status":STATUS,
        "official_races":len(rows),"meeting_dates":len(days),
        "horse_race_entries":sum(len(market_features(x["row"])[
            "horse_numbers"]) for x in produced),
        "actual_JRA_GPS_used":False,
        "JRA_history_retrospectively_retrieved_not_asof_attested":True,
        "physical_PDE_is_factorized_nonlocal_marginal_closure":True,
        "physical_PDE_conditions_on_fixed_drift_not_full_Gumbel":True,
        "no_fitted_horse_crowding_or_bettor_feedback_coefficients":True,
        "same_kernel_and_diffusion_for_agent_and_PDE":True,
        "horse_crowd_counterfactual_only_enters_market_via_voter_signal":True,
        "original_Kikka_M0_M1_M2_and_v31_unchanged":True,
        "baseline_observed_later_WIN_M0": {
            k:float(mean(z["baseline"][k] for z in scored))
            for k in metrics},
        "mean_race_equal_scores":scores,
        "market_index_TV_to_real_later":tvs,
        "physical_interaction_to_bettor_market_transmission":transfer,
        "nonlocal_particle_PDE_diagnostics":physical,
        "by_meeting_date":date_effects,
        "real_successful_forward_threshold_or_bet_EV":"HOLD",
        "no_result_used_for_mechanism_selection":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--draws",type=int,default=350)
    p.add_argument("--pde-particles",type=int,default=1500)
    p.add_argument("--output",type=Path,
        default=Path("tmp/nonlocal-horse-pde-coupled.json"))
    a=p.parse_args()
    result=archived_six_race_audit(
        draws=a.draws,pde_particles=a.pde_particles)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
       "status":result["status"],"n_races":result["official_races"],
       "PDE":result["nonlocal_particle_PDE_diagnostics"],
       "forecast_status":result["real_successful_forward_threshold_or_bet_EV"]},
       ensure_ascii=False))


if __name__=="__main__":
    main()
