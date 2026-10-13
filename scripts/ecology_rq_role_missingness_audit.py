#!/usr/bin/env python3
"""Original RQ source-covariate completeness vs observed early timing.

The ONLY empirical question is SOURCE SELECTION:
Do original HORSES-ID first-GPS observed records WITH all of original
Weight/Jockey/Trainer licence fields systematically have different first
GPS sectional timings from records missing ≥1 of those fields *within
the same original race*?

We use ONLY 2026 fixed Cannon Park dates/official original HORSES-ID
GPS records already screened in ecology_rq_2026_calendar_overlap.
No HORSES IDs/names/licence IDs/individual rows are published.

This is NOT estimation of actual starter/finisher missingness, horse H1
ground reaction or H2 competitive behavior. GPS *unobserved* animals
are NOT present: even a null result cannot justify MCAR/MAR assumptions
for these unobserved outcomes. Race-level mean differences, a 499-seed
WITHIN-RACE reassignment of source-metadata completeness flags, and
delete-one-meeting-day sensitivity are descriptive diagnostics only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import random
from statistics import mean


MIN_OBSERVED_PER_RACE=4
MIN_MIXED_RACES=8
MIN_MIXED_DATES=4


def has_complete_documented_roles(row:dict)->bool:
    try:
        kg=float(row.get("weight_kg"))
    except (TypeError,ValueError):
        return False
    if not math.isfinite(kg) or not 35.0<=kg<=75.0:
        return False
    return all(
        str(row.get(label) or "").isdecimal()
        and int(row[label])>0
        for label in ("jockey_license_id","trainer_license_id")
    )


def build_race_strata(rows:list[dict],
                      min_race_telemetry:int=MIN_OBSERVED_PER_RACE)->tuple[list[dict],dict]:
    if min_race_telemetry<4:
        raise ValueError("HOLD_COVARIATE_MISSINGNESS_LOW_FIELD_MIN")
    indexed=defaultdict(list)
    observed=set()
    for row in rows:
        required={"day","race_number","horse_id","horse_name",
                  "first_section_sec","first_marker_m","distance","class","ground"}
        if required-set(row):
            raise ValueError("HOLD_COVARIATE_MISSINGNESS_REQUIRED_ORIGINAL_ROW_FIELDS")
        key=(row["day"],row["race_number"],row["horse_id"])
        if key in observed:
            raise ValueError("HOLD_DUPLICATE_INTERNAL_HORSES_ID_IN_RACE")
        observed.add(key)
        duration=float(row["first_section_sec"])
        if not math.isfinite(duration) or duration<=0:
            raise ValueError("HOLD_NO_VERIFIED_FIRST_POSITIVE_SOURCE_INTERVAL")
        indexed[(row["day"],row["race_number"])].append(row)
    source_races=len(indexed)
    used=[]
    quality=Counter()
    for (day,race),records in sorted(indexed.items()):
        quality["observed_positive_GPS_race_headers"]+=1
        quality["positive_GPS_source_rows"]+=len(records)
        if len(records)<min_race_telemetry:
            quality["fields_below_minimum_observed_GPS"]+=1
            continue
        if len({r["first_marker_m"] for r in records})!=1 or len(
            {r["distance"] for r in records})!=1:
            raise ValueError("HOLD_UNHOMOGENEOUS_OFFICIAL_RACE_FIRST_SECTION")
        if len({r["ground"] for r in records})!=1:
            raise ValueError("HOLD_UNHOMOGENEOUS_OFFICIAL_RACE_GROUND")
        documented=[has_complete_documented_roles(r) for r in records]
        n1=sum(documented)
        n0=len(documented)-n1
        quality["races_with_minimum_timed_GPS"]+=1
        quality["timed_GPS_rows_in_minimum_races"]+=len(records)
        quality["documented_weight_jockey_trainer_rows_in_minimum_races"]+=n1
        quality["incomplete_weight_jockey_trainer_rows_in_minimum_races"]+=n0
        if not n1 or not n0:
            quality["races_with_no_within_race_role_completeness_contrast"]+=1
            continue
        used.append({
            "day":day,
            "ground":records[0]["ground"],
            "timings":[float(r["first_section_sec"]) for r in records],
            "documented_flags":documented,
            "n_complete":n1,
            "n_incomplete":n0,
        })
        quality["races_with_both_complete_and_incomplete_roles"]+=1
        quality["complete_role_rows_in_mixed_races"]+=n1
        quality["incomplete_role_rows_in_mixed_races"]+=n0
    quality["original_distinct_race_headers"]=source_races
    quality["source_days_with_both_complete_and_incomplete_rows"]=len({s["day"] for s in used})
    return used,dict(quality)


def _contrast(y:list[float],flags:list[bool])->float:
    if len(y)!=len(flags) or all(flags) or not any(flags):
        raise ValueError("HOLD_WITHIN_RACE_TWO_METADATA_STATES_REQUIRED")
    return mean(v for v,f in zip(y,flags) if f)-mean(
        v for v,f in zip(y,flags) if not f)


def _statistic(strata:list[dict])->tuple[float,float,dict]:
    if not strata:
        raise ValueError("HOLD_NO_MIXED_RACES")
    diffs=[]
    weights=[]
    by_going=defaultdict(list)
    by_date=defaultdict(list)
    for s in strata:
        diff=_contrast(s["timings"],s["documented_flags"])
        diffs.append(diff)
        n1=s["n_complete"];n0=s["n_incomplete"]
        # Harmonic effective sample weight of within-race means.
        weights.append(n1*n0/(n1+n0))
        by_going[s["ground"]].append(diff)
        by_date[s["day"]].append(diff)
    out={
        "source_races_with_both_documented_and_incomplete_metadata":len(strata),
        "original_dates_with_both_roles_states":len(by_date),
        "equal_race_weighted_complete_minus_incomplete_first_sec":mean(diffs),
        "positive_race_differences_complete_slower_than_incomplete":
            sum(x>0 for x in diffs),
        "negative_race_differences_complete_faster_than_incomplete":
            sum(x<0 for x in diffs),
        "source_ground_specific_equal_race_mean_diff_sec":{
            k:{"source_races":len(v),"complete_minus_incomplete_sec":mean(v)}
            for k,v in sorted(by_going.items())
        },
        "date_specific_completeness_difference_counts":{
            day:{"source_races":len(v),"direction_complete_slower_count":sum(x>0 for x in v)}
            for day,v in sorted(by_date.items())
        },
    }
    weighted=sum(x*w for x,w in zip(diffs,weights))/sum(weights)
    return mean(diffs),weighted,out


def audit(
    rows:list[dict], *, min_race_telemetry:int=4,
    permutations:int=499,seed:int=20261013,
)->dict:
    if not 49<=permutations<=1999:
        raise ValueError("HOLD_UNSUPPORTED_SOURCE_MISSINGNESS_REASSIGNMENT_COUNT")
    strata,q=build_race_strata(rows,min_race_telemetry)
    base={
        "outcome":"original FIRST positive GPS section seconds; not certified finish time",
        "missingness":"presence of original public registered Weight+JockeyId+TrainerId among GPS-observed HORSES ID rows",
        "source_positive_GPS_rows_not_documenting_licences_are_NOT_zero_pace":
            True,
        "not_a_test_of_unobserved_GPS_outcomes_or_nonfinishers":True,
        "source_provenance":"Racing Queensland first-party original HORSES XML + GPS sectionals",
        "minimum_positive_GPS_animals_per_original_race":min_race_telemetry,
        "original_source_support":q,
        "no_original_horse_jockey_trainer_IDs_names_or_individual_rows_exported":True,
        "not_mcAR_mar_mnar_identification_or_selection_correction":True,
        "no_causes_of_documentation_missingness_identified":True,
    }
    if (len(strata)<MIN_MIXED_RACES or
            q["source_days_with_both_complete_and_incomplete_rows"]<MIN_MIXED_DATES):
        return {**base,"status":"HOLD_TOO_FEW_WITHIN_RACE_SOURCE_METADATA_STATES"}
    original,weighted,description=_statistic(strata)
    rng=random.Random(seed)
    null=[]
    for _ in range(permutations):
        variant=[]
        for race in strata:
            flags=list(race["documented_flags"])
            rng.shuffle(flags)
            variant.append({**race,"documented_flags":flags})
        val,_,_=_statistic(variant)
        null.append(val)
    null.sort()
    signs=Counter()
    delete=[]
    for excluded in sorted({s["day"] for s in strata}):
        retained=[s for s in strata if s["day"]!=excluded]
        if len(retained)<MIN_MIXED_RACES:
            continue
        val,_,_=_statistic(retained)
        delete.append(val)
        signs["positive"]+=int(val>0)
        signs["negative"]+=int(val<0)
    if len(delete)<4:
        deletion={
            "status":"HOLD_TOO_FEW_SOURCE_DATES_FOR_DELETE_ONE_MEETING_SENSITIVITY",
            "fitted_sources":len(delete)
        }
    else:
        deletion={
            "status":"EXPLORATORY_DATE_DELETION_STABILITY_NOT_CI",
            "deleted_dates_refitted":len(delete),
            "min_equal_race_mean_difference_sec":min(delete),
            "max_equal_race_mean_difference_sec":max(delete),
            "not_an_independent_95pct_uncertainty_interval":True,
            "positive_date_deletion_results":signs["positive"],
            "negative_date_deletion_results":signs["negative"],
        }
    return {
        **base,"status":"EXPLORATORY_ORIGINAL_METADATA_COMPLETENESS_TIMING_ASSOCIATION",
        "observed_within_race_descriptive": {
            **description,
            "harmonic_source_group_weighted_mean_complete_minus_incomplete_sec":
                weighted,
        },
        "race_stratified_completeness_label_shuffle_reference":{
            "source_label_shuffles":permutations,
            "observed_equal_race_difference_sec":original,
            "mean_null_equal_race_difference_sec":mean(null),
            "reference_05_50_95_quantiles_sec":[
                null[int((len(null)-1)*p)] for p in (.05,.5,.95)],
            "fraction_absolute_shuffle_diff_at_least_observed":
                (1+sum(abs(x)>=abs(original) for x in null))/(1+len(null)),
            "not_a_confirmatory_p_value_or_randomized_source_missingness_test":
                True,
        },
        "delete_one_original_meeting_date":deletion,
        "interpretation":(
            "Association between recorded-source metadata completeness "
            "and a simultaneously observed first GPS interval, within "
            "the observed timing subset. It neither proves nor refutes "
            "missing-at-random of unobserved GPS/true finish outcomes; "
            "no inverse-probability correction is identified."
        ),
    }
