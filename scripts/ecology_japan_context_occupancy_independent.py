#!/usr/bin/env python3
"""Source-B 2022–24 validation of frozen source-A annual context occupancy.

Only old-horse identity candidates corroborated by >=2 pre-2022 events.
A race-place code is eligible only after pre-2022 event-based circuit audit.
Do not claim new entrant validation, causal genetics, or prospective results.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_2022_joint_strict_strong import strict_mask_exact_horse_race
from ecology_japan_2022_independent_forward import parse_independent_history
from ecology_japan_hf_event_anchor_gate import anchor_name_histories
from ecology_japan_archive_forward import SOURCE_SHA
from ecology_japan_sire_context_specificity import CONTEXTS,SEEDS,_hash_half
from ecology_japan_sire_context_exposure_transfer import historical_panel,evaluate_exposure,OWN_SHRINK,TRAINER_SHRINK
from ecology_japan_sire_context_time_transfer import evaluate

TEST=(2022,2023,2024)
MIN_RACES=20
MIN_DAYS=5
MIN_HORSES=100

def make_circuit_map(evidence, min_races=MIN_RACES, min_days=MIN_DAYS):
    """Use distinct matched source-B race events, not repeated horse rows.

    Reject every place code with conflicting JRA/NAR evidence or ambiguous
    race linkage; do not use a majority threshold to resolve conflicts.
    """
    grouped=defaultdict(lambda:defaultdict(lambda:{"races":set(),"days":set()}))
    for code,rid,day,circuit in evidence:
        if not code or circuit not in ("JRA","NAR"):
            continue
        g=grouped[code][circuit]
        g["races"].add(rid);g["days"].add(day)
    out={};status=Counter()
    for code,g in grouped.items():
        if len(g)!=1:
            status["conflicting_codes"]+=1;continue
        c,v=next(iter(g.items()))
        if len(v["races"])<min_races or len(v["days"])<min_days:
            status["low_support_codes"]+=1;continue
        out[code]=c
        status["verified_"+c+"_codes"]+=1
        status["supporting_"+c+"_races"]+=len(v["races"])
    return out,dict(status)

def audit_circuits(raw,old,db,n_anchors):
    """Derive venue/circuit code mapping entirely from pre-2022 overlaps."""
    h=old[["horse","day","distance","surface","rank","circuit"]].copy()
    h["horse"]=h.horse.astype(str)
    h["day"]=h.day.dt.normalize()
    keys=["horse","day","distance","surface","rank"]
    # Only unambiguous source-A event keys; exclude duplicate matches even
    # if both happen to carry the same circuit label.
    h=h.loc[~h.duplicated(keys,keep=False)]
    lookup=h.set_index(keys).circuit.astype(str).to_dict()
    con=sqlite3.connect(f"file:{db}?mode=ro",uri=True)
    try:
        meta={str(rid):(day,dist,course,str(place).strip() if place is not None else "")
              for rid,day,dist,course,place in con.execute("SELECT rid,date,distance,course,place_id FROM race")}
        if len(meta)!=con.execute("SELECT count(*) FROM race").fetchone()[0]:
            raise ValueError("HOLD_RACE_ID_COLLISION")
        def records():
            return con.execute("SELECT hid,name,races FROM horse")
        cw,gate=anchor_name_histories(raw[["horse_id","horse_name","date","place","distance"]],
            records,race_dates={k:v[0] for k,v in meta.items()})
        if gate["two_event_anchor_horses"]!=n_anchors or len(set(cw.values()))!=len(cw):
            raise ValueError("HOLD_ANCHOR_PARITY")
        pre={k:v[:3] for k,v in meta.items() if str(v[0])[:4] and str(v[0])[:4]<"2022"}
        evidence=set(); per_race=defaultdict(set)
        for hid,_,hist in records():
            horse=cw.get(str(hid))
            if horse is None:
                continue
            events,_=parse_independent_history(hist,pre)
            for e in events:
                if e["year"]>=2022:
                    raise ValueError("HOLD_VENUE_FUTURE_LEAK")
                rid=str(e["race_id"])
                rank=1+e["y"]*(e["source_declared_field_size"]-1)
                if not np.isclose(rank,round(rank),atol=1e-8):
                    continue
                c=lookup.get((horse,e["day"].normalize(),e["distance"],e["surface"],round(rank)))
                if c:
                    code=meta[rid][3]
                    if code:
                        evidence.add((code,rid,e["day"].date().isoformat(),c))
                        per_race[rid].add(c)
        # Conflicting matches are deliberately retained in the code gate,
        # rather than removing their adverse evidence.
        mapping,qa=make_circuit_map(evidence)
        qa["matched_distinct_pre2022_source_B_races"]=len(per_race)
        qa["conflicting_pre2022_races"]=sum(len(v)>1 for v in per_race.values())
        qa["two_event_anchor_horses"]=len(cw)
        qa["future_race_code_mapping_uses_only_pre2022_records"]=True
        return {rid:mapping.get(v[3],"UNKNOWN") for rid,v in meta.items()},qa
    finally:
        con.close()

def target_occupancy(future,circuit):
    f=future.copy()
    f["circuit"]=f.race.astype(str).map(circuit).fillna("UNKNOWN")
    eligible=f.loc[f.stratum.isin(CONTEXTS)&f.circuit.eq("JRA")&f.sire_id.astype(str).ne("")].copy()
    qa={}
    for y in TEST:
        a=f.loc[f.year.eq(y)]
        e=eligible.loc[eligible.year.eq(y)]
        qa[str(y)]={"source_starts":len(a),"unknown_circuit_starts":int(a.circuit.eq("UNKNOWN").sum()),
                     "JRA_starts":int(a.circuit.eq("JRA").sum()),"eligible_starts":len(e),
                     "eligible_horses":int(e.horse.nunique())}
    if eligible.duplicated(["horse","race"]).any():
        raise ValueError("HOLD_DUPLICATE_TARGET_START")
    eligible["turf"]=eligible.surface.eq("turf").astype(float)
    t=eligible.groupby(["year","horse","sire_id"],observed=True).turf.agg(["mean","size"]).reset_index()
    t=t.rename(columns={"mean":"occupancy","size":"starts"})
    if t.duplicated(["horse","year"]).any():
        raise ValueError("HOLD_PARENT_CONFLICT")
    return t,qa

def source_a_baseline(old,target,seed):
    """Freeze all own and last-known-trainer priors at 2021-12-31.

    No source-B target-year or earlier-B outcomes used as model inputs.
    The annual observed target surface fraction is used only at scoring.
    """
    if not old.year.lt(2022).all() or not target.year.ge(2022).all():
        raise ValueError("HOLD_CUTOFF")
    h=old.loc[old.circuit.eq("JRA")&old.stratum.isin(CONTEXTS)&old.sire_id.astype(str).ne(""),
              ["horse","trainer_id","day","race","surface"]].copy()
    for c in ("horse","trainer_id","race"):
        h[c]=h[c].astype(str)
    h["half"]=_hash_half(h.horse,seed,"horse")
    h["turf"]=h.surface.eq("turf").astype(float)
    t=target.copy().reset_index(drop=True)
    t["horse"]=t.horse.astype(str);t["sire_id"]=t.sire_id.astype(str)
    t["half"]=_hash_half(t.horse,seed,"horse")
    a=h.groupby(["horse","half"],observed=True).turf.agg(["mean","size"]).reset_index()
    means=a.groupby("half",observed=True)["mean"].mean()
    a=a.set_index("horse")
    n=t.horse.map(a["size"]).fillna(0).to_numpy(float)
    p=t.horse.map(a["mean"]).fillna(0).to_numpy(float)
    g=t.half.map(means).to_numpy(float)
    if not np.isfinite(g).all():
        raise ValueError("HOLD_PRIOR")
    t["base_own"]=(n*p+OWN_SHRINK*g)/(n+OWN_SHRINK)
    last=h.sort_values(["day","race","horse"],kind="mergesort").drop_duplicates("horse",keep="last").set_index("horse").trainer_id
    tr=t.horse.map(last).fillna("")
    peer=h.loc[h.trainer_id.ne("")].groupby(["trainer_id","horse"],observed=True).turf.mean()
    total=peer.groupby(level=0).agg(["sum","size"])
    s=tr.map(total["sum"]).fillna(0).to_numpy(float)
    k=tr.map(total["size"]).fillna(0).to_numpy(float)
    focal=peer.reindex(pd.MultiIndex.from_arrays([tr,t.horse]))
    s-=focal.fillna(0).to_numpy(float);k-=focal.notna().to_numpy(float)
    if (k<0).any() or (s< -1e-10).any() or (s-k>1e-10).any():
        raise ValueError("HOLD_FOCAL_EXCLUSION")
    prior=(s+TRAINER_SHRINK*g)/(k+TRAINER_SHRINK)
    t["base_own_trainer"]=(n*p+OWN_SHRINK*prior)/(n+OWN_SHRINK)
    t["own_prior_count"]=n.astype(int)
    t["prior_trainer_peers"]=k.astype(int)
    return t

def summarize_target(t):
    return {"horses":len(t),"sires":int(t.sire_id.nunique()),"starts":int(t.starts.sum()),
        "turf_only":int(t.occupancy.eq(1).sum()),"dirt_only":int(t.occupancy.eq(0).sum()),
        "both":int(t.occupancy.between(0,1,inclusive="neither").sum()),
        "no_eligible_A_history":int(t.own_prior_count.eq(0).sum()),
        "with_prior_trainer_peers":int(t.prior_trainer_peers.gt(0).sum())}

def validate_fold(train,target,year,seed,model):
    t=target.loc[target.year.eq(year)].copy()
    if len(t)<MIN_HORSES:
        return {"status":"HOLD_FEW_HORSES","target_horses":len(t)}
    p=train[["horse","sire_id","year","half"]].copy()
    p["difference"]=train.occupancy-train[model]
    q=t[["horse","sire_id","year","half"]].copy()
    q["difference"]=t.occupancy-t[model]
    # Concatenate only the current target year, never a previous B target.
    return evaluate(pd.concat([p,q],ignore_index=True),year,seed)

def analyze(archive,db):
    raw,old,future,_,gate,_=load_sources(archive,db)
    if len(old)!=2092836 or old.horse.nunique()!=90962 or len(future)!=255484 or future.horse.nunique()!=12919:
        raise ValueError("HOLD_SOURCE_COHORT_PARITY")
    circuit,cqa=audit_circuits(raw,old,db,gate["two_event_anchor_horses"])
    mask,sqa=strict_mask_exact_horse_race(raw,future,db,gate["two_event_anchor_horses"])
    strict=future.loc[mask].copy()
    if len(strict)!=244147 or strict.horse.nunique()!=12887:
        raise ValueError("HOLD_STRICT_PARITY")
    out={}
    for seed in SEEDS:
        train=historical_panel(old,seed,False)
        if seed==SEEDS[0]:
            check=evaluate_exposure(train,seed,"base_own")["2021"]["all_targets"]
            if abs(check["contrasts"]["M0_minus_M1"]["MSE_gain"]-.01471092236633107)>1e-10:
                raise ValueError("HOLD_PR81_SCORE_PARITY")
        out[str(seed)]={}
        for name,f in (("all_source_B_valid",future),("strict_classified",strict)):
            t,qa=target_occupancy(f,circuit)
            if t.empty:
                out[str(seed)][name]={"status":"HOLD_NO_VERIFIED_JRA_TARGET","scope":qa}
                continue
            t=source_a_baseline(old,t,seed)
            out[str(seed)][name]={"scope":qa,"years":{}}
            for year in TEST:
                a=t.loc[t.year.eq(year)]
                out[str(seed)][name]["years"][str(year)]={"target_support":summarize_target(a),
                    "own_history":validate_fold(train,t,year,seed,"base_own"),
                    "own_last_trainer":validate_fold(train,t,year,seed,"base_own_trainer")}
    return {"status":"RETROSPECTIVE_SECOND_SOURCE_CONTEXT_OCCUPANCY",
            "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,
            "circuit_gate":cqa,"strict_source_gate":sqa,
            "primary":"20261124/strict_classified/2022/own_history/all_targets/M0_minus_M1",
            "results":out,
            "limitations":["Source B outcomes from 2022–24 were previously used for other research; new endpoint but not pristine independent or prospective holdout.",
                "Anchored continuing horses only, no new entrants or official studbook certification.",
                "Place-code mapping from pre-2022 corroborated events, not official course registry; unknown/conflicting codes excluded.",
                "Strict race filter requires classified finishers; observed eligible turf fraction conditional on source inclusion, not all intended starts.",
                "No source B post-2021 labels or metadata other than eligibility/current year and known identity enter historical model features.",
                "Same source A profiles and fixed shrinkage as PR81; not a replication of PR82 strong learned entry model.",
                "Separate sire bootstrap is conditional pointwise; no all-dependence or genetic causal inference.",
                "No raw identifiers, individual records, market or betting results exported."]}

def self_test():
    evidence=[("A","r1","2019-01-01","JRA"),("A","r2","2019-01-02","JRA"),
              ("B","r3","2019-01-01","NAR"),("B","r4","2019-01-02","JRA"),
              ("C","r5","2019-01-01","NAR"),("C","r5","2019-01-01","NAR")]
    m,qa=make_circuit_map(evidence,2,2)
    assert m=={"A":"JRA"} and qa["conflicting_codes"]==1 and qa["low_support_codes"]==1
    h=pd.DataFrame({"horse":["a","b","c"],"sire_id":["s","s","z"],"trainer_id":["T","T","U"],
        "year":[2021]*3,"day":pd.to_datetime(["2021-01-01"]*3),"race":["r1","r2","r3"],
        "surface":["turf","dirt","turf"],"circuit":["JRA"]*3,"stratum":["turf:4","dirt:4","turf:4"]})
    # Deterministically find a seed with both halves represented.
    seed=next(s for s in range(100) if len(set(_hash_half(h.horse,s,"horse")))==2)
    target=pd.DataFrame({"horse":["a","b"],"sire_id":["s","s"],"year":[2022,2022],"occupancy":[0.,1.],"starts":[1,1]})
    x=source_a_baseline(h,target,seed)
    y=source_a_baseline(h,target.assign(occupancy=1-target.occupancy),seed)
    assert np.allclose(x[["base_own","base_own_trainer"]],y[["base_own","base_own_trainer"]])
    assert (x.own_prior_count==1).all()
    print("synthetic pre-year venue gate, duplicate evidence and held-label invariance passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--sqlite",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if not all((a.archive,a.sqlite,a.output)):
        p.error("archive, sqlite and output required")
    z=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    compact={}
    for seed,scopes in z["results"].items():
        compact[seed]={}
        for scope,v in scopes.items():
            compact[seed][scope]={"scope":v.get("scope"),"status":v.get("status"),"years":{}}
            for y,q in v.get("years",{}).items():
                compact[seed][scope]["years"][y]={"target_support":q["target_support"]}
                for k in ("own_history","own_last_trainer"):
                    r=q[k]
                    compact[seed][scope]["years"][y][k]={key:r[key] for key in ("status","target_horses","total_targets","supported_targets","matched_targets","all_targets","matched_targets_scores") if key in r}
    print(json.dumps({"status":z["status"],"primary":z["primary"],"circuit_gate":z["circuit_gate"],"strict_source_gate":z["strict_source_gate"],"results":compact},allow_nan=False))

if __name__=="__main__":
    main()
