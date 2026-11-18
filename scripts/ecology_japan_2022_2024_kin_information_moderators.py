#!/usr/bin/env python3
"""Actual-source 2022-24 family-information moderation on FIXED strict cohort.

This POST-HOC analysis was specified after the main kin effect and 2026
information-freshness outcomes were viewed. No new independent holdout is
claimed. Reuse frozen 2018-21 ridge coefficients, pre-2022 A horse/family
histories and two-event original A->B ID bridge; restrict to EXACT original
244147 strict-complete 2022-24 starts from 12887 older horses.

Moderators: recorded OWN racing history count, other-horse same-parent
history count and recency, source A last-own-record age, outcome year.
All are ascertained from SOURCE A only before 2022. Missing parent codes
are NOT biological zero relatedness; parent history coverage is not A/G.
Report negative scores, selection, single-way clustered uncertainty, and
HOLD of small subgroups. NO horse names, ids, predictions, source races or
breeding farm info are included in saved aggregates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_parent_placebo import load_sources, SQLITE_SHA
from ecology_japan_2022_denominator_audit import one_observation_original_baselines
from ecology_japan_2022_joint_strict_strong import (
    strict_mask_exact_horse_race, predictions_stronger_old_history,
    STRICT_ROWS, STRICT_HORSES, STRICT_ORIGINAL_NO_KIN, STRICT_ORIGINAL_KIN,
)
from ecology_japan_2022_independent_forward import (
    make_common_features, _scores, _pooled_ci,
)

STATUS="POSTHOC_2022_2024_STRICT_KIN_INFORMATION_MODERATORS_NOT_CAUSAL"
LOCKED_STRICT_NO=0.31242944828841407
LOCKED_STRICT_KIN=0.3121678685067159
LOCKED_STRICT_MID=0.3217441421829057
SUBGROUP_MIN_STARTS=120
SUBGROUP_MIN_HORSES=30
SUBGROUP_MIN_DAYS=15

OWN_CUTS=(-1,3,7,15,float("inf"))
OWN_NAMES=("0-3","4-7","8-15","16+")
KIN_CUTS=(-1,0,1,4,float("inf"))
KIN_NAMES=("no_recorded_peer","one_recorded_peer","2-4_peers","5+_peers")
AGE_CUTS=(-1,365,1095,float("inf"))
AGE_NAMES=("0-365d","366-1095d","1096+d")


def count_bin(counts,kind):
    """Predeclared coarse support bins, NOT selected for positive test."""
    if kind=="own":
        cuts,names=OWN_CUTS,OWN_NAMES
    elif kind=="family":
        cuts,names=KIN_CUTS,KIN_NAMES
    else:
        raise ValueError("HOLD_INVALID_MODERATOR_BIN_KIND")
    x=np.asarray(counts,float)
    if np.any(~np.isfinite(x)) or np.any(x<0):
        raise ValueError("HOLD_INVALID_RECORD_COUNT")
    return pd.cut(x,cuts,labels=names,include_lowest=True).astype(str)


def age_bin(days):
    s=pd.to_numeric(pd.Series(days),errors="coerce")
    if (s.dropna()<0).any():
        raise ValueError("HOLD_NEGATIVE_TIME_LAG_IN_SOURCE_A")
    c=pd.cut(s,AGE_CUTS,labels=AGE_NAMES,include_lowest=True)
    return c.astype(object).where(c.notna(),"NO_RECORDED_DATE").astype(str)


def peer_last_day_excluding_self(old:pd.DataFrame,t:pd.DataFrame,parent:str):
    """For each target, choose the latest OTHER horse sharing a parent/bin.

    One horse's multiple starts are collapsed to a single last date per
    parent x race stratum x horse. If the latest horse is the focal, use
    the second most recent distinct horse. No identity-specific export.
    """
    if parent not in ("sire_id","dam_id"):
        raise ValueError("HOLD_UNKNOWN_PARENT_ID_COLUMN")
    h=old.loc[old[parent].astype(str).ne(""),
              [parent,"stratum","horse","day"]].copy()
    latest=h.groupby([parent,"stratum","horse"],observed=True).day.max().reset_index()
    latest=latest.sort_values(
        [parent,"stratum","day","horse"],
        ascending=[True,True,False,True],kind="mergesort"
    )
    latest["position"]=latest.groupby(
        [parent,"stratum"],observed=True,sort=False).cumcount()
    cols=[parent,"stratum","horse","day"]
    first=latest.loc[latest.position.eq(0),cols].rename(
        columns={"horse":"first_horse","day":"first_day"})
    second=latest.loc[latest.position.eq(1),cols].rename(
        columns={"horse":"second_horse","day":"second_day"})
    targets=t[[parent,"stratum","horse"]].reset_index(drop=True)
    merged=targets.merge(first,on=[parent,"stratum"],how="left",
                         sort=False,validate="many_to_one")
    merged=merged.merge(second,on=[parent,"stratum"],how="left",
                        sort=False,validate="many_to_one")
    if len(merged)!=len(t) or not merged["horse"].equals(targets["horse"]):
        raise ValueError("HOLD_SOURCE_A_PEER_JOIN_DRIFT")
    select_other=merged.first_horse.eq(merged.horse)
    chosen=merged.first_day.where(~select_other,merged.second_day)
    chosen=chosen.where(targets[parent].astype(str).ne(""))
    return pd.to_datetime(chosen,errors="coerce").reset_index(drop=True)


def fixed_sourceA_context(old:pd.DataFrame,strict:pd.DataFrame):
    """All moderation features come from historical source A <=2021."""
    if old.day.max()>=strict.day.min():
        raise ValueError("HOLD_NEWER_RESULTS_IN_HISTORIC_MODERATOR")
    feat=make_common_features(old,strict)
    own=np.rint(np.expm1(feat["log_own_count"].to_numpy(float))).astype(int)
    sire=np.rint(feat["sire_relative_count"].to_numpy(float)).astype(int)
    dam=np.rint(feat["dam_relative_count"].to_numpy(float)).astype(int)
    if np.any(own<2):
        # Cross-source witness requires >=2 pre2022 historic race dates.
        raise ValueError("HOLD_FOCAL_COHORT_NOT_TWO_EVENT_PRE2022_ANCHORED")
    if np.any(sire<0) or np.any(dam<0):
        raise ValueError("HOLD_NEGATIVE_RECORDED_PEER_COUNT")
    # Highest cardinality single recorded parent channel; avoid calling
    # sire+dam counts "distinct" because siblings may occur in both.
    peer_count=np.maximum(sire,dam)
    own_last=old.groupby("horse",observed=True).day.max()
    own_day=strict.horse.astype(str).map(own_last)
    if own_day.isna().any():
        raise ValueError("HOLD_MISSING_SOURCE_A_OWN_HISTORY")
    own_lag=(strict.day.reset_index(drop=True)-own_day.reset_index(drop=True)).dt.days

    sire_last=peer_last_day_excluding_self(old,strict,"sire_id")
    dam_last=peer_last_day_excluding_self(old,strict,"dam_id")
    if not sire_last.index.equals(dam_last.index):
        raise ValueError("HOLD_SIRE_DAM_SOURCE_PEER_TIMESTAMP_INDEX")
    # An observed relative from either parent is a family-history proxy.
    latest=pd.concat([sire_last.rename("sire"),dam_last.rename("dam")],
                     axis=1).max(axis=1)
    kin_lag=(strict.day.reset_index(drop=True)-latest).dt.days
    if bool(((peer_count==0)&kin_lag.notna().to_numpy()).any()):
        raise ValueError("HOLD_PEER_DATE_WITH_NO_MATCHING_PEER")
    if bool(((peer_count>0)&kin_lag.isna().to_numpy()).any()):
        raise ValueError("HOLD_PEER_COUNT_WITHOUT_HISTORIC_DATE")
    if kin_lag.dropna().lt(0).any() or own_lag.lt(0).any():
        raise ValueError("HOLD_SOURCE_DATE_AFTER_FOCAL_EVENT")
    own_name=count_bin(own,"own")
    family_name=count_bin(peer_count,"family")
    ctx=pd.DataFrame({
        "own_record_count_bin":own_name,
        "other_same_parent_horse_count_bin":family_name,
        "sourceA_own_record_age_bin":age_bin(own_lag),
        "sourceA_other_same_parent_record_age_bin":age_bin(kin_lag),
        "outcome_calendar_year":strict.year.astype(str).reset_index(drop=True),
    })
    if len(ctx)!=len(strict) or ctx.isna().any().any():
        raise ValueError("HOLD_MISSING_PRETARGET_CONTEXT")
    return ctx,{
        "sourceA_pre2022_focal_own_record_count":{
            "minimum":int(own.min()),"maximum":int(own.max()),
            "median":float(np.median(own))
        },
        "sourceA_pre2022_documented_other_peer_count_by_largest_single_parent_channel":{
            "minimum":int(peer_count.min()),"maximum":int(peer_count.max()),
            "median":float(np.median(peer_count))
        },
        "focal_rows_with_any_peer_history":int((peer_count>0).sum()),
        "focal_rows_with_zero_peer_history":int((peer_count==0).sum()),
        "sourceA_last_focal_history_lag_days_median":float(np.median(own_lag)),
        "sourceA_last_other_horse_history_lag_days_median_or_null":
            (float(np.median(kin_lag.dropna())) if kin_lag.notna().any() else None),
        "last_other_horse_excludes_focal":True,
        "source_A_historical_record_dates_not_certified_result_known_at":True,
    }


def group_score(t:pd.DataFrame,p0,p1,idx,*,boot=199):
    """Equal-horse-weighted subgroup RMSE; no individual IDs leave runner."""
    idx=np.asarray(idx,bool)
    if len(idx)!=len(t):
        raise ValueError("HOLD_GROUP_MASK_LENGTH")
    s=t.loc[idx].reset_index(drop=True)
    qa={"starts":len(s),"horses":int(s.horse.nunique()),
        "races":int(s.race.nunique()),"race_days":int(s.day.nunique())}
    if (qa["starts"]<SUBGROUP_MIN_STARTS or
        qa["horses"]<SUBGROUP_MIN_HORSES or
        qa["race_days"]<SUBGROUP_MIN_DAYS):
        return {**qa,"status":"HOLD_POSTHOC_SUBGROUP_INSUFFICIENT_SUPPORT"}
    result=_scores(s,np.asarray(p0)[idx],np.asarray(p1)[idx])
    result["status"]="POSTHOC_SUBGROUP_DESCRIPTIVE_NOT_GENERALIZED"
    # Report risk-scale direction as well as RMSE; no reweighting across
    # cohorts as if they were disjoint horse-ID sampling experiments.
    a=s.y.to_numpy(float)
    wt=1/s.horse.astype(str).map(s.horse.astype(str).value_counts()).to_numpy()
    result["MSE_no_kin_minus_family"]=float(np.average(
        (a-np.asarray(p0)[idx])**2-(a-np.asarray(p1)[idx])**2,weights=wt
    ))
    result["single_way_horse_and_race_day_199_bootstrap"]=_pooled_ci(
        s,np.asarray(p0)[idx],np.asarray(p1)[idx],B=boot
    )
    return result


def analyze(archive:Path,db:Path):
    # load_sources checks locked source A/B SHA and pre-2022 two-event IDs.
    raw,old,f,_,gate,_=load_sources(archive,db)
    p_old0,p_old1,_=one_observation_original_baselines(old,f)
    p0_all,p1_all,allstrong,_=predictions_stronger_old_history(raw,old,f)
    mask,source_qa=strict_mask_exact_horse_race(
        raw,f,db,gate["two_event_anchor_horses"]
    )
    t=f.loc[mask].reset_index(drop=True)
    p0=np.asarray(p0_all)[mask]
    p1=np.asarray(p1_all)[mask]
    p_old0=np.asarray(p_old0)[mask]
    p_old1=np.asarray(p_old1)[mask]
    if len(t)!=STRICT_ROWS or t.horse.nunique()!=STRICT_HORSES:
        raise ValueError("HOLD_LOCKED_STRICT_COHORT_DRIFT")
    if source_qa["strict_races"]!=35333:
        raise ValueError("HOLD_LOCKED_COMPLETE_RACES_CHANGED")
    original=_scores(t,p_old0,p_old1)
    strong=_scores(t,p0,p1)
    if any(abs(original[k]-v)>1e-8 for k,v in (
            ("RMSE_portable_no_kin",STRICT_ORIGINAL_NO_KIN),
            ("RMSE_portable_kin",STRICT_ORIGINAL_KIN))):
        raise ValueError("HOLD_LOCKED_ORIGINAL_2022_24_STRICT_SCORE_PARITY")
    if any(abs(strong[k]-v)>1e-8 for k,v in (
            ("RMSE_portable_no_kin",LOCKED_STRICT_NO),
            ("RMSE_portable_kin",LOCKED_STRICT_KIN),
            ("RMSE_unchanged_midpoint",LOCKED_STRICT_MID))):
        raise ValueError("HOLD_LOCKED_STRONG_2022_24_STRICT_SCORE_PARITY")

    ctx,context_qa=fixed_sourceA_context(old,t)
    dimensions=list(ctx.columns[:4])+["outcome_calendar_year"]
    strata={}
    for dim in dimensions:
        strata[dim]={}
        for key in sorted(ctx[dim].unique()):
            ix=ctx[dim].eq(key).to_numpy()
            strata[dim][str(key)]=group_score(t,p0,p1,ix)
    crosses={}
    for name,a,b in (
        ("own_count_x_recorded_peer_count",
         "own_record_count_bin","other_same_parent_horse_count_bin"),
        ("own_count_x_peer_record_age",
         "own_record_count_bin","sourceA_other_same_parent_record_age_bin"),
        ("own_count_x_calendar_year",
         "own_record_count_bin","outcome_calendar_year"),
    ):
        crosses[name]={}
        for x in sorted(ctx[a].unique()):
            for y in sorted(ctx[b].unique()):
                ix=(ctx[a].eq(x)&ctx[b].eq(y)).to_numpy()
                crosses[name][str(x)+" | "+str(y)]=group_score(t,p0,p1,ix,
                                                                  boot=199)
    # Reproduce per-year aggregate and explicitly retain 2024 failure.
    yr24=ctx["outcome_calendar_year"].eq("2024").to_numpy()
    year24=_scores(t.loc[yr24],p0[yr24],p1[yr24])
    if year24["midpoint_minus_kin_gain"]>=0:
        raise ValueError("HOLD_2024_NEGATIVE_MIDPOINT_COMPARATOR_MISSING")

    return {
        "status":"POSTHOC_2022_2024_STRICT_KIN_INFORMATION_MODERATORS_NOT_CAUSAL",
        "source_A_SHA256":"c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f",
        "source_B_SHA256":SQLITE_SHA,
        "retrospective_original_horse_identity_certified_by_studbook":False,
        "two_pre2022_sourceA_B_history_events_required":True,
        "model_training_2018_2021_pre_focal_outcome_only":True,
        "model_alpha_previously_frozen":100.,
        "strict_sample_QA":source_qa,
        "strict_original_parity":original,
        "strict_strong_parity":strong,
        "2024_midpoint_beats_strong_family_model":True,
        "pre2022_sourceA_context_support":context_qa,
        "all_strong_all_rows_baseline":allstrong,
        "posthoc_single_variable_subgroups":strata,
        "posthoc_interactions_not_causal":crosses,
        "subgroup_thresholds":{
            "minimum_starts":SUBGROUP_MIN_STARTS,
            "minimum_horses":SUBGROUP_MIN_HORSES,
            "minimum_days":SUBGROUP_MIN_DAYS,
            "horse_and_race_day_singleway_bootstrap_iterations":199,
        },
        "hypothesis_derived_after_inspecting_2022_24_and_2026_results":True,
        "no_official_live_known_on_or_source_JRA_NAR_license_verified":True,
        "shared_stable_breeding_environment_not_measured":True,
        "family_record_recency_is_prior_to_2022_because_coefficients_frozen":True,
        "no_genomic_G_horse_ID_join_or_heritability":True,
        "all_subgroups_descriptive_not_independent_confirmatory_tests":True,
        "no_source_rows_race_or_horse_names_IDs_individual_predictions_exported":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--sqlite",type=Path,required=True)
    p.add_argument("--aggregate-out",type=Path,required=True)
    a=p.parse_args()
    result=analyze(a.archive,a.sqlite)
    a.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
    a.aggregate_out.write_text(
        json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
        encoding="utf-8")
    compact={
        "status":result["status"],
        "strict_strong_parity":result["strict_strong_parity"],
        "pre2022_sourceA_context_support":result["pre2022_sourceA_context_support"],
        "posthoc_single_variable_subgroups":result["posthoc_single_variable_subgroups"],
        "posthoc_interactions_not_causal":result["posthoc_interactions_not_causal"],
        "2024_midpoint_beats_strong_family_model":True,
        "empirical_positive_parent_signal_not_additive_genetic_effect":True,
    }
    print(json.dumps(compact,ensure_ascii=False,indent=2,allow_nan=False),
          flush=True)


if __name__=="__main__":
    main()
