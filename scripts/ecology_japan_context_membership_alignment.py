#!/usr/bin/env python3
"""Direct source replay of membership-related weighting heterogeneity.
Retrospective, selected archive cohorts; no individual identifiers exported.
Bootstrap whole sire across years, membership strata, history strata.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
from ecology_japan_context_transitional_heterogeneity import (
    YEARS, SEEDS, same, frame, common_panels, load_sources, SQLITE_SHA, SOURCE_SHA,
    audit_circuits, strict_mask_exact_horse_race, target_occupancy, source_a_reference,
    source_a_baseline, update_own, predictions, DRAWS, MIN_HORSES, MIN_SIRES,
    MIN_VALID_DRAWS, GROUPS, PROFILES,
)
ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"docs/evidence/information-heterogeneity-membership-mechanics-20261126.json"
PARTS=("proportions","energy","alignment_per_energy","total")
CONTRASTS=("peak_discrepancy","alignment_component_change")

def state(s):
    """s: [..., history stratum, n/sum(rd)/sum(d^2)]"""
    n,A,E=np.moveaxis(s,-1,0)
    if not (np.isfinite(s).all() and (n>0).all() and (E>1e-12).all()):
        raise ValueError("HOLD_EMPTY_OR_ZERO_ENERGY")
    return n/n.sum(axis=-1,keepdims=True),E/n,A/E

def H(p,e,r):
    a=e*r
    w=np.clip(r,0,1)
    A=(p*a).sum(axis=-1);E=(p*e).sum(axis=-1)
    W=np.clip(A/E,0,1)
    return (p*(2*w*a-w*w*e)).sum(axis=-1)-(2*W*A-W*W*E)

def shapley(common,annual):
    X=state(common);Y=state(annual)
    vals=[H(*(Y[i] if mask&(1<<i) else X[i] for i in range(3))) for mask in range(8)]
    z=[]
    for i in range(3):
        a=np.zeros_like(vals[0])
        for mask in range(8):
            if not mask&(1<<i):
                k=mask.bit_count()
                a+=(1/6 if k==1 else 1/3)*(vals[mask|(1<<i)]-vals[mask])
        z.append(a)
    total=vals[7]-vals[0]
    same(sum(z),total,"SHAPLEY_CLOSURE")
    return np.stack([*z,total],axis=-1),vals[0],vals[7]

def measures(s):
    """s: [..., year, membership=2, history=2, statistic=3].
    Membership 0=all-three-years, 1=annual complement.
    """
    common=s[...,0,:,:]
    other=s[...,1,:,:]
    annual=common+other
    phi,hc,ha=shapley(common,annual)
    delta=phi[...,1,:]-phi[...,0,:]
    # Four-cell contrast of unconstrained scalar slopes in 2023.
    # Positive = complement-common difference larger in low-history group.
    _,_,r0=state(common);_,_,r1=state(other)
    gap=r1-r0
    interaction=gap[...,1,0]-gap[...,1,1]
    return {"phi":phi,"H_common":hc,"H_annual":ha,"peak_discrepancy":delta[...,3],
            "alignment_component_change":delta[...,2],"interaction_2023":interaction,
            "common_r":r0,"complement_r":r1}

def make_cube(panels,partition,profile):
    common=common_panels(panels)
    ids=set(common[0].index)
    # Shared sire clusters even for horses present in only one of the years.
    sires=sorted(set().union(*(set(p.sire_id) for p in panels.values())))
    if "" in sires:raise ValueError("HOLD_UNKNOWN_SIRE")
    smap={s:i for i,s in enumerate(sires)}
    cube=np.zeros((len(sires),3,2,2,3),float)
    support=[]
    for j,y in enumerate(YEARS):
        p=panels[y]
        if p.horse.duplicated().any():raise ValueError("HOLD_DUPLICATE_HORSE")
        k=p.sire_id.map(smap).to_numpy(int)
        m=~p.horse.isin(ids).to_numpy()
        n=p.own_prior_count.to_numpy(float)
        hist=n>0 if partition=="zero_vs_positive" else n>3
        if profile=="fixed":
            d=p.d.to_numpy(float);r=(p.r-p.u).to_numpy(float)
        else:
            d=(p.M11-p.B11).to_numpy(float);r=(p.occupancy-p.B11).to_numpy(float)
        if not np.isfinite(d).all() or not np.isfinite(r).all():raise ValueError("HOLD_NONFINITE")
        yr=[]
        for a in range(2):
            hh=[]
            for b in range(2):
                z=(m==bool(a))&(hist==bool(b))
                np.add.at(cube[:,j,a,b,0],k[z],1.)
                np.add.at(cube[:,j,a,b,1],k[z],(r*d)[z])
                np.add.at(cube[:,j,a,b,2],k[z],(d*d)[z])
                hh.append({"horses":int(z.sum()),"sires":int(len(np.unique(k[z])))})
            yr.append(hh)
        support.append(yr)
        same(cube[:,j,:,:,0].sum(),len(p),"ANNUAL_COUNT")
        same(cube[:,j,0,:,0].sum(),len(ids),"COMMON_COUNT")
    if profile=="fixed":
        same(cube[:,1:,0,:,2],np.repeat(cube[:,:1,0,:,2],2,axis=1),"COMMON_FIXED_ENERGY")
    return cube,support

def check_reference(stat,seed,profile,reference):
    """Directly reproduce the recovered group counts and moments."""
    q=[x for x in reference["rows"] if x["seed"]==str(seed) and x["profile"]==profile]
    if len(q)!=3:raise ValueError("HOLD_REFERENCE_KEYS")
    q=sorted(q,key=lambda x:x["year"])
    for j,v in enumerate(q):
        for g,name in ((0,"common"),(1,"not_observed_all_three_years")):
            for k,z in enumerate(v[name]["groups"]):
                n,a,e=stat[j,g,k]
                same(n,z["n"],"RECOVERED_N")
                same(a/n,z["A"],"RECOVERED_A")
                same(e/n,z["E"],"RECOVERED_E")
        x=measures(stat)
        same(x["phi"][j],[v["decomposition"][k] for k in PARTS],"RECOVERED_SHAPLEY")
        same(x["H_common"][j],v["H_common"],"RECOVERED_H_COMMON")
        same(x["H_annual"][j],v["H_all"],"RECOVERED_H_ALL")

def score(cube,support,seed):
    stat=cube.sum(axis=0)
    # Require the same full cell support in each year and each membership
    # group. All three years retained; no opportunistic omission.
    if (stat[...,0]<=0).any() or (stat[...,2]<=1e-12).any():
        return {"status":"HOLD_EMPTY_OR_ZERO_ENERGY","support":support}
    x=measures(stat)
    out={"status":"DESCRIPTIVE","support":support,
         "point":{k:np.asarray(v).tolist() for k,v in x.items()},
         "direct_cell_moments":(stat[...,1:]/stat[...,0,None]).tolist(),
         "moment_columns":["mean_rd","mean_d2"],"phi_columns":list(PARTS)}
    if any(g["horses"]<MIN_HORSES or g["sires"]<MIN_SIRES for year in support for mem in year for g in mem):
        out["status"]="HOLD_LOW_CELL_SUPPORT";return out
    # Same sire draw for all times and membership/history cells, and same
    # weight for each horse from that cluster. No raw rows exported.
    rng=np.random.default_rng(seed)
    ix=rng.integers(len(cube),size=(DRAWS,len(cube)))
    boot=cube[ix].sum(axis=1)
    valid=(boot[...,0]>0).all(axis=(1,2,3))&(boot[...,2]>1e-12).all(axis=(1,2,3))
    out["valid_draws"]=int(valid.sum())
    if valid.sum()<MIN_VALID_DRAWS:
        out["status"]="HOLD_BOOTSTRAP_SUPPORT";return out
    b=measures(boot[valid])
    vals=np.column_stack([b[k] for k in CONTRASTS])
    out["contrasts"]=list(CONTRASTS)
    out["pointwise_CI95"]=np.quantile(vals,[.025,.975],axis=0).T.tolist()
    adj=np.quantile(vals,[.0125,.9875],axis=0).T
    out["two_contrast_adjusted_CI97_5"]=adj.tolist()
    out["joint_positive"]=bool((adj[:,0]>0).all())
    out["interaction_2023_pointwise_CI95"]=np.quantile(b["interaction_2023"],[.025,.975]).tolist()
    return out

def analyze(archive,db):
    reference=json.loads(REFERENCE.read_text())
    raw,old,future,_,gate,_=load_sources(archive,db)
    if len(old)!=2092836 or old.horse.nunique()!=90962 or len(future)!=255484 or future.horse.nunique()!=12919:
        raise ValueError("HOLD_SOURCE_PARITY")
    circuit,cqa=audit_circuits(raw,old,db,gate["two_event_anchor_horses"])
    if cqa.get("verified_JRA_codes")!=10 or cqa.get("verified_NAR_codes")!=14 or cqa["matched_distinct_pre2022_source_B_races"]!=85856:
        raise ValueError("HOLD_CIRCUIT_PARITY")
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
        common=common_panels(panels)
        if len(common[0])!=527 or common[0].sire_id.nunique()!=115:raise ValueError("HOLD_COMMON_PARITY")
        result={}
        for partition in GROUPS:
            result[partition]={}
            for profile in PROFILES:
                cube,support=make_cube(panels,partition,profile)
                if partition=="zero_vs_positive":
                    check_reference(cube.sum(axis=0),seed,profile,reference)
                result[partition][profile]=score(cube,support,seed)
        out[str(seed)]=result
    return {"status":"RETROSPECTIVE_DIRECT_MEMBERSHIP_ALIGNMENT_UNCERTAINTY",
            "primary":"20261124/zero_vs_positive/fixed/2022_to_2023_peak_discrepancy_and_alignment_component",
            "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,"target_scope":qa,
            "direct_reconstruction_parity":"ALL_18_ZERO_VS_POSITIVE_SEED_YEAR_PROFILE_CONDITIONS",
            "support_gate":{"horses_per_cell":MIN_HORSES,"sires_per_cell":MIN_SIRES,"valid_draws":MIN_VALID_DRAWS},
            "years":list(YEARS),"membership_order":["common_three_years","not_common_three_years"],
            "history_order":{"zero_vs_positive":["0","1+"],"0_to_3_vs_4_plus":["0-3","4+"]},
            "results":out,
            "limitations":["Retrospective after previously inspected same-source results, not independent data.",
                "H uses evaluated outcomes; no forecast or causal selection effect.",
                "Sire bootstrap conditional on fixed prediction profiles and observed membership; no refit, no joint race/day/deep-pedigree dependence.",
                "Support per all 12 cells; if fails no interval. Sensitivities do not replace primary.",
                "Alignment per energy is A/E, not a correlation, genetic or learning parameter. Shapley hybrids arithmetic only.",
                "No private horse/sire IDs or individual observations in output."]}

def self_test():
    # Construct fictional clusters with stable membership and two strata.
    # All 40 clusters contribute 3 horses per cell. Annual low-history
    # complement has a high ratio in 2023 while common ratios converge.
    cube=np.zeros((40,3,2,2,3))
    for y in range(3):
        for g in range(2):
            for h in range(2):
                r=((.8,.4),(.5,.4),(.3,.25))[y][h]
                if y==1 and g==1 and h==0:r=1.1
                cube[:,y,g,h,:]=[3,3*r,3]
    support=[[[{"horses":120,"sires":40} for _ in range(2)] for _ in range(2)] for _ in range(3)]
    x=score(cube,support,123)
    assert x["joint_positive"]
    assert x["point"]["interaction_2023"]>0
    support[0][0][0]["horses"]=99
    y=score(cube,support,123)
    assert y["status"]=="HOLD_LOW_CELL_SUPPORT" and "two_contrast_adjusted_CI97_5" not in y
    # Identical annual/complement profiles: no membership-induced change.
    c=cube.copy();c[:,:,1,:,:]=c[:,:,0,:,:]
    q=measures(c.sum(axis=0))
    same(q["phi"],np.zeros((3,4)),"IDENTICAL_PROFILE")
    print("synthetic membership Shapley closure, paired cluster support and clipping checks passed")

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
