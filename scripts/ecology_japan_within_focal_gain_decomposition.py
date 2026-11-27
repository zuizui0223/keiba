#!/usr/bin/env python3
"""Within-focal observed context novelty and parent-score ablation.
No causal biological inference or raw exports."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
import ecology_japan_context_novelty_family as ctx
prev=ctx.prev

MAX_GAP=120
MIN_OPPONENTS=2
MIN_HORSES=100
MIN_DATES=30
DRAWS=999
SEED=20261127
METRICS=("focal_gain","pair_gain","alignment","penalty")

def replay(t,N,sizes):
    # Same PR111 pre-day replay with individual signal/count columns retained
    # privately so the focal contribution can be ablated without removing the rival.
    st=prev.State(N);labels={k:np.full(N,-1,dtype=np.int64) for k in prev.PARENTS}
    panels={y:[] for y in (prev.CAL,*prev.TEST)}
    for day,d in t.groupby("day",sort=True,observed=True):
        yr=int(day.year);di=int(day.toordinal());ids=d.id.to_numpy(np.int64);active=np.unique(ids)
        if yr in panels:
            own=st.starts[active].copy()
            f={k:prev.parent_scores(labels[k],sizes[k],st,di,active) for k in prev.PARENTS}
        q=prev.process_day(d,st,yr in panels)
        if q is not None:
            a=np.searchsorted(active,q.a.to_numpy(np.int64));b=np.searchsorted(active,q.b.to_numpy(np.int64))
            q["log_own"]=np.log1p(own[a])-np.log1p(own[b])
            q["a_total"]=own[a];q["b_total"]=own[b]
            q["min_starts"]=np.minimum(own[a],own[b]);q["max_starts"]=np.maximum(own[a],own[b])
            for k in prev.PARENTS:
                for v in ("known","log_peers","ability","raw_ability"):
                    x=f[k][v];q[k+"_"+v]=x[a]-x[b]
                x=f[k]["raw_ability"];q["a_"+k+"_raw_ability"]=x[a];q["b_"+k+"_raw_ability"]=x[b]
                n=f[k]["peers"];q[k+"_both_supported"]=(n[a]>0)&(n[b]>0)
                q[k+"_either_supported"]=(n[a]>0)|(n[b]>0)
                q["a_"+k+"_peers"]=n[a];q["b_"+k+"_peers"]=n[b]
            q["either_parent_supported"]=q.sire_either_supported|q.dam_either_supported
            if not (q.loc[q.both_one_start,"max_starts"]==1).all():raise ValueError("HOLD_HISTORY_PARITY")
            panels[yr].append(q)
        for k in prev.PARENTS:prev.register(labels[k],ids,d[k+"_code"].to_numpy(np.int64))
    qa={k:{"known_final":int((v>=0).sum()),"conflict_quarantine_final":int((v==-2).sum()),
        "no_recorded_label_final":int((v==-1).sum()),"distinct_source_labels":int(sizes[k])} for k,v in labels.items()}
    return {y:pd.concat(panels[y],ignore_index=True) for y in panels},qa

def depth(n):
    return np.where(n<=7,0,np.where(n<=15,1,2))

def oriented(t,fits):
    q=t.loc[t.connected&t["first"]&t.min_starts.ge(4)].copy()
    m=fits["V"]
    x,_=prev.design(q,m["cols"],np.asarray(m["scale"]))
    logits=x@np.asarray(m["beta"])
    p=expit(logits);y=q.y.to_numpy(float)
    prev.same(p,prev.predict(q,m),"V_PREDICT")
    pair_gain=(y-prev.predict(q,fits["C"]))**2-(y-p)**2
    raw_beta=dict(zip(m["cols"],m["raw_scale_beta"]))
    parts=[]
    scores={side:sum(raw_beta[k+"_raw_ability"]*q[side+"_"+k+"_raw_ability"].to_numpy(float) for k in prev.PARENTS) for side in ("a","b")}
    expected=sum(raw_beta[k+"_raw_ability"]*q[k+"_raw_ability"].to_numpy(float) for k in prev.PARENTS)
    prev.same(scores["a"]-scores["b"],expected,"FOCAL_SIGNAL_DIFFERENCE")
    for side,other,sign in (("a","b",1.),("b","a",-1.)):
        n=q[side+"_ctx_n"].to_numpy();r=q[other+"_ctx_n"].to_numpy()
        supported=np.logical_or.reduce([q[side+"_"+k+"_peers"].to_numpy()>0 for k in prev.PARENTS])
        keep=((n==0)|(n>=3))&(r>=3)&supported
        target=y if sign==1 else 1-y
        z=sign*logits
        full=expit(z);ablated=expit(z-scores[side])
        g=(target-ablated)**2-(target-full)**2
        d=full-ablated
        alignment=2*(target-ablated)*d;penalty=d*d
        prev.same(g,alignment-penalty,"GAIN_IDENTITY")
        v=pd.DataFrame({"focal":q[side].to_numpy(),"opponent":q[other].to_numpy(),
            "race":q.race.to_numpy(),"day":q.day.to_numpy(),"context":q.ctx.to_numpy(),
            "novel":n==0,"focal_depth":depth(q[side+"_total"].to_numpy()),
            "opponent_depth":depth(q[other+"_total"].to_numpy()),
            "focal_gain":g,"pair_gain":pair_gain,
            "full_loss":(target-full)**2,"ablated_loss":(target-ablated)**2,
            "focal_signal_abs":np.abs(scores[side]),"focal_signal":scores[side],
            "alignment":alignment,"penalty":penalty,"target":target,"ablated_logit":z-scores[side]})
        parts.append(v.loc[keep])
    z=pd.concat(parts,ignore_index=True)
    if z.duplicated(["focal","opponent","race","day"]).any():raise ValueError("HOLD_DUPLICATE_ORIENTATION")
    return z

def choose_events(z):
    # Match opponents by total-experience bin; choose events by date and IDs,
    # never using prediction losses or rank to select a matched event.
    cols=["focal","race","day","context","novel","focal_depth","opponent_depth"]
    agg={k:(k,"mean") for k in (*METRICS,"full_loss","ablated_loss","focal_signal_abs","focal_signal")}
    e=z.groupby(cols,observed=True).agg(n=("opponent","nunique"),**agg).reset_index()
    e=e.loc[e.n.ge(MIN_OPPONENTS)].sort_values(["focal","day","race","opponent_depth"],kind="mergesort")
    pairs=[];eligible_novel=int(e.loc[e.novel,["focal","race","day"]].drop_duplicates().shape[0])
    for h,v in e.groupby("focal",sort=True,observed=True):
        novel=v.loc[v.novel]
        familiar=v.loc[~v.novel]
        if novel.empty or familiar.empty:continue
        # A focal-year contributes at most one novel event and one familiar
        # event, with same focal and opponent-depth bins. First eligible novel.
        for n in novel.itertuples(index=False):
            a=familiar.loc[(familiar.day<n.day)&(familiar.day>=n.day-pd.Timedelta(days=MAX_GAP))&
                familiar.focal_depth.eq(n.focal_depth)&familiar.opponent_depth.eq(n.opponent_depth)&familiar.context.ne(n.context)]
            if a.empty:continue
            b=a.sort_values(["day","race"],ascending=[False,True],kind="mergesort").iloc[0]
            pair={"focal":int(h),"novel_day":n.day,"familiar_day":b.day,"novel_race":n.race,"familiar_race":b.race,"gap":int((n.day-b.day).days),
                "novel_n":int(n.n),"familiar_n":int(b.n),"focal_depth":int(n.focal_depth),"opponent_depth":int(n.opponent_depth)}
            for k in (*METRICS,"full_loss","ablated_loss","focal_signal_abs","focal_signal"):
                pair["novel_"+k]=float(getattr(n,k));pair["familiar_"+k]=float(b[k])
            pairs.append(pair);break
    p=pd.DataFrame(pairs)
    if not p.empty and (p.focal.duplicated().any() or not p.gap.between(1,MAX_GAP).all()):raise ValueError("HOLD_MATCH")
    return p,{"oriented_pairs":len(z),"eligible_novel_event_bins":int(e.novel.sum()),
        "eligible_familiar_event_bins":int((~e.novel).sum()),"eligible_novel_events":eligible_novel,
        "eligible_novel_horses":int(e.loc[e.novel].focal.nunique()),"eligible_familiar_horses":int(e.loc[~e.novel].focal.nunique())}

def summarize(p,qa):
    out={"candidate":qa,"matched_horses":len(p)}
    if p.empty:out["status"]="HOLD_NO_MATCHES";return out
    d=np.column_stack([p["novel_"+k]-p["familiar_"+k] for k in METRICS])
    out.update(novel_days=int(p.novel_day.nunique()),familiar_days=int(p.familiar_day.nunique()),
        mean_gap_days=float(p.gap.mean()),mean_eligible_opponents={"novel":float(p.novel_n.mean()),"familiar":float(p.familiar_n.mean())},
        matched_horse_coverage=len(p)/qa["eligible_novel_horses"],
        means={arm:{k:float(p[arm+"_"+k].mean()) for k in (*METRICS,"full_loss","ablated_loss","focal_signal_abs","focal_signal")} for arm in ("novel","familiar")},
        novel_minus_familiar=dict(zip(METRICS,d.mean(axis=0).tolist())))
    if len(p)<MIN_HORSES or min(out["novel_days"],out["familiar_days"])<MIN_DATES:
        out["status"]="HOLD_SUPPORT";return out
    out["status"]="OBSERVED_CONDITIONAL"
    out["conditional_97_5"]={}
    for k in ("focal","novel_day","familiar_day"):
        tab=pd.DataFrame(d,columns=METRICS);tab["group"]=p[k].to_numpy();tab["n"]=1
        a=tab.groupby("group",observed=True)[list(METRICS)+["n"]].sum().to_numpy()
        rng=np.random.default_rng(SEED)
        draw=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
        out["conditional_97_5"][k]=dict(zip(METRICS,np.quantile(draw[:,:-1]/draw[:,-1,None],[.0125,.9875],axis=0).T.tolist()))
    return out


def carry_forward(z,p):
    # Compare the same events without using new focal parent scores. The
    # familiar-event signed logit contribution is carried forward unchanged.
    if p.empty:return p
    q=z.merge(p[["focal","novel_day","novel_race","opponent_depth","familiar_focal_signal"]],
        left_on=["focal","day","race","opponent_depth"],
        right_on=["focal","novel_day","novel_race","opponent_depth"],how="inner",validate="many_to_one")
    if not q.novel.all():raise ValueError("HOLD_NOVEL_EVENT")
    target=q.target.to_numpy(float);base=expit(q.ablated_logit.to_numpy(float))
    corrected=expit(q.ablated_logit.to_numpy(float)+q.familiar_focal_signal.to_numpy(float))
    d=corrected-base
    q["carry_gain"]=(target-base)**2-(target-corrected)**2
    q["carry_alignment"]=2*(target-base)*d;q["carry_penalty"]=d*d
    prev.same(q.carry_gain,q.carry_alignment-q.carry_penalty,"CARRY_IDENTITY")
    a=q.groupby("focal",observed=True).agg(carry_gain=("carry_gain","mean"),
        carry_alignment=("carry_alignment","mean"),carry_penalty=("carry_penalty","mean"),count=("opponent","nunique")).reset_index()
    if len(a)!=len(p):raise ValueError("HOLD_CARRY_HORSES")
    p=p.merge(a,on="focal",validate="one_to_one",sort=False)
    prev.same(p["count"],p.novel_n,"CARRY_COUNT")
    return p.drop(columns="count")

def decompose(p):
    if p.empty:return {"status":"HOLD_EMPTY"}
    # Exact pointwise loss accounting, separate from predictive/causal inference.
    d=pd.DataFrame({"alignment_change":p.novel_alignment-p.familiar_alignment,
        "penalty_change":p.novel_penalty-p.familiar_penalty,
        "gain_change":p.novel_focal_gain-p.familiar_focal_gain,
        "carry_gain_change":p.carry_gain-p.familiar_focal_gain,
        "new_signal_increment":p.novel_focal_gain-p.carry_gain})
    prev.same(d.gain_change,d.alignment_change-d.penalty_change,"MATCHED_DECOMP")
    prev.same(d.gain_change,d.carry_gain_change+d.new_signal_increment,"MATCHED_CARRY")
    out={"status":"OBSERVED_CONDITIONAL","matched_horses":len(p),
      "means":{arm:{k:float(p[arm+"_"+k].mean()) for k in ("alignment","penalty","focal_gain","focal_signal","focal_signal_abs")} for arm in ("novel","familiar")},
      "carry_novel_means":{k:float(p["carry_"+k].mean()) for k in ("gain","alignment","penalty")},
      "mean_abs_signed_signal_change":float((p.novel_focal_signal-p.familiar_focal_signal).abs().mean()),
      "mean_change":{k:float(v) for k,v in d.mean().items()}}
    if len(p)<MIN_HORSES or min(p.novel_day.nunique(),p.familiar_day.nunique())<MIN_DATES:
        out["status"]="HOLD_SUPPORT";return out
    names=list(d.columns);out["conditional_97_5"]={}
    for k in ("focal","novel_day","familiar_day"):
        tab=d.copy();tab["group"]=p[k].to_numpy();tab["n"]=1
        a=tab.groupby("group",observed=True)[names+["n"]].sum().to_numpy()
        rng=np.random.default_rng(SEED)
        draw=a[rng.integers(len(a),size=(DRAWS,len(a)))].sum(axis=1)
        out["conditional_97_5"][k]=dict(zip(names,np.quantile(draw[:,:-1]/draw[:,-1,None],[.0125,.9875],axis=0).T.tolist()))
    return out

def analyze(archive,receipt,matched_receipt):
    ref=json.loads(receipt.read_text())["result"]
    old_match=json.loads(matched_receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=prev.SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:raw=pd.read_csv(f,usecols=prev.COLS,dtype=str,keep_default_na=False)
    old,_=prev.prepare_frame(raw);del raw
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N,sizes=prev.prepare_parents(old);del old
    v,qa=replay(t,N,sizes)
    h=ctx.context_history(t);del t
    for yr in (prev.CAL,*prev.TEST):
        v[yr]=ctx.attach(v[yr],h.loc[h.day.dt.year.eq(yr)])
        if (v[yr].a_ctx_n>v[yr].a_total).any() or (v[yr].b_ctx_n>v[yr].b_total).any():raise ValueError("HOLD_EXACT_CONTEXT_DEPTH")
    del h
    q=v[prev.CAL].loc[prev.groupmask(v[prev.CAL],"first_meeting")]
    if len(q)!=ref["calibration"]["pairs"]:raise ValueError("HOLD_CALIBRATION_COUNT")
    fits={k:prev.fit(q,cols) for k,cols in ctx.MODELS.items()}
    for k,m in fits.items():
        r=ref["calibration"]["fits"][k]
        if m["cols"]!=r["cols"]:raise ValueError("HOLD_FEATURES")
        for field in ("scale","beta"):prev.same(m[field],r[field],"PR112_"+field)
    out={}
    for yr in prev.TEST:
        r=ctx.contrast(v[yr],fits);p=ref["results"][str(yr)]
        if r["status"]!=p["status"] or r["cells"]!=p["cells"]:raise ValueError("HOLD_PR112_CELLS")
        for arm in ("novel","familiar"):
            prev.same(r["matched"][arm]["pairs"],p["matched"][arm]["pairs"],"PR112_COUNTS")
            for k in ctx.CONTRASTS:
                prev.same(r["standardized_gain"][arm][k],p["standardized_gain"][arm][k],"PR112_STANDARDIZED_GAIN")
        z=oriented(v[yr],fits);matched,support=choose_events(z)
        r=summarize(matched,support);old=old_match["results"][str(yr)]
        if r["candidate"]!=old["candidate"] or r["status"]!=old["status"]:raise ValueError("HOLD_PR113_SUPPORT")
        for k in ("matched_horses","novel_days","familiar_days","mean_gap_days","matched_horse_coverage"):
            prev.same(r[k],old[k],"PR113_"+k)
        for arm in ("novel","familiar"):
            for k in old["means"][arm]:prev.same(r["means"][arm][k],old["means"][arm][k],"PR113_MEAN")
        for k in old["novel_minus_familiar"]:prev.same(r["novel_minus_familiar"][k],old["novel_minus_familiar"][k],"PR113_CONTRAST")
        for axis,b in old["conditional_97_5"].items():
            for k,v in b.items():prev.same(r["conditional_97_5"][axis][k],v,"PR113_INTERVAL")
        out[str(yr)]={"original_matched":r,"decomposition":decompose(carry_forward(z,matched))}
    return {"status":"RETROSPECTIVE_WITHIN_FOCAL_GAIN_DECOMPOSITION","source_sha256":prev.SOURCE_SHA,
      "original_PR112_parity":True,"original_PR113_parity":True,"parent_QA":qa,"primary":"2021 matched alignment change and carry-forward gain change, conditional diagnostic",
      "parameters":{"max_gap_days":MAX_GAP,"min_opponents_per_depth_bin":MIN_OPPONENTS,"min_horses":MIN_HORSES,"min_dates_each_arm":MIN_DATES},
      "results":out,"limits":["Exact Brier decomposition and carry-forward familiar logit score on fixed V ablation, not refitted model performance or causal genotype effect.",
       "Selected same-year focal horses with earlier familiar events, common coarse total-depth bins for both focal and opponents. No outcome-based matching.",
       "Both events use different opponents and contexts, different days; within-focal matching is not a controlled transition experiment.",
       "Same previously inspected archive. Single-axis conditional resampling omits crossed opponent, race, parent and fit dependence.",
       "Recorded JRA histories only; no official career, future forecasting or raw exports."]}

def self_test():
    rows=[]
    for h in range(110):
        for novel,day,c in [(False,pd.Timestamp("2021-01-01")+pd.Timedelta(days=h%40),"turf:4"),(True,pd.Timestamp("2021-04-01")+pd.Timedelta(days=h%40),"dirt:4")]:
            for j in (0,1):
                rows.append({"focal":h,"opponent":h*2+j+1000,"race":str(h)+"-"+str(novel),"day":day,"context":c,
                   "novel":novel,"focal_depth":1,"opponent_depth":0,"focal_gain":.02 if novel else .01,"pair_gain":.04 if novel else .02,
                   "full_loss":.20,"ablated_loss":.22 if novel else .21,"focal_signal_abs":.1,
                   "focal_signal":.1,"alignment":.025 if novel else .015,"penalty":.005,
                   "target":1.,"ablated_logit":0.})
    p,qa=choose_events(pd.DataFrame(rows));r=summarize(p,qa)
    assert len(p)==110 and r["status"]=="OBSERVED_CONDITIONAL"
    prev.same(list(r["novel_minus_familiar"].values()),[.01,.02,.01,0.],"TEST_MATCH")
    p=carry_forward(pd.DataFrame(rows),p)
    rr=decompose(p);assert rr["status"]=="OBSERVED_CONDITIONAL"
    prev.same(rr["mean_change"]["alignment_change"],.01,"TEST_DECOMP")
    prev.same(p.carry_gain,.25-(1-expit(.1))**2,"TEST_CARRY")
    z=pd.DataFrame(rows);z.loc[z.novel,"opponent_depth"]=2
    p,_=choose_events(z);assert p.empty
    # Focal-only ablation respects orientation, rival score unchanged.
    l=.2+.3-(-.1);a=.3;b=-.1
    prev.same(expit(l-a),expit(.2-b),"TEST_ABLATE_A")
    prev.same(expit(-l-b),expit(-.2-a),"TEST_ABLATE_B")
    print("Synthetic within-focal date/depth matching, support and ablation checks passed")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--matched-receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.matched_receipt,a.output)):p.error("archive/receipt/output required")
    r=analyze(a.archive,a.receipt,a.matched_receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
