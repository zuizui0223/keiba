#!/usr/bin/env python3
"""Attach only VERIFIED official JRA horse numbers to unchanged v3.1 C1/U/Q1/K1 output.

The racecard has been updated AFTER historical pre-draw JRA
profiles were sourced. This only joins the exact 17 distinct
official horse names to 17 official horse numbers. It cannot
calculate M without real dated JRA win odds and does not
create a prospective v3.1 formal holdout freeze.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from shuka2026_official_rule_audit import (
    audit,blob_sha,SOURCE_FILE,MANIFEST,CLASSIFIER,HERE
)

DRAW_FILE=HERE/"data/2026-10-18/shuka-jra-official-17-horse-numbers.json"


def join_draw(audit_result:dict,draw:dict)->dict:
    if (draw.get("schema")!="SHUKA2026_JRA_OFFICIAL_DRAW_17_NAMES_V1"
        or draw.get("actual_timestamped_win_odds_captured") is not False
        or draw.get("rate_or_model_not_retrained") is not True):
        raise ValueError("HOLD_JRA_OFFICIAL_DRAW_OR_MARKET_NOT_VERIFIED")
    base=audit_result["horse_records"]
    official=draw["JRA_official_horse_number_by_name"]
    if (len(base)!=17 or len(official)!=17
        or sorted(int(x["official_horse_number"]) for x in official)!=list(range(1,18))):
        raise ValueError("HOLD_MISSING_OR_DUPLICATED_FINAL_JRA_HORSE_NUMBER")
    lookup={str(z["horse_name"]):int(z["official_horse_number"]) for z in official}
    if len(lookup)!=17 or set(lookup)!={x["horse_name"] for x in base}:
        raise ValueError("HOLD_OFFICIAL_JRA_DRAW_NAMES_DO_NOT_MATCH_PAST_HISTORIES")
    if any(x["official_horse_number"] is not None or x["market_M"] is not None
           or x["full_union"] is not None for x in base):
        raise ValueError("HOLD_BASELINE_RESULT_ALREADY_HAS_FORBIDDEN_ODDS_OR_NUMBERS")
    rows=[]
    for orig in base:
        item=dict(orig)
        item["official_horse_number"]=lookup[orig["horse_name"]]
        item["official_draw_verified_source"]=draw["source_JRA_card_url"]
        rows.append(item)
    rows.sort(key=lambda r:r["official_horse_number"])
    nominated=[r["official_horse_number"] for r in rows
               if r["nonmarket_C1_or_U_or_rescue"]]
    return {
        **{k:v for k,v in audit_result.items() if k!="horse_records"},
        "status":"JRA_OFFICIAL_DRAW_JOINED_TO_LOCKED_V31_NONMARKET_NO_LIVE_ODDS",
        "official_JRA_number_source":draw["source_JRA_card_url"],
        "official_17_horse_numbers_confirmed":True,
        "actual_live_market_M_still_HOLD":True,
        "official_17_horse_number_names_unique":True,
        "official_nonmarket_v31_candidate_numbers_NOT_RANKING":nominated,
        "market_plus_historical_v31_complete_union":None,
        "horse_records":rows,
        "draw_join_not_a_race_probability_or_expected_value":True,
    }


def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--output",type=Path,required=True)
    opts=arg.parse_args()
    inp=json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    frozen=json.loads(MANIFEST.read_text(encoding="utf-8"))
    baseline=audit(inp,manifest=frozen,
                   actual_classifier_blob_sha=blob_sha(CLASSIFIER))
    draw=json.loads(DRAW_FILE.read_text(encoding="utf-8"))
    result=join_draw(baseline,draw)
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "official_horse_numbers_verified":result["official_17_horse_numbers_confirmed"],
        "nonmarket_v31_candidate_numbers":
            result["official_nonmarket_v31_candidate_numbers_NOT_RANKING"],
        "nonmarket_candidates":[
            [r["official_horse_number"],r["horse_name"],
             r["source_chosen_channel_names"]]
            for r in result["horse_records"] if r["nonmarket_C1_or_U_or_rescue"]
        ],
        "v31_full_market_union_computed":not result["actual_live_market_M_still_HOLD"],
        "never_return_fictional_or_predicted_betting_odds":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
