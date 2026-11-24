#!/usr/bin/env python3
"""Read-only 2026-11-23 morning source-drift evidence; never a frozen day plan."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

try:
    from scripts.ticket_forward_program_preflight import audit_preliminary_program
except ModuleNotFoundError:
    from ticket_forward_program_preflight import audit_preliminary_program


def compare(previous: dict, morning: dict, staged: dict, odds: dict) -> dict:
    audit_preliminary_program(staged)
    if (previous.get("status") != "PRE_RACE_JRA_READONLY_NUMBERED_TABLE_AUDIT_NOT_FULL_DAY_SEALED"
            or previous.get("total_card_pages") != 24
            or previous.get("official_card_pages_with_contiguous_numbered_table") != 24
            or morning.get("target_date") != "2026-11-23"
            or odds.get("date") != "2026-11-23"
            or odds.get("page_count") != 2):
        raise ValueError("invalid_morning_comparison_source")
    old = {r["race_id"]: r for r in previous["races"]}
    current = {r["race_id"]: r for r in morning.get("races", [])}
    expected = {r["race_id"] for r in staged["races"]}
    if set(old) != expected or (current and set(current) != expected):
        raise ValueError("partial_or_wrong_day_morning_cards")
    differences = []
    sha_drift = []
    unusable = []
    for rid in sorted(expected):
        prior = old[rid]
        live = current.get(rid)
        if not live or live.get("parse_status") != "OFFICIAL_NUMBER_SEQUENCE_EXTRACTED":
            unusable.append(rid)
            continue
        newcount = live.get("strict_numbered_horse_rows")
        oldcount = prior.get("numbered_card_rows")
        if (type(newcount) is not int or not 1 <= newcount <= 18 or
                type(oldcount) is not int or not 1 <= oldcount <= 18):
            unusable.append(rid)
            continue
        if newcount != oldcount:
            differences.append({"race_id": rid, "previous_numbered_rows": oldcount,
                                "morning_numbered_rows": newcount})
        sha = live.get("raw_page_sha256")
        if not isinstance(sha, str) or not re.fullmatch("[a-f0-9]{64}", sha):
            unusable.append(rid)
        elif sha != prior.get("raw_page_sha256"):
            sha_drift.append(rid)
    markets = {}
    for kind, row in odds["source_pages"].items():
        if row.get("status") != "READ_ONLY_ODDS_STRUCTURE_NOT_FROZEN":
            markets[kind] = {"status": row.get("status"), "updated_at": []}
            continue
        markets[kind] = {
            "status": "EARLY_READONLY_UNFROZEN",
            "updated_at": row.get("upstream_updated_at_jst_detected", []),
            "quote_table_count": row.get("num_html_tables"),
            "raw_sha256": row.get("sha256"),
            "received_at_utc": row.get("observed_at_utc"),
            "win_wide_quote_coverage_not_verified": True,
        }
    return {
        "schema_version": 1,
        "status": "MORNING_SOURCE_DRIFT_NOT_PROSPECTIVE_DAY_SEAL",
        "race_date": "2026-11-23",
        "previous_official_card_count": len(old),
        "morning_official_numbered_card_count": sum(
            r.get("parse_status") == "OFFICIAL_NUMBER_SEQUENCE_EXTRACTED"
            for r in current.values()),
        "numbered_count_changes": differences,
        "changed_page_sha256_race_ids": sha_drift,
        "unavailable_or_unparseable_races": unusable,
        "early_market_source_readiness": markets,
        "candidate_intent_selection_fixed_as_of_previous_night": True,
        "official_active_scratch_status_verified": False,
        "formal_pre_first_start_day_plan_sealed": False,
        "source_visible_updated_at_verified_at_prediction_time": False,
        "full_win_and_wide_quote_board_archived": False,
        "actual_forward_predictions": 0,
        "note": "A digest drift is not evidence of a scratch. JRA row sequence is not necessarily final active roster.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", required=True, type=Path)
    p.add_argument("--previous", required=True, type=Path)
    p.add_argument("--morning", required=True, type=Path)
    p.add_argument("--odds", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    try:
        output = compare(*[
            json.loads(path.read_text(encoding="utf-8"))
            for path in (args.previous, args.morning, args.stage, args.odds)
        ])
    except (ValueError, KeyError, TypeError, OSError) as error:
        p.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        "status": output["status"],
        "cards": output["morning_official_numbered_card_count"],
        "count_changed": len(output["numbered_count_changes"]),
        "page_sha_changed": len(output["changed_page_sha256_race_ids"]),
        "unusable": len(output["unavailable_or_unparseable_races"]),
        "odds_updates": {kind: p["updated_at"]
                         for kind,p in output["early_market_source_readiness"].items()},
        "forward_predictions": 0,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
