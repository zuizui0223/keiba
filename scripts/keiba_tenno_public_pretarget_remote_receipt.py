#!/usr/bin/env python3
"""Typed SHA-only GitHub server proof for PUBLIC-NEWS -> FUTURE-WIN lane C.

PR #41 is a dedicated anchor distinct from PR #30 (six physically linked
models), PR #37 (five attached models), and the full WIN+WIDE PR #22.
A GitHub comment only witnesses pretarget existence of THIS precomputed
PUBLIC-ARTICLE forecast. It does NOT authenticate JRA quote publication,
independently verify licensed receipt/complete q2 or prove betting value.

"prepare" never POSTs; operator must separately permit posting. "verify-live"
reads all issue comments plus individual matching comment through real GitHub
REST with gh api and validates GitHub's server-created timestamp. Offline
fixture verification can NEVER claim independent live attestation.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re

from keiba_tenno_public_pretarget_future_shadow import (
    freeze,verify_freeze,_canonical,
    TARGET_START,TARGET_END,POST,
    SCORE_SCHEMA,SCORED_STATUS,
)
from keiba_nextprice_pr_comment_attestation import _gh_json
from odds_shadow_freeze_score import _aware

ANCHOR_REPO="zuizui0223/keiba"
ANCHOR_PR=41
EXPECTED_AUTHOR="zuizui0223"
SCHEMA="KEIBA_TENNO_PUBLIC_NEWS_PRETARGET_COMMENT_CLAIM_V1"
MARKER="KEIBA_PUBLIC_NEWS_F0_TO_FIXED_NEXTWIN_SHA_V1"
STATUS_PREPARED="PUBLIC_NEWS_SHA_PREPARED_NOT_GITHUB_POSTED"
STATUS_FIXTURE="HOLD_OFFLINE_PUBLIC_NEWS_COMMENT_NOT_LIVE_PROOF"
STATUS_REMOTE="GITHUB_SERVER_PUBLIC_NEWS_SHA_BEFORE_FIXED_NEXTWIN_TARGET"
STATUS_LOCALLY_SCORED="PUBLIC_NEWS_SHA_PRETARGET_LOCAL_ONLY_TARGET_SCORING"
SAFE_SHA=re.compile(r"^[0-9a-f]{64}$")
MAX_PAGES=20


def _claim(frozen):
    p=verify_freeze(frozen)
    digest=frozen["sha256_of_canonical_frozen_payload"]
    if not isinstance(digest,str) or not SAFE_SHA.fullmatch(digest):
        raise ValueError("HOLD_NEWS_PUBLIC_SHA_NOT_HEX64")
    return {
        "schema":SCHEMA,
        "repository":ANCHOR_REPO,
        "anchor_PR":ANCHOR_PR,
        "research_lane":"PUBLIC_NEWS_ONLY_DISTINCT_FROM_PR30_AND_PR37",
        "registered_slot":p["registered_fixed_2026_race_slot"],
        "frozen_full_17_public_forecast_SHA256":digest,
        "source_1742_news_published_jst":
            p["source_article_published_at_jst_NOT_original_market_update"],
        "source_public_article_URL":p["source_url"],
        "source_is_editorial_NOT_vendor_original":True,
        "target_provider_predeclared_not_same_as_news":
            p["target_source_provider_fixed_before_tomorrow"],
        "fixed_future_source_update_start_jst":TARGET_START,
        "fixed_future_source_update_end_jst":TARGET_END,
        "scheduled_post_jst":POST,
        "frozen_model_count":4,
        "no_original_prices_or_licensed_data_in_comment":True,
    }


def _body(c):
    return MARKER+"\n"+_canonical(c)


def prepare(frozen):
    claim=_claim(frozen)
    comment=_body(claim)
    if (len(comment)>1900 or "frozen_price_index_forecasts" in comment
            or "odds_by_horse_number" in comment):
        raise ValueError("HOLD_PUBLIC_NEWS_SHA_COMMENT_UNSAFE")
    return {
        "status":STATUS_PREPARED,
        "anchor_PR_to_post_once":f"https://github.com/{ANCHOR_REPO}/pull/{ANCHOR_PR}",
        "sha_only_comment_BODY_not_posted":comment,
        "sha256":claim["frozen_full_17_public_forecast_SHA256"],
        "requires_explicit_operator_POST":True,
        "created_comment":False,
        "original_source_or_future_quote_independently_attested":False,
    }


def _is_this_race_attempt(body):
    return isinstance(body,str) and body.startswith(MARKER+"\n")


def _evaluate(frozen,comments):
    claim=_claim(frozen)
    if not isinstance(comments,list):
        raise ValueError("HOLD_PUBLIC_NEWS_GITHUB_COMMENT_LIST_MISSING")
    related=[c for c in comments if isinstance(c,dict) and
             _is_this_race_attempt(c.get("body"))]
    if len(related)!=1:
        raise ValueError("HOLD_NEWS_ZERO_OR_MULTIPLE_SHA_ATTEMPTS")
    c=related[0]
    ident=c.get("id")
    if (type(ident) is not int or ident<=0 or
            c.get("body")!=_body(claim) or
            not isinstance(c.get("user"),dict) or
            c["user"].get("login")!=EXPECTED_AUTHOR or
            c.get("issue_url")!=
                f"https://api.github.com/repos/{ANCHOR_REPO}/issues/{ANCHOR_PR}" or
            c.get("html_url")!=
                f"https://github.com/{ANCHOR_REPO}/pull/{ANCHOR_PR}#issuecomment-{ident}"):
        raise ValueError("HOLD_NEWS_WRONG_OWNER_TARGET_OR_PUBLIC_SHA_COMMENT")
    created=_aware(c.get("created_at"))
    updated=_aware(c.get("updated_at"))
    news=_aware(claim["source_1742_news_published_jst"])
    target=_aware(TARGET_START)
    end=_aware(TARGET_END)
    post=_aware(POST)
    if created!=updated:
        raise ValueError("HOLD_NEWS_GITHUB_SHA_COMMENT_WAS_EDITED")
    if not news<=created<target<=end<post:
        raise ValueError("HOLD_NEWS_REMOTE_COMMITMENT_NOT_BEFORE_TARGET")
    return {
        "schema":SCHEMA,
        "race_slot":claim["registered_slot"],
        "status":"STRUCTURAL_ONLY_NOT_REMOTE_PROOF",
        "public_news_frozen_model_SHA256":
            claim["frozen_full_17_public_forecast_SHA256"],
        "github_server_created_at_claim":created.isoformat(),
        "github_comment_id":ident,
        "github_comment_url":c["html_url"],
        "source_article_is_not_JRA_original_quote":True,
        "future_target_stream_completeness_not_verified":True,
        "public_only_distinct_from_11_linked_models":True,
        "market_herding_horse_GPS_and_bet_ROI":"HOLD",
    }


def inspect_fixture(frozen,comments):
    return {
        **_evaluate(frozen,comments),
        "status":STATUS_FIXTURE,
        "real_GitHub_server_comment_verified":False,
        "fake_offline_comment_not_pretarget_proof":True,
    }


def _all_comments():
    entries=[]
    ids=set()
    for page in range(1,MAX_PAGES+1):
        arr=_gh_json(
            f"/repos/{ANCHOR_REPO}/issues/{ANCHOR_PR}/comments"
            f"?per_page=100&page={page}")
        if not isinstance(arr,list):
            raise ValueError("HOLD_NEWS_GITHUB_COMMENTS_API_WRONG_SHAPE")
        for c in arr:
            ident=c.get("id") if isinstance(c,dict) else None
            if type(ident) is not int or ident<=0 or ident in ids:
                raise ValueError("HOLD_NEWS_GITHUB_COMMENT_ID_INVALID_OR_DUPLICATE")
            ids.add(ident); entries.append(c)
        if len(arr)<100:
            return entries
    raise ValueError("HOLD_NEWS_GITHUB_UNBOUNDED_PAGINATION")


def verify_live(frozen):
    """Only real gh api list + detail fetch produces true remote SHA proof."""
    _claim(frozen)
    comments=_all_comments()
    v=_evaluate(frozen,comments)
    ident=v["github_comment_id"]
    single=_gh_json(f"/repos/{ANCHOR_REPO}/issues/comments/{ident}")
    listed=next(c for c in comments if c["id"]==ident)
    if not isinstance(single,dict):
        raise ValueError("HOLD_NEWS_GITHUB_SINGLE_COMMENT_MISSING")
    for k in ("id","created_at","updated_at","body","issue_url","html_url"):
        if single.get(k)!=listed.get(k):
            raise ValueError("HOLD_NEWS_GITHUB_LIST_AND_DETAIL_DISAGREE")
    if single.get("user",{}).get("login")!=EXPECTED_AUTHOR:
        raise ValueError("HOLD_NEWS_GITHUB_REMOTE_OWNER_MISMATCH")
    return {
        **v,
        "status":STATUS_REMOTE,
        "real_GitHub_server_comment_verified":True,
        "SHA_existed_before_new_market_target_start":True,
        "original_JRA_provider_published_clock_unverified":True,
        "actual_target_quote_and_rights_not_verified":True,
        "new_formal_PR30_or_PR37_11model_prospective_trials":0,
    }


def attach_local_score(proof,score):
    if (not isinstance(proof,dict) or proof.get("status")!=STATUS_REMOTE
            or proof.get("real_GitHub_server_comment_verified") is not True
            or proof.get("SHA_existed_before_new_market_target_start")
                is not True):
        raise ValueError("HOLD_NEWS_NO_LIVE_REMOTE_SHA_CERTIFICATE")
    if (not isinstance(score,dict) or score.get("schema")!=SCORE_SCHEMA or
            score.get("status")!=SCORED_STATUS or
            score.get("registered_slot_id")!=proof["race_slot"] or
            score.get("original_pretarget_public_forecast_sha256")!=
                proof["public_news_frozen_model_SHA256"] or
            score.get("observed_eligible_next_win_targets")!=1 or
            score.get("new_independently_verified_JRA_market_trial")
                is not False):
        raise ValueError("HOLD_NEWS_LOCAL_Q2_NOT_MATCHING_PUBLIC_SHA")
    target=_aware(score["selected_first_eligible_full_WIN_published"])
    rx=_aware(score["selected_full_WIN_locally_received"])
    if not (_aware(proof["github_server_created_at_claim"])<
            _aware(TARGET_START)<=target<=_aware(TARGET_END) and
            target<=rx):
        raise ValueError("HOLD_NEWS_PUBLIC_COMMENT_TOO_LATE_VS_Q2")
    return {
        "status":STATUS_LOCALLY_SCORED,
        "race_slot":proof["race_slot"],
        "public_forecast_sha_existed_pre_target_by_GitHub":True,
        "news_article_and_original_JRA_sources_not_same_provider":True,
        "local_17_full_WIN_index_model_scores":
            score["target_price_index_TV_KL_by_all_four_fixed_models"],
        "original_live_JRA_target_receipt_independently_authenticated":False,
        "formal_11_horse_ABM_PDE_bettor_future_trials":0,
        "no_win_probability_or_expected_bet_ROI_claim":True,
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    op=p.add_subparsers(dest="action",required=True)
    for mode in ("prepare","verify-live"):
        s=op.add_parser(mode)
        s.add_argument("--frozen",type=Path,required=True)
        s.add_argument("--output",type=Path,required=True)
        if mode=="verify-live":
            s.add_argument("--local-score",type=Path)
    z=p.parse_args()
    frozen=_read(z.frozen)
    if z.action=="prepare":
        obj=prepare(frozen)
        summary={"status":obj["status"],"comment_posted_by_tool":False,
                 "sha256":obj["sha256"]}
    else:
        obj=verify_live(frozen)
        if z.local_score:
            obj=attach_local_score(obj,_read(z.local_score))
        summary={"status":obj["status"],
                 "source_original_independently_authenticated":False}
    z.output.parent.mkdir(parents=True,exist_ok=True)
    with z.output.open("x",encoding="utf-8") as fh:
        fh.write(json.dumps(obj,ensure_ascii=False,indent=2,
                            allow_nan=False)+"\n")
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
