#!/usr/bin/env python3
"""One-hop historical opponent evidence after a focal horse's last race.
A pre-day statistical revision, not a physical or causal ability change."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from ecology_japan_daily_ability import (
    SOURCE_SHA,COLS,prepare_frame,prepare,State,process_day,CAL,TEST,
    HALF_LIFE_DAYS,MIN_PAIRS,MIN_DAYS,DRAWS,SEED,weights,
    calibrate as original_calibrate,evaluate as original_evaluate
)

GRID=(0.,.25,.5,.75,1.,1.5,2.)
GROUPS=("first_both_one_start_one_win","first_both_one_win")
SLOPE=2.

def same(a,b,label):
    if not np.allclose(a,b,rtol=0,atol=1e-10):raise ValueError("HOLD_"+label)

def snapshot(st,opponents):
    ids=np.asarray(opponents,dtype=np.int64)
    return (ids.copy(),st.global_rating[ids].copy(),st.starts[ids].copy())

def innovation(st,record,anchor,day):
    ids,base,starts=record
    if len(ids)==0 or not anchor<day or (st.last[ids]<anchor).any() or (st.last[ids]>=day).any():
        raise ValueError("HOLD_OPPONENT_TIME")
    current=st.global_rating[ids]*2.**(-(day-st.last[ids])/HALF_LIFE_DAYS)
    passive=base*2.**(-(day-anchor)/HALF_LIFE_DAYS)
    d=current-passive
    n=st.starts[ids]-starts
    if (n<0).any():raise ValueError("HOLD_OPPONENT_COUNT")
    same(d[n==0],0.,"PASSIVE_DECAY")
    return float(d.mean()),int((n>0).sum()),int(n.sum())

def anchored_features(st,anchors,active,day):
    v=np.zeros(st.n);p=np.zeros(st.n);updated=np.zeros(st.n,dtype=int)
    pupdated=np.zeros(st.n,dtype=int);eligible=np.zeros(st.n,bool)
    matched=np.zeros(st.n,bool);gap=np.zeros(st.n)
    for h in active:
        h=int(h)
        if h not in anchors:continue
        anchor,actual,control,matchgap=anchors[h]
        if anchor!=st.last[h]:raise ValueError("HOLD_FOCAL_LAST_DAY")
        v[h],updated[h],_=innovation(st,actual,anchor,day);eligible[h]=True
        if control is not None:
            p[h],pupdated[h],_=innovation(st,control,anchor,day)
            matched[h]=True;gap[h]=matchgap
    return v,p,updated,pupdated,eligible,matched,gap

def store_anchors(t,st,anchors,day):
    # Only after all same-day outcomes are processed. The control is a different
    # race on the same date/surface/distance band with enough distinct horses.
    # It matches size and post-day mean rating, not subsequent results.
    races=[]
    appearances={}
    for rid,x in t.groupby("race",sort=True,observed=True):
        ids=np.sort(x.id.to_numpy(np.int64))
        surf=str(x.surface.iloc[0]);band=int(x.distance.iloc[0])//400
        if len(ids)<2 or len(np.unique(ids))!=len(ids) or x.surface.nunique()!=1 or x.distance.nunique()!=1:
            raise ValueError("HOLD_ANCHOR_RACE")
        races.append((str(rid),ids,surf,band,float(st.global_rating[ids].mean())))
        for h in ids:appearances.setdefault(int(h),[]).append(ids)
    for h,sets in appearances.items():
        actual=np.unique(np.concatenate(sets));actual=actual[actual!=h]
        if len(actual)==0:raise ValueError("HOLD_NO_ANCHOR_OPPONENTS")
        anchors[h]=(day,snapshot(st,actual),None,0.)
    for rid,ids,surf,band,mu in races:
        n=len(ids)
        candidates=[(abs(len(j)-(n-1)),abs(m-mu),r,j)
            for r,j,s,b,m in races if r!=rid and s==surf and b==band and len(j)>=n-1 and not np.intersect1d(ids,j).size]
        if not candidates:continue
        _,_,_,other=min(candidates,key=lambda z:z[:3])
        for h in ids:
            h=int(h)
            if len(appearances[h])!=1:continue
            actual=anchors[h][1];mu_a=float(actual[1].mean())
            # Deterministic closest post-day rating to real opponent mean;
            # select equal number. The comparison does not require unrelatedness
            # or never having met earlier.
            ix=np.lexsort((other,np.abs(st.global_rating[other]-mu_a)))[:n-1]
            controls=other[ix]
            if len(controls)!=len(actual[0]) or np.intersect1d(controls,ids).size:
                raise ValueError("HOLD_CONTROL_MATCH")
            g=abs(float(st.global_rating[controls].mean())-mu_a)
            anchors[h]=(day,actual,snapshot(st,controls),g)

def mask(t,group):
    q=t.connected&t["first"]
    if group=="first_both_one_win":return q&t.both_one_win
    if group=="first_both_one_start_one_win":return q&t.both_one_start
    if group=="first_meeting":return q
    raise ValueError("HOLD_GROUP")

def calibrate(t,group):
    q=t.loc[mask(t,group)].copy()
    if q.empty or q.key.nunique()<MIN_PAIRS or q.day.nunique()<MIN_DAYS:
        return {"status":"HOLD_CALIBRATION_SUPPORT","pairs":len(q),"days":int(q.day.nunique())}
    w=weights(q);y=q.y.to_numpy(float);g=q.graph.to_numpy(float);v=q.revision.to_numpy(float)
    losses=[float(np.average((y-expit(SLOPE*(g+a*v)))**2,weights=w)) for a in GRID]
    j=min(range(len(GRID)),key=lambda i:(losses[i],GRID[i]))
    return {"status":"CALIBRATED","selected":GRID[j],"grid":list(GRID),"Brier":losses,
        "pairs":len(q),"days":int(q.day.nunique())}

def ci(t,d,w):
    tab=pd.DataFrame({"day":t.day.to_numpy(),"w":w,"d":w*d})
    a=tab.groupby("day",observed=True)[["w","d"]].sum().to_numpy()
    rng=np.random.default_rng(SEED)
    rep=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
    return np.quantile(rep[:,1]/rep[:,0],[.0125,.9875]).tolist()

def score(t,group,cal,matched_only=False):
    q=t.loc[mask(t,group)].copy()
    denominator=len(q)
    if matched_only:q=q.loc[q.control_both]
    if q.empty:return {"status":"HOLD_EMPTY","pairs":0,"denominator":denominator}
    n=int(q.key.nunique());days=int(q.day.nunique())
    supported=n>=MIN_PAIRS and days>=MIN_DAYS
    w=weights(q);y=q.y.to_numpy(float);g=q.graph.to_numpy(float);v=q.revision.to_numpy(float)
    control=q.control_revision.to_numpy(float)
    base=(y-expit(SLOPE*g))**2
    fixed=(y-expit(SLOPE*(g+v)))**2
    r={"status":"OBSERVED" if supported else "HOLD_SUPPORT",
       "pairs":len(q),"denominator":denominator,"distinct_pairs":n,"days":days,"races":int(q.race.nunique()),
       "horses":len(np.unique(np.r_[q.a,q.b])),
       "both_anchor_pairs":int(q.anchor_both.sum()),"either_actual_opponent_updated_pairs":int(q.actual_updated.sum()),
       "control_matched_pairs":int(q.control_both.sum()),"mean_abs_revision_gap":float(np.average(np.abs(v),weights=w)),
       "baseline_Brier":float(np.average(base,weights=w)),
       "fixed_weight_1_gain":float(np.average(base-fixed,weights=w))}
    if matched_only:
        r["mean_abs_control_anchor_rating_mismatch"]=float(np.average(q.matchgap,weights=w))
        r["either_control_opponent_updated_pairs"]=int(q.control_updated.sum())
    if cal["status"]!="CALIBRATED":
        r["calibration_status"]=cal["status"];return r
    a=cal["selected"]
    loss=(y-expit(SLOPE*(g+a*v)))**2;d=base-loss
    r.update(weight=a,corrected_Brier=float(np.average(loss,weights=w)),gain=float(np.average(d,weights=w)))
    if supported:r["conditional_day_97_5_gain"]=ci(q,d,w)
    if matched_only:
        pl=(y-expit(SLOPE*(g+a*control)))**2
        r.update(control_Brier=float(np.average(pl,weights=w)),actual_minus_control_gain=float(np.average(pl-loss,weights=w)))
        if supported:r["conditional_day_97_5_actual_minus_control"]=ci(q,pl-loss,w)
    return r

def replay(t,N):
    st=State(N);anchors={};panels={y:[] for y in (CAL,*TEST)}
    for day,d in t.groupby("day",sort=True,observed=True):
        yr=int(day.year);di=int(day.toordinal());active=np.unique(d.id.to_numpy(np.int64))
        if yr in panels:
            v,p,u,pu,eligible,matched,gap=anchored_features(st,anchors,active,di)
        q=process_day(d,st,yr in panels)
        if q is not None:
            a=q.a.to_numpy(np.int64);b=q.b.to_numpy(np.int64)
            q["revision"]=v[a]-v[b];q["control_revision"]=p[a]-p[b]
            q["anchor_both"]=eligible[a]&eligible[b];q["control_both"]=matched[a]&matched[b]
            q["actual_updated"]=(u[a]+u[b])>0;q["control_updated"]=(pu[a]+pu[b])>0
            q["matchgap"]=(gap[a]+gap[b])/2
            if not q.loc[q.connected,"anchor_both"].all():raise ValueError("HOLD_MISSING_CONNECTED_ANCHOR")
            panels[yr].append(q)
        store_anchors(d,st,anchors,di)
    return {y:pd.concat(panels[y],ignore_index=True) for y in panels}

def analyze(archive,receipt):
    old_result=json.loads(receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw);del raw
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N=prepare(old);del old
    if len(t)!=550062 or N!=62199:raise ValueError("HOLD_JRA_PARITY")
    v=replay(t,N)
    orig={k:original_calibrate(v[CAL],k) for k in ("naive","graph","context")}
    for k in orig:
        ref=old_result["calibration"][k]
        same(orig[k]["Brier"],ref["Brier"],"ORIGINAL_CALIBRATION")
        same(orig[k]["slope"],ref["slope"],"ORIGINAL_SLOPE")
    cal={g:calibrate(v[CAL],g) for g in GROUPS}
    out={}
    for yr in TEST:
        r=original_evaluate(v[yr],orig);ref=old_result["results"][str(yr)]
        for k in ("all_pairs","connected_pairs","first_pairs","first_connected_pairs","first_both_one_win_pairs_all","first_both_one_start_one_win_pairs_all"):
            same(r[k],ref[k],"ORIGINAL_DENOMINATOR")
        for k,a in r["groups"].items():
            b=ref["groups"][k]
            same(a["pairs"],b["pairs"],"ORIGINAL_GROUP")
            if "Brier" in a:
                same(list(a["Brier"].values()),list(b["Brier"].values()),"ORIGINAL_BRIER")
        out[str(yr)]={g:{"all":score(v[yr],g,cal[g]),"matched_control":score(v[yr],g,cal[g],True)} for g in GROUPS}
    return {"status":"RETROSPECTIVE_OPPONENT_EVIDENCE_REVISION","source_sha256":SOURCE_SHA,
            "original_PR107_parity":True,"primary":"2021 both one-start-one-win; broader one-win second contrast",
            "calibration":cal,"results":out,
            "limits":["Post-PR107 diagnostic; frozen before new revision fits, not an independent sample.",
              "One-hop change in former opponents' online ratings since last focal race, removing passive decay, not full graph refit or causal ability change.",
              "Same-day alternate-race controls matched on surface/distance band, available count and post-day ratings; neither randomized nor fully matched on future opportunities or earlier encounters.",
              "Conditional date intervals omit crossed horse, graph and training dependence. Historical complete classified fields, not official career/debut.",
              "No absolute speed, genetic, prospective or wagering claim. No raw data exported."]}

def self_test():
    st=State(6);anchors={}
    def race(day,r,ids,rank,surf="turf",dist=1600):
        n=len(ids)
        return pd.DataFrame({"id":ids,"horse":list(map(str,ids)),"race":r,"day":pd.Timestamp(day),"rank":rank,"field":n,
          "surface":surf,"distance":dist,"y":(np.array(rank)-1)/(n-1)})
    t=pd.concat([race("2018-01-01","a",[0,1],[1,2]),race("2018-01-01","b",[2,3],[1,2])])
    day=t.day.iloc[0].toordinal();process_day(t,st,False);store_anchors(t,st,anchors,day)
    z=anchors[0]
    before,_,_=innovation(st,z[1],day,day+1);same(before,0.,"NO_NEW_RECORDS")
    t=race("2018-01-02","c",[1,4],[1,2]);process_day(t,st,False);store_anchors(t,st,anchors,day+1)
    v,p,u,pu,e,m,g=anchored_features(st,anchors,np.array([0]),day+2)
    assert e[0] and m[0] and u[0]==1 and v[0]>0 and pu[0]==0
    same(p[0],0.,"PLACEBO_PASSIVE")
    # Focal rating itself has not been updated; opponent evidence can change.
    assert st.last[0]==day
    print("Synthetic indirect post-encounter update, passive decay, matched control and time gates passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.output)):p.error("archive/receipt/output required")
    r=analyze(a.archive,a.receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
