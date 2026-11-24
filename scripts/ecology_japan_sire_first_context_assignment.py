#!/usr/bin/env python3
"""First observed annual context assignment vs later use, learned baseline.

Historical source A only; fixed year-first information cutoff. First eligible
start is an observed endpoint, not official debut. Anonymous aggregates only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_sire_context_specificity import CONTEXTS, SEEDS, _hash_half
from ecology_japan_sire_context_time_transfer import count_match, MIN_PEERS, SHRINK
from ecology_japan_archive_forward import SOURCE_SHA, COLS, prepare_frame, clean_id
from ecology_japan_2022_independent_forward import fit_weighted_ridge, predict_weighted_ridge
from ecology_japan_2022_strong_portable_baseline import SEX_MAP

TRAIN_FIRST=2016
TEST_YEARS=(2020,2021)
DRAWS=999
ALPHA=100.
MIN_SIRES=30

def annual_rows(old):
    x=old.loc[old.circuit.eq("JRA")&old.stratum.isin(CONTEXTS),
              ["horse","sire_id","trainer_id","day","year","race","stratum"]].copy()
    for c in ("horse","sire_id","trainer_id","race","stratum"):
        x[c]=x[c].astype(str)
    if x.horse.eq("").any() or x.day.isna().any() or x.duplicated(["horse","race"]).any():
        raise ValueError("HOLD_ELIGIBLE_IDENTITY")
    if x.groupby("horse",observed=True).sire_id.nunique().max()>1:
        raise ValueError("HOLD_PARENT_CONFLICT")
    x=x.loc[x.sire_id.ne("")].sort_values(["day","race","horse"]).copy()
    x["turf"]=x.stratum.eq(CONTEXTS[0]).astype(float)
    key=["horse","year"]
    firstday=x.groupby(key,observed=True).day.transform("min")
    if x.loc[x.day.eq(firstday)].duplicated(key).any():
        raise ValueError("HOLD_AMBIGUOUS_FIRST_DAY")
    g=x.groupby(key,observed=True).turf.agg(["sum","size"]).reset_index()
    t=x.drop_duplicates(key,keep="first").merge(g,on=key,validate="one_to_one")
    t=t.rename(columns={"turf":"first","size":"starts"})
    t["later"]=np.divide(t["sum"]-t["first"],t.starts-1,
                         out=np.full(len(t),np.nan),where=t.starts.to_numpy()>1)
    return t.drop(columns="sum").reset_index(drop=True)

def attach_entry_metadata(t, raw):
    """Exact source row key, age/sex as recorded at first eligible start.
    No rank, odds or current outcome enters this lookup.
    """
    d=pd.to_datetime(raw.date,format="mixed",errors="coerce")
    num=pd.to_numeric(raw.race_number,errors="coerce")
    r=pd.DataFrame({"horse":clean_id(raw.horse_id),"day":d,
        "race":d.dt.strftime("%Y-%m-%d").fillna("")+"|"+raw.racecourse.astype(str).str.strip()+"|"+num.fillna(-1).astype("int16").astype(str),
        "age_raw":pd.to_numeric(raw.age,errors="coerce"),
        "sex_raw":raw.sex.astype(str).str.strip().str.casefold().map(SEX_MAP).fillna(0)})
    earliest=r.loc[r.horse.ne("")&r.day.notna()].groupby("horse").day.min()
    t=t.copy()
    t["raw_earliest"]=t.horse.map(earliest)
    if t.raw_earliest.isna().any() or (t.raw_earliest>t.day).any():
        raise ValueError("HOLD_RAW_CHRONOLOGY")
    keys=pd.MultiIndex.from_frame(t[["horse","race"]])
    r=r.set_index(["horse","race"])
    r=r.loc[r.index.isin(keys)]
    if r.index.has_duplicates:
        raise ValueError("HOLD_ENTRY_META_DUPLICATE")
    r=r.reindex(keys)
    if r.day.isna().any() or not np.array_equal(r.day.to_numpy(),t.day.to_numpy()):
        raise ValueError("HOLD_ENTRY_META_MISSING")
    t["age_raw"]=r.age_raw.to_numpy(float)
    t["sex_raw"]=r.sex_raw.to_numpy(float)
    return t

def own_group(h,t,prefix):
    g=h.groupby("horse",observed=True).agg(n=("y","size"),turf=("turf","mean"),
                                               rank=("y","mean"),distance=("distance","mean"))
    q=g.reindex(t.horse)
    n=q.n.fillna(0).to_numpy(float)
    p=q.turf.fillna(.5).to_numpy(float)
    return pd.DataFrame({prefix+"_log_n":np.log1p(n),prefix+"_known":(n>0).astype(float),
            prefix+"_turf":p,prefix+"_turf_shrunk":(n*p+2.5)/(n+5),
            prefix+"_rank":q["rank"].fillna(.5).to_numpy(float),
            prefix+"_distance":q.distance.fillna(1800).to_numpy(float)/1000})

def trainer_features(h,t,ids,prefix):
    z=h.loc[h.trainer_id.ne("")].groupby(["trainer_id","horse"],observed=True).turf.mean()
    a=z.groupby(level=0).agg(["sum","size"])
    n=ids.map(a["size"]).fillna(0).to_numpy(float)
    s=ids.map(a["sum"]).fillna(0).to_numpy(float)
    focal=z.reindex(pd.MultiIndex.from_arrays([ids,t.horse]))
    n-=focal.notna().to_numpy(float);s-=focal.fillna(0).to_numpy(float)
    if (n<0).any() or (s< -1e-9).any() or (s-n>1e-9).any():
        raise ValueError("HOLD_TRAINER_EXCLUSION")
    return pd.DataFrame({prefix+"_log_n":np.log1p(n),prefix+"_known":(n>0).astype(float),
                         prefix+"_turf":(s+4)/(n+8)})

def build_baseline(old, annual, raw):
    t=attach_entry_metadata(annual.loc[annual.year.ge(TRAIN_FIRST)].copy(),raw)
    h=old[["horse","trainer_id","day","year","race","stratum","circuit","surface","distance","y"]].copy()
    for c in ("horse","trainer_id","race"):
        h[c]=h[c].astype(str)
    h["turf"]=h.surface.eq("turf").astype(float)
    out=[]
    for year in range(TRAIN_FIRST,2022):
        a=t.loc[t.year.eq(year)].reset_index(drop=True)
        p=h.loc[h.year.lt(year)]
        if p.empty or a.empty or p.day.max()>=a.day.min():
            raise ValueError("HOLD_TIME_CUTOFF")
        j=p.loc[p.circuit.eq("JRA")]
        e=j.loc[j.stratum.isin(CONTEXTS)]
        blocks=[own_group(p,a,"all"),own_group(j,a,"jra"),own_group(e,a,"eligible")]
        last=p.sort_values(["day","race","horse"]).drop_duplicates("horse",keep="last").set_index("horse")
        lasttr=a.horse.map(last.trainer_id).fillna("")
        blocks.extend([trainer_features(e,a,lasttr,"last_trainer"),
                       trainer_features(e,a,a.trainer_id,"entry_trainer")])
        gap=(pd.Timestamp(f"{year}-01-01")-a.horse.map(last.day)).dt.days
        age=a.age_raw.where(a.age_raw.between(2,20))
        sex=a.sex_raw.fillna(0)
        # Entry-day recorded age/sex/trainer are conditional covariates, not
        # claims about pre-entry publication or causes of assignment.
        extra=pd.DataFrame({"age":age.fillna(5).to_numpy(float),"age_known":age.notna().astype(float),
            "age_squared":(age.fillna(5).to_numpy(float)/5)**2,
            "female":sex.eq(2).astype(float),"gelding":sex.eq(3).astype(float),
            "sex_unknown":sex.eq(0).astype(float),
            "last_turf":a.horse.map(last.turf).fillna(.5).to_numpy(float),
            "last_rank":a.horse.map(last.y).fillna(.5).to_numpy(float),
            "log_gap":np.log1p(gap.fillna(3650).clip(0,3650).to_numpy(float)),
            "calendar":np.full(len(a),year-TRAIN_FIRST,dtype=float)})
        x=pd.concat([*blocks,extra],axis=1)
        x["eligible_turf_x_count"]=x.eligible_turf*x.eligible_log_n
        x["jra_turf_x_count"]=x.jra_turf*x.jra_log_n
        x["entry_trainer_turf_x_cold"]=x.entry_trainer_turf*(1-x.eligible_known)
        a["cold_at_entry_raw"]=a.raw_earliest.eq(a.day)
        a["no_eligible_before_year"]=x.eligible_known.eq(0)
        a["no_classified_before_year"]=x.all_known.eq(0)
        for col in x:
            a[col]=x[col].to_numpy(float)
        out.append(a)
    p=pd.concat(out,ignore_index=True)
    return p,tuple(x.columns)

def family_features(annual,p,seed,endpoint):
    """Donors from earlier years, opposite horse half, horse-equal means."""
    a=annual[["horse","sire_id","year",endpoint]].dropna().copy()
    a["half"]=_hash_half(a.horse,seed,"horse")
    q=p.copy()
    q["half"]=_hash_half(q.horse,seed,"horse")
    cols=["kin_log_n","kin_signal","kin_signal_x_eligible","kin_signal_x_count"]
    z=np.zeros((len(q),len(cols)))
    alt=np.zeros((len(q),len(cols)))
    matched=np.zeros(len(q),bool)
    for year in range(TRAIN_FIRST,2022):
        for half in (0,1):
            ix=np.flatnonzero(q.year.eq(year).to_numpy()&q.half.eq(half).to_numpy())
            if not len(ix):
                continue
            h=a.loc[a.year.lt(year)&a.half.ne(half)]
            if h.empty:
                raise ValueError("HOLD_EMPTY_DONORS")
            t=q.iloc[ix]
            if set(h.horse)&set(t.horse):
                raise ValueError("HOLD_DONOR_HORSE_OVERLAP")
            hh=h.groupby(["horse","sire_id"],observed=True)[endpoint].mean().reset_index()
            g=hh.groupby("sire_id",observed=True)[endpoint].agg(["mean","size"])
            mu=float(hh[endpoint].mean())
            n=t.sire_id.map(g["size"]).fillna(0).to_numpy(float)
            mean=t.sire_id.map(g["mean"]).fillna(mu).to_numpy(float)
            good=n>=MIN_PEERS
            sh=np.where(good,n/(n+SHRINK),0)
            s=sh*(mean-mu)
            match=count_match(g["size"],seed)
            donor=t.sire_id.map(match)
            matched[ix]=donor.notna().to_numpy()&good
            palt=donor.map(g["mean"]).fillna(mu).to_numpy(float)
            sa=sh*(palt-mu)
            k=t.eligible_known.to_numpy(float)
            c=t.eligible_log_n.to_numpy(float)
            z[ix,:]=np.column_stack((np.log1p(n),s,s*k,s*c))
            alt[ix,:]=np.column_stack((np.log1p(n),sa,sa*k,sa*c))
    for i,k in enumerate(cols):
        q[k]=z[:,i];q["P_"+k]=alt[:,i]
    q["matched"]=matched
    return q,tuple(cols)

def score(p,seed):
    if p.empty:
        return {"status":"HOLD_EMPTY","horses":0}
    if p.horse.duplicated().any():
        raise ValueError("HOLD_TARGET_DENOMINATOR")
    y=p.y.to_numpy(float)
    losses={k:(y-p[k].to_numpy(float))**2 for k in ("B","C","F")}
    out={"horses":len(p),"sires":int(p.sire_id.nunique()),"RMSE":{k:float(np.sqrt(v.mean())) for k,v in losses.items()}}
    def contrast(frame, d):
        g=pd.DataFrame({"sire":frame.sire_id.to_numpy(),"d":d}).groupby("sire",observed=True).d.agg(["sum","size"])
        r={"MSE_gain":float(np.mean(d)),"sires":len(g)}
        if len(g)>=MIN_SIRES:
            rng=np.random.default_rng(seed);a=g.to_numpy(float)
            b=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
            r["CI95_pointwise"]=np.quantile(b[:,0]/b[:,1],[.025,.975]).tolist()
        else:
            r["status"]="HOLD_FEW_SIRES"
        return r
    out["B_minus_F"]=contrast(p,losses["B"]-losses["F"])
    out["C_minus_F"]=contrast(p,losses["C"]-losses["F"])
    m=p.loc[p.matched]
    out["matched_horses"]=len(m)
    if len(m):
        a=m.y.to_numpy(float)
        out["matched_RMSE"]={k:float(np.sqrt(np.mean((a-m[k].to_numpy(float))**2))) for k in ("C","F","P")}
        out["P_minus_F_matched"]=contrast(m,(a-m.P.to_numpy(float))**2-(a-m.F.to_numpy(float))**2)
    return out

def evaluate(p,base,kin,endpoint,year,seed):
    q=p.loc[p[endpoint].notna()].copy()
    parts=[]
    for half in (0,1):
        train=q.loc[q.year.lt(year)&q.half.ne(half)]
        target=q.loc[q.year.eq(year)&q.half.eq(half)].copy()
        if train.empty or target.empty or set(train.horse)&set(target.horse):
            raise ValueError("HOLD_FIT_SPLIT")
        cols={"B":base,"C":base+(kin[0],),"F":base+kin}
        for key,c in cols.items():
            model=fit_weighted_ridge(train,train[endpoint],train.horse,c,alpha=ALPHA)
            target[key]=predict_weighted_ridge(model,target)
        # Swap only performance signal, identical count and fitted model.
        placebo=target.copy()
        for k in kin[1:]:
            placebo[k]=target["P_"+k]
        target["P"]=predict_weighted_ridge(model,placebo)
        target["y"]=target[endpoint]
        parts.append(target)
    t=pd.concat(parts,ignore_index=True)
    if len(t)!=len(q.loc[q.year.eq(year)]) or t.horse.duplicated().any():
        raise ValueError("HOLD_FIT_DENOMINATOR")
    groups={"all":t,"no_eligible_before_year":t.loc[t.no_eligible_before_year],
            "has_eligible_before_year":t.loc[~t.no_eligible_before_year],
            "raw_first_record_at_entry":t.loc[t.cold_at_entry_raw],
            "raw_prior_at_entry":t.loc[~t.cold_at_entry_raw]}
    return {k:score(v,seed) for k,v in groups.items()}

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
    n=a.loc[a.year.isin((2019,2020,2021))].groupby("year").size().to_dict()
    if n!={2019:7265,2020:7381,2021:7276}:
        raise ValueError("HOLD_PR81_PARITY")
    p,base=build_baseline(old,a,raw)
    results={}
    for seed in SEEDS:
        r={}
        for endpoint in ("first","later"):
            q,kin=family_features(a,p,seed,endpoint)
            # For later starts the first observed surface is a known new input.
            b=base+(("first",) if endpoint=="later" else ())
            r[endpoint]={str(y):evaluate(q,b,kin,endpoint,y,seed) for y in TEST_YEARS}
        results[str(seed)]=r
    return {"status":"RETROSPECTIVE_INITIAL_ASSIGNMENT_AND_LATER_USE",
            "source_A_sha256":SOURCE_SHA,"primary":"20261124/first/2021/all/C_minus_F",
            "annual_horse_counts_2019_21":{str(k):int(v) for k,v in n.items()},
            "base_features":list(base),"results":results,
            "limitations":["First eligible classified source record within year is not official debut, true first environment exposure, or decision time.",
             "All prior summaries use earlier years; entry age/sex/current trainer are as-recorded conditional covariates, not pre-entry publication evidence.",
             "Historical training labels split by horse, but own and family features reuse allowed earlier source histories; no claim of full dataset independence.",
             "Later endpoint conditions on >=2 eligible starts and adds first observed surface; different denominator from first endpoint.",
             "Count-matched other-sire swap is a support control, not genomic unrelatedness.",
             "Pointwise whole-sire bootstrap conditional on fitted models; shared environment and pedigree dependence remain.",
             "Previously inspected years; no causal adaptation or market/wagering inference. No individual records exported."]}

def self_test():
    rows=[]
    for y in (2015,2016,2017,2018,2019,2020,2021):
        for i in range(48):
            for j,c in enumerate(CONTEXTS):
                rows.append(dict(horse=f"h{i}",sire_id=f"s{i%4}",trainer_id=f"t{i%5}",
                    day=pd.Timestamp(f"{y}-01-0{j+1}"),year=y,race=f"{y}-{j}",stratum=c,
                    circuit="JRA",surface=c.split(":")[0],distance=1800,y=.5))
    old=pd.DataFrame(rows)
    a=annual_rows(old)
    assert len(a)==7*48 and np.allclose(a["first"],1) and np.allclose(a.later,0)
    one=old.loc[~(old.horse.eq("h0")&old.year.eq(2021)&old.stratum.eq(CONTEXTS[1]))]
    assert annual_rows(one).loc[lambda x:x.horse.eq("h0")&x.year.eq(2021),"later"].isna().all()
    p=a.loc[a.year.ge(TRAIN_FIRST)].copy().reset_index(drop=True)
    p["eligible_known"]=1.;p["eligible_log_n"]=2.;p["no_eligible_before_year"]=False;p["cold_at_entry_raw"]=False
    q,k=family_features(a,p,SEEDS[0],"first")
    b=a.copy();b.loc[b.year.eq(2021),"first"]=0
    q2,_=family_features(b,p,SEEDS[0],"first")
    assert np.allclose(q[list(k)],q2[list(k)])
    assert np.allclose(q.kin_signal,0)
    s=evaluate(q,("eligible_known","eligible_log_n"),k,"first",2021,SEEDS[0])
    assert s["all"]["horses"]==48 and s["all"]["C_minus_F"]["MSE_gain"]==0
    print("synthetic first/later denominator, donor exclusion and held-label invariance passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not a.archive or not a.output:
        p.error("archive and output required")
    z=analyze(a.archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    # All group-level data in artifact; compact primary and annual sensitivity in logs.
    compact={s:{e:{y:v["all"] for y,v in yy.items()} for e,yy in r.items()} for s,r in z["results"].items()}
    print(json.dumps({"status":z["status"],"primary":z["primary"],"annual_horse_counts_2019_21":z["annual_horse_counts_2019_21"],
        "all_groups":compact,"primary_subgroups":z["results"][str(SEEDS[0])]["first"]["2021"]},allow_nan=False))

if __name__=="__main__":
    main()
