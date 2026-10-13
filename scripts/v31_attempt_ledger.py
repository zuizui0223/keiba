#!/usr/bin/env python3
"""Record every chronologically eligible v3.1 race attempt, including pre-result failures."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

VALID_STATUSES = {"FROZEN", "PRE_RESULT_DATA_FAILURE"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_aware_iso(value: str, label: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid_datetime:{label}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"naive_datetime:{label}")
    return dt


def summarize(entries: list[dict]) -> dict:
    eligible = len(entries)
    frozen = sum(entry.get("status") == "FROZEN" for entry in entries)
    failures = sum(entry.get("status") == "PRE_RESULT_DATA_FAILURE" for entry in entries)
    return {
        "eligible_attempts": eligible,
        "frozen_attempts": frozen,
        "pre_result_data_failures": failures,
        "freeze_success_rate": frozen / eligible if eligible else None,
    }


def validate_event(event: dict) -> None:
    status = event.get("status")
    if status not in VALID_STATUSES:
        raise ValueError("invalid_attempt_status")
    if not event.get("race_id"):
        raise ValueError("missing_race_id")
    parse_aware_iso(event["scheduled_start_jst"], "scheduled_start_jst")
    if status == "FROZEN":
        sha = event.get("freeze_sha256")
        if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
            raise ValueError("invalid_freeze_sha256")
    else:
        reason = event.get("failure_reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("missing_failure_reason")


def register(ledger: dict, event: dict) -> dict:
    validate_event(event)
    entries = list(ledger.get("entries", []))
    if any(entry.get("race_id") == event["race_id"] for entry in entries):
        raise ValueError("duplicate_attempt_race")
    current = parse_aware_iso(event["scheduled_start_jst"], "current_start")
    if entries:
        last = parse_aware_iso(entries[-1]["scheduled_start_jst"], "last_start")
        if current <= last:
            raise ValueError("attempt_backfill_forbidden")

    row = dict(event)
    row["attempt_index"] = len(entries) + 1
    entries.append(row)
    out = dict(ledger)
    out["entries"] = entries
    out["summary"] = summarize(entries)
    out["status"] = "collecting"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("register")
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--event", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command != "register":
            raise ValueError("unknown_command")
        result = register(read_json(args.ledger), read_json(args.event))
        write_json(args.output, result)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
