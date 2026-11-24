#!/usr/bin/env python3
"""Same-sire vs no-direct-shared-parent donors under matched management metadata.

Retrospective first eligible annual surface, same source and strong baseline
as PR82. Equal donor count and exact observed trainer/year/age-bin/sex-bin
within each target. No causal genetic interpretation; anonymous output only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame
from ecology_japan_sire_context_specificity import SEEDS,_hash_half
from ecology_japan_sire_first_context_assignment import (
    annual_rows,build_baseline,family_features,evaluate,TRAIN_FIRST,ALPHA,
)
from ecology_japan_2022_independent_forward import fit_weighted_ridge,predict_weighted_ridge

HISTORY_FIRST=2018
TEST_YEARS=(2020,2021)
SHRINK=8.
MAX_PAIRS=8
MIN_SIRES=30
MIN_HORSES=100
DRAWS=999

def attach_dam(old,p):
    a=old[["horse","sire_id","dam_id"]].astype(str).drop_duplicates()
    if a.horse.duplicated().any():
        raise ValueError("HOLD_PARENT_CONFLICT")
    a=a.set_index("horse")
    t=p.copy()
    if not t.horse.isin(a.index).all() or not np.array_equal(
        t.horse.map(a.sire_id).to_numpy(),t.sire_id.to_numpy()):
        raise ValueError("HOLD_PARENT_JOIN")
    t["dam_id"]=t.horse.map(a.dam_id)
    return t

def baseline_panel(p,base,seed):
    """Held-year opposite-half no-family model, including donor residuals."""
    p=p.copy()
    p["half"]=_hash_half(p.horse,seed,"horse")
    parts=[]
    for year in range(HISTORY_FIRST,2022):
        for half in (0,1):
            train=p.loc[p.year.lt(year)&p.half.ne(half)]
            t=p.loc[p.year.eq(year)&p.half.eq(half)].copy()
            if train.empty or t.empty or set(train.horse)&set(t.horse):
                raise ValueError("HOLD_BASELINE_SPLIT")
            model=fit_weighted_ridge(train,train["first"],train.horse,base,alpha=ALPHA)
            t["B"]=predict_weighted_ridge(model,t)
            t["residual"]=t["first"]-t.B
            parts.append(t[["horse","sire_id","dam_id","trainer_id","year","day","half",
                            "age_raw","sex_raw","first","B","residual",
                            "no_eligible_before_year","cold_at_entry_raw"]])
    q=pd.concat(parts,ignore_index=True)
    if q.duplicated(["horse","year"]).any():
        raise ValueError("HOLD_DUPLICATE_PANEL")
    # Coarse exact match classes fixed prior to results. Unknown metadata
    # never forms a matching class.
    q["age_bin"]=q.age_raw.where(q.age_raw.isin([2,3,4]),5)
    q.loc[~q.age_raw.between(2,20),"age_bin"]=0
    q["sex_bin"]=q.sex_raw.where(q.sex_raw.isin([1,2,3]),0)
    return q

def _rank(seed,year,half,target,kind,horse):
    return hashlib.sha256(f"{seed}|{year}|{half}|{target}|{kind}|{horse}".encode()).digest()

def valid_match_rows(p):
    return p.loc[p.sire_id.ne("")&p.dam_id.ne("")&p.trainer_id.ne("")&
                 p.age_bin.gt(0)&p.sex_bin.gt(0)]

def select_pairs(h,t,seed,year,half):
    """Same observed entry trainer, age/sex category and donor calendar year.

    Restrict both sides to known direct parents; same-sire donors must have
    different recorded dams. Control shares neither direct recorded parent.
    One latest eligible year per donor horse, no reuse within focal target.
    Selection uses only IDs and exact metadata, never outcome or residual.
    """
    if h.empty:
        return []
    if h.horse.duplicated().any() or t.horse in set(h.horse):
        raise ValueError("HOLD_DONOR_IDENTITY")
    if not t.sire_id or not t.dam_id or not t.trainer_id or t.age_bin<=0 or t.sex_bin<=0:
        return []
    if not h.year.lt(year).all() or not h.half.ne(half).all():
        raise ValueError("HOLD_DONOR_TIME_OR_HALF")
    x=h.loc[h.trainer_id.eq(t.trainer_id)&h.age_bin.eq(t.age_bin)&h.sex_bin.eq(t.sex_bin)]
    pairs=[]
    for donor_year,g in x.groupby("year",observed=True,sort=True):
        kin=g.loc[g.sire_id.eq(t.sire_id)&g.dam_id.ne(t.dam_id)]
        non=g.loc[g.sire_id.ne(t.sire_id)&g.dam_id.ne(t.dam_id)]
        k=sorted(kin.itertuples(index=False),key=lambda r:_rank(seed,year,half,t.horse,"kin",r.horse))
        n=sorted(non.itertuples(index=False),key=lambda r:_rank(seed,year,half,t.horse,"non",r.horse))
        pairs.extend(zip(k,n))
    # A cap avoids one target's large family dominating; ordering is blind
    # to observed surface and baseline residual.
    pairs=sorted(pairs,key=lambda pair:_rank(seed,year,half,t.horse,"pair",pair[0].horse))[:MAX_PAIRS]
    seen=set()
    for a,b in pairs:
        if (a.horse in seen or b.horse in seen or a.horse==b.horse or
            a.sire_id!=t.sire_id or a.dam_id==t.dam_id or
            b.sire_id==t.sire_id or b.dam_id==t.dam_id or
            a.year!=b.year or a.trainer_id!=b.trainer_id or
            a.age_bin!=b.age_bin or a.sex_bin!=b.sex_bin):
            raise ValueError("HOLD_MATCH_INVARIANT")
        seen.update([a.horse,b.horse])
    return pairs

def predict(p,year,seed):
    out=[]
    for half in (0,1):
        # Latest *eligible* record per donor, before filtering unknown labels,
        # so a missing latest record is not silently replaced with older data.
        h=p.loc[p.year.lt(year)&p.half.ne(half)].sort_values(["year","day","horse"]).drop_duplicates("horse",keep="last")
        t=p.loc[p.year.eq(year)&p.half.eq(half)].copy()
        if h.empty or t.empty or set(h.horse)&set(t.horse):
            raise ValueError("HOLD_SPLIT")
        # Global baseline correction estimated from all prior opposite-half
        # residuals before any matching. B0 and both corrections use it.
        mu=float(h.residual.mean())
        h=valid_match_rows(h)
        # Preindex exact trainer/age/sex keys to avoid repeated full scans.
        pools={k:v for k,v in h.groupby(["trainer_id","age_bin","sex_bin"],observed=True,sort=False)}
        empty=h.iloc[:0]
        n=[];ks=[];ps=[]
        for r in t.itertuples(index=False):
            pool=pools.get((r.trainer_id,r.age_bin,r.sex_bin),empty)
            pairs=select_pairs(pool,r,seed,year,half)
            k=len(pairs)
            n.append(k)
            ks.append(sum(a.residual-mu for a,b in pairs)/(k+SHRINK))
            ps.append(sum(b.residual-mu for a,b in pairs)/(k+SHRINK))
        t["matched_n"]=n
        t["M0"]=np.clip(t.B+mu,0,1)
        t["K"]=np.clip(t.B+mu+np.asarray(ks),0,1)
        t["P"]=np.clip(t.B+mu+np.asarray(ps),0,1)
        out.append(t)
    z=pd.concat(out,ignore_index=True)
    if z.horse.duplicated().any() or len(z)!=int(p.year.eq(year).sum()):
        raise ValueError("HOLD_TARGET_DENOMINATOR")
    if not np.allclose(z.loc[z.matched_n.eq(0),"K"],z.loc[z.matched_n.eq(0),"M0"]) or not np.allclose(z.loc[z.matched_n.eq(0),"P"],z.loc[z.matched_n.eq(0),"M0"]):
        raise ValueError("HOLD_FALLBACK")
    return z

def cluster(t,d,column,seed):
    key=t[column].astype(str).where(t[column].ne(""),"missing:"+t.horse)
    x=pd.DataFrame({"g":key.to_numpy(),"d":d}).groupby("g").d.agg(["sum","size"]).to_numpy(float)
    n=len(x)
    if n<MIN_SIRES or len(t)<MIN_HORSES:
        return {"groups":n,"status":"HOLD_LOW_SUPPORT"}
    rng=np.random.default_rng(seed)
    rep=x[rng.integers(n,size=(DRAWS,n))].sum(axis=1)
    return {"groups":n,"CI95_pointwise":np.quantile(rep[:,0]/rep[:,1],[.025,.975]).tolist()}

def score(t,seed):
    if t.empty:
        return {"horses":0,"status":"HOLD_EMPTY"}
    y=t["first"].to_numpy(float)
    loss={k:(y-t[k].to_numpy(float))**2 for k in ("B","M0","K","P")}
    out={"horses":len(t),"sires":int(t.sire_id.nunique()),
         "known_trainers":int(t.loc[t.trainer_id.ne(""),"trainer_id"].nunique()),
         "matched_horses":int(t.matched_n.gt(0).sum()),
         "mean_matched_pairs":float(t.matched_n.mean()),
         "RMSE":{k:float(np.sqrt(v.mean())) for k,v in loss.items()},
         "contrasts":{}}
    for a,b in (("M0","K"),("M0","P"),("P","K")):
        d=loss[a]-loss[b]
        out["contrasts"][a+"_minus_"+b]={"MSE_gain":float(d.mean()),
            "sire":cluster(t,d,"sire_id",seed),"trainer":cluster(t,d,"trainer_id",seed)}
    return out

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
    p,base=build_baseline(old,a,raw)
    n=p.loc[p.year.isin((2019,2020,2021))].groupby("year").size().to_dict()
    if n!={2019:7265,2020:7381,2021:7276}:
        raise ValueError("HOLD_PR82_DENOMINATOR")
    q,k=family_features(a,p,SEEDS[0],"first")
    parity=evaluate(q,base,k,"first",2021,SEEDS[0])["all"]
    if abs(parity["C_minus_F"]["MSE_gain"]-.013750704256089798)>1e-10:
        raise ValueError("HOLD_PR82_SCORE_PARITY")
    p=attach_dam(old,p)
    results={}
    for seed in SEEDS:
        b=baseline_panel(p,base,seed)
        results[str(seed)]={}
        for year in TEST_YEARS:
            t=predict(b,year,seed)
            if year==2021 and seed==SEEDS[0] and abs(np.sqrt(np.mean(t.residual**2))-.4043074139709618)>1e-10:
                raise ValueError("HOLD_PR82_B_PARITY")
            masks={"all":np.ones(len(t),bool),"matched":t.matched_n.gt(0),
                   "matched_min3":t.matched_n.ge(3),
                   "matched_no_eligible_prior":t.matched_n.gt(0)&t.no_eligible_before_year,
                   "matched_raw_first":t.matched_n.gt(0)&t.cold_at_entry_raw}
            results[str(seed)][str(year)]={"groups":{k:score(t.loc[v],seed) for k,v in masks.items()},
                "eligible_target_metadata":len(valid_match_rows(t)),
                "pair_count_distribution":{str(int(k)):int(v) for k,v in t.matched_n.value_counts().sort_index().items()}}
    return {"status":"RETROSPECTIVE_MANAGEMENT_MATCHED_DONOR_CONTROL",
            "source_A_sha256":SOURCE_SHA,"primary":"20261124/2021/matched/P_minus_K",
            "PR82_primary_parity":parity["C_minus_F"]["MSE_gain"],
            "max_pairs":MAX_PAIRS,"shrink":SHRINK,"results":results,
            "limitations":["Same inspected archive, not independent prospective confirmation.",
             "Same recorded trainer is not identical rearing environment; age bins, sex, calendar year do not balance all covariates.",
             "No shared direct recorded parents is not genomic unrelatedness. Same-sire donors exclude same dam.",
             "Matching conditions on observed entry metadata, not predecision publication; no causal estimate of allocation or genetic effect.",
             "Primary matched subset may have limited and selected support. All targets include zero-signal fallback; no relaxation after outcome inspection.",
             "Earlier donor residuals use their own chronological opposite-half B fits; shared historical fits/dependence remain.",
             "Separate whole-sire and trainer bootstrap pointwise sensitivities; not joint or simultaneous intervals.",
             "No individual rows, identifiers, wagering or fitness outcomes exported."]}

def self_test():
    from types import SimpleNamespace
    t=SimpleNamespace(horse="f",sire_id="S",dam_id="D",trainer_id="T",age_bin=3,sex_bin=1)
    rows=[
      ("a","S","E","T",3,1,2019,.2),("b","Q","F","T",3,1,2019,-.2),
      ("c","Q","D","T",3,1,2019,9.),("d","S","D","T",3,1,2019,9.),
      ("e","Q","G","T",3,1,2018,9.),("g","S","G","U",3,1,2019,9.),
      ("h","Q","G","T",4,1,2019,9.),("i","Q","G","T",3,2,2019,9.)]
    h=pd.DataFrame(rows,columns=["horse","sire_id","dam_id","trainer_id","age_bin","sex_bin","year","residual"])
    h["half"]=1
    a=select_pairs(h,t,SEEDS[0],2021,0)
    assert [(k.horse,n.horse) for k,n in a]==[("a","b")]
    b=h.sample(frac=1,random_state=3).copy();b["residual"]=-b.residual
    assert [(k.horse,n.horse) for k,n in select_pairs(b,t,SEEDS[0],2021,0)]==[("a","b")]
    assert not select_pairs(h.loc[h.horse.ne("b")],t,SEEDS[0],2021,0)
    try:
        select_pairs(h.assign(year=2021),t,SEEDS[0],2021,0)
    except ValueError:
        pass
    else:
        raise AssertionError("future donor accepted")
    print("synthetic management exact match, direct-parent exclusion, chronology and blind ranking passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not a.archive or not a.output:
        p.error("archive and output required")
    r=analyze(a.archive)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    compact={s:{y:{"groups":{k:v for k,v in q["groups"].items() if k in ("all","matched","matched_raw_first")},
                 "eligible_target_metadata":q["eligible_target_metadata"],
                 "pair_count_distribution":q["pair_count_distribution"]} for y,q in v.items()} for s,v in r["results"].items()}
    print(json.dumps({"status":r["status"],"primary":r["primary"],
        "PR82_primary_parity":r["PR82_primary_parity"],"results":compact},allow_nan=False))

if __name__=="__main__":
    main()
