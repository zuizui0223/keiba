#!/usr/bin/env python3
"""2026 Tenno Sho: explicitly PARTIAL, editorially timestamped WIN quote path.

Five within-article self-reported quote timestamps (06:08 through 15:08)
contain 4 or 5 cited horses, not all 17. The original linked PR33/35
tables at 17:00 and 17:42 contain all 17. Only the **intersection**
of actually quoted horse IDs can enter a pairwise comparison.
Never impute the missing 12-13 runners, never normalize four/five as if
they were a 17-runner market, and never treat editorial as-of claims as
independently authenticated provider-update and reception clocks.

Separate same-day SPREAD circa-noon article confirms #1=2.5/#7=2.9
but does not give an exactly shared market-update timestamp and is
NOT mixed into the model time series or treated as true bet stakes.

All intervals compare published DISPLAYED odds, not vote shares or true
win probabilities. Price-rank crossing is algebraic; there is NO proof
of herding, information arrival, self-reinforcement or critical odds.
Historical within-article data were read after updates; ZERO genuinely
remote-sealed pretarget next-quote trials are created here.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from itertools import combinations
import argparse
import json
import math
from pathlib import Path

from keiba_tenno_20261101_m0_rank_stability import (
    declared_field, RACE, MARKET_SOURCE_REPORTED_CLOCK,
)
from keiba_tenno_20261101_public_market_shadow import RACE_LOCAL_POST
from keiba_public_article_vs_real_archival_rank_geometry import (
    _declared_later, rank_contrast, CORROBORATING_NEWS_PUBLISHED,
)

STATUS="SEVEN_PARTIAL_OR_FULL_EDITORIAL_REPORTED_MARKET_POINTS_NOT_PRETARGET_ATTESTED"
BLOG_URL="https://race-postman.hateblo.jp/entry/2026/10/31/061338"
BLOG_SOURCE_TYPE="mutable_editorial_blog_self_reported_asof_not_original_vendor_receipt"
NOON_CONTEXT_URL="https://spread-sports.jp/archives/402071"
BLOG_PARTIAL=(
    ("06:08",((1,2.6),(3,9.0),(7,2.6),(11,9.0))),
    ("08:09",((1,2.6),(3,9.5),(7,2.4),(11,9.5),(17,11.9))),
    ("12:07",((1,2.5),(3,8.7),(7,2.9),(11,10.2),(17,10.3))),
    ("13:08",((1,2.7),(3,9.1),(7,2.8),(11,10.4),(17,9.7))),
    ("15:08",((1,2.6),(3,9.8),(7,2.5),(11,11.6),(17,10.4))),
)
PINNED_BLOG_DECLARED_PARTIAL_SHA256=(
    "6ac80f588f4ade9007a4db1150dc628b421195ff20db5854c2085fbbff2336f9"
)
QUOTE_HALF_DECIMAL=0.05
ROUNDING_SAFETY_TOL=1e-12


def _quoted_subset(value):
    """No partial vector is ever promoted to normalized market shares."""
    if (not isinstance(value,dict) or not 2<=len(value)<=17 or
            any(type(k) is not int or k<1 or k>17 or
                type(p) not in (float,int) or not math.isfinite(p) or p<=1
                for k,p in value.items())):
        raise ValueError("HOLD_PARTIAL_QUOTE_FIELD_NOT_REAL_POSITIVE_WIN_ODDS")
    return value


def _blog_reported_quotes():
    records=[]
    for label,raw in BLOG_PARTIAL:
        if (not isinstance(raw,tuple) or len(raw) not in (4,5) or
                len({i for i,_ in raw})!=len(raw)):
            raise ValueError("HOLD_BLOG_REPORTED_PARTIAL_COHORT_CHANGED")
        p=_quoted_subset(dict(raw))
        if (set(p)!={1,3,7,11} and set(p)!={1,3,7,11,17}
                or 1 not in p or 7 not in p or
                list(p)!=sorted(p)):
            raise ValueError("HOLD_BLOG_REPORTED_PARTIAL_RUNNERS_CHANGED")
        t=datetime.fromisoformat("2026-10-31T"+label+":00+09:00")
        if t.utcoffset() is None:
            raise ValueError("HOLD_BLOG_NAIVE_ARTICLE_TIME")
        records.append({"source_reported_jst":t.isoformat(),
                        "prices":p,
                        "source_url":BLOG_URL,
                        "source_kind":BLOG_SOURCE_TYPE,
                        "source_updated_at_independently_proven":False,
                        "original_receipt_independently_proven":False,
                        "all_17_prices_observed":False})
    manifest={
        "source_url":BLOG_URL,
        "source_type":BLOG_SOURCE_TYPE,
        "rows":[{
            "source_reported_jst":row["source_reported_jst"],
            "reported_partial_prices":[[i,repr(float(row["prices"][i]))]
                                       for i in sorted(row["prices"])]
        } for row in records],
    }
    digest=sha256(json.dumps(
        manifest,ensure_ascii=False,sort_keys=True,
        separators=(",",":")).encode("utf-8")).hexdigest()
    if digest!=PINNED_BLOG_DECLARED_PARTIAL_SHA256:
        raise ValueError("HOLD_BLOG_REPORTED_PARTIAL_OR_TIMESTAMP_TAMPERED")
    if [len(z["prices"]) for z in records]!=[4,5,5,5,5]:
        raise ValueError("HOLD_PARTIAL_HORSE_DENOMINATOR_CHANGED")
    return records,digest


def _relative_price_pair(a,b):
    """For pair i,j, lower odds = higher DISPLAYED public price rank.

    Rounded 0.1 payout quotes imply an interval ±0.05 per horse.
    A sign classified 'robust' must retain its strict sign throughout
    these quoted rounding intervals (conservative boundary handling).
    """
    if a<=QUOTE_HALF_DECIMAL or b<=QUOTE_HALF_DECIMAL:
        raise ValueError("HOLD_PRICE_ROUNDING_OUTSIDE_VALID_DOMAIN")
    logratio=math.log(a/b)
    low=math.log((a-QUOTE_HALF_DECIMAL)/(b+QUOTE_HALF_DECIMAL))
    high=math.log((a+QUOTE_HALF_DECIMAL)/(b-QUOTE_HALF_DECIMAL))
    robust=("positive" if low>ROUNDING_SAFETY_TOL else
            "negative" if high< -ROUNDING_SAFETY_TOL else
            "uncertain_or_rounded_tie")
    return {
        "displayed_log_odds_ratio":logratio,
        "displayed_symmetric_log_price_tie_margin":abs(logratio)/2,
        "nearest_tenth_rounding_log_ratio_lower":low,
        "nearest_tenth_rounding_log_ratio_upper":high,
        "robust_sign_under_decimal_rounding":robust,
    }


def _interval(first,second):
    a=_quoted_subset(first["prices"])
    b=_quoted_subset(second["prices"])
    common=sorted(set(a)&set(b))
    allpairs=list(combinations(common,2))
    reversed_pairs=[]
    tied_to_untied=[]
    untied_to_tied=[]
    for i,j in allpairs:
        old=math.copysign(1.,a[i]-a[j]) if a[i]!=a[j] else 0.
        new=math.copysign(1.,b[i]-b[j]) if b[i]!=b[j] else 0.
        if old*new<0:
            reversed_pairs.append([i,j])
        elif old==0 and new!=0:
            tied_to_untied.append([i,j])
        elif old!=0 and new==0:
            untied_to_tied.append([i,j])
    before=_relative_price_pair(a[1],a[7])
    after=_relative_price_pair(b[1],b[7])
    robust_crossing={
        before["robust_sign_under_decimal_rounding"],
        after["robust_sign_under_decimal_rounding"]
    }=={"positive","negative"}
    dt=(datetime.fromisoformat(second["source_reported_jst"])-
        datetime.fromisoformat(first["source_reported_jst"])).total_seconds()/60
    if dt<=0:
        raise ValueError("HOLD_NONPOSITIVE_ARTICLE_REPORTED_INTERVAL")
    return {
        "start_source_reported_jst":first["source_reported_jst"],
        "end_source_reported_jst":second["source_reported_jst"],
        "reported_elapsed_minutes_NOT_verified_market_elapsed":dt,
        "first_reported_horse_count":len(a),
        "later_reported_horse_count":len(b),
        "common_reported_horse_numbers":common,
        "compared_pair_count_ONLY_common_reported_horses":len(allpairs),
        "strictly_reversed_displayed_pairs":reversed_pairs,
        "strict_reversed_displayed_pair_count":len(reversed_pairs),
        "reported_tied_to_untied_pairs":tied_to_untied,
        "reported_untied_to_tied_pairs":untied_to_tied,
        "number_1_vs_7_strict_sign_reversal":
            [1,7] in reversed_pairs,
        "number_1_vs_7_opposite_sign_robust_under_nearest_tenth_rounding":
            robust_crossing,
        "not_an_independent_authenticated_market_transition":True,
        "full_17_runner_market_TV": "UNAVAILABLE_PARTIAL" if
            len(a)<17 or len(b)<17 else "AVAILABLE_ONLY_FULL_FIELD",
    }


def audit():
    partial,sha=_blog_reported_quotes()
    parent, parent_sha=declared_field()
    later,late_sha=_declared_later()
    post=datetime.fromisoformat(RACE_LOCAL_POST)
    full_times=(
        ("2026-10-31T17:00:00+09:00",parent,
         "https://keiba-times.com/tennosho-aki-2026-zenjitsu-odds/"),
        (CORROBORATING_NEWS_PUBLISHED,later,
         "https://news.netkeiba.com/?no=347359&pid=news_view"),
    )
    if MARKET_SOURCE_REPORTED_CLOCK!=full_times[0][0]:
        raise ValueError("HOLD_ORIGINAL_17H_PARENT_SOURCE_CHANGED")
    records=list(partial)
    for ts,prices,url in full_times:
        if len(prices)!=17 or set(prices)!=set(range(1,18)):
            raise ValueError("HOLD_ORIGINAL_LATER_PUBLIC_ALL_17_REQUIRED")
        records.append({
            "source_reported_jst":ts,
            "prices":_quoted_subset(prices),
            "source_url":url,
            "source_kind":"different_editorial_publisher_full_market_quote",
            "source_updated_at_independently_proven":False,
            "original_receipt_independently_proven":False,
            "all_17_prices_observed":True,
        })
    if (len(records)!=7 or not all(
            datetime.fromisoformat(records[i]["source_reported_jst"])<
            datetime.fromisoformat(records[i+1]["source_reported_jst"])
            for i in range(len(records)-1)) or
            any(datetime.fromisoformat(r["source_reported_jst"])>=post
                for r in records)):
        raise ValueError("HOLD_ARTICLE_PATH_TIME_MISORDERED_OR_POSTRACE")
    intervals=[_interval(x,y) for x,y in zip(records,records[1:])]
    trace=[]
    for r in records:
        h1,h7=r["prices"][1],r["prices"][7]
        margin=_relative_price_pair(h1,h7)
        displayed=("7" if h7<h1 else "1" if h1<h7 else "TIE")
        trace.append({
            "reported_jst":r["source_reported_jst"],
            "horse_1_WIN_displayed_odds":h1,
            "horse_7_WIN_displayed_odds":h7,
            "displayed_favorite_between_1_and_7":displayed,
            "reported_horses_at_this_time_NOT_imputed":
                len(r["prices"]),
            "full_17_runner_qM0_eligible":len(r["prices"])==17,
            "pair_log_ratio_and_rounding":margin,
        })
    if ([z["reported_horses_at_this_time_NOT_imputed"] for z in trace]
            !=[4,5,5,5,5,17,17]):
        raise ValueError("HOLD_PARTIAL_TO_FULL_EDITORIAL_TIMELINE_CHANGED")
    full=rank_contrast(parent,later)
    assert full["unique_unordered_horse_pairs"]==136
    return {
        "status":STATUS,
        "race":RACE,
        "publisher_self_reported_timepoints_not_provider_attested":7,
        "one_mutable_blog_partial_timepoints":5,
        "different_editorial_full_field_timepoints":2,
        "source_blog_URL":BLOG_URL,
        "independent_noon_context_URL":NOON_CONTEXT_URL,
        "independent_noon_context_reported_1_2p5_and_7_2p9":True,
        "blog_declared_prices_SHA256_not_original_vendor_or_capture":
            sha,
        "parent_declared_full_17h_SHA256_not_original_vendor":parent_sha,
        "later_declared_full_1742_SHA256_not_original_vendor":late_sha,
        "by_timepoint_1_vs_7":trace,
        "by_adjacent_publication_timepoint_interval":intervals,
        "strict_price_pair_reversals_over_reported_intervals":
            sum(z["strict_reversed_displayed_pair_count"] for z in intervals),
        "reported_1_vs_7_strict_reversal_interval_count":
            sum(z["number_1_vs_7_strict_sign_reversal"] for z in intervals),
        "robust_1_vs_7_reversal_under_conservative_one_decimal_rounding":
            sum(z["number_1_vs_7_opposite_sign_robust_under_nearest_tenth_rounding"]
                for z in intervals),
        "full_17runner_1700_to_1742_index_TV_pp_ONLY":{
            "source_times_not_a_certified_time_interval":True,
            "original_17_full_source_and_later_full_source_diff":
                full["normalized_inverse_quote_TV_percentage_points"],
            "full_17_pair_rank_reversals":
                full["strictly_reversed_pair_count"],
        },
        "missing_partial_runners_NOT_imputed_and_NOT_renormalized":True,
        "source_updates_publications_NOT_independently_time_attested":True,
        "reported_large_bet_events_NOT_assumed_observed_transactions":True,
        "no_real_bettor_votes_original_JRA_GPS_or_official_target_result_used":
            True,
        "criticality_self_reinforcement_or_betting_EV":"HOLD",
        "new_genuinely_pretarget_SHA_verified_price_score_count":0,
        "sealed_kikka_original_M0_to_M2_v31_main_unchanged":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=Path(
        "tmp/tenno-20261031-article-only-partial-odds-path.json"))
    a=ap.parse_args()
    r=audit()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2,
                                   allow_nan=False)+"\n",encoding="utf-8")
    print("DECLARED_PARTIAL_EDITORIAL_SOURCE_SHA",
          r["blog_declared_prices_SHA256_not_original_vendor_or_capture"])
    for z in r["by_adjacent_publication_timepoint_interval"]:
        print("REPORTED_PARTIAL_PAIR_TRANSITION",
              z["start_source_reported_jst"],z["end_source_reported_jst"],
              "common_N",len(z["common_reported_horse_numbers"]),
              "strict_flips",z["strictly_reversed_displayed_pairs"],
              "one_seven_robust",z[
                  "number_1_vs_7_opposite_sign_robust_under_nearest_tenth_rounding"])
    print("NEW_AUTHENTICATED_PROSPECTIVE_TRIALS",
          r["new_genuinely_pretarget_SHA_verified_price_score_count"])


if __name__=="__main__":
    main()
