#!/usr/bin/env python3
"""Same-horse transitional heterogeneity test on pinned historical archives.
Posthoc relative to inspected annual aggregates; no individual exports.
Fixed original correction primary, refreshed profile separate sensitivity.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_context_within_individual import (
    YEARS, SEEDS, same, frame, load_sources, SQLITE_SHA, SOURCE_SHA,
    audit_circuits, strict_mask_exact_horse_race, target_occupancy,
    source_a_reference, source_a_baseline, update_own, predictions,
)
DRAWS=999
MIN_HORSES=100
MIN_SIRES=30
MIN_VALID_DRAWS=950
GROUPS=("zero_vs_positive","0_to_3_vs_4_plus")
PROFILES=("fixed","refreshed")

def summaries(stat):
    """Inputs [..., years=3, groups=2, (n,sum(r*d),sum(d^2))]."""
    n=stat[...,0]
    a=stat[...,1]
    e=stat[...,2]
    if not (np.isfinite(stat).all() and (n>0).all() and (e>1e-12).all()):
        raise ValueError("HOLD_EMPTY_OR_ZERO_ENERGY")
    N=n.sum(axis=-1)
    A=a.sum(axis=-1)
    E=e.sum(axis=-1)
    r=a/e
    R=A/E
    w=np.clip(r,0,1)
    W=np.clip(R,0,1)
    separate=(2*w*a-w*w*e).sum(axis=-1)/N
    pooled=(2*W*A-W*W*E)/N
    H=separate-pooled
    variance=(e*(r-R[...,None])**2).sum(axis=-1)/N
    clip=(e*(w-r)**2).sum(axis=-1)/N-E*(W-R)**2/N
    same(H,variance-clip,"HETEROGENEITY_IDENTITY")
    if (H < -1e-10).any():
        raise ValueError("HOLD_NEGATIVE_H")
    return H,w,W,separate,pooled

def score_clusters(cube,groups,seed,support):
    stat=cube.sum(axis=0)
    H,w,W,sep,pool=summaries(stat)
    point=np.array([H[1]-H[0],H[1]-H[2]])
    r={"status":"DESCRIPTIVE","years":list(YEARS),"group_labels":groups,
       "stratum_support":support,"H":H.tolist(),"stratified_weights":w.tolist(),
       "pooled_weights":W.tolist(),"stratified_oracle_gain":sep.tolist(),"pooled_oracle_gain":pool.tolist(),
       "peak_contrasts":{"2023_minus_2022":float(point[0]),"2023_minus_2024":float(point[1])},
       "both_point_positive":bool((point>0).all())}
    # Earlier-year weights applied to later-year moments on identical
    # selected future-common horses. Not a prospective result; current
    # year labels are not used to select that year's weights.
    transfer={}
    for i,j in ((0,1),(1,2)):
        n=stat[j,:,0].sum();a=stat[j,:,1];e=stat[j,:,2]
        v=(2*w[i]*a-w[i]**2*e).sum()/n
        q=(2*W[i]*a-W[i]**2*e).sum()/n
        transfer[f"{YEARS[i]}_to_{YEARS[j]}"]={"pooled_gain":float(q),
            "two_stratum_gain":float(v),"stratified_minus_pooled":float(v-q)}
    r["earlier_year_weight_transfer_selected_common_cohort"]=transfer
    if any(x["horses"]<MIN_HORSES or x["sires"]<MIN_SIRES for x in support):
        r["status"]="HOLD_LOW_STRATUM_SUPPORT"
        r["peak_inference"]="HOLD"
        return r
    rng=np.random.default_rng(seed)
    draws=rng.integers(len(cube),size=(DRAWS,len(cube)))
    boot=cube[draws].sum(axis=1)
    valid=(boot[...,0]>0).all(axis=(1,2))&(boot[...,2]>1e-12).all(axis=(1,2))
    r["valid_draws"]=int(valid.sum())
    if valid.sum()<MIN_VALID_DRAWS:
        r["status"]="HOLD_BOOTSTRAP_SUPPORT";r["peak_inference"]="HOLD";return r
    h,*_=summaries(boot[valid])
    d=np.column_stack((h[:,1]-h[:,0],h[:,1]-h[:,2]))
    pointwise=np.quantile(d,[.025,.975],axis=0).T
    adjusted=np.quantile(d,[.0125,.9875],axis=0).T
    r["pointwise_CI95"]=pointwise.tolist()
    r["two_contrast_bonferroni_percentile_CI97_5"]=adjusted.tolist()
    r["peak_inference"]="BOTH_LOWER_BOUNDS_POSITIVE" if (adjusted[:,0]>0).all() else "NOT_ESTABLISHED"
    return r

def common_panels(panels):
    ids=sorted(set.intersection(*(set(p.horse) for p in panels.values())))
    if not ids:raise ValueError("HOLD_EMPTY_COMMON")
    x=[panels[y].set_index("horse").loc[ids].copy() for y in YEARS]
    for a in x[1:]:
        if not a.sire_id.equals(x[0].sire_id) or not a.own_prior_count.equals(x[0].own_prior_count):
            raise ValueError("HOLD_STABLE_ID_OR_BASELINE_COUNT")
        same(a.d,x[0].d,"FIXED_CORRECTION")
        same(a.B00,x[0].B00,"FIXED_BASELINE")
    return x

def cluster_cube(x,partition,profile):
    n0=x[0].own_prior_count.to_numpy(float)
    mask=n0==0 if partition=="zero_vs_positive" else n0<=3
    if profile not in PROFILES or partition not in GROUPS:raise ValueError("HOLD_ANALYSIS_LABEL")
    if not mask.any() or mask.all():return None,None
    sires,cluster=np.unique(x[0].sire_id.to_numpy(str),return_inverse=True)
    if any(s=="" for s in sires):raise ValueError("HOLD_UNKNOWN_SIRE")
    support=[{"horses":int(m.sum()),"sires":int(len(np.unique(cluster[m])))} for m in (mask,~mask)]
    cube=np.zeros((len(sires),3,2,3),float)
    for j,t in enumerate(x):
        if profile=="fixed":
            d=t.d.to_numpy(float);r=(t.r-t.u).to_numpy(float)
        else:
            d=(t.M11-t.B11).to_numpy(float);r=(t.occupancy-t.B11).to_numpy(float)
        for k,m in enumerate((mask,~mask)):
            np.add.at(cube[:,j,k,0],cluster[m],1.)
            np.add.at(cube[:,j,k,1],cluster[m],(r*d)[m])
            np.add.at(cube[:,j,k,2],cluster[m],(d*d)[m])
    if profile=="fixed":same(cube[:,1:,:,2],np.repeat(cube[:,:1,:,2],2,axis=1),"GROUP_FIXED_ENERGY")
    return cube,support

def evaluate(panels,seed):
    x=common_panels(panels)
    if len(x[0])!=527 or x[0].sire_id.nunique()!=115:raise ValueError("HOLD_PR88_COMMON_PARITY")
    out={"common_horses":len(x[0]),"common_sires":int(x[0].sire_id.nunique()),"partitions":{}}
    for part in GROUPS:
        out["partitions"][part]={}
        for prof in PROFILES:
            cube,support=cluster_cube(x,part,prof)
            if cube is None:
                out["partitions"][part][prof]={"status":"HOLD_EMPTY_GROUP"};continue
            labels=["no_prior_A","prior_A"] if part=="zero_vs_positive" else ["0_to_3_prior_A","4_plus_prior_A"]
            out["partitions"][part][prof]=score_clusters(cube,labels,seed,support)
    return out

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
    t,qa=target_occupancy(strict,circuit)
    if t.groupby("year",observed=True).size().to_dict()!={2022:3011,2023:1588,2024:743}:raise ValueError("HOLD_TARGET_PARITY")
    out={}
    for seed in SEEDS:
        a,_=source_a_reference(old,seed)
        b=update_own(old,source_a_baseline(old,t,seed),seed)
        panels={y:frame(predictions(a,b,y,seed)) for y in YEARS}
        if seed==SEEDS[0]:
            same(panels[2022].g_stale.mean(),.001961299416552986,"PR85")
            same(panels[2024].g_fresh.mean(),-.009304296089139295,"PR86")
            common=common_panels(panels)
            same([q.g_own.mean() for q in common],[.01149267179627036,-.005572102049202894,-.017617195217782693],"PR88_COMMON_GAIN")
        out[str(seed)]=evaluate(panels,seed)
    return {"status":"RETROSPECTIVE_COMMON_COHORT_TRANSITIONAL_HETEROGENEITY",
            "primary":"20261124/zero_vs_positive/fixed/both_peak_contrasts",
            "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
            "target_scope":qa,"support_gate":{"horses_per_stratum":MIN_HORSES,"sires_per_stratum":MIN_SIRES},
            "results":out,"limitations":["Prior annual aggregate peak already inspected; no prospective confirmation.",
            "Identical 2022–24 eligible observed horses, not survival or national registry.",
            "Pre-2022 own count groups are fixed, not current no-history or debut.",
            "H is a sample-optimal diagnostic. Earlier-year weights conditional on future common membership are not genuine forecasts.",
            "Paired sire resampling is conditional on selected cohort and fixed model; correction/profile estimates not refit. Two-contrast adjustment within one specification only.",
            "No new data, causal genetic effect, animal learning, or market inference."]}

def self_test():
    # Equal group energy; sample optimal r=.2/.6, .1/.9, .2/.3.
    c=np.zeros((40,3,2,3),float)
    for j,(r,s) in enumerate(((.2,.6),(.1,.9),(.2,.3))):
        c[:,j,0,:]=[3,3*r,3];c[:,j,1,:]=[3,3*s,3]
    support=[{"horses":120,"sires":40}]*2
    o=score_clusters(c,["a","b"],123,support)
    same(o["H"],[.04,.16,.0025],"SYNTHETIC_H")
    assert o["peak_inference"]=="BOTH_LOWER_BOUNDS_POSITIVE"
    assert score_clusters(c,["a","b"],123,[{"horses":99,"sires":40},support[1]])["peak_inference"]=="HOLD"
    # Boundary clipping and weighted covariance identity.
    z=c.copy();z[:,1,0,1]=-3;z[:,1,1,1]=6
    h,*_=summaries(z.sum(axis=0));assert h[1]>=0
    print("synthetic paired-stratum peak, support HOLD and clipping identity passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path);p.add_argument("--sqlite",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.sqlite,a.output)):p.error("archive, sqlite and output required")
    z=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(z,allow_nan=False))

if __name__=="__main__":main()
