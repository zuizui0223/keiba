#!/usr/bin/env python3
"""Two-site original Thoroughbred source-ID overlap: Cannon Park vs Eagle Farm.

This checks an ACTUAL animal-ID comparability requirement before claiming
that a second racing venue "replicates" individual repeatability or
environmental sensitivity: ARE THE SAME ORIGINAL HORSES IDs OBSERVED
ON BOTH TRACKS? If so, do any have early GPS times at the SAME
FIRST MARKER and OFFICIAL scheduled distance/class?

Both lists of original source dates and race numbers are versioned and
already fixed: Cannon Park 12 dated meetings/R1-8, Eagle Farm 12 dated
meetings/R1-6 in 2026. 24 source dates maximum; original RQ SOAP/GPS
files only, no other racing sources, no arbitrary downloads.

Only AGGREGATE counts, coarse classes and original file SHA256s are
returned. Individual HORSES IDs, names, riding history and GPS times
are processed in memory and never committed/output.

NO inferential test, horse/H1 environmental reaction slopes, H2
competitor causal effect, genetic personality, race results, or
independent population-wide replication is claimed. Positive GPS
is measured telemetry, not final verified starter/finisher status.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from ecology_rq_2026_calendar_overlap import (
    COHORT as CANNON_COHORT,
    LOCKED_RACE_NUMBERS as CANNON_RACES,
    safe_failure,
    validate_cohort as validate_cannon,
)
from ecology_rq_eagle_farm_external_icc import (
    DATES as EAGLE_DATES,
    RACE_NUMBERS as EAGLE_RACES,
    collect as collect_eagle,
    validate_source_lock as validate_eagle,
)
from ecology_rq_multigoing_h1_preflight import audit_one_day
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


def collect_cannon(*, soap=request_xml, gps=fetch_official,
                   on_source_error="record_HOLD") -> tuple[list[dict],dict]:
    validate_cannon()
    if on_source_error not in ("record_HOLD","raise"):
        raise ValueError("HOLD_CROSS_VENUE_SOURCE_ERROR_MODE")
    rows=[]
    manifest={}
    for day,(ground,source) in CANNON_COHORT.items():
        config={"source":source,"ground_expected":ground,"races":CANNON_RACES}
        try:
            summary,eligible=audit_one_day(
                day,soap=soap,gps=gps,venue="Ladbrokes Cannon Park",
                locked_config=config,race_selection=CANNON_RACES,
            )
            manifest[day]={
                "status":"ORIGINAL_CANNON_HORSES_GPS_LINKS_AUDITED",
                "race_numbers_with_official_IDs":len(summary["official_race_numbers_available"]),
                "missing_original_official_race_numbers":summary["missing_official_race_numbers"],
                "linked_positive_first_GPS_rows":len(eligible),
                "source_sha256":summary["source_hashes"],
                "original_race_TrackRating_used":True,
            }
            rows.extend(eligible)
        except (ValueError,OSError,TimeoutError) as exc:
            if on_source_error=="raise":
                raise
            manifest[day]=safe_failure(exc)
    return rows,manifest


def _valid_paired_identity(row):
    required=("horse_id","horse_name","day","distance","class",
              "first_marker_m","first_section_sec","ground")
    if any(k not in row for k in required):
        raise ValueError("HOLD_CROSS_VENUE_REQUIRED_SOURCE_COLUMNS_MISSING")
    if not row["horse_id"] or not row["horse_name"]:
        raise ValueError("HOLD_CROSS_VENUE_ANIMAL_IDENTITY_MISSING")
    if float(row["first_marker_m"])<=0 or float(row["first_section_sec"])<=0:
        raise ValueError("HOLD_CROSS_VENUE_GPS_UNOBSERVED_NOT_ZERO")


def support(cannon:list[dict],eagle:list[dict])->dict:
    """Return descriptive OVERLAP SUPPORT ONLY; no per-animal values."""
    raw={"Cannon Park":cannon,"Eagle Farm":eagle}
    both=defaultdict(list)
    rowkeys=set()
    site_sets={}
    for site,rows in raw.items():
        for row in rows:
            _valid_paired_identity(row)
            k=(site,row["day"],row["horse_id"])
            if k in rowkeys:
                raise ValueError("HOLD_CROSS_VENUE_DUPLICATE_HORSES_ID_PER_DAY")
            rowkeys.add(k)
            both[row["horse_id"]].append((site,row))
        site_sets[site]=set(r["horse_id"] for r in rows)
    changed_names={hid for hid,record in both.items()
                   if len({r["horse_name"] for _,r in record})>1}
    same_day_both={hid for hid,record in both.items()
                   if any(
                       (d in {r["day"] for site,r in record if site=="Cannon Park"})
                       for d in {r["day"] for site,r in record if site=="Eagle Farm"}
                   )}
    blocked=changed_names | same_day_both
    eligible_cannon={r["horse_id"] for r in cannon
                     if r["horse_id"] not in blocked}
    eligible_eagle={r["horse_id"] for r in eagle
                    if r["horse_id"] not in blocked}
    shared=eligible_cannon & eligible_eagle
    site_rows={
        name:[r for r in rows if r["horse_id"] not in blocked]
        for name,rows in raw.items()
    }
    c_by_id=defaultdict(list)
    e_by_id=defaultdict(list)
    for row in site_rows["Cannon Park"]: c_by_id[row["horse_id"]].append(row)
    for row in site_rows["Eagle Farm"]: e_by_id[row["horse_id"]].append(row)
    same_marker=set()
    same_marker_distance=set()
    same_marker_distance_class=set()
    multi_venue_2each=set()
    for hid in shared:
        ca=c_by_id[hid]; ea=e_by_id[hid]
        mkc={round(float(r["first_marker_m"]),4) for r in ca}
        mke={round(float(r["first_marker_m"]),4) for r in ea}
        if mkc & mke: same_marker.add(hid)
        dc={(round(float(r["first_marker_m"]),4),str(r["distance"])) for r in ca}
        de={(round(float(r["first_marker_m"]),4),str(r["distance"])) for r in ea}
        if dc & de: same_marker_distance.add(hid)
        cc={(round(float(r["first_marker_m"]),4),str(r["distance"]),str(r["class"]))
            for r in ca}
        ce={(round(float(r["first_marker_m"]),4),str(r["distance"]),str(r["class"]))
            for r in ea}
        if cc & ce: same_marker_distance_class.add(hid)
        if len({r["day"] for r in ca})>=2 and len({r["day"] for r in ea})>=2:
            multi_venue_2each.add(hid)
    return {
        "status":"CROSS_VENUE_SOURCE_HORSES_ID_OVERLAP_SCREEN_NOT_ECOLOGY_EFFECT",
        "source_positive_GPS_rows_by_venue":{s:len(x) for s,x in raw.items()},
        "source_distinct_HORSES_IDs_by_venue":{
            s:len(ids) for s,ids in site_sets.items()
        },
        "combined_distinct_source_HORSES_IDs":len(both),
        "numeric_original_HORSES_IDs_in_BOTH_venues_before_conflict_blocks":
            len(site_sets["Cannon Park"] & site_sets["Eagle Farm"]),
        "original_HORSES_IDs_with_changed_name_across_venues_or_dates_BLOCKED":
            len(changed_names),
        "original_HORSES_IDs_appearing_at_both_venues_on_same_date_BLOCKED":
            len(same_day_both),
        "distinct_same_name_safe_original_HORSES_IDs_observed_at_both_venues":
            len(shared),
        "BOTH_venues_with_2plus_independent_dates_in_each":len(multi_venue_2each),
        "BOTH_venues_with_1plus_identical_first_marker":len(same_marker),
        "BOTH_venues_with_1plus_identical_marker_AND_official_distance":
            len(same_marker_distance),
        "BOTH_venues_with_1plus_identical_marker_distance_AND_official_class":
            len(same_marker_distance_class),
        "candidate_records_after_identity_conflict_block_by_venue":{
            s:len(x) for s,x in site_rows.items()
        },
        "shared_IDs_truly_confirmed_starters_or_finishers":False,
        "shared_GPS_first_interval_has_identical_distance_outcome_without_matching_marker":False,
        "no_cross_site_behavioral_coefficient_fitted":True,
        "no_names_numeric_HORSES_IDs_or_original_GPS_rows_exported":True,
        "scientific_decision": (
            "AT_LEAST_ONE_MATCHED_SOURCE_ANIMAL_MARKER_DISTANCE_CLASS_NOT_AN_IDENTIFIED_CAUSAL_SITE_EFFECT"
            if same_marker_distance_class else
            "HOLD_NO_SAME_HORSE_IDENTICAL_MARKER_DISTANCE_CLASS_ACROSS_VENUES"
        ),
        "no_confirmatory_p_value_or_genetic_or_adaptive_claim":True,
    }


def compare(*,soap=request_xml,gps=fetch_official,
            on_source_error="record_HOLD")->dict:
    validate_eagle()
    validate_cannon()
    eagle_rows,eagle_manifest=collect_eagle(
        soap=soap,gps=gps,on_source_error=on_source_error
    )
    cannon_rows,cannon_manifest=collect_cannon(
        soap=soap,gps=gps,on_source_error=on_source_error
    )
    count=support(cannon_rows,eagle_rows)
    dates_eagle=[d for d,v in eagle_manifest.items() if
                 v["status"]=="SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED"]
    dates_cannon=[d for d,v in cannon_manifest.items() if
                  v["status"]=="ORIGINAL_CANNON_HORSES_GPS_LINKS_AUDITED"]
    return {
        "status":"ORIGINAL_HORSES_ID_CROSS_SITE_OBSERVATION_COMPARABILITY_NOT_H1_H2",
        "venue_names":["Ladbrokes Cannon Park","Eagle Farm"],
        "source_publisher":"Racing Queensland",
        "data_lock":{
            "cannon_original_design":"docs/ecology-rq-2026-calendar-cohort-lock.md",
            "eagle_original_design":"docs/ecology-rq-eagle-farm-2026-independent-track-lock.md",
            "selected_Cannon_original_meetings":len(CANNON_COHORT),
            "selected_Eagle_original_meetings":len(EAGLE_DATES),
            "Cannon_source_dates_verified":len(dates_cannon),
            "Eagle_source_dates_verified":len(dates_eagle),
            "Cannon_source_dates_HOLD":sorted(set(CANNON_COHORT)-set(dates_cannon)),
            "Eagle_source_dates_HOLD":sorted(set(EAGLE_DATES)-set(dates_eagle)),
            "requested_official_race_numbers_Cannon":list(CANNON_RACES),
            "requested_official_race_numbers_Eagle":list(EAGLE_RACES),
        },
        "source_manifest_sha256_only":{
            "Cannon Park":cannon_manifest,"Eagle Farm":eagle_manifest
        },
        "same_HORSES_ID_animal_source_overlap":count,
        "no_original_individual_identity_or_GPS_outcome_exported":True,
        "H1_ground_response_supported":False,
        "H2_competitor_effect_supported":False,
        "independent_stable_individual_effect_replication_without_matching_course_measurement":False,
        "notes":[
            "Original numerical HORSES ID reappearing in different venues is not proof of randomized venue choice or a biological plasticity effect.",
            "Different original first-section distance markers render raw-seconds ICC models non-equivalent even if each venue separately has nonzero horse ID variance.",
            "A horse ID observed in both venues with no matching marker/race distance/class is NOT an identifiable paired effect.",
            "First positive GPS source observation is not final official starter or finisher status; 0 GPS is not zero performance.",
            "Original source may have selective nominations, missing telemetry, class/rider/trainer differences and measurement error.",
            "Only source-level ID overlap and positivity are evaluated; no propensity model, causal test, ICC confidence interval or evolutionary claim.",
        ],
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--strict-source-errors",action="store_true")
    args=p.parse_args()
    result=compare(on_source_error=(
        "raise" if args.strict_source_errors else "record_HOLD"
    ))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8"
    )
    print(json.dumps({
        "status":result["status"],
        "source_date_coverage":result["data_lock"],
        "overlap":result["same_HORSES_ID_animal_source_overlap"],
        "H1_H2_HOLD":not result["H1_ground_response_supported"]
                     and not result["H2_competitor_effect_supported"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
