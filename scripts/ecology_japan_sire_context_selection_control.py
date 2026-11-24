#!/usr/bin/env python3
"""Follow-up to PR78: context sorting and count-matched sire correspondence.

Uses source A only, same fixed chronological baseline and disjoint splits.
No new data or untouched validation. Outputs anonymous aggregates only.
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
    YEARS, CONTEXTS, SEEDS, baseline, disjoint_panel, contrasts, summary,
)
MIN_PAIRED_HORSES = 3
CALIPER = np.log(2.)
MIN_MATCHED_PAIRS = 20
DRAWS = 999

def paired_horse_contrasts(p, min_cell=MIN_PAIRED_HORSES):
    """Require the same horse to contribute both contexts within year/half."""
    keys = ["sire_id","year","half","horse","stratum"]
    h = p.groupby(keys, observed=True).residual.mean().unstack("stratum")
    h = h.reindex(columns=list(CONTEXTS)).dropna()
    v = (h[CONTEXTS[0]]-h[CONTEXTS[1]]).rename("difference").reset_index()
    if v.empty:
        return pd.DataFrame(columns=["sire_id","year","delta_A","delta_B","product"]), {
            "paired_horse_year_cells":0,"paired_distinct_horses":0,"possible_sire_years":0,
            "supported_sire_years":0,"supported_sires":0}
    v["difference"] -= v.groupby(["year","half"],observed=True).difference.transform("mean")
    g=v.groupby(["sire_id","year","half"],observed=True).difference.agg(["mean","size"])
    s=g["size"].unstack("half").reindex(columns=[0,1])
    m=g["mean"].unstack("half").reindex(columns=[0,1])
    keep=s.ge(min_cell).all(axis=1)
    m=m.loc[keep]
    q=pd.DataFrame({"delta_A":m[0],"delta_B":m[1],"product":m[0]*m[1]}).reset_index()
    return q,{"paired_horse_year_cells":len(v),"paired_distinct_horses":int(v.horse.nunique()),
              "possible_sire_years":len(s),"supported_sire_years":len(q),"supported_sires":int(q.sire_id.nunique())}

def cell_counts(p):
    keys=["sire_id","year","half","stratum","horse"]
    h=p[keys].drop_duplicates()
    n=h.groupby(keys[:-1],observed=True).size().unstack(["half","stratum"])
    return n.reindex(columns=pd.MultiIndex.from_product([[0,1],CONTEXTS],names=["half","stratum"]))

def matched_correspondence(q, counts, seed, draws=DRAWS, min_pairs=MIN_MATCHED_PAIRS):
    """Deterministic disjoint sire pairs, same supported years, each of 4
    horse counts within factor two. Match on support, not residual contrasts.
    Swapping B profiles within pairs is an observational placebo, not a
    randomization experiment. Sires may be genetically related.
    """
    if q.empty:
        return {"status":"HOLD_EMPTY_SIRE_YEAR_PANEL","matched_pairs":0}
    q=q.set_index(["sire_id","year"]).sort_index()
    n=counts.reindex(q.index)
    if n.isna().any().any() or (n<3).any().any():
        raise ValueError("HOLD_MATCH_SUPPORT")
    groups={}
    profiles={}
    for sire,r in q.groupby(level=0,sort=True):
        years=tuple(int(y) for y in r.index.get_level_values(1))
        k=n.loc[sire].loc[list(years)].to_numpy(float).ravel()
        profiles[sire]=(years,np.log(k))
        groups.setdefault(years,[]).append(sire)
    pairs=[]
    for years,ids in sorted(groups.items()):
        candidates=[]
        for i,s in enumerate(ids):
            for t in ids[i+1:]:
                gap=np.abs(profiles[s][1]-profiles[t][1])
                if gap.max()<=CALIPER+1e-12:
                    # Ties only are broken by stable hash, not by outcomes.
                    tie=hashlib.sha256(f"{seed}|{s}|{t}".encode()).hexdigest()
                    candidates.append((float(gap@ gap),tie,s,t,float(gap.max())))
        used=set()
        for _,_,s,t,gap in sorted(candidates):
            if s not in used and t not in used:
                used.update((s,t))
                pairs.append((s,t,gap))
    if not pairs:
        return {"status":"HOLD_NO_MATCHES","eligible_sires":len(profiles),"matched_pairs":0}
    true,placebo,gaps=[],[],[]
    for s,t,gap in pairs:
        a=q.loc[s];b=q.loc[t]
        if not a.index.equals(b.index):
            raise ValueError("HOLD_YEAR_PATTERN_MISMATCH")
        A,B=a.delta_A.to_numpy(),a.delta_B.to_numpy()
        C,D=b.delta_A.to_numpy(),b.delta_B.to_numpy()
        true.append(float(np.mean((A*B+C*D)/2)))
        placebo.append(float(np.mean((A*D+C*B)/2)))
        if not np.isclose(true[-1]-placebo[-1],np.mean((A-C)*(B-D)/2),atol=1e-12,rtol=0):
            raise ValueError("HOLD_PLACEBO_IDENTITY")
        gaps.append(gap)
    d=np.asarray(true)-np.asarray(placebo)
    out={"status":"DESCRIPTIVE" if len(d)>=min_pairs else "HOLD_FEW_MATCHED_PAIRS",
         "eligible_sires":len(profiles),"matched_pairs":len(d),"matched_sires":2*len(d),
         "matched_fraction":2*len(d)/len(profiles),
         "same_sire_product":float(np.mean(true)),
         "swapped_other_sire_product":float(np.mean(placebo)),
         "same_minus_swapped":float(d.mean()),
         "max_matched_cell_count_ratio":float(np.exp(max(gaps)))}
    if len(d)>=min_pairs:
        rng=np.random.default_rng(seed)
        reps=np.array([d[rng.integers(len(d),size=len(d))].mean() for _ in range(draws)])
        out["matched_pair_bootstrap_pointwise_CI95"]=np.quantile(reps,[.025,.975]).tolist()
    return out

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
        raise ValueError("HOLD_PR78_CANDIDATE_PARITY")
    out={}
    for strict in (False,True):
        mode="horse_day_trainer_disjoint" if strict else "horse_day_disjoint"
        out[mode]={}
        for seed in SEEDS:
            split=disjoint_panel(p,seed,strict)
            q,qa=contrasts(split)
            orig=summary(q,seed)
            if not strict and seed==SEEDS[0]:
                if orig["sires"]!=83 or orig["sire_years"]!=174 or abs(orig["equal_sire_mean_split_product"]-.006530724376455479)>1e-10:
                    raise ValueError("HOLD_PR78_PRIMARY_PARITY")
            pair,pqa=paired_horse_contrasts(split)
            out[mode][str(seed)]={"original":orig,"original_support":qa,
                "within_horse":summary(pair,seed),"within_horse_support":pqa,
                "within_horse_by_year":{str(y):summary(pair.loc[pair.year.eq(y)],seed) for y in YEARS},
                "matched_other_sire_control":matched_correspondence(q,cell_counts(split),seed)}
    return {"status":"RETROSPECTIVE_SELECTION_AND_CORRESPONDENCE_DIAGNOSTICS",
            "source_A_sha256":digest,"baseline":model_qa,"candidate_starts":len(p),
            "candidate_horses":int(p.horse.nunique()),"results":out,
            "primary_split":"horse_day_disjoint/20261124",
            "minimum_paired_horses_each_half":MIN_PAIRED_HORSES,
            "maximum_cell_count_ratio":2.0,"minimum_matched_sire_pairs":MIN_MATCHED_PAIRS,
            "limitations":["Same inspected historical source, not independent replication.",
                "Within-horse surface contrast selects animals with both surfaces; changes over time and race composition remain.",
                "Count-matched swapped sires are a negative control for correspondence, not genomic nonkin or randomized treatment.",
                "Sire and pair bootstrap are conditional pointwise sensitivity; common fitted baseline and environmental dependence remain.",
                "Matching only on support years and cell counts does not balance rearing, age, trainer composition or exposure selection.",
                "No absolute speed, causal competition, heritability or individual records exported."]}

def self_test():
    rows=[]
    for s,sign in (("S",1.),("T",-1.)):
        for half in (0,1):
            for i in range(3):
                for c,ctx in enumerate(CONTEXTS):
                    rows.append(dict(sire_id=s,year=2019,half=half,horse=f"{s}{half}{i}",
                         stratum=ctx,residual=sign*(1 if c==0 else -1)))
    p=pd.DataFrame(rows)
    q,qa=paired_horse_contrasts(p)
    assert qa["supported_sires"]==2 and np.allclose(q["product"],4.)
    pp=p.copy()
    pp["residual"]+=np.where(pp.sire_id.eq("S"),20.,-20.)
    assert np.allclose(paired_horse_contrasts(pp)[0]["product"],4.)
    assert paired_horse_contrasts(p.loc[~(p.half.eq(1)&p.stratum.eq(CONTEXTS[0]))])[0].empty
    m=matched_correspondence(q,cell_counts(p),SEEDS[0],min_pairs=1)
    assert m["matched_pairs"]==1 and np.isclose(m["same_minus_swapped"],8.)
    assert matched_correspondence(q,cell_counts(p),SEEDS[0],min_pairs=2)["status"]=="HOLD_FEW_MATCHED_PAIRS"
    bad=cell_counts(p).copy()
    bad.loc[("T",2019),:]=10
    assert matched_correspondence(q,bad,SEEDS[0],min_pairs=1)["status"]=="HOLD_NO_MATCHES"
    print("synthetic paired-horse / matched correspondence tests passed")

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
