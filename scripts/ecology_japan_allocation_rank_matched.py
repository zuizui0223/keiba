#!/usr/bin/env python3
"""Matched horse-year surface allocation versus relative finishing performance.

Same source-locked starts, same target horses, same family/own history rules.
No prediction of physiological speed, causation, or wagering. Aggregate only.
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_2022_joint_strict_strong import strict_mask_exact_horse_race
from ecology_japan_archive_forward import SOURCE_SHA
from ecology_japan_sire_context_specificity import CONTEXTS,SEEDS,_hash_half
from ecology_japan_context_occupancy_independent import audit_circuits,target_occupancy,source_a_baseline
from ecology_japan_context_occupancy_refresh import source_a_reference,update_own,predictions
from ecology_japan_context_within_individual import frame
from ecology_japan_sire_context_time_transfer import predict_fold

TRAITS=("turf","rank")
YEARS=(2022,2023,2024)
SHRINK=5.
MIN_HORSES=100
MIN_SIRES=30
DRAWS=999

def same(a,b,label):
    if not np.allclose(a,b,atol=1e-10,rtol=0):
        raise ValueError("HOLD_"+label)

def eligible(a,circuit=None):
    x=a.copy()
    if circuit is not None:
        x["circuit"]=x.race.astype(str).map(circuit).fillna("UNKNOWN")
    x=x.loc[x.circuit.eq("JRA")&x.stratum.isin(CONTEXTS)&x.sire_id.astype(str).ne(""),
            ["horse","sire_id","year","day","race","surface","y"]].copy()
    for k in ("horse","sire_id","race"):
        x[k]=x[k].astype(str)
    if x.duplicated(["horse","race"]).any() or x.horse.eq("").any() or x.sire_id.eq("").any():
        raise ValueError("HOLD_ELIGIBLE_KEYS")
    if x.groupby("horse",observed=True).sire_id.nunique().max()>1 or not x.y.between(0,1).all():
        raise ValueError("HOLD_PARENT_OR_RANK")
    x["turf"]=x.surface.eq("turf").astype(float)
    x["rank"]=x.y.astype(float)
    return x[["horse","sire_id","year","day","race","turf","rank"]]

def annual(x,seed):
    x=x.copy()
    x["half"]=_hash_half(x.horse,seed,"horse")
    a=x.groupby(["horse","sire_id","half","year"],observed=True).agg(
        turf=("turf","mean"),rank=("rank","mean"),starts=("turf","size")).reset_index()
    if a.duplicated(["horse","year"]).any():raise ValueError("HOLD_ANNUAL_KEYS")
    return a

def prior(x,seed):
    x=x.copy()
    x["half"]=_hash_half(x.horse,seed,"horse")
    h=x.groupby(["horse","half"],observed=True).agg(turf=("turf","sum"),rank=("rank","sum"),n=("turf","size")).reset_index()
    means=h[list(TRAITS)].div(h.n,axis=0)
    means["half"]=h.half
    return h.set_index("horse"),means.groupby("half",observed=True)[list(TRAITS)].mean()

def baselines(target,h,g,earlier=None):
    t=target.copy()
    n=t.horse.map(h.n).fillna(0).to_numpy(float)
    add=np.zeros(len(t)); sums={k:np.zeros(len(t)) for k in TRAITS}
    if earlier is not None and not earlier.empty:
        if earlier.year.max()>=target.year.min():raise ValueError("HOLD_FUTURE_HISTORY")
        e=earlier.copy()
        for k in TRAITS:e[k]=e[k]*e.starts
        e=e.groupby("horse",observed=True).agg(turf=("turf","sum"),rank=("rank","sum"),n=("starts","sum"))
        add=t.horse.map(e.n).fillna(0).to_numpy(float)
        for k in TRAITS:sums[k]=t.horse.map(e[k]).fillna(0).to_numpy(float)
    for k in TRAITS:
        s=t.horse.map(h[k]).fillna(0).to_numpy(float)
        m=t.half.map(g[k]).to_numpy(float)
        t[k+"_stale"]=(s+SHRINK*m)/(n+SHRINK)
        t[k+"_fresh"]=(s+sums[k]+SHRINK*m)/(n+add+SHRINK)
    t["n0"]=n;t["n1"]=n+add
    return t

def fit_scores(a,b,seed):
    ah=annual(a,seed);bh=annual(b,seed)
    hist=[]
    for yr in (2019,2020,2021):
        h,g=prior(a.loc[a.year.lt(yr)],seed)
        hist.append(baselines(ah.loc[ah.year.eq(yr)],h,g))
    train=pd.concat(hist,ignore_index=True)
    h,g=prior(a,seed)
    out=[]
    for yr in YEARS:
        t=baselines(bh.loc[bh.year.eq(yr)],h,g,bh.loc[bh.year.lt(yr)])
        for half in (0,1):
            q=t.loc[t.half.eq(half)].copy()
            donors=train.loc[train.half.ne(half)].copy()
            for k in TRAITS:
                donors["difference"]=donors[k]-donors[k+"_stale"]
                p,_=predict_fold(donors,q,seed)
                p=p.set_index("horse").reindex(q.horse)
                q[k+"_B"]=q[k+"_stale"].to_numpy()+p.M0.to_numpy()
                q[k+"_d"]=(p.M1-p.M0).to_numpy()
                q[k+"_u"]=q[k+"_fresh"]-q[k+"_stale"]
                q[k+"_g0"]=2*(q[k]-q[k+"_B"])*q[k+"_d"]-q[k+"_d"]**2
                q[k+"_g1"]=q[k+"_g0"]-2*q[k+"_u"]*q[k+"_d"]
                same(q[k+"_g1"],(q[k]-q[k+"_B"]-q[k+"_u"])**2-(q[k]-q[k+"_B"]-q[k+"_u"]-q[k+"_d"])**2,"GAIN_IDENTITY")
                if k=="turf":q["support"]=p.n.to_numpy()
                else:same(q.support,p.n,"TRAIT_DONOR_PARITY")
            out.append(q)
    x=pd.concat(out,ignore_index=True)
    # A2021 annual horse-equal variance, independent of B outcomes, fixed scaling.
    scale=ah.loc[ah.year.eq(2021),list(TRAITS)].var(ddof=0).to_dict()
    if any(not np.isfinite(v) or v<=1e-12 for v in scale.values()):
        raise ValueError("HOLD_A_SCALE")
    return x,scale

def paired(x,scale,seed):
    a=x.loc[x.year.eq(2022)].set_index("horse");b=x.loc[x.year.eq(2024)].set_index("horse")
    ids=a.index.intersection(b.index)
    a=a.loc[ids];b=b.loc[ids]
    if not a.sire_id.equals(b.sire_id):raise ValueError("HOLD_SIRE")
    n=len(a);ns=a.sire_id.nunique()
    if n<MIN_HORSES or ns<MIN_SIRES:return {"status":"HOLD_SUPPORT","horses":n,"sires":int(ns)}
    z={};effects={}
    for k in TRAITS:
        same(a[k+"_B"],b[k+"_B"],"FIXED_B")
        same(a[k+"_d"],b[k+"_d"],"FIXED_D")
        du=-2*a[k+"_d"]*(b[k+"_u"]-a[k+"_u"])
        dy=2*a[k+"_d"]*(b[k]-a[k])
        same(b[k+"_g1"]-a[k+"_g1"],du+dy,"TEMPORAL_IDENTITY")
        effects[k]=np.column_stack((a[k+"_g1"],du,dy,b[k+"_g1"]))
        z[k]={"raw_means":effects[k].mean(axis=0).tolist(),
              "scaled_means":(effects[k].mean(axis=0)/scale[k]).tolist(),
              "A2021_variance":float(scale[k]),
              "correction_rms":float(np.sqrt(np.mean(a[k+"_d"]**2))),
              "update_rms":float(np.sqrt(np.mean((b[k+"_u"]-a[k+"_u"])**2)))}
    # Two primary contrasts: initial gain and within-horse own-update term.
    e=effects["turf"]/scale["turf"]-effects["rank"]/scale["rank"]
    m=e[:,[0,1]]
    q=pd.DataFrame(m,columns=["initial","update"]);q["sire"]=a.sire_id.to_numpy();q["n"]=1
    p=q.groupby("sire",observed=True)[["initial","update","n"]].sum().to_numpy()
    rng=np.random.default_rng(seed+19)
    samples=p[rng.integers(len(p),size=(DRAWS,len(p)))].sum(axis=1)
    rep=samples[:,:2]/samples[:,2,None]
    return {"status":"OBSERVED_MATCHED","horses":n,"sires":int(ns),
        "metric_order":["2022_gain","own_update","observed_outcome_shift","2024_gain"],
        "traits":z,"contrasts":["turf_minus_rank_initial_scaled_gain","turf_minus_rank_scaled_own_update"],
        "contrast_means":m.mean(axis=0).tolist(),"conditional_97_5_intervals":np.quantile(rep,[.0125,.9875],axis=0).T.tolist()}

def analyze(archive,db):
    raw,old,future,_,gate,_=load_sources(archive,db)
    if len(old)!=2092836 or old.horse.nunique()!=90962 or len(future)!=255484 or future.horse.nunique()!=12919:
        raise ValueError("HOLD_SOURCE_PARITY")
    circuit,cqa=audit_circuits(raw,old,db,gate["two_event_anchor_horses"])
    if cqa.get("verified_JRA_codes")!=10 or cqa.get("verified_NAR_codes")!=14 or cqa["matched_distinct_pre2022_source_B_races"]!=85856:
        raise ValueError("HOLD_VENUE_PARITY")
    mask,_=strict_mask_exact_horse_race(raw,future,db,gate["two_event_anchor_horses"])
    strict=future.loc[mask]
    if len(strict)!=244147 or strict.horse.nunique()!=12887:raise ValueError("HOLD_STRICT_PARITY")
    target,qa=target_occupancy(strict,circuit)
    if target.groupby("year",observed=True).size().to_dict()!={2022:3011,2023:1588,2024:743}:raise ValueError("HOLD_TARGET_PARITY")
    aa=eligible(old);bb=eligible(strict,circuit)
    if int(target.starts.sum())!=len(bb):raise ValueError("HOLD_START_DENOMINATOR")
    result={}
    for seed in SEEDS:
        x,scale=fit_scores(aa,bb,seed)
        hist,_=source_a_reference(old,seed)
        ref=update_own(old,source_a_baseline(old,target,seed),seed)
        for yr in YEARS:
            r=frame(predictions(hist,ref,yr,seed)).set_index("horse")
            z=x.loc[x.year.eq(yr)].set_index("horse")
            if set(r.index)!=set(z.index):raise ValueError("HOLD_REFERENCE_IDS")
            z=z.loc[r.index]
            for kc,rc in (("turf","occupancy"),("turf_B","B00"),("turf_d","d"),("turf_u","u"),("turf_g1","g_own")):
                same(z[kc],r[rc],"ORIGINAL_OCCUPANCY_PARITY_"+kc)
        result[str(seed)]=paired(x,scale,seed)
        if result[str(seed)]["horses"]!=599 or result[str(seed)]["sires"]!=122:raise ValueError("HOLD_COMMON_PARITY")
    return {"status":"RETROSPECTIVE_MATCHED_ALLOCATION_RANK","source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
        "target_scope":qa,"primary_seed":SEEDS[0],"original_occupancy_parity":True,"results":result,
        "limits":["Shared inspected sources and cohort; not independent replication.",
                  "Rank is mean normalized finishing order among classified eligible starts, not speed or surface-specific performance reaction.",
                  "Allocation is managed realized surface fraction, not voluntary habitat choice.",
                  "Variance normalization from A2021 is fixed; conditional sire bootstrap excludes race, deeper kin, management and fit dependence.",
                  "No causal mechanism, genetic effect or raw records exported."]}

def self_test():
    rows=[]
    for yr in range(2018,2025):
        for i in range(120):
            v=float((i+yr)%3==0)
            rows.append(dict(horse=f"h{i}",sire_id=f"s{i%30}",year=yr,day=pd.Timestamp(f"{yr}-01-01"),
                race=f"{yr}-{i}",turf=v,rank=v))
    t=pd.DataFrame(rows)
    x,sc=fit_scores(t[t.year.lt(2022)],t[t.year.ge(2022)],SEEDS[0])
    r=paired(x,sc,SEEDS[0])
    assert r["horses"]==120 and r["sires"]==30
    same(r["contrast_means"],[0,0],"IDENTICAL_TRAITS")
    same(r["conditional_97_5_intervals"],[[0,0],[0,0]],"IDENTICAL_INTERVALS")
    print("Synthetic matched trait, chronology and fixed correction checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--sqlite",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.sqlite,a.output)):p.error("archive, sqlite and output required")
    r=analyze(a.archive,a.sqlite);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n")
    print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
