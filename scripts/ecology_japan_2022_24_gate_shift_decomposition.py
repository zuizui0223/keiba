#!/usr/bin/env python3
"""Decompose the FAILED 2022-learned family-information gate on 2023/24.

Only original fixed 244147 strict 2022-24 classified starts, old-source A/B
SHA, previously frozen 2018-21 M1/M2 ridge, and already-selected 2022
own<=15 / parent-peer>=1 gate. No new model, optimized thresholds or horse
source records exported. Entire analysis is POST-HOC after inspecting years.

Decompose horse-equal-weighted MSE advantage of GATE over always-parent M2:
  D_y = sum_b w_yb * d_yb
  D_y - D_2022 =
       sum_b (w_yb - w_2022b) * d_2022b  [own-bin COMPOSITION]
     + sum_b w_yb * (d_yb - d_2022b)    [WITHIN-BIN change].
This algebra is exact, but not a causal mediation decomposition: different
racing cohorts, source B labels and environment change within each bin.
Family info age is fixed at pre-2022; no actual registered JRA ID/known-on.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_2022_joint_strict_strong import (
    strict_mask_exact_horse_race, predictions_stronger_old_history,
    STRICT_HORSES, STRICT_ROWS,
)
from ecology_japan_2022_2024_kin_information_moderators import (
    fixed_sourceA_context, LOCKED_STRICT_NO, LOCKED_STRICT_KIN,
    LOCKED_STRICT_MID, OWN_NAMES,
)
from ecology_japan_2022_trained_family_gate import (
    gate_mask, select_rule_with_2022_only, switch_prediction,
    year_fixed_comparison, EXPECTED_YEARS
)
from ecology_japan_2022_independent_forward import _scores

STATUS = "POSTHOC_2022_TO_2024_KIN_GATE_COMPOSITION_VS_WITHIN_BIN_MSE_NOT_CAUSAL"
SOURCE_A_SHA = "c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f"
PREVIOUS_RULE = "own_upto_8to15__peer_from_one_recorded_peer"
MIN_BIN_STARTS = 120
MIN_BIN_HORSES = 30
ABS_TOL = 5e-12

EXPECTED_YEAR_SCORES = {
    "2022": {"M0":0.3221321594881176,"M1":0.3100595066614328,
             "M2":0.309804310250263,"gate":0.30972684214623947,
             "starts":120381},
    "2023": {"M0":0.3204516628348531,"M1":0.31789412624407515,
             "M2":0.3175663502644569,"gate":0.31765341385178414,
             "starts":80939},
    "2024": {"M0":0.3180587844880855,"M1":0.3198657266599239,
             "M2":0.31925671437194697,"gate":0.3194679718134001,
             "starts":42827},
}


def horse_equal_weights(horses) -> np.ndarray:
    h=pd.Series(horses).astype(str).reset_index(drop=True)
    if h.isna().any() or (h=="").any() or not len(h):
        raise ValueError("HOLD_EMPTY_OR_INVALID_FOCAL_HORSE_ID")
    counts=h.value_counts()
    w=1/h.map(counts).to_numpy(float)
    w/=w.sum()
    if not np.isclose(w.sum(),1.,atol=1e-12):
        raise ValueError("HOLD_HORSE_WEIGHT_NORMALIZATION")
    return w


def by_own_info_bin(t, own_bins, p2, pg, *, min_starts=MIN_BIN_STARTS,
                    min_horses=MIN_BIN_HORSES) -> dict:
    n=len(t)
    bins=pd.Series(own_bins).astype(str).reset_index(drop=True)
    x=np.asarray(p2,float)
    z=np.asarray(pg,float)
    if n!=len(bins) or n!=len(x) or n!=len(z) or n==0:
        raise ValueError("HOLD_DECOMPOSITION_ROW_LENGTH")
    if not bins.isin(OWN_NAMES).all():
        raise ValueError("HOLD_UNEXPECTED_OWN_HISTORY_BIN")
    y=t.y.to_numpy(float)
    if (not np.isfinite(y).all() or not np.isfinite(x).all()
        or not np.isfinite(z).all()
        or np.any((y<0)|(y>1)|(x<0)|(x>1)|(z<0)|(z>1))):
        raise ValueError("HOLD_NONFINITE_OR_OUT_OF_BOUNDS_NORMALIZED_SCORE")
    w=horse_equal_weights(t.horse)
    loss2=(y-x)**2
    lossg=(y-z)**2
    d=loss2-lossg
    c={}
    for group in OWN_NAMES:
        ix=bins.eq(group).to_numpy()
        subset=t.loc[ix]
        support={"starts":int(ix.sum()),
                 "horses":int(subset.horse.nunique()),
                 "race_days":int(subset.day.nunique())}
        if support["starts"]<min_starts or support["horses"]<min_horses:
            c[group]={**support,
                "status":"HOLD_OWN_HISTORY_BIN_NOT_ENOUGH_TO_STANDARDIZE"}
            continue
        share=float(w[ix].sum())
        change=float(np.average(d[ix],weights=w[ix]))
        c[group]={
            **support,
            "status":"POSTHOC_OWN_HISTORY_SOURCE_A_BIN",
            "share_equal_horse_weight":share,
            "share_raw_starts":float(np.mean(ix)),
            "conditional_MSE_advantage_GATE_minus_always_M2":change,
            "conditional_MSE_always_M2":float(
                np.average(loss2[ix],weights=w[ix])),
            "conditional_MSE_gate":float(
                np.average(lossg[ix],weights=w[ix])),
        }
    overall={
        "starts":n,"horses":int(t.horse.nunique()),
        "race_days":int(t.day.nunique()),
        "MSE_always_M2":float(np.sum(w*loss2)),
        "MSE_gate":float(np.sum(w*lossg)),
        "MSE_advantage_GATE_over_always_M2":float(np.sum(w*d)),
        "RMSE_always_M2":float(np.sqrt(np.sum(w*loss2))),
        "RMSE_gate":float(np.sqrt(np.sum(w*lossg))),
        "cells":c,
    }
    if all(v.get("status")=="POSTHOC_OWN_HISTORY_SOURCE_A_BIN" for v in c.values()):
        covered=sum(v["share_equal_horse_weight"] for v in c.values())
        recon=sum(v["share_equal_horse_weight"]*
                  v["conditional_MSE_advantage_GATE_minus_always_M2"]
                  for v in c.values())
        if not (abs(covered-1)<ABS_TOL
                and abs(recon-overall["MSE_advantage_GATE_over_always_M2"])<ABS_TOL):
            raise ValueError("HOLD_OWN_BIN_MSE_NOT_RECONSTRUCTED")
        overall["all_predeclared_bins_standardizable"]=True
    else:
        overall["all_predeclared_bins_standardizable"]=False
    return overall


def exact_oaxaca(reference:dict, later:dict) -> dict:
    """2022-reference exact composition vs within-own-bin comparison."""
    cells0=reference["cells"]
    cells1=later["cells"]
    if not reference["all_predeclared_bins_standardizable"] or not (
            later["all_predeclared_bins_standardizable"]):
        return {"status":"HOLD_NO_FULL_OWN_BIN_OVERLAP_FOR_DECOMPOSITION"}
    comp=0.
    within=0.
    values={}
    for k in OWN_NAMES:
        r,l=cells0[k],cells1[k]
        a=r["share_equal_horse_weight"]
        b=l["share_equal_horse_weight"]
        d0=r["conditional_MSE_advantage_GATE_minus_always_M2"]
        d1=l["conditional_MSE_advantage_GATE_minus_always_M2"]
        composition=(b-a)*d0
        within_bin=b*(d1-d0)
        comp+=composition
        within+=within_bin
        values[k]={
            "2022_equal_horse_weight_share":a,
            "later_equal_horse_weight_share":b,
            "2022_conditional_MSE_advantage":d0,
            "later_conditional_MSE_advantage":d1,
            "composition_component_reference_2022":composition,
            "within_bin_component_reference_2022":within_bin,
            "not_a_matched_horse_counterfactual":True,
        }
    target=float(later["MSE_advantage_GATE_over_always_M2"]-
                 reference["MSE_advantage_GATE_over_always_M2"])
    if not (np.isclose(comp+within,target,atol=ABS_TOL,rtol=0)
        and np.isclose(sum(x["composition_component_reference_2022"]+
                           x["within_bin_component_reference_2022"]
                           for x in values.values()),target,atol=ABS_TOL,rtol=0)):
        raise ValueError("HOLD_DECOMPOSITION_NOT_ALGEBRAICALLY_EXACT")
    return {
        "status":"EXACT_ALGEBRAIC_DESCRIPTIVE_STANDARDIZATION_NOT_CAUSAL",
        "MSE_advantage_change_from_2022":target,
        "composition_change_using_2022_bin_effects":float(comp),
        "within_bin_prediction_effect_change_at_later_weights":float(within),
        "composition_plus_within_equals_total":True,
        "conditional_group_membership_not_same_matched_individuals":True,
        "year_specific_environment_and_source_vintage_still_confound_within_bin":True,
        "MSE_NOT_RMSE_additivity":True,
        "cells":values,
    }


def shared_eligible_horse_coverage(by_year):
    """Observed participation overlap, NOT survival, retirement or fitness."""
    sets={str(k):set(v.horse.astype(str)) for k,v in by_year.items()}
    q={}
    for start,end in (("2022","2023"),("2022","2024"),("2023","2024")):
        a,b=sets[start],sets[end]
        q[start+"_to_"+end]={
            "first_year_observed_distinct_horses":len(a),
            "later_year_observed_distinct_horses":len(b),
            "same_candidate_horse_in_both_years":len(a&b),
            "later_year_fraction_also_seen_in_first":float(len(a&b)/len(b)),
            "first_year_fraction_also_seen_in_later":float(len(a&b)/len(a)),
        }
    return {
        "status":"OBSERVED_COHORT_PARTICIPATION_OVERLAP_NOT_SURVIVAL_OR_BREEDING",
        "pairs":q,
    }


def analyze(archive:Path, sqlite:Path) -> dict:
    raw,old,f,_,gate,qa=load_sources(archive,sqlite)
    m1_all,m2_all,_,_=predictions_stronger_old_history(raw,old,f)
    mask,source_qa=strict_mask_exact_horse_race(
        raw,f,sqlite,gate["two_event_anchor_horses"])
    t=f.loc[mask].reset_index(drop=True)
    if len(t)!=STRICT_ROWS or int(t.horse.nunique())!=STRICT_HORSES:
        raise ValueError("HOLD_ORIGINAL_244147_STRICT_SAMPLE_CHANGED")
    if source_qa["strict_races"]!=35333:
        raise ValueError("HOLD_STRICT_COMPLETE_RACES_CHANGED")
    p1=np.asarray(m1_all,float)[mask]
    p2=np.asarray(m2_all,float)[mask]
    original=_scores(t,p1,p2)
    for k,v in (("RMSE_portable_no_kin",LOCKED_STRICT_NO),
                ("RMSE_portable_kin",LOCKED_STRICT_KIN),
                ("RMSE_unchanged_midpoint",LOCKED_STRICT_MID)):
        if abs(original[k]-v)>1e-8:
            raise ValueError("HOLD_ORIGINAL_2022_24_RMSE_PARITY")
    ctx,context_qa=fixed_sourceA_context(old,t)
    is_22=t.year.eq(2022).to_numpy()
    selected,choice=select_rule_with_2022_only(
        t.loc[is_22].reset_index(drop=True),
        ctx.loc[is_22].reset_index(drop=True),p1[is_22],p2[is_22])
    if choice["selected_rule_name"]!=PREVIOUS_RULE:
        raise ValueError("HOLD_PREVIOUS_2022_RULE_NOT_REPRODUCED")

    scored={}
    original_year={}
    by_year={}
    for year in EXPECTED_YEARS:
        name=str(year)
        ix=t.year.eq(year).to_numpy()
        year_t=t.loc[ix].reset_index(drop=True)
        by_year[name]=year_t
        year_ctx=ctx.loc[ix].reset_index(drop=True)
        g=gate_mask(year_ctx,selected)
        pg=switch_prediction(p1[ix],p2[ix],g)
        scored[name]=by_own_info_bin(
            year_t,year_ctx.own_record_count_bin,
            p2[ix],pg
        )
        numeric=year_fixed_comparison(
            year_t,p1[ix],p2[ix],g,with_ci=False)
        original_year[name]=numeric
        expected=EXPECTED_YEAR_SCORES[name]
        if numeric["starts"]!=expected["starts"]:
            raise ValueError("HOLD_LOCKED_YEAR_STARTS_CHANGED")
        for k,col in (("M0","RMSE_midpoint"),
                      ("M1","RMSE_own_M1"),
                      ("M2","RMSE_always_family_M2"),
                      ("gate","RMSE_2022_chosen_gate")):
            if abs(numeric[col]-expected[k])>1e-8:
                raise ValueError("HOLD_ORIGINAL_YEAR_SCORE_CHANGED_"+name+"_"+k)
        if abs(scored[name]["RMSE_gate"]-numeric["RMSE_2022_chosen_gate"])>ABS_TOL:
            raise ValueError("HOLD_NEW_MSE_YEAR_SCORE_DOES_NOT_MATCH_RMSE")
        if abs(scored[name]["RMSE_always_M2"]-numeric["RMSE_always_family_M2"])>ABS_TOL:
            raise ValueError("HOLD_NEW_MSE_FAMILY_SCORE_DOES_NOT_MATCH_RMSE")
    comparisons={
        "2022_to_2023":exact_oaxaca(scored["2022"],scored["2023"]),
        "2022_to_2024":exact_oaxaca(scored["2022"],scored["2024"])
    }
    if any(x["status"].startswith("HOLD") for x in comparisons.values()):
        raise ValueError("HOLD_2022_REFERENCE_BIN_MISSING_FOR_TRANSFER")
    if not (original_year["2022"]["RMSE_2022_chosen_gate"] <
            original_year["2022"]["RMSE_always_family_M2"] and
            original_year["2024"]["RMSE_2022_chosen_gate"] >
            original_year["2024"]["RMSE_always_family_M2"] and
            original_year["2024"]["RMSE_2022_chosen_gate"] >
            original_year["2024"]["RMSE_midpoint"]):
        raise ValueError("HOLD_PREVIOUSLY_REPORTED_GATE_FAILURE_NOT_PRESERVED")
    return {
        "status":STATUS,
        "source_A_SHA256":SOURCE_A_SHA,
        "source_B_SHA256":SQLITE_SHA,
        "strict_source_qa":source_qa,
        "locked_all_2022_24_scores":original,
        "selected_rule_2022_only":choice["selected_rule_name"],
        "selection_year_2022_already_inspected":True,
        "same_original_strict_sample_and_original_M1_M2_coefficients":True,
        "outcomes_2023_2024_previously_inspected_so_NOT_independent_test":True,
        "source_A_modifiers_from_pre2022_only":True,
        "source_A_history_published_at_jst_NOT_verified":True,
        "source_A_focal_record_summary":context_qa,
        "actual_all_year_M0_M1_M2_gate_RMSE_parity":original_year,
        "within_year_own_history_cells":scored,
        "ref_2022_exact_MSE_decomposition":comparisons,
        "observed_horse_participation_overlap":shared_eligible_horse_coverage(by_year),
        "no_experimental_intervention_or_causal_attribution":True,
        "no_genetic_A_G_or_MSTN_outcome_link":True,
        "no_breeder_stable_jockey_environment_separated":True,
        "no_market_odds_time_series_or_profitability_result":True,
        "2027_real_pre_race_predictions_submitted":0,
        "no_individual_horse_names_race_IDs_predictions_or_raw_rows_exported":True
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--sqlite",type=Path,required=True)
    p.add_argument("--aggregate-out",type=Path,required=True)
    args=p.parse_args()
    result=analyze(args.archive,args.sqlite)
    args.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
    args.aggregate_out.write_text(json.dumps(
        result,ensure_ascii=False,sort_keys=True,indent=2,
        allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "locked_all_2022_24_scores":result["locked_all_2022_24_scores"],
        "selected_rule_2022_only":result["selected_rule_2022_only"],
        "ref_2022_exact_MSE_decomposition":result["ref_2022_exact_MSE_decomposition"],
        "observed_horse_participation_overlap":result["observed_horse_participation_overlap"],
        "2024_gate_worse_than_M2_and_M0_remains":True,
        "not_causal_genetics_or_independent_prospective_validation":True,
    },ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False),flush=True)


if __name__=="__main__":
    main()
