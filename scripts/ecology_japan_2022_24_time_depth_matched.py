#!/usr/bin/env python3
"""2022–24 exact history-year × start-depth negative-control overlap and refits.

First enforce PR70, PR72 and all 32 PR73 draws. Match the SAME true selected
peers to recorded non-kin candidates from the same last historical observation
year and 1/2–4/5+ historical-start depth. Any unsupported focal × side ×
category (across ALL 32 frozen seeds) stops whole-cohort model claims.
Only anonymized support and, if fully supported, model/uncertainty totals
leave the runner.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import NormalDist
import numpy as np
import pandas as pd

import ecology_japan_2022_24_family_feature_ablation as ablation
import ecology_japan_2022_24_parent_performance_channels as channels
import ecology_japan_2022_24_equal_peer_information as eq
import ecology_japan_2022_24_peer_identity_placebo as placebo
from ecology_japan_2022_24_sire_signal_concentration import (
    ATOL, REFERENCE, REFERENCE_SHA, _periods, _require_parity,
)
from ecology_japan_balanced_parent_history import replace_performance
from ecology_japan_time_depth_nonkin_match import (
    prepare_temporal_match, sample_matched,
)

PR74_REFERENCE=REFERENCE.with_name("japan-2022-24-unrelated-peer-placebo-20261122.json")
PR74_SHA256="45f78eeee82b6a125632d6794de6282c25d0a0daa14220a85353d90ccdd79e46"
PRIMARY=("sire_over_matched_nonkin", "dam_over_matched_nonkin")
N_COMPARE=2*(1+len(ablation.TEST_YEARS))
STATUS="POSTHOC_SAME_HISTORY_LAST_YEAR_AND_START_DEPTH_NONKIN_SENSITIVITY"
HOLD="HOLD_INCOMPLETE_EXACT_YEAR_AND_START_DEPTH_NONKIN_SUPPORT"


def _new_support(old,strict,training_blocks,evaluation_block):
    out=[]
    for year,base in zip(ablation.TRAIN_YEARS,training_blocks,strict=True):
        out.append(prepare_temporal_match(old.loc[old.year.lt(year)],
                                         old.loc[old.year.eq(year),ablation.CONTEXT],
                                         base,cutoff_year=year))
    out.append(prepare_temporal_match(old,strict.loc[:,ablation.CONTEXT],
                                     evaluation_block,cutoff_year=2022))
    return out


def _audit(blocks, *, seeds=eq.SEEDS):
    if not seeds or len(blocks)!=len(ablation.TRAIN_YEARS)+1:
        raise ValueError("HOLD_INCOMPLETE_MATCHED_HISTORICAL_BLOCKS")
    storage={}
    totals=Counter()
    year_side={}
    for block in blocks:
        yr=str(block.base.cutoff)
        for side,label in enumerate(("sire","dam")):
            year_side[f"{yr}_{label}"]={
                "unique_requests":len(block.base.source.request_k),
                "positive_k_requests":int((block.base.source.request_k>0).sum()),
                "matched_draws":0,
                "unsupported_draws":0,
                "unsupported_request_groups":0,
                "minimum_missing_peer_slots":0,
                "requested_true_peer_slots":0,
                "matched_peer_slots":0,
                "unmatched_depth_bin_peer_slots":{k:0 for k in ("1","2-4","5+")}}
    for seed in seeds:
        for i,block in enumerate(blocks):
            for side,label in enumerate(("sire","dam")):
                values,stat=sample_matched(block,seed=seed,side=side)
                key=f"{block.base.cutoff}_{label}"
                d=year_side[key]
                d["requested_true_peer_slots"]+=stat["requested_true_peer_slots"]
                d["matched_peer_slots"]+=stat["matched_peer_slots"]
                d["unsupported_request_groups"]+=stat["unsupported_request_groups"]
                d["minimum_missing_peer_slots"]+=stat["minimum_missing_slots"]
                for k,v in stat["unmatched_selected_peer_bins"].items():
                    d["unmatched_depth_bin_peer_slots"][k]+=v
                if values is None:
                    d["unsupported_draws"]+=1
                    totals["failed_draw_block_side_checks"]+=1
                else:
                    d["matched_draws"]+=1
                    # do not store arrays unless we have at least one complete
                    # seed; numerical predictions can only use ALL 32.
                    storage[(seed,i,side)]=values
    needed=len(seeds)*len(blocks)*2
    matched=len(storage)
    status="EXACT_MATCH_SUPPORT_COMPLETE" if matched==needed else HOLD
    public={
        "status":status,
        "fixed_draws":len(seeds),
        "blocks_per_draw":len(blocks),
        "parent_side_comparisons_per_block":2,
        "total_draw_block_side_checks":needed,
        "fully_matched_draw_block_side_checks":matched,
        "unsupported_draw_block_side_checks":needed-matched,
        "aggregate_2022_target_requests":int(len(blocks[-1].base.source.request_k)),
        "year_side":year_side,
        "one_unmatched_target_invalidates_full_population_model_comparison":True,
        "no_vintage_or_depth_coarsening_or_duplicate_peer_replacement":True,
        "no_individual_horse_parent_race_or_peer_ID_exported":True,
    }
    if matched!=needed:
        return public,None
    return public,storage


def _refit(train,y,horse,evaluation,observed,storage,blocks):
    """Refit NS/ND, each using exactly the same count features as PR73."""
    losses={k:np.empty((len(eq.SEEDS),len(observed)),float) for k in ("NS","ND")}
    lengths=[len(b.base.source.k) for b in blocks]
    if sum(lengths[:-1])!=len(train) or lengths[-1]!=len(evaluation):
        raise ValueError("HOLD_MATCH_FEATURE_ROW_ALIGNMENT")
    for di,seed in enumerate(eq.SEEDS):
        for side,name,feature in ((0,"NS","MS"),(1,"ND","MD")):
            frames=[]
            for bi,b in enumerate(blocks[:-1]):
                v=storage[(seed,bi,side)]
                frames.append(pd.DataFrame({col:v for col in ablation.PERFORMANCE}))
            sampled_train=replace_performance(train,pd.concat(frames,ignore_index=True))
            ev=storage[(seed,len(blocks)-1,side)]
            sampled_eval=replace_performance(evaluation,pd.DataFrame(
                {col:ev for col in ablation.PERFORMANCE}))
            fit=ablation.fit_weighted_ridge(sampled_train,y,horse,
                                           channels.FEATURES[feature],
                                           alpha=ablation.RIDGE_ALPHA)
            fitted=ablation.predict_weighted_ridge(fit,sampled_eval)
            losses[name][di]=eq._squared_loss(observed,fitted)
    return losses


def summarize_period(panel, full, true_losses, negative_losses, pr73,
                     *, draws=channels.DRAWS,min_clusters=channels.MIN_CLUSTERS):
    p=channels._period_panel(panel)
    n=len(p)
    weights=p.weight.to_numpy()
    true={k:np.asarray(true_losses[k],float) for k in ("MS","MD")}
    negative={k:np.asarray(negative_losses[k],float) for k in ("NS","ND")}
    if any(x.shape!=(len(eq.SEEDS),n) or not np.isfinite(x).all()
           or (x<0).any() or (x>1).any() for x in [*true.values(),*negative.values()]):
        raise ValueError("HOLD_MATCHED_CONTROL_LOSS_SHAPE_OR_FINITE")
    terms={
        "sire_over_matched_nonkin":(negative["NS"]-true["MS"]).mean(axis=0),
        "dam_over_matched_nonkin":(negative["ND"]-true["MD"]).mean(axis=0),
    }
    balanced_parent=pr73["mean_MSE_contrasts"]["balanced_sire_advantage"]
    true_parent=float(np.average((true["MD"]-true["MS"]).mean(axis=0),weights=weights))
    if abs(balanced_parent-true_parent)>ATOL:
        raise ValueError("HOLD_PR73_FIXED_TRUE_PARENT_MSE_DRIFT")
    for name,origin in (("MS","MS"),("MD","MD")):
        actual=float(np.average(true[name].mean(axis=0),weights=weights))
        if abs(actual-pr73["balanced_models"][origin]["MSE"])>ATOL:
            raise ValueError("HOLD_MATCH_TRUE_PARENT_ABSOLUTE_RISK_DRIFT")
    mc=channels._losses(p.y,full)["MC"]
    m0=(p.y.to_numpy()-.5)**2
    risks={"M0":m0,"MC":mc,"MS":true["MS"].mean(axis=0),
           "MD":true["MD"].mean(axis=0),
           "NS":negative["NS"].mean(axis=0),"ND":negative["ND"].mean(axis=0)}
    means={}
    for key,loss in risks.items():
        m=float(np.average(loss,weights=weights))
        means[key]={"MSE":m,"RMSE":float(np.sqrt(m))}
    for old,new in (("M0","M0"),("MC","MC")):
        if abs(means[new]["MSE"]-pr73["full_models"][old]["MSE"])>ATOL:
            raise ValueError("HOLD_MATCH_MC_M0_RISK_DRIFT")
    per_draw={}
    monte={}
    for key,(neg,true_name) in {
        "sire_over_matched_nonkin":("NS","MS"),
        "dam_over_matched_nonkin":("ND","MD")}.items():
        values=np.average(negative[neg]-true[true_name],axis=1,weights=weights)
        per_draw[key]=values
        sd=float(values.std(ddof=1))
        monte[key]={"mean":float(values.mean()),"SD":sd,
                    "MCSE":sd/np.sqrt(len(eq.SEEDS)),
                    "min":float(values.min()),"max":float(values.max())}
        if abs(float(np.average(terms[key],weights=weights))-float(values.mean()))>ATOL:
            raise ValueError("HOLD_MATCHED_DRAW_VS_ROW_AVERAGE")
    avg_diff=float(np.average(terms[PRIMARY[0]]-terms[PRIMARY[1]],weights=weights))
    nonkin_diff=float(np.average((negative["NS"]-negative["ND"]).mean(axis=0),weights=weights))
    if abs(avg_diff-(nonkin_diff+true_parent))>ATOL:
        raise ValueError("HOLD_MATCHED_NEGATIVE_CONTROL_LOSS_IDENTITY")
    covered=channels._coverage(p)
    uncertainty={}
    for key in PRIMARY:
        uncertainty[key]=eq._uncertainty(p,terms[key],covered,draws,min_clusters)
    return {
        "starts":n,"horses":int(p.horse.nunique()),"races":int(p.race.nunique()),
        "models":means,
        "main_MSE_contrasts":{key:float(np.average(terms[key],weights=weights)) for key in PRIMARY},
        "negative_control_side_difference":nonkin_diff,
        "original_PR73_true_sire_advantage":true_parent,
        "exact_paired_parent_and_negative_control_identity":True,
        "main_uncertainty":uncertainty,
        "monte_carlo":monte,
        "per_draw":[{"seed":int(seed),**{key:float(v[i]) for key,v in per_draw.items()}}
                    for i,seed in enumerate(eq.SEEDS)],
    }


def analyze(archive:Path,sqlite:Path)->dict:
    refs={
        "PR70":eq._reference(REFERENCE,REFERENCE_SHA,"PR70"),
        "PR72":eq._reference(eq.PARENT_REFERENCE,eq.PARENT_REFERENCE_SHA,"PR72"),
        "PR73":eq._reference(placebo.PR73_REFERENCE,placebo.PR73_SHA256,"PR73"),
        "PR74":eq._reference(PR74_REFERENCE,PR74_SHA256,"PR74"),
    }
    raw,old,future,_,gate,_=ablation.load_sources(archive,sqlite)
    if not old.year.lt(2022).all() or set(future.year.unique())!=set(ablation.TEST_YEARS):
        raise ValueError("HOLD_SOURCE_YEAR_CUTOFF")
    train,labels,horses,features=eq._base_matrices(old,future,ablation.old_metadata(raw))
    original=channels.fit_factorial(train,labels,horses)
    all_preds=channels.predict_factorial(original,features)
    scores=ablation._scores(future,all_preds["M1"],all_preds["M2"])
    _require_parity(ablation.canonical_parity_scores(scores),
                    refs["PR70"]["strong_all_row_parity"],"PR70")
    mask,qa=ablation.strict_mask_exact_horse_race(
        raw,future,sqlite,gate["two_event_anchor_horses"])
    _require_parity(qa,refs["PR70"]["strict_source_qa"],"PR70.strict")
    strict=future.loc[mask].reset_index(drop=True)
    features=features.loc[np.asarray(mask)].reset_index(drop=True)
    original_pred={k:v[mask] for k,v in all_preds.items()}
    if not (len(strict)==244147 and strict.horse.nunique()==12887
            and strict.race.nunique()==35333):
        raise ValueError("HOLD_HISTORICAL_STRICT_COHORT")
    support=features[channels.SUPPORT_COLUMNS]
    del raw,future
    for label,p,pred in _periods(strict,original_pred):
        legacy={k:pred[k] for k in ablation.FEATURES}
        for key,actual in (
            ("PR70",ablation.summarize_period(p,legacy)),
            ("PR72",channels.summarize_period(p,pred,support.loc[p.index]))
        ):
            expected=refs[key][label] if label=="pooled" else refs[key]["by_year"][label]
            _require_parity(actual,expected,key+"."+label)
    true_blocks,eval_block=eq._prepare_blocks(old,strict,train,features)
    true_losses=eq._draw_losses(train,labels,horses,features,strict.y,
                               true_blocks,eval_block)
    for label,p,pred in _periods(strict,original_pred):
        subset=true_losses if label=="pooled" else {
            k:v[:,p.index] for k,v in true_losses.items()}
        expected=refs["PR73"][label] if label=="pooled" else refs["PR73"]["by_year"][label]
        actual=eq.summarize_period(p,pred,subset,support.loc[p.index],
                         pd.Series(eval_block.k,index=strict.index).loc[p.index])
        _require_parity(actual,expected,"PR73."+label)
    blocks=_new_support(old,strict,true_blocks,eval_block)
    matched,storage=_audit(blocks)
    header={
        "status":STATUS if storage is not None else HOLD,
        "source_A_sha256":ablation.SOURCE_SHA,
        "source_B_sha256":ablation.SQLITE_SHA,
        "pr70_reference_sha256":REFERENCE_SHA,
        "pr72_reference_sha256":eq.PARENT_REFERENCE_SHA,
        "pr73_reference_sha256":placebo.PR73_SHA256,
        "pr74_reference_sha256":PR74_SHA256,
        "strict_horses":12887,
        "strict_starts":244147,
        "strict_races":35333,
        "training_years":list(ablation.TRAIN_YEARS),
        "evaluation_cutoff_year":2022,
        "frozen_seeds":list(eq.SEEDS),
        "matching_support":matched,
        "original_PR70_PR72_PR73_parity":True,
        "matched_nonkin_full_population_model_gain_unidentified_if_any_HOLD":True,
        "scientific_holds":{
            "historical_outcomes_already_inspected":True,
            "strict_matching_does_not_identify_genetic_causation":True,
            "not_proof_of_complete_pedigree_unrelatedness":True,
            "not_matched_on_stable_training_environment_or_birth_cohort":True,
            "official_source_publication_and_license_not_verified":True,
            "original_individual_horse_parent_peers_and_predictions_not_exported":True,
        }
    }
    if storage is None:
        return {**header,"main_comparisons":"HOLD_INCOMPLETE_SOURCE_MATCH_SUPPORT",
                "pooled":None,"by_year":None}
    negatives=_refit(train,labels,horses,features,strict.y,storage,blocks)
    results={}
    for label,p,pred in _periods(strict,original_pred):
        subset=true_losses if label=="pooled" else {
            k:v[:,p.index] for k,v in true_losses.items()}
        neg=negatives if label=="pooled" else {
            k:v[:,p.index] for k,v in negatives.items()}
        reference=refs["PR73"][label] if label=="pooled" else refs["PR73"]["by_year"][label]
        results[label]=summarize_period(p,pred,subset,neg,reference)
    return {**header,"main_comparisons":"POSTHOC_CONDITIONAL_ON_FULL_MATCH_SUPPORT",
            "pooled":results.pop("pooled"),"by_year":results,
            "eight_comparisons_Bonferroni":True,
            "original_model_baseline_M0_reported":True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--sqlite",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    j=analyze(a.archive,a.sqlite)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(j,indent=2,sort_keys=True,
                                  allow_nan=False,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":j["status"],
                      "match_support":j["matching_support"]["status"],
                      "matched_draw_block_side_checks":
                          j["matching_support"]["fully_matched_draw_block_side_checks"]},
                      ensure_ascii=False,allow_nan=False))


if __name__=="__main__":
    main()
