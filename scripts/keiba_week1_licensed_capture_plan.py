#!/usr/bin/env python3
"""Operator checklist for first TWO publicly announced JRA programme dates.

2026-10-31 Kyoto and 2026-11-01 Tokyo R05-R12 (16 preliminary
race-number slots) are drawn from the auxiliary 64-slot denominator.
Current official JRA RACE PROGRAMME page gives planned post times and
conditions but explicitly warns schedule and final runner cards can
change. None is a final race ID, published starter, actual WIN/WIDE
provider quote, independently time-attested capture or allowed stake.

Predefine morning operator observation checkpoints as post -100 and
post -65 minutes. These are APPEND attempts, not assumed official quote
source-update times. Target candidates (first eligible source quote)
are 15..20 minutes AFTER the ACTUAL middle quote update, NOT after
this planned checkpoint. Wrong or unavailable data -> HOLD.

No internet fetching, no scheduling/background automation, no bets.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta
import json
from pathlib import Path

from keiba_fixed_denominator_market_campaign import (
    JST,_aware,LOCKED_MARKET_HORIZON_MINUTES,
    LOCKED_MARKET_TARGET_WINDOW_MINUTES,_locked_universe,
)
from keiba_secondary_64_market_slots import defined_slots

STATUS="PLANNED_JRA_PROGRAMME_CAPTURE_TIMES_NOT_FINAL_ENTRANTS_OR_REAL_MARKET"
FIRST_BEFORE_POST_MINUTES=100
MIDDLE_BEFORE_POST_MINUTES=65
PROGRAMME_PAGES={
    "2026-10-31":{
        "venue":"京都",
        "official_preliminary_source_url":
            "https://jra.jp/keiba/calendar2026/2026/10/1031.html",
        # planned race number -> local post clock, metres, surface
        "races":{
            5:("12:25",2000,"芝"),6:("12:55",1400,"ダ"),
            7:("13:25",1800,"ダ"),8:("14:00",1200,"ダ"),
            9:("14:35",2000,"芝"),10:("15:10",1900,"ダ"),
            11:("15:45",1400,"芝"),12:("16:25",1600,"芝"),
        },
    },
    "2026-11-01":{
        "venue":"東京",
        "official_preliminary_source_url":
            "https://jra.jp/keiba/calendar2026/2026/11/1101.html",
        "races":{
            5:("12:20",2000,"芝"),6:("12:50",1400,"ダ"),
            7:("13:20",1600,"ダ"),8:("13:50",2400,"芝"),
            9:("14:25",1600,"芝"),10:("15:00",1300,"ダ"),
            11:("15:40",2000,"芝"),12:("16:25",1600,"ダ"),
        },
    },
}
LOCKED_QMID_MARKET_STUDY_HORIZON=(15,5)

# JRA official FAQ, https://jra.jp/faq/pop02/2_2.html :
# Tian-no-sho Autumn is a special-numbered-G1 Thursday-after-14 case.
# Ordinary Saturday graded cards usually show UNNUMBERED Thursday-after-16
# and numbered Friday-after-10 (some race-dependent 09:00 exceptions).
# A scheduled announcement must NEVER be confused with a RECEIVED final card.
PRELIMINARY_FINAL_CARD_RELEASE_CHECKS={
    "2026-10-31|京都|R11":{
        "rule":"ORDINARY_SATURDAY_GRADED_UNNUMBERED_THURSDAY_NUMBERED_FRIDAY",
        "check_unumbered_list_after_jst":"2026-10-29T16:00:00+09:00",
        "check_numbered_card_normally_after_jst":"2026-10-30T10:00:00+09:00",
        "provider_may_use_earlier_friday_09_special_exception":True,
        "racecard_confirmed_received":False,
        "source":"https://jra.jp/faq/pop02/2_2.html",
    },
    "2026-11-01|東京|R11":{
        "rule":"SPECIAL_G1_THURSDAY_NUMBERED_TENNO_SHO_AUTUMN",
        "check_numbered_card_after_jst":"2026-10-29T14:00:00+09:00",
        "exact_publication_time_not_yet_attested":True,
        "racecard_confirmed_received":False,
        "source":"https://jra.jp/faq/pop02/2_2.html",
    },
}


def plan_week1(*, asof="2026-10-26T01:14:00+09:00"):
    now=_aware(asof)
    selected=defined_slots()
    expected={x["slot_id"] for x in selected
              if x["scheduled_date_jst"] in PROGRAMME_PAGES}
    graded,_=_locked_universe()
    grade_ids={x["slot_id"] for x in graded}
    if len(expected)!=16:
        raise ValueError("HOLD_WEEK1_AUXILIARY_FIXED_DENOMINATOR_CHANGED")
    slots=[]
    for day,metadata in PROGRAMME_PAGES.items():
        for rn,(time,distance,surface) in metadata["races"].items():
            sid=f"{day}|{metadata['venue']}|R{rn:02d}"
            if sid not in expected:
                raise ValueError("HOLD_NONPREREGISTERED_WEEK1_RACE")
            post=_aware(f"{day}T{time}:00+09:00")
            source_attempt=post-timedelta(minutes=FIRST_BEFORE_POST_MINUTES)
            middle_attempt=post-timedelta(minutes=MIDDLE_BEFORE_POST_MINUTES)
            if not (source_attempt<middle_attempt<post-
                    timedelta(minutes=35)):
                raise ValueError("HOLD_NO_TIME_FOR_BEFORE_TARGET_SHA_COMMIT")
            overlapping=[
                x["slot_id"] for x in graded
                if x["scheduled_date_jst"]==day and
                   x["venue"]==metadata["venue"] and
                   (x["race_name_jp"] in
                    ("ファンタジーS","天皇賞（秋）")) and rn==11
            ]
            slots.append({
                "auxiliary_slot_id":sid,
                "date_jst":day,"venue":metadata["venue"],
                "programme_race_number_not_verified_final":rn,
                "programme_surface_not_verified_final":surface,
                "programme_distance_m_not_verified_final":distance,
                "planned_post_time_not_authoritative":
                    post.isoformat(),
                "programme_source_url":
                    metadata["official_preliminary_source_url"],
                "candidate_first_full_WIN_observation_jst":
                    source_attempt.isoformat(),
                "candidate_middle_WIN_and_WIDE_observation_jst":
                    middle_attempt.isoformat(),
                "target_start_only_after_actual_middle_update_minutes":
                    LOCKED_MARKET_HORIZON_MINUTES,
                "target_end_only_after_actual_middle_update_minutes":
                    LOCKED_MARKET_HORIZON_MINUTES+
                    LOCKED_MARKET_TARGET_WINDOW_MINUTES,
                "confirmed_official_card_or_runner_numbers_available":False,
                "authorized_provider_WIN_WIDE_captured":False,
                "actual_full_market_source_update_time_available":False,
                "externally_SHA_frozen_before_next_quote":False,
                "legitimate_next_price_scored":False,
                "status":"PRELIMINARY_PROGRAMME_WAIT_FOR_FINAL_CARD_AND_SOURCE",
                "possible_grade_calendar_overlap_slots":overlapping,
                "official_final_card_publication_check_only_not_receipt":
                    PRELIMINARY_FINAL_CARD_RELEASE_CHECKS.get(sid),
            })
    if (len(slots)!=16 or len({s["auxiliary_slot_id"] for s in slots})!=16
            or sum(bool(s["possible_grade_calendar_overlap_slots"])
                   for s in slots)!=2):
        raise ValueError("HOLD_WEEK1_PRELIMINARY_CAPTURE_READINESS_DRIFT")
    return {
        "status":STATUS,
        "asof_jst":now.isoformat(),
        "programme_review_date_jst":"2026-10-26",
        "2026_oct31_and_nov01_race_programme_only_not_final_start_list":True,
        "JRA_programme_warns_post_race_number_and_conditions_can_change":True,
        "first_two_auxiliary_dates_captured_as_scheduling_ideas":2,
        "predeclared_slots_in_first_two_dates":len(slots),
        "possible_overlap_with_prior_26_graded_race_calendar":2,
        "actual_full_field_win_wide_quote_snapshots_collected":0,
        "actually_authenticated_SHA_pre_next_price":0,
        "observed_next_market_targets":0,
        "potential_unique_after_proper_overlap_dedup_not_observations":16,
        "real_market_information_or_positive_wager_EV":"HOLD",
        "no_actual_scheduled_future_background_fetch":True,
        "special_Tenno_Sho_G1_numbered_card_Thu_after_14_distinct_from_regular_graded":True,
        "slots":slots,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of",default=datetime.now(JST).isoformat())
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args()
    result=plan_week1(asof=a.as_of)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                        encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "week1_planned_slots":result[
            "predeclared_slots_in_first_two_dates"],
        "actual_JRA_prices_ingested":
            result["actual_full_field_win_wide_quote_snapshots_collected"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
