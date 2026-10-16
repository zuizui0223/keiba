#!/usr/bin/env python3
"""H2 falsification/design stress tests using explicitly FABRICATED race histories.

Tests 3 distinct mechanisms:
  null: no true style×opponent effect;
  planted: a known nonzero style×opponent effect;
  confounded_null: no true opponent effect but nonrandom race entry plus
                   horse-style×ground interactions.
The nominal CI-excludes-zero indicator is an *algorithm stress metric*, not
a valid scientific significance/power/FPR claim. No wagers or live data.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np

from ecology_demo_competitors import fabricate_competition
from ecology_h2_within_between import run
from ecology_panel import REQUIRED

SCENARIOS = {
    "null_random_entry": {
        "interaction": 0.0, "assortment": 0.0, "going_style_effect": 0.0,
    },
    "planted_opponent_interaction": {
        "interaction": -0.9, "assortment": 0.0, "going_style_effect": 0.0,
    },
    "confounded_null": {
        "interaction": 0.0, "assortment": 0.65, "going_style_effect": 0.7,
    },
}

def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=list(REQUIRED)+["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)


def run_stress(seeds=(512,911), n_days=65, n_horses=36, runners=12) -> dict:
    if len(set(seeds)) != len(seeds) or not seeds:
        raise ValueError("seeds must be nonempty and distinct")
    if n_days < 30 or n_horses < 2*runners:
        raise ValueError("inadequate fabricated longitudinal design")
    all_trials=[]
    for scenario, parameters in SCENARIOS.items():
        for seed in seeds:
            records=fabricate_competition(
                n_days=n_days,n_horses=n_horses,runners=runners,
                seed=seed,**parameters
            )
            with tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/"fictional-stress.csv"
                _write(path,records)
                snapshot_hash=hashlib.sha256(path.read_bytes()).hexdigest()
                try:
                    result=run(path,surface="turf",permit_synthetic_demo=True)
                except ValueError as exc:
                    # Identifiability failure is not a negative biological
                    # result. Continue, with an explicit HOLD per scenario.
                    all_trials.append({
                        "scenario":scenario,"seed":int(seed),
                        "data_sha256":snapshot_hash,"status":"HOLD_MODEL_OR_DESIGN",
                        "hold_reason":str(exc),
                    })
                    continue
            entry={
                "scenario":scenario,"seed":int(seed),
                "true_generator_parameters":parameters,
                "data_sha256":snapshot_hash,
                "status":"SYNTHETIC_SOFTWARE_STRESS_ONLY",
                "sample_size":result["data_support"],
                "definitions":{},
            }
            for definition, variant in result["context_definitions"].items():
                model=variant["interaction"]
                beta=model["interaction_beta_descriptive"]
                lo,hi=model["two_way_cluster_nominal_95pct_interval"]
                gain=variant["forward_test"]["m0_minus_m1_rmse_positive_means_m1_better"]
                entry["definitions"][definition]={
                    "interaction_beta":beta,
                    "descriptive_nominal_interval":[lo,hi],
                    "nominal_interval_excludes_zero":bool(lo>0 or hi<0),
                    "forward_rmse_gain":gain,
                }
            all_trials.append(entry)
    summary={}
    for scenario in SCENARIOS:
        selected=[t for t in all_trials if t["scenario"]==scenario]
        valid=[t for t in selected if t["status"]=="SYNTHETIC_SOFTWARE_STRESS_ONLY"]
        summary[scenario]={
            "runs":len(selected), "model_completed":len(valid),
            "hold_count":len(selected)-len(valid),
            "nominal_exclusion_counts_by_definition":{
                key:sum(t["definitions"][key]["nominal_interval_excludes_zero"] for t in valid)
                for key in ("leave_one_out_other_horses","full_race_field")
            },
            "mean_rmse_gain_by_definition":{
                key:(float(np.mean([
                    t["definitions"][key]["forward_rmse_gain"] for t in valid
                ])) if valid else None)
                for key in ("leave_one_out_other_horses","full_race_field")
            },
        }
    return {
        "status":"SYNTHETIC_DESIGN_STRESS_ONLY",
        "scenarios":SCENARIOS,
        "seeds":list(seeds),
        "panel_generator":{"days":n_days,"horses":n_horses,"runners_per_race":runners},
        "summary":summary,
        "runs":all_trials,
        "interpretation":(
            "Software sensitivity check only. With so few simulations these "
            "frequencies are not calibrated power/type-I error or valid "
            "biological tests; the embedded effect is measured on a DIFFERENT "
            "scale than the race-relative fitted coefficient."
        ),
        "never_conclude":[
            "natural selection, social plasticity or competition established",
            "a zero synthetic ground truth implies any single fitted coefficient must equal zero",
            "apparent significance in a confounded null establishes a real causal effect",
            "licensed historical data access or actual horse performance estimates",
        ],
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seeds",type=int,nargs="+",default=[512,911])
    p.add_argument("--days",type=int,default=65)
    p.add_argument("--horses",type=int,default=36)
    p.add_argument("--runners",type=int,default=12)
    args=p.parse_args()
    report=run_stress(tuple(args.seeds),args.days,args.horses,args.runners)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"summary":report["summary"]},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
