#!/usr/bin/env python3
"""Compare parent ability with exactly support-matched other-horse donors.
Earlier classified JRA data only; no genetic causation or wagering."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import ecology_japan_family_depth_unconstrained as prev
import ecology_japan_context_novelty_family as ctx
from scipy.special import expit

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

def own_snapshot(st,day,ids,surface):
    # Exact pre-day state used by the original daily model, without mutation.
    elapsed=np.where(st.last[ids]<0,0,day-st.last[ids])
    if (elapsed<0).any() or (st.last[ids]>=day).any():raise ValueError("HOLD_OWN_SNAPSHOT_TIME")
    dec=2.**(-elapsed/prev.HALF_LIFE_DAYS)
    total=st.total[ids]*dec;count=st.count[ids]*dec
    p=(total+2.5)/(count+5.)
    return {"naive":np.log(p/(1-p)),"graph":st.global_rating[ids]*dec,
        "context":(st.context_global[ids]+st.surface[ids,surface])*dec,
        "total":total,"count":count}

def replay(t,N,sizes):
    st=prev.State(N);labels={k:np.full(N,-1,dtype=np.int64) for k in prev.PARENTS}
    panels={y:[] for y in (prev.CAL,*prev.TEST)};rngs=[np.random.default_rng(seed) for seed in SEEDS]
    for day,d in t.groupby("day",sort=True,observed=True):
        yr=int(day.year);di=int(day.toordinal());ids=d.id.to_numpy(np.int64);active=np.unique(ids)
        if yr in panels:
            own=st.starts[active].copy()
            f={k:prev.parent_scores(labels[k],sizes[k],st,di,active) for k in prev.PARENTS}
            scores,ok=match_day(st,labels,sizes,di,active,rngs,f)
            pre={k:own_snapshot(st,di,active,k) for k in (0,1)}
        q=prev.process_day(d,st,yr in panels)
        if q is not None:
            a=np.searchsorted(active,q.a.to_numpy(np.int64));b=np.searchsorted(active,q.b.to_numpy(np.int64))
            # Race-specific surface obtained from same-day race metadata only.
            sf=q.race.map(d.drop_duplicates("race").set_index("race").surface.astype(str)).map({"turf":0,"dirt":1})
            if sf.isna().any():raise ValueError("HOLD_SURFACE_JOIN")
            ksf=sf.to_numpy(int)
            for side,ix in (("a",a),("b",b)):
                for k in ("naive","graph","context","total","count"):
                    q[side+"_own_"+k]=np.where(ksf==0,pre[0][k][ix],pre[1][k][ix])
            for k in ("naive","graph","context"):
                prev.same(q["a_own_"+k]-q["b_own_"+k],q[k],"OWN_SCORE_PARITY")
            q["log_own"]=np.log1p(own[a])-np.log1p(own[b])
            q["a_total"]=own[a];q["b_total"]=own[b]
            q["min_starts"]=np.minimum(own[a],own[b]);q["max_starts"]=np.maximum(own[a],own[b])
            match=np.ones(len(q),bool)
            for k in prev.PARENTS:
                for v in ("known","log_peers","ability","raw_ability"):
                    x=f[k][v];q[k+"_"+v]=x[a]-x[b]
                x=f[k]["peers"];q[k+"_both_supported"]=(x[a]>0)&(x[b]>0)
                q[k+"_either_supported"]=(x[a]>0)|(x[b]>0)
                q[k+"_control_matched"]=ok[k][a]&ok[k][b]
                match&=q[k+"_control_matched"].to_numpy()
                x=f[k]["raw_ability"];q["a_"+k+"_true"]=x[a];q["b_"+k+"_true"]=x[b]
                q["a_"+k+"_peers"]=f[k]["peers"][a];q["b_"+k+"_peers"]=f[k]["peers"][b]
                for j in range(K):
                    q[k+"_alt_"+str(j)]=scores[k][a,j]-scores[k][b,j]
                    q["a_"+k+"_alt_"+str(j)]=scores[k][a,j]
                    q["b_"+k+"_alt_"+str(j)]=scores[k][b,j]
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

MAX_GAP=180
MIN_OPPONENTS=2
MIN_FOCALS=100
MIN_FOCAL_DAYS=30
FOCAL_METRICS=("specificity","actual_gain","alt_gain","fixed_early_gain","alignment","penalty")

def make_oriented(t,fit):
    # Only historically connected first meetings, all donor matches available.
    q=t.loc[t.connected&t["first"]&t.matched_control].copy()
    x,_=prev.design(q,fit["cols"],np.asarray(fit["scale"]))
    logits=x@np.asarray(fit["beta"])
    prev.same(expit(logits),prev.predict(q,fit),"U_SCORE")
    beta=dict(zip(fit["cols"],fit["raw_scale_beta"]))
    true={side:sum(beta[k+"_raw_ability"]*q[side+"_"+k+"_true"].to_numpy(float) for k in prev.PARENTS) for side in ("a","b")}
    expected=sum(beta[k+"_raw_ability"]*q[k+"_raw_ability"].to_numpy(float) for k in prev.PARENTS)
    prev.same(true["a"]-true["b"],expected,"SIGNED_FAMILY_SCORE")
    parts=[];y=q.y.to_numpy(float)
    for side,other,sign in (("a","b",1.),("b","a",-1.)):
        n=q[side+"_total"].to_numpy();r=q[other+"_total"].to_numpy()
        supported=np.logical_or.reduce([q[side+"_"+k+"_peers"].to_numpy()>0 for k in prev.PARENTS])
        keep=supported&(n>=1)&(r>=1)
        target=y if sign==1 else 1-y
        b=sign*logits-true[side];p0=expit(b);p1=expit(b+true[side])
        real=(target-p0)**2-(target-p1)**2;d=p1-p0
        align=2*(target-p0)*d;penalty=d*d
        prev.same(real,align-penalty,"ABLATION_IDENTITY")
        alt=[];alt_scores=[]
        for j in range(K):
            f=sum(beta[k+"_raw_ability"]*q[side+"_"+k+"_alt_"+str(j)].to_numpy(float) for k in prev.PARENTS)
            alt.append((target-p0)**2-(target-expit(b+f))**2)
            alt_scores.append(f)
        pg=np.column_stack(alt).mean(axis=1)
        v=pd.DataFrame({"focal":q[side].to_numpy(),"opponent":q[other].to_numpy(),"race":q.race.to_numpy(),
             "day":q.day.to_numpy(),"context":q.ctx.to_numpy(),"low":n<=3,
             "own_n":n,"rival_bin":np.where(r<=3,0,np.where(r<=7,1,np.where(r<=15,2,3))),
             "specificity":real-pg,"actual_gain":real,"alt_gain":pg,"alignment":align,"penalty":penalty,
             "target":target,"ablated_logit":b,"signed_parent":true[side]})
        for k in ("naive","graph","context","total","count"):
            v["own_"+k]=q[side+"_own_"+k].to_numpy(float)
        for j in range(K):v["alt_signal_"+str(j)]=alt_scores[j]
        parts.append(v.loc[keep])
    z=pd.concat(parts,ignore_index=True)
    if z.duplicated(["focal","opponent","race","day"]).any():raise ValueError("HOLD_DUPLICATE")
    return z

def select_matches(z):
    cols=["focal","race","day","context","low","own_n","rival_bin"]
    agg={k:(k,"mean") for k in ("specificity","actual_gain","alt_gain","alignment","penalty","signed_parent")}
    e=z.groupby(cols,observed=True).agg(n=("opponent","nunique"),**agg).reset_index()
    e=e.loc[e.n.ge(MIN_OPPONENTS)].sort_values(["focal","day","race","rival_bin"],kind="mergesort")
    out=[]
    for h,g in e.groupby("focal",observed=True,sort=True):
        low=g.loc[g.low];high=g.loc[~g.low]
        if low.empty or high.empty:continue
        # First eligible late event, nearest earlier low-depth event,
        # exact same context and opponent total-history bin, 1–180 days.
        for b in high.itertuples(index=False):
            a=low.loc[(low.day<b.day)&(low.day>=b.day-pd.Timedelta(days=MAX_GAP))&
                low.context.eq(b.context)&low.rival_bin.eq(b.rival_bin)]
            if a.empty:continue
            a=a.sort_values(["day","race"],ascending=[False,True],kind="mergesort").iloc[0]
            row={"focal":int(h),"low_day":a.day,"high_day":b.day,"low_race":a.race,"high_race":b.race,
                 "rival_bin":int(b.rival_bin),"gap":int((b.day-a.day).days),"low_n":int(a.n),"high_n":int(b.n),
                 "low_own_n":int(a.own_n),"high_own_n":int(b.own_n)}
            for k in ("specificity","actual_gain","alt_gain","alignment","penalty","signed_parent"):
                row["low_"+k]=float(a[k]);row["high_"+k]=float(getattr(b,k))
            out.append(row);break
    p=pd.DataFrame(out)
    if not p.empty and (p.focal.duplicated().any() or not p.gap.between(1,MAX_GAP).all() or
       not p.low_own_n.between(1,3).all() or not p.high_own_n.ge(4).all()):raise ValueError("HOLD_MATCH_ORDER")
    return p,{"oriented_pairs":len(z),"eligible_early_horses":int(e.loc[e.low].focal.nunique()),
         "eligible_late_horses":int(e.loc[~e.low].focal.nunique()),"eligible_early_event_bins":int(e.low.sum()),
         "eligible_late_event_bins":int((~e.low).sum())}

def carry_early(z,p):
    if p.empty:return p
    q=z.merge(p[["focal","high_day","high_race","rival_bin","low_signed_parent"]],
        left_on=["focal","day","race","rival_bin"],right_on=["focal","high_day","high_race","rival_bin"],
        how="inner",validate="many_to_one")
    if q.low.any():raise ValueError("HOLD_CARRY_LATE")
    y=q.target.to_numpy(float);b=q.ablated_logit.to_numpy(float)
    q["gain"]=(y-expit(b))**2-(y-expit(b+q.low_signed_parent.to_numpy(float)))**2
    a=q.groupby("focal",observed=True).agg(gain=("gain","mean"),n=("opponent","nunique"))
    if len(a)!=len(p):raise ValueError("HOLD_CARRY_HORSES")
    prev.same(a.n.reindex(p.focal).to_numpy(),p.high_n,"CARRY_COUNTS")
    p=p.copy();p["high_fixed_early_gain"]=a.gain.reindex(p.focal).to_numpy();p["low_fixed_early_gain"]=p.low_actual_gain
    return p

def focal_summary(p,qa):
    out={"status":"HOLD_EMPTY","candidate":qa,"matched_horses":len(p)}
    if p.empty:return out
    out.update(early_days=int(p.low_day.nunique()),late_days=int(p.high_day.nunique()),
       early_coverage=len(p)/qa["eligible_early_horses"],mean_gap_days=float(p.gap.mean()),
       mean_own_starts={"early":float(p.low_own_n.mean()),"late":float(p.high_own_n.mean())},
       mean_eligible_opponents={"early":float(p.low_n.mean()),"late":float(p.high_n.mean())},
       means={a:{k:float(p[b+"_"+k].mean()) for k in FOCAL_METRICS} for a,b in (("early","low"),("late","high"))})
    d=pd.DataFrame({k:p["low_"+k]-p["high_"+k] for k in FOCAL_METRICS})
    prev.same(d.specificity,d.actual_gain-d.alt_gain,"SPECIFICITY_IDENTITY")
    prev.same(d.actual_gain,d.alignment-d.penalty,"GAIN_DECOMP")
    out["early_minus_late"]={k:float(v) for k,v in d.mean().items()}
    if len(p)<MIN_FOCALS or min(out["early_days"],out["late_days"])<MIN_FOCAL_DAYS:
        out["status"]="HOLD_SUPPORT";return out
    out["status"]="OBSERVED_CONDITIONAL";out["conditional_97_5"]={}
    for axis in ("focal","low_day","high_day"):
        a=d.copy();a["group"]=p[axis].to_numpy();a["n"]=1
        b=a.groupby("group",observed=True)[list(FOCAL_METRICS)+["n"]].sum().to_numpy()
        rng=np.random.default_rng(SEEDS[0]);draw=b[rng.integers(len(b),size=(prev.DRAWS,len(b)))].sum(axis=1)
        out["conditional_97_5"][axis]=dict(zip(FOCAL_METRICS,np.quantile(draw[:,:-1]/draw[:,-1,None],[.0125,.9875],axis=0).T.tolist()))
    return out


ROLLBACK_METRICS=("specificity_rollback_minus_current","actual_gain_rollback_minus_current",
                  "specificity_current_parent_rollback_minus_current",
                  "ablated_loss_rollback_minus_current","full_loss_rollback_minus_current")

def rollback(z,p,fit):
    if p.empty:return {"status":"HOLD_EMPTY","matched_horses":0}
    cols=["focal","day","race","rival_bin"]
    keys=["focal","rival_bin"]
    early=p[["focal","low_day","low_race","rival_bin","low_n"]]
    e=z.merge(early,left_on=cols,right_on=["focal","low_day","low_race","rival_bin"],how="inner",validate="many_to_one")
    if not e.low.all():raise ValueError("HOLD_EARLY_ORIENTATION")
    features=["own_naive","own_graph","own_context","own_total","own_count","signed_parent"]+["alt_signal_"+str(j) for j in range(K)]
    by=e.groupby("focal",observed=True)
    for k in features:
        prev.same(by[k].max(),by[k].min(),"EARLY_FOCAL_CONSTANT")
    anc=by[features].first().add_prefix("early_").reset_index()
    prev.same(by.opponent.nunique().reindex(p.focal).to_numpy(),p.low_n,"EARLY_OPPONENTS")
    h=z.merge(p[["focal","high_day","high_race","rival_bin","gap","high_n","low_day"]],
        left_on=cols,right_on=["focal","high_day","high_race","rival_bin"],how="inner",validate="many_to_one")
    h=h.merge(anc,on="focal",validate="many_to_one")
    if h.low.any() or not (h.low_day<h.day).all():raise ValueError("HOLD_TARGET_ORDER")
    prev.same(h.groupby("focal").opponent.nunique().reindex(p.focal).to_numpy(),p.high_n,"LATE_OPPONENTS")
    beta=dict(zip(fit["cols"],fit["raw_scale_beta"]))
    y=h.target.to_numpy(float);b=h.ablated_logit.to_numpy(float)
    dec=2.**(-h.gap.to_numpy(float)/prev.HALF_LIFE_DAYS)
    old_total=h.early_own_total.to_numpy(float)*dec;old_count=h.early_own_count.to_numpy(float)*dec
    a=(old_total+2.5)/(old_count+5.)
    naive=np.log(a/(1-a))
    earlier={"naive":naive,"graph":h.early_own_graph.to_numpy(float)*dec,"context":h.early_own_context.to_numpy(float)*dec}
    shift=sum(beta[k]*(earlier[k]-h["own_"+k].to_numpy(float)) for k in earlier)
    rb=b+shift
    # Same late target and rival, both models use exactly the same fixed EARLY
    # focal actual and alternate parent-score vector. Counts stay current.
    def gain(base,actual,alts):
        p0=expit(base);p1=expit(base+actual)
        l0=(y-p0)**2;l1=(y-p1)**2
        la=np.column_stack([(y-expit(base+v))**2 for v in alts]).mean(axis=1)
        return l0-l1,la-l1,l0,l1
    actual=h.early_signed_parent.to_numpy(float)
    alts=[h["early_alt_signal_"+str(j)].to_numpy(float) for j in range(K)]
    g,s,l0,l1=gain(b,actual,alts);rg,rs,rl0,rl1=gain(rb,actual,alts)
    current=h.signed_parent.to_numpy(float);ca=[h["alt_signal_"+str(j)].to_numpy(float) for j in range(K)]
    cg,cs,_,_=gain(b,current,ca);crg,crs,_,_=gain(rb,current,ca)
    prev.same(cg,h.actual_gain,"LATE_ACTUAL_PARITY");prev.same(cs,h.specificity,"LATE_SPECIFICITY_PARITY")
    h["specificity_current"]=s;h["specificity_rollback"]=rs
    h["actual_gain_current"]=g;h["actual_gain_rollback"]=rg
    h["specificity_rollback_minus_current"]=rs-s
    h["actual_gain_rollback_minus_current"]=rg-g
    h["specificity_current_parent_rollback_minus_current"]=crs-cs
    h["ablated_loss_rollback_minus_current"]=rl0-l0
    h["full_loss_rollback_minus_current"]=rl1-l1
    h["abs_logit_shift"]=np.abs(shift)
    cols2=["specificity_current","specificity_rollback","actual_gain_current","actual_gain_rollback","abs_logit_shift",*ROLLBACK_METRICS]
    agg=h.groupby("focal",observed=True)[cols2].mean().reindex(p.focal)
    if agg.isna().any().any():raise ValueError("HOLD_AGGREGATE")
    prev.same(agg.actual_gain_current,p.high_fixed_early_gain.to_numpy(),"PR117_CARRY_PARITY")
    out={"status":"HOLD_SUPPORT","matched_horses":len(p),"late_dates":int(p.high_day.nunique()),"early_dates":int(p.low_day.nunique()),
      "means":{k:float(v) for k,v in agg.mean().items()}}
    if len(p)<MIN_FOCALS or min(out["late_dates"],out["early_dates"])<MIN_FOCAL_DAYS:return out
    out["status"]="OBSERVED_CONDITIONAL";out["conditional_97_5"]={}
    for axis in ("focal","low_day","high_day"):
        tab=agg[list(ROLLBACK_METRICS)].reset_index(drop=True);tab["group"]=p[axis].to_numpy();tab["n"]=1
        a=tab.groupby("group",observed=True)[list(ROLLBACK_METRICS)+["n"]].sum().to_numpy()
        rng=np.random.default_rng(SEEDS[0]);draw=a[rng.integers(len(a),size=(prev.DRAWS,len(a)))].sum(axis=1)
        out["conditional_97_5"][axis]=dict(zip(ROLLBACK_METRICS,np.quantile(draw[:,:-1]/draw[:,-1,None],[.0125,.9875],axis=0).T.tolist()))
    return out

def analyze(archive,receipt,matched_receipt,focal_receipt):
    ref=json.loads(receipt.read_text())["result"]
    matched_ref=json.loads(matched_receipt.read_text())["result"]
    focal_ref=json.loads(focal_receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=prev.SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:raw=pd.read_csv(f,usecols=prev.COLS,dtype=str,keep_default_na=False)
    src,_=prev.prepare_frame(raw);del raw
    if len(src)!=2092836 or src.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N,sizes=prev.prepare_parents(src);del src
    v,qa=replay(t,N,sizes)
    h=ctx.context_history(t);del t
    for yr in (prev.CAL,*prev.TEST):v[yr]=ctx.attach(v[yr],h.loc[h.day.dt.year.eq(yr)])
    del h
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
    prev.same(len(z),matched_ref["calibration"]["pairs"],"PR116_CALIBRATION")
    for k,m in fits.items():
        r=matched_ref["calibration"]["fits"][k]
        if m["cols"]!=r["cols"]:raise ValueError("HOLD_PR116_FEATURES")
        for field in ("scale","beta"):prev.same(m[field],r[field],"PR116_"+field)
    for yr in prev.TEST:
        groups={g:summary(v[yr],g,fits) for g in GROUPS}
        depth=depth_contrast(v[yr],fits,groups)
        r=matched_ref["results"][str(yr)]
        for g,a in groups.items():
            b=r["groups"][g]
            if a["status"]!=b["status"]:raise ValueError("HOLD_PR116_STATUS")
            for k in ("denominator","matched_pairs","coverage"):prev.same(a[k],b[k],"PR116_SUPPORT")
            for k in b["Brier"]:prev.same(a["Brier"][k],b["Brier"][k],"PR116_BRIER")
            for k in b["gains"]:prev.same(a["gains"][k],b["gains"][k],"PR116_GAIN")
        for k in r["depth_contrast"]["low_minus_high"]:
            prev.same(depth["low_minus_high"][k],r["depth_contrast"]["low_minus_high"][k],"PR116_DEPTH")
        zz=make_oriented(v[yr],fits["U"]);p,support=select_matches(zz)
        p=carry_early(zz,p)
        original=focal_summary(p,support);r=focal_ref["results"][str(yr)]["within_focal"]
        if original["status"]!=r["status"] or original["candidate"]!=r["candidate"]:raise ValueError("HOLD_PR117_SUPPORT")
        for k in ("matched_horses","early_days","late_days","mean_gap_days","early_coverage"):prev.same(original[k],r[k],"PR117_"+k)
        for arm in ("early","late"):
            for k,val in r["means"][arm].items():prev.same(original["means"][arm][k],val,"PR117_MEANS")
        for axis,intervals in r["conditional_97_5"].items():
            for k,interval in intervals.items():prev.same(original["conditional_97_5"][axis][k],interval,"PR117_INTERVAL")
        out[str(yr)]={"original_within_focal":original,"rollback":rollback(zz,p,fits["U"])}
    return {"status":"RETROSPECTIVE_FIXED_TARGET_OWN_SCORE_ROLLBACK","source_sha256":prev.SOURCE_SHA,"original_PR111_parity":True,"original_PR116_parity":True,"original_PR117_parity":True,
       "primary":"2021 fixed late target, earlier-own-score rollback minus current specificity, fixed early focal parent and alternate scores",
       "seeds":list(SEEDS),"calibration":{"pairs":len(z),"all_pairs":len(q),"coverage":coverage,"fits":fits},
       "results":out,"limits":["Controls share neither recorded direct parent with focal; deeper relatedness unknown.",
       "Exact matching within coarse observed start-count and recency bins, same distinct peer count and shrinkage. Control groups randomly assembled, not natural families.",
       "All models refitted on the same supported 2019 pairs; original full-sample PR111 fits reproduced separately.",
       "Parent information may proxy management, ancestry, age, selection and shared competition; no causal inheritance inference.",
       "Fixed late target rollback changes only focal naive/global/surface performance-score terms, not current count, rival or focal parent terms. Earlier snapshot is passively decayed; no simulated retraining or causal counterfactual. Conditional separate-axis intervals omit crossed dependence. No prospective or official career claims, no raw export."]}

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
    rows=[]
    for j in range(110):
        day=pd.Timestamp("2021-01-01")+pd.Timedelta(days=j%40)
        for low,dt,n,ga,pa in ((True,0,2,.02,.005),(False,40,5,.008,.003)):
            for op in (0,1):
                rows.append({"focal":j,"opponent":1000+2*j+op,"race":f"{j}-{low}","day":day+pd.Timedelta(days=dt),"context":"turf:4",
                  "low":low,"own_n":n,"rival_bin":1,"specificity":ga-pa,"actual_gain":ga,"alt_gain":pa,"alignment":ga+.001,"penalty":.001,
                  "signed_parent":.1,"target":1.,"ablated_logit":0.})
    zz=pd.DataFrame(rows);p,qa=select_matches(zz);assert len(p)==110
    p=carry_early(zz,p);r=focal_summary(p,qa)
    assert r["status"]=="OBSERVED_CONDITIONAL"
    prev.same(r["early_minus_late"]["specificity"],.01,"MATCH_TEST")
    prev.same(p.high_fixed_early_gain,.25-(1-expit(.1))**2,"CARRY_TEST")
    zz.loc[~zz.low,"context"]="dirt:4";p,_=select_matches(zz);assert p.empty
    # Snapshot parity with the exact original pre-day state.
    st=prev.State(2);st.last[:]=10;st.starts[:]=2;st.total[:]=[1.4,.7];st.count[:]=2
    st.global_rating[:]=[.2,-.3];st.context_global[:]=[.1,.4];st.surface[:]=[[.1,-.2],[.2,-.1]]
    snap=own_snapshot(st,11,np.array([0,1]),0)
    dec=2.**(-1/prev.HALF_LIFE_DAYS)
    prev.same(snap["graph"],np.array([.2,-.3])*dec,"TEST_OWN_SNAPSHOT")
    prev.same(snap["context"],np.array([.2,.6])*dec,"TEST_CONTEXT_SNAPSHOT")
    print("Synthetic donor matching, fixed-target snapshot and prior-state checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--matched-receipt",type=Path);p.add_argument("--focal-receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.matched_receipt,a.focal_receipt,a.output)):p.error("archive/receipt/output required")
    r=analyze(a.archive,a.receipt,a.matched_receipt,a.focal_receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
