#!/usr/bin/env python3
"""Retrospective test: does environmental breadth moderate off-context kin signal?

Frozen pre-2022 history, same strict 2022-24 focal cohort. No current
outcomes enter features. Outputs only anonymous aggregate statistics.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

SIDES = ("sire_id", "dam_id")
FIELDS = ("log_n", "log_starts", "mean_age", "same_surface", "distance_gap", "signal", "log_D")
CONTROLS = ("log_n", "log_starts", "mean_age", "same_surface", "distance_gap")
TRAIN = (2018, 2019, 2020, 2021)
TEST = (2022, 2023, 2024)

def _divide(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return np.divide(a, b, out=np.zeros_like(a), where=b > 0)

def _environment(s):
    surface, band = s.split(":")
    if surface not in ("turf", "dirt") or not band.isdigit():
        raise ValueError("HOLD_INVALID_CONTEXT")
    return surface, int(band)

def cross_context_features(history, targets):
    """One peer gets one unit of environmental mass; exclude focal and target.
    
    Horse-specific counts across non-target contexts determine the distribution
    of that horse's unit mass. Parents with no eligible peers get explicit zero
    features. Rank signal is an equal-peer mean shrunk toward zero by n/(n+8).
    No target outcome column is read.
    """
    if history.empty or targets.empty or history.day.max() >= targets.day.min():
        raise ValueError("HOLD_NONHISTORICAL_FEATURES")
    t = targets[["horse", "stratum", "sire_id", "dam_id", "day"]].reset_index(drop=True).copy()
    h = history[["horse", "stratum", "sire_id", "dam_id", "day", "y"]].copy()
    for c in ("horse", "stratum", *SIDES):
        t[c] = t[c].astype(str)
        h[c] = h[c].astype(str)
    if h.horse.eq("").any() or t.horse.eq("").any() or not np.isfinite(h.y).all() or not h.y.between(0, 1).all():
        raise ValueError("HOLD_INVALID_HISTORY")
    envs = sorted(set(h.stratum) | set(t.stratum))
    parsed = [_environment(e) for e in envs]
    h["last_year"] = h.day.dt.year
    cutoff_year = int(t.day.min().year)
    out = {}
    for side in SIDES:
        prefix = side.split("_")[0] + "_off_"
        result = np.zeros((len(t), len(FIELDS)))
        hist = h.loc[h[side].ne("")]
        if not hist.empty:
            profile = hist.groupby([side, "horse", "stratum"], observed=True, sort=True).agg(
                starts=("y", "size"), scores=("y", "sum"), last=("last_year", "max"))
            counts = profile.starts.unstack(fill_value=0).reindex(columns=envs, fill_value=0)
            sums = profile.scores.unstack(fill_value=0).reindex(columns=envs, fill_value=0)
            years = profile["last"].unstack(fill_value=0).reindex(columns=envs, fill_value=0)
            if not counts.index.equals(sums.index) or not counts.index.equals(years.index):
                raise ValueError("HOLD_PROFILE_INDEX")
            c0, s0, yr0 = counts.to_numpy(float), sums.to_numpy(float), years.to_numpy(float)
            for j, env in enumerate(envs):
                ix = np.flatnonzero(t.stratum.eq(env).to_numpy())
                if not len(ix):
                    continue
                c = c0.copy()
                c[:, j] = 0.
                nstart = c.sum(axis=1)
                valid = nstart > 0
                mass = _divide(c, nstart[:, None])
                score = _divide(s0.sum(axis=1)-s0[:, j], nstart) - .5
                score[~valid] = 0.
                yy = yr0.copy()
                yy[:, j] = 0.
                age = np.where(valid, cutoff_year-yy.max(axis=1), 0.)
                if (age < 0).any():
                    raise ValueError("HOLD_FUTURE_PEER_YEAR")
                contrib = pd.DataFrame(np.column_stack((valid.astype(float), nstart, age, score, mass)),
                                       index=counts.index)
                total = contrib.groupby(level=0, sort=False).sum()
                sub = t.iloc[ix]
                a = total.reindex(sub[side]).fillna(0).to_numpy(float)
                b = contrib.reindex(pd.MultiIndex.from_frame(sub[[side, "horse"]])).fillna(0).to_numpy(float)
                v = a-b
                n, starts = v[:, 0], v[:, 1]
                if (n < -1e-8).any() or (starts < -1e-8).any() or (v[:, 4:] < -1e-8).any():
                    raise ValueError("HOLD_FOCAL_EXCLUSION")
                n = np.maximum(n, 0)
                starts = np.maximum(starts, 0)
                p = _divide(np.maximum(v[:, 4:], 0), n[:, None])
                if not np.allclose(p.sum(axis=1), (n > 0).astype(float), atol=1e-8, rtol=0):
                    raise ValueError("HOLD_PEER_MASS")
                if not np.allclose(p[:, j], 0, atol=1e-10):
                    raise ValueError("HOLD_TARGET_CONTEXT_LEAK")
                diversity = _divide(np.ones(len(n)), np.square(p).sum(axis=1))
                surf, band = parsed[j]
                same = np.array([e[0] == surf for e in parsed], float)
                gap = np.array([abs(e[1]-band) for e in parsed], float)
                result[ix, :] = np.column_stack((
                    np.log1p(n), np.log1p(starts), _divide(v[:, 2], n),
                    p @ same, p @ gap, _divide(v[:, 3], n+8),
                    np.log(np.maximum(diversity, 1.))))
        for k, field in enumerate(FIELDS):
            out[prefix+field] = result[:, k]
    x = pd.DataFrame(out)
    if not np.isfinite(x.to_numpy()).all():
        raise ValueError("HOLD_NONFINITE_CONTEXT_FEATURE")
    return x

def augment(base, off):
    x = pd.concat([base.reset_index(drop=True), off.reset_index(drop=True)], axis=1)
    for side in ("sire", "dam"):
        p = side+"_off_"
        for k in (*CONTROLS, "log_D"):
            x[p+"signal_x_"+k] = x[p+"signal"] * x[p+k]
        for k in ("log_own_count", "log_context_n"):
            x[p+"signal_x_"+k] = x[p+"signal"] * x[k]
    return x

def models_columns(strong):
    controls, main, mod = [], [], []
    for side in ("sire", "dam"):
        p = side+"_off_"
        controls.extend(p+k for k in (*CONTROLS, "signal"))
        controls.extend(p+"signal_x_"+k for k in (*CONTROLS, "log_own_count", "log_context_n"))
        main.append(p+"log_D")
        mod.append(p+"signal_x_log_D")
    return {"M2": tuple(strong), "M3": tuple(strong)+tuple(controls),
            "M4": tuple(strong)+tuple(controls+main),
            "M5": tuple(strong)+tuple(controls+main+mod)}

def summarize(panel, pred):
    if not len(panel):
        return {"status":"HOLD_EMPTY"}
    y = panel.y.to_numpy(float)
    w = 1/panel.groupby("horse", observed=True).horse.transform("size").to_numpy(float)
    mse = {k:float(np.average((y-v)**2, weights=w)) for k,v in pred.items()}
    mse["M0"] = float(np.average((y-.5)**2, weights=w))
    return {"starts":len(panel),"horses":int(panel.horse.nunique()),
            "races":int(panel.race.nunique()), "days":int(panel.day.nunique()),
            "RMSE":{k:float(np.sqrt(v)) for k,v in mse.items()},
            "MSE_gain_M4_minus_M5":mse["M4"]-mse["M5"],
            "MSE_gain_M3_minus_M4":mse["M3"]-mse["M4"],
            "MSE_gain_M2_minus_M5":mse["M2"]-mse["M5"],
            "MSE_gain_M0_minus_M5":mse["M0"]-mse["M5"]}

def analyze(archive, db):
    from ecology_japan_archive_forward import SOURCE_SHA
    from ecology_japan_2022_parent_placebo import SQLITE_SHA, load_sources
    from ecology_japan_2022_24_family_feature_ablation import _strong_features, paired_uncertainty
    from ecology_japan_2022_independent_forward import RIDGE_ALPHA, fit_weighted_ridge, predict_weighted_ridge, _scores
    from ecology_japan_2022_joint_strict_strong import strict_mask_exact_horse_race, ALL_STRONG_KIN, STRICT_ROWS, STRICT_HORSES
    from ecology_japan_2022_strong_portable_baseline import old_metadata, STRONG_KIN
    from ecology_japan_2022_2024_kin_information_moderators import LOCKED_STRICT_KIN
    raw, old, future, _, gate, _ = load_sources(archive, db)
    if not old.year.lt(2022).all() or set(future.year.unique()) != set(TEST):
        raise ValueError("HOLD_SCOPE")
    meta = old_metadata(raw)
    mask, qa = strict_mask_exact_horse_race(raw, future, db, gate["two_event_anchor_horses"])
    strict = future.loc[mask].reset_index(drop=True)
    if len(strict)!=STRICT_ROWS or strict.horse.nunique()!=STRICT_HORSES or strict.race.nunique()!=35333:
        raise ValueError("HOLD_STRICT_PARITY")
    def features(h,t):
        return augment(_strong_features(h,t,meta), cross_context_features(h,t))
    blocks, ys, ids = [], [], []
    for year in TRAIN:
        t = old.loc[old.year.eq(year)]
        blocks.append(features(old.loc[old.year.lt(year)],t))
        ys.append(t.y.to_numpy(float))
        ids.append(t.horse.astype(str).to_numpy())
    train = pd.concat(blocks, ignore_index=True)
    del blocks
    y, horse = np.concatenate(ys), np.concatenate(ids)
    columns = models_columns(STRONG_KIN)
    models = {k:fit_weighted_ridge(train,y,horse,v,alpha=RIDGE_ALPHA) for k,v in columns.items()}
    del train, y, horse, ys, ids
    f = features(old,future)
    pred_all = {k:predict_weighted_ridge(v,f) for k,v in models.items()}
    parity = _scores(future,pred_all["M2"],pred_all["M2"])["RMSE_portable_kin"]
    if abs(parity-ALL_STRONG_KIN)>1e-8:
        raise ValueError("HOLD_ALL_M2_PARITY")
    x = f.loc[mask].reset_index(drop=True)
    pred = {k:v[mask] for k,v in pred_all.items()}
    overall = summarize(strict,pred)
    if abs(overall["RMSE"]["M2"]-LOCKED_STRICT_KIN)>1e-8:
        raise ValueError("HOLD_STRICT_M2_PARITY")
    eligible = (x.sire_off_log_n.gt(0) | x.dam_off_log_n.gt(0)).to_numpy()
    novel = x.log_context_n.eq(0).to_numpy()
    primary = novel & eligible
    def sub(m):
        return summarize(strict.loc[m].reset_index(drop=True),{k:v[m] for k,v in pred.items()})
    groups={"all":overall,"novel_supported":sub(primary),"seen_supported":sub(~novel & eligible),
            "no_off_context_peers":sub(~eligible)}
    yearly={str(yr):{"all":sub(strict.year.eq(yr).to_numpy()),
                    "novel_supported":sub(primary & strict.year.eq(yr).to_numpy())} for yr in TEST}
    p = strict.loc[primary].reset_index(drop=True)
    if len(p) and min(p.horse.nunique(),p.day.nunique())>=30:
        delta=(p.y.to_numpy()-pred["M4"][primary])**2-(p.y.to_numpy()-pred["M5"][primary])**2
        uncertainty=paired_uncertainty(p,delta)
    else:
        uncertainty={"status":"HOLD_INSUFFICIENT_PRIMARY_SUPPORT"}
    # Main diversity distribution, conditional on peer count; equal-horse summaries.
    coverage={}
    for side in ("sire","dam"):
        count=np.rint(np.expm1(x[side+"_off_log_n"].to_numpy())).astype(int)
        d=np.exp(x[side+"_off_log_D"].to_numpy())
        stats={}
        for k,m in {"1":count==1,"2-4":(count>=2)&(count<=4),"5-19":(count>=5)&(count<=19),"20+":count>=20}.items():
            if m.any():
                tmp=strict.loc[m,["horse"]].copy()
                tmp["D"]=d[m]
                stats[k]={"starts":int(m.sum()),"horses":int(tmp.horse.nunique()),
                          "horse_equal_mean_effective_contexts":float(tmp.groupby("horse",observed=True).D.mean().mean())}
            else:
                stats[k]={"starts":0,"horses":0}
        coverage[side]=stats
    m=models["M5"]
    slopes={k:float(m["coef"][i+1]/m["sd"][i]) for i,k in enumerate(m["columns"]) if k.endswith("signal_x_log_D")}
    return {"status":"RETROSPECTIVE_KIN_CONTEXT_DIVERSITY_NOT_CAUSAL_OR_PROSPECTIVE",
            "source_A_sha256":SOURCE_SHA,"source_B_sha256":SQLITE_SHA,"strict_source_qa":qa,
            "train_years":list(TRAIN),"test_years":list(TEST),"ridge_alpha":RIDGE_ALPHA,
            "M2_all_RMSE_parity":parity,"groups":groups,"yearly":yearly,
            "primary":"M4 minus M5 equal-horse MSE in novel_supported, both cluster sensitivities",
            "primary_uncertainty":uncertainty,"M5_unscaled_diversity_signal_interaction":slopes,
            "context_diversity_by_count":coverage,
            "limitations":["Retrospective held calendar period already examined; not new independent replication.",
                           "Parent IDs are direct recorded relationships, not genome or causal effects.",
                           "Context is surface x 400m distance band; diversity is exposure, not niche preference.",
                           "M3 controls observed peer count, depth, age, and context proximity; not exact matching.",
                           "Full-sibling duplication and shared environments can still induce dependence.",
                           "Relative ranks are not absolute speed or competition intensity.",
                           "No raw source rows or individual prediction, name, parent or horse IDs exported."]}

def self_test():
    def row(horse, env, y, sire="S", dam=""):
        return dict(horse=horse,stratum=env,y=y,sire_id=sire,dam_id=dam,day=pd.Timestamp("2020-01-01"))
    h=pd.DataFrame([row("X","turf:3",.9),row("X","dirt:4",.99),row("P","turf:4",.2),
                    row("P","turf:4",.2),row("P","turf:3",.99),row("Q","dirt:3",.6),
                    row("U","dirt:3",.99,"OTHER")])
    t=pd.DataFrame([row("X","turf:3",.99),row("Z","turf:3",.99,"NONE")])
    t["day"]=pd.Timestamp("2021-01-01")
    x=cross_context_features(h,t)
    assert np.isclose(x.loc[0,"sire_off_log_n"],np.log(3))
    assert np.isclose(x.loc[0,"sire_off_log_starts"],np.log(4))
    assert np.isclose(x.loc[0,"sire_off_log_D"],np.log(2))
    assert np.isclose(x.loc[0,"sire_off_signal"],-.02)
    assert np.isclose(x.loc[0,"sire_off_same_surface"],.5)
    assert np.isclose(x.loc[0,"sire_off_distance_gap"],.5)
    assert np.isclose(x.loc[0,"sire_off_mean_age"],1)
    assert np.allclose(x.filter(regex="^dam_"),0)
    assert np.allclose(x.iloc[1],0)
    # Current labels, target-context histories and focal off-context labels do not alter result.
    tt=t.copy()
    tt["y"]=0.
    hh=h.copy()
    hh.loc[hh.horse.eq("X") | hh.stratum.eq("turf:3"),"y"]=0.
    assert np.allclose(cross_context_features(hh,tt),x)
    # Ordering and row multiplicity of an identical peer in one context do not change diversity.
    hh=pd.concat([h,h.loc[h.horse.eq("P") & h.stratum.eq("turf:4")]],ignore_index=True)
    assert np.isclose(cross_context_features(hh,t).loc[0,"sire_off_log_D"],np.log(2))
    assert np.allclose(cross_context_features(h.sample(frac=1,random_state=1),t),x)
    try:
        cross_context_features(h,t.assign(day=pd.Timestamp("2020-01-01")))
    except ValueError:
        pass
    else:
        raise AssertionError("temporal overlap was accepted")
    print("synthetic context-diversity tests passed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--archive",type=Path)
    p.add_argument("--sqlite",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if a.self_test:
        self_test()
        return
    if not all((a.archive,a.sqlite,a.output)):
        p.error("archive, sqlite and output required")
    z=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":z["status"],"groups":z["groups"],"primary_uncertainty":z["primary_uncertainty"]},allow_nan=False))

if __name__=="__main__":
    main()
