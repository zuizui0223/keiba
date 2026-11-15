#!/usr/bin/env python3
"""Independent calendar-year/source race-rank test with a frozen pre-2022 model.

Two historical race-result anchors link the sources. Source-specific horse IDs
are NOT assumed to match and no future result establishes identity.
No race, individual name, ID or predicted rank is exported. These are direct
sire/dam history features, NOT genomic or whole-pedigree genetic effects.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

import numpy as np
import pandas as pd

from ecology_japan_archive_forward import COLS, SOURCE_SHA, prepare_frame
from ecology_japan_hf_event_anchor_gate import anchor_name_histories
from ecology_japan_hf_sqlite_source_gate import normalize_date

FEATURE_NO_KIN=("own_mean","log_own_count","context_mean","log_context_n",
                "last1","last3","surface_turf","distance_km")
FEATURE_KIN=FEATURE_NO_KIN+("sire_kin_history","dam_kin_history",
                            "log_sire_relative_count","log_dam_relative_count")
RIDGE_ALPHA=100.0


def parse_independent_history(raw, race_index:dict) -> tuple[list[dict],dict]:
    if not race_index:
        raise ValueError("HOLD_SOURCE_EVENT_DATE_TABLE_EMPTY")
    qa=Counter()
    events=[]
    if not raw:
        return events,dict(qa)
    rows=json.loads(raw)
    if isinstance(rows,list) and rows and isinstance(rows[0],list) and rows[0] and isinstance(rows[0][0],list):
        rows=rows[0]
    if not isinstance(rows,list):
        return events,{"invalid_structure":1}
    for rec in rows:
        qa["candidate_history_rows"]+=1
        if not isinstance(rec,list) or len(rec)<17:
            qa["invalid_structure"]+=1
            continue
        race_id=str(rec[0]).strip()
        metadata=race_index.get(race_id)
        if metadata is None:
            qa["missing_race_id_lookup"]+=1
            continue
        date_value,distance,ctype=metadata
        date=normalize_date(date_value)
        if qa["sampled_field_types"]<500:
            qa["sampled_field_types"]+=1
            for key,value in (("race_surface",ctype),("horse_surface",rec[4]),
                              ("race_distance",distance),("horse_distance",rec[5]),
                              ("source_field_size",rec[7]),("source_placing",rec[12])):
                qa["field_type_"+key+"_"+type(value).__name__]+=1
                qa["field_int_castable_"+key]+=str(value).strip().lstrip("-").isdigit()
        def require_int(value,key):
            try:
                return int(value)
            except (TypeError,ValueError,OverflowError):
                qa["invalid_"+key]+=1
                return None
        source_distance=require_int(distance,"race_distance")
        source_surface=require_int(ctype,"race_surface")
        horse_distance=require_int(rec[5],"horse_distance")
        horse_surface=require_int(rec[4],"horse_surface")
        n=require_int(rec[7],"source_field_size")
        place=require_int(rec[12],"source_placing")
        if any(v is None for v in (source_distance,source_surface,
                                   horse_distance,horse_surface,n,place)):
            qa["invalid_structural_values"]+=1
            continue
        if not date:
            qa["missing_source_calendar_date"]+=1
            continue
        if horse_distance!=source_distance or horse_surface!=source_surface:
            qa["source_race_metadata_conflicts"]+=1
            continue
        if not (2<=n<=30 and 1<=place<=n):
            qa["invalid_relative_rank_or_field"]+=1
            continue
        if not (600<=horse_distance<=4000 and horse_surface in (0,1)):
            qa["unsupported_distance_or_surface"]+=1
            continue
        if len(rec)>=18:
            embedded=normalize_date(rec[17])
            if embedded and embedded!=date:
                qa["inconsistent_embedded_source_date"]+=1
                continue
        when=pd.Timestamp(f"{date[:4]}-{date[4:6]}-{date[6:]}")
        events.append({
            "race_id":race_id,"day":when,"year":int(date[:4]),
            "distance":horse_distance,"surface":"turf" if horse_surface==1 else "dirt",
            "stratum":("turf" if horse_surface==1 else "dirt")+":"+str(horse_distance//400),
            "y":(place-1)/(n-1),"source_declared_field_size":n,
        })
        qa["eligible_rows"]+=1
    return events,dict(qa)


def _peer(history:pd.DataFrame, targets:pd.DataFrame, group:str):
    hh=history[history[group].astype(str).ne("")]
    if hh.empty:
        return np.zeros(len(targets)),np.zeros(len(targets))
    p=hh.groupby([group,"stratum","horse"],observed=True).y.mean().rename("score").reset_index()
    p["score"]=p.score-.5
    total=p.groupby([group,"stratum"],observed=True).score.agg(["sum","size"])
    keys=pd.MultiIndex.from_frame(targets[[group,"stratum"]])
    all_=total.reindex(keys).fillna(0)
    focal=p.set_index([group,"stratum","horse"]).score.reindex(
        pd.MultiIndex.from_frame(targets[[group,"stratum","horse"]]))
    n=np.maximum(0,all_["size"].to_numpy()-focal.notna().to_numpy())
    v=all_["sum"].to_numpy()-focal.fillna(0).to_numpy()
    return v,n


def make_common_features(history:pd.DataFrame, targets:pd.DataFrame) -> pd.DataFrame:
    if history.empty or targets.empty:
        raise ValueError("HOLD_EMPTY_COMPARISON_COHORT")
    if history.day.max()>=targets.day.min():
        raise ValueError("HOLD_FUTURE_LABELS_IN_FEATURE_HISTORY")
    hist=history.sort_values(["day","horse"])
    t=targets.reset_index(drop=True)
    old=hist.groupby("horse",observed=True).y.agg(["mean","size"])
    g=old.reindex(t.horse.astype(str)).fillna({"mean":.5,"size":0})
    n=g["size"].to_numpy(float)
    own=.5+n/(n+5)*(g["mean"].to_numpy(float)-.5)
    context=hist.groupby(["horse","stratum"],observed=True).y.agg(["mean","size"])
    c=context.reindex(pd.MultiIndex.from_frame(t[["horse","stratum"]])).fillna({"mean":.5,"size":0})
    cn=c["size"].to_numpy(float)
    cm=.5+cn/(cn+3)*(c["mean"].to_numpy(float)-.5)
    last={}
    for k in (1,3):
        r=hist.groupby("horse",observed=True).tail(k).groupby("horse",observed=True).y.mean()
        last["last"+str(k)]=r.reindex(t.horse.astype(str)).fillna(.5).to_numpy()
    ss,sn=_peer(hist,t,"sire_id")
    ds,dn=_peer(hist,t,"dam_id")
    return pd.DataFrame({
        "own_mean":own,
        "log_own_count":np.log1p(n),
        "context_mean":cm,
        "log_context_n":np.log1p(cn),
        **last,
        "surface_turf":t.surface.eq("turf").astype(float).to_numpy(),
        "distance_km":pd.to_numeric(t.distance,errors="coerce").fillna(1600).to_numpy()/1000,
        "sire_kin_history":(5/(n+5))*ss/(8+sn),
        "dam_kin_history":(5/(n+5))*ds/(8+dn),
        "log_sire_relative_count":np.log1p(sn),
        "log_dam_relative_count":np.log1p(dn),
        "sire_relative_count":sn,
        "dam_relative_count":dn,
    })


def _horse_weights(horses):
    ids=pd.Series(np.asarray(horses).astype(str))
    return (1/ids.map(ids.value_counts())).to_numpy(float)


def fit_weighted_ridge(features:pd.DataFrame,y,horses,columns,*,alpha=RIDGE_ALPHA):
    cols=list(columns)
    if not cols or alpha<=0:
        raise ValueError("HOLD_MODEL_FEATURES_OR_REGULARIZATION")
    x=features[cols].to_numpy(float)
    target=np.asarray(y,float)
    if len(x)!=len(target):
        raise ValueError("HOLD_LABEL_ROW_COUNT")
    mu=np.mean(x,axis=0)
    sd=np.std(x,axis=0)
    sd[sd<1e-12]=1
    z=np.column_stack((np.ones(len(x)),(x-mu)/sd))
    w=_horse_weights(horses);w=w/w.mean()
    lhs=z.T@(z*w[:,None])
    diag=np.full(z.shape[1],alpha);diag[0]=0
    lhs+=np.diag(diag)
    coef=np.linalg.solve(lhs,z.T@(target*w))
    return {"columns":cols,"mean":mu,"sd":sd,"coef":coef,"alpha":alpha}


def predict_weighted_ridge(model,features:pd.DataFrame):
    x=features[model["columns"]].to_numpy(float)
    z=np.column_stack((np.ones(len(x)),(x-model["mean"])/model["sd"]))
    return np.clip(z@model["coef"],0,1)


def _scores(targets:pd.DataFrame,p0,p1):
    y=targets.y.to_numpy(float)
    w=_horse_weights(targets.horse)
    m0=np.sqrt(np.average((y-p0)**2,weights=w))
    m1=np.sqrt(np.average((y-p1)**2,weights=w))
    neutral=np.sqrt(np.average((y-.5)**2,weights=w))
    return {
        "rows":len(targets),"unique_horses":int(targets.horse.nunique()),
        "races":int(targets.race.nunique()),
        "RMSE_unchanged_midpoint":float(neutral),
        "RMSE_portable_no_kin":float(m0),
        "RMSE_portable_kin":float(m1),
        "M0_minus_kin_gain":float(m0-m1),
        "midpoint_minus_kin_gain":float(neutral-m1),
    }


def _pooled_ci(t:pd.DataFrame,p0,p1,B=499):
    y=t.y.to_numpy(float)
    w=_horse_weights(t.horse)
    sq=np.column_stack(((y-p0)**2,(y-p1)**2,(y-.5)**2))*w[:,None]
    out={}
    for label,grp in (("horse",t.horse.astype(str)),("race_day",t.day.astype(str))):
        tab=pd.DataFrame(sq,columns=["base","kin","neutral"])
        tab["w"]=w
        tab["group"]=grp.to_numpy()
        vals=tab.groupby("group",observed=True).sum().to_numpy()
        N=len(vals)
        if N<20:
            out[label]={"status":"HOLD_LT20_CLUSTERS","clusters":N}
            continue
        rng=np.random.default_rng(20261115)
        arr=[]
        for _ in range(B):
            sel=vals[rng.integers(N,size=N)].sum(axis=0)
            r=np.sqrt(sel[:3]/sel[3])
            arr.append([r[0]-r[1],r[2]-r[1]])
        a=np.asarray(arr)
        out[label]={
            "clusters":N,"bootstrap_draws":B,
            "CI95_M0_minus_kin_gain":np.quantile(a[:,0],[.025,.975]).tolist(),
            "CI95_neutral_minus_kin_gain":np.quantile(a[:,1],[.025,.975]).tolist(),
            "single_way_approximation_only":True,
        }
    return out


def analyze(original_archive:Path, new_sqlite:Path) -> dict:
    if hashlib.sha256(original_archive.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError("HOLD_ORIGINAL_TRAINING_DATA_SOURCE_SHA")
    with zipfile.ZipFile(original_archive) as z,z.open("2010-2021.csv") as fd:
        raw=pd.read_csv(fd,dtype=str,keep_default_na=False,
                        usecols=COLS)
    original,qa=prepare_frame(raw)
    original["stratum"]=original.surface.astype(str)+":"+(original.distance//400).astype(int).astype(str)
    history_source=original.copy()
    selected_columns=["horse_id","horse_name","date","place","distance"]
    anchor_source=raw[selected_columns].copy()
    con=sqlite3.connect(f"file:{new_sqlite}?mode=ro",uri=True)
    lookup={
        str(rid): (date,distance,int(surface))
        for rid,date,distance,surface in con.execute("SELECT rid,date,distance,course FROM race")
    }
    def source_horses():
        return con.execute("SELECT hid,name,races FROM horse")
    crosswalk,identity=anchor_name_histories(anchor_source,source_horses,race_dates={
        k:v[0] for k,v in lookup.items()
    })
    if identity["status"]!="CROSS_SOURCE_TWO_EVENT_NAME_IDENTITY_CANDIDATE_NOT_STUDBOOK":
        return {"status":"HOLD_CROSS_SOURCE_IDENTITY_SUPPORT","identity":identity}
    parents=original[["horse","sire_id","dam_id"]].astype(str).drop_duplicates()
    if parents.horse.duplicated().any():
        raise ValueError("HOLD_PEDIGREE_CONFLICT_IN_PRE2022_SOURCE")
    known=parents.set_index("horse")
    future=[]
    event_qa=Counter()
    independent_names=Counter()
    for newhid,rawhistory in con.execute("SELECT hid,races FROM horse"):
        oldid=crosswalk.get(str(newhid))
        if oldid not in known.index:
            continue
        recs,diagnostics=parse_independent_history(rawhistory,lookup)
        event_qa.update(diagnostics)
        p=known.loc[oldid]
        for row in recs:
            if not 2022<=row["year"]<=2025:
                continue
            row.update({
                "horse":oldid,
                "sire_id":p["sire_id"],
                "dam_id":p["dam_id"],
                "race":row["race_id"],
            })
            future.append(row)
    con.close()
    if not future:
        return {"status":"HOLD_NO_VALID_INDEPENDENT_2022_OUTCOMES",
                "identity":identity,"source_independent_quality":dict(event_qa)}
    f=pd.DataFrame(future)
    f=f.sort_values(["day","race","horse"]).reset_index(drop=True)
    duplicates=int(f.duplicated(["race","horse"]).sum())
    if duplicates:
        raise ValueError("HOLD_DUPLICATE_HORSE_RACE_IN_INDEPENDENT_SOURCE")
    f["first_recorded_new_source"]=~f.duplicated(["horse"])
    training=[]
    for yr in (2018,2019,2020,2021):
        h=history_source[history_source.year<yr]
        target=history_source[history_source.year==yr]
        features=make_common_features(h,target)
        training.append((yr,target[["horse","y"]].reset_index(drop=True),features))
    features=pd.concat([x[2] for x in training],ignore_index=True)
    labels=pd.concat([x[1] for x in training],ignore_index=True)
    models={
        "no_kin":fit_weighted_ridge(features,labels.y.to_numpy(),labels.horse.to_numpy(),FEATURE_NO_KIN),
        "kin":fit_weighted_ridge(features,labels.y.to_numpy(),labels.horse.to_numpy(),FEATURE_KIN),
    }
    end=history_source.day.max()
    ff=make_common_features(history_source,f)
    p0=predict_weighted_ridge(models["no_kin"],ff)
    p1=predict_weighted_ridge(models["kin"],ff)
    # Full calendar years only for primary external holdout; 2025 incomplete.
    keep=f.year.between(2022,2024).to_numpy()
    pooled=_scores(f.loc[keep],p0[keep],p1[keep])
    year={}
    for yr in (2022,2023,2024,2025):
        mask=f.year.eq(yr).to_numpy()
        if mask.any():
            year[str(yr)]=_scores(f.loc[mask],p0[mask],p1[mask])
            year[str(yr)]["partial_calendar_year"]=yr==2025
    pooled["cluster_intervals"]=_pooled_ci(f.loc[keep],p0[keep],p1[keep],B=399)
    return {
        "status":"ACTUAL_INDEPENDENT_2022_2024_SOURCE_HOLDOUT_SCORE_NOT_GENETIC_CAUSATION",
        "old_source_sha256":SOURCE_SHA,
        "new_source_sha256":"7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9",
        "sources":"ayuser 2010-2021 original; KBlueLeaf SQLite from 1990-2025",
        "original_training_accepted_horses":qa["analysis_horses"],
        "original_training_accepted_rows":qa["analysis_rows"],
        "identity_gate":{k:identity[k] for k in (
            "two_event_anchor_horses","new_names_with_multiple_ids",
            "old_names_with_multiple_ids","independent_future_rows_on_anchors",
            "only_pre2022_results_used_for_anchoring")},
        "training_calendar_years":[x[0] for x in training],
        "last_original_history_date":str(end.date()),
        "model_training_rows":len(features),
        "model_features":{
            "no_kin":list(FEATURE_NO_KIN),"with_kin":list(FEATURE_KIN),
            "ridge_alpha_fixed":RIDGE_ALPHA,
            "source_invariant_only":True,
        },
        "new_source_raw_anchored_events":identity["independent_future_rows_on_anchors"],
        "new_source_event_quality":dict(event_qa),
        "eligible_2022_2025_source_rows":len(f),
        "eligible_source_distinct_horses":int(f.horse.nunique()),
        "pooled_full_2022_2024":pooled,
        "by_year":year,
        "source_original_rights":"redistribution licence unknown",
        "source_new_underlying_rights":"unverified despite apache-2.0 dataset label",
        "no_original_horse_rows_or_identifiers_exported":True,
        "no_future_2022_plus_outcome_used_for_model_training_or_anchoring":True,
        "not_a_full_JRA_NAR_census":True,
        "not_GPS_genomic_G_multigeneration_A_heritability_or_betting":True,
        "limitations":[
            "The 2022+ source's actual horse identity is event-anchored, not official studbook-certified.",
            "The cohort is older surviving horses with >=2 historical matched pre-2022 race dates; not new debutants or all JRA/NAR starters.",
            "Original training normalized rank by classified finishers; independent source uses declared runners, creating a source-outcome mismatch.",
            "Model uses only features shared reliably between sources, not previous trainer/jockey/race-class/odds strong baseline.",
            "Frozen source histories through December 2021; no rolling updates after 2022 starts.",
            "Independent source collection may derive from overlapping original upstream racing websites, despite different dataset releases.",
            "2019-2021 known outcomes were analyzed previously; model specification is post-hoc with respect to those years, but 2022+ results were not used for its training.",
            "No genomic effects or genetic causality can be inferred from direct-parent past-history prediction.",
            "2025 data partial through March 27 and excluded from primary pooled 2022-24 result.",
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--sqlite",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=analyze(args.archive,args.sqlite)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "source_sha256":result.get("new_source_sha256"),
        "identity_gate":result.get("identity_gate"),
        "source_qa":result.get("source_independent_quality"),
        "training_years":result.get("training_calendar_years"),
        "year":result.get("by_year"),
        "pooled":result.get("pooled_full_2022_2024"),
        "source_rights_clear":False,
    },ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
