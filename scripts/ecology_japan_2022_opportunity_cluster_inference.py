#!/usr/bin/env python3
"""Source-locked post-hoc uncertainty of 2022 observation-opportunity-adjusted MG loss.

Extend the existing six opportunity-standardization point estimates, without
changing 2022 animals, coefficients, race outcomes, older four-bin history
values or future-record classifications. Fixed full-2022 scope weights;
2022 final month and number of 2022 recorded starts are POST-OUTCOME
observation proxies, not known-on forecasting features or causal variables.
No source-level horse, race, sire, day or individual residual is exported.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

from ecology_japan_2022_observation_selection_dependence import (
    _validated_2022_panel, EXPECTED as OLD_EXPECTED
)
from ecology_japan_2022_24_dependency_sensitivity import _cluster_variance, _interval
from ecology_japan_2022_24_observation_paths import (
    _opportunity_standardization, analyze_paths, EXPECTED_STATES
)

STATUS = "POSTHOC_2022_OPPORTUNITY_HORSE_DATE_SIRE_CLUSTERS_NOT_CAUSAL"
SPECIFICATIONS = (
    ("all_2022", ("own_bin", "last_2022_half")),
    ("all_2022", ("own_bin", "recorded_2022_starts_bin")),
    ("all_2022", ("own_bin", "last_2022_half", "recorded_2022_starts_bin")),
    ("observed_2023", ("own_bin", "last_2022_half")),
    ("observed_2023", ("own_bin", "recorded_2022_starts_bin")),
    ("observed_2023", ("own_bin", "last_2022_half", "recorded_2022_starts_bin")),
)
EXPECTED_POINT = {
    "all_2022__own_bin__last_2022_half": -0.00007740339889992373,
    "all_2022__own_bin__recorded_2022_starts_bin": -0.00007692714652507203,
    "observed_2023__own_bin__recorded_2022_starts_bin": -0.0000751566374547203,
}
EXPECTED_HOLD_CELLS = {
    "all_2022__own_bin__last_2022_half__recorded_2022_starts_bin": 4,
    "observed_2023__own_bin__last_2022_half": 2,
    "observed_2023__own_bin__last_2022_half__recorded_2022_starts_bin": 7,
}
Z_95 = 1.959963984540054
Z_SIX = 2.638257273476751  # familywise 95%, all six investigated specifications


def _source_panel(panel: pd.DataFrame, present2023: set[str],
                  present2024: set[str]) -> pd.DataFrame:
    p = _validated_2022_panel(panel)
    h = p.groupby("horse", observed=True, sort=False).agg(
        gain=("gain", "mean"), nstarts=("race", "size"),
        last_day=("day", "max"), own_bin=("own_bin", "first"),
        sire_id=("sire_id", "first")
    ).reset_index()
    ids23 = set(str(x) for x in present2023)
    ids24 = set(str(x) for x in present2024)
    h["observed2023"] = h.horse.isin(ids23)
    h["observed2024"] = h.horse.isin(ids24)
    h["last_2022_half"] = np.where(h.last_day.dt.month.le(6), "Jan-Jun", "Jul-Dec")
    h["recorded_2022_starts_bin"] = np.where(h.nstarts.le(4), "1-4", "5+")
    return h


def evaluate_opportunity(panel: pd.DataFrame, present2023: set[str],
                         present2024: set[str], *, source_lock: bool = False,
                         draws: int = 999, seed: int = 20221125,
                         min_group: int = 30, min_sires: int = 30,
                         min_days: int = 30) -> dict:
    p = _validated_2022_panel(panel)
    h = _source_panel(p, present2023, present2024)
    if min(min_group, min_sires, min_days, draws) < 2:
        raise ValueError("HOLD_INVALID_OPPORTUNITY_CLUSTER_SUPPORT_THRESHOLD")
    if source_lock:
        if len(h)!=12755 or len(p)!=120381 or h.observed2023.sum()!=8659 or h.observed2024.sum()!=5163:
            raise ValueError("HOLD_SOURCE_LOCKED_2022_HORSE_START_YEAR_PARITY")
    # Each source-connected 2022 horse is sampled once, no pseudoreplication.
    h["sire_group"] = np.where(h.sire_id.eq(""), "UNKNOWN_SINGLETON:"+h.horse,
                                "RECORDED_SIRE:"+h.sire_id)
    sire_sizes = h.sire_group.value_counts()
    sire_n = len(sire_sizes)
    base = {
        "status": STATUS,
        "2022_horses": int(len(h)),
        "2022_starts": int(len(p)),
        "2023_observed_horses": int(h.observed2023.sum()),
        "2024_observed_horses": int(h.observed2024.sum()),
        "recorded_sire_plus_unknown_singleton_clusters": sire_n,
        "max_horses_sharing_source_A_recorded_sire": int(sire_sizes.max()),
        "sire_missing_horses_as_singletons": int(h.sire_id.eq("").sum()),
        "six_preselected_opportunity_specifications_familywise_test": True,
        "familywise_z_for_six": Z_SIX,
        "year_2022_last_record_and_2022_starts_not_known_on_earlier_races": True,
        "year_2024_record_absence_not_retirement_death_or_breeding_fitness": True,
        "no_three_way_joint_cluster_claim": True,
        "original_MG_selected_on_2022_outcomes_and_all_results_posthoc": True,
        "no_sire_horse_race_day_individual_predictions_or_residuals_exported": True,
    }
    if sire_n < min_sires:
        return {**base, "status": "HOLD_TOO_FEW_SIRE_CLUSTERS"}
    p_counts = p.groupby("horse",observed=True).size().rename("starts")
    if not p_counts.reindex(h.horse).to_numpy().astype(int).tolist() == h.nstarts.to_numpy().tolist():
        raise ValueError("HOLD_OPPORTUNITY_HORSE_START_COUNTS_CHANGED")
    results = {}
    for ix, (scope, dims) in enumerate(SPECIFICATIONS):
        key = scope+"__"+"__".join(dims)
        sub = h.loc[h.observed2023] if scope == "observed_2023" else h
        # Verify original aggregate point and HOLD, rather than redefining
        # the population until a favorable result appears.
        earlier = _opportunity_standardization(
            h, h.observed2023.to_numpy(bool) if scope == "observed_2023"
            else np.ones(len(h),bool), dims, min_group=min_group
        )
        basic = {
            "status": earlier["status"],
            "source_scope": scope, "controls": list(dims),
            "horses": int(len(sub)),
            "supported_or_attempted_strata": int(earlier["planned_nonempty_strata"]),
            "unsupported_strata": int(earlier["strata_with_insufficient_or_missing_future_2024_group"]),
            "year2022_target_mix_held_fixed_within_scope": True,
            "horse_by_2022_calendar_date_and_sire_inference_separate": True,
        }
        if earlier["status"].startswith("HOLD_"):
            if source_lock and EXPECTED_HOLD_CELLS.get(key) != basic["unsupported_strata"]:
                raise ValueError("HOLD_LOCKED_2022_OPPORTUNITY_SPARSE_GROUPS_CHANGED_"+key)
            results[key] = basic
            continue
        delta = float(earlier["2024_observed_minus_unobserved_MG_vs_M2_gain"])
        if source_lock and abs(delta-EXPECTED_POINT[key]) > 1e-8:
            raise ValueError("HOLD_PRIOR_2022_OPPORTUNITY_STANDARDIZED_POINT_CHANGED_"+key)
        work = sub.reset_index(drop=True).copy()
        # Fixed target distribution of 2022 horse candidates in the scope.
        levels = work.groupby(list(dims), observed=True, sort=True, dropna=False).size()
        total = len(work)
        work["sire_group"] = np.where(
            work.sire_id.eq(""),"UNKNOWN_SINGLETON:"+work.horse,
            "RECORDED_SIRE:"+work.sire_id)
        work["q"] = 0.
        weights = {}
        # Use exact categorical tuple indices (no string concat collision).
        for level, ns in levels.items():
            lev = level if isinstance(level, tuple) else (level,)
            cmask = np.ones(len(work),bool)
            for dim,val in zip(dims,lev):
                cmask &= work[dim].eq(val).to_numpy(bool)
            w = float(ns/total)
            for flag in (False, True):
                m = cmask & work.observed2024.eq(flag).to_numpy(bool)
                ng = int(m.sum())
                if ng < min_group:
                    raise ValueError("HOLD_OPPORTUNITY_POINT_CLUSTER_SUPPORT_INCONSISTENT")
                avg = float(work.loc[m, "gain"].mean())
                work.loc[m, "q"] = (w/float(ng))*(1. if flag else -1.)*(
                    work.loc[m,"gain"]-avg
                )
                weights[(lev,flag)] = (ng, float(work.loc[m,"gain"].sum()), w)
        # Conditioning on the observed 2022 stratum composition is explicit.
        if abs(float(work.q.sum()))>1e-12:
            raise ValueError("HOLD_FIXED_2022_STRATA_SCORE_NOT_CENTERED")
        d = p.loc[p.horse.isin(work.horse)].copy()
        if len(d) != int(work.nstarts.sum()):
            raise ValueError("HOLD_SAME_HORSE_STARTS_NOT_COVERED")
        lookup=work.set_index("horse")
        d["q"] = d.horse.map(lookup.q) / d.horse.map(lookup.nstarts)
        if d.q.isna().any() or abs(float(d.q.sum()))>1e-12:
            raise ValueError("HOLD_OPPORTUNITY_ROW_INFLUENCE_NO_HORSE_PARITY")
        nh, vh = _cluster_variance(d, ["horse"])
        nd, vd = _cluster_variance(d, ["day"])
        n_hd, v_hd = _cluster_variance(d, ["horse","day"])
        # Numerical horse-only check against direct horse-level linearization.
        expected_h=(nh/(nh-1))*float(np.square(work.q).sum())
        if abs(vh-expected_h)>1e-14:
            raise ValueError("HOLD_OPPORTUNITY_HORSE_CLUSTER_PARITY")
        basic.update({
            "standardized_2022_MSE_gain_present_minus_absent": delta,
            "horse_clusters": nh, "calendar_day_clusters": nd,
            "horse_day_intersections": n_hd,
            "horse_CR0_SE": float(np.sqrt(vh)),
            "calendar_CR0_SE": float(np.sqrt(vd)),
        })
        if min(nh,nd,n_hd)<min_days:
            basic["two_way_status"]="HOLD_INSUFFICIENT_HORSE_OR_DAY_CLUSTERS"
        else:
            var=vh+vd-v_hd
            basic["two_way_CR0_variance"]=float(var)
            if not np.isfinite(var) or var<=1e-24:
                basic["two_way_status"]="HOLD_NONPOSITIVE_TWO_WAY_CLUSTER_VARIANCE"
            else:
                se=float(np.sqrt(var))
                basic.update({
                    "two_way_status":"POSTHOC_TWO_WAY_HORSE_DATE_LINEARIZED_CR0",
                    "two_way_se":se,
                    "two_way_95pct_sensitivity_interval":_interval(delta,se,Z_95),
                    "six_opportunity_specs_bonferroni_95pct_interval":_interval(delta,se,Z_SIX),
                    "two_way_interval_contains_zero":bool(abs(delta)<=Z_95*se),
                    "bonferroni_six_interval_contains_zero":bool(abs(delta)<=Z_SIX*se),
                })
        # Recompute whole recorded-sire clusters, not horses sampled
        # individually; each cluster preserves its shared source label.
        cells=list(weights)
        ngroups=work.sire_group.nunique()
        sire_to_idx={v:i for i,v in enumerate(sorted(work.sire_group.unique()))}
        cell_to_idx={v:i for i,v in enumerate(cells)}
        group_counts=np.zeros((ngroups,len(cells)),float)
        group_sum=np.zeros_like(group_counts)
        for row in work.itertuples(index=False):
            lev=tuple(getattr(row, dim) for dim in dims)
            j=cell_to_idx[(lev,bool(row.observed2024))]
            i=sire_to_idx[row.sire_group]
            group_counts[i,j]+=1
            group_sum[i,j]+=float(row.gain)
        n0=group_counts.sum(axis=0)
        s0=group_sum.sum(axis=0)
        def fixed_mix_effect(counts, totals):
            # Reference weights taken ONLY from the initial 2022 subcohort.
            avg=totals/counts
            z=0.
            for lev in levels.index:
                keylev=lev if isinstance(lev,tuple) else (lev,)
                w=weights[(keylev,False)][2]
                z+=w*(avg[cell_to_idx[(keylev,True)]] -
                      avg[cell_to_idx[(keylev,False)]])
            return float(z)
        if abs(fixed_mix_effect(n0,s0)-delta)>1e-12:
            raise ValueError("HOLD_RECORDED_SIRE_MATRIX_POINT_ESTIMATE_PARITY")
        rng=np.random.default_rng(seed+ix)
        values=[]
        rejected=0
        for _ in range(draws):
            idx=rng.integers(0,ngroups,size=ngroups)
            nn=group_counts[idx].sum(axis=0)
            ss=group_sum[idx].sum(axis=0)
            if (nn<max(2,min_group//10)).any():
                rejected+=1
                continue
            values.append(fixed_mix_effect(nn,ss))
        basic["sire_resample_draws_requested"]=draws
        basic["sire_resamples_rejected_for_support"]=rejected
        basic["sire_clusters_in_this_scope"]=ngroups
        if len(values)<draws*.99:
            basic["sire_status"]="HOLD_SIRE_BOOTSTRAP_GROUP_STRATUM_SUPPORT"
        else:
            lo,hi=np.quantile(values,[.025,.975])
            basic.update({
                "sire_status":"POSTHOC_ENTIRE_RECORDED_SIRE_CLUSTER_RESAMPLING",
                "sire_95pct_percentile_sensitivity_interval":[float(lo),float(hi)],
                "sire_interval_contains_zero":bool(lo<=0<=hi),
            })
        results[key]=basic
    if source_lock and sum(x["status"].startswith("HOLD_") for x in results.values())!=3:
        raise ValueError("HOLD_OLD_SPARSE_STRATUM_SETS_CHANGED")
    return {**base,"results":results}


def run(archive:Path, sqlite:Path)->dict:
    from ecology_japan_2022_24_gate_shift_decomposition import (
        load_sources, predictions_stronger_old_history, strict_mask_exact_horse_race,
        fixed_sourceA_context, select_rule_with_2022_only, gate_mask, switch_prediction,
        year_fixed_comparison, EXPECTED_YEAR_SCORES, PREVIOUS_RULE,
        SOURCE_A_SHA, SQLITE_SHA, STRICT_ROWS, STRICT_HORSES,
    )
    raw,old,f,_,gate,_=load_sources(archive,sqlite)
    p1,p2,_,_=predictions_stronger_old_history(raw,old,f)
    mask,qa=strict_mask_exact_horse_race(raw,f,sqlite,gate["two_event_anchor_horses"])
    t=f.loc[mask].reset_index(drop=True)
    if len(t)!=STRICT_ROWS or t.horse.nunique()!=STRICT_HORSES or qa["strict_races"]!=35333:
        raise ValueError("HOLD_PREVIOUS_SOURCE_STRICT_COHORT_CHANGED")
    p1,p2=np.asarray(p1,float)[mask],np.asarray(p2,float)[mask]
    context,_=fixed_sourceA_context(old,t)
    m22=t.year.eq(2022).to_numpy(bool)
    rule,choice=select_rule_with_2022_only(
        t.loc[m22].reset_index(drop=True),
        context.loc[m22].reset_index(drop=True),p1[m22],p2[m22])
    if choice["selected_rule_name"]!=PREVIOUS_RULE:
        raise ValueError("HOLD_OLD_2022_CHOSEN_GATE_CHANGED")
    for year in (2022,2023,2024):
        ix=t.year.eq(year).to_numpy(bool)
        y=t.loc[ix].reset_index(drop=True)
        g=gate_mask(context.loc[ix].reset_index(drop=True),rule)
        score=year_fixed_comparison(y,p1[ix],p2[ix],g,with_ci=False)
        ref=EXPECTED_YEAR_SCORES[str(year)]
        if score["starts"]!=ref["starts"] or any(
            abs(score[k]-ref[b])>1e-8 for b,k in (
                ("M0","RMSE_midpoint"),("M1","RMSE_own_M1"),
                ("M2","RMSE_always_family_M2"),("gate","RMSE_2022_chosen_gate"))
        ):
            raise ValueError("HOLD_ORIGINAL_YEAR_RANK_SCORE_CHANGED")
    panel=t.loc[m22,["horse","race","day","sire_id"]].reset_index(drop=True)
    yy=t.loc[m22].y.to_numpy(float)
    pg=switch_prediction(
        p1[m22],p2[m22],
        gate_mask(context.loc[m22].reset_index(drop=True),rule)
    )
    panel["gain"]=(yy-p2[m22])**2-(yy-pg)**2
    panel["own_bin"]=context.loc[m22,"own_record_count_bin"].reset_index(drop=True)
    record23=set(t.loc[t.year.eq(2023)].horse.astype(str))
    record24=set(t.loc[t.year.eq(2024)].horse.astype(str))
    # Recompute existing path evidence and source-/score-level old value
    # to guarantee that inference extends EXACTLY the old 2022 panel.
    previous=analyze_paths(panel,record23,record24,expected_states=EXPECTED_STATES,
                           source_lock=True,sire_draws=399)
    result=evaluate_opportunity(panel,record23,record24,source_lock=True)
    if abs(previous["2024_gap"]-OLD_EXPECTED["contrast"])>1e-10:
        raise ValueError("HOLD_PREVIOUS_OBSERVATION_2024_GAP_CHANGED")
    return {
        **result,
        "source_A_SHA256":SOURCE_A_SHA,
        "source_B_SHA256":SQLITE_SHA,
        "source_2022_2024_strict_horses":STRICT_HORSES,
        "source_2022_2024_strict_starts":STRICT_ROWS,
        "source_2022_2024_strict_races":35333,
        "prior_four_observation_paths_verified":True,
        "original_2018_21_coefficients_and_2022_chosen_gate_fixed":True,
        "historical_2024_M2_and_MG_both_worse_than_M0":True,
        "2024_observation_outcome_not_biological_survival":True,
        "formal_registration_IDs_and_time_varying_market_not_linked":True,
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
                                          allow_nan=False,indent=2,sort_keys=True)+"\n",
                               encoding="utf-8")
    print(json.dumps(j,ensure_ascii=False,allow_nan=False,sort_keys=True))


if __name__=="__main__":
    main()
