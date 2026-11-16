#!/usr/bin/env python3
"""Joint source-B strict-complete-race and strong old-history kin sensitivity.

All empirical family/rank scores were inspected BEFORE this study; explicitly
post-hoc. Recompute locked primary, original strict and new strong all-rows
benchmarks to 1e-8 before returning a source-locked *joint* cohort score.
Only after original->later source crosswalk from >=2 PRE-2022 matching
race events can Horse.races be linked to Race.horses on the same horse ID.
No individual results, aliases, source rows, horses or fitted predictions
ever leave the runner.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_hf_event_anchor_gate import anchor_name_histories
from ecology_japan_2022_denominator_audit import (
    audit_race_entries, one_observation_original_baselines
)
from ecology_japan_2022_strong_portable_baseline import (
    old_metadata, extra_features, STRONG_NO_KIN, STRONG_KIN
)
from ecology_japan_2022_independent_forward import (
    RIDGE_ALPHA, make_common_features, fit_weighted_ridge,
    predict_weighted_ridge, _scores, _pooled_ci
)

ALL_STRONG_NO_KIN = 0.31169267268761647
ALL_STRONG_KIN = 0.31143282328331967
STRICT_ROWS = 244147
STRICT_HORSES = 12887
STRICT_ORIGINAL_NO_KIN = 0.31354335632983643
STRICT_ORIGINAL_KIN = 0.3132186661774923


def strict_mask_exact_horse_race(raw, future, db, n_anchors):
    con = sqlite3.connect(f"file:{db}?mode=ro",uri=True)
    try:
        old_anchor=raw[["horse_id","horse_name","date","place","distance"]]
        calendar={str(rid):day for rid,day in con.execute("SELECT rid,date FROM race")}
        def new_records():
            return con.execute("SELECT hid,name,races FROM horse")
        crosswalk, gate=anchor_name_histories(
            old_anchor,new_records,race_dates=calendar
        )
        if gate["two_event_anchor_horses"]!=n_anchors:
            raise ValueError("HOLD_CROSSWALK_COUNT_DRIFT_JOINT")
        reverse={}
        for n,o in crosswalk.items():
            if o in reverse:
                raise ValueError("HOLD_AMBIGUOUS_OLD_HORSE_IN_JOINT")
            reverse[o]=str(n)
        new_horse_ids=future.horse.astype(str).map(reverse)
        if new_horse_ids.isna().any():
            raise ValueError("HOLD_MISSING_NEW_ID_FOR_FROZEN_HORSE")
        declared=future.groupby("race",sort=False).source_declared_field_size
        if (declared.nunique()!=1).any():
            raise ValueError("HOLD_INCONSISTENT_DECLARED_FIELD")
        fields=declared.first()
        strict_race={}
        race_ranks={}
        counts=Counter()
        for rid,raw_horses in con.execute(
            "SELECT rid,horses FROM race WHERE substr(date,1,4) BETWEEN '2022' AND '2024'"
        ):
            rid=str(rid)
            if rid not in fields.index:
                continue
            rec,ranks=audit_race_entries(raw_horses,int(fields.loc[rid]))
            is_strict=(rec["status"]=="STRICT_COMPLETE_CLASSIFIED_RACE")
            strict_race[rid]=is_strict
            if is_strict:
                race_ranks[rid]=ranks
            counts[rec["status"]]+=1
        if len(strict_race)!=len(fields):
            raise ValueError("HOLD_MISSING_RACE_TABLE_ROWS_IN_JOINT")
        okay=np.zeros(len(future),dtype=bool)
        failure=Counter()
        for i,(rid,hid,old_y,n) in enumerate(zip(
            future.race,new_horse_ids,future.y,
            future.source_declared_field_size
        )):
            if not strict_race[str(rid)]:
                failure["non_strict_race"]+=1
                continue
            actual=race_ranks[str(rid)].get(str(hid))
            expected=1+old_y*(n-1)
            if actual is None or not np.isclose(actual,expected,atol=1e-9):
                failure["strict_race_horse_id_or_rank_mismatch"]+=1
                continue
            okay[i]=True
        if okay.sum()!=STRICT_ROWS or future.loc[okay].horse.nunique()!=STRICT_HORSES:
            raise ValueError("HOLD_STRICT_COHORT_VS_ORIGINAL_AUDIT")
        return okay,{
            "all_frozen_races":len(fields),
            "strict_races":int(sum(strict_race.values())),
            "strict_focal_rows":int(okay.sum()),
            "strict_focal_horses":int(future.loc[okay].horse.nunique()),
            "race_qa_counts":dict(counts),
            "excluded_focal_rows":dict(failure),
            "same_new_source_horse_ID_and_rank_verified":True
        }
    finally:
        con.close()


def predictions_stronger_old_history(raw, old, future):
    meta=old_metadata(raw)
    blocks=[]
    train_quality={}
    for yr in (2018,2019,2020,2021):
        h=old[old.year<yr]
        t=old[old.year==yr]
        b=make_common_features(h,t)
        x,q=extra_features(h,t,meta)
        blocks.append((t,pd.concat([b.reset_index(drop=True),x],axis=1)))
        train_quality[str(yr)]=q
    train=pd.concat([b for t,b in blocks],ignore_index=True)
    y=np.concatenate([t.y.to_numpy() for t,b in blocks])
    ids=np.concatenate([t.horse.astype(str).to_numpy() for t,b in blocks])
    nm=fit_weighted_ridge(train,y,ids,STRONG_NO_KIN,alpha=RIDGE_ALPHA)
    km=fit_weighted_ridge(train,y,ids,STRONG_KIN,alpha=RIDGE_ALPHA)
    f0=make_common_features(old,future)
    extras,quality=extra_features(old,future,meta)
    x=pd.concat([f0.reset_index(drop=True),extras],axis=1)
    p0=predict_weighted_ridge(nm,x)
    p1=predict_weighted_ridge(km,x)
    all_= _scores(future,p0,p1)
    if (abs(all_["RMSE_portable_no_kin"]-ALL_STRONG_NO_KIN)>1e-8
            or abs(all_["RMSE_portable_kin"]-ALL_STRONG_KIN)>1e-8):
        raise ValueError("HOLD_STRONG_ORIGINAL_SCORE_PARITY")
    return p0,p1,all_,quality


def analyze(archive:Path,db:Path):
    raw,old,f,_,gate,_=load_sources(archive,db)
    p_old0,p_old1,all_original=one_observation_original_baselines(old,f)
    p_new0,p_new1,all_strong,strong_quality=predictions_stronger_old_history(raw,old,f)
    mask,strict_qa=strict_mask_exact_horse_race(
        raw,f,db,gate["two_event_anchor_horses"]
    )
    t=f.loc[mask]
    old_strict=_scores(t,p_old0[mask],p_old1[mask])
    if (abs(old_strict["RMSE_portable_no_kin"]-STRICT_ORIGINAL_NO_KIN)>1e-8
            or abs(old_strict["RMSE_portable_kin"]-STRICT_ORIGINAL_KIN)>1e-8):
        raise ValueError("HOLD_STRICT_ORIGINAL_COHORT_SCORE_PARITY")
    p0,p1=p_new0[mask],p_new1[mask]
    score=_scores(t,p0,p1)
    score["CI95_singleway_cluster"]=_pooled_ci(t,p0,p1,B=399)
    score["posthoc_age_sex_recency_no_kin_gain_vs_original_no_kin"]=(
        old_strict["RMSE_portable_no_kin"]-score["RMSE_portable_no_kin"]
    )
    by_year={}
    for yr in (2022,2023,2024):
        y=t.year.eq(yr).to_numpy()
        if y.any():
            by_year[str(yr)]=_scores(t.loc[t.year==yr],p0[y],p1[y])
    return {
        "status":"POSTHOC_JOINT_STRICT_RACE_AND_STRONG_AGE_SEX_RECENCY_NOT_GENETIC_CAUSATION",
        "old_archive_sha256":"c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f",
        "new_sqlite_sha256":SQLITE_SHA,
        "frozen_source_identity_horses":int(gate["two_event_anchor_horses"]),
        "original_all_row_parity":all_original,
        "strong_all_row_parity":all_strong,
        "strict_original_parity":old_strict,
        "strict_source_qa":strict_qa,
        "strong_history_coverage":strong_quality,
        "strict_strong":score,
        "strict_strong_yearly":by_year,
        "training_2018_2021_only":True,
        "strong_model_feature_families":{
            "no_kin":list(STRONG_NO_KIN),
            "with_kin":list(STRONG_KIN),
            "ridge_alpha":RIDGE_ALPHA
        },
        "interpretation_limits":[
            "Completely post-hoc, not untouched prospective test.",
            "Future source Race.horses rank and Horse.races declared runners are both from same database; not independent official certification.",
            "Horses have prior pre2022 racing records; new debutants are excluded.",
            "Old-source sex and inferred age can be stale; only source-A pretarget historical data used.",
            "Parent IDs share genes AND breeding management and selection, cannot identify causality.",
            "JRA/NAR all registered horse studbook A and anonymous genomic G not linked.",
            "2024 performance against midpoint must be reported, as must all unfavorable findings.",
            "SourceA and sourceB underlying record reuse and redistribution rights unverified."
        ],
        "no_raw_horse_ids_names_race_rows_or_individual_predictions_exported":True
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--sqlite",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":r["status"],
        "strict_source_qa":r["strict_source_qa"],
        "strict_original_parity":r["strict_original_parity"],
        "strict_strong":r["strict_strong"],
        "strict_strong_yearly":r["strict_strong_yearly"]
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
