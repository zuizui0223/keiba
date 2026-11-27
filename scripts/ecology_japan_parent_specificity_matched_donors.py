#!/usr/bin/env python3
"""Compare parent ability with exactly support-matched other-horse donors.
Earlier classified JRA data only; no genetic causation or wagering."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import ecology_japan_family_depth_unconstrained as prev

SEEDS=(20261127,20261128,20261129)
MIN_COVERAGE=.50
K=len(SEEDS)
LOW,HIGH=prev.GROUPS[3:5]
GROUPS=prev.GROUPS
CONTROL_NAMES=tuple("P"+str(i) for i in range(K))
NAMES=("N","U",*CONTROL_NAMES)
CONTRASTS=("actual_vs_count","mean_control_vs_actual")

def cell_ids(st,day):
    # Donor experience and time since last recorded start, fixed coarse bins.
    starts=np.searchsorted([1,3,7,15],st.starts,side="left")
    recency=np.searchsorted([90,365,730],day-st.last,side="left")
    return 4*starts+recency

def match_day(st,labels,sizes,day,active,rngs,f):
    seen=st.starts>0
    if (st.last[seen]>=day).any():raise ValueError("HOLD_DONOR_TIME")
    cell=cell_ids(st,day)
    cur=np.zeros(st.n)
    cur[seen]=st.global_rating[seen]*2.**(-(day-st.last[seen])/prev.HALF_LIFE_DAYS)
    both=seen&(labels["sire"]>=0)&(labels["dam"]>=0)
    pools=[np.flatnonzero(both&(cell==k)) for k in range(20)]
    groups={}
    for channel in prev.PARENTS:
        lab=labels[channel]
        ids=np.flatnonzero(seen&(lab>=0))
        order=np.argsort(lab[ids],kind="stable");ids=ids[order]
        split=np.flatnonzero(np.diff(lab[ids]))+1
        groups[channel]={int(lab[g[0]]):g for g in np.split(ids,split) if len(g)}
    scores={channel:np.zeros((len(active),K)) for channel in prev.PARENTS}
    ok={channel:np.zeros(len(active),bool) for channel in prev.PARENTS}
    for r,h in enumerate(active):
        h=int(h)
        if not both[h]:continue
        # Cache the actual eligible alternate pool per cell/focal, never
        # select based on rating or target outcome.
        allowed={}
        for channel in prev.PARENTS:
            donor=groups[channel][int(labels[channel][h])]
            donor=donor[donor!=h]
            n=len(donor)
            if n!=f[channel]["peers"][r]:raise ValueError("HOLD_TRUE_COUNT")
            prev.same(cur[donor].sum()/(n+prev.PARENT_SHRINK),f[channel]["raw_ability"][r],"TRUE_SIGNAL")
            demand=np.bincount(cell[donor],minlength=20)
            need=np.flatnonzero(demand)
            feasible=True
            for k in need:
                if k not in allowed:
                    pool=pools[k]
                    allowed[k]=pool[(pool!=h)&(labels["sire"][pool]!=labels["sire"][h])&(labels["dam"][pool]!=labels["dam"][h])]
                if len(allowed[k])<demand[k]:feasible=False;break
            if not feasible:continue
            sums=np.zeros(K)
            for k in need:
                pool=allowed[k];n_k=int(demand[k])
                for j,rng in enumerate(rngs):
                    take=rng.choice(pool,size=n_k,replace=False)
                    if len(np.unique(take))!=n_k or not (cell[take]==k).all() or (labels["sire"][take]==labels["sire"][h]).any() or (labels["dam"][take]==labels["dam"][h]).any():
                        raise ValueError("HOLD_CONTROL_SUPPORT")
                    sums[j]+=cur[take].sum()
            scores[channel][r]=sums/(n+prev.PARENT_SHRINK)
            ok[channel][r]=True
    return scores,ok

def replay(t,N,sizes):
    st=prev.State(N);labels={k:np.full(N,-1,dtype=np.int64) for k in prev.PARENTS}
    panels={y:[] for y in (prev.CAL,*prev.TEST)};rngs=[np.random.default_rng(seed) for seed in SEEDS]
    for day,d in t.groupby("day",sort=True,observed=True):
        yr=int(day.year);di=int(day.toordinal());ids=d.id.to_numpy(np.int64);active=np.unique(ids)
        if yr in panels:
            own=st.starts[active].copy()
            f={k:prev.parent_scores(labels[k],sizes[k],st,di,active) for k in prev.PARENTS}
            scores,ok=match_day(st,labels,sizes,di,active,rngs,f)
        q=prev.process_day(d,st,yr in panels)
        if q is not None:
            a=np.searchsorted(active,q.a.to_numpy(np.int64));b=np.searchsorted(active,q.b.to_numpy(np.int64))
            q["log_own"]=np.log1p(own[a])-np.log1p(own[b])
            q["min_starts"]=np.minimum(own[a],own[b]);q["max_starts"]=np.maximum(own[a],own[b])
            match=np.ones(len(q),bool)
            for k in prev.PARENTS:
                for v in ("known","log_peers","ability","raw_ability"):
                    x=f[k][v];q[k+"_"+v]=x[a]-x[b]
                x=f[k]["peers"];q[k+"_both_supported"]=(x[a]>0)&(x[b]>0)
                q[k+"_either_supported"]=(x[a]>0)|(x[b]>0)
                q[k+"_control_matched"]=ok[k][a]&ok[k][b]
                match&=q[k+"_control_matched"].to_numpy()
                for j in range(K):q[k+"_alt_"+str(j)]=scores[k][a,j]-scores[k][b,j]
            q["either_parent_supported"]=q.sire_either_supported|q.dam_either_supported
            q["matched_control"]=match
            if not (q.loc[q.both_one_start,"max_starts"]==1).all():raise ValueError("HOLD_HISTORY_PARITY")
            panels[yr].append(q)
        for k in prev.PARENTS:prev.register(labels[k],ids,d[k+"_code"].to_numpy(np.int64))
    qa={k:{"known_final":int((v>=0).sum()),"conflict_quarantine_final":int((v==-2).sum()),
        "no_recorded_label_final":int((v==-1).sum()),"distinct_source_labels":int(sizes[k])} for k,v in labels.items()}
    return {y:pd.concat(panels[y],ignore_index=True) for y in panels},qa

def model_columns():
    m={k:prev.MODELS[k] for k in ("N","U")}
    for j,k in enumerate(CONTROL_NAMES):
        m[k]=prev.BASE+prev.COUNTS+tuple(ch+"_alt_"+str(j) for ch in prev.PARENTS)
    return m

def matched(t,g):
    z=t.loc[prev.groupmask(t,g)].copy()
    return z,z.loc[z.matched_control].copy()

def losses(z,fits):
    y=z.y.to_numpy(float)
    l={k:(y-prev.predict(z,m))**2 for k,m in fits.items()}
    avg=np.column_stack([l[k] for k in CONTROL_NAMES]).mean(axis=1)
    d=np.column_stack([l["N"]-l["U"],avg-l["U"]])
    return l,d

def summary(t,g,fits):
    all_,z=matched(t,g)
    r={"denominator":len(all_),"matched_pairs":len(z),"coverage":len(z)/len(all_) if len(all_) else 0.,
       "sire_matched_pairs":int(all_.sire_control_matched.sum()),"dam_matched_pairs":int(all_.dam_control_matched.sum())}
    if z.empty:r["status"]="HOLD_EMPTY";return r
    l,d=losses(z,fits);w=prev.weights(z);days=int(z.day.nunique());pairs=int(z.key.nunique())
    r.update(days=days,distinct_pairs=pairs,races=int(z.race.nunique()),horses=len(np.unique(np.r_[z.a,z.b])),
        Brier={k:float(np.average(v,weights=w)) for k,v in l.items()},
        gains=dict(zip(CONTRASTS,np.average(d,weights=w,axis=0).tolist())),
        individual_control_minus_actual={k:float(np.average(l[k]-l["U"],weights=w)) for k in CONTROL_NAMES})
    if r["coverage"]<MIN_COVERAGE or pairs<prev.MIN_PAIRS or days<prev.MIN_DAYS:
        r["status"]="HOLD_SUPPORT";return r
    tab=pd.DataFrame(d*w[:,None],columns=CONTRASTS);tab["w"]=w;tab["day"]=z.day.to_numpy()
    a=tab.groupby("day",observed=True)[list(CONTRASTS)+["w"]].sum().to_numpy()
    rng=np.random.default_rng(SEEDS[0]);draw=a[rng.integers(len(a),size=(prev.DRAWS,len(a)))].sum(axis=1)
    r["status"]="OBSERVED_CONDITIONAL"
    r["conditional_day_97_5"]=dict(zip(CONTRASTS,np.quantile(draw[:,:2]/draw[:,2,None],[.0125,.9875],axis=0).T.tolist()))
    return r

def depth_contrast(t,fits,groups):
    if any(groups[g]["status"]!="OBSERVED_CONDITIONAL" for g in (LOW,HIGH)):
        return {"status":"HOLD_SUPPORT"}
    dates=pd.Index(sorted(t.day.unique()));a=[]
    for g in (LOW,HIGH):
        _,z=matched(t,g);_,d=losses(z,fits);w=prev.weights(z)
        tab=pd.DataFrame(d*w[:,None],columns=CONTRASTS);tab["w"]=w;tab["day"]=z.day.to_numpy()
        a.append(tab.groupby("day",observed=True)[list(CONTRASTS)+["w"]].sum().reindex(dates,fill_value=0).to_numpy())
    def avg(x):return x[...,:2]/x[...,2,None]
    low,high=a;diff=avg(low.sum(axis=0))-avg(high.sum(axis=0))
    rng=np.random.default_rng(SEEDS[0]);ix=rng.integers(len(dates),size=(prev.DRAWS,len(dates)))
    l=low[ix].sum(axis=1);h=high[ix].sum(axis=1)
    if (l[:,2]<=0).any() or (h[:,2]<=0).any():return {"status":"HOLD_BOOTSTRAP_SUPPORT"}
    draw=avg(l)-avg(h)
    return {"status":"OBSERVED_CONDITIONAL","low_minus_high":dict(zip(CONTRASTS,diff.tolist())),
      "conditional_day_97_5":dict(zip(CONTRASTS,np.quantile(draw,[.0125,.9875],axis=0).T.tolist()))}

def analyze(archive,receipt):
    ref=json.loads(receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=prev.SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:raw=pd.read_csv(f,usecols=prev.COLS,dtype=str,keep_default_na=False)
    src,_=prev.prepare_frame(raw);del raw
    if len(src)!=2092836 or src.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N,sizes=prev.prepare_parents(src);del src
    v,qa=replay(t,N,sizes);del t
    if qa!=ref["parent_QA"]:raise ValueError("HOLD_PARENT_QA")
    q=v[prev.CAL].loc[prev.groupmask(v[prev.CAL],"first_meeting")]
    if len(q)!=ref["calibration"]["pairs"]:raise ValueError("HOLD_CALIBRATION_COUNT")
    full={k:prev.fit(q,cols) for k,cols in prev.MODELS.items()}
    for k,m in full.items():
        r=ref["calibration"]["fits"][k]
        if m["cols"]!=r["cols"]:raise ValueError("HOLD_FEATURES")
        for field in ("scale","beta"):prev.same(m[field],r[field],"PR111_"+field)
    out={}
    for yr in prev.TEST:
        for g in GROUPS:
            a=prev.evaluate(v[yr],full,g);r=ref["results"][str(yr)]["groups"][g]
            prev.same(a["pairs"],r["pairs"],"PR111_PAIRS")
            for k in r["Brier"]:prev.same(a["Brier"][k],r["Brier"][k],"PR111_BRIER")
            for k in r["gain"]:prev.same(a["gain"][k],r["gain"][k],"PR111_GAIN")
            if a["support"]!=r["support"]:raise ValueError("HOLD_PR111_SUPPORT")
    z=q.loc[q.matched_control]
    coverage=len(z)/len(q)
    if coverage<MIN_COVERAGE or z.key.nunique()<prev.MIN_PAIRS or z.day.nunique()<prev.MIN_DAYS:
        return {"status":"HOLD_MATCHED_CALIBRATION","original_PR111_parity":True,"calibration_pairs":len(z),"all_calibration_pairs":len(q),"coverage":coverage}
    fits={k:prev.fit(z,cols) for k,cols in model_columns().items()}
    for yr in prev.TEST:
        groups={g:summary(v[yr],g,fits) for g in GROUPS}
        out[str(yr)]={"groups":groups,"depth_contrast":depth_contrast(v[yr],fits,groups)}
    return {"status":"RETROSPECTIVE_MATCHED_PARENT_SPECIFICITY","source_sha256":prev.SOURCE_SHA,"original_PR111_parity":True,
       "primary":"2021 all-first mean control minus actual loss, and low-minus-high specificity",
       "seeds":list(SEEDS),"calibration":{"pairs":len(z),"all_pairs":len(q),"coverage":coverage,"fits":fits},
       "results":out,"limits":["Controls share neither recorded direct parent with focal; deeper relatedness unknown.",
       "Exact matching within coarse observed start-count and recency bins, same distinct peer count and shrinkage. Control groups randomly assembled, not natural families.",
       "All models refitted on the same supported 2019 pairs; original full-sample PR111 fits reproduced separately.",
       "Parent information may proxy management, ancestry, age, selection and shared competition; no causal inheritance inference.",
       "Same inspected archive, conditional date bootstrap ignores crossed horse, parent, donor-draw and fit dependence. No prospective or official career claims, no raw export."]}

def self_test():
    st=prev.State(8);st.starts[:]=2;st.last[:]=10
    st.global_rating[:]=[.1,.4,-.3,.2,.6,-.1,.7,.5]
    labels={"sire":np.array([0,0,1,1,2,2,3,3]),"dam":np.array([0,1,0,1,2,2,3,3])}
    sizes={"sire":4,"dam":4};active=np.array([0,1])
    f={k:prev.parent_scores(labels[k],sizes[k],st,11,active) for k in prev.PARENTS}
    r,ok=match_day(st,labels,sizes,11,active,[np.random.default_rng(j) for j in SEEDS],f)
    assert all(x.all() for x in ok.values())
    assert all(x.shape==(2,K) for x in r.values())
    # True donor 1 shares sire, 2 shares dam; neither is an eligible control.
    eligible=np.array([3,4,5,6,7]);vals=st.global_rating[eligible]*2.**(-1/prev.HALF_LIFE_DAYS)/9
    for k in prev.PARENTS:assert np.isclose(r[k][0,:,None],vals[None,:]).any(axis=1).all()
    st.starts[3:]=20
    f={k:prev.parent_scores(labels[k],sizes[k],st,11,np.array([0])) for k in prev.PARENTS}
    _,ok=match_day(st,labels,sizes,11,np.array([0]),[np.random.default_rng(j) for j in SEEDS],f)
    assert not any(x.any() for x in ok.values())
    print("Synthetic matched count/recency support, recorded-parent exclusion and sparse HOLD passed")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.output)):p.error("archive/receipt/output required")
    r=analyze(a.archive,a.receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
