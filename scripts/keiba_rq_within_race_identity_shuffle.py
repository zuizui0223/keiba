#!/usr/bin/env python3
"""Within-original-GPS-race horse-history permutation, aggregate-only.

Retrospective source-conditional negative control for Cannon Park 2026
original locked 12 dates. The eligibility, context and n/(n+2)
shrinkage are EXACTLY the previously frozen main-ecology historical
comparator design (including documented NEW jockey-source IDs).
Only historical GPS observations are randomly reassigned to horse
identities WITHIN THE SAME OBSERVED RACE, preserving every date,
original race, horse field, GPS marker, distance, class and target
eligibility. The target observed real horse-relative time is unchanged.

Strictly earlier source dates only are used for profile predictions.
The same 44/22 real future rows are scored in both real and shuffled
conditions; after scoring a date, the date's randomized source rows
can contribute to predictions on later dates.

This IS NOT a causal shuffle of real competitor interactions, genetics,
rider assignment, or socially learned behavior. Horse-label
exchangeability is not established in the selected source cohort.
Null percentiles are not a preregistered population p-value/CI.
Never write original IDs, GPS seconds or private predictions to JSON.
"""
from __future__ import annotations

from collections import defaultdict
from math import sqrt
from statistics import mean
import random

from ecology_rq_forward_alternative_history import (
    matched_source_rows_private, _context, _paired_score
)

STATUS="RETROSPECTIVE_SAME_RQ_SOURCE_WITHIN_RACE_HISTORY_IDENTITY_NULL"


def _score_equal_horse(candidates,predictions):
    groups=defaultdict(list)
    if len(candidates)!=len(predictions):
        raise ValueError("HOLD_MISMATCHED_OBSERVED_NULL_CANDIDATES")
    for r,yhat in zip(candidates,predictions):
        if not isinstance(yhat,(float,int)):
            raise ValueError("HOLD_INVALID_MODEL_FORECAST")
        groups[r["horse_id"]].append((r["observed"]-float(yhat))**2)
    if not groups:
        raise ValueError("HOLD_NO_SAME_HORSE_PROFILES")
    return sqrt(mean(mean(errs) for errs in groups.values()))


def _forecast_historical(timed,candidates,strict_class,assignment):
    """Only strictly earlier dates; never reselect the target set."""
    by_day=defaultdict(list)
    for row in timed:
        by_day[str(row["day"])].append(row)
    wanted=defaultdict(list)
    for i,row in enumerate(candidates):
        wanted[str(row["day"])].append((i,row))
    if set(wanted)-set(by_day):
        raise ValueError("HOLD_NULL_PREDICTION_TARGET_NOT_IN_SOURCE")
    past=defaultdict(list)
    pred=[None]*len(candidates)
    for day in sorted(by_day):
        for index,r in wanted.get(day,[]):
            horse,context=r["context"]
            key=(horse,context)
            values=past.get(key,[])
            if not values:
                raise ValueError("HOLD_NULL_SHUFFLE_REMOVED_MATCHED_HORSE_HISTORY")
            # Already frozen earlier by the original main ecology study.
            n=len(values)
            pred[index]=n/(n+2)*mean(values)
        for r in by_day[day]:
            ctx=_context(r,strict_class=strict_class)
            key=(r["horse_id"],ctx)
            historic=(r["day"],r["race_number"],r["horse_id"])
            if historic not in assignment:
                raise ValueError("HOLD_NULL_HISTORY_RACE_IDENTITY_NOT_MATCHED")
            past[key].append(assignment[historic])
    if any(v is None for v in pred):
        raise ValueError("HOLD_NULL_MISSING_PREDICTION")
    return pred


def _remap_original_gps(timed,rng):
    by_race=defaultdict(list)
    for row in timed:
        key=(str(row["day"]),row["race_number"])
        by_race[key].append(row)
    remapped={}
    for (_,group) in sorted(by_race.items()):
        # All horses have the same marker and distance inside each
        # GPS race (already gated by source_timed_panel).
        values=[float(x["relative_seconds"]) for x in group]
        rng.shuffle(values)
        for row,value in zip(group,values):
            key=(row["day"],row["race_number"],row["horse_id"])
            if key in remapped:
                raise ValueError("HOLD_DUPLICATE_ORIGINAL_TIMED_HORSE_RECORD")
            remapped[key]=value
    if len(remapped)!=len(timed):
        raise ValueError("HOLD_PERMUTATION_GPS_HORSE_COUNT_DRIFT")
    return remapped


def identity_history_shuffle(timed, *, strict_class=False,
                             permutations=299,seed=20261026):
    if (type(strict_class) is not bool or
            type(permutations) is not int or not 49<=permutations<=2000
            or type(seed) is not int):
        raise ValueError("HOLD_NULL_DESIGN_NOT_LOCKED")
    # This frozen eligibility is allowed to depend on the original
    # source labels and histories, NOT on random shuffle results.
    candidates,readiness=matched_source_rows_private(
        timed,strict_class=strict_class)
    original=_paired_score(candidates,"context_prediction")
    base={
       "design":"previously_locked_new_documented_Jockey_source_ID_comparator",
       "status":original["status"],
       "race_class_also_matched":strict_class,
       "matched_chronological_future_source_rows":
           original["matched_chronological_future_source_rows"],
       "distinct_original_HORSES_IDs":
           original["distinct_original_HORSES_IDs"],
       "distinct_future_source_dates":
           original["distinct_future_original_source_dates"],
       "no_identifiers_individual_GPS_or_predictions_exported":True,
       "same_GPS_field_context_and_future_denominator_in_all_nulls":True,
       "null_is_not_verified_exchangeable_causal_randomization":True,
       "not_a_prospective_new_JRA_market_or_absolute_GPS_prediction":True,
       "no_population_p_value_or_confidence_interval":True,
    }
    if original["status"].startswith("HOLD_"):
        return {**base,"status":"HOLD_ORIGINAL_CONTEXT_DID_NOT_PASS_EVIDENCE_GATE"}
    selected=[r for r in candidates if r["context_prediction"] is not None]
    if len(selected)!=original["matched_chronological_future_source_rows"]:
        raise AssertionError("HOLD_TARGET_DENOMINATOR_DRIFT")
    true_assignment={(r["day"],r["race_number"],r["horse_id"]):
                     float(r["relative_seconds"]) for r in timed}
    if len(true_assignment)!=len(timed):
        raise ValueError("HOLD_REPEAT_ORIGINAL_GPS_ROW")
    computed=_forecast_historical(
        timed,selected,strict_class,true_assignment)
    for r,pred in zip(selected,computed):
        if abs(pred-r["horse_prediction"])>1e-12:
            raise AssertionError("HOLD_FAILED_ORIGINAL_SOURCE_CHRONOLOGICAL_PROFILE_REPLAY")
    observed_rmse=_score_equal_horse(selected,computed)
    reference=original["equal_HORSES_weighted_past_horse_RMSE_sec"]
    if abs(reference-observed_rmse)>1e-11:
        raise AssertionError("HOLD_ORIGINAL_PROFILE_SCORING_NOT_REPRODUCED")
    rng=random.Random(seed)
    null=[]
    for _ in range(permutations):
        shuffled=_remap_original_gps(timed,rng)
        shuffled_preds=_forecast_historical(
            timed,selected,strict_class,shuffled)
        null.append(_score_equal_horse(selected,shuffled_preds))
    null_sorted=sorted(null)
    def at(fraction):
        return null_sorted[int((len(null_sorted)-1)*fraction)]
    null_better_or_equal=sum(v<=observed_rmse for v in null)
    return {
       **base,
       "status":STATUS,
       "previously_locked_context_history_real_source_rmse_seconds":
           observed_rmse,
       "previously_locked_other_horse_same_context_rmse_seconds":
           original["equal_HORSES_weighted_past_other_horse_baseline_RMSE_sec"],
       "new_within_race_history_identity_null_permutations":permutations,
       "null_seed_for_code_reproducibility_only":seed,
       "null_mean_equal_horse_RMSE_seconds":mean(null),
       "null_rmse_q05_q50_q95_seconds":[at(.05),at(.50),at(.95)],
       "fraction_synthetic_history_label_null_better_or_equal_real":
           null_better_or_equal/len(null),
       "descriptive_real_minus_null_mean_RMSE_seconds":
           observed_rmse-mean(null),
       "no_origin_source_horse_row_or_jockey_ID_exposed":True,
       "null_label_exchangeability_untested":True,
       "never_claim_population_significance_from_this_exploratory_null":True,
       "original_source_selection_not_fully_reproduced_if_manifest_drift":True,
    }
