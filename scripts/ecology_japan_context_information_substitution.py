#!/usr/bin/env python3
"""History-count-dependent calibration of environmental allocation information.

Frozen source-A calibration, separate historical source-B evaluation.
The predicted outcome is observed turf fraction, not an animal's habitat
choice, physiological reaction norm, or wagering result.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_2022_joint_strict_strong import strict_mask_exact_horse_race
from ecology_japan_archive_forward import SOURCE_SHA
from ecology_japan_sire_context_specificity import SEEDS
from ecology_japan_sire_context_time_transfer import predict_fold
from ecology_japan_context_occupancy_independent import audit_circuits, target_occupancy, source_a_baseline
from ecology_japan_context_occupancy_refresh import source_a_reference, update_own, predictions, ci

BINS=("0","1-3","4-7","8+")
MIN_HORSES=100
MIN_SIRES=30
B_YEARS=(2022,2023,2024)
CAL_YEARS=(2020,2021)

def count_bin(n):
    n=np.asarray(n,float)
    if not np.isfinite(n).all() or (n<0).any() or (n!=np.floor(n)).any():
        raise ValueError("HOLD_OWN_COUNT")
    return np.searchsorted([1,4,8],n,side="right")

def decreasing_projection(num,den):
    """Weighted least squares for decreasing slopes on [0,1].

    Minimize sum_j den_j lambda_j^2-2 num_j lambda_j. PAVA pools
    violations before clipping the fitted solution to its common bounds.
    """
    num=np.asarray(num,float);den=np.asarray(den,float)
    if num.shape!=(4,) or den.shape!=(4,) or not np.isfinite(num).all() or not np.isfinite(den).all() or (den<=0).any():
        raise ValueError("HOLD_CALIBRATION_INFORMATION")
    blocks=[]
    for j in range(4):
        blocks.append([j,j,num[j],den[j]])
        while len(blocks)>1 and blocks[-2][2]/blocks[-2][3] < blocks[-1][2]/blocks[-1][3]:
            b=blocks.pop();a=blocks.pop()
            blocks.append([a[0],b[1],a[2]+b[2],a[3]+b[3]])
    out=np.zeros(4)
    for lo,hi,a,b in blocks:
        out[lo:hi+1]=np.clip(a/b,0,1)
    if (np.diff(out)>1e-12).any():
        raise ValueError("HOLD_MONOTONE")
    return out

def calibration(a,seed):
    """Construct chronological source-A out-of-year correction targets."""
    q=[]
    for yr in CAL_YEARS:
        for half in (0,1):
            t=a.loc[a.year.eq(yr)&a.half.eq(half)].copy()
            h=a.loc[a.year.lt(yr)&a.half.ne(half),["horse","sire_id","year","half","occupancy","base_own"]].copy()
            h["difference"]=h.occupancy-h.base_own
            p,_=predict_fold(h,t[["horse","sire_id","year","half"]],seed)
            p=p.set_index("horse").reindex(t.horse)
            if p[["M0","M1"]].isna().any().any():
                raise ValueError("HOLD_CALIBRATION_JOIN")
            t["r"]=t.occupancy.to_numpy()-t.base_own.to_numpy()-p.M0.to_numpy()
            t["d"]=p.M1.to_numpy()-p.M0.to_numpy()
            t["B"]=t.base_own.to_numpy()+p.M0.to_numpy()
            t["M"]=t.base_own.to_numpy()+p.M1.to_numpy()
            q.append(t)
    p=pd.concat(q,ignore_index=True)
    if p.duplicated(["horse","year"]).any() or set(p.year)!=set(CAL_YEARS):
        raise ValueError("HOLD_CALIBRATION_KEYS")
    if p.groupby("year",observed=True).size().to_dict()!={2020:7381,2021:7276}:
        raise ValueError("HOLD_CALIBRATION_DENOMINATOR")
    return p

def fit_weights(cal,eval_half,cutoff):
    """Fit only earlier A calibration years and opposite horse half.

    Repeated annual outcomes weighted so each training horse contributes
    equal total weight. Donor profiles and baselines may share histories;
    this is not full source or sample independence.
    """
    h=cal.loc[cal.year.lt(cutoff)&cal.half.ne(eval_half)].copy()
    if h.empty or h.year.max()>=cutoff:
        raise ValueError("HOLD_WEIGHT_TIME")
    w=1/h.groupby("horse",observed=True).horse.transform("size").to_numpy(float)
    k=count_bin(h.prior_count)
    d=h.d.to_numpy(float);r=h.r.to_numpy(float)
    den=[];num=[];support=[]
    for j in range(4):
        m=k==j
        # Only nonzero corrections identify a slope; support gate counts them.
        m_info=m&(np.abs(d)>1e-12)
        horses=int(h.loc[m_info,"horse"].nunique())
        sires=int(h.loc[m_info,"sire_id"].nunique())
        a=float(np.sum(w[m]*d[m]*r[m]));b=float(np.sum(w[m]*d[m]**2))
        if horses<MIN_HORSES or sires<MIN_SIRES or b<=1e-12:
            raise ValueError("HOLD_CALIBRATION_BIN_SUPPORT")
        num.append(a);den.append(b)
        support.append({"bin":BINS[j],"rows":int(m.sum()),"informative_horses":horses,
                        "informative_sires":sires,"unconstrained":a/b})
    monotone=decreasing_projection(num,den)
    pooled=float(np.clip(sum(num)/sum(den),0,1))
    return {"training_years":sorted(int(x) for x in h.year.unique()),
            "calibration_horses":int(h.horse.nunique()),"monotone":monotone.tolist(),
            "pooled":pooled,"support":support}

def apply_weights(t,base,full,count,weights):
    x=t.copy()
    k=count_bin(x[count])
    d=x[full].to_numpy(float)-x[base].to_numpy(float)
    g=np.zeros(len(x));p=np.zeros(len(x))
    for half in (0,1):
        m=x.half.eq(half).to_numpy()
        w=weights[str(half)]
        g[m]=np.asarray(w["monotone"])[k[m]]
        p[m]=w["pooled"]
    x["N"]=x[base]
    x["F"]=x[full]
    x["P"]=x.N+p*d
    x["H"]=x.N+(k==0)*d
    x["G"]=x.N+g*d
    x["count_bin"]=k
    x["gate_weight"]=g
    return x

def score(t,seed):
    if t.empty:
        return {"status":"HOLD_EMPTY","horses":0}
    if t.horse.duplicated().any() or not np.isfinite(t[["N","F","P","H","G","occupancy"]]).all().all():
        raise ValueError("HOLD_SCORE")
    y=t.occupancy.to_numpy(float)
    l={k:(y-t[k].to_numpy(float))**2 for k in ("N","F","P","H","G")}
    result={"horses":len(t),"sires":int(t.sire_id.nunique()),
            "RMSE":{k:float(np.sqrt(v.mean())) for k,v in l.items()},
            "mean_gate_weight":float(t.gate_weight.mean()),"contrasts":{}}
    for a,b in (("N","F"),("N","P"),("N","H"),("N","G"),("F","G"),("P","G"),("H","G")):
        result["contrasts"][a+"_minus_"+b]=ci(t,l[a]-l[b],seed)
    return result

def groups(t,seed):
    return {"all":score(t,seed),**{label:score(t.loc[t.count_bin.eq(j)],seed) for j,label in enumerate(BINS)}}

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
    t,qa=target_occupancy(strict,circuit)
    if t.groupby("year",observed=True).size().to_dict()!={2022:3011,2023:1588,2024:743}:
        raise ValueError("HOLD_TARGET_PARITY")
    result={}
    for seed in SEEDS:
        a,ref=source_a_reference(old,seed)
        cal=calibration(a,seed)
        # Source-A 2021 check: fit weights on 2020 only.
        early={str(half):fit_weights(cal,half,2021) for half in (0,1)}
        early_target=cal.loc[cal.year.eq(2021)].copy()
        e=apply_weights(early_target,"B","M","prior_count",early)
        if seed==SEEDS[0] and abs(score(e,seed)["contrasts"]["N_minus_F"]["MSE_gain"]-.01471092236633107)>1e-10:
            raise ValueError("HOLD_PR81_PARITY")
        # No B observations in any calibrated weight, including late years.
        weights={str(half):fit_weights(cal,half,2022) for half in (0,1)}
        b=update_own(old,source_a_baseline(old,t,seed),seed)
        result[str(seed)]={"A2021_weights":early,"A2021":groups(e,seed),
                           "frozen_A_weights":weights,"B":{}}
        for yr in B_YEARS:
            z=predictions(a,b,yr,seed)
            if seed==SEEDS[0] and yr==2024:
                l=(z.occupancy-z.B11)**2-(z.occupancy-z.M11)**2
                if abs(l.mean()+.009304296089139295)>1e-10:
                    raise ValueError("HOLD_PR86_PARITY")
            out={}
            for state,base,full,count in (("stale","B00","M00","own_prior_count"),
                    ("refreshed","B11","M11","refreshed_own_n")):
                x=apply_weights(z,base,full,count,weights)
                out[state]=groups(x,seed)
            result[str(seed)]["B"][str(yr)]=out
    return {"status":"RETROSPECTIVE_SOURCE_A_CALIBRATED_INFORMATION_SUBSTITUTION",
            "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
            "circuit_gate":cqa,"strict_gate":sqa,"target_scope":qa,
            "primary":"20261124/B/2024/refreshed/all/N_minus_G",
            "calibration_years":list(CAL_YEARS),"bins":list(BINS),"results":result,
            "limitations":["B results already inspected in PR85/86; new post-hoc hypothesis, not pristine prospective test.",
             "Weight fitting uses only A outcomes; opposite horse-half calibration does not remove shared historical records or deeper pedigree.",
             "The monotone nonnegative correction is a prespecified model constraint, not proof of a monotone biological effect.",
             "B updates use completed earlier observed years; missing starts and new entrants excluded.",
             "Unbounded scores preserve PR85/86 parity; not calibrated probabilities.",
             "Whole-sire pointwise intervals conditional on fitted predictions; no simultaneous or all-dependence inference.",
             "Observed allocation, not genetic causation, animal habitat choice, absolute performance, or wagering. No individual data exported."]}

def self_test():
    assert np.array_equal(count_bin([0,1,3,4,7,8,20]),[0,1,1,2,2,3,3])
    assert np.allclose(decreasing_projection([2,.1,.6,-1],[1,1,1,1]),[1,.35,.35,0])
    assert np.allclose(decreasing_projection([.3,.4,.5,.6],[1,1,1,1]),.45)
    t=pd.DataFrame({"horse":["a","b","c","d"],"sire_id":["s","s","t","t"],"half":[0,0,1,1],
                    "n":[0,3,4,9],"base":[.4]*4,"full":[.6]*4,"occupancy":[0.,1.,0.,1.]})
    w={str(k):{"monotone":[1,.5,.25,0],"pooled":.4} for k in (0,1)}
    z=apply_weights(t,"base","full","n",w)
    assert np.allclose(z.G,[.6,.5,.45,.4])
    assert np.allclose(z.H,[.6,.4,.4,.4])
    assert np.allclose(z.P,.48)
    q=apply_weights(t.assign(occupancy=1-t.occupancy),"base","full","n",w)
    assert np.array_equal(z.G,q.G)
    # Zero signal preserves the no-kin estimate irrespective of weights.
    assert np.allclose(apply_weights(t.assign(full=t.base),"base","full","n",w).G,t.base)
    print("synthetic count bins, bounded monotone fit, prediction and outcome invariance passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path);p.add_argument("--sqlite",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.archive,a.sqlite,a.output)):
        p.error("archive, sqlite and output required")
    r=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    compact={}
    for s,v in r["results"].items():
        compact[s]={"A2021_weights":v["A2021_weights"],"A2021":v["A2021"]["all"],
                    "frozen_A_weights":v["frozen_A_weights"],"B":{}}
        for y,g in v["B"].items():
            compact[s]["B"][y]={k:w["all"] for k,w in g.items()}
            if s==str(SEEDS[0]):
                compact[s]["B"][y]["refreshed_bins"]=g["refreshed"]
    print(json.dumps({"status":r["status"],"primary":r["primary"],"results":compact},allow_nan=False))

if __name__=="__main__":
    main()
