#!/usr/bin/env python3
"""H2 selection stress: simulated nonfinishing is not a zero-speed outcome.

All entrant data are wholly fabricated. Compare a complete fictitious
horse×race panel against another in which some race starters fail to
finish. In the selective scenario the algorithm uses otherwise hidden
post-race speed to delete outcomes: an intentional MNAR sensitivity test,
NOT an acceptable feature for prediction or real-data missingness correction.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import random

from ecology_demo_competitors import fabricate_competition
from ecology_h2_absolute_speed import run
from ecology_panel import REQUIRED


def inject_nonfinishing(rows: list[dict], scheme: str, seed: int=17) -> list[dict]:
    if scheme not in {"none","random","speed_dependent"}:
        raise ValueError("unknown outcome-loss scheme")
    result=[dict(row) for row in rows]
    if scheme == "none":
        return result
    rng=random.Random(seed)
    by_race={}
    for row in result:
        by_race.setdefault(row["race_id"],[]).append(row)
    for race_id,group in sorted(by_race.items()):
        day_index=int(race_id.rsplit("R",1)[-1])
        # Preserve early historical feature support; introduce attrition
        # only from later race dates and in every third selected race.
        if day_index<22 or day_index%3!=0:
            continue
        if scheme=="random":
            chosen=rng.choice(group)
        else:
            # Only poor ground, then drop the *slowest* of early-call horses.
            # The generator knows true finish speed before censoring; real
            # observed datasets cannot reconstruct this counterfactual.
            if group[0]["track_going"]=="良":
                continue
            front=sorted(group,key=lambda r:int(r["first_call_position"]))
            chosen=max(front[:max(3,len(group)//2)],
                       key=lambda r:float(r["finish_time_s"]))
        chosen["finish_status"]="did_not_finish"
        chosen["finishing_position"]=""
        chosen["finish_time_s"]=""
    return result


def _write(path: Path, rows:list[dict]) -> None:
    with path.open("w",newline="",encoding="utf-8") as fd:
        writer=csv.DictWriter(fd,fieldnames=list(REQUIRED)+["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)


def compare(seed=512,n_days=65,n_horses=36,runners=12)->dict:
    complete=fabricate_competition(n_days=n_days,n_horses=n_horses,
                                   runners=runners,seed=seed,interaction=-0.9)
    results={}
    for scheme in ("none","random","speed_dependent"):
        manipulated=inject_nonfinishing(complete,scheme=scheme,seed=seed+31)
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"fictional-horse-starts.csv"
            _write(file,manipulated)
            checksum=hashlib.sha256(file.read_bytes()).hexdigest()
            # Fail hard on errors: CI must expose rather than conceal
            # failures in the selection/sensitivity machinery.
            model=run(file,permit_synthetic_demo=True)
        selection=model["outcome_selection_audit"]
        results[scheme]={
            "status":"FABRICATED_SELECTION_SENSITIVITY_ONLY",
            "input_sha256":checksum,
            "nonfinisher_count":int(sum(
                r["finish_status"]=="did_not_finish" for r in manipulated)),
            "selection_audit":selection,
            "empirical_missingness_decision":model["empirical_missingness_decision"],
            "interaction_beta_leave_one_out":model["models"]["other_horses_only"]["M1"]["beta_raw_speed_mps_per_style_context_product"],
            "interaction_beta_full_field":model["models"]["whole_field"]["M1"]["beta_raw_speed_mps_per_style_context_product"],
            "future_rmse_gain_mps":model["models"]["other_horses_only"]["future_within_race_speed_mps_test"]["m0_minus_m1_rmse_gain_mps"],
        }
    reference=results["none"]["interaction_beta_leave_one_out"]
    for val in results.values():
        val["difference_from_complete_panel_beta_loo_mps"]=(
            val["interaction_beta_leave_one_out"]-reference)
    return {
        "status":"SYNTHETIC_MISSINGNESS_FALSIFICATION_ONLY",
        "scheme_definition":{
            "none":"all simulated finishers' times observed",
            "random":"one entrant per 3rd late race censored without outcome information",
            "speed_dependent":"one selective earlier-running horse with worse latent speed removed on non-good going",
        },
        "seed":seed,"days":n_days,"horses":n_horses,
        "runners_per_race":runners,"scenarios":results,
        "interpretation":(
            "This exercise illustrates that conditioning on timed finishers "
            "can change a fitted association. Neither baseline nor difference "
            "is an ecological effect, and the original missing times cannot "
            "be recovered from observed data without assumptions."
        ),
        "no_empirical_horse_claims":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=512)
    args=p.parse_args()
    report=compare(seed=args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={
        k:{
            "nonfinishers":v["nonfinisher_count"],
            "selected_timed_fraction":round(
                1-v["selection_audit"]["observed_speed_loss_fraction"],4),
            "beta_shift_from_no_missing":round(
                v["difference_from_complete_panel_beta_loo_mps"],5),
        }
        for k,v in report["scenarios"].items()
    }
    print(json.dumps({"status":report["status"],"summary":summary},ensure_ascii=False))


if __name__=="__main__":
    main()
