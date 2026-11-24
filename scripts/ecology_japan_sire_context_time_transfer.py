#!/usr/bin/env python3
"""Retrospective temporal transfer of within-horse turf-dirt residual differences.

The original PR78 year-forward own/trainer baseline is unchanged.
No date thinning: held years are disjoint from training years, and
horse IDs are disjoint within each of two cross-fitted directions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

from ecology_japan_sire_context_specificity import (
    YEARS, CONTEXTS, SEEDS, baseline, _hash_half,
)
MIN_PEERS=3
SHRINK=8.
MIN_SIRES=30
DRAWS=999
MAX_RATIO=2.

def paired_panel(p, seed, strict_trainer=False):
    cols=["horse","sire_id","trainer_id","year","stratum","residual"]
    if not set(cols).issubset(p):
        raise ValueError("HOLD_PANEL_SCHEMA")
    x=p.loc[p.stratum.isin(CONTEXTS),cols].copy()
    for c in ("horse","sire_id","trainer_id","stratum"):
        x[c]=x[c].astype(str)
    if x.horse.eq("").any() or not np.isfinite(x.residual).all():
        raise ValueError("HOLD_PANEL_VALUES")
    x=x.loc[x.sire_id.ne("")].copy()
    if x.groupby("horse",observed=True).sire_id.nunique().max()>1:
        raise ValueError("HOLD_PARENT_CONFLICT")
    x["half"]=_hash_half(x.horse,seed,"horse")
    if strict_trainer:
        x=x.loc[x.trainer_id.ne("")].copy()
        x=x.loc[x.half.to_numpy()==_hash_half(x.trainer_id,seed,"trainer")].copy()
        if len(x) and x.groupby("trainer_id",observed=True).half.nunique().max()>1:
            raise ValueError("HOLD_TRAINER_LEAK")
    if len(x) and x.groupby("horse",observed=True).half.nunique().max()>1:
        raise ValueError("HOLD_HORSE_LEAK")
    cells=x.groupby(["horse","sire_id","year","half","stratum"],observed=True).residual.mean().unstack("stratum")
    cells=cells.reindex(columns=list(CONTEXTS)).dropna()
    pairs=(cells[CONTEXTS[0]]-cells[CONTEXTS[1]]).rename("difference").reset_index()
    return pairs,{"retained_starts":len(x),"paired_horse_years":len(pairs),
                  "paired_unique_horses":int(pairs.horse.nunique()),
                  "paired_sires":int(pairs.sire_id.nunique())}

def count_match(n, seed):
    """Disjoint training-only sire pairs; support ratio <=2, no outcome input."""
    n=n.loc[n.ge(MIN_PEERS)].sort_index()
    cand=[]
    for i,s in enumerate(n.index):
        for t in n.index[i+1:]:
            ratio=max(n[s],n[t])/min(n[s],n[t])
            if ratio<=MAX_RATIO:
                tie=hashlib.sha256(f"{seed}|{s}|{t}".encode()).hexdigest()
                cand.append((abs(np.log(n[s]/n[t])),tie,s,t))
    match={}
    for _,_,s,t in sorted(cand):
        if s not in match and t not in match:
            match[s]=t; match[t]=s
    return match

def predict_fold(train, target, seed):
    """Train on earlier years, different horses and opposite half.
    
    Target outcome is deliberately not consulted to build predictions.
    Fallback uses the training global mean; never discard unmatched targets
    from the main denominator. Count matching uses the training profiles.
    """
    if train.empty:
        raise ValueError("HOLD_NO_TRAINING_PAIRS")
    if target.empty:
        return pd.DataFrame(),{"target_horses":0}
    if train.year.max()>=target.year.min() or set(train.horse)&set(target.horse):
        raise ValueError("HOLD_TIME_OR_HORSE_OVERLAP")
    if set(train.half)&set(target.half):
        raise ValueError("HOLD_HALF_OVERLAP")
    if target.horse.duplicated().any() or train.groupby("horse").sire_id.nunique().max()>1:
        raise ValueError("HOLD_IDENTITY_CONFLICT")
    # Equal horse weight; average repeated training-year contrasts within horse.
    h=train.groupby(["horse","sire_id"],observed=True).difference.mean().reset_index()
    m=float(h.difference.mean())
    g=h.groupby("sire_id",observed=True).difference.agg(["mean","size"])
    n=g["size"]
    match=count_match(n,seed)
    t=target[["horse","sire_id","year","half"]].copy()
    t["n"]=t.sire_id.map(n).fillna(0).astype(int)
    t["M0"]=m
    t["supported"]=t.n.ge(MIN_PEERS)
    own=t.sire_id.map(g["mean"]).fillna(m)
    shrink=t.n/(t.n+SHRINK)
    t["M1"]=np.where(t.supported,m+shrink*(own-m),m)
    donor=t.sire_id.map(match)
    t["matched"]=donor.notna()&t.supported
    donor_mean=donor.map(g["mean"]).fillna(m)
    # Same recipient support/shrinkage for true and swapped sire profiles.
    t["P"]=np.where(t.matched,m+shrink*(donor_mean-m),np.nan)
    return t,{"training_unique_horses":len(h),"training_sires":int(len(g)),
              "training_supported_sires":int(n.ge(MIN_PEERS).sum()),
              "training_matched_sire_pairs":len(match)//2,
              "target_horses":len(t),"supported_targets":int(t.supported.sum()),
              "matched_targets":int(t.matched.sum()),"training_mean_difference":m}

def _score(t, models, seed):
    if not len(t):
        return {"status":"HOLD_EMPTY"}
    if t.horse.duplicated().any() or not np.isfinite(t[["difference",*models]].to_numpy()).all():
        raise ValueError("HOLD_SCORE_INPUT")
    y=t.difference.to_numpy(float)
    losses={k:(y-t[k].to_numpy(float))**2 for k in models}
    risk={k:float(v.mean()) for k,v in losses.items()}
    n_sires=int(t.sire_id.nunique())
    out={"status":"DESCRIPTIVE" if n_sires>=MIN_SIRES else "HOLD_FEW_SIRES",
         "horses":len(t),"sires":n_sires,"RMSE":{k:float(np.sqrt(v)) for k,v in risk.items()}}
    contrasts={}
    for other in ("M0","P"):
        if other not in models:
            continue
        d=losses[other]-losses["M1"]
        g=pd.DataFrame({"sire":t.sire_id.to_numpy(),"d":d}).groupby("sire",observed=True).d.agg(["sum","size"])
        z={"MSE_gain":float(d.mean())}
        if n_sires>=MIN_SIRES:
            a=g.to_numpy(float)
            rng=np.random.default_rng(seed)
            ix=rng.integers(len(a),size=(DRAWS,len(a)))
            b=a[ix].sum(axis=1)
            z["whole_sire_bootstrap_pointwise_CI95"]=np.quantile(b[:,0]/b[:,1],[.025,.975]).tolist()
        contrasts[other+"_minus_M1"]=z
    out["contrasts"]=contrasts
    return out

def evaluate(panel, year, seed):
    target=panel.loc[panel.year.eq(year)].copy()
    if target.empty:
        return {"status":"HOLD_NO_TARGET_PAIRS"}
    predictions=[]; folds={}
    for half in (0,1):
        train=panel.loc[panel.year.lt(year)&panel.half.ne(half)]
        test=target.loc[target.half.eq(half)]
        if not len(test):
            folds[str(half)]={"target_horses":0}
            continue
        if train.empty:
            return {"status":"HOLD_EMPTY_TRAIN_FOLD","target_horses":len(target)}
        pr,qa=predict_fold(train,test,seed)
        predictions.append(pr)
        folds[str(half)]=qa
    pr=pd.concat(predictions,ignore_index=True)
    if len(pr)!=len(target) or pr.horse.duplicated().any():
        raise ValueError("HOLD_DENOMINATOR")
    z=pr.merge(target[["horse","difference"]],on="horse",how="left",validate="one_to_one")
    z["zero"]=0.
    all_= _score(z,["zero","M0","M1"],seed)
    supported=_score(z.loc[z.supported],["zero","M0","M1"],seed)
    matched=_score(z.loc[z.matched],["zero","M0","M1","P"],seed)
    return {"status":"EVALUATED_RETROSPECTIVE","folds":folds,
            "total_targets":len(z),"supported_targets":int(z.supported.sum()),
            "matched_targets":int(z.matched.sum()),
            "all_targets":all_,"supported_targets_scores":supported,
            "matched_targets_scores":matched}

def analyze(archive):
    from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame
    with archive.open("rb") as fd:
        digest=hashlib.file_digest(fd,"sha256").hexdigest()
    if digest!=SOURCE_SHA:
        raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as fd:
        raw=pd.read_csv(fd,dtype=str,keep_default_na=False,usecols=COLS)
    old,_=prepare_frame(raw)
    if len(old)!=2092836 or old.horse.nunique()!=90962:
        raise ValueError("HOLD_SOURCE_PARITY")
    old["stratum"]=old.surface.astype(str)+":"+(old.distance//400).astype(int).astype(str)
    p,model_qa=baseline(raw,old)
    if len(p)!=57208 or p.horse.nunique()!=15129:
        raise ValueError("HOLD_CANDIDATE_PARITY")
    results={}
    for strict in (False,True):
        mode="horse_and_trainer_disjoint" if strict else "horse_disjoint"
        results[mode]={}
        for seed in SEEDS:
            panel,qa=paired_panel(p,seed,strict)
            results[mode][str(seed)]={"support":qa,"years":{
                str(year):evaluate(panel,year,seed) for year in (2020,2021)}}
    return {"status":"RETROSPECTIVE_PAIRED_CONTEXT_TIME_TRANSFER",
            "source_A_sha256":digest,"baseline":model_qa,
            "candidate_starts":len(p),"candidate_horses":int(p.horse.nunique()),
            "primary":"horse_disjoint/20261124/2021/all_targets/M0_minus_M1",
            "min_training_peers":MIN_PEERS,"shrink":SHRINK,
            "min_sires_for_interval":MIN_SIRES,"count_match_max_ratio":MAX_RATIO,
            "results":results,
            "limitations":["Previously inspected historical years, not prospective independent validation.",
                "Conditioned on paired surface observations, not forecasts of which horse changes surface.",
                "Relative rank residual difference, not absolute speed, reaction-norm heritability or causal competition.",
                "Within-fold identities disjoint; baseline histories/fits shared, and across-fold outcomes are dependent.",
                "Sire bootstrap is pointwise conditional sensitivity; race-day and deeper pedigree dependence remain.",
                "Other-sire control balances training peer counts only, not actual genomic unrelatedness.",
                "Unobserved rearing, exposure choice, age and environmental changes may confound transfer.",
                "No raw names, horse IDs, sire IDs or individual predictions exported."]}

def self_test():
    rows=[]
    for y,half in ((2019,0),(2021,1)):
        for s,delta in (("A",.3),("B",-.3)):
            for i in range(3):
                for c,ctx in enumerate(CONTEXTS):
                    rows.append(dict(horse=f"{y}-{s}-{i}",sire_id=s,trainer_id=f"t{half}",
                        year=y,half=half,stratum=ctx,residual=delta*(1 if c==0 else 0)))
    p=pd.DataFrame(rows)
    h=p.groupby(["horse","sire_id","year","half","stratum"]).residual.mean().unstack("stratum")
    q=(h[CONTEXTS[0]]-h[CONTEXTS[1]]).rename("difference").reset_index()
    train=q.loc[q.year.eq(2019)]; test=q.loc[q.year.eq(2021)]
    pr,qa=predict_fold(train,test,SEEDS[0])
    assert qa["training_matched_sire_pairs"]==1 and pr.supported.all() and pr.matched.all()
    assert np.allclose(pr.M1,-pr.P) and np.allclose(pr.M0,0.)
    mutated=test.copy(); mutated["difference"]+=9
    pd.testing.assert_frame_equal(pr,predict_fold(train,mutated,SEEDS[0])[0])
    absent=test.iloc[[0]].assign(sire_id="missing")
    x=predict_fold(train,absent,SEEDS[0])[0]
    assert not x.supported.iloc[0] and x.M0.iloc[0]==x.M1.iloc[0]
    try:
        predict_fold(train,test.assign(year=2019),SEEDS[0])
    except ValueError:
        pass
    else:
        raise AssertionError("time leak")
    try:
        predict_fold(train,test.assign(horse=train.horse.iloc[0]),SEEDS[0])
    except ValueError:
        pass
    else:
        raise AssertionError("horse leak")
    a,_=paired_panel(p,SEEDS[0])
    assert len(a)==12
    b,_=paired_panel(p.loc[~(p.horse.eq("2019-A-0")&p.stratum.eq(CONTEXTS[1]))],SEEDS[0])
    assert len(b)==11
    print("synthetic time/horse separation, paired surfaces, fallback, and placebo passed")

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
    z=analyze(a.archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(z,allow_nan=False))

if __name__=="__main__":
    main()
