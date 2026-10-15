#!/usr/bin/env python3
"""Independently compare two *anonymous* original RQ Doomben source reruns.

Input: JSON aggregates from TWO previously successful GitHub Actions
runs, never original animal records. Compare source byte-derived SHA256
digests, documented source response availability and fixed original
HORSES-ID support. An effect based on 21 horses that drops to 17 at
a rerun has NOT passed cross-run robustness.

No per-animal IDs/timings/runner records are accepted or exported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ecology_rq_doomben_2025_marker_extension import (
    LOCKED_DATES,DATES_2025,PREVIOUS_2026_DATES,
)

SOURCE_OK="OFFICIAL_2025_OR_2026_DOOMBEN_SOURCE_ID_GPS_AUDITED"
SOURCE_FIELDS=(
    "original_first_party_meeting_race_GPS_source_SHA256",
    "original_horse_roster_combined_SHA256",
    "original_horse_roster_response_count",
    "original_positive_first_GPS_HORSES_ID_rows",
    "numeric_race_IDs_returned",
    "original_race_numbers_requested",
)
YEAR_MARKERS=(("2025",150),("2025",200),("2026",150),("2026",200))
NUMERIC_OK="EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY"
HOLD="HOLD_TOO_FEW_WITHIN_YEAR_REPEATED_HORSES_FUTURE_ROWS_OR_DATES"


def _validate_input(data:dict):
    cal=data["original_source_calendar"]
    if (cal["fixed_2025_date_count"]!=len(DATES_2025)
        or cal["fixed_2026_date_count"]!=len(PREVIOUS_2026_DATES)
        or set(data["source_manifest"])!=set(LOCKED_DATES)
        or not data["no_individual_horse_names_IDs_role_IDs_section_times_or_predictions_exported"]):
        raise ValueError("HOLD_NOT_MATCHING_ORIGINAL_SOURCE_COHORT_OR_PRIVACY")
    common=set(data["comparisons_by_year_marker_context"])
    expected={
        f"{year}_{marker}m_same_distance"+("" if not cls else "_and_Class")
        for year,marker in YEAR_MARKERS for cls in (False,True)
    }
    if common!=expected:
        raise ValueError("HOLD_MISSING_PREDECLARED_SOURCE_COMPARISON_CONTEXTS")
    nsuccess=sum(x.get("status")==SOURCE_OK for x in data["source_manifest"].values())
    if nsuccess!=cal["original_locked_source_dates_successful"]:
        raise ValueError("HOLD_SCIENTIFIC_SOURCE_SUCCESS_COUNT_INCONSISTENT")
    hold=sorted(d for d,v in data["source_manifest"].items()
                if v.get("status")!=SOURCE_OK)
    if hold!=cal["original_source_HOLD_dates"]:
        raise ValueError("HOLD_REPORTED_SOURCE_DATES_DIFFER_FROM_MANIFEST")
    for day in LOCKED_DATES:
        entry=data["source_manifest"][day]
        if entry.get("status")==SOURCE_OK:
            for key in SOURCE_FIELDS:
                if key not in entry:
                    raise ValueError("HOLD_UNFINGERPRINTED_ORIGINAL_SOURCE_COMPONENT")
            dig=entry["original_first_party_meeting_race_GPS_source_SHA256"]
            if set(dig)!={"meeting_xml_sha256","race_xml_sha256","gps_csv_sha256"}:
                raise ValueError("HOLD_INCOMPLETE_ORIGINAL_SOURCE_HASHES")
            if not all(isinstance(v,str) and len(v)==64 for v in dig.values()):
                raise ValueError("HOLD_INVALID_ORIGINAL_SOURCE_HASH")
            orig=entry["original_horse_roster_combined_SHA256"]
            if not isinstance(orig,str) or len(orig)!=64:
                raise ValueError("HOLD_INVALID_HORSES_ROSTER_HASH")
    for key,cell in data["comparisons_by_year_marker_context"].items():
        status=cell["status"]
        n=cell["comparison_population"]["scored_anonymous_distinct_original_HORSES_IDs"]
        if status not in (NUMERIC_OK,HOLD):
            raise ValueError("HOLD_UNAPPROVED_SCIENTIFIC_SOURCE_SCORE_STATUS")
        if status==NUMERIC_OK:
            if n<20 or "equal_horse_RMSE_seconds" not in cell:
                raise ValueError("HOLD_NUMERIC_SCORE_WITHOUT_ORIGINAL_HORSE_SUPPORT")
        elif "equal_horse_RMSE_seconds" in cell:
            raise ValueError("HOLD_EMITTED_UNSUPPORTED_HORSE_SCORE")


def _digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def compare(a:dict,b:dict,*,a_sha256:str,b_sha256:str)->dict:
    _validate_input(a)
    _validate_input(b)
    successA={d for d,v in a["source_manifest"].items() if v["status"]==SOURCE_OK}
    successB={d for d,v in b["source_manifest"].items() if v["status"]==SOURCE_OK}
    both=sorted(successA&successB)
    onlyA=sorted(successA-successB)
    onlyB=sorted(successB-successA)
    common_field_match={k:0 for k in SOURCE_FIELDS}
    changed={}
    for day in both:
        aa=a["source_manifest"][day]
        bb=b["source_manifest"][day]
        fields=[k for k in SOURCE_FIELDS if aa[k]!=bb[k]]
        if fields:
            changed[day]=fields
        for k in SOURCE_FIELDS:
            if aa[k]==bb[k]:
                common_field_match[k]+=1
    read_on_one={
        day:{
            "only_one_run_successful":"A" if day in onlyA else "B",
            "original_matched_positive_GPS_candidates":(
                a if day in onlyA else b
            )["source_manifest"][day]["original_positive_first_GPS_HORSES_ID_rows"],
            "other_run_source_hold_code":(
                b if day in onlyA else a
            )["source_manifest"][day].get("error_code","HOLD_SOURCE_UNAVAILABLE"),
        } for day in sorted(set(onlyA)|set(onlyB))
    }
    locked_criteria={}
    any_nonrobust=False
    for key in sorted(a["comparisons_by_year_marker_context"]):
        x=a["comparisons_by_year_marker_context"][key]
        y=b["comparisons_by_year_marker_context"][key]
        xi=x["comparison_population"]
        yi=y["comparison_population"]
        both_numeric=x["status"]==y["status"]==NUMERIC_OK
        # Distinct source day coverage alone cannot identify the
        # exact individual animals in both inference populations.
        same_n=(
            xi["scored_anonymous_distinct_original_HORSES_IDs"]
            ==yi["scored_anonymous_distinct_original_HORSES_IDs"]
            and xi["scored_anonymous_original_future_rows"]
            ==yi["scored_anonymous_original_future_rows"]
        )
        stable_numeric=both_numeric and same_n and set(successA)==set(successB)
        if x["status"]==NUMERIC_OK or y["status"]==NUMERIC_OK:
            if not stable_numeric:
                any_nonrobust=True
        locked_criteria[key]={
            "runA_status":x["status"],
            "runB_status":y["status"],
            "runA_original_HORSES_IDs":xi[
                "scored_anonymous_distinct_original_HORSES_IDs"],
            "runB_original_HORSES_IDs":yi[
                "scored_anonymous_distinct_original_HORSES_IDs"],
            "runA_later_source_records":xi["scored_anonymous_original_future_rows"],
            "runB_later_source_records":yi["scored_anonymous_original_future_rows"],
            "runA_numeric_GAIN_if_supported":(
                x.get("equal_horse_RMSE_seconds",{}).get(
                    "OTHER_minus_OWN_positive_horse_history_better")
                if x["status"]==NUMERIC_OK else None
            ),
            "runB_numeric_GAIN_if_supported":(
                y.get("equal_horse_RMSE_seconds",{}).get(
                    "OTHER_minus_OWN_positive_horse_history_better")
                if y["status"]==NUMERIC_OK else None
            ),
            "same_source_population_supported_across_two_runs":stable_numeric,
            "no_HOLD_interpreted_as_zero_horse_variation":True,
        }
    count_hash=all(v==len(both) for v in common_field_match.values())
    return {
        "status":(
            "HOLD_DOOMBEN_WITHIN_YEAR_SCORE_NOT_ROBUST_TO_SOURCE_AVAILABILITY"
            if (any_nonrobust or changed or not count_hash) else
            "SOURCE_RUNS_AGREE_ON_AVAILABLE_SCIENTIFIC_NUMERIC_GATES_ONLY"
        ),
        "publisher":"Racing Queensland",
        "original_fixed_source_2025_dates":len(DATES_2025),
        "original_fixed_source_2026_dates":len(PREVIOUS_2026_DATES),
        "runA_file_SHA256":a_sha256,
        "runB_file_SHA256":b_sha256,
        "runA_source_dates_succeeded":len(successA),
        "runB_source_dates_succeeded":len(successB),
        "shared_original_source_success_dates":len(both),
        "shared_success_source_component_equality_counts":common_field_match,
        "shared_dates_with_changed_original_source_fingerprints_or_counts":changed,
        "dates_only_runA_read_successfully":onlyA,
        "dates_only_runB_read_successfully":onlyB,
        "different_original_source_availability_details":read_on_one,
        "source_HOLD_date_union":sorted(set(LOCKED_DATES)-(successA&successB)),
        "original_year_marker_class_context_gate_sensitivity":locked_criteria,
        "runA_positive_result_NOT_independent_replication_when_runB_HOLD":True,
        "no_animal_age_development_or_causal_year_effect_identified":True,
        "source_missing_date_not_zero_horse_or_neglected_result":True,
        "no_original_horse_names_IDs_licence_GPS_row_or_predictions_exported":True,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runA",type=Path,required=True)
    parser.add_argument("--runB",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    rawA=args.runA.read_bytes()
    rawB=args.runB.read_bytes()
    data=compare(json.loads(rawA),json.loads(rawB),
                 a_sha256=_digest(rawA),b_sha256=_digest(rawB))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":data["status"],
        "shared_success_dates":data["shared_original_source_success_dates"],
        "source_digest_same_counts":data["shared_success_source_component_equality_counts"],
        "different_source_dates":data["different_original_source_availability_details"],
        "2025_150m_support":data[
            "original_year_marker_class_context_gate_sensitivity"][
            "2025_150m_same_distance"],
        "no_individual_source_records":True,
    }))


if __name__=="__main__":
    main()
