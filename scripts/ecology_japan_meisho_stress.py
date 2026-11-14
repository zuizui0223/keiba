#!/usr/bin/env python3
"""Run the Japan name/owner/kin forecaster on THREE ARTIFICIAL mechanisms only.

Values have arbitrary simulation units and are NOT real Japan/Meisho
prediction results, p-values, horse genetics, or betting signals.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
import tempfile

from ecology_pedigree_stress import SCENARIOS, fabricate
from ecology_japan_meisho_forward import analyze

SEEDS=(101,202,303)


def add_artificial_asof(source: Path) -> None:
    with source.open(encoding="utf-8") as fd:
        rows=list(csv.DictReader(fd))
    for row in rows:
        family=int(row["horse_id"].split("-")[2])
        row["horse_name"] = (
            "メイショウ【架空】-" if family%2==0 else "架空ノン冠名-"
        ) + row["horse_id"]
        # Synthetic historic owner groups coincide with synthetic trainer
        # partitions; this allows management-only signals to be discovered.
        row["owner_id"]=row["trainer_id"]
        row["owner_known_on"]="1990-01-01"
    with source.open("w",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run() -> dict:
    result={}
    for scenario in SCENARIOS:
        row_results=[]
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as td:
                obs,ped=fabricate(Path(td),scenario,seed)
                add_artificial_asof(obs)
                score=analyze(obs,ped,min_horses=10)
            if score["status"]!="EXPLORATORY_OUT_OF_TIME_NAME_OWNER_KIN_SCORE_NOT_CAUSAL":
                return {
                    "status":"HOLD_SYNTHETIC_JAPAN_DESIGN_SUPPORT",
                    "scenario":scenario,"no_real_horse_data":True
                }
            row_results.append(score)
        keys=("M_name","M_owner","M_kin","M_owner_plus_kin")
        result[scenario]={
            "n_simulated_seeds":len(row_results),
            "n_outer_horses_each_seed":[
                r["results"]["all"]["unique_horses"] for r in row_results],
            "mean_future_RMSE_gain_vs_M0_in_arbitrary_artificial_seconds":{
                key:mean(r["results"]["all"]["gain_relative_M0"][key]
                         for r in row_results) for key in keys
            },
            "mean_named_meisho_cold_start_RMSE_gain_vs_M0":{
                key:mean(r["results"]["meisho_first_observed"]["gain_relative_M0"][key]
                         for r in row_results) for key in keys
            },
            "no_actual_japan_or_meisho_horse_was_observed":True,
        }
    return {
        "status":"SYNTHETIC_JAPAN_NAME_OWNER_KIN_FALSIFICATION_ONLY",
        "source_license":"synthetic",
        "scenarios":result,
        "real_Japan_prediction_or_relatedness_effect_estimated":False,
        "no_real_horse_data_names_ids_odds_or_stakes":True,
        "not_heritability_or_causal_ownership_effect":True,
        "note":"With observational collinearity among owner, prefix and pedigree, predictive contribution is not inherited causation."
    }


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,required=True)
    opts=ap.parse_args()
    result=run()
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
