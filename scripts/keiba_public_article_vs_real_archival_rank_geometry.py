#!/usr/bin/env python3
"""Observed public-article price contrast versus source-locked archival ranks.

TENNO 2026-10-31: 17:00 listed by one publisher, nominal 18:00 by
another. The nominal 18:00 full vector *also appears* in a news article
published at 17:42. Thus a numerical cross-article contrast IS possible,
but two independently authenticated real JRA market-update times are NOT
established. In particular: DO NOT treat a publisher's article timestamp
as a tote update, this difference as a 60-minute genuine q0->q1 path,
or a same-provider prospective score.

Archived Kyoto 2026-10-12 races R8-R12: verify existing source-locked
same-provider prestart full fields (5 distinct races, 2 timepoints each)
and a third R8 source-locked timepoint; outcome, wager and postrace label
files never opened. All are retrospective descriptive evidence, NOT a
prospective market experiment.

Shared diagnostic: geometry of price rank intersections, observed changes
in normalized inverse displayed WIN prices, and exact necessary
counterfactual rank reversal envelopes. No inference of true stakes,
horse behavior, bettors' herding, information arrivals, market phase
transitions, actual win probabilities or expected wager returns.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path

from keiba_tenno_20261101_m0_rank_stability import (
    declared_field, RACE, MARKET_SOURCE_REPORTED_CLOCK
)

STATUS="SOURCE_QUOTE_RANK_GEOMETRY_DESCRIPTIVE_NO_TIPPING_INFERENCE"
LATER_URL="https://umanity.jp/racedata/race_newsdet.php?nid=11881172"
LATER_REPORTED_ASOF="2026-10-31T18:00:00+09:00"
CORROBORATING_NEWS_URL="https://news.netkeiba.com/?no=347359&pid=news_view"
CORROBORATING_NEWS_PUBLISHED="2026-10-31T17:42:00+09:00"
LATER_FULL_WIN=(
    (1,2.5),(2,226.6),(3,9.8),(4,49.5),(5,171.9),
    (6,27.2),(7,2.4),(8,234.7),(9,66.0),(10,46.5),
    (11,11.5),(12,109.2),(13,36.2),(14,120.3),
    (15,102.7),(16,58.1),(17,11.2),
)
# Independently transcribed full 17-runner article published 17:42;
# exact same prices as the 18:00 described list. A publication time
# is NOT verified data receipt or a new JRA quote update time.
NETKEIBA_1742_FULL_WIN=(
    (7,2.4),(1,2.5),(3,9.8),(17,11.2),(11,11.5),
    (6,27.2),(13,36.2),(10,46.5),(4,49.5),(16,58.1),
    (9,66.0),(15,102.7),(12,109.2),(14,120.3),
    (5,171.9),(2,226.6),(8,234.7),
)
PINNED_LATER_DECLARED_ARTICLE_FIELD_SHA256=(
    "3b8fc4798664a090963d5e8221029643cf9205934ba7fe7db0cc37a8d1f6e37b"
)


def _declared_later():
    field=dict(LATER_FULL_WIN)
    if (len(field)!=17 or sorted(field)!=list(range(1,18))
            or len(LATER_FULL_WIN)!=17 or
            any(type(v) not in (float,int) or not math.isfinite(v) or v<=1
                for v in field.values())):
        raise ValueError("HOLD_TENNO_SECOND_ARTICLE_INCOMPLETE_OR_INVALID")
    if field!=dict(NETKEIBA_1742_FULL_WIN) or len(
            NETKEIBA_1742_FULL_WIN)!=17:
        raise ValueError("HOLD_PUBLIC_ARTICLES_DO_NOT_MATCH_EXACT_FULL_FIELD")
    manifest={
        "race":RACE,
        "article_reported_asof":LATER_REPORTED_ASOF,
        "article_url":LATER_URL,
        "full_field":[[i,repr(float(field[i]))] for i in sorted(field)],
    }
    raw=json.dumps(manifest,ensure_ascii=False,sort_keys=True,
                   separators=(",",":")).encode("utf-8")
    digest=sha256(raw).hexdigest()
    if digest!=PINNED_LATER_DECLARED_ARTICLE_FIELD_SHA256:
        raise ValueError("HOLD_PUBLIC_LATER_ARTICLE_PRICE_FIELD_MUTATED")
    t0=datetime.fromisoformat(MARKET_SOURCE_REPORTED_CLOCK)
    late=datetime.fromisoformat(LATER_REPORTED_ASOF)
    corroborating=datetime.fromisoformat(CORROBORATING_NEWS_PUBLISHED)
    if (t0.utcoffset() is None or late.utcoffset() is None or
            corroborating.utcoffset() is None or
            not t0<corroborating<late):
        raise ValueError("HOLD_ARTICLE_TIME_SEMANTICS_CHANGED")
    return field,digest


def _valid_pair(before,after):
    if (not isinstance(before,dict) or not isinstance(after,dict) or
            before.keys()!=after.keys() or not 5<=len(before)<=30 or
            any(type(k) is not int or k<=0 for k in before) or
            any(type(x) not in (float,int) or not math.isfinite(x) or x<=1
                for d in (before,after) for x in d.values())):
        raise ValueError("HOLD_INCOMPLETE_OR_INVALID_MATCHED_FULL_WIN")
    return sorted(before)


def rank_contrast(before,after):
    """Pure before/after price-rank geometry. No article/market time assumption.

    Worst-case symmetric log-price shock determined *post hoc* from the
    largest absolute observed one-horse change. It is a descriptive
    envelope, not a forecast confidence band or calibrated uncertainty.
    """
    ids=_valid_pair(before,after)
    w0={i:1/before[i] for i in ids}
    w1={i:1/after[i] for i in ids}
    s0=sum(w0.values());s1=sum(w1.values())
    q0={i:w0[i]/s0 for i in ids}
    q1={i:w1[i]/s1 for i in ids}
    if not (math.isclose(sum(q0.values()),1,abs_tol=1e-12)
            and math.isclose(sum(q1.values()),1,abs_tol=1e-12)):
        raise ValueError("HOLD_SOURCE_INDEX_PROBABILITY_MASS")
    ranked0=sorted(ids,key=lambda i:(before[i],i))
    ranked1=sorted(ids,key=lambda i:(after[i],i))
    deltas={i:math.log(after[i]/before[i]) for i in ids}
    max_abs_delta=max(abs(v) for v in deltas.values())
    flips=[]
    newly_tied=[]
    possible_by_posthoc_bound=[]
    for i,j in combinations(ids,2):
        x0=math.log(before[i]/before[j])
        x1=math.log(after[i]/after[j])
        if x0*x1<0:
            flips.append([i,j])
        if x0!=0 and x1==0:
            newly_tied.append([i,j])
        if .5*abs(x0)<=max_abs_delta:
            possible_by_posthoc_bound.append([i,j])
    # Exact pairwise identity x1=x0+(u_i-u_j): a ranking reversal
    # can be due solely to smoothly changing real-valued price quotes.
    changed=len([i for i in ids if before[i]!=after[i]])
    ordered_pairs=len(ids)*(len(ids)-1)//2
    return {
        "horse_count":len(ids),
        "unique_unordered_horse_pairs":ordered_pairs,
        "initial_sum_inverse_payout_odds_not_stakes":s0,
        "later_sum_inverse_payout_odds_not_stakes":s1,
        "normalized_inverse_quote_TV_percentage_points":
            50*sum(abs(q1[i]-q0[i]) for i in ids),
        "normalized_inverse_quote_KL_later_vs_earlier_nats":
            sum(q1[i]*math.log(q1[i]/q0[i]) for i in ids),
        "individual_display_prices_changed":changed,
        "horse_ids_whose_ordinal_rank_changed":
            sum(ranked0.index(i)!=ranked1.index(i) for i in ids),
        "strictly_reversed_pair_count":len(flips),
        "strictly_reversed_horse_pairs":flips,
        "newly_equal_pair_count":len(newly_tied),
        "later_horse_price_log_shock_max_abs_posthoc":max_abs_delta,
        "pair_earlier_tie_boundary_within_posthoc_worst_case_shock_count":
            len(possible_by_posthoc_bound),
        "geometrically_possible_under_uniform_posthoc_bound_but_not_observed":
            len(possible_by_posthoc_bound)-
            sum(pair in possible_by_posthoc_bound for pair in flips+newly_tied),
        "top_two_horse_set_preserved":
            set(ranked0[:2])==set(ranked1[:2]),
        "top_three_horse_set_preserved":
            set(ranked0[:3])==set(ranked1[:3]),
        "initial_top_two_normalized_quote_index_share":
            sum(q0[i] for i in ranked0[:2]),
        "later_initial_top_two_normalized_quote_index_share":
            sum(q1[i] for i in ranked0[:2]),
        "full_order_preserved":ranked0==ranked1,
        "relative_payout_price_indices_NOT_observed_vote_or_true_win_prob":True,
        "geometric_rank_crossing_NOT_evidence_of_dynamic_market_criticality":True,
    }


def tenno_public_articles():
    initial,first_digest=declared_field()
    later,later_digest=_declared_later()
    a=rank_contrast(initial,later)
    a.update({
        "status":"CROSS_PUBLISHER_PUBLIC_REPORT_DIFFERENCE_ONLY",
        "race":RACE,
        "source_reported_early_asof":MARKET_SOURCE_REPORTED_CLOCK,
        "source_reported_later_asof":LATER_REPORTED_ASOF,
        "early_publisher_url":
            "https://keiba-times.com/tennosho-aki-2026-zenjitsu-odds/",
        "nominal_later_publisher_url":LATER_URL,
        "earlier_publication_of_exact_same_nominal_18h_vector_url":
            CORROBORATING_NEWS_URL,
        "earlier_identical_17runner_publication_at":
            CORROBORATING_NEWS_PUBLISHED,
        "nominal_18h_quote_already_published_in_1742_article":True,
        "initial_declared_source_field_sha256_not_vendor_bytes":
            first_digest,
        "later_declared_article_field_sha256_not_vendor_bytes":
            later_digest,
        "independently_attested_genuine_two_time_JRA_feed":False,
        "measured_60min_market_path_identified":False,
        "authenticated_original_receipt_count":0,
        "not_eligible_for_original_PR22_PR30_prospective_score":True,
    })
    # An article available by 17:42 cannot by itself certify a NEW
    # underlying tote update at nominal 18:00. Fail if future developers
    # accidentally promote this to a verified dynamic market feed.
    if not a["nominal_18h_quote_already_published_in_1742_article"]:
        raise ValueError("HOLD_TIME_CROSS_PUBLISHER_NEGATIVE_CONTROL_MISSING")
    return a


def archived_kyoto_prices(root):
    """Exactly the five already source-locked real races, without results."""
    from odds_real_multirace_archive_audit import SOURCE_SHA,read_file,_one_race
    from odds_r8_real_three_time_market import collect_pre_race_price_panels
    data=[]
    for r in (8,9,10,11,12):
        first=read_file(root,SOURCE_SHA[r][0])
        mid=read_file(root,SOURCE_SHA[r][1])
        _one_race(first,mid,r)  # existing raw clock/roster/source gates
        a={int(row["number"]):float(row["win_odds"])
           for row in first["horses"]}
        b={int(row["selection"][0]):float(row["odds_low"])
           for row in mid["quotes"]["win"]}
        if set(a)!=set(b) or len(a)!=len(first["horses"]):
            raise ValueError("HOLD_ARCHIVED_PRICE_ROSTER_CHANGED")
        contrast=rank_contrast(a,b)
        data.append({
            "race_number":r,
            "early_source_published":first["odds_updated_at_jst"],
            "late_source_published":mid["updated_at_jst"],
            "interval":"first_to_second",
            "diagnostic":contrast,
        })
    triplet,_,_,_,_=collect_pre_race_price_panels(root)
    if len(triplet)!=3 or [x["label"] for x in triplet]!=[
            "12:21","13:26","13:44"]:
        raise ValueError("HOLD_ARCHIVED_R8_THREE_PRICE_POINTS_CHANGED")
    if (triplet[1]["win_prices"]!=
            {int(k):float(v) for k,v in
             ((row["selection"][0],row["odds_low"]) for row in
              read_file(root,SOURCE_SHA[8][1])["quotes"]["win"])}):
        raise ValueError("HOLD_ARCHIVED_R8_MIDDLE_SOURCE_MISMATCH")
    data.append({
        "race_number":8,
        "early_source_published":triplet[1]["provider_published_quote_minute"],
        "late_source_published":triplet[2]["provider_published_quote_minute"],
        "interval":"second_to_third",
        "diagnostic":rank_contrast(triplet[1]["win_prices"],
                                   triplet[2]["win_prices"]),
    })
    return {
        "status":"EXISTING_OCT12_ARCHIVED_SOURCE_SHA_RECHECKED_RETROSPECTIVE",
        "original_distinct_races":5,
        "original_distinct_meeting_dates":1,
        "original_source_price_intervals":6,
        "third_point_is_R8_NOT_A_SIXTH_NEW_RACE":True,
        "single_source_provider_family":
            "Yahoo/SportsNavi archived prestart quote reports",
        "no_official_outcome_or_result_or_bettor_records_read":True,
        "not_a_prospective_SHA_posted_trial":True,
        "by_interval":data,
        "total_rank_reversed_pairs_descriptive_not_independent_samples":
            sum(x["diagnostic"]["strictly_reversed_pair_count"] for x in data),
        "intervals_with_one_or_more_reversed_pairs":
            sum(x["diagnostic"]["strictly_reversed_pair_count"]>0 for x in data),
        "max_single_interval_quoted_win_TV_pp":
            max(x["diagnostic"][
                "normalized_inverse_quote_TV_percentage_points"] for x in data),
    }


def audit(*,include_archives=True,root=None):
    report={
        "status":STATUS,
        "tenno_cross_publisher":tenno_public_articles(),
        "retrospective_kyoto_archived":(
            archived_kyoto_prices(root or Path(__file__).resolve().parents[1])
            if include_archives else "NOT_RUN"),
        "source_quote_vs_tote_update_clocks_not_conflated":True,
        "public_tenno_report_not_a_true_independent_next_price_score":True,
        "r8_archived_3points_repeated_same_race_not_3_independent_races":True,
        "no_target_JRA_winner_or_finishing_order_used":True,
        "no_market_criticality_or_herding_mechanism_identified":True,
        "full_original_licensed_WIDE_or_ballot_stream_still_missing":True,
        "sealed_kikka_and_v31_ledgers_unchanged":True,
    }
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tenno-only",action="store_true")
    ap.add_argument("--output",type=Path,
                    default=Path("tmp/tenno-public-vs-kyoto-real-rank-geometry.json"))
    args=ap.parse_args()
    report=audit(include_archives=not args.tenno_only)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,
                                      allow_nan=False)+"\n",encoding="utf-8")
    t=report["tenno_cross_publisher"]
    print("PUBLIC_ARTICLE_QUOTES_NOT_VERIFIED_TOTE_TIMES",True)
    print("TENNO_ARTICLE_CONTRAST",json.dumps({
        "changed_horse_prices":t["individual_display_prices_changed"],
        "actual_pair_reversals":t["strictly_reversed_pair_count"],
        "posthoc_worst_case_possible_pairs":
            t["pair_earlier_tie_boundary_within_posthoc_worst_case_shock_count"],
        "index_TV_pp":t["normalized_inverse_quote_TV_percentage_points"],
        "nominal_1800_already_in_1742_news":
            t["nominal_18h_quote_already_published_in_1742_article"],
    },ensure_ascii=False,sort_keys=True))
    if not args.tenno_only:
        k=report["retrospective_kyoto_archived"]
        for r in k["by_interval"]:
            print("ARCHIVED_REAL_INTERVAL_NO_RESULTS",json.dumps({
                "race":r["race_number"],"window":r["interval"],
                "n_horses":r["diagnostic"]["horse_count"],
                "reversed_pairs":r["diagnostic"]["strictly_reversed_pair_count"],
                "observed_TV_pp":r["diagnostic"][
                    "normalized_inverse_quote_TV_percentage_points"],
            },sort_keys=True))
    print("NO_TRUE_BETTOR_THRESHOLD_OR_FUTURE_WINNER_INFERENCE",True)


if __name__=="__main__":
    main()
