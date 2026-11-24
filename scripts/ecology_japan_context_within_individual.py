#!/usr/bin/env python3
"""Within-horse fixed-signal loss decomposition, chronological A/B occupancy.
No causal age, learning, genetic or wagering inference; aggregate only.
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
from ecology_japan_context_occupancy_independent import audit_circuits,target_occupancy,source_a_baseline
from ecology_japan_context_occupancy_refresh import source_a_reference,update_own,predictions,ci

YEARS=(2022,2023,2024)

def same(a,b,label):
    if not np.allclose(a,b,atol=1e-10,rtol=0):
        raise ValueError("HOLD_"+label)

def moment(r,d):
    c=float(np.mean(r*d));q=float(np.mean(d*d))
    return {"alignment":c,"correction_energy":q,"gain":2*c-q,
            "descriptive_oracle_weight_0_1":float(np.clip(c/q,0,1)) if q>1e-15 else None}

def frame(p):
    if p.horse.duplicated().any():
        raise ValueError("HOLD_DUPLICATE_HORSE")
    x=p[["horse","sire_id","year","occupancy","own_prior_count","refreshed_own_n",
         "B00","B10","B01","B11","M00","M10","M01","M11"]].copy()
    for c in ("horse","sire_id"):
        x[c]=x[c].astype(str)
    x["d"]=x.M00-x.B00
    x["u"]=x.B10-x.B00
    x["r"]=x.occupancy-x.B00
    x["g_stale"]=2*x.r*x.d-x.d**2
    x["g_own"]=2*(x.r-x.u)*x.d-x.d**2
    same(x.M10-x.B10,x.d,"FIXED_PROFILE")
    same(x.g_stale,(x.occupancy-x.B00)**2-(x.occupancy-x.M00)**2,"GAIN")
    same(x.g_own-x.g_stale,-2*x.d*x.u,"UPDATE_IDENTITY")
    d1=x.M01-x.B01
    same(x.M11-x.B11,d1,"FRESH_PROFILE")
    x["g_fresh_stale_own"]=2*(x.occupancy-x.B01)*d1-d1*d1
    x["g_fresh"]=2*(x.occupancy-x.B11)*d1-d1*d1
    same(x.g_fresh-x.g_fresh_stale_own,-2*d1*x.u,"FRESH_UPDATE_IDENTITY")
    return x

def comparison(a,b,seed,cohort=None):
    if a.year.nunique()!=1 or b.year.nunique()!=1 or int(a.year.iloc[0])>=int(b.year.iloc[0]):
        raise ValueError("HOLD_YEAR_ORDER")
    x=a.set_index("horse");y=b.set_index("horse")
    ids=x.index.intersection(y.index)
    if cohort is not None:
        ids=ids.intersection(cohort)
    if not len(ids):
        return {"status":"HOLD_NO_COMMON_HORSES"}
    aa=x.loc[ids];bb=y.loc[ids]
    if not aa.sire_id.equals(bb.sire_id):
        raise ValueError("HOLD_PARENT_IDENTITY")
    same(aa.d,bb.d,"ACROSS_YEAR_SIGNAL")
    same(aa.B00,bb.B00,"ACROSS_YEAR_BASELINE")
    if (bb.refreshed_own_n<aa.refreshed_own_n).any():
        raise ValueError("HOLD_HISTORY_COUNT")
    # For 2022 the own-update term is zero. The difference formula below
    # also works for 2023 -> 2024 when previous B records were added.
    dy=2*aa.d*(bb.occupancy-aa.occupancy)
    du=-2*aa.d*(bb.u-aa.u)
    total=bb.g_own-aa.g_own
    same(total,dy+du,"WITHIN_HORSE_IDENTITY")
    between=float(b.g_own.mean()-a.g_own.mean())
    # Population membership term relative to this fixed intersection.
    membership=float((b.g_own.mean()-bb.g_own.mean())-(a.g_own.mean()-aa.g_own.mean()))
    same(between,total.mean()+membership,"COMPOSITION_IDENTITY")
    return {"status":"DESCRIPTIVE","early_year":int(a.year.iloc[0]),"late_year":int(b.year.iloc[0]),
        "early_all":len(a),"late_all":len(b),"common_horses":len(ids),
        "common_sires":int(aa.sire_id.nunique()),
        "early_only_relative_to_common":len(a)-len(ids),"late_only_relative_to_common":len(b)-len(ids),
        "common_early_gain":float(aa.g_own.mean()),"common_late_gain":float(bb.g_own.mean()),
        "observed_occupancy_shift":ci(aa,dy.to_numpy(float),seed),
        "own_information_update_shift":ci(aa,du.to_numpy(float),seed),
        "within_common_total":ci(aa,total.to_numpy(float),seed),
        "full_population_gain_change":between,"membership_remainder":membership,
        "mean_history_count_early":float(aa.refreshed_own_n.mean()),
        "mean_history_count_late":float(bb.refreshed_own_n.mean()),
        "mean_absolute_occupancy_change":float(np.abs(bb.occupancy-aa.occupancy).mean())}

def summarize(x,seed):
    if x.empty:
        return {"status":"HOLD_EMPTY"}
    return {"horses":len(x),"sires":int(x.sire_id.nunique()),
        "stale_own_stale_profile":moment(x.r,x.d),
        "fresh_own_stale_profile":moment(x.r-x.u,x.d),
        "stale_own_fresh_profile":moment(x.occupancy-x.B01,x.M01-x.B01),
        "fresh_own_fresh_profile":moment(x.occupancy-x.B11,x.M11-x.B11),
        "own_update_fixed_profile":ci(x,(x.g_own-x.g_stale).to_numpy(float),seed),
        "own_update_fresh_profile":ci(x,(x.g_fresh-x.g_fresh_stale_own).to_numpy(float),seed)}

def analyze(archive,db):
    raw,old,future,_,gate,_=load_sources(archive,db)
    if len(old)!=2092836 or old.horse.nunique()!=90962 or len(future)!=255484 or future.horse.nunique()!=12919:
        raise ValueError("HOLD_SOURCE_PARITY")
    circuit,cqa=audit_circuits(raw,old,db,gate["two_event_anchor_horses"])
    if cqa.get("verified_JRA_codes")!=10 or cqa.get("verified_NAR_codes")!=14 or cqa["matched_distinct_pre2022_source_B_races"]!=85856:
        raise ValueError("HOLD_VENUE_PARITY")
    mask,sqa=strict_mask_exact_horse_race(raw,future,db,gate["two_event_anchor_horses"])
    strict=future.loc[mask]
    if len(strict)!=244147 or strict.horse.nunique()!=12887:
        raise ValueError("HOLD_STRICT_PARITY")
    t,qa=target_occupancy(strict,circuit)
    if t.groupby("year",observed=True).size().to_dict()!={2022:3011,2023:1588,2024:743}:
        raise ValueError("HOLD_TARGET_PARITY")
    out={}
    for seed in SEEDS:
        a,_=source_a_reference(old,seed)
        b=update_own(old,source_a_baseline(old,t,seed),seed)
        panels={yr:frame(predictions(a,b,yr,seed)) for yr in YEARS}
        if seed==SEEDS[0]:
            same(panels[2022].g_stale.mean(),.001961299416552986,"PR85")
            same(panels[2024].g_fresh.mean(),-.009304296089139295,"PR86")
        ids=set.intersection(*(set(p.horse) for p in panels.values()))
        annual={}
        for yr,p in panels.items():
            annual[str(yr)]={"all":summarize(p,seed),
                "no_prior_A":summarize(p.loc[p.own_prior_count.eq(0)],seed),
                "prior_A":summarize(p.loc[p.own_prior_count.gt(0)],seed),
                "common_three_years":summarize(p.loc[p.horse.isin(ids)],seed)}
        out[str(seed)]={"annual":annual,"common_three_years":len(ids),"pairs":{}}
        for u,v in ((2022,2023),(2022,2024),(2023,2024)):
            k=f"{u}-{v}"
            out[str(seed)]["pairs"][k]={"pair_intersection":comparison(panels[u],panels[v],seed),
                "three_year_intersection":comparison(panels[u],panels[v],seed,ids)}
    return {"status":"RETROSPECTIVE_WITHIN_HORSE_FIXED_SIGNAL_DECOMPOSITION",
        "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
        "primary":"20261124/2022-2024/pair_intersection/own_information_update_shift",
        "target_scope":qa,"results":out,
        "limitations":["Same historical cohorts already inspected; not independent replication.",
            "Intersection conditions on observed eligible starts in both years, not survival or fitness. Membership remainder is descriptive.",
            "Own update is a change in model inputs, not a causal learning or age effect.",
            "Observed turf fraction, not physiological response or voluntary preference.",
            "Fixed-signal moments use target labels only for evaluation; oracle weights are descriptive, not predictions.",
            "Separate sire bootstrap pointwise sensitivity, not joint or simultaneous inference. No individual records exported."]}

def self_test():
    def row(h,y,o,u):
        return dict(horse=h,sire_id="s"+h,year=y,occupancy=o,own_prior_count=1,refreshed_own_n=1+y-2022,
            B00=.3,B10=.3+u,B01=.4,B11=.4+u,M00=.5,M10=.5+u,M01=.5,M11=.5+u)
    a=frame(pd.DataFrame([row("a",2022,.2,0),row("b",2022,.8,0),row("c",2022,.6,0)]))
    b=frame(pd.DataFrame([row("a",2024,.4,.1),row("b",2024,.9,.2),row("d",2024,.1,.1)]))
    z=comparison(a,b,SEEDS[0])
    assert z["common_horses"]==2
    same(z["observed_occupancy_shift"]["MSE_gain"],.06,"TEST_Y")
    same(z["own_information_update_shift"]["MSE_gain"],-.06,"TEST_U")
    same(z["within_common_total"]["MSE_gain"],0,"TEST_TOTAL")
    same(z["full_population_gain_change"],z["membership_remainder"],"TEST_MEMBERSHIP")
    same(moment(a.r,a.d)["gain"],a.g_stale.mean(),"TEST_MOMENT")
    print("synthetic fixed-signal algebra, common-cohort and membership checks passed")

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
    print(json.dumps(r,allow_nan=False))

if __name__=="__main__":
    main()
