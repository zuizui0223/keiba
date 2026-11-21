#!/usr/bin/env python3
"""Frozen 2022 MG-vs-M2 future-observation gap: switch exposure vs conditional gain.

Exact identity at horse-equal weight:
  D_group = R_group * A_group,
where R is the fraction of 2022 start-records where the 2022-selected MG
chooses the own-history M1, and A is the M1-vs-M2 MSE gain per active
horse-weighted start. This is an arithmetic information-use decomposition,
NOT adaptive information choice, genetic causality, selective survival or
a new independent 2022 outcome test.

Two retrospective observational populations: all 2022 horses and the
subset with a strict source-B 2023 record. Parent/sire bootstrap provides
one sensitivity; a separate horse-by-day analysis of the frozen M1-vs-M2
comparison checks whether the result is peculiar to the 2022-selected gate.
Only anonymized aggregates are written.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_observation_selection_dependence import (
    EXPECTED, _validated_2022_panel, selection_dependency_audit,
)

STATUS = "POSTHOC_2022_INFORMATION_SWITCH_EXPOSURE_VS_CONDITIONAL_MODEL_GAIN_NOT_CAUSAL"
PAIRED_SCOPE = ("all_2022", "2023_recorded_2022")
EXPECTED_2023_CONDITIONAL_DELTA = -0.00007626948566923974


def _qinterval(values: np.ndarray) -> dict:
    a = np.asarray(values, float)
    if not len(a) or not np.isfinite(a).all():
        raise ValueError("HOLD_INVALID_CLUSTER_RESAMPLED_EFFECTS")
    lo, hi = np.quantile(a, [.025, .975])
    return {"sire_cluster_percentile_95pct_sensitivity_interval":[float(lo),float(hi)],
            "interval_contains_zero":bool(lo<=0<=hi)}


def _sire_label(h: pd.DataFrame) -> pd.Series:
    ids = h.sire_id.fillna("").astype(str).str.strip()
    ids = ids.where(~ids.isin(("nan","None","0","NULL")), "")
    return pd.Series(
        np.where(ids.eq(""),
                 "UNKNOWN_UNRELATED_SINGLETON:"+h.horse.astype(str),
                 "RECORDED_SIRE:"+ids),
        index=h.index
    )


def _audit_scope(h: pd.DataFrame, *, seed: int, draws: int,
                 min_group: int, min_sires: int) -> dict:
    if len(h)==0:
        return {"status":"HOLD_EMPTY_OBSERVATION_SCOPE"}
    x = h.loc[h.observed2024].copy()
    y = h.loc[~h.observed2024].copy()
    base={
        "status":STATUS,
        "horses":int(len(h)),
        "with_2024_record_horses":int(len(x)),
        "without_2024_record_horses":int(len(y)),
        "horse_equal_2022_starts_mean_with_record":float(x.nstarts.mean()) if len(x) else None,
        "horse_equal_2022_starts_mean_without_record":float(y.nstarts.mean()) if len(y) else None,
        "source_A_parent_id_not_genomic_G_or_complete_studbook_A":True,
        "not_mortality_retirement_breeding_or_evolution":True,
    }
    if min(len(x),len(y))<min_group:
        return {**base,"status":"HOLD_TOO_FEW_FUTURE_OBSERVATION_GROUP_HORSES"}
    def stats(a):
        rate=float(a.M1_selected_fraction.mean())
        gain=float(a.MG_minus_M2_mean_gain.mean())
        raw=float(a.frozen_M1_minus_M2_mean_gain.mean())
        return {
            "horse_equal_M1_selection_fraction_in_MG":rate,
            "horse_equal_MG_over_M2_MSE_gain":gain,
            "horse_equal_frozen_M1_over_M2_MSE_gain":raw,
            "active_M1_switch_weighted_gain_per_selected_start":
                float(gain/rate) if rate>1e-12 else None,
            "horses_never_choose_M1_in_2022":int(a.M1_selected_fraction.eq(0).sum()),
            "horses_always_choose_M1_in_2022":int(a.M1_selected_fraction.eq(1).sum()),
            "horses_use_both_models_in_2022":int(a.M1_selected_fraction.between(0,1, inclusive="neither").sum()),
        }
    g1,g0=stats(x),stats(y)
    d1,d0=g1["horse_equal_MG_over_M2_MSE_gain"],g0["horse_equal_MG_over_M2_MSE_gain"]
    r1,r0=g1["horse_equal_M1_selection_fraction_in_MG"],g0["horse_equal_M1_selection_fraction_in_MG"]
    if min(r1,r0)<1e-12:
        return {**base, "status":"HOLD_INFORMATION_SWITCH_EXPOSURE_ZERO_IN_GROUP",
                "2024_recorded":g1,"2024_not_recorded":g0}
    a1,a0=d1/r1,d0/r0
    exposure=(r1-r0)*a0
    conditional=r1*(a1-a0)
    delta=d1-d0
    if abs(exposure+conditional-delta)>1e-12:
        raise ValueError("HOLD_GATE_EXPOSURE_GAIN_DECOMPOSITION_IDENTITY")
    rawcontrast = (
        g1["horse_equal_frozen_M1_over_M2_MSE_gain"]
        -g0["horse_equal_frozen_M1_over_M2_MSE_gain"]
    )
    summary={
        **base,
        "2024_recorded":g1,
        "2024_not_recorded":g0,
        "MG_minus_M2_2024_recorded_vs_unrecorded_gap":float(delta),
        "M1_activation_rate_group_difference":float(r1-r0),
        "M1_switch_conditional_MSE_gain_group_difference":float(a1-a0),
        "exposure_composition_component_at_not_recorded_conditional_gain":float(exposure),
        "within_active_switch_gain_component_at_recorded_activation_share":float(conditional),
        "exposure_plus_conditional_exactly_equals_original_MG_gap":True,
        "frozen_M1_minus_M2_full_2022_recorded_vs_unrecorded_gap":float(rawcontrast),
        "switch_conditional_gain_is_not_an_observed_biological_trait":True,
    }
    h = h.copy()
    h["sire_cluster"]=_sire_label(h)
    groups = sorted(h.sire_cluster.unique())
    ng = len(groups)
    summary.update({
        "recorded_sire_plus_unknown_singleton_clusters":ng,
        "missing_sire_horses_individually_singleton":int(h.sire_id.eq("").sum()),
        "largest_recorded_sire_cluster_horses":int(h.sire_cluster.value_counts().max()),
    })
    if ng<min_sires or draws<30:
        return {**summary,"sire_bootstrap_status":"HOLD_TOO_FEW_SIRE_CLUSTERS_OR_DRAWS"}
    # 2 future-observation groups x (n, gate activation, MG gain, frozen M1 gain).
    columns=("n","r","d","raw")
    arrays=np.zeros((ng,2,len(columns)),float)
    sire_idx={s:i for i,s in enumerate(groups)}
    for row in h.itertuples(index=False):
        i=sire_idx[row.sire_cluster]
        j=1 if row.observed2024 else 0
        arrays[i,j,:]+=np.array([1,row.M1_selected_fraction,
                                  row.MG_minus_M2_mean_gain,
                                  row.frozen_M1_minus_M2_mean_gain],float)
    def vector(totals):
        counts=totals[:,0]
        if (counts<min_group).any():
            return None
        r=totals[:,1]/counts
        d=totals[:,2]/counts
        raw=totals[:,3]/counts
        if (r<1e-12).any():
            return None
        a=d/r
        comp=(r[1]-r[0])*a[0]
        within=r[1]*(a[1]-a[0])
        return np.array([
            d[1]-d[0],
            r[1]-r[0],
            a[1]-a[0],
            comp, within,
            raw[1]-raw[0]
        ],float)
    truth = vector(arrays.sum(axis=0))
    assert truth is not None
    needed=np.array([delta,r1-r0,a1-a0,exposure,conditional,rawcontrast],float)
    if not np.allclose(truth,needed,rtol=0,atol=1e-12):
        raise ValueError("HOLD_INFORMATION_SWITCH_CLUSTER_MATRIX_POINT_PARITY")
    rng=np.random.default_rng(seed)
    reps=[]
    bad=0
    for _ in range(draws):
        idx=rng.integers(0,ng,size=ng)
        v=vector(arrays[idx].sum(axis=0))
        if v is None:
            bad+=1
        else:
            reps.append(v)
    summary["sire_resamples_requested"]=draws
    summary["sire_resamples_invalid_for_group_or_activation_support"]=bad
    if len(reps)<.99*draws:
        return {**summary,"sire_bootstrap_status":"HOLD_SIRE_CLUSTER_RESAMPLED_SUPPORT"}
    zz=np.asarray(reps,float)
    names=(
        "MG_gap","M1_gate_exposure_gap","conditional_M1_switch_gain_gap",
        "exposure_composition_component","conditional_gain_component",
        "frozen_M1_vs_M2_all_starts_gap"
    )
    summary["sire_bootstrap_status"]="POSTHOC_WHOLE_RECORDED_SIRE_CLUSTER_SENSITIVITY"
    summary["sire_cluster_999_draw_95pct_sensitivity"]={
        n:_qinterval(zz[:,i]) for i,n in enumerate(names)
    }
    summary["sire_cluster_source_labeled_horses_not_genetic_effects"]=True
    return summary


def audit_switches(panel_2022: pd.DataFrame, future_2023: set[str],
                   future_2024: set[str], *, chosen_family: np.ndarray,
                   frozen_m1: np.ndarray, frozen_m2: np.ndarray,
                   y: np.ndarray, draws: int=999,
                   min_group: int=30, min_sires: int=30,
                   source_lock: bool=False, benchmark: bool=True) -> dict:
    p=_validated_2022_panel(panel_2022)
    n=len(p)
    m1=np.asarray(frozen_m1,float)
    m2=np.asarray(frozen_m2,float)
    y=np.asarray(y,float)
    choice=np.asarray(chosen_family,bool)
    if any(len(z)!=n for z in (m1,m2,y,choice)):
        raise ValueError("HOLD_FROZEN_MG_AND_BASELINE_VECTOR_LENGTHS")
    if not np.isfinite(np.c_[m1,m2,y]).all() or any(
        ((q<0)|(q>1)).any() for q in (m1,m2,y)
    ):
        raise ValueError("HOLD_NONFINITE_OR_INVALID_NORMALIZED_PREDICTIONS")
    own_selected=~choice  # MG=M2 for True; otherwise MG=M1
    raw=(y-m2)**2-(y-m1)**2
    gain=raw*own_selected
    pg=np.where(choice,m2,m1)
    if not np.allclose(gain,(y-m2)**2-(y-pg)**2,
                       rtol=0,atol=1e-12):
        raise ValueError("HOLD_FROZEN_GATE_PREDICTION_LOSS_IDENTITY")
    new=p.copy()
    new["M1_selected"] = own_selected
    new["raw_gain"] = raw
    new["gain"] = gain
    h=new.groupby("horse",observed=True,sort=False).agg(
        nstarts=("race","size"),
        M1_selected_fraction=("M1_selected","mean"),
        MG_minus_M2_mean_gain=("gain","mean"),
        frozen_M1_minus_M2_mean_gain=("raw_gain","mean"),
        sire_id=("sire_id","first"),
        own_bin=("own_bin","first")
    ).reset_index()
    if h.sire_id.isna().any():
        raise ValueError("HOLD_MISSING_SOURCE_A_RECORDED_SIRE")
    h["observed2023"] = h.horse.isin(set(str(v) for v in future_2023))
    h["observed2024"] = h.horse.isin(set(str(v) for v in future_2024))
    if source_lock:
        if n!=120381 or len(h)!=12755 or int(h.observed2023.sum())!=8659 or int(h.observed2024.sum())!=5163:
            raise ValueError("HOLD_PREVIOUS_SOURCE_A_B_IDENTICAL_COHORT_LOCK")
        if abs(float(h.MG_minus_M2_mean_gain.mean()) - EXPECTED["mean_all"])>1e-10:
            raise ValueError("HOLD_2022_FROZEN_GATE_HORSE_EQUAL_MSE_PARITY")
    scopes = {
        "all_2022":h,
        "2023_recorded_2022":h.loc[h.observed2023]
    }
    results={}
    for i,(label,part) in enumerate(scopes.items()):
        r=_audit_scope(part,seed=20221126+i,draws=draws,
                       min_group=min_group,min_sires=min_sires)
        if source_lock:
            exp=EXPECTED["contrast"] if label=="all_2022" else -0.00007626948566923974
            if r.get("status")!=STATUS or abs(r["MG_minus_M2_2024_recorded_vs_unrecorded_gap"]-exp)>1e-10:
                raise ValueError("HOLD_2022_FUTURE_OBSERVATION_SWITCH_EXACT_OLD_MSE_PARITY")
        results[label]=r
    benchmarks={}
    if benchmark:
        for label,part in scopes.items():
            ix=new.horse.isin(set(part.horse))
            testing=new.loc[ix,["horse","race","day","sire_id","own_bin"]].copy()
            testing["gain"] = new.loc[ix,"raw_gain"].to_numpy(float)
            later=set(h.loc[h.observed2024,"horse"])
            z=selection_dependency_audit(testing,later,sire_draws=399)
            # If rare history strata do not meet support, retain HOLD without
            # replacing the population, threshold or 2022 feature design.
            benchmarks[label]={
                "status":z["status"],
                "frozen_not_2022_selected_M1_vs_M2_comparison":True,
                "unadjusted_horse_by_day":z.get("unadjusted_horse_by_2022_day"),
                "pre2022_own_bin_standardized_horse_by_day":
                    z.get("historical_bin_standardized_horse_by_2022_day"),
                "recorded_sire_bootstrap":z.get("recorded_sire_group_resampling"),
                "unadjusted_2024_recorded_vs_unrecorded":z.get(
                    "unadjusted_future_observed_minus_unobserved"),
                "four_bin_standardized_2024_recorded_vs_unrecorded":z.get(
                    "2022_historical_own_count_bin_standardized_gap"),
            }
            if z["status"].startswith("HOLD_"):
                benchmarks[label]["cause"]="INSUFFICIENT_HISTORY_BIN_SUPPORT_NOT_IMPUTED"
    return {
        "status":STATUS,
        "source_population_2022_horses":int(len(h)),
        "source_population_2022_starts":n,
        "source_frozen_M1_M2_rank_preds_reused":True,
        "MG_selects_M2_when_gate_true_otherwise_M1":True,
        "gate_2022_chosen_from_already_inspected_outcomes":True,
        "M1_M2_contrast_frozen_2018_21_not_2022_outcome_selected":True,
        "grouping_2024_is_eligible_record_presence_not_survival_or_fitness":True,
        "horse_equal_contributions_no_hidden_start_weight_reweighting":True,
        "reported_scopes":results,
        "frozen_M1_vs_M2_group_observation_benchmark":benchmarks,
        "information_switch_identity_not_mechanism_of_biological_aging_or_genetic_selection":True,
        "no_individual_source_horse_sire_race_day_or_predictions_exported":True,
    }


def run(archive:Path, sqlite:Path) -> dict:
    from ecology_japan_2022_24_gate_shift_decomposition import (
        load_sources, predictions_stronger_old_history, strict_mask_exact_horse_race,
        fixed_sourceA_context, select_rule_with_2022_only, gate_mask,
        year_fixed_comparison, EXPECTED_YEAR_SCORES, PREVIOUS_RULE,
        SOURCE_A_SHA, SQLITE_SHA, STRICT_HORSES, STRICT_ROWS
    )
    raw, old, f, _, gate, _=load_sources(archive,sqlite)
    p1,p2,_,_=predictions_stronger_old_history(raw,old,f)
    strict,qa=strict_mask_exact_horse_race(
        raw,f,sqlite,gate["two_event_anchor_horses"])
    t=f.loc[strict].reset_index(drop=True)
    if len(t)!=STRICT_ROWS or t.horse.nunique()!=STRICT_HORSES or qa["strict_races"]!=35333:
        raise ValueError("HOLD_SOURCE_A_B_STRICT_RACE_COHORT_CHANGED")
    p1,p2=np.asarray(p1,float)[strict],np.asarray(p2,float)[strict]
    ctx,_=fixed_sourceA_context(old,t)
    first=t.year.eq(2022).to_numpy(bool)
    rule,choice=select_rule_with_2022_only(
        t.loc[first].reset_index(drop=True),
        ctx.loc[first].reset_index(drop=True),p1[first],p2[first])
    if choice["selected_rule_name"]!=PREVIOUS_RULE:
        raise ValueError("HOLD_PREVIOUS_2022_MG_GATE_RESELECTED")
    for year in (2022,2023,2024):
        flag=t.year.eq(year).to_numpy(bool)
        z=t.loc[flag].reset_index(drop=True)
        chosen=gate_mask(ctx.loc[flag].reset_index(drop=True),rule)
        score=year_fixed_comparison(z,p1[flag],p2[flag],chosen,with_ci=False)
        for mod,key in (("M0","RMSE_midpoint"),("M1","RMSE_own_M1"),
                        ("M2","RMSE_always_family_M2"),("gate","RMSE_2022_chosen_gate")):
            if abs(score[key]-EXPECTED_YEAR_SCORES[str(year)][mod])>1e-8:
                raise ValueError("HOLD_YEARLY_2022_24_ORIGINAL_MODELS_DRIFT")
        if score["starts"]!=EXPECTED_YEAR_SCORES[str(year)]["starts"]:
            raise ValueError("HOLD_2022_24_STRICT_YEAR_STARTS_DRIFT")
    p=t.loc[first,["horse","race","day","sire_id"]].reset_index(drop=True)
    p["gain"]=np.zeros(len(p))  # replaced with model-exact value above
    p["own_bin"]=ctx.loc[first,"own_record_count_bin"].reset_index(drop=True)
    out=audit_switches(
        p, set(t.loc[t.year.eq(2023)].horse.astype(str)),
        set(t.loc[t.year.eq(2024)].horse.astype(str)),
        chosen_family=gate_mask(ctx.loc[first].reset_index(drop=True),rule),
        frozen_m1=p1[first],frozen_m2=p2[first],
        y=t.loc[first].y.to_numpy(float),
        source_lock=True
    )
    if out["source_population_2022_horses"]!=12755:
        raise ValueError("HOLD_2022_INFORMATION_SWITCH_COHORT_DRIFT")
    return {
        **out,
        "source_A_SHA256":SOURCE_A_SHA,
        "source_B_SHA256":SQLITE_SHA,
        "original_strict_horses":STRICT_HORSES,
        "original_strict_starts":STRICT_ROWS,
        "original_strict_races":35333,
        "original_training_2018_21_and_2022_gate_preserved":True,
        "year2024_M2_and_MG_worse_than_fixed_midpoint_M0":True,
        "no_official_JRA_studbook_ID_or_2027_known_on_verified":True,
        "no_real_genomic_A_G_MSTN_or_market_odds_time_series_join":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",type=Path,required=True)
    ap.add_argument("--sqlite",type=Path,required=True)
    ap.add_argument("--aggregate-out",type=Path,required=True)
    a=ap.parse_args()
    j=run(a.archive,a.sqlite)
    a.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
    a.aggregate_out.write_text(json.dumps(j,ensure_ascii=False,
                                          sort_keys=True,allow_nan=False,indent=2)+"\n",
                               encoding="utf-8")
    print(json.dumps(j,ensure_ascii=False,sort_keys=True,allow_nan=False))


if __name__=="__main__":
    main()
