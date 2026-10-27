#!/usr/bin/env python3
"""TYPE-SAFE GitHub PR30 SHA-only timestamps for the SECONDARY WIN-only lane.

Primary WIN+WIDE predictions use PR22/PR23 and their DIFFERENT schema/anchor.
WIN-only is a distinct, PREDECLARED experimental lane. The same physical
race is still ONE real market interval, not two independent trials.

No POST. 'prepare' emits a SHA-only body for the user to post deliberately
on existing Draft PR #30 BEFORE the +15-minute q2 target window starts.
Only a live gh-api GET of ALL current PR30 comments and the individual
matching comment can verify its server-created timestamp. Offline test
fixtures are structurally checkable but NEVER independently attested.

Source/card/time records and code hashes are LOCAL/operator claimed.
A real GitHub SHA timestamp says only that the pretarget digest publicly
existed then. It cannot prove source publication truth, total authorized
stake pool, intact/deleted comment history, complete target snapshot stream,
actual horse GPS or predictive/betting edge. Existing Kikka M0-M2 and v3.1
are never touched. GitHub comments need explicit human authorization.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
import re

from keiba_win_only_shadow_lane import (
    verify_win_only, _model_code_manifest,
    SCORE_STATUS as WIN_SCORE_STATUS, TARGET_SCHEMA,
)
from keiba_nextprice_pr_comment_attestation import _gh_json
from odds_shadow_freeze_score import _aware

ANCHOR_REPO="zuizui0223/keiba"
ANCHOR_PR=30
EXPECTED_AUTHOR="zuizui0223"
MARKER="KEIBA_SECONDARY_WIN_ONLY_NEXT_QUOTE_SHA_V1"
SCHEMA="KEIBA_SECONDARY_WIN_ONLY_COMMENT_CLAIM_V1"
STATUS_PREPARED="WIN_ONLY_SHA_COMMENT_PREPARED_NOT_POSTED"
STATUS_FIXTURE="HOLD_OFFLINE_COMMENT_FIXTURE_NOT_GITHUB_ATTESTATION"
STATUS_REMOTE="WIN_ONLY_SHA_CREATED_BEFORE_Q2_BY_GITHUB_SERVER"
STATUS_SCORED="WIN_ONLY_REMOTE_SHA_BOUND_TO_LOCAL_Q2_SCORE_CAPTURE_UNATTESTED"
MAX_COMMENT_PAGES=20
SAFE_RACE_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,95}$")
SAFE_SHA=re.compile(r"^[0-9a-f]{64}$")


def _canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False)


def _claim(freeze, *, synthetic_fixture=False):
    p=verify_win_only(freeze)
    if not synthetic_fixture and not (
            p["card_operator_provenance"]=="authorized_private_local_export" and
            p["operator_rights_confirmed_locally_only"] is True):
        raise ValueError("HOLD_WIN_ONLY_UNAUTHORIZED_OR_SYNTHETIC_PR_COMMENT")
    if not synthetic_fixture and p["model_code_content_SHA256"]!=_model_code_manifest():
        raise ValueError("HOLD_WIN_ONLY_CODE_CHANGED_SINCE_SOURCE_FREEZE")
    rid=p["race_id"]
    digest=freeze["seal_sha256_of_canonical_payload"]
    if (not isinstance(rid,str) or not SAFE_RACE_ID.fullmatch(rid) or
            not isinstance(digest,str) or not SAFE_SHA.fullmatch(digest)):
        raise ValueError("HOLD_WIN_ONLY_UNSAFE_PUBLIC_SHA_OR_RACE_ID")
    if p["research_lane"]!="SECONDARY_SEPARATE_WIN_ONLY_NOT_FULL_WIDE":
        raise ValueError("HOLD_ATTEMPT_TO_MIX_WIN_ONLY_AND_FULL_WIDE_SCHEMAS")
    if len(p["fixed_next_quote_model_indices"])!=6:
        raise ValueError("HOLD_WIN_ONLY_WRONG_CANDIDATE_MODEL_COUNT")
    return {
        "schema":SCHEMA,
        "research_lane":"SECONDARY_WIN_ONLY_NOT_WIDE",
        "repository":ANCHOR_REPO,
        "anchor_pull_request":ANCHOR_PR,
        "race_id":rid,
        "model_SHA256":digest,
        "last_WIN_source_received_jst":p["source_second_WIN_received"],
        "local_freeze_created_jst":p["local_freeze_created"],
        "next_WIN_target_window_start_jst":p["target_WIN_window_start"],
        "next_WIN_target_window_end_jst":p["target_WIN_window_end"],
        "scheduled_post_jst":p["scheduled_post"],
        "fixed_candidate_count":6,
        "raw_source_card_stakes_and_prediction_vectors_NOT_in_comment":True,
    }


def _body(data):
    return MARKER+"\n"+_canonical(data)


def prepare(freeze):
    claim=_claim(freeze)
    body=_body(claim)
    if (len(body)>1700 or "fixed_next_quote_model_indices" in body or
            "odds_by_horse_number" in body or "source_url" in body):
        raise ValueError("HOLD_WIN_ONLY_SHA_COMMENT_INCLUDES_PRIVATE_VALUES")
    return {
        "status":STATUS_PREPARED,
        "post_to_existing_PR_once_URL":
            f"https://github.com/{ANCHOR_REPO}/pull/{ANCHOR_PR}",
        "sha_only_comment_body_NOT_POSTED":body,
        "source_race_id":claim["race_id"],
        "model_SHA256":claim["model_SHA256"],
        "created_GitHub_comment":False,
        "external_timestamp_proven":False,
        "explicit_human_POST_action_required":True,
    }


def _race_in_comment(body):
    """Count malformed duplicate commitments still carrying same race ID."""
    if not isinstance(body,str) or not body.startswith(MARKER+"\n"):
        return None
    match=re.search(r'"race_id"\s*:\s*"([^"\n]{1,96})"',body)
    return match.group(1) if match else "MALFORMED_RACE_ID"


def _evaluate(freeze, comments, *, fixture=False):
    claim=_claim(freeze,synthetic_fixture=fixture)
    if not isinstance(comments,list):
        raise ValueError("HOLD_WIN_ONLY_COMMENT_HISTORY_NOT_LIST")
    matching=[x for x in comments if (
        isinstance(x,dict) and _race_in_comment(x.get("body"))==claim["race_id"])]
    if len(matching)!=1:
        raise ValueError("HOLD_WIN_ONLY_ZERO_OR_MULTIPLE_SAME_RACE_COMMENTS")
    comment=matching[0]
    ident=comment.get("id")
    issue=f"https://api.github.com/repos/{ANCHOR_REPO}/issues/{ANCHOR_PR}"
    comment_url=f"https://github.com/{ANCHOR_REPO}/pull/{ANCHOR_PR}#issuecomment-{ident}"
    if (type(ident) is not int or ident<1 or
            not isinstance(comment.get("user"),dict) or
            comment["user"].get("login")!=EXPECTED_AUTHOR or
            comment.get("issue_url")!=issue or
            comment.get("html_url")!=comment_url):
        raise ValueError("HOLD_WIN_ONLY_UNTRUSTED_AUTHOR_PR_OR_COMMENT_ID")
    if comment.get("body")!=_body(claim):
        raise ValueError("HOLD_WIN_ONLY_COMMENT_NOT_CANONICAL_OR_WRONG_SHA")
    created=_aware(comment.get("created_at"))
    edited=_aware(comment.get("updated_at"))
    if created!=edited:
        raise ValueError("HOLD_WIN_ONLY_GITHUB_COMMENT_EDITED")
    last_rx=_aware(claim["last_WIN_source_received_jst"])
    frozen=_aware(claim["local_freeze_created_jst"])
    target=_aware(claim["next_WIN_target_window_start_jst"])
    end=_aware(claim["next_WIN_target_window_end_jst"])
    post=_aware(claim["scheduled_post_jst"])
    if not (last_rx<=frozen<=created<target<=end<
            post-timedelta(minutes=10)):
        raise ValueError("HOLD_WIN_ONLY_GITHUB_SHA_LATE_VS_NEXT_PRICE")
    return {
        "schema":SCHEMA,
        "status":"STRUCTURAL_COMMENT_CLOCK_ONLY_NOT_LIVE_VERIFIED",
        "race_id":claim["race_id"],
        "frozen_model_SHA256":claim["model_SHA256"],
        "github_comment_id":ident,
        "github_comment_url":comment_url,
        "github_server_created_at_claim":created.isoformat(),
        "next_price_target_window_start":target.isoformat(),
        "next_price_target_window_end":end.isoformat(),
        "minutes_between_GitHub_SHA_and_target_start":
            (target-created).total_seconds()/60,
        "GitHub_creation_and_update_timestamp_equal":True,
        "current_visible_same_race_claim_count":1,
        "deleted_comments_or_same_second_edits_not_recoverable":True,
        "underlying_source_clock_and_licensing_NOT_authenticated":True,
        "full_target_stream_not_independently_certified":True,
        "real_win_probabilities_betting_ROI_or_criticality":"HOLD",
    }


def inspect_fixture(freeze, comments):
    obj=_evaluate(freeze,comments,fixture=True)
    return {**obj,"status":STATUS_FIXTURE,
            "live_GitHub_API_comment_GET_performed":False,
            "server_time_pre_next_WIN_target_verified":False}


def _get_all_comments():
    """Fetch only actual GitHub REST, fail closed if pages are incomplete."""
    out=[]
    seen=set()
    for page in range(1,MAX_COMMENT_PAGES+1):
        url=(f"/repos/{ANCHOR_REPO}/issues/{ANCHOR_PR}/comments"
             f"?per_page=100&page={page}")
        batch=_gh_json(url)
        if not isinstance(batch,list):
            raise ValueError("HOLD_WIN_ONLY_GITHUB_COMMENTS_API_UNEXPECTED_SHAPE")
        for c in batch:
            ident=c.get("id") if isinstance(c,dict) else None
            if type(ident) is not int or ident in seen:
                raise ValueError("HOLD_WIN_ONLY_GITHUB_COMMENT_ID_DUPLICATED")
            seen.add(ident)
            out.append(c)
        if len(batch)<100:
            return out
    raise ValueError("HOLD_WIN_ONLY_GITHUB_COMMENTS_EXCEED_PAGINATION_CAP")


def verify_live(freeze):
    """Only direct API GET may assert SHA server-time; never fixture JSON."""
    _claim(freeze)
    comments=_get_all_comments()
    proof=_evaluate(freeze,comments)
    ident=proof["github_comment_id"]
    detailed=_gh_json(f"/repos/{ANCHOR_REPO}/issues/comments/{ident}")
    listed=next(x for x in comments if x["id"]==ident)
    if not isinstance(detailed,dict):
        raise ValueError("HOLD_WIN_ONLY_GITHUB_DETAIL_NOT_OBJECT")
    for key in ("id","body","created_at","updated_at","issue_url","html_url"):
        if detailed.get(key)!=listed.get(key):
            raise ValueError("HOLD_WIN_ONLY_GITHUB_DETAIL_VS_LISTING_MISMATCH")
    if detailed.get("user",{}).get("login")!=EXPECTED_AUTHOR:
        raise ValueError("HOLD_WIN_ONLY_GITHUB_OWNER_NOT_AUTHENTICATED")
    return {
        **proof,
        "status":STATUS_REMOTE,
        "live_GitHub_API_comment_GET_performed":True,
        "server_time_pre_next_WIN_target_verified":True,
        "public_digest_existence_only_not_original_prices":True,
        "true_captured_source_and_target_integrity_independently_proven":False,
    }


def attach_locally_scored_target(proof, local_score):
    """Even a real remote SHA does not prove locally reported q2 truth."""
    if (not isinstance(proof,dict) or proof.get("status")!=STATUS_REMOTE
            or proof.get("live_GitHub_API_comment_GET_performed") is not True
            or proof.get("server_time_pre_next_WIN_target_verified") is not True):
        raise ValueError("HOLD_WIN_ONLY_SHA_PROOF_NEVER_LIVE_VERIFIED")
    if (not isinstance(local_score,dict) or
            local_score.get("schema")!=TARGET_SCHEMA or
            local_score.get("status")!=WIN_SCORE_STATUS or
            local_score.get("race_id")!=proof["race_id"] or
            local_score.get("local_frozen_model_sha256")!=
                proof["frozen_model_SHA256"] or
            local_score.get("new_independently_proven_next_market_trial") is not False):
        raise ValueError("HOLD_WIN_ONLY_LOCAL_SCORE_SHA_RACE_OR_STATUS_MISMATCH")
    t=_aware(local_score["source_target_published"])
    receipt=_aware(local_score["source_target_received"])
    if not (_aware(proof["github_server_created_at_claim"])<
            _aware(proof["next_price_target_window_start"])<=t<=
            _aware(proof["next_price_target_window_end"]) and t<=receipt):
        raise ValueError("HOLD_WIN_ONLY_TARGET_CLOCK_CHANGED_AFTER_SHA")
    return {
        "status":STATUS_SCORED,
        "race_id":proof["race_id"],
        "github_comment_url":proof["github_comment_url"],
        "frozen_model_SHA256":proof["frozen_model_SHA256"],
        "source_target_clock_only_locally_declared":True,
        "github_SHA_was_posted_before_declared_next_market_target":True,
        "independently_authenticated_WIN_source_and_complete_q2":False,
        "full_WIDE_primary_study_unchanged":True,
        "model_TV_KL_on_one_local_market_target":local_score["model_score_TV_KL"],
        "new_independently_verified_JRA_market_trials":0,
        "real_betting_or_horse_GPS_inference":"HOLD",
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,indent=2,
                           allow_nan=False)+"\n")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest="action",required=True)
    a=s.add_parser("prepare")
    a.add_argument("--private-freeze",required=True,type=Path)
    a.add_argument("--private-output",required=True,type=Path)
    b=s.add_parser("inspect-fixture")
    b.add_argument("--private-freeze",required=True,type=Path)
    b.add_argument("--comments-json",required=True,type=Path)
    b.add_argument("--private-output",required=True,type=Path)
    c=s.add_parser("verify-live")
    c.add_argument("--private-freeze",required=True,type=Path)
    c.add_argument("--private-output",required=True,type=Path)
    c.add_argument("--private-local-score",type=Path)
    args=p.parse_args()
    model=_read(args.private_freeze)
    if args.action=="prepare":
        result=prepare(model)
    elif args.action=="inspect-fixture":
        result=inspect_fixture(model,_read(args.comments_json))
    else:
        result=verify_live(model)
        if args.private_local_score is not None:
            result=attach_locally_scored_target(
                result,_read(args.private_local_score))
    _write(args.private_output,result)
    print(json.dumps({
        "status":result["status"],
        "GitHub_comment_automatically_POSTed":False,
        "independent_JRA_next_quote_attested":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
