#!/usr/bin/env python3
"""Doomben 2025 first-GPS marker extension + fixed 2026 cohort, source-only.

2025 dates were LOCKED by earliest/latest public original CSV per month
before original 2025 HORSES IDs / GPS rows / ICC outcomes were fetched.
Existing 19-date 2026 third-venue cohort remains unmodified.
All outputs are ANONYMOUS aggregates; no horse identifiers, names,
rider/trainer licences, raw timings or original XML are written.

This is a POST-HOC source feasibility / measurement compatibility study:
NOT an independent preregistered effect or an experiment, NOT H1
environment random slopes, H2 competitor social effects, heritability,
fitness, personality, track geometry causation or betting advice.

Strict ORIGINAL model gate for same 150m / 200m source first marker:
>=20 repeated numeric HORSES IDs across dates, 6 original source dates,
12 races, 80 positive timed source records, 4 timed horses per race.
A smaller or failed source cohort returns HOLD, never zero ICC.
"""
from __future__ import annotations

import argparse
from collections import Counter
from http.client import HTTPException
import hashlib
import json
from pathlib import Path

from ecology_rq_doomben_third_venue_icc import (
    DATES as PREVIOUS_2026_DATES,
    RACE_NUMBERS,
    VENUE,
    marker_support,
    match_cannon_eagle,
    NUMERIC_ICC_STATUSES,
)
from ecology_rq_eagle_farm_external_icc import identity_overlap
from ecology_rq_multigoing_h1_preflight import audit_one_day
from ecology_rq_2026_calendar_overlap import safe_failure
from ecology_rq_race_fixed_icc import race_fixed_reml
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import APPROVED, fetch_official


DATES_2025 = (
    "2025-01-22","2025-01-27",
    "2025-02-01","2025-02-26",
    "2025-03-19",
    "2025-04-01","2025-04-23",
    "2025-05-17","2025-05-28",
    "2025-06-04","2025-06-25",
    "2025-07-12","2025-07-30",
    "2025-08-06","2025-08-27",
    "2025-09-06","2025-09-17",
    "2025-10-04","2025-10-29",
    "2025-11-15","2025-11-29",
    "2025-12-06","2025-12-12",
)
LOCKED_DATES = DATES_2025 + PREVIOUS_2026_DATES
FIRST_MARKERS=(150.,200.)
MIN_GPS_PER_RACE=4
PREDECLARED_2025_SOURCE_DOCUMENT="docs/ecology-rq-doomben-2025-marker-calendar-lock.md"


def verify_lock() -> None:
    from ecology_rq_doomben_third_venue_icc import validate_lock as verify_2026
    verify_2026()
    if (len(DATES_2025)!=23 or DATES_2025!=tuple(sorted(DATES_2025))
            or len(set(DATES_2025))!=23
            or not all(d.startswith("2025-") for d in DATES_2025)
            or len(LOCKED_DATES)!=42
            or RACE_NUMBERS!=tuple(range(1,7))
            or PREVIOUS_2026_DATES!=tuple(sorted(PREVIOUS_2026_DATES))):
        raise ValueError("HOLD_DOOMBEN_2025_YEAR_SOURCE_LOCK_CHANGED")
    for day in DATES_2025:
        source=day.replace("-","")+"-doomben"
        expected=day.replace("-","")+"_Doomben_T.csv"
        if source not in APPROVED or APPROVED[source]!=expected:
            raise ValueError("HOLD_DOOMBEN_2025_SOURCE_CSV_NOT_EXACTLY_ALLOWLISTED")


def _digest_rosters(roots:dict[str,str])->str:
    """Anonymous date-specific source roster fingerprint, no race IDs output."""
    return hashlib.sha256("".join(
        f"{rid}:{digest}\n" for rid,digest in sorted(roots.items())
    ).encode("ascii")).hexdigest()


def collect(
    *,soap=request_xml,gps=fetch_official,
    on_error:str="record_HOLD",
)->tuple[list[dict],dict]:
    verify_lock()
    if on_error not in ("record_HOLD","raise"):
        raise ValueError("HOLD_UNAPPROVED_DOOMBEN_SOURCE_ERROR_MODE")
    manifest={}
    observations=[]
    for day in LOCKED_DATES:
        hashes={}
        def original_horse_roster_request(op,params):
            root,url,sha=soap(op,params)
            if op=="GetHorsesForRace":
                rid=str(params["raceId"])
                if rid in hashes:
                    raise ValueError("HOLD_DUPLICATE_ORIGINAL_ROSTER_RESPONSE")
                if not isinstance(sha,str) or len(sha)!=64:
                    raise ValueError("HOLD_ORIGINAL_HORSE_SOURCE_FINGERPRINT_UNVERIFIABLE")
                hashes[rid]=sha
            return root,url,sha
        try:
            source=day.replace("-","")+"-doomben"
            info,rows=audit_one_day(
                day,soap=original_horse_roster_request,gps=gps,
                venue=VENUE,
                locked_config={
                    "source":source,
                    "ground_expected":"SOURCE_RACE_LEVEL",
                    "races":RACE_NUMBERS,
                },
                race_selection=RACE_NUMBERS,
            )
            if (info["venue"]!=VENUE or
                    not info["source_race_level_TrackRating_always_used"]):
                raise ValueError("HOLD_ORIGINAL_VENUE_OR_GOING_NOT_VERIFIED")
            # No original HORSES ID, name or positive individual timing
            # leaves this method. Source hashes may be shared as digests.
            manifest[day]={
                "status":"OFFICIAL_2025_OR_2026_DOOMBEN_SOURCE_ID_GPS_AUDITED",
                "original_race_numbers_requested":list(RACE_NUMBERS),
                "numeric_race_IDs_returned":len(info["official_race_numbers_available"]),
                "unavailable_official_race_numbers":info["missing_race_numbers"] if "missing_race_numbers" in info else info["missing_official_race_numbers"],
                "original_positive_first_GPS_HORSES_ID_rows":len(rows),
                "original_first_party_meeting_race_GPS_source_SHA256":info["source_hashes"],
                "original_horse_roster_response_count":len(hashes),
                "original_horse_roster_combined_SHA256":_digest_rosters(hashes),
                "source_race_going_category_counts":info["actual_official_ground_labels"],
                "nonstarter_or_dnf_not_inferred_from_zero_GPS":True,
                "individual_HORSES_ID_and_GPS_measurements_withheld":True,
            }
            observations.extend(rows)
        except (ValueError,TimeoutError,OSError,HTTPException) as e:
            if on_error=="raise":
                raise
            # The upstream SOAP server sometimes terminates a chunked
            # HTTP body (http.client.IncompleteRead), even when its
            # original GPS CSV exists. NEVER parse partial XML, infer
            # zero racehorses, or treat this as biological absence.
            failure=safe_failure(e)
            if isinstance(e,HTTPException):
                failure["error_code"]="HOLD_INCOMPLETE_OR_TRUNCATED_OFFICIAL_HTTP_RESPONSE"
                failure["error_type"]=type(e).__name__
                failure["original_API_response_may_be_truncated"]=True
            manifest[day]=failure
    return observations,manifest


def summarize(
    raw_rows:list[dict],*, period_label:str
)->dict:
    clean,identity=identity_overlap(raw_rows)
    if not clean:
        return {
            "status":"HOLD_NO_ORIGINAL_ID_MATCHED_POSITIVE_GPS_IN_PERIOD",
            "period_label":period_label,
            "source_id_linkage":identity,
            "individual_original_data_exported":False,
        }
    supports={str(x):marker_support(clean,x) for x in FIRST_MARKERS}
    fits={str(x):race_fixed_reml(
        [r for r in clean if float(r["first_marker_m"])==x],
        min_race_telemetry=MIN_GPS_PER_RACE,
    ) for x in FIRST_MARKERS}
    comparisons=match_cannon_eagle(fits)
    return {
        "status":"DOOMBEN_2025_2026_SOURCE_MARKER_SUPPORT_NOT_H1_H2_EFFECT",
        "period_label":period_label,
        "source_id_linkage":identity,
        "source_marker_repeated_IDs":supports,
        "first_marker_race_FE_Gaussian_horse_ICC":fits,
        "prior_Cannon150_Eagle200_reference_gates":comparisons,
        "matched_original_first_segment_not_confirmed_cross_vendor":True,
        "not_a_test_of_same_HORSES_ID_across_venues":True,
        "original_GPS_record_coverage_is_not_complete_true_starters":True,
        "individual_original_data_exported":False,
    }


def evaluate(*,soap=request_xml,gps=fetch_official,
             on_error:str="record_HOLD")->dict:
    rows,manifest=collect(soap=soap,gps=gps,on_error=on_error)
    dates_2025=set(DATES_2025)
    source_2025=[r for r in rows if r["day"] in dates_2025]
    previous=[r for r in rows if r["day"] not in dates_2025]
    if len(source_2025)+len(previous)!=len(rows):
        raise ValueError("HOLD_UNEXPECTED_YEAR_IN_SOURCE_RESULTS")
    success=[
        d for d in LOCKED_DATES
        if manifest[d]["status"]=="OFFICIAL_2025_OR_2026_DOOMBEN_SOURCE_ID_GPS_AUDITED"
    ]
    failed=sorted(set(LOCKED_DATES)-set(success))
    a=summarize(source_2025,period_label="separately_selected_2025_source_year")
    b=summarize(rows,period_label="exploratory_combined_2025_2026_same_venue")
    return {
        "status":(
            "POSTHOC_DOOMBEN_2025_2026_FIRST_MARKER_SOURCE_FEASIBILITY_PARTIAL_HOLD"
            if failed else
            "POSTHOC_DOOMBEN_2025_2026_FIRST_MARKER_SOURCE_FEASIBILITY_COMPLETE"
        ),
        "source_publisher":"Racing Queensland official Open Data",
        "locked_source_design":{
            "documentation":PREDECLARED_2025_SOURCE_DOCUMENT,
            "new_2025_dates_fixed_BEFORE_any_new_2025_HORSES_ID_or_ICC_data":True,
            "selected_2025_original_CSV_dates":list(DATES_2025),
            "previous_2026_Doomben_dates_unchanged":list(PREVIOUS_2026_DATES),
            "source_dates_successfully_audited":success,
            "source_dates_on_HOLD":failed,
            "race_numbers_requested_per_original_date":list(RACE_NUMBERS),
            "original_2025_first_last_month_source_calendar_not_outcome_selected":True,
            "expansion_after_prior_positive_site_ICC_and_2026_marker_HOLD":True,
            "not_prospectively_preregistered_effect_test":True,
        },
        "per_original_date_source_fingerprints_and_anonymous_coverage":manifest,
        "2025_ONLY_first_marker_source_models":a,
        "2025_AND_2026_first_marker_source_models":b,
        "missing_original_dates_are_not_zero_effects":True,
        "no_source_HORSES_ID_names_rider_trainer_licences_or_raw_GPS_published":True,
        "no_official_true_starter_finisher_or_certified_full_race_time_verified":True,
        "H1_ground_individual_reaction_norm_estimated":False,
        "H2_opponent_competition_social_effect_estimated":False,
        "not_direct_Cannon_Eagle_Doomben_biological_replication":True,
        "limits":[
            "Earlier Cannon and Eagle first-section timing markers differ; even a numeric Doomben ICC at 150m or 200m is not an experiment on the same horse population.",
            "The full 2026 Doomben original cohort previously had a documented 2026-08-26 upstream API error; never infer zero animal timing there.",
            "Source horse nominees are not independently confirmed final starters; all-zero GPS is not DNF.",
            "The included 2025 meeting dates were fixed by calendar/source availability before this run, but the entire extension followed earlier source results.",
            "All numerical variance components depend on Gaussian iid residual and nonrandom source missingness assumptions.",
            "Race-fixed intercepts absorb race-common timing shifts but cannot separate stable horse/trainer or selection effects.",
            "Any same-marker across-venue comparison still needs original interval calibration and scientifically justified covariate adjustment.",
        ],
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--strict-source-errors",action="store_true")
    opts=p.parse_args()
    result=evaluate(on_error=("raise" if opts.strict_source_errors else "record_HOLD"))
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    compact={}
    for key in ("2025_ONLY_first_marker_source_models",
                "2025_AND_2026_first_marker_source_models"):
        summary=result[key]
        compact[key]={
            "status":summary["status"],
            "source_id_linkage":summary.get("source_id_linkage",{}),
            "repeat_IDs":{
                marker:row["HORSES_IDs_seen_at_least_twice_on_distinct_dates"]
                for marker,row in summary.get("source_marker_repeated_IDs",{}).items()
            },
            "first_marker_ICC":{
                marker:{
                    "status":row["status"],
                    "source_rows":row.get("source_rows",0),
                    "ICC_point":row.get("conditional_observational_ICC_point_estimate"),
                }
                for marker,row in summary.get("first_marker_race_FE_Gaussian_horse_ICC",{}).items()
            },
        }
    print(json.dumps({
        "status":result["status"],
        "original_dates_successfully_audited":len(result["locked_source_design"]["source_dates_successfully_audited"]),
        "original_dates_HOLD":result["locked_source_design"]["source_dates_on_HOLD"],
        "period_support":compact,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
