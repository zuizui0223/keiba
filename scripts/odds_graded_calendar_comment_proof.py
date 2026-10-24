#!/usr/bin/env python3
"""Independent GitHub comment proof for the 26-race future JRA calendar.

The FIRST externally posted coverage comment on PR #10, ID 6382991405,
committed 2026 Oct25–Dec27's 26 flat G1/G2/G3 slots and the version-1
ranking score rules on 2026-10-24 (BEFORE the next day's Kikka).

A comment's server created_at, updated_at, and body are read afresh
from GitHub REST using gh CLI. The local source files are compared
bytewise to the COMMENT'S frozen SHA1 Git BLOBS. This remains a manual
transcription of an official JRA web calendar, not an authenticated
machine-readable official schedule or full 2027 Q1 registry.

Offline fixture checks always return HOLD to prevent forged local JSON
from masquerading as a real GitHub server record. Publication before
Kikka proves the registered denominator's preexistence, not real
market probability calibration, prediction advantage or betting ROI.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta
from hashlib import sha1
import json
from pathlib import Path
import re
import subprocess

from odds_graded_calendar_coverage import (
    audit as audit_coverage, aware as _aware, JST,
)

REPO="zuizui0223/keiba"
PR_NUMBER=10
COMMENT_ID=6382991405
STATUS="EXTERNAL_GITHUB_26_RACE_CALENDAR_AND_PROTOCOL_SHA_PREEXISTENCE_ONLY"
OFFLINE="HOLD_LOCAL_FIXTURE_NOT_INDEPENDENT_GITHUB_EVIDENCE"
SEGMENT_FIRST_POST="2026-10-25T15:40:00+09:00"
_CAL=re.compile(r"(?m)^- 対象一覧のGit blob SHA: ([0-9a-f]{40})\s*$")
_REG=re.compile(r"(?m)^- 状態台帳のGit blob SHA: ([0-9a-f]{40})\s*$")
_PROTO=re.compile(r"(?m)^- 事前固定モデル・評価規則v1のGit blob SHA: ([0-9a-f]{40})\s*$")
HEADER="### 【事前登録・対象競走の分母固定】"


def git_blob_sha(raw:bytes):
    return sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()


def _one(pattern,body):
    matches=pattern.findall(body)
    if len(matches)!=1:
        raise ValueError("HOLD_MISSING_OR_DUPLICATE_PRECOMMITTED_BLOB_SHA")
    return matches[0]


def inspect_fixture(calendar_bytes,registry_bytes,protocol_bytes,comment):
    """Mathematically check raw content vs server fields; NOT independent fetch."""
    if not isinstance(comment,dict) or comment.get("id")!=COMMENT_ID:
        raise ValueError("HOLD_WRONG_GITHUB_PR_COMMENT")
    body=comment.get("body")
    if not isinstance(body,str) or not body.startswith(HEADER):
        raise ValueError("HOLD_NOT_PRECOMMITTED_COHORT_CALENDAR_COMMENT")
    actual={
        "calendar":git_blob_sha(calendar_bytes),
        "registry":git_blob_sha(registry_bytes),
        "protocol":git_blob_sha(protocol_bytes),
    }
    stated={
        "calendar":_one(_CAL,body),
        "registry":_one(_REG,body),
        "protocol":_one(_PROTO,body),
    }
    if actual!=stated:
        raise ValueError("HOLD_PRECOMMITTED_CALENDAR_OR_PROTOCOL_BLOB_CHANGED")
    c=json.loads(calendar_bytes.decode("utf-8"))
    r=json.loads(registry_bytes.decode("utf-8"))
    p=json.loads(protocol_bytes.decode("utf-8"))
    coverage=audit_coverage(c,r)
    if (p.get("schema")!="KEIBA_WIN_ODDS_PREQUENTIAL_COHORT_V1"
            or p.get("fixed_model_M1")!=(
                "M0 plus beta=+0.25 times centered log-relative early-to-late price change")
            or p.get("primary_metric")!=(
                "race-equal average M1 minus M0 winner categorical logloss; smaller is better")):
        raise ValueError("HOLD_PRECOMMITTED_COHORT_PRIMARY_OR_BETA_CHANGED")
    if coverage["calendar_segment_event_count"]!=26:
        raise ValueError("HOLD_WRONG_JRA_REGISTRY_COHORT_SIZE")
    # All 26 originally listed races must be inside the prior GH comment,
    # not only the opaque SHA. Avoid accepting duplicate or missing lines.
    original=[]
    for e in c["events"]:
        line=(f"- {e['scheduled_date_jst']} {e['venue']} "
              f"{e['grade']} {e['race_name_jp']}")
        original.append(line)
        if body.splitlines().count(line)!=1:
            raise ValueError("HOLD_GITHUB_DENOMINATOR_RACE_MISSING_OR_DUPLICATED")
    created=_aware(comment.get("created_at"))
    updated=_aware(comment.get("updated_at"))
    first_post=_aware(SEGMENT_FIRST_POST)
    if updated!=created:
        raise ValueError("HOLD_GITHUB_PRECOMMITMENT_COMMENT_EDITED")
    if created>=first_post-timedelta(minutes=10):
        raise ValueError("HOLD_GITHUB_PRECOMMITMENT_NOT_BEFORE_FIRST_RACE")
    return {
        "status":OFFLINE,
        "external_GitHub_timestamp_independently_verified":False,
        "registered_race_slots":len(original),
        "registered_distinct_meeting_dates":coverage[
            "calendar_segment_distinct_race_dates"],
        "first_registered_race_post_jst":first_post.isoformat(),
        "claimed_server_GitHub_created_at":created.isoformat(),
        "comment_url":f"https://github.com/{REPO}/pull/{PR_NUMBER}#issuecomment-{COMMENT_ID}",
        "all_26_calendar_slots_predeclared_in_comment":True,
        "three_frozen_content_git_blob_SHAs":actual,
        "study_period_end_2027_03_31_not_yet_fully_scheduled":True,
        "no_future_winner_or_top3_outcome_used":True,
        "cannot_assert_win_probability_advantage":True,
        "no_private_price_or_probability_rows_exported":True,
    }


def verify_live(calendar_bytes,registry_bytes,protocol_bytes):
    try:
        proc=subprocess.run(
            ["gh","api",f"/repos/{REPO}/issues/comments/{COMMENT_ID}"],
            text=True,capture_output=True,check=True)
        comment=json.loads(proc.stdout)
    except (OSError,subprocess.CalledProcessError,json.JSONDecodeError) as exc:
        raise ValueError("HOLD_GITHUB_API_INDEPENDENT_CALENDAR_COMMENT_FETCH_FAILED") from exc
    result=inspect_fixture(calendar_bytes,registry_bytes,protocol_bytes,comment)
    return {
        **result,
        "status":STATUS,
        "external_GitHub_timestamp_independently_verified":True,
        "github_server_created_at":result["claimed_server_GitHub_created_at"],
        "scope_of_evidence":"26 races and protocol existed as a submitted SHA+list before first event; source correctness not proven",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calendar",type=Path,required=True)
    parser.add_argument("--registry",type=Path,required=True)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=verify_live(
        args.calendar.read_bytes(),
        args.registry.read_bytes(),
        args.protocol.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "calendar_slots":report["registered_race_slots"],
        "independent_GitHub_proof":True,
        "full_2027_calendar_verified":False,
        "real_forecast_result_score":None,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
