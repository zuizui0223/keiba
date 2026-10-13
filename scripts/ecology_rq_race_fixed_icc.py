#!/usr/bin/env python3
"""Race-fixed-effect Gaussian HORSES random-intercept variance decomposition.

This is an *exploratory* conditional repeatability / adjusted-ICC
POINT ESTIMATE for first-section ABSOLUTE seconds in actual racing
Thoroughbreds, NOT an H1 ground reaction-norm random slope, H2
competitor interaction, inherited personality or causal result.

Mathematics: y_ir = alpha_r + b_i + e_ir, with alpha_r an unrestricted
fixed intercept for every original race, b_i ~ N(0,sigma_h^2), and
e_ir ~ iid N(0,sigma_e^2). Remove fixed alpha_r EXACTLY via orthonormal
Helmert within-race contrasts. The resulting restricted Gaussian
likelihood has covariance sigma_e^2 I + sigma_h^2 (QZ)(QZ)'.
Eigen-decomposition + scalar likelihood profiling estimates both
variances without fitting noisy 80+ separate race dummy coefficients.
The conditional ICC point estimate is sigma_h^2/(sigma_h^2+sigma_e^2).

IMPORTANT: race contrasts mathematically couple competing rows,
but covariance in the reduced model is explicitly represented.
The model ASSUMES homoscedastic Gaussian independent residual errors
conditional on race+horse; no rider, weight, age, GPS missingness,
selective nomination, or date-clustered uncertainty is corrected.
No robust confidence interval or confirmatory p-value is provided.
A bounded observational point estimate can be an artefact of context.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import random

import numpy as np
from scipy.linalg import eigh, helmert
from scipy.optimize import minimize_scalar

from ecology_rq_early_pace_repeatability import prepare


def race_fixed_reml(rows: list[dict], min_race_telemetry: int = 4) -> dict:
    """Return anonymous source-conditioned ICC point estimate or explicit HOLD.

    Input is original HORSES-ID/time data prepared in memory. Output
    never materializes identities or raw timing observations.
    """
    relative, quality=prepare(rows,min_race_telemetry=min_race_telemetry)
    race_members=defaultdict(list)
    actual_by_day_id={
        (r["day"],r["horse_id"]):float(r["first_section_sec"])
        for r in rows
    }
    for row in relative:
        key=(row["day"],row["race_number"])
        actual=actual_by_day_id.get((row["day"],row["horse_id"]))
        if actual is None:
            raise ValueError("HOLD_ABSOLUTE_SOURCE_SEGMENT_NOT_FOUND")
        race_members[key].append((row["horse_id"],float(actual)))
    all_horses=[r["horse_id"] for r in relative]
    counts=Counter(all_horses)
    n_repeated=sum(1 for v in counts.values() if v>=2)
    n_independent_dates=len({d for d,n in race_members})
    base={
        "outcome":"original individual first GPS interval in SECONDS; NOT whole-race time",
        "estimation":"Gaussian random horse intercept, exact fixed race intercepts eliminated by Helmert REML contrasts",
        "minimum_positive_GPS_horses_per_race":min_race_telemetry,
        "source_rows":len(relative),
        "original_races":len(race_members),
        "original_date_clusters":n_independent_dates,
        "different_official_HORSES_IDs":len(counts),
        "HORSES_IDs_observed_at_least_twice":n_repeated,
        "race_intercepts_adjust_for_shared_ground_class_distance_and_other_race_factors":True,
        "no_class_rider_weight_age_or_selection_specific_horse_effect_correction":True,
        "not_an_adjusted_mixed_model_with_independent_date_clusters":True,
        "no_H1_random_ground_slope_or_H2_social_interaction_estimated":True,
        "not_verified_official_starters_or_finish_times":True,
        "no_original_horse_names_IDs_or_raw_segment_times_exported":True,
        "not_confirmatory_inference_or_genetic_heritability":True,
        "source_field_coverage":quality,
    }
    if (len(relative)<80 or len(race_members)<12 or
            n_independent_dates<6 or n_repeated<20):
        return {**base,"status":"HOLD_INSUFFICIENT_REPEATED_HORSES_OR_RACES_FOR_ICC"}

    ordered_horse_ids=list(dict.fromkeys(all_horses))
    horse_col={h:i for i,h in enumerate(ordered_horse_ids)}
    # Avoid huge 2D dummy design for every race intercept; in each
    # race the n-1 rows of Helmert orthonormal contrasts sum to zero.
    zs=[]
    Bblocks=[]
    for group in race_members.values():
        n=len(group)
        Q=helmert(n,full=False)
        y=np.asarray([v for _,v in group],dtype=float)
        zs.append(Q@y)
        b=np.zeros((n-1,len(ordered_horse_ids)),dtype=float)
        for position,(horse_id,_) in enumerate(group):
            b[:,horse_col[horse_id]]=Q[:,position]
        Bblocks.append(b)
    z=np.concatenate(zs)
    B=np.vstack(Bblocks)
    m=len(z)
    if m<50:
        return {**base,"status":"HOLD_TOO_FEW_INDEPENDENT_RACE_CONTRASTS"}
    gram=B@B.T
    eigenvalues,eigenvectors=eigh(gram,check_finite=True)
    if eigenvalues.min() < -1e-7:
        raise ValueError("HOLD_NUMERIC_COVARIANCE_NOT_PSD")
    eigenvalues=np.clip(eigenvalues,0,None)
    scores=(eigenvectors.T@z)**2

    if (float(np.max(eigenvalues)-np.min(eigenvalues))<1e-6 or
            float(np.sum(scores))<1e-12):
        return {**base,"status":"HOLD_HORSE_VARIANCE_COMPONENT_NOT_IDENTIFIABLE"}

    def profile(log_ratio):
        lam=math.exp(log_ratio)
        inflated=1+lam*eigenvalues
        evar=float(np.sum(scores/inflated)/m)
        if evar<=0 or not math.isfinite(evar):
            return float("inf")
        return m*math.log(evar)+float(np.log(inflated).sum())

    # ratio between 1e-8 and 1e8 is a numeric search envelope, NOT a
    # biological plausible-prior constraint or statistical interval.
    bounds=(-18.,18.)
    opt=minimize_scalar(profile,method="bounded",bounds=bounds,
                        options={"xatol":1e-7,"maxiter":250})
    if not opt.success or not math.isfinite(opt.fun):
        return {**base,"status":"HOLD_GAUSSIAN_REML_NUMERIC_OPTIMIZATION_FAILED"}

    zero=profile(-80.)
    improvement=max(0.,float(zero-opt.fun))
    if opt.fun >= zero-1e-7:
        ratio=0.
        best=zero
        status="EXPLORATORY_RACE_ADJUSTED_ICC_AT_ZERO_BOUNDARY"
    else:
        if min(abs(opt.x-bounds[0]),abs(opt.x-bounds[1])) < .15:
            return {**base,"status":"HOLD_VARIANCE_RATIO_HITS_NUMERIC_SEARCH_BOUNDARY"}
        ratio=math.exp(opt.x)
        best=opt.fun
        status="EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY"
    sigma_e=float(np.sum(scores/(1+ratio*eigenvalues))/m)
    sigma_h=ratio*sigma_e
    icc=ratio/(1+ratio)

    if not all(math.isfinite(v) and v>=0 for v in (sigma_e,sigma_h,icc)):
        raise ValueError("HOLD_NONFINITE_OR_NEGATIVE_REML_VARIANCE")
    return {
        **base,"status":status,
        "race_fixed_effect_contrast_observations":m,
        "horse_variance_component_sec_squared":sigma_h,
        "independent_error_variance_component_sec_squared":sigma_e,
        "conditional_observational_ICC_point_estimate":icc,
        "source_variance_ratio_horse_over_residual":ratio,
        "restricted_profile_objective_improvement_vs_zero_horse_variance":improvement,
        "biological_effect_size_is_a_random_slope_variance":False,
        "formal_hypothesis_p_value_provided":False,
        "robust_ICC_confidence_interval_provided":False,
        "experimental_ground_or_competitor_treatment_assignment":False,
        "no_reliable_horse_age_jockey_weight_control":True,
        "caution":[
            "Horse random-intercept variance may include consistent unmeasured rider/trainer, selective race entry and fitness effects.",
            "Race fixed effects absorb all race-common track/condition shifts but NOT animal-specific race-by-condition response.",
            "Gaussian equal residual variance and source completeness are unvalidated in these official GPS observations.",
            "Nonrandom nominations, GPS missingness and 12 clustered date sources undermine naive conventional inference.",
            "The ICC is a conditional descriptive variance ratio, not standard heritability, personality or adaptation.",
        ],
    }


def delete_date_sensitivity(rows:list[dict],
                            min_race_telemetry:int=4)->dict:
    """Twelve leave-one-meeting-out re-fits; DESCRIPTIVE stability, not CI."""
    days=sorted({r["day"] for r in rows})
    results=[]
    hold=0
    if len(days)<8:
        return {"status":"HOLD_TOO_FEW_DATES_FOR_DATE_DELETION"}
    for deleted in days:
        cut=[r for r in rows if r["day"]!=deleted]
        fit=race_fixed_reml(cut,min_race_telemetry=min_race_telemetry)
        icc=fit.get("conditional_observational_ICC_point_estimate")
        if icc is None:
            hold+=1
        else:
            results.append(float(icc))
    if len(results)<len(days)-2:
        return {"status":"HOLD_MANY_DELETED_DATE_VARIANCE_FITS",
                "date_count":len(days),"fitted_count":len(results),
                "HOLD_count":hold}
    return {
        "status":"EXPLORATORY_ONE_DATE_DELETION_STABILITY_NOT_CONFIDENCE_INTERVAL",
        "deleted_meeting_dates":len(days),
        "models_with_numeric_ICC":len(results),
        "models_returning_HOLD":hold,
        "minimum_conditional_ICC_point":min(results),
        "maximum_conditional_ICC_point":max(results),
        "not_a_jackknife_variance_or_uncertainty_interval":True,
    }


def source_race_identity_shuffle_reference(
    rows:list[dict], permutations:int=99, seed:int=20261013,
    minimum_per_race:int=4,
)->dict:
    """Exploratory label-exchange benchmark, not a valid causal randomization.

    Keep each REAL race's absolute section times, distance, timing marker
    and number of observed GPS records intact. Reassign horse ID + name
    LABELS only to the originally observed horses WITHIN each race.
    Under genuinely exchangeable labels the stable-individual intercept
    should collapse; source selection and other unobserved variables
    make exchangeability biologically untrue.
    """
    if permutations < 50 or permutations > 500:
        raise ValueError("HOLD_IDENTITY_SHUFFLE_COUNT_OUTSIDE_GUARD")
    eligible,_=prepare(rows,min_race_telemetry=minimum_per_race)
    if not eligible:
        return {"status":"HOLD_NO_RACE_FIELDS_FOR_PERMUTATION"}
    included={(r["day"],r["race_number"],r["horse_id"]) for r in eligible}
    observations=[dict(row) for row in rows if
                  (row["day"],row["race_number"],row["horse_id"]) in included]
    base=race_fixed_reml(observations,min_race_telemetry=minimum_per_race)
    observed=base.get("conditional_observational_ICC_point_estimate")
    if observed is None:
        return {
            "status":"HOLD_ORIGINAL_GAUSSIAN_ICC_NOT_IDENTIFIABLE",
            "base_status":base["status"],
            "no_original_horse_IDs_exported":True,
        }
    by_race=defaultdict(list)
    for i,r in enumerate(observations):
        by_race[(r["day"],r["race_number"])].append(i)
    rng=random.Random(seed)
    samples=[]
    held=0
    for _ in range(permutations):
        shuffled=[dict(x) for x in observations]
        for positions in by_race.values():
            labels=[(shuffled[i]["horse_id"],shuffled[i]["horse_name"])
                    for i in positions]
            rng.shuffle(labels)
            for i,(ident,name) in zip(positions,labels):
                shuffled[i]["horse_id"]=ident
                shuffled[i]["horse_name"]=name
        result=race_fixed_reml(shuffled,min_race_telemetry=minimum_per_race)
        point=result.get("conditional_observational_ICC_point_estimate")
        if point is None:
            held+=1
        else:
            samples.append(float(point))
    if len(samples) < permutations-5:
        return {"status":"HOLD_SHUFFLED_MODELS_HAVE_TOO_MANY_NUMERIC_HOLDS",
                "valid_shuffle_fits":len(samples),
                "requested_shuffle_fits":permutations,
                "no_original_horse_IDs_exported":True}
    samples.sort()
    return {
        "status":"EXPLORATORY_RACE_CONDITIONED_HORSE_ID_REASSIGNMENT_REFERENCE",
        "original_conditional_ICC":float(observed),
        "valid_within_race_identity_shuffle_models":len(samples),
        "shuffle_models_with_HOLD":held,
        "minimum_positive_GPS_horses_per_race":minimum_per_race,
        "shuffle_reference_mean_conditional_ICC":sum(samples)/len(samples),
        "shuffle_reference_quantiles_05_50_95_conditional_ICC":[
            samples[int((len(samples)-1)*p)] for p in (.05,.5,.95)],
        "fraction_shuffled_ICC_at_least_original":
            (1+sum(s>=observed for s in samples))/(len(samples)+1),
        "shuffle_horse_ID_names_in_original_race_only":True,
        "shuffle_does_not_make_true_race_entry_exchangeable":True,
        "this_fraction_is_not_confirmatory_p_value":True,
        "no_original_horse_IDs_exported":True,
    }


def analyze(rows:list[dict])->dict:
    return {
        "status":"EXPLORATORY_REAL_THOROUGHBRED_RACE_FE_HORSE_RE_ICC_DIAGNOSTIC",
        "all_races_at_least_four_timed_horses":race_fixed_reml(rows,4),
        "races_at_least_six_timed_horses":race_fixed_reml(rows,6),
        # Pre-specified first GPS distance marker strata. Unequal
        # source segment lengths make Gaussian residual variance
        # heteroskedastic, an important sensitivity of pooled ICC.
        "first_section_marker_sensitivity": {
            str(marker):race_fixed_reml(
                [r for r in rows
                 if float(r["first_marker_m"])==marker],4
            )
            for marker in (100.0,150.0,200.0,250.0)
        },
        "leave_one_date_out_four_GPS_minimum":delete_date_sensitivity(rows,4),
        "within_race_horse_ID_shuffle_reference":source_race_identity_shuffle_reference(
            rows,permutations=99,minimum_per_race=4
        ),
        "not_H1_or_H2_or_causal_or_heritability":True,
        "requires_confirmed_starter_roster_true_individual_results_and_jockey_weight_adjustment":True,
        "publisher":"Racing Queensland official source",
    }
