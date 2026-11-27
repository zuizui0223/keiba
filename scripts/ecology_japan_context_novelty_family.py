#!/usr/bin/env python3
"""Experienced first meetings in novel vs familiar surface-distance contexts."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import ecology_japan_family_depth_unconstrained as prev

CTX=("ctx_rank","ctx_log_n","ctx_known")
MODELS={**prev.MODELS,"C":prev.BASE+prev.COUNTS+CTX,"V":prev.BASE+prev.COUNTS+CTX+prev.UNATTENUATED}
CONTRASTS=("raw_gain","context_adjusted_gain")
MIN_CELL_PAIRS=20
MIN_CELL_DAYS=10
MIN_COVERAGE=.50

def context_history(t):
    x=t[["id","race","day","surface","distance","y"]].copy()
    x["ctx"]=x.surface.astype(str)+":"+(x.distance.astype(int)//400).astype(str)
    if x.duplicated(["id","race"]).any():raise ValueError("HOLD_CONTEXT_KEY")
    x["quality"]=1-x.y
    d=x.groupby(["id","ctx","day"],observed=True).quality.agg(n="size",s="sum").reset_index()
    d=d.sort_values(["id","ctx","day"],kind="mergesort")
    hist=d.groupby(["id","ctx"],observed=True)[["n","s"]].cumsum()-d[["n","s"]]
    d["ctx_n"]=hist.n;d["ctx_sum"]=hist.s
    if (d.ctx_n<0).any() or (d.ctx_sum< -1e-9).any() or (d.ctx_sum>d.ctx_n+1e-9).any():
        raise ValueError("HOLD_CONTEXT_HISTORY")
    p=(d.ctx_sum+2.5)/(d.ctx_n+5.)
    d["ctx_rating"]=np.log(p/(1-p))
    z=x.merge(d[["id","ctx","day","ctx_n","ctx_rating"]],on=["id","ctx","day"],validate="many_to_one",sort=False)
    if len(z)!=len(x):raise ValueError("HOLD_CONTEXT_COUNT")
    # Same-day rows share the same earlier-day context state.
    return z[["id","race","day","ctx","ctx_n","ctx_rating"]]

def attach(q,ctx):
    q=q.copy();n=len(q)
    for side in ("a","b"):
        ref=ctx.rename(columns={"id":side,"ctx":side+"_ctx","ctx_n":side+"_ctx_n","ctx_rating":side+"_ctx_rating"})
        q=q.merge(ref,on=[side,"race","day"],how="left",validate="many_to_one",sort=False)
    if len(q)!=n or q[["a_ctx_n","b_ctx_n","a_ctx_rating","b_ctx_rating"]].isna().any().any():
        raise ValueError("HOLD_CONTEXT_JOIN")
    if not (q.a_ctx==q.b_ctx).all() or (np.minimum(q.a_ctx_n,q.b_ctx_n)>q.min_starts).any() or (np.maximum(q.a_ctx_n,q.b_ctx_n)>q.max_starts).any():
        raise ValueError("HOLD_CONTEXT_RACE_OR_COUNT")
    q["ctx_rank"]=q.a_ctx_rating-q.b_ctx_rating
    q["ctx_log_n"]=np.log1p(q.a_ctx_n)-np.log1p(q.b_ctx_n)
    q["ctx_known"]=q.a_ctx_n.gt(0).astype(float)-q.b_ctx_n.gt(0).astype(float)
    q["ctx"]=q.a_ctx
    return q

def novelty_panel(t,fits):
    a=t.a_ctx_n.to_numpy();b=t.b_ctx_n.to_numpy()
    novel=((a==0)&(b>=3))|((b==0)&(a>=3))
    familiar=(a>=3)&(b>=3)
    keep=(t.connected&t["first"]&t.min_starts.ge(4)).to_numpy()&(novel|familiar)
    q=t.loc[keep].copy();q["novel"]=novel[keep]
    def depth(n):return np.where(n<=7,"4-7",np.where(n<=15,"8-15","16+"))
    q["cell"]=q.ctx.astype(str)+"|"+depth(q.min_starts.to_numpy())+"|"+depth(q.max_starts.to_numpy())
    y=q.y.to_numpy(float)
    loss={k:(y-prev.predict(q,fits[k]))**2 for k in ("N","U","C","V")}
    q["raw_gain"]=loss["N"]-loss["U"];q["context_adjusted_gain"]=loss["C"]-loss["V"]
    for k,v in loss.items():q["loss_"+k]=v
    return q

def pair_summary(q):
    if q.empty:return {"pairs":0,"days":0,"races":0}
    w=prev.weights(q)
    return {"pairs":len(q),"days":int(q.day.nunique()),"races":int(q.race.nunique()),
        "gain":{k:float(np.average(q[k],weights=w)) for k in CONTRASTS},
        "Brier":{k:float(np.average(q["loss_"+k],weights=w)) for k in ("N","U","C","V")}}

def contrast(t,fits):
    q=novelty_panel(t,fits)
    out={"unmatched":{"novel":pair_summary(q.loc[q.novel]),"familiar":pair_summary(q.loc[~q.novel])}}
    cells=[];details={}
    for k,z in q.groupby("cell",observed=True):
        a=z.loc[z.novel];b=z.loc[~z.novel]
        if min(a.key.nunique(),b.key.nunique())<MIN_CELL_PAIRS or min(a.day.nunique(),b.day.nunique())<MIN_CELL_DAYS:continue
        cells.append(k);details[k]={"novel_pairs":len(a),"familiar_pairs":len(b),"novel_days":int(a.day.nunique()),"familiar_days":int(b.day.nunique())}
    p=q.loc[q.cell.isin(cells)].copy()
    out["common_cells"]=len(cells);out["cells"]=details
    out["matched"]={"novel":pair_summary(p.loc[p.novel]),"familiar":pair_summary(p.loc[~p.novel])}
    orig_n=int(q.novel.sum());n=int(p.novel.sum())
    out["novel_pair_coverage"]=n/orig_n if orig_n else 0.
    if not cells or out["novel_pair_coverage"]<MIN_COVERAGE:
        out["status"]="HOLD_COMMON_CELL_COVERAGE";return out
    if any(out["matched"][k]["pairs"]<prev.MIN_PAIRS or out["matched"][k]["days"]<prev.MIN_DAYS for k in ("novel","familiar")):
        out["status"]="HOLD_SUPPORT";return out
    dates=pd.Index(sorted(t.day.unique()));arrays=[];masses=[]
    for k in cells:
        z=p.loc[p.cell.eq(k)];arms=[]
        for flag in (True,False):
            a=z.loc[z.novel.eq(flag)];w=prev.weights(a)
            df=pd.DataFrame(a[list(CONTRASTS)].to_numpy()*w[:,None],columns=CONTRASTS)
            df["w"]=w;df["day"]=a.day.to_numpy()
            arms.append(df.groupby("day",observed=True)[list(CONTRASTS)+["w"]].sum().reindex(dates,fill_value=0).to_numpy())
        arrays.append(arms);masses.append(min(x[:,2].sum() for x in arms))
    a=np.asarray(arrays);mass=np.asarray(masses,float);mass/=mass.sum()
    def standardized(z):
        if (z[...,2]<=0).any():return None
        return np.sum((z[...,:2]/z[...,2,None])*mass[:,None,None],axis=0)
    m=standardized(a.sum(axis=2))
    if m is None:raise ValueError("HOLD_STANDARDIZATION")
    out["standardized_gain"]={"novel":dict(zip(CONTRASTS,m[0].tolist())),"familiar":dict(zip(CONTRASTS,m[1].tolist()))}
    out["novel_minus_familiar"]=dict(zip(CONTRASTS,(m[0]-m[1]).tolist()))
    rng=np.random.default_rng(prev.SEED);draw=[]
    for _ in range(prev.DRAWS):
        ix=rng.integers(len(dates),size=len(dates))
        b=standardized(a[:,:,ix,:].sum(axis=2))
        if b is None:
            out["status"]="HOLD_BOOTSTRAP_SUPPORT";return out
        draw.append(b[0]-b[1])
    out["status"]="OBSERVED_CONDITIONAL"
    out["conditional_day_97_5_novel_minus_familiar"]=dict(zip(CONTRASTS,np.quantile(draw,[.0125,.9875],axis=0).T.tolist()))
    return out

def analyze(archive,receipt):
    ref=json.loads(receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=prev.SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=prev.COLS,dtype=str,keep_default_na=False)
    old,_=prev.prepare_frame(raw);del raw
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N,sizes=prev.prepare_parents(old);del old
    v,qa=prev.replay(t,N,sizes)
    if qa!=ref["parent_QA"]:raise ValueError("HOLD_PARENT_QA")
    h=context_history(t);del t
    for yr in (prev.CAL,*prev.TEST):v[yr]=attach(v[yr],h.loc[h.day.dt.year.eq(yr)])
    del h
    q=v[prev.CAL].loc[prev.groupmask(v[prev.CAL],"first_meeting")]
    if len(q)!=217613:raise ValueError("HOLD_CALIBRATION_PARITY")
    fits={k:prev.fit(q,cols) for k,cols in MODELS.items()}
    for k in prev.MODELS:
        r=ref["calibration"]["fits"][k]
        if fits[k]["cols"]!=r["cols"]:raise ValueError("HOLD_FEATURES")
        for field in ("scale","beta"):prev.same(fits[k][field],r[field],"PR111_"+field)
    out={}
    for yr in prev.TEST:
        groups={g:prev.evaluate(v[yr],{k:fits[k] for k in prev.MODELS},g) for g in prev.GROUPS}
        for g,z in groups.items():
            r=ref["results"][str(yr)]["groups"][g]
            prev.same(z["pairs"],r["pairs"],"PR111_COUNTS")
            for k in r["Brier"]:prev.same(z["Brier"][k],r["Brier"][k],"PR111_BRIER")
            for k in r["gain"]:prev.same(z["gain"][k],r["gain"][k],"PR111_GAIN")
            if z["support"]!=r["support"]:raise ValueError("HOLD_PR111_SUPPORT")
        out[str(yr)]=contrast(v[yr],fits)
    return {"status":"RETROSPECTIVE_CONTEXT_NOVELTY_FAMILY_ABILITY","source_sha256":prev.SOURCE_SHA,
        "original_PR111_parity":True,"calibration":{"year":prev.CAL,"pairs":len(q),"fits":fits},
        "primary":"2021 standardized novel-minus-familiar V vs C gain",
        "results":out,"limits":["Observed earlier JRA surface-distance-band history only; novelty is not official career novelty.",
        "No imposed own-history or novelty attenuation in V; parent peer shrinkage retained.",
        "Context-adjusted baseline does not fully control age, class, trainer, management or physical capacity.",
        "Different pairs in matched coarse total-start/context cells; conditional date intervals omit horse, kin, graph and fitting dependence. Not within-horse or causal.",
        "Same inspected archive; no prospective or genetic claim or raw data export."]}

def self_test():
    t=pd.DataFrame({"id":[0,0,0,1],"race":["r1","r2","r3","r3"],"day":pd.to_datetime(["2020-01-01","2020-01-01","2020-01-02","2020-01-02"]),
        "surface":"turf","distance":1600,"y":[0.,1.,0.,1.]})
    h=context_history(t)
    assert h.ctx_n.tolist()==[0,0,2,0]
    z=attach(pd.DataFrame({"a":[0],"b":[1],"race":["r3"],"day":pd.to_datetime(["2020-01-02"]),"min_starts":[0],"max_starts":[2]}),h)
    assert z.a_ctx_n.iloc[0]==2 and z.b_ctx_n.iloc[0]==0
    n=240
    z=pd.DataFrame({"race":[f"r{i//2}" for i in range(n)],"day":pd.to_datetime(["2020-01-01"]*n)+pd.to_timedelta(np.arange(n)%40,unit="D"),
      "key":np.arange(n),"connected":True,"first":True,"min_starts":4,"max_starts":5,
      "ctx":"turf:4","a_ctx_n":np.r_[np.zeros(120),np.full(120,3)],"b_ctx_n":3,"y":np.arange(n)%2})
    for k in set(sum((list(x) for x in MODELS.values()),[])):z[k]=np.tile([.4,-.4],n//2)
    fits={k:prev.fit(z,cols) for k,cols in MODELS.items()}
    r=contrast(z,fits);assert r["status"]=="OBSERVED_CONDITIONAL"
    prev.same(list(r["novel_minus_familiar"].values()),0.,"NOVELTY_TEST")
    print("Synthetic prior-day context history and matched novelty contrast passed")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.output)):p.error("archive/receipt/output required")
    r=analyze(a.archive,a.receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
