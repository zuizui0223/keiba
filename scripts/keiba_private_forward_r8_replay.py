#!/usr/bin/env python3
"""Use ONE real archived R8 market solely as a future pipeline REPLAY TEST.

The 2026-10-12 Kyoto 8R quote source is already historic. A locally
invented freeze time is explicitly marked as historical_replay_unattested.
The separate SHA-locked 13:44 target is opened only AFTER the pre-13:44
feature freeze, never as a feature. No official finish or payout is read.

The resulting score MUST NOT be called independently pre-registered or
certified by a GitHub server timestamp. Replays test engineering ONLY.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from odds_real_multirace_archive_audit import SOURCE_SHA,read_file
from odds_r8_real_three_time_market import OTHER_SOURCE,_locked,_win_vector
from keiba_private_multirace_winwide_shadow import (
    ROOT,FEATURE_SCHEMA,TARGET_SCHEMA,
    freeze_source_bytes,score_target,score_cohort,
)

RACE_ID="2608040508"
PROVIDER="Yahoo/SportsNavi"


def make_pretarget_r8_document(root=ROOT):
    """Reads source-fixed first+middle WIN and middle WIDE. NO later file."""
    early=read_file(root,SOURCE_SHA[8][0])
    mid=read_file(root,SOURCE_SHA[8][1])
    wide=_locked(*OTHER_SOURCE["mid_wide"],root=root)
    if (early["race_id"]!=RACE_ID or mid["race"]!=8 or wide["race"]!=8
            or mid["updated_at_jst"]!=wide["updated_at_jst"]
            or len(early["horses"])!=11 or len(mid["quotes"]["win"])!=11
            or len(wide["quotes"]["wide"])!=55):
        raise ValueError("HOLD_R8_PRETARGET_MARKET_SNAPSHOT_INCOMPLETE")
    return {
        "schema":FEATURE_SCHEMA,
        "provenance":"historical_replay_unattested",
        "operator_confirmed_research_rights":False,
        "race_id":RACE_ID,
        "scheduled_post_jst":early["start_jst"],
        "race_distance_m":early["distance_m"],
        "provider":PROVIDER,
        "model_coefficient_lock_at_jst":"2026-10-12T12:20:00+09:00",
        # The following timestamp is a retrospective TEST FIXTURE, NOT a
        # recorded proof that this model existed before 13:44 in 2026.
        "local_forecast_created_at_jst":"2026-10-12T13:28:00+09:00",
        "horizon_minutes":18,
        "target_window_minutes":0,
        "first_win":{
            "market":"win","provider":PROVIDER,"source_clock_verified":True,
            "source_updated_at_jst":early["odds_updated_at_jst"],
            "received_at_jst":early["odds_observed_at_jst"],
            "odds_by_horse_number":{
                str(v["number"]):v["win_odds"] for v in early["horses"]},
        },
        "middle_win":{
            "market":"win","provider":PROVIDER,"source_clock_verified":True,
            "source_updated_at_jst":mid["updated_at_jst"],
            "received_at_jst":mid["observed_at_jst"],
            "odds_by_horse_number":{
                str(v["selection"][0]):v["odds_low"]
                for v in mid["quotes"]["win"]},
        },
        "middle_wide":{
            "market":"wide","provider":PROVIDER,"source_clock_verified":True,
            "source_updated_at_jst":wide["updated_at_jst"],
            "received_at_jst":wide["observed_at_jst"],
            "pairs":wide["quotes"]["wide"],
        },
    }


def read_later_r8_series(root=ROOT):
    """Opens the later price file independently AFTER the model freeze."""
    future=_locked(*OTHER_SOURCE["late_all"],root=root)
    if future["race_id"]!=RACE_ID or future["horse_count"]!=11:
        raise ValueError("HOLD_R8_LATER_SOURCE_IDENTITY")
    win=future["markets"]["win"]
    prices=_win_vector(win["quotes"])
    return {
        "schema":TARGET_SCHEMA,"race_id":RACE_ID,"provider":PROVIDER,
        "operator_declares_complete_capture_stream":True,
        "snapshots":[{
            "market":"win","provider":PROVIDER,"source_clock_verified":True,
            "source_updated_at_jst":win["updated_at_jst"],
            "received_at_jst":win["observed_at_utc"],
            "odds_by_horse_number":{str(n):p for n,p in prices.items()},
        }],
    }


def audit(root=ROOT,*,horse_draws=120,seed=20261025):
    source=make_pretarget_r8_document(root)
    raw=json.dumps(source,ensure_ascii=False,sort_keys=True,
                   separators=(",",":")).encode("utf-8")
    freeze=freeze_source_bytes(raw,horse_draws=horse_draws,
                               horse_seed=seed)
    # This function call is intentionally BELOW the freeze, so model
    # feature calculations cannot read the separately locked future.
    later=read_later_r8_series(root)
    scored=score_target(freeze,later)
    cohort=score_cohort([scored])
    return {
        "status":"ONE_ARCHIVED_R8_ENGINEERING_REPLAY_NO_REMOTE_PRESTART_PROOF",
        "source_date":"2026-10-12",
        "actual_source_races":1,
        "real_future_after_freeze_event_count":0,
        "original_model_did_not_exist_in_authentic_2026_10_12_seal":True,
        "sha_256_freeze_verifies_internal_bytes_not_historical_time":True,
        "n_market_models":len(freeze["payload"]["candidate_predictions"]),
        "n_horses":len(freeze["payload"]["horse_numbers"]),
        "n_score_models":len(scored["all_model_scores"]),
        "scores":scored["all_model_scores"],
        "synthetic_duplicate_cohort":cohort,
        "original_Kikka_and_v31_untouched":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--horse-draws",type=int,default=120)
    p.add_argument("--seed",type=int,default=20261025)
    p.add_argument("--output",type=Path,
                   default=Path("tmp/private-multirace-r8-replay.json"))
    a=p.parse_args()
    result=audit(horse_draws=a.horse_draws,seed=a.seed)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+
                        "\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
                      "models":result["n_score_models"],
                      "one_retro_race":1,"prospective_certified":False},
                     ensure_ascii=False))


if __name__=="__main__":
    main()
