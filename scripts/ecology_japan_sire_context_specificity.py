#!/usr/bin/env python3
"""Retrospective context-specific sire information: disjoint-half contrast.

Source A only. Horse, race-day and (strict sensitivity) trainer identities
are assigned globally to halves by fixed hashes. No current rank selects a
split or context. Only anonymous aggregates leave the runner.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

YEARS = (2019, 2020, 2021)
TRAIN_FIRST = 2016
CONTEXTS = ("turf:4", "dirt:4")  # JRA 1600-1999 m only for diagnostic.
SEEDS = (20261124, 20261125, 20261126)
MIN_PER_CELL = 3
MIN_SIRES = 30
BOOT_DRAWS = 999

def _hash_half(values, seed, namespace):
    """Stable across row ordering; distinct ID namespaces."""
    s = values.astype(str)
    u = pd.Index(s.unique())
    mapping = {v: hashlib.sha256(f"{seed}|{namespace}|{v}".encode()).digest()[0] & 1 for v in u}
    return s.map(mapping).to_numpy(np.int8)

def disjoint_panel(frame, seed, strict_trainer=False):
    cols = ["horse", "sire_id", "trainer_id", "day", "year", "stratum", "circuit", "residual"]
    if not set(cols).issubset(frame):
        raise ValueError("HOLD_PANEL_SCHEMA")
    p = frame.loc[frame.stratum.isin(CONTEXTS) & frame.circuit.eq("JRA"), cols].copy()
    for c in ("horse","sire_id","trainer_id","stratum"):
        p[c] = p[c].astype(str)
    if p.horse.eq("").any() or p.day.isna().any() or not np.isfinite(p.residual).all():
        raise ValueError("HOLD_PANEL_VALUE")
    p = p.loc[p.sire_id.ne("")].copy()
    if strict_trainer:
        p = p.loc[p.trainer_id.ne("")].copy()
    p["half"] = _hash_half(p.horse, seed, "horse")
    day = p.day.dt.normalize().dt.strftime("%Y-%m-%d")
    p = p.loc[p.half.to_numpy() == _hash_half(day, seed, "day")].copy()
    if strict_trainer:
        p = p.loc[p.half.to_numpy() == _hash_half(p.trainer_id, seed, "trainer")].copy()
    if p.empty:
        return p
    for field in ("horse", "day", *(("trainer_id",) if strict_trainer else ())):
        if p.groupby(field, observed=True).half.nunique().max() > 1:
            raise ValueError("HOLD_SPLIT_IDENTITY_OVERLAP")
    return p

def contrasts(p, min_cell=MIN_PER_CELL):
    """One vote per observed horse within each year/context; four cells needed.
    
    Center by each half's population context mean before taking the
    turf-minus-dirt contrast. Family common offsets cancel algebraically.
    """
    keys = ["year","half","stratum","sire_id","horse"]
    if p.empty:
        return pd.DataFrame(columns=["sire_id","year","delta_A","delta_B","product"]), {"supported_sire_years":0,"supported_sires":0}
    if p.groupby("horse", observed=True).sire_id.nunique().max()>1:
        raise ValueError("HOLD_PARENT_CONFLICT")
    h = p.groupby(keys, observed=True).residual.mean().rename("r").reset_index()
    h["r"] -= h.groupby(["year","half","stratum"], observed=True).r.transform("mean")
    cell = h.groupby(["sire_id","year","half","stratum"], observed=True).r.agg(["size","mean"])
    support = cell["size"].unstack(["half","stratum"])
    value = cell["mean"].unstack(["half","stratum"])
    wanted = pd.MultiIndex.from_product([[0,1],CONTEXTS],names=["half","stratum"])
    support = support.reindex(columns=wanted)
    value = value.reindex(columns=wanted)
    keep = support.ge(min_cell).all(axis=1)
    v = value.loc[keep]
    a = v[(0,CONTEXTS[0])] - v[(0,CONTEXTS[1])]
    b = v[(1,CONTEXTS[0])] - v[(1,CONTEXTS[1])]
    q = pd.DataFrame({"delta_A":a,"delta_B":b,"product":a*b}).reset_index()
    # Exact same-context-minus-cross-context algebra. Not causal variance.
    aa, ab = v[(0,CONTEXTS[0])], v[(0,CONTEXTS[1])]
    ba, bb = v[(1,CONTEXTS[0])], v[(1,CONTEXTS[1])]
    if not np.allclose(q["product"], aa*ba+ab*bb-aa*bb-ab*ba, atol=1e-12, rtol=0):
        raise ValueError("HOLD_CONTRAST_IDENTITY")
    return q, {"supported_sire_years":len(q), "supported_sires":int(q.sire_id.nunique()),
               "retained_starts":len(p),"retained_horses":int(p.horse.nunique()),
               "retained_days":int(p.day.nunique()),"retained_trainers":int(p.trainer_id.nunique()),
               "horse_context_year_cells":len(h),
               "possible_sire_years_before_four_cell_gate":len(support)}

def summary(q, seed, draws=BOOT_DRAWS, min_sires=MIN_SIRES):
    if q.empty:
        return {"status":"HOLD_NO_FOUR_CELL_SUPPORT","sires":0,"sire_years":0}
    by_sire = q.groupby("sire_id",observed=True)["product"].mean().to_numpy(float)
    n=len(by_sire)
    center=float(by_sire.mean())
    out={"status":"DESCRIPTIVE" if n>=min_sires else "HOLD_FEW_SIRES",
         "sires":n,"sire_years":len(q),"equal_sire_mean_split_product":center,
         "positive_sire_year_products":int(q["product"].gt(0).sum()),
         "negative_sire_year_products":int(q["product"].lt(0).sum())}
    if n>=min_sires:
        rng=np.random.default_rng(seed)
        rep=np.array([by_sire[rng.integers(n,size=n)].mean() for _ in range(draws)])
        out["whole_sire_bootstrap_pointwise_CI95"]=np.quantile(rep,[.025,.975]).tolist()
    return out

def baseline(raw, old):
    from ecology_japan_2022_independent_forward import _peer, fit_weighted_ridge, predict_weighted_ridge, RIDGE_ALPHA
    from ecology_japan_2022_strong_portable_baseline import old_metadata, STRONG_NO_KIN
    from ecology_japan_2022_24_family_feature_ablation import _strong_features
    meta=old_metadata(raw)
    features=tuple(STRONG_NO_KIN)+("trainer_context_history","trainer_context_log_support")
    xs, ys, ids, targets, output = [], [], [], [], []
    qa={}
    for year in range(TRAIN_FIRST, max(YEARS)+1):
        h=old.loc[old.year.lt(year)]
        t=old.loc[old.year.eq(year)&old.circuit.eq("JRA")].reset_index(drop=True)
        x=_strong_features(h,t,meta)[list(STRONG_NO_KIN)].copy()
        # Historical trainer peers in the same context, excluding focal horse.
        s,n=_peer(h,t,"trainer_id")
        x["trainer_context_history"]=s/(n+8)
        x["trainer_context_log_support"]=np.log1p(n)
        if year in YEARS:
            train=pd.concat(xs,ignore_index=True)
            model=fit_weighted_ridge(train,np.concatenate(ys),np.concatenate(ids),features,alpha=RIDGE_ALPHA)
            pred=predict_weighted_ridge(model,x)
            y=t.y.to_numpy(float)
            w=1/t.groupby("horse",observed=True).horse.transform("size").to_numpy(float)
            qa[str(year)]={"training_starts":len(train),"JRA_evaluation_starts":len(t),
                           "JRA_evaluation_horses":int(t.horse.nunique()),
                           "own_trainer_RMSE":float(np.sqrt(np.average((y-pred)**2,weights=w))),
                           "midrank_RMSE":float(np.sqrt(np.average((y-.5)**2,weights=w)))}
            sel=t.stratum.isin(CONTEXTS).to_numpy()
            f=t.loc[sel,["horse","sire_id","trainer_id","day","year","stratum","circuit"]].copy()
            f["residual"]=(y-pred)[sel]
            output.append(f)
            del train
        if year<max(YEARS):
            xs.append(x);ys.append(t.y.to_numpy(float));ids.append(t.horse.astype(str).to_numpy())
        print(json.dumps({"stage":"historical_feature_year","year":year,"JRA_rows":len(t)}),flush=True)
    return pd.concat(output,ignore_index=True),qa

def analyze(archive):
    from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame
    with archive.open("rb") as fd:
        digest=hashlib.file_digest(fd,"sha256").hexdigest()
    if digest!=SOURCE_SHA:
        raise ValueError("HOLD_SOURCE_A_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as fd:
        raw=pd.read_csv(fd,dtype=str,keep_default_na=False,usecols=COLS)
    old,qa=prepare_frame(raw)
    if len(old)!=2092836 or old.horse.nunique()!=90962:
        raise ValueError("HOLD_SOURCE_COHORT_PARITY")
    old["stratum"]=old.surface.astype(str)+":"+(old.distance//400).astype(int).astype(str)
    p, model_qa=baseline(raw,old)
    out={}
    for strict in (False,True):
        mode="horse_day_trainer_disjoint" if strict else "horse_day_disjoint"
        out[mode]={}
        for seed in SEEDS:
            split=disjoint_panel(p,seed,strict)
            q,support=contrasts(split)
            out[mode][str(seed)]={"support":support,"pooled":summary(q,seed),
                "by_year":{str(y):summary(q.loc[q.year.eq(y)],seed) for y in YEARS}}
    return {"status":"RETROSPECTIVE_CONTEXT_CONTRAST_NOT_GENETIC_CAUSAL_EFFECT",
            "source_A_sha256":digest,"original_source_starts":len(old),
            "original_source_horses":int(old.horse.nunique()),"baseline":model_qa,
            "diagnostic_candidate_starts":len(p),"diagnostic_candidate_horses":int(p.horse.nunique()),
            "contexts":list(CONTEXTS),"years":list(YEARS),"seeds":list(SEEDS),
            "min_distinct_horses_per_cell":MIN_PER_CELL,"primary":"horse_day_disjoint / seed 20261124 / pooled",
            "results":out,"limitations":[
                "All data are historical and already inspected for other analyses; not prospective replication.",
                "Contrast is excess cross-half agreement of sire x context residual means, not genetic variance or proof of measurement noise.",
                "Residuals are relative rank, not speed. Disjoint race days avoid direct same-race rank dependence across halves.",
                "Stable recorded parent IDs, nonrandom context exposure, selection and unmeasured rearing remain.",
                "Trainer-disjoint split tests exact recorded trainer labels, not independent farms or all shared environments.",
                "Shared fitted baseline and within-sire/calendar dependence remain; sire bootstrap is conditional pointwise sensitivity.",
                "Fixed seeds reuse data and are not independent replicates. No raw IDs, ranks or predictions exported."]}

def self_test():
    # Four cells for two families with exactly opposite context contrasts.
    rows=[]
    for sire,sign in [("S",1.),("T",-1.)]:
        for half in (0,1):
            for c,ctx in enumerate(CONTEXTS):
                for i in range(3):
                    rows.append(dict(year=2019,half=half,stratum=ctx,sire_id=sire,
                                     horse=f"{sire}{half}{c}{i}",residual=sign*(1 if c==0 else -1),
                                     day=pd.Timestamp(f"2019-01-0{half+1}"),trainer_id=f"trainer{half}"))
    p=pd.DataFrame(rows)
    q,qa=contrasts(p)
    assert qa["supported_sires"]==2
    assert np.allclose(q["product"],4.)
    # A shared family offset cancels, even with a large common effect.
    p["residual"] += np.where(p.sire_id.eq("S"),10.,-10.)
    assert np.allclose(contrasts(p)[0]["product"],4.)
    p["residual"]=np.where(p.sire_id.eq("S"),10.,-10.)
    assert np.allclose(contrasts(p)[0]["product"],0.)
    # Four-cell gate refuses missing cell.
    assert contrasts(p.loc[~(p.half.eq(1)&p.stratum.eq(CONTEXTS[1]))])[0].empty
    rng=np.random.default_rng(5)
    z=pd.DataFrame({"horse":[f"h{i%100}" for i in range(300)],
        "sire_id":"S","trainer_id":[f"t{i%23}" for i in range(300)],
        "day":pd.to_datetime("2019-01-01")+pd.to_timedelta(np.arange(300)%60,unit="D"),
        "year":2019,"stratum":np.where(np.arange(300)%2,CONTEXTS[0],CONTEXTS[1]),
        "circuit":"JRA","residual":rng.normal(size=300)})
    for strict in (False,True):
        a=disjoint_panel(z,SEEDS[0],strict)
        assert len(a)>0
        for field in ("horse","day",*(("trainer_id",) if strict else ())):
            assert a.groupby(field).half.nunique().max()==1
        assert set(a.index)==set(disjoint_panel(z.sample(frac=1,random_state=9),SEEDS[0],strict).index)
    print("synthetic split-disjointness / contrast / support tests passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test()
        return
    if not a.archive or not a.output:
        p.error("archive and output required")
    r=analyze(a.archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(r,allow_nan=False))
if __name__=="__main__":
    main()
