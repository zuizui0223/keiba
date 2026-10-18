#!/usr/bin/env python3
"""Audit 2026 Shuka Sho race-day genuine JRA odds and other public pools.

The primary 17 single-win quotes come from the JRA official racecard
with an EXPLICIT source update timestamp; all 136 wide and all 136
quinella pair prices come from independently refreshed SportsNavi
public pools. Cross-pool values are NOT an atomic market snapshot.

Compare against original Saturday 2026-10-17 15:37 intermediate
quotes, unchanged v3.1 C1/U/Q1/K1/M rules, and earlier ASSISTANT
subjective ordinal ranks. NOT calibrated horse probabilities,
positive EV, or the formal 15–25-min prospective holdout freeze.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

from shuka2026_market_overlay import HERE, source_base, START
from v31_candidate_channels import market_channel
from shuka2026_multipool_valuation_gap import (
    _validate_pair_rows, BASE_NON_M, OUR_HISTORICAL_QUALITATIVE_RANKS,
)

RACE_DAY=HERE/"data/2026-10-18/shuka2026-JRA-official-win-plus-multipool-morning.json"
SATURDAY=HERE/"data/2026-10-17/shuka2026-sportsnavi-multipool-intermediate-1537.json"
SOURCE_TIMESTAMP="2026-10-18T11:42:00+09:00"
PRIOR_TIMESTAMP="2026-10-17T15:37:39+09:00"
PUBLISHER_NAME="JRA"
SOURCE_JRA_URL="https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0108202604071120261018%2F30"
SOURCE_WIDE_URL="https://sports.yahoo.co.jp/keiba/race/odds/wide/2608040711?ninki=1"
SOURCE_QUIN_URL="https://sports.yahoo.co.jp/keiba/race/odds/ur/2608040711?ninki=1"
ALL=set(range(1,18))
SELECTED_PAIRS=((8,13),(8,6),(8,3),(8,14),(8,9),(8,4),(13,14),(3,14))
NOT_EVALUATED="NOT_ESTIMATED_MODEL_FAIR_WIN_OR_TOP3_PROBABILITY"


def _check_time(t:str)->datetime:
    try:
        d=datetime.fromisoformat(t)
    except (TypeError,ValueError) as exc:
        raise ValueError("HOLD_SOURCE_PUBLICATION_TIME_NOT_VERIFIABLE") from exc
    if d.utcoffset()!=timedelta(hours=9) or not d<START:
        raise ValueError("HOLD_NOT_GENUINE_BEFORE_RACE_JRA_ODDS_TIME")
    return d


def verify(official:dict,sat:dict,base:dict)->tuple[list[dict],dict,dict,dict,list[dict],dict]:
    if (official.get("schema")!="SHUKA2026_PUBLIC_ORIGINAL_JRA_WIN_AND_SPORTSNAVI_3_BET_POOLS_OCT18_V1"
        or official.get("status")!="ORIGINAL_JRA_EXPLICIT_MINUTE_OFFICIAL_WIN_PRICES_WITH_SEPARATE_THIRD_PARTY_PAIRS"
        or official.get("event",{}).get("race_id")!="2026-10-18-KYOTO-11"
        or official["event"].get("going")!="良"
        or official["event"].get("registered_runners")!=17):
        raise ValueError("HOLD_NOT_CORRECT_ORIGINAL_JRA_SHUKA_COHORT")
    jra=official["first_party_JRA_win"]
    if (jra.get("source_url")!=SOURCE_JRA_URL
        or jra.get("publisher_explicit_update_timestamp_jst")!=SOURCE_TIMESTAMP
        or not jra.get("provider_timestamp_was_extracted_not_invented")):
        raise ValueError("HOLD_JRA_OFFICIAL_QUOTE_PUBLICATION_TIME_NOT_VERIFIED")
    _check_time(jra["publisher_explicit_update_timestamp_jst"])
    if (sat.get("schema")!="SHUKA2026_PUBLIC_MULTIPOOL_SPORTSNAVI_INTERMEDIATE_20261017_V1"
        or sat.get("observation_started_jst")!=PRIOR_TIMESTAMP):
        raise ValueError("HOLD_PREVIOUSLY_ARCHIVED_SATURDAY_MARKET_CHANGED")
    info=official["separately_refreshed_SportsNavi"]
    if (info["source_urls"].get("wide")!=SOURCE_WIDE_URL
        or info["source_urls"].get("quinella")!=SOURCE_QUIN_URL
        or info.get("source_last_update_timestamp")!="NOT_EXPOSED"
        or not info.get("source_pages_NOT_atomic_cross_pool_snapshot")):
        raise ValueError("HOLD_UNRECONCILED_PUBLIC_WIDE_AND_QUINELLA_SOURCE")
    official_lines=jra["displayed_official_win_prices_all_17"]
    third=info["win_odds_all_17"]
    if (len(official_lines)!=17 or len(third)!=17
        or set(x.get("horse_number") for x in official_lines)!=ALL
        or set(x.get("horse_number") for x in third)!=ALL):
        raise ValueError("HOLD_ORIGINAL_JRA_OR_PUBLIC_WIN_NOT_ALL_17")
    lookup={z["official_horse_number"]:z["horse_name"] for z in base["horse_records"]}
    if set(lookup)!=ALL:
        raise ValueError("HOLD_MISMATCH_PRE_RACE_JRA_17_IDENTITY")
    single={}
    secondary={x["horse_number"]:x for x in third}
    for r in official_lines:
        n=r["horse_number"]
        odd=r.get("official_displayed_win_odds")
        rank=r.get("official_odds_market_rank")
        if (r.get("horse_name")!=lookup[n]
            or secondary[n].get("horse_name")!=lookup[n]
            or type(odd) not in (int,float) or not math.isfinite(odd) or odd<1
            or type(rank) is not int or not 1<=rank<=17):
            raise ValueError("HOLD_ORIGINAL_OFFICIAL_HORSE_OR_WIN_VALUE_INVALID")
        single[n]={"number":n,"name":lookup[n],"odds":odd,"rank":rank}
    if sorted(z["rank"] for z in single.values())!=list(range(1,18)):
        raise ValueError("HOLD_JRA_RACE_DAY_MARKET_RANK_NOT_ALL_17")
    market_sorted=sorted(single.values(),key=lambda x:(x["odds"],x["number"]))
    if [v["rank"] for v in market_sorted]!=list(range(1,18)):
        raise ValueError("HOLD_REAL_JRA_PAYOUT_RANK_INCONSISTENT_WITH_PRICE")
    if any(secondary[n]["win_odds"]!=single[n]["odds"]
           or secondary[n]["market_rank"]!=single[n]["rank"] for n in ALL):
        raise ValueError("HOLD_ORIGINAL_JRA_AND_THIRD_PARTY_QUOTES_NOT_EQUAL_IN_THIS_ARCHIVE")
    wide=_validate_pair_rows([
        {"rank":row["market_rank"],"horse_numbers":row["horse_numbers"],
         "quoted_odds_min":row["payout_odds_low"],
         "quoted_odds_max":row["payout_odds_high"]}
        for row in info["wide_odds_all_136"]
    ],wide=True)
    quin=_validate_pair_rows([
        {"rank":row["market_rank"],"horse_numbers":row["horse_numbers"],
         "quoted_odds":row["displayed_odds"]}
        for row in info["quinella_odds_all_136"]
    ],wide=False)
    triples=info["selected_trio_only_not_full_680"]
    if not (isinstance(triples,list) and 1<=len(triples)<680
            and len({tuple(r["horse_numbers"]) for r in triples})==len(triples)):
        raise ValueError("HOLD_PARTIAL_3HORSE_SOURCE_NOT_VALIDATED")
    for z in triples:
        if (len(z["horse_numbers"])!=3
            or any(n not in ALL for n in z["horse_numbers"])
            or type(z.get("displayed_odds")) not in (int,float)
            or not math.isfinite(z["displayed_odds"])
            or z["displayed_odds"]<1):
            raise ValueError("HOLD_THREE_HORSE_BET_QUOTE_INVALID")
    prior_win=sat["win_prices_all_17"]
    if len(prior_win)!=17 or set(z["horse_number"] for z in prior_win)!=ALL:
        raise ValueError("HOLD_SATURDAY_PRIOR_SINGLE_MARKET_INCOMPLETE")
    prev={z["horse_number"]:z for z in prior_win}
    if any(prev[n]["name"]!=lookup[n] for n in ALL):
        raise ValueError("HOLD_SATURDAY_SOURCE_ORIGINAL_NAME_MISMATCH")
    if len(sat["wide_pair_all_136"])!=136 or len(sat["quinella_pair_all_136"])!=136:
        raise ValueError("HOLD_YESTERDAY_WIDE_OR_QUINELLA_NOT_ALL_136")
    # Independently revalidate prior pair identities and ranges as well.
    old_wide=_validate_pair_rows(sat["wide_pair_all_136"],wide=True)
    old_quin=_validate_pair_rows(sat["quinella_pair_all_136"],wide=False)
    return market_sorted,wide,quin,prev,triples,{
        "wide":old_wide,"quinella":old_quin
    }


def compare(day:dict,previous:dict,base:dict)->dict:
    sorted_market,wide,quin,old,trio,oldpair=verify(day,previous,base)
    current={x["number"]:x for x in sorted_market}
    m=market_channel([{"number":x["number"],"win_odds":x["odds"]}
                       for x in sorted_market])
    if set(base["official_nonmarket_v31_candidate_numbers_NOT_RANKING"])!=BASE_NON_M:
        raise ValueError("HOLD_FROZEN_V31_HISTORICAL_CHANNELS_CHANGED")
    chosen=sorted(m|BASE_NON_M)
    if len(chosen)>17:
        raise ValueError("HOLD_CANDIDATE_COUNT_INVALID")
    prev_M=market_channel([{"number":n,"win_odds":old[n]["win_odds"]}
                           for n in ALL])
    inverse_sum=sum(1/x["odds"] for x in sorted_market)
    movements=[{
        "horse_number":n,"horse_name":current[n]["name"],
        "saturday_15_37_win_odds":old[n]["win_odds"],
        "sunday_JRA_11_42_win_odds":current[n]["odds"],
        "percent_change_in_payout_odds_NOT_change_in_win_probability":
            100*(current[n]["odds"]/old[n]["win_odds"]-1),
        "saturday_market_win_rank":old[n]["rank"],
        "sunday_official_JRA_market_win_rank":current[n]["rank"],
        "saturday_to_sunday_market_rank_change":
            current[n]["rank"]-old[n]["rank"],
        "Sunday_normalized_reciprocal_odds_market_weight_NOT_probability_percent":
            100/(current[n]["odds"]*inverse_sum),
        "unit_win_ticket_profit_breakeven_probability_percent_NOT_estimated_probability":
            100/current[n]["odds"],
        "in_frozen_nonmarket_C1_U_rescue":n in BASE_NON_M,
        "in_actual_Sunday_market_M":n in m,
    } for n in sorted(ALL)]
    def pack_pair(n:int,k:int)->dict:
        key=tuple(sorted((n,k)))
        a,b=wide[key],oldpair["wide"][key]
        c,d=quin[key],oldpair["quinella"][key]
        return {
            "horse_numbers":list(key),
            "SATURDAY_wide_rank_among_all136":b["rank"],
            "SUNDAY_wide_rank_among_all136":a["rank"],
            "SATURDAY_wide_payout_quote_range":[b["low"],b["high"]],
            "SUNDAY_wide_payout_quote_range":[a["low"],a["high"]],
            "low_end_wide_odds_percent_change_NOT_probability":
                100*(a["low"]/b["low"]-1),
            "SATURDAY_quinella_rank_among_all136":d["rank"],
            "SUNDAY_quinella_rank_among_all136":c["rank"],
            "SATURDAY_quinella_odds":d["odds"],
            "SUNDAY_quinella_odds":c["odds"],
            "wide_joint_top3_breakeven_probability_percent_if_payout_at_Sunday_range":
                [100/a["high"],100/a["low"]],
            "quinella_joint_top2_breakeven_percent_if_same_quote":
                100/c["odds"],
        }
    pairs=[pack_pair(*x) for x in SELECTED_PAIRS]
    def event_partner_ranks(o:dict,w:dict,q:dict)->dict:
        others=sorted(ALL-{8})
        win_r={n:i+1 for i,n in enumerate(
            sorted(others,key=lambda n:(o[n]["odds"] if "odds" in o[n] else o[n]["win_odds"],n))
        )}
        w_r={n:i+1 for i,n in enumerate(
            sorted(others,key=lambda n:w[tuple(sorted((8,n)))]['rank'])
        )}
        q_r={n:i+1 for i,n in enumerate(
            sorted(others,key=lambda n:q[tuple(sorted((8,n)))]['rank'])
        )}
        return {n:{"win_partner_rank_16":win_r[n],
                   "wide_partner_rank_16":w_r[n],
                   "quinella_partner_rank_16":q_r[n],
                   "wide_rank_gain_relative_to_win_partner_order":
                       win_r[n]-w_r[n]} for n in others}
    sundayr=event_partner_ranks(current,wide,quin)
    satr=event_partner_ranks(old,oldpair["wide"],oldpair["quinella"])
    watched=[]
    prior_qualitative=[8,13,3,14,4,1,9]
    if prior_qualitative!=OUR_HISTORICAL_QUALITATIVE_RANKS:
        raise ValueError("HOLD_PREVIOUS_OUR_OPINION_RANK_REWRITTEN_AFTER_MARKET")
    for rank,n in enumerate(prior_qualitative,start=1):
        watched.append({
            "horse_number":n,"name":current[n]["name"],
            "earlier_ASSISTANT_qualitative_order_NOT_users_calibrated_probability":rank,
            "actual_Sunday_JRA_market_rank":current[n]["rank"],
            "market_minus_assistant_rank":current[n]["rank"]-rank,
            "SUNDAY_JRA_win_odds":current[n]["odds"],
            "old_8_fixed_win_wide_quinella_partner_ranks":
                satr.get(n),
            "SUNDAY_8_fixed_win_wide_quinella_partner_ranks":
                sundayr.get(n)
        })
    if sundayr[14]["wide_partner_rank_16"]>=sundayr[3]["wide_partner_rank_16"] and satr[14]["wide_partner_rank_16"]<satr[3]["wide_partner_rank_16"]:
        wide_reversal="PRIOR_14_WIDE_MORE_POPULAR_THAN_3_BUT_SUNDAY_3_WIDE_MORE_POPULAR"
    else:
        wide_reversal="NO_YESTERDAY_TO_SUNDAY_14_VS_3_WIDE_ORDER_REVERSAL"
    monitored_moved=sorted([
        z for z in movements
        if z["horse_number"] in {8,13,3,14,9}
        and abs(z["percent_change_in_payout_odds_NOT_change_in_win_probability"])>=20
    ],key=lambda z:abs(z["percent_change_in_payout_odds_NOT_change_in_win_probability"]),reverse=True)
    return {
        "status":"ORIGINAL_JRA_SUNDAY_1142_BETTING_MARKET_AND_SATURDAY_MULTIPOOL_DIFFERENCE",
        "official_JRA_odds_publication_jst":
            day["first_party_JRA_win"]["publisher_explicit_update_timestamp_jst"],
        "official_JRA_win_source_url":
            day["first_party_JRA_win"]["source_url"],
        "current_Kyoto_turf_going":"良",
        "SUNDAY_wide_quote_source_url":
            day["separately_refreshed_SportsNavi"]["source_urls"]["wide"],
        "SUNDAY_quinella_source_url":
            day["separately_refreshed_SportsNavi"]["source_urls"]["quinella"],
        "SUNDAY_trio_source_url":
            day["separately_refreshed_SportsNavi"]["source_urls"]["trio"],
        "SUNDAY_SportsNavi_pool_page_quote_publication_time_UNKNOWN":True,
        "multi_pool_sources_may_have_been_refreshed_at_different_times":True,
        "compared_original_source_Saturday_15_37_JST":
            previous["observation_started_jst"],
        "genuine_JRA_official_seventeen_horses_verified":True,
        "JRA_and_SportsNavi_17_win_quotes_exactly_match_on_these_saved_pages":True,
        "frozen_v31_market_M_on_JRA_official_priced_five":sorted(m),
        "frozen_v31_last_Saturday_M_on_public_actual_five":sorted(prev_M),
        "frozen_v31_market_M_CHANGED":m!=prev_M,
        "frozen_v31_original_nonmarket_six":sorted(BASE_NON_M),
        "frozen_v31_market_plus_history_shadow_union":chosen,
        "frozen_v31_shadow_candidate_fraction":len(chosen)/17,
        "frozen_v31_thresholds_or_model_weights_NOT_changed":True,
        "WATCH_wide_8_14_vs_8_3_event_order_reversal":wide_reversal,
        "earlier_vs_Sunday_assistant_opinion_rank":watched,
        "actual_17_official_win_market_vs_Saturday":movements,
        "watch_prices_20pct_or_more_changed_since_Saturday":monitored_moved,
        "selected_pair_market_change":pairs,
        "SUNDAY_8_fixed_partner_rank_per_16_other_horses":{
            str(n):sundayr[n] for n in sorted(ALL-{8})
        },
        "SATURDAY_8_fixed_partner_rank_per_16_other_horses":{
            str(n):satr[n] for n in sorted(ALL-{8})
        },
        "selected_Sunday_trios_ONLY_not_all_680":
            day["separately_refreshed_SportsNavi"]["selected_trio_only_not_full_680"],
        "Sunday_reciprocal_odds_sum_NOT_a_probability_model":inverse_sum,
        "no_ASSISTANT_or_USER_supplied_calibrated_win_top3_or_top2_probabilities":True,
        "no_positive_expected_value_proof":True,
        "no_wagers_or_orders_executed":True,
        "not_formal_15_to_25min_JRA_pre_start_holdout":True,
        "not_prospectively_validated_better_than_market":True,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=RACE_DAY)
    p.add_argument("--prior",type=Path,default=SATURDAY)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=compare(
        json.loads(args.source.read_text(encoding="utf-8")),
        json.loads(args.prior.read_text(encoding="utf-8")),
        source_base()
    )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "JRA_publisher_update":result["official_JRA_odds_publication_jst"],
        "market_M":result["frozen_v31_market_M_on_JRA_official_priced_five"],
        "union":result["frozen_v31_market_plus_history_shadow_union"],
        "wide_8_14_vs_8_3":result["WATCH_wide_8_14_vs_8_3_event_order_reversal"],
        "large_odds_moves":[
            (x["horse_number"],round(x["percent_change_in_payout_odds_NOT_change_in_win_probability"],1))
            for x in result["watch_prices_20pct_or_more_changed_since_Saturday"]
        ],
        "formal_v31_holdout":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
