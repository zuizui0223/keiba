#!/usr/bin/env python3
"""Reproduce EXACT locked v3.1 C1/U/Q1/K1/rescue for 2026 Shuka Sho.

Important: this is a before-draw, NO-MARKET, OUT-OF-HOLDOUT source audit.
It is not a calibrated winning probability, an actual odds forecast,
a formally timed v3.1 freeze, or a validated profitable betting model.
Do NOT alter any v3.1 coefficient/gate based on this race.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parents[1]
from v31_candidate_channels import classify_horse, uncertainty_flags, _enrich_last4

EXPECTED_HORSES=17
SOURCE_FILE=HERE/"data/2026-10-18/shuka-jra-official-17-pre-draw.json"
MANIFEST=HERE/"docs/v31-holdout-freeze.json"
CLASSIFIER=HERE/"scripts/v31_candidate_channels.py"
TARGET_DAY="2026-10-18"
TARGET_DISTANCE=2000
TARGET_CLASS_RANK=7


def blob_sha(path:Path)->str:
    value=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(value)).encode()+b"\0"+value).hexdigest()


def audit(inputs:dict,*,manifest:dict,actual_classifier_blob_sha:str)->dict:
    if inputs.get("schema")!="SHUKA2026_OFFICIAL_JRA_PRE_DRAW_17_HISTORY_V1":
        raise ValueError("HOLD_UNEXPECTED_OFFICIAL_JRA_SOURCE_SCHEMA")
    if (inputs.get("horse_numbers_available") is not False or
        inputs.get("actual_timestamped_win_odds_available") is not False or
        inputs.get("entry_order_is_not_official_horse_number") is not True):
        raise ValueError("HOLD_PRICE_OR_FRAME_STATUS_CHANGED_USE_FULL_FREEZE_INSTEAD")
    target=inputs["target"]
    if not (target["date"]==TARGET_DAY and target["venue"]=="京都"
            and target["race_number"]==11 and target["surface"]=="芝"
            and target["distance_m"]==TARGET_DISTANCE
            and target["class_rank"]==TARGET_CLASS_RANK):
        raise ValueError("HOLD_TARGET_SHUKA_GI_KYOTO_2000_NOT_VERIFIED")
    if manifest.get("status")!="frozen_for_prospective_holdout":
        raise ValueError("HOLD_V31_ORIGINAL_FREEZE_MANIFEST_INVALID")
    original_sha=manifest["frozen_blobs"]["classifier"]
    if actual_classifier_blob_sha!=original_sha:
        raise ValueError("HOLD_LOCKED_V31_CLASSIFIER_CODE_HAS_CHANGED")
    runners=inputs["runners"]
    if len(runners)!=EXPECTED_HORSES:
        raise ValueError("HOLD_NOT_17_ORIGINAL_CONFIRMED_JRA_ENTRIES")
    names=[r["name"] for r in runners]
    if len(set(names))!=EXPECTED_HORSES:
        raise ValueError("HOLD_DUPLICATE_ORIGINAL_JRA_RACE_HORSE_NAME")
    if sorted(r["entry_order_not_draw_number"] for r in runners)!=list(range(1,18)):
        raise ValueError("HOLD_JRA_ENTRY_ORDER_NOT_STABLE_SOURCE_ONLY")

    tiers=inputs["quality_tiers_verified_from_official_race_labels"]
    result=[]
    for source in runners:
        if source["age"]!=3:
            raise ValueError("HOLD_NOT_THREE_YEAR_OLD_JRA_GI")
        if (source.get("win_odds") is not None or
            source.get("number") is not None):
            raise ValueError("HOLD_NO_FAKE_HORSE_NUMBER_OR_WIN_ODDS")
        history=source["full_history_before_target"]
        if (not history or len(history)!=source["career_starts_before_target"]
            or history!=sorted(history,key=lambda x:x["date"],reverse=True)
            or source["last4"]!=history[:4]):
            raise ValueError("HOLD_INCOMPLETE_OR_UNSORTED_JRA_OFFICIAL_HORSE_HISTORY")
        if any(date.fromisoformat(v["date"])>=date.fromisoformat(TARGET_DAY)
               for v in history):
            raise ValueError("HOLD_AFTER_TARGET_HISTORY_DATA_LEAKAGE")
        if any(v["class_rank"] is None for v in history):
            raise ValueError("HOLD_UNVERIFIED_ORIGINAL_PAST_RACE_CLASS")
        enriched=_enrich_last4(source,tiers)
        model=classify_horse(enriched,"芝",TARGET_DISTANCE,TARGET_CLASS_RANK,tiers)
        flags=uncertainty_flags(
            enriched,"芝",TARGET_DISTANCE,TARGET_CLASS_RANK,
            TARGET_DAY,tiers,"京都",
        )
        marketless=bool(model["C1"] or model["U"] or model["rescue"])
        result.append({
            "entry_order_for_source_reference_only_NOT_horse_number":
                source["entry_order_not_draw_number"],
            "official_horse_number":None,
            "horse_name":source["name"],
            "jockey_JRA":source["current_jockey"],
            "2026_JRA_pre_rating_NOT_a_model_input":source["pre_rating_JRA"],
            "past_starts_verified_JRA":source["career_starts_before_target"],
            "C1":model["C1"],"U":model["U"],"Q1":model["Q1"],
            "K1":model["K1"],"rescue":model["rescue"],
            "K_prior_kyoto_band_wins":model["K_wins"],
            "K_prior_kyoto_band_top3":model["K_top3"],
            "nonmarket_C1_or_U_or_rescue":marketless,
            "source_chosen_channel_names":[
                key for key in ("C1","U","rescue") if model[key]
            ],
            "uncertainty_flags":flags,
            "quality_race_names_not_verified":model["unknown_quality_tiers"],
            "market_M":None,
            "full_union":None,
            "does_NOT_estimate_win_or_top3_probability":True,
        })
    result.sort(key=lambda z:z[
        "entry_order_for_source_reference_only_NOT_horse_number"
    ])
    count=Counter()
    for h in result:
        for k in ("C1","U","Q1","K1","rescue","nonmarket_C1_or_U_or_rescue"):
            count[k]+=bool(h[k])
    return {
        "status":"OFFICIAL_JRA_17_HORSE_PRE_DRAW_PRICE_FREE_V31_CHANNEL_AUDIT",
        "race":"2026-10-18 Kyoto 11R Shuka Sho GI 3yo turf 2000m",
        "JRA_official_card_source":inputs["source_card_url"],
        "original_v31_classifier_git_blob_SHA":original_sha,
        "original_v31_thresholds_changed":False,
        "official_profile_history_complete_for_ALL_17":True,
        "real_confirmed_horse_numbers_captured":False,
        "real_timestamped_pre_race_win_odds_captured":False,
        "market_M_channel_completed":False,
        "official_v31_market_plus_historical_full_union_completed":False,
        "formal_v31_pre_result_15_to_25_minutes_freeze":False,
        "named_class_metadata_completed_from_public_JRA_sources":True,
        "qualified_JRA_race_tier_metadata_newly_completed":
            inputs["new_quality_tier_metadata"],
        "horse_count":EXPECTED_HORSES,
        "nonmarket_C1_or_U_or_rescue_names":[
            h["horse_name"] for h in result if h["nonmarket_C1_or_U_or_rescue"]
        ],
        "counts_by_channel":dict(count),
        "horse_records":result,
        "important_betting_prediction_limitation":
            "Broad C1/U/Q1/K1 candidate selection, not probabilities, EV or a calibrated finishing order. M/top-quarter win odds cannot be computed before official market snapshot.",
        "avoid_treating_entry_order_as_betting_numbers":True,
        "data_use":"Hypothesis-free descriptive run of existing locked rules on JRA official data; NOT a v3.1 prospective holdout freeze."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE_FILE)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    d=json.loads(args.source.read_text(encoding="utf-8"))
    frozen=json.loads(MANIFEST.read_text(encoding="utf-8"))
    result=audit(d,manifest=frozen,actual_classifier_blob_sha=blob_sha(CLASSIFIER))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "official_17":result["horse_count"],
        "counts_by_channel":result["counts_by_channel"],
        "nonmarket_names":result["nonmarket_C1_or_U_or_rescue_names"],
        "full_v31_without_timestamped_M_is_HOLD":not result[
            "official_v31_market_plus_historical_full_union_completed"],
        "no_horse_numbers_invented":result[
            "avoid_treating_entry_order_as_betting_numbers"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
