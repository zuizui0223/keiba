#!/usr/bin/env python3
"""Chronological common ability scale from the opponent network.
Relative classified-rank ability, not physiological capacity or wagers.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame

CAL=2019
TEST=(2020,2021)
HALF_LIFE=2.
RIDGE=1.
SLOPES=(0.,.25,.5,.75,1.,1.25,1.5,2.,3.,4.)
SEED=20261126
DRAWS=999
MIN_PAIRS=100
MIN_DAYS=30

def prepare(old):
    t=old.loc[old.circuit.eq("JRA"),["horse","race","day","year","field","rank","y","surface","distance"]].copy()
    t["horse"]=t.horse.astype(str);t["race"]=t.race.astype(str)
    t=t.sort_values(["day","race","horse"],kind="mergesort").reset_index(drop=True)
    if t.duplicated(["horse","race"]).any():raise ValueError("HOLD_KEYS")
    ids=np.sort(t.horse.unique());t["id"]=pd.Categorical(t.horse,categories=ids).codes.astype(np.int64)
    if (t.id<0).any():raise ValueError("HOLD_IDS")
    return t,len(ids)

def make_pairs(t,N):
    arrays={k:t[k].to_numpy() for k in ("id","rank","field","year","day","race","surface")}
    a=[];b=[]
    for _,ix in t.groupby("race",observed=True,sort=False).indices.items():
        n=len(ix)
        if n<2 or not (arrays["field"][ix]==n).all() or not np.array_equal(np.sort(arrays["rank"][ix]),np.arange(1,n+1)):
            raise ValueError("HOLD_COMPLETE_FIELD")
        i,j=np.triu_indices(n,1);a.append(ix[i]);b.append(ix[j])
    a=np.concatenate(a);b=np.concatenate(b)
    ai=arrays["id"][a];bi=arrays["id"][b]
    if not (ai<bi).all():raise ValueError("HOLD_PAIR_ORIENTATION")
    y=(arrays["rank"][a]<arrays["rank"][b]).astype(float)
    p=pd.DataFrame({"a":ai,"b":bi,"key":ai*N+bi,"y":y,"field":arrays["field"][a],
        "year":arrays["year"][a],"day":arrays["day"][a],"race":arrays["race"][a]})
    p["first_day"]=p.groupby("key",sort=False).day.transform("min")
    return p

def fit_graph(hist,N,year):
    if hist.empty or int(hist.year.max())>=year:raise ValueError("HOLD_HISTORY_CUTOFF")
    a=hist.a.to_numpy(np.int64);b=hist.b.to_numpy(np.int64);y=hist.y.to_numpy(float)
    time=2.**(-(year-1-hist.year.to_numpy(float))/HALF_LIFE)
    w=time/(hist.field.to_numpy(float)-1)
    # Aggregate observed win and loss weights for each ordered ID pair.
    key=hist.key.to_numpy(np.int64)
    k,inv=np.unique(key,return_inverse=True)
    aw=np.bincount(inv,weights=w*y);total=np.bincount(inv,weights=w)
    a=k//N;b=k%N
    active=np.unique(np.r_[a,b]);ix=np.full(N,-1,dtype=np.int64);ix[active]=np.arange(len(active))
    A=ix[a];B=ix[b];n=len(active)
    def objective(theta):
        z=theta[A]-theta[B];p=expit(z)
        loss=float(np.dot(total,np.logaddexp(0,z))-np.dot(aw,z)+.5*RIDGE*np.dot(theta,theta))
        g=total*p-aw
        grad=np.bincount(A,weights=g,minlength=n)-np.bincount(B,weights=g,minlength=n)+RIDGE*theta
        return loss,grad
    res=minimize(objective,np.zeros(n),jac=True,method="L-BFGS-B",options={"maxiter":250,"ftol":1e-12,"gtol":1e-5})
    if not res.success or not np.isfinite(res.x).all():raise ValueError("HOLD_GRAPH_OPTIMIZATION:"+str(res.message))
    gradient=float(np.max(np.abs(objective(res.x)[1])))
    if gradient>0.05:raise ValueError("HOLD_GRAPH_GRADIENT")
    # Separate graph component identifiability from ridge anchoring.
    adj=coo_matrix((np.ones(len(A)),(A,B)),shape=(n,n)).tocsr()
    nc,lab=connected_components(adj,directed=False,return_labels=True)
    comp=np.full(N,-1,dtype=np.int64);comp[active]=lab
    ability=np.zeros(N);ability[active]=res.x
    exposure=np.bincount(np.r_[a,b],minlength=N)
    return ability,comp,{"active_horses":n,"unique_edges":len(k),"components":int(nc),
        "largest_component_horses":int(np.bincount(lab).max()),"optimizer_iterations":int(res.nit),
        "max_abs_gradient":gradient,"objective":float(res.fun)}

def baseline(t,N,year):
    h=t.loc[t.year.lt(year)]
    if h.empty:raise ValueError("HOLD_NO_HISTORY")
    i=h.id.to_numpy(np.int64);w=2.**(-(year-1-h.year.to_numpy(float))/HALF_LIFE)
    n=np.bincount(i,weights=w,minlength=N)
    y=np.bincount(i,weights=w*(1-h.y.to_numpy(float)),minlength=N)
    score=(y+2.5)/(n+5)
    return np.log(score/(1-score)),np.bincount(i,minlength=N)

def prior_day_counts(t,N):
    # All results strictly before the race day; same-day races never enter counts.
    h=t[["id","day","rank"]].copy();h["win"]=h["rank"].eq(1).astype(int)
    g=h.groupby(["id","day"],observed=True).agg(starts=("win","size"),wins=("win","sum")).reset_index().sort_values(["id","day"])
    for k in ("starts","wins"):g["prior_"+k]=g.groupby("id",observed=True)[k].cumsum()-g[k]
    return g[["id","day","prior_starts","prior_wins"]]

def features(p,theta,comp,naive,counts,prior,year):
    q=p.loc[p.year.eq(year)].copy().reset_index(drop=True)
    a=q.a.to_numpy(np.int64);b=q.b.to_numpy(np.int64)
    q["connected"]=(comp[a]>=0)&(comp[a]==comp[b])
    q["seen_both"]=(counts[a]>0)&(counts[b]>0)
    q["first"]=(q.day==q.first_day)
    q["naive"]=naive[a]-naive[b];q["graph"]=theta[a]-theta[b]
    # Day-based first-meeting and one-win categories are evaluation strata, not model inputs.
    for k in ("a","b"):
        z=prior.rename(columns={"id":k,"prior_starts":k+"_prior_starts","prior_wins":k+"_prior_wins"})
        q=q.merge(z,on=[k,"day"],how="left",validate="many_to_one",sort=False)
    if q[["a_prior_starts","a_prior_wins","b_prior_starts","b_prior_wins"]].isna().any().any():raise ValueError("HOLD_PRIOR_COUNT_JOIN")
    q["both_one_win"]=(q.a_prior_wins==1)&(q.b_prior_wins==1)
    q["both_one_start"]=(q.a_prior_starts==1)&(q.b_prior_starts==1)&q.both_one_win
    q["naive_tie"]=np.abs(q.naive)<1e-12
    return q

def weights(t):
    return 1/t.groupby("race",observed=True).race.transform("size").to_numpy(float)

def calibrate(t,k):
    t=t.loc[t.connected&t.first]
    if t.empty:raise ValueError("HOLD_CALIBRATION")
    x=t[k].to_numpy(float);y=t.y.to_numpy(float);w=weights(t)
    loss=[float(np.average((y-expit(a*x))**2,weights=w)) for a in SLOPES]
    i=min(range(len(loss)),key=lambda j:(loss[j],SLOPES[j]))
    return {"slope":SLOPES[i],"grid":list(SLOPES),"Brier":loss,"pairs":len(t),"races":int(t.race.nunique())}

def evaluate(t,cal):
    # Cross-component comparisons cannot identify data-supported relative offsets.
    q=t.loc[t.connected].copy()
    masks={"all_connected":np.ones(len(q),bool),"first_meeting":q.first,
           "first_both_one_win":q.first&q.both_one_win,
           "first_both_one_start_one_win":q.first&q.both_one_start,
           "first_naive_tie":q.first&q.naive_tie}
    out={}
    for name,mask in masks.items():
        z=q.loc[mask]
        if z.empty:
            out[name]={"status":"HOLD_EMPTY","pairs":0};continue
        w=weights(z);y=z.y.to_numpy(float)
        pred={k:expit(cal[k]["slope"]*z[k].to_numpy(float)) for k in ("naive","graph")}
        loss={k:(y-v)**2 for k,v in pred.items()}
        d=loss["naive"]-loss["graph"]
        pairs=int(z.key.nunique());days=int(z.day.nunique())
        r={"status":"OBSERVED" if pairs>=MIN_PAIRS and days>=MIN_DAYS else "HOLD_SUPPORT",
           "pairs":len(z),"distinct_pairs":pairs,"races":int(z.race.nunique()),"days":days,
           "horses":len(np.unique(np.r_[z.a,z.b])),"Brier":{"neutral":.25,**{k:float(np.average(v,weights=w)) for k,v in loss.items()}},
           "gain":float(np.average(d,weights=w)),
           "accuracy_half_for_ties":{k:float(np.average(np.where(v==.5,.5,((v>.5)==(y==1)).astype(float)),weights=w)) for k,v in pred.items()},
           "mean_abs_graph_ability_gap":float(np.average(np.abs(z.graph),weights=w))}
        if r["status"]=="OBSERVED":
            tab=pd.DataFrame({"day":z.day.to_numpy(),"w":w,"d":w*d})
            a=tab.groupby("day",observed=True)[["w","d"]].sum().to_numpy()
            rng=np.random.default_rng(SEED)
            draws=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
            r["conditional_day_97_5_gain"]=np.quantile(draws[:,1]/draws[:,0],[.0125,.9875]).tolist()
        out[name]=r
    return {"all_pairs":len(t),"connected_pairs":len(q),"both_seen_pairs":int(t.seen_both.sum()),
        "first_pairs":int(t.first.sum()),"first_connected_pairs":int((t.first&t.connected).sum()),
        "first_both_one_win_pairs_all":int((t.first&t.both_one_win).sum()),
        "first_both_one_start_one_win_pairs_all":int((t.first&t.both_one_start).sum()),"groups":out}

def analyze(archive):
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw);del raw
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N=prepare(old);del old
    p=make_pairs(t,N);prior=prior_day_counts(t,N)
    cal=None;out={}
    for year in (CAL,*TEST):
        theta,comp,qa=fit_graph(p.loc[p.year.lt(year)],N,year)
        naive,count=baseline(t,N,year)
        q=features(p,theta,comp,naive,count,prior,year)
        if year==CAL:
            cal={k:calibrate(q,k) for k in ("naive","graph")}
            out[str(year)]={"graph":qa,"calibration":cal}
        else:out[str(year)]={"graph":qa,"evaluation":evaluate(q,cal)}
    # Pool the untouched-in-model-design 2020/21 targets after year-specific
    # graph fits (the underlying archive was previously studied).
    return {"status":"RETROSPECTIVE_COMMON_ABILITY_NETWORK","source_sha256":SOURCE_SHA,
        "JRA_starts":len(t),"JRA_horses":N,"primary":"2021/first_both_one_win, with first_meeting general comparator",
        "calibration":cal,"results":out,
        "limits":["Only JRA complete classified finishers and recorded meetings; no official debut/total career win or full entry claims.",
        "Historical graph uses all JRA flat surfaces and distances; ability is scalar and context averaged, year-start frozen. No within-year feature refresh.",
        "First meeting and prior-win counts are strictly before target date for evaluation stratification, not inputs to ratings.",
        "Disconnected and unseen comparisons are excluded from supported inference and retained in coverage denominators.",
        "Ridge regularization sets scale/anchor within fit; year-to-year absolute rating change not identified. Conditional date intervals omit repeated-horse/graph-fit dependence.",
        "No absolute speed, genetic causation, physical interference, prospective forecast or wagering claim. No individual records exported."]}

def self_test():
    # Stronger chains with no direct A-B meeting; bridge via C.
    N=6;rows=[]
    for a,b,y in [(0,2,1),(1,2,0),(2,3,1),(4,5,1)]:
        for _ in range(4):rows.append({"a":a,"b":b,"key":a*N+b,"y":y,"field":2,"year":2018})
    h=pd.DataFrame(rows);v,c,q=fit_graph(h,N,2019)
    assert v[0]>v[2]>v[1] and c[0]==c[1] and c[0]!=c[4]
    assert q["components"]==2
    # Two wins on the same day do not enter one another's prior count.
    t=pd.DataFrame({"id":[0,0,0,1],"day":pd.to_datetime(["2018-01-01","2018-01-01","2018-02-01","2018-01-01"]),"rank":[1,1,2,1]})
    g=prior_day_counts(t,N)
    assert g.loc[(g.id==0)&g.day.eq(pd.Timestamp("2018-02-01")),"prior_wins"].iloc[0]==2
    assert g.loc[g.day.eq(pd.Timestamp("2018-01-01")),"prior_wins"].eq(0).all()
    print("Synthetic indirect comparison, disconnected component and strict prior-day count checks passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.output)):p.error("archive/output required")
    r=analyze(a.archive);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
