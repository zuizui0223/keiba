#!/usr/bin/env python3
"""H2 alternative outcome model: individual raw speed with horse AND race FE.

This is an exploratory robustness test, NOT a confirmed ecological result.
Unlike race-relative z-speed, its fitted outcome (m/s) does not divide by the
contemporaneous opponent speed spread. Shared race-day influences are handled
with race fixed intercepts, horse identities with horse fixed intercepts.

Race and horse categories from held-out dates are NOT learned. Temporal
predictive evaluation compares *within-held-out-race speed differences*,
since a new race intercept cannot be known before the event.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ecology_h1_pilot import score, split_dates
from ecology_h2_pilot import competition_frame, horse_context_support
from ecology_h2_within_between import (
    add_total_field_fraction, check_rights, construct_context, _assortment
)
from ecology_panel import load_panel, audit, lagged_features


def frame_with_individual_speed(enriched: list[dict], surface: str) -> pd.DataFrame:
    """Only race-complete records, matched to official individual times."""
    df=competition_frame(enriched, surface)
    speeds=[]
    for r in enriched:
        if r["finish_status"] == "finished" and r["finish_time_s"] is not None:
            speeds.append({
                "race_id":r["race_id"],"horse_id":r["horse_id"],
                "speed_mps":r["course_distance_m"]/r["finish_time_s"],
            })
    if not speeds:
        raise ValueError("HOLD_NO_INDIVIDUAL_SPEEDS")
    speed=pd.DataFrame(speeds)
    result=df.merge(speed,on=["race_id","horse_id"],validate="one_to_one")
    if len(result) != len(df):
        raise ValueError("HOLD_SPEED_MERGE")
    if not np.isfinite(result["speed_mps"]).all():
        raise ValueError("nonfinite individual speed")
    if float(result["speed_mps"].std()) <= 1e-6:
        raise ValueError("HOLD_NO_SPEED_VARIATION")
    return result


def matrix(train: pd.DataFrame, test: pd.DataFrame, interaction: bool):
    """No intercept; full horse dummies and R-1 race dummies.

    Race-level going, field-wide composition, and track shocks are absorbed
    by race FE. We intentionally omit the rival main effect because the
    full-field context is perfectly decomposable into horse/race means.
    """
    # With complete roster, the leave-one-out mean rival ability equals
    # race mean ability minus focal ability/(field_size-1); it is linearly
    # dependent on race FE + own ability when field size is fixed. Drop it.
    numeric=[
        "c_prior_strength_score",
        "c_prior_front_runner_score", "style_x_poor_going",
    ]
    if interaction:
        numeric.append("style_x_context_within")
    horses=sorted(train["horse_id"].unique().tolist())
    races=sorted(train["race_id"].unique().tolist())
    if len(horses)<8 or len(races)<20:
        raise ValueError("HOLD_TOO_FEW_HORSES_OR_RACES")
    horse_map={h:i for i,h in enumerate(horses)}
    # Drop first race dummy to fix intercept redundancy with full horse FE.
    race_map={r:i for i,r in enumerate(races[1:])}
    def build(df):
        n=len(df)
        horse=np.zeros((n,len(horses)),dtype=float)
        race=np.zeros((n,len(races)-1),dtype=float)
        for i,(h,r) in enumerate(zip(df["horse_id"],df["race_id"])):
            if h in horse_map:horse[i,horse_map[h]]=1.
            if r in race_map:race[i,race_map[r]]=1.
        arr=np.column_stack([df[numeric].to_numpy(dtype=float),horse,race])
        if not np.isfinite(arr).all():
            raise ValueError("nonfinite design matrix")
        return arr
    return (
        build(train),build(test),
        numeric+[f"horse:{h}" for h in horses]+
        [f"race:{r}" for r in races[1:]],
        int((~test["horse_id"].isin(horses)).sum()),
        len(races),
    )


def fit(train: pd.DataFrame, test: pd.DataFrame, interaction: bool):
    x0,x1,names,unseen,n_races=matrix(train,test,interaction)
    rank=int(np.linalg.matrix_rank(x0))
    if rank<x0.shape[1]:
        raise ValueError(
            f"HOLD_NONIDENTIFIABLE_CROSSED_FIXED_EFFECTS rank={rank} "
            f"n_columns={x0.shape[1]}"
        )
    # Training outcome is RAW SPEED, not the within-race z transformation.
    ols=sm.OLS(train["speed_mps"].to_numpy(dtype=float),x0).fit()
    # All test race IDs are unseen; a future race-specific intercept has
    # zero dummy coding, and disappears after within-race centering.
    raw_pred=x1@ols.params
    # Use positional alignment, not the original frame indices.
    predicted=pd.DataFrame({
        "race_id":test["race_id"].to_numpy(),
        "prediction":np.asarray(raw_pred,float),
    })
    pred=(predicted["prediction"]-
          predicted.groupby("race_id")["prediction"].transform("mean")).to_numpy()
    out={
        "training_outcome":"raw_individual_speed_m_per_s",
        "train_race_fixed_effects":n_races,
        "train_horse_fixed_effects":len(train["horse_id"].unique()),
        "horse_and_race_effects_both_controlled":True,
        "race_context_main_effect_omitted_as_collinear":True,
        "ground_main_effect_absorbed_by_race_intercepts":True,
        "rival_average_ability_main_effect_absorbed_by_race_FE_plus_own_ability":True,
        "horse_style_x_ground_competing_effect_adjusted":True,
        "unseen_test_horse_starts":unseen,
        "numerical_rank":rank,
        "training_r_squared":float(ols.rsquared),
    }
    if interaction:
        index=names.index("style_x_context_within")
        groups=np.column_stack([
            pd.factorize(train["horse_id"])[0],
            pd.factorize(train["race_id"])[0],
        ])
        robust=ols.get_robustcov_results(cov_type="cluster",groups=groups,use_t=False)
        se=float(robust.bse[index])
        if not np.isfinite(se) or se<=0:
            raise ValueError("HOLD_TWO_WAY_COVARIANCE")
        beta=float(ols.params[index])
        out.update({
            "beta_raw_speed_mps_per_style_context_product":beta,
            "two_way_cluster_nominal_standard_error":se,
            "two_way_cluster_nominal_interval":[beta-1.96*se,beta+1.96*se],
            "interval_is_causal_or_confirmatory":False,
        })
    return out,pred


def run(path:Path,surface="turf",permit_synthetic_demo=False,test_fraction=0.2)->dict:
    rows=load_panel(path)
    synthetic=check_rights(rows,permit_synthetic_demo)
    enriched=lagged_features(rows)
    diag=audit(rows,enriched)
    if not synthetic and diag["status"]!="DESIGN_READY_NOT_EVIDENCE":
        raise ValueError("HOLD_AUDIT:"+diag["status"])
    frame=add_total_field_fraction(frame_with_individual_speed(enriched,surface))
    train0,test0,cutoff=split_dates(frame,test_fraction)
    support=horse_context_support(train0)
    if support<(8 if synthetic else 30):
        raise ValueError("HOLD_TOO_FEW_WITHIN_HORSE_CONTEXTS")
    if train0["race_id"].nunique()<20 or test0["race_id"].nunique()<4:
        raise ValueError("HOLD_TOO_FEW_TEMPORAL_RACES")
    versions={}
    for key,field in (
        ("other_horses_only","other_front_runner_share"),
        ("whole_field","total_front_runner_share"),
    ):
        train,test,meta=construct_context(train0,test0,field)
        if train["context_within"].std()<1e-7:
            raise ValueError("HOLD_NO_RIVAL_CONTEXT_VARIATION")
        base,p0=fit(train,test,False)
        full,p1=fit(train,test,True)
        # Heldout validation is on speed differences within the future race,
        # not on raw speed with a future race intercept oracle.
        test_centered=test.copy()
        test_centered["y"]=(test_centered["speed_mps"]-
                            test_centered.groupby("race_id")["speed_mps"].transform("mean"))
        # Reuse race-block scoring, but record its actual units correctly.
        metrics=score(test_centered,p0,p1,bootstrap=500,seed=20261012)
        # The shared scoring utility is labelled for z-speed. Convert its
        # three metric keys into the physical m/s unit actually passed in.
        for original,physical in (
            ("m0_rmse_race_relative_speed_z","m0_rmse_within_race_mps"),
            ("m1_rmse_race_relative_speed_z","m1_rmse_within_race_mps"),
            ("m0_minus_m1_rmse_positive_means_m1_better",
             "m0_minus_m1_rmse_gain_mps"),
        ):
            metrics[physical]=metrics.pop(original)
        metrics["metric_units"]="m/s within-race speed deviation"
        versions[key]={"preprocessing":meta,"M0":base,"M1":full,
                       "future_within_race_speed_mps_test":metrics}
    return {
        "status":("SYNTHETIC_ABSOLUTE_SPEED_H2_DEMO_ONLY" if synthetic
                  else "EXPLORATORY_ABSOLUTE_SPEED_H2_NO_CAUSAL_CLAIM"),
        "input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_license":"synthetic" if synthetic else "needs independent legal verification",
        "primary_outcome":"individual_speed_mps",
        "relative_outcome_avoided_in_training":True,
        "train_before_test":str(train0["date"].max())<str(cutoff),
        "train_max_date":str(train0["date"].max()),
        "future_first_date":str(cutoff),
        "support_horses_with_repeated_rival_contexts":support,
        "models":versions,
        "limitations":[
            "Crossed horse/race fixed effects prevent treating contemporaneous "
            "race-relative speed z scores as an independent focal phenotype.",
            "Race FE absorb shared day/track effects, but nonrandom entry, "
            "class/jockey and tactical effects can still confound the interaction.",
            "Both social composition measurements are made from strict prior-day "
            "running-style histories; this is NOT randomized partner assignment.",
            "Nominal two-way-clustered uncertainty is descriptive and not "
            "a confidence interval for causal animal social plasticity.",
            "Heldout prediction uses within-race raw SPEED contrasts (m/s); "
            "this differs from the model fit outcome (absolute m/s).",
            "A cohort excluding incomplete or nonfinishing races can "
            "condition on post-treatment performance and bias results.",
            "No actual licensed horse race histories or fitness phenotypes used.",
        ],
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--surface",choices=("turf","dirt"),default="turf")
    p.add_argument("--permit-synthetic-demo",action="store_true")
    p.add_argument("--test-fraction",type=float,default=0.2)
    args=p.parse_args()
    out=run(args.input,args.surface,args.permit_synthetic_demo,args.test_fraction)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "loo_beta_mps":out["models"]["other_horses_only"]["M1"]["beta_raw_speed_mps_per_style_context_product"],
        "full_beta_mps":out["models"]["whole_field"]["M1"]["beta_raw_speed_mps_per_style_context_product"],
        "train_before_test":out["train_before_test"],
    },ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
