#!/usr/bin/env python3
"""Model-conditional Monte Carlo variability for existing original RQ horse ICC.

This is a DESCRIPTIVE simulation of uncertainty under the previously
fitted, homoscedastic Gaussian race-fixed / horse-random-intercept
source model. It is NOT a robust 95% confidence interval, formal
preregistered p value, age/weight/rider correction, H1 environment
reaction norm, H2 competitor response, or genetic heritability.

For the original observational design, source HORSES IDs are used only
in memory to construct the race-contrasted covariance eigenvalues.
Gaussian draws are generated in that eigenbasis: no original horse,
race, rider or trainer identifiers or individual GPS observations are
present in model-simulation outputs.

These are post-hoc diagnostics: the original positive Cannon/Eagle ICC
values were known before this simulation method was defined.
"""
from __future__ import annotations

from collections import defaultdict
import math

import numpy as np
from scipy.linalg import eigh, helmert
from scipy.optimize import minimize_scalar

from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_race_fixed_icc import race_fixed_reml

DEFAULT_SEED=20261014
MIN_MC_DRAWS=99
MAX_MC_DRAWS=999


def _reduced_source_design(rows:list[dict], min_gps:int):
    """Source membership and orthonormal race Helmert contrasts."""
    retained,_=prepare(rows,min_race_telemetry=min_gps)
    keep={(x["day"],x["race_number"],x["horse_id"]) for x in retained}
    groups=defaultdict(list)
    for r in rows:
        if (r["day"],r["race_number"],r["horse_id"]) in keep:
            groups[(r["day"],r["race_number"])].append(r)
    ids=list(dict.fromkeys(r["horse_id"] for group in groups.values()
                           for r in group))
    index={hid:i for i,hid in enumerate(ids)}
    design=[]
    response=[]
    for group in groups.values():
        n=len(group)
        Q=helmert(n,full=False)
        y=np.array([r["first_section_sec"] for r in group],dtype=float)
        incidence=np.zeros((n,len(ids)),dtype=float)
        for rownum,r in enumerate(group):
            incidence[rownum,index[r["horse_id"]]]=1.
        design.append(Q@incidence)
        response.append(Q@y)
    if not response:
        raise ValueError("HOLD_NO_OBSERVED_GPS_CONTRAST_DESIGN")
    B=np.vstack(design)
    z=np.concatenate(response)
    return B,z,len(groups)


def _point_given_squared_spectral_scores(eigen:np.ndarray,
                                         energy:np.ndarray)->float|None:
    """Exactly the same Gaussian REML ratio profile as the source fit.

    None is an explicit optimizer nonidentifiability, not an ICC of zero.
    """
    m=len(eigen)
    if m<50 or len(energy)!=m:
        return None
    if (float(np.ptp(eigen))<1e-7 or
            not np.isfinite(energy).all() or
            float(np.sum(energy))<=1e-12):
        return None
    def profile(logratio:float)->float:
        ratio=math.exp(logratio)
        inflated=1+ratio*eigen
        v=float(np.sum(energy/inflated)/m)
        if not math.isfinite(v) or v<=0:
            return float("inf")
        return m*math.log(v)+float(np.log(inflated).sum())
    result=minimize_scalar(profile,method="bounded",
                           bounds=(-18.,18.),
                           options={"xatol":1e-7,"maxiter":250})
    if not result.success or not math.isfinite(result.fun):
        return None
    null=profile(-80.)
    if result.fun>=null-1e-7:
        return 0.0
    if min(abs(result.x-(-18.)),abs(result.x-18.))<.15:
        return None
    ratio=math.exp(result.x)
    return float(ratio/(1+ratio))


def _quantile_summary(points:list[float])->dict:
    ordered=np.sort(np.asarray(points,dtype=float))
    q=np.quantile(ordered,[.025,.05,.5,.95,.975]).tolist()
    return {
        "point_estimator_quantiles_025_05_50_95_975":q,
        "point_estimator_mean":float(ordered.mean()),
        "point_estimator_zero_boundary_fraction":float(np.mean(ordered==0)),
        "replicate_fit_count":len(ordered),
        "not_a_calibrated_population_confidence_interval":True,
    }


def audit(
    rows:list[dict], *,
    min_positive_GPS_per_race:int=4,
    fitted_draws:int=299,
    zero_variance_draws:int=199,
    seed:int=DEFAULT_SEED,
) ->dict:
    """Returns aggregates or HOLD; never returns animal/source identifiers."""
    base=race_fixed_reml(
        rows,min_race_telemetry=min_positive_GPS_per_race
    )
    diag={
        "status":"HOLD_ORIGINAL_SOURCE_DESIGN_NOT_IDENTIFIABLE",
        "original_fit_status":base["status"],
        "original_fit_source_rows":base.get("source_rows",0),
        "original_fit_repeated_HORSES_ID_count":
            base.get("HORSES_IDs_observed_at_least_twice",0),
        "minimum_positive_GPS_per_race":min_positive_GPS_per_race,
        "no_animal_ID_name_GPS_record_or_licence_emitted":True,
        "H1_ground_slope_or_H2_social_effect_identified":False,
        "not_a_robust_confidence_interval_or_confirmatory_test":True,
    }
    if "conditional_observational_ICC_point_estimate" not in base:
        return diag
    if (fitted_draws<MIN_MC_DRAWS or fitted_draws>MAX_MC_DRAWS or
        zero_variance_draws<MIN_MC_DRAWS or
        zero_variance_draws>MAX_MC_DRAWS):
        raise ValueError("HOLD_PARAMETRIC_SOURCE_MC_REPLICATES_OUTSIDE_BOUND")
    B,z,racecount=_reduced_source_design(rows,min_positive_GPS_per_race)
    eigen,U=eigh(B@B.T,check_finite=True)
    if float(eigen.min())< -1e-7:
        return {**diag,"status":"HOLD_ORIGINAL_SOURCE_COVARIANCE_NOT_PSD"}
    eigen=np.clip(eigen,0.,None)
    scores=(U.T@z)**2
    point=_point_given_squared_spectral_scores(eigen,scores)
    observed=float(base["conditional_observational_ICC_point_estimate"])
    if point is None or abs(point-observed)>2e-5:
        return {
            **diag,
            "status":"HOLD_INDEPENDENT_REPRODUCTION_OF_ORIGINAL_REML_POINT_FAILED",
            "original_point_vs_independent_eigenprofile_within_tolerance":False,
        }
    vh=float(base["horse_variance_component_sec_squared"])
    ve=float(base["independent_error_variance_component_sec_squared"])
    if not (math.isfinite(vh) and math.isfinite(ve) and
            vh>=0 and ve>0):
        raise ValueError("HOLD_ORIGINAL_SOURCE_VARIANCE_COMPONENT_INVALID")
    # Efficient exact simulation in the diagonalized covariance of the
    # transformed source data. This retains the ORIGINAL original horse
    # ID incidence and race fields, not the original observed outcomes.
    rng=np.random.default_rng(seed)
    fitted_variance=ve+vh*eigen
    null_error_variance=float(np.sum(scores)/len(scores))
    fitted=[]
    zero=[]
    held_fitted=0
    held_null=0
    for _ in range(fitted_draws):
        draw2=fitted_variance*rng.standard_normal(len(eigen))**2
        icc=_point_given_squared_spectral_scores(eigen,draw2)
        if icc is None:
            held_fitted+=1
        else:
            fitted.append(icc)
    for _ in range(zero_variance_draws):
        # A very narrow Gaussian NULL, not a true source selection null.
        draw2=null_error_variance*rng.standard_normal(len(eigen))**2
        icc=_point_given_squared_spectral_scores(eigen,draw2)
        if icc is None:
            held_null+=1
        else:
            zero.append(icc)
    if (len(fitted)<fitted_draws-5 or
            len(zero)<zero_variance_draws-5):
        return {
            **diag,
            "status":"HOLD_GAUSSIAN_SOURCE_SIMULATION_NUMERIC_FAILURES",
            "fitted_numeric_HOLDS":held_fitted,
            "zero_horse_variance_numeric_HOLDS":held_null,
            "fitted_successful_simulations":len(fitted),
            "zero_variance_successful_simulations":len(zero),
        }
    return {
        **diag,
        "status":"EXPLORATORY_CONDITIONAL_GAUSSIAN_SOURCE_DESIGN_SAMPLING_ONLY",
        "observed_original_race_FE_conditional_ICC":observed,
        "independent_eigenprofile_original_point_reproduced":True,
        "maximum_absolute_point_disagreement_original_vs_independent":
            abs(point-observed),
        "source_race_contrasts":len(z),
        "original_source_races_in_fitted_design":racecount,
        "original_source_fixed_horse_race_incidence_used":True,
        "original_horse_variance_seconds_squared":vh,
        "original_residual_variance_seconds_squared":ve,
        "random_seed":seed,
        "conditional_on_exact_source_recorded_races_horses_GPS_coverage":True,
        "fitted_Gaussian_model_parametric_sampling":{
            **_quantile_summary(fitted),
            "requested_simulations":fitted_draws,
            "numeric_HOLD_replicates":held_fitted,
            "model_parameters_taken_from_observed_fitted_variance":True,
            "interval_is_sampling_distribution_not_robust_95pct_CI":True,
        },
        "zero_horse_component_Gaussian_null_simulation":{
            **_quantile_summary(zero),
            "requested_simulations":zero_variance_draws,
            "numeric_HOLD_replicates":held_null,
            "null_horse_variance_component_seconds_squared":0.,
            "null_residual_variance_fitted_under_zero_component":
                null_error_variance,
            "fraction_of_simulated_null_ICCs_at_least_original":
                float((1+sum(v>=observed for v in zero))/(len(zero)+1)),
            "fraction_is_NOT_credible_frequentist_ecological_p_value":True,
        },
        "limitations":[
            "Parametric simulated ICC quantiles describe the previously fitted Gaussian model only; they are NOT a validated 95 percent confidence interval.",
            "Racing nominees, horse age, actual rider and weight, trainer, injury, selective entry and GPS dropout are not correctly simulated.",
            "Race/meeting date/horse-specific source dependence beyond the Gaussian HORSES intercept is not simulated.",
            "First GPS segment length may vary by race and across racecourses, and the common residual variance assumption can fail.",
            "Cannon versus Eagle source cohorts use different marker mixes; overlapping simulation intervals would not establish same-trait cross-venue replication.",
            "Both model and simulation question were chosen after observing initial source individual ICC and are not pre-registered.",
            "True ground H1 random slopes, social competitor H2 effects, heritability and adaptation are NOT estimated.",
        ],
    }


def markers(
    rows:list[dict], *,
    marker_values:tuple[float,...],
    fitted_draws:int=199, null_draws:int=99,
    seed:int=DEFAULT_SEED,
)->dict:
    if len(marker_values)>5 or len(set(marker_values))!=len(marker_values):
        raise ValueError("HOLD_DUPLICATE_OR_TOO_MANY_SOURCE_MARKERS")
    return {
        str(int(marker) if float(marker).is_integer() else marker):audit(
            [r for r in rows if float(r["first_marker_m"])==float(marker)],
            fitted_draws=fitted_draws,
            zero_variance_draws=null_draws,
            seed=seed+index,
        )
        for index,marker in enumerate(marker_values)
    }
