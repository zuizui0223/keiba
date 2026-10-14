#!/usr/bin/env python3
"""Strictly past-only horse early-GPS timing profiles under documented jockey change.

On the ORIGINAL 12-date Cannon Park RQ cohort only.  Post-hoc exploratory
source-conditional out-of-time verification, not source independence,
pre-race betting, confirmed final jockey assignment, heritability or H1/H2.

The input 'timed' rows are in-memory original HORSES ID and race-relative
first GPS time rows prepared by ecology_rq_rider_switch_consistency.
Only anonymous aggregate counts and model errors leave this module.
"""
from __future__ import annotations

from collections import defaultdict
from math import sqrt
from statistics import mean

MIN_SCORABLE_HORSES=20
MIN_SCORABLE_ROWS=20
MIN_FUTURE_SOURCE_DATES=6
MIN_SOURCE_CONTEXT_STRATA=20
FIXED_SHRINKAGE_PSEUDO_COUNT=2


def context(r:dict, strict_class:bool)->tuple:
    return (
        r["horse_id"], str(r["distance"]),
        float(r["marker"]), r["race_class"] if strict_class else None
    )


def forward_records(timed:list[dict],*,strict_class:bool=False)->list[dict]:
    """Return private ephemeral scoring data only; NEVER serialize it publicly.

    All observations on a test day are scored against only earlier
    dates before any same-day observation is appended to history.
    Jockey metadata is checked only against earlier *documented*
    licences, not assumed historical actual rider assignments.
    """
    keyed=defaultdict(list)
    for r in timed:
        keyed[r["day"]].append(r)
    history=defaultdict(list)
    result=[]
    for day in sorted(keyed):
        daily=keyed[day]
        # No training update within the same source date
        for row in daily:
            past=history.get(context(row,strict_class),[])
            if not past:
                continue
            valid_riders={r["jockey_id"] for r in past if r["jockey_id"] is not None}
            current=row["jockey_id"]
            if not current or not valid_riders:
                continue
            if not all(x["day"]<day for x in past):
                raise ValueError("HOLD_TRAINING_USES_PRESENT_OR_FUTURE_SOURCE_DATE")
            n=len(past)
            prior_mean=mean(r["relative_seconds"] for r in past)
            profile=(n/(n+FIXED_SHRINKAGE_PSEUDO_COUNT))*prior_mean
            y=row["relative_seconds"]
            same_known_trainer=(
                row["trainer_id"] is not None
                and any(old["trainer_id"]==row["trainer_id"] for old in past)
            )
            record={
                # only local ephemeral identities
                "horse_id":row["horse_id"],
                "context":context(row,strict_class),
                "day":day,
                "previous_same_documented_jockey":current in valid_riders,
                "same_documented_trainer_seen_in_prior_context":
                    same_known_trainer,
                "one_or_more_unidentified_jockeys_in_prior_context":
                    any(old["jockey_id"] is None for old in past),
                "zero_squared_error":y*y,
                "profile_squared_error":(y-profile)**2,
                "zero_absolute_error":abs(y),
                "profile_absolute_error":abs(y-profile),
            }
            result.append(record)
        for row in daily:
            history[context(row,strict_class)].append(row)
    return result


def summarize_forward(scored:list[dict], category:str,*,strict_class:bool)->dict:
    conditions={
        "new_documented_rider":lambda x:not x["previous_same_documented_jockey"],
        "previously_seen_documented_rider":lambda x:x["previous_same_documented_jockey"],
        "new_documented_rider_and_same_documented_trainer":
            lambda x:(not x["previous_same_documented_jockey"]
                      and x["same_documented_trainer_seen_in_prior_context"]),
    }
    if category not in conditions:
        raise ValueError("HOLD_NOT_AN_APPROVED_CHRONOLOGICAL_SCORING_COHORT")
    eligible=[r for r in scored if conditions[category](r)]
    animal=defaultdict(list)
    for r in eligible:
        animal[r["horse_id"]].append(r)
    future_dates={r["day"] for r in eligible}
    strata={r["context"] for r in eligible}
    measured={
        "status":"HOLD_INSUFFICIENT_PRIOR_SOURCE_MATCH_AND_FUTURE_CHANGED_RIDER_SUPPORT",
        "original_animal_IDs_with_out_of_date_predictions":len(animal),
        "out_of_date_matched_source_rows_scored":len(eligible),
        "distinct_future_source_meeting_dates_scored":len(future_dates),
        "distinct_same_animal_marker_distance_contexts_scored":len(strata),
        "future_rows_with_unknown_at_least_one_past_jockey_ID":
            sum(r["one_or_more_unidentified_jockeys_in_prior_context"]
                for r in eligible),
        "source_selection_requires_at_least_one_known_prior_jockey":True,
        "all_training_dates_strictly_before_current_date":True,
        "prior_shrinkage_n_over_n_plus_two_fixed":True,
        "outcome_uses_postrace_other_timed_GPS_peers":True,
        "not_actual_final_rider_change_or_betting_prediction":True,
        "no_individual_source_animal_jockey_trainer_or_timing_exported":True,
    }
    sufficient=(len(animal)>=MIN_SCORABLE_HORSES
                and len(eligible)>=MIN_SCORABLE_ROWS
                and len(future_dates)>=MIN_FUTURE_SOURCE_DATES
                and len(strata)>=MIN_SOURCE_CONTEXT_STRATA)
    if not sufficient:
        return measured

    def per_horse_mean(field):
        return mean(mean(r[field] for r in vals) for vals in animal.values())

    null_horse_rmse=sqrt(per_horse_mean("zero_squared_error"))
    known_horse_rmse=sqrt(per_horse_mean("profile_squared_error"))
    measured.update({
        "status":"EXPLORATORY_HORSE_PROFILE_CHRONOLOGICAL_SOURCE_CHECK_ONLY",
        "equal_horse_weighted_zero_benchmark_RMSE_seconds":null_horse_rmse,
        "equal_horse_weighted_past_horse_RMSE_seconds":known_horse_rmse,
        "equal_horse_weighted_RMSE_reduction_seconds_positive_if_persistent":
            null_horse_rmse-known_horse_rmse,
        "equal_horse_weighted_zero_benchmark_MAE_seconds":
            per_horse_mean("zero_absolute_error"),
        "equal_horse_weighted_past_horse_MAE_seconds":
            per_horse_mean("profile_absolute_error"),
        "source_row_weighted_zero_benchmark_RMSE_seconds":
            sqrt(mean(r["zero_squared_error"] for r in eligible)),
        "source_row_weighted_past_horse_RMSE_seconds":
            sqrt(mean(r["profile_squared_error"] for r in eligible)),
        "not_a_valid_out_of_sample_rider_causal_effect_or_significance":True,
    })
    return measured


def analyze_forward(timed:list[dict])->dict:
    report={}
    for strict_class,key in (
        (False,"same_original_distance_and_first_GPS_marker"),
        (True,"also_same_original_race_Class"),
    ):
        ephemeral=forward_records(timed,strict_class=strict_class)
        report[key]={
            "original_Class_also_required":strict_class,
            "all_dated_past_only_scored_rows_with_known_riders":len(ephemeral),
            "source_cohorts":{
                label:summarize_forward(ephemeral,label,strict_class=strict_class)
                for label in (
                    "new_documented_rider",
                    "previously_seen_documented_rider",
                    "new_documented_rider_and_same_documented_trainer",
                )
            },
        }
    return {
        "status":"POST_HOC_RQ_CHRONOLOGICAL_PAST_ONLY_SOURCE_CHECK_NOT_CAUSAL",
        "fixed_minimum_new_rider_distinct_original_HORSES_IDs":MIN_SCORABLE_HORSES,
        "fixed_minimum_future_observations":MIN_SCORABLE_ROWS,
        "fixed_minimum_future_original_meeting_dates":MIN_FUTURE_SOURCE_DATES,
        "fixed_minimum_original_animal_by_measurement_contexts":
            MIN_SOURCE_CONTEXT_STRATA,
        "source_chronological_evaluation_in_memory_only":True,
        "no_original_IDs_licence_IDs_timing_predictions_or_history_exported":True,
        "not_H1_H2_heritability_actual_final_riders_or_wagering":True,
        "contexts":report,
    }
