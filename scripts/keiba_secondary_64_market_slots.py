#!/usr/bin/env python3
"""PREDECLARED auxiliary 64 JRA-market shadow slots on 8 future meeting dates.

A 26-race, 20-day already-frozen graded cohort cannot meet the minimum
60-race development guard in the earlier PR10 protocol. Do not pretend
its 25 not-yet-observed next-market candidate races are 60 samples.

This auxiliary denominator is a separate, nonreplacement EXPERIMENT:
select the FIRST 8 distinct future date rows in the *unchanged* graded
calendar and, for each date, the VENUE of the FIRST registered grade
event; nominate all local numbered flat R05 through R12 (8 per date).
This deterministic rule selects 8*8=64 future date-venue-race-number slots
WITHOUT seeing any future winner, betting price, cards or horses.

All 64 are merely PROPOSED SLOT NUMBERS. Some calendar race orders, type,
post time or permissions may change. Confirm with lawful official cards
before any freeze, leave cancelled/not-observed slots missing, NEVER
substitute a different date, venue or race. A date with 8 hypothetical
slots is one date cluster, not 8 independent calendar clusters.

The auxiliary sample may overlap the original 26-grade campaign; NEVER
sum raw counts or treat that overlap as independent. Source race IDs and
all full-field odds, past form and GitHub proof remain unavailable. This
script accepts no raw quote rows or private forecasts and creates none.
"""
from __future__ import annotations
import argparse
from datetime import datetime, date
import json
from pathlib import Path

from keiba_fixed_denominator_market_campaign import (
    ROOT, _locked_universe, _aware, JST,
    CALENDAR_GIT_BLOB_SHA, REGISTRY_GIT_BLOB_SHA,
    LOCKED_MARKET_HORIZON_MINUTES, LOCKED_MARKET_TARGET_WINDOW_MINUTES,
)

STATUS="AUXILIARY_FIXED_64_MARKET_SLOTS_NOT_JRA_OFFICIAL_RACE_CARDS"
START_AFTER="2026-10-25"
DATE_COUNT=8
RACE_NUMBERS=tuple(range(5,13))
AUX_SCHEMA="KEIBA_AUXILIARY_FIXED_64_MARKET_SLOT_REGISTRY_V1"
EXPLICIT_FIRST_8_DAY_VENUE=(
    ("2026-10-31","京都"),
    ("2026-11-01","東京"),
    ("2026-11-07","東京"),
    ("2026-11-08","東京"),
    ("2026-11-14","東京"),
    ("2026-11-15","京都"),
    ("2026-11-21","福島"),
    ("2026-11-22","京都"),
)


def defined_slots(root=ROOT):
    source,coverage=_locked_universe(root)
    ordered={}
    for entry in source:
        when=entry["scheduled_date_jst"]
        if when>START_AFTER and when not in ordered:
            ordered[when]=entry["venue"]
    assigned=tuple(list(ordered.items())[:DATE_COUNT])
    if assigned!=EXPLICIT_FIRST_8_DAY_VENUE:
        raise ValueError("HOLD_SECONDARY_RACE_DATE_VENUE_SELECTION_CHANGED")
    slots=[]
    for day,venue in assigned:
        for n in RACE_NUMBERS:
            slots.append({
                "slot_id":f"{day}|{venue}|R{n:02d}",
                "scheduled_date_jst":day,
                "venue":venue,
                "planned_race_number_not_official":n,
                "source_calendar_git_blob_sha":CALENDAR_GIT_BLOB_SHA,
                "is_verified_official_race_ID_or_post_time":False,
                "full_WIN_2point_and_WIDE_grid_received":False,
                "original_horse_form_asof_attested":False,
                "separately_SHA_frozen_before_next_quote":False,
                "source_rights_independently_verified":False,
                "predeclared_target_horizon_minutes":LOCKED_MARKET_HORIZON_MINUTES,
                "predeclared_target_window_minutes":
                    LOCKED_MARKET_TARGET_WINDOW_MINUTES,
                "counted_as_new_prospective_scored_trial":False,
                "status":"UPCOMING_AUXILIARY_SLOT_UNACQUIRED",
            })
    if (len(slots)!=64 or len({x["slot_id"] for x in slots})!=64
            or len({x["scheduled_date_jst"] for x in slots})!=8):
        raise ValueError("HOLD_AUXILIARY_64_DENOMINATOR_DRIFT")
    return slots


def audit(root=ROOT, *, asof="2026-10-25T23:18:00+09:00"):
    now=_aware(asof)
    slots=defined_slots(root)
    for s in slots:
        d=date.fromisoformat(s["scheduled_date_jst"])
        if d<now.date():
            s["status"]="PAST_UNCOLLECTED_DO_NOT_DROP_FROM_DENOMINATOR"
        elif d==now.date():
            s["status"]="SAME_DATE_UNVERIFIED_POST_DO_NOT_DECIDE_IF_CLOSED"
    return {
        "schema":AUX_SCHEMA,
        "status":STATUS,
        "as_of_jst":now.isoformat(),
        "original_frozen_26_race_calendar_blob":CALENDAR_GIT_BLOB_SHA,
        "original_frozen_26_race_registry_blob":REGISTRY_GIT_BLOB_SHA,
        "auxiliary_real_future_market_targets_collected":0,
        "auxiliary_source_and_target_remote_Sha_authenticated":0,
        "old_26_race_calendar_unchanged":True,
        "future_independent_races_only_after_actual_proven_capture":0,
        "predeclared_auxiliary_slots":len(slots),
        "predeclared_distinct_meeting_dates":DATE_COUNT,
        "dates_and_selected_venues":[{"day":a,"venue":b}
                                     for a,b in EXPLICIT_FIRST_8_DAY_VENUE],
        "race_numbers_in_each_date":list(RACE_NUMBERS),
        "target_horizon_plus_window_minutes":[
            LOCKED_MARKET_HORIZON_MINUTES,
            LOCKED_MARKET_TARGET_WINDOW_MINUTES],
        "nominal_60race_8date_development_slot_capacity":True,
        "observed_60race_8date_development_guard_met":False,
        "cannot_pool_with_grade_26_without_deduplicating_race_ids":True,
        "actual_official_race_ids_and_post_times_not_recorded_here":True,
        "some_proposed_slots_may_change_or_be_canceled":True,
        "no_real_future_vote_flow_GPS_or_market_criticality":"HOLD",
        "slots":slots,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of",default=datetime.now(JST).isoformat())
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    out=audit(asof=args.as_of)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "fixed_future_slots":out["predeclared_auxiliary_slots"],
        "distinct_dates":out["predeclared_distinct_meeting_dates"],
        "genuine_new_observations":out[
            "auxiliary_real_future_market_targets_collected"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
