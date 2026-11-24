#!/usr/bin/env python3
"""Separate cohort composition and dated information refresh in occupancy transfer.

Retrospective source A/B, strict anchored continuing-horse cohort. B histories
are updated only from completed earlier calendar years. No wagering/outcome
model, no causal genetic inference, no individual records exported.
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
from ecology_japan_sire_context_specificity import CONTEXTS, SEEDS, _hash_half
from ecology_japan_sire_context_exposure_transfer import historical_panel, OWN_SHRINK
from ecology_japan_context_occupancy_independent import audit_circuits, target_occupancy, source_a_baseline
from ecology_japan_sire_context_time_transfer import predict_fold

YEARS=(2022,2023,2024)
MODELS=("B00","B10","M00","M10","M01","M11")
DRAWS=999
MIN_SIRES=30
MIN_HORSES=100

def weighted_own_prior(n,p,g):
    return (n*p+OWN_SHRINK*g)/(n+OWN_SHRINK)

def update_own(old,t,seed):
    """Update only eligible own counts using completed B years, not current year.

    The A half-specific horse-equal population prior is fixed. B target
    inclusion is strict classified races; B missing observations are not
    evidence of no actual starts.
    """
    a=old.loc[old.circuit.eq("JRA")&old.stratum.isin(CONTEXTS)&old.sire_id.astype(str).ne(""),
              ["horse","surface"]].copy()
    a["horse"]=a.horse.astype(str)
    a["half"]=_hash_half(a.horse,seed,"horse")
    a["turf"]=a.surface.eq("turf").astype(float)
    h=a.groupby(["horse","half"],observed=True).turf.agg(["sum","size","mean"]).reset_index()
    g=h.groupby("half",observed=True)["mean"].mean()
    h=h.set_index("horse")
    q=t.copy()
    if q.duplicated(["horse","year"]).any() or not q.year.isin(YEARS).all():
        raise ValueError("HOLD_TARGET_KEYS")
    if (q.starts<=0).any() or not q.occupancy.between(0,1).all():
        raise ValueError("HOLD_TARGET_VALUES")
    q["base_refreshed"]=0.
    q["refreshed_own_n"]=0
    for yr in YEARS:
        ix=q.year.eq(yr)
        x=q.loc[ix]
        # All B records entering this sum have earlier years.
        earlier=q.loc[q.year.lt(yr),["horse","starts","occupancy"]].copy()
        earlier["turf_starts"]=earlier.starts*earlier.occupancy
        agg=earlier.groupby("horse",observed=True).agg(n=("starts","sum"),s=("turf_starts","sum"))
        old_n=x.horse.map(h["size"]).fillna(0).to_numpy(float)
        old_s=x.horse.map(h["sum"]).fillna(0).to_numpy(float)
        n=old_n+x.horse.map(agg.n).fillna(0).to_numpy(float)
        s=old_s+x.horse.map(agg.s).fillna(0).to_numpy(float)
        prior=x.half.map(g).to_numpy(float)
        if not np.isfinite(prior).all() or (s< -1e-9).any() or (s>n+1e-9).any():
            raise ValueError("HOLD_PRIOR")
        q.loc[ix,"base_refreshed"]=(s+OWN_SHRINK*prior)/(n+OWN_SHRINK)
        q.loc[ix,"refreshed_own_n"]=n.astype(int)
        if yr==2022 and not np.allclose(q.loc[ix,"base_refreshed"],x.base_own,atol=1e-12,rtol=0):
            raise ValueError("HOLD_FIRST_YEAR_PARITY")
    return q

def donor_panel(a,b,yr,refreshed):
    cols=["horse","sire_id","year","half"]
    d=a[cols].copy()
    d["difference"]=a.occupancy-a.base_own
    if refreshed:
        q=b.loc[b.year.lt(yr)]
        e=q[cols].copy()
        # Past B labels are residualized against their own as-of-year baseline,
        # never against the final target-year baseline.
        e["difference"]=q.occupancy-q.base_refreshed
        d=pd.concat([d,e],ignore_index=True)
    if d.empty or not d.year.lt(yr).all() or d.duplicated(["horse","year"]).any():
        raise ValueError("HOLD_DONOR_TIME_KEYS")
    return d

def predictions(a,b,yr,seed):
    """2x2 crossed updates with corresponding no-family controls.

    B00/B10: stale/refreshed own prior + original A global residual.
    M00/M10: add original A same-sire correction.
    M01/M11: replace A donor profile by A+earlier B profile, including
    global residual recalibration. Compare B11 (updated own + refreshed
    global residual) separately to isolate refreshed sire increment.
    """
    target=b.loc[b.year.eq(yr)].copy()
    out=[]
    for half in (0,1):
        t=target.loc[target.half.eq(half)].copy()
        if t.empty:
            continue
        profiles=[]
        for fresh in (False,True):
            d=donor_panel(a,b,yr,fresh)
            h=d.loc[d.half.ne(half)]
            p,_=predict_fold(h,t[["horse","sire_id","year","half"]],seed)
            p=p.set_index("horse").reindex(t.horse)
            if p[["M0","M1","n"]].isna().any().any():
                raise ValueError("HOLD_PREDICTION_JOIN")
            profiles.append(p)
        stale,fresh=profiles
        x=t.base_own.to_numpy(float);y=t.base_refreshed.to_numpy(float)
        m0=stale.M0.to_numpy(float);m1=stale.M1.to_numpy(float)
        f0=fresh.M0.to_numpy(float);f1=fresh.M1.to_numpy(float)
        t["B00"]=x+m0;t["B10"]=y+m0
        t["B01"]=x+f0;t["B11"]=y+f0
        t["M00"]=x+m1;t["M10"]=y+m1
        t["M01"]=x+f1;t["M11"]=y+f1
        t["stale_support"]=stale.n.to_numpy(int)
        t["fresh_support"]=fresh.n.to_numpy(int)
        out.append(t)
    z=pd.concat(out,ignore_index=True)
    if len(z)!=len(target) or z.horse.duplicated().any():
        raise ValueError("HOLD_TARGET_DENOMINATOR")
    if not np.isfinite(z[["B00","B10","B01","B11","M00","M10","M01","M11"]]).all().all():
        raise ValueError("HOLD_NONFINITE")
    if yr==2022:
        for c in ("B10","B01","B11"):
            if not np.allclose(z[c],z.B00,atol=1e-12,rtol=0):
                raise ValueError("HOLD_2022_BASELINE_IDENTITY")
        for c in ("M10","M01","M11"):
            if not np.allclose(z[c],z.M00,atol=1e-12,rtol=0):
                raise ValueError("HOLD_2022_MODEL_IDENTITY")
    return z

def loss_table(t):
    y=t.occupancy.to_numpy(float)
    cols=("B00","B10","B01","B11","M00","M10","M01","M11")
    return {c:(y-t[c].to_numpy(float))**2 for c in cols}

def ci(t,d,seed):
    g=pd.DataFrame({"sire":t.sire_id.to_numpy(),"d":d}).groupby("sire",observed=True).d.agg(["sum","size"])
    r={"MSE_gain":float(np.mean(d)),"sires":len(g)}
    if len(t)<MIN_HORSES or len(g)<MIN_SIRES:
        r["status"]="HOLD_LOW_SUPPORT"
    else:
        a=g.to_numpy(float);rng=np.random.default_rng(seed)
        rep=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
        r["CI95_pointwise"]=np.quantile(rep[:,0]/rep[:,1],[.025,.975]).tolist()
    return r

def score(t,seed):
    if t.empty:
        return {"horses":0,"status":"HOLD_EMPTY"}
    l=loss_table(t)
    r={"horses":len(t),"sires":int(t.sire_id.nunique()),
       "mean_old_own_count":float(t.own_prior_count.mean()),
       "mean_refreshed_own_count":float(t.refreshed_own_n.mean()),
       "RMSE":{k:float(np.sqrt(v.mean())) for k,v in l.items()},
       "contrasts":{}}
    for a,b in (("B00","M00"),("B10","M10"),("B01","M01"),("B11","M11"),
                ("M00","M10"),("M00","M01"),("M10","M11"),("M01","M11"),
                ("M00","M11"),("B00","B10"),("B10","B11")):
        r["contrasts"][a+"_minus_"+b]=ci(t,l[a]-l[b],seed)
    # Exact Shapley allocation across the two update routes: arithmetic,
    # not a causal decomposition.
    d0=l["M00"]-l["M11"]
    own=((l["M00"]-l["M10"])+(l["M01"]-l["M11"]))/2
    family=((l["M00"]-l["M01"])+(l["M10"]-l["M11"]))/2
    if not np.allclose(own+family,d0,atol=1e-12,rtol=0):
        raise ValueError("HOLD_FACTORIAL_IDENTITY")
    r["update_decomposition"]={"own":float(own.mean()),"profile_including_global":float(family.mean()),
                              "total":float(d0.mean())}
    return r

def source_a_reference(old,seed):
    a=historical_panel(old,seed,False)
    # Historical panel own residuals and exact original PR81 prior cutoff.
    z=[]
    for half in (0,1):
        t=a.loc[a.year.eq(2021)&a.half.eq(half)].copy()
        h=a.loc[a.year.lt(2021)&a.half.ne(half),["horse","sire_id","year","half","occupancy","base_own"]].copy()
        h["difference"]=h.occupancy-h.base_own
        p,_=predict_fold(h,t[["horse","sire_id","year","half"]],seed)
        p=p.set_index("horse").reindex(t.horse)
        t["gain"]=(t.occupancy.to_numpy()-t.base_own.to_numpy()-p.M0.to_numpy())**2-(t.occupancy.to_numpy()-t.base_own.to_numpy()-p.M1.to_numpy())**2
        z.append(t)
    q=pd.concat(z,ignore_index=True)
    if len(q)!=7276:
        raise ValueError("HOLD_A_REFERENCE")
    if seed==SEEDS[0] and abs(q.gain.mean()-.01471092236633107)>1e-10:
        raise ValueError("HOLD_PR81_PARITY")
    return a,q

def composition(a,b):
    """Compare source A 2021 vs B 2022; symmetric two-stratum decomposition."""
    def cells(t,prior):
        x=t[prior].eq(0)
        return [{"horses":int(m.sum()),"weight":float(m.mean()),"gain":float(t.loc[m,"gain"].mean())}
                for m in (x,~x)]
    aa=cells(a,"prior_count");bb=cells(b,"own_prior_count")
    if any(x["horses"]==0 for x in aa+bb):
        return {"status":"HOLD_EMPTY_STRATUM","A":aa,"B":bb}
    comp=sum((x["weight"]-y["weight"])*(x["gain"]+y["gain"])/2 for x,y in zip(aa,bb))
    within=sum((x["gain"]-y["gain"])*(x["weight"]+y["weight"])/2 for x,y in zip(aa,bb))
    change=float(a.gain.mean()-b.gain.mean())
    if abs(comp+within-change)>1e-10:
        raise ValueError("HOLD_COMPOSITION_IDENTITY")
    return {"status":"DESCRIPTIVE","strata":["no_prior_eligible","prior_eligible"],
            "A_2021":aa,"B_2022":bb,"A_minus_B_gain":change,
            "composition_term":float(comp),"within_stratum_term":float(within)}

def analyze(archive,db):
    raw,old,future,_,gate,_=load_sources(archive,db)
    if len(old)!=2092836 or old.horse.nunique()!=90962 or len(future)!=255484 or future.horse.nunique()!=12919:
        raise ValueError("HOLD_SOURCE_PARITY")
    circuit,cqa=audit_circuits(raw,old,db,gate["two_event_anchor_horses"])
    if cqa.get("verified_JRA_codes")!=10 or cqa.get("verified_NAR_codes")!=14 or cqa["matched_distinct_pre2022_source_B_races"]!=85856:
        raise ValueError("HOLD_CIRCUIT_PARITY")
    mask,sqa=strict_mask_exact_horse_race(raw,future,db,gate["two_event_anchor_horses"])
    strict=future.loc[mask].copy()
    if len(strict)!=244147 or strict.horse.nunique()!=12887:
        raise ValueError("HOLD_STRICT_PARITY")
    t,qa=target_occupancy(strict,circuit)
    n=t.groupby("year",observed=True).size().to_dict()
    if n!={2022:3011,2023:1588,2024:743}:
        raise ValueError("HOLD_PR85_DENOMINATOR")
    result={}
    for seed in SEEDS:
        a,ref=source_a_reference(old,seed)
        b=source_a_baseline(old,t,seed)
        b=update_own(old,b,seed)
        result[str(seed)]={"years":{}}
        for yr in YEARS:
            p=predictions(a,b,yr,seed)
            l=loss_table(p)
            p["gain"]=l["B00"]-l["M00"]
            if yr==2022:
                if seed==SEEDS[0] and abs(p.gain.mean()-.001961299416552986)>1e-10:
                    raise ValueError("HOLD_PR85_PARITY")
                result[str(seed)]["composition_A2021_B2022"]=composition(ref,p)
            groups={"all":p,"no_prior_A_eligible":p.loc[p.own_prior_count.eq(0)],
                    "prior_A_eligible":p.loc[p.own_prior_count.gt(0)],
                    "has_earlier_B_eligible":p.loc[p.refreshed_own_n.gt(p.own_prior_count)],
                    "no_earlier_B_eligible":p.loc[p.refreshed_own_n.eq(p.own_prior_count)]}
            result[str(seed)]["years"][str(yr)]={k:score(v,seed) for k,v in groups.items()}
    return {"status":"RETROSPECTIVE_CONTEXT_COMPOSITION_AND_REFRESH",
            "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
            "circuit_gate":cqa,"strict_gate":sqa,"target_scope":qa,
            "primary":"20261124/2024/all/B11_minus_M11",
            "secondary":"20261124/2024/all/M10_minus_M11",
            "results":result,
            "limitations":["Historical source B already inspected, new endpoint/update contrast not prospective.",
               "Only pre-2022 anchored continuing horses and strict classified eligible starts. B history is incomplete for true total exposure.",
               "Cohort composition decomposition compares different years and sources, not causal time decay.",
               "B residual donor updates use only prior years; global residual recalibration included, so profile update is not isolated kin signal.",
               "B11 minus M11 isolates incremental sire term relative to the updated global comparator; unbounded linear scores match PR85.",
               "Separate sire bootstrap pointwise sensitivity; repeated horses/years/seed fits are dependent.",
               "No genetic or voluntary preference claim, no raw records or individual predictions exported."]}

def self_test():
    # Source A prior and B updates use no same-year outcomes.
    old=pd.DataFrame({"horse":["a","b","c"],"sire_id":["s","s","t"],"surface":["turf","dirt","turf"],
                      "circuit":"JRA","stratum":["turf:4","dirt:4","turf:4"]})
    seed=next(k for k in range(100) if len(set(_hash_half(old.horse,k,"horse")))==2)
    q=pd.DataFrame({"horse":["a","b","a","b","a","b"],"sire_id":"s",
        "year":[2022,2022,2023,2023,2024,2024],"starts":[2]*6,
        "occupancy":[0.,1.,.5,.5,1.,0.]})
    q["half"]=_hash_half(q.horse,seed,"horse")
    old["half"]=_hash_half(old.horse,seed,"horse")
    prior=old.assign(turf=old.surface.eq("turf").astype(float)).groupby("half").turf.mean()
    q["base_own"]=(q.horse.map({"a":1.,"b":0.})+5*q.half.map(prior))/6
    q["own_prior_count"]=1
    u=update_own(old,q,seed)
    assert list(u.refreshed_own_n)==[1,1,3,3,5,5]
    v=q.copy();v.loc[v.year.eq(2024),"occupancy"]=.25
    w=update_own(old,v,seed)
    assert np.allclose(u.base_refreshed,w.base_refreshed)
    a=pd.DataFrame({"gain":[1.,3.,3.,3.],"prior_count":[0,1,1,1]})
    b=pd.DataFrame({"gain":[1.,1.,2.,2.],"own_prior_count":[0,0,1,1]})
    r=composition(a,b)
    assert abs(r["composition_term"]+r["within_stratum_term"]-r["A_minus_B_gain"])<1e-12
    p=pd.DataFrame({"horse":["a","b"],"sire_id":["s","t"],"occupancy":[.2,.8],
        "own_prior_count":[1,1],"refreshed_own_n":[2,2]})
    for k,x in {"B00":.5,"B10":.4,"B01":.45,"B11":.4,"M00":.5,"M10":.4,"M01":.45,"M11":.35}.items():
        p[k]=x
    r=score(p,seed)
    d=r["update_decomposition"]
    assert abs(d["own"]+d["profile_including_global"]-d["total"])<1e-12
    print("synthetic prior-year update, target-label invariance and decomposition checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--sqlite",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.archive,a.sqlite,a.output)):
        p.error("archive, sqlite and output required")
    r=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    compact={}
    for seed,v in r["results"].items():
        compact[seed]={"composition_A2021_B2022":v["composition_A2021_B2022"],
            "years":{y:{"all":w["all"],"no_prior_A_eligible":w["no_prior_A_eligible"],
                        "prior_A_eligible":w["prior_A_eligible"]} for y,w in v["years"].items()}}
    print(json.dumps({"status":r["status"],"primary":r["primary"],"secondary":r["secondary"],
        "results":compact},allow_nan=False))

if __name__=="__main__":
    main()
