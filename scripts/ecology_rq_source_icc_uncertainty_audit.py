#!/usr/bin/env python3
"""Run model-conditional ICC sampling checks at two PREVIOUSLY LOCKED venues.

No new source dates, horse IDs or timing values are cherry-picked here.
Cannon Park and Eagle Farm were independently source/date locked before
this retrospective conditional Gaussian simulation was designed.
Only public Racing Queensland original read-only API and sectional
files are used. No source HORSES IDs, race IDs, animal names or GPS rows
are emitted; only aggregate model/coverage diagnostics and original
per-date source hashes.

Source failures lead to explicit HOLD; never silently treat missing
meeting dates as zero horses or exclude them for a favorable ICC.
The model-based 2.5–97.5% re-estimated-point quantiles ARE NOT robust,
source-selection-adjusted 95% confidence intervals. Identical traits
across tracks have NOT been established because first marker differs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ecology_rq_2026_calendar_overlap import (
    COHORT as CANNON_DATES, safe_failure,
)
from ecology_rq_cross_venue_identity_support import collect_cannon
from ecology_rq_eagle_farm_external_icc import (
    DATES as EAGLE_DATES,collect as collect_eagle,identity_overlap,
)
from ecology_rq_icc_parametric_uncertainty import audit, markers
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


SOURCE_LOCK={
    "cannon":{
        "official_venue":"Ladbrokes Cannon Park",
        "dates":tuple(CANNON_DATES),
        "source_doc":"docs/ecology-rq-2026-calendar-cohort-lock.md",
        "race_numbers":list(range(1,9)),
        "first_marker_sensitivities":(150.,250.),
    },
    "eagle":{
        "official_venue":"Eagle Farm",
        "dates":tuple(EAGLE_DATES),
        "source_doc":"docs/ecology-rq-eagle-farm-2026-independent-track-lock.md",
        "race_numbers":list(range(1,7)),
        "first_marker_sensitivities":(100.,200.),
    },
}


def source_model_audit(
    venue:str, *,
    soap=request_xml,gps=fetch_official,
    reader=None, fitted_draws:int=299,
    zero_draws:int=199, seed:int=20261014,
)->dict:
    if venue not in SOURCE_LOCK:
        raise ValueError("HOLD_UNAPPROVED_SOURCE_RACECOURSE")
    config=SOURCE_LOCK[venue]
    original_reader=reader or (
        collect_cannon if venue=="cannon" else collect_eagle
    )
    candidates,source_manifest=original_reader(
        soap=soap,gps=gps,on_source_error="record_HOLD"
    )
    if set(source_manifest)!=set(config["dates"]):
        raise ValueError("HOLD_DATE_MANIFEST_NOT_MATCHING_LOCKED_COHORT")
    cannon_status="SOURCE_CANNON_PARK_IDS_AND_GPS_AUDITED"
    eagle_status="SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED"
    accepted=cannon_status if venue=="cannon" else eagle_status
    missed=[
        date for date in config["dates"]
        if source_manifest[date]["status"]!=accepted
    ]
    original_hashes={}
    counts_by_date={}
    for date,info in source_manifest.items():
        hashes=info.get("original_source_SHA256_only") if venue=="cannon" else info.get("source_sha256")
        original_hashes[date]=hashes
        counts_by_date[date]={
            "status":info["status"],
            "positive_first_GPS_HORSES_ID_matches":info.get(
                "positive_first_GPS_candidates",
                info.get("first_positive_GPS_source_HORSES_ID_matches",None)
            ),
            "not_a_certified_original_finisher_count":True,
        }
    base={
        "venue":config["official_venue"],
        "source_first_party_publisher":"Racing Queensland",
        "original_source_selection_doc":config["source_doc"],
        "original_dates_requested":list(config["dates"]),
        "original_race_numbers_requested_per_date":config["race_numbers"],
        "source_dates_fully_audited":len(config["dates"])-len(missed),
        "source_date_HOLD_not_auto_excluded":missed,
        "per_date_original_source_SHA256_fingerprints":original_hashes,
        "per_date_original_source_data_readiness":counts_by_date,
        "source_is_not_independent_operator_or_sensor_platform":True,
        "same_marker_phenotype_across_Cannon_Eagle_verified":False,
        "original_horse_ID_entrant_status_is_confirmed_official_starter":False,
        "original_first_GPS_time_is_verified_full_distance_finish_time":False,
        "no_original_horse_rider_trainer_IDs_names_or_GPS_values_exported":True,
        "H1_random_ground_slopes_estimated":False,
        "H2_causal_social_interaction_estimated":False,
        "not_a_robust_population_95pct_ICC_confidence_interval":True,
    }
    consistent,identity=identity_overlap(candidates)
    base["original_identity_support"]=identity
    if missed:
        return {
            **base,
            "status":"HOLD_INCOMPLETE_LOCKED_VENUE_SOURCE_COHORT",
            "model_conditional_MC_was_not_run_on_partial_source_cohort":True,
            "not_a_zero_or_negative_horse_ICC":True,
        }
    if not consistent:
        return {
            **base,
            "status":"HOLD_NO_SOURCE_LINKED_ORIGINAL_HORSES_ID_GPS_OBSERVATIONS",
            "not_a_zero_or_negative_horse_ICC":True,
        }
    main=audit(
        consistent,min_positive_GPS_per_race=4,
        fitted_draws=fitted_draws,zero_variance_draws=zero_draws,seed=seed
    )
    filtered=markers(
        consistent,marker_values=config["first_marker_sensitivities"],
        fitted_draws=max(99,fitted_draws//2),
        null_draws=max(99,zero_draws//2),seed=seed+10000
    )
    return {
        **base,
        "status":"SOURCE_CONDITIONAL_GAUSSIAN_UNCERTAINTY_AUDITED_NOT_BIOLOGICAL_REPLICATION",
        "pooled_first_section_source_model_conditional_sampling":main,
        "first_GPS_marker_specific_model_conditional_sampling":filtered,
        "source_site_marker_mismatch_precludes_interpreting_pooled_Cannon_Eagle_as_same_trait":True,
        "source_missingness_selection_rider_trainer_and_date_dependence_not_simulated":True,
        "simulation_was_posthoc_to_positive_initial_ICCs":True,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venue",required=True,choices=tuple(SOURCE_LOCK))
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--draws",type=int,default=299)
    parser.add_argument("--null-draws",type=int,default=199)
    args=parser.parse_args()
    result=source_model_audit(
        args.venue,fitted_draws=args.draws,zero_draws=args.null_draws
    )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",
        encoding="utf-8",
    )
    main=result.get("pooled_first_section_source_model_conditional_sampling",{})
    marker=result.get("first_GPS_marker_specific_model_conditional_sampling",{})
    print(json.dumps({
        "status":result["status"],
        "venue":result["venue"],
        "source_dates_fully_audited":result["source_dates_fully_audited"],
        "source_dates_HOLD":result["source_date_HOLD_not_auto_excluded"],
        "original_identity_support":result["original_identity_support"],
        "pooled_model":{
            "status":main.get("status"),
            "observed_ICC":main.get("observed_original_race_FE_conditional_ICC"),
            "fitted_model_conditional_point_sampling":
                main.get("fitted_Gaussian_model_parametric_sampling"),
            "null_model_reference":
                main.get("zero_horse_component_Gaussian_null_simulation"),
        },
        "marker_specific":{
            k:{
                "status":v.get("status"),
                "observed_ICC":v.get("observed_original_race_FE_conditional_ICC"),
                "fitted_sampling":v.get("fitted_Gaussian_model_parametric_sampling"),
            } for k,v in marker.items()
        },
    },ensure_ascii=False))


if __name__=="__main__":
    main()
