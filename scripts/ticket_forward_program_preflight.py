#!/usr/bin/env python3
"""Validate a provisional JRA program against its own strictly scoped contract.

This is *not* an official racecard or prospective scoring input. JRA's published
program is subject to change. Independent non-JRA starter counts are labeled
as indicative, cannot satisfy official day-plan proof and are never used to
freeze a ticket prediction.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

TARGET_DATE = "2026-11-23"
SOURCE_STATUS = "PRELIMINARY_NOT_OFFICIAL_COMPLETE_DAY_CARD_NOT_SERVER_SEALED"
HOLD_STATUS = "HOLD_AWAITING_OFFICIAL_24_CARD_COUNTS_AND_PRE_FIRST_RACE_PROOF"
PROGRAM_TIMES = {
    "福島": ("09:45", "10:15", "10:45", "11:15", "12:05", "12:35",
           "13:05", "13:35", "14:05", "14:40", "15:15", "15:55"),
    "東京": ("10:00", "10:30", "11:00", "11:30", "12:20", "12:50",
           "13:20", "13:50", "14:20", "14:55", "15:30", "16:05"),
}
RACE_CODES = {"福島": "FUKUSHIMA", "東京": "TOKYO"}


def audit_preliminary_program(stage: dict) -> dict:
    if (stage.get("schema_version") != 1 or stage.get("race_date") != TARGET_DATE
            or stage.get("full_program_count") != 24
            or stage.get("official_card_count_confirmed") != 0
            or stage.get("official_page_raw_bytes_archived") is not False
            or stage.get("day_plan_git_server_attested") is not False
            or stage.get("day_universe_status") != HOLD_STATUS
            or stage.get("no_results_used") is not True):
        raise ValueError("stage_attempts_to_claim_real_frozen_data")
    provenance = stage.get("source")
    if (not isinstance(provenance, dict)
            or provenance.get("status") != SOURCE_STATUS
            or provenance.get("official_program_url")
            != "https://jra.jp/keiba/calendar2026/2026/11/1123.html"
            or provenance.get("secondary_runner_counts_url")
            != "https://uma5.com/races/20261123/"):
        raise ValueError("source_provenance_not_separated")
    rows = stage.get("races")
    if not isinstance(rows, list) or len(rows) != 24:
        raise ValueError("not_all_24_planned_races_present")
    observed = set()
    program = {}
    for row in rows:
        if set(row) != {
            "race_id", "venue", "race_number", "scheduled_start_jst",
            "programmed_surface", "programmed_distance_m",
            "third_party_displayed_runner_count",
            "official_current_card_runner_count", "confirmed_official_card_source_url",
        }:
            raise ValueError("unapproved_staging_row_schema")
        if (row["official_current_card_runner_count"] is not None
                or row["confirmed_official_card_source_url"] is not None):
            raise ValueError("unverified_official_card_claim")
        venue, number = row["venue"], row["race_number"]
        if venue not in PROGRAM_TIMES or type(number) is not int or not 1 <= number <= 12:
            raise ValueError("invalid_venue_or_race")
        key = (venue, number)
        expected_id = f"{TARGET_DATE}-{RACE_CODES[venue]}-{number:02d}"
        expected_time = f"{TARGET_DATE}T{PROGRAM_TIMES[venue][number-1]}:00+09:00"
        if (key in observed or row["race_id"] != expected_id
                or row["scheduled_start_jst"] != expected_time):
            raise ValueError("duplicate_or_mismatched_program_race")
        observed.add(key)
        if (row["programmed_surface"] not in {"芝", "ダ", "障"}
                or (venue == "福島" and number == 4) != (row["programmed_surface"] == "障")):
            raise ValueError("obstacle_flat_classification_mismatch")
        if (type(row["programmed_distance_m"]) is not int or
                not 1000 <= row["programmed_distance_m"] <= 3600):
            raise ValueError("invalid_program_distance")
        n = row["third_party_displayed_runner_count"]
        if type(n) is not int or not 1 <= n <= 18:
            raise ValueError("missing_secondary_entrant_count")
        program[key] = row
    if observed != {(venue, number) for venue in PROGRAM_TIMES for number in range(1, 13)}:
        raise ValueError("not_all_24_planned_races_present")
    ordered = sorted(rows, key=lambda r: (
        r["scheduled_start_jst"], r["venue"], r["race_number"]))
    if [r["race_id"] for r in ordered] != [r["race_id"] for r in rows]:
        raise ValueError("staging_rows_not_sorted")
    candidates = [r for r in ordered if r["programmed_surface"] in {"芝", "ダ"}
                  and 9 <= r["third_party_displayed_runner_count"] <= 18]
    expected_top = [r["race_id"] for r in candidates[:10]]
    if expected_top != stage.get("provisional_first_ten_using_third_party_counts"):
        raise ValueError("provisional_selection_does_not_reproduce")
    if len(expected_top) != 10:
        raise ValueError("fewer_than_ten_provisional_candidates")
    plan = [{
        "race_id": r["race_id"], "scheduled_start_jst": r["scheduled_start_jst"],
        "third_party_displayed_runner_count": r["third_party_displayed_runner_count"],
        "nominal_forecast_window_start_jst": (
            datetime.fromisoformat(r["scheduled_start_jst"]) - timedelta(minutes=25)
        ).isoformat(),
        "nominal_forecast_window_end_jst": (
            datetime.fromisoformat(r["scheduled_start_jst"]) - timedelta(minutes=15)
        ).isoformat(),
    } for r in candidates[:10]]
    return {
        "status": HOLD_STATUS,
        "program_full_day_rows": len(rows),
        "program_flat_rows": sum(r["programmed_surface"] in {"芝", "ダ"} for r in rows),
        "program_obstacle_rows": sum(r["programmed_surface"] == "障" for r in rows),
        "provisional_eligible_by_secondary_counts": len(candidates),
        "provisional_first_ten": plan,
        "official_entrant_counts_verified": 0,
        "day_plan_pre_first_race_server_sealed": False,
        "market_snapshots_frozen": 0,
        "future_prospective_scores": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        audit = audit_preliminary_program(
            json.loads(args.staging.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    text = json.dumps(audit, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(json.dumps({"status": audit["status"],
                          "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
