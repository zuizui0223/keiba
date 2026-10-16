#!/usr/bin/env python3
"""Official Queensland jockey/trainer/weight completeness and adjusted ICC.

Racing Queensland's GetHorsesForRace returns HORSES numeric Id, Weight,
Jockey @Id (licence) and Trainer @Id (licence). Their values are kept
ONLY in memory. This exploratory adapter must not infer verified
starters, individual finish times, age, physiology, jockey causation or
horse-by-ground H1/H2 responses.

For EXACTLY the same source records and race fields, fit Gaussian:
   first GPS time = fixed race intercept + fixed nuisance X
                    + N(0, horse random-intercept variance) + error.
We eliminate (race + nuisance) fixed effects with orthonormal contrasts
and profile the restricted Gaussian likelihood. X = (within-race riding
weight, common jockey licence fixed effects, common trainer licence
fixed effects) in separate nested comparisons.

Sparse nuisance categories are pooled into the omitted reference; the
threshold is a *source-support rule*, not an optimized effect model.
No valid age covariate, independent source-result roster, clustered
uncertainty, genetics, or causal inference is provided.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math

import numpy as np
from scipy.linalg import eigh, helmert, svd
from scipy.optimize import minimize_scalar

from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_single_race_id_probe import attr, local, value, xml_nodes
from ecology_rq_race_fixed_icc import race_fixed_reml


WEIGHT_MIN_KG=35.
WEIGHT_MAX_KG=75.
MIN_REPEATED_NUISANCE_RECORDS=4
MIN_CONTRAST_DIMS_AFTER_NUISANCE=55


def official_covariates(root) -> tuple[dict[str,dict],dict]:
    """Extract only *documented* direct source fields; never infer role from name.

    Jockey/Trainer require their original numeric licence ID attribute;
    FullName is NOT a substitute. Suspicious weights are unavailable,
    not silently clipped. Source race start/finish status is unknown.
    """
    nodes=xml_nodes(root,"Horse")
    if not nodes:
        raise ValueError("HOLD_NO_OFFICIAL_HORSES_IN_COVARIATE_XML")
    observed={}
    raw_counts=Counter()
    for node in nodes:
        hid=attr(node,"Id")
        if not hid or not hid.isdecimal() or hid in observed:
            raise ValueError("HOLD_MISSING_OR_DUPLICATE_COVARIATE_HORSES_ID")
        rider=[x for x in node if local(x.tag).casefold()=="jockey"]
        trainer=[x for x in node if local(x.tag).casefold()=="trainer"]
        if len(rider)>1 or len(trainer)>1:
            raise ValueError("HOLD_AMBIGUOUS_LICENSE_ELEMENT")
        jid=attr(rider[0],"Id") if rider else None
        tid=attr(trainer[0],"Id") if trainer else None
        if jid and (not jid.isdecimal() or int(jid)==0):
            jid=None
        if tid and (not tid.isdecimal() or int(tid)==0):
            tid=None
        raw=value(node,"Weight")
        kg=None
        if raw:
            try:
                trial=float(raw)
                if math.isfinite(trial) and WEIGHT_MIN_KG<=trial<=WEIGHT_MAX_KG:
                    kg=trial
            except ValueError:
                pass
        raw_counts["documented_horses"]+=1
        raw_counts["weight_kg_documented_in_plausible_range"]+=int(kg is not None)
        raw_counts["jockey_numeric_license_ID_present"]+=int(bool(jid))
        raw_counts["trainer_numeric_license_ID_present"]+=int(bool(tid))
        raw_counts["all_three_documented_and_valid"]+=int(bool(kg is not None and jid and tid))
        observed[hid]={
            "weight_kg":kg,
            "jockey_license_id":jid,
            "trainer_license_id":tid,
        }
    return observed,{
        "source_operation":"GetHorsesForRace",
        "documented_direct_weight_range_screen_kg":[WEIGHT_MIN_KG,WEIGHT_MAX_KG],
        "age_not_returned_by_this_operation":True,
        "role_IDs_from_Jockey_Trainer_Id_attributes_only":True,
        "counts":dict(raw_counts),
    }


def _complete_sample(rows:list[dict], min_gps:int=4):
    selected=[]
    reasons=Counter()
    by_ground_candidates=Counter()
    by_ground_complete=Counter()
    by_date_candidates=Counter()
    by_date_complete=Counter()
    for r in rows:
        ground=str(r.get("ground") or "UNKNOWN")
        day=str(r.get("day") or "UNKNOWN")
        by_ground_candidates[ground]+=1
        by_date_candidates[day]+=1
        try:
            kg=float(r.get("weight_kg"))
        except (ValueError,TypeError):
            reasons["missing_or_bad_weight"]+=1
            continue
        if not math.isfinite(kg) or not (WEIGHT_MIN_KG<=kg<=WEIGHT_MAX_KG):
            reasons["missing_or_bad_weight"]+=1
            continue
        if not str(r.get("jockey_license_id") or "").isdecimal():
            reasons["missing_jockey_licence"]+=1
            continue
        if not str(r.get("trainer_license_id") or "").isdecimal():
            reasons["missing_trainer_licence"]+=1
            continue
        selected.append(r)
        by_ground_complete[ground]+=1
        by_date_complete[day]+=1
    if not selected:
        return [],{"status":"HOLD_NO_COMPLETE_OFFICIAL_ROLE_AND_WEIGHT_SOURCE_ROWS",
                    "source_candidates":len(rows),"row_exclusions":dict(reasons)}
    relative,quality=prepare(selected,min_race_telemetry=min_gps)
    valid={(r["day"],r["race_number"],r["horse_id"]) for r in relative}
    trimmed=[r for r in selected
             if (r["day"],r["race_number"],r["horse_id"]) in valid]
    by_ground_kept=Counter(str(r.get("ground") or "UNKNOWN") for r in trimmed)
    by_date_kept=Counter(str(r.get("day") or "UNKNOWN") for r in trimmed)
    # Source attrition can differ substantially between going categories
    # and dates, so baseline ICC changes after filtering are NOT an
    # inferential comparison with the full source population.
    def attrition_rates(counts,total,after_field):
        return {str(label):{
            "source_positive_first_GPS_rows":count,
            "all_three_documented_covariate_rows":int(total[label]),
            "after_fully_documented_race_min4_rows":int(after_field[label]),
            "fraction_of_source_rows_remaining":(
                float(after_field[label]/count) if count else None
            ),
        } for label,count in sorted(counts.items())}
    return trimmed,{
        "status":"SOURCE_NUISANCE_COMPLETE_CASE_COHORT_ONLY",
        "source_candidates":len(rows),
        "raw_rows_with_weight_jockey_trainer":len(selected),
        "row_exclusions":dict(reasons),
        "valid_complete_case_fields_after_minimum_GPS_filter":
            quality["races_with_at_least_requested_minimum_positive_first_intervals"],
        "valid_complete_case_rows_after_field_filter":len(trimmed),
        "original_positive_GPS_rows_excluded_after_nuisance_gate":len(rows)-len(trimmed),
        "coverage_by_official_race_ground":attrition_rates(
            by_ground_candidates,by_ground_complete,by_ground_kept
        ),
        "coverage_by_original_meeting_date":attrition_rates(
            by_date_candidates,by_date_complete,by_date_kept
        ),
        "remaining_fraction_of_original_positive_first_section_records":
            float(len(trimmed)/len(rows)),
        "selection_on_source_availability_not_welfare_or_true_finish":True,
    }


def _nuisance_basis(rows:list[dict], mode:str):
    """Predictor columns contain NO intercept: race contrasts remove all race means."""
    if mode not in ("weight","weight_jockey","weight_jockey_trainer"):
        raise ValueError("HOLD_UNAPPROVED_FIXED_NUISANCE_MODEL")
    kg=np.array([float(r["weight_kg"]) for r in rows])
    if np.std(kg)<1e-9:
        return None,{"status":"HOLD_NO_WEIGHT_VARIATION"}
    x=[(kg-kg.mean())/kg.std()]
    diagnostics={
        "mode":mode,
        "riding_weight_source_kg_range":[float(kg.min()),float(kg.max())],
        "nuisance_levels_minimum_records":MIN_REPEATED_NUISANCE_RECORDS,
        "age_not_available":True,
    }
    for field,label in (
        ("jockey_license_id","jockey"),
        ("trainer_license_id","trainer"),
    ):
        if label=="trainer" and mode!="weight_jockey_trainer":
            continue
        if label=="jockey" and mode=="weight":
            continue
        vals=[str(r[field]) for r in rows]
        ct=Counter(vals)
        groups=sorted(k for k,v in ct.items() if v>=MIN_REPEATED_NUISANCE_RECORDS)
        diag={
            "distinct_valid_license_IDs":len(ct),
            "IDs_with_4plus_positive_GPS_records":len(groups),
            "ID_observations_covered_by_4plus_categories":
                sum(ct[c] for c in groups),
            "all_other_license_IDs_pooled_into_unlabelled_reference":True,
        }
        diagnostics[label+"_support"]=diag
        # No valid common categories means no reliably estimable
        # fixed rider/trainer design. Explicit HOLD, no implicit 0-effect.
        if len(groups)<2:
            return None,{
                **diagnostics,
                "status":"HOLD_INSUFFICIENT_"+label.upper()+"_LEVEL_SUPPORT"
            }
        # One level omitted as reference; race dummies may absorb some
        # other columns (tested with SVD rank after Helmert transform).
        for lic in groups:
            x.append(np.array([int(v==lic) for v in vals],dtype=float))
    return np.column_stack(x),diagnostics


def _fit_projected(z:np.ndarray, Z:np.ndarray)->dict:
    dims=len(z)
    M=Z@Z.T
    eigen,U=eigh(M,check_finite=True)
    if eigen.min() < -1e-7:
        raise ValueError("HOLD_NON_PSD_RANDOM_HORSE_COVARIANCE")
    eigen=np.clip(eigen,0.,None)
    energy=(U.T@z)**2
    if (len(eigen)<MIN_CONTRAST_DIMS_AFTER_NUISANCE or
            np.ptp(eigen)<1e-7 or
            sum(energy)<1e-9):
        return {"status":"HOLD_NO_CROSS_RACE_HORSE_VARIANCE_IDENTIFIABILITY"}
    def loss(log_ratio:float):
        r=math.exp(log_ratio)
        v=1+r*eigen
        err=float(np.sum(energy/v)/dims)
        if err<=0 or not math.isfinite(err):
            return float("inf")
        return dims*math.log(err)+float(np.log(v).sum())
    res=minimize_scalar(loss,bounds=(-18.,18.),method="bounded",
                        options={"xatol":1e-7,"maxiter":250})
    if not res.success or not math.isfinite(res.fun):
        return {"status":"HOLD_NUMERIC_NUISANCE_REML"}
    null=loss(-80.)
    if res.fun>=null-1e-7:
        rr=0.
        state="EXPLORATORY_ADJUSTED_ICC_ZERO_VARIANCE_BOUNDARY"
    elif min(abs(res.x-(-18.)),abs(res.x-18.))<.15:
        return {"status":"HOLD_NUMERIC_RATIO_AT_SEARCH_LIMIT"}
    else:
        rr=math.exp(res.x)
        state="EXPLORATORY_ADJUSTED_ICC_MODEL_POINT_ONLY"
    variance_e=float(np.sum(energy/(1+rr*eigen))/dims)
    return {
        "status":state,
        "horse_variance_sec2":float(rr*variance_e),
        "residual_variance_sec2":variance_e,
        "conditional_ICC_point":float(rr/(1+rr)),
        "restricted_profile_improvement_vs_no_horse_variance":float(max(0,null-res.fun)),
        "causal_horse_effect_or_valid_significance":False,
        "ICC_robust_cluster_confidence_interval":False,
    }


def adjusted_race_icc(rows:list[dict],mode:str)->dict:
    """REML after orthogonal elimination of observed race and nuisance X.

    Nested models are compared ONLY on a common source-complete case
    population. Restricted profile objectives from different fixed-X
    models are NOT directly comparable (different contrast spaces).
    """
    if not rows:
        return {"status":"HOLD_NO_COMPLETE_ROLE_COHORT"}
    by_race=defaultdict(list)
    for row in rows:
        by_race[(row["day"],row["race_number"])].append(row)
    counts=Counter(r["horse_id"] for r in rows)
    repeated_ids=sum(v>=2 for v in counts.values())
    n_source_dates=len({r["day"] for r in rows})
    if (len(by_race)<12 or len(rows)<80 or len(counts)<30
            or repeated_ids<20 or n_source_dates<8):
        # Correct a key biological-identifiability trap: with few
        # repeated HORSES IDs, fixed rider/trainer contrasts can produce
        # a large numeric variance ratio WITHOUT evidence of stable
        # individual variance. A successfully optimized number is not
        # an identifiable horse component.
        return {
            "status":"HOLD_TOO_FEW_REPEATED_HORSES_OR_SOURCE_DATES_FOR_NUISANCE_ICC",
            "source_rows":len(rows),
            "source_races":len(by_race),
            "source_date_clusters":n_source_dates,
            "distinct_original_HORSES_IDs":len(counts),
            "HORSES_IDs_observed_2plus_times":repeated_ids,
            "point_estimate_suppressed_not_imputed_zero":True,
            "original_animal_and_licence_IDs_not_exported":True,
        }
    IDs=list(dict.fromkeys(r["horse_id"] for r in rows))
    index={hid:i for i,hid in enumerate(IDs)}
    labels,_info=_nuisance_basis(rows,mode)
    if labels is None:
        return {"status":_info["status"],"predictor_design":_info}
    # Use stable input row order; build an anonymous local lookup for X.
    lookup={
        (r["day"],r["race_number"],r["horse_id"]):i
        for i,r in enumerate(rows)
    }
    zs=[];B=[];W=[]
    for rac,group in by_race.items():
        n=len(group)
        if n<4:
            raise ValueError("HOLD_RACE_LOST_MINIMUM_COMPLETE_CASE_COVERAGE")
        Q=helmert(n,full=False)
        y=np.array([r["first_section_sec"] for r in group],dtype=float)
        zs.append(Q@y)
        inc=np.zeros((n,len(IDs)))
        for i,r in enumerate(group):
            inc[i,index[r["horse_id"]]]=1.
        B.append(Q@inc)
        X=np.array([labels[lookup[(r["day"],r["race_number"],r["horse_id"])]] for r in group])
        W.append(Q@X)
    zz=np.concatenate(zs)
    BB=np.vstack(B)
    WW=np.vstack(W)
    singular_U,S,_=svd(WW,full_matrices=True)
    eps=np.finfo(float).eps
    threshold=max(WW.shape)*eps*S[0]*80 if len(S) else 0.
    rank=int(sum(S>threshold))
    if rank>=len(zz)-MIN_CONTRAST_DIMS_AFTER_NUISANCE:
        return {"status":"HOLD_NUISANCE_FIXED_EFFECT_DESIGN_EXHAUSTS_RACE_CONTRASTS",
                "nuisance_design_rank":rank,"source_race_contrast_dimensions":len(zz),
                "predictor_design":_info}
    residual_basis=singular_U[:,rank:].T
    z0=residual_basis@zz
    B0=residual_basis@BB
    result=_fit_projected(z0,B0)
    return {
        **result,
        "nuisance_mode":mode,
        "source_eligible_rows":len(rows),
        "source_distinct_races":len(by_race),
        "HORSES_IDs_observed_twice_or_more":sum(
            n>=2 for n in Counter(r["horse_id"] for r in rows).values()
        ),
        "original_race_contrast_dimensions":len(zz),
        "source_nuisance_basis_candidate_columns":WW.shape[1],
        "within_race_nuisance_design_rank":rank,
        "remaining_restricted_likelihood_dimensions":len(z0),
        "predictor_design":_info,
        "horse_ICC_contains_unmodeled_age_fitness_rider_interaction_and_selective_entries":True,
        "not_ground_random_slope_or_competitor_social_response":True,
        "not_confirmatory_robust_inference":True,
        "individual_IDs_names_jockey_licences_trainer_licences_not_exported":True,
    }


def leave_one_meeting_out_adjusted_ICC(complete:list[dict])->dict:
    """Same original source-complete cohort, deleting ONE meeting date.

    Each re-fit uses identical held-in rows for unadjusted race-FE horse
    ICC and fully weight+jockey+trainer adjusted ICC. The label support
    and Gaussian residual assumptions can change when a meeting is
    deleted; this is an observational stability analysis, *not* a
    confidence interval or a jackknife variance estimate.
    """
    days=sorted({r["day"] for r in complete})
    if len(days)<8:
        return {
            "status":"HOLD_TOO_FEW_COMPLETE_SOURCE_DATES_FOR_JACKKNIFE_SCREEN",
            "source_days":len(days),
            "no_original_identifiers_exported":True,
        }
    baseline=[]
    fully=[]
    delta=[]
    hold_reasons=Counter()
    for day in days:
        kept=[r for r in complete if r["day"]!=day]
        main=race_fixed_reml(kept,4)
        full=adjusted_race_icc(kept,"weight_jockey_trainer")
        x=main.get("conditional_observational_ICC_point_estimate")
        y=full.get("conditional_ICC_point")
        if x is None or y is None:
            hold_reasons[(main["status"] if x is None else full["status"])]+=1
            continue
        baseline.append(float(x))
        fully.append(float(y))
        delta.append(float(y-x))
    n=len(baseline)
    if n<len(days)-2:
        return {
            "status":"HOLD_UNSTABLE_DATE_DELETION_MODEL_IDENTIFIABILITY",
            "source_days":len(days),
            "successful_identical_cohort_model_pairs":n,
            "date_deletion_model_HOLD_counts":dict(hold_reasons),
            "not_a_95_percent_confidence_interval":True,
            "no_original_identifiers_exported":True,
        }
    return {
        "status":"EXPLORATORY_DATE_DELETION_NUISANCE_ICC_STABILITY_NOT_CI",
        "source_complete_case_dates":len(days),
        "same_sample_baseline_and_adjusted_in_each_leave_one_date_out_fit":True,
        "source_dates_with_both_model_ICCs":n,
        "source_date_model_HOLD_counts":dict(hold_reasons),
        "unadjusted_conditional_ICC_min":min(baseline),
        "unadjusted_conditional_ICC_max":max(baseline),
        "weight_jockey_trainer_conditional_ICC_min":min(fully),
        "weight_jockey_trainer_conditional_ICC_max":max(fully),
        "full_minus_baseline_conditional_ICC_min":min(delta),
        "full_minus_baseline_conditional_ICC_max":max(delta),
        "date_deletion_fits_with_lower_ICC_after_full_adjustment":
            sum(x<0 for x in delta),
        "date_deletion_fits_with_higher_ICC_after_full_adjustment":
            sum(x>0 for x in delta),
        "not_a_95_percent_confidence_interval":True,
        "not_a_prospective_validation_or_causal_attribution":True,
        "no_original_identifiers_exported":True,
    }


def compare(rows:list[dict], minimum_GPS:int=4)->dict:
    complete,gate=_complete_sample(rows,minimum_GPS)
    if not complete:
        return {
            "status":"HOLD_NO_SOURCE_COMPLETE_COVARIATES",
            "source_gate":gate,
            "no_horse_jockey_trainer_IDs_exported":True,
        }
    # Baseline on precisely the same complete-case rows as adjusted
    # models, no inappropriate ICC comparisons across different horses.
    base=race_fixed_reml(complete,minimum_GPS)
    source_counts=Counter(r["horse_id"] for r in complete)
    source_feasibility={
        "complete_source_observations":len(complete),
        "observed_original_races":len({
            (r["day"],r["race_number"]) for r in complete
        }),
        "observed_original_meeting_dates":len({r["day"] for r in complete}),
        "different_original_HORSES_IDs":len(source_counts),
        "repeated_HORSES_IDs_with_2plus_observations":sum(
            n>=2 for n in source_counts.values()
        ),
        "minimum_repeated_HORSES_IDs_for_nuisance_ICC_point":20,
        "minimum_independent_source_dates_for_nuisance_ICC_point":8,
        "source_candidate_rows_not_guaranteed_actual_starters":True,
    }
    if base.get("conditional_observational_ICC_point_estimate") is None:
        return {
            "status":"HOLD_SOURCE_COMPLETE_CASE_RANDOM_HORSE_INTERCEPT_UNIDENTIFIABLE",
            "source_gate":gate,
            "source_repeated_horse_support":source_feasibility,
            "models":{
                "same_rows_unadjusted_race_HORSES":base,
                "weight_within_race":{"status":"HOLD_SHARED_SOURCE_BASELINE_UNIDENTIFIABLE"},
                "weight_plus_jockey_license":{"status":"HOLD_SHARED_SOURCE_BASELINE_UNIDENTIFIABLE"},
                "weight_jockey_trainer_license":{
                    "status":"HOLD_SHARED_SOURCE_BASELINE_UNIDENTIFIABLE",
                    "numeric_ICC_suppressed_not_assumed_zero":True,
                },
            },
            "modeled_row_overlap_identical_for_all_models":True,
            "adjusted_ICC_not_reported_when_original_source_baseline_HOLD":True,
            "same_source_cohort_full_adjustment_minus_unadjusted_ICC_point":None,
            "no_horse_jockey_trainer_IDs_exported":True,
            "no_race_horse_betting_scores_or_individual_predictions":True,
        }
    models={
        "same_rows_unadjusted_race_HORSES":base,
        "weight_within_race":adjusted_race_icc(complete,"weight"),
        "weight_plus_jockey_license":adjusted_race_icc(complete,"weight_jockey"),
        "weight_jockey_trainer_license":adjusted_race_icc(complete,"weight_jockey_trainer"),
    }
    base_icc=base.get("conditional_observational_ICC_point_estimate")
    adjusted_icc=models["weight_jockey_trainer_license"].get("conditional_ICC_point")
    source_delta=(float(adjusted_icc-base_icc)
                  if base_icc is not None and adjusted_icc is not None else None)
    date_stability=leave_one_meeting_out_adjusted_ICC(complete)
    return {
        "status":"ORIGINAL_HORSE_SOURCE_EXPLORATORY_COVARIATE_ADJUSTMENT_ONLY",
        "source_repeated_horse_support":source_feasibility,
        "date_deletion_same_source_baseline_vs_nuisance_stability":date_stability,
        "source_gate":gate,
        "same_source_cohort_full_adjustment_minus_unadjusted_ICC_point":
            source_delta,
        "delta_is_not_caused_by_nuisance_variables_or_significance":True,
        "modeled_row_overlap_identical_for_all_models":True,
        "source_real_horse_covariate_support": {
            "distinct_jockey_licences":len({r["jockey_license_id"] for r in complete}),
            "distinct_trainer_licences":len({r["trainer_license_id"] for r in complete}),
            "jockey_licences_used_by_2plus_distinct_HORSES_IDs":sum(
                len(horses)>=2 for horses in _id_to_horses(complete,"jockey_license_id").values()
            ),
            "trainer_licences_used_by_2plus_distinct_HORSES_IDs":sum(
                len(horses)>=2 for horses in _id_to_horses(complete,"trainer_license_id").values()
            ),
            "HORSES_IDs_with_multiple_jockey_licences":sum(
                len(vals)>=2 for vals in _horse_to_ids(complete,"jockey_license_id").values()
            ),
            "HORSES_IDs_with_multiple_trainer_licences":sum(
                len(vals)>=2 for vals in _horse_to_ids(complete,"trainer_license_id").values()
            ),
            "source_carries_age_or_birthdate":False,
        },
        "models":models,
        "ICC_from_race_and_nuisance_fixed_effects_is_not_heritability_or_causal":True,
        "no_horse_jockey_trainer_IDs_exported":True,
        "no_race_horse_betting_scores_or_individual_predictions":True,
        "limitations":[
            "Only original publicly visible Weight, Jockey/@Id, Trainer/@Id fields enter nuisance models; no invented age.",
            "Complete-case source selection may change individual/race population relative to original 523 rows.",
            "Jockey and trainer licences with fewer than 4 observed source starts form an unmodelled reference; effects are not independently causal.",
            "Original race categories and all entered animals do not establish final starters/finishers.",
            "Jockey/trainer persistent pairings, injury/fitness, resting interval, age and selection may remain confounded with HORSES ID.",
            "Normal iid residual and constant measurement variance remain assumptions; no validated date-clustered ICC uncertainty is provided.",
            "H1 ground response and H2 competitor context are not fitted or scientifically identified here.",
        ],
    }


def _id_to_horses(rows:list[dict],field:str):
    out=defaultdict(set)
    for r in rows:
        out[r[field]].add(r["horse_id"])
    return out


def _horse_to_ids(rows:list[dict],field:str):
    out=defaultdict(set)
    for r in rows:
        out[r["horse_id"]].add(r[field])
    return out
