#!/usr/bin/env python3
"""Chronological horse-vs-horse residual correspondence in JRA classified fields.
Research on repeated competition, not causal interference, wagering or payouts.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame

CAL=(2017,2018)
YEARS=(2017,2018,2019,2020,2021)
SEED=20261126
DRAWS=999
MIN_PAIRS=500
MIN_DAYS=60
FEATURES=("broad","context","family","log_n","log_nc")
RIDGE=.001
def sig(x):
    return 1/(1+np.exp(-np.clip(x,-35,35)))
def same(a,b):
    if not np.allclose(a,b,rtol=0,atol=1e-10):raise ValueError("HOLD_IDENTITY")

def prepare(old):
    j=old.loc[old.circuit.eq("JRA"),["horse","sire_id","year","day","race","surface","distance","rank","field","y"]].copy()
    for k in ("horse","sire_id","race","surface"):j[k]=j[k].astype(str)
    if j.duplicated(["horse","race"]).any():raise ValueError("HOLD_DUPLICATE")
    if j.groupby("horse",observed=True).sire_id.nunique().max()>1:raise ValueError("HOLD_PARENT_CONFLICT")
    return j,j.loc[j.distance.between(1600,1999)].copy()

def inputs(j,x,year):
    h=j.loc[j.year.lt(year)];hc=x.loc[x.year.lt(year)]
    t=x.loc[x.year.eq(year)].copy()
    if t.empty or h.empty or h.day.max()>=t.day.min():raise ValueError("HOLD_TIME")
    b=h.groupby("horse",observed=True).y.agg(["sum","size"])
    t["n"]=t.horse.map(b["size"]).fillna(0)
    t["broad"]=(t.horse.map(b["sum"]).fillna(0)+2.5)/(t.n+5)
    c=hc.groupby(["horse","surface"],observed=True).y.agg(["sum","size"])
    k=pd.MultiIndex.from_frame(t[["horse","surface"]]);cs=c.reindex(k)
    t["nc"]=cs["size"].fillna(0).to_numpy()
    t["context"]=(cs["sum"].fillna(0).to_numpy()+5*t.broad)/(t.nc+5)
    # Equal historical horse weights; exclude focal horse in family profile.
    q=hc.loc[hc.sire_id.ne("")].groupby(["sire_id","surface","horse"],observed=True).y.mean()
    g=q.groupby(level=[0,1]).agg(["sum","size"])
    v=g.reindex(pd.MultiIndex.from_frame(t[["sire_id","surface"]]))
    own=q.reindex(pd.MultiIndex.from_frame(t[["sire_id","surface","horse"]]))
    n=v["size"].fillna(0).to_numpy()-own.notna().to_numpy()
    sums=v["sum"].fillna(0).to_numpy()-own.fillna(0).to_numpy()
    if (n<0).any() or (sums< -1e-8).any() or (sums>n+1e-8).any():raise ValueError("HOLD_FOCAL_EXCLUSION")
    t["family"]=(sums+4)/(n+8)
    t["log_n"]=np.log1p(t.n)/4
    t["log_nc"]=np.log1p(t.nc)/4
    return t

def pairs(t):
    t=t.sort_values(["race","horse"],kind="mergesort").reset_index(drop=True)
    F=t[list(FEATURES)].to_numpy(float)
    a=[];b=[]
    for _,ix in t.groupby("race",sort=False,observed=True).indices.items():
        if len(ix)!=int(t.field.iloc[ix[0]]) or not np.array_equal(np.sort(t["rank"].to_numpy()[ix]),np.arange(1,len(ix)+1)):
            raise ValueError("HOLD_FIELD")
        i,k=np.triu_indices(len(ix),1);a.append(ix[i]);b.append(ix[k])
    if not a:raise ValueError("HOLD_NO_PAIRS")
    a=np.concatenate(a);b=np.concatenate(b)
    h=t.horse.to_numpy()
    if not (h[a]<h[b]).all():raise ValueError("HOLD_ORIENTATION")
    z=pd.DataFrame({"race":t.race.to_numpy()[a],"day":t.day.to_numpy()[a],"surface":t.surface.to_numpy()[a],
        "a":h[a],"b":h[b],"y":(t["rank"].to_numpy()[a]>t["rank"].to_numpy()[b]).astype(float)})
    for i,k in enumerate(FEATURES):z[k]=F[a,i]-F[b,i]
    return z

def fit(cal):
    X=cal[list(FEATURES)].to_numpy(float);y=cal.y.to_numpy(float)
    w=1/cal.groupby("race",observed=True).race.transform("size").to_numpy(float);w/=w.sum()
    beta=np.zeros(X.shape[1])
    def loss(b):
        z=X@b;return float(np.sum(w*(np.logaddexp(0,z)-y*z))+.5*RIDGE*np.dot(b,b))
    for _ in range(80):
        p=sig(X@beta)
        gr=X.T@(w*(p-y))+RIDGE*beta
        if np.max(np.abs(gr))<1e-10:break
        H=X.T@(X*(w*p*(1-p))[:,None])+RIDGE*np.eye(X.shape[1])
        step=np.linalg.solve(H,gr);l=loss(beta);k=1.
        while loss(beta-k*step)>l+1e-14 and k>1e-8:k/=2
        beta-=k*step
    if not np.isfinite(beta).all() or np.max(np.abs(X.T@(w*(sig(X@beta)-y))+RIDGE*beta))>1e-7:
        raise ValueError("HOLD_CALIBRATION_CONVERGENCE")
    return beta

def add_base(p,beta):
    q=p.copy();q["p"]=sig(q[list(FEATURES)].to_numpy(float)@beta);q["e"]=q.y-q.p
    return q

def horse_profile(d):
    # Signed residual averages per horse-race, then equal-start shrinkage.
    a=d[["race","a","e"]].rename(columns={"a":"horse"})
    b=d[["race","b","e"]].rename(columns={"b":"horse"});b["e"]=-b.e
    x=pd.concat([a,b],ignore_index=True).groupby(["horse","race"],observed=True).e.mean()
    q=x.groupby(level=0).agg(["sum","size"])
    return q["sum"]/(q["size"]+5.)

def horse_correction(d,h):
    return d.a.map(h).fillna(0).to_numpy()-d.b.map(h).fillna(0).to_numpy()

def score(d,t):
    if d.day.max()>=t.day.min():raise ValueError("HOLD_DONOR_TIME")
    h=horse_profile(d)
    d=d.copy();d["e2"]=d.e-horse_correction(d,h)
    p=d.groupby(["surface","a","b"],observed=True).e2.agg(["sum","size"])
    r=p.reindex(pd.MultiIndex.from_frame(t[["surface","a","b"]]))
    t=t.copy();t["prior_meetings"]=r["size"].fillna(0).to_numpy(int)
    t["dyad"]=r["sum"].fillna(0).to_numpy()/(t.prior_meetings+3.)
    t["H"]=t.p+horse_correction(t,h)
    t["D"]=t.H+t.dyad
    t["N"]=t.p
    return t

def summary(t,seed,threshold):
    x=t.loc[t.prior_meetings.ge(threshold)].copy()
    if x.empty:return {"status":"HOLD_EMPTY","rows":0}
    n=len(x);pairs=int(x[["surface","a","b"]].drop_duplicates().shape[0])
    horses=len(set(x.a)|set(x.b));days=int(x.day.nunique());races=int(x.race.nunique())
    w=1/x.groupby("race",observed=True).race.transform("size").to_numpy(float)
    y=x.y.to_numpy(float)
    errs=np.column_stack([(y-np.clip(x[k].to_numpy(),0,1))**2 for k in ("N","H","D")])
    raw=(y-x.H.to_numpy())**2-(y-x.D.to_numpy())**2
    diff=errs[:,1]-errs[:,2];improve=errs[:,0]-errs[:,1]
    z=pd.DataFrame({"day":x.day.to_numpy(),"w":w,"d":w*diff,"h":w*improve})
    day=z.groupby("day",observed=True)[["w","d","h"]].sum().to_numpy(float)
    out={"status":"OBSERVED_DESCRIPTIVE","rows":n,"distinct_surface_dyads":pairs,"horses":horses,"days":days,"races":races,
      "prior_meeting_mean":float(x.prior_meetings.mean()),"race_equal_brier":dict(zip(("N","H","D"),np.average(errs,axis=0,weights=w).tolist())),
      "horse_correction_gain":float(np.average(improve,weights=w)),"dyad_increment":float(np.average(diff,weights=w)),
      "unclipped_dyad_increment":float(np.average(raw,weights=w))}
    if pairs<MIN_PAIRS or days<MIN_DAYS or horses<100:
        out["status"]="HOLD_SUPPORT";return out
    rng=np.random.default_rng(seed);draw=day[rng.integers(len(day),size=(DRAWS,len(day)))].sum(axis=1)
    out["conditional_day_95_dyad_increment"]=np.quantile(draw[:,1]/draw[:,0],[.025,.975]).tolist()
    out["conditional_day_95_horse_increment"]=np.quantile(draw[:,2]/draw[:,0],[.025,.975]).tolist()
    return out

def analyze(archive):
    with archive.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=SOURCE_SHA:raise ValueError("HOLD_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as f:
        raw=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    old,_=prepare_frame(raw)
    if len(old)!=2092836 or old.horse.nunique()!=90962:raise ValueError("HOLD_SOURCE_PARITY")
    j,x=prepare(old)
    v=x.loc[x.year.isin([2019,2020,2021])]
    if len(v)!=57208 or v.horse.nunique()!=15129:raise ValueError("HOLD_CANDIDATE_PARITY")
    p={yr:pairs(inputs(j,x,yr)) for yr in YEARS}
    beta=fit(pd.concat([p[y] for y in CAL],ignore_index=True))
    q={yr:add_base(p[yr],beta) for yr in (2019,2020,2021)}
    out={}
    for yr in (2020,2021):
        d=pd.concat([q[y] for y in range(2019,yr)],ignore_index=True)
        t=score(d,q[yr])
        out[str(yr)]={"donor_rows":len(d),"target_rows":len(t),"prior_meeting_rows":int(t.prior_meetings.ge(1).sum()),
          "prior_two_meeting_rows":int(t.prior_meetings.ge(2).sum()),"all":summary(t,SEED+yr,0),
          "one_or_more":summary(t,SEED+yr,1),"two_or_more":summary(t,SEED+yr,2)}
    return {"status":"RETROSPECTIVE_REPEATED_COMPETITION","source_A_sha256":SOURCE_SHA,
      "primary":"2021/one_or_more/dyad_increment","calibration_years":list(CAL),"baseline_features":list(FEATURES),"coefficients":beta.tolist(),
      "pair_counts":{str(k):len(v) for k,v in p.items()},"results":out,
      "limitations":["Observed relative finishing order and repeated dyad correspondence; not physiological speed, physical interaction or genetic causation.",
        "Calendar-year frozen inputs, only earlier donor outcomes; retrospective inspected archive, no prospective validation.",
        "Selected rematches and complete classified fields; no actual race-entry alternatives, class or jockey adjustment.",
        "Day-block interval conditional on fixed predictions ignores horse, pedigree and donor-fit dependence; no independent pair inference.",
        "Shared horse residual fitted on same donor records as dyad residual; conservative nested comparator, not a causal interaction model.",
        "Unknown publisher license; no raw data or individual IDs exported."]}

def self_test():
    a=pd.DataFrame({"race":["r"]*3,"day":pd.to_datetime(["2020-01-01"]*3),"surface":["turf"]*3,
      "horse":["a","b","c"],"rank":[1,3,2],"field":[3]*3,**{k:[.1,.5,.3] for k in FEATURES}})
    p=pairs(a);assert len(p)==3 and p.y.tolist()==[0.,0.,1.]
    beta=fit(p)
    assert np.isfinite(beta).all()
    d=add_base(p,beta);t=d.copy();t["day"]=pd.Timestamp("2021-01-01");t["race"]="r2"
    z=score(d,t);assert z.prior_meetings.tolist()==[1,1,1]
    same(z.D-z.H,z.dyad)
    zz=score(d,t.assign(surface="dirt"));assert (zz.prior_meetings==0).all()
    same(zz.D,zz.H)
    try:score(d,d)
    except ValueError as e:assert str(e)=="HOLD_DONOR_TIME"
    else:raise AssertionError("time gate")
    print("Synthetic orientation, calibration, dyad support, fallback and time gates passed")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--archive",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    if a.self_test:self_test();return
    if not all((a.archive,a.output)):p.error("archive/output required")
    r=analyze(a.archive);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n")
    print(json.dumps(r,allow_nan=False))
if __name__=="__main__":main()
