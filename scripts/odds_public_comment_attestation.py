#!/usr/bin/env python3
"""Independently verify a prestart SHA-only GitHub PR conversation commitment.

Unlike a workflow_dispatch receipt, this variant works BEFORE the
workflow is merged to the repository default branch. GitHub issue/PR
comments have server-created_at and server-updated_at metadata. The
comment must be unedited (created_at==updated_at), contain exactly the
SHA of the privately stored prediction and the race ID, and have been
created before post time minus 10 minutes. Earlier submissions for
that race cannot be discarded or superseded.

IMPORTANT: a GitHub comment proves preexistence of a SHA only, NOT
the integrity or license of third-party market observations, empirical
probability calibration, odds feedback, winnings, or formal v3.1 holdout.

For authentic verification this module fetches directly from GitHub via
the user's authenticated gh CLI. Offline JSON fixtures return HOLD.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta
import json
import re
import subprocess
from pathlib import Path

from odds_public_two_point_freeze import verify_freeze, score

REPO="zuizui0223/keiba"
PR=10
COMMENT_ID=6381798252
STATUS="GH_SERVER_PRESTART_DIGEST_COMMITMENT_VERIFIED_ONLY"
STATUS_OFFLINE="HOLD_OFFLINE_JSON_IS_NOT_SERVER_PRESTART_ATTESTATION"
HEADER="### 【事前提出・SHA-only】"
RACE_FIELD_RE=re.compile(r"(?m)^- race_id:\s*(\S+)\s*$")
SHA_FIELD_RE=re.compile(r"(?m)^- freeze_payload_sha256:\s*([a-f0-9]{64})\s*$")


def _date(text):
    if not isinstance(text,str):
        raise ValueError("HOLD_GITHUB_COMMENT_TIME_INVALID")
    d=datetime.fromisoformat(text.replace("Z","+00:00"))
    if d.utcoffset() is None:
        raise ValueError("HOLD_GITHUB_COMMENT_TIME_NO_TZ")
    return d


def _unique_field(pattern,body,what):
    matches=pattern.findall(body)
    if len(matches)!=1:
        raise ValueError("HOLD_MULTIPLE_OR_MISSING_PRECOMMITMENT_"+what)
    return matches[0]


def inspect_records(freeze,comment,all_comments):
    p=verify_freeze(freeze)
    if not isinstance(comment,dict) or not isinstance(all_comments,list):
        raise ValueError("HOLD_GITHUB_COMMENT_NOT_ACQUIRED")
    commentid=comment.get("id")
    if commentid!=COMMENT_ID:
        raise ValueError("HOLD_GITHUB_COMMENT_ID_CHANGED")
    body=comment.get("body")
    if not isinstance(body,str) or not body.startswith(HEADER):
        raise ValueError("HOLD_GITHUB_COMMENT_MISSING_PRECOMMIT_MARKER")
    race=_unique_field(RACE_FIELD_RE,body,"RACE")
    digest=_unique_field(SHA_FIELD_RE,body,"SHA")
    if race!=p["race_id"] or digest!=freeze["seal_sha256_of_payload"]:
        raise ValueError("HOLD_SHA_OR_RACE_DOES_NOT_MATCH_FROZEN_PREDICTION")
    created=_date(comment.get("created_at"))
    updated=_date(comment.get("updated_at"))
    generated=_date(p["local_freeze_generated_at_jst"])
    post=_date(p["post_jst"])
    if updated!=created:
        raise ValueError("HOLD_POSTED_SHA_COMMENT_WAS_EDITED")
    if not generated<=created<post-timedelta(minutes=10):
        raise ValueError("HOLD_COMMENT_NOT_SERVER_CREATED_PRESTART")
    matching=[c for c in all_comments if
        isinstance(c,dict) and isinstance(c.get("body"),str)
        and c["body"].startswith(HEADER) and
        RACE_FIELD_RE.findall(c["body"])==[race]]
    if not any(c.get("id")==commentid for c in matching):
        raise ValueError("HOLD_POSTED_COMMENT_ABSENT_FROM_GITHUB_PR")
    if any((c.get("id")!=commentid and
             (_date(c.get("created_at")),int(c.get("id") or 0))<
             (created,int(commentid))) for c in matching):
        raise ValueError("HOLD_PRIOR_COMMITMENT_FOR_SAME_RACE_DISCARDED")
    if len({c.get("id") for c in all_comments})!=len(all_comments):
        raise ValueError("HOLD_DUPLICATED_GITHUB_COMMENT_IDS")
    return {
        "status":STATUS,
        "race_id":p["race_id"],
        "sha256_of_original_frozen_payload":digest,
        "github_repo":REPO,
        "github_pr_number":PR,
        "github_comment_id":commentid,
        "github_comment_url":f"https://github.com/{REPO}/pull/{PR}#issuecomment-{commentid}",
        "server_created_at":created.isoformat(),
        "server_updated_at":updated.isoformat(),
        "local_freeze_generated_at":generated.isoformat(),
        "official_scheduled_post_at":post.isoformat(),
        "lead_time_hours":(post-created).total_seconds()/3600,
        "trusted_claim_limited_to_SHA_preexistence":True,
        "does_not_enter_v31_formal_holdout":True,
        "source_quotes_and_odds_trained_coefficients_unverified":True,
    }


def offline_fixture_check(freeze,comment,all_comments):
    """Never certify user-provided fake JSON as authentic GH API evidence."""
    audit=inspect_records(freeze,comment,all_comments)
    return {**audit,"status":STATUS_OFFLINE,
            "GitHub_API_independently_fetched":False}


def _gh_api(url):
    try:
        x=subprocess.run(["gh","api",url],check=True,
                         capture_output=True,text=True)
    except (OSError,subprocess.CalledProcessError) as e:
        raise ValueError("HOLD_FAILED_TO_FETCH_GITHUB_SERVER_COMMENT") from e
    try:
        return json.loads(x.stdout)
    except json.JSONDecodeError as e:
        raise ValueError("HOLD_GITHUB_SERVER_RETURNED_INVALID_JSON") from e


def fetch_all_comments():
    all_comments=[]
    # Never accept a partial history that could conceal an earlier attempt.
    for page in range(1,21):
        rows=_gh_api(f"/repos/{REPO}/issues/{PR}/comments?per_page=100&page={page}")
        if not isinstance(rows,list):
            raise ValueError("HOLD_UNEXPECTED_GITHUB_COMMENT_LIST")
        all_comments.extend(rows)
        if len(rows)<100:
            return all_comments
    raise ValueError("HOLD_GITHUB_COMMENT_HISTORY_EXCEEDS_AUDIT_LIMIT")


def verify_live(freeze,*,with_result=None):
    # Cannot substitute a forged local fixture for independent gh api data.
    comment=_gh_api(f"/repos/{REPO}/issues/comments/{COMMENT_ID}")
    all_comments=fetch_all_comments()
    proof=inspect_records(freeze,comment,all_comments)
    proof["GitHub_API_independently_fetched"]=True
    if with_result is None:
        return proof
    return {
        **proof,
        "status":"GH_PRESTART_SHA_VERIFIED_AND_POSTRACE_JRA_SCORE_NOT_V31",
        "postrace_scores":score(freeze,with_result),
        "no_retroactive_tuning_allowed":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--result",type=Path)
    args=p.parse_args()
    frozen=json.loads(args.freeze.read_text(encoding="utf-8"))
    result=(json.loads(args.result.read_text(encoding="utf-8"))
            if args.result else None)
    proof=verify_live(frozen,with_result=result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":proof["status"],"race":proof["race_id"],
                      "lead_hours":proof["lead_time_hours"],
                      "digest":proof["sha256_of_original_frozen_payload"]}))


if __name__=="__main__":
    main()
