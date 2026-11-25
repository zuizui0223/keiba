#!/usr/bin/env python3
"""Identity control for alignment of own updates with frozen family corrections.
Retrospective, historical-only donor matching; no genetic or learning causation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_2022_parent_placebo import load_sources,SQLITE_SHA
from ecology_japan_2022_joint_strict_strong import strict_mask_exact_horse_race
from ecology_japan_archive_forward import SOURCE_SHA
from ecology_japan_sire_context_specificity import SEEDS
from ecology_japan_sire_context_exposure_transfer import historical_panel
from ecology_japan_sire_context_time_transfer import predict_fold
from ecology_japan_context_occupancy_independent import audit_circuits,target_occupancy,source_a_baseline
from ecology_japan_context_occupancy_refresh import update_own,predictions,donor_panel,ci
from ecology_japan_context_within_individual import frame,same
from ecology_japan_context_distance_generalization import BANDS,band_view
from ecology_japan_context_opportunity_diversity import common_rows,REF_COUNTS,REF_UPDATE

EPS=1e-12
YEARS=(2022,2024)

def swap_profile(hist,b,seed):
    # All paired profiles constructed using only A 2019-21.
    d=donor_panel(hist,b,2022,False)
    target=b.loc[b.year.eq(2022),["horse","sire_id","year","half"]]
    out=[]
    for half in (0,1):
        t=target.loc[target.half.eq(half)]
        p,_=predict_fold(d.loc[d.half.ne(half)],t,seed)
        p["true_d"]=p.M1-p.M0
        p["swap_d"]=p.P-p.M0
        out.append(p[["horse","sire_id","matched","n","true_d","swap_d"]])
    r=pd.concat(out,ignore_index=True)
    if len(r)!=len(target) or r.horse.duplicated().any():
        raise ValueError("HOLD_PROFILE_JOIN")
    return r

def augment(rows,profile,early,late):
    x=rows.merge(profile,on=["horse","sire_id"],how="left",validate="one_to_one")
    if x.matched.isna().any():
        raise ValueError("HOLD_MISSING_PROFILE")
    same(x.d,x.true_d,"TRUE_PROFILE")
    e=early.set_index("horse");l=late.set_index("horse")
    for label,q in (("early",e),("late",l)):
        # With own update and frozen A global mean.
        x["r_"+label]=x.horse.map(q.occupancy-q.B10)
    if not np.isfinite(x[["d","du","r_early","r_late"]]).all().all():
        raise ValueError("HOLD_TARGET_VALUES")
    return x

def scoring(x,seed):
    # Magnitude-equalized placebo is defined only if the swapped sign exists.
    # Use same eligible set for raw and magnitude-controlled comparisons.
    m=x.matched&x.swap_d.notna()&x.d.abs().gt(EPS)&x.swap_d.abs().gt(EPS)
    q=x.loc[m].copy()
    out={"all_horses":len(x),"all_sires":int(x.sire_id.nunique()),
         "count_matched_horses":int(x.matched.sum()),"matched_nonzero_horses":len(q),
         "matched_nonzero_sires":int(q.sire_id.nunique())}
    if q.empty:
        return {"status":"HOLD_EMPTY",**out}
    t=q.d.to_numpy(float);p=q.swap_d.to_numpy(float);u=q.du.to_numpy(float)
    # Preserve true absolute magnitude exactly, change only sign according
    # to the historical count-matched other-sire correction. Not a forecast.
    e=np.abs(t)*np.sign(p)
    same(e*e,t*t,"MAGNITUDE_MATCH")
    def stats(d):
        a=np.mean(d*u);sd=np.sqrt(np.mean(d*d)*np.mean(u*u))
        return {"own_update_term":float(-2*a),"correction_rms":float(np.sqrt(np.mean(d*d))),
                "cosine":float(a/sd) if sd>EPS else None}
    out.update(status="DESCRIPTIVE",sign_discordant=int((np.sign(t)!=np.sign(p)).sum()),
        true=stats(t),swap=stats(p),equal_magnitude_swap=stats(e),
        alignment_true_minus_swap=ci(q,2*(t-p)*u,seed),
        alignment_true_minus_equal_magnitude_swap=ci(q,2*(t-e)*u,seed))
    # Secondary outcome checks: a more aligned correction can still have
    # negative incremental gain. Report its actual squared-loss gain.
    out["target_gain"]={}
    for y in ("early","late"):
        r=q["r_"+y].to_numpy(float)
        g={k:2*r*d-d*d for k,d in (("true",t),("swap",p),("equal_magnitude_swap",e))}
        out["target_gain"][y]={k:ci(q,v,seed) for k,v in g.items()}
        out["target_gain"][y]["true_minus_equal_magnitude_swap"]=ci(q,g["true"]-g["equal_magnitude_swap"],seed)
    return out

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
    out={}
    for j,(lo,hi) in enumerate(BANDS):
        label=f"{lo}-{hi}"
        a=band_view(old,lo,hi);b=band_view(strict,lo,hi)
        target,_=target_occupancy(b,circuit)
        out[label]={}
        for seed in SEEDS:
            hist=historical_panel(a,seed,False)
            z=update_own(a,source_a_baseline(a,target,seed),seed)
            early=frame(predictions(hist,z,2022,seed))
            late=frame(predictions(hist,z,2024,seed))
            r=common_rows(early,late,label)
            if len(r)!=REF_COUNTS[j]:
                raise ValueError("HOLD_PR89_COUNTS")
            if seed==SEEDS[0]:
                same(r.change.mean(),REF_UPDATE[j],"PR89_MEAN")
            x=augment(r,swap_profile(hist,z,seed),early,late)
            out[label][str(seed)]=scoring(x,seed)
    return {"status":"RETROSPECTIVE_FIXED_PROFILE_IDENTITY_ALIGNMENT_CONTROL",
        "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
        "primary":"1600-1999/20261124/alignment_true_minus_equal_magnitude_swap",
        "results":out,
        "limitations":["Count-matched other sire is not verified genetically unrelated, and management may differ.",
            "Equal-magnitude swap preserves true correction magnitude by design, not a deployable alternative predictor or independent effect estimate.",
            "Primary contrast tests alignment of directions; it is not a test of positive predictive gain. Separate outcome comparisons retain negative gains.",
            "Previously inspected archives, selected common observed horses and reused splits; not prospective.",
            "Conditional whole-sire pointwise intervals do not capture all shared-history/deeper-pedigree dependence.",
            "No genetic adaptation, animal learning, fitness, or wagering claim. Anonymous aggregates only."]}

def self_test():
    x=pd.DataFrame({"sire_id":["s","t","v"],"d":[.2,-.1,0.],"swap_d":[-.3,.4,.5],
        "du":[.1,-.2,.3],"matched":[True]*3,"r_early":[.3,-.3,.1],"r_late":[.1,-.1,.1]})
    r=scoring(x,SEEDS[0])
    assert r["matched_nonzero_horses"]==2 and r["sign_discordant"]==2
    same(r["alignment_true_minus_equal_magnitude_swap"]["MSE_gain"],.08,"SIGN_CONTROL")
    same(r["true"]["own_update_term"],-.04,"TRUE_TERM")
    same(r["equal_magnitude_swap"]["own_update_term"],.04,"SWAP_TERM")
    # Alignment result cannot be caused by final target surface labels.
    q=scoring(x.assign(r_late=99.),SEEDS[0])
    assert r["alignment_true_minus_equal_magnitude_swap"]==q["alignment_true_minus_equal_magnitude_swap"]
    print("synthetic fixed-scale direction and outcome-invariance checks passed")

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
