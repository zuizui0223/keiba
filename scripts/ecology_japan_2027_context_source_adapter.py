#!/usr/bin/env python3
"""Fictional normalized source adapter for pre-window seasonal allocation.

Transforms complete observed race/entry/result lists and dated registry/
parent snapshots into the existing historical fitter's prepared schema.
No provider DB reader, permission check, authentic timestamp, or claim of
source census completeness. Actual H:/B: registration identifiers rejected.
"""
from collections import Counter, defaultdict
from ecology_japan_2027_context_allocation_kernel import (
    START, STATES, require, fields, time, fid, count, digest, keyed,
)
from ecology_japan_2027_context_history_fit import fit, jan

REG={"horse","known_at","unraced_status","unraced_known_at"}
PARENT={"horse","sire_state","sire","known_at"}
RACE={"race","start_at","known_at","surface","distance","circuit","declared_entries"}
ENTRY={"race","horse","status","known_at"}
RESULT={"race","horse","status","rank","known_at"}
SCHEMA="FICTIONAL_NORMALIZED_CONTEXT_SOURCE_V1"

def prepare(registry,parents,races,entries,results,*,captured_at_jst,cutoff_jst):
    cap=time(captured_at_jst);cutoff=time(cutoff_jst)
    require(cap<cutoff<START,"CAPTURE_TIME")
    reg=keyed(registry,("horse",),REG)
    require(bool(reg),"EMPTY_REGISTRY")
    # Multiple identical state observations can certify an earlier first
    # known time. Revisions changing state or ID must HOLD until versioned
    # historical fitter exists. Never resolve conflicts with later labels.
    pm={}
    for x in parents:
        fields(x,PARENT)
        h=fid(x["horse"],"H");s=x["sire"];state=x["sire_state"];k=time(x["known_at"])
        require(k<=cap,"FUTURE_PARENT")
        require(state in STATES,"PARENT_STATE")
        if state=="KNOWN":
            fid(s,"H");require(h!=s,"SELF_PARENT")
        else:require(s=="","UNKNOWN_SHARED_PARENT")
        old=pm.get(h)
        if old:
            require((state,s)==old[:2],"VERSIONED_PARENT_CHANGE_UNSUPPORTED")
            k=min(k,old[2])
        pm[h]=(state,s,k)
    rs=keyed(races,("race",),RACE)
    es=keyed(entries,("race","horse"),ENTRY)
    ys=keyed(results,("race","horse"),RESULT)
    require(all((rid,) in rs for rid,h in es),"ENTRY_UNKNOWN_RACE")
    require(set(ys)<=set(es),"RESULT_UNKNOWN_ENTRY")
    ee=defaultdict(list);yy=defaultdict(list)
    observed_started=set()
    for (rid,h),x in es.items():
        fid(rid,"R");fid(h,"H")
        k=time(x["known_at"]);day=time(rs[(rid,)]["start_at"])
        require(k<=cap,"FUTURE_ENTRY")
        require(x["status"] in {"STARTED","WITHDRAWN","UNRESOLVED"},"ENTRY_STATE")
        if x["status"]=="STARTED":
            require(day<=k,"START_NOT_YET_OBSERVED")
            observed_started.add(h)
        ee[rid].append(x)
    for (rid,h),x in ys.items():
        require(es[(rid,h)]["status"]=="STARTED","RESULT_NOT_STARTER")
        require(time(rs[(rid,)]["start_at"])<=time(x["known_at"])<=cap,"RESULT_TIME")
        require(x["status"] in {"CLASSIFIED","UNCLASSIFIED"},"RESULT_STATE")
        rank=count(x["rank"])
        require((x["status"]=="CLASSIFIED" and rank>=1) or
                (x["status"]=="UNCLASSIFIED" and rank==0),"RESULT_RANK_STATE")
        yy[rid].append(x)
    history=[];status=Counter();scope=Counter();own=Counter();observed_eligible=set()
    for (rid,),x in sorted(rs.items()):
        fid(rid,"R");day=time(x["start_at"]);header=time(x["known_at"])
        require(jan(2010)<=day<=cap and header<=cap,"RACE_TIME")
        require(x["circuit"] in {"JRA","NAR","OTHER"} and
                x["surface"] in {"turf","dirt","other"},"RACE_SCOPE")
        dist=count(x["distance"],1);n=count(x["declared_entries"],2)
        require(n<=30,"DECLARED_COUNT")
        e=ee[rid];y=yy[rid]
        require(len(e)<=n,"EXCESS_ENTRIES")
        if x["circuit"]!="JRA" or x["surface"] not in {"turf","dirt"} or not 1600<=dist<=1999:
            scope["outside_eligible_scope"]+=1;continue
        scope["eligible_candidate_races"]+=1
        starters={v["horse"] for v in e if v["status"]=="STARTED"}
        observed_eligible.update(starters)
        good=len(e)==n and all(v["status"]!="UNRESOLVED" for v in e) and len(starters)>=2
        good=good and {v["horse"] for v in y}==starters and all(v["status"]=="CLASSIFIED" for v in y)
        good=good and sorted(v["rank"] for v in y)==list(range(1,len(starters)+1))
        if not good:
            status["INCOMPLETE_OR_UNCLASSIFIED"]+=1;continue
        status["STRICT_COMPLETE"]+=1
        # The strict complete-race predicate itself becomes known only
        # when all its evidence is present. Do not backdate to each result.
        known=max([header,day]+[time(v["known_at"]) for v in e+y])
        for h in sorted(starters):
            require(h in pm,"MISSING_HISTORICAL_PARENT_STATE")
            history.append({"race":rid,"horse":h,"start_at":day.isoformat(),
                "known_at":known.isoformat(),"surface":x["surface"],
                "distance":dist,"circuit":"JRA"})
            own[h]+=1
    require(bool(history),"EMPTY_STRICT_HISTORY")
    prepared_reg=[]
    for (h,),x in sorted(reg.items()):
        fid(h,"H");known=time(x["known_at"])
        require(known<=cap,"FUTURE_REGISTRY")
        require(h in pm,"MISSING_REGISTRY_PARENT_STATE")
        state,s,pk=pm[h]
        unraced=x["unraced_status"]
        require(unraced in {"VERIFIED_UNRACED","NOT_CERTIFIED"},"UNRACED_STATE")
        if unraced=="VERIFIED_UNRACED":
            require(x["unraced_known_at"]!="" and time(x["unraced_known_at"])<=cap,"UNRACED_EVIDENCE_TIME")
            require(h not in observed_started,"UNRACED_CONTRADICTION")
            hs="VERIFIED_UNRACED"
        else:
            require(x["unraced_known_at"]=="","UNEXPECTED_UNRACED_EVIDENCE")
            hs="OBSERVED_HISTORY" if h in observed_started else "NO_OBSERVED_HISTORY"
        prepared_reg.append({"horse":h,"sire_state":state,"sire":s,"prior_n":own[h],
            "history_state":hs,"registry_known_at":known.isoformat(),"parent_known_at":pk.isoformat()})
    prepared_parents=[{"horse":h,"sire_state":v[0],"sire":v[1],"known_at":v[2].isoformat()}
                      for h,v in sorted(pm.items())]
    prepared={"history":history,"parents":prepared_parents,"registry":prepared_reg}
    q={"schema":SCHEMA,"status":"SYNTHETIC_ONLY_SOURCE_ADAPTER",
       "real_observations":0,"external_attestation_verified":False,
       "official_census_completeness_verified":False,"captured_at_jst":captured_at_jst,
       "source_sha256":digest({"registry":registry,"parents":parents,"races":races,
                               "entries":entries,"results":results}),
       "prepared_sha256":digest(prepared),
       "registry_horses":len(prepared_reg),"parent_state_counts":dict(Counter(x["sire_state"] for x in prepared_reg)),
       "history_state_counts":dict(Counter(x["history_state"] for x in prepared_reg)),
       "candidate_races":len(rs),"scope":dict(scope),"eligible_race_status":dict(status),
       "strict_history_starts":len(history),"strict_history_horses":len(own),
       "observed_eligible_starter_horses":len(observed_eligible),
       "registry_horses_with_observed_eligible_start_but_no_strict_history":
           sum(h in observed_eligible and not own[h] for h, in reg),
       "zero_observed_strict_eligible_history_registry_horses":sum(x["prior_n"]==0 for x in prepared_reg)}
    require(sum(status.values())==scope["eligible_candidate_races"],"DENOMINATOR")
    return prepared,q

def adapt_and_fit(registry,parents,races,entries,results,*,captured_at_jst,cutoff_jst,frozen_at_jst):
    x,q=prepare(registry,parents,races,entries,results,captured_at_jst=captured_at_jst,cutoff_jst=cutoff_jst)
    p,f,qa=fit(x["history"],x["parents"],x["registry"],cutoff_jst=cutoff_jst,frozen_at_jst=frozen_at_jst)
    return p,f,{"status":"SYNTHETIC_ONLY_SOURCE_TO_FIT","real_observations":0,
                "adapter":q,"fit":qa}
