#!/usr/bin/env python3
"""Calendar-complete 2026 Cannon Park H1 overlap audit; original public data.

SOURCE DESIGN (frozen 2026-10-13, before the seven added dates' ID overlap):
All 12 Cannon Park original 2026 sectional-CSV dates through 2026-10-13,
up to Race 1-8 per meeting, never actual outcome-driven subsampling.

An official HORSES-ID reappearance and positive *first GPS interval*
is a DATA-SUPPORT observation, not proof of verified starting/finishing,
nor an H1 reaction norm. No individual horse names, IDs, raw GPS,
or positive/negative first-section effect estimates are exported.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from ecology_rq_multigoing_h1_preflight import (
    ALL_EIGHT_RACES, audit_one_day,
    SELECTED as PREVIOUS_FIVE_DATES,
)
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


# Locked BEFORE inspecting the seven additional dates' individual ID overlaps.
# Existing five meetings are retained without alteration.
COHORT = {
    "2026-02-16": ("Heavy", "20260216-cairns"),
    "2026-03-12": ("Heavy", "20260312-cairns"),
    "2026-03-26": ("Heavy", "20260326-cairns"),
    "2026-04-04": ("Heavy", "20260404-cairns"),
    "2026-04-09": ("Soft", "20260409-cairns"),
    "2026-05-15": ("Heavy", "20260515-cairns"),
    "2026-05-29": ("Soft", "20260529-cairns"),
    "2026-07-23": ("Soft", "20260723-cairns"),
    "2026-08-22": ("Soft", "20260822-cairns"),
    "2026-08-28": ("Good", "20260828-cairns"),
    "2026-08-29": ("Good", "20260829-cairns"),
    "2026-10-11": ("Good", "20261011-cairns"),
}
LOCKED_DATES = tuple(COHORT)
LOCKED_RACE_NUMBERS = ALL_EIGHT_RACES
NEW_DATES = tuple(d for d in COHORT if d not in PREVIOUS_FIVE_DATES)


def validate_cohort() -> None:
    if (len(COHORT) != 12 or len(NEW_DATES) != 7 or
            len(PREVIOUS_FIVE_DATES) != 5 or
            LOCKED_RACE_NUMBERS != tuple(range(1, 9)) or
            LOCKED_DATES != tuple(sorted(LOCKED_DATES))):
        raise ValueError("HOLD_LOCKED_COHORT_CONFIG_CHANGED")
    if set(PREVIOUS_FIVE_DATES) - set(COHORT):
        raise ValueError("HOLD_PREVIOUS_DATA_DATES_DROPPED")
    for day, old in PREVIOUS_FIVE_DATES.items():
        if (COHORT[day][0] != old["ground_expected"] or
                COHORT[day][1] != old["source"]):
            raise ValueError("HOLD_PRIOR_FIVE_DATA_ORIGIN_CHANGED")


def safe_failure(exc: Exception) -> dict:
    # Omit raw exception string: a third-party or future service may
    # include an individual name or ID in its error response.
    msg = str(exc).split(":", 1)[0]
    code = msg if msg.startswith("HOLD_") and len(msg) < 95 else "HOLD_SOURCE_REVIEW_REQUIRED"
    return {"status": "HOLD_DATE_SOURCE_NOT_RECONCILED",
            "error_code": code, "error_type": type(exc).__name__,
            "not_counted_as_zero_participation": True}


def overlap_support(rows: list[dict]) -> dict:
    animal = defaultdict(list)
    for row in rows:
        animal[row["horse_id"]].append(row)

    changed_name_count = 0
    repeated = []
    eligible_animals = []
    for horse_id, records in animal.items():
        if len({r["horse_name"] for r in records}) > 1:
            changed_name_count += 1
            continue
        eligible_animals.append(records)
        if len({r["day"] for r in records}) >= 2:
            repeated.append(records)

    def split_ground(rows):
        good = [r for r in rows if r["ground"] == "Good"]
        wet = [r for r in rows if r["ground"] in ("Soft", "Heavy")]
        return good, wet

    cross = [
        series for series in repeated
        if all(split_ground(series))
    ]
    repeated_by_ground = {
        "Good_and_Soft": sum(any(r["ground"]=="Soft" for r in seq) for seq in cross),
        "Good_and_Heavy": sum(any(r["ground"]=="Heavy" for r in seq) for seq in cross),
    }

    def stratified(include_class: bool) -> dict:
        # Units: horse ID × official distance × first GPS distance marker
        # and, optionally, original official race Class label.
        comparable = []
        for rows_animal in eligible_animals:
            strata = defaultdict(list)
            for r in rows_animal:
                key = (
                    r["distance"],
                    round(r["first_marker_m"], 4),
                    r["class"] if include_class else None,
                )
                strata[key].append(r)
            for sample in strata.values():
                gd, wd = split_ground(sample)
                if not gd or not wd:
                    continue
                unique_gd = len({r["day"] for r in gd})
                unique_wd = len({r["day"] for r in wd})
                comparable.append({
                    "id": sample[0]["horse_id"],
                    "n_good": unique_gd,
                    "n_wet": unique_wd,
                    "n_good_source_rows": len(gd),
                    "n_wet_source_rows": len(wd),
                    "first_section_marker_m": sample[0]["first_marker_m"],
                })
        eligible = [x for x in comparable
                    if x["n_good"] >= 2 and x["n_wet"] >= 2]
        return {
            "horse_IDs_with_at_least_one_Good_and_wet_first_section_in_matching_stratum":
                len({s["id"] for s in comparable}),
            "horse_by_stratum_Good_and_wet_comparisons": len(comparable),
            "horse_IDs_with_2plus_independent_dates_each_Good_and_wet":
                len({s["id"] for s in eligible}),
            "horse_by_stratum_with_2plus_independent_dates_each_Good_and_wet":
                len(eligible),
            "n_first_section_measurements_is_nothing_like_verified_full_distance_finish_time": True,
            "a_matching_class_label_is_not_a_matching_age_weight_jockey_or_fitness": True,
        }

    out = {
        "positive_first_section_id_linked_candidate_rows": len(rows),
        "distinct_HORSES_internal_IDs_with_positive_first_GPS_in_sample":
            len(animal),
        "HORSES_IDs_with_inconsistent_names_across_dates_BLOCKED":
            changed_name_count,
        "stable_name_HORSES_IDs_on_two_or_more_original_dates":
            len(repeated),
        "stable_name_HORSES_IDs_with_both_Good_and_nonGood":
            len(cross),
        "ground_overlap_categories_are_not_disjoint":
            repeated_by_ground,
        "same_official_distance_and_first_section_marker": stratified(False),
        "same_official_distance_first_section_marker_and_class": stratified(True),
        "strict_cohort_is_a_statistical_power_calculation": False,
    }
    return out


def compare(
    *,
    soap=request_xml,
    gps=fetch_official,
    warn_on_source_errors=True,
) -> dict:
    validate_cohort()
    data = []
    manifest = {}
    for day, (ground, filekey) in COHORT.items():
        cfg = {
            "source": filekey, "ground_expected": ground,
            "races": LOCKED_RACE_NUMBERS,
        }
        try:
            audit, candidates = audit_one_day(
                day, soap=soap, gps=gps,
                locked_config=cfg,
                race_selection=LOCKED_RACE_NUMBERS,
            )
            if audit["ground_disagreeing_with_page"]:
                # Hold the entire source date; different official
                # race ground labels need resolution prior to pooling.
                manifest[day] = {
                    "status": "HOLD_MEETING_RACE_GROUND_DISAGREEMENT",
                    "ground_label_expected": ground,
                    "official_race_labels": audit["actual_official_ground_labels"],
                    "source_hashes": audit["source_hashes"],
                    "eligible_rows_excluded_not_automatically_zero": len(candidates),
                }
                continue
            manifest[day] = {
                "status": "SOURCE_DATE_READ_AND_ID_GPS_MATCHED",
                "meeting_page_ground": ground,
                "official_races_returned": len(audit["official_race_numbers_available"]),
                "official_race_numbers_missing_from_requested_1_to_8":
                    audit["missing_official_race_numbers"],
                "official_race_ground_labels": audit["actual_official_ground_labels"],
                "official_race_class_counts": audit["official_race_class_labels"],
                "official_race_distance_counts": audit["official_race_distances"],
                "nominee_horse_list_records": audit["api_horse_row_count"],
                "candidate_ID_linked_positive_first_GPS_rows":
                    audit["eligible_official_ID_matched_first_section_rows"],
                "same_day_duplicate_name_candidate_rows":
                    audit["candidate_rows_with_same_day_duplicate_gps_name"],
                "official_IDs_listed_in_multiple_races_same_day":
                    audit["official_ids_listed_more_than_once_on_date"],
                "source_hashes": audit["source_hashes"],
                "all_horse_names_ids_raw_intervals_withheld": True,
            }
            data.extend(candidates)
        except (ValueError, OSError, TimeoutError) as exc:
            if not warn_on_source_errors:
                raise
            manifest[day] = safe_failure(exc)

    support = overlap_support(data)
    included = [
        d for d, info in manifest.items()
        if info["status"] == "SOURCE_DATE_READ_AND_ID_GPS_MATCHED"
    ]
    excluded = sorted(set(LOCKED_DATES)-set(included))
    if len(included) < 2:
        status = "HOLD_FEWER_THAN_TWO_ORIGINAL_SOURCE_DATES"
    else:
        status = "REAL_EQUINE_2026_CALENDAR_SOURCE_OVERLAP_NOT_H1_H2_EFFECT"
    return {
        "status": status,
        "source": "Racing Queensland original HORSES IDs + sectionals",
        "temporal_cohort": {
            "calendar_selection_doc": "docs/ecology-rq-2026-calendar-cohort-lock.md",
            "all_twelve_source_dates_locked_before_seven_new_ID_OVERLAP": True,
            "this_is_not_prospective_hypothesis_preregistration": True,
            "prior_five_source_dates_inspected_before_calendar_lock": True,
            "calendar_dates_requested": list(LOCKED_DATES),
            "race_numbers_requested_per_meeting": list(LOCKED_RACE_NUMBERS),
            "new_source_dates": list(NEW_DATES),
            "source_dates_successful": included,
            "source_dates_HOLD": excluded,
            "all_missing_requested_race_IDs_are_recorded_not_guessed": True,
        },
        "date_scoped_source_manifest": manifest,
        "support": support,
        "actual_confirmed_starter_and_finish_status_verified": False,
        "official_full_race_individual_finish_times_verified": False,
        "ground_effect_or_random_slope_variance_fitted": False,
        "competitor_context_H2_fitted": False,
        "no_raw_runner_names_IDs_or_source_telemetry_output": True,
        "limitations": [
            "Even 12 dates and up to eight races per day cannot identify causal ground effects from nonrandom race entries.",
            "Original numeric HORSES IDs may include nominated/nonstarting horses; positive GPS is telemetry not a confirmed final result.",
            "Horse/jockey/age/weight/trainer, environmental changes and race course maintenance are not jointly adjusted.",
            "Original race Class field is often coarse and does not fully control race competition quality.",
            "H1 is a within-animal variance of environment reaction slopes; overlap counts are NOT slope or variance estimates.",
            "One missing official date/race is recorded as missing data, never zero response or exclusion based on an observed performance outcome.",
            "Repeated raw first-section times are not verified whole-course individual finish times.",
            "This is a source/data-readiness assessment using observed exposures; all scientific effect results remain HOLD.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--strict-source-errors", action="store_true")
    args = p.parse_args()
    result = compare(warn_on_source_errors=not args.strict_source_errors)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "successful_days": len(result["temporal_cohort"]["source_dates_successful"]),
        "hold_days": result["temporal_cohort"]["source_dates_HOLD"],
        "support": result["support"],
    }, ensure_ascii=False))


if __name__=="__main__":
    main()
