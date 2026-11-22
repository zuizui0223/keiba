#!/usr/bin/env python3
"""Independent day-universe proof: official schedule bytes + GitHub pre-first-race seal.

The result-blind race selection must exist on a GitHub server before the first
race of the day. This is a *separate* proof from each per-race forecast seal.
We never upgrade an unsealed local plan to a prospective plan merely because
its textual captured_at claims to precede the races.

The source page is only SHA-checked here; a separate audit is still required
to determine whether the saved raw page really supports every parsed entry.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from scripts.ticket_forward_freeze import (
        VERSION, REPO_ROOT, _jst, _time, canonical, sha256_bytes,
        git_blob_sha1, valid_hex, _http_host, OFFICIAL_HOSTS
    )
    from scripts.ticket_forward_universe import plan_day
except ModuleNotFoundError:
    from ticket_forward_freeze import (
        VERSION, REPO_ROOT, _jst, _time, canonical, sha256_bytes,
        git_blob_sha1, valid_hex, _http_host, OFFICIAL_HOSTS
    )
    from ticket_forward_universe import plan_day

REPO = "zuizui0223/keiba"
ROOT_PATH = "holdout/ticket-forward-v1/"


def validate_day_evidence(schedule_raw: bytes, source_raw: bytes,
                          plan_raw: bytes, manifest: dict) -> dict:
    """Recompute complete roster plan and refuse any out-of-band alteration."""
    if any(not isinstance(x, bytes) or not x for x in (
        schedule_raw, source_raw, plan_raw
    )):
        raise ValueError("day_evidence_bytes_missing")
    schedule = json.loads(schedule_raw)
    frozen = json.loads(plan_raw)
    if sha256_bytes(source_raw) != schedule.get("source_text_sha256"):
        raise ValueError("official_schedule_raw_source_sha_mismatch")
    _http_host(schedule["source_url"], OFFICIAL_HOSTS)
    recomputed = plan_day(schedule, manifest, schedule_raw=schedule_raw)
    if canonical(frozen) != canonical(recomputed):
        raise ValueError("stored_day_plan_not_reproducible")
    date = recomputed["schedule_date"]
    if not isinstance(date, str) or recomputed["status"] != "PRE_RACE_SCHEDULE_PLAN_UNATTESTED":
        raise ValueError("day_plan_contract_changed")
    return {
        "status": "DAY_EVIDENCE_CONSISTENT_BUT_NOT_SERVER_ATTESTED",
        "schedule_date": date,
        "first_race_start_jst": recomputed["first_race_start_jst"],
        "source_url": schedule["source_url"],
        "source_text_sha256": sha256_bytes(source_raw),
        "schedule_file_sha256": sha256_bytes(schedule_raw),
        "day_plan_file_sha256": sha256_bytes(plan_raw),
        "planned_races": len(recomputed["included_first_ten"]),
        "schedule_races": recomputed["raw_schedule_count"],
        "captured_at_jst": schedule["captured_at_jst"],
    }


def _github_get(url: str) -> dict:
    if not url.startswith("https://api.github.com/repos/zuizui0223/keiba/"):
        raise ValueError("disallowed_github_url")
    req = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "keiba-forward-day-universe-proof",
    })
    with urlopen(req, timeout=15) as response:
        return json.loads(response.read())


def attest_day_plan(schedule_raw: bytes, source_raw: bytes, plan_raw: bytes,
                    manifest: dict, *, run_id: int, plan_path: str,
                    getter=None) -> dict:
    """Require all 3 day-plan evidence files on a pre-first-race run git head.

    run.created_at is provider-server timestamp; source authenticity beyond
    saved bytes is not certified, and an actual JRA schedule/entry audit remains
    separately necessary before scoring a race as scientifically prospective.
    """
    evidence = validate_day_evidence(schedule_raw, source_raw, plan_raw, manifest)
    day = evidence["schedule_date"]
    expected_plan_path = f"{ROOT_PATH}{day}/day-plan.json"
    if type(run_id) is not int or run_id < 1 or plan_path != expected_plan_path:
        raise ValueError("untrusted_day_proof_identifier")
    if getter is None:
        getter = _github_get
    run = getter(f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}")
    first = _jst(evidence["first_race_start_jst"])
    committed = _time(run["created_at"])
    observed = _jst(evidence["captured_at_jst"])
    if (
        run.get("repository", {}).get("full_name") != REPO
        or run.get("event") not in {"push", "pull_request", "workflow_dispatch"}
        or run.get("conclusion") != "success"
        or not observed <= committed < first
        or not valid_hex(run.get("head_sha"), 40)
    ):
        raise ValueError("day_plan_not_pre_first_race_server_attested")
    head = run["head_sha"]
    copies = {
        "day-plan.json": plan_raw,
        "day-schedule.json": schedule_raw,
        "day-schedule-source.txt": source_raw,
    }
    for filename, expected in copies.items():
        path = f"{ROOT_PATH}{day}/{filename}"
        entry = getter(
            f"https://api.github.com/repos/{REPO}/contents/"
            f"{quote(path, safe='/')}?ref={head}"
        )
        if entry.get("encoding") != "base64" or entry.get("path") != path:
            raise ValueError(f"missing_or_bad_day_companion:{filename}")
        actual = base64.b64decode(entry["content"], validate=False)
        if actual != expected or entry.get("sha") != git_blob_sha1(expected):
            raise ValueError(f"day_companion_does_not_match_git_head:{filename}")
    return {
        **evidence,
        "status": "DAY_PLAN_SERVER_SEALED_PRE_FIRST_RACE",
        "server_created_at_utc": run["created_at"],
        "server_run_id": run_id,
        "git_head_sha": head,
        "committed_plan_path": plan_path,
        "limits": "GitHub proves pre-first-start bytes, not independent truth of official page or all parsed entries",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--schedule", type=Path, required=True)
    p.add_argument("--source-page", type=Path, required=True)
    p.add_argument("--day-plan", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--github-run-id", type=int)
    p.add_argument("--github-plan-path")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        params = (
            args.schedule.read_bytes(), args.source_page.read_bytes(),
            args.day_plan.read_bytes(),
            json.loads(args.manifest.read_bytes()),
        )
        if bool(args.github_run_id) != bool(args.github_plan_path):
            raise ValueError("provide_both_github_run_and_path_or_neither")
        data = (
            attest_day_plan(*params, run_id=args.github_run_id, plan_path=args.github_plan_path)
            if args.github_run_id else validate_day_evidence(*params)
        )
    except (ValueError, KeyError, OSError, TypeError) as error:
        p.error(str(error))
    result = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
