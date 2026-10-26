#!/usr/bin/env python3
"""Race-fixed Gaussian REML variance estimation from PRE-QUOTE horse GPS.

This uses each original horse's ABSOLUTE first-section time, not the
peer-relative transform as if each row were independent. For race r,
  t_r = mu_r 1 + Z_r a + epsilon_r, a ~ N(0,a2 I),
  epsilon_r ~ N(0,e2 I).
Orthonormal within-race Helmert contrasts Q_r 1 = 0 are stacked:
  z=Q t, B=Q Z, cov(z)=e2 I + a2 B B'.
This is a restricted Gaussian likelihood after fixed race means
have been removed; it is conditional on homoscedastic Gaussian errors,
historical roster selection and available GPS rows. No JRA bettors,
post-race target labels, current race prices, or actual upcoming GPS
timings are used.

Profile the variance ratio r=a2/e2 with e2(r)=z'C(r)^-1 z/m,
log det C(r)=sum log(1+r*lambda_j). B'B has <=160 dimensions;
there is no scipy dependency, and all numerical boundaries are guarded.
The profile envelope is a SENSITIVITY SET (not a 95% CI, p-value,
posterior or generalization guarantee).
"""
from __future__ import annotations

from collections import defaultdict
import math
import numpy as np

from keiba_individual_trait_to_market_cascade import repeatable_traits

REML_STATUS="SOURCE_LOCKED_RACE_FIXED_CONTRAST_REML_POINT_EXPLORATORY"
MIN_LOGR=-18.0
MAX_LOGR=18.0
N_GRID=121
MAX_HORSES=160
MAX_CONTRASTS=2500


def _helmert(n: int):
    if type(n) is not int or not (4 <= n <= 30):
        raise ValueError("HOLD_UNSUPPORTED_RACE_CONTRAST_FIELD")
    Q=np.zeros((n-1,n),dtype=float)
    for row in range(1,n):
        denom=math.sqrt(row*(row+1))
        Q[row-1,:row]=1/denom
        Q[row-1,row]=-row/denom
    return Q


def _data(source, target):
    gate=repeatable_traits(source,target)
    observed=sorted({row["horse_id"] for row in source["records"]})
    if len(observed)>MAX_HORSES:
        raise ValueError("HOLD_DENSE_REML_SOURCE_TOO_LARGE")
    by_race=defaultdict(list)
    for row in source["records"]:
        by_race[(row["race_day"],row["race_id"])].append(row)
    total_n=sum(len(x)-1 for x in by_race.values())
    if not 12 <= total_n <= MAX_CONTRASTS:
        raise ValueError("HOLD_CONTRAST_COUNT_INSUFFICIENT_OR_HUGE")
    idx={k:i for i,k in enumerate(observed)}
    responses=[]
    design=[]
    dates=set()
    for key, group in sorted(by_race.items()):
        n=len(group)
        Q=_helmert(n)
        actual=np.asarray([x["first_section_seconds"] for x in group],
                          dtype=float)
        group_index=[idx[row["horse_id"]] for row in group]
        if len(set(group_index))!=len(group_index):
            raise ValueError("HOLD_DUPLICATE_HORSE_WITHIN_RACE")
        R=np.zeros((n,len(observed)),dtype=float)
        for j,col in enumerate(group_index):
            R[j,col]=1.
        responses.append(Q@actual)
        design.append(Q@R)
        dates.add(key[0].split("T")[0])
    z=np.concatenate(responses)
    B=np.vstack(design)
    if not (z.shape==(total_n,) and B.shape==(total_n,len(observed))):
        raise AssertionError("HOLD_REML_CONTRAST_SHAPE")
    return z,B,{
        "source_races":len(by_race),
        "independent_observed_source_dates":len(dates),
        "source_horse_count":len(observed),
        "eligible_repeated_source_horses":gate["repeated_source_horses"],
        "target_horse_count":len(gate["horse_ids"]),
        "contrasts":total_n,
        "source_row_count":len(source["records"]),
    }


def _golden_min(fn,lo,hi,niter=95):
    ratio=(math.sqrt(5)-1)/2
    c=hi-ratio*(hi-lo)
    d=lo+ratio*(hi-lo)
    fc=fn(c);fd=fn(d)
    for _ in range(niter):
        if fc<fd:
            hi,d,fd=d,c,fc
            c=hi-ratio*(hi-lo)
            fc=fn(c)
        else:
            lo,c,fc=c,d,fd
            d=lo+ratio*(hi-lo)
            fd=fn(d)
    best=(lo+hi)/2
    return best,fn(best)


def estimate_race_fixed_reml(source, target, *, profile_deviance_tolerance=2.0):
    """Restricted ML point plus exploratory low/central/high variance scenarios.

    For source scarcity, near-zero or numerical search-boundary
    results fail CLOSED. The method-of-moments prior is not re-used.
    """
    if (type(profile_deviance_tolerance) not in (int,float)
            or not math.isfinite(profile_deviance_tolerance)
            or not 0.25 <= profile_deviance_tolerance <= 8):
        raise ValueError("HOLD_INVALID_EXPLORATORY_PROFILE_TOLERANCE")
    z,B,audit=_data(source,target)
    m=len(z)
    gram=B.T@B
    eigen,U=np.linalg.eigh((gram+gram.T)/2)
    if min(eigen)<-1e-8:
        raise ValueError("HOLD_NONPSD_RACE_CONTRAST_HORSE_GRAM")
    eigen=np.maximum(eigen,0)
    valid=eigen>1e-8*max(1.,float(max(eigen)))
    if valid.sum()<2 or m<=int(valid.sum()):
        raise ValueError("HOLD_HORSE_CONTRAST_VARIANCE_COMPONENT_NOT_IDENTIFIABLE")
    lam=eigen[valid]
    projected=U[:,valid].T@(B.T@z)
    alpha=np.maximum(projected**2/lam,0.)
    baseline=float(z@z)
    residual=baseline-float(alpha.sum())
    if residual< -max(1e-8,baseline*1e-8):
        raise ValueError("HOLD_INCONSISTENT_CONTRAST_PROJECTION")
    residual=max(0.,residual)
    if residual<=1e-12 or baseline<=1e-12:
        raise ValueError("HOLD_NO_INDEPENDENT_GAUSSIAN_RESIDUAL_INFORMATION")
    def obj_ratio(r):
        if not (r>=0 and math.isfinite(r)):
            return float("inf")
        inflation=1+r*lam
        q=residual+float(np.sum(alpha/inflation))
        e2=q/m
        if not (e2>0 and math.isfinite(e2)):
            return float("inf")
        return float(m*math.log(e2)+np.log(inflation).sum())
    grid=np.linspace(MIN_LOGR,MAX_LOGR,N_GRID)
    values=np.asarray([obj_ratio(math.exp(v)) for v in grid])
    if not np.all(np.isfinite(values)):
        raise ValueError("HOLD_NONFINITE_REML_PROFILE")
    best_ind=int(np.argmin(values))
    if best_ind in (0,len(grid)-1):
        raise ValueError("HOLD_VARIANCE_RATIO_NUMERIC_SEARCH_BOUNDARY")
    logratio,best=_golden_min(lambda y:obj_ratio(math.exp(y)),
                              float(grid[best_ind-1]),
                              float(grid[best_ind+1]))
    ratio=math.exp(logratio)
    null_value=obj_ratio(0)
    if best>=null_value-1e-7:
        raise ValueError("HOLD_REML_HORSE_VARIANCE_ZERO_BOUNDARY")
    if (abs(logratio-MIN_LOGR)<.25 or
            abs(logratio-MAX_LOGR)<.25):
        raise ValueError("HOLD_VARIANCE_RATIO_NUMERIC_SEARCH_BOUNDARY")
    e2=float((residual+np.sum(alpha/(1+ratio*lam)))/m)
    a2=ratio*e2
    if not (a2>0 and e2>0 and math.isfinite(a2) and math.isfinite(e2)):
        raise ValueError("HOLD_INVALID_REML_VARIANCES")
    # To report sensitivity of the variance hyperparameters without
    # treating them as a fitted random posterior, use all grid ratios
    # with deviance no more than the user-designated non-inferential
    # tolerance away from the best result.
    selected=[r for r,v in zip(grid,values) if
              v-best<=profile_deviance_tolerance+1e-10]
    if not selected:
        raise AssertionError("HOLD_EMPTY_REML_SENSITIVITY_GRID")
    ratios=[math.exp(min(selected)),ratio,math.exp(max(selected))]
    scenarios=[]
    for label,r in zip(("low","central","high"),ratios):
        ee=float((residual+np.sum(alpha/(1+r*lam)))/m)
        aa=float(r*ee)
        scenarios.append({"label":label,"horse_variance_seconds2":aa,
                          "error_variance_seconds2":ee,
                          "variance_ratio":r,
                          "profile_objective":obj_ratio(r)})
    return {
        "status":REML_STATUS,
        "source_summary":audit,
        "horse_effect_variance_seconds_squared":a2,
        "independent_absolute_time_error_variance_seconds_squared":e2,
        "conditional_icc_point":a2/(a2+e2),
        "variance_ratio":ratio,
        "log_variance_ratio":logratio,
        "n_independent_contrast_dimensions":m,
        "horse_contrast_rank":int(valid.sum()),
        "profile_objective_at_optimum":best,
        "profile_improvement_vs_zero_horse_variance":null_value-best,
        "numerical_envelope_not_biological_prior": [MIN_LOGR,MAX_LOGR],
        "sensitivity_deviance_tolerance_not_confidence_interval":
            float(profile_deviance_tolerance),
        "sensitivity_scenarios":scenarios,
        "same_horse_repeatable_id_source_asof_verified_locally":True,
        "covariance_assumptions":{
            "within_race_absolute_time_noise_independent":True,
            "equal_absolute_noise_variance_across_races":True,
            "fixed_race_intercepts_eliminated_by_orthonormal_Helmert":True,
            "learned_from_target_race_outcome_or_odds":False,
            "unmeasured_jockey_going_selective_entry_controlled":False,
            "robust_date_cluster_uncertainty_estimated":False,
            "population_CI_or_Bayesian_posterior":False,
            "no_verified_licensed_individual_horse_data_in_repo":True
        },
    }


def leave_one_source_date_out_reml(source, target):
    """Descriptive clustered source-date sensitivity, not a 95% CI.

    Each *source date* is deleted in its entirety so that multiple
    repeated horse/peer rows from that same day cannot masquerade as
    independent uncertainty replicates. Failed source-eligibility or
    variance-boundary refits remain explicit HOLD counts.
    """
    gate=repeatable_traits(source,target)
    days=sorted({row["race_day"].split("T")[0]
                 for row in source["records"]})
    if len(days)<5:
        raise ValueError("HOLD_TOO_FEW_SOURCE_DATE_CLUSTERS_FOR_DELETION")
    full=estimate_race_fixed_reml(source,target)
    rows=[]
    for omitted in days:
        source_minus={**source,
                      "records":[r for r in source["records"]
                                 if r["race_day"].split("T")[0]!=omitted]}
        try:
            trial=estimate_race_fixed_reml(source_minus,target)
            rows.append({"source_date_omitted":omitted,
                         "status":"EXPLORATORY_SOURCE_DATE_DELETION_FIT",
                         "icc":trial["conditional_icc_point"],
                         "horse_variance_seconds2":
                             trial["horse_effect_variance_seconds_squared"],
                         "residual_variance_seconds2":
                             trial[
                               "independent_absolute_time_error_variance_seconds_squared"]})
        except ValueError as exc:
            if not str(exc).startswith("HOLD_"):
                raise
            rows.append({"source_date_omitted":omitted,
                         "status":str(exc)})
    available=[x for x in rows if x["status"]==
               "EXPLORATORY_SOURCE_DATE_DELETION_FIT"]
    if len(available)<len(days)-2:
        status="HOLD_MANY_DATE_CLUSTER_REML_VARIANCES_UNIDENTIFIABLE"
    else:
        status="EXPLORATORY_SOURCE_DATE_DELETION_SENSITIVITY_NOT_CI"
    summary={
      "status":status,
      "source_dates":len(days),
      "full_icc":full["conditional_icc_point"],
      "successful_leave_one_source_date_fits":len(available),
      "HOLD_leave_one_source_date_fits":len(days)-len(available),
      "minimum_deletion_icc":(
          min(x["icc"] for x in available) if available else None),
      "maximum_deletion_icc":(
          max(x["icc"] for x in available) if available else None),
      "no_confirmatory_significance_or_population_confidence_interval":True,
      "no_target_race_outcomes_or_odds_loaded":True,
      "no_independent_date_bootstrap_claim":True,
    }
    # Individual dates are retained only in private returned metadata;
    # synthetic demo reports aggregates, never licensed race date roster.
    summary["date_deletion_details"]=rows
    return summary
