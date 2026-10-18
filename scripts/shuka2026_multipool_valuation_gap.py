#!/usr/bin/env python3
"""Compare betting pools against *earlier* pre-market qualitative horse ordering.

CROSS-MARKET DIAGNOSTIC, NOT WIN/PLACE PROBABILITY FIT:
- JRA official runner-name/number concordance is fixed in the PR.
- Third party SportsNavi *intermediate* 17-runner single-win odds and
  all 136 wide and all 136 quinella prices are recorded at approx. 15:37 JST.
- First win snapshot is archived at approx. 14:37 JST.
- These are separately refreshed pari-mutuel pools, with UNKNOWN official
  source publication timestamps. A screenshot price is NOT a calibrated
  future win probability, fair price, or independent model estimate.
- v3.1 classifier thresholds and 20-race prospective holdout are untouched.

This source does not authenticate JRA original HTML bytes or wager purchases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
from statistics import mean

from shuka2026_market_overlay import HERE, source_base
from v31_candidate_channels import market_channel
from shuka2026_compare_own_vs_crowd import (
    SOURCE as EARLIER_SINGLE_SNAPSHOT,
    MARKET_URL, OUR_HISTORICAL_QUALITATIVE_RANKS,
)

NEW_SNAPSHOT=HERE/"data/2026-10-17/shuka2026-sportsnavi-multipool-intermediate-1537.json"
EARLIER_MARKET_RETRIEVAL="2026-10-17T14:37:44+09:00"
COMPARISON_SOURCE="2026-10-17T15:37:39+09:00"
ALL_17=set(range(1,18))
BASE_NON_M={1,3,6,8,9,12}


def _pair_key(nums:list[int])->tuple[int,int]:
    if (not isinstance(nums,list) or len(nums)!=2
        or any(type(x) is not int or x not in ALL_17 for x in nums)
        or nums[0]>=nums[1]):
        raise ValueError("HOLD_INVALID_PUBLIC_PAIR_HORSE_NUMBERS")
    return tuple(nums)


def _validate_pair_rows(rows:list[dict],*,wide:bool)->dict:
    if len(rows)!=136 or sorted(q.get("rank") for q in rows)!=list(range(1,137)):
        raise ValueError("HOLD_NOT_COMPLETE_17_CHOOSE_2_PUBLIC_PAIR_POOL")
    pairs={}
    for item in rows:
        key=_pair_key(item["horse_numbers"])
        if key in pairs:
            raise ValueError("HOLD_DUPLICATE_PUBLIC_MARKET_PAIR")
        if wide:
            lo=item.get("quoted_odds_min")
            hi=item.get("quoted_odds_max")
            if (type(lo) not in (int,float) or type(hi) not in (int,float)
                or not math.isfinite(lo) or not math.isfinite(hi)
                or lo<1 or hi<lo):
                raise ValueError("HOLD_INVALID_PUBLIC_WIDE_ODDS_RANGE")
            pairs[key]={"rank":item["rank"],"low":lo,"high":hi}
        else:
            odd=item.get("quoted_odds")
            if type(odd) not in (int,float) or not math.isfinite(odd) or odd<1:
                raise ValueError("HOLD_INVALID_PUBLIC_QUINELLA_ODDS")
            pairs[key]={"rank":item["rank"],"odds":odd}
    if len(pairs)!=136:
        raise ValueError("HOLD_INCOMPLETE_PAIR_SET")
    return pairs


def audited(snapshot:dict,earlier:dict,base:dict)->dict:
    if (snapshot.get("schema")!="SHUKA2026_PUBLIC_MULTIPOOL_SPORTSNAVI_INTERMEDIATE_20261017_V1"
        or snapshot.get("observation_started_jst")!=COMPARISON_SOURCE
        or not snapshot.get("source_provider_reported_last_update_not_available")
        or not snapshot.get("separate_pool_pages_not_transactionally_synchronized")
        or snapshot.get("source_urls",{}).get("win")!=MARKET_URL):
        raise ValueError("HOLD_INTERMEDIATE_SOURCE_PROVENANCE_OR_COHORT_CHANGED")
    if (earlier.get("schema")!="SHUKA2026_SPORTSNAVI_ACTUAL_INTERMEDIATE_SINGLE_WIN_ODDS_17_V1"
        or earlier.get("observation_started_at_jst")!=EARLIER_MARKET_RETRIEVAL):
        raise ValueError("HOLD_DIFFERENT_OR_EARLIER_SINGLE_SOURCE_NOT_VERIFIED")
    old_rows=earlier["horses"]
    new_rows=snapshot["win_prices_all_17"]
    if len(old_rows)!=17 or len(new_rows)!=17:
        raise ValueError("HOLD_INCOMPLETE_SINGLE_WIN_ODDS_SOURCE")
    old={r["number"]:r for r in old_rows}
    newer={r["horse_number"]:r for r in new_rows}
    expected={r["official_horse_number"]:r["horse_name"] for r in base["horse_records"]}
    if (set(newer)!=ALL_17 or set(old)!=ALL_17
        or len(expected)!=17 or set(expected)!=ALL_17
        or any(old[n]["name"]!=expected[n] or
               newer[n]["name"]!=expected[n] for n in ALL_17)
        or sorted(r["rank"] for r in new_rows)!=list(range(1,18))):
        raise ValueError("HOLD_MISSING_OR_WRONG_JRA_RACE_HORSE_NAMES")
    sorted_by_price=sorted(new_rows,key=lambda r:
                           (r["win_odds"],r["horse_number"]))
    if [r["rank"] for r in sorted_by_price]!=list(range(1,18)):
        raise ValueError("HOLD_PUBLIC_WIN_RANK_INCONSISTENT_WITH_QUOTED_ODDS")
    for r in new_rows:
        odd=r.get("win_odds")
        if type(odd) not in (int,float) or not math.isfinite(odd) or odd<1:
            raise ValueError("HOLD_INVALID_LATEST_DISPLAYED_WIN_PRICE")
    wide=_validate_pair_rows(snapshot["wide_pair_all_136"],wide=True)
    quin=_validate_pair_rows(snapshot["quinella_pair_all_136"],wide=False)
    trio=snapshot["selected_trio_three_horse_quotes_only"]
    if (len(trio)!=5 or snapshot["data_quality"]["selected_three_horse_count"]!=5
        or not snapshot["data_quality"]["selected_three_horse_ranks_only_no_full_680_claim"]):
        raise ValueError("HOLD_DONT_MISREPRESENT_PARTIAL_TRIO_SOURCE_AS_FULL")
    m=market_channel([{"number":n,"win_odds":newer[n]["win_odds"]}
                      for n in ALL_17])
    if set(base["official_nonmarket_v31_candidate_numbers_NOT_RANKING"])!=BASE_NON_M:
        raise ValueError("HOLD_UNEXPECTED_PRE_MARKET_V31_HISTORICAL_CANDIDATES")
    total=sorted(m|BASE_NON_M)
    moves=[{
        "horse_number":n,"horse_name":newer[n]["name"],
        "earlier_win":float(old[n]["win_odds"]),
        "later_win":float(newer[n]["win_odds"]),
        "odds_percent_change_not_bet_share_change":
            100*(newer[n]["win_odds"]/old[n]["win_odds"]-1),
        "earlier_win_rank":old[n]["market_rank"],
        "later_win_rank":newer[n]["rank"],
        "market_rank_change_later_minus_earlier":
            newer[n]["rank"]-old[n]["market_rank"],
    } for n in sorted(ALL_17)]
    def pair(a:int,b:int,*,source:dict)->dict:
        return dict(source[tuple(sorted((a,b)))])
    pairs=[]
    for a,b in ((8,6),(8,13),(8,3),(8,14),(8,9),(8,4),
                (13,14),(3,14),(9,14)):
        pairs.append({
            "pair":[a,b],
            "wide_two_horses_top_three":pair(a,b,source=wide),
            "quinella_two_horses_top_two_unordered":pair(a,b,source=quin),
        })
    def get(a,b):
        return next(r for r in pairs if r["pair"]==[a,b])
    race={
        "14_more_favored_than_3_in_WIN_market":newer[14]["rank"]<newer[3]["rank"],
        "14_more_favored_than_3_in_WIDE_given_pairing_8":
            get(8,14)["wide_two_horses_top_three"]["rank"]<
            get(8,3)["wide_two_horses_top_three"]["rank"],
        "14_more_favored_than_3_in_QUINELLA_given_pairing_8":
            get(8,14)["quinella_two_horses_top_two_unordered"]["rank"]<
            get(8,3)["quinella_two_horses_top_two_unordered"]["rank"],
        "14_wide_pair8_global_rank":get(8,14)["wide_two_horses_top_three"]["rank"],
        "3_wide_pair8_global_rank":get(8,3)["wide_two_horses_top_three"]["rank"],
        "9_wide_pair8_global_rank":get(8,9)["wide_two_horses_top_three"]["rank"],
        "14_quinella_pair8_global_rank":get(8,14)["quinella_two_horses_top_two_unordered"]["rank"],
        "3_quinella_pair8_global_rank":get(8,3)["quinella_two_horses_top_two_unordered"]["rank"],
    }
    # Compare ranks among the exact SAME 16 possible partners of
    # horse 8.  Unlike raw global 136-pair ranks, these are comparable
    # 1..16 order statistics within a defined fixed-anchor population.
    # The win rankings exclude horse 8 to use the same 16 animals.
    other_horses=sorted(ALL_17-{8})
    win_rank={n:i+1 for i,n in enumerate(
        sorted(other_horses,key=lambda n:(newer[n]["win_odds"],n))
    )}
    wide_rank={n:i+1 for i,n in enumerate(
        sorted(other_horses,key=lambda n:(wide[tuple(sorted((8,n)))]["rank"],n))
    )}
    quin_rank={n:i+1 for i,n in enumerate(
        sorted(other_horses,key=lambda n:(quin[tuple(sorted((8,n)))]["rank"],n))
    )}
    anchor_partner_rankings=[{
        "partner_horse_number":n,
        "partner_name":newer[n]["name"],
        "win_order_AMONG_16_NON_8_horses":win_rank[n],
        "wide_pair_with8_order_AMONG_16_pair_choices":wide_rank[n],
        "quinella_pair_with8_order_AMONG_16_pair_choices":quin_rank[n],
        "wide_partner_preference_rank_gain_over_win_order":
            win_rank[n]-wide_rank[n],
        "quinella_partner_preference_rank_gain_over_win_order":
            win_rank[n]-quin_rank[n],
        "event_rank_differences_not_place_win_probabilities":True,
    } for n in other_horses]
    author=[
        {"number":n,"name":newer[n]["name"],
         "our_prior_qualitative_order_NOT_personal_win_probability":i,
         "market_win_rank":newer[n]["rank"],
         "market_minus_our_rank":newer[n]["rank"]-i,
         "win_odds":newer[n]["win_odds"]}
        for i,n in enumerate(OUR_HISTORICAL_QUALITATIVE_RANKS,start=1)
    ]
    selected_trios=[]
    for r in trio:
        vals=r.get("horse_numbers")
        if (not isinstance(vals,list) or len(vals)!=3 or
            any(type(n) is not int or n not in ALL_17 for n in vals) or
            len(set(vals))!=3 or type(r.get("rank")) is not int or
            type(r.get("quoted_odds")) not in (int,float) or
            not math.isfinite(r["quoted_odds"]) or r["quoted_odds"]<1):
            raise ValueError("HOLD_PARTIAL_TRIO_ORIGIN_INVALID")
        selected_trios.append({
          "triple_unordered_horse_numbers":vals,"rank_among_trifectas":r["rank"],
          "quoted_trio_odds":r["quoted_odds"],
        })
    max_change=max(abs(r["odds_percent_change_not_bet_share_change"])
                   for r in moves if r["horse_number"] in (8,13,3,14,9))
    return {
        "status":"PUBLIC_INTERMEDIATE_MULTIPOOL_SOURCE_CONDITIONAL_DESCRIPTIVE_COMPARISON_ONLY",
        "source_prior_win_retrieval_JST":earlier["observation_started_at_jst"],
        "source_later_four_pool_retrieval_JST":snapshot["observation_started_jst"],
        "source_later_reported_update_timestamp":"UNKNOWN",
        "not_a_simultaneously_locked_cross_pool_price_vector":True,
        "official_JRA_source_winners_performance_NOT_USED":True,
        "model_frozen_C1_U_Q1_K1_or_M_rules_not_modified":True,
        "prior_assistant_ordinal_ranks_NOT_user_supplied_calibrated_probabilities":True,
        "exact_frozen_v31_market_M_top5":sorted(m),
        "exact_frozen_v31_nonmarket_six":sorted(BASE_NON_M),
        "market_shadow_union":total,
        "market_shadow_union_fraction":len(total)/17,
        "pair_event_rank_inversion":race,
        "win_wide_quinella_anchor8_partner_ranks_16_comparable_members":
            anchor_partner_rankings,
        "source_market_rank_14_place_tilt_relative_to_win_order_only":
            win_rank[14]-wide_rank[14],
        "source_market_rank_3_place_tilt_relative_to_win_order_only":
            win_rank[3]-wide_rank[3],
        "source_market_rank_9_place_tilt_relative_to_win_order_only":
            win_rank[9]-wide_rank[9],
        "selected_pair_quotes":pairs,
        "selected_three_horse_quotes_partial_pool_ONLY":selected_trios,
        "first_win_rank_vs_later_win_rank_changes_all_17":moves,
        "largest_watched_8_13_3_14_9_absolute_win_odds_pct_change":
            max_change,
        "prior_assistant_vs_later_win_market_rank":author,
        "frozen_v31_does_NOT_estimate_a_fair_odds_value":True,
        "wide_range_is_quote_NOT_actual_payoff_or_top3_chance":True,
        "pool_specific_bettor_preference_not_true_place_vs_win_probability":True,
        "no_positive_expected_value_recommendation":True,
        "no_wager_purchased":True,
        "not_v31_formal_prerace_holdout_15_to_25min_window":True,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=NEW_SNAPSHOT)
    p.add_argument("--prior",type=Path,default=EARLIER_SINGLE_SNAPSHOT)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    s=json.loads(args.source.read_text(encoding="utf-8"))
    old=json.loads(args.prior.read_text(encoding="utf-8"))
    result=audited(s,old,source_base())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                          encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "market_M":result["exact_frozen_v31_market_M_top5"],
        "market_shadow_union":result["market_shadow_union"],
        "pool_event_inversion":result["pair_event_rank_inversion"],
        "watched_odds_max_absolute_change_pct":
            result["largest_watched_8_13_3_14_9_absolute_win_odds_pct_change"],
        "official_JRA_update_time_NOT_claimed":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
