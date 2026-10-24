#!/usr/bin/env python3
"""Independent server-time audit for 2027 PROVISIONAL G1/G2/G3 cohort SHA.

The JRA's 2027 schedule was published provisionally on 2026-09-28.
A SHA-only + explicitly listed 36-race draft was posted in PR #10
comment 6385029173 before any 2027 race. The 2026 26-race/score
precommitment is a distinct earlier record and must stay immutable.

Only independently fetched GH server comment created_at is trusted.
Offline fabricated JSON fixtures MUST return HOLD. A pre-event GitHub
SHA cannot establish regulatory approval, actual tote clock alignment,
future official results, calibrated winner probabilities or positive
betting value.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timedelta
from hashlib import sha1
import json
from pathlib import Path
import re
import subprocess

from odds_multiyear_provisional_coverage import audit_2027

REPO="zuizui0223/keiba"
COMMENT_ID=6385029173
HEADER="### 【2027年1〜3月・暫定36競走の事前記録】"
CAL_LABEL="- 新たな2027暫定カレンダーのGit blob SHA:"
REG_LABEL="- 新たな2027暫定状態台帳のGit blob SHA:"
STATUS="GH_SERVER_2027_PRELIMINARY_36_SLOT_SHA_EXISTENCE_VERIFIED_NOT_FINAL_JRA"
OFFLINE="HOLD_LOCAL_ONLY_2027_COMMENT_FIXTURE_NOT_REMOTE_EVIDENCE"
_FIRST_POST="2027-01-04T09:00:00+09:00"
_SHA=re.compile(r"^[a-f0-9]{40}$")


def _time(x):
    if not isinstance(x,str):raise ValueError("HOLD_GITHUB_COHORT_TIMESTAMP_TYPE")
    d=datetime.fromisoformat(x.replace("Z","+00:00"))
    if d.utcoffset() is None:raise ValueError("HOLD_GITHUB_COHORT_TIMESTAMP_TZ")
    return d


def _blob(raw):
    if type(raw) is not bytes:raise ValueError("HOLD_GIT_BLOB_BYTES_REQUIRED")
    return sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()


def _sha_line(body,label):
    matches=[line[len(label):].strip() for line in body.splitlines()
             if line.startswith(label)]
    if len(matches)!=1 or not _SHA.fullmatch(matches[0]):
        raise ValueError("HOLD_COMMITMENT_SHA_FIELD_DUPLICATE_OR_MISSING")
    return matches[0]


def _listed_name(e):
    alt=(f"（他資料の候補日：{'・'.join(e['alternate_reported_dates_jst'])}、確定要照合）"
         if e["alternate_reported_dates_jst"] else "")
    up=(f"（{e['grade_upgrade_application_pending']}昇格審査待ち）"
        if e["grade_upgrade_application_pending"] else "")
    return (f"- {e['candidate_date_jst']} {e['venue']} "
            f"{e['provisional_grade']} {e['race_name_jp']}{alt}{up}")


def inspect_fixture(calendar_bytes,registry_bytes,comment):
    """Structural check only: DO NOT treat caller's JSON as GH evidence."""
    if not isinstance(comment,dict) or comment.get("id")!=COMMENT_ID:
        raise ValueError("HOLD_WRONG_2027_GITHUB_PR_COMMENT")
    body=comment.get("body")
    if not isinstance(body,str) or not body.startswith(HEADER):
        raise ValueError("HOLD_NOT_ORIGINAL_PROVISIONAL_2027_COMMENT")
    if (_sha_line(body,CAL_LABEL)!=_blob(calendar_bytes)
            or _sha_line(body,REG_LABEL)!=_blob(registry_bytes)):
        raise ValueError("HOLD_2027_SUBMITTED_CALENDAR_REGISTRY_HASH_CHANGED")
    try:
        cal=json.loads(calendar_bytes)
        reg=json.loads(registry_bytes)
    except (UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("HOLD_UNREADABLE_2027_STAGING_FILES") from exc
    aud=audit_2027(cal,reg)
    for e in cal["events"]:
        if body.splitlines().count(_listed_name(e))!=1:
            raise ValueError("HOLD_2027_PROVISIONAL_RACE_MISSING_OR_DUPLICATED_IN_COMMENT")
    if (body.count("**暫定36件の全競走")!=1
            or "正式認可済みの正式日程を意味しない" not in body
            or "日付の資料間不一致" not in body):
        raise ValueError("HOLD_COMMENT_REMOVED_UNCERTAINTY_OR_PROVISIONAL_SCOPE")
    created=_time(comment.get("created_at"))
    updated=_time(comment.get("updated_at"))
    if updated!=created:
        raise ValueError("HOLD_SUBMITTED_2027_PR_COMMENT_EDITED")
    if not created<_time(_FIRST_POST)-timedelta(minutes=10):
        raise ValueError("HOLD_2027_CALENDAR_COMMITTED_AFTER_FIRST_START")
    return {
        "status":OFFLINE,
        "external_GitHub_API_trusted":False,
        "comment_id":COMMENT_ID,
        "github_comment_url":f"https://github.com/{REPO}/pull/10#issuecomment-{COMMENT_ID}",
        "server_time_supplied_by_fixture":created.isoformat(),
        "candidate_2027_flat_graded_races":aud["provisional_candidates"],
        "documented_disputed_date_cases":aud["n_disputed_exact_dates"],
        "two_grade_promotions_pending_not_final":len(
            aud["grade_upgrade_applications_pending"])==2,
        "candidate_2027_listed_lines_all_present_once":True,
        "raw_source_files_sha1_git_blobs":{
            "provisional_calendar":_blob(calendar_bytes),
            "provisional_registry":_blob(registry_bytes),
        },
        "official_2027_regulatory_approval_not_proven":True,
        "prediction_scores_from_actual_races":0,
        "original_2026_calendar_or_protocol_altered":False,
    }


def verify_live(calendar_bytes,registry_bytes):
    try:
        r=subprocess.run(
            ["gh","api",f"/repos/{REPO}/issues/comments/{COMMENT_ID}"],
            check=True,text=True,capture_output=True)
        comment=json.loads(r.stdout)
    except (OSError,subprocess.CalledProcessError,json.JSONDecodeError) as exc:
        raise ValueError("HOLD_GITHUB_SERVER_PRECOMMITMENT_FETCH_FAILED") from exc
    verified=inspect_fixture(calendar_bytes,registry_bytes,comment)
    return {
        **verified,
        "status":STATUS,
        "external_GitHub_API_trusted":True,
        "server_verified_created_at":verified["server_time_supplied_by_fixture"],
        "source_claim_limited_to_time_and_exact_submitted_SHA":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--calendar",required=True,type=Path)
    p.add_argument("--registry",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    x=verify_live(a.calendar.read_bytes(),a.registry.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":x["status"],
        "2027_provisional_candidates":x["candidate_2027_flat_graded_races"],
        "GH_server_timestamp_independently_verified":True,
        "official_2027_schedule_final":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
