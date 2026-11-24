#!/usr/bin/env python3
"""Observed historical race-supply balance and own-information substitution.

An allocation opportunity proxy from earlier classified races, not a verified
choice set for a horse. Retrospective source A/B. Aggregate output only.
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
from ecology_japan_sire_context_exposure_transfer import historical_panel
from ecology_japan_context_occupancy_independent import audit_circuits,target_occupancy,source_a_baseline
from ecology_japan_context_occupancy_refresh import update_own,predictions
from ecology_japan_context_within_individual import frame,same
from ecology_japan_context_distance_generalization import BANDS,band_view

SUPPLY_YEARS=(2017,2018,2019,2020,2021)
MIN_RACES=10
MIN_COVERAGE=.8
MIN_HORSES=100
MIN_SIRES=30
DRAWS=999
REF_COUNTS=(531,599,267)
REF_UPDATE=(-.01503752854633637,-.016105814555317205,-.0015884911465663262)
BAND_LABELS=tuple(f"{lo}-{hi}" for lo,hi in BANDS)
CONTROLS=("log_prior","log_added","baseline_extremity","log_supply")
ENERGY=("abs_d","abs_u","abs_product")

def historical_supply(old):
    """Supply counts distinct classified races; portfolio counts starts.

    The venue-quarter mix comes from each horse's earlier JRA starts at all
    flat distances. No 2022+ rows, target surface outcomes, current venues,
    or target race counts enter this index.
    """
    a=old.loc[old.year.isin(SUPPLY_YEARS)&old.circuit.eq("JRA")&
              old.surface.isin(["turf","dirt"]),
              ["horse","race","day","year","course","distance","surface"]].copy()
    for c in ("horse","race","course","surface"):
        a[c]=a[c].astype(str)
    if a.empty or not a.year.lt(2022).all() or a.day.isna().any():
        raise ValueError("HOLD_SUPPLY_HISTORY")
    a["quarter"]=a.day.dt.quarter
    race=a[["race","course","quarter","distance","surface"]].drop_duplicates()
    if race.race.duplicated().any() or a.duplicated(["horse","race"]).any():
        raise ValueError("HOLD_SUPPLY_RACE_IDENTITY")
    port=a.groupby(["horse","course","quarter"],observed=True).size().rename("portfolio_n").reset_index()
    port["portfolio_total"]=port.groupby("horse",observed=True).portfolio_n.transform("sum")
    port["weight"]=port.portfolio_n/port.portfolio_total
    if not np.allclose(port.groupby("horse",observed=True).weight.sum(),1):
        raise ValueError("HOLD_PORTFOLIO_WEIGHT")
    return race,port

def opportunity(race,port,lo,hi):
    b=race.loc[race.distance.between(lo,hi)].copy()
    b["turf"]=b.surface.eq("turf").astype(int)
    counts=b.groupby(["course","quarter"],observed=True).turf.agg(["sum","size"]).reset_index()
    counts=counts.rename(columns={"sum":"turf_races","size":"n_races"})
    counts["supported"]=counts.n_races.ge(MIN_RACES)
    p=counts.turf_races/counts.n_races
    counts["balance"]=4*p*(1-p)
    q=port.merge(counts,on=["course","quarter"],how="left",validate="many_to_one")
    good=q.supported.eq(True)
    q["covered"]=q.weight*good.astype(float)
    q["balance_mass"]=q.covered*q.balance.fillna(0)
    q["supply_mass"]=q.covered*q.n_races.fillna(0)
    # Equal cell weight, rather than number of historical focal starts.
    q["cell"]=good.astype(int)
    q["cell_balance"]=q.cell*q.balance.fillna(0)
    o=q.groupby("horse",observed=True).agg(coverage=("covered","sum"),
        balance_mass=("balance_mass","sum"),supply_mass=("supply_mass","sum"),
        covered_cells=("cell","sum"),all_cells=("cell","size"),
        cell_balance=("cell_balance","sum"))
    o["q"]=o.balance_mass/o.coverage.replace(0,np.nan)
    o["q_equal_cell"]=o.cell_balance/o.covered_cells.replace(0,np.nan)
    o["supply"]=o.supply_mass/o.coverage.replace(0,np.nan)
    o["eligible"]=o.coverage.ge(MIN_COVERAGE-1e-12)&o.covered_cells.gt(0)
    o.loc[~o.eligible,["q","q_equal_cell","supply"]]=np.nan
    if not o.loc[o.eligible,"q"].between(0,1+1e-12).all():
        raise ValueError("HOLD_BALANCE_RANGE")
    return o.reset_index()[["horse","coverage","all_cells","covered_cells","eligible","q","q_equal_cell","supply"]],{
        "distinct_races":len(b),"cells":len(counts),
        "supported_cells":int(counts.supported.sum()),
        "turf_races":int(b.turf.sum()),"dirt_races":int(len(b)-b.turf.sum())}

def common_rows(a,b,band):
    x=a.set_index("horse");y=b.set_index("horse")
    ids=x.index.intersection(y.index)
    aa=x.loc[ids];bb=y.loc[ids]
    if not aa.sire_id.equals(bb.sire_id):
        raise ValueError("HOLD_PARENT_IDENTITY")
    same(aa.d,bb.d,"FIXED_D")
    same(aa.B00,bb.B00,"FIXED_BASELINE")
    n=bb.refreshed_own_n-aa.refreshed_own_n
    if (n<0).any():
        raise ValueError("HOLD_NEGATIVE_HISTORY")
    u=bb.u-aa.u;d=aa.d
    r=pd.DataFrame({"horse":ids,"sire_id":aa.sire_id.to_numpy(),
        "band":band,"prior_n":aa.refreshed_own_n.to_numpy(int),
        "added_n":n.to_numpy(int),"baseline":aa.B00.to_numpy(float),
        "d":d.to_numpy(float),"du":u.to_numpy(float),
        "change":(-2*d*u).to_numpy(float)})
    return r

def panel_support(x):
    return {"rows":len(x),"horses":int(x.horse.nunique()),"sires":int(x.sire_id.nunique()),
        "by_band":{k:{"rows":len(g),"horses":int(g.horse.nunique()),
                     "sires":int(g.sire_id.nunique())}
                   for k,g in x.groupby("band",observed=True)}}

def prepare(x):
    y=x.copy()
    y["log_prior"]=np.log1p(y.prior_n)
    y["log_added"]=np.log1p(y.added_n)
    y["baseline_extremity"]=np.abs(y.baseline-.5)
    y["log_supply"]=np.log1p(y.supply)
    y["abs_d"]=np.abs(y.d)
    y["abs_u"]=np.abs(y.du)
    y["abs_product"]=y.abs_d*y.abs_u
    return y

def design(x,mode,q_col):
    """No outcome-informed variables or bin selection in regression design.

    Energy sensitivity controls realized correction magnitudes, not a causal
    adjustment; within-horse analysis demeans all design columns and response.
    """
    y=x.copy()
    if mode=="within_horse":
        n=y.groupby("horse",observed=True).band.transform("size")
        y=y.loc[n.ge(2)].copy()
    if len(y)<MIN_HORSES or y.horse.nunique()<MIN_HORSES or y.sire_id.nunique()<MIN_SIRES:
        return None,y,{"status":"HOLD_LOW_SUPPORT",**panel_support(y)}
    if set(y.band)!=set(BAND_LABELS) or any(len(g)<MIN_HORSES for _,g in y.groupby("band",observed=True)):
        return None,y,{"status":"HOLD_BAND_SUPPORT",**panel_support(y)}
    if y.groupby("horse",observed=True).sire_id.nunique().max()>1:
        raise ValueError("HOLD_HORSE_PARENT_CONFLICT")
    wt=1/y.groupby("horse",observed=True).band.transform("size").to_numpy(float)
    xq=y[q_col].to_numpy(float)
    # The primary scale is per 0.1 balance; band fixed effects remove
    # comparisons driven solely by distance category.
    cols={"balance_per_0_1":xq/.1}
    for label in BAND_LABELS[1:]:
        cols["band_"+label]=y.band.eq(label).to_numpy(float)
    controls=() if mode=="band_only" else CONTROLS+(ENERGY if mode=="energy" else ())
    for c in controls:
        a=y[c].to_numpy(float);m=np.average(a,weights=wt)
        sd=np.sqrt(np.average((a-m)**2,weights=wt))
        if sd<1e-10:
            return None,y,{"status":"HOLD_CONSTANT_CONTROL","control":c,**panel_support(y)}
        cols[c]=(a-m)/sd
    X=pd.DataFrame(cols,index=y.index);r=y.change.to_numpy(float)
    if mode=="within_horse":
        X=X-X.groupby(y.horse,observed=True).transform("mean")
        r=r-y.groupby("horse",observed=True).change.transform("mean").to_numpy(float)
    else:
        X.insert(0,"intercept",1.)
    if not np.isfinite(X.to_numpy()).all() or not np.isfinite(r).all():
        raise ValueError("HOLD_NONFINITE_DESIGN")
    if np.linalg.matrix_rank(X.to_numpy()*np.sqrt(wt)[:,None])!=len(X.columns):
        return None,y,{"status":"HOLD_RANK",**panel_support(y)}
    return (X.to_numpy(float),r,wt,list(X.columns)),y,None

def fit(x,seed,mode="adjusted",q_col="q"):
    z,y,hold=design(x,mode,q_col)
    if hold is not None:
        return hold
    X,r,w,names=z
    # Equal total weight per horse; resample whole sire blocks jointly over
    # all distance bands. Crossproducts preserve joint dependence of rows.
    levels=pd.factorize(y.sire_id,sort=True)[0];n=len(np.unique(levels))
    k=X.shape[1]
    xx=np.zeros((n,k,k));xy=np.zeros((n,k))
    np.add.at(xx,levels,X[:,:,None]*X[:,None,:]*w[:,None,None])
    np.add.at(xy,levels,X*(w*r)[:,None])
    mat=xx.sum(axis=0);vec=xy.sum(axis=0)
    if np.linalg.cond(mat)>1e10:
        return {"status":"HOLD_ILL_CONDITIONED",**panel_support(y)}
    point=np.linalg.solve(mat,vec)
    index=names.index("balance_per_0_1")
    rng=np.random.default_rng(seed)
    draws=[]
    for _ in range(DRAWS):
        count=np.bincount(rng.integers(n,size=n),minlength=n)
        a=np.einsum("i,ijk->jk",count,xx)
        b=count@xy
        if np.linalg.cond(a)<=1e10:
            draws.append(float(np.linalg.solve(a,b)[index]))
    out={"status":"DESCRIPTIVE","beta_per_0_1":float(point[index]),
         "valid_bootstrap_draws":len(draws),"mode":mode,"balance_definition":q_col,
         "mean_balance":float(np.average(y[q_col],weights=w)),**panel_support(y)}
    if len(draws)>=.95*DRAWS:
        out["CI95_pointwise"]=np.quantile(draws,[.025,.975]).tolist()
    else:
        out["status"]="HOLD_BOOTSTRAP_SUPPORT"
    return out

def band_summary(x):
    r={}
    for label,g in x.groupby("band",observed=True):
        # Raw own-update term equals -2 times the alignment of d and du.
        a=float(np.mean(g.d*g.du));d2=float(np.mean(g.d*g.d));u2=float(np.mean(g.du*g.du))
        same(g.change.mean(),-2*a,"ENERGY_IDENTITY")
        r[label]={"rows":len(g),"horses":int(g.horse.nunique()),"sires":int(g.sire_id.nunique()),
            "mean_prior_n":float(g.prior_n.mean()),"mean_added_n":float(g.added_n.mean()),
            "mean_balance":float(g.q.mean()),"sd_balance":float(g.q.std(ddof=0)),
            "mean_change":float(g.change.mean()),"d_rms":float(np.sqrt(d2)),
            "u_rms":float(np.sqrt(u2)),
            "cosine_alignment":float(a/np.sqrt(d2*u2)) if d2*u2>1e-20 else None}
    return r

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
    race,port=historical_supply(old)
    supply={};panels={str(s):[] for s in SEEDS}
    for j,(lo,hi) in enumerate(BANDS):
        label=BAND_LABELS[j]
        a=band_view(old,lo,hi);b=band_view(strict,lo,hi)
        target,qa=target_occupancy(b,circuit)
        opp,supply[label]=opportunity(race,port,lo,hi)
        for seed in SEEDS:
            hist=historical_panel(a,seed,False)
            z=update_own(a,source_a_baseline(a,target,seed),seed)
            early=frame(predictions(hist,z,2022,seed));late=frame(predictions(hist,z,2024,seed))
            rows=common_rows(early,late,label)
            if len(rows)!=REF_COUNTS[j]:
                raise ValueError("HOLD_PR89_COUNTS")
            if seed==SEEDS[0]:
                same(rows.change.mean(),REF_UPDATE[j],"PR89_MEAN")
            panels[str(seed)].append(rows.merge(opp,on="horse",how="left",validate="one_to_one"))
    out={}
    for seed,parts in panels.items():
        x=pd.concat(parts,ignore_index=True)
        if x.duplicated(["horse","band"]).any():
            raise ValueError("HOLD_PANEL_DUPLICATE")
        matched=x.loc[x.eligible.eq(True)&x.q.notna()&x.q_equal_cell.notna()&x.supply.notna()].copy()
        matched=prepare(matched)
        out[seed]={"all_support":panel_support(x),"supported_opportunity":panel_support(matched),
            "unsupported_rows":len(x)-len(matched),
            "band_summary":band_summary(matched) if len(matched) else {},
            "fits":{mode:fit(matched,int(seed),mode) for mode in ("adjusted","band_only","energy","within_horse")}}
        out[seed]["fits"]["equal_cell_weights"]=fit(matched,int(seed),"adjusted","q_equal_cell")
    return {"status":"RETROSPECTIVE_HISTORICAL_SUPPLY_BALANCE_ASSOCIATION",
        "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
        "primary":"20261124/fits/adjusted/beta_per_0_1",
        "supply_years":list(SUPPLY_YEARS),"min_races_per_cell":MIN_RACES,
        "minimum_portfolio_coverage":MIN_COVERAGE,
        "supply_summary":supply,"results":out,
        "limitations":["Historical classified race supply near observed former venue-quarter portfolio is not an individual feasible choice set.",
            "Portfolio is selected by past management and allocation; measured association is not an exogenous environmental cause.",
            "Own-update outcome is an algebraic model-input contrast; 2024 occupancy is not used to construct it, but cohort selection conditions on 2024 observations.",
            "Counts and energy terms are descriptive controls, some from earlier B history; not causal adjustment.",
            "Same archives and overlapping horses, bands and seeds; no prospective independent validation.",
            "Whole-sire refitted pointwise intervals are conditional on supplied histories and predictions, not all-dependence or simultaneous intervals.",
            "No genetic, learning, habitat choice, physiological or fitness claim. No individual records exported."]}

def self_test():
    r=pd.DataFrame({"race":["a","b","c","d"]*5,"course":["T"]*20,"quarter":[1]*20,
                    "distance":[1200]*20,"surface":["turf","dirt","turf","dirt"]*5})
    r["race"]=[f"r{i}" for i in range(20)]
    p=pd.DataFrame({"horse":["h","h","j"],"course":["T","U","T"],"quarter":[1,1,1],
                    "weight":[.9,.1,1.]})
    q,s=opportunity(r,p,1200,1599)
    assert len(q)==2 and np.allclose(q.q,1) and np.allclose(q.q_equal_cell,1)
    assert s["distinct_races"]==20
    q2,_=opportunity(r,p.assign(weight=[.5,.5,1.]),1200,1599)
    assert not q2.loc[q2.horse.eq("h"),"eligible"].iloc[0]
    assert q2.loc[q2.horse.eq("h"),"q"].isna().all()
    p=[]
    rng=np.random.default_rng(4)
    for j in range(150):
        for band in BAND_LABELS:
            q=float(rng.uniform(.2,.9))
            p.append({"horse":str(j),"sire_id":str(j%50),"band":band,"q":q,"q_equal_cell":q,
                "prior_n":int(rng.integers(0,15)),"added_n":int(rng.integers(1,15)),
                "baseline":float(rng.uniform(.1,.9)),"supply":float(rng.uniform(10,100)),
                "d":float(rng.normal()),"du":float(rng.normal()),"change":-.02*q/.1})
    x=prepare(pd.DataFrame(p))
    for mode in ("adjusted","band_only","within_horse"):
        z=fit(x,SEEDS[0],mode)
        assert z["status"]=="DESCRIPTIVE" and abs(z["beta_per_0_1"]+.02)<1e-10
        assert z["CI95_pointwise"][1]<0
    print("synthetic distinct supply, coverage gate and within-band/horse regression checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path);p.add_argument("--sqlite",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.archive,a.sqlite,a.output)):
        p.error("archive, sqlite and output required")
    z=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(z,allow_nan=False))

if __name__=="__main__":
    main()
