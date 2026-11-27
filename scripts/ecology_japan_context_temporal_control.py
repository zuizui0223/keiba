#!/usr/bin/env python3
"""Same-focal three-event temporal control for context information recovery."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
import ecology_japan_within_focal_gain_decomposition as base
ctx=base.ctx;prev=base.prev
MAX_GAP_DIFF=30
METRICS=("observed_gain","fixed_signal_gain")
SEED=20261127

def events(z):
    cols=["focal","race","day","context","novel","focal_depth","opponent_depth"]
    e=z.groupby(cols,observed=True).agg(n=("opponent","nunique"),gain=("focal_gain","mean"),
        signal=("focal_signal","mean"),alignment=("alignment","mean"),penalty=("penalty","mean")).reset_index()
    return e.loc[e.n.ge(base.MIN_OPPONENTS)].copy()

def select_triplets(z,p):
    e=events(z);groups={int(h):x for h,x in e.groupby("focal",sort=False,observed=True)}
    rows=[]
    for n in p.itertuples(index=False):
        g=groups[int(n.focal)]
        f=g.loc[(~g.novel)&g.day.eq(n.familiar_day)&g.race.eq(n.familiar_race)&g.opponent_depth.eq(n.opponent_depth)]
        a=g.loc[g.novel&g.day.eq(n.novel_day)&g.race.eq(n.novel_race)&g.opponent_depth.eq(n.opponent_depth)]
        if len(f)!=1 or len(a)!=1:raise ValueError("HOLD_ORIGINAL_EVENT_JOIN")
        f=f.iloc[0];a=a.iloc[0]
        if f.context==a.context or f.focal_depth!=a.focal_depth:raise ValueError("HOLD_ORIGINAL_EVENT_MATCH")
        prev.same([f.gain,a.gain],[n.familiar_focal_gain,n.novel_focal_gain],"ORIGINAL_EVENT_GAIN")
        # The PR113 familiar anchor was already the nearest qualifying past
        # event. A third, earlier familiar event avoids selecting a logically
        # impossible intervening familiar control. Match both interval lengths.
        cand=g.loc[(~g.novel)&g.context.eq(f.context)&g.day.lt(f.day)&
            g.day.ge(f.day-pd.Timedelta(days=base.MAX_GAP))&
            g.focal_depth.eq(f.focal_depth)&g.opponent_depth.eq(f.opponent_depth)].copy()
        if cand.empty:continue
        cand["gap"]=(f.day-cand.day).dt.days
        cand["gap_diff"]=(cand.gap-int(n.gap)).abs()
        cand=cand.loc[cand.gap_diff.le(MAX_GAP_DIFF)]
        if cand.empty:continue
        b=cand.sort_values(["gap_diff","day","race"],ascending=[True,False,True],kind="mergesort").iloc[0]
        rows.append({"focal":int(n.focal),"early_day":b.day,"early_race":b.race,
            "middle_day":f.day,"middle_race":f.race,"novel_day":a.day,"novel_race":a.race,
            "opponent_depth":int(n.opponent_depth),"early_signal":float(b.signal),
            "gap_early_middle":int(b.gap),"gap_middle_novel":int(n.gap),
            "early_n":int(b.n),"middle_n":int(f.n),"novel_n":int(a.n),
            "early_gain":float(b.gain),"middle_gain":float(f.gain),"novel_gain":float(a.gain)})
    t=pd.DataFrame(rows)
    if not t.empty:
        if t.focal.duplicated().any() or not (t.early_day.lt(t.middle_day)&t.middle_day.lt(t.novel_day)).all():
            raise ValueError("HOLD_TRIPLET_ORDER")
        if not (t.gap_early_middle-t.gap_middle_novel).abs().le(MAX_GAP_DIFF).all():raise ValueError("HOLD_GAP_BALANCE")
    return t

def fixed_score(z,t):
    if t.empty:return t
    out=t.copy()
    for arm in ("early","middle","novel"):
        q=z.merge(t[["focal",arm+"_day",arm+"_race","opponent_depth","early_signal"]],
            left_on=["focal","day","race","opponent_depth"],
            right_on=["focal",arm+"_day",arm+"_race","opponent_depth"],validate="many_to_one",how="inner")
        if not q.novel.eq(arm=="novel").all():raise ValueError("HOLD_ARM")
        y=q.target.to_numpy(float);p0=expit(q.ablated_logit.to_numpy(float))
        p1=expit(q.ablated_logit.to_numpy(float)+q.early_signal.to_numpy(float))
        q["fixed"]=(y-p0)**2-(y-p1)**2
        g=q.groupby("focal",observed=True).agg(gain=("fixed","mean"),n=("opponent","nunique"))
        if len(g)!=len(t):raise ValueError("HOLD_FIXED_COUNT")
        prev.same(g.n.reindex(t.focal).to_numpy(),t[arm+"_n"],"FIXED_OPPONENTS")
        out[arm+"_fixed"]=g.gain.reindex(t.focal).to_numpy()
    prev.same(out.early_fixed,out.early_gain,"EARLY_FIXED_PARITY")
    return out

def summarize(t,n_original):
    out={"matched_triplets":len(t),"original_matched_horses":n_original,"coverage":len(t)/n_original if n_original else 0.}
    if t.empty:out["status"]="HOLD_NO_TRIPLETS";return out
    out["dates"]={k:int(t[k+"_day"].nunique()) for k in ("early","middle","novel")}
    out["mean_gaps_days"]={"early_middle":float(t.gap_early_middle.mean()),"middle_novel":float(t.gap_middle_novel.mean()),
        "absolute_gap_difference":float((t.gap_early_middle-t.gap_middle_novel).abs().mean())}
    arms=("early","middle","novel")
    out["means"]={k:{"observed_gain":float(t[k+"_gain"].mean()),"fixed_signal_gain":float(t[k+"_fixed"].mean())} for k in arms}
    ds={}
    for lab,col in (("observed_gain","gain"),("fixed_signal_gain","fixed")):
        before=t["middle_"+col]-t["early_"+col];after=t["novel_"+col]-t["middle_"+col]
        ds[lab+"_before"]=before;ds[lab+"_after"]=after;ds[lab+"_difference"]=after-before
    d=pd.DataFrame(ds)
    out["contrasts"]={k:float(x) for k,x in d.mean().items()}
    if len(t)<base.MIN_HORSES or min(out["dates"].values())<base.MIN_DATES:
        out["status"]="HOLD_SUPPORT";return out
    out["status"]="OBSERVED_CONDITIONAL";out["conditional_97_5"]={}
    names=list(d)
    for axis in ("focal","early_day","middle_day","novel_day"):
        a=d.copy();a["group"]=t[axis].to_numpy();a["n"]=1
        b=a.groupby("group",observed=True)[names+["n"]].sum().to_numpy()
        rng=np.random.default_rng(SEED);draw=b[rng.integers(len(b),size=(base.DRAWS,len(b)))].sum(axis=1)
        out["conditional_97_5"][axis]=dict(zip(names,np.quantile(draw[:,:-1]/draw[:,-1,None],[.0125,.9875],axis=0).T.tolist()))
    return out

def analyze(archive,receipt,matched_receipt):
    ref=json.loads(receipt.read_text())["result"];old=json.loads(matched_receipt.read_text())["result"]
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=prev.SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:raw=pd.read_csv(f,usecols=prev.COLS,dtype=str,keep_default_na=False)
    src,_=prev.prepare_frame(raw);del raw
    if len(src)!=2092836 or src.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    t,N,sizes=prev.prepare_parents(src);del src
    panels,qa=base.replay(t,N,sizes)
    if qa!=old["parent_QA"]:raise ValueError("HOLD_PARENT_QA")
    h=ctx.context_history(t);del t
    for yr in (prev.CAL,*prev.TEST):
        panels[yr]=ctx.attach(panels[yr],h.loc[h.day.dt.year.eq(yr)])
        if (panels[yr].a_ctx_n>panels[yr].a_total).any() or (panels[yr].b_ctx_n>panels[yr].b_total).any():raise ValueError("HOLD_DEPTH")
    del h
    q=panels[prev.CAL].loc[prev.groupmask(panels[prev.CAL],"first_meeting")]
    if len(q)!=ref["calibration"]["pairs"]:raise ValueError("HOLD_CALIBRATION")
    fits={k:prev.fit(q,cols) for k,cols in ctx.MODELS.items()}
    for k,m in fits.items():
        r=ref["calibration"]["fits"][k]
        if m["cols"]!=r["cols"]:raise ValueError("HOLD_FEATURES")
        for field in ("scale","beta"):prev.same(m[field],r[field],"PR112_"+field)
    out={}
    for yr in prev.TEST:
        r=ctx.contrast(panels[yr],fits);p=ref["results"][str(yr)]
        if r["status"]!=p["status"] or r["cells"]!=p["cells"]:raise ValueError("HOLD_PR112_CELLS")
        for arm in ("novel","familiar"):
            prev.same(r["matched"][arm]["pairs"],p["matched"][arm]["pairs"],"PR112_COUNTS")
            for k in ctx.CONTRASTS:prev.same(r["standardized_gain"][arm][k],p["standardized_gain"][arm][k],"PR112_GAIN")
        z=base.oriented(panels[yr],fits);p,qa=base.choose_events(z);r=base.summarize(p,qa);o=old["results"][str(yr)]
        if r["candidate"]!=o["candidate"] or r["status"]!=o["status"]:raise ValueError("HOLD_PR113_SUPPORT")
        for k in ("matched_horses","novel_days","familiar_days","mean_gap_days","matched_horse_coverage"):
            prev.same(r[k],o[k],"PR113_"+k)
        for arm in ("novel","familiar"):
            for k in o["means"][arm]:prev.same(r["means"][arm][k],o["means"][arm][k],"PR113_MEAN")
        for k in o["novel_minus_familiar"]:prev.same(r["novel_minus_familiar"][k],o["novel_minus_familiar"][k],"PR113_CONTRAST")
        for axis,intervals in o["conditional_97_5"].items():
            for k,interval in intervals.items():prev.same(r["conditional_97_5"][axis][k],interval,"PR113_INTERVAL")
        trip=select_triplets(z,p);trip=fixed_score(z,trip)
        out[str(yr)]=summarize(trip,len(p))
    return {"status":"RETROSPECTIVE_CONTEXT_THREE_EVENT_CONTROL","source_sha256":prev.SOURCE_SHA,
      "original_PR112_PR113_parity":True,"primary":"2021 observed_gain_difference (novel transition minus earlier familiar transition)",
      "parameters":{"max_each_gap_days":base.MAX_GAP,"max_gap_difference_days":MAX_GAP_DIFF,"min_horses":base.MIN_HORSES,"min_dates_each_arm":base.MIN_DATES},
      "results":out,"limits":["Post-result diagnostic on selected same-horse triplets, not an independent confirmation or a controlled causal experiment.",
      "The familiar-to-familiar transition precedes novelty and uses the same middle event. Difference-of-changes can reflect regression to mean, aging, competition, time-varying management and selection.",
      "Equal focal weight, separate-axis conditional resampling, not simultaneous crossed horse, race, kin and fit uncertainty.",
      "Fixed-score diagnostic holds the earliest focal parent contribution constant across all three observed events; other terms remain contemporaneous.",
      "Classified JRA archive only; no official career completeness, prospective or genetic claim, no raw export."]}

def self_test():
    rows=[]
    for j in range(110):
        day=pd.Timestamp("2021-01-01")+pd.Timedelta(days=j%40)
        for k,gap in enumerate((0,35,70)):
            for op in (0,1):
                rows.append({"focal":j,"opponent":1000+j*2+op,"race":f"{j}-{k}","day":day+pd.Timedelta(days=gap),
                 "context":"turf:4" if k<2 else "dirt:4","novel":k==2,"focal_depth":1,"opponent_depth":0,
                 "focal_gain":.01 if k<2 else .03,"focal_signal":.1,"alignment":.02,"penalty":.01,"pair_gain":.01,
                 "full_loss":.20,"ablated_loss":.21,"focal_signal_abs":.1,"target":1.,"ablated_logit":0.})
    z=pd.DataFrame(rows);p,_=base.choose_events(z);t=select_triplets(z,p)
    assert len(t)==110
    # Synthetic gains need be internally consistent with fixed-score evaluation.
    real=.25-(1-expit(.1))**2
    z["focal_gain"]=real;p,_=base.choose_events(z);t=select_triplets(z,p)
    t=fixed_score(z,t);r=summarize(t,len(p));assert r["status"]=="OBSERVED_CONDITIONAL"
    prev.same(list(r["contrasts"].values()),0.,"TRIPLET_CONSTANT_GAIN")
    # Remove the earlier control while keeping all original matched events.
    assert select_triplets(z.loc[~z.race.str.endswith("-0")],p).empty
    print("Synthetic shared-anchor triplet, fixed signal and support tests passed")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--receipt",type=Path);p.add_argument("--matched-receipt",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.receipt,a.matched_receipt,a.output)):p.error("archive/receipt/matched-receipt/output required")
    r=analyze(a.archive,a.receipt,a.matched_receipt);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
