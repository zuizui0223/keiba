#!/usr/bin/env python3
"""Train frozen M1/M2 coefficients for the 2027 JRA official-ID forecast ledger.

PRIVATE licensed/source-certified training input only. This is a software
implementation, NOT a data acquisition client or a real JRA genetic result.
Train on actual historical results known before 2025-01-01, evaluate fixed
2025/26 chronology before the model freeze, and never read a 2027 label.
Use exactly the point-in-time ledger's asof_features() and model schema.
Every feature is historical: known_on < the TARGET entry snapshot known-on.
No horse IDs, trainer IDs, source rows or model coefficients in public JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

import numpy as np

from ecology_japan_2027_official_knownon_preflight import (
    ENTRY_REQUIRED, PARENT_REQUIRED, local_jst, typed_id, read_csv,
)
from ecology_japan_2027_point_in_time_ledger import (
    OWN, KIN, HISTORICAL_INPUT, JST_ZONE, MODEL_SCHEMA,
    FROZEN_2027_START, asof_features, validate_models,
    linear_predict, digest_file, digest_bytes, canonical_bytes,
    _private_destination, _bootstrap,
)

TRAIN_START = datetime(2018, 1, 1, tzinfo=JST_ZONE)
SPLIT_AT = datetime(2025, 1, 1, tzinfo=JST_ZONE)
TRAIN_END = SPLIT_AT
VAL_END = FROZEN_2027_START
ALPHA = 100.0
MIN_TRAIN = (100, 30, 30)
MIN_VAL = (50, 20, 15)


def _time(x):
    return local_jst(x)


def parse_licensed_panel(entries:list[dict], parents:list[dict],
                         results:list[dict], *, clock:datetime):
    """One official ID namespace; transient detailed data NEVER exported."""
    if clock.tzinfo is None or clock.utcoffset()!=timedelta(hours=9):
        raise ValueError("HOLD_FIT_CLOCK_NOT_EXPLICIT_JST")
    parent={}
    for p in parents:
        horse=typed_id(p["horse_id"],("H:",))
        sire=typed_id(p["sire_id"],("H:","B:"),blank=True)
        dam=typed_id(p["dam_id"],("H:","B:"),blank=True)
        known=_time(p["pedigree_master_known_at_jst"])
        if horse in parent or horse in (sire,dam) or (sire and sire==dam):
            raise ValueError("HOLD_DUPLICATE_OR_SELF_PARENT_ID")
        if known>=clock:
            raise ValueError("HOLD_FUTURE_PEDIGREE_MASTER_IN_TRAINING_SOURCE")
        parent[horse]=(sire,dam,known)

    history=[]
    seen=set()
    race_conditions={}
    for raw in results:
        horse=typed_id(raw["horse_id"],("H:",))
        race=raw["race_id"]
        if not race.startswith("JRA:") or not race:
            raise ValueError("HOLD_NON_JRA_HISTORICAL_RACE_ID")
        if (race,horse) in seen:
            raise ValueError("HOLD_DUPLICATE_OFFICIAL_HISTORICAL_RESULT")
        seen.add((race,horse))
        start=_time(raw["race_start_at_jst"])
        known=_time(raw["result_known_at_jst"])
        if not start<known<clock or not start<FROZEN_2027_START:
            raise ValueError("HOLD_FUTURE_OR_PRE_RACE_HISTORICAL_RESULT")
        try:
            n=int(raw["classified_field_size"])
            rank=int(raw["finish_rank"]) if raw["finish_rank"] else 0
            distance=int(raw["distance_m"])
        except (TypeError, ValueError):
            raise ValueError("HOLD_INVALID_RANK_FIELD_DISTANCE") from None
        if not 2<=n<=30 or not 600<=distance<=4000:
            raise ValueError("HOLD_RACE_FIELD_SIZE_OR_DISTANCE")
        if raw["surface"] not in ("turf","dirt"):
            raise ValueError("HOLD_BAD_RACING_SURFACE")
        for field in ("course_id","jockey_id","trainer_id"):
            if not raw[field]:
                raise ValueError("HOLD_MISSING_OFFICIAL_CONDITION_ID")
        cond=(start,raw["surface"],distance,raw["course_id"])
        if race in race_conditions and race_conditions[race]!=cond:
            raise ValueError("HOLD_CONFLICTING_HISTORICAL_RACE_CONDITIONS")
        race_conditions[race]=cond
        history.append({
            "horse":horse,"race":race,"start":start,"known":known,
            "rank":rank,"n":n,"status":raw["finish_status"],
            "surface":raw["surface"],"distance":distance,
            "course_id":raw["course_id"],"jockey_id":raw["jockey_id"],
            "trainer_id":raw["trainer_id"],
        })
    # Reject / quarantine incomplete, tied, missing, DNF and nonconsecutive
    # race histories. This applies to both predictor histories and labels.
    by_race=defaultdict(list)
    for h in history:
        by_race[h["race"]].append(h)
    eligible_hist=[]
    excluded=Counter()
    complete_race_count=0
    for race,rows in by_race.items():
        n=len(rows)
        if (n<2 or n>30 or any(h["n"]!=n for h in rows)
                or any(h["status"]!="CLASSIFIED" for h in rows)
                or sorted(h["rank"] for h in rows)!=list(range(1,n+1))):
            excluded["incomplete_tied_dnf_or_invalid_race"]+=1
            continue
        complete_race_count+=1
        for h in rows:
            h["y"]=(h["rank"]-1)/(n-1)
            eligible_hist.append(h)

    entrants=[]
    seen_entries=set()
    entrant_races=defaultdict(list)
    entrant_conditions={}
    for raw in entries:
        horse=typed_id(raw["horse_id"],("H:",))
        race=raw["race_id"]
        if not race.startswith("JRA:"):
            raise ValueError("HOLD_NON_JRA_TRAINING_ENTRY_ID")
        if (race,horse) in seen_entries:
            raise ValueError("HOLD_DUPLICATE_TRAINING_HORSE_ENTRY")
        seen_entries.add((race,horse))
        start=_time(raw["race_start_at_jst"])
        cutoff=_time(raw["entry_known_at_jst"])
        if not TRAIN_START<=start<VAL_END or not cutoff<start<clock:
            raise ValueError("HOLD_TRAINING_ENTRY_OUTSIDE_HISTORICAL_CUTOFF")
        if horse not in parent or not parent[horse][2]<cutoff:
            raise ValueError("HOLD_TRAINING_PEDIGREE_NOT_KNOWN_AT_ENTRY")
        try:
            distance=int(raw["distance_m"])
            age=int(raw["age"])
        except (TypeError,ValueError):
            raise ValueError("HOLD_INVALID_TRAINING_AGE_DISTANCE") from None
        if not 600<=distance<=4000 or not 2<=age<=20:
            raise ValueError("HOLD_INVALID_TRAINING_AGE_DISTANCE")
        if raw["surface"] not in ("turf","dirt") or raw["sex"] not in ("M","F","G","U"):
            raise ValueError("HOLD_INVALID_TRAINING_SURFACE_OR_SEX")
        if any(not raw[key] for key in ("course_id","jockey_id","trainer_id")):
            raise ValueError("HOLD_UNCERTIFIED_TRAINING_CONTEXT")
        # Every horse in one race must come from the SAME certified pre-race
        # snapshot. Mixing publication cutoffs across entrants gives them
        # different accessible history windows within one outcome.
        cond=(start,raw["surface"],distance,raw["course_id"],cutoff)
        if race in entrant_conditions and entrant_conditions[race]!=cond:
            raise ValueError("HOLD_INCONSISTENT_ENTERED_RACE_CONDITIONS_OR_CUTOFF")
        entrant_conditions[race]=cond
        sire,dam,_=parent[horse]
        record={
            "race":race,"horse":horse,"start":start,"cutoff":cutoff,
            "sire":sire,"dam":dam,"surface":raw["surface"],
            "distance":distance,"raw":raw,
        }
        entrants.append(record)
        entrant_races[race].append(record)
    # Never pass a subset of a race off as all starters.
    labels={(h["race"],h["horse"]):h for h in eligible_hist}
    target=[]
    eligible_groups=Counter()
    for race,erows in entrant_races.items():
        selected=[labels.get((race,e["horse"])) for e in erows]
        if (not 2<=len(erows)<=30 or any(h is None for h in selected)
                or len(by_race.get(race,[]))!=len(erows)):
            eligible_groups["incomplete_entry_result_or_DNF"]+=1
            continue
        if any(h["start"]!=e["start"] or
               h["distance"]!=e["distance"] or
               h["surface"]!=e["surface"] or
               h["course_id"]!=e["raw"]["course_id"]
               for e,h in zip(erows,selected)):
            raise ValueError("HOLD_ENTRY_OUTCOME_RACE_METADATA_CONFLICT")
        # Replaced jockeys or inconsistent trainer mappings invalidate the
        # PRE-RACE covariate comparison, so quarantine the WHOLE target race.
        # A final result may truthfully report a later replacement; it must
        # not be silently backfilled into the pre-race entrant predictors.
        if any(h["jockey_id"]!=e["raw"]["jockey_id"] or
               h["trainer_id"]!=e["raw"]["trainer_id"]
               for e,h in zip(erows,selected)):
            eligible_groups["changed_rider_or_trainer_after_entry"]+=1
            continue
        if any(e["start"]<SPLIT_AT and h["known"]>=SPLIT_AT
               for e,h in zip(erows,selected)):
            eligible_groups["cross_split_result_publication"]+=1
            continue
        for e,h in zip(erows,selected):
            target.append((e,h["y"],h["known"]))
        eligible_groups["matched_complete_races"]+=1
    if not target:
        raise ValueError("HOLD_NO_COMPLETE_HISTORICAL_TRAINING_TARGETS")
    return {
        "parents":parent,
        "history":eligible_hist,
        "targets":target,
        "complete_history_races":complete_race_count,
        "history_bad_races":dict(excluded),
        "matched_target_race_qa":dict(eligible_groups),
    }


def build_time_features(panel:dict):
    """Fast candidate indexes; precise timestamp filtering in ledger function."""
    parents=panel["parents"]
    by_horse=defaultdict(list)
    by_course=defaultdict(list)
    by_jockey=defaultdict(list)
    by_trainer=defaultdict(list)
    for h in panel["history"]:
        by_horse[h["horse"]].append(h)
        by_course[h["course_id"]].append(h)
        by_jockey[h["jockey_id"]].append(h)
        by_trainer[h["trainer_id"]].append(h)
    sire_index=defaultdict(list)
    dam_index=defaultdict(list)
    for h,(s,d,known) in parents.items():
        if s:sire_index[s].append(h)
        if d:dam_index[d].append(h)
    outputs=[]
    metrics=Counter()
    for entry,y,known in panel["targets"]:
        cutoff=entry["cutoff"]
        raw=entry["raw"]
        horse=entry["horse"]
        si,da=entry["sire"],entry["dam"]
        relset={horse}
        if si:relset.update(sire_index.get(si,[]))
        if da:relset.update(dam_index.get(da,[]))
        # Per-horse peer aggregation only over members of its own family.
        context_parents={h:parents[h] for h in relset}
        peer_hist={h:by_horse.get(h,[]) for h in relset}
        # Course, jockey and trainer history may be from unrelated horses.
        # Deduplicate shared observations when e.g. rider and trainer both
        # match the same record.
        context_ids={}
        for key in ("course_id","jockey_id","trainer_id"):
            idx = (by_course if key=="course_id" else
                   by_jockey if key=="jockey_id" else by_trainer)
            for result in idx.get(raw[key],[]):
                context_ids[id(result)]=result
        f, support=asof_features(
            entry,raw,context_parents,peer_hist,
            list(context_ids.values()),cutoff
        )
        if not all(np.isfinite(list(f.values()))):
            raise ValueError("HOLD_NONFINITE_MODEL_TRAINING_FEATURES")
        metrics.update(support)
        outputs.append({
            "horse":horse,"race":entry["race"],
            "start":entry["start"],"known":known,
            "y":y,"features":f,
            "known_sire":bool(si),"known_dam":bool(da),
        })
    return outputs,dict(metrics)


def required_support(rows, minimum):
    n=len(rows)
    horses=len({r["horse"] for r in rows})
    days=len({r["start"].date() for r in rows})
    return (n>=minimum[0] and horses>=minimum[1] and
            days>=minimum[2]), {"starts":n,"horses":horses,"days":days,
                                "required_starts_horses_days":minimum}


def fit_ridge(rows, *, alpha=ALPHA):
    """Horse-equal weighted ridge, common unweighted scaler in M1/M2."""
    if alpha!=ALPHA:
        raise ValueError("HOLD_UNFROZEN_RIDGE_PENALTY")
    all_features=list(OWN+KIN)
    x=np.asarray([[r["features"][k] for k in all_features] for r in rows],
                 dtype=np.float64)
    y=np.asarray([r["y"] for r in rows],dtype=np.float64)
    horses=[r["horse"] for r in rows]
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("HOLD_TRAINING_MATRIX_NONFINITE")
    mu=np.mean(x,axis=0)
    sd=np.std(x,axis=0)
    sd=np.where(sd<1e-12,1.0,sd)
    count=Counter(horses)
    w=np.asarray([1/count[h] for h in horses],dtype=float)
    w/=np.mean(w)
    models={}
    for kind,cols in (("M1",OWN),("M2",OWN+KIN)):
        indices=[all_features.index(col) for col in cols]
        z=(x[:,indices]-mu[indices])/sd[indices]
        Z=np.column_stack((np.ones(len(y)),z))
        mat=Z.T @ (Z*w[:,None])
        regularizer=np.full(Z.shape[1],alpha)
        regularizer[0]=0
        mat+=np.diag(regularizer)
        coef=np.linalg.solve(mat,Z.T@(y*w))
        models[kind]={
            "intercept":float(coef[0]),
            "features":{
                key:{"coefficient":float(coef[pos+1]),
                     "mean":float(mu[all_features.index(key)]),
                     "sd":float(sd[all_features.index(key)])}
                for pos,key in enumerate(cols)
            }
        }
    return models


def cohort_scores(rows, models, *, with_bootstrap=False):
    if not rows:
        raise ValueError("HOLD_EMPTY_VALIDATION")
    n=Counter(r["horse"] for r in rows)
    observed=[]
    den=0.0
    sums=[0.,0.,0.]
    for r in rows:
        y=r["y"]
        p=[.5,linear_predict(models["M1"],r["features"]),
           linear_predict(models["M2"],r["features"])]
        observed.append({
            "horse_id":r["horse"],
            "race_start_at_jst":r["start"].isoformat(),
            "y":y,"M0":p[0],"M1":p[1],"M2":p[2],
        })
        wt=1/n[r["horse"]]
        den+=wt
        for i in range(3):
            sums[i]+=wt*(y-p[i])**2
    rmse=[float(np.sqrt(v/den)) for v in sums]
    answer = {
        "M0_midpoint":rmse[0],"M1_own_context":rmse[1],
        "M2_own_context_plus_family":rmse[2],
        "gain_M1_minus_M2":rmse[1]-rmse[2],
        "gain_M0_minus_M2":rmse[0]-rmse[2],
        "M2_beats_both":bool(rmse[2]<rmse[1] and rmse[2]<rmse[0]),
    }
    if with_bootstrap:
        answer["one_way_horse_cluster"]=_bootstrap(observed,"horse",B=399)
        answer["one_way_race_day_cluster"]=_bootstrap(observed,"race_day",B=399)
    return answer


def train(entries:list[dict],parents:list[dict],history:list[dict],
          *, clock:datetime, source_sha:dict[str,str]):
    """Returns private model file and public aggregate QA; no real source in CI."""
    panel=parse_licensed_panel(entries,parents,history,clock=clock)
    rows,feature_support=build_time_features(panel)
    training=[r for r in rows if r["start"]<SPLIT_AT]
    validation=[r for r in rows if r["start"]>=SPLIT_AT]
    ok_train,tqa=required_support(training,MIN_TRAIN)
    ok_val,vqa=required_support(validation,MIN_VAL)
    if not ok_train or not ok_val:
        raise ValueError(
            "HOLD_INSUFFICIENT_COMPLETE_TRAIN_OR_VALIDATION_SUPPORT:"
            +json.dumps({"train":tqa,"validation":vqa},sort_keys=True)
        )
    models=fit_ridge(training)
    train_max=max(r["known"] for r in training)
    val_max=max(r["known"] for r in validation)
    if not train_max<SPLIT_AT<=val_max<clock<FROZEN_2027_START:
        raise ValueError("HOLD_HISTORICAL_TRAINING_VAL_OR_FREEZE_ORDER")
    model={
        "schema":MODEL_SCHEMA,
        "training_through_jst":train_max.isoformat(),
        "model_frozen_at_jst":clock.isoformat(),
        "models":models,
    }
    # The same contract used by the actual 2027 future forecast CLI.
    validate_models(model,clock,FROZEN_2027_START+timedelta(hours=12))
    scores={
        "training_descriptive":cohort_scores(training,models),
        "2025_2026_out_of_training_temporal_validation":cohort_scores(
            validation,models,with_bootstrap=True)
    }
    return model,{
        "status":"PRIVATE_OFFICIAL_ID_HISTORIC_M1_M2_MODEL_TRAINED_NOT_2027_PROSPECTIVE",
        "historical_source_file_SHA256":source_sha,
        "private_fitted_model_file_SHA256":digest_bytes(canonical_bytes(model)),
        "time_split":{
            "train_start":"2018-01-01T00:00:00+09:00",
            "train_end_exclusive":"2025-01-01T00:00:00+09:00",
            "validation_end_exclusive":"2027-01-01T00:00:00+09:00",
            "model_frozen_at_jst":clock.isoformat(),
            "strict_pre_entry_knownon_for_each_feature":True,
            "historical_labels_published_before_model_freeze":True,
        },
        "source_qa":{
            "original_historical_complete_races":panel["complete_history_races"],
            "quarantined_historical_races":panel["history_bad_races"],
            "training_target_races":panel["matched_target_race_qa"],
            "feature_known_on_support_aggregates":feature_support,
            "training_support":tqa,"validation_support":vqa,
        },
        "methodology":{
            "fixed_ridge_alpha":ALPHA,
            "equal_horse_training_weights":True,
            "M1_and_M2_same_own_features_and_scalers":True,
            "not_tuned_to_validation_labels":True,
            "one_way_validation_resampling_not_two_way_CI":True,
            "target_2027_outcomes_used":False,
            "genetic_causality_estimated":False,
        },
        "historical_scores":scores,
        "no_Horse_ID_parent_ID_model_coefficients_or_source_rows_exported":True,
        "provider_rights_and_ID_authenticity_require_external_verification":True,
        "not_yet_2027_future_forecast":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--historical-entries",type=Path,required=True)
    p.add_argument("--historical-results",type=Path,required=True)
    p.add_argument("--parent-master",type=Path,required=True)
    p.add_argument("--private-model-out",type=Path,required=True)
    p.add_argument("--public-summary-out",type=Path,required=True)
    args=p.parse_args()
    _private_destination(args.private_model_out)
    files={
        "historical_entries":args.historical_entries,
        "historical_results":args.historical_results,
        "parent_master":args.parent_master,
    }
    source_sha={k:digest_file(v) for k,v in files.items()}
    model,summ=train(
        read_csv(args.historical_entries,ENTRY_REQUIRED),
        read_csv(args.parent_master,PARENT_REQUIRED),
        read_csv(args.historical_results,HISTORICAL_INPUT),
        clock=datetime.now(timezone.utc).astimezone(JST_ZONE),
        source_sha=source_sha,
    )
    args.private_model_out.parent.mkdir(parents=True,exist_ok=True)
    args.private_model_out.write_bytes(canonical_bytes(model))
    args.private_model_out.chmod(0o600)
    args.public_summary_out.parent.mkdir(parents=True,exist_ok=True)
    # The full model coefficients, horse IDs and row predictions stay private.
    args.public_summary_out.write_bytes(canonical_bytes(summ))
    print(json.dumps(summ,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
