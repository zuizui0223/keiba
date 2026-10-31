#!/usr/bin/env python3
"""BEFORE Nov1: fixed public NEWS full WIN forecast -> a FUTURE legal quote.

This is a deliberately SEPARATE public-media lane C, NOT PR30/37's
authorized two-WIN-snapshot 11-model physics/social prediction.
All frozen price indices are functions of a published, SOURCE-DECLARED
17-runner news table from Oct31 17:42. Article publication time does
NOT certify the original JRA tote update or reception timestamp.

Tomorrow's ONE target, predetermined now: the FIRST complete WIN
source-published update in 2026-11-01 14:45..15:05 JST (inclusive),
received by the authorized local operator no later than 15:15 JST;
same provider and official 17-runner source card. No substitutions if
there is no complete eligible quote: record HOLD only after race post.

Four no-training control vectors: persistence, fixed 10% uniform dilution,
and support exponent 0.9 / 1.1. The latter are hypothetical sensitivity
models, NOT discovered herding coefficients, independently measured horse
ability or betting/ROI forecasts. News-to-vendor source mismatch limits
the meaning of comparison even when a future target is captured.

Freeze is deterministic; SHA includes all 17 source-declared odds,
forecast vectors, source URL, fixed future window, model source-file
digests, and the old full-source SHA. A GitHub SHA-only comment on this
PR can certify *pretarget existence of the PUBLIC MEDIA forecast only*.
That comment alone never attests source truth, legal rights, or target
capture completeness. No automatic GitHub POST, proprietary scraping,
race outcomes, payout, bettor votes or GPS access.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
import json
import math

from keiba_public_article_vs_real_archival_rank_geometry import (
    _declared_later,NETKEIBA_1742_FULL_WIN,
    CORROBORATING_NEWS_PUBLISHED,CORROBORATING_NEWS_URL,
    PINNED_LATER_DECLARED_ARTICLE_FIELD_SHA256,
)
from keiba_tenno_20261101_public_market_shadow import RACE_LOCAL_POST
from keiba_operator_winwide_capture import (
    ROOT,JST,_aware,_check_card,_read_ledger,
)
from odds_shadow_freeze_score import _normalized_odds

SCHEMA="KEIBA_TENNO_PUBLIC_NEWS_NEXTWIN_FUTURE_FIXED_V1"
SCORE_SCHEMA="KEIBA_TENNO_PUBLIC_NEWS_NEXTWIN_LOCAL_SCORE_V1"
STATUS="PUBLIC_1742_ARTICLE_M0_FROZEN_FOR_FUTURE_FULL_WIN_SOURCE_ONLY"
SCORED_STATUS="PUBLIC_NEWS_NEXTWIN_LOCALLY_SCORED_NOT_AUTHENTICATED_SOURCE"
MISSING_STATUS="HOLD_PUBLIC_NEWS_TARGET_NO_COMPLETE_ELIGIBLE_WIN"
SLOT="2026-11-01|東京|天皇賞（秋）"
TARGET_PROVIDER="JRA-VAN Data Lab"
TARGET_START="2026-11-01T14:45:00+09:00"
TARGET_END="2026-11-01T15:05:00+09:00"
RECEIPT_CUTOFF="2026-11-01T15:15:00+09:00"
POST=RACE_LOCAL_POST
MODEL_NAMES=(
    "PUBLIC_news_M0_persistence",
    "PUBLIC_fixed_10pct_uniform_dilution",
    "PUBLIC_log_support_power_0p9",
    "PUBLIC_log_support_power_1p1",
)
CODE_FILES=(
    "scripts/keiba_tenno_public_pretarget_future_shadow.py",
    "scripts/keiba_public_article_vs_real_archival_rank_geometry.py",
    "scripts/keiba_tenno_20261101_public_market_shadow.py",
    "scripts/keiba_operator_winwide_capture.py",
    "scripts/odds_shadow_freeze_score.py",
)


def _canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False)


def _sha(payload):
    return sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _model_code_sha(root=ROOT):
    return {p:sha256((Path(root)/p).read_bytes()).hexdigest()
            for p in CODE_FILES}


def _prob(q):
    if (not isinstance(q,(tuple,list)) or len(q)!=17 or
            any(type(a) not in (float,int) or
                not math.isfinite(a) or a<=0 for a in q)):
        raise ValueError("HOLD_NEWS_FORECAST_NOT_17_POSITIVE_INDICES")
    s=sum(q)
    return [float(x/s) for x in q]


def _model_rows(vector):
    v=_prob(vector)
    return [{"n":i,"p":p} for i,p in enumerate(v,1)]


def _validate_rows(rows):
    if (not isinstance(rows,list) or len(rows)!=17 or
            any(not isinstance(r,dict) or
                    set(r)!={"n","p"} or
                    type(r["n"]) is not int or r["n"]!=i or
                    type(r["p"]) not in (int,float) or
                    not math.isfinite(r["p"]) or r["p"]<=0
                for i,r in enumerate(rows,1)) or
            not math.isclose(sum(r["p"] for r in rows),1,
                             abs_tol=1e-11)):
        raise ValueError("HOLD_PUBLIC_FROZEN_MODEL_ROSTER_OR_MASS")
    return rows


def freeze(root=ROOT):
    """No target file, no clock now(), no result and no target website read."""
    full,declared_sha=_declared_later()
    if (dict(NETKEIBA_1742_FULL_WIN)!=full or
            declared_sha!=PINNED_LATER_DECLARED_ARTICLE_FIELD_SHA256 or
            sorted(full)!=list(range(1,18))):
        raise ValueError("HOLD_ORIGINAL_1742_NEWS_FULL_FIELD_DRIFT")
    ids=sorted(full)
    if (not _aware(CORROBORATING_NEWS_PUBLISHED)<
            _aware(TARGET_START)<=_aware(TARGET_END)<
            _aware(RECEIPT_CUTOFF)<_aware(POST)-timedelta(minutes=10)):
        raise ValueError("HOLD_TARGET_NOT_FUTURE_OF_NEWS_OR_RACE")
    q=_prob([1/full[i] for i in ids])
    smooth=_prob([x**.9 for x in q])
    concentrate=_prob([x**1.1 for x in q])
    four={
        MODEL_NAMES[0]:_model_rows(q),
        MODEL_NAMES[1]:_model_rows([.9*x+.1/17 for x in q]),
        MODEL_NAMES[2]:_model_rows(smooth),
        MODEL_NAMES[3]:_model_rows(concentrate),
    }
    # Data needed by all four models is the ONE original 17:42 article
    # table; the reported 18:00 table was identical, not a next update.
    p={
        "schema":SCHEMA,"status":STATUS,
        "source_class":"public_news_article_only_NOT_JRA_OR_VENDOR_RAW_RECEIPT",
        "source_url":CORROBORATING_NEWS_URL,
        "source_article_published_at_jst_NOT_original_market_update":
            CORROBORATING_NEWS_PUBLISHED,
        "17_full_public_article_reported_odds":
            [{"n":i,"displayed_WIN_odds":float(full[i])} for i in ids],
        "source_identical_18h_editorial_manifest_sha256_not_vendor":
            declared_sha,
        "registered_fixed_2026_race_slot":SLOT,
        "scheduled_post_jst_source_context_not_local_official_receipt":POST,
        "target_source_provider_fixed_before_tomorrow":TARGET_PROVIDER,
        "target_source_update_window_start_jst":TARGET_START,
        "target_source_update_window_end_jst":TARGET_END,
        "target_local_receipt_cutoff_jst":RECEIPT_CUTOFF,
        "fixed_one_first_eligible_complete_WIN_quote_no_cherry_pick":True,
        "target_requires_exact_full_final_card_and_rights_review":True,
        "code_file_content_sha256":_model_code_sha(root),
        "model_universe_predeclared":list(MODEL_NAMES),
        "model_index_definition":"normalized_inverse_published_WIN_displayed_payout_odds",
        "frozen_price_index_forecasts":four,
        "baseline_two_favorites_ordered_at_article":[7,1],
        "baseline_top_two_horse_set":[1,7],
        "all_forecasts_are_price_indices_not_true_win_probabilities":True,
        "no_independent_horse_signal_or_social_parameter_fitted":True,
        "different_public_news_vs_later_licensed_provider":True,
        "PR30_PR37_11_physically_coupled_models_NOT_promoted_or_altered":True,
        "race_outcome_or_payout_consumed":False,
        "actual_future_JRA_quote_or_licence_acquired_by_script":False,
    }
    out={
        "schema":SCHEMA,
        "payload":p,
        "sha256_of_canonical_frozen_payload":_sha(p),
        "external_GitHub_public_SHA_comment_verified":False,
        "public_news_is_not_original_tote_source":True,
    }
    verify_freeze(out,root=root)
    return out


def verify_freeze(frozen,*,root=ROOT):
    if (not isinstance(frozen,dict) or set(frozen)!={
            "schema","payload","sha256_of_canonical_frozen_payload",
            "external_GitHub_public_SHA_comment_verified",
            "public_news_is_not_original_tote_source"} or
            frozen["schema"]!=SCHEMA or
            frozen["external_GitHub_public_SHA_comment_verified"] is not False or
            frozen["public_news_is_not_original_tote_source"] is not True):
        raise ValueError("HOLD_PUBLIC_FROZEN_SCHEME_OR_FALSE_REMOTE_CERTIFICATE")
    p=frozen["payload"]
    if (p.get("schema")!=SCHEMA or p.get("status")!=STATUS or
            frozen["sha256_of_canonical_frozen_payload"]!=_sha(p) or
            p.get("registered_fixed_2026_race_slot")!=SLOT or
            p.get("target_source_provider_fixed_before_tomorrow")!=
                TARGET_PROVIDER or
            p.get("target_source_update_window_start_jst")!=TARGET_START or
            p.get("target_source_update_window_end_jst")!=TARGET_END or
            p.get("target_local_receipt_cutoff_jst")!=RECEIPT_CUTOFF or
            p.get("code_file_content_sha256")!=_model_code_sha(root) or
            p.get("model_universe_predeclared")!=list(MODEL_NAMES) or
            p.get("baseline_two_favorites_ordered_at_article")!=[7,1] or
            p.get("source_identical_18h_editorial_manifest_sha256_not_vendor")
                !=PINNED_LATER_DECLARED_ARTICLE_FIELD_SHA256):
        raise ValueError("HOLD_PUBLIC_FORECAST_SOURCE_CODE_OR_CLOCK_CHANGED")
    prices=p.get("17_full_public_article_reported_odds")
    if (not isinstance(prices,list) or
            [x.get("n") for x in prices if isinstance(x,dict)]
                !=list(range(1,18)) or
            any(not isinstance(x,dict) or
                    set(x)!={"n","displayed_WIN_odds"}
                for x in prices)):
        raise ValueError("HOLD_PUBLIC_ORIGINAL_NEWS_FIELD_MUTATED")
    fresh,_=_declared_later()
    if any(float(fresh[x["n"]])!=x["displayed_WIN_odds"] for x in prices):
        raise ValueError("HOLD_PUBLIC_1742_ARTICLE_SOURCE_CHANGED")
    data=p.get("frozen_price_index_forecasts")
    if not isinstance(data,dict) or set(data)!=set(MODEL_NAMES):
        raise ValueError("HOLD_PUBLIC_NEWS_FIXED_FOUR_MODEL_UNIVERSE")
    for rows in data.values():
        _validate_rows(rows)
    # A malicious local operator could rehash altered forecast rows:
    # recompute ALL four models strictly from the source-declared odds.
    odds=[float(x["displayed_WIN_odds"]) for x in prices]
    q=_prob([1/x for x in odds])
    expected=(
        _model_rows(q),
        _model_rows([.9*x+.1/17 for x in q]),
        _model_rows([x**.9 for x in q]),
        _model_rows([x**1.1 for x in q]),
    )
    for name,reference in zip(MODEL_NAMES,expected):
        if any(abs(a["p"]-b["p"])>1e-13 for a,b in
               zip(data[name],reference)):
            raise ValueError("HOLD_NEWS_MODEL_VECTOR_NOT_FROM_PINNED_SOURCE")
    return p


def score_local(ledger,card,frozen,*,asof,
                operator_confirms_full_capture):
    """Report only local source-declared q2, NEVER certify a new JRA feed.

    Call after the target window closes. If no quote is captured, retain
    the original target as missing only after official scheduled post.
    """
    p=verify_freeze(frozen)
    if operator_confirms_full_capture is not True:
        raise ValueError("HOLD_PUBLIC_Q2_CAPTURE_COMPLETENESS_NOT_DECLARED")
    c=_check_card(card)
    if (c["slot_id"]!=SLOT or c["provider"]!=TARGET_PROVIDER or
            c["horse_numbers"]!=list(range(1,18)) or
            c["race_number"]!=11 or c["race_distance_m"]!=2000 or
            _aware(c["scheduled_post_jst"])!=_aware(POST)):
        raise ValueError("HOLD_NEWS_FUTURE_CARD_SLOT_FIELD_SOURCE_MISMATCH")
    now=_aware(asof)
    if now<=_aware(TARGET_END):
        raise ValueError("HOLD_PUBLIC_Q2_WINDOW_NOT_CLOSED")
    entries=_read_ledger(ledger)
    eligible=[]
    for event in entries:
        source=event["captured_source"]
        pub=_aware(source["source_updated_at_jst"])
        rx=_aware(event["captured_at_jst"])
        if (source["race_id"]!=c["race_id"] or
                source["provider"]!=TARGET_PROVIDER or
                source["provenance"]!=c["provenance"] or
                source["rights_reviewed_by_operator"]!=
                    c["rights_reviewed_by_operator"]):
            raise ValueError("HOLD_NEWS_Q2_WRONG_RACE_PROVIDER_OR_RIGHTS")
        if rx>now:
            raise ValueError("HOLD_NEWS_FUTURE_RECEIPT_AFTER_SCORING_CLOCK")
        if source["market"]!="win":
            continue
        if _aware(TARGET_START)<=pub<=_aware(TARGET_END):
            prices=_normalized_odds(source["odds_by_horse_number"])
            if set(prices)!=set(range(1,18)):
                raise ValueError("HOLD_NEWS_TARGET_INCOMPLETE_WIN_FIELD")
            if rx>_aware(RECEIPT_CUTOFF):
                raise ValueError("HOLD_NEWS_TARGET_LOCAL_RECEIPT_AFTER_LOCKED_CUTOFF")
            eligible.append((pub,rx,prices))
    if not eligible:
        if now<_aware(POST):
            raise ValueError("HOLD_PUBLIC_MISSING_TARGET_FINAL_STATUS_BEFORE_POST")
        return {
            "schema":SCORE_SCHEMA,
            "status":MISSING_STATUS,
            "registered_slot_id":SLOT,
            "source_article_sha256":
                p["source_identical_18h_editorial_manifest_sha256_not_vendor"],
            "original_pretarget_public_forecast_sha256":
                frozen["sha256_of_canonical_frozen_payload"],
            "observed_eligible_next_win_targets":0,
            "target_missing_not_zero_price_error":True,
            "new_independently_verified_JRA_market_trial":False,
        }
    pub,rx,quotes=min(eligible,key=lambda x:(x[0],x[1]))
    q=_prob([1/quotes[i] for i in range(1,18)])
    scores={}
    for name,rows in p["frozen_price_index_forecasts"].items():
        model=[x["p"] for x in rows]
        scores[name]={
            "full_17_relative_display_WIN_TV_pp":
                50*sum(abs(a-b) for a,b in zip(model,q)),
            "next_display_quote_index_KL_nats":
                sum(a*math.log(a/b) for a,b in zip(q,model)),
        }
    before={r["n"]:r["displayed_WIN_odds"]
            for r in p["17_full_public_article_reported_odds"]}
    first_pre_race=sorted(before,key=lambda i:(before[i],i))
    first_target=sorted(quotes,key=lambda i:(quotes[i],i))
    return {
        "schema":SCORE_SCHEMA,
        "status":SCORED_STATUS,
        "registered_slot_id":SLOT,
        "source_article_sha256_not_vendor_original":
            p["source_identical_18h_editorial_manifest_sha256_not_vendor"],
        "original_pretarget_public_forecast_sha256":
            frozen["sha256_of_canonical_frozen_payload"],
        "selected_first_eligible_full_WIN_published":pub.isoformat(),
        "selected_full_WIN_locally_received":rx.isoformat(),
        "selected_provider":TARGET_PROVIDER,
        "one_market_target_for_all_four_models":True,
        "observed_eligible_next_win_targets":1,
        "target_price_index_TV_KL_by_all_four_fixed_models":scores,
        "news_top_two_set_preserved":
            set(first_pre_race[:2])==set(first_target[:2]),
        "news_favorite_7_still_first":first_target[0]==7,
        "retrospective_actual_winner_or_JRA_stakes_read":False,
        "market_source_public_news_and_private_vendor_are_different":True,
        "full_target_stream_completeness_claim_not_independently_verified":
            True,
        "new_independently_verified_JRA_market_trial":False,
        "PR30_PR37_future_11_model_prospective_evidence_unchanged":True,
        "no_horse_win_probabilities_or_bet_expected_value_inferred":True,
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="action",required=True)
    a=sub.add_parser("freeze")
    a.add_argument("--output",type=Path,required=True)
    b=sub.add_parser("score-local")
    b.add_argument("--frozen",type=Path,required=True)
    b.add_argument("--ledger",type=Path,required=True)
    b.add_argument("--final-card",type=Path,required=True)
    b.add_argument("--operator-confirms-full-capture",action="store_true")
    b.add_argument("--output",type=Path,required=True)
    z=parser.parse_args()
    if z.action=="freeze":
        result=freeze()
        summary={"status":STATUS,
                 "frozen_sha256":
                     result["sha256_of_canonical_frozen_payload"],
                 "source_genuine_vendor_receipt":False,
                 "target_opened":False}
    else:
        result=score_local(
            z.ledger,_read(z.final_card),_read(z.frozen),
            asof=datetime.now(JST).isoformat(),
            operator_confirms_full_capture=z.operator_confirms_full_capture)
        summary={"status":result["status"],
                 "new_real_source_attestation":False}
    z.output.parent.mkdir(parents=True,exist_ok=True)
    with z.output.open("x",encoding="utf-8") as handle:
        handle.write(json.dumps(result,ensure_ascii=False,indent=2,
                                allow_nan=False)+"\n")
    print(json.dumps(summary,ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
