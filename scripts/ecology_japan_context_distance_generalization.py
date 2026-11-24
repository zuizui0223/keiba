#!/usr/bin/env python3
"""Distance-band generalization of fixed family correction information dynamics.

Same source-lock and prior-year updates as PR88; no new outcomes outside
the already examined historical archives. Only aggregate output.
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
from ecology_japan_sire_context_exposure_transfer import historical_panel,evaluate_exposure
from ecology_japan_context_occupancy_independent import audit_circuits,target_occupancy,source_a_baseline
from ecology_japan_context_occupancy_refresh import update_own,predictions
from ecology_japan_context_within_individual import frame,comparison,summarize,same

BANDS=((1200,1599),(1600,1999),(2000,2399))
AYEARS=(2019,2020,2021)
BYEARS=(2022,2023,2024)
MIN_SURFACE_STARTS=20
MIN_TARGET_HORSES=100

def band_view(d,lo,hi):
    """Restrict *before* internal context encoding, never mix distance bands.

    Existing helpers use turf:4/dirt:4 as context labels; recode only the
    already selected band's valid flat starts to those internal tokens.
    Distance itself stays unchanged, and the original frame is not modified.
    """
    if (lo,hi) not in BANDS:
        raise ValueError("HOLD_UNREGISTERED_BAND")
    x=d.loc[d.distance.between(lo,hi)&d.surface.isin(["turf","dirt"])].copy()
    x["stratum"]=x.surface.astype(str)+":4"
    if len(x) and not x.distance.between(lo,hi).all():
        raise ValueError("HOLD_BAND_LEAK")
    return x

def surface_support(d,years):
    out={}
    for y in years:
        p=d.loc[d.year.eq(y)&d.circuit.eq("JRA")&d.sire_id.astype(str).ne("")]
        out[str(y)]={"starts":len(p),"horses":int(p.horse.nunique()),
            "turf_starts":int(p.surface.eq("turf").sum()),
            "dirt_starts":int(p.surface.eq("dirt").sum())}
    return out

def has_support(q):
    return all(v["horses"]>=MIN_TARGET_HORSES and
               min(v["turf_starts"],v["dirt_starts"])>=MIN_SURFACE_STARTS
               for v in q.values())

def band_analysis(old,strict,circuit,lo,hi):
    a=band_view(old,lo,hi)
    b=band_view(strict,lo,hi)
    b["circuit"]=b.race.astype(str).map(circuit).fillna("UNKNOWN")
    sa=surface_support(a,AYEARS);sb=surface_support(b,BYEARS)
    target,scope=target_occupancy(b,circuit)
    result={"source_A_support":sa,"source_B_support":sb,"source_B_scope":scope,
        "status":"HOLD_BAND_SUPPORT"}
    if not has_support(sa) or not has_support(sb):
        return result
    out={}
    for seed in SEEDS:
        hist=historical_panel(a,seed,False)
        ref=evaluate_exposure(hist,seed,"base_own")
        z=update_own(a,source_a_baseline(a,target,seed),seed)
        p={y:frame(predictions(hist,z,y,seed)) for y in BYEARS}
        if seed==SEEDS[0] and lo==1600:
            if [len(p[y]) for y in BYEARS]!=[3011,1588,743]:
                raise ValueError("HOLD_REFERENCE_DENOMINATOR")
            same(ref["2021"]["all_targets"]["contrasts"]["M0_minus_M1"]["MSE_gain"],
                .01471092236633107,"PR81")
            same(p[2022].g_stale.mean(),.001961299416552986,"PR85")
            same(p[2024].g_fresh.mean(),-.009304296089139295,"PR86")
        ids=set.intersection(*(set(x.horse) for x in p.values()))
        primary=comparison(p[2022],p[2024],seed)
        if seed==SEEDS[0] and lo==1600:
            if primary["common_horses"]!=599:
                raise ValueError("HOLD_PR88_INTERSECTION")
            same(primary["own_information_update_shift"]["MSE_gain"],
                -.016105814555317205,"PR88")
        out[str(seed)]={"source_A":{y:r["all_targets"] for y,r in ref.items()},
            "source_B_annual":{str(y):summarize(x,seed) for y,x in p.items()},
            "common_three_year_horses":len(ids),
            "pair_intersections":{f"{u}-{v}":comparison(p[u],p[v],seed)
                                  for u,v in ((2022,2023),(2022,2024),(2023,2024))},
            "three_year_intersection_2022_2024":comparison(p[2022],p[2024],seed,ids)}
    result.update(status="EVALUATED_RETROSPECTIVE",results=out)
    return result

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
    result={}
    for lo,hi in BANDS:
        result[f"{lo}-{hi}"]=band_analysis(old,strict,circuit,lo,hi)
    if result["1600-1999"]["status"]!="EVALUATED_RETROSPECTIVE":
        raise ValueError("HOLD_REFERENCE")
    return {"status":"RETROSPECTIVE_DISTANCE_BAND_GENERALIZATION",
        "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
        "primary":"1200-1599/20261124/2022-2024/pair_intersections/own_information_update_shift",
        "bands":[list(b) for b in BANDS],
        "minimum_surface_starts_per_year":MIN_SURFACE_STARTS,
        "minimum_target_horses_per_year":MIN_TARGET_HORSES,
        "circuit_gate":cqa,"strict_gate":sqa,"results":result,
        "limitations":["Predeclared adjacent distance bands in previously inspected archives; not prospective replication.",
            "Horse and sire membership can overlap bands, years and seeds; estimates dependent.",
            "Support-conditioned observations of annual turf fraction, not physiology or animal choice.",
            "Source B anchored continuing horses and strictly classified starts only; not all entries.",
            "Fixed additive correction loss and model-input updates, not causal biological learning or genetic effects.",
            "Pointwise sire bootstrap; no simultaneous or all-dependence inference. No individual records exported."]}

def self_test():
    d=pd.DataFrame({"distance":[1199,1200,1599,1600,1999,2000,2399,2400],
         "surface":["turf","turf","dirt","turf","dirt","turf","dirt","dirt"],
         "stratum":["original"]*8})
    seen=set()
    for lo,hi in BANDS:
        x=band_view(d,lo,hi)
        assert len(x)==2 and x.stratum.tolist()==["turf:4","dirt:4"]
        assert not (set(x.index)&seen)
        seen.update(x.index)
        assert x.distance.between(lo,hi).all()
    assert d.stratum.eq("original").all()
    assert has_support({"2020":{"horses":100,"turf_starts":20,"dirt_starts":20}})
    assert not has_support({"2020":{"horses":100,"turf_starts":20,"dirt_starts":19}})
    print("synthetic nonoverlapping band selection and support gate passed")

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
