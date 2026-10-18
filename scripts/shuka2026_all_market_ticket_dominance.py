#!/usr/bin/env python3
"""2026 秋華賞: cross-pool same-event and event-superset price dominance.

The source is the JRA original minute-stamped 17-runner win snapshot
and *separate* Yahoo/SportsNavi current public pools. All prices are
intermediate and the sites may not share the identical quote time.
DO NOT claim risk-free returns, positive EV, calibrated win chance,
or an exhaustive price census of 4080 trifecta quotes: we have only
the first 400 trifecta quotes. All eight normal single-race betting
types have source examples; WIN5 is multi-race and NOT covered.
The committed v3.1 classifier is never altered.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime,timedelta
from itertools import combinations
import json
import math
from pathlib import Path

from shuka2026_market_overlay import HERE,source_base
from v31_candidate_channels import market_channel

SOURCE=HERE/"data/2026-10-18/shuka2026-JRA-all-bet-pools-and-superset-20261018.json"
FIXED_HISTORY={1,3,6,8,9,12}
BEFORE_OUR_QUALITATIVE=[8,13,3,14,4,1,9]
N=17
SOURCE_STATUS="SHUKA2026_REAL_INTERMEDIATE_ALL_COMMON_BET_TYPES_20261018_V1"
FRAME_COUNT=36
Q_COUNT=136
W_COUNT=136
EXACTA_COUNT=272
TRIO_COUNT=680
PARTIAL_TRIFECTA_COUNT=400


def pairkey(a,b):
    return tuple(sorted((a,b)))


def _validate_market(rows,*,required_count,size):
    if len(rows)!=required_count:
        raise ValueError("HOLD_MARKET_TABLE_NOT_COMPLETE_FOR_TICKET_FAMILY")
    pool={}
    for row in rows:
        numbers=tuple(row["numbers"])
        if (len(numbers)!=size or
            any(type(n) is not int or n<1 or n>17 for n in numbers) or
            not all(isinstance(row.get("odds"),(int,float)) for _ in (0,)) or
            not math.isfinite(row["odds"]) or row["odds"]<1):
            raise ValueError("HOLD_INVALID_MARKET_TICKET_ODDS")
        if size==2 and numbers[0]>=numbers[1]:
            raise ValueError("HOLD_UNORDERED_MARKET_TICKET_NOT_CANONICAL")
        if size==3 and tuple(sorted(numbers))!=numbers:
            raise ValueError("HOLD_UNORDERED_TRIO_NOT_CANONICAL")
        if numbers in pool:
            raise ValueError("HOLD_DUPLICATE_MARKET_TICKET")
        pool[numbers]=row
    return pool


def validate_and_compare(source:dict)->dict:
    if (source.get("schema")!=SOURCE_STATUS
        or source.get("event",{}).get("field_size")!=N
        or source.get("event",{}).get("race")!="京都11R 第31回 秋華賞"
        or source.get("event",{}).get("going")!="良"
        or source.get("betting_pools_not_captured_atomically") is not True
        or source.get("quoted_prices_may_change_until_final_payout") is not True
        or source.get("not_captured_3ren_tan_quotes")!=3680):
        raise ValueError("HOLD_SOURCE_SCOPE_NOT_ORIGINAL_PRE_RACE_2026_SHUKA")
    stamp=datetime.fromisoformat(source["official_jra_win_published_at_jst"])
    if (stamp.utcoffset()!=timedelta(hours=9)
        or not datetime.fromisoformat("2026-10-18T09:00:00+09:00")<=stamp<
               datetime.fromisoformat("2026-10-18T15:40:00+09:00")):
        raise ValueError("HOLD_UNVERIFIED_OR_POSTRESULT_JRA_WIN_MARKET_TIME")
    if source["source_coverage_counts"]!={"jra":17,"win":17,
        "frame":36,"q":136,"wide":136,"exact":272,"trio":680,
        "trioTop":400,"trifectaTop":400}:
        raise ValueError("HOLD_BETTING_METHOD_SOURCE_DENOMINATOR_CHANGED")
    orig=source["official_JRA_win_all17"]
    other=source["published_third_party_win_place_all17"]
    if len(orig)!=N or len(other)!=N:
        raise ValueError("HOLD_JRA_OR_THIRD_PARTY_ACTIVE_RUNNERS_MISSING")
    origmap={r["number"]:r for r in orig}
    thirdmap={r["number"]:r for r in other}
    if (set(origmap)!=set(range(1,N+1))
        or set(thirdmap)!=set(origmap)):
        raise ValueError("HOLD_JRA_WIN_NUMBER_IDENTITY_NOT_COMPLETE")
    for n in origmap:
        a,b=origmap[n],thirdmap[n]
        if (a["name"]!=b["name"]
            or a["win_odds"]!=b["win_odds"]
            or a["rank"]!=b["rank"]
            or b["frame"] not in range(1,9)
            or b["place_low"]<1
            or b["place_high"]<b["place_low"]):
            raise ValueError("HOLD_NOT_SAME_SOURCE_WIN_PRICE_OR_RUNNER")
    if sorted(x["rank"] for x in orig)!=list(range(1,N+1)):
        raise ValueError("HOLD_NO_COMPLETE_JRA_ODDS_POPULARITY_RANKING")

    frame=source["frame_quinella_all36"]
    if (len(frame)!=36
        or sorted(x["rank"] for x in frame)!=list(range(1,37))
        or len({tuple(x["numbers"]) for x in frame})!=36):
        raise ValueError("HOLD_FRAME_QUINELLA_36_SOURCE_INCOMPLETE")
    frameMap={}
    for r in frame:
        a,b=r["numbers"]
        if not (1<=a<=b<=8 and 1<=r["odds"] and math.isfinite(r["odds"])):
            raise ValueError("HOLD_FRAME_SOURCE_QUOTE_INVALID")
        frameMap[(a,b)]=r
    if set(frameMap)!={(a,b) for a in range(1,9) for b in range(a,9)}:
        raise ValueError("HOLD_MISSING_VALID_FRAMES")
    qMap=_validate_market(
        source["horse_quinella_all136"],required_count=Q_COUNT,size=2
    )
    wMap=_validate_market(
        source["wide_all136"],required_count=W_COUNT,size=2
    )
    exactRows=source["horse_exacta_all272"]
    if (len(exactRows)!=EXACTA_COUNT or
        sorted(x["rank"] for x in exactRows)!=list(range(1,273))):
        raise ValueError("HOLD_NOT_ALL_272_TWO_ORDER_EXACTA_ROWS")
    exactMap={}
    for r in exactRows:
        a,b=r["numbers"]
        if (type(a) is not int or type(b) is not int or a==b
            or a not in origmap or b not in origmap
            or not isinstance(r["odds"],(int,float))
            or not math.isfinite(r["odds"]) or r["odds"]<1):
            raise ValueError("HOLD_INVALID_EXACTA_SOURCE_ROW")
        if (a,b) in exactMap:
            raise ValueError("HOLD_DUPLICATE_ORDERED_EXACTA")
        exactMap[(a,b)]=r
    if set(exactMap)!={(a,b) for a in range(1,18) for b in range(1,18) if a!=b}:
        raise ValueError("HOLD_EXACTA_NOT_ALL_272_ORDERED_PAIRS")
    for r in source["wide_all136"]:
        if (not math.isfinite(r["odds_high"]) or
            r["odds_high"]<r["odds"]):
            raise ValueError("HOLD_INVALID_PUBLIC_WIDE_LOWER_UPPER_RANGE")
    tMap=_validate_market(
        source["trio_all680_grid"],required_count=TRIO_COUNT,size=3
    )
    top=source["trio_top400_rank_list"]
    trifectaTop=source["trifecta_top400_rank_list_only_NOT_full4080"]
    if (len(top)!=PARTIAL_TRIFECTA_COUNT
        or len(trifectaTop)!=PARTIAL_TRIFECTA_COUNT
        or sorted(r["rank"] for r in top)!=list(range(1,401))
        or sorted(r["rank"] for r in trifectaTop)!=list(range(1,401))):
        raise ValueError("HOLD_CANNOT_LABEL_TOP400_AS_FULL_ORDERED_ODDS")
    # The pool may update between ninki=0 and ninki=1 source pages.
    # Verify triple tickets are source rows, not that their values
    # necessarily match after a non-atomic public source refresh.
    if any(tuple(r["numbers"]) not in tMap for r in top):
        raise ValueError("HOLD_SOURCE_TOP400_TRIO_KEYS_NOT_IN_ALL680")

    historical=set(source["v31_frozen_nonmarket_six"])
    if historical!=FIXED_HISTORY or (
        source["our_previous_assistant_qualitative_seven"]
        !=BEFORE_OUR_QUALITATIVE
    ):
        raise ValueError("HOLD_CHANGED_FROZEN_MODEL_OR_PREV_SUBJECTIVE_RANKING")
    prior=source_base()
    if set(prior["official_nonmarket_v31_candidate_numbers_NOT_RANKING"])!=historical:
        raise ValueError("HOLD_REAL_LOCKED_V31_HISTORICAL_COUNT_CHANGED")
    m=market_channel([{"number":n,"win_odds":origmap[n]["win_odds"]}
                      for n in origmap])
    if len(m)!=5:
        raise ValueError("HOLD_UNSUPPORTED_M_TIES_IN_THIS_SOURCE_QUOTE")
    if not m=={3,6,8,12,13}:
        raise ValueError("HOLD_THIS_SOURCE_CHANGED_2026_SOURCE_MARKET_M")

    coverage=Counter()
    byFrame={}
    for n,row in thirdmap.items():
        byFrame.setdefault(row["frame"],[]).append(n)
    allPairEdges={}
    for pair,q in qMap.items():
        a,b=pair
        fr=pairkey(thirdmap[a]["frame"],thirdmap[b]["frame"])
        frameQuote=frameMap[fr]["odds"]
        twoA=exactMap[(a,b)]["odds"]
        twoB=exactMap[(b,a)]["odds"]
        totalExactaStraddle=1/(1/twoA+1/twoB)
        minEqualStake=0.5*min(twoA,twoB)
        hWin=q["odds"]
        w=wMap[pair]
        frameOutcomes=sum(
            1 for x in combinations(range(1,N+1),2)
            if pairkey(thirdmap[x[0]]["frame"],thirdmap[x[1]]["frame"])==fr
        )
        result={
            "horse_pair":list(pair),
            "horse_quinella_market_rank":q["rank"],
            "horse_quinella_odds":hWin,
            "frame_pair":list(fr),
            "frame_quinella_odds":frameQuote,
            "frame_quinella_covers_number_of_distinct_horse_pairs":frameOutcomes,
            "frame_event_subset_or_same_pair":True,
            "frame_quinella_weakly_dominates_horse_pair_quinella_at_this_quote":
                frameQuote>=hWin,
            "two_order_exacta_odds":[twoA,twoB],
            "two_order_stake_optimally_balanced_effective_odds_INFINITE_GRANULARITY":
                totalExactaStraddle,
            "two_order_exacta_equal_100yen_each_WORST_case_effective_odds":
                minEqualStake,
            "two_order_exacta_equal_100yen_each_weakly_dominates_200yen_quinella":
                minEqualStake>=hWin,
            "wide_min_odds":w["odds"],
            "wide_max_odds":w["odds_high"],
            "wide_event_is_broader_than_top2_quinella_event":True
        }
        allPairEdges[pair]=result
        if result["frame_quinella_weakly_dominates_horse_pair_quinella_at_this_quote"]:
            coverage["frame_vs_horse_quinella_strict_relative_dominance"]+=1
        if minEqualStake>=hWin:
            coverage["two_100yen_exacta_vs_horse_200yen_quinella_min_payout_better"]+=1
        if totalExactaStraddle>=hWin:
            coverage["continuous_proportional_two_exacta_vs_quinella"]+=1

    # Narrow, transparent and EXPLICITLY selected after seeing market:
    # best *relative* ticket value among top-five quinella tickets
    # whose constituent horses were BOTH admitted independently
    # by the frozen NON-market classifier, using strict broad-event
    # coverage at at least the same displayed payoff multiple.
    consensus_top5=[
        x for p,x in allPairEdges.items()
        if x["horse_quinella_market_rank"]<=5
        and p[0] in historical and p[1] in historical
    ]
    edge=[r for r in consensus_top5
          if r["frame_quinella_weakly_dominates_horse_pair_quinella_at_this_quote"]]
    if not (len(edge)==1 and edge[0]["horse_pair"]==[6,8]
            and edge[0]["frame_pair"]==[3,4]
            and edge[0]["frame_quinella_odds"]==6.9
            and edge[0]["horse_quinella_odds"]==6.8
            and edge[0]["frame_quinella_covers_number_of_distinct_horse_pairs"]==4):
        raise ValueError("HOLD_SOURCE_CHANGED_NO_LONGER_EXACT_TOP_MARKET_CONSENSUS_RELATIVE_EDGE")

    selected=allPairEdges[(6,8)]
    # Total amount paid 200 JPY, same payout odds IF the win event
    # 6–8 actually occurs, at the quoted—not guaranteed final—odds.
    frameComparison={
        "best_single_ticket_for_model_and_market_top5_relative_payout_domination":
            "枠連 3-4",
        "IMPORTANT_frame_numbers_NOT_horse_numbers":True,
        "frame3_real_horse_numbers_and_names":[
            [n,thirdmap[n]["name"]] for n in sorted(byFrame[3])],
        "frame4_real_horse_numbers_and_names":[
            [n,thirdmap[n]["name"]] for n in sorted(byFrame[4])],
        "baseline_alternative":"馬連 6-8",
        "frame_quote":selected["frame_quinella_odds"],
        "horse_quinella_6_8_quote":selected["horse_quinella_odds"],
        "frame_covers_exactly_horse_quinella_pair_events":[
            list(p) for p in combinations(range(1,18),2)
            if pairkey(thirdmap[p[0]]["frame"],thirdmap[p[1]]["frame"])==(3,4)
        ],
        "identical_200yen_cost_bet_result_if_6_and_8_finish_top_two_frame_return_yen":
            200*selected["frame_quinella_odds"],
        "identical_200yen_cost_bet_result_if_6_and_8_finish_top_two_horse_quinella_return_yen":
            200*selected["horse_quinella_odds"],
        "ticket_price_advantage_over_specific_horse_pair_pct":
            100*(selected["frame_quinella_odds"]/selected["horse_quinella_odds"]-1),
        "win_probability_needed_if_that_frame_odds_final_and_true_estimate_available_pct":
            100/selected["frame_quinella_odds"],
        "THIS_IS_EVENT_SUPERSET_PLUS_PRICE_NOT_A_GUARANTEED_WIN_OR_POSITIVE_EV":True,
        "price_margin_is_only_0_1x_and_may_reverse_before_betting":True
    }
    alternative=[
        {
          "method":"ワイド","horses":[8,13],
          "quote_range":[wMap[(8,13)]["odds"],wMap[(8,13)]["odds_high"]],
          "joint_top3_breakeven_range_pct":[
              100/wMap[(8,13)]["odds_high"],
              100/wMap[(8,13)]["odds"]
          ],
          "qualitative":"most DIRECT overlap between prior assistant opinion and win/pair public popularity",
        },
        {
          "method":"ワイド","horses":[8,14],
          "quote_range":[wMap[(8,14)]["odds"],wMap[(8,14)]["odds_high"]],
          "joint_top3_breakeven_range_pct":[
              100/wMap[(8,14)]["odds_high"],
              100/wMap[(8,14)]["odds"]
          ],
          "qualitative":"largest subjective race-form contrast with current single-win public ranking; not independent model value"
        },
        {
          "method":"馬連","horses":[8,13],
          "quote":qMap[(8,13)]["odds"],
          "top2_breakeven_pct":100/qMap[(8,13)]["odds"],
          "qualitative":"public top pair and subjective top two; no stronger absolute EV claim"
        },
        {
          "method":"馬単","order":[8,13],
          "quote":exactMap[(8,13)]["odds"],
          "exact_order_breakeven_pct":100/exactMap[(8,13)]["odds"],
          "qualitative":"higher odds than quinella with stricter event; NOT free odds"
        },
        {
          "method":"3連複","horses":[3,8,13],
          "quote":tMap[(3,8,13)]["odds"],
          "top3_exact_set_breakeven_pct":100/tMap[(3,8,13)]["odds"],
          "qualitative":"exact assistant prior top 3, higher variance"
        },
    ]
    pairNotes=[
        allPairEdges[x] for x in
        ((6,8),(3,8),(8,13),(8,14),(8,9),(3,13),(3,4),(13,14),(11,12))
    ]
    return {
        "status":"ORIGINAL_JRA_WIN_PLUS_MULTI_TOTE_PRICE_STRUCTURE_EVENT_DOMINANCE_POSTHOC",
        "source_official_JRA_publication_time_jst":
            source["official_jra_win_published_at_jst"],
        "source_covered_methods":{
            "win":17,"place_ranges":17,"frame_quinella":36,
            "horse_quinella":136,"wide":136,"exacta":272,
            "trio_all":680,"trifecta_TOP400_ONLY":400,
            "trifecta_full_bet_combinations":4080,
            "WIN5_not_evaluable_with_one_race_only":True,
        },
        "third_party_multi_pool_publication_timestamps_NOT_VERIFIED":True,
        "all_ticket_prices_INTERMEDIATE_and_can_reverse":True,
        "independent_nonmarket_H_horses":sorted(historical),
        "public_top_five_official_M_horses":sorted(m),
        "independent_model_history_H_intersection_market_M":sorted(historical&m),
        "market_plus_history_7_candidate_union":sorted(historical|m),
        "source_independently_ranked_ASSISTANT_horses_NOT_calibrated_probabilities":
            BEFORE_OUR_QUALITATIVE,
        "model_and_market_consensus_top5_unordered_quinella_pairs":
            consensus_top5,
        "single_ticket_relative_dominance_case":frameComparison,
        "frame_vs_quinella_all_source_pair_relative_dominances":[
            x for x in allPairEdges.values()
            if x["frame_quinella_weakly_dominates_horse_pair_quinella_at_this_quote"]
        ],
        "source_pair_coverage_dominance_counts":dict(coverage),
        "representative_same_event_or_more_constrained_alternatives":alternative,
        "selected_other_pair_pricing_not_all_are_expected_value_edges":pairNotes,
        "not_proven_single_global_max_expected_value_no_true_probabilities":True,
        "original_frozen_v31_not_modified":True,
        "one_ticket_selected_only_on_specific_stated_criterion_not_global_bet_EV":True,
        "no_actual_bet_purchase":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    o=validate_and_compare(json.loads(args.source.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    s=o["single_ticket_relative_dominance_case"]
    print(json.dumps({
        "status":o["status"],
        "source_jra_time":o["source_official_JRA_publication_time_jst"],
        "historical_and_market_overlap":
            o["independent_model_history_H_intersection_market_M"],
        "single_ticket_conditional_relative_odds_advantage":
            s["best_single_ticket_for_model_and_market_top5_relative_payout_domination"],
        "frame_3_4_vs_horse_6_8_odds":[s["frame_quote"],s["horse_quinella_6_8_quote"]],
        "strict_frame_count":
            o["source_pair_coverage_dominance_counts"]["frame_vs_horse_quinella_strict_relative_dominance"],
        "outcome_or_probability_not_known":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
