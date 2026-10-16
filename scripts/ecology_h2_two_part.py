#!/usr/bin/env python3
"""Exploratory two-part ecological H2: finish completion + conditional speed.

All actual starters contribute pre-race competitor composition even if they
later fail to finish. Completion is a BIOLOGICAL/ADMINISTRATIVE outcome,
not a missing numeric zero-speed measurement.

Part A: regularized binomial comparison of completion probability with
and without own prior style × rival prior style composition.
Part B: original raw-speed crossed-horse/race analysis conditional on an
observed timed finish (run independently, never imputing DNF speed).

Important: hypothesis is NOT empirically supported. Model is not a causal
effect, nor a welfare or betting recommendation. Real-data source rights
must be separately verified outside this code.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ecology_h1_pilot import split_dates
from ecology_h2_absolute_speed import run as fit_conditional_speed
from ecology_h2_within_between import check_rights
from ecology_panel import audit, lagged_features, load_panel


PREDICTORS = (
    "prior_strength_score", "other_prior_strength_mean",
    "prior_front_runner_score", "other_front_runner_share",
)


def starter_completion_panel(enriched: list[dict], surface="turf") -> tuple[pd.DataFrame,dict]:
    """Eligibility uses PRE-race history and actual start, never finish time.

    Complete entrant roster and full historical profiles are necessary.
    No minimum number of eventual timed finishers applies at this stage.
    """
    grouped=defaultdict(list)
    for r in enriched:
        if r["course_surface"]==surface:
            grouped[r["race_id"]].append(r)
    reasons=Counter()
    rows=[]
    if not grouped:
        raise ValueError("HOLD_NO_RACES_ON_SURFACE")
    for rid,group in grouped.items():
        if len(group)<4 or len(group)!=group[0]["field_size"]:
            reasons["incomplete_start_roster"]+=1
            continue
        if any(r["finish_status"]=="pending" for r in group):
            reasons["not_officially_resolved"]+=1
            continue
        if any(any(r[f] is None for f in PREDICTORS) for r in group):
            reasons["insufficient_pre_race_history"]+=1
            continue
        for r in group:
            finished=(r["finish_status"]=="finished")
            timed=(finished and r["finish_time_s"] is not None)
            rows.append({
                "race_id":rid, "horse_id":r["horse_id"],
                "date":r["race_date_jst"],
                "finished":int(finished),
                "timed_finish":int(timed),
                "poor":int(r["track_going"]!="良"),
                "prior_strength_score":float(r["prior_strength_score"]),
                "other_prior_strength_mean":float(r["other_prior_strength_mean"]),
                "prior_front_runner_score":float(r["prior_front_runner_score"]),
                "other_front_runner_share":float(r["other_front_runner_share"]),
            })
    if not rows:
        raise ValueError("HOLD_NO_HISTORY_COMPLETE_STARTERS")
    df=pd.DataFrame(rows).sort_values(
        ["date","race_id","horse_id"]).reset_index(drop=True)
    if df[["race_id","horse_id"]].duplicated().any():
        raise ValueError("duplicate starter")
    return df,{
        "candidate_races":len(grouped),
        "history_eligible_races":int(df["race_id"].nunique()),
        "all_history_eligible_starts":len(df),
        "full_roster_without_postrace_time_filter":True,
        "excluded_races":dict(reasons),
        "finished_count":int(df["finished"].sum()),
        "did_not_finish_count":int((1-df["finished"]).sum()),
        "finished_but_timing_unavailable":int(
            ((df["finished"]==1)&(df["timed_finish"]==0)).sum()),
        "started_horses_with_missing_full_race_speed":int(
            (df["timed_finish"]==0).sum()),
        "no_zero_speed_imputation":True,
    }


def make_features(train:pd.DataFrame,test:pd.DataFrame,interaction:bool):
    """Use only earlier training-date means/SDs for predictors."""
    centers={p:float(train[p].mean()) for p in PREDICTORS}
    scales={p:float(train[p].std(ddof=0)) for p in PREDICTORS}
    if any(not np.isfinite(v) or v<1e-8 for v in scales.values()):
        raise ValueError("HOLD_NO_PRE_RACE_PREDICTOR_OVERLAP")
    def build(df):
        z={p:(df[p].to_numpy(dtype=float)-centers[p])/scales[p]
           for p in PREDICTORS}
        x=[
            np.ones(len(df)),
            z["prior_strength_score"],z["other_prior_strength_mean"],
            z["prior_front_runner_score"],z["other_front_runner_share"],
            df["poor"].to_numpy(dtype=float),
            z["prior_front_runner_score"]*df["poor"].to_numpy(dtype=float),
        ]
        if interaction:
            x.append(z["prior_front_runner_score"]*
                     z["other_front_runner_share"])
        matrix=np.column_stack(x)
        if not np.isfinite(matrix).all():
            raise ValueError("nonfinite completion predictor")
        return matrix
    return build(train),build(test),{
        "means_frozen_from_training":centers,
        "scales_frozen_from_training":scales,
        "interaction_included":bool(interaction),
        "no_horse_or_race_fixed_intercepts":True,
        "all_explanatory_values_pre_race_historical":True,
    }


def score_completion(truth:np.ndarray, pred:np.ndarray)->dict:
    if len(truth)==0 or len(pred)!=len(truth):
        raise ValueError("empty or mismatched test data")
    p=np.clip(np.asarray(pred,float),1e-6,1-1e-6)
    y=np.asarray(truth,float)
    return {
        "brier":float(np.mean((y-p)**2)),
        "log_loss":float(-np.mean(y*np.log(p)+(1-y)*np.log1p(-p))),
        "mean_predicted_finish_probability":float(p.mean()),
        "observed_finish_fraction":float(y.mean()),
        "test_dnf_count":int((1-y).sum()),
    }


def fit_binomial(train:pd.DataFrame,test:pd.DataFrame,interaction:bool,
                 ridge_penalty=0.004)->dict:
    if ridge_penalty<=0:
        raise ValueError("ridge_penalty must be >0")
    xtrain,xtest,metadata=make_features(train,test,interaction)
    y=train["finished"].to_numpy(dtype=float)
    # All but intercept get a small fixed ridge penalty. This avoids
    # numerical separation in rare-event synthetic demonstrations;
    # it is NOT a validated choice for real DNF prediction.
    alpha=np.full(xtrain.shape[1],ridge_penalty)
    alpha[0]=0.0
    glm=sm.GLM(y,xtrain,family=sm.families.Binomial())
    result=glm.fit_regularized(alpha=alpha,L1_wt=0.0,maxiter=500)
    pred=1/(1+np.exp(-np.clip(xtest@result.params,-30,30)))
    if not np.isfinite(pred).all():
        raise ValueError("nonfinite completion probabilities")
    out={
        "estimation":"ridge-regularized descriptive binomial GLM",
        "regularization_penalty":ridge_penalty,
        "preprocessing":metadata,
        "n_coefficients":len(result.params),
        "training_dnf_count":int((1-y).sum()),
        "training_finish_fraction":float(y.mean()),
        "heldout":score_completion(test["finished"].to_numpy(),pred),
        "fitted_coefficient_is_causal_or_confirmatory":False,
    }
    if interaction:
        out["style_x_rival_context_log_odds_coefficient"]=float(result.params[-1])
    return out


def run(path:Path,surface="turf",permit_synthetic_demo=False,
        test_fraction=0.2)->dict:
    starts=load_panel(path)
    synthetic=check_rights(starts,permit_synthetic_demo)
    enriched=lagged_features(starts)
    readiness=audit(starts,enriched)
    if not synthetic and readiness["status"]!="DESIGN_READY_NOT_EVIDENCE":
        raise ValueError("HOLD_AUDIT: "+readiness["status"])
    entire,counts=starter_completion_panel(enriched,surface)
    train,test,cutoff=split_dates(entire,test_fraction)
    if train["race_id"].nunique()<20 or test["race_id"].nunique()<4:
        raise ValueError("HOLD_INSUFFICIENT_TEMPORAL_RACES")
    events_tr=int((train["finished"]==0).sum())
    events_te=int((test["finished"]==0).sum())
    # Engineering only; sparse outcomes should be reported as HOLD
    # instead of interpreting a regularized coefficient.
    if events_tr<12 or events_te<3:
        raise ValueError(
            f"HOLD_TOO_FEW_COMPLETION_EVENTS: train_DNF={events_tr}, "
            f"test_DNF={events_te}"
        )
    m0=fit_binomial(train,test,False)
    m1=fit_binomial(train,test,True)
    continuous=fit_conditional_speed(
        path,surface,permit_synthetic_demo,test_fraction)
    conditional_audit=continuous["outcome_selection_audit"]
    return {
        "status":("SYNTHETIC_TWO_PART_H2_DEMO_ONLY" if synthetic
                  else "EXPLORATORY_TWO_PART_ASSOCIATION_NOT_BIOLOGICAL_SUPPORT"),
        "input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "dataset_selection_gate":counts,
        "date_split":{
            "train_max_date":str(train["date"].max()),
            "test_start_date":str(cutoff),
            "train_races":int(train["race_id"].nunique()),
            "test_races":int(test["race_id"].nunique()),
            "training_DNF":events_tr,"future_DNF":events_te,
        },
        "part_A_completion":{
            "outcome":"binary FINISHED vs DID_NOT_FINISH among actual starters",
            "baseline":m0,"style_by_rival_competition_interaction":m1,
            "future_log_loss_gain_positive_is_better":(
                m0["heldout"]["log_loss"]-m1["heldout"]["log_loss"]),
            "future_brier_gain_positive_is_better":(
                m0["heldout"]["brier"]-m1["heldout"]["brier"]),
        },
        "part_B_speed_conditional_on_timed_finish":{
            "outcome":"raw individual speed in m/s ONLY for timed finishers",
            "observed_speed_selection":conditional_audit,
            "scientific_selection_hold":continuous["empirical_missingness_decision"],
            "models":continuous["models"],
            "never_impute_a_nonfinisher_full_distance_speed":True,
        },
        "no_causal_or_empirical_claim":True,
        "limitations":[
            "DNF can be injury, tactical noncompletion, accident, or recording error.",
            "The first-stage completion GLM has no crossed horse/race effects.",
            "Ridge strength is an engineering choice; not calibrated for rare-event inference.",
            "Nonrandom race entry, time-varying fitness, jockey decisions and class remain confounded.",
            "The speed stage conditions on timed finishers; the estimand differs from all-starter completion.",
            "An all-starter average speed is not defined for horses that never completed the distance.",
            "Even both simulated stages passing is not a real horse ecology result.",
        ],
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--surface",choices=("turf","dirt"),default="turf")
    p.add_argument("--permit-synthetic-demo",action="store_true")
    args=p.parse_args()
    outcome=run(args.input,args.surface,args.permit_synthetic_demo)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":outcome["status"],
        "training_DNF":outcome["date_split"]["training_DNF"],
        "future_DNF":outcome["date_split"]["future_DNF"],
        "completion_heldout_log_loss_gain":outcome["part_A_completion"]["future_log_loss_gain_positive_is_better"],
        "conditional_speed_selection_hold":outcome["part_B_speed_conditional_on_timed_finish"]["scientific_selection_hold"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
