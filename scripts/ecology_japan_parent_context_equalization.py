#!/usr/bin/env python3
"""Count-equalized paternal/maternal channels for first observed context.
Retrospective source A, same strong baseline and annual horse denominator as PR82.
No claim of genes, causal preference, wagering or independent replication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame
from ecology_japan_sire_context_specificity import SEEDS,_hash_half
from ecology_japan_sire_first_context_assignment import annual_rows,build_baseline,family_features,evaluate,TRAIN_FIRST,ALPHA
from ecology_japan_2022_independent_forward import fit_weighted_ridge,predict_weighted_ridge

DRAW_IDS=tuple(range(8))
SIDES=("sire_id","dam_id")
TEST=(2020,2021)
BOOT=999
MIN_GROUPS=30
SHRINK=8.

def attach_dam(old,a,p):
    m=old[["horse","sire_id","dam_id"]].astype(str).drop_duplicates()
    if m.horse.duplicated().any():
        raise ValueError("HOLD_PARENT_CONFLICT")
    m=m.set_index("horse")
    result=[]
    for t in (a,p):
        t=t.copy()
        if not t.horse.isin(m.index).all():
            raise ValueError("HOLD_PARENT_ID")
        if not np.array_equal(t.horse.map(m.sire_id).to_numpy(),t.sire_id.to_numpy()):
            raise ValueError("HOLD_SIRE_PARITY")
        t["dam_id"]=t.horse.map(m.dam_id)
        result.append(t)
    return result

def donor_profiles(a,year,half):
    h=a.loc[a.year.lt(year)&a.half.ne(half)]
    if h.empty:
        raise ValueError("HOLD_EMPTY_DONORS")
    h=h.groupby(["horse","sire_id","dam_id"],observed=True,sort=True)["first"].mean().reset_index()
    if h.horse.duplicated().any() or not h["first"].between(0,1).all():
        raise ValueError("HOLD_DONOR_PROFILE")
    return h

def side_arrays(h,t,side,k,seed,year,half,draw):
    """Equal-count prefix of outcome-blind SHA-ranked unique donor IDs.
    All targets with the same parent/half/year share the same sampled prefix.
    """
    sums=np.zeros(len(t))
    n=np.zeros(len(t),dtype=int)
    for parent,inds in t.groupby(side,observed=True,sort=False).indices.items():
        if not parent:
            continue
        q=h.loc[h[side].eq(parent),["horse","first"]]
        if q.empty:
            continue
        ix=np.asarray(inds,dtype=int)
        scores=q["first"].to_numpy(float)
        n[ix]=len(q)
        if draw is None:
            sums[ix]=scores.sum()
        else:
            order=sorted(range(len(q)),key=lambda j:hashlib.sha256(
                f"{seed}|{year}|{half}|{draw}|{side}|{parent}|{q.horse.iloc[j]}".encode()).digest())
            prefix=np.r_[0.,np.cumsum(scores[order])]
            if (k[ix]>len(q)).any():
                raise ValueError("HOLD_EQUAL_COUNT_OVERFLOW")
            sums[ix]=prefix[k[ix]]
    return n,sums

def make_features(a,p,seed,draw):
    a=a.copy();q=p.copy().reset_index(drop=True)
    a["half"]=_hash_half(a.horse,seed,"horse")
    q["half"]=_hash_half(q.horse,seed,"horse")
    out=np.zeros((len(q),7),float)
    for year in range(TRAIN_FIRST,2022):
        for half in (0,1):
            ix=np.flatnonzero(q.year.eq(year).to_numpy()&q.half.eq(half).to_numpy())
            if not len(ix):
                continue
            t=q.iloc[ix].reset_index(drop=True)
            h=donor_profiles(a,year,half)
            if set(h.horse)&set(t.horse):
                raise ValueError("HOLD_HORSE_OVERLAP")
            zero=np.zeros(len(t),dtype=int)
            ns,ss=side_arrays(h,t,"sire_id",zero,seed,year,half,None)
            nd,sd=side_arrays(h,t,"dam_id",zero,seed,year,half,None)
            k=np.minimum(ns,nd)
            es,ps=side_arrays(h,t,"sire_id",k,seed,year,half,draw)
            ed,pd_=side_arrays(h,t,"dam_id",k,seed,year,half,draw)
            if not np.array_equal(ns,es) or not np.array_equal(nd,ed):
                raise ValueError("HOLD_PEER_COUNT")
            mu=float(h["first"].mean())
            out[ix,:]=np.column_stack((ns,nd,k,
                (ss-ns*mu)/(ns+SHRINK),(sd-nd*mu)/(nd+SHRINK),
                (ps-k*mu)/(k+SHRINK),(pd_-k*mu)/(k+SHRINK)))
    for j,name in enumerate(("ns","nd","k","full_s","full_d","equal_s","equal_d")):
        q[name]=out[:,j]
    for col in ("ns","nd","k"):
        q["log_"+col]=np.log1p(q[col])
    for name in ("full_s","full_d","equal_s","equal_d"):
        q[name+"_own"]=q[name]*q.eligible_known
        q[name+"_count"]=q[name]*q.eligible_log_n
    if not np.isfinite(out).all() or not (q.k<=q.ns).all() or not (q.k<=q.nd).all():
        raise ValueError("HOLD_NONFINITE_SUPPORT")
    if not np.allclose(q.loc[q.k.eq(0),["equal_s","equal_d"]],0):
        raise ValueError("HOLD_ZERO_COUNT_SIGNAL")
    return q

def fit_draw(q,base,year):
    blocks={}
    c=base+("log_ns","log_nd","log_k")
    def block(name):
        return (name,name+"_own",name+"_count")
    cols={"C":c,"FS":c+block("full_s"),"FD":c+block("full_d"),
          "ES":c+block("equal_s"),"ED":c+block("equal_d"),
          "EB":c+block("equal_s")+block("equal_d")}
    out=[]
    for half in (0,1):
        train=q.loc[q.year.lt(year)&q.half.ne(half)]
        t=q.loc[q.year.eq(year)&q.half.eq(half)].copy()
        if train.empty or t.empty or set(train.horse)&set(t.horse):
            raise ValueError("HOLD_MODEL_SPLIT")
        for key,names in cols.items():
            mod=fit_weighted_ridge(train,train["first"],train.horse,names,alpha=ALPHA)
            pred=predict_weighted_ridge(mod,t)
            t[key]=(t["first"].to_numpy(float)-pred)**2
        out.append(t[["horse","sire_id","dam_id","ns","nd","k","no_eligible_before_year","cold_at_entry_raw",*cols]])
    t=pd.concat(out).sort_values("horse").reset_index(drop=True)
    if len(t)!=int(q.year.eq(year).sum()) or t.horse.duplicated().any():
        raise ValueError("HOLD_SCORE_DENOMINATOR")
    return t

def cluster_ci(t,d,side,seed):
    # Separate parent cluster sensitivities; missing parents are singletons.
    group=t[side].astype(str).where(t[side].ne(""),"missing:"+t.horse.astype(str))
    x=pd.DataFrame({"g":group.to_numpy(),"d":np.asarray(d,float)}).groupby("g").d.agg(["sum","size"]).to_numpy(float)
    n=len(x)
    if n<MIN_GROUPS:
        return {"groups":n,"status":"HOLD_FEW_GROUPS"}
    rng=np.random.default_rng(seed)
    b=x[rng.integers(n,size=(BOOT,n))].sum(axis=1)
    return {"groups":n,"CI95_pointwise":np.quantile(b[:,0]/b[:,1],[.025,.975]).tolist()}

def score(t,seed):
    if t.empty:
        return {"status":"HOLD_EMPTY","horses":0}
    models=("C","FS","FD","ES","ED","EB")
    out={"horses":len(t),"sires":int(t.sire_id.nunique()),"known_dams":int(t.loc[t.dam_id.ne(""),"dam_id"].nunique()),
         "RMSE":{k:float(np.sqrt(t[k].mean())) for k in models},
         "mean_sire_peers":float(t.ns.mean()),"mean_dam_peers":float(t.nd.mean()),"mean_equal_peers":float(t.k.mean()),
         "contrasts":{}}
    for a,b in (("C","FS"),("C","FD"),("C","ES"),("C","ED"),("C","EB"),("FD","FS"),("ED","ES"),("ES","EB"),("ED","EB")):
        d=t[a].to_numpy()-t[b].to_numpy()
        out["contrasts"][a+"_minus_"+b]={"MSE_gain":float(d.mean()),
            "sire":cluster_ci(t,d,"sire_id",seed),"dam":cluster_ci(t,d,"dam_id",seed)}
    return out

def combine_draws(tables):
    t=tables[0].copy()
    models=["C","FS","FD","ES","ED","EB"]
    for q in tables[1:]:
        pd.testing.assert_frame_equal(t.drop(columns=models),q.drop(columns=models))
    t[models]=np.mean([q[models].to_numpy(float) for q in tables],axis=0)
    return t

def analyze(archive):
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:
            raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw)
    if len(old)!=2092836 or old.horse.nunique()!=90962:
        raise ValueError("HOLD_SOURCE_PARITY")
    old["stratum"]=old.surface.astype(str)+":"+(old.distance//400).astype(int).astype(str)
    a=annual_rows(old)
    p,base=build_baseline(old,a,raw)
    n=p.loc[p.year.isin((2019,2020,2021))].groupby("year").size().to_dict()
    if n!={2019:7265,2020:7381,2021:7276}:
        raise ValueError("HOLD_PR82_DENOMINATOR")
    # Reproduce frozen primary PR82 before interpreting any new contrast.
    q,kin=family_features(a,p,SEEDS[0],"first")
    parity=evaluate(q,base,kin,"first",2021,SEEDS[0])["all"]
    if abs(parity["C_minus_F"]["MSE_gain"]-.013750704256089798)>1e-10:
        raise ValueError("HOLD_PR82_SCORE_PARITY")
    a,p=attach_dam(old,a,p)
    results={}
    for seed in SEEDS:
        fits={y:[] for y in TEST}
        for draw in DRAW_IDS:
            q=make_features(a,p,seed,draw)
            for y in TEST:
                fits[y].append(fit_draw(q,base,y))
        results[str(seed)]={}
        for y in TEST:
            t=combine_draws(fits[y])
            masks={"all":np.ones(len(t),bool),"equal_supported":t.k.gt(0),
                   "both_min3":t.k.ge(3),"no_eligible_prior":t.no_eligible_before_year,
                   "raw_first":t.cold_at_entry_raw,
                   "raw_first_equal_supported":t.cold_at_entry_raw&t.k.gt(0)}
            results[str(seed)][str(y)]={"groups":{k:score(t.loc[v],seed) for k,v in masks.items()},
                "zero_equal_support":int(t.k.eq(0).sum()),"missing_dam_rows":int(t.dam_id.eq("").sum()),
                "draw_specific_supported_ED_minus_ES_MSE":[float((r.loc[r.k.gt(0),"ED"]-r.loc[r.k.gt(0),"ES"]).mean()) if r.k.gt(0).any() else None for r in fits[y]]}
    return {"status":"RETROSPECTIVE_PARENT_CHANNEL_COUNT_EQUALIZATION",
            "source_A_sha256":SOURCE_SHA,"PR82_primary_parity":parity["C_minus_F"]["MSE_gain"],
            "primary":"20261124/2021/equal_supported/ED_minus_ES",
            "draws":list(DRAW_IDS),"results":results,
            "limitations":["Already inspected historical years; no prospective replication.",
             "Equal numbers of distinct observed parent-sharing horses, not equal relatedness, chronology, management, measurement precision or effective information.",
             "Same horse may belong to both parent pools; shared environments and deeper pedigree remain.",
             "Model re-estimation can change zero-support predictions despite zero equalized signals.",
             "Average squared losses over eight fixed subsamples, not eight independent experiments or loss of averaged predictions.",
             "Separate sire/dam pointwise bootstrap sensitivities are not joint or simultaneous intervals.",
             "Observed entry context, not physiological adaptation, choice or official debut; no betting or individual outputs."]}

def self_test():
    h=pd.DataFrame({"horse":["a","b","c","d"],"sire_id":["S","S","S","T"],
                    "dam_id":["A","A","B","A"],"first":[1.,0.,1.,0.]})
    t=pd.DataFrame({"horse":["new"],"sire_id":["S"],"dam_id":["B"]})
    z=np.array([0]);ns,ss=side_arrays(h,t,"sire_id",z,1,2021,0,None)
    nd,sd=side_arrays(h,t,"dam_id",z,1,2021,0,None)
    assert ns[0]==3 and nd[0]==1 and ss[0]==2 and sd[0]==1
    k=np.minimum(ns,nd)
    n,a=side_arrays(h,t,"sire_id",k,1,2021,0,0)
    m,b=side_arrays(h,t,"dam_id",k,1,2021,0,0)
    assert n[0]==3 and m[0]==1 and a[0] in (0,1) and b[0]==1
    assert np.array_equal(a,side_arrays(h.sample(frac=1,random_state=2),t,"sire_id",k,1,2021,0,0)[1])
    hh=h.copy();hh["first"]=1-hh["first"]
    assert np.array_equal(k-a,side_arrays(hh,t,"sire_id",k,1,2021,0,0)[1])
    assert side_arrays(h,t.assign(dam_id=""),"dam_id",z,1,2021,0,0)[0][0]==0
    print("synthetic equal-count, order, outcome-blind sample and missing-parent checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not a.archive or not a.output:
        p.error("archive and output required")
    r=analyze(a.archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    compact={s:{y:{"groups":{k:v for k,v in q["groups"].items() if k in ("all","equal_supported","raw_first_equal_supported")},"zero_equal_support":q["zero_equal_support"],"missing_dam_rows":q["missing_dam_rows"],"draw_specific_supported_ED_minus_ES_MSE":q["draw_specific_supported_ED_minus_ES_MSE"]} for y,q in v.items()} for s,v in r["results"].items()}
    print(json.dumps({"status":r["status"],"primary":r["primary"],"PR82_primary_parity":r["PR82_primary_parity"],"results":compact},allow_nan=False))

if __name__=="__main__":
    main()
