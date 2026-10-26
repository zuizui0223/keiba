#!/usr/bin/env python3
"""Source-matched, race-contrast Gaussian random-effects posterior.

Corrects a central mathematical weakness in the 2026-10-26 synthetic
horse -> market bridge: peer-relative initial sectional times from a
SINGLE RACE are not independent observations across horses.

Condition on artificial/estimated σ_a², σ_e²:
    t_{ir} = μ_r + a_i + ε_{ir}
    a_i ~ N(0, σ_a²), ε_ir ~ N(0, σ_e²) independent on absolute times.
The same race's mean is eliminated using the orthogonal projector
    P_r = I_r - (1/n_r) 11'.
Each contrast likelihood is a Gaussian in an (n_r-1) dimensional
orthonormal subspace, with independent σ_e² residual components.
The exact conditional Gaussian posterior for the horse random effects is
    V^{-1} = I/σ_a² + ∑_r Z_r' P_r Z_r / σ_e²
    m = V ∑_r Z_r' P_r t_r / σ_e².

This accounts for within-race contrast covariance, unlike taking the
peer-relative y_ir as conditionally independent errors. There are NO
raw Racing Queensland horses or actual JRA stakes included here.
The hyperparameters (σ_a²,σ_e²) are currently crude, source-conditional
method-of-moments estimates from the old experimental module; they are
NOT calibrated REML, include no random slopes, trainer/rider adjustment,
nor uncertainty in hyperparameter estimates.

All inputs MUST be source-authorized, same horse IDs, historical,
pre-first-market, and clock validated by repeatable_traits(). A caller's
Boolean publisher-clock assertion is still NOT third-party evidence.
"""
from __future__ import annotations

from collections import defaultdict
import math
import numpy as np

from keiba_individual_trait_to_market_cascade import repeatable_traits

STATUS = "RACE_CONTRAST_JOINT_GAUSSIAN_CONDITIONAL_POSTERIOR_UNCALIBRATED"
MAX_HISTORICAL_HORSE_IDS = 160


def fit_race_contrast_posterior(source: dict, target: dict, *,
                                variance_override=None):
    """Return ordered target horse effects AND full covariance.

    variance_override may be an explicitly specified tuple
    (between_horse_variance_seconds2, residual_variance_seconds2).
    It changes a WHAT-IF model, never learns hyperparameters from the
    target event or actual odds. The default is source-only MoM.
    """
    gate=repeatable_traits(source,target)
    ids=gate["horse_ids"]
    records=source["records"]
    observed=sorted({r["horse_id"] for r in records})
    if len(observed) > MAX_HISTORICAL_HORSE_IDS:
        raise ValueError("HOLD_TOO_MANY_HISTORICAL_HORSES_FOR_DENSE_GAUSSIAN")
    if variance_override is None:
        a2=gate["horse_effect_variance_seconds_squared"]
        e2=gate["residual_variance_seconds_squared"]
        origin="SOURCE_CONDITIONAL_METHOD_OF_MOMENTS_NOT_REML"
    else:
        if (not isinstance(variance_override,(list,tuple))
            or len(variance_override)!=2):
            raise ValueError("HOLD_HYPERPARAMETER_TUPLE")
        a2,e2=variance_override
        origin="EXPLICIT_SYNTHETIC_SENSITIVITY_NOT_AN_ESTIMATED_EFFECT"
    if (type(a2) not in (float,int) or type(e2) not in (float,int)
            or not math.isfinite(a2) or not math.isfinite(e2)
            or a2<=0 or e2<=0):
        raise ValueError("HOLD_NO_IDENTIFIABLE_POSITIVE_VARIANCE_COMPONENTS")
    a2,e2=float(a2),float(e2)
    all_ids=sorted(set(observed)|set(ids))
    index={h:i for i,h in enumerate(all_ids)}
    N=len(all_ids)
    precision=np.eye(N)/a2
    rhs=np.zeros(N)
    by_race=defaultdict(list)
    for row in records:
        by_race[(row["race_day"],row["race_id"])].append(row)
    race_sizes=[]
    for race,group in sorted(by_race.items()):
        idx=[index[row["horse_id"]] for row in group]
        n=len(idx)
        if n<4 or len(set(idx))!=n:
            raise ValueError("HOLD_BAD_RACE_ROSTER_IN_CONTRAST")
        times=np.asarray([row["first_section_seconds"] for row in group],
                         dtype=float)
        projector=np.eye(n)-np.ones((n,n))/n
        # This is the complete information in n-1 independent
        # orthogonal contrasts; no fake n independent y_ir values.
        precision[np.ix_(idx,idx)]+=projector/e2
        rhs[idx]+=(times-times.mean())/e2
        race_sizes.append(n)
    covariance=np.linalg.solve(precision,np.eye(N))
    covariance=(covariance+covariance.T)/2
    posterior_mean=np.linalg.solve(precision,rhs)
    if (not np.all(np.isfinite(covariance))
            or not np.all(np.isfinite(posterior_mean))):
        raise ValueError("HOLD_NONFINITE_JOINT_POSTERIOR")
    if np.min(np.linalg.eigvalsh(covariance))<=0:
        raise ValueError("HOLD_POSTERIOR_COVARIANCE_NOT_POSITIVE")
    ix=[index[i] for i in ids]
    mean=posterior_mean[ix]
    cov=covariance[np.ix_(ix,ix)]
    cov=(cov+cov.T)/2
    diag=np.sqrt(np.diag(cov))
    corr=cov/np.outer(diag,diag)
    # Pairwise effects (a_i-a_j) remove the globally unidentifiable
    # common intercept. They generally have smaller uncertainty
    # than under independent per-horse Gaussian posterior draws.
    vdiff={}
    for x in range(len(ids)):
        for y in range(x+1,len(ids)):
            vdiff[f"{ids[x]}|{ids[y]}"]=float(
                cov[x,x]+cov[y,y]-2*cov[x,y])
    if any(v< -1e-11 for v in vdiff.values()):
        raise AssertionError("HOLD_NEGATIVE_PAIR_EFFECT_VARIANCE")
    maxcorr=max((abs(float(corr[i,j]))
                 for i in range(len(ids))
                 for j in range(i+1,len(ids))),default=0)
    return {
      "status":STATUS,
      "horse_ids":ids,
      "mean":mean.tolist(),
      "covariance":cov.tolist(),
      "marginal_sd":diag.tolist(),
      "max_absolute_offdiagonal_effect_correlation":maxcorr,
      "pair_effect_variance":vdiff,
      "historical_horses_in_joint_fit":len(observed),
      "historical_race_count":len(by_race),
      "source_race_sizes":race_sizes,
      "hyperparameters":{
          "horse_between_variance_seconds2":a2,
          "absolute_time_residual_variance_seconds2":e2,
          "source":origin,
          "held_fixed_in_posterior":True
      },
      "shared_race_residual_covariance_model":"orthogonal_n_minus_1_contrasts",
      "global_mean_unidentified_by_within_race_contrasts":True,
      "no_horse_rider_trainer_or_going_random_slope":True,
      "not_original_RQ_REML_fit":True,
      "no_independent_real_market_source_proof":True
    }


def draw_joint_effects(posterior: dict, *, draws: int, seed: int,
                       enabled=True):
    """Reproducible correlated Gaussian draws, not population credible intervals."""
    ids=posterior["horse_ids"]
    if (type(draws) is not int or draws<2 or draws>64
            or type(seed) is not int or type(enabled) is not bool):
        raise ValueError("HOLD_INVALID_SYNTHETIC_JOINT_DRAW_REQUEST")
    mean=np.asarray(posterior["mean"],dtype=float)
    cov=np.asarray(posterior["covariance"],dtype=float)
    n=len(ids)
    if (mean.shape!=(n,) or cov.shape!=(n,n)
            or len(set(ids))!=n or not np.all(np.isfinite(mean))
            or not np.all(np.isfinite(cov))
            or not np.allclose(cov,cov.T,atol=1e-10)):
        raise ValueError("HOLD_INVALID_SOURCE_JOINT_GAUSSIAN")
    if np.linalg.eigvalsh(cov)[0]<=0:
        raise ValueError("HOLD_INVALID_SOURCE_JOINT_COVARIANCE")
    if not enabled:
        return np.broadcast_to(mean,(draws,n)).copy()
    rng=np.random.default_rng(seed)
    chol=np.linalg.cholesky(cov)
    return mean[None,:]+rng.standard_normal((draws,n))@chol.T
