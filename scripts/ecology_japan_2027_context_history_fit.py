#!/usr/bin/env python3
"""Fictional-only chronological seasonal family-history fitter.

Accepts synthetic, already audited classified eligible start records and
dated synthetic sire observations. No raw official data, real fitting,
license verification, or external timestamp attestation. Full prior-year
history and Jan1-Mar27 donor labels; calibration never uses 2025/26 labels.
"""
from collections import defaultdict
from datetime import datetime
import math
from ecology_japan_2027_context_allocation_kernel import (
    JST, START, SEEDS, BINS, MIN_HORSES, MIN_SIRES, STATES,
    require, fields, time, fid, count, number, digest, half, bin_index,
    keyed, validate_registry, freeze, score_group,
)

HISTORY_FIELDS={"race","horse","start_at","known_at","surface","distance","circuit"}
PARENT_FIELDS={"horse","sire_state","sire","known_at"}
DONOR_YEARS=tuple(range(2018,2027))
CAL_YEARS=tuple(range(2019,2025))
VAL_YEARS=(2025,2026)
OWN_SHRINK=5.
FAMILY_SHRINK=8.
MIN_PEERS=3

def jan(y):
    return datetime(y,1,1,tzinfo=JST)

def in_season(day):
    return (day.month,day.day)<=(3,27)

def avg(v):
    require(bool(v),"EMPTY_MEAN")
    return sum(v)/len(v)

def validate(history,parents,registry,cutoff):
    reg=validate_registry(registry,cutoff)
    pm={}
    for (h,),p in keyed(parents,("horse",),PARENT_FIELDS).items():
        fid(h,"H")
        require(p["sire_state"] in STATES,"PARENT_STATE")
        require(time(p["known_at"])<cutoff,"LATE_PARENT_HISTORY")
        if p["sire_state"]=="KNOWN":
            fid(p["sire"],"H")
            require(p["sire"]!=h,"SELF_PARENT")
        else:
            require(p["sire"]=="","UNKNOWN_SHARED_PARENT")
        pm[h]=(p["sire_state"],p["sire"],time(p["known_at"]))
    # A frozen registry's stated parent must agree with the dated historical
    # parent map if that horse is in the latter. No name joins or imputation.
    for h,q in reg.items():
        if h in pm:
            a,b,k=pm[h]
            require((a,b)==(q["sire_state"],q["sire"]),"PARENT_MAP_CONFLICT")
    hist=[];race={}
    for (rid,h),x in keyed(history,("race","horse"),HISTORY_FIELDS).items():
        fid(rid,"R");fid(h,"H")
        day=time(x["start_at"]);known=time(x["known_at"])
        require(jan(2010)<=day<=known<cutoff<START,"HISTORY_TIME")
        require(x["circuit"]=="JRA" and x["surface"] in {"turf","dirt"} and 1600<=count(x["distance"])<=1999,"HISTORY_SCOPE")
        require(h in pm,"MISSING_HISTORICAL_PARENT_STATE")
        k=(day,x["surface"],x["distance"])
        require(rid not in race or race[rid]==k,"RACE_METADATA")
        race[rid]=k
        hist.append((h,day,known,int(x["surface"]=="turf")))
    require(bool(hist),"EMPTY_HISTORY")
    return hist,pm,reg

def known_sire(pm,h,cutoff):
    p=pm.get(h)
    return p[1] if p and p[0]=="KNOWN" and p[2]<cutoff else ""

def own_history(hist,cutoff,year,seed,pm):
    """Full previous calendar years, only records known strictly by cutoff."""
    sums=defaultdict(lambda:[0,0])
    for h,day,known,t in hist:
        if day.year<year and known<cutoff:
            sums[h][0]+=t;sums[h][1]+=1
    global_by_half={0:[],1:[]}
    for h,(s,n) in sums.items():
        # Same known-sire reference population as historical PR93.
        # Focal unknown-sire horses still get their own recorded history.
        if known_sire(pm,h,cutoff):
            global_by_half[half(h,seed)].append(s/n)
    means={k:avg(v) for k,v in global_by_half.items()}
    return sums,means

def own_base(sums,means,h,seed):
    s,n=sums.get(h,(0,0))
    return (s+OWN_SHRINK*means[half(h,seed)])/(n+OWN_SHRINK),n

def donor_profile(panel,year,target_half):
    # Average each donor horse's prior annual residuals before sire means.
    # Same target horse cannot be in opposite half by construction.
    hh=defaultdict(list);ps={}
    for p in panel:
        if p["year"]<year and p["half"]!=target_half:
            h=p["horse"];s=p["sire"]
            require(h not in ps or ps[h]==s,"DONOR_PARENT_CONFLICT")
            ps[h]=s;hh[h].append(p["residual"])
    require(bool(hh),"EMPTY_DONOR_POOL")
    vals={h:avg(v) for h,v in hh.items()}
    global_mean=avg(list(vals.values()))
    by=defaultdict(list)
    for h,v in vals.items():
        by[ps[h]].append(v)
    return global_mean,{s:(avg(v),len(v)) for s,v in by.items()}

def correction(profile,sire):
    m,by=profile
    q,n=by.get(sire,(m,0))
    d=n/(n+FAMILY_SHRINK)*(q-m) if n>=MIN_PEERS else 0.
    return m,d,n

def make_panel(hist,pm,seed,freeze_cutoff):
    panel=[]
    for year in DONOR_YEARS:
        asof=jan(year)
        require(asof<freeze_cutoff,"CALENDAR_HISTORY")
        sums,means=own_history(hist,asof,year,seed,pm)
        labels=defaultdict(list)
        for h,day,known,t in hist:
            if day.year!=year or not in_season(day):
                continue
            # Late labels cannot enter the next year's donor fit; hold
            # rather than silently change the prepared historical endpoint.
            require(known<min(jan(year+1),freeze_cutoff),"LATE_SEASON_LABEL")
            if known_sire(pm,h,asof):
                labels[h].append(t)
        require(bool(labels),"EMPTY_DONOR_YEAR")
        profiles={k:donor_profile(panel,year,k) for k in (0,1)} if year>DONOR_YEARS[0] else {}
        for h,ts in sorted(labels.items()):
            b,n=own_base(sums,means,h,seed);y=avg(ts);k=half(h,seed)
            row={"horse":h,"sire":known_sire(pm,h,asof),"year":year,
                 "half":k,"prior_n":n,"occupancy":y,"residual":y-b}
            if profiles:
                m,d,np=correction(profiles[k],row["sire"])
                row.update(N=b+m,d=d,peer_n=np,r=y-b-m)
            panel.append(row)
    return panel

def decreasing_projection(num,den):
    require(len(num)==len(den)==4 and all(v>1e-12 for v in den),"WEIGHT_INFORMATION")
    blocks=[]
    for j,(a,b) in enumerate(zip(num,den)):
        blocks.append([j,j,a,b])
        while len(blocks)>1 and blocks[-2][2]/blocks[-2][3]<blocks[-1][2]/blocks[-1][3]:
            y=blocks.pop();x=blocks.pop()
            blocks.append([x[0],y[1],x[2]+y[2],x[3]+y[3]])
    w=[0.]*4
    for lo,hi,a,b in blocks:
        for j in range(lo,hi+1):
            w[j]=max(0.,min(1.,a/b))
    return w

def calibrate(panel,eval_half):
    rows=[p for p in panel if p["year"] in CAL_YEARS and p["half"]!=eval_half]
    require(bool(rows),"EMPTY_CALIBRATION")
    freq=defaultdict(int)
    for x in rows:freq[x["horse"]]+=1
    num=[];den=[];support=[]
    for j in range(4):
        g=[x for x in rows if bin_index(x["prior_n"])==j]
        active=[x for x in g if abs(x["d"])>1e-12]
        h=len({x["horse"] for x in active});s=len({x["sire"] for x in active})
        require(h>=MIN_HORSES and s>=MIN_SIRES,"CALIBRATION_BIN_SUPPORT")
        num.append(sum(x["d"]*x["r"]/freq[x["horse"]] for x in g))
        den.append(sum(x["d"]**2/freq[x["horse"]] for x in g))
        support.append({"informative_horses":h,"informative_sires":s})
    return {"monotone":decreasing_projection(num,den),
            "pooled":max(0.,min(1.,sum(num)/sum(den))),"support":support}

def validation(panel,weights,seed):
    out={}
    for year in VAL_YEARS:
        rows=[]
        for p in panel:
            if p["year"]!=year:continue
            w=weights[str(p["half"])];k=bin_index(p["prior_n"]);n=p["N"];d=p["d"]
            rows.append({"horse":p["horse"],"sire":p["sire"],"sire_state":"KNOWN",
                         "occupancy":p["occupancy"],"N":n,"F":n+d,
                         "P":n+w["pooled"]*d,"H":n+(d if k==0 else 0),
                         "G":n+w["monotone"][k]*d})
        out[str(year)]=score_group(rows,seed)
    return out

def fit(history,parents,registry,*,cutoff_jst,frozen_at_jst):
    """Return fictional private freeze bundle, public hash and QA summary.

    Prepared historical records are not source-certified by this function.
    No production path, no real identifiers. Last prior year may be partial
    at freeze; use records actually supplied before cutoff, never fill gaps.
    """
    cutoff=time(cutoff_jst)
    require(jan(2026)<cutoff<START,"FIT_CUTOFF")
    hist,pm,reg=validate(history,parents,registry,cutoff)
    weights={};components=[];qa={}
    # Known-at is latest supplied input availability; not model-build or
    # externally certified publication time.
    known=max([z[2] for z in hist]+[p[2] for p in pm.values()]+
        [time(q["registry_known_at"]) for q in reg.values()]+
        [time(q["parent_known_at"]) for q in reg.values() if q["parent_known_at"]])
    for seed in SEEDS:
        panel=make_panel(hist,pm,seed,cutoff)
        w={str(k):calibrate(panel,k) for k in (0,1)}
        weights[str(seed)]=w
        qa[str(seed)]={"calibration_years":list(CAL_YEARS),"donor_years":list(DONOR_YEARS),
            "seasonal_donor_rows":len(panel),"validation":validation(panel,w,seed)}
        sums,means=own_history(hist,cutoff,2027,seed,pm)
        profiles={k:donor_profile(panel,2027,k) for k in (0,1)}
        for h,g in sorted(reg.items()):
            b,n=own_base(sums,means,h,seed)
            require(n==g["prior_n"],"REGISTRY_HISTORY_COUNT_MISMATCH")
            m,d,npeer=correction(profiles[half(h,seed)],g["sire"] if g["sire_state"]=="KNOWN" else "")
            components.append({"horse":h,"seed":seed,"N":b+m,"d":d,
                               "peer_n":npeer,"known_at":known.isoformat()})
    private,receipt=freeze(registry,components,weights,cutoff_jst=cutoff_jst,frozen_at_jst=frozen_at_jst)
    # Bind exact prepared inputs to the synthetic fitting receipt. This is
    # a local hash, not a server proof. Private input bytes remain private.
    out={"status":"SYNTHETIC_ONLY_FITTED_REHEARSAL","real_observations":0,
         "history_sha256":digest(history),"parents_sha256":digest(parents),
         "freeze_receipt":receipt,"calibration_years":list(CAL_YEARS),
         "validation_years":list(VAL_YEARS),"results":qa}
    return private,receipt,out
