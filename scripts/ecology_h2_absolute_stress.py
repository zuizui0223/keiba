#!/usr/bin/env python3
"""Fictional-data stress check for ABSOLUTE-speed horse+race H2 model.

Like the relative-z stress suite, this simulates null, planted, and
confounded-null rival effects. Negative-control failure is a WARNING and
never biological evidence or calibrated type-I error.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np

from ecology_demo_competitors import fabricate_competition
from ecology_h2_falsification import SCENARIOS
from ecology_h2_absolute_speed import run
from ecology_panel import REQUIRED


def stress(seeds=(512,911), days=65,horses=36,runners=12):
    if not seeds or len(seeds)!=len(set(seeds)):
        raise ValueError("distinct seeds required")
    results=[]
    for mechanism,arguments in SCENARIOS.items():
        for seed in seeds:
            artificial=fabricate_competition(
                n_days=days,n_horses=horses,runners=runners,seed=seed,**arguments
            )
            with tempfile.TemporaryDirectory() as tmp:
                source=Path(tmp)/"fake.csv"
                with source.open("w",encoding="utf-8",newline="") as fd:
                    writer=csv.DictWriter(fd,fieldnames=list(REQUIRED)+["first_call_position"])
                    writer.writeheader()
                    writer.writerows(artificial)
                checksum=hashlib.sha256(source.read_bytes()).hexdigest()
                try:
                    output=run(source,permit_synthetic_demo=True)
                except ValueError as e:
                    results.append({
                        "scenario":mechanism,"seed":int(seed),
                        "status":"HOLD_DESIGN_OR_COVARIANCE",
                        "reason":str(e),"input_sha256":checksum
                    })
                    continue
            item={
                "scenario":mechanism,"seed":int(seed),
                "status":"SYNTHETIC_ABSOLUTE_MODEL_STRESS_ONLY",
                "input_sha256":checksum,
                "true_generator_parameters":arguments,
                "models":{},
            }
            for key,variant in output["models"].items():
                m=variant["M1"]
                lo,hi=m["two_way_cluster_nominal_interval"]
                item["models"][key]={
                    "raw_speed_interaction_beta_mps":m["beta_raw_speed_mps_per_style_context_product"],
                    "nominal_interval_mps":[lo,hi],
                    "nominal_interval_excludes_zero":bool(lo>0 or hi<0),
                    "future_within_race_rmse_gain_mps":
                        variant["future_within_race_speed_mps_test"]["m0_minus_m1_rmse_gain_mps"],
                }
            results.append(item)
    reports={}
    for scenario in SCENARIOS:
        matches=[v for v in results if v["scenario"]==scenario]
        good=[v for v in matches if v["status"]=="SYNTHETIC_ABSOLUTE_MODEL_STRESS_ONLY"]
        reports[scenario]={
            "tested":len(matches),"fit":len(good),"hold":len(matches)-len(good),
            "loo_nominal_zero_exclusions":sum(
                v["models"]["other_horses_only"]["nominal_interval_excludes_zero"]
                for v in good),
            "full_nominal_zero_exclusions":sum(
                v["models"]["whole_field"]["nominal_interval_excludes_zero"]
                for v in good),
            "mean_loo_rmse_gain_mps":(
                float(np.mean([v["models"]["other_horses_only"]["future_within_race_rmse_gain_mps"]
                               for v in good])) if good else None),
            "mean_full_rmse_gain_mps":(
                float(np.mean([v["models"]["whole_field"]["future_within_race_rmse_gain_mps"]
                               for v in good])) if good else None),
        }
    return {
        "status":"SYNTHETIC_ABSOLUTE_SPEED_STRESS_ONLY",
        "outcome":"individual_raw_speed_mps_with_crossed_horse_race_fixed_intercepts",
        "validation":"heldout_within_race_speed_contrasts_mps",
        "simulated_scenarios":SCENARIOS,"seeds":list(seeds),
        "summary":reports,"trials":results,
        "interpretation":(
            "An engineering/design test on fictitious horses. Nominal intervals "
            "are not causal or calibrated operating characteristics. With two "
            "seeds each, exclusion counts cannot estimate false-positive rates."
        ),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seeds",type=int,nargs="+",default=[512,911])
    args=p.parse_args()
    result=stress(tuple(args.seeds))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"summary":result["summary"]},ensure_ascii=False))


if __name__=="__main__":
    main()
