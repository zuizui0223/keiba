#!/usr/bin/env python3
"""Post-hoc augment of portable old-source 2022-24 family-history benchmark.

Adds only independently historically-known focal-horse information:
estimated current age (from source A pre-cutoff birth year), last
known source-A sex, time since last pre-cutoff start, last ten results,
and share of past JRA starts. No later-source sex/age/venue/class ID guess.
Fits no-parent and +same-parent-other-horse history ridge identically.
The untouched original 2022-24 result MUST reproduce exactly beforehand.
No horse IDs, names, outcomes, individual predictions or source rows exported.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_archive_forward import clean_id
from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_2022_denominator_audit import one_observation_original_baselines
from ecology_japan_2022_independent_forward import (
    FEATURE_NO_KIN, FEATURE_KIN, RIDGE_ALPHA,
    fit_weighted_ridge, make_common_features, predict_weighted_ridge,
    _scores, _pooled_ci,
)

ADDED_FEATURES = (
    "log_days_since_last", "log_last10_mean", "prior_jra_fraction",
    "age_from_pre2022_year", "age_available", "age_conflict",
    "sex_female", "sex_gelding", "sex_unknown",
)
STRONG_NO_KIN = FEATURE_NO_KIN + ADDED_FEATURES
STRONG_KIN = FEATURE_KIN + ADDED_FEATURES

SEX_MAP = {
    "牡": 1, "牡馬": 1, "male": 1, "colt": 1, "horse": 1,
    "m": 1, "c": 1,
    "牝": 2, "牝馬": 2, "female": 2, "filly": 2, "mare": 2,
    "f": 2,
    "セ": 3, "せん": 3, "騸": 3, "セン": 3,
    "gelding": 3, "g": 3,
}

def old_metadata(raw):
    """Store only pre-2022 source-A age/sex features, no future outcomes."""
    horse = clean_id(raw.horse_id).astype(str)
    day = pd.to_datetime(raw.date,format="mixed",errors="coerce")
    age = pd.to_numeric(raw.age,errors="coerce")
    year = day.dt.year.astype(float)
    birth = (year - age).where(age.between(2,19) & year.between(2000,2021))
    sex = raw.sex.fillna("").astype(str).str.strip().str.casefold().map(SEX_MAP).fillna(0)
    m = pd.DataFrame({
        "horse":horse,"day":day,
        "year":year,
        "birthyear":birth,
        "sex_code":sex.astype("int8"),
    })
    m = m[m.horse.ne("") & m.day.notna() & m.day.lt(pd.Timestamp("2022-01-01"))]
    return m.reset_index(drop=True)


def extra_features(history, targets, metadata):
    """All historical features have timestamps strictly before FIRST target.

    Age/sex are inferred only from pre-target source A entries; if the current
    horse appears for the first time, unknown is explicitly represented.
    """
    if history.empty or targets.empty or history.day.max() >= targets.day.min():
        raise ValueError("HOLD_INVALID_TEMPORAL_HISTORY_FOR_STRONG_BASELINE")
    t = targets.reset_index(drop=True)
    cutoff = t.day.min()
    past = metadata[metadata.day < cutoff]
    hids = t.horse.astype(str)
    past_age = past[past.birthyear.notna()]
    if len(past_age):
        births = past_age.groupby("horse").birthyear.agg(["median","min","max"])
        byear = births["median"].reindex(hids).to_numpy(float)
        conflict = (births["max"] != births["min"]).reindex(hids).fillna(False).to_numpy(bool)
    else:
        byear = np.full(len(t),np.nan)
        conflict = np.zeros(len(t),dtype=bool)
    age = t.year.to_numpy(float) - byear
    age_ok = np.isfinite(age) & (age >= 2) & (age <= 20) & ~conflict
    age_f = np.where(age_ok, age, 5.0)
    # Avoid inferring a biological sex from blank, misleading strings or
    # assigning missing source labels as a shared demographic group.
    sex_past = past[past.sex_code.ne(0)]
    if len(sex_past):
        last_sex = (sex_past.sort_values(["day","horse"],kind="mergesort")
                    .drop_duplicates("horse",keep="last")
                    .set_index("horse").sex_code)
        sex = last_sex.reindex(hids).fillna(0).to_numpy(int)
    else:
        sex = np.zeros(len(t),dtype=int)
    last_day = history.groupby("horse",observed=True).day.max()
    last = last_day.reindex(hids)
    gap = (t.day.to_numpy(dtype="datetime64[ns]")
           - last.to_numpy(dtype="datetime64[ns]")) / np.timedelta64(1,"D")
    gap = np.where(np.isfinite(gap),np.clip(gap,0,3650),3650)
    ordered = history.sort_values(["day","horse","race"])
    last10 = (ordered.groupby("horse",observed=True)
              .tail(10).groupby("horse",observed=True).y.mean())
    last10 = last10.reindex(hids).fillna(.5).to_numpy(float)
    jra_share = (history.assign(_jra=history.circuit.astype(str).eq("JRA").astype(float))
                 .groupby("horse",observed=True)._jra.mean())
    jra_share = jra_share.reindex(hids).fillna(.5).to_numpy(float)
    x = pd.DataFrame({
        "log_days_since_last": np.log1p(gap),
        "log_last10_mean": last10,
        "prior_jra_fraction": jra_share,
        "age_from_pre2022_year": age_f,
        "age_available": age_ok.astype(float),
        "age_conflict": conflict.astype(float),
        "sex_female": sex.eq(2).astype(float) if isinstance(sex,pd.Series) else (sex==2).astype(float),
        "sex_gelding": (sex==3).astype(float),
        "sex_unknown": (sex==0).astype(float),
    })
    if not np.isfinite(x.to_numpy(float)).all():
        raise ValueError("HOLD_NONFINITE_STRONG_PREHISTORY_FEATURES")
    return x, {
        "rows": len(t),
        "age_available_fraction":float(age_ok.mean()),
        "age_pre2022_birthyear_conflict_fraction":float(conflict.mean()),
        "sourceA_sex_known_fraction":float((sex!=0).mean()),
        "unknown_lifetime_last_race_fraction":float((gap==3650).mean()),
        "feature_cutoff":str(cutoff.date()),
        "no_future_sourceB_outcome_or_race_class_in_features":True,
    }


def analyze(archive:Path, sqlite_file:Path):
    raw,old,f,quality,identity,event_qa=load_sources(archive,sqlite_file)
    old_p0, old_p1, frozen = one_observation_original_baselines(old,f)
    meta=old_metadata(raw)
    training=[]
    quality_train={}
    for year in (2018,2019,2020,2021):
        h=old[old.year < year]
        t=old[old.year == year]
        orig=make_common_features(h,t)
        extra, stat=extra_features(h,t,meta)
        training.append((t,pd.concat([orig.reset_index(drop=True),extra],axis=1)))
        quality_train[str(year)]=stat
    x=pd.concat([a[1] for a in training],ignore_index=True)
    y=np.concatenate([a[0].y.to_numpy(float) for a in training])
    horse=np.concatenate([a[0].horse.astype(str).to_numpy() for a in training])
    base=fit_weighted_ridge(x,y,horse,STRONG_NO_KIN,alpha=RIDGE_ALPHA)
    family=fit_weighted_ridge(x,y,horse,STRONG_KIN,alpha=RIDGE_ALPHA)
    orig_f=make_common_features(old,f)
    extra_f, stat_f=extra_features(old,f,meta)
    xf=pd.concat([orig_f.reset_index(drop=True),extra_f],axis=1)
    p0=predict_weighted_ridge(base,xf)
    p1=predict_weighted_ridge(family,xf)
    main=_scores(f,p0,p1)
    main["CI95_singleway_sensitivity"]=_pooled_ci(f,p0,p1,B=399)
    main["RMSE_frozen_original_no_kin"]=frozen["RMSE_portable_no_kin"]
    main["RMSE_frozen_original_kin"]=frozen["RMSE_portable_kin"]
    main["extra_no_kin_vs_frozen_no_kin"]=(frozen["RMSE_portable_no_kin"]
                                          - main["RMSE_portable_no_kin"])
    per_year={}
    for yr in (2022,2023,2024):
        mask=f.year.eq(yr).to_numpy()
        per_year[str(yr)] = _scores(f.loc[mask],p0[mask],p1[mask])
        per_year[str(yr)]["extra_no_kin_vs_frozen_no_kin"] = (
            _scores(f.loc[mask],old_p0[mask],old_p1[mask])["RMSE_portable_no_kin"]
            - per_year[str(yr)]["RMSE_portable_no_kin"]
        )
    return {
        "status":"POSTHOC_2022_2024_PRE2022_AGE_SEX_RECENCY_HISTORY_BASELINE_NOT_CAUSAL",
        "sourceA_archive_sha256":"c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f",
        "sourceB_sqlite_sha256":SQLITE_SHA,
        "model_features":{
            "frozen_original_no_kin":list(FEATURE_NO_KIN),
            "new_pre2022_only_history_features":list(ADDED_FEATURES),
            "new_no_kin":list(STRONG_NO_KIN),
            "new_kin":list(STRONG_KIN),
            "same_ridge_penalty":RIDGE_ALPHA,
            "posthoc_not_preregistered":True,
        },
        "old_original_source_score_parity":frozen,
        "training_years":[2018,2019,2020,2021],
        "meta_qa":{"training":quality_train,"heldout_2022_2024":stat_f},
        "pooled":main,
        "by_year":per_year,
        "interpretation_gate":[
            "Age/sex/recency estimated strictly from Source A pretarget dates, no Source B demographic guess.",
            "The primary 2022-24 result has been seen before choosing extra features: this is exploratory conditional sensitivity, not a new holdout.",
            "No new source race class, trainer or current jockey IDs were verified across archives.",
            "Even a remaining conditional family gain cannot distinguish genetic inheritance from breeding, rearing or selection environments.",
            "Original 2022-2024 rank denominator mismatch remains, audited in a separate pipeline.",
            "No national studbook, genomic G, full pedigree A or market profitability inferred."
        ],
        "no_names_ids_or_individual_results_exported":True
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--sqlite",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    j=analyze(args.archive,args.sqlite)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":j["status"],"pooled":j["pooled"],"by_year":j["by_year"],
        "source_meta_qa":j["meta_qa"]
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
