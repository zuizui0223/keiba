#!/usr/bin/env python3
"""Compare immutable public intermediate SportsNavi tote odds with pre-odds opinion.

The JRA 17-runner list and unchanged v3.1 classifier are checked against
GitHub-pinned sources. This is a 2026-10-17 after-onset, source-displayed
intermediate shadow M calculation using frozen v3.1 market_channel().
It is NOT an official-JRA-HTML-verified prospective 15–25-min holdout
freeze, trained probability model, or user-calibrated win-chance estimate.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import math

from shuka2026_market_overlay import HERE, source_base, PRESALE_OPEN, START
from v31_candidate_channels import market_channel

SOURCE=HERE/"data/2026-10-17/shuka2026-sportsnavi-intermediate-win-odds.json"
MARKET_URL="https://sports.yahoo.co.jp/keiba/race/odds/tfw/2608040711?ninki=1"
OUR_HISTORICAL_QUALITATIVE_RANKS=[8,13,3,14,4,1,9]
NOT_MODEL_RANK="Earlier assistant qualitative order, not user's numeric estimated probabilities"
MODEL_HIST_NM={1,3,6,8,9,12}
JST=timezone(timedelta(hours=9))


def validate_source(odds:dict,base:dict)->list[dict]:
    if (odds.get("schema")!="SHUKA2026_SPORTSNAVI_ACTUAL_INTERMEDIATE_SINGLE_WIN_ODDS_17_V1"
        or odds.get("status")!="THIRD_PARTY_DISPLAYED_ACTUAL_PARIMUTUEL_ODDS_NOT_OFFICIAL_JRA_BYTE_VERIFIED"
        or odds.get("target_race")!="2026-10-18-KYOTO-11"
        or odds.get("quoted_source_url")!=MARKET_URL
        or odds.get("source_display_type")!="中間オッズ (not final payout and subject to change)"
        or odds.get("original_JRA_tote_html_byte_verification_not_performed") is not True
        or odds.get("source_page_last_updated_timestamp")!="NOT_EXPOSED_BY_THIS_EXTRACTION"
        or odds.get("source_odds_from_live_display_not_pre_event_forecast") is not True):
        raise ValueError("HOLD_UNVERIFIED_SOURCE_NOT_INTERMEDIATE_PUBLIC_MARKET")
    try:
        started=datetime.fromisoformat(odds["observation_started_at_jst"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("HOLD_NO_REAL_AFTER_SALE_TIME") from exc
    if (started.tzinfo is None or started.utcoffset()!=timedelta(hours=9)
        or not (PRESALE_OPEN<=started<START)):
        raise ValueError("HOLD_NOT_POST_TOTE_SALE_AND_BEFORE_START")
    people=odds.get("horses")
    if not isinstance(people,list) or len(people)!=17:
        raise ValueError("HOLD_INCOMPLETE_REAL_INTERMEDIATE_17_WIN_ODDS")
    cross={int(h["official_horse_number"]):h["horse_name"] for h in
           base["horse_records"]}
    if len(cross)!=17 or set(cross)!=set(range(1,18)):
        raise ValueError("HOLD_NOT_JRA_CONFIRMED_SEVENTEEN_RUNNERS")
    has=set()
    results=[]
    for row in people:
        number=row.get("number")
        if type(number) is not int or number not in cross or number in has:
            raise ValueError("HOLD_MISSING_DUPLICATE_OR_FAKE_OFFICIAL_HORSE_NUMBER")
        has.add(number)
        if str(row.get("name"))!=cross[number]:
            raise ValueError("HOLD_MARKET_NAME_DOES_NOT_MATCH_JRA_OFFICIAL_DRAW")
        price=row.get("win_odds")
        if type(price) not in (int,float) or not math.isfinite(price) or price<1:
            raise ValueError("HOLD_INVALID_OR_MISSING_DISPLAYED_REAL_WIN_ODDS")
        market_rank=row.get("market_rank")
        if type(market_rank) is not int or not 1<=market_rank<=17:
            raise ValueError("HOLD_NO_SOURCE_RANKED_PUBLIC_TOTE_ODDS")
        results.append({
            "number":number,"name":cross[number],"win_odds":float(price),
            "source_market_rank":market_rank,
        })
    if has!=set(range(1,18)):
        raise ValueError("HOLD_INCOMPLETE_JRA_RACE_ENTRANTS")
    sorted_market=sorted(results,key=lambda x:(x["win_odds"],x["number"]))
    if [r["source_market_rank"] for r in sorted_market]!=list(range(1,18)):
        raise ValueError("HOLD_PUBLISHER_ODDS_RANK_NOT_CONSISTENT")
    return sorted_market


def measure(odds:dict,base:dict)->dict:
    rows=validate_source(odds,base)
    market=market_channel([{"number":r["number"],"win_odds":r["win_odds"]}
                           for r in rows])
    hist=set(base["official_nonmarket_v31_candidate_numbers_NOT_RANKING"])
    if hist!=MODEL_HIST_NM:
        raise ValueError("HOLD_FROZEN_JRA_HISTORICAL_CANDIDATES_CHANGED")
    union=market|hist
    inverse_sum=sum(1/r["win_odds"] for r in rows)
    market_by_num={r["number"]:r for r in rows}
    ranked=[]
    for index,num in enumerate(OUR_HISTORICAL_QUALITATIVE_RANKS):
        r=market_by_num[num]
        ranked.append({
            "horse_number":num,"horse_name":r["name"],
            "earlier_ASSISTANT_qualitative_pre_market_rank":index+1,
            "current_market_rank":r["source_market_rank"],
            "market_rank_minus_earlier_assistant_rank":
                r["source_market_rank"]-(index+1),
            "actual_intermediate_win_odds":r["win_odds"],
            "breakeven_chance_for_unit_win_ticket_NOT_our_estimated_probability_percent":
                100/r["win_odds"],
            "renormalized_reciprocal_odds_weight_percent_NOT_calibrated_probability":
                100/(r["win_odds"]*inverse_sum),
            "in_frozen_historical_six":num in hist,
            "in_frozen_actual_odds_M_five":num in market,
        })
    full_market=[{
        "horse_number":r["number"],"horse_name":r["name"],
        "current_market_rank":r["source_market_rank"],
        "win_odds":r["win_odds"],
        "payout_breakeven_percent_NOT_win_probability":
            100/r["win_odds"],
        "renormalized_odds_weight_percent_NOT_win_probability":
            100/(r["win_odds"]*inverse_sum),
        "historical_v31_channel_candidate":r["number"] in hist,
        "M_top_5_win_odds":r["number"] in market,
        "in_complete_shadow_v31_union":r["number"] in union,
    } for r in rows]
    assert len(ranked)==7 and len(full_market)==17
    differences=sorted(ranked,key=lambda r:
                       r["market_rank_minus_earlier_assistant_rank"],
                       reverse=True)
    return {
        "status":"THIRD_PARTY_LIVE_INTERMEDIATE_ODDS_SHADOW_V31_M_AND_ORDINAL_DISAGREEMENT",
        "race":"2026-10-18 Kyoto 11R Shuka Sho GI",
        "odds_source_url":odds["quoted_source_url"],
        "source_market_observation_started_at_jst":
            odds["observation_started_at_jst"],
        "provider_last_update_time_not_available_from_extraction":True,
        "prices_can_move_before_actual_race_and_are_not_final":True,
        "original_JRA_win_odds_HTML_NOT_independently_verified":True,
        "historical_v31_classifier_blob_sha":
            base["original_v31_classifier_git_blob_SHA"],
        "frozen_v31_market_channel_ACTUALLY_EXECUTED_on_observed_prices":True,
        "market_M_numbers":sorted(market),
        "historical_nonmarket_C1_U_or_rescue_numbers":sorted(hist),
        "market_M_added_only_horse_numbers":sorted(market-hist),
        "historic_only_not_market_M_horse_numbers":sorted(hist-market),
        "market_M_cutoff_win_odds":max(market_by_num[n]["win_odds"] for n in market),
        "full_shadow_v31_candidate_union_numbers":sorted(union),
        "full_shadow_v31_candidate_union_size":len(union),
        "full_shadow_v31_candidate_fraction":len(union)/17,
        "not_formal_v31_holdout_15_25min_timed_source_freeze":True,
        "inverse_win_odds_sum_over_17_NOT_probability_calibration":inverse_sum,
        "relative_odds_weight_is_market_concentration_proxy_not_chance":True,
        "explicit_prior_ordinal_rank_description":NOT_MODEL_RANK,
        "earlier_assistant_qualitative_ranks_vs_crowd":ranked,
        "biggest_ordinal_underappreciation_by_crowd":differences[:2],
        "market_higher_than_qualitative_shortlist":
            [r for r in full_market if r["current_market_rank"]<=5
             and r["horse_number"] not in OUR_HISTORICAL_QUALITATIVE_RANKS],
        "market_intermediate_odds_all_17":full_market,
        "no_USER_supplied_calibrated_win_probabilities_to_compare":True,
        "no_measured_positive_expected_value_or_own_fair_odds":True,
        "not_a_profitable_ticket_purchase_recommendation":True,
    }


def main()->None:
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--source",type=Path,default=SOURCE)
    arg.add_argument("--output",type=Path,required=True)
    opts=arg.parse_args()
    base=source_base()
    quoted=json.loads(opts.source.read_text(encoding="utf-8"))
    result=measure(quoted,base)
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "source_capture_started_JST":result["source_market_observation_started_at_jst"],
        "market_M_actual_numbers":result["market_M_numbers"],
        "historical_model_M_additions":result["market_M_added_only_horse_numbers"],
        "full_union_shadow_numbers":result["full_shadow_v31_candidate_union_numbers"],
        "full_union_fraction":result["full_shadow_v31_candidate_fraction"],
        "first_three_rank_equal":all(
            r["earlier_ASSISTANT_qualitative_pre_market_rank"]==
                r["current_market_rank"] for r in
            result["earlier_assistant_qualitative_ranks_vs_crowd"][:3]
        ),
        "remaining_model_not_calibrated_to_probability":True
    },ensure_ascii=False))


if __name__=="__main__":
    main()
