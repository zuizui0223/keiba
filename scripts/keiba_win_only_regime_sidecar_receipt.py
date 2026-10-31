#!/usr/bin/env python3
"""Independent *SHA-only* remote timestamp check for WIN-only B+ companion.

The ORIGINAL six informed-horse/PDE/voter models have their own, separate,
existing SHA-only proof on PR #30. New five regime-null candidate predictions
are contained in a second SHA digest posted manually on DRAFT PR #37.
Never use the PR30 digest alone to attest B+ predictions.

NO API writes/post/betting. 'prepare' only prints/saves a safe SHA-only body.
For real proof, require BOTH:
  1. the original PR30 six-model SHA exists in a live, complete GitHub
     issue-comment list before the target, using existing strict verifier,
  2. an OWNER-authored B+ SHA comment on PR37, unedited, uniquely matching
     this race, created no earlier than parent server comment and before
     first eligible target window, with live list + individual-comment GET.

Even valid GitHub timestamps prove only that DIGESTS existed before q2.
They do NOT independently prove real JRA-VAN licensing, original source
publication/reception time, feed completeness, actual bettor stakes,
horse/GPS model calibration, winner probabilities or profit.
Offline fixture tests can NEVER self-certify a live remote commitment.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
import re

from keiba_win_only_regime_sidecar import (
    verify_companion, _code_manifest, SCORE_SCHEMA,
    SCORED_STATUS,
)
from keiba_win_only_shadow_lane import (
    verify_win_only, _model_code_manifest,
)
import keiba_win_only_github_receipt as parent_proof
from keiba_nextprice_pr_comment_attestation import _gh_json
from odds_shadow_freeze_score import _aware

ANCHOR_REPO="zuizui0223/keiba"
ANCHOR_PR=37
EXPECTED_AUTHOR="zuizui0223"
MARKER="KEIBA_BPLUS_SMOOTH_HARD_NOINFO_COMPANION_SHA_V1"
SCHEMA="KEIBA_WIN_ONLY_BPLUS_REMOTE_COMMENT_CLAIM_V1"
STATUS_PREPARED="BPLUS_SHA_COMMENT_PREPARED_NOT_POSTED"
STATUS_FIXTURE="HOLD_BPLUS_OFFLINE_COMMENT_NOT_REMOTE_CERTIFICATE"
STATUS_REMOTE="BPLUS_AND_PARENT_GITHUB_SHA_CREATED_BEFORE_Q2"
STATUS_BOUND="BPLUS_AND_PARENT_REMOTE_SHA_BOUND_TO_LOCAL_UNVERIFIED_Q2"
MAX_COMMENT_PAGES=20
SAFE_RACE_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,95}$")
SAFE_SHA=re.compile(r"^[0-9a-f]{64}$")


def _canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False)


def _claim(parent,frozen,*,fixture=False):
    p=verify_win_only(parent)
    f=verify_companion(frozen)
    if (p["race_id"]!=f["source_race_id"] or
            p["provider"]!=f["source_provider"] or
            p["registered_primary_slot_id"]!=f["registered_slot_id"] or
            p["horse_numbers"]!=f["horse_numbers"] or
            p["target_WIN_window_start"]!=f["target_WIN_window_start"] or
            p["target_WIN_window_end"]!=f["target_WIN_window_end"] or
            p["source_second_WIN_received"]!=f["source_second_WIN_received"] or
            parent["seal_sha256_of_canonical_payload"]!=
                f["parent_original_six_model_freeze_SHA256"]):
        raise ValueError("HOLD_BPLUS_DIFFERENT_RACE_SOURCE_SHA_OR_TARGET")
    if (not fixture and
            not (p["card_operator_provenance"]==
                 f["source_provenance"]=="authorized_private_local_export"
                 and p["operator_rights_confirmed_locally_only"] is True
                 and f["operator_rights_reviewed_locally_only"] is True)):
        raise ValueError("HOLD_BPLUS_NOT_AUTHORIZED_TO_PREPARE_PUBLIC_COMMENT")
    if not fixture and (p["model_code_content_SHA256"]!=
            _model_code_manifest() or
            f["code_file_SHA256"]!=_code_manifest()):
        raise ValueError("HOLD_BPLUS_MODEL_VERSION_CHANGED_SINCE_FREEZE")
    rid=p["race_id"]
    parent_sha=parent["seal_sha256_of_canonical_payload"]
    sidecar_sha=frozen["sidecar_local_SHA256_not_remote_receipt"]
    if (not isinstance(rid,str) or not SAFE_RACE_ID.fullmatch(rid) or
            any(not isinstance(h,str) or not SAFE_SHA.fullmatch(h)
                for h in (parent_sha,sidecar_sha))):
        raise ValueError("HOLD_BPLUS_UNSAFE_RACE_OR_HASH_FOR_PUBLIC_COMMENT")
    return {
        "schema":SCHEMA,
        "research_lane":"B_PLUS_SAME_ONE_RACE_AND_TARGET_AS_WIN_ONLY",
        "repository":ANCHOR_REPO,
        "anchor_pull_request":ANCHOR_PR,
        "race_id":rid,
        "parent_original_six_model_SHA256":parent_sha,
        "sidecar_five_additional_model_SHA256":sidecar_sha,
        "last_source_received_jst":f["source_second_WIN_received"],
        "parent_local_freeze_jst":f["original_parent_freeze_clock"],
        "sidecar_local_freeze_jst":f["sidecar_local_freeze_clock"],
        "target_WIN_window_start_jst":f["target_WIN_window_start"],
        "target_WIN_window_end_jst":f["target_WIN_window_end"],
        "scheduled_post_jst":f["scheduled_post"],
        "unchanged_parent_model_count":6,
        "added_fixed_candidate_count":5,
        "one_same_race_target_not_independent_trials":True,
        "original_odds_card_stakes_and_model_vectors_NOT_in_comment":True,
    }


def _body(claim):
    return MARKER+"\n"+_canonical(claim)


def prepare(parent,frozen):
    claim=_claim(parent,frozen)
    body=_body(claim)
    if (len(body)>2200 or "odds_by_horse_number" in body or
            "fixed_next_quote_model_indices" in body or
            "horse_numbers" in body or
            "sidecar_price_candidate_indices" in body or
            "source_url" in body):
        raise ValueError("HOLD_BPLUS_PRIVATE_RAW_MODEL_VALUES_IN_PUBLIC_COMMENT")
    return {
        "status":STATUS_PREPARED,
        "post_once_to_existing_PR37_URL":
            f"https://github.com/{ANCHOR_REPO}/pull/{ANCHOR_PR}",
        "sidecar_sha_only_comment_NOT_POSTED":body,
        "parent_six_sha256":claim["parent_original_six_model_SHA256"],
        "sidecar_five_sha256":claim["sidecar_five_additional_model_SHA256"],
        "explicit_operator_POST_action_required":True,
        "this_tool_never_posts_GitHub_comment":True,
        "actual_GitHub_SHA_timestamp_verified":False,
    }


def _race_in_comment(body):
    if not isinstance(body,str) or not body.startswith(MARKER+"\n"):
        return None
    match=re.search(r'"race_id"\s*:\s*"([^"\n]{1,96})"',body)
    return match.group(1) if match else "MALFORMED_RACE_ID"


def _evaluate(parent,frozen,comments,*,fixture=False):
    claim=_claim(parent,frozen,fixture=fixture)
    if not isinstance(comments,list):
        raise ValueError("HOLD_BPLUS_COMMENT_HISTORY_NOT_COMPLETE_LIST")
    matching=[x for x in comments
              if isinstance(x,dict) and
              _race_in_comment(x.get("body"))==claim["race_id"]]
    if len(matching)!=1:
        raise ValueError("HOLD_BPLUS_NO_UNIQUE_CURRENT_SHA_COMMENT_FOR_RACE")
    comment=matching[0]
    ident=comment.get("id")
    issue=f"https://api.github.com/repos/{ANCHOR_REPO}/issues/{ANCHOR_PR}"
    html=f"https://github.com/{ANCHOR_REPO}/pull/{ANCHOR_PR}#issuecomment-{ident}"
    if (type(ident) is not int or ident<1 or
            not isinstance(comment.get("user"),dict) or
            comment["user"].get("login")!=EXPECTED_AUTHOR or
            comment.get("issue_url")!=issue or
            comment.get("html_url")!=html or
            comment.get("body")!=_body(claim)):
        raise ValueError("HOLD_BPLUS_WRONG_OWNER_PR_COMMENT_OR_SHA_BODY")
    created=_aware(comment.get("created_at"))
    updated=_aware(comment.get("updated_at"))
    if created!=updated:
        raise ValueError("HOLD_BPLUS_SHA_COMMENT_EDITED")
    received=_aware(claim["last_source_received_jst"])
    parent_local=_aware(claim["parent_local_freeze_jst"])
    sidecar_local=_aware(claim["sidecar_local_freeze_jst"])
    target_start=_aware(claim["target_WIN_window_start_jst"])
    target_end=_aware(claim["target_WIN_window_end_jst"])
    post=_aware(claim["scheduled_post_jst"])
    if not (received<=parent_local<=sidecar_local<=created<
            target_start<=target_end<post-timedelta(minutes=10)):
        raise ValueError("HOLD_BPLUS_GITHUB_SHA_NOT_BEFORE_NEXT_PRICE_TARGET")
    return {
        "schema":SCHEMA,
        "race_id":claim["race_id"],
        "parent_original_six_model_SHA256":
            claim["parent_original_six_model_SHA256"],
        "sidecar_five_additional_model_SHA256":
            claim["sidecar_five_additional_model_SHA256"],
        "github_sidecar_comment_id":ident,
        "github_sidecar_comment_url":html,
        "github_sidecar_created_at":created.isoformat(),
        "target_window_start":target_start.isoformat(),
        "target_window_end":target_end.isoformat(),
        "original_source_clock_not_externally_authenticated":True,
        "comment_or_source_deletion_history_not_recoverable":True,
        "real_stakes_horse_GPS_criticality_or_wagering_EV":"HOLD",
    }


def inspect_fixture(parent,frozen,comments):
    structured=_evaluate(parent,frozen,comments,fixture=True)
    return {
        **structured,"status":STATUS_FIXTURE,
        "live_GitHub_API_parent_and_sidecar_comment_GET":False,
        "both_models_externally_pretarget_timewitnessed":False,
    }


def _all_sidecar_comments():
    out=[]
    seen=set()
    for page in range(1,MAX_COMMENT_PAGES+1):
        batch=_gh_json(
            f"/repos/{ANCHOR_REPO}/issues/{ANCHOR_PR}/comments"
            f"?per_page=100&page={page}")
        if not isinstance(batch,list):
            raise ValueError("HOLD_BPLUS_GITHUB_COMMENTS_API_BAD_RESPONSE")
        for c in batch:
            ident=c.get("id") if isinstance(c,dict) else None
            if type(ident) is not int or ident in seen:
                raise ValueError("HOLD_BPLUS_GITHUB_DUPLICATE_OR_INVALID_COMMENT_ID")
            seen.add(ident)
            out.append(c)
        if len(batch)<100:
            return out
    raise ValueError("HOLD_BPLUS_GITHUB_COMMENT_PAGINATION_UNVERIFIED")


def verify_live(parent,frozen):
    """Requires REAL GitHub REST GET for PR30 parent and PR37 sidecar."""
    _claim(parent,frozen)
    # Parent proof must be genuinely verified from its OWN PR30 thread.
    pproof=parent_proof.verify_live(parent)
    if (pproof.get("status")!=parent_proof.STATUS_REMOTE or
            pproof.get("live_GitHub_API_comment_GET_performed") is not True or
            pproof.get("server_time_pre_next_WIN_target_verified") is not True or
            pproof.get("race_id")!=frozen["payload"]["source_race_id"] or
            pproof.get("frozen_model_SHA256")!=
                parent["seal_sha256_of_canonical_payload"]):
        raise ValueError("HOLD_BPLUS_PARENT_PR30_REMOTE_SHA_NOT_VERIFIED")
    comments=_all_sidecar_comments()
    proof=_evaluate(parent,frozen,comments)
    ident=proof["github_sidecar_comment_id"]
    detail=_gh_json(f"/repos/{ANCHOR_REPO}/issues/comments/{ident}")
    listed=next(x for x in comments if x["id"]==ident)
    if not isinstance(detail,dict):
        raise ValueError("HOLD_BPLUS_GITHUB_COMMENT_DETAIL_NOT_OBJECT")
    for key in ("id","body","created_at","updated_at",
                "issue_url","html_url"):
        if detail.get(key)!=listed.get(key):
            raise ValueError("HOLD_BPLUS_GITHUB_LIST_VS_DETAIL_CHANGED")
    if detail.get("user",{}).get("login")!=EXPECTED_AUTHOR:
        raise ValueError("HOLD_BPLUS_GITHUB_COMMENT_OWNER_IN_DETAIL_CHANGED")
    parent_at=_aware(pproof["github_server_created_at_claim"])
    sidecar_at=_aware(proof["github_sidecar_created_at"])
    target=_aware(proof["target_window_start"])
    if not parent_at<=sidecar_at<target:
        raise ValueError("HOLD_BPLUS_PARENT_SHA_NOT_POSTED_BEFORE_SIDECAR_AND_Q2")
    return {
        **proof,"status":STATUS_REMOTE,
        "github_parent_comment_url":pproof["github_comment_url"],
        "github_parent_created_at":parent_at.isoformat(),
        "both_parent_and_sidecar_SHA_created_before_target":True,
        "live_GitHub_API_parent_and_sidecar_comment_GET":True,
        "only_DIGEST_timewitnessed_NOT_original_quote_truth":True,
        "licensed_source_ownership_and_capture_completeness_NOT_proven":True,
    }


def bind_local_score(proof,score):
    """Typed linkage is NOT proof that original JRA quotes are truthful."""
    if (not isinstance(proof,dict) or proof.get("status")!=STATUS_REMOTE or
            proof.get("live_GitHub_API_parent_and_sidecar_comment_GET")
                is not True or
            proof.get("both_parent_and_sidecar_SHA_created_before_target")
                is not True):
        raise ValueError("HOLD_BPLUS_NOT_DUAL_LIVE_GITHUB_PRESSEAL_PROOF")
    if (not isinstance(score,dict) or score.get("schema")!=SCORE_SCHEMA or
            score.get("status")!=SCORED_STATUS or
            score.get("race_id")!=proof["race_id"] or
            score.get("parent_original_six_model_SHA256")!=
                proof["parent_original_six_model_SHA256"] or
            score.get("sidecar_local_SHA256")!=
                proof["sidecar_five_additional_model_SHA256"] or
            score.get("independent_race_count_not_six_plus_five")!=1 or
            score.get("new_independently_proven_next_market_trial") is not False):
        raise ValueError("HOLD_BPLUS_SCORE_NOT_FROM_SAME_DUAL_FROZEN_RACE")
    t=_aware(score["source_target_published"])
    rx=_aware(score["source_target_received"])
    if not (_aware(proof["github_sidecar_created_at"])<
            _aware(proof["target_window_start"])<=t<=
            _aware(proof["target_window_end"]) and t<=rx):
        raise ValueError("HOLD_BPLUS_LOCAL_Q2_NOT_IN_REMOTE_DECLARED_WINDOW")
    return {
        "status":STATUS_BOUND,
        "race_id":proof["race_id"],
        "original_six_model_remote_SHA_comment":proof[
            "github_parent_comment_url"],
        "sidecar_five_model_remote_SHA_comment":proof[
            "github_sidecar_comment_url"],
        "same_original_next_quote_source_published_local_claim":
            score["source_target_published"],
        "same_original_next_quote_source_received_local_claim":
            score["source_target_received"],
        "eleven_models_scored_on_one_locally_claimed_q2":True,
        "remote_GitHub_proves_digest_preexistence_only":True,
        "real_market_updated_at_or_feed_completeness_not_authenticated":True,
        "new_independently_verified_JRA_next_market_trials":0,
        "market_dynamics_social_threshold_horse_GPS_and_EV":"HOLD",
    }


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    for name in ("prepare","verify-live"):
        op=sub.add_parser(name)
        op.add_argument("--original-win-only-freeze",type=Path,required=True)
        op.add_argument("--sidecar-freeze",type=Path,required=True)
        op.add_argument("--private-output",type=Path,required=True)
        if name=="verify-live":
            op.add_argument("--private-local-score",type=Path)
    args=parser.parse_args()
    parent=_load(args.original_win_only_freeze)
    frozen=_load(args.sidecar_freeze)
    if args.command=="prepare":
        result=prepare(parent,frozen)
    else:
        result=verify_live(parent,frozen)
        if args.private_local_score:
            result=bind_local_score(result,_load(args.private_local_score))
    args.private_output.parent.mkdir(parents=True,exist_ok=True)
    with args.private_output.open("x",encoding="utf-8") as out:
        out.write(json.dumps(result,ensure_ascii=False,indent=2,
                             allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "GitHub_POST_was_not_performed":True,
        "independently_verified_actual_JRA_source":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
