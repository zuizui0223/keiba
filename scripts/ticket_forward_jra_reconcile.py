#!/usr/bin/env python3
"""Reconcile all 24 JRA official numbered-card rows with provisional racing program.

The JRA card table has horse-number rows; this is stronger than unverified
third-party "runner count", but is NOT a certified post-scratch active roster.
The raw HTML is not publicly redistributed. A GitHub Actions source hash and
URL alone cannot certify exact source-to-JSON parsing or formal preregistration.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

try:
    from scripts.ticket_forward_program_preflight import (
        HOLD_STATUS, audit_preliminary_program
    )
    from scripts.ticket_forward_jra_full_day_readonly import card_key
except ModuleNotFoundError:
    from ticket_forward_program_preflight import (
        HOLD_STATUS, audit_preliminary_program
    )
    from ticket_forward_jra_full_day_readonly import card_key


def reconcile(stage: dict, raw_meta: dict) -> dict:
    plan = audit_preliminary_program(stage)
    if plan["status"] != HOLD_STATUS:
        raise ValueError("provisional_stage_contract_changed")
    if (
        raw_meta.get("schema_version") != 1 or raw_meta.get("date") != stage["race_date"]
        or raw_meta.get("status") != "PRE_RACE_JRA_READONLY_NUMBERED_TABLE_AUDIT_NOT_FULL_DAY_SEALED"
        or raw_meta.get("official_card_pages_with_contiguous_numbered_table") != 24
        or raw_meta.get("total_card_pages") != 24
        or raw_meta.get("official_scratch_status_verified") is not False
        or raw_meta.get("official_day_schedule_server_sealed") is not False
        or raw_meta.get("complete_win_wide_odds_frozen") is not False
        or raw_meta.get("forward_scored_races") != 0
        or raw_meta.get("raw_html_redistributed") is not False
    ):
        raise ValueError("official_card_meta_claims_unobserved_prospective_state")
    rows=raw_meta.get("races")
    if not isinstance(rows,list) or len(rows)!=24:
        raise ValueError("incomplete_JRA_card_metadata")
    stage_rows={r["race_id"]:r for r in stage["races"]}
    if len(stage_rows)!=24:
        raise ValueError("staging_duplicate_race")
    seen=set()
    counts={}
    diffs=[]
    for row in rows:
        rid=row["race_id"]
        if rid in seen or rid not in stage_rows:
            raise ValueError("duplicated_or_unlisted_JRA_race")
        seen.add(rid)
        base=stage_rows[rid]
        key=card_key(row["official_card_url"])
        if key!=(base["venue"],base["race_number"]):
            raise ValueError("JRA_official_link_does_not_match_race")
        count=row["numbered_card_rows"]
        if (row.get("parse_status")!="OFFICIAL_NUMBER_SEQUENCE_EXTRACTED"
            or type(count) is not int or not 1<=count<=18
            or not isinstance(row.get("raw_page_sha256"),str)
            or re.fullmatch(r"[0-9a-f]{64}",row["raw_page_sha256"]) is None
            or row.get("official_active_runner_count_independently_verified") is not False
            or row.get("third_party_preliminary_count") != base["third_party_displayed_runner_count"]
            or row.get("agrees_with_secondary_display") is not (
               count == base["third_party_displayed_runner_count"]
            )):
            raise ValueError("unverified_or_invalid_JRA_numbered_rows")
        counts[rid]=count
        if count != base["third_party_displayed_runner_count"]:
            diffs.append({
                "race_id":rid,
                "official_numbered_table_rows":count,
                "secondary_displayed_count":base["third_party_displayed_runner_count"],
                "difference":count-base["third_party_displayed_runner_count"],
            })
    if seen!=set(stage_rows) or len(diffs)!=raw_meta["discrepancies_count"]:
        raise ValueError("official_metadata_coverage_or_diff_mismatch")
    flat=[
        row for row in stage["races"]
        if row["programmed_surface"] in {"芝","ダ"} and 9<=counts[row["race_id"]]<=18
    ]
    flat.sort(key=lambda r:(r["scheduled_start_jst"],r["venue"],r["race_number"]))
    selected=flat[:10]
    # This is *not* day-schedule.json: no official racecard raw bytes or server proof.
    return {
        "schema_version":1,
        "status":"READ_ONLY_OFFICIAL_NUMBERED_ROWS_RECONCILED_NOT_FORMAL_FORWARD",
        "target_date":stage["race_date"],
        "official_card_number_sequences_parsed":len(counts),
        "scheduled_races":len(stage["races"]),
        "flat_candidate_count_by_numbered_rows":len(flat),
        "official_vs_secondary_count_discrepancies":sorted(diffs,key=lambda r:r["race_id"]),
        "first_ten_race_ids_unchanged":
            [x["race_id"] for x in selected] ==
            stage["provisional_first_ten_using_third_party_counts"],
        "first_ten_with_numbered_card_rows":[{
            "race_id":r["race_id"],
            "scheduled_start_jst":r["scheduled_start_jst"],
            "official_numbered_rows":counts[r["race_id"]],
            "third_party_preliminary_count":r["third_party_displayed_runner_count"],
            "forecast_window_if_schedule_unchanged":[
               (datetime.fromisoformat(r["scheduled_start_jst"])-timedelta(minutes=k)).isoformat()
               for k in (25,15)
            ],
        } for r in selected],
        "source_actions_run_id":raw_meta["observed_git_actions_run_id"],
        "source_metadata_artifact_url":raw_meta["official_raw_metadata_artifact_url"],
        "has_verified_current_active_runners_after_scratches":False,
        "has_server_sealed_whole_day_forecast_universe":False,
        "actual_market_price_snapshots":0,
        "prospective_predictions":0,
        "do_not_promote_to_formal_day_plan":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--staging",type=Path,required=True)
    p.add_argument("--jra-card-meta",type=Path,required=True)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    try:
        report=reconcile(
            json.loads(args.staging.read_text(encoding="utf-8")),
            json.loads(args.jra_card_meta.read_text(encoding="utf-8")),
        )
    except (ValueError,KeyError,TypeError,OSError) as exc:
        p.error(str(exc))
    out=json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(out,encoding="utf-8")
    else:
        print(out,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
