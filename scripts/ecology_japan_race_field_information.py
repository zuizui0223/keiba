#!/usr/bin/env python3
"""Horse competition: coherent relative ranks from a full classified field.
Chronological, retrospective. No inference of physical interference or wagering.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_archive_forward import COLS,SOURCE_SHA,prepare_frame
from ecology_japan_2022_independent_forward import _peer,fit_weighted_ridge,predict_weighted_ridge,RIDGE_ALPHA
from ecology_japan_2022_strong_portable_baseline import STRONG_NO_KIN,STRONG_KIN,old_metadata
from ecology_japan_2022_24_family_feature_ablation import _strong_features

TRAIN=(2016,2017,2018)
CAL=2019
TEST=(2020,2021)
EXTRA=("trainer_context_history","trainer_context_log_support")
COLSET={"own":STRONG_NO_KIN+EXTRA,"kin":STRONG_KIN+EXTRA}
LINEAR=(0.,.25,.5,.75,1.,1.25,1.5,2.,3.,4.)
PAIR=(0.,.5,1.,2.,3.,4.,6.,8.,12.,16.,24.,32.,48.,64.)
DRAWS=999
SEED=20261126
MODELS=("neutral","own_raw","kin_raw","own_linear","kin_linear","own_pair","kin_pair")

def field_blocks(t,check_outcome=True):
    if t.empty or t.duplicated(["race","horse"]).any():raise ValueError("HOLD_FIELD_KEYS")
    blocks={};field=t.field.to_numpy();y=t.y.to_numpy() if check_outcome else None
    for rid,ix in t.groupby("race",observed=True,sort=False).indices.items():
        n=len(ix)
        if n<2 or not (field[ix]==n).all():raise ValueError("HOLD_FIELD_SIZE")
        if check_outcome and not np.allclose(np.sort(y[ix]),np.arange(n)/(n-1),atol=1e-12,rtol=0):
            raise ValueError("HOLD_COMPLETE_CLASSIFIED_FIELD")
        blocks.setdefault(n,[]).append(ix)
    out={n:np.stack(xs) for n,xs in blocks.items()}
    allidx=np.concatenate([x.ravel() for x in out.values()])
    if len(allidx)!=len(t) or not np.array_equal(np.sort(allidx),np.arange(len(t))):raise ValueError("HOLD_FIELD_PARTITION")
    return out

def project(raw,blocks,mode,parameter):
    raw=np.asarray(raw,float)
    if not np.isfinite(raw).all() or not ((raw>=0)&(raw<=1)).all() or parameter<0:
        raise ValueError("HOLD_BAD_SCORES")
    out=np.empty_like(raw)
    for n,ix in blocks.items():
        s=raw[ix]
        if mode=="linear":
            d=s-s.mean(axis=1,keepdims=True)
            # Bound scaling within each race without breaking mean-rank closure.
            m=np.max(np.abs(d),axis=1,keepdims=True)
            cap=np.divide(.5,m,out=np.full_like(m,np.inf),where=m>0)
            v=.5+d*np.minimum(parameter,cap)
        elif mode=="pair":
            # p(j ahead of i)=sigmoid(lambda*(score_i-score_j)); larger score is worse.
            diff=parameter*(s[:,:,None]-s[:,None,:])
            p=1/(1+np.exp(-diff))
            v=(p.sum(axis=2)-.5)/(n-1)
        else:raise ValueError("HOLD_UNKNOWN_PROJECTION")
        if not np.allclose(v.mean(axis=1),.5,atol=1e-12,rtol=0) or (v< -1e-12).any() or (v>1+1e-12).any():
            raise ValueError("HOLD_COHERENCE")
        out[ix]=v
    return out

def weights(t):
    return 1/t.field.to_numpy(float)

def calibrate(t,raw,blocks,mode,grid):
    y=t.y.to_numpy(float);w=weights(t)
    risks=[]
    for a in grid:
        p=project(raw,blocks,mode,a)
        risks.append(float(np.average((y-p)**2,weights=w)))
    # deterministic smallest coefficient on ties
    i=min(range(len(grid)),key=lambda j:(risks[j],grid[j]))
    return {"selected":grid[i],"grid":list(grid),"validation_race_equal_MSE":risks}

def annual_features(old,meta,yr):
    h=old.loc[old.year.lt(yr)]
    t=old.loc[old.year.eq(yr)&old.circuit.eq("JRA")].reset_index(drop=True)
    if h.empty or t.empty or h.day.max()>=t.day.min():raise ValueError("HOLD_CHRONOLOGY")
    x=_strong_features(h,t,meta)
    s,n=_peer(h,t,"trainer_id")
    x[EXTRA[0]]=s/(8+n);x[EXTRA[1]]=np.log1p(n)
    if len(x)!=len(t):raise ValueError("HOLD_FEATURE_ROWS")
    return t,x

def scores(t,p):
    y=t.y.to_numpy(float)
    w=weights(t)
    wh=1/t.groupby("horse",observed=True).horse.transform("size").to_numpy(float)
    return {"starts":len(t),"races":int(t.race.nunique()),"horses":int(t.horse.nunique()),
            "race_equal_RMSE":{m:float(np.sqrt(np.average((y-p[m])**2,weights=w))) for m in MODELS},
            "horse_equal_RMSE":{m:float(np.sqrt(np.average((y-p[m])**2,weights=wh))) for m in MODELS},
            "mean_absolute_race_mean_deviation":{m:float(pd.DataFrame({"race":t.race.to_numpy(),"p":p[m]}).groupby("race",observed=True).p.mean().sub(.5).abs().mean()) for m in MODELS}}

def contrasts(t,p):
    y=t.y.to_numpy(float);w=weights(t)
    loss={m:(y-p[m])**2 for m in MODELS}
    # First two primary contrasts, all other comparisons descriptive.
    effects={"nonlinear_beyond_linear_no_kin":loss["own_linear"]-loss["own_pair"],
             "kin_given_pairwise_field":loss["own_pair"]-loss["kin_pair"],
             "linear_field_beyond_raw_no_kin":loss["own_raw"]-loss["own_linear"],
             "kin_raw":loss["own_raw"]-loss["kin_raw"],
             "kin_given_linear_field":loss["own_linear"]-loss["kin_linear"],
             "nonlinear_beyond_linear_kin":loss["kin_linear"]-loss["kin_pair"]}
    names=list(effects)
    point={k:float(np.average(v,weights=w)) for k,v in effects.items()}
    tab=pd.DataFrame({k:effects[k]*w for k in names[:2]})
    tab["w"]=w;tab["day"]=t.day.to_numpy()
    a=tab.groupby("day",observed=True)[names[:2]+["w"]].sum().to_numpy()
    out={"race_equal_MSE_gain":point,"date_clusters":len(a)}
    if len(a)<30:out["status"]="HOLD_FEW_DATES";return out
    rng=np.random.default_rng(SEED)
    rep=np.array([a[rng.integers(len(a),size=len(a))].sum(axis=0) for _ in range(DRAWS)])
    intervals=np.quantile(rep[:,:2]/rep[:,2,None],[.0125,.9875],axis=0).T
    out.update(status="OBSERVED_CONDITIONAL_DATE_BOOTSTRAP",primary_conditional_97_5={k:v.tolist() for k,v in zip(names[:2],intervals)})
    return out

def predict(t,x,fit,cal):
    blocks=field_blocks(t);p={"neutral":np.full(len(t),.5)}
    for k in ("own","kin"):
        raw=predict_weighted_ridge(fit[k],x)
        p[k+"_raw"]=raw
        for mode in ("linear","pair"):
            p[k+"_"+mode]=project(raw,blocks,mode,cal[k][mode]["selected"])
    return p

def analyze(archive):
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw)
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    old["stratum"]=old.surface.astype(str)+":"+(old.distance//400).astype(int).astype(str)
    meta=old_metadata(raw);del raw
    xs=[];ys=[];ids=[];train_counts={}
    for yr in TRAIN:
        t,x=annual_features(old,meta,yr)
        xs.append(x);ys.append(t.y.to_numpy());ids.append(t.horse.astype(str).to_numpy())
        train_counts[str(yr)]={"starts":len(t),"races":int(t.race.nunique())}
    X=pd.concat(xs,ignore_index=True);Y=np.concatenate(ys);H=np.concatenate(ids)
    fit={k:fit_weighted_ridge(X,Y,H,v,alpha=RIDGE_ALPHA) for k,v in COLSET.items()}
    del xs,ys,ids,X,Y,H
    t,x=annual_features(old,meta,CAL);b=field_blocks(t)
    cal={}
    for k in ("own","kin"):
        raw=predict_weighted_ridge(fit[k],x)
        cal[k]={"linear":calibrate(t,raw,b,"linear",LINEAR),"pair":calibrate(t,raw,b,"pair",PAIR)}
    out={"training":train_counts,"calibration":{"year":CAL,"starts":len(t),"races":int(t.race.nunique()),"models":cal},"years":{}}
    parts=[];allp=[]
    for yr in TEST:
        t,x=annual_features(old,meta,yr);p=predict(t,x,fit,cal)
        out["years"][str(yr)]={"scores":scores(t,p),"contrasts":contrasts(t,p)}
        parts.append(t[["horse","race","day","field","y"]].copy());allp.append(p)
    t=pd.concat(parts,ignore_index=True);p={k:np.concatenate([v[k] for v in allp]) for k in MODELS}
    out["pooled"]={"scores":scores(t,p),"contrasts":contrasts(t,p)}
    return {"status":"RETROSPECTIVE_CLASSIFIED_FIELD_INFORMATION","source_sha256":SOURCE_SHA,
        "primary":"pooled 2020-21 race-equal; two directional conditional contrasts","results":out,
        "limitations":["Field is retrospectively classified finishers, not independently confirmed pre-race entrants.",
        "Year-start historical features, previous years only; same-year outcomes excluded. Fixed fit 2016-18 and projection calibration 2019.",
        "Pairwise logistic scores are a coherent relative-rank representation, not fitted physical interaction, speed, causal effect or joint outcome probabilities.",
        "Race-day conditional intervals ignore all repeated horse, kin and trainer dependence and fitting uncertainty. Horse-equal secondary scores descriptive.",
        "Same inspected archive; no independent prospective or wagering claim. No raw data exported."]}

def self_test():
    t=pd.DataFrame({"race":["r1"]*3+["r2"]*2,"horse":["a","b","c","a","d"],"field":[3]*3+[2]*2,
                    "y":[0,.5,1,0,1],"day":pd.to_datetime(["2020-01-01"]*5)})
    b=field_blocks(t);raw=np.array([.1,.3,.8,.5,.5])
    for mode,grid in (("linear",LINEAR),("pair",PAIR)):
        for a in grid:
            p=project(raw,b,mode,a)
            assert np.allclose([p[:3].mean(),p[3:].mean()],[.5,.5])
            assert p[0]<=p[1]<=p[2] and np.allclose(p[3:],.5)
        assert np.allclose(project(raw,b,mode,0),.5)
    try:field_blocks(t.iloc[:-1].reset_index(drop=True))
    except ValueError:pass
    else:raise AssertionError("incomplete field accepted")
    # Same focal score and mean rival score, different rival spread: nonlinear
    # expected ranks may differ even though a mean-centered linear rule does not.
    x=np.array([.3,.5,.5,.3,.2,.8]);blocks={3:np.array([[0,1,2],[3,4,5]])}
    a=project(x,blocks,"linear",1);p=project(x,blocks,"pair",8)
    assert abs(a[0]-a[3])<1e-12 and abs(p[0]-p[3])>1e-3
    print("Synthetic rank closure, opponent distribution and incomplete-field tests passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:self_test();return
    if not a.archive or not a.output:p.error("archive and output required")
    r=analyze(a.archive);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n")
    print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
