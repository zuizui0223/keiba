#!/usr/bin/env python3
"""Season-matched retrospective 2025 allocation transfer and identity audit.

2025 through March 27 only; not new-entrant or prospective validation.
No individual source records exported.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from ecology_japan_2022_parent_placebo import load_sources,SQLITE_SHA
from ecology_japan_2022_joint_strict_strong import strict_mask_exact_horse_race
from ecology_japan_2022_denominator_audit import audit_race_entries
from ecology_japan_2022_independent_forward import parse_independent_history
from ecology_japan_hf_event_anchor_gate import anchor_name_histories
from ecology_japan_hf_sqlite_source_gate import normalize_date,parse_horse_history
from ecology_japan_archive_forward import SOURCE_SHA
from ecology_japan_sire_context_specificity import CONTEXTS,SEEDS,_hash_half
from ecology_japan_sire_context_exposure_transfer import historical_panel,OWN_SHRINK
from ecology_japan_context_occupancy_independent import audit_circuits,target_occupancy,source_a_baseline
from ecology_japan_context_occupancy_refresh import update_own,predictions
from ecology_japan_context_information_substitution import calibration,fit_weights,apply_weights,groups
from ecology_japan_sire_context_time_transfer import predict_fold
from ecology_japan_context_within_individual import same

YEARS=(2022,2023,2024,2025)
END_MMDD=327
MIN_HORSES=100
MIN_SIRES=30

def season_mask(day):
    return (day.dt.month*100+day.dt.day).le(END_MMDD)

def source_2025(raw,old,db,circuit,n_anchors):
    """Audit the new seasonal denominator before restricting to A identities.

    All B horse-history records in eligible 2025 races define candidates.
    Strict consistency uses unanimous declared N and exact race-table rank.
    It does not certify official entries or native pedigree identities.
    """
    parent=old[["horse","sire_id","dam_id"]].astype(str).drop_duplicates()
    if parent.horse.duplicated().any():
        raise ValueError("HOLD_PARENT_CONFLICT")
    parent=parent.set_index("horse")
    con=sqlite3.connect(f"file:{db}?mode=ro",uri=True)
    try:
        meta={str(rid):(date,dist,surf) for rid,date,dist,surf in con.execute(
            "SELECT rid,date,distance,course FROM race")}
        cal={k:v[0] for k,v in meta.items()}
        dates=[d for d in map(normalize_date,cal.values()) if d]
        if max(dates)!="20250327":
            raise ValueError("HOLD_SOURCE_DATE")
        def records():
            return con.execute("SELECT hid,name,races FROM horse")
        cw,gate=anchor_name_histories(raw[["horse_id","horse_name","date","place","distance"]],records,race_dates=cal)
        if len(cw)!=n_anchors or len(set(cw.values()))!=len(cw):
            raise ValueError("HOLD_ANCHOR_PARITY")
        idx={}
        for rid,(date,dist,surf) in meta.items():
            d=normalize_date(date)
            if not d or not ("20250101"<=d<="20250327") or circuit.get(rid)!="JRA":
                continue
            try:
                dd=int(dist);ss=int(surf)
            except (TypeError,ValueError,OverflowError):
                continue
            if 1600<=dd<=1999 and ss in (0,1):
                idx[rid]=(date,dd,ss)
        if not idx:
            raise ValueError("HOLD_EMPTY_2025_RACES")
        events=[];first_season=set()
        for hid,_,history in records():
            e,_=parse_independent_history(history,idx)
            if not e:
                continue
            hid=str(hid)
            # This is earliest valid dated record in B history, not debut.
            previous=parse_horse_history(history,race_dates=cal)
            if previous and min(x[0] for x in previous)>="20250101":
                first_season.add(hid)
            for x in e:
                events.append({**x,"native_horse":hid,"race":x["race_id"]})
        if not events:
            raise ValueError("HOLD_EMPTY_2025_EVENTS")
        f=pd.DataFrame(events)
        if f.duplicated(["race","native_horse"]).any():
            raise ValueError("HOLD_DUPLICATE_2025_HISTORY")
        fields=f.groupby("race",observed=True).source_declared_field_size.agg(["size","nunique","first"])
        strict_ranks={};status=Counter()
        for rid,raw_horses in con.execute("SELECT rid,horses FROM race WHERE substr(date,1,4)='2025'"):
            rid=str(rid)
            if rid not in idx:
                continue
            if rid not in fields.index:
                status["NO_VALID_HORSE_HISTORY"]+=1;continue
            if fields.loc[rid,"nunique"]!=1:
                status["CONFLICTING_DECLARED_N"]+=1;continue
            q,ranks=audit_race_entries(raw_horses,int(fields.loc[rid,"first"]))
            status[q["status"]]+=1
            if q["status"]=="STRICT_COMPLETE_CLASSIFIED_RACE":
                strict_ranks[rid]=ranks
        if sum(status.values())!=len(idx):
            raise ValueError("HOLD_RACE_SCOPE")
        okay=[]
        for x in f.itertuples(index=False):
            rank=strict_ranks.get(x.race,{}).get(x.native_horse)
            okay.append(rank is not None and np.isclose(rank,1+x.y*(x.source_declared_field_size-1),atol=1e-9))
        strict=f.loc[okay].copy()
        # All evaluated ranks/horse identities come from the same native DB.
        strict["horse"]=strict.native_horse.map(cw)
        anchored=strict.loc[strict.horse.notna()].copy()
        anchored["sire_id"]=anchored.horse.map(parent.sire_id)
        anchored["dam_id"]=anchored.horse.map(parent.dam_id)
        if anchored[["sire_id","dam_id"]].isna().any().any():
            raise ValueError("HOLD_UNJOINED_ANCHOR_PARENT")
        col=[v[1] for v in con.execute("PRAGMA table_info(horse)")]
        direct_parent_cols=[c for c in col if c.lower() in {
            "sire_id","dam_id","father_id","mother_id","sire_hid","dam_hid","father_hid","mother_hid"}]
        def counts(t):
            return {"starts":len(t),"native_horses":int(t.native_horse.nunique()),
                "first_valid_B_record_in_2025_horses":int(t.loc[t.native_horse.isin(first_season)].native_horse.nunique())}
        qa={"source_date_max":max(dates),"eligible_races":len(idx),"race_status":dict(status),
            "candidate":counts(f),"strict_exact":counts(strict),"anchored":counts(anchored),
            "anchored_known_sire":counts(anchored.loc[anchored.sire_id.ne("")]),
            "unanchored_strict":counts(strict.loc[strict.horse.isna()]),
            "horse_table_columns":col,"explicit_direct_parent_id_columns":direct_parent_cols,
            "native_parent_identity_verified":False,
            "strict_race_entries_missing_valid_matching_history":int(sum(len(v) for v in strict_ranks.values())-len(strict))}
        if qa["strict_race_entries_missing_valid_matching_history"]<0:
            raise ValueError("HOLD_RACE_HISTORY_COUNT")
        return anchored.drop(columns="native_horse"),qa
    finally:
        con.close()

def season_target(f,circuit=None):
    x=f.loc[season_mask(f.day)].copy()
    if circuit is not None:
        x["circuit"]=x.race.astype(str).map(circuit).fillna("UNKNOWN")
    x=x.loc[x.circuit.eq("JRA")&x.stratum.isin(CONTEXTS)&x.sire_id.astype(str).ne("")].copy()
    for c in ("horse","sire_id"):
        x[c]=x[c].astype(str)
    x["turf"]=x.surface.eq("turf").astype(float)
    t=x.groupby(["horse","sire_id","year"],observed=True).turf.agg(["mean","size"]).reset_index()
    t=t.rename(columns={"mean":"occupancy","size":"starts"})
    if t.duplicated(["horse","year"]).any():
        raise ValueError("HOLD_SEASON_IDENTITY")
    return t

def seasonalize(full,season):
    """Use full-year history-derived predictors; replace only target response."""
    keys=["horse","sire_id","year"]
    q=full.drop(columns=["occupancy","starts","target_starts"],errors="ignore").merge(
        season,on=keys,how="inner",validate="one_to_one")
    if len(q)!=len(season):
        raise ValueError("HOLD_SEASON_JOIN")
    return q

def append_2025(old,b,t,seed):
    """Full 2022-24 observed eligible history, no 2025 inputs in priors."""
    if not b.year.lt(2025).all() or not t.year.eq(2025).all():
        raise ValueError("HOLD_TIME")
    x=old.loc[old.circuit.eq("JRA")&old.stratum.isin(CONTEXTS)&old.sire_id.astype(str).ne(""),
        ["horse","surface"]].copy()
    x["horse"]=x.horse.astype(str);x["half"]=_hash_half(x.horse,seed,"horse")
    x["turf"]=x.surface.eq("turf").astype(float)
    a=x.groupby(["horse","half"],observed=True).turf.agg(["mean","sum","size"]).reset_index()
    prior=a.groupby("half",observed=True)["mean"].mean()
    a=a.set_index("horse")
    earlier=b.copy()
    earlier["turf_starts"]=earlier.occupancy*earlier.starts
    v=earlier.groupby("horse",observed=True).agg(n=("starts","sum"),s=("turf_starts","sum"))
    q=source_a_baseline(old,t,seed)
    n=q.own_prior_count.to_numpy(float)+q.horse.map(v.n).fillna(0).to_numpy(float)
    s=q.horse.map(a["sum"]).fillna(0).to_numpy(float)+q.horse.map(v.s).fillna(0).to_numpy(float)
    g=q.half.map(prior).to_numpy(float)
    if not np.isfinite(g).all() or (s<0).any() or (s>n+1e-9).any():
        raise ValueError("HOLD_REFRESH_COUNTS")
    q["base_refreshed"]=(s+OWN_SHRINK*g)/(n+OWN_SHRINK)
    q["refreshed_own_n"]=n.astype(int)
    return q

def season_calibration(a,seed):
    blocks=[]
    for yr in (2020,2021):
        for half in (0,1):
            t=a.loc[a.year.eq(yr)&a.half.eq(half)].copy()
            h=a.loc[a.year.lt(yr)&a.half.ne(half)].copy()
            h["difference"]=h.occupancy-h.base_own
            p,_=predict_fold(h,t[["horse","sire_id","year","half"]],seed)
            p=p.set_index("horse").reindex(t.horse)
            t["r"]=t.occupancy.to_numpy()-t.base_own.to_numpy()-p.M0.to_numpy()
            t["d"]=p.M1.to_numpy()-p.M0.to_numpy()
            if not np.isfinite(t[["r","d"]]).all().all():
                raise ValueError("HOLD_SEASON_CALIBRATION_JOIN")
            blocks.append(t)
    return pd.concat(blocks,ignore_index=True)

def support(t):
    return {"horses":len(t),"sires":int(t.sire_id.nunique()),"starts":int(t.starts.sum())}

def analyze(archive,db):
    raw,old,future,_,gate,_=load_sources(archive,db)
    if len(old)!=2092836 or old.horse.nunique()!=90962 or len(future)!=255484 or future.horse.nunique()!=12919:
        raise ValueError("HOLD_SOURCE_PARITY")
    circuit,cqa=audit_circuits(raw,old,db,gate["two_event_anchor_horses"])
    if cqa.get("verified_JRA_codes")!=10 or cqa.get("verified_NAR_codes")!=14 or cqa["matched_distinct_pre2022_source_B_races"]!=85856:
        raise ValueError("HOLD_VENUE_PARITY")
    mask,sqa=strict_mask_exact_horse_race(raw,future,db,gate["two_event_anchor_horses"])
    strict=future.loc[mask].copy()
    if len(strict)!=244147 or strict.horse.nunique()!=12887:
        raise ValueError("HOLD_STRICT_PARITY")
    t,_=target_occupancy(strict,circuit)
    if t.groupby("year",observed=True).size().to_dict()!={2022:3011,2023:1588,2024:743}:
        raise ValueError("HOLD_TARGET_PARITY")
    late,lqa=source_2025(raw,old,db,circuit,gate["two_event_anchor_horses"])
    a_season=season_target(old.loc[old.year.isin([2019,2020,2021])])
    b_season=season_target(strict,circuit)
    c_season=season_target(late,circuit)
    result={"status":"RETROSPECTIVE_2025_SEASONAL_ALLOCATION_TRANSFER",
        "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
        "primary":"20261124/2025/season_calibrated/refreshed/all/N_minus_G",
        "window":"January 1–March 27 inclusive each year",
        "source_2025_gate":lqa,
        "season_support":{str(y):support(x) for y,x in pd.concat([a_season,b_season,c_season]).groupby("year",observed=True)},
        "results":{},"limitations":["2025 season not full year; same B source previously inspected for ranks, not prospective.",
            "Only pre-2022 event-anchored horses can receive A parent IDs; native parent identity not verified; first recorded B season not official debut.",
            "Target conditional on observed strict starts, not complete eligibility or choice. No current-season label in history.",
            "No genetic, learning, physiological or fitness inference. Conditional pointwise sire intervals, dependent splits.",
            "Season-specific calibration can HOLD on prespecified support. Annual-trained gate is separate sensitivity, not replacement primary."]}
    if c_season.empty:
        result["status"]="HOLD_NO_ANCHORED_2025_TARGETS";return result
    for seed in SEEDS:
        a=historical_panel(old,seed,False)
        b=update_own(old,source_a_baseline(old,t,seed),seed)
        # Original annual PR87 and PR86 parity before any season scoring.
        if seed==SEEDS[0]:
            p=predictions(a,b,2024,seed)
            same(np.mean((p.occupancy-p.B11)**2-(p.occupancy-p.M11)**2),-.009304296089139295,"PR86")
        annual_cal=calibration(a,seed)
        annual_weights={str(k):fit_weights(annual_cal,k,2022) for k in (0,1)}
        aa=seasonalize(a,a_season)
        bb=seasonalize(b,b_season)
        cc=append_2025(old,b,c_season,seed)
        z=pd.concat([bb,cc],ignore_index=True)
        if z.duplicated(["horse","year"]).any():
            raise ValueError("HOLD_SEASON_PANEL")
        cal=season_calibration(aa,seed)
        try:
            weights={str(k):fit_weights(cal,k,2022) for k in (0,1)}
            state="EVALUATED"
        except ValueError as e:
            if str(e)!="HOLD_CALIBRATION_BIN_SUPPORT":
                raise
            weights=None;state=str(e)
        q={"season_weights_status":state,"season_weights":weights,"annual_weights":annual_weights,"years":{}}
        for yr in YEARS:
            if not z.year.eq(yr).any():
                q["years"][str(yr)]={"status":"HOLD_EMPTY"};continue
            p=predictions(aa,z,yr,seed)
            out={}
            for st,base,full,n in (("stale","B00","M00","own_prior_count"),
                                  ("refreshed","B11","M11","refreshed_own_n")):
                v=apply_weights(p,base,full,n,annual_weights)
                out[st]={"annual_gate_on_season_profile":groups(v,seed)}
                if weights is not None:
                    out[st]["season_calibrated"]=groups(apply_weights(p,base,full,n,weights),seed)
                else:
                    out[st]["season_calibrated"]={"status":state}
            q["years"][str(yr)]=out
        result["results"][str(seed)]=q
    return result

def self_test():
    dates=pd.Series(pd.to_datetime(["2024-03-27","2024-03-28","2024-01-01","2025-03-27","2025-12-31"]))
    assert season_mask(dates).tolist()==[True,False,True,True,False]
    a=pd.DataFrame({"horse":["a","b"],"sire_id":["s","s"],"year":[2022,2022],
        "occupancy":[.7,.2],"starts":[10,5],"base_own":[.4,.3],"refreshed_own_n":[4,0]})
    b=pd.DataFrame({"horse":["a"],"sire_id":["s"],"year":[2022],"occupancy":[.5],"starts":[2]})
    x=seasonalize(a,b)
    assert len(x)==1 and x.occupancy.iloc[0]==.5 and x.base_own.iloc[0]==.4
    assert x.refreshed_own_n.iloc[0]==4 and x.starts.iloc[0]==2
    assert a.occupancy.iloc[0]==.7
    print("synthetic season cutoff and preservation of full-history predictors passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path);p.add_argument("--sqlite",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.archive,a.sqlite,a.output)):
        p.error("archive, sqlite and output required")
    z=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    # Print only aggregate all-target results and fitted weights; full artifact
    # retains all count-bin results. No individual records.
    compact={k:v for k,v in z.items() if k!="results"}
    compact["results"]={}
    for s,v in z["results"].items():
        q={k:x for k,x in v.items() if k!="years"}
        q["years"]={}
        for yr,g in v["years"].items():
            if "status" in g:
                q["years"][yr]=g;continue
            q["years"][yr]={st:{model:out.get("all",out) for model,out in x.items()} for st,x in g.items()}
        compact["results"][s]=q
    print(json.dumps(compact,allow_nan=False))

if __name__=="__main__":
    main()
