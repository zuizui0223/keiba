#!/usr/bin/env python3
"""Result-blind denominator for prospective 30-attempt ticket forecasts.

Plan each JRA race date BEFORE its first scheduled start from a source-hashed,
complete race schedule; take the earliest ten eligible flat races (9-18 runners).
Record *every* selection even when win+wide quote capture later fails. This
ledger is separate from the immutable v3.1 prospective score ledger.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import re

try:
    from scripts.ticket_forward_freeze import (
        VERSION, REPO_ROOT, _jst, _http_host, OFFICIAL_HOSTS,
        sha256_bytes, canonical, valid_hex, validate_manifest, _no_outcomes,
    )
except ModuleNotFoundError:
    from ticket_forward_freeze import (
        VERSION, REPO_ROOT, _jst, _http_host, OFFICIAL_HOSTS,
        sha256_bytes, canonical, valid_hex, validate_manifest, _no_outcomes,
    )

ALLOWED_MARKS = ("HOLD_NO_WIN_WIDE_SNAPSHOT", "HOLD_INCOMPLETE_MARKET",
                 "HOLD_STALE_QUOTE", "HOLD_INVALID_ROSTER",
                 "HOLD_MISSING_SERVER_RECEIPT", "SUBMITTED_FOR_GITHUB_PROOF")


def new_attempt_ledger(manifest: dict) -> dict:
    validate_manifest(manifest)
    return {
        "schema_version": 1, "version": VERSION,
        "manifest_sha256": sha256_bytes(canonical(manifest)),
        "status": "NO_PROSPECTIVE_ATTEMPTS_REGISTERED",
        "day_plans": [], "attempts": [], "events": [],
        "target_attempts": manifest["holdout_attempts"],
        "note": "Empty initial cohort; not measured forward racing evidence",
    }


def plan_day(schedule: dict, manifest: dict, *, schedule_raw: bytes) -> dict:
    validate_manifest(manifest)
    _no_outcomes(schedule)
    if (set(schedule) != {
        "schema_version", "schedule_date", "source_url", "source_text_sha256",
        "captured_at_jst", "races"
    } or schedule["schema_version"] != 1):
        raise ValueError("unapproved_schedule_schema")
    _http_host(schedule["source_url"], OFFICIAL_HOSTS)
    if not valid_hex(schedule["source_text_sha256"]):
        raise ValueError("schedule_source_sha_missing")
    date = schedule["schedule_date"]
    if not isinstance(date, str) or not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", date):
        raise ValueError("bad_schedule_date")
    if date < manifest["start_eligible_on_or_after_jst_date"]:
        raise ValueError("historical_schedule_not_prospective")
    observed = _jst(schedule["captured_at_jst"])
    all_entries = []
    seen = set()
    races = schedule["races"]
    if not isinstance(races, list) or not races:
        raise ValueError("missing_complete_schedule_roster")
    for row in races:
        if set(row) != {
            "race_id", "venue", "race_number", "date", "scheduled_start_jst",
            "surface", "declared_runner_count", "status",
        }:
            raise ValueError("unapproved_schedule_race_row")
        rid = row["race_id"]
        start = _jst(row["scheduled_start_jst"])
        if (not isinstance(rid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{7,79}", rid) or
                rid in seen or row["date"] != date or start.date().isoformat() != date):
            raise ValueError("duplicate_or_mismatched_schedule_race")
        seen.add(rid)
        if (type(row["race_number"]) is not int or not 1 <= row["race_number"] <= 12 or
                not isinstance(row["venue"], str) or not row["venue"] or
                type(row["declared_runner_count"]) is not int or
                not 0 <= row["declared_runner_count"] <= 18 or
                row["surface"] not in {"芝", "ダ", "障"} or
                row["status"] not in {"RUNNING", "CANCELLED"}):
            raise ValueError("invalid_schedule_race_values")
        all_entries.append(row)
    first_start = min(_jst(row["scheduled_start_jst"]) for row in all_entries)
    if not observed < first_start:
        raise ValueError("schedule_captured_after_first_race_start")
    eligible = [
        row for row in all_entries
        if row["status"] == "RUNNING" and row["surface"] in {"芝", "ダ"} and
        manifest["min_runners"] <= row["declared_runner_count"] <= manifest["max_runners"]
    ]
    eligible.sort(key=lambda r: (_jst(r["scheduled_start_jst"]), r["venue"],
                                r["race_number"], r["race_id"]))
    chosen = eligible[:manifest["max_attempts_per_race_date"]]
    return {
        "schema_version": 1,
        "version": VERSION,
        "status": "PRE_RACE_SCHEDULE_PLAN_UNATTESTED",
        "schedule_date": date,
        "captured_at_jst": schedule["captured_at_jst"],
        "first_race_start_jst": first_start.isoformat(),
        "source_url": schedule["source_url"],
        "source_text_sha256": schedule["source_text_sha256"],
        "schedule_file_sha256": sha256_bytes(schedule_raw),
        "raw_schedule_count": len(all_entries),
        "eligible_races_before_cap": len(eligible),
        "included_first_ten": [ {
            "race_id": row["race_id"],
            "scheduled_start_jst": row["scheduled_start_jst"],
            "race_date": date,
            "venue": row["venue"], "race_number": row["race_number"],
            "declared_runner_count": row["declared_runner_count"],
        } for row in chosen ],
        "no_result_based_selection": True,
        "usage_note": "Requires pre-first-race independent GitHub server receipt for genuine universe audit",
    }


def register_day(ledger: dict, plan: dict, manifest: dict) -> dict:
    validate_manifest(manifest)
    if (ledger.get("version") != VERSION or
            ledger.get("manifest_sha256") != sha256_bytes(canonical(manifest)) or
            ledger.get("target_attempts") != manifest["holdout_attempts"] or
            set(ledger) != {"schema_version", "version", "manifest_sha256", "status",
                           "day_plans", "attempts", "events", "target_attempts", "note"}):
        raise ValueError("ledger_contract_mismatch")
    if (plan.get("status") != "PRE_RACE_SCHEDULE_PLAN_UNATTESTED" or
            plan.get("version") != VERSION or plan.get("no_result_based_selection") is not True):
        raise ValueError("invalid_pre_race_plan")
    if ledger["day_plans"]:
        last = ledger["day_plans"][-1]["schedule_date"]
        if plan["schedule_date"] <= last:
            raise ValueError("retroactive_or_duplicate_day")
    if len(ledger["attempts"]) >= ledger["target_attempts"]:
        raise ValueError("cohort_full")
    selected = plan["included_first_ten"]
    if not selected or len(selected) > manifest["max_attempts_per_race_date"]:
        raise ValueError("day_has_no_supported_races_or_exceeds_cap")
    if len(selected) > ledger["target_attempts"] - len(ledger["attempts"]):
        raise ValueError("day_crosses_target_limit")
    observed = _jst(plan["captured_at_jst"])
    dates = set()
    existing = {row["race_id"] for row in ledger["attempts"]}
    last_order = None
    for row in selected:
        if (row["race_id"] in existing or row["race_id"] in dates or
                row["race_date"] != plan["schedule_date"] or
                not observed < _jst(row["scheduled_start_jst"])):
            raise ValueError("invalid_or_repeated_day_selection")
        dates.add(row["race_id"])
        order = (_jst(row["scheduled_start_jst"]), row["venue"], row["race_number"], row["race_id"])
        if last_order is not None and order < last_order:
            raise ValueError("day_selection_not_chronological")
        last_order = order
    new = deepcopy(ledger)
    fingerprint = sha256_bytes(canonical(plan))
    new["day_plans"].append({
        "schedule_date": plan["schedule_date"], "source_schedule_sha256": plan["schedule_file_sha256"],
        "plan_sha256": fingerprint,
        "included_count": len(selected), "schedule_first_race": plan["first_race_start_jst"],
    })
    for r in selected:
        new["attempts"].append({
            "race_id": r["race_id"], "race_date": r["race_date"],
            "scheduled_start_jst": r["scheduled_start_jst"],
            "venue": r["venue"], "race_number": r["race_number"],
            "plan_sha256": fingerprint,
        })
    new["status"] = "COHORT_PLAN_IN_PROGRESS"
    return new


def record_attempt(ledger: dict, event: dict) -> dict:
    if set(event) - {"race_id", "status", "forecast_sha256", "github_run_id", "github_committed_path"}:
        raise ValueError("unsupported_event_fields")
    status, race_id = event["status"], event["race_id"]
    if status not in ALLOWED_MARKS:
        raise ValueError("invalid_attempt_status")
    if any(row["race_id"] == race_id for row in ledger["events"]):
        raise ValueError("attempt_already_registered_immutable")
    ordered = [x["race_id"] for x in ledger["attempts"]]
    if race_id not in ordered:
        raise ValueError("attempt_not_in_prepublished_universe")
    if len(ledger["events"]) >= len(ordered) or ordered[len(ledger["events"])] != race_id:
        raise ValueError("attempt_backfill_or_skipped_earlier_race")
    if status == "SUBMITTED_FOR_GITHUB_PROOF":
        if (not valid_hex(event.get("forecast_sha256")) or
                type(event.get("github_run_id")) is not int or event["github_run_id"] < 1 or
                not isinstance(event.get("github_committed_path"), str) or
                not event["github_committed_path"].startswith("holdout/ticket-forward-v1/") or
                not event["github_committed_path"].endswith("/forecast.json")):
            raise ValueError("successful_attempt_missing_server_proof_identifiers")
    elif set(event) != {"race_id", "status"}:
        raise ValueError("held_attempt_must_not_contain_forecast")
    out = deepcopy(ledger)
    out["events"].append(event)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    initialize = sub.add_parser("init")
    initialize.add_argument("--manifest", type=Path, required=True)
    initialize.add_argument("--output", type=Path, required=True)
    plan = sub.add_parser("plan-day")
    plan.add_argument("--schedule", type=Path, required=True)
    plan.add_argument("--manifest", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    register = sub.add_parser("register-day")
    register.add_argument("--ledger", type=Path, required=True)
    register.add_argument("--day-plan", type=Path, required=True)
    register.add_argument("--manifest", type=Path, required=True)
    register.add_argument("--output", type=Path, required=True)
    event = sub.add_parser("record-attempt")
    event.add_argument("--ledger", type=Path, required=True)
    event.add_argument("--event", type=Path, required=True)
    event.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            model = json.loads(args.manifest.read_bytes())
            output = new_attempt_ledger(model)
        elif args.command == "plan-day":
            model = json.loads(args.manifest.read_bytes())
            raw = args.schedule.read_bytes()
            output = plan_day(json.loads(raw), model, schedule_raw=raw)
        elif args.command == "register-day":
            output = register_day(json.loads(args.ledger.read_bytes()),
                                  json.loads(args.day_plan.read_bytes()),
                                  json.loads(args.manifest.read_bytes()))
        else:
            output = record_attempt(json.loads(args.ledger.read_bytes()),
                                    json.loads(args.event.read_bytes()))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({"status": output["status"] if "status" in output else "event_registered",
                      "file": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
