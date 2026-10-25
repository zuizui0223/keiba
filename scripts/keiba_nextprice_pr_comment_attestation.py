#!/usr/bin/env python3
"""Remote SHA-only commitment using GitHub PR ISSUE comments, not Actions.

This resolves one operational blocker in PR22: the SHA-only workflow_dispatch
is NOT installed on main, so a Draft branch cannot run it. Instead, publish
ONLY this strictly formatted digest manifest as an issue-type comment on
the already-existing Draft PR #22, then independently fetch GitHub's REST
server-created timestamp and the complete issue-comment history.

Security/causal time CONTRACT for predicting a NEXT market quote (stricter
than simply being before the horse race):
  last source receipt <= local forecast freeze <= GitHub comment creation
  < BEGINNING of locked future-quote target window
  AND GitHub creation < scheduled post minus 10 minutes.
This avoids publishing a hash after an already-observed price target.

A GitHub-created-at record proves at most that a SHA *was publicly posted*
before the next-market target. It does NOT establish provider truth, source
rights, original horse history receipt, complete next-price capture, actual
stake counts, bookmaker prices, or a calibrated/forward winning edge.

Comments can be deleted; the existing comment set cannot prove historical
deleted attempts absent. Enforce one currently visible race commitment on
this fixed PR and reject any edits, extra fields, other authors and any
same-race duplicates (whether posted before or after). This is NOT equivalent
to an append-only independently archived receipt.

The body emitted by 'prepare' contains only race ID, 64-digit SHA and
declared nonsecret race/source/target times. It is NOT POSTED automatically.
A user must explicitly make the single issue comment after privately
checking the source and BEFORE the first target quote time.

The 'inspect-fixture' mode can only return HOLD even when fabricated
timestamps pass. 'verify-live' calls authenticated GitHub CLI GET endpoints
itself and only then can describe the *SHA timestamp* as verified.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
import re
import subprocess

from keiba_private_multirace_winwide_shadow import (verify_freeze,SCORE_SCHEMA,SCORE_STATUS)
from odds_shadow_freeze_score import _aware

REPOSITORY="zuizui0223/keiba"
COMMIT_PR=22
COMMIT_AUTHOR="zuizui0223"
MARKER="KEIBA_SHA_ONLY_NEXT_MARKET_PR_COMMENT_V1"
SCHEMA="KEIBA_SHA_ONLY_NEXT_MARKET_COMMITMENT_V1"
STATUS_LOCAL="HOLD_OFFLINE_GITHUB_COMMENT_FIXTURE_NOT_SERVER_ATTESTATION"
STATUS_PREPARED="PREPARED_PUBLIC_SHA_ONLY_COMMENT_NOT_POSTED"
STATUS_REMOTE="GITHUB_SERVER_CREATED_BEFORE_NEXT_MARKET_SHA_ONLY_VERIFIED"
SAFE_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,95}$")
SAFE_SHA=re.compile(r"^[0-9a-f]{64}$")


def _canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False)


def _commitment(freeze, *, fixture=False):
    payload=verify_freeze(freeze)
    if (payload["source_provenance"]!="authorized_private_local_export"
            and not fixture):
        raise ValueError("HOLD_REPLAY_OR_SYNTHETIC_IS_NOT_AN_AUTHORIZED_LIVE_COMMITMENT")
    race=payload["race_id"]
    digest=freeze["seal_sha256_of_canonical_payload"]
    if (not isinstance(race,str) or not SAFE_ID.fullmatch(race)
            or not isinstance(digest,str) or not SAFE_SHA.fullmatch(digest)):
        raise ValueError("HOLD_UNSAFE_RACE_ID_OR_SHA")
    data={
        "schema":SCHEMA,
        "repo":REPOSITORY,
        "commitment_pr":COMMIT_PR,
        "race_id":race,
        "seal_sha256":digest,
        "last_source_received_jst":max(
            _aware(payload["middle_WIN_quote_received_at"]),
            _aware(payload["middle_WIDE_quote_received_at"])).isoformat(),
        "local_freeze_created_at_jst":payload["local_freeze_created_at"],
        "next_quote_target_window_start_jst":
            payload["next_quote_min_published_at"],
        "next_quote_target_window_end_jst":
            payload["next_quote_max_published_at"],
        "scheduled_post_jst":payload["scheduled_post_jst"],
        "model_count":len(payload["candidate_predictions"]),
        "no_raw_market_prices_predictions_or_horse_history_in_comment":True,
    }
    return data


def prepare_comment(freeze):
    """No network, no GitHub POST, never returns private forecast content."""
    data=_commitment(freeze)
    body=_comment_body(data)
    if len(body)>1600 or "candidate_predictions" in body:
        raise ValueError("HOLD_PUBLIC_COMMENT_MAY_LEAK_PRIVATE_PREDICTIONS")
    return {
        "status":STATUS_PREPARED,
        "body_to_post_once_in_PR22_comment":body,
        "anchor_url":"https://github.com/zuizui0223/keiba/pull/22",
        "expected_race_id":data["race_id"],
        "remote_sha_publication_confirmed":False,
        "private_forecast_content_uploaded":False,
        "requires_explicit_user_action_to_post":True,
    }


def _comment_body(data):
    return MARKER+"\n"+_canonical(data)


def _decode_race(body):
    """Distinguish a duplicate attempt even if the rest is malformed."""
    if not isinstance(body,str) or not body.startswith(MARKER+"\n"):
        return None
    for key in ("race_id",):
        match=re.search(r'"'+key+r'"\s*:\s*"([^"\n]{1,96})"',body)
        if match:
            return match.group(1)
    return "MALFORMED_RACE_ID_IN_SHA_COMMITMENT"


def _evaluate(freeze, comments, *, fixture=False):
    """Structural check ONLY; does not itself assert remote authenticity.

    The ONLY caller allowed to promote to STATUS_REMOTE is verify_live(),
    which independently fetches the complete GitHub REST comment set.
    """
    data=_commitment(freeze,fixture=fixture)
    if not isinstance(comments,list) or not comments:
        raise ValueError("HOLD_NO_GITHUB_COMMITMENT_COMMENT_WAS_FOUND")
    race=data["race_id"]
    race_related=[x for x in comments
                  if _decode_race(x.get("body"))==race]
    if len(race_related)!=1:
        raise ValueError("HOLD_ABSENT_OR_MULTIPLE_SAME_RACE_SHA_COMMITMENT_ATTEMPTS")
    c=race_related[0]
    if (not isinstance(c.get("id"),int) or c["id"]<=0 or
            not isinstance(c.get("user"),dict) or
            c["user"].get("login")!=COMMIT_AUTHOR):
        raise ValueError("HOLD_GITHUB_COMMENT_AUTHOR_OR_IDENTIFIER")
    issue_url=f"https://api.github.com/repos/{REPOSITORY}/issues/{COMMIT_PR}"
    comment_url=(f"https://github.com/{REPOSITORY}/pull/{COMMIT_PR}"
                 f"#issuecomment-{c['id']}")
    if (c.get("issue_url")!=issue_url or
            c.get("html_url")!=comment_url):
        raise ValueError("HOLD_GITHUB_COMMENT_WRONG_ISSUE_OR_URL")
    if c.get("body")!=_comment_body(data):
        raise ValueError("HOLD_COMMITMENT_BODY_OR_SEALED_PAYLOAD_MISMATCH")
    t=_aware(c.get("created_at"))
    changed=_aware(c.get("updated_at"))
    if t!=changed:
        raise ValueError("HOLD_ISSUE_COMMENT_WAS_EDITED_AFTER_ORIGINAL_CREATION")
    source_rx=_aware(data["last_source_received_jst"])
    freeze_created=_aware(data["local_freeze_created_at_jst"])
    target_start=_aware(data["next_quote_target_window_start_jst"])
    target_end=_aware(data["next_quote_target_window_end_jst"])
    post=_aware(data["scheduled_post_jst"])
    if not (source_rx<=freeze_created<=t<target_start<=target_end
            <post-timedelta(minutes=10)):
        raise ValueError("HOLD_GITHUB_SHA_CREATED_AFTER_TARGET_OR_CLOCK_ORDER")
    return {
        "schema":SCHEMA,
        "status":"STRUCTURAL_ONLY_NOT_INDEPENDENT_REMOTE_PROOF",
        "race_id":race,
        "sha256_of_full_private_frozen_model":data["seal_sha256"],
        "github_server_comment_created_at_claim":t.isoformat(),
        "github_comment_url":comment_url,
        "github_comment_id":c["id"],
        "anchor_pr":COMMIT_PR,
        "target_market_window_begins_at":target_start.isoformat(),
        "race_post_at":post.isoformat(),
        "margin_to_market_target_minutes":(target_start-t).total_seconds()/60,
        "github_updated_at_equals_created_at":True,
        "only_one_currently_visible_race_sha_on_fixed_PR22":True,
        "deleted_past_issue_comments_cannot_be_detected":True,
        "provider_market_clocks_not_authenticated_by_GitHub_SHA":True,
        "actual_target_quote_completeness_not_externally_proven":True,
        "probability_calibration_market_criticality_or_wager_ROI":"HOLD",
        "unchanged_original_Kikka_M0_M2_and_v31":True,
    }


def inspect_fixture(freeze,comments):
    """Untrusted JSON can NEVER supply external timestamp evidence."""
    x=_evaluate(freeze,comments,fixture=True)
    return {**x,"status":STATUS_LOCAL,
            "independent_GitHub_API_fetch_performed":False,
            "fixture_timestamps_can_be_invented":True,
            "external_sha_pre_target_verified":False}


def _gh_json(uri):
    try:
        got=subprocess.run(["gh","api",uri],check=True,text=True,
                           capture_output=True)
    except (FileNotFoundError,subprocess.CalledProcessError) as e:
        raise ValueError("HOLD_CANNOT_FETCH_GITHUB_SERVER_COMMENTS_INDEPENDENTLY") from e
    try:
        return json.loads(got.stdout)
    except json.JSONDecodeError as e:
        raise ValueError("HOLD_GITHUB_SERVER_COMMENTS_NOT_JSON") from e


def _fetch_all_comments():
    """Fail closed if pagination is incomplete; no hidden earlier attempt."""
    comments=[]
    seen=set()
    for page in range(1,21):
        uri=(f"/repos/{REPOSITORY}/issues/{COMMIT_PR}/comments"
             f"?per_page=100&page={page}")
        x=_gh_json(uri)
        if not isinstance(x,list):
            raise ValueError("HOLD_INVALID_GITHUB_PR_COMMENT_API_COLLECTION")
        for comment in x:
            if (not isinstance(comment,dict) or
                    type(comment.get("id")) is not int or
                    comment["id"] in seen):
                raise ValueError("HOLD_DUPLICATE_OR_MALFORMED_GITHUB_COMMENT")
            seen.add(comment["id"])
            comments.append(comment)
        if len(x)<100:
            return comments
    raise ValueError("HOLD_GITHUB_COMMENT_HISTORY_EXCEEDS_AUDIT_PAGINATION_LIMIT")


def verify_live(freeze):
    """Live comment API GET; no fixture/API data can be supplied by user."""
    # Restrict to private-source-enabled forecasts; mocks used by unit tests
    # may verify structural gates but cannot create a real Github receipt.
    proof_data=_commitment(freeze)
    comments=_fetch_all_comments()
    structure=_evaluate(freeze,comments,fixture=False)
    comment_id=structure["github_comment_id"]
    remote=_gh_json(f"/repos/{REPOSITORY}/issues/comments/{comment_id}")
    listed=next(x for x in comments if x["id"]==comment_id)
    for k in ("id","created_at","updated_at","body","issue_url","html_url"):
        if remote.get(k)!=listed.get(k):
            raise ValueError("HOLD_GITHUB_SINGLE_COMMENT_AND_HISTORY_DISAGREE")
    if remote.get("user",{}).get("login")!=COMMIT_AUTHOR:
        raise ValueError("HOLD_GITHUB_COMMIT_AUTHOR_DRIFT")
    if proof_data["seal_sha256"]!=structure["sha256_of_full_private_frozen_model"]:
        raise ValueError("HOLD_GITHUB_DIGEST_CHANGED_AFTER_VERIFICATION")
    return {
        **structure,
        "status":STATUS_REMOTE,
        "independent_GitHub_API_fetch_performed":True,
        "external_sha_pre_target_verified":True,
        "source_market_receipt_externally_authenticated":False,
        "target_capture_stream_independently_complete":False,
        "formal_v31_or_independent_predictive_superiority_established":False,
    }


def bind_scored_next_market_to_proof(proof, score):
    """Match a LOCAL next-price score to a remotely proven SHA timestamp.

    Does not independently verify the completeness of the target quote
    capture. A correct score with a real GitHub pretarget commitment is
    still *not* an authenticated betting-pool or horse-outcome experiment.
    """
    if (not isinstance(proof,dict) or proof.get("status")!=STATUS_REMOTE
            or proof.get("external_sha_pre_target_verified") is not True
            or proof.get("independent_GitHub_API_fetch_performed") is not True):
        raise ValueError("HOLD_SHA_PROOF_NOT_INDEPENDENT_GITHUB_VERIFIED")
    if (not isinstance(score,dict) or score.get("schema")!=SCORE_SCHEMA
            or score.get("status")!=SCORE_STATUS
            or score.get("race_id")!=proof["race_id"]
            or score.get("sealed_prediction_sha256")!=
               proof["sha256_of_full_private_frozen_model"]
            or score.get("external_preseal_authenticated") is not False
            or score.get("capture_stream_independently_complete") is not False):
        raise ValueError("HOLD_LOCAL_SCORE_AND_EXTERNALLY_PROVEN_SHA_DO_NOT_MATCH")
    observed_at=_aware(score["selected_first_eligible_source_published_at"])
    recorded_at=_aware(proof["github_server_comment_created_at_claim"])
    min_target=_aware(proof["target_market_window_begins_at"])
    if not recorded_at<min_target<=observed_at:
        raise ValueError("HOLD_TARGET_PRICE_PUBLISHED_BEFORE_GITHUB_COMMITMENT")
    return {
        "status":"SHA_CREATED_BEFORE_TARGET_VERIFIED_SCORE_CAPTURE_STILL_LOCAL",
        "race_id":proof["race_id"],
        "github_comment_url":proof["github_comment_url"],
        "sealed_SHA256":proof["sha256_of_full_private_frozen_model"],
        "score_primary_TV_model_values": {
            name:{"next_price_index_TV_pp":value["next_price_index_TV_pp"],
                  "next_price_index_KL_nats":value["next_price_index_KL_nats"]}
            for name,value in score["all_model_scores"].items()
        },
        "external_GitHub_SHA_creation_time_verified":True,
        "source_receipts_independently_verified":False,
        "later_price_capture_completeness_independently_verified":False,
        "true_win_place_probability_calibration":False,
        "wager_profit_or_market_phase_transition":"HOLD",
        "formal_v31_evaluation_unchanged":True,
    }


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,
                               allow_nan=False)+"\n",encoding="utf-8")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("prepare")
    a.add_argument("--freeze",required=True,type=Path)
    a.add_argument("--output",required=True,type=Path)
    b=sub.add_parser("inspect-fixture")
    b.add_argument("--freeze",required=True,type=Path)
    b.add_argument("--comments-json",required=True,type=Path)
    b.add_argument("--output",required=True,type=Path)
    c=sub.add_parser("verify-live")
    c.add_argument("--freeze",required=True,type=Path)
    c.add_argument("--output",required=True,type=Path)
    c.add_argument("--score",type=Path)
    args=p.parse_args()
    freeze=read_json(args.freeze)
    if args.action=="prepare":
        out=prepare_comment(freeze)
    elif args.action=="inspect-fixture":
        out=inspect_fixture(freeze,read_json(args.comments_json))
    else:
        out=verify_live(freeze)
        if args.score is not None:
            out=bind_scored_next_market_to_proof(out,read_json(args.score))
    write_json(args.output,out)
    print(json.dumps({
        "status":out["status"],
        "public_digest_only":args.action=="prepare",
        "independent_GitHub_server_timestamp":
            out.get("external_sha_pre_target_verified",False),
    },ensure_ascii=False))


if __name__=="__main__":
    main()
