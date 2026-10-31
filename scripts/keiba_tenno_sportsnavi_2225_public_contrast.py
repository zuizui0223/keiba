#!/usr/bin/env python3
"""Tenno Oct31 17:42 news vs SportsNavi 22:25 quoted full 17-runner WIN.

The SportsNavi live intermediate WIN page visibly printed "2026/10/31
22:25 更新" with ALL 17 runners. Those 17 displayed odds were inspected
twice and transcribed in a fixed canonical SHA256 declaration; they are
NOT original JRA/JRA-VAN byte-captured data, and the mutable page need
not continue to show the same observation in the future.

The 17:42 full news odds were already declared in PR35. PR41 froze four
news-derived candidate indices on GitHub; its owner-authored SHA-only
comment was created AFTER 22:25, therefore THIS contrast is strictly
retrospective/diagnostic, NEVER a prospective target for PR41.
The legitimate Nov1 14:45..15:05 JRA-VAN target stays untouched.

This file never edits PR41's pinned code/dependencies or source-model SHA,
never reads the race finish, payoff, real stakes or bettor flows, and does
not imply that different publisher articles are atomic market snapshots.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path

from keiba_public_article_vs_real_archival_rank_geometry import (
    _declared_later, rank_contrast, CORROBORATING_NEWS_PUBLISHED
)
from keiba_tenno_public_pretarget_future_shadow import (
    freeze as original_news_freeze,
    TARGET_START, TARGET_END, SLOT, MODEL_NAMES
)

STATUS="FULL_17_PUBLIC_CROSS_PROVIDER_DISPLAY_ODDS_NOT_PROSPECTIVE_Q2"
SOURCE_PAGE_URL="https://sports.yahoo.co.jp/keiba/race/odds/tfw/2605041111"
SOURCE_DISPLAYED_UPDATED_AT="2026-10-31T22:25:00+09:00"
SOURCE_TYPE="SportsNavi publicly displayed intermediate full WIN odds"
EXPECTED_DISPLAY_FIELD_SHA256=(
    "10f80acc48b11e3d5db4dc172d6bc90adbd902e9485dd9a46aac1ab6bac2745f"
)
EXPECTED_ORIGINAL_NEWS_FREEZE_SHA256=(
    "5a3a948194c83af8570abd80d3f2cde6ba3da3e255ad841cb22f6da4e78df7cb"
)
SPORTSNAVI_2225_FULL_WIN=(
    (1,2.7),(2,224.4),(3,8.8),(4,52.5),(5,163.3),
    (6,24.6),(7,2.5),(8,227.2),(9,61.2),(10,46.2),
    (11,10.8),(12,102.8),(13,31.1),(14,113.8),
    (15,98.2),(16,54.3),(17,10.4),
)


def _canonical(data):
    return json.dumps(data,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False)


def _declared_2225():
    if (len(SPORTSNAVI_2225_FULL_WIN)!=17 or
            [n for n,_ in SPORTSNAVI_2225_FULL_WIN]!=list(range(1,18)) or
            any(type(n) is not int or type(o) not in (float,int) or
                not math.isfinite(o) or o<=1
                for n,o in SPORTSNAVI_2225_FULL_WIN)):
        raise ValueError("HOLD_SPORTSNAVI_2225_NOT_COMPLETE_17_WIN")
    prices=dict(SPORTSNAVI_2225_FULL_WIN)
    manifest={
        "source_url":SOURCE_PAGE_URL,
        "source_displayed_updated_at_jst":SOURCE_DISPLAYED_UPDATED_AT,
        "reported_source_type":SOURCE_TYPE,
        "full_field":[[n,repr(float(prices[n]))] for n in sorted(prices)],
    }
    digest=sha256(_canonical(manifest).encode("utf-8")).hexdigest()
    if digest!=EXPECTED_DISPLAY_FIELD_SHA256:
        raise ValueError("HOLD_SPORTSNAVI_PUBLISHED_2225_VALUES_CHANGED")
    if (not datetime.fromisoformat(CORROBORATING_NEWS_PUBLISHED)<
            datetime.fromisoformat(SOURCE_DISPLAYED_UPDATED_AT)<
            datetime.fromisoformat(TARGET_START)<
            datetime.fromisoformat(TARGET_END)):
        raise ValueError("HOLD_SOURCE_DISPLAY_CLOCK_NOT_BEFORE_FUTURE_TARGET")
    return prices,digest


def _index(prices):
    if (set(prices)!=set(range(1,18)) or
            any(type(p) not in (int,float) or p<=1 or not math.isfinite(p)
                for p in prices.values())):
        raise ValueError("HOLD_PUBLIC_ODDS_NOT_17_POSITIVE_DISPLAY_VALUES")
    weights=[1/prices[i] for i in range(1,18)]
    total=sum(weights)
    return [w/total for w in weights]


def _error(source_model,target):
    if (len(source_model)!=17 or len(target)!=17 or
            any(x<=0 or not math.isfinite(x)
                for x in source_model+target)):
        raise ValueError("HOLD_PUBLIC_PRICE_INDEX_NOT_FULL_POSITIVE")
    return {
        "TV_percentage_points":50*sum(abs(x-y)
                                   for x,y in zip(source_model,target)),
        "KL_later_vs_article_model_nats":
            sum(x*math.log(x/y) for x,y in zip(target,source_model)),
    }


def audit():
    before,before_digest=_declared_later()
    after,source_digest=_declared_2225()
    original=original_news_freeze()
    if (original["sha256_of_canonical_frozen_payload"]!=
            EXPECTED_ORIGINAL_NEWS_FREEZE_SHA256 or
            original["payload"]["registered_fixed_2026_race_slot"]!=SLOT or
            set(original["payload"]["frozen_price_index_forecasts"])!=
                set(MODEL_NAMES)):
        raise ValueError("HOLD_PR41_ORIGINAL_NEWS_FROZEN_FOUR_CHANGED")
    change=rank_contrast(before,after)
    q=_index(after)
    evaluations={}
    for name,rows in original["payload"][
            "frozen_price_index_forecasts"].items():
        model=[x["p"] for x in rows]
        evaluations[name]=_error(model,q)
    if (not math.isclose(
            evaluations["PUBLIC_news_M0_persistence"][
                "TV_percentage_points"],
            change["normalized_inverse_quote_TV_percentage_points"],
            abs_tol=1e-12) or
            evaluations["PUBLIC_news_M0_persistence"][
                "TV_percentage_points"]<=0):
        raise ValueError("HOLD_CROSS_PROVIDER_PUBLIC_INDEX_MISMATCH")
    updated=change["individual_display_prices_changed"]
    if (updated!=17 or
            change["strictly_reversed_pair_count"]!=0 or
            change["unique_unordered_horse_pairs"]!=136 or
            not change["top_two_horse_set_preserved"]):
        raise ValueError("HOLD_SPORTSNAVI_2225_SOURCE_PREDECLARED_COMPARISON")
    return {
        "status":STATUS,
        "one_race_not_two_independent_market_experiments":True,
        "race_slot":SLOT,
        "initial_news_published_at_jst_NOT_original_provider_receipt":
            CORROBORATING_NEWS_PUBLISHED,
        "latest_public_page_displayed_updated_at_jst_NOT_original_vendor_receipt":
            SOURCE_DISPLAYED_UPDATED_AT,
        "latest_public_source_url":SOURCE_PAGE_URL,
        "latest_public_source_field_sha256_DECLARED_not_raw_original":
            source_digest,
        "initial_published_news_original_sha256_DECLARED":
            before_digest,
        "frozen_PR41_pretarget_news_four_model_SHA256":
            EXPECTED_ORIGINAL_NEWS_FREEZE_SHA256,
        "source_sportsnavi_complete_horse_count":17,
        "earlier_all_17_news_horse_prices_changed":updated,
        "source_different_public_media_and_vendor":True,
        "source_updated_at_NOT_an_independent_timestamp_of_web_receipt":
            True,
        "cross_public_page_descriptive_price_change":change,
        "old_PR41_four_news_models_same_later_public_quoted_price_DIAGNOSTIC_ONLY":
            evaluations,
        "same_source_17_runner_price_index_support_proxy_NOT_real_vote_or_winprob":
            True,
        "news_1742_vs_2225_comparison_known_before_PR41_GitHub_SHA_comment":
            True,
        "retrospective_diagnostic_NOT_a_PR41_Nov1_target":True,
        "PR41_fixed_Nov1_1445_1505_target_remains_unobserved":True,
        "no_legally_acquired_JRA_VAN_original_WIN_source_bytes":True,
        "no_future_winner_JRA_bettor_votes_or_betting_returns_read":True,
        "new_independently_confirmed_prospective_market_trial":False,
        "PR30_PR37_original_11_models_and_main_sealed_data_unchanged":True,
    }



def remote_GitHub_22h25_not_a_prospective_test():
    """Read REAL PR41 GitHub owner SHA comment, not offline fixture JSON.

    This verifies two separate facts:
      GitHub genuinely witnessed the PR41 digest at a server time;
      the *page-reported* 22:25 quote timestamp is BEFORE that time.
    It cannot attest original SportsNavi clock truth, target license,
    or real JRA-VAN source completeness. It MUST NOT turn 22:25 into
    the preregistered Nov1 14:45..15:05 target.
    """
    from keiba_tenno_public_pretarget_remote_receipt import (
        verify_live, STATUS_REMOTE
    )
    frozen=original_news_freeze()
    proof=verify_live(frozen)
    if (proof.get("status")!=STATUS_REMOTE or
            proof.get("real_GitHub_server_comment_verified") is not True or
            proof.get("public_news_frozen_model_SHA256")!=
                EXPECTED_ORIGINAL_NEWS_FREEZE_SHA256):
        raise ValueError("HOLD_PR41_SHA_NOT_AUTHENTICATED_BY_REAL_GITHUB")
    when=datetime.fromisoformat(proof["github_server_created_at_claim"])
    public=datetime.fromisoformat(SOURCE_DISPLAYED_UPDATED_AT)
    target=datetime.fromisoformat(TARGET_START)
    if not public<when<target:
        raise ValueError("HOLD_2225_PUBLIC_QUOTE_NOT_PROVEN_BEFORE_PR41_GITHUB_SHA")
    return {
        "status":"REAL_PR41_GITHUB_SHA_AFTER_PUBLIC_2225_DECLARED_CLOCK",
        "original_PR41_SHA256":EXPECTED_ORIGINAL_NEWS_FREEZE_SHA256,
        "github_comment_url":proof["github_comment_url"],
        "github_server_created_at_jst":when.isoformat(),
        "public_2225_published_clock_not_original_vendor_receipt":
            SOURCE_DISPLAYED_UPDATED_AT,
        "site_displayed_update_before_GitHub_original_news_sha":True,
        "original_future_target_window_still_Nov1_not_today":True,
        "real_GitHub_SHA_time_does_NOT_attest_SportsNavi_source_clock":True,
        "this_quote_cannot_be_scored_as_prospective_PR41_target":True,
        "real_independently_authenticated_JRA_VAN_future_quote":False,
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-live-remote-clock",action="store_true")
    parser.add_argument("--output",type=Path,default=Path(
        "tmp/tenno-sportsnavi-2225-public-source-declared-descriptive.json"))
    args=parser.parse_args()
    result=audit()
    if args.verify_live_remote_clock:
        result["actual_PR41_GitHub_remote_time_relative_to_2225_quote"]=remote_GitHub_22h25_not_a_prospective_test()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,
                                       allow_nan=False)+"\n",encoding="utf-8")
    print("SPORTSNAVI_2225_SOURCE_DECLARED_SHA",
          result["latest_public_source_field_sha256_DECLARED_not_raw_original"])
    print("ALL_17_PUBLIC_QUOTES_CHANGED",
          result["earlier_all_17_news_horse_prices_changed"])
    print("PUBLIC_1742_VS_2225_TV_pp",
          result["cross_public_page_descriptive_price_change"][
              "normalized_inverse_quote_TV_percentage_points"])
    print("PUBLIC_1742_VS_2225_STRICT_PAIR_INVERSIONS",
          result["cross_public_page_descriptive_price_change"][
              "strictly_reversed_pair_count"])
    for name,score in result[
            "old_PR41_four_news_models_same_later_public_quoted_price_DIAGNOSTIC_ONLY"
            ].items():
        print("RETROSPECTIVE_PUBLIC_MODEL_DIAGNOSTIC_NOT_PRETARGET",
              name,score["TV_percentage_points"])
    print("ACTUAL_NOV1_VENDOR_Q2_OR_BETTING_RESULTS_NOT_OBSERVED",True)


if __name__=="__main__":
    main()
