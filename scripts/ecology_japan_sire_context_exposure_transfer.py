#!/usr/bin/env python3
"""Retrospective family-associated context occupancy vs paired rank response.

Uses the PR80 opposite-half chronological transfer evaluator without changing
its primary result. Occupancy means the fraction of observed eligible starts
on turf, conditional on having at least one eligible start in a year.
No causal habitat preference, absolute speed, or wagering model.
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
from ecology_japan_sire_context_time_transfer import evaluate

YEARS=(2019,2020,2021)
OWN_SHRINK=5.
TRAINER_SHRINK=8.

def historical_panel(old, seed, strict_trainer=False):
    """Build chronological occupancy residuals, with one horse-year per row.

    Keep all eligible classified starts, never use target starts to compute
    own prior or trainer prior. In the strict sensitivity retain only records
    whose globally assigned trainer and horse halves agree, even in history.
    """
    x=old.loc[old.circuit.eq("JRA") & old.stratum.isin(CONTEXTS),
              ["horse","sire_id","trainer_id","day","year","race","stratum"]].copy()
    for k in ("horse","sire_id","trainer_id","race","stratum"):
        x[k]=x[k].astype(str)
    x=x.loc[x.sire_id.ne("")].copy()
    if x.horse.eq("").any() or x.day.isna().any() or x.duplicated(["horse","race"]).any():
        raise ValueError("HOLD_IDENTITY")
    if x.groupby("horse",observed=True).sire_id.nunique().max()>1:
        raise ValueError("HOLD_PARENT_CONFLICT")
    x["half"]=_hash_half(x.horse,seed,"horse")
    if strict_trainer:
        x=x.loc[x.trainer_id.ne("")].copy()
        x=x.loc[x.half.to_numpy()==_hash_half(x.trainer_id,seed,"trainer")].copy()
        if x.groupby("trainer_id",observed=True).half.nunique().max()>1:
            raise ValueError("HOLD_TRAINER_OVERLAP")
    x["turf"]=x.stratum.eq(CONTEXTS[0]).astype(float)
    result=[]
    for y in YEARS:
        prior=x.loc[x.year.lt(y)]
        target=x.loc[x.year.eq(y)]
        if prior.empty or target.empty:
            raise ValueError("HOLD_EMPTY_YEAR")
        if prior.day.max()>=target.day.min():
            raise ValueError("HOLD_TIME_OVERLAP")
        # Target turf fraction is the response, not a baseline feature.
        t=target.groupby(["horse","sire_id","half"],observed=True).turf.agg(["mean","size"]).reset_index()
        t=t.rename(columns={"mean":"occupancy","size":"target_starts"})
        if t.horse.duplicated().any():
            raise ValueError("HOLD_TARGET_DUPLICATE")
        # Equal-horse global prior per historical half, and own exact counts.
        a=prior.groupby(["horse","half"],observed=True).turf.agg(["mean","size"]).reset_index()
        global_mean=a.groupby("half",observed=True)["mean"].mean()
        own=a.set_index("horse")
        n=t.horse.map(own["size"]).fillna(0).to_numpy(float)
        p=t.horse.map(own["mean"]).fillna(0).to_numpy(float)
        g=t.half.map(global_mean).to_numpy(float)
        if not np.isfinite(g).all():
            raise ValueError("HOLD_HALF_PRIOR")
        t["prior_count"]=n.astype(int)
        t["base_own"]=(n*p+OWN_SHRINK*g)/(n+OWN_SHRINK)
        # Last known trainer prior (not the trainer on the current target),
        # using equal horse contributions and subtracting the focal horse.
        last=prior.sort_values(["day","race","horse"],kind="mergesort").drop_duplicates("horse",keep="last").set_index("horse").trainer_id
        tr=t.horse.map(last).fillna("")
        peer=prior.loc[prior.trainer_id.ne("")].groupby(["trainer_id","horse"],observed=True).turf.mean()
        totals=peer.groupby(level=0).agg(["sum","size"])
        peer_sum=tr.map(totals["sum"]).fillna(0).to_numpy(float)
        peer_n=tr.map(totals["size"]).fillna(0).to_numpy(float)
        focal=peer.reindex(pd.MultiIndex.from_arrays([tr,t.horse]))
        peer_n-=focal.notna().to_numpy(float)
        peer_sum-=focal.fillna(0).to_numpy(float)
        if (peer_n<0).any() or (peer_sum< -1e-10).any() or (peer_sum-peer_n>1e-10).any():
            raise ValueError("HOLD_TRAINER_PEER_EXCLUSION")
        prior_trainer=(peer_sum+TRAINER_SHRINK*g)/(peer_n+TRAINER_SHRINK)
        t["base_own_trainer"]=(n*p+OWN_SHRINK*prior_trainer)/(n+OWN_SHRINK)
        t["trainer_peers"]=peer_n.astype(int)
        t["year"]=y
        result.append(t)
    p=pd.concat(result,ignore_index=True)
    for k in ("occupancy","base_own","base_own_trainer"):
        if not np.isfinite(p[k]).all() or not p[k].between(0,1).all():
            raise ValueError("HOLD_OCCUPANCY_VALUE")
    return p

def occupancy_qa(p):
    z={}
    for year in YEARS:
        t=p.loc[p.year.eq(year)]
        z[str(year)]={"horse_years":len(t),"sires":int(t.sire_id.nunique()),
            "starts":int(t.target_starts.sum()),"turf_only":int(t.occupancy.eq(1).sum()),
            "dirt_only":int(t.occupancy.eq(0).sum()),
            "both_surfaces":int(t.occupancy.between(0,1,inclusive="neither").sum()),
            "no_own_prior":int(t.prior_count.eq(0).sum()),
            "with_prior_trainer_peers":int(t.trainer_peers.gt(0).sum()),
            "horse_equal_mean_turf_fraction":float(t.occupancy.mean())}
    return z

def evaluate_exposure(p, seed, name):
    # PR80's evaluator scores residuals, with zero = the baseline specified
    # here, M0 = add training-only global residual, M1 = shrunk same-sire
    # residual. Linear MSE is unchanged by adding back base_own; no probability
    # calibration or clipping is claimed. P = matched other-sire residual.
    q=p[["horse","sire_id","half","year"]].copy()
    q["difference"]=p.occupancy-p[name]
    return {str(y):evaluate(q,y,seed) for y in (2020,2021)}

def analyze(archive):
    from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame
    with archive.open("rb") as f:
        digest=hashlib.file_digest(f,"sha256").hexdigest()
    if digest!=SOURCE_SHA:
        raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw)
    if len(old)!=2092836 or old.horse.nunique()!=90962:
        raise ValueError("HOLD_SOURCE_PARITY")
    old["stratum"]=old.surface.astype(str)+":"+(old.distance//400).astype(int).astype(str)
    candidate=old.loc[old.year.isin(YEARS)&old.circuit.eq("JRA")&old.stratum.isin(CONTEXTS)]
    if len(candidate)!=57208 or candidate.horse.nunique()!=15129:
        raise ValueError("HOLD_PR80_CANDIDATE_PARITY")
    out={}
    for strict in (False,True):
        mode="horse_and_trainer_disjoint" if strict else "horse_disjoint"
        out[mode]={}
        for seed in SEEDS:
            p=historical_panel(old,seed,strict)
            qa=occupancy_qa(p)
            if not strict and sum(v["both_surfaces"] for v in qa.values())!=3031:
                raise ValueError("HOLD_PR80_PAIRED_PARITY")
            out[mode][str(seed)]={"occupancy_support":qa,
                    "own_history":evaluate_exposure(p,seed,"base_own"),
                    "own_and_last_trainer_history":evaluate_exposure(p,seed,"base_own_trainer")}
    return {"status":"RETROSPECTIVE_FAMILY_CONTEXT_OCCUPANCY_TRANSFER",
            "source_A_sha256":digest,"candidate_starts":len(candidate),
            "candidate_horses":int(candidate.horse.nunique()),"results":out,
            "primary":"horse_disjoint/20261124/2021/own_history/all_targets/M0_minus_M1",
            "own_shrink":OWN_SHRINK,"trainer_shrink":TRAINER_SHRINK,
            "limitations":["Historically inspected source; not new prospective validation.",
                "Occupancy is observed turf-start fraction among eligible observed JRA starts; not habitat choice, fitness or genetically caused preference.",
                "The own and last-trainer baseline uses only previous calendar years; residual predictions are unbounded linear scores, not calibrated probabilities.",
                "Opposite horse halves and strict trainer sensitivity as PR80; global prior computed within half, shared historical cohort dependence remains.",
                "Trainer-disjoint row thinning changes the occupancy denominator.",
                "Occupancy and paired rank response have different endpoints and support; their raw MSE gains cannot be directly compared.",
                "Sire bootstrap is a conditional pointwise sensitivity; other-sire matching is count-only, not genomic unrelatedness.",
                "No individual records, wagering, or causal inference."]}

def self_test():
    rows=[]
    for y in (2018,2019,2020,2021):
        for i in range(24):
            for c,ctx in enumerate(CONTEXTS):
                rows.append(dict(horse=f"h{i}",sire_id=f"s{i%3}",trainer_id=f"t{i%7}",
                   day=pd.Timestamp(f"{y}-01-0{c+1}"),year=y,race=f"{y}-{c}",stratum=ctx,circuit="JRA"))
    x=pd.DataFrame(rows)
    p=historical_panel(x,SEEDS[0])
    assert len(p)==72 and np.allclose(p.occupancy,.5)
    assert np.allclose(p.base_own,.5) and np.allclose(p.base_own_trainer,.5)
    xx=x.copy()
    xx.loc[xx.year.eq(2021),"stratum"]=CONTEXTS[0]
    p2=historical_panel(xx,SEEDS[0])
    a=p.loc[p.year.eq(2021)].sort_values("horse")
    b=p2.loc[p2.year.eq(2021)].sort_values("horse")
    assert np.allclose(a.base_own,b.base_own)
    assert np.allclose(a.base_own_trainer,b.base_own_trainer)
    assert np.allclose(b.occupancy,1)
    assert occupancy_qa(p)["2021"]["both_surfaces"]==24
    assert occupancy_qa(p2)["2021"]["turf_only"]==24
    pd.testing.assert_frame_equal(p,historical_panel(x.sample(frac=1,random_state=7),SEEDS[0]))
    s=historical_panel(x,SEEDS[0],True)
    assert len(s)>0
    print("synthetic prior-only occupancy, invariance, and trainer exclusion checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not a.archive or not a.output:
        p.error("archive and output required")
    r=analyze(a.archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    # Emit compact group-level evidence, full receipt saved separately.
    compact={}
    for mode,seeds in r["results"].items():
        compact[mode]={}
        for seed,v in seeds.items():
            compact[mode][seed]={"occupancy_support":v["occupancy_support"]}
            for model in ("own_history","own_and_last_trainer_history"):
                compact[mode][seed][model]={y:{"total_targets":k["total_targets"],
                    "supported_targets":k["supported_targets"],"matched_targets":k["matched_targets"],
                    "all_targets":k["all_targets"],"matched_targets_scores":k["matched_targets_scores"]}
                    for y,k in v[model].items()}
    print(json.dumps({"status":r["status"],"source_A_sha256":r["source_A_sha256"],
        "candidate_starts":r["candidate_starts"],"candidate_horses":r["candidate_horses"],
        "primary":r["primary"],"results":compact},allow_nan=False))

if __name__=="__main__":
    main()
