#!/usr/bin/env python3
"""Post-hoc 2026 stale-vs-day-lagged source-C racing history diagnostic.

A->B->C identity witnesses remain PRE-2025; source-A ridge coefficients are
FROZEN through 2021. Compare exactly the SAME 2026 232 horses / 480 starts:
    1. 2021-stale A only (must match original run 43897234479);
    2. A + available source-C history through 2025-12-31;
    3. A + C outcomes strictly before each 2026 target calendar DAY.
There are no historical race-result publication timestamps in the public
source, so before-day is only a conservative chronology proxy, not a
certified pre-race known-on panel. NO 2026 tuning or new holdout claim.
All names, crosswalks, runner histories and predictions remain transient.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2026_triple_source import (
    three_source_cohort, _scores, _pooled_ci,
    make_common_features, fit_weighted_ridge, predict_weighted_ridge,
    old_metadata, extra_features, FEATURE_NO_KIN, FEATURE_KIN,
    STRONG_NO_KIN, STRONG_KIN, RIDGE_ALPHA,
)

# These are independently fixed in the original successful 2026 source-C run.
ORIGINAL_2026 = {
    "ordinary": (0.319681772293503, 0.32030160640717165),
    "strong": (0.3215185305911288, 0.3180747501712852),
}
LOCKED_ROWS, LOCKED_HORSES, LOCKED_RACES, LOCKED_DAYS = 480, 232, 259, 42
REFERENCE_MIDPOINT_RMSE = 0.31214627917891946


def fit_sourceA_models(old, raw):
    """Reconstruct source-A-only coefficients, without any 2022+ labels."""
    metadata = old_metadata(raw)
    fitted = {}
    for kind, (c0, c1) in {
        "ordinary": (FEATURE_NO_KIN, FEATURE_KIN),
        "strong": (STRONG_NO_KIN, STRONG_KIN),
    }.items():
        parts = []
        labels = []
        horseids = []
        for year in (2018, 2019, 2020, 2021):
            h = old[old.year < year]
            t = old[old.year == year]
            x = make_common_features(h, t)
            if kind == "strong":
                e, _ = extra_features(h, t, metadata)
                x = pd.concat([x.reset_index(drop=True), e], axis=1)
            parts.append(x)
            labels.append(t.y.to_numpy(float))
            horseids.append(t.horse.astype(str).to_numpy())
        X = pd.concat(parts, ignore_index=True)
        y = np.concatenate(labels)
        hors = np.concatenate(horseids)
        fitted[kind] = (
            fit_weighted_ridge(X, y, hors, c0, alpha=RIDGE_ALPHA),
            fit_weighted_ridge(X, y, hors, c1, alpha=RIDGE_ALPHA),
        )
    return fitted, metadata


def only_complete_classified_c(c):
    """Whole C race 1..N rank check before using its previous-day result."""
    good = []
    count = Counter()
    for _, group in c.groupby("race_key", sort=False):
        n = len(group)
        if not (2 <= n <= 30):
            count["excluded_field"] += 1
        elif (group.normalized_name.duplicated().any()
                or group.surf.nunique() != 1
                or group.distance.nunique() != 1
                or group.venue.nunique() != 1):
            count["excluded_duplicate_or_conflict"] += 1
        elif sorted(group["rank"].astype(int).tolist()) != list(range(1, n+1)):
            count["excluded_nonconsecutive_or_tied"] += 1
        else:
            g = group.copy()
            g["_complete_N"] = n
            good.append(g)
            count["source_complete_races"] += 1
    if not good:
        raise ValueError("HOLD_SOURCE_C_NO_COMPLETE_RACES_TO_UPDATE")
    return pd.concat(good, ignore_index=True), dict(count)


def transient_source_c_history(c, bridge, old):
    """Only historically anchored A identities may contribute later histories."""
    verified, quality = only_complete_classified_c(c)
    verified = verified[verified.year.between(2023, 2026)].copy()
    verified["horse"] = verified.normalized_name.map(bridge)
    verified = verified[verified.horse.notna()].copy()
    if verified.empty:
        raise ValueError("HOLD_NO_HISTORICALLY_IDENTIFIED_NEW_SOURCE_HISTORY")
    if verified.duplicated(["race_key", "horse"]).any():
        raise ValueError("HOLD_DUPLICATE_C_SOURCE_HORSE_RACE_HISTORY")
    parent = old[["horse", "sire_id", "dam_id"]].astype(str).drop_duplicates()
    if parent.horse.duplicated().any():
        raise ValueError("HOLD_OLD_PARENT_MAP_CONFLICT")
    p = parent.set_index("horse")
    if not set(verified.horse.astype(str)).issubset(p.index):
        raise ValueError("HOLD_PUBLIC_RACING_NAME_NOT_IN_ORIGINAL_PEDIGREE")
    h = pd.DataFrame({
        "horse": verified.horse.astype(str),
        "day": verified.day,
        "year": verified.year.astype(int),
        "race": verified.race_key.astype(str),
        "distance": verified.distance.astype(int),
        "surface": verified.surf.astype(str),
        "stratum": (verified.surf.astype(str) + ":" +
                    (verified.distance // 400).astype(int).astype(str)),
        "y": ((verified["rank"].astype(float)-1) /
              (verified["_complete_N"].astype(float)-1)),
        "circuit": "JRA",
        "sire_id": verified.horse.map(p.sire_id).astype(str),
        "dam_id": verified.horse.map(p.dam_id).astype(str),
    })
    if h[["sire_id","dam_id"]].isna().any().any():
        raise ValueError("HOLD_C_HISTORY_PARENT_REFERENCE_MISSING")
    if not h.y.between(0,1).all():
        raise ValueError("HOLD_C_HISTORY_RANK_OUT_OF_RANGE")
    return h.sort_values(["day","race","horse"],kind="mergesort").reset_index(drop=True),quality


def relevant_old_history(old, target):
    """Lossless filter for focal and all documented same-sire/dam relatives."""
    tparents = target[["horse","sire_id","dam_id"]].astype(str)
    horses = set(tparents.horse)
    sires = set(tparents.sire_id) - {""}
    dams = set(tparents.dam_id) - {""}
    o = old[
        old.horse.astype(str).isin(horses) |
        old.sire_id.astype(str).isin(sires) |
        old.dam_id.astype(str).isin(dams)
    ].copy()
    x_all = make_common_features(old, target)
    x_reduced = make_common_features(o, target)
    if list(x_all.columns) != list(x_reduced.columns):
        raise ValueError("HOLD_REDUCED_HISTORY_COLUMN_PARITY")
    for col in x_all:
        if not np.allclose(x_all[col], x_reduced[col], atol=1e-10, rtol=1e-10):
            raise ValueError("HOLD_REDUCED_HISTORY_FEATURE_PARITY_" + col)
    return o, {
        "sourceA_rows_original":int(len(old)),
        "sourceA_rows_relevant":int(len(o)),
        "all_original_feature_columns_exactly_reproduced":True
    }


def predictions_for_history(h, target, models, meta):
    """Single cutoff, no same-day results in predictors."""
    if h.day.max() >= target.day.min():
        raise ValueError("HOLD_TARGET_DAY_LABEL_IN_HISTORY")
    common = make_common_features(h, target)
    result = {}
    for kind,(m0,m1) in models.items():
        x=common
        if kind=="strong":
            extra,_ = extra_features(h,target,meta)
            x = pd.concat([x.reset_index(drop=True),extra],axis=1)
        result[kind] = (
            predict_weighted_ridge(m0,x),
            predict_weighted_ridge(m1,x)
        )
    return result


def history_before_day(sourceA, sourceC, day, *, mode):
    """Source C may supply no results from target calendar day or later."""
    day = pd.Timestamp(day)
    if mode == "stale":
        out = sourceA
    elif mode == "through2025":
        x=sourceC[sourceC.day.lt(pd.Timestamp("2026-01-01"))]
        out=pd.concat([sourceA,x],ignore_index=True)
    elif mode == "prior_day":
        x=sourceC[sourceC.day.lt(day)]
        out=pd.concat([sourceA,x],ignore_index=True)
    else:
        raise ValueError("HOLD_UNKNOWN_DAY_LAG_MODE")
    if out.day.max() >= day:
        raise ValueError("HOLD_SAME_DAY_OR_FUTURE_INFO_IN_HISTORY")
    return out


def analyze(a:Path,b:Path,cpath:Path):
    private,quality=three_source_cohort(a,b,cpath,private_research_context=True)
    if private is None:
        return {"status":"HOLD_THREE_SOURCE_IDENTITY_GATE",
                "original_gate":quality}
    raw,old,f,bridge,c=private
    if (len(f)!=LOCKED_ROWS or f.horse.nunique()!=LOCKED_HORSES
            or f.race.nunique()!=LOCKED_RACES or f.day.nunique()!=LOCKED_DAYS
            or len(bridge)!=1945):
        raise ValueError("HOLD_2026_SAMPLE_OR_HISTORIC_BRIDGE_DRIFT")
    f=f.reset_index(drop=True)
    models,meta=fit_sourceA_models(old,raw)
    original = predictions_for_history(old,f,models,meta)
    assert np.isfinite(f.y.to_numpy(float)).all()
    old_scores={}
    for kind,(p0,p1) in original.items():
        sc=_scores(f,p0,p1)
        exp0,exp1=ORIGINAL_2026[kind]
        if (abs(sc["RMSE_portable_no_kin"]-exp0)>1e-8
                or abs(sc["RMSE_portable_kin"]-exp1)>1e-8
                or abs(sc["RMSE_unchanged_midpoint"]-REFERENCE_MIDPOINT_RMSE)>1e-8):
            raise ValueError("HOLD_ORIGINAL_2026_PREDICTION_DRIFT_"+kind)
        old_scores[kind]=sc
    relevant,filter_qa=relevant_old_history(old,f)
    # Check optimized own/covariate history not just ordinary but strong too.
    truncated = predictions_for_history(relevant,f,models,meta)
    for kind in models:
        for y,z in zip(original[kind], truncated[kind]):
            if not np.allclose(y,z,atol=1e-10,rtol=1e-10):
                raise ValueError("HOLD_STRONG_OLD_HISTORY_REDUCTION_PARITY")
    hC,c_qa=transient_source_c_history(c,bridge,old)
    hC=hC[hC.day.lt(pd.Timestamp("2026-05-18"))].reset_index(drop=True)
    if hC.empty:
        raise ValueError("HOLD_NO_SOURCE_C_HISTORIC_RESULTS")
    # Only B->C 2023-24-anchored names may influence family/own features.
    if not set(hC.horse).issubset(set(bridge.values())):
        raise ValueError("HOLD_UNVERIFIED_NAME_AS_RECENT_HORSE")
    target_horses=set(f.horse.astype(str))
    target_parent_s=set(f.sire_id.astype(str))-{""}
    target_parent_d=set(f.dam_id.astype(str))-{""}
    hC = hC[
        hC.horse.isin(target_horses) |
        hC.sire_id.isin(target_parent_s) |
        hC.dam_id.isin(target_parent_d)
    ].reset_index(drop=True)
    if hC.empty:
        raise ValueError("HOLD_NO_TARGET_OR_FAMILY_RECENT_RACES")
    pre2026=hC[hC.day.lt(pd.Timestamp("2026-01-01"))]
    first_2026=f.day.min()
    end_2026=f.day.max()
    prediction={}
    for mode in ("through2025","prior_day"):
        prediction[mode]={
            k:[np.full(len(f),np.nan),np.full(len(f),np.nan)]
            for k in models
        }
        for day in sorted(f.day.unique()):
            ix=np.flatnonzero(f.day.eq(day).to_numpy())
            target=f.iloc[ix]
            hist=history_before_day(relevant,hC,day,mode=mode)
            result=predictions_for_history(hist,target,models,meta)
            for k,(p0,p1) in result.items():
                prediction[mode][k][0][ix]=p0
                prediction[mode][k][1][ix]=p1
        for k,(p0,p1) in prediction[mode].items():
            if not (np.isfinite(p0).all() and np.isfinite(p1).all()):
                raise ValueError("HOLD_MISSING_OR_NONFINITE_ROLLING_PREDICTION")
    def score(mode,kind,p0,p1):
        s=_scores(f,p0,p1)
        s["singleway_399_bootstrap"]=_pooled_ci(f,p0,p1,B=399)
        s["monthly"]={}
        for yearmonth,g in f.groupby(f.day.dt.strftime("%Y-%m")):
            mask=f.day.dt.strftime("%Y-%m").eq(yearmonth).to_numpy()
            s["monthly"][yearmonth]=_scores(f.loc[mask],p0[mask],p1[mask])
        s["no_kin_rmse_gain_vs_stale"]=(
            old_scores[kind]["RMSE_portable_no_kin"]-
            s["RMSE_portable_no_kin"]
        )
        s["kin_rmse_gain_vs_stale"]=(
            old_scores[kind]["RMSE_portable_kin"]-
            s["RMSE_portable_kin"]
        )
        return s
    scores={"stale_2021":old_scores}
    for mode,types in prediction.items():
        scores[mode]={}
        for kind,(p0,p1) in types.items():
            scores[mode][kind]=score(mode,kind,p0,p1)
    last_A=old.groupby("horse",observed=True).day.max()
    old_last=last_A.reindex(f.horse.astype(str)).to_numpy(dtype="datetime64[ns]")
    dated=(f.day.to_numpy(dtype="datetime64[ns]")-old_last)/np.timedelta64(1,"D")
    past_target=pre2026[pre2026.horse.isin(target_horses)]
    hist_2026=hC[hC.day.ge(pd.Timestamp("2026-01-01"))]
    paired_recency = (
        past_target.groupby("horse").day.max().reindex(f.horse.astype(str))
    )
    have_C2025 = set(pre2026[pre2026.year.eq(2025)].horse)
    past_2026_horses=set(hist_2026.horse)
    report = {
        "status":"POSTHOC_2026_DAY_LAGGED_SOURCE_C_RECENCY_REPLAY_NOT_CAUSAL",
        "source_sha256":{
            "sourceA":"c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f",
            "sourceB":"7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9",
            "sourceC":"ca14ff253018433e8e14bc583628f85ca909195d5e4edb42c6d1e2ade939ba6f"
        },
        "original_2026_source_gate":quality,
        "parity":{
            "locked_focal_rows":len(f),
            "locked_focal_horses":int(f.horse.nunique()),
            "locked_focal_races":int(f.race.nunique()),
            "locked_focal_days":int(f.day.nunique()),
            "locked_B_to_C_pre2025_two_day_horses":len(bridge),
            "frozen_original_models_reproduced_to_1e8":True,
            "reduced_sourceA_family_features_reproduce_original_to_1e10":True,
            **filter_qa
        },
        "historic_sourceC_qa":{
            "all_complete_race_count_by_year":{
                str(y):int(n) for y,n in
                hC.groupby("year").race.nunique().items()
            },
            "target_or_relative_linked_history_rows_by_year":{
                str(y):int(n) for y,n in hC.year.value_counts().sort_index().items()
            },
            "prior_2026_sourceC_history_rows":int(len(pre2026)),
            "prior_2026_distinct_C_horses":int(pre2026.horse.nunique()),
            "2025_prior_history_horse_coverage":{
                "unique_focal_horses_with_2025_C_runs":
                    len(have_C2025.intersection(target_horses)),
                "all_2026_focal_horses":len(target_horses),
                "focal_2026_start_rows_with_2025_C_runs":
                    int(f.horse.isin(have_C2025).sum())
            },
            "rolling_2026_sourceC_horse_coverage":{
                "unique_target_horses_with_any_2026_C_rows":
                    len(past_2026_horses.intersection(target_horses))
            },
            "stale_sourceA_last_race_days":{
                "median_days":float(np.nanmedian(dated)),
                "q25_days":float(np.nanquantile(dated,.25)),
                "q75_days":float(np.nanquantile(dated,.75)),
            },
            "original_C_complete_race_quality":c_qa,
            "no_same_day_sourceC_result_used":True,
            "no_publication_time_at_day_resolution":True
        },
        "frozen_ridge_alpha":RIDGE_ALPHA,
        "training_sourceA_2018_2021_only":True,
        "mode_results":scores,
        "interpretation_limits":[
            "Post-hoc after original 2026 outcome inspection; no untouched evaluation.",
            "Only earlier calendar days, not independently verified result_known_at timestamps.",
            "All focal and family C history identities fixed from pre2025 two-event crosswalk.",
            "C source rank is classified-finisher normalization and differs from old source's selection.",
            "Cannot separate race-history aging from source/coverage/cohort changes.",
            "The 2026 target is a small group of previously active horses; 2026 data stops May 17.",
            "H: official studbook, pedigree A, anonymous genotype G and odds market are not provided.",
            "Third-party upstream racing-data rights and license not independently cleared.",
        ],
        "no_horse_names_ids_race_rows_or_predictions_exported":True
    }
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",type=Path,required=True)
    ap.add_argument("--sqlite",type=Path,required=True)
    ap.add_argument("--jra-csv",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    r=analyze(args.archive,args.sqlite,args.jra_csv)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
