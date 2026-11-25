#!/usr/bin/env python3
"""Synthetic-only 2027 seasonal allocation freeze/score kernel.

Private prepared registry, model components and candidate race census.
NOT a source adapter, historical fitter, real attestation or licensed data
collector. Production entrypoints intentionally unavailable. Test fixtures
must use fictional IDs. No individual records are returned by score.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import random
import re

JST=timezone(timedelta(hours=9))
START=datetime(2027,1,1,tzinfo=JST)
END=datetime(2027,3,28,tzinfo=JST)
SEEDS=(20261124,20261125,20261126)
MODELS=("N","F","P","H","G")
BINS=("0","1-3","4-7","8+")
DRAWS=999
MIN_HORSES=100
MIN_SIRES=30
SCHEMA="FICTIONAL_JRA_2027_CONTEXT_ALLOCATION_V1"
STATES={"KNOWN","UNKNOWN","CONFLICT","UNRESOLVED"}
HISTORY_STATES={"OBSERVED_HISTORY","NO_OBSERVED_HISTORY","VERIFIED_UNRACED"}
REG_FIELDS={"horse","sire_state","sire","prior_n","history_state","registry_known_at","parent_known_at"}
COMP_FIELDS={"horse","seed","N","d","peer_n","known_at"}
RACE_FIELDS={"race","start_at","surface","distance","circuit","declared_entries"}
ENTRY_FIELDS={"race","horse","status"}
RESULT_FIELDS={"race","horse","rank","known_at"}

def require(ok,reason):
    if not ok:
        raise ValueError("HOLD_"+reason)

def fields(x,expected):
    require(type(x) is dict and set(x)==expected,"SCHEMA")

def time(x):
    try:
        t=datetime.fromisoformat(x)
    except (ValueError,TypeError):
        raise ValueError("HOLD_TIMESTAMP") from None
    require(t.tzinfo is not None and t.utcoffset()==timedelta(hours=9),"TIMEZONE")
    return t

def number(x):
    require(type(x) in (int,float) and math.isfinite(x),"NUMERIC")
    return float(x)

def count(x,minimum=0):
    require(type(x) is int and x>=minimum,"COUNT")
    return x

def fid(x,prefix):
    # Intentional hard gate: real source IDs cannot be ingested by this kernel.
    require(type(x) is str and re.fullmatch(prefix+r":FICTIONAL_[A-Za-z0-9_-]+",x) is not None,"SYNTHETIC_ID_ONLY")
    return x

def digest(x):
    return hashlib.sha256((json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n").encode()).hexdigest()

def half(h,seed):
    return hashlib.sha256(f"{seed}|horse|{h}".encode()).digest()[0]&1

def bin_index(n):
    return sum(n>=k for k in (1,4,8))

def keyed(rows,keys,expected):
    d={}
    for row in rows:
        fields(row,expected)
        k=tuple(row[v] for v in keys)
        require(k not in d,"DUPLICATE_KEY")
        d[k]=row
    return d

def validate_registry(reg,cutoff):
    out={}
    for (h,),r in keyed(reg,("horse",),REG_FIELDS).items():
        fid(h,"H")
        state=r["sire_state"];require(state in STATES,"SIRE_STATE")
        n=count(r["prior_n"])
        hist=r["history_state"];require(hist in HISTORY_STATES,"HISTORY_STATE")
        # Positive eligible history contradicts no-history and verified-unraced.
        require(not(n>0 and hist!="OBSERVED_HISTORY"),"HISTORY_CONTRADICTION")
        require(time(r["registry_known_at"])<cutoff,"LATE_REGISTRY")
        if state=="KNOWN":
            fid(r["sire"],"H")
            require(r["sire"]!=h,"SELF_PARENT")
            require(time(r["parent_known_at"])<cutoff,"LATE_PARENT")
        else:
            require(r["sire"]=="","UNKNOWN_SHARED_PARENT")
            if r["parent_known_at"]!="":
                require(time(r["parent_known_at"])<cutoff,"LATE_PARENT_STATE")
        out[h]=r
    require(bool(out),"EMPTY_UNIVERSE")
    return out

def validate_weights(weights):
    require(type(weights) is dict and set(weights)==set(map(str,SEEDS)),"SEEDS")
    for seed,g in weights.items():
        require(type(g) is dict and set(g)=={"0","1"},"HALVES")
        for w in g.values():
            fields(w,{"monotone","pooled","support"})
            a=w["monotone"]
            require(type(a) is list and len(a)==4,"WEIGHT_SHAPE")
            a=list(map(number,a));p=number(w["pooled"])
            require(all(0<=x<=1 for x in [p,*a]) and all(x>=y for x,y in zip(a,a[1:])),"WEIGHT_BOUNDS")
            require(type(w["support"]) is list and len(w["support"])==4,"CALIBRATION_SUPPORT")
            for b in w["support"]:
                fields(b,{"informative_horses","informative_sires"})
                require(count(b["informative_horses"])>=MIN_HORSES and count(b["informative_sires"])>=MIN_SIRES and b["informative_sires"]<=b["informative_horses"],"CALIBRATION_SUPPORT")

def freeze(registry,components,weights,*,cutoff_jst,frozen_at_jst):
    """Fictional offline rehearsal; supplied components not independently fitted.

    Exact whole-universe cross-product across seeds. Private bundle never
    published. Public rehearsal receipt contains counts/digests only.
    """
    cutoff=time(cutoff_jst);frozen=time(frozen_at_jst)
    require(cutoff<=frozen<START,"PREWINDOW_TIME")
    r=validate_registry(registry,cutoff)
    validate_weights(weights)
    c=keyed(components,("horse","seed"),COMP_FIELDS)
    require(set(c)=={(h,s) for h in r for s in SEEDS},"PREDICTION_UNIVERSE")
    pred=[]
    for (h,s),row in sorted(c.items()):
        require(type(s) is int and s in SEEDS,"SEED")
        require(time(row["known_at"])<cutoff,"LATE_COMPONENT")
        n=number(row["N"]);d=number(row["d"]);peers=count(row["peer_n"])
        g=r[h];supported=g["sire_state"]=="KNOWN" and peers>=3
        if not supported:
            require(d==0,"UNSUPPORTED_NONZERO_CORRECTION")
        if g["sire_state"]!="KNOWN":
            require(peers==0,"UNKNOWN_PARENT_PEERS")
        w=weights[str(s)][str(half(h,s))]
        k=bin_index(g["prior_n"])
        # Same linear, unclipped scoring family as PR87/93.
        pred.append({"horse":h,"seed":s,"N":n,"F":n+d,"P":n+w["pooled"]*d,
                     "H":n+(d if k==0 else 0),"G":n+w["monotone"][k]*d})
    private={"schema":SCHEMA,"cutoff_jst":cutoff_jst,"frozen_at_jst":frozen_at_jst,
             "registry":registry,"components":components,"weights":weights,"predictions":pred}
    receipt={"schema":SCHEMA,"status":"SYNTHETIC_ONLY_UNATTESTED",
             "private_bundle_sha256":digest(private),"registry_sha256":digest(registry),
             "components_sha256":digest(components),"weights_sha256":digest(weights),
             "predictions_sha256":digest(pred),"horses":len(r),"prediction_rows":len(pred),
             "known_sire_horses":sum(x["sire_state"]=="KNOWN" for x in r.values()),
             "zero_observed_eligible_history_horses":sum(x["prior_n"]==0 for x in r.values()),
             "verified_unraced_horses":sum(x["history_state"]=="VERIFIED_UNRACED" for x in r.values()),
             "external_attestation_verified":False,"real_observations":0}
    return private,receipt

def verify(private,receipt):
    fields(private,{"schema","cutoff_jst","frozen_at_jst","registry","components","weights","predictions"})
    require(private["schema"]==SCHEMA,"PRIVATE_SCHEMA")
    rebuilt,public=freeze(private["registry"],private["components"],private["weights"],
                          cutoff_jst=private["cutoff_jst"],frozen_at_jst=private["frozen_at_jst"])
    require(rebuilt==private and public==receipt,"COMMITMENT_MISMATCH")
    return validate_registry(private["registry"],time(private["cutoff_jst"]))

def interval(rows,loss,seed):
    # Cluster unknown/unresolved/conflicting sire as unique horse singletons.
    # A separate >=30 KNOWN sire gate applies, not 30 arbitrary singletons.
    n=len(rows)
    known={r["sire"] for r in rows if r["sire_state"]=="KNOWN"}
    if not n:
        return {"status":"HOLD_EMPTY","horses":0,"known_sires":0}
    sums=defaultdict(lambda:[0.,0])
    for r,v in zip(rows,loss):
        k=("sire",r["sire"]) if r["sire_state"]=="KNOWN" else ("singleton",r["horse"])
        sums[k][0]+=v;sums[k][1]+=1
    point=sum(loss)/n
    z={"status":"DESCRIPTIVE","MSE_gain":point,"horses":n,"known_sires":len(known),"clusters":len(sums)}
    if n<MIN_HORSES or len(known)<MIN_SIRES:
        z["status"]="HOLD_LOW_SUPPORT";return z
    a=list(sums.values());rng=random.Random(seed);draw=[]
    for _ in range(DRAWS):
        s=0.;k=0
        for _ in a:
            u,v=a[rng.randrange(len(a))];s+=u;k+=v
        draw.append(s/k)
    draw.sort()
    def quantile(q):
        i=q*(len(draw)-1);lo=int(i);return draw[lo]+(i-lo)*(draw[min(lo+1,len(draw)-1)]-draw[lo])
    z["CI95_pointwise"]=[quantile(.025),quantile(.975)]
    return z

def score_group(rows,seed):
    if not rows:
        return {"status":"HOLD_EMPTY","horses":0}
    loss={k:[(r["occupancy"]-r[k])**2 for r in rows] for k in MODELS}
    contrasts={}
    for a,b in (("N","F"),("N","P"),("N","H"),("N","G"),("F","G"),("P","G"),("H","G")):
        contrasts[a+"_minus_"+b]=interval(rows,[u-v for u,v in zip(loss[a],loss[b])],seed)
    return {"horses":len(rows),"known_sire_horses":sum(r["sire_state"]=="KNOWN" for r in rows),
            "RMSE":{k:math.sqrt(sum(v)/len(v)) for k,v in loss.items()},"contrasts":contrasts}

def score(private,receipt,races,entries,results,*,scored_at_jst):
    """Post-window fictional census score; no production attestation.
    
    Race list is supplied, not externally certified exhaustive. Only strict
    races with exact full declared entries, resolved starter status and
    finalized consecutive rank list are scored. Missing races/rows never
    filled in; retain no-observation and partial-coverage counts.
    """
    reg=verify(private,receipt)
    clock=time(scored_at_jst);require(clock>=END,"PREWINDOW_SCORE")
    race=keyed(races,("race",),RACE_FIELDS)
    en=keyed(entries,("race","horse"),ENTRY_FIELDS)
    res=keyed(results,("race","horse"),RESULT_FIELDS)
    require(all((k[0],) in race for k in en),"ENTRY_UNKNOWN_RACE")
    require(set(res)<=set(en),"RESULT_UNKNOWN_ENTRY")
    by_e=defaultdict(list);by_r=defaultdict(list)
    for (rid,h),x in en.items():
        fid(rid,"R");fid(h,"H")
        require(x["status"] in {"STARTED","WITHDRAWN","UNRESOLVED"},"ENTRY_STATUS")
        by_e[rid].append(x)
    for (rid,h),x in res.items():
        require(en[(rid,h)]["status"]=="STARTED","RESULT_NOT_STARTER")
        count(x["rank"],1)
        require(time(race[(rid,)]["start_at"])<=time(x["known_at"])<=clock,"RESULT_TIME")
        by_r[rid].append(x)
    states=Counter();obs=defaultdict(list);seen=Counter();outside=set();candidate_starts=0
    for (rid,),r in race.items():
        fid(rid,"R")
        start=time(r["start_at"])
        require(START<=start<END and r["circuit"]=="JRA" and r["surface"] in {"turf","dirt"}
                and 1600<=count(r["distance"])<=1999,"RACE_SCOPE")
        declared=count(r["declared_entries"],2);require(declared<=30,"RACE_ENTRY_COUNT")
        e=by_e[rid];a=by_r[rid]
        require(len(e)<=declared,"EXCESS_ENTRIES")
        starters={x["horse"] for x in e if x["status"]=="STARTED"}
        candidate_starts+=len(starters)
        for x in e:
            h=x["horse"]
            if h not in reg:
                outside.add(h)
            elif x["status"]!="WITHDRAWN":
                seen[h]+=1
        good=(len(e)==declared and all(x["status"]!="UNRESOLVED" for x in e)
              and len(starters)>=2 and {x["horse"] for x in a}==starters
              and sorted(x["rank"] for x in a)==list(range(1,len(starters)+1)))
        if not good:
            states["INCOMPLETE_OR_UNCLASSIFIED"]+=1;continue
        states["STRICT_COMPLETE"]+=1
        for h in starters:
            if h in reg:
                obs[h].append(int(r["surface"]=="turf"))
    covered={h for h in obs if obs[h]}
    q={"frozen_horses":len(reg),"candidate_races":len(race),"race_status":dict(states),
       "candidate_observed_starts":candidate_starts,"outside_universe_observed_horses":len(outside),
       "strict_observed_horses":len(covered),"strict_observed_starts":sum(map(len,obs.values())),
       "observed_but_no_strict_start_horses":len(set(seen)-covered),
       "strict_with_additional_unresolved_observations_horses":sum(seen[h]>len(obs[h]) for h in covered),
       "no_observed_candidate_start_horses":len(set(reg)-set(seen)),
       "official_race_census_completeness_verified":False}
    require(q["strict_observed_horses"]+q["observed_but_no_strict_start_horses"]+q["no_observed_candidate_start_horses"]==len(reg),"COVERAGE_IDENTITY")
    out={}
    for seed in SEEDS:
        rows=[]
        for p in private["predictions"]:
            h=p["horse"]
            if p["seed"]==seed and h in covered:
                rows.append({**reg[h],**p,"occupancy":sum(obs[h])/len(obs[h])})
        groups={"all":rows,"known_sire":[x for x in rows if x["sire_state"]=="KNOWN"],
                "unknown_or_unresolved_sire":[x for x in rows if x["sire_state"]!="KNOWN"],
                "verified_unraced":[x for x in rows if x["history_state"]=="VERIFIED_UNRACED"]}
        groups.update({label:[x for x in rows if bin_index(x["prior_n"])==j] for j,label in enumerate(BINS)})
        out[str(seed)]={k:score_group(v,seed) for k,v in groups.items()}
    return {"schema":SCHEMA,"status":"SYNTHETIC_ONLY_CONDITIONAL_STRICT_SCORE",
            "real_observations":0,"external_attestation_verified":False,
            "coverage":q,"results":out}
