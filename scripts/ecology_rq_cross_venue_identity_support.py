#!/usr/bin/env python3
"""Cross-venue original HORSES-ID overlap audit; NO performance-effect estimate.

Reuses the already frozen Cannon Park 12-date and Eagle Farm 12-date
official RQ cohorts. Source rows remain in memory; only counts, date
coverage and anonymous scientific HOLD decisions are emitted.

Same source operator and source-linked ID is not a verified starter,
finisher, biological lineage, or causal animal-specific reaction.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path

from ecology_rq_2026_calendar_overlap import (
    COHORT, LOCKED_RACE_NUMBERS, safe_failure, validate_cohort,
)
from ecology_rq_eagle_farm_external_icc import (
    DATES as EAGLE_DATES, collect as collect_eagle,
    identity_overlap, validate_source_lock as validate_eagle,
)
from ecology_rq_multigoing_h1_preflight import (
    VENUE as CANNON_VENUE, audit_one_day,
)
from ecology_rq_single_race_id_probe import request_xml
from ecology_rq_thoroughbred_sectional_audit import fetch_official


def collect_cannon(*, soap=request_xml, gps=fetch_official,
                   on_source_error="record_HOLD"):
    """Read the locked original Cannon cohort, without fitting ICC."""
    validate_cohort()
    if on_source_error not in ("record_HOLD", "raise"):
        raise ValueError("HOLD_UNAPPROVED_SOURCE_ERROR_MODE")
    rows, manifest = [], {}
    for day, (expected_ground, source) in COHORT.items():
        try:
            details, candidates = audit_one_day(
                day, soap=soap, gps=gps, venue=CANNON_VENUE,
                race_selection=LOCKED_RACE_NUMBERS,
                locked_config={
                    "source": source, "ground_expected": expected_ground,
                    "races": LOCKED_RACE_NUMBERS,
                },
            )
            if details["venue"] != CANNON_VENUE:
                raise ValueError("HOLD_SOURCE_CANNON_VENUE_MISMATCH")
            rows.extend(candidates)
            manifest[day] = {
                "status": "SOURCE_CANNON_PARK_IDS_AND_GPS_AUDITED",
                "positive_first_GPS_candidates": len(candidates),
                "actual_official_races_found": len(
                    details["official_race_numbers_available"]
                ),
                "race_level_ground_used": True,
            }
        except (ValueError, OSError, TimeoutError) as exc:
            if on_source_error == "raise":
                raise
            manifest[day] = safe_failure(exc)
    return rows, manifest


def _attribute(row, field):
    return " ".join(str(row.get(field, "")).split()).casefold()


def _marker(row):
    val = row.get("first_marker_m")
    return round(float(val), 4) if val is not None else None


def summarize_cross_venue(cannon_rows, eagle_rows):
    """Count *genuinely same-ID* cross-site support, never return IDs.

    Same-day positive telemetry for one ID at two distant venues is
    contradictory for a racing animal: exclude that whole ID. Same ID
    with discordant normalized names is excluded. Identical names with
    different IDs never create a link.
    """
    cannon, cs = identity_overlap(cannon_rows)
    eagle, es = identity_overlap(eagle_rows)

    def index(rows):
        result = defaultdict(list)
        for row in rows:
            result[row["horse_id"]].append(row)
        return result

    ci, ei = index(cannon), index(eagle)
    common = set(ci).intersection(ei)
    cross_name_conflicts = {
        h for h in common
        if len({r["horse_name"] for r in ci[h]+ei[h]}) != 1
    }
    impossible_same_day = {
        h for h in common
        if {r["day"] for r in ci[h]}.intersection(
            r["day"] for r in ei[h]
        )
    }
    eligible = common-cross_name_conflicts-impossible_same_day

    # Ambiguous same-name matches are documented but NEVER promoted
    # to the official-ID intersection.
    def names_to_ids(rows):
        d = defaultdict(set)
        for r in rows:
            d[r["horse_name"]].add(r["horse_id"])
        return d

    cn, en = names_to_ids(cannon), names_to_ids(eagle)
    same_name_different_id = sum(
        not cn[n].intersection(en[n]) for n in set(cn).intersection(en)
    )

    shared_marker_ids = set()
    shared_distance_marker_ids = set()
    shared_class_distance_marker_ids = set()
    two_dates_each_marker_ids = set()
    two_dates_each_distance_marker_ids = set()
    for h in eligible:
        crows, erows = ci[h], ei[h]
        cm = {_marker(r) for r in crows if _marker(r) is not None}
        em = {_marker(r) for r in erows if _marker(r) is not None}
        markers = cm.intersection(em)
        if not markers:
            continue
        shared_marker_ids.add(h)
        for marker in markers:
            c_same = [r for r in crows if _marker(r) == marker]
            e_same = [r for r in erows if _marker(r) == marker]
            if (len({r["day"] for r in c_same}) >= 2 and
                    len({r["day"] for r in e_same}) >= 2):
                two_dates_each_marker_ids.add(h)
            cdist = {_attribute(r, "distance") for r in c_same}
            edist = {_attribute(r, "distance") for r in e_same}
            if cdist.intersection(edist):
                shared_distance_marker_ids.add(h)
                for distance in cdist.intersection(edist):
                    cc = [r for r in c_same
                          if _attribute(r, "distance") == distance]
                    ee = [r for r in e_same
                          if _attribute(r, "distance") == distance]
                    if ({_attribute(r, "class") for r in cc}.intersection(
                            _attribute(r, "class") for r in ee)):
                        shared_class_distance_marker_ids.add(h)
                    if (len({r["day"] for r in cc}) >= 2 and
                            len({r["day"] for r in ee}) >= 2):
                        two_dates_each_distance_marker_ids.add(h)

    if not eligible:
        status = "HOLD_NO_VALID_SAME_HORSE_ID_ACROSS_TWO_VENUES"
    elif not shared_marker_ids:
        status = "HOLD_SHARED_HORSE_IDS_BUT_NO_IDENTICAL_FIRST_GPS_MARKER"
    else:
        status = "EXPLORATORY_CROSS_VENUE_ID_AND_MARKER_DATA_SUPPORT_ONLY"
    return {
        "status": status,
        "Cannon_positive_GPS_rows_after_within_venue_name_screen": len(cannon),
        "Eagle_positive_GPS_rows_after_within_venue_name_screen": len(eagle),
        "Cannon_distinct_original_HORSES_IDs": len(ci),
        "Eagle_distinct_original_HORSES_IDs": len(ei),
        "same_numeric_HORSES_ID_seen_at_both_venues_before_cross_screen": len(common),
        "shared_numeric_ID_cross_venue_name_conflicts_blocked":
            len(cross_name_conflicts),
        "shared_numeric_ID_same_day_two_venues_conflicts_blocked":
            len(impossible_same_day),
        "same_name_different_HORSES_ID_never_linked": same_name_different_id,
        "valid_named_original_HORSES_IDs_recorded_at_both_venues": len(eligible),
        "shared_HORSES_IDs_with_any_exact_first_GPS_marker_at_both_venues":
            len(shared_marker_ids),
        "shared_HORSES_IDs_with_exact_first_marker_and_official_distance":
            len(shared_distance_marker_ids),
        "shared_HORSES_IDs_with_exact_marker_distance_and_source_class":
            len(shared_class_distance_marker_ids),
        "shared_HORSES_IDs_with_2plus_independent_dates_per_venue_same_marker":
            len(two_dates_each_marker_ids),
        "shared_HORSES_IDs_with_2plus_dates_per_venue_same_marker_distance":
            len(two_dates_each_distance_marker_ids),
        "source_ID_name_anomalies_within_Cannon_blocked":
            cs["HORSES_IDs_with_different_names_across_dates_blocked"],
        "source_ID_name_anomalies_within_Eagle_blocked":
            es["HORSES_IDs_with_different_names_across_dates_blocked"],
        "shared_marker_alone_does_not_verify_same_segment_definition": True,
        "zero_shared_IDs_would_not_be_a_zero_biological_effect": True,
        "no_raw_horse_names_ids_licences_or_times_exported": True,
        "not_a_ground_reaction_norm_or_social_competition_test": True,
    }


def compare(*, soap=request_xml, gps=fetch_official,
            on_source_error="record_HOLD",
            cannon_reader=collect_cannon, eagle_reader=collect_eagle):
    validate_cohort()
    validate_eagle()
    cannon_rows, cannon_manifest = cannon_reader(
        soap=soap, gps=gps, on_source_error=on_source_error)
    eagle_rows, eagle_manifest = eagle_reader(
        soap=soap, gps=gps, on_source_error=on_source_error)
    c_ok = [d for d, x in cannon_manifest.items()
            if x["status"] == "SOURCE_CANNON_PARK_IDS_AND_GPS_AUDITED"]
    e_ok = [d for d, x in eagle_manifest.items()
            if x["status"] == "SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED"]
    missing_c = sorted(set(COHORT)-set(c_ok))
    missing_e = sorted(set(EAGLE_DATES)-set(e_ok))
    support = summarize_cross_venue(cannon_rows, eagle_rows)
    return {
        "status": ("SOURCE_COHORT_INCOMPLETE_HOLD_CROSS_VENUE_INFERENCE"
                   if missing_c or missing_e else
                   "EXPLORATORY_SOURCE_ID_CROSS_VENUE_AUDIT_NOT_H1_H2"),
        "design": {
            "source": "Racing Queensland official HORSES IDs + positive GPS",
            "Cannon_dates_original_previously_locked": list(COHORT),
            "Eagle_dates_original_previously_locked": list(EAGLE_DATES),
            "Cannon_requested_original_race_numbers": list(LOCKED_RACE_NUMBERS),
            "Eagle_requested_original_race_numbers": list(range(1, 7)),
            "not_a_new_post_outcome_date_or_race_selection": True,
        },
        "Cannon_source_dates_audited": len(c_ok),
        "Eagle_source_dates_audited": len(e_ok),
        "Cannon_source_dates_on_HOLD": missing_c,
        "Eagle_source_dates_on_HOLD": missing_e,
        "source_cross_venue_overlap": support,
        "same_operator_individual_ID_does_not_validate_actual_starter": True,
        "not_identified": [
            "Identical biological GPS interval definition across venues",
            "Valid cross-venue ICC/horse-by-venue interaction estimate",
            "Complete official starters, disqualifications or finish times",
            "Environmental H1 random slope and social competition H2",
            "Independent-source replication and heritability",
        ],
        "no_raw_individual_data_or_predictions_exported": True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--strict-source-errors", action="store_true")
    args = p.parse_args()
    output = compare(
        on_source_error="raise" if args.strict_source_errors else "record_HOLD"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status": output["status"],
        "Cannon_audited_days": output["Cannon_source_dates_audited"],
        "Eagle_audited_days": output["Eagle_source_dates_audited"],
        "cross_venue": output["source_cross_venue_overlap"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
