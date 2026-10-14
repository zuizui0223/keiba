#!/usr/bin/env python3
"""Test whether past focal horse history beats strictly earlier OTHER-horse history.

Original prelocked 12-date Cannon Park source; exploratory post-hoc control,
not an independent study or valid causal decomposition of horse/trainer/rider.
Input is an in-memory original HORSES-ID/first GPS relative-time panel;
returned report contains aggregates only. See frozen design in
docs/ecology-rq-forward-alternative-history-lock.md.
"""
from __future__ import annotations

from collections import defaultdict
from math import sqrt
from statistics import mean

from ecology_rq_rider_forward_check import (
    MIN_SCORABLE_HORSES, MIN_SCORABLE_ROWS, MIN_FUTURE_SOURCE_DATES,
    MIN_SOURCE_CONTEXT_STRATA, FIXED_SHRINKAGE_PSEUDO_COUNT,
)


def _context(row:dict, strict_class:bool)->tuple:
    return (str(row["distance"]),float(row["marker"]),
            row["race_class"] if strict_class else None)


def _fixed_profile(earlier:list[dict])->float:
    """Original fixed n/(n+2), no model tuning on future outcomes."""
    n=len(earlier)
    if n==0:
        raise ValueError("HOLD_NO_PREVIOUS_HISTORY_FOR_ROLE_CONTEXT_PREDICTOR")
    return n/(n+FIXED_SHRINKAGE_PSEUDO_COUNT)*mean(
        float(r["relative_seconds"]) for r in earlier)


def matched_source_rows_private(
    timed:list[dict],*,strict_class:bool=False
)->tuple[list[dict],dict]:
    """Never export rows of this function; use audit_other_horse_baselines.

    Score a date BEFORE appending any of its own rows to training history.
    Never use focal horse's previous rows as "other-horse" controls.
    """
    by_day=defaultdict(list)
    horse_on_day=set()
    for row in timed:
        key=(str(row["horse_id"]),str(row["day"]))
        if key in horse_on_day:
            raise ValueError("HOLD_DUPLICATE_HORSES_ID_WITHIN_ORIGINAL_DATE")
        horse_on_day.add(key)
        by_day[row["day"]].append(row)

    past_by_horse=defaultdict(list)
    past_by_context=defaultdict(list)
    past_by_trainer=defaultdict(list)
    past_by_rider=defaultdict(list)
    candidates=[]
    for day in sorted(by_day):
        today=by_day[day]
        for row in today:
            h=row["horse_id"]
            context=_context(row,strict_class)
            past=past_by_horse.get((h,context),[])
            if not past:
                continue
            earlier_documented_jockeys={
                p["jockey_id"] for p in past if p["jockey_id"] is not None
            }
            current_jockey=row.get("jockey_id")
            if (current_jockey is None or
                not earlier_documented_jockeys or
                current_jockey in earlier_documented_jockeys):
                continue
            if not all(x["day"] < day for x in past):
                raise ValueError("HOLD_FUTURE_OR_SAME_DATE_HORSE_HISTORY")

            past_context=[
                x for x in past_by_context.get(context,[])
                if x["horse_id"]!=h
            ]
            current_trainer=row.get("trainer_id")
            past_trainer=[
                x for x in past_by_trainer.get((current_trainer,context),[])
                if x["horse_id"]!=h
            ] if current_trainer is not None else []
            past_jockey=[
                x for x in past_by_rider.get((current_jockey,context),[])
                if x["horse_id"]!=h
            ]
            if not all(x["day"]<day for seq in
                       (past_context,past_trainer,past_jockey) for x in seq):
                raise ValueError("HOLD_FUTURE_CONTEXT_OR_ROLE_REFERENCE")

            observed=float(row["relative_seconds"])
            # Ephemeral source IDs and outcomes are intentionally kept
            # only inside this process. Never JSON-serialize candidates.
            candidates.append({
                "horse_id":h,
                "context":(h,context),
                "day":day,
                "observed":observed,
                "zero_prediction":0.,
                "horse_prediction":_fixed_profile(past),
                "context_prediction":(
                    _fixed_profile(past_context) if past_context else None),
                "trainer_other_prediction":(
                    _fixed_profile(past_trainer) if past_trainer else None),
                "jockey_other_prediction":(
                    _fixed_profile(past_jockey) if past_jockey else None),
                "earlier_horse_observations":len(past),
                "earlier_different_horse_context_observations":len(past_context),
                "earlier_different_horse_trainer_observations":len(past_trainer),
                "earlier_different_horse_jockey_observations":len(past_jockey),
            })
        # Crucially add the ENTIRE test date only AFTER all prediction.
        for row in today:
            context=_context(row,strict_class)
            past_by_horse[(row["horse_id"],context)].append(row)
            past_by_context[context].append(row)
            if row.get("trainer_id") is not None:
                past_by_trainer[(row["trainer_id"],context)].append(row)
            if row.get("jockey_id") is not None:
                past_by_rider[(row["jockey_id"],context)].append(row)

    return candidates,{
        "new_documented_jockey_future_rows_prior_to_alternative_baseline_gate":
            len(candidates),
        "new_documented_jockey_distinct_HORSES_IDs_prior_to_alternative_gate":
            len({r["horse_id"] for r in candidates}),
        "future_rows_with_prior_other_horse_context":sum(
            r["context_prediction"] is not None for r in candidates),
        "future_rows_with_prior_other_horse_same_trainer":sum(
            r["trainer_other_prediction"] is not None for r in candidates),
        "future_rows_with_prior_other_horse_same_jockey":sum(
            r["jockey_other_prediction"] is not None for r in candidates),
        "prior_roles_are_documented_not_verified_actual_postrace":True,
        "all_training_dates_strictly_earlier_than_prediction_date":True,
        "other_horse_role_controls_exclude_focal_HORSES_ID":True,
    }


def _paired_score(private_rows:list[dict], competitor:str)->dict:
    if competitor not in (
        "context_prediction","trainer_other_prediction","jockey_other_prediction"
    ):
        raise ValueError("HOLD_UNAPPROVED_HISTORICAL_COMPARATOR")
    selected=[r for r in private_rows if r[competitor] is not None]
    by_horse=defaultdict(list)
    for row in selected:
        by_horse[row["horse_id"]].append(row)
    n_dates=len({r["day"] for r in selected})
    n_contexts=len({r["context"] for r in selected})
    status="HOLD_INSUFFICIENT_MATCHED_HORSE_AND_OTHER_HORSE_HISTORIES"
    res={
        "status":status,
        "distinct_original_HORSES_IDs":len(by_horse),
        "matched_chronological_future_source_rows":len(selected),
        "distinct_future_original_source_dates":n_dates,
        "distinct_original_horse_by_matching_contexts":n_contexts,
        "same_future_rows_for_each_compared_predictor":True,
        "conditional_on_GPS_positive_and_documented_Jockey_ID":True,
        "no_original_HORSES_Jockey_Trainer_IDs_or_individual_outcomes_exported":True,
    }
    if not (len(by_horse)>=MIN_SCORABLE_HORSES
            and len(selected)>=MIN_SCORABLE_ROWS
            and n_dates>=MIN_FUTURE_SOURCE_DATES
            and n_contexts>=MIN_SOURCE_CONTEXT_STRATA):
        return res

    def mse_equal_horse(field:str)->float:
        return mean(
            mean((row["observed"]-row[field])**2 for row in grp)
            for grp in by_horse.values()
        )
    def mae_equal_horse(field:str)->float:
        return mean(
            mean(abs(row["observed"]-row[field]) for row in grp)
            for grp in by_horse.values()
        )
    names=("zero_prediction","horse_prediction",competitor)
    e_rmse={key:sqrt(mse_equal_horse(key)) for key in names}
    e_mae={key:mae_equal_horse(key) for key in names}
    row_rmse={
        key:sqrt(mean((row["observed"]-row[key])**2 for row in selected))
        for key in names
    }
    res.update({
        "status":"EXPLORATORY_IDENTICAL_FUTURE_HORSES_ROLE_CONTEXT_COMPARISON_ONLY",
        "equal_HORSES_weighted_zero_baseline_RMSE_sec":e_rmse["zero_prediction"],
        "equal_HORSES_weighted_past_horse_RMSE_sec":e_rmse["horse_prediction"],
        "equal_HORSES_weighted_past_other_horse_baseline_RMSE_sec":
            e_rmse[competitor],
        "zero_minus_horse_RMSE_sec":e_rmse["zero_prediction"]-e_rmse["horse_prediction"],
        "past_other_horse_minus_focal_horse_RMSE_sec":
            e_rmse[competitor]-e_rmse["horse_prediction"],
        "equal_HORSES_weighted_zero_baseline_MAE_sec":e_mae["zero_prediction"],
        "equal_HORSES_weighted_past_horse_MAE_sec":e_mae["horse_prediction"],
        "equal_HORSES_weighted_other_horse_baseline_MAE_sec":e_mae[competitor],
        "source_row_weighted_zero_baseline_RMSE_sec":row_rmse["zero_prediction"],
        "source_row_weighted_past_horse_RMSE_sec":row_rmse["horse_prediction"],
        "source_row_weighted_past_other_horse_RMSE_sec":row_rmse[competitor],
        "post_hoc_selected_rider_model_not_CI_p_value_or_causal_decomposition":True,
    })
    return res


def audit_other_horse_baselines(timed:list[dict])->dict:
    analyses={}
    for strict_class,key in (
        (False,"same_official_distance_and_exact_GPS_marker"),
        (True,"also_same_original_race_Class"),
    ):
        internal,readiness=matched_source_rows_private(
            timed,strict_class=strict_class)
        analyses[key]={
            "source_readiness_counts_only":readiness,
            "identical_scored_future_records":{
                "historical_other_horses_same_context":
                    _paired_score(internal,"context_prediction"),
                "historical_other_horses_same_documented_trainer":
                    _paired_score(internal,"trainer_other_prediction"),
                "historical_other_horses_same_documented_new_jockey":
                    _paired_score(internal,"jockey_other_prediction"),
            },
            "source_race_Class_also_matched":strict_class,
        }
    return {
        "status":"POST_HOC_SOURCE_CONDITIONAL_HORSE_VS_OTHER_HORSE_HISTORY_COMPARATORS",
        "previously_locked_12_date_Cannon_population_only":True,
        "strictly_earlier_date_train_then_update":True,
        "same_fixed_n_over_n_plus_2_history_shrinkage_for_all_models":True,
        "all_comparisons_matched_future_observations_not_subgroup_causality":True,
        "source_race_relative_GPS_target_is_postrace_not_betting":True,
        "not_starter_qualified_rider_verified_personality_heritability_or_H1_H2":True,
        "no_original_horse_rider_trainer_ID_or_row_level_output":True,
        "contexts":analyses,
    }
