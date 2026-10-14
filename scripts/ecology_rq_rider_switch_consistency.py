#!/usr/bin/env python3
"""Exploratory original-RQ same-horse early-GPS consistency across Jockey/@Id changes.

Purely observational source-readiness/retrospective description on the
PREVIOUSLY LOCKED 12-date Cannon Park 2026 horse/GPS records; new rider
question developed after the source-conditioned positive horse ICC.
No certified starter/finish or postrace jockey, causal rider effect,
innate animal personality, H1 random slope, H2 social interaction or bet.

Original runner names, HORSES/jockey/trainer IDs and first-GPS row outcomes
stay in memory; ALL returned objects contain anonymized aggregate counts.
See docs/ecology-rq-rider-switch-persistence-design.md.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
import argparse
import json
from pathlib import Path
import random
from statistics import mean

from ecology_rq_early_pace_repeatability import prepare


MIN_IDS = 20
MIN_STRATA = 20
MIN_SOURCE_DATES = 6
MIN_MEETING_DATE_PAIR_TYPES = 6
GAP_CUTOFF_DAYS = 90
DEFAULT_REFERENCE_SHUFFLES = 199
DEFAULT_SEED = 20261014

MODES = (
    "switched",
    "same",
    "switched_same_trainer",
    "switched_gap_at_most_90d",
    "switched_gap_over_90d",
)


def _numeric_id(val):
    """Validated internal original-source licence ID; never use names."""
    s=str(val or "").strip()
    return s if s.isdecimal() and int(s)>0 else None


def source_timed_panel(rows: list[dict], min_gps: int = 4):
    """Build race-relative endpoint with ALL first-GPS timed peers.

    Missing jockey metadata on *peers* must not change the denominator
    for a documented-rider focal animal.
    """
    eligible, q=prepare(rows, min_race_telemetry=min_gps)
    by_key={}
    names=defaultdict(set)
    for original in rows:
        k=(original["day"],original["race_number"],original["horse_id"])
        if k in by_key:
            raise ValueError("HOLD_DUPLICATE_ORIGINAL_HORSE_ID_IN_SOURCE_RACE")
        by_key[k]=original
    for r in eligible:
        names[r["horse_id"]].add(r["horse_name"])
    if any(len(v)>1 for v in names.values()):
        raise ValueError("HOLD_HORSES_ID_NAME_CONSISTENCY_NOT_VERIFIED")
    timed=[]
    for r in eligible:
        original=by_key[(r["day"],r["race_number"],r["horse_id"])]
        timed.append({
            "horse_id":r["horse_id"],
            "horse_name":r["horse_name"],
            "day":r["day"],
            "race_number":r["race_number"],
            "distance":r["official_distance"],
            "marker":round(r["first_section_marker"],4),
            "race_class":r["race_class"],
            "relative_seconds":float(r["relative_early_section_sec"]),
            "jockey_id":_numeric_id(original.get("jockey_license_id")),
            "trainer_id":_numeric_id(original.get("trainer_license_id")),
        })
    return timed,{
        "source_GPS_positive_rows_before_race_minimum":len(rows),
        "source_races_after_positive_GPS_field_gate":
            q["races_with_at_least_requested_minimum_positive_first_intervals"],
        "source_GPS_rows_after_race_minimum":len(timed),
        "original_source_dates_after_race_minimum":len({r["day"] for r in timed}),
        "source_rows_with_valid_original_Jockey_Id":
            sum(r["jockey_id"] is not None for r in timed),
        "source_rows_with_both_Jockey_and_Trainer_Id":
            sum(r["jockey_id"] is not None and r["trainer_id"] is not None
                for r in timed),
        "rider_incomplete_peers_retained_in_race_baseline":True,
        "rider_source_values_are_declared_not_actual_verified_postrace":True,
    }


def _context_key(r:dict, strict_class:bool)->tuple:
    return (r["horse_id"],r["distance"],r["marker"],
            r["race_class"] if strict_class else None)


def pair_records(timed:list[dict], *, strict_class:bool):
    by_stratum=defaultdict(list)
    for r in timed:
        if r["jockey_id"] is not None:
            by_stratum[_context_key(r,strict_class)].append(r)

    result=[]
    for key, items in by_stratum.items():
        if len(items)<2:
            continue
        if len({r["day"] for r in items})!=len(items):
            raise ValueError("HOLD_ONE_HORSE_MORE_THAN_ONCE_ON_SOURCE_DATE")
        # Join only pairwise distinct dates and identical marker/distance.
        for i in range(len(items)):
            for j in range(i+1,len(items)):
                a,b=items[i],items[j]
                gap=abs((date.fromisoformat(a["day"])-date.fromisoformat(b["day"])).days)
                result.append({
                    "key":key,       # original source ID stays in memory
                    "horse_id":a["horse_id"],
                    "days":tuple(sorted((a["day"],b["day"]))),
                    "gap_days":gap,
                    "switched":a["jockey_id"]!=b["jockey_id"],
                    "same_known_trainer":(
                        a["trainer_id"] is not None
                        and a["trainer_id"]==b["trainer_id"]
                    ),
                    "pair_product_s2":a["relative_seconds"]*b["relative_seconds"],
                })
    return result


def _is_mode(pair:dict, mode:str)->bool:
    if mode=="switched":
        return pair["switched"]
    if mode=="same":
        return not pair["switched"]
    if mode=="switched_same_trainer":
        return pair["switched"] and pair["same_known_trainer"]
    if mode=="switched_gap_at_most_90d":
        return pair["switched"] and pair["gap_days"]<=GAP_CUTOFF_DAYS
    if mode=="switched_gap_over_90d":
        return pair["switched"] and pair["gap_days"]>GAP_CUTOFF_DAYS
    raise ValueError("HOLD_UNKNOWN_RIDER_CHANGE_PAIR_MODE")


def summarize_pairs(pairs:list[dict],mode:str):
    chosen=[p for p in pairs if _is_mode(p,mode)]
    units=defaultdict(list)
    horses=set()
    meeting_dates=set()
    meeting_date_pairs=set()
    for p in chosen:
        units[p["key"]].append(p["pair_product_s2"])
        horses.add(p["horse_id"])
        meeting_dates.update(p["days"])
        meeting_date_pairs.add(p["days"])
    stats={
        "status":"HOLD_INSUFFICIENT_WITHIN_ID_CROSS_DATE_RIDER_PAIR_SUPPORT",
        "distinct_official_HORSES_IDs":len(horses),
        "horse_by_matching_distance_marker_class_strata":len(units),
        "within_horse_cross_date_pairs":len(chosen),
        "original_meeting_dates_represented":len(meeting_dates),
        "unique_calendar_meeting_date_pairs":len(meeting_date_pairs),
        "no_original_horse_rider_trainer_identifiers_exported":True,
        "this_is_not_actual_verified_jockey_switch_or_causal_rider_effect":True,
    }
    eligible=(len(horses)>=MIN_IDS and len(units)>=MIN_STRATA
              and len(meeting_dates)>=MIN_SOURCE_DATES
              and len(meeting_date_pairs)>=MIN_MEETING_DATE_PAIR_TYPES)
    if eligible:
        # Equal weight each horse-by-distance-marker stratum, not pair count.
        stats["status"]="EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY"
        stats["equal_horse_stratum_mean_pair_product_seconds_squared"]=mean(
            mean(v) for v in units.values()
        )
    return stats


def _one_pair_set(timed:list[dict], strict_class:bool)->dict:
    pairs=pair_records(timed, strict_class=strict_class)
    stats={mode:summarize_pairs(pairs,mode) for mode in MODES}
    # Same animal/stratum appearing in both same- and switched-rider
    # pair comparisons indicates whether groups overlap; no difference
    # coefficient is inferred from this quantity.
    equal={p["key"] for p in pairs if not p["switched"]}
    switched={p["key"] for p in pairs if p["switched"]}
    return {
        "original_eligible_pair_count_with_both_valid_source_jockey_IDs":len(pairs),
        "strata_with_both_same_and_changed_declared_jockey_pairs":
            len(equal&switched),
        "original_source_class_also_matched":strict_class,
        "status_by_rider_pair_condition":stats,
    }


def rider_label_shuffled_time_reference(
    timed:list[dict], *,
    strict_class:bool=False, permutations:int=DEFAULT_REFERENCE_SHUFFLES,
    seed:int=DEFAULT_SEED,
)->dict:
    if not (50<=permutations<=499):
        raise ValueError("HOLD_UNAPPROVED_SOURCE_SHUFFLE_COUNT")
    primary=_one_pair_set(timed,strict_class)["status_by_rider_pair_condition"]["switched"]
    if primary["status"]!="EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY":
        return {
            "status":"HOLD_RIDER_SWITCH_PAIR_SUPPORT_BELOW_PREDECLARED_MINIMUM",
            "valid_null_references":0,
            "not_a_zero_effect_or_confirmatory_significance":True,
        }

    # The race-relative outcome, not horse/rider identities, is shuffled
    # within each ACTUAL race, keeping the realized source membership,
    # documented rider switch and date/distance classes intact.
    indices=defaultdict(list)
    for i,r in enumerate(timed):
        indices[(r["day"],r["race_number"])].append(i)
    rng=random.Random(seed)
    original=[r["relative_seconds"] for r in timed]
    ref=[]
    for _ in range(permutations):
        copied=list(original)
        for positions in indices.values():
            vals=[copied[i] for i in positions]
            rng.shuffle(vals)
            for i,x in zip(positions,vals):
                copied[i]=x
        shuffled=[{**r,"relative_seconds":copied[i]} for i,r in enumerate(timed)]
        s=summarize_pairs(pair_records(shuffled,strict_class=strict_class),"switched")
        if s["status"]!="EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY":
            raise ValueError("HOLD_REFERENCE_SUPPORT_CHANGED_WITH_FIXED_SOURCE_LABELS")
        ref.append(s["equal_horse_stratum_mean_pair_product_seconds_squared"])
    ref.sort()
    obs=primary["equal_horse_stratum_mean_pair_product_seconds_squared"]
    return {
        "status":"EXPLORATORY_WITHIN_ORIGINAL_RACE_OUTCOME_SHUFFLE_REFERENCE_ONLY",
        "reference_iterations":permutations,
        "fixed_random_seed":seed,
        "reference_mean_seconds_squared":mean(ref),
        "reference_quantiles_05_50_95_seconds_squared":[
            ref[int((len(ref)-1)*p)] for p in (.05,.50,.95)
        ],
        "algorithmic_upper_tail_reference_fraction_NOT_p_value":
            (1+sum(v>=obs for v in ref))/(permutations+1),
        "not_randomized_jockey_assignment":True,
        "not_causal_or_preregistered_significance":True,
    }


def analyze(rows:list[dict],*,min_race_telemetry:int=4,
            permutations:int=DEFAULT_REFERENCE_SHUFFLES)->dict:
    if min_race_telemetry not in (4,6):
        raise ValueError("HOLD_FIELD_COVERAGE_NOT_IN_SENSITIVITY_DESIGN")
    timed,q=source_timed_panel(rows,min_gps=min_race_telemetry)
    if not timed:
        return {
            "status":"HOLD_NO_SOURCE_TIMED_FIELDS",
            "source_coverage":q,
            "no_original_animal_or_rider_values_exported":True,
        }
    broad=_one_pair_set(timed,strict_class=False)
    strict=_one_pair_set(timed,strict_class=True)
    reference=rider_label_shuffled_time_reference(
        timed,strict_class=False,permutations=permutations
    )
    # Extra strict original Class is secondary; avoid fitting another
    # null reference without a specific validated decision need.
    return {
        "status":"POST_HOC_ORIGINAL_RQ_RIDER_SWITCH_PERSISTENCE_FEASIBILITY_NOT_H1_H2",
        "source_publisher":"Racing Queensland",
        "source_cohort":"previously locked Cannon Park 2026 12-meeting cohort",
        "positive_GPS_horses_per_race_minimum":min_race_telemetry,
        "source_coverage":q,
        "same_official_race_distance_and_exact_first_GPS_marker":broad,
        "also_same_original_race_Class":strict,
        "changed_declared_jockey_within_race_outcome_shuffle_reference":reference,
        "minimum_distinct_HORSES_IDs_for_numeric_pair_stat":MIN_IDS,
        "minimum_horse_strata_for_numeric_pair_stat":MIN_STRATA,
        "minimum_distinct_source_meeting_dates":MIN_SOURCE_DATES,
        "minimum_different_source_meeting_date_pairs":MIN_MEETING_DATE_PAIR_TYPES,
        "not_an_absolute_speed_or_certified_finishing_time":True,
        "actual_postrace_rider_or_finisher_status_NOT_verified":True,
        "trainer_unchanged_does_not_identify_intrinsic_horse_behavior":True,
        "horse_going_H1_ground_random_slope_fitted":False,
        "horse_competitor_H2_interaction_fitted":False,
        "causal_jockey_or_evolutionary_or_heritability_claim_supported":False,
        "raw_animal_name_id_licence_or_interval_not_published":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    from ecology_rq_2026_calendar_overlap import (
        COHORT, LOCKED_RACE_NUMBERS, validate_cohort, safe_failure
    )
    from ecology_rq_multigoing_h1_preflight import audit_one_day
    from ecology_rq_single_race_id_probe import request_xml
    from ecology_rq_thoroughbred_sectional_audit import fetch_official

    validate_cohort()
    data=[]
    manifest={}
    for day,(ground,source) in COHORT.items():
        try:
            audit,rows=audit_one_day(
                day,soap=request_xml,gps=fetch_official,
                locked_config={
                    "source":source,
                    "ground_expected":ground,
                    "races":LOCKED_RACE_NUMBERS,
                },
                race_selection=LOCKED_RACE_NUMBERS
            )
            manifest[day]={
                "status":"SOURCE_ORIGINAL_ID_GPS_AND_DECLARED_RIDER_AUDITED",
                "first_GPS_matched_original_source_rows":len(rows),
                "original_source_SHA256":audit["source_hashes"],
            }
            data.extend(rows)
        except (ValueError,OSError,TimeoutError) as exc:
            manifest[day]=safe_failure(exc)

    result=analyze(data) if data else {
        "status":"HOLD_NO_ORIGINAL_FIRST_GPS_SOURCE_COHORT",
        "raw_animal_name_id_licence_or_interval_not_published":True,
    }
    failures=[d for d,v in manifest.items()
              if v["status"]!="SOURCE_ORIGINAL_ID_GPS_AND_DECLARED_RIDER_AUDITED"]
    # Never interpret missing source dates as zero animal variation.
    if failures:
        result={
            "status":"HOLD_SOURCE_DATES_UNAVAILABLE_FOR_RIDER_SWITCH_INFERENCE",
            "source_dates_HOLD":failures,
            "source_dates_successful":len(COHORT)-len(failures),
            "effect_not_reported_from_incomplete_source_cohort":True,
            "raw_animal_name_id_licence_or_interval_not_published":True,
        }
    result["source_manifest_original_SHA256_no_individuals"]=manifest
    result["all_twelve_original_source_dates_requested"]=list(COHORT)
    result["no_original_horse_jockey_trainer_names_IDs_or_times_emitted"]=True
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "date_sources_successful":len(COHORT)-len(failures),
        "date_sources_HOLD":len(failures),
        "primary_switched_jockey":{
            "status":result.get("same_official_race_distance_and_exact_first_GPS_marker",{})
            .get("status_by_rider_pair_condition",{}).get("switched",{})
            .get("status","HOLD"),
            "ID_count":result.get("same_official_race_distance_and_exact_first_GPS_marker",{})
            .get("status_by_rider_pair_condition",{}).get("switched",{})
            .get("distinct_official_HORSES_IDs",0),
        },
        "all_individual_names_and_times_withheld":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
