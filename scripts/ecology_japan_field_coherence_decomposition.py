#!/usr/bin/env python3
"""Separate rank closure, scale and nonlinear shape; fixed PR103 scores.
No physical competition or prospective inference. Aggregate only."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_race_field_information import (
    COLS,SOURCE_SHA,prepare_frame,old_metadata,annual_features,TRAIN,CAL,TEST,
    COLSET,RIDGE_ALPHA,fit_weighted_ridge,predict_weighted_ridge,
    field_blocks,calibrate,LINEAR,PAIR,predict,scores,MODELS
)
SEED=20261126
DRAWS=999

def same(a,b):
    if not np.allclose(a,b,atol=1e-10,rtol=0):raise ValueError("HOLD_IDENTITY_OR_PARITY")

def mean(x,w):
    return float(np.average(x,weights=w))

def decompose(t,p):
    blocks=field_blocks(t)
    y=t.y.to_numpy(float)
    racew=1/t.field.to_numpy(float)
    horsew=1/t.groupby("horse",observed=True).horse.transform("size").to_numpy(float)
    out={}
    for k in ("own","kin"):
        r=p[k+"_raw"];l=p[k+"_linear"];f=p[k+"_pair"]
        C=np.empty(len(t));E=np.empty(len(t));delta=np.empty(len(t))
        for n,ix in blocks.items():
            v=r[ix];d=.5-v.mean(axis=1,keepdims=True)
            c=v+d;z=c-.5
            sd=np.sqrt(np.mean(z*z,axis=1,keepdims=True))
            fs=np.sqrt(np.mean((f[ix]-.5)**2,axis=1,keepdims=True))
            ratio=np.divide(fs,sd,out=np.zeros_like(sd),where=sd>1e-14)
            eq=.5+z*ratio
            same(eq.mean(axis=1),.5)
            same(np.mean((eq-.5)**2,axis=1),np.mean((f[ix]-.5)**2,axis=1))
            C[ix]=c;E[ix]=eq;delta[ix]=np.broadcast_to(d,v.shape)
        loss=lambda q:(y-q)**2
        closure=loss(r)-loss(C)
        guaranteed=delta**2
        imbalance=2*delta*((y-r)-delta)
        same(closure,guaranteed+imbalance)
        same(mean(imbalance,racew),0)
        cap=loss(C)-loss(l)
        energy=loss(l)-loss(E)
        shape=loss(E)-loss(f)
        same(loss(r)-loss(f),closure+cap+energy+shape)
        # Equal per-race prediction energy makes shape contribution purely
        # residual alignment under equal within-race weights.
        same(mean(shape,racew),mean(2*(y-.5)*(f-E),racew))
        arr={"closure":closure,"guaranteed_mean_bias":guaranteed,"within_race_weighting_cross_term":imbalance,
             "center_to_original_linear":cap,"linear_to_equal_energy":energy,
             "equal_energy_linear_to_pair_shape":shape,"linear_to_pair_total":energy+shape,
             "raw_to_pair_total":closure+cap+energy+shape}
        z={"race_equal":{n:mean(v,racew) for n,v in arr.items()},
           "horse_equal":{n:mean(v,horsew) for n,v in arr.items()},
           "unbounded_diagnostic_rows":{"center":int(((C<0)|(C>1)).sum()),"equal_energy":int(((E<0)|(E>1)).sum())}}
        # Contrasts conditional on the exact fitted scores; two separate clustering
        # axes, not simultaneous multiway intervals. Same primary shape and
        # weighting-cross term, no multiple outcome discovery.
        for lab,grp,w in (("date_race_equal",t.day.to_numpy(),racew),("horse_race_equal",t.horse.to_numpy(),racew),
                          ("horse_horse_equal",t.horse.to_numpy(),horsew)):
            tab=pd.DataFrame({"shape":w*shape,"cross":w*imbalance,"w":w,"g":grp})
            a=tab.groupby("g",observed=True)[["shape","cross","w"]].sum().to_numpy()
            if len(a)<30:
                z[lab]={"status":"HOLD_SUPPORT","clusters":len(a)};continue
            rng=np.random.default_rng(SEED)
            draws=np.array([a[rng.integers(len(a),size=len(a))].sum(axis=0) for _ in range(DRAWS)])
            z[lab]={"clusters":len(a),"conditional_97_5_shape_cross":np.quantile(draws[:,:2]/draws[:,2,None],[.0125,.9875],axis=0).T.tolist()}
        out[k]=z
    return out

def analyze(archive,receipt):
    old_result=json.loads(receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw)
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    old["stratum"]=old.surface.astype(str)+":"+(old.distance//400).astype(str)
    meta=old_metadata(raw);del raw
    xs=[];ys=[];ids=[]
    for yr in TRAIN:
        t,x=annual_features(old,meta,yr);xs.append(x);ys.append(t.y.to_numpy());ids.append(t.horse.astype(str).to_numpy())
    X=pd.concat(xs,ignore_index=True);Y=np.concatenate(ys);H=np.concatenate(ids)
    fit={k:fit_weighted_ridge(X,Y,H,v,alpha=RIDGE_ALPHA) for k,v in COLSET.items()}
    del xs,ys,ids,X,Y,H
    t,x=annual_features(old,meta,CAL);b=field_blocks(t);cal={}
    for k in ("own","kin"):
        raw=predict_weighted_ridge(fit[k],x)
        cal[k]={"linear":calibrate(t,raw,b,"linear",LINEAR),"pair":calibrate(t,raw,b,"pair",PAIR)}
        for mode in ("linear","pair"):
            ref=old_result["results"]["calibration"]["models"][k][mode]
            same(cal[k][mode]["selected"],ref["selected"])
            same(cal[k][mode]["validation_race_equal_MSE"],ref["validation_race_equal_MSE"])
    out={};parts=[];allp=[]
    for yr in TEST:
        t,x=annual_features(old,meta,yr);p=predict(t,x,fit,cal)
        z=scores(t,p);ref=old_result["results"]["years"][str(yr)]["scores"]
        for k in ("race_equal_RMSE","horse_equal_RMSE"):
            same([z[k][m] for m in MODELS],[ref[k][m] for m in MODELS])
        out[str(yr)]=decompose(t,p)
        parts.append(t[["horse","race","day","field","y"]].copy());allp.append(p)
    t=pd.concat(parts,ignore_index=True);p={k:np.concatenate([v[k] for v in allp]) for k in MODELS}
    z=scores(t,p);ref=old_result["results"]["pooled"]["scores"]
    for k in ("race_equal_RMSE","horse_equal_RMSE"):
        same([z[k][m] for m in MODELS],[ref[k][m] for m in MODELS])
    out["pooled"]=decompose(t,p)
    return {"status":"RETROSPECTIVE_FIELD_COHERENCE_DECOMPOSITION","source_sha256":SOURCE_SHA,
            "original_PR103_calibration_and_score_parity":True,"pooled_counts":{k:z[k] for k in ("starts","horses","races")},
            "results":out,"limits":["Same inspected source and model; post-result diagnostic, not new independent validation.",
            "Unbounded centered/equal-energy linear counterfactuals are arithmetic controls, not probabilities or deployable forecasts.",
            "Per-race equal-energy control distinguishes shape from scale conditional on original pair projection; not physical interaction.",
            "Horse weighting uses observed test participation and changes the estimand; not a causal participation mechanism.",
            "Fixed-fit single-axis conditional intervals omit crossed dependence. No source raw records exported."]}

def self_test():
    t=pd.DataFrame({"horse":["a","b","c","a","d"],"race":["r1"]*3+["r2"]*2,"day":pd.to_datetime(["2020-01-01"]*5),"field":[3]*3+[2]*2,"y":[0,.5,1,1,0]})
    from ecology_japan_race_field_information import project
    raw=np.array([.1,.3,.8,.5,.7]);b=field_blocks(t)
    p={}
    for k in ("own","kin"):
        p[k+"_raw"]=raw;p[k+"_linear"]=project(raw,b,"linear",1);p[k+"_pair"]=project(raw,b,"pair",4)
    r=decompose(t,p)["own"]
    same(r["race_equal"]["closure"],r["race_equal"]["guaranteed_mean_bias"])
    assert abs(r["horse_equal"]["within_race_weighting_cross_term"])>1e-6
    print("Synthetic closure, weighting, equal-energy and exact decomposition checks passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.output)):p.error("archive, receipt, output required")
    r=analyze(a.archive,a.receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
