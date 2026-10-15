#!/usr/bin/env python3
"""Can the SAME Doomben horse/marker/distance support BOTH horizon scores?

A very narrow post-hoc support audit of 2025 within-year source timings
and independent 2025→2026 source timings, using ONLY original 42
previously locked RQ Doomben dates. Never interpret two separate sample
averages as within-animal time decay. Never publish original individual
horse names/IDs, jockey/trainer licences, interval times or predictions.

Methods fixed in
docs/ecology-rq-doomben-matched-individual-timescale-overlap-lock.md.
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
    collect, verify_lock,
)
from ecology_rq_doomben_within_year_history import (
    score_private as within_score_private,
)
from ecology_rq_doomben_cross_year_forward import (
    _scored_rows_private as across_score_private,
    context as source_context,
)
from ecology_rq_eagle_farm_external_icc import identity_overlap
from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


MIN_MATCHED_HORSE_IDS=20
MIN_FUTURE_2025_ROWS=20
MIN_FUTURE_2026_ROWS=20
MIN_DATES_IN_2025=6
MIN_DATES_IN_2026=3
MIN_MATCHED_STRATA=20
FIXED_MARKER=150.
MIN_GPS_TIMED_PER_RACE=4
PRIMARY_STATUS="HOLD_INSUFFICIENT_SAME_HORSE_TWO_TIMESCALE_CONTEXT_SUPPORT"


def _same_horse_measurement_context(row:dict, *,strict_class:bool)->tuple:
    return (row["horse_id"], source_context(row,strict_class))


def independent_original_exposure_overlap(
    relative:list[dict],*,marker:float=FIXED_MARKER,
    strict_class:bool=False
)->dict:
    """Pure DATE/ID incidence counts, independent of BOTH scoring routines.

    Post-result independent check of the previously observed zero
    overlap between the two scored cohorts. It uses NO outcome values:
    only original source horse IDs, date/year, original first marker,
    official distance and optionally Class.
    """
    if marker!=FIXED_MARKER:
        raise ValueError("HOLD_UNAPPROVED_DIRECT_SOURCE_OVERLAP_MARKER")
    dates_by_context=defaultdict(
        lambda: {"2025":set(),"2026":set()}
    )
    for r in relative:
        if abs(float(r["first_section_marker"])-marker)>1e-6:
            continue
        year=r["day"][:4]
        if year not in ("2025","2026"):
            raise ValueError("HOLD_ORIGINAL_SOURCE_YEAR_NOT_2025_OR_2026")
        key=(r["horse_id"],source_context(r,strict_class))
        if r["day"] in dates_by_context[key][year]:
            raise ValueError("HOLD_DUPLICATE_SAME_HORSE_DATE_FOR_DIRECT_OVERLAP")
        dates_by_context[key][year].add(r["day"])

    has_two_in_2025=set()
    has_one_both=set()
    has_2025_two_2026_one=set()
    has_two_both=set()
    contexts_2025_two_2026_one=0
    contexts_two_both=0
    for (horse,ctx),years in dates_by_context.items():
        n25=len(years["2025"])
        n26=len(years["2026"])
        if n25>=2:
            has_two_in_2025.add(horse)
        if n25>=1 and n26>=1:
            has_one_both.add(horse)
        if n25>=2 and n26>=1:
            has_2025_two_2026_one.add(horse)
            contexts_2025_two_2026_one+=1
        if n25>=2 and n26>=2:
            has_two_both.add(horse)
            contexts_two_both+=1
    return {
        "status":"DIRECT_SOURCE_ID_DATE_EXPOSURE_COUNTS_ONLY_NO_PREDICTION",
        "exact_150m_original_marker":int(marker),
        "exact_source_Class_required":strict_class,
        "source_horse_IDs_2plus_distinct_dates_in_2025_same_context":
            len(has_two_in_2025),
        "source_horse_IDs_1plus_date_each_of_2025_2026_same_context":
            len(has_one_both),
        "source_horse_IDs_2plus_dates_2025_and_1plus_2026_same_context":
            len(has_2025_two_2026_one),
        "horse_context_strata_2plus_2025_and_1plus_2026":
            contexts_2025_two_2026_one,
        "source_horse_IDs_2plus_dates_IN_EACH_year_same_context":
            len(has_two_both),
        "horse_context_strata_2plus_dates_IN_EACH_year":
            contexts_two_both,
        "no_first_GPS_timings_or_individual_IDs_exported":True,
        "not_a_within_individual_year_decay_or_biological_hypothesis_test":True,
        "source_only_support_does_not_force_positive_or_negative_RMSE":True,
    }


def _safe_rmse_by_horse(rows:list[dict], actual:str, pred:str)->float:
    by_horse=defaultdict(list)
    for row in rows:
        by_horse[row["horse_id"]].append(row)
    if not by_horse:
        raise ValueError("HOLD_NO_CROSS_TIMESCALE_COMMON_IDS_FOR_ERROR")
    value=math.sqrt(mean(
        mean((float(v[actual])-float(v[pred]))**2 for v in vals)
        for vals in by_horse.values()
    ))
    if not math.isfinite(value):
        raise ValueError("HOLD_NONFINITE_CROSS_TIMESCALE_RMSE")
    return value


def paired_timescale_support(
    relative:list[dict],*,marker:float=FIXED_MARKER,
    strict_class:bool=False
)->dict:
    """Re-evaluate two existing chronological source analyses privately.

    Preserve the very same HORSES ID AND same exact first GPS marker,
    race distance and optional Class in both sets of scored predictions.
    Both cohorts are separate outcome dates: no inference from the
    difference of their RMSE values about an individual annual change.
    """
    if marker!=FIXED_MARKER:
        raise ValueError("HOLD_UNAPPROVED_POSTHOC_GPS_FIRST_MARKER")

    earlier,_=within_score_private(
        relative,year="2025",marker=marker,strict_class=strict_class
    )
    later,_=across_score_private(
        relative,marker=marker,strict_class=strict_class
    )

    # Recover contextual KEY for scored 2026 original run internally.
    # The source prepare() gate already refuses the same HORSES ID
    # appearing twice on one source day. Assert it again rather
    # than guessing a duplicate horse+date context.
    keyed={}
    for row in relative:
        if not row["day"].startswith("2026-"):
            continue
        if abs(float(row["first_section_marker"])-marker)>1e-6:
            continue
        original=(row["horse_id"],row["day"])
        if original in keyed:
            raise ValueError("HOLD_MULTIPLE_ORIGINAL_RECORDS_ONE_HORSE_2026_DATE")
        keyed[original]=_same_horse_measurement_context(
            row,strict_class=strict_class
        )

    for row in later:
        original=(row["horse_id"],row["day"])
        if original not in keyed:
            raise ValueError("HOLD_CROSSYEAR_SCORE_LOST_ORIGINAL_CONTEXT")
        row["_internal_source_matched_key"]=keyed[original]

    early_keys={r["context"] for r in earlier}
    year_forward_keys={r["_internal_source_matched_key"] for r in later}
    intersection=early_keys & year_forward_keys
    common_2025=[r for r in earlier if r["context"] in intersection]
    common_2026=[
        r for r in later
        if r["_internal_source_matched_key"] in intersection
    ]
    all_2025_ids={r["horse_id"] for r in earlier}
    all_2026_ids={r["horse_id"] for r in later}
    same_id_not_necessarily_same_context=all_2025_ids & all_2026_ids
    common_ids={r["horse_id"] for r in common_2025}
    if common_ids!={r["horse_id"] for r in common_2026}:
        raise ValueError("HOLD_CROSS_TIMESCALE_SOURCE_ID_SET_NOT_IDENTICAL")

    result={
        "status":PRIMARY_STATUS,
        "fixed_original_marker_m":int(marker),
        "exact_original_Class_also_matched":strict_class,
        "original_within_2025_focal_HORSES_IDs":len(all_2025_ids),
        "original_2025_to_2026_focal_HORSES_IDs":len(all_2026_ids),
        "identity_overlap_IGNORING_exact_context_count":len(same_id_not_necessarily_same_context),
        "common_original_HORSES_IDs_with_identical_marker_and_distance_optional_class":
            len(common_ids),
        "common_horse_by_exact_measurement_context_strata":len(intersection),
        "same_HORSES_ID_original_2025_scored_rows":len(common_2025),
        "same_HORSES_ID_original_2026_scored_rows":len(common_2026),
        "distinct_2025_later_meeting_dates":len({r["day"] for r in common_2025}),
        "distinct_2026_later_meeting_dates":len({r["day"] for r in common_2026}),
        "original_record_dates_remain_separate_years":True,
        "all_2025_histories_strictly_prior_to_2025_scored_date":True,
        "all_2026_outcomes_NOT_used_to_fit_2025_historical_profiles":True,
        "same_original_HORSES_IDs_scored_in_both_horizons_if_supported":True,
        "source_relative_GPS_target_is_postrace_conditional_on_measured_field":True,
        "not_a_identified_year_effect_or_within_horse_phenotypic_change":True,
        "no_original_horse_name_ID_or_individual_GPS_outcome_exported":True,
    }
    supported=(
        len(common_ids)>=MIN_MATCHED_HORSE_IDS and
        len(common_2025)>=MIN_FUTURE_2025_ROWS and
        len(common_2026)>=MIN_FUTURE_2026_ROWS and
        len({r["day"] for r in common_2025})>=MIN_DATES_IN_2025 and
        len({r["day"] for r in common_2026})>=MIN_DATES_IN_2026 and
        len(intersection)>=MIN_MATCHED_STRATA
    )
    if not supported:
        return result

    own_2025=_safe_rmse_by_horse(common_2025,"actual","own")
    other_2025=_safe_rmse_by_horse(common_2025,"actual","other")
    own_2026=_safe_rmse_by_horse(common_2026,"observed","own_prediction")
    other_2026=_safe_rmse_by_horse(common_2026,"observed","other_prediction")
    return {
        **result,
        "status":"EXPLORATORY_MATCHED_SOURCE_ID_TIMESCALE_CONTEXTS_NOT_CAUSAL",
        "conditional_equal_ID_weighted_RMSE_seconds":{
            "2025_own_history":own_2025,
            "2025_other_horses_history":other_2025,
            "2025_other_minus_own_gain":other_2025-own_2025,
            "2026_own_2025_history":own_2026,
            "2026_other_horses_2025_history":other_2026,
            "2026_other_minus_own_gain":other_2026-own_2026,
        },
        "do_NOT_interpret_between_year_gain_difference_as_ageing_effect":True,
        "not_a_valid_confidence_interval_significance_or_experiment":True,
    }


def evaluate(*,soap=request_xml,gps=fetch_official,
             source_error_mode:str="record_HOLD")->dict:
    verify_lock()
    if source_error_mode not in ("record_HOLD","raise"):
        raise ValueError("HOLD_INVALID_SOURCE_ERROR_MODE")
    raw,manifest=collect(soap=soap,gps=gps,on_error=source_error_mode)
    clean,identity=identity_overlap(raw)
    if clean:
        relative,peer_info=prepare(
            clean,min_race_telemetry=MIN_GPS_TIMED_PER_RACE
        )
    else:
        relative=[]
        peer_info={"status":"HOLD_NO_ORIGINAL_POSITIVE_GPS_RACE_DATA"}
    successes=sorted(
        d for d,info in manifest.items() if info.get("status")==
        "OFFICIAL_2025_OR_2026_DOOMBEN_SOURCE_ID_GPS_AUDITED"
    )
    failed=sorted(set(LOCKED_DATES)-set(successes))
    if len(successes)+len(failed)!=len(LOCKED_DATES):
        raise ValueError("HOLD_SOURCE_CALENDAR_SUM_NOT_LOCKED")
    result={
        "status":"SOURCE_CONDITIONAL_SAME_HORSE_TIMESCALE_OVERLAP_SUPPORT_CHECK",
        "source":"Racing Queensland public original 42-day Doomben cohort",
        "original_locked_2025_dates":len(DATES_2025),
        "original_locked_2026_dates":len(PREVIOUS_2026_DATES),
        "original_source_dates_successfully_read":len(successes),
        "original_source_dates_HOLD":failed,
        "source_HORSES_roster_and_GPS_fingerprints":manifest,
        "original_ID_consistency_counts_only":identity,
        "original_GPS_peer_field_counts_only":peer_info,
        "exact_150m_marker_distance_overlap":paired_timescale_support(
            relative,marker=FIXED_MARKER,strict_class=False
        ),
        "also_same_original_race_Class_support":paired_timescale_support(
            relative,marker=FIXED_MARKER,strict_class=True
        ),
        "independent_pre_score_direct_same_horse_original_incidence":
            independent_original_exposure_overlap(
                relative,marker=FIXED_MARKER,strict_class=False
            ),
        "independent_pre_score_exact_Class_incidence":
            independent_original_exposure_overlap(
                relative,marker=FIXED_MARKER,strict_class=True
            ),
        "study_WAS_POSTHOC_after_both_original_favorable_unfavorable_results":True,
        "not_a_source_independent_biological_replication":True,
        "NOT_ageing_H1_H2_heritability_personality_or_wagering":True,
        "no_original_animal_ID_name_licence_time_or_predictions_published":True,
    }
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=evaluate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        "status":report["status"],
        "original_success_dates":report["original_source_dates_successfully_read"],
        "original_source_HOLD_dates":report["original_source_dates_HOLD"],
        "matched_150m_exact_distance":report["exact_150m_marker_distance_overlap"],
        "also_same_Class":report["also_same_original_race_Class_support"],
        "direct_incidence":report[
            "independent_pre_score_direct_same_horse_original_incidence"
        ],
        "direct_Class_incidence":report[
            "independent_pre_score_exact_Class_incidence"
        ],
        "no_animal_identifiers_output":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
