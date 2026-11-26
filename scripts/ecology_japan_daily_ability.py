#!/usr/bin/env python3
"""Day-batched relative ability and surface deviation, no same-day leakage.
Historical classified fields only; no wagering, causal physiology or absolute speed."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from ecology_japan_common_ability import (
    SOURCE_SHA,COLS,prepare_frame,prepare,CAL,TEST,SLOPES,MIN_PAIRS,MIN_DAYS,DRAWS,SEED,weights
)
HALF_LIFE_DAYS=730.
GLOBAL_STEP=.5
SURFACE_STEP=.25

class State:
    def __init__(self,n):
        self.n=n;self.parent=np.arange(n);self.size=np.ones(n,dtype=int)
        self.last=np.full(n,-1,dtype=int)
        self.starts=np.zeros(n,dtype=int);self.wins=np.zeros(n,dtype=int)
        self.count=np.zeros(n);self.total=np.zeros(n)
        self.global_rating=np.zeros(n)
        self.context_global=np.zeros(n);self.surface=np.zeros((n,2))
        self.seen=set()
    def root(self,i):
        while self.parent[i]!=i:
            self.parent[i]=self.parent[self.parent[i]];i=self.parent[i]
        return i
    def join(self,a,b):
        a=self.root(a);b=self.root(b)
        if a==b:return
        if self.size[a]<self.size[b]:a,b=b,a
        self.parent[b]=a;self.size[a]+=self.size[b]
    def snapshot(self,ids,day):
        elapsed=np.where(self.last[ids]<0,0,day-self.last[ids])
        if (elapsed<0).any():raise ValueError("HOLD_TIME_ORDER")
        decay=2.**(-elapsed/HALF_LIFE_DAYS)
        self.count[ids]*=decay;self.total[ids]*=decay
        self.global_rating[ids]*=decay;self.context_global[ids]*=decay
        self.surface[ids,:]*=decay[:,None]
        self.last[ids]=day

def process_day(t,st,emit):
    t=t.sort_values(["race","id"],kind="mergesort").reset_index(drop=True)
    ids=t.id.to_numpy(np.int64);ranks=t["rank"].to_numpy();field=t.field.to_numpy()
    ss=t.surface.astype(str).map({"turf":0,"dirt":1}).to_numpy()
    if not np.isin(ss,[0,1]).all():raise ValueError("HOLD_SURFACE")
    ss=ss.astype(int);active=np.unique(ids)
    date=t.day.iloc[0];day=int(date.toordinal())
    if t.day.nunique()!=1 or (st.last[active]>=day).any():raise ValueError("HOLD_SAME_DAY_UPDATE")
    st.snapshot(active,day)
    aa=[];bb=[];race_groups=[]
    for _,ix in t.groupby("race",observed=True,sort=False).indices.items():
        n=len(ix)
        if n<2 or not (field[ix]==n).all() or not np.array_equal(np.sort(ranks[ix]),np.arange(1,n+1)) or len(np.unique(ss[ix]))!=1:
            raise ValueError("HOLD_COMPLETE_FIELD")
        a,b=np.triu_indices(n,1);aa.append(ix[a]);bb.append(ix[b]);race_groups.append(ids[ix])
    a=np.concatenate(aa);b=np.concatenate(bb);i=ids[a];j=ids[b]
    if not (i<j).all():raise ValueError("HOLD_ORIENTATION")
    key=i*st.n+j;win=(ranks[a]<ranks[b]).astype(float)
    ww=1./(field[a]-1)
    g=st.global_rating[i]-st.global_rating[j]
    ctx=st.context_global[i]+st.surface[i,ss[a]]-st.context_global[j]-st.surface[j,ss[b]]
    p=(st.total[active]+2.5)/(st.count[active]+5.)
    ns=np.log(p/(1-p))
    x=np.searchsorted(active,i);z=np.searchsorted(active,j)
    naive=ns[x]-ns[z]
    # All evaluated features are taken before any update from this day.
    result=None
    if emit:
        roots=np.array([st.root(int(h)) for h in active])
        first=np.fromiter((int(k) not in st.seen for k in key),bool,count=len(key))
        connected=(st.starts[i]>0)&(st.starts[j]>0)&(roots[x]==roots[z])
        result=pd.DataFrame({"a":i,"b":j,"key":key,"race":t.race.to_numpy()[a],"day":date,"y":win,
            "connected":connected,"first":first,"both_one_win":(st.wins[i]==1)&(st.wins[j]==1),
            "both_one_start":(st.starts[i]==1)&(st.starts[j]==1)&(st.wins[i]==1)&(st.wins[j]==1),
            "naive":naive,"graph":g,"context":ctx,"naive_tie":np.abs(naive)<1e-12})
    # Simultaneous day-batched updates. Use one gradient unit per start,
    # average over starts for a horse if multiple records share a day.
    nh=np.bincount(ids,minlength=st.n)
    def gradient(res):
        return np.bincount(i,weights=ww*res,minlength=st.n)-np.bincount(j,weights=ww*res,minlength=st.n)
    rg=win-expit(g);rc=win-expit(ctx)
    st.global_rating[active]+=GLOBAL_STEP*gradient(rg)[active]/nh[active]
    st.context_global[active]+=GLOBAL_STEP*gradient(rc)[active]/nh[active]
    for k in (0,1):
        keep=ss[a]==k
        su=np.bincount(i[keep],weights=(ww*rc)[keep],minlength=st.n)-np.bincount(j[keep],weights=(ww*rc)[keep],minlength=st.n)
        nc=np.bincount(ids[ss==k],minlength=st.n)
        ac=active[nc[active]>0]
        st.surface[ac,k]+=SURFACE_STEP*su[ac]/nc[ac]
    st.count[active]+=nh[active]
    st.total[active]+=np.bincount(ids,weights=1-t.y.to_numpy(float),minlength=st.n)[active]
    st.starts[active]+=nh[active]
    st.wins[active]+=np.bincount(ids,weights=(ranks==1).astype(int),minlength=st.n)[active].astype(int)
    for members in race_groups:
        for other in members[1:]:st.join(int(members[0]),int(other))
    st.seen.update(map(int,key))
    return result

def calibrate(t,k):
    q=t.loc[t.connected&t["first"]]
    if q.empty:raise ValueError("HOLD_CALIBRATION")
    w=weights(q);y=q.y.to_numpy(float);x=q[k].to_numpy(float)
    loss=[float(np.average((y-expit(v*x))**2,weights=w)) for v in SLOPES]
    j=min(range(len(loss)),key=lambda i:(loss[i],SLOPES[i]))
    return {"slope":SLOPES[j],"grid":list(SLOPES),"Brier":loss,"pairs":len(q)}

def evaluate(t,cal):
    q=t.loc[t.connected].copy()
    masks={"all_connected":np.ones(len(q),bool),"first_meeting":q["first"],
           "first_both_one_win":q["first"]&q.both_one_win,
           "first_both_one_start_one_win":q["first"]&q.both_one_start,
           "first_naive_tie":q["first"]&q.naive_tie}
    out={}
    for name,mask in masks.items():
        z=q.loc[mask]
        if z.empty:out[name]={"status":"HOLD_EMPTY","pairs":0};continue
        w=weights(z);y=z.y.to_numpy(float)
        pred={k:expit(cal[k]["slope"]*z[k].to_numpy(float)) for k in ("naive","graph","context")}
        loss={k:(y-v)**2 for k,v in pred.items()}
        d=np.column_stack([loss["naive"]-loss["graph"],loss["graph"]-loss["context"]])
        names=["daily_network_vs_naive","surface_vs_daily_network"]
        pairs=int(z.key.nunique());days=int(z.day.nunique())
        r={"status":"OBSERVED" if pairs>=MIN_PAIRS and days>=MIN_DAYS else "HOLD_SUPPORT",
           "pairs":len(z),"distinct_pairs":pairs,"races":int(z.race.nunique()),"days":days,
           "horses":len(np.unique(np.r_[z.a,z.b])),"Brier":{"neutral":.25,**{k:float(np.average(v,weights=w)) for k,v in loss.items()}},
           "gain":dict(zip(names,np.average(d,axis=0,weights=w).tolist())),
           "accuracy_half_for_ties":{k:float(np.average(np.where(v==.5,.5,((v>.5)==(y==1)).astype(float)),weights=w)) for k,v in pred.items()},
           "mean_abs_ability_gap":{k:float(np.average(np.abs(z[k]),weights=w)) for k in pred}}
        if r["status"]=="OBSERVED":
            tab=pd.DataFrame({"day":z.day.to_numpy(),"w":w,"d0":w*d[:,0],"d1":w*d[:,1]})
            a=tab.groupby("day",observed=True)[["w","d0","d1"]].sum().to_numpy()
            rng=np.random.default_rng(SEED)
            draws=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
            r["conditional_day_97_5_gain"]=dict(zip(names,np.quantile(draws[:,1:]/draws[:,0,None],[.0125,.9875],axis=0).T.tolist()))
        out[name]=r
    return {"all_pairs":len(t),"connected_pairs":len(q),"first_pairs":int(t["first"].sum()),
            "first_connected_pairs":int((t["first"]&t.connected).sum()),
            "first_both_one_win_pairs_all":int((t["first"]&t.both_one_win).sum()),
            "first_both_one_start_one_win_pairs_all":int((t["first"]&t.both_one_start).sum()),"groups":out}

def analyze(archive):
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw);del raw
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N=prepare(old);del old
    st=State(N);panels={y:[] for y in (CAL,*TEST)}
    for day,d in t.groupby("day",sort=True,observed=True):
        year=int(day.year)
        q=process_day(d,st,year in panels)
        if q is not None:panels[year].append(q)
    v={y:pd.concat(panels[y],ignore_index=True) for y in panels};del panels
    cal={k:calibrate(v[CAL],k) for k in ("naive","graph","context")}
    return {"status":"RETROSPECTIVE_DAILY_COMMON_ABILITY","source_sha256":SOURCE_SHA,"JRA_starts":len(t),"JRA_horses":N,
        "primary":"2021/first_both_one_win/daily_network_vs_naive and first_meeting/surface_vs_daily_network",
        "parameters":{"half_life_days":HALF_LIFE_DAYS,"global_step":GLOBAL_STEP,"surface_step":SURFACE_STEP},
        "calibration":cal,"results":{str(y):evaluate(v[y],cal) for y in TEST},
        "limits":["Historical complete classified fields, not confirmed entries, all career records or wagers.",
        "Daily ratings use outcomes strictly before the target date. Context residual is only turf/dirt; no exact distance, going or age.",
        "Online gradients do not retrospectively propagate new opponent evidence to an inactive horse; batch graph refit is a distinct model.",
        "Historical graph connectivity does not guarantee well-identified ability; no individual rating intervals.",
        "Conditional calendar-day bootstrap excludes repeated horse and fit dependence. No physiological or genetic inference, no raw export."]}

def self_test():
    st=State(4)
    def race(day,r,ids,rank,surf="turf"):
        n=len(ids)
        return pd.DataFrame({"id":ids,"horse":list(map(str,ids)),"race":r,"day":pd.Timestamp(day),"rank":rank,"field":n,
            "surface":surf,"y":(np.array(rank)-1)/(n-1)})
    a=race("2018-01-01","a",[0,1],[1,2]);b=race("2018-01-01","b",[2,3],[1,2])
    q=process_day(pd.concat([a,b]),st,True)
    assert not q.connected.any() and q["first"].all() and np.allclose(q.graph,0)
    q=process_day(race("2018-01-02","c",[0,2],[1,2]),st,True)
    assert q.both_one_start.all() and q["first"].all() and not q.connected.any()
    q=process_day(race("2018-01-03","d",[1,3],[1,2]),st,True)
    assert q.connected.all() and q["first"].all()
    assert np.allclose(st.global_rating.sum(),0,atol=.01)
    try:process_day(race("2018-01-03","e",[1,3],[1,2]),st,True)
    except ValueError as e:assert str(e)=="HOLD_SAME_DAY_UPDATE"
    else:raise AssertionError("same-day leak")
    # Calibration/scoring integration check, including first column.
    cal={k:calibrate(q,k) for k in ("naive","graph","context")}
    assert evaluate(q,cal)["groups"]["first_meeting"]["pairs"]==1
    print("Synthetic daily graph, first-win, chronology and evaluation tests passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.output)):p.error("archive/output required")
    r=analyze(a.archive);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
