#!/usr/bin/env python3
"""Doomben third original Thoroughbred venue, frozen 19-date source cohort.

Purpose: find NUMERICALLY SUPPORTED EXACT SAME FIRST GPS MARKER
individual race-adjusted Gaussian conditional ICCs at 150m
(Cannon Park previously) or 200m (Eagle Farm previously).

This is an observational source/method transfer study, not:
- independent GPS vendor, identical racing population/conditions
- individual horses seen at two venues without verified same original Id
- a causal track-distance effect, age/trainer adjustment, H1/H2
- true final starter roster, finish outcome, heritability or wagering.

Original HORSES names, numeric IDs, trainer/rider IDs and raw
individual times NEVER leave memory or enter returned JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from ecology_rq_multigoing_h1_preflight import audit_one_day
from ecology_rq_2026_calendar_overlap import safe_failure
from ecology_rq_eagle_farm_external_icc import identity_overlap
from ecology_rq_race_fixed_icc import race_fixed_reml, delete_date_sensitivity
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official, APPROVED


VENUE = "Doomben"
# Calendar chosen from original RQ sectionals index BEFORE first
# original Doomben HORSES-Id/GPS cohort was inspected:
# earliest/latest 2026 CSV date by month (Oct through October 5).
DATES = (
    "2026-01-14", "2026-01-29",
    "2026-02-07", "2026-02-25",
    "2026-03-04", "2026-03-28",
    "2026-04-01", "2026-04-22",
    "2026-05-16", "2026-05-27",
    "2026-06-03", "2026-06-24",
    "2026-07-11", "2026-07-22",
    "2026-08-01", "2026-08-26",
    "2026-09-12", "2026-09-30",
    "2026-10-05",
)
RACE_NUMBERS = (1,2,3,4,5,6)
FILES = {day: day.replace("-","")+"-doomben" for day in DATES}
NUMERIC_ICC_STATUSES = {
    "EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY",
    "EXPLORATORY_RACE_ADJUSTED_ICC_AT_ZERO_BOUNDARY",
}
# Original independent model estimates were observed before this study,
# with very different animal cohorts and original GPS first-marker mix.
EXISTING_REFERENCES = {
    "Cannon Park": {
        "first_marker_m":150.,
        "original_marker_model_observational_ICC":0.547296,
        "original_marker_model_source_rows":209,
        "original_marker_model_races":29,
    },
    "Eagle Farm": {
        "first_marker_m":200.,
        "original_marker_model_observational_ICC":0.528346,
        "original_marker_model_source_rows":293,
        "original_marker_model_races":None,
    },
}


def validate_lock() -> None:
    if (len(DATES)!=19 or DATES!=tuple(sorted(DATES))
            or len(set(DATES))!=19
            or RACE_NUMBERS!=tuple(range(1,7))):
        raise ValueError("HOLD_DOOMBEN_ORIGINAL_CALENDAR_LOCK_CHANGED")
    for day,source in FILES.items():
        filename=day.replace("-","")+"_Doomben_T.csv"
        if source not in APPROVED or APPROVED[source]!=filename:
            raise ValueError("HOLD_DOOMBEN_EXACT_ORIGINAL_GPS_SOURCE_NOT_ALLOWLISTED")


def collect(*, soap=request_xml, gps=fetch_official,
            source_errors="record_HOLD") -> tuple[list[dict],dict]:
    validate_lock()
    if source_errors not in ("record_HOLD","raise"):
        raise ValueError("HOLD_DOOMBEN_UNAPPROVED_SOURCE_ERROR_MODE")
    manifest={}
    rows=[]
    for day in DATES:
        original_horse_roster_shas={}
        def verified_hashing_soap(operation,params):
            xml,url,digest=soap(operation,params)
            if operation=="GetHorsesForRace":
                race_identifier=str(params["raceId"])
                if race_identifier in original_horse_roster_shas:
                    raise ValueError("HOLD_DUPLICATE_HORSES_API_ROSTER_REQUEST")
                original_horse_roster_shas[race_identifier]=digest
            return xml,url,digest
        cfg={
            "source":FILES[day],
            "ground_expected":"SOURCE_RACE_LEVEL",
            "races":RACE_NUMBERS,
        }
        try:
            audit,candidates=audit_one_day(
                day,
                soap=verified_hashing_soap,gps=gps,
                locked_config=cfg,
                race_selection=RACE_NUMBERS,
                venue=VENUE,
            )
            if audit["venue"]!=VENUE or not audit[
                    "source_race_level_TrackRating_always_used"]:
                raise ValueError("HOLD_OFFICIAL_RACE_VENUE_RATING_NOT_VERIFIED")
            # Only anonymous field-counts and cryptographic source
            # hashes, NEVER the original HORSES identities, are emitted.
            manifest[day]={
                "status":"SOURCE_DOOMBEN_OFFICIAL_IDS_AND_GPS_AUDITED",
                "original_races_requested":list(RACE_NUMBERS),
                "original_numeric_race_IDs_found":len(audit[
                    "official_race_numbers_available"]),
                "missing_official_race_numbers":audit[
                    "missing_official_race_numbers"],
                "original_race_ground_categories":audit[
                    "actual_official_ground_labels"],
                "original_positive_first_GPS_HORSES_ID_rows":len(candidates),
                "original_HORSES_ID_in_multiple_races_same_date":
                    audit["official_ids_listed_more_than_once_on_date"],
                "same_day_name_repeated_source_rows_blocked":
                    audit["candidate_rows_with_same_day_duplicate_gps_name"],
                "original_source_sha256_only":audit["source_hashes"],
                "official_horse_rosters_hashed":len(original_horse_roster_shas),
                "official_HORSES_roster_XML_sha256_combined_without_IDs":hashlib.sha256(
                    "".join(
                        f"{rid}:{sha}\n" for rid,sha in
                        sorted(original_horse_roster_shas.items())
                    ).encode("ascii")
                ).hexdigest(),
                "roster_snapshot_source_hashes_are_needed_to_identify_edition_changes":True,
                "no_individual_source_data_exported":True,
            }
            rows.extend(candidates)
        except (ValueError,TimeoutError,OSError) as exc:
            if source_errors=="raise":
                raise
            manifest[day]=safe_failure(exc)
    return rows,manifest


def marker_support(rows:list[dict],marker:float)->dict:
    """Bounded anonymous original HORSES-ID recurrence positivity screen.

    A large number of original GPS source rows is not equivalent to
    repeated measurements of individual biological subjects.
    """
    sample=[r for r in rows if abs(float(r["first_marker_m"])-marker)<1e-6]
    by_id={}
    races=set()
    for r in sample:
        by_id.setdefault(r["horse_id"],set()).add(r["day"])
        races.add((r["day"],r["race_number"]))
    repeated=[n for n in by_id.values() if len(n)>=2]
    return {
        "first_section_marker_m":marker,
        "original_positive_first_GPS_source_rows":len(sample),
        "source_races":len(races),
        "source_distinct_dates":len({r["day"] for r in sample}),
        "distinct_internal_HORSES_IDs":len(by_id),
        "HORSES_IDs_seen_at_least_twice_on_distinct_dates":len(repeated),
        "source_repetition_threshold_of_existing_Gaussian_ICC":20,
        "source_repeated_id_threshold_passed":len(repeated)>=20,
        "no_original_identity_or_individual_time_exported":True,
    }


def _marker_model(rows:list[dict],marker:float)->dict:
    sample=[r for r in rows if abs(float(r["first_marker_m"])-marker)<1e-6]
    # For no source rows return HOLD, not a fabricated 0 ICC.
    if not sample:
        return {
            "status":"HOLD_NO_ORIGINAL_POSITIVE_FIRST_GPS_SOURCE_AT_MARKER",
            "source_rows":0,"original_races":0,
            "not_a_zero_horse_variance":True,
        }
    fit=race_fixed_reml(sample,4)
    return fit


def match_cannon_eagle(models:dict)->dict:
    matches={}
    for track,ref in EXISTING_REFERENCES.items():
        marker=ref["first_marker_m"]
        model=models[str(marker)]
        match=model["status"] in NUMERIC_ICC_STATUSES
        matches[track]={
            "first_GPS_measurement_marker_m":marker,
            "reference_observational_ICC_point":ref[
                "original_marker_model_observational_ICC"],
            "reference_source_rows":ref[
                "original_marker_model_source_rows"],
            "Doomben_original_source_rows":model.get("source_rows",0),
            "Doomben_estimator_status":model["status"],
            "Doomben_numerical_ICC_support_at_identical_marker":match,
            "Doomben_observational_ICC_point_at_marker":model.get(
                "conditional_observational_ICC_point_estimate"),
            "matched_measurement_marker_not_same_animals_or_identical_race_context":True,
        }
    n=sum(x["Doomben_numerical_ICC_support_at_identical_marker"]
          for x in matches.values())
    return {
        "status":(
            "EXPLORATORY_THIRD_VENUE_EXACT_MARKER_ICC_SUPPORT"
            if n else "HOLD_NO_SHARED_SOURCE_MARKER_WITH_NUMERIC_HORSE_ICC"
        ),
        "reference_venue_marker_comparisons":matches,
        "matched_marker_numeric_comparisons_supported":n,
        "same_original_HORSES_IDs_at_both_venues_not_verified_in_this_program":True,
        "this_is_not_a_direct_paired_trait_replication_or_racecourse_effect_test":True,
    }


def evaluate(*,soap=request_xml,gps=fetch_official,
             source_errors="record_HOLD")->dict:
    rows,manifest=collect(
        soap=soap,gps=gps,source_errors=source_errors
    )
    eligible,ident=identity_overlap(rows)
    successes=[
        day for day in DATES
        if manifest[day]["status"]=="SOURCE_DOOMBEN_OFFICIAL_IDS_AND_GPS_AUDITED"
    ]
    # NOT recomputing 99 shuffled complete-source pooled models here,
    # because the scientific target is original identical first marker
    # support, not maximizing another pooled correlation.
    selected_models={
        "150.0":_marker_model(eligible,150.),
        "200.0":_marker_model(eligible,200.),
    }
    source_marker_repeat_support={
        "150.0":marker_support(eligible,150.),
        "200.0":marker_support(eligible,200.),
    }
    if len(successes)==len(DATES):
        status="DOOMBEN_THIRD_VENUE_ORIGINAL_SOURCE_MARKER_PILOT_NO_H1_H2"
    else:
        status="HOLD_INCOMPLETE_LOCKED_DOOMBEN_SOURCE_DATES"
    return {
        "status":status,
        "publisher":"Racing Queensland",
        "source_lock":{
            "source_calendar_document":
                "docs/ecology-rq-doomben-2026-third-venue-calendar-lock.md",
            "dates_selected_before_original_Doomben_HORSES_ID_or_ICC":
                True,
            "locked_meeting_dates":list(DATES),
            "dates_successfully_original_source_audited":successes,
            "dates_source_HOLD":sorted(set(DATES)-set(successes)),
            "original_race_numbers_per_meeting":list(RACE_NUMBERS),
            "source_selection_based_on_first_and_last_CSV_per_month":
                True,
            "one_prior_source_schema_inventory_known_before_lock":
                True,
            "not_prospective_scientific_preregistration":True,
        },
        "source_manifest":manifest,
        "original_numeric_HORSES_ID_source_support":ident,
        "first_marker_150_and_200_original_race_FE_ICC":selected_models,
        "first_marker_150_and_200_repeat_ID_identifiability":
            source_marker_repeat_support,
        "Cannon_Eagle_reference_marker_compatibility":
            match_cannon_eagle(selected_models),
        "first_GPS_time_is_early_section_NOT_official_finish_time":True,
        "actual_starter_and_welfare_DNF_status_unverified":True,
        "H1_ground_reaction_norm_variance_estimated":False,
        "H2_social_context_response_estimated":False,
        "migrating_ID_cross_venue_matched_original_results_estimated":False,
        "raw_original_horse_names_IDs_or_individual_interval_exported":False,
        "no_causal_track_or_hereditary_or_wager_claim":True,
    }


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--strict-source-errors",action="store_true")
    args=cli.parse_args()
    obj=evaluate(source_errors=(
        "raise" if args.strict_source_errors else "record_HOLD"
    ))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":obj["status"],
        "successful_original_source_days":len(
            obj["source_lock"]["dates_successfully_original_source_audited"]),
        "source_HOLD_dates":obj["source_lock"]["dates_source_HOLD"],
        "source_HOLD_reasons_by_date":{
            day:{
                "status":obj["source_manifest"][day]["status"],
                "error_code":obj["source_manifest"][day].get("error_code"),
                "error_type":obj["source_manifest"][day].get("error_type"),
            } for day in obj["source_lock"]["dates_source_HOLD"]
        },
        "source_support":obj["original_numeric_HORSES_ID_source_support"],
        "marker_repeat_ID_support":obj[
            "first_marker_150_and_200_repeat_ID_identifiability"],
        "marker_compatibility":obj["Cannon_Eagle_reference_marker_compatibility"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
