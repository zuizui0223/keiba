#!/usr/bin/env python3
"""Prior-day recorded-parent ratings on the same scale as individual daily ability.
No genetic causation, official debut, prospective prediction or wagering."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.optimize import minimize
from ecology_japan_daily_ability import (
    SOURCE_SHA,COLS,prepare_frame,prepare,State,process_day,CAL,TEST,
    HALF_LIFE_DAYS,MIN_PAIRS,MIN_DAYS,DRAWS,SEED,weights,
    calibrate as original_calibrate,evaluate as original_evaluate
)

PARENTS=("sire","dam")
BASE=("naive","graph","context","log_own")
COUNTS=("sire_known","dam_known","sire_log_peers","dam_log_peers")
SIGNAL=("sire_ability","dam_ability")
MODELS={"O":BASE,"N":BASE+COUNTS,"F":BASE+COUNTS+SIGNAL}
RIDGE=.001
PARENT_SHRINK=8.
OWN_SHRINK=5.
GROUPS=("first_both_one_start_one_win","first_both_one_win","first_meeting",
        "first_both_1_to_3_starts","first_both_4_plus_starts")

def same(a,b,label):
    if not np.allclose(a,b,rtol=0,atol=1e-10):raise ValueError("HOLD_"+label)

def prepare_parents(old):
    t,N=prepare(old)
    m=old.loc[old.circuit.eq("JRA"),["horse","race","sire_id","dam_id"]].copy()
    for k in m:m[k]=m[k].astype(str)
    t=t.merge(m,on=["horse","race"],how="left",validate="one_to_one",sort=False)
    if t[["sire_id","dam_id"]].isna().any().any() or len(t)!=550062 or N!=62199:
        raise ValueError("HOLD_JRA_PARENT_JOIN")
    sizes={}
    for k in PARENTS:
        v=t[k+"_id"].where(t[k+"_id"].ne(""))
        codes,unique=pd.factorize(v,sort=True)
        t[k+"_code"]=codes.astype(np.int64);sizes[k]=len(unique)
    t=t.sort_values(["day","race","horse"],kind="mergesort").reset_index(drop=True)
    return t,N,sizes

def register(labels,ids,codes):
    # Nonempty labels are learned only after their recorded date.
    # A conflict is quarantined forever; blank never becomes a shared parent.
    for h,k in zip(ids,codes):
        if k<0 or labels[h]==-2:continue
        if labels[h]==-1:labels[h]=k
        elif labels[h]!=k:labels[h]=-2

def parent_scores(labels,group_n,st,day,active):
    seen=st.starts>0
    if (st.last[seen]>=day).any():raise ValueError("HOLD_PARENT_FUTURE")
    valid=(labels>=0)&seen
    cur=st.global_rating[valid]*2.**(-(day-st.last[valid])/HALF_LIFE_DAYS)
    lab=labels[valid]
    totals=np.bincount(lab,weights=cur,minlength=group_n)
    counts=np.bincount(lab,minlength=group_n)
    lab=labels[active];known=lab>=0
    s=np.zeros(len(active));n=np.zeros(len(active),dtype=np.int64)
    ii=np.flatnonzero(known)
    h=active[ii]
    if len(h):
        own=st.starts[h]>0
        theta=st.global_rating[h]*2.**(-np.where(own,day-st.last[h],0)/HALF_LIFE_DAYS)
        s[ii]=totals[lab[ii]]-theta*own
        n[ii]=counts[lab[ii]]-own.astype(int)
    if (n<0).any() or not np.isfinite(s).all():raise ValueError("HOLD_FOCAL_EXCLUSION")
    same(s[n==0],0.,"NO_PEER_SIGNAL")
    # Shrink the earlier other-horse mean towards the common zero-rating anchor,
    # and reduce its potential weight as the focal's recorded starts accumulate.
    signal=s/(n+PARENT_SHRINK)*OWN_SHRINK/(st.starts[active]+OWN_SHRINK)
    return {"known":known.astype(float),"log_peers":np.log1p(n),"ability":signal,"peers":n}

def replay(t,N,sizes):
    st=State(N);labels={k:np.full(N,-1,dtype=np.int64) for k in PARENTS}
    panels={y:[] for y in (CAL,*TEST)}
    for day,d in t.groupby("day",sort=True,observed=True):
        yr=int(day.year);di=int(day.toordinal());ids=d.id.to_numpy(np.int64);active=np.unique(ids)
        if yr in panels:
            own=st.starts[active].copy()
            f={k:parent_scores(labels[k],sizes[k],st,di,active) for k in PARENTS}
        q=process_day(d,st,yr in panels)
        if q is not None:
            a=np.searchsorted(active,q.a.to_numpy(np.int64));b=np.searchsorted(active,q.b.to_numpy(np.int64))
            q["log_own"]=np.log1p(own[a])-np.log1p(own[b])
            q["min_starts"]=np.minimum(own[a],own[b]);q["max_starts"]=np.maximum(own[a],own[b])
            for k in PARENTS:
                for v in ("known","log_peers","ability"):
                    x=f[k][v];q[k+"_"+v]=x[a]-x[b]
                x=f[k]["peers"];q[k+"_both_supported"]=(x[a]>0)&(x[b]>0)
                q[k+"_either_supported"]=(x[a]>0)|(x[b]>0)
            q["either_parent_supported"]=q.sire_either_supported|q.dam_either_supported
            if not (q.loc[q.both_one_start,"max_starts"]==1).all():raise ValueError("HOLD_HISTORY_PARITY")
            panels[yr].append(q)
        for k in PARENTS:register(labels[k],ids,d[k+"_code"].to_numpy(np.int64))
    qa={k:{"known_final":int((v>=0).sum()),"conflict_quarantine_final":int((v==-2).sum()),
        "no_recorded_label_final":int((v==-1).sum()),"distinct_source_labels":int(sizes[k])} for k,v in labels.items()}
    return {y:pd.concat(panels[y],ignore_index=True) for y in panels},qa

def design(t,cols,scale=None):
    x=t[list(cols)].to_numpy(float)
    if not np.isfinite(x).all():raise ValueError("HOLD_NONFINITE")
    if scale is None:
        w=weights(t);scale=np.sqrt(np.average(x*x,axis=0,weights=w))
        scale=np.where(scale>1e-10,scale,1.)
    return x/scale,scale

def fit(t,cols):
    x,scale=design(t,cols);y=t.y.to_numpy(float);w=weights(t);w/=w.sum()
    def objective(b):
        z=x@b;res=expit(z)-y
        return float(np.sum(w*(np.logaddexp(0,z)-y*z))+.5*RIDGE*(b@b)),x.T@(w*res)+RIDGE*b
    r=minimize(objective,np.zeros(len(cols)),jac=True,method="L-BFGS-B",options={"maxiter":300,"ftol":1e-13,"gtol":1e-8})
    grad=float(np.max(np.abs(objective(r.x)[1])))
    if not r.success or grad>1e-5 or not np.isfinite(r.x).all():raise ValueError("HOLD_MODEL_FIT")
    return {"cols":list(cols),"scale":scale.tolist(),"beta":r.x.tolist(),"raw_scale_beta":(r.x/scale).tolist(),"max_abs_gradient":grad}

def predict(t,m):
    x,_=design(t,m["cols"],np.asarray(m["scale"]))
    return expit(x@np.asarray(m["beta"]))

def groupmask(t,g):
    q=t.connected&t["first"]
    if g==GROUPS[0]:return q&t.both_one_start
    if g==GROUPS[1]:return q&t.both_one_win
    if g==GROUPS[2]:return q
    if g==GROUPS[3]:return q&t.min_starts.ge(1)&t.max_starts.le(3)
    if g==GROUPS[4]:return q&t.min_starts.ge(4)
    raise ValueError("HOLD_GROUP")

def evaluate(t,fits,g):
    z=t.loc[groupmask(t,g)]
    if z.empty:return {"status":"HOLD_EMPTY","pairs":0}
    w=weights(z);y=z.y.to_numpy(float)
    pred={k:predict(z,m) for k,m in fits.items()}
    pred["daily_surface"]=expit(2*z.context.to_numpy(float))
    pred["daily_global"]=expit(2*z.graph.to_numpy(float))
    loss={k:(y-p)**2 for k,p in pred.items()}
    contrast={"family_signal_given_counts":loss["N"]-loss["F"],
        "family_count_given_own":loss["O"]-loss["N"],
        "family_all_given_own":loss["O"]-loss["F"],
        "family_model_vs_daily_surface":loss["daily_surface"]-loss["F"]}
    days=int(z.day.nunique());n=int(z.key.nunique())
    status="OBSERVED" if n>=MIN_PAIRS and days>=MIN_DAYS else "HOLD_SUPPORT"
    out={"status":status,"pairs":len(z),"distinct_pairs":n,"days":days,"races":int(z.race.nunique()),
        "horses":len(np.unique(np.r_[z.a,z.b])),
        "support":{k:int(z[k].sum()) for k in ("sire_both_supported","dam_both_supported","sire_either_supported","dam_either_supported","either_parent_supported")},
        "Brier":{k:float(np.average(v,weights=w)) for k,v in loss.items()},
        "accuracy":{k:float(np.average(np.where(p==.5,.5,((p>.5)==(y==1)).astype(float)),weights=w)) for k,p in pred.items()},
        "gain":{k:float(np.average(v,weights=w)) for k,v in contrast.items()}}
    if status=="OBSERVED":
        names=list(contrast)
        tab=pd.DataFrame({k:w*contrast[k] for k in names});tab["w"]=w;tab["day"]=z.day.to_numpy()
        a=tab.groupby("day",observed=True)[names+["w"]].sum().to_numpy()
        rng=np.random.default_rng(SEED);draw=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
        out["conditional_day_97_5_gain"]=dict(zip(names,np.quantile(draw[:,:-1]/draw[:,-1,None],[.0125,.9875],axis=0).T.tolist()))
    return out

def analyze(archive,receipt):
    prior=json.loads(receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw);del raw
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N,sizes=prepare_parents(old);del old
    v,qa=replay(t,N,sizes)
    orig={k:original_calibrate(v[CAL],k) for k in ("naive","graph","context")}
    for k in orig:
        ref=prior["calibration"][k]
        same(orig[k]["Brier"],ref["Brier"],"ORIGINAL_CALIBRATION");same(orig[k]["slope"],ref["slope"],"ORIGINAL_SLOPE")
    q=v[CAL].loc[groupmask(v[CAL],"first_meeting")]
    if len(q)!=217613:raise ValueError("HOLD_CALIBRATION_PARITY")
    fits={k:fit(q,cols) for k,cols in MODELS.items()}
    out={}
    for yr in TEST:
        r=original_evaluate(v[yr],orig);ref=prior["results"][str(yr)]
        for k in ("all_pairs","connected_pairs","first_pairs","first_connected_pairs","first_both_one_win_pairs_all","first_both_one_start_one_win_pairs_all"):
            same(r[k],ref[k],"ORIGINAL_DENOMINATOR")
        for k,a in r["groups"].items():
            b=ref["groups"][k];same(a["pairs"],b["pairs"],"ORIGINAL_GROUP")
            if "Brier" in a:same(list(a["Brier"].values()),list(b["Brier"].values()),"ORIGINAL_BRIER")
        out[str(yr)]={g:evaluate(v[yr],fits,g) for g in GROUPS}
    return {"status":"RETROSPECTIVE_DAILY_FAMILY_ABILITY_COMPLEMENT","source_sha256":SOURCE_SHA,
      "original_PR107_parity":True,"JRA_starts":len(t),"JRA_horses":N,"parent_QA":qa,
      "primary":"2021 first_both_one_start_one_win and first_both_one_win, F vs N",
      "calibration":{"year":CAL,"pairs":len(q),"ridge":RIDGE,"fits":fits},
      "results":out,"limits":["Parent labels learned from earlier recorded classified JRA rows; missing not grouped, conflicting prior labels quarantined. Not verified pedigree or genomic relationship.",
        "Other-horse current pre-day ratings share historical competitions with focal horses; excluding focal as donor does not make donor scores independent.",
        "Counts and prior labels controlled in nested model, but management, environment, deeper kin and selection remain.",
        "History-dependent shrinkage imposed; subgroup contrasts descriptive, no formal moderation or calibrated individual uncertainty.",
        "Same inspected archive and conditional date intervals omit shared horse/graph/fit dependence. No official debut, full entry census, absolute speed, causal genetics, prospective or wagering claim. No raw IDs exported."]}

def self_test():
    st=State(5);st.starts[:4]=[1,2,3,1];st.global_rating[:4]=[.4,.8,-.3,.2];st.last[:4]=10
    labels=np.array([0,0,1,-1,-1])
    x=parent_scores(labels,2,st,11,np.arange(5))
    decay=2.**(-1/HALF_LIFE_DAYS)
    assert x["peers"].tolist()==[1,1,0,0,0]
    same(x["ability"][0],.8*decay/9*5/6,"SIRE_EXCLUDE")
    same(x["ability"][1],.4*decay/9*5/7,"SIRE_EXCLUDE_2")
    same(x["ability"][2:],0.,"NO_PEER")
    register(labels,np.array([3,4,0]),np.array([1,-1,1]))
    assert labels.tolist()==[-2,0,1,1,-1]
    register(labels,np.array([0]),np.array([0]));assert labels[0]==-2
    # Feature signs reverse probabilities under pair reversal.
    t=pd.DataFrame({"race":["r"]*4+["s"]*4,"y":[1,0,1,0]*2})
    for k in BASE+COUNTS+SIGNAL:t[k]=[.4,-.4,.2,-.2]*2
    m=fit(t,MODELS["F"]);q=predict(t,m)
    same(q[0]+q[1],1.,"ANTISYMMETRY")
    print("Synthetic parent time, conflict, self exclusion, zero support and antisymmetry checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.output)):p.error("archive/receipt/output required")
    r=analyze(a.archive,a.receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
