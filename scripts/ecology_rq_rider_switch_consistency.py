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
import hashlib
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
    by_date=defaultdict(lambda:{"GPS_records":0,"with_numeric_Jockey_ID":0})
    by_source_going=defaultdict(lambda:{"GPS_records":0,"with_numeric_Jockey_ID":0})
    for r in timed:
        date_counter=by_date[r["day"]]
        original=by_key[(r["day"],r["race_number"],r["horse_id"])]
        going=str(original.get("ground") or "UNKNOWN")
        ground_counter=by_source_going[going]
        for counter in (date_counter,ground_counter):
            counter["GPS_records"]+=1
            counter["with_numeric_Jockey_ID"]+=int(r["jockey_id"] is not None)
    return timed,{
        "numeric_Jockey_ID_coverage_by_original_meeting_date":{
            day:{
                **counts,
                "observed_source_coverage_fraction":(
                    counts["with_numeric_Jockey_ID"]/counts["GPS_records"]
                    if counts["GPS_records"] else None
                ),
            } for day,counts in sorted(by_date.items())
        },
        "numeric_Jockey_ID_coverage_by_official_source_going":{
            going:{
                **counts,
                "observed_source_coverage_fraction":(
                    counts["with_numeric_Jockey_ID"]/counts["GPS_records"]
                    if counts["GPS_records"] else None
                ),
            } for going,counts in sorted(by_source_going.items())
        },
        "coverage_is_conditional_on_positive_GPS_not_all_actual_starters":True,
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


def rider_switch_influence_audit(timed:list[dict])->dict:
    """Post-hoc original date and animal deletion, with original peers fixed.

    This measures influence on the SAME source-defined, relative first-GPS
    outcome, not robustness to changes in the definition of competitor peers.
    All identifiers stay in local memory.  Never output per-animal results.
    """
    source_pairs=pair_records(timed,strict_class=False)
    observed=summarize_pairs(source_pairs,"switched")
    if observed["status"]!="EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY":
        return {
            "status":"HOLD_PRIMARY_SWITCHED_RIDER_PAIR_SUPPORT_INSUFFICIENT",
            "primary_support_counts_only":observed,
            "no_original_HORSES_or_rider_identifiers_exported":True,
            "not_a_confidence_interval_or_independent_cohort":True,
        }

    original=observed["equal_horse_stratum_mean_pair_product_seconds_squared"]
    dates=sorted({r["day"] for r in timed})
    dates_with_pairs={day for p in source_pairs if p["switched"] for day in p["days"]}
    source_date_refits={}
    date_values=[]
    date_hold=0
    for dropped in dates:
        remaining=[p for p in source_pairs if dropped not in p["days"]]
        stat=summarize_pairs(remaining,"switched")
        row={
            "status":stat["status"],
            "original_HORSES_IDs":stat["distinct_official_HORSES_IDs"],
            "original_horse_by_marker_distance_strata":
                stat["horse_by_matching_distance_marker_class_strata"],
            "remaining_cross_date_source_pairs":
                stat["within_horse_cross_date_pairs"],
            "removed_meeting_had_an_original_changed_rider_pair":
                dropped in dates_with_pairs,
        }
        if stat["status"]=="EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY":
            point=stat["equal_horse_stratum_mean_pair_product_seconds_squared"]
            row["mean_pair_product_seconds_squared"]=point
            date_values.append(point)
        else:
            date_hold+=1
        source_date_refits[dropped]=row

    contributors={p["horse_id"] for p in source_pairs if p["switched"]}
    id_values=[]
    id_hold=0
    for removed in contributors:
        # IMPORTANT: filter only this horse's *pair* records.  Recomputing
        # leave-one-horse-out GPS peer means would change every other
        # horse's outcome mechanically, confounding influence with redefinition.
        remaining=[p for p in source_pairs if p["horse_id"]!=removed]
        stat=summarize_pairs(remaining,"switched")
        if stat["status"]=="EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY":
            id_values.append(stat["equal_horse_stratum_mean_pair_product_seconds_squared"])
        else:
            id_hold+=1

    def counts(vals,holds,total):
        summary={
            "number_of_deletions_attempted":total,
            "numeric_refits_meeting_original_support_gate":len(vals),
            "refits_on_HOLD":holds,
            "positive_refits":sum(x>0 for x in vals),
            "zero_refits":sum(x==0 for x in vals),
            "negative_refits":sum(x<0 for x in vals),
            "status":(
                "EXPLORATORY_ALL_DELETIONS_IDENTIFIABLE_NOT_CONFIDENCE_INTERVAL"
                if len(vals)==total and holds==0
                else "HOLD_AT_LEAST_ONE_DELETION_INSUFFICIENT_SUPPORT"
            ),
            "not_a_confidence_interval_or_p_value":True,
        }
        if vals and len(vals)==total and holds==0:
            summary.update({
                "minimum_refitted_pair_product_seconds_squared":min(vals),
                "maximum_refitted_pair_product_seconds_squared":max(vals),
                "maximum_absolute_change_vs_original_pair_product_seconds_squared":
                    max(abs(x-original) for x in vals),
            })
        return summary

    date_result=counts(date_values,date_hold,len(dates))
    date_result["source_date_keyed_anonymous_support"]=source_date_refits
    date_result["deletions_without_any_original_changed_rider_pairs"]=sum(
        d not in dates_with_pairs for d in dates
    )
    id_result=counts(id_values,id_hold,len(contributors))
    id_result["only_aggregate_deletion_range_not_any_original_HORSES_ID"]=True
    return {
        "status":"POST_HOC_SOURCE_CONDITIONAL_INFLUENCE_DIAGNOSTIC_ONLY",
        "original_switch_rider_pair_product_seconds_squared":original,
        "date_deletion":date_result,
        "horse_ID_deletion_ANON_AGGREGATES_ONLY":id_result,
        "same_GPS_peer_reference_kept_fixed_after_horse_deletion":True,
        "not_actual_jockey_switch_or_intrinsic_personality_or_H1_H2":True,
        "not_an_independent_replication_or_confidence_interval":True,
        "no_original_HORSES_or_rider_identifiers_exported":True,
    }


def safe_original_source_error_category(exc:Exception)->dict:
    """Never save raw URLs, original race IDs, XML or exception messages."""
    from urllib.error import HTTPError
    code=int(exc.code) if isinstance(exc,HTTPError) and exc.code is not None else None
    if code is not None and not 100<=code<=599:
        code=None
    return {
        "source_error_http_status_if_available":code,
        "source_http_rate_limited_429":code==429,
        "source_http_upstream_5xx":bool(code is not None and 500<=code<600),
        "raw_error_url_and_source_response_NOT_recorded":True,
        "source_unavailable_is_not_zero_animal_response":True,
    }


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
        "post_hoc_leave_one_original_meeting_and_anonymous_animal_influence":
            rider_switch_influence_audit(timed),
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
        # Capture original GetHorsesForRace SOAP SHA256s independently
        # of previously hashed meeting, race and GPS source responses.
        # Do NOT emit horse IDs, names or individual XML.
        horse_roster_hashes={}
        def traced_soap(op,params):
            root,url,sha=request_xml(op,params)
            if op=="GetHorsesForRace":
                race_id=str(params["raceId"])
                if race_id in horse_roster_hashes:
                    raise ValueError("HOLD_DUPLICATE_ORIGINAL_HORSE_ROSTER_REQUEST")
                horse_roster_hashes[race_id]=sha
            return root,url,sha
        try:
            audit,rows=audit_one_day(
                day,soap=traced_soap,gps=fetch_official,
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
                "original_HORSES_roster_XML_sha256_aggregate":hashlib.sha256(
                    "".join(
                        f"{race}:{digest}\n"
                        for race,digest in sorted(horse_roster_hashes.items())
                    ).encode("ascii")
                ).hexdigest(),
                "official_original_HORSES_roster_races_hashed":
                    len(horse_roster_hashes),
            }
            data.extend(rows)
        except (ValueError,OSError,TimeoutError) as exc:
            manifest[day]={
                **safe_failure(exc),
                **safe_original_source_error_category(exc),
            }

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
    # Earlier official Cannon cohort count was 548 (run #38411913010).
    # Per-race HORSES roster fingerprints were NOT captured in that run,
    # so a new count cannot retroactively prove why original matches differ.
    prior_source_candidate_rows=548
    current_source_candidate_rows=sum(
        m.get("first_GPS_matched_original_source_rows",0)
        for m in manifest.values()
    )
    result["source_snapshot_candidate_count_audit"]= {
        "prior_locked_original_Cannon_candidate_rows":prior_source_candidate_rows,
        "now_original_Cannon_candidate_rows":(
            current_source_candidate_rows if not failures else None
        ),
        "source_candidate_count_difference_now_minus_previous":(
            current_source_candidate_rows-prior_source_candidate_rows
            if not failures else None
        ),
        "previous_runs_had_no_original_HORSES_roster_per_race_SHA256":True,
        "cause_of_different_matched_source_ID_GPS_candidate_count_unverified":True,
        "never_treat_source_join_changes_as_biological_response":True,
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
