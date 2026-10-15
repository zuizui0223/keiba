#!/usr/bin/env python3
"""Past-only within-year Doomben source-identified horse profile test.

This method is a post-hoc SAME VENUE context check after seeing a
positive within-year Cannon result and a negative Doomben 2025→2026
result. It uses no new dates, races, GPS markers or IDs and does not
constitute a study of intrinsic personality or year-related behavior.

Data records and identifying source fields stay in memory. Returned
JSON is anonymous aggregates, explicit scientific source HOLDs and
source fingerprints. Read:
docs/ecology-rq-doomben-within-year-history-design-lock.md.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import mean

from ecology_rq_doomben_2025_marker_extension import (
    DATES_2025, PREVIOUS_2026_DATES, LOCKED_DATES,
    FIRST_MARKERS, collect, verify_lock,
)
from ecology_rq_doomben_cross_year_forward import (
    MIN_OTHER_ORIGINAL_HORSES_IDS, FIXED_HISTORY_PSEUDOCOUNT,
)
from ecology_rq_eagle_farm_external_icc import identity_overlap
from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


MIN_SCORABLE_HORSES=20
MIN_SCORABLE_ROWS=20
MIN_FUTURE_DATES=6
MIN_CONTEXT_STRATA=20
MIN_GPS_PEERS=4
VALID_YEARS=("2025","2026")


def _context(row:dict, strict_class:bool)->tuple:
    return (
        round(float(row["first_section_marker"]),4),
        str(row["official_distance"]),
        str(row["race_class"]) if strict_class else None,
    )


def score_private(
    relative:list[dict], *,year:str, marker:float,strict_class:bool
)->tuple[list[dict],dict]:
    """Keep raw horse IDs and results ephemeral; NEVER serialize scored."""
    if year not in VALID_YEARS or marker not in FIRST_MARKERS:
        raise ValueError("HOLD_UNAPPROVED_WITHIN_YEAR_OR_ORIGINAL_MARKER")
    annual=[]
    for row in relative:
        day=str(row["day"])
        if len(day)<10 or day[:4] not in VALID_YEARS:
            raise ValueError("HOLD_SOURCE_DATE_YEAR_NOT_ORIGINAL")
        if day[:4]==year and abs(float(row["first_section_marker"])-marker)<1e-6:
            annual.append(row)

    grouped=defaultdict(list)
    for row in annual:
        grouped[row["day"]].append(row)

    own_history=defaultdict(list)
    other_history=defaultdict(list)
    eligible_prior_horse_ids=set()
    scored=[]
    no_other=0
    for day in sorted(grouped):
        current_rows=grouped[day]
        # Explicit no SAME-DATE update before scoring all original races.
        for row in current_rows:
            context=_context(row,strict_class)
            horse=row["horse_id"]
            prior=own_history.get((horse,context),[])
            if not prior:
                continue
            eligible_prior_horse_ids.add(horse)
            others=[r for r in other_history.get(context,[])
                    if r["horse_id"]!=horse]
            other_ids={r["horse_id"] for r in others}
            if len(other_ids)<MIN_OTHER_ORIGINAL_HORSES_IDS:
                no_other+=1
                continue
            if not all(
                r["day"]<day for r in prior+others
            ):
                raise ValueError("HOLD_SAME_DAY_OR_LATER_HISTORY_LEAKAGE")

            def historical(sh):
                n=len(sh)
                return n/(n+FIXED_HISTORY_PSEUDOCOUNT)*mean(
                    float(r["relative_early_section_sec"]) for r in sh
                )
            scored.append({
                # Purely private and never included in returned dictionary.
                "horse_id":horse,
                "day":day,
                "context":(horse,context),
                "actual":float(row["relative_early_section_sec"]),
                "own":historical(prior),
                "other":historical(others),
                "zero":0.,
            })
        for row in current_rows:
            context=_context(row,strict_class)
            own_history[(row["horse_id"],context)].append(row)
            other_history[context].append(row)

    return scored,{
        "original_source_year":int(year),
        "original_first_GPS_marker_m":int(marker),
        "official_race_class_matching_required":strict_class,
        "source_dates_with_positive_original_GPS_timing_for_marker":
            len(grouped),
        "original_positive_timed_GPS_rows_for_marker":len(annual),
        "original_source_HORSES_IDs_with_at_least_one_earlier_matching_observation":
            len(eligible_prior_horse_ids),
        "original_matched_future_rows_missing_3_other_HORSES_IDs":no_other,
        "scored_anonymous_distinct_original_HORSES_IDs":
            len({r["horse_id"] for r in scored}),
        "scored_anonymous_original_future_rows":len(scored),
        "distinct_future_original_meeting_dates_scored":
            len({r["day"] for r in scored}),
        "distinct_horse_by_marker_distance_optional_class_contexts":
            len({r["context"] for r in scored}),
        "only_same_original_year_prior_date_training":True,
        "same_date_not_used_to_fit_prior_profiles":True,
        "focal_horse_excluded_from_other_history":True,
        "no_original_HORSES_ID_names_licence_or_times_exported":True,
    }


def scoring_summary(
    relative:list[dict], *,year:str,marker:float,strict_class:bool
)->dict:
    scored,support=score_private(relative,year=year,marker=marker,
                                 strict_class=strict_class)
    common={
        "status":"HOLD_TOO_FEW_WITHIN_YEAR_REPEATED_HORSES_FUTURE_ROWS_OR_DATES",
        "comparison_population":support,
        "minimum_HORSES_IDs":MIN_SCORABLE_HORSES,
        "minimum_future_rows":MIN_SCORABLE_ROWS,
        "minimum_future_dates":MIN_FUTURE_DATES,
        "minimum_horse_by_contexts":MIN_CONTEXT_STRATA,
        "relative_first_GPS_target_requires_observed_postrace_peers":True,
        "no_2025_or_2026_crossyear_combination_for_training":True,
        "no_2025_training_values_used_for_a_2026_within_year_prediction":True,
        "not_a_causal_year_trainer_jockey_ground_or_evolution_effect":True,
        "no_original_horse_ID_names_role_IDs_or_individual_predictions":True,
    }
    if not (
        support["scored_anonymous_distinct_original_HORSES_IDs"]>=MIN_SCORABLE_HORSES
        and support["scored_anonymous_original_future_rows"]>=MIN_SCORABLE_ROWS
        and support["distinct_future_original_meeting_dates_scored"]>=MIN_FUTURE_DATES
        and support["distinct_horse_by_marker_distance_optional_class_contexts"]>=MIN_CONTEXT_STRATA
    ):
        return common

    by_id=defaultdict(list)
    for r in scored:
        by_id[r["horse_id"]].append(r)
    if not by_id:
        raise ValueError("HOLD_EMPTY_WITHIN_YEAR_SCORE_DESPITE_SUPPORT")
    def error(key:str,power:int):
        return mean(
            mean(abs(r["actual"]-r[key])**power for r in grp)
            for grp in by_id.values()
        )
    rmse={name:math.sqrt(error(name,2))
          for name in ("zero","own","other")}
    mae={name:error(name,1)
         for name in ("zero","own","other")}
    if not all(math.isfinite(v) for v in list(rmse.values())+list(mae.values())):
        raise ValueError("HOLD_NONFINITE_WITHIN_YEAR_ERROR")

    return {
        **common,
        "status":"EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY",
        "equal_horse_RMSE_seconds":{
            "zero":rmse["zero"],
            "own":rmse["own"],
            "other_horses_same_marker_and_distance":rmse["other"],
            "OTHER_minus_OWN_positive_horse_history_better":rmse["other"]-rmse["own"],
            "ZERO_minus_OWN_positive_horse_history_better":rmse["zero"]-rmse["own"],
        },
        "equal_horse_MAE_seconds":mae,
        "not_an_independent_cohort_or_valid_population_CI":True,
    }


def analyze(
    relative:list[dict], *,source_dates:list[str],
    source_HOLD_dates:list[str],source_manifests:dict
)->dict:
    original_keys={"2025":list(DATES_2025),
                   "2026":list(PREVIOUS_2026_DATES)}
    if (set(source_dates)|set(source_HOLD_dates)!=set(LOCKED_DATES)
        or set(source_dates)&set(source_HOLD_dates)):
        raise ValueError("HOLD_NOT_EXACTLY_PREVIOUSLY_LOCKED_DOOMBEN_SOURCE_DATES")
    comparisons={}
    for year in VALID_YEARS:
        for marker in FIRST_MARKERS:
            for strict in (False,True):
                key=f"{year}_{int(marker)}m_same_distance"+(
                    "_and_Class" if strict else ""
                )
                comparisons[key]=scoring_summary(
                    relative,year=year,marker=marker,strict_class=strict
                )

    return {
        "status":"EXPLORATORY_ORIGINAL_DOOMBEN_SAME_YEAR_CONTEXT_CONTROL_NOT_CAUSAL",
        "original_venue":"Doomben",
        "source_publisher":"Racing Queensland",
        "design_frozen_before_NEW_within_year_scores":True,
        "original_source_calendar":{
            "fixed_2025_date_count":len(original_keys["2025"]),
            "fixed_2026_date_count":len(original_keys["2026"]),
            "fixed_original_meeting_date_counts_not_adapted_after_outcome":True,
            "original_locked_source_dates_successful":len(source_dates),
            "original_source_HOLD_dates":source_HOLD_dates,
            "success_counts_by_calendar_year":{
                y:sum(d.startswith(y) for d in source_dates) for y in VALID_YEARS
            },
        },
        "source_manifest":source_manifests,
        "comparisons_by_year_marker_context":comparisons,
        "not_a_within_individual_year_change_or_H1_H2":True,
        "cannon_study_had_DIFFERENT_source_rider_eligibility":True,
        "crossyear_2025_to_2026_study_evaluated_DIFFERENT_observations":True,
        "no_individual_horse_names_IDs_role_IDs_section_times_or_predictions_exported":True,
    }


def evaluate(*,soap=request_xml,gps=fetch_official,
             source_error_mode:str="record_HOLD")->dict:
    verify_lock()
    if source_error_mode not in ("record_HOLD","raise"):
        raise ValueError("HOLD_UNAPPROVED_SOURCE_ERROR_MODE")
    raw,source=collect(soap=soap,gps=gps,on_error=source_error_mode)
    clean,identity=identity_overlap(raw)
    if clean:
        relative,peer_coverage=prepare(clean,min_race_telemetry=MIN_GPS_PEERS)
    else:
        relative=[]
        peer_coverage={"status":"HOLD_NO_OFFICIAL_RACE_RELATIVE_SOURCE_ROWS"}
    successes=sorted(d for d,info in source.items()
        if info.get("status")=="OFFICIAL_2025_OR_2026_DOOMBEN_SOURCE_ID_GPS_AUDITED")
    holds=sorted(set(LOCKED_DATES)-set(successes))
    aggregate=analyze(relative,source_dates=successes,
                      source_HOLD_dates=holds,source_manifests=source)
    aggregate["source_join_identity_counts_only"]=identity
    aggregate["source_timed_GPS_peer_coverage_counts_only"]=peer_coverage
    aggregate["not_preregistered_annual_personality_decay_or_betting"]=True
    return aggregate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_source_dates_successful":
            result["original_source_calendar"]["original_locked_source_dates_successful"],
        "original_source_HOLD_dates":
            result["original_source_calendar"]["original_source_HOLD_dates"],
        "year_marker_status_scores":{
            key:{
                "status":data["status"],
                "source_support":data["comparison_population"],
                "rmse":data.get("equal_horse_RMSE_seconds"),
            } for key,data in result["comparisons_by_year_marker_context"].items()
        },
        "source_personal_identifiers_never_output":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
