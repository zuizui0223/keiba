#!/usr/bin/env python3
"""Individual GPS repeatability -> horse ABM/PDE -> delayed bettor ABM.

EXPERIMENTAL METHODOLOGY, NOT AN OBSERVATION OF JRA HORSE PERSONALITY
OR JRA BETTOR ACTIONS. All original animal and market records must be
source-authorized and received before a target market cutoff; neither
first-GPS timing nor horse traits from Racing Queensland are silently
transferred to unrelated JRA horse IDs.

The *observed* early q0 is already social: it is NEVER used to estimate
the independent horse trait. New synthetic information cannot influence
voters before its release round. The mathematical instability boundary
is a Jacobian property, not an odds=10 price gate.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import math
from typing import Mapping

import numpy as np

from keiba_nonlocal_horse_pde_bettor_bridge import (
    CROWD_COEFFICIENT_M2_PER_S,
    finish_pair,
    pde_density_and_agent_check,
)

SOURCE_SCHEMA = "KEIBA_SAME_HORSE_GPS_REPEATABILITY_HISTORY_V1"
TRIAL_STATUS = "SYNTHETIC_INTEGRATION_ONLY_NOT_A_REAL_HORSE_OR_MARKET_INFERENCE"
AGENT_TYPES = ("fundamental", "herding", "informed")
MIN_RACE_TIMED_PEERS = 4


def _clock(s: str) -> datetime:
    if not isinstance(s, str):
        raise ValueError("HOLD_INVALID_TIME")
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("HOLD_NO_OFFSET_AWARE_ASOF")
    return t


def unit_weights(a):
    x = np.asarray(a, dtype=float)
    if (x.ndim != 1 or x.size < 4 or
            not np.all(np.isfinite(x)) or np.min(x) <= 0):
        raise ValueError("HOLD_INVALID_PROBABILITY_WEIGHTS")
    return x / x.sum()


def _finite_nonnegative(v, name):
    if type(v) not in (float, int) or not math.isfinite(v) or v < 0:
        raise ValueError(f"HOLD_INVALID_{name}")
    return float(v)


def _target(target: dict) -> tuple[list[str], datetime]:
    required = ("source_system", "horse_ids", "asof_jst",
                "initial_market_published_at_jst",
                "initial_market_received_at_jst",
                "first_marker_m", "distance_m", "race_class")
    if any(k not in target for k in required):
        raise ValueError("HOLD_TARGET_CONTEXT_INCOMPLETE")
    ids = target["horse_ids"]
    if (not isinstance(ids, list) or len(ids) < 5 or len(ids) > 30
            or any(not isinstance(i, str) or not i for i in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError("HOLD_INVALID_TARGET_HORSE_IDENTITIES")
    t = _clock(target["asof_jst"])
    quote_pub = _clock(target["initial_market_published_at_jst"])
    quote_recv = _clock(target["initial_market_received_at_jst"])
    if not quote_pub <= quote_recv <= t:
        raise ValueError("HOLD_INITIAL_MARKET_SOURCE_CLOCK_ORDER")
    if (not isinstance(target["source_system"], str)
            or not target["source_system"]
            or type(target["first_marker_m"]) is not int
            or target["first_marker_m"] <= 0
            or type(target["distance_m"]) is not int
            or target["distance_m"] < 800
            or target["distance_m"] > 5000
            or not target["race_class"]):
        raise ValueError("HOLD_UNSUPPORTED_TARGET_CONTEXT")
    # The independent horse information must predate the very first
    # publicly quoted market snapshot, not just this later forecast.
    return ids, quote_pub


def repeatable_traits(source: dict, target: dict, *, min_dates=3):
    """A source-conditional empirical-Bayes horse random intercept.

    Response = first GPS seconds minus other observed timed horses'
    mean in the SAME race. This is NOT focal absolute speed, nor a
    causal competitor response. The simple method-of-moments variance
    estimator and normal shrinkage are uncalibrated, not identical to
    main's race-fixed REML ICC or an inferred inherited personality.
    """
    ids, cutoff = _target(target)
    if source.get("schema") != SOURCE_SCHEMA:
        raise ValueError("HOLD_INCORRECT_SOURCE_SCHEMA")
    if (source.get("source_system") != target["source_system"]
            or source.get("rights_checked_locally") is not True
            or not isinstance(source.get("records"), list)):
        raise ValueError("HOLD_SOURCE_RIGHTS_OR_IDENTITIES")
    # All historical source receipts must precede the FIRST observed
    # market quote publication, even if the target forecast is later.
    # No measured GPS from other providers / unrelated animal IDs may
    # be "ported" to this target's identities.
    if source.get("authenticated_publisher_clock") is not True:
        raise ValueError("HOLD_ORIGINAL_HISTORY_CLOCK_UNAUTHENTICATED")
    if any(k in source for k in ("target_finish", "winner", "market_odds",
                                  "postrace_outcome")):
        raise ValueError("HOLD_TARGET_OUTCOME_OR_ODDS_IN_TRAIT_SOURCE")
    by_race = defaultdict(list)
    individual_days = defaultdict(set)
    for row in source["records"]:
        keys = ("source_system", "horse_id", "race_id", "race_day",
                "received_at", "first_marker_m", "distance_m",
                "race_class", "first_section_seconds")
        if any(k not in row for k in keys):
            raise ValueError("HOLD_INCOMPLETE_GPS_ROW")
        dt = _clock(row["race_day"])
        recv = _clock(row["received_at"])
        if not dt < recv < cutoff:
            raise ValueError("HOLD_TARGET_OR_FUTURE_GPS_DATA_LEAK")
        if row["source_system"] != target["source_system"]:
            raise ValueError("HOLD_CROSS_SOURCE_HORSE_ID")
        if (not isinstance(row["horse_id"], str) or
                not isinstance(row["race_id"], str)):
            raise ValueError("HOLD_INVALID_HISTORY_ID")
        if (type(row["first_section_seconds"]) not in (float,int)
                or not math.isfinite(row["first_section_seconds"])
                or row["first_section_seconds"] <= 0):
            raise ValueError("HOLD_INVALID_GPS_SECONDS")
        if (row["first_marker_m"] != target["first_marker_m"]
                or row["distance_m"] != target["distance_m"]
                or row["race_class"] != target["race_class"]):
            # All observations must describe the SAME measured context,
            # not silently combine 150m and 200m or classes.
            raise ValueError("HOLD_NOT_SAME_GPS_MARKER_DISTANCE_CLASS")
        racekey=(row["race_day"],row["race_id"])
        by_race[racekey].append(row)
        key=(row["horse_id"],row["race_day"])
        if row["race_id"] in individual_days[key]:
            raise ValueError("HOLD_DUPLICATE_HORSE_RACE")
        individual_days[key].add(row["race_id"])
    if len(by_race) < min_dates or len({r[0] for r in by_race}) < min_dates:
        raise ValueError("HOLD_TOO_FEW_INDEPENDENT_SOURCE_DATES")
    residuals=defaultdict(list)
    counted_races=0
    for key, rows in by_race.items():
        horses=[row["horse_id"] for row in rows]
        if len(horses) < MIN_RACE_TIMED_PEERS or len(horses) != len(set(horses)):
            raise ValueError("HOLD_INCOMPLETE_OR_DUPLICATE_RACE_GPS_PEERS")
        values=np.asarray([row["first_section_seconds"] for row in rows])
        total=values.sum()
        for r,val in zip(rows,values):
            # current horse's absolute time is held fixed in this subtraction
            y=float(val-(total-val)/(len(values)-1))
            residuals[r["horse_id"]].append((r["race_day"],y))
        counted_races+=1
    eligible={i:r for i,r in residuals.items()
              if len({day for day,_ in r})>=2}
    if len(eligible) < 5:
        raise ValueError("HOLD_TOO_FEW_REPEATED_HORSE_IDS")
    # The same horse must occur on separate historical dates: no
    # pseudo-replication across duplicates or alternative GPS markers.
    hmeans={i:float(np.mean([v for _,v in r]))
            for i,r in eligible.items()}
    df=sum(len(r)-1 for r in eligible.values())
    if df<=0:
        raise ValueError("HOLD_UNIDENTIFIABLE_WITHIN_HORSE_VARIANCE")
    evar=sum((v-hmeans[i])**2 for i,r in eligible.items()
             for _,v in r)/df
    if evar<=0 or not math.isfinite(evar):
        raise ValueError("HOLD_NO_MEASUREMENT_VARIANCE")
    # Exploratory unbalanced-count method of moments, not a REML fit.
    bvar=max(0.0,float(np.var(list(hmeans.values()),ddof=1))-
             evar*float(np.mean([1/len(v) for v in eligible.values()])))
    icc=bvar/(bvar+evar)
    posterior={}
    for i in ids:
        obs=eligible.get(i,[])
        n=len(obs)
        if n and bvar>0:
            factor=n*bvar/(n*bvar+evar)
            est=factor*hmeans[i]
            pv=bvar*evar/(n*bvar+evar)
        else:
            est=0.0
            pv=bvar
        posterior[i]={"mean_relative_seconds":float(est),
                      "variance_seconds_squared":float(pv),
                      "n_historical_dates":n,
                      "has_repeat_support":n>=2}
    return {
        "status":"SOURCE_CONDITIONAL_RANDOM_INTERCEPT_MOMENTS_NOT_HERITABILITY",
        "horse_ids":ids, "posterior":posterior,
        "source_races":counted_races,
        "distinct_source_days":len({day for day,_ in by_race}),
        "repeated_source_horses":len(eligible),
        "residual_variance_seconds_squared":float(evar),
        "horse_effect_variance_seconds_squared":float(bvar),
        "source_conditional_approx_icc":float(icc),
        "is_original_main_RQ_REML_ICC":False,
        "target_context_compatible":True,
        "underlying_absolute_or_relative_speed_causal":False,
    }


def objective_horse_prior(traits: dict, *, seconds_to_logweight=3.0,
                          prestart_objective_log_covariates=None):
    """Independent of market q0; unknown conversion coefficients are scenario-only."""
    scale = _finite_nonnegative(seconds_to_logweight,"UNFITTED_SPEED_CONVERSION")
    ids=traits["horse_ids"]
    x=np.asarray([-scale*traits["posterior"][i]["mean_relative_seconds"]
                  for i in ids],dtype=float)
    if prestart_objective_log_covariates is not None:
        # Inputs may encode going, distance, jockey, condition, etc. but
        # MUST be fitted/published prior to q0. Never treat as verified
        # quantitative biology without its original source contract.
        if set(prestart_objective_log_covariates) != set(ids):
            raise ValueError("HOLD_PRESTART_OBJECTIVE_COVARIATES_ROSTER")
        vals=np.array([prestart_objective_log_covariates[i] for i in ids])
        if not np.all(np.isfinite(vals)):
            raise ValueError("HOLD_NONFINITE_OBJECTIVE_COVARIATE")
        x+=vals
    return unit_weights(np.exp(x-np.max(x)))



def premarket_context_log_scores(receipt: dict, target: dict):
    """Use only independently prepared objective features known before q0.

    The feature log scores are outputs of an *earlier* context model, not
    estimates of weather, ground or jockey coefficients by this script.
    Timestamps and rights are caller supplied, not external proof.
    """
    ids,_ = _target(target)
    if (receipt.get("schema") != "KEIBA_PUBLISHED_OBJECTIVE_CONTEXT_V1"
            or receipt.get("rights_checked_locally") is not True
            or receipt.get("target_source_system") != target["source_system"]
            or not isinstance(receipt.get("feature_names"),list)):
        raise ValueError("HOLD_UNAUTHORIZED_OBJECTIVE_CONTEXT_RECEIPT")
    allowed={"past_form","gps","track","going","weather","jockey",
             "distance","body_condition","layoff"}
    f=receipt["feature_names"]
    if not f or len(set(f))!=len(f) or not set(f).issubset(allowed):
        raise ValueError("HOLD_UNAPPROVED_CONTEXT_OR_ODDS_FEATURE")
    quote_pub=_clock(target["initial_market_published_at_jst"])
    pub=_clock(receipt["source_published_at_jst"])
    received=_clock(receipt["source_received_at_jst"])
    frozen=_clock(receipt["feature_model_frozen_at_jst"])
    if not frozen <= pub <= received < quote_pub:
        raise ValueError("HOLD_CONTEXT_NOT_KNOWN_BEFORE_FIRST_MARKET_QUOTE")
    if any(k in receipt for k in ("odds", "market_q0", "market_share",
                                   "target_finish", "target_winner")):
        raise ValueError("HOLD_MARKET_OR_FUTURE_TARGET_CONTAMINATES_CONTEXT")
    scores=receipt.get("objective_log_score_by_horse_id")
    if not isinstance(scores,dict) or set(scores)!=set(ids):
        raise ValueError("HOLD_OBJECTIVE_CONTEXT_ROSTER_MISMATCH")
    if any(type(x) not in (int,float) or not math.isfinite(x)
           for x in scores.values()):
        raise ValueError("HOLD_NONFINITE_INDEPENDENT_CONTEXT_SCORES")
    return {i:float(scores[i]) for i in ids}


def initial_market_proxy(odds: Mapping, horse_ids: list[str]):
    """Observed early odds are ALREADY crowdsourced, NEVER horse traits."""
    if set(odds) != set(horse_ids):
        raise ValueError("HOLD_MARKET_TARGET_ROSTER_DIFFERENT")
    if any(type(odds[i]) not in (int,float) or odds[i]<=1
           or not math.isfinite(odds[i]) for i in horse_ids):
        raise ValueError("HOLD_INVALID_INITIAL_MARKET_ODDS")
    return unit_weights(np.array([1/odds[i] for i in horse_ids]))


def _herding_index(q, gamma):
    gamma=_finite_nonnegative(gamma,"HERDING_POWER")
    return unit_weights(q**gamma)


def layered_vote_market(q0, objective, horse_signal, *,
                        voter_shares=None, gamma=1.0,
                        release_step=1, rounds=4, pool_size=3000,
                        votes_per_round=250, seed=20261026):
    """Objective information, feedback, and released news are three channels.

    'fundamental' voters use ONLY objective form; 'herding' voters
    use ONLY the already visible market q_t; 'informed' bettors
    use objective and new horse signal AFTER its public release.
    Counterfactuals use the same per-round uniforms.
    """
    q0=unit_weights(q0)
    objective=unit_weights(objective)
    horse_signal=unit_weights(horse_signal)
    n=len(q0)
    if not (len(objective)==len(horse_signal)==n
            and type(release_step) is int
            and type(rounds) is int and 1<=release_step<=rounds+1
            and rounds>=1 and pool_size>0 and votes_per_round>0):
        raise ValueError("HOLD_MARKET_SHAPE_OR_INFORMATION_CLOCK")
    shares=voter_shares or {"fundamental":.25,"herding":.50,"informed":.25}
    if set(shares)!=set(AGENT_TYPES) or any(
            type(shares[k]) not in (int,float) or shares[k]<0
            or not math.isfinite(shares[k]) for k in AGENT_TYPES
        ) or not math.isclose(sum(shares.values()),1,abs_tol=1e-12):
        raise ValueError("HOLD_INVALID_HETEROGENEOUS_VOTER_SHARES")
    counts={}
    remaining=votes_per_round
    for kind in AGENT_TYPES[:-1]:
        counts[kind]=int(votes_per_round*shares[kind])
        remaining-=counts[kind]
    counts[AGENT_TYPES[-1]]=remaining
    rng=np.random.default_rng(seed)
    pool=q0*pool_size
    paths=[q0.copy()]
    contributions=[]
    for step in range(1,rounds+1):
        current=unit_weights(pool)
        available=(step>=release_step)
        probabilities={
            "fundamental":objective,
            "herding":_herding_index(current,gamma),
            "informed":unit_weights(objective*horse_signal if available
                                    else objective),
        }
        new=np.zeros(n,dtype=int)
        for kind in AGENT_TYPES:
            draws=rng.random(counts[kind])
            assigned=np.searchsorted(np.cumsum(probabilities[kind]),
                                     draws,side="right")
            new+=np.bincount(np.minimum(assigned,n-1),minlength=n)
        pool+=new
        paths.append(unit_weights(pool))
        contributions.append({"round":step,"new_votes":int(new.sum()),
                              "horse_information_visible":available})
    if not math.isclose(pool.sum(),pool_size+rounds*votes_per_round,
                        rel_tol=0,abs_tol=1e-8):
        raise AssertionError("HOLD_CUMULATIVE_VOTE_ACCOUNTING")
    return {"initial_market":q0,"path":paths,"final":paths[-1],
            "assumed_pool_votes":pool_size,
            "assumed_next_votes":rounds*votes_per_round,
            "voter_shares":shares,"beta_social":gamma,
            "information_first_visible_round":release_step,
            "rounds":contributions,"has_real_bettor_transactions":False}


def theoretical_gain(*, herding_fraction, gamma, new_vote_fraction):
    """Uniform no-news simplex tangent gain in deterministic mean-field.

    Only the social fraction depends on current q in this 3-type law.
    For the deterministic one-step mixture,
    G = (1-lambda) + lambda * f_herding * gamma.
    Hence local neutrality at gamma=1/f_herding (when lambda>0).
    This is NOT an empirically detected 'critical horse odds'.
    """
    f=_finite_nonnegative(herding_fraction,"HERD_FRACTION")
    g=_finite_nonnegative(gamma,"HERD_GAMMA")
    l=_finite_nonnegative(new_vote_fraction,"NEW_VOTE_FRACTION")
    if f>1 or l>1:
        raise ValueError("HOLD_INVALID_FRACTIONS")
    gain=(1-l)+l*f*g
    return {"linear_gain":float(gain),
            "neutral_social_exponent":float(1/f) if f>0 and l>0 else None,
            "regime":("amplifying" if gain>1+1e-12 else
                      "damping" if gain<1-1e-12 else "neutral"),
            "critical_absolute_win_odds":None,
            "only_uniform_no_news_mean_field":True,
            "not_observed_JRA_phase_transition":True}



def deterministic_market_step(q, objective, signal, *,
                              voter_shares=None, gamma=1.0,
                              new_vote_fraction=.2):
    """Expected cumulative-vote update, free of Monte Carlo ballot noise.

    This is a stylized one-step mean-field transformation in relative
    SUPPORT. It does not reconstruct JRA observed stake amounts or payout.
    """
    q=unit_weights(q)
    obj=unit_weights(objective)
    news=unit_weights(signal)
    if len(q)!=len(obj) or len(q)!=len(news):
        raise ValueError("HOLD_UNALIGNED_DETERMINISTIC_INFO")
    f=voter_shares or {"fundamental":.25,"herding":.5,"informed":.25}
    if (set(f)!=set(AGENT_TYPES) or any(
          type(f[k]) not in (int,float) or f[k]<0 or not math.isfinite(f[k])
          for k in AGENT_TYPES)
          or not math.isclose(sum(f.values()),1,abs_tol=1e-12)):
        raise ValueError("HOLD_INVALID_EXPECTED_VOTER_MIX")
    lam=_finite_nonnegative(new_vote_fraction,"NEW_SHARE")
    if lam>1:
        raise ValueError("HOLD_INVALID_LAMBDA")
    fchoice=(f["fundamental"]*obj+
             f["herding"]*_herding_index(q,gamma)+
             f["informed"]*unit_weights(obj*news))
    return (1-lam)*q+lam*fchoice


def local_market_gain(q, objective, signal, *,
                      voter_shares=None, gamma=1.0,
                      new_vote_fraction=.2, eps=1e-6):
    """Numerically differentiate the expected market update on simplex.

    In a NON-equilibrium state this is only a local response measure,
    NOT a local stability test / bifurcation. Criticality requires a
    stationary solution and a calibrated voting response law.
    """
    x=unit_weights(q)
    n=len(x)
    if not (0<eps<min(x)/3):
        raise ValueError("HOLD_BAD_FINITE_DIFFERENCE_STEP")
    differences=np.zeros((n,n-1))
    differences[:-1,:]=np.eye(n-1)
    differences[-1,:]=-1.
    B,_=np.linalg.qr(differences,mode="reduced")
    args=dict(voter_shares=voter_shares,gamma=gamma,
              new_vote_fraction=new_vote_fraction)
    f0=deterministic_market_step(x,objective,signal,**args)
    derivative=np.zeros((n,n-1))
    for col in range(n-1):
        v=B[:,col]
        plus=deterministic_market_step(x+eps*v,objective,signal,**args)
        minus=deterministic_market_step(x-eps*v,objective,signal,**args)
        derivative[:,col]=(plus-minus)/(2*eps)
    tangential=B.T@derivative
    eigen=np.linalg.eigvals(tangential)
    spectral=float(max(abs(v) for v in eigen))
    equilibrium=bool(np.max(abs(f0-x))<1e-9)
    return {"local_simplex_spectral_gain":spectral,
            "is_evaluated_at_equilibrium":equilibrium,
            "gain_is_an_instability_test":equilibrium,
            "model_critical_absolute_odds":None,
            "real_market_criticality":"HOLD"}

def run_coupled_repeatability_trial(
        source, target, *, observed_first_odds, prior_scale=3.0,
        distance_m=None, horse_draws=80, seed=20261026,
        info_release_round=1, herding_gamma=1.0, pde_particles=0,
        premarket_context_receipt=None):
    """One coherent source-matched path; synthetic/authorized use only.

    The original horse prior is independent of observed q0. A source
    publisher verification is an input contract, NOT proven by this
    locally supplied Boolean: output never claims external attestation.
    """
    trait=repeatable_traits(source,target)
    horse_ids=trait["horse_ids"]
    context = (premarket_context_log_scores(premarket_context_receipt,target)
               if premarket_context_receipt is not None else None)
    fundamental=objective_horse_prior(
        trait, seconds_to_logweight=prior_scale,
        prestart_objective_log_covariates=context)
    q0=initial_market_proxy(observed_first_odds,horse_ids)
    if distance_m is not None and distance_m!=target["distance_m"]:
        raise ValueError("HOLD_DISTANCE_NOT_SOURCE_MATCHED")
    physical=finish_pair(fundamental,distance_m=target["distance_m"],
                         draws=horse_draws,seed=seed,
                         crowd_coefficient=CROWD_COEFFICIENT_M2_PER_S)
    c0=unit_weights(physical["scenarios"]["no_crowd"]["win"])
    c1=unit_weights(physical["scenarios"]["nonlocal_crowd"]["win"])
    market0=layered_vote_market(q0,fundamental,c0,
                               release_step=info_release_round,
                               gamma=herding_gamma,seed=seed+100)
    market1=layered_vote_market(q0,fundamental,c1,
                               release_step=info_release_round,
                               gamma=herding_gamma,seed=seed+100)
    market_never0=layered_vote_market(q0,fundamental,c0,
                                     release_step=5,gamma=herding_gamma,
                                     seed=seed+100)
    market_never1=layered_vote_market(q0,fundamental,c1,
                                     release_step=5,gamma=herding_gamma,
                                     seed=seed+100)
    if not all(np.array_equal(a,b) for a,b in
               zip(market_never0["path"],market_never1["path"])):
        raise AssertionError("HOLD_PRIVATE_RACE_INFO_LEAKED_INTO_EARLY_MARKET")
    out={
      "status":TRIAL_STATUS,
      "source_same_horse_repeatability":trait,
      "independent_horse_objective_prior":fundamental,
      "premarket_context_used":premarket_context_receipt is not None,
      "premarket_context_proof":"LOCAL_ONLY_EXTERNAL_ATTESTATION_HOLD",
      "observed_early_market_proxy":q0,
      "physical_nonlocal_horse_model":{
          "crowding_winner_change_in_paired_runs":
              physical["paired_prob_winner_difference"],
          "no_crowd_win_signal":c0,"crowded_win_signal":c1,
          "source_physical_constants_hypothetical":physical["parameters"],
      },
      "post_release_market_no_crowd":market0,
      "post_release_market_crowd":market1,
      "information_never_market_identical":True,
      "market_crowding_effect_TV_points":float(
          50*np.abs(market0["final"]-market1["final"]).sum()),
      "initial_market_not_a_pure_objective_rating":True,
      "same_original_RQ_horse_IDs_not_crosslinked_to_JRA":True,
      "original_or_live_tote_bettor_volumes_missing":True,
      "not_empirically_calibrated":True,
    }
    if pde_particles:
        check=pde_density_and_agent_check(
            fundamental,particles=pde_particles,
            strength=CROWD_COEFFICIENT_M2_PER_S,
            duration_s=2.,dx=1.,dt=.05,halfwidth=25.,seed=seed)
        out["matching_kernel_agent_PDE"]=check
    return out
