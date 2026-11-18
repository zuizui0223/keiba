#!/usr/bin/env python3
"""Source-gated pedigree/genotype -> parimutuel MARKET-share prediction.

NO genome/horse mapping, pre-race validated market time series, or individual
market performance is presently available in this repo. This code can only
produce empirical claims with authorized, stable-ID-linked, source-timestamped
inputs. Outcome is the NEXT PRE-RACE quote's *relative implied support*,
not race win probability, pool tickets, payout odds, or betting value.

A separate toy fixture proves timeline and channel handling; toy improvements
must never be represented as empirical Japanese racing results.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random

BETA = (-1.0,-0.5,-0.25,0.0,0.25,0.5,1.0)
GAMMA = (0.0,0.5,1.0,1.5)
SOURCE_SNAPSHOT = "data/2026-10-18/ticket-odds-snapshot.json"


def iso(value: str, field: str) -> datetime:
    try:
        stamp=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (ValueError,TypeError,AttributeError) as exc:
        raise ValueError("HOLD_INVALID_TIME_"+field) from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_TIME_"+field)
    return stamp.astimezone(timezone.utc)


def read_rows(path: Path, names: set[str]) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fd:
        reader=csv.DictReader(fd)
        if not reader.fieldnames or not names.issubset(reader.fieldnames):
            raise ValueError("HOLD_MISSING_REQUIRED_MARKET_PANEL_FIELDS")
        output=list(reader)
    if not output:
        raise ValueError("HOLD_EMPTY_MARKET_PANEL")
    return output


def source_snapshot_readiness(path: Path) -> dict:
    """Inspect already-saved intermediary prices, never infer missing join keys."""
    raw=path.read_bytes()
    item=json.loads(raw)
    races=item.get("races", [])
    n_rows=sum(len(r.get("horses", [])) for r in races)
    id_rows=sum(bool(h.get("horse_id")) for r in races for h in r.get("horses", []))
    sire_rows=sum(bool(h.get("sire_id")) for r in races for h in r.get("horses", []))
    dam_rows=sum(bool(h.get("dam_id")) for r in races for h in r.get("horses", []))
    source_time_rows=sum(bool(h.get("odds_updated_at_jst")) for r in races for h in r.get("horses", []))
    validated_race_times=sum(bool(r.get("win_place_upstream_updated_at") or r.get("upstream_quote_updated_at")) for r in races)
    return {
        "status":"HOLD_NO_ID_LINKED_CERTIFIED_TIME_SERIES_FOR_GENEALOGY_MARKET",
        "source_snapshot_SHA256":hashlib.sha256(raw).hexdigest(),
        "saved_races":len(races),
        "saved_horse_price_rows":n_rows,
        "stable_horse_ID_rows":id_rows,
        "sire_ID_rows":sire_rows,
        "dam_ID_rows":dam_rows,
        "source_updated_at_per_horse":source_time_rows,
        "source_updated_at_per_race":validated_race_times,
        "quoted_observation_window":(
            item.get("observed_window_start_jst"),item.get("observed_window_end_jst")
        ),
        "source_name_only_pairing_not_authorized":True,
        "snapshot_not_official_asof_or_proof_of_true_market_dynamics":True,
        "no_genotype_or_market_prediction_tested":True,
    }


def _softmax(values: list[float]) -> list[float]:
    maximum=max(values)
    u=[math.exp(v-maximum) for v in values]
    z=sum(u)
    return [v/z for v in u]


def _supports(odds: dict[str,float], horse_ids: list[str]) -> list[float]:
    inv=[1.0/odds[h] for h in horse_ids]
    z=sum(inv)
    return [v/z for v in inv]


def _center(values: list[float]) -> list[float]:
    m=sum(values)/len(values)
    return [v-m for v in values]


def _gene_proxy(mstn: str, distance_m: int) -> float:
    """Exploratory allele-dose×distance contrast, never known race fitness."""
    alleles={"CC":2,"CT":1,"TC":1,"TT":0}
    return alleles[mstn] * (2000.0-distance_m)/1000.0


def build_races(cards: list[dict], quotes: list[dict]) -> tuple[list[dict],dict]:
    ids=set()
    cards_per_race=defaultdict(dict)
    has_genotype=0
    for r in cards:
        key=(r["race_id"],r["horse_id"])
        if not all(key) or key in ids:
            raise ValueError("HOLD_DUPLICATE_OR_BLANK_RACE_HORSE")
        ids.add(key)
        start=iso(r["start_at"],"start_at")
        known=iso(r["feature_known_at"],"feature_known_at")
        if not known<start:
            raise ValueError("HOLD_FEATURES_NOT_PRERACE")
        try:
            kin=float(r["kin_signal"])
            distance=int(r["distance_m"])
        except (ValueError,TypeError) as exc:
            raise ValueError("HOLD_INVALID_KIN_OR_DISTANCE") from exc
        if not math.isfinite(kin) or not 600<=distance<=4000:
            raise ValueError("HOLD_NONFINITE_KIN_OR_DISTANCE")
        gene=(r.get("mstn_genotype") or "").replace("/","").upper()
        if gene:
            if gene not in {"CC","CT","TC","TT"}:
                raise ValueError("HOLD_INVALID_MSTN_GENOTYPE")
            verified=(r.get("mstn_assay_verified") or "").lower()=="true"
            if not verified:
                raise ValueError("HOLD_INFERRED_OR_UNVERIFIED_MSTN")
            genetime=iso(r.get("genotype_known_at",""),"genotype_known_at")
            if not genetime<start:
                raise ValueError("HOLD_GENOTYPE_NOT_PRERACE")
            has_genotype+=1
        cards_per_race[r["race_id"]][r["horse_id"]]={
            "start":start,"feature_known":known,"kin":kin,
            "distance":distance,"gene":gene
        }
    quotes_per_race=defaultdict(lambda:defaultdict(dict))
    for r in quotes:
        race,horse=r["race_id"],r["horse_id"]
        if horse not in cards_per_race.get(race,{}):
            raise ValueError("HOLD_QUOTED_HORSE_NO_STABLE_PEDIGREE_LINK")
        if (r.get("source_quote_time_verified") or "").lower()!="true":
            raise ValueError("HOLD_UNVERIFIED_SOURCE_QUOTE_UPDATE_TIME")
        quote_at=iso(r["quote_at"],"quote_at")
        card=cards_per_race[race][horse]
        if not (card["feature_known"]<quote_at<card["start"]):
            raise ValueError("HOLD_FUTURE_FEATURE_OR_POSTTIME_QUOTE")
        try:
            odds=float(r["win_odds"])
        except (ValueError,TypeError) as exc:
            raise ValueError("HOLD_INVALID_WIN_ODDS") from exc
        if not math.isfinite(odds) or odds<=1.0:
            raise ValueError("HOLD_NONFINITE_OR_INVALID_WIN_ODDS")
        if horse in quotes_per_race[race][quote_at]:
            raise ValueError("HOLD_DUPLICATE_QUOTE_AT_SOURCE_TIMESTAMP")
        quotes_per_race[race][quote_at][horse]=odds
    assembled=[]
    declined=Counter()
    for race,cards_by_horse in sorted(cards_per_race.items()):
        horses=sorted(cards_by_horse)
        starts={x["start"] for x in cards_by_horse.values()}
        if len(starts)!=1:
            raise ValueError("HOLD_INCONSISTENT_RACE_START")
        ts=sorted(quotes_per_race.get(race,{}))
        if len(ts)<3:
            declined["HOLD_NO_THREE_CERTIFIED_PRE_START_SNAPSHOTS"]+=1
            continue
        if any(set(quotes_per_race[race][t])!=set(horses) for t in ts):
            raise ValueError("HOLD_NOT_COMPLETE_SAME_FIELD_AT_EACH_QUOTE")
        if len(horses)<3:
            declined["HOLD_TOO_FEW_HORSES"]+=1
            continue
        g=sum(bool(cards_by_horse[h]["gene"]) for h in horses)
        if 0<g<len(horses):
            declined["HOLD_GENOTYPE_INCOMPLETE_RACE"]+=1
            # Keep for pedigree-only models; don't score gene channel.
        genetime_ok=all(
            not cards_by_horse[h]["gene"] or
            iso(next(r["genotype_known_at"] for r in cards if r["race_id"]==race and r["horse_id"]==h),
                "genotype_known_at")<ts[0]
            for h in horses
        )
        if not genetime_ok:
            raise ValueError("HOLD_GENOTYPE_AFTER_FIRST_MARKET_SNAPSHOT")
        q0=_supports(quotes_per_race[race][ts[0]],horses)
        qmid=_supports(quotes_per_race[race][ts[-2]],horses)
        qlast=_supports(quotes_per_race[race][ts[-1]],horses)
        kin=_center([cards_by_horse[h]["kin"] for h in horses])
        gene=_center([_gene_proxy(cards_by_horse[h]["gene"],cards_by_horse[h]["distance"])
                      if cards_by_horse[h]["gene"] else 0.0 for h in horses])
        assembled.append({
            "race_id":race,"date":next(iter(starts)).date().isoformat(),
            "n_horses":len(horses),"first_quote":ts[0].isoformat(),
            "early_last":ts[-2].isoformat(),"last_pre_start_quote":ts[-1].isoformat(),
            "q0":q0,"qmid":qmid,"qlast":qlast,
            "kin":kin,"genotype_distance":gene,"gene_complete":g==len(horses)
        })
    return assembled,{
        "all_races":len(cards_per_race),
        "eligible_races":len(assembled),
        "rejected_by_reason":dict(declined),
        "measured_genotype_card_rows":has_genotype,
        "note":"Relative reciprocal odds share, NOT calibrated win chance or observed betting volume"
    }


def _predict(r: dict, gamma: float=0.0, beta: float=0.0,
             gene_beta:float=0.0, threshold:float|None=None,
             high_gamma:float|None=None, initial:bool=False) -> list[float]:
    current=r["q0"] if initial else r["qmid"]
    q0=r["q0"]
    z=[]
    for i,p in enumerate(current):
        momentum=math.log(max(p,1e-15)/max(q0[i],1e-15))
        local_gamma=(high_gamma if threshold is not None
                     and abs(momentum)>threshold else gamma)
        if local_gamma is None:
            raise ValueError("HOLD_THRESHOLD_MODEL_HIGH_GAMMA_MISSING")
        z.append(math.log(p)+
                 (0.0 if initial else local_gamma*momentum)+
                 beta*r["kin"][i]+gene_beta*r["genotype_distance"][i])
    return _softmax(z)


def _kl(target: list[float],pred: list[float]) -> float:
    return sum(t*math.log(t/max(p,1e-15)) for t,p in zip(target,pred))


def _rmse(target: list[float],pred: list[float]) -> float:
    return math.sqrt(sum((t-p)**2 for t,p in zip(target,pred))/len(target))


def _train_grid(train:list[dict],mode:str)->tuple[float,float,float]:
    if mode=="momentum":
        candidates=[(g,0.0,0.0) for g in GAMMA]
    elif mode=="kin":
        candidates=[(0.0,b,0.0) for b in BETA]
    elif mode=="joint":
        candidates=[(g,b,0.0) for g in GAMMA for b in BETA]
    elif mode=="joint_genotype":
        candidates=[(g,b,v) for g in GAMMA for b in BETA for v in BETA]
    elif mode=="initial_kin":
        candidates=[(0.0,b,0.0) for b in BETA]
    elif mode=="threshold":
        # Thresholds are on *already observed* q0→qmid changes only.
        # Earlier race dates select a discrete regime, later dates test it.
        candidates=[(g,b,0.0,t,hi)
                    for t in (0.1,0.25,0.5)
                    for g in (0.0,0.5,1.0)
                    for hi in (0.0,0.5,1.5)
                    for b in (0.0,0.25,0.5)]
    else:
        raise ValueError("UNKNOWN_TRAIN_MODE")
    if mode=="joint_genotype":
        eligible=[r for r in train if r["gene_complete"]]
        if len(eligible)<5:
            raise ValueError("HOLD_GENOTYPE_COHORT_TRAIN_TOO_SMALL")
        train=eligible
    def loss(param):
        b=param[1]
        scores=[
            _kl(r["q0"],_softmax([b*k for k in r["kin"]]))
            if mode=="initial_kin" else
            _kl(r["qlast"],_predict(r,*param))
            for r in train
        ]
        return (sum(scores)/len(scores),sum(abs(v) for v in param),param)
    return min(candidates,key=loss)


def score(races:list[dict]) -> dict:
    days=sorted({r["date"] for r in races})
    if len(days)<8:
        return {"status":"HOLD_TOO_FEW_DISTINCT_RACE_DATES",
                "observed_races":len(races),"distinct_dates":len(days)}
    boundary=days[max(1,int(len(days)*0.8))]
    train=[r for r in races if r["date"]<boundary]
    test=[r for r in races if r["date"]>=boundary]
    if len(train)<6 or len(test)<2:
        return {"status":"HOLD_INSUFFICIENT_MARKET_TRAIN_OR_TEST",
                "train_races":len(train),"test_races":len(test)}
    parameters={
        "M_market_momentum":_train_grid(train,"momentum"),
        "M_kin_only":_train_grid(train,"kin"),
        "M_market_plus_kin":_train_grid(train,"joint"),
        "M_market_threshold_kin":_train_grid(train,"threshold"),
        "M_initial_kin":_train_grid(train,"initial_kin"),
    }
    # One fixed seeded family-information falsification: shuffle documented
    # relatedness only within each RACE, preserving every other market state.
    # Refit on earlier sham races; no calibration of permutation p-values.
    rng=random.Random(20261115)
    def shuffled(race):
        kin=list(race["kin"])
        rng.shuffle(kin)
        return {**race,"kin":kin}
    sham_train=[shuffled(r) for r in train]
    sham_test=[shuffled(r) for r in test]
    sham_weight=_train_grid(sham_train,"joint")
    genetr=[r for r in train if r["gene_complete"]]
    genet=[r for r in test if r["gene_complete"]]
    if len(genetr)>=5 and len(genet)>=2:
        parameters["M_market_kin_MSTN"]= _train_grid(train,"joint_genotype")
    def eval_one(method:str,parameter, subset):
        arr=[]
        for r in subset:
            if method=="M_initial_kin":
                target=r["q0"]
                # Cannot claim one source-based sire signal predicts *all* initial factors.
                pred=_softmax([parameter[1]*k for k in r["kin"]])
            else:
                target=r["qlast"]
                pred=_predict(r,*parameter)
            arr.append((_kl(target,pred),_rmse(target,pred)))
        return {
            "mean_KL_true_market_support_vs_model":sum(x[0] for x in arr)/len(arr),
            "mean_race_share_RMSE":sum(x[1] for x in arr)/len(arr),
        }
    zeros=(0.0,0.0,0.0)
    scores={
        "M_penultimate_market_persistence":eval_one("M_market",zeros,test),
        "M_earliest_market_persistence":{
            "mean_KL_true_market_support_vs_model":
                sum(_kl(r["qlast"],r["q0"]) for r in test)/len(test),
            "mean_race_share_RMSE":
                sum(_rmse(r["qlast"],r["q0"]) for r in test)/len(test)
        },
        "M_initial_uniform":{
            "mean_KL_true_market_support_vs_model":
                sum(_kl(r["q0"],[1/r["n_horses"]]*r["n_horses"]) for r in test)/len(test),
            "mean_race_share_RMSE":
                sum(_rmse(r["q0"],[1/r["n_horses"]]*r["n_horses"]) for r in test)/len(test)
        },
    }
    for k,v in parameters.items():
        sub=genet if k=="M_market_kin_MSTN" else test
        scores[k]=eval_one(k,v,sub)
    scores["M_market_plus_shuffled_kin"]=eval_one(
        "M_market_plus_shuffled_kin",sham_weight,sham_test)
    source_races=len(races)
    return {
        "status":"MARKET_SUPPORT_TIMESERIES_OUT_OF_DATE_SCORE_NOT_CAUSAL",
        "first_test_race_date":boundary,
        "training_races":len(train),"test_races":len(test),
        "train_latest_date":max(x["date"] for x in train),
        "no_races_from_same_calendar_day_cross_train_test":True,
        "outcome":"future_PRE_START_relative_implied_support_not_race_finish",
        "models":scores,
        "train_only_selected_parameters":{k:list(v) for k,v in parameters.items()},
        "negative_control_parameters":{"M_market_plus_shuffled_kin":list(sham_weight)},
        "negative_control_permutations":1,
        "negative_control_is_not_calibrated_p_value":True,
        "threshold_is_exploratory_not_critical_point":True,
        "genotype_channel":("MEASURED_MSTN_COHORT_ONLY" if "M_market_kin_MSTN" in parameters
                            else "HOLD_NO_VERIFIED_ID_LINKED_MSTN_COHORT"),
        "source_snapshot_count":source_races,
        "limitations":[
            "q_i normalized from 1/win_odds, not a directly measured vote count.",
            "Odds markets are pari-mutuel and conditional on other horses; q is not physiological performance.",
            "Genotype C-allele-count × distance is an exploratory proxy, NOT validated individual performance.",
            "No price movement threshold or genetic causality is identified by this model.",
            "No odds/money returns: last observed pre-race prices are not final settled payouts.",
            "No ability/win predictor; a separate outcome-calibrated model is required."
        ]
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-repo-snapshot",type=Path)
    parser.add_argument("--racecards",type=Path)
    parser.add_argument("--odds",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.audit_repo_snapshot:
        result=source_snapshot_readiness(args.audit_repo_snapshot)
    elif args.racecards and args.odds:
        card=read_rows(args.racecards,{"race_id","horse_id","start_at","feature_known_at","kin_signal","distance_m"})
        quote=read_rows(args.odds,{"race_id","horse_id","quote_at","win_odds","source_quote_time_verified"})
        races,qa=build_races(card,quote)
        result={"data_quality":qa,**score(races)}
    else:
        raise ValueError("HOLD_NEED_COMPLETE_MARKET_SNAPSHOT_OR_BOTH_SOURCE_TABLES")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
