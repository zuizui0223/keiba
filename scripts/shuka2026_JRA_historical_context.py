#!/usr/bin/env python3
"""Historical JRA Shuka Sho context stress, explicitly OUTSIDE locked v3.1.

Reads original JRA 2026 pre-race card (17 named horses and previous
race 4th-corner position) alongside JRA's published 2016-2025
retrospective summary. Does NOT update source v3.1 C1/U/Q1/K1/M,
rank horses, compute a calibrated probability, or forecast a win.
The retrospective trends are confounded, small and not causal.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from shuka2026_market_overlay import HERE,source_base

CONTEXT_PATH=HERE/"data/2026-10-18/shuka-jra-2026-context-last4c-history.json"
HISTORICAL_WINS={"oaks_direct":7,"shion_stakes":3,"rose_stakes":0}


def context_stress(data:dict)->dict:
    original=source_base()
    if (data.get("schema")!="SHUKA2026_JRA_OFFICIAL_CONTEXT_STRESS_SOURCE_V1"
        or data.get("status")!="OFFICIAL_JRA_HISTORICAL_CONTEXT_ONLY_NOT_FROZEN_V31_FEATURES"
        or data.get("JRA_previous_race_winner_counts_10years")!=HISTORICAL_WINS):
        raise ValueError("HOLD_NOT_JRA_2026_GI_SOURCE_HISTORICAL_CONTEXT")
    corners=data.get("JRA_previous_race_finish_4c_kyoto_8editions",{})
    early=corners.get("last_race_corner_at_most_4",{})
    later=corners.get("last_race_corner_at_least_5",{})
    if (early!={"first":0,"second":3,"third":2,"outside_top3":50}
        or later!={"first":8,"second":5,"third":6,"outside_top3":65}):
        raise ValueError("HOLD_UNFROZEN_OR_UNVERIFIED_JRA_HISTORICAL_4C_STATISTICS")
    rows=data.get("official_17_recent_past_races",[])
    actual=original["horse_records"]
    official={r["official_horse_number"]:r["horse_name"] for r in actual}
    if (len(rows)!=17 or len(official)!=17
        or sorted(row.get("official_number") for row in rows)!=list(range(1,18))):
        raise ValueError("HOLD_NOT_EXACT_OFFICIAL_SEVENTEEN_CONTEXT_ROWS")
    result=[]
    for r in rows:
        num=r["official_number"]
        if r["name"]!=official[num]:
            raise ValueError("HOLD_CONTEXT_LAST_RACE_NAMES_DIFFER_FROM_OFFICIAL_JRA_DRAW")
        finish=r["last_race_finish"]
        fourth=r["last_race_fourth_corner_position"]
        race=r["last_race_name"]
        if (not isinstance(finish,int) or finish<1
            or not isinstance(fourth,int) or fourth<1 or fourth>18):
            raise ValueError("HOLD_INVALID_LAST_RUN_JRA_SOURCE_POSITION_OR_FINISH")
        prep=("SHION" if race=="紫苑S"
              else "ROSE" if race=="ローズS"
              else "OAKS_DIRECT" if race=="優駿牝馬"
              else "OTHER")
        if prep=="SHION" and finish<=3 and fourth>=5:
            label="HISTORICALLY_COMPARABLE_SHION_PLUS_MIDFIELD"
        elif prep=="SHION" and finish<=3:
            label="SHION_TOP3_BUT_PREVIOUS_RACE_FRONT4"
        elif prep=="ROSE" and fourth<=4:
            label="ROSE_PRIOR_PATH_AND_PREVIOUS_RACE_FRONT4_STRESS"
        elif prep=="ROSE":
            label="ROSE_PRIOR_PATH_HISTORIC_ZERO_WINNERS"
        else:
            label="DIFFERENT_PREP_OR_LESS_DIRECT_HISTORICAL_REFERENCE"
        result.append({
            "JRA_official_horse_number":num,
            "JRA_name":r["name"],
            "latest_prior_race":race,
            "latest_prior_race_finish":finish,
            "latest_prior_race_fourth_corner":fourth,
            "previous_race_group":prep,
            "descriptive_context_label_NOT_a_win_probability":label,
            "nonmarket_v31_C1_U_or_rescue":num in {
                int(x) for x in original[
                    "official_nonmarket_v31_candidate_numbers_NOT_RANKING"]
            },
        })
    labels={
        "HISTORICALLY_COMPARABLE_SHION_PLUS_MIDFIELD",
        "SHION_TOP3_BUT_PREVIOUS_RACE_FRONT4",
        "ROSE_PRIOR_PATH_AND_PREVIOUS_RACE_FRONT4_STRESS",
        "ROSE_PRIOR_PATH_HISTORIC_ZERO_WINNERS",
        "DIFFERENT_PREP_OR_LESS_DIRECT_HISTORICAL_REFERENCE",
    }
    if any(row["descriptive_context_label_NOT_a_win_probability"] not in labels
           for row in result):
        raise ValueError("HOLD_UNKNOWN_JRA_HISTORICAL_CONTEXT_LABEL")
    return {
        "status":"RETROSPECTIVE_JRA_DESCRIPTIVE_CONTEXT_SHADOW_ONLY",
        "official_JRA_17_source":data["original_card_source"],
        "official_JRA_2026_GI_historical_ten_year_source":data["historic_trend_source"],
        "past_10_years_winner_counts_not_target_probabilities":HISTORICAL_WINS,
        "past_Kyoto_8_editions_previous_fourth_corner_position_by_finish":{
            "front_four":early,"fifth_or_later":later,
        },
        "official_seventeen_horse_count":17,
        "official_JRA_source_date_prior_to_2026_10_18":True,
        "original_frozen_v31_model_code_or_thresholds_NOT_modified":True,
        "original_v31_hist_nonmarket_candidate_numbers":
            original["official_nonmarket_v31_candidate_numbers_NOT_RANKING"],
        "not_added_to_model_rank_win_probabilities_or_M_market":True,
        "historical_zero_winners_DOES_NOT_imply_impossible_event":True,
        "historical_race_differences_not_a_randomized_effect":True,
        "source_historical_8_Kyoto_editions_not_national_independent_future_validation":True,
        "horse_history_context_rows":result,
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=CONTEXT_PATH)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    val=context_stress(json.loads(args.source.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(val,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    selected={
        r["JRA_official_horse_number"]:r["descriptive_context_label_NOT_a_win_probability"]
        for r in val["horse_history_context_rows"]
        if r["JRA_official_horse_number"] in (3,8,13,14)
    }
    print(json.dumps({
        "status":val["status"],
        "selected_source_contexts":selected,
        "frozen_v31_six_unaltered":
            val["original_v31_hist_nonmarket_candidate_numbers"],
        "outcome_not_win_probability_or_betting_ev":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
