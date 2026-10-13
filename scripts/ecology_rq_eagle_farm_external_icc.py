#!/usr/bin/env python3
"""Cross-racecourse original RQ Thoroughbred source: Eagle Farm, 2026.

This is a venue-external *exploratory observational* check of the
race-fixed Gaussian horse-ID ICC previously computed at Cannon Park.

The 12 Eagle Farm meeting dates and race numbers 1-6 were selected
and COMMITTED TO docs/ecology-rq-eagle-farm-2026-independent-track-lock.md
before their original HORSES IDs, first GPS times or ICC were inspected.

Same original source, measurement pipeline, publisher and potentially
overlapping animals: this is NOT an independent biological experiment.
No names, HORSES IDs, rider/trainer licence values, race result rows,
individual timing records, predictions or betting recommendations are
written to GitHub or to the aggregate JSON artifact.

API may list nominated/nonstarting animals; positive source GPS confirms
telemetry ONLY, not official starters, final finish times or true DNF.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from ecology_rq_multigoing_h1_preflight import audit_one_day
from ecology_rq_2026_calendar_overlap import safe_failure
from ecology_rq_race_fixed_icc import analyze as race_fixed_icc
from ecology_rq_covariate_icc import compare as nuisance_adjusted_icc
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


VENUE="Eagle Farm"
DATES=(
    "2026-01-03",
    "2026-02-14",
    "2026-03-07",
    "2026-04-18",
    "2026-05-02",
    "2026-06-13",
    "2026-07-25",
    "2026-08-08",
    "2026-08-29",
    "2026-09-19",
    "2026-10-03",
    "2026-10-10",
)
RACE_NUMBERS=(1,2,3,4,5,6)
EXPECTED_ORIGINAL_FILES={
    d: d.replace("-","")+"-eagle-farm" for d in DATES
}

# FROZEN ORIGINAL CANNON PARK 2026 12-date source-marker support,
# independently recorded BEFORE this new Eagle Farm outcome was seen.
# See docs/ecology-rq-real-horse-race-adjusted-icc.md (not a paired design).
CANNON_MARKER_SOURCE_SUPPORT={
    "100.0":{"positive_GPS_rows":32,"original_races":4,
             "ICC_estimable":False},
    "150.0":{"positive_GPS_rows":209,"original_races":29,
             "ICC_estimable":True},
    "200.0":{"positive_GPS_rows":56,"original_races":8,
             "ICC_estimable":False},
    "250.0":{"positive_GPS_rows":226,"original_races":33,
             "ICC_estimable":True},
}


def cross_venue_marker_identifiability(fitted:dict)->dict:
    """Cannot compare pooled ICCs if source interval measurements differ."""
    eagle=fitted.get("first_section_marker_sensitivity",{})
    statuses={
        "EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY",
        "EXPLORATORY_RACE_ADJUSTED_ICC_AT_ZERO_BOUNDARY",
    }
    rows={}
    comparable=[]
    for marker,ref in CANNON_MARKER_SOURCE_SUPPORT.items():
        cross=eagle.get(marker,{})
        eagle_status=cross.get("status","HOLD_NO_EAGLE_SOURCE_MODEL")
        passed=ref["ICC_estimable"] and eagle_status in statuses
        rows[marker]={
            "original_Cannon_source_positive_GPS_rows":ref["positive_GPS_rows"],
            "original_Cannon_source_races":ref["original_races"],
            "original_Cannon_ICC_numeric_gate_passed":ref["ICC_estimable"],
            "Eagle_original_positive_GPS_rows":int(cross.get("source_rows",0)),
            "Eagle_original_numeric_ICC_status":eagle_status,
            "identical_first_section_marker_model_estimable_at_both_venues":passed,
        }
        if passed:
            comparable.append(marker)
    return {
        "status":(
            "EXPLORATORY_SAME_FIRST_MARKER_VENUE_ICC_COMPARABLE"
            if comparable else
            "HOLD_NO_SHARED_FIRST_SECTION_MARKER_WITH_ESTIMABLE_ICC"
        ),
        "original_source_markers_screened":rows,
        "first_markers_with_estimable_ICC_at_both_venues":comparable,
        "pooled_Cannon_vs_Eagle_ICC_can_establish_universal_horse_trait":False,
        "original_marker_distribution_mismatch_is_a_source_bias":True,
    }



def validate_source_lock()->None:
    from ecology_rq_thoroughbred_sectional_audit import APPROVED
    if len(DATES)!=12 or DATES!=tuple(sorted(DATES)) or len(RACE_NUMBERS)!=6:
        raise ValueError("HOLD_EAGLE_FARM_CALENDAR_LOCK_CHANGED")
    if len(set(DATES))!=12 or len(set(EXPECTED_ORIGINAL_FILES.values()))!=12:
        raise ValueError("HOLD_EAGLE_FARM_SOURCE_DUPLICATE")
    for d,key in EXPECTED_ORIGINAL_FILES.items():
        if key not in APPROVED or APPROVED[key]!=d.replace("-","")+"_Eagle_Farm_T.csv":
            raise ValueError("HOLD_EAGLE_FARM_SOURCE_NOT_IN_EXPLICIT_ALLOWLIST")


def collect(
    *,
    soap=request_xml,
    gps=fetch_official,
    on_source_error: str="record_HOLD",
)->tuple[list[dict],dict]:
    validate_source_lock()
    if on_source_error not in ("record_HOLD","raise"):
        raise ValueError("HOLD_EAGLE_FARM_UNAPPROVED_ERROR_MODE")

    eligible=[]
    manifest={}
    for day in DATES:
        cfg={
            "source":EXPECTED_ORIGINAL_FILES[day],
            "ground_expected":"SOURCE_RACE_LEVEL",
            "races":RACE_NUMBERS,
        }
        try:
            info,rows=audit_one_day(
                day,soap=soap,gps=gps,
                venue=VENUE,locked_config=cfg,
                race_selection=RACE_NUMBERS,
            )
            if info["venue"]!=VENUE or not info["source_race_level_TrackRating_always_used"]:
                raise ValueError("HOLD_ORIGINAL_VENUE_OR_GROUND_MISMATCH")
            manifest[day]={
                "status":"SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED",
                "race_numbers_requested":list(RACE_NUMBERS),
                "numeric_official_race_IDs_returned":
                    len(info["official_race_numbers_available"]),
                "official_race_numbers_not_in_API":
                    info["missing_official_race_numbers"],
                "official_race_level_going_labels":
                    info["actual_official_ground_labels"],
                "first_positive_GPS_source_HORSES_ID_matches":len(rows),
                "api_nomination_horse_rows":info["api_horse_row_count"],
                "source_HORSES_IDs_listed_in_multiple_races_same_date":
                    info["official_ids_listed_more_than_once_on_date"],
                "source_same_day_duplicate_names_detected":
                    info["candidate_rows_with_same_day_duplicate_gps_name"],
                "source_missing_or_zero_positive_first_GPS_candidates":
                    info["candidate_rows_with_no_exact_positive_first_section"],
                "complete_weight_jockey_trainer_first_GPS_candidates":
                    info["matched_positive_GPS_with_complete_weight_jockey_trainer"],
                "source_sha256":info["source_hashes"],
                "first_party_original_source_attribution":"Racing Queensland",
                "no_individual_raw_source_values_in_report":True,
            }
            eligible.extend(rows)
        except (ValueError,OSError,TimeoutError) as exc:
            if on_source_error=="raise":
                raise
            manifest[day]=safe_failure(exc)
    return eligible,manifest


def identity_overlap(rows:list[dict])->tuple[list[dict],dict]:
    """Prohibit a numeric official HORSES ID associated with changed name.

    This should be a rare source anomaly; discarding ALL observations
    of suspect IDs avoids choosing the name/date with better GPS results.
    """
    by_id=defaultdict(list)
    for row in rows:
        by_id[row["horse_id"]].append(row)
    bad={horse for horse,records in by_id.items()
         if len({r["horse_name"] for r in records})>1}
    good=[r for r in rows if r["horse_id"] not in bad]
    counts=Counter(r["horse_id"] for r in good)
    days=defaultdict(set)
    markers=Counter()
    ground=Counter()
    for row in good:
        days[row["horse_id"]].add(row["day"])
        markers[str(row["first_marker_m"])]+=1
        ground[row["ground"]]+=1
    return good,{
        "original_ID_matched_positive_first_GPS_candidate_rows":len(rows),
        "rows_after_original_ID_name_identity_consistency":len(good),
        "distinct_original_IDs_after_name_identity_screen":len(counts),
        "HORSES_IDs_with_different_names_across_dates_blocked":len(bad),
        "horse_IDs_in_2plus_source_dates":sum(len(v)>=2 for v in days.values()),
        "HORSES_IDs_with_4plus_source_starts":sum(v>=4 for v in counts.values()),
        "first_positive_GPS_segment_markers":dict(sorted(markers.items())),
        "official_source_race_level_ground_of_matched_GPS_rows":
            dict(sorted(ground.items())),
        "not_confirmed_complete_entrant_or_finisher_population":True,
        "individual_numeric_HORSES_IDs_and_names_not_exported":True,
    }


def compare(*,soap=request_xml,gps=fetch_official,
            on_source_error:str="record_HOLD") ->dict:
    rows,manifest=collect(
        soap=soap,gps=gps,on_source_error=on_source_error
    )
    good,identity=identity_overlap(rows)
    status="EAGLE_FARM_DIFFERENT_VENUE_OBSERVATIONAL_ICC_FEASIBILITY_HOLD_H1_H2"
    if not good:
        baseline={
            "status":"HOLD_NO_ORIGINAL_EAGLE_FARM_ID_POSITIVE_GPS_LINKS",
            "not_a_statistical_zero":True,
        }
        adjustment={
            "status":"HOLD_NO_ORIGINAL_EAGLE_FARM_ID_POSITIVE_GPS_LINKS",
            "not_a_statistical_zero":True,
        }
    else:
        # Exactly the preexisting Cannon Park model and the same
        # source-completeness/role fixed effect implementation.
        baseline=race_fixed_icc(good)
        adjustment=nuisance_adjusted_icc(good,minimum_GPS=4)
    successful=[d for d in DATES if manifest[d]["status"]==
                "SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED"]
    return {
        "status":status,
        "publication_risk":"EXPLORATORY_DIFFERENT_TRACK_SAME_DATA_OPERATOR",
        "locked_source_design":{
            "source_cohort_doc":
                "docs/ecology-rq-eagle-farm-2026-independent-track-lock.md",
            "original_dates_requested":list(DATES),
            "original_dates_successfully_audited":successful,
            "source_dates_on_HOLD":sorted(set(DATES)-set(successful)),
            "race_numbers_requested_per_meeting":list(RACE_NUMBERS),
            "cohort_was_fixed_before_Eagle_Farm_original_HORSES_ID_or_ICC_read":
                True,
            "comparison_to_Cannon_Park_is_not_random_animal_assignment":True,
        },
        "original_source_per_date":manifest,
        "independent_venue_original_ID_support":identity,
        "conditional_ICC_at_Eagle_Farm_existing_race_FE_implementation":baseline,
        "different_venue_same_first_GPS_marker_ICC_identifiability":
            cross_venue_marker_identifiability(baseline),
        "documented_source_weight_jockey_trainer_adjustment":adjustment,
        "historical_Cannon_Park_source_ICC_reference_ONLY_not_a_paired_model":{
            "race_FE_absolute_first_segment_seconds":
                0.431738,
            "original_horse_source_rows":523,
            "races":74,
            "source_date_count":12,
            "different_source_selection_and_measurement_marker_mix":True,
            "not_formally_statistically_tested_as_venue_effect":True,
        },
        "public_raw_horse_rider_trainer_ids_or_original_times_exported":False,
        "source_license_attribution":"Racing Queensland",
        "ecological_H1_ground_reaction_norm_var_supported":False,
        "ecological_H2_competitor_social_interaction_supported":False,
        "actual_starter_DNF_and_individual_official_finish_verified":False,
        "claims_not_supported":[
            "A positive new-venue ICC proves inherited horse personality",
            "A cross-track ICC difference is a causal effect of venue",
            "The reference Cannon Park ICC and Eagle Farm ICC use the same random animal population",
            "All GPS-silent horses are nonfinishers",
            "Rider, trainer or horse age is completely controlled or randomly assigned",
            "H1 ground-response random slopes and H2 social competitor effects",
            "Independent operator/sensor replication or population-wide heritability",
        ],
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--strict-source-errors",action="store_true")
    args=p.parse_args()
    x=compare(on_source_error=("raise" if args.strict_source_errors
                               else "record_HOLD"))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    diag=x["conditional_ICC_at_Eagle_Farm_existing_race_FE_implementation"]
    adj=x["documented_source_weight_jockey_trainer_adjustment"]
    models=adj.get("models",{})
    def model_point(key):
        return models.get(key,{}).get(
            "conditional_ICC_point",
            models.get(key,{}).get("conditional_observational_ICC_point_estimate")
        )
    print(json.dumps({
        "status":x["status"],
        "source_dates_verified":len(
            x["locked_source_design"]["original_dates_successfully_audited"]),
        "source_dates_HOLD":
            x["locked_source_design"]["source_dates_on_HOLD"],
        "identity_support":x["independent_venue_original_ID_support"],
        "original_race_FE_ICC_model":
            diag.get("all_races_at_least_four_timed_horses",diag),
        "six_positive_GPS_race_ICC":
            diag.get("races_at_least_six_timed_horses"),
        "first_section_marker_model_status": {
            m:{"status":v.get("status"),
               "source_rows":v.get("source_rows",0),
               "source_races":v.get("original_races",0),
               "point":v.get("conditional_observational_ICC_point_estimate")}
            for m,v in diag.get("first_section_marker_sensitivity",{}).items()
        },
        "meeting_date_deletion_range":
            diag.get("leave_one_date_out_four_GPS_minimum"),
        "within_race_identity_shuffle_reference":
            diag.get("within_race_horse_ID_shuffle_reference"),
        "source_covariate_complete_case_gate":adj.get("source_gate"),
        "same_eligible_source_rows_adjusted_ICC_points":{
            "baseline":model_point("same_rows_unadjusted_race_HORSES"),
            "weight_only":model_point("weight_within_race"),
            "weight_jockey":model_point("weight_plus_jockey_license"),
            "weight_jockey_trainer":model_point("weight_jockey_trainer_license"),
        },
        "source_adjusted_ICC_stability":
            adj.get("date_deletion_same_source_baseline_vs_nuisance_stability"),
        "cross_venue_same_first_section_marker_ICC_gate":
            x["different_venue_same_first_GPS_marker_ICC_identifiability"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
