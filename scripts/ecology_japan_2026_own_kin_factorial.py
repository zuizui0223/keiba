#!/usr/bin/env python3
"""2026 own-versus-family information freshness: four-way post-hoc factorial.

Same 232 horses / 480 starts / 259 races / 42 dates; same fixed source A/B/C
digests and 2018-21-trained model coefficients as earlier 2026 analyses.
A->B and B->C IDs established solely from pre-2025 historic matches.
Every source-C predictor outcome is from a STRICTLY EARLIER CALENDAR DAY
than its target in 2026, never same-day; no actual publication timestamps.

Factorial:
 SS = 2021-stale own and 2021-stale relatives
 FS = updated own, stale relatives
 SF = stale own, updated relatives
 FF = updated own and updated relatives (existing day-lagged replay)

Critically, peer features include the focal's own-history attenuation factor;
a peer signal moved from one history to another must be rescaled for the
chosen OWN history so that the factorial separation is mathematically correct.

This is a POST-HOC feature diagnostic after 2026 results were inspected,
not a new holdout or a genetic-causal study. Aggregate JSON only; source
race rows, names, IDs, crosswalks and per-horse predictions are transient.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2026_day_rolling import (
    three_source_cohort, fit_sourceA_models, relevant_old_history,
    transient_source_c_history, history_before_day,
    predictions_for_history, ORIGINAL_2026, LOCKED_ROWS, LOCKED_HORSES,
    LOCKED_RACES, LOCKED_DAYS, REFERENCE_MIDPOINT_RMSE,
    _scores, _pooled_ci, make_common_features, extra_features,
    predict_weighted_ridge, RIDGE_ALPHA,
)

KIN_SIGNALS = ("sire_kin_history", "dam_kin_history")
KIN_COUNTS = ("log_sire_relative_count", "log_dam_relative_count")
KIN_FEATURES = KIN_SIGNALS + KIN_COUNTS

# Already inspected source-C day-lagged results from run #44007279933.
FROZEN_2026_DAY_LAGGED = {
    "ordinary": (0.2747824093514717, 0.2764268976888031),
    "strong": (0.27470562307974966, 0.274422587127491),
}
SAMPLES = (480, 232, 259, 42)
SCENARIOS = {
    "SS": ("stale", "stale"),
    "FS": ("fresh", "stale"),
    "SF": ("stale", "fresh"),
    "FF": ("fresh", "fresh"),
}


def mix_own_kin(stale:pd.DataFrame, fresh:pd.DataFrame,
                *, own:str, family:str) -> pd.DataFrame:
    """Choose own-history family and relative-history family independently.

    n_own in kin signals is *the focal's own starts*, not a family property.
    Recover peer part with scale_source^-1 and reapply scale_own:
    peer_new = peer_old * (n_source+5)/(n_own+5).
    """
    if own not in ("stale","fresh") or family not in ("stale","fresh"):
        raise ValueError("HOLD_UNKNOWN_FRESHNESS_FACTOR")
    if list(stale.columns)!=list(fresh.columns) or len(stale)!=len(fresh):
        raise ValueError("HOLD_FACTORIAL_FEATURE_SCHEMA_MISMATCH")
    if not all(v in stale for v in KIN_FEATURES+("log_own_count",)):
        raise ValueError("HOLD_MISSING_KIN_OR_OWN_HISTORY_FEATURES")
    o = stale if own=="stale" else fresh
    kin = stale if family=="stale" else fresh
    out=o.copy()
    n_own=np.expm1(o["log_own_count"].to_numpy(float))
    n_kin=np.expm1(kin["log_own_count"].to_numpy(float))
    if (not np.isfinite(n_own).all() or not np.isfinite(n_kin).all()
            or np.any(n_own < -1e-10) or np.any(n_kin < -1e-10)):
        raise ValueError("HOLD_INVALID_FOCAL_COUNT_FOR_ATTENUATION")
    ratio=(n_kin+5.0)/(n_own+5.0)
    for col in KIN_SIGNALS:
        out[col]=kin[col].to_numpy(float)*ratio
    for col in KIN_COUNTS:
        out[col]=kin[col].to_numpy(float)
    if not np.isfinite(out.to_numpy(float)).all():
        raise ValueError("HOLD_NONFINITE_MIXED_OWN_RELATIVE_FEATURES")
    # Identity controls must preserve exact original underlying features.
    if own==family:
        base=stale if own=="stale" else fresh
        if not np.allclose(out.to_numpy(float),base.to_numpy(float),
                           atol=1e-12,rtol=1e-12):
            raise ValueError("HOLD_IDENTITY_FACTORIAL_FEATURE_PARITY")
    return out


def score_pair(t:pd.DataFrame,pa:np.ndarray,pb:np.ndarray):
    s=_scores(t,pa,pb)
    if len(t)>=100 and t.horse.nunique()>=30:
        s["oneway_cluster_399"]=_pooled_ci(t,pa,pb,B=399)
    return s


def analyze(a:Path,b:Path,cpath:Path):
    private,quality=three_source_cohort(a,b,cpath,private_research_context=True)
    if private is None:
        return {"status":"HOLD_ORIGINAL_TRIPLE_SOURCE_COHORT","old_gate":quality}
    raw,old,f,bridge,c=private
    f=f.reset_index(drop=True)
    observed_sample=(len(f),int(f.horse.nunique()),
                     int(f.race.nunique()),int(f.day.nunique()))
    if observed_sample!=SAMPLES or len(bridge)!=1945:
        raise ValueError("HOLD_ORIGINAL_2026_HORSE_COHORT_OR_ID_BRIDGE_DRIFT")
    models,meta=fit_sourceA_models(old,raw)
    original=predictions_for_history(old,f,models,meta)
    for kind,(no,yes) in original.items():
        expected_no,expected_yes=ORIGINAL_2026[kind]
        if (abs(_scores(f,no,yes)["RMSE_portable_no_kin"]-expected_no)>1e-8
                or abs(_scores(f,no,yes)["RMSE_portable_kin"]-expected_yes)>1e-8):
            raise ValueError("HOLD_ORIGINAL_STALE_2026_MODEL_PARITY_"+kind)

    relevant,reduction_qa=relevant_old_history(old,f)
    reduced=predictions_for_history(relevant,f,models,meta)
    for kind in models:
        for p,z in zip(original[kind],reduced[kind]):
            if not np.allclose(p,z,atol=1e-10,rtol=1e-10):
                raise ValueError("HOLD_STALE_RELATIVE_REDUCTION_PARITY_"+kind)

    recent,history_qa=transient_source_c_history(c,bridge,old)
    recent=recent[recent.day.lt(pd.Timestamp("2026-05-18"))].reset_index(drop=True)
    if not set(recent.horse.astype(str)).issubset(set(bridge.values())):
        raise ValueError("HOLD_UNVERIFIED_RECENT_FAMILY_ID")
    focals=set(f.horse.astype(str))
    sire_ids=set(f.sire_id.astype(str))-{""}
    dam_ids=set(f.dam_id.astype(str))-{""}
    recent=recent[
        recent.horse.isin(focals) | recent.sire_id.isin(sire_ids) |
        recent.dam_id.isin(dam_ids)
    ].reset_index(drop=True)
    if recent.empty:
        raise ValueError("HOLD_NO_FOCAL_OR_RELATIVE_RECENT_HISTORY")

    pred={
        kind:{m:{
            "no_kin":np.full(len(f),np.nan),
            "with_kin":np.full(len(f),np.nan),
        } for m in SCENARIOS}
        for kind in models
    }
    coverage={
        "target_rows_with_prior_C_own":0,
        "target_rows_with_prior_C_other_relatives":0,
        "target_rows_with_both_sources":0,
        "target_rows_without_prior_C":0,
        "sourceC_own_prior_rows_used_sum_across_target_dates":0,
        "sourceC_relatives_prior_rows_used_sum_across_target_dates":0,
    }
    fresh_days=[]
    for day in sorted(f.day.unique()):
        ix=np.flatnonzero(f.day.eq(day).to_numpy())
        t=f.iloc[ix]
        h=history_before_day(relevant,recent,day,mode="prior_day")
        if h.day.max()>=pd.Timestamp(day):
            raise ValueError("HOLD_SAME_DAY_OR_FUTURE_RESULTS_IN_FACTORIAL")
        stale=make_common_features(relevant,t)
        current=make_common_features(h,t)
        extra_stale,_=extra_features(relevant,t,meta)
        extra_current,_=extra_features(h,t,meta)
        features={
            "ordinary":(stale,current),
            "strong":(
                pd.concat([stale.reset_index(drop=True),extra_stale],axis=1),
                pd.concat([current.reset_index(drop=True),extra_current],axis=1),
            )
        }
        for kind,(a_old,a_new) in features.items():
            model_no,model_kin=models[kind]
            for mode,(own,family) in SCENARIOS.items():
                x=mix_own_kin(a_old,a_new,own=own,family=family)
                p0=predict_weighted_ridge(model_no,x)
                p1=predict_weighted_ridge(model_kin,x)
                pred[kind][mode]["no_kin"][ix]=p0
                pred[kind][mode]["with_kin"][ix]=p1

        past_c=recent[recent.day.lt(pd.Timestamp(day))]
        own_count=past_c[past_c.horse.isin(set(t.horse.astype(str)))]
        focus_parents=t[["horse","sire_id","dam_id"]].astype(str)
        for horse,sire,dam in focus_parents.itertuples(index=False,name=None):
            h_own=past_c.horse.eq(horse)
            h_relative=past_c.horse.ne(horse) & (
                (past_c.sire_id.eq(sire) if sire else False) |
                (past_c.dam_id.eq(dam) if dam else False)
            )
            own=bool(h_own.any())
            related=bool(h_relative.any())
            coverage["target_rows_with_prior_C_own"]+=int(own)
            coverage["target_rows_with_prior_C_other_relatives"]+=int(related)
            coverage["target_rows_with_both_sources"]+=int(own and related)
            coverage["target_rows_without_prior_C"]+=int(not own and not related)
            coverage["sourceC_own_prior_rows_used_sum_across_target_dates"]+=int(h_own.sum())
            coverage["sourceC_relatives_prior_rows_used_sum_across_target_dates"]+=int(h_relative.sum())
        fresh_days.append(str(pd.Timestamp(day).date()))

    result={}
    for kind,modes in pred.items():
        result[kind]={}
        for mode,z in modes.items():
            p0,p1=z["no_kin"],z["with_kin"]
            if not np.isfinite(p0).all() or not np.isfinite(p1).all():
                raise ValueError("HOLD_NONFINITE_OR_MISSING_FACTORIAL_PREDICTION")
            result[kind][mode]=score_pair(f,p0,p1)
        # Important invariant: no-family prediction ignores family choice.
        if not np.allclose(modes["SS"]["no_kin"],modes["SF"]["no_kin"],
                           atol=1e-12,rtol=1e-12):
            raise ValueError("HOLD_KIN_FEATURE_LEAKED_TO_NO_FAMILY_STALE")
        if not np.allclose(modes["FS"]["no_kin"],modes["FF"]["no_kin"],
                           atol=1e-12,rtol=1e-12):
            raise ValueError("HOLD_KIN_FEATURE_LEAKED_TO_NO_FAMILY_FRESH")
        locked_stale=ORIGINAL_2026[kind]
        locked_fresh=FROZEN_2026_DAY_LAGGED[kind]
        for mode,pair in (("SS",locked_stale),("FF",locked_fresh)):
            s=result[kind][mode]
            if (abs(s["RMSE_portable_no_kin"]-pair[0])>1e-8 or
                    abs(s["RMSE_portable_kin"]-pair[1])>1e-8 or
                    abs(s["RMSE_unchanged_midpoint"]-REFERENCE_MIDPOINT_RMSE)>1e-8):
                raise ValueError("HOLD_ORIGINAL_SCORE_PARITY_"+kind+"_"+mode)
        p_ss=modes["SS"]["with_kin"]
        p_fs=modes["FS"]["with_kin"]
        p_sf=modes["SF"]["with_kin"]
        p_ff=modes["FF"]["with_kin"]
        contrasts={
            "refresh_own_given_stale_family":
                score_pair(f,p_ss,p_fs),
            "refresh_family_given_stale_own":
                score_pair(f,p_ss,p_sf),
            "refresh_family_given_fresh_own":
                score_pair(f,p_fs,p_ff),
            "refresh_own_given_fresh_family":
                score_pair(f,p_sf,p_ff),
        }
        R={m:result[kind][m]["RMSE_portable_kin"] for m in SCENARIOS}
        result[kind]["factorial_contrasts"]={
            k:{ "RMSE_improvement":v["M0_minus_kin_gain"],
                "horse_cluster_CI95":
                  v.get("oneway_cluster_399",{}).get("horse",{}).get(
                       "CI95_M0_minus_kin_gain"),
                "race_day_cluster_CI95":
                  v.get("oneway_cluster_399",{}).get("race_day",{}).get(
                       "CI95_M0_minus_kin_gain"),
                } for k,v in contrasts.items()
        }
        result[kind]["factorial_contrasts"]["descriptive_RMSE_interaction"]={
            "difference_of_improvements":float(R["SS"]-R["FS"]-R["SF"]+R["FF"]),
            "CAUTION":"Nonlinear RMSE interaction, not a causal estimand"
        }

    return {
        "status":"POSTHOC_2026_OWN_VS_KIN_HISTORY_FRESHNESS_FACTORIAL_NOT_CAUSAL",
        "original_source_SHA256":{
            "A":"c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f",
            "B":"7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9",
            "C":"ca14ff253018433e8e14bc583628f85ca909195d5e4edb42c6d1e2ade939ba6f",
        },
        "source_cohort":quality,
        "model_2018_2021_sourceA_training_only":True,
        "model_ridge_alpha":RIDGE_ALPHA,
        "same_2026_focals_and_dates":observed_sample,
        "pre2025_two_event_B_to_C_horses":len(bridge),
        "sourceA_family_feature_reduction_parity":reduction_qa,
        "historic_C_qa":history_qa,
        "identity_and_source_rights_unverified":True,
        "factorial_codes":SCENARIOS,
        "family_peer_signals_rescaled_for_own_count":True,
        "all_original_and_updated_score_parity_1e8_passed":True,
        "sourceC_new_history_coverage":coverage,
        "mode_results":result,
        "scientific_status":{
            "posthoc_after_2026_results_inspected":True,
            "not_independent_new_holdout":True,
            "no_same_day_or_later_result_used":True,
            "sourceC_publication_timestamps_not_certified":True,
            "recorded_parents_not_additive_genetic_causality":True,
            "2027_official_registered_ID_panel_not_obtained":True,
            "no_raw_IDs_names_race_rows_or_individual_forecasts_exported":True,
        },
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--sqlite",type=Path,required=True)
    p.add_argument("--jra-csv",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    j=analyze(args.archive,args.sqlite,args.jra_csv)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
       "status":j["status"],
       "same_2026_focals_and_dates":j["same_2026_focals_and_dates"],
       "sourceC_new_history_coverage":j["sourceC_new_history_coverage"],
       "by_model":{
           kind:{
                mode:{"rmse_own":val["RMSE_portable_no_kin"],
                      "rmse_kin":val["RMSE_portable_kin"],
                      "family_increment":val["M0_minus_kin_gain"]}
                for mode,val in results.items()
                if mode in SCENARIOS
           } for kind,results in j["mode_results"].items()
       },
       "factorial_contrasts":{
           k:v["factorial_contrasts"]
           for k,v in j["mode_results"].items()
       }
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
