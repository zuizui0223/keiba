#!/usr/bin/env python3
"""Post-hoc source-locked 2022-learned parent-information gate; 2023/24 transfer.

Use exact A/B SHA, two PRE2022 historic source-identity witnesses, the SAME
2018-21 ridge models and the SAME 244147 strict classified-race test rows.
Fit ONE discrete choice of when to trust SAME-PARENT OTHER-HORSE INFORMATION
using 2022 labels ONLY. Apply unchanged to 2023 and 2024.

This is historical forward-calendar *diagnostics*, NOT an untouched holdout:
the model/design and year-specific results were inspected before this study.
No new coefficients, genetics, JRA/NAR official IDs, odds or source rights.
Only aggregated scores, counts and source QA exit the runner.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_2022_joint_strict_strong import (
    strict_mask_exact_horse_race, predictions_stronger_old_history,
    STRICT_ROWS, STRICT_HORSES,
)
from ecology_japan_2022_2024_kin_information_moderators import (
    fixed_sourceA_context, LOCKED_STRICT_NO, LOCKED_STRICT_KIN, LOCKED_STRICT_MID,
)
from ecology_japan_2022_independent_forward import _scores, _pooled_ci

STATUS="POSTHOC_2022_TRAINED_KIN_GATE_2023_2024_CALENDAR_TRANSFER_NOT_PROSPECTIVE"
SOURCE_A_SHA="c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f"
OWN_BIN_ORDER=("0-3","4-7","8-15","16+")
PEER_BIN_ORDER=("no_recorded_peer","one_recorded_peer","2-4_peers","5+_peers")
MIN_SELECTED_STARTS=500
MIN_SELECTED_HORSES=30
MIN_SELECTED_DAYS=15
BOOTSTRAP_DRAWS=399
EXPECTED_YEARS=(2022,2023,2024)

# Fully explicit fixed search grid. No 2023/24 labels are read to select it.
# Require at least one *other horse's documented outcome* as prerequisite,
# never a fabricated biological relatedness zero.
CANDIDATES=tuple(
    (own_max,peer_min)
    for own_max in (0,1,2,3)
    for peer_min in (1,2,3)
)
RULE_BASELINES=("never_family","always_family")


def rule_name(rule):
    if rule in RULE_BASELINES:
        return rule
    if (not isinstance(rule,tuple) or len(rule)!=2 or
            rule not in CANDIDATES):
        raise ValueError("HOLD_UNDECLARED_PARENT_INFORMATION_GATE")
    own,peer=rule
    return "own_upto_"+OWN_BIN_ORDER[own].replace("+","plus").replace("-","to") + (
        "__peer_from_"+PEER_BIN_ORDER[peer])


def gate_mask(ctx:pd.DataFrame,rule):
    if not {"own_record_count_bin","other_same_parent_horse_count_bin"}.issubset(ctx):
        raise ValueError("HOLD_MISSING_INFORMATION_MODERATOR_FOR_GATE")
    n=len(ctx)
    if rule=="never_family":
        return np.zeros(n,bool)
    if rule=="always_family":
        return np.ones(n,bool)
    if rule not in CANDIDATES:
        raise ValueError("HOLD_UNDECLARED_PARENT_INFORMATION_GATE")
    own=ctx.own_record_count_bin
    peer=ctx.other_same_parent_horse_count_bin
    if not own.isin(OWN_BIN_ORDER).all() or not peer.isin(PEER_BIN_ORDER).all():
        raise ValueError("HOLD_UNKNOWN_PAST_ONLY_INFORMATION_BIN")
    own_idx=own.map({x:i for i,x in enumerate(OWN_BIN_ORDER)}).to_numpy(int)
    peer_idx=peer.map({x:i for i,x in enumerate(PEER_BIN_ORDER)}).to_numpy(int)
    return (own_idx<=rule[0]) & (peer_idx>=rule[1])


def switch_prediction(no_kin,with_kin,selected):
    a=np.asarray(no_kin,float)
    b=np.asarray(with_kin,float)
    gate=np.asarray(selected,bool)
    if not (len(a)==len(b)==len(gate)) or not (
            np.isfinite(a).all() and np.isfinite(b).all()
    ):
        raise ValueError("HOLD_GATE_PREDICTION_VECTOR_PARITY")
    if np.any((a<0)|(a>1)|(b<0)|(b>1)):
        raise ValueError("HOLD_GATE_FORECAST_OUT_OF_RANGE")
    return np.where(gate,b,a)


def _support(t,mask):
    mask=np.asarray(mask,bool)
    if len(mask)!=len(t):
        raise ValueError("HOLD_GATE_SUPPORT_LENGTH")
    subset=t.loc[mask]
    return {
        "starts":int(mask.sum()),
        "horses":int(subset.horse.nunique()),
        "race_days":int(subset.day.nunique()),
        "races":int(subset.race.nunique()),
        "selected_fraction_starts":float(np.mean(mask))
    }


def _supported(s):
    return (s["starts"]>=MIN_SELECTED_STARTS and
            s["horses"]>=MIN_SELECTED_HORSES and
            s["race_days"]>=MIN_SELECTED_DAYS)


def year_fixed_comparison(t,p0,p1,gate,*,with_ci=False):
    """Equal-horse RMSE on exactly same 2022, 2023, or 2024 test rows."""
    if not (len(t)==len(p0)==len(p1)==len(gate)) or not len(t):
        raise ValueError("HOLD_YEAR_SCORE_SHAPE_OR_SUPPORT")
    g=switch_prediction(p0,p1,gate)
    own=_scores(t,p0,p0)
    kin=_scores(t,p0,p1)
    chosen=_scores(t,p0,g)
    if abs(own["RMSE_portable_no_kin"]-kin["RMSE_portable_no_kin"])>1e-12:
        raise ValueError("HOLD_SAME_FOCAL_M1_BASELINE")
    s=_support(t,gate)
    result={
        "starts":int(len(t)),
        "unique_horses":int(t.horse.nunique()),
        "races":int(t.race.nunique()),
        "race_days":int(t.day.nunique()),
        "selected_parent_information_support":s,
        "RMSE_midpoint":float(own["RMSE_unchanged_midpoint"]),
        "RMSE_own_M1":float(own["RMSE_portable_no_kin"]),
        "RMSE_always_family_M2":float(kin["RMSE_portable_kin"]),
        "RMSE_2022_chosen_gate":float(chosen["RMSE_portable_kin"]),
        "M1_minus_selected_gate_RMSE_gain":float(
            own["RMSE_portable_no_kin"]-chosen["RMSE_portable_kin"]
        ),
        "always_family_minus_selected_gate_RMSE_gain":float(
            kin["RMSE_portable_kin"]-chosen["RMSE_portable_kin"]
        ),
        "midpoint_minus_selected_gate_RMSE_gain":float(
            own["RMSE_unchanged_midpoint"]-chosen["RMSE_portable_kin"]
        ),
        "selected_gate_better_than_M1_M2_midpoint_all":bool(
            chosen["RMSE_portable_kin"]<min(
                own["RMSE_portable_no_kin"],kin["RMSE_portable_kin"],
                own["RMSE_unchanged_midpoint"]
            )
        ),
    }
    if with_ci and (t.horse.nunique()>=20 and t.day.nunique()>=20):
        result["oneway_399_horse_or_race_day_CI_vs_M1"]=_pooled_ci(
            t,p0,g,B=BOOTSTRAP_DRAWS
        )
        result["oneway_399_horse_or_race_day_CI_vs_always_M2"]=_pooled_ci(
            t,p1,g,B=BOOTSTRAP_DRAWS
        )
    return result


def select_rule_with_2022_only(t,ctx,p0,p1):
    """NO 2023/24 y or feature information passes into rule selection."""
    if len(t)!=len(ctx) or len(t)!=len(p0) or len(t)!=len(p1):
        raise ValueError("HOLD_TRAINING_GATE_ROW_ALIGNMENT")
    if not np.all(t.year.eq(2022)):
        raise ValueError("HOLD_NON2022_YEAR_LABEL_IN_GATE_TRAINING")
    if t.horse.nunique()<100 or t.day.nunique()<100:
        raise ValueError("HOLD_GATE_TRAIN_2022_LOW_SUPPORT")
    candidates={}
    ranked=[]
    for rule in ("never_family","always_family",*CANDIDATES):
        mask=gate_mask(ctx,rule)
        sc=year_fixed_comparison(t,p0,p1,mask)
        support=sc["selected_parent_information_support"]
        if rule not in RULE_BASELINES and not _supported(support):
            candidates[rule_name(rule)]={
                "status":"HOLD_GATE_2022_SELECTED_GROUP_LOW_SUPPORT",
                "selected_support":support
            }
            continue
        name=rule_name(rule)
        candidates[name]={
            "status":"2022_HISTORICAL_IN_SAMPLE_GATE_SELECTION_CANDIDATE",
            **sc,
        }
        ranked.append((sc["RMSE_2022_chosen_gate"],name,rule))
    if not ranked:
        raise ValueError("HOLD_NO_SUPPORTED_2022_RULE")
    # Deterministic tie-break: prefer never-family by sorted name on
    # exact equal score; prevents positive-result cherry-picking.
    ranked.sort(key=lambda x:(round(x[0],12),x[1]))
    rmse,name,rule=ranked[0]
    return rule,{
        "status":"SELECTED_WITH_ALREADY_INSPECTED_2022_OUTCOMES_ONLY",
        "selected_rule_name":name,
        "selection_criterion":"MINIMUM_2022_EQUAL_HORSE_WEIGHTED_NORMALIZED_RANK_RMSE",
        "selection_candidate_count_total":len(CANDIDATES)+2,
        "selection_candidate_count_supported":len(ranked),
        "minimum_selected_support":{
            "starts":MIN_SELECTED_STARTS,
            "horses":MIN_SELECTED_HORSES,
            "race_days":MIN_SELECTED_DAYS,
        },
        "selected_2022_in_sample_RMSE":float(rmse),
        "all_2022_candidate_results_including_unfavorable":candidates,
        "selection_uses_2023_or_2024_labels":False,
        "not_an_independent_holdout":True,
    }


def analyze(archive:Path,sqlite:Path):
    raw,old,f,_,gate,quality=load_sources(archive,sqlite)
    p0_all,p1_all,allstrong,_=predictions_stronger_old_history(raw,old,f)
    mask,strict_qa=strict_mask_exact_horse_race(
        raw,f,sqlite,gate["two_event_anchor_horses"]
    )
    t=f.loc[mask].reset_index(drop=True)
    if len(t)!=STRICT_ROWS or t.horse.nunique()!=STRICT_HORSES:
        raise ValueError("HOLD_ORIGINAL_STRICT_HORSE_COHORT_CHANGED")
    if strict_qa["strict_races"]!=35333:
        raise ValueError("HOLD_SOURCE_B_COMPLETE_RACES_NOT_35333")
    p0=np.asarray(p0_all)[mask]
    p1=np.asarray(p1_all)[mask]
    baseline=_scores(t,p0,p1)
    for key,val in (
        ("RMSE_portable_no_kin",LOCKED_STRICT_NO),
        ("RMSE_portable_kin",LOCKED_STRICT_KIN),
        ("RMSE_unchanged_midpoint",LOCKED_STRICT_MID),
    ):
        if abs(baseline[key]-val)>1e-8:
            raise ValueError("HOLD_LOCKED_PREVIOUS_STRICT_BASELINE_DRIFT_"+key)
    years=tuple(sorted(int(x) for x in t.year.unique()))
    if years!=EXPECTED_YEARS:
        raise ValueError("HOLD_UNEXPECTED_STRICT_SCORE_YEARS")
    ctx,ctx_qa=fixed_sourceA_context(old,t)
    im22=t.year.eq(2022).to_numpy()
    rule,train=select_rule_with_2022_only(
        t.loc[im22].reset_index(drop=True),
        ctx.loc[im22].reset_index(drop=True),p0[im22],p1[im22]
    )
    year_results={}
    for year in EXPECTED_YEARS:
        idx=t.year.eq(year).to_numpy()
        sub_t=t.loc[idx].reset_index(drop=True)
        sub_ctx=ctx.loc[idx].reset_index(drop=True)
        selected=gate_mask(sub_ctx,rule)
        year_results[str(year)]=year_fixed_comparison(
            sub_t,p0[idx],p1[idx],selected,with_ci=(year!=2022))
        year_results[str(year)]["selected_after_using_2022_labels"]=bool(year==2022)
        year_results[str(year)]["calendar_year_not_used_for_rule_fit"]=bool(
            year!=2022)
    future_idx=t.year.ge(2023).to_numpy()
    future_ctx=ctx.loc[future_idx].reset_index(drop=True)
    future_t=t.loc[future_idx].reset_index(drop=True)
    transferred=year_fixed_comparison(
        future_t,p0[future_idx],p1[future_idx],
        gate_mask(future_ctx,rule),with_ci=True
    )
    if not (
        year_results["2024"]["RMSE_always_family_M2"]>
        year_results["2024"]["RMSE_midpoint"]
    ):
        raise ValueError("HOLD_MISSING_2024_NEGATIVE_BASELINE")
    # Invariance test: expected weighted RMSE from same strict sample.
    full_gate=gate_mask(ctx,rule)
    full=year_fixed_comparison(t,p0,p1,full_gate)
    all_year_count=sum(year_results[str(y)]["starts"] for y in EXPECTED_YEARS)
    if all_year_count!=STRICT_ROWS or full["starts"]!=STRICT_ROWS:
        raise ValueError("HOLD_GATE_STRICT_FOCAL_ROWS_NOT_PRESERVED")
    return {
        "status":STATUS,
        "source_A_SHA256":SOURCE_A_SHA,
        "source_B_SHA256":SQLITE_SHA,
        "source_B_same_studbook_ID_not_certified":True,
        "original_strict_source_QA":strict_qa,
        "locked_pre2022_2018_21_sourceA_ridge_models":True,
        "locked_original_244147_scores":baseline,
        "own_and_family_moderators_from_pre2022_sourceA_only":True,
        "source_record_publication_timestamp_not_certified":True,
        "observed_parent_other_horse_information_not_genomic_A_G":True,
        "shared_environment_breeding_management_not_separated":True,
        "2022_gate_choice_from_historically_observed_labels":train,
        "fixed_selected_rule":"none" if rule=="never_family" else rule_name(rule),
        "fixed_rule_2022_and_calendar_year_transfer":year_results,
        "2023_2024_same_rule_pooled":transferred,
        "all_2022_2024_fixed_rule_pooled":full,
        "original_years_previously_inspected_before_this_design":True,
        "calendar_order_is_not_untouched_prospective_test":True,
        "test_years_scored_without_reranking_or_retraining":True,
        "no_2023_24_outcome_driven_rule_change":True,
        "source_A_own_and_peer_coverage_QA":ctx_qa,
        "no_horse_names_IDs_source_rows_or_individual_predictions_exported":True,
        "no_2027_future_real_forecast_or_heritability_proven":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",type=Path,required=True)
    ap.add_argument("--sqlite",type=Path,required=True)
    ap.add_argument("--aggregate-out",type=Path,required=True)
    args=ap.parse_args()
    out=analyze(args.archive,args.sqlite)
    args.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
    args.aggregate_out.write_text(
        json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
        encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "source_A_SHA256":out["source_A_SHA256"],
        "source_B_SHA256":out["source_B_SHA256"],
        "locked_original_244147_scores":out["locked_original_244147_scores"],
        "2022_choice":out["2022_gate_choice_from_historically_observed_labels"][
            "selected_rule_name"],
        "fixed_rule_2022_and_calendar_year_transfer":
            out["fixed_rule_2022_and_calendar_year_transfer"],
        "2023_2024_same_rule_pooled":out["2023_2024_same_rule_pooled"],
        "2024_midpoint_failure_of_always_kin_preserved":True,
        "no_real_independent_prospective_or_genetic_claim":True,
    },ensure_ascii=False,indent=2,allow_nan=False),flush=True)


if __name__=="__main__":
    main()
