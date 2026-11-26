#!/usr/bin/env python3
"""Monthly joint Bradley-Terry network vs same-cutoff and daily online ratings.
Retrospective classified race research, not physical ability or wagering."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from ecology_japan_common_ability import make_pairs,RIDGE
from ecology_japan_daily_ability import (
    SOURCE_SHA,COLS,prepare_frame,prepare,State,process_day,CAL,TEST,SLOPES,
    HALF_LIFE_DAYS,MIN_PAIRS,MIN_DAYS,DRAWS,SEED,weights,
    calibrate as original_calibrate,evaluate as original_evaluate
)

MODELS=("frozen_naive","frozen_online","batch","daily_naive","daily_online","daily_surface")
GROUPS=("first_both_one_start_one_win","first_both_one_win","first_meeting")

def same(a,b,label):
    if not np.allclose(a,b,rtol=0,atol=1e-10):raise ValueError("HOLD_"+label)

def fit_month(hist,N,cut,warm):
    if hist.empty or hist.day.max()>=cut:raise ValueError("HOLD_HISTORY_CUTOFF")
    age=(cut-hist.day).dt.days.to_numpy(float)
    w=2.**(-age/HALF_LIFE_DAYS)/(hist.field.to_numpy(float)-1.)
    key=hist.key.to_numpy(np.int64);y=hist.y.to_numpy(float)
    k,inv=np.unique(key,return_inverse=True)
    total=np.bincount(inv,weights=w);wins=np.bincount(inv,weights=w*y)
    a=k//N;b=k%N
    active=np.unique(np.r_[a,b]);ix=np.full(N,-1,dtype=np.int64);ix[active]=np.arange(len(active))
    A=ix[a];B=ix[b];n=len(active)
    def objective(theta):
        z=theta[A]-theta[B];p=expit(z)
        loss=float(np.dot(total,np.logaddexp(0,z))-np.dot(wins,z)+.5*RIDGE*np.dot(theta,theta))
        g=total*p-wins
        grad=np.bincount(A,weights=g,minlength=n)-np.bincount(B,weights=g,minlength=n)+RIDGE*theta
        return loss,grad
    res=minimize(objective,warm[active],jac=True,method="L-BFGS-B",options={"maxiter":250,"ftol":1e-12,"gtol":1e-5})
    if not res.success or not np.isfinite(res.x).all():raise ValueError("HOLD_MONTH_OPTIMIZATION:"+str(res.message))
    gradient=float(np.max(np.abs(objective(res.x)[1])))
    if gradient>0.05:raise ValueError("HOLD_MONTH_GRADIENT")
    adj=coo_matrix((np.ones(len(A)),(A,B)),shape=(n,n)).tocsr()
    nc,lab=connected_components(adj,directed=False,return_labels=True)
    comp=np.full(N,-1,dtype=np.int64);comp[active]=lab
    rating=np.zeros(N);rating[active]=res.x
    p=expit(res.x[A]-res.x[B]);curv=total*p*(1-p)
    hdiag=np.full(N,RIDGE)
    hdiag[active]+=np.bincount(A,weights=curv,minlength=n)+np.bincount(B,weights=curv,minlength=n)
    if not np.isfinite(hdiag).all() or (hdiag<RIDGE).any():raise ValueError("HOLD_CURVATURE")
    return rating,comp,hdiag,{"history_pairs":len(hist),"active_horses":n,"components":int(nc),
        "largest_component":int(np.bincount(lab).max()),"edges":len(k),"iterations":int(res.nit),
        "max_abs_gradient":gradient}

def freeze_online(st,cut):
    day=cut.toordinal()
    if (st.last>=day).any():raise ValueError("HOLD_SNAPSHOT_FUTURE")
    elapsed=np.where(st.last<0,0,day-st.last)
    decay=2.**(-elapsed/HALF_LIFE_DAYS)
    p=(st.total*decay+2.5)/(st.count*decay+5)
    return st.global_rating*decay,np.log(p/(1-p)),st.starts.copy()

def attach(q,theta,comp,hdiag,online,naive,snap_n,cut):
    a=q.a.to_numpy(np.int64);b=q.b.to_numpy(np.int64)
    if (q.day<cut).any():raise ValueError("HOLD_SNAPSHOT_ORDER")
    q=q.copy()
    q["snapshot_connected"]=(comp[a]>=0)&(comp[a]==comp[b])
    if (q.snapshot_connected&~q.connected).any():raise ValueError("HOLD_COMPONENT_MONOTONICITY")
    q["batch"]=theta[a]-theta[b]
    q["frozen_online"]=online[a]-online[b];q["frozen_naive"]=naive[a]-naive[b]
    q["daily_online"]=q.graph;q["daily_naive"]=q.naive;q["daily_surface"]=q.context
    # For a true first recorded meeting, the historical Hessian has H_ab=0.
    # Cauchy-Schwarz: (e_a-e_b)'H^-1(e_a-e_b) >= 4/(H_aa+H_bb).
    # H >= ridge I gives upper bound 2/ridge. Not a calibrated CI.
    q["var_lower"]=4/(hdiag[a]+hdiag[b])
    q["var_upper"]=2./RIDGE
    strict=(q["first"]&q.both_one_start&q.snapshot_connected).to_numpy()
    if not ((snap_n[a[strict]]==1)&(snap_n[b[strict]]==1)).all():raise ValueError("HOLD_STRICT_SNAPSHOT_HISTORY")
    return q

def groupmask(t,g):
    q=t.connected&t["first"]
    if g==GROUPS[0]:return q&t.both_one_start
    if g==GROUPS[1]:return q&t.both_one_win
    if g==GROUPS[2]:return q
    raise ValueError("HOLD_GROUP")

def calibration(t):
    q=t.loc[groupmask(t,GROUPS[2])&t.snapshot_connected]
    if q.empty or q.key.nunique()<MIN_PAIRS or q.day.nunique()<MIN_DAYS:raise ValueError("HOLD_CALIBRATION_SUPPORT")
    y=q.y.to_numpy(float);w=weights(q)
    out={}
    for k in MODELS[:3]:
        x=q[k].to_numpy(float)
        risk=[float(np.average((y-expit(v*x))**2,weights=w)) for v in SLOPES]
        j=min(range(len(risk)),key=lambda i:(risk[i],SLOPES[i]))
        out[k]={"slope":SLOPES[j],"grid":list(SLOPES),"Brier":risk}
    for k in MODELS[3:]:out[k]={"slope":2.,"frozen_PR107":True}
    return {"pairs":len(q),"days":int(q.day.nunique()),"models":out}

def score(t,g,cal):
    all_=t.loc[groupmask(t,g)]
    z=all_.loc[all_.snapshot_connected].copy()
    den=len(all_)
    if z.empty:return {"status":"HOLD_EMPTY","daily_connected_pairs":den,"matched_pairs":0}
    w=weights(z);y=z.y.to_numpy(float)
    pred={k:expit(cal["models"][k]["slope"]*z[k].to_numpy(float)) for k in MODELS}
    loss={k:(y-p)**2 for k,p in pred.items()}
    contrasts={"batch_vs_frozen_online":loss["frozen_online"]-loss["batch"],
        "batch_vs_daily_online":loss["daily_online"]-loss["batch"],
        "batch_vs_frozen_naive":loss["frozen_naive"]-loss["batch"],
        "daily_vs_frozen_online":loss["frozen_online"]-loss["daily_online"]}
    names=list(contrasts)[:2];days=int(z.day.nunique());pairs=int(z.key.nunique())
    support=days>=MIN_DAYS and pairs>=MIN_PAIRS
    lower=np.sqrt(z.var_lower.to_numpy(float));upper=np.sqrt(z.var_upper.to_numpy(float));gap=np.abs(z.batch.to_numpy(float))
    if (lower>upper+1e-10).any():raise ValueError("HOLD_VARIANCE_BOUND")
    out={"status":"OBSERVED" if support else "HOLD_SUPPORT","daily_connected_pairs":den,"matched_pairs":len(z),
        "coverage":len(z)/den,"distinct_pairs":pairs,"days":days,"races":int(z.race.nunique()),
        "horses":len(np.unique(np.r_[z.a,z.b])),
        "Brier":{k:float(np.average(v,weights=w)) for k,v in loss.items()},
        "accuracy":{k:float(np.average(np.where(p==.5,.5,((p>.5)==(y==1)).astype(float)),weights=w)) for k,p in pred.items()},
        "gain":{k:float(np.average(v,weights=w)) for k,v in contrasts.items()},
        "curvature_diagnostic":{"mean_absolute_batch_gap":float(np.average(gap,weights=w)),
          "mean_lower_bound_laplace_sd":float(np.average(lower,weights=w)),
          "upper_bound_laplace_sd":float(np.sqrt(2/RIDGE)),
          "fraction_exceeds_1_96_lower_sd":float(np.average(gap>1.96*lower,weights=w)),
          "fraction_exceeds_1_96_upper_sd":float(np.average(gap>1.96*upper,weights=w))}}
    if support:
        tab=pd.DataFrame({k:w*contrasts[k] for k in names})
        tab["w"]=w;tab["day"]=z.day.to_numpy()
        a=tab.groupby("day",observed=True)[names+["w"]].sum().to_numpy()
        rng=np.random.default_rng(SEED);draw=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
        out["conditional_day_97_5_gain"]=dict(zip(names,np.quantile(draw[:,:2]/draw[:,2,None],[.0125,.9875],axis=0).T.tolist()))
    return out

def replay(t,p,N):
    st=State(N);panels={y:[] for y in (CAL,*TEST)};month=None;warm=np.zeros(N);qa={}
    dates=p.day.to_numpy(dtype="datetime64[ns]")
    if not p.day.is_monotonic_increasing:raise ValueError("HOLD_UNSORTED_PAIR_HISTORY")
    for day,d in t.groupby("day",sort=True,observed=True):
        year=int(day.year)
        if year in panels:
            cut=pd.Timestamp(year=year,month=day.month,day=1)
            if month!=cut:
                idx=np.searchsorted(dates,np.datetime64(cut,"ns"),side="left")
                theta,comp,hdiag,rec=fit_month(p.iloc[:idx],N,cut,warm)
                online,naive,snap_n=freeze_online(st,cut)
                if not np.array_equal(comp>=0,snap_n>0):raise ValueError("HOLD_SNAPSHOT_SEEN_PARITY")
                warm=theta.copy();month=cut
                qa[str(cut.date())]=rec
                print(json.dumps({"stage":"MONTH_FIT","cutoff":str(cut.date()),**rec}),flush=True)
        q=process_day(d,st,year in panels)
        if q is not None:panels[year].append(attach(q,theta,comp,hdiag,online,naive,snap_n,month))
    return {y:pd.concat(panels[y],ignore_index=True) for y in panels},qa

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
    p=make_pairs(t,N);v,qa=replay(t,p,N)
    orig={k:original_calibrate(v[CAL],k) for k in ("naive","graph","context")}
    for k in orig:
        ref=old_result["calibration"][k]
        same(orig[k]["Brier"],ref["Brier"],"ORIGINAL_CALIBRATION");same(orig[k]["slope"],ref["slope"],"ORIGINAL_SLOPE")
    cal=calibration(v[CAL]);out={}
    for yr in TEST:
        r=original_evaluate(v[yr],orig);ref=old_result["results"][str(yr)]
        for k in ("all_pairs","connected_pairs","first_pairs","first_connected_pairs","first_both_one_win_pairs_all","first_both_one_start_one_win_pairs_all"):
            same(r[k],ref[k],"ORIGINAL_DENOMINATOR")
        for k,a in r["groups"].items():
            b=ref["groups"][k];same(a["pairs"],b["pairs"],"ORIGINAL_GROUP")
            if "Brier" in a:same(list(a["Brier"].values()),list(b["Brier"].values()),"ORIGINAL_BRIER")
        out[str(yr)]={g:score(v[yr],g,cal) for g in GROUPS}
    return {"status":"RETROSPECTIVE_MONTHLY_JOINT_ABILITY","source_sha256":SOURCE_SHA,
      "original_PR107_parity":True,"primary":"2021/first_both_one_start_one_win, batch vs same-cutoff online and actual daily online",
      "monthly_fits":qa,"calibration":cal,"results":out,
      "limits":["Monthly static joint fit versus fixed and actual daily online; difference also reflects objective, regularization and recency implementation, not pure indirect information.",
        "Both strict one-start winners must already be seen and connected at month start; report missing coverage.",
        "Curvature bounds on a formal inverse penalized composite-likelihood Hessian, not validated individual uncertainty or confidence intervals; 1.96 multiples are diagnostics.",
        "Conditional day intervals omit shared horse/graph/fitting dependence. Source previously examined; no prospective or physical/causal ability claim.",
        "Classified JRA finishers and observed histories only; no complete career or entry census. No raw IDs exported."]}

def self_test():
    N=5
    rows=[]
    for a,b,y,d in [(0,2,1,"2018-01-01"),(1,3,1,"2018-01-01"),(2,3,1,"2018-01-15"),(2,4,1,"2018-01-20")]:
        rows.append(dict(a=a,b=b,key=a*N+b,y=y,field=2,day=pd.Timestamp(d)))
    h=pd.DataFrame(rows)
    theta,comp,diag,qa=fit_month(h,N,pd.Timestamp("2018-02-01"),np.zeros(N))
    assert comp[0]==comp[1] and theta[0]>theta[1]
    # Focal 0 and 1 never reran: later encounters change joint ratings.
    old,oldc,_,_=fit_month(h.iloc[:2],N,pd.Timestamp("2018-01-02"),np.zeros(N))
    assert oldc[0]!=oldc[1] and abs(old[0]-old[1])<1e-10
    A=h.a.to_numpy();B=h.b.to_numpy();w=2.**(-((pd.Timestamp("2018-02-01")-h.day).dt.days.to_numpy())/HALF_LIFE_DAYS)
    H=np.eye(N)*RIDGE
    for a,b,v in zip(A,B,w):
        x=np.eye(N)[a]-np.eye(N)[b];p=expit(theta[a]-theta[b]);H+=v*p*(1-p)*np.outer(x,x)
    same(diag,np.diag(H),"HESSIAN_DIAGONAL")
    x=np.eye(N)[0]-np.eye(N)[1];v=x@np.linalg.solve(H,x)
    assert 4/(diag[0]+diag[1])<=v+1e-12 and v<=2/RIDGE+1e-12
    try:fit_month(h,N,pd.Timestamp("2018-01-20"),np.zeros(N))
    except ValueError as e:assert str(e)=="HOLD_HISTORY_CUTOFF"
    else:raise AssertionError("cutoff leak")
    print("Synthetic joint indirect revision, exact curvature bounds and cutoff checks passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.output)):p.error("archive/receipt/output required")
    r=analyze(a.archive,a.receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
