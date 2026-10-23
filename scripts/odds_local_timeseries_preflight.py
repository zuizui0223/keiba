#!/usr/bin/env python3
"""Validate an already-authorized LOCAL normalized win-odds time-series export.

This is NOT a JV-Link/0B41 binary parser and does not download licensed
JRA-VAN records. Export is normalized separately in the operator's
rights-cleared environment. No raw prices/runner identities are copied
to the output: aggregate race-level readiness and market-movement only.

Synthetic CLI example:
  python scripts/odds_local_timeseries_preflight.py --demo-synthetic \
    --output tmp/odds-local-preflight.json

For actual local input:
  python scripts/odds_local_timeseries_preflight.py --input PRIVATE.json \
    --output tmp/odds-local-preflight.json

Exactly one source capture clock (producer quote time) per quote snapshot.
Observation/receipt time is separate. Released archives where producer
timestamp is unknown MUST return HOLD_SOURCE_CLOCKS_NOT_VERIFIED.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import random
from statistics import mean

STATUS_READY_SYN = "SYNTHETIC_SOURCE_PANEL_DESIGN_READY_NOT_EVIDENCE"
STATUS_READY_LOCAL = "LOCAL_SELF_ATTESTED_ACCESS_NOT_INDEPENDENTLY_VERIFIED_RIGHTS"
STATUS_HOLD = "HOLD_INSUFFICIENT_SOURCE_PANEL"
SCHEMA = "KEIBA_AUTHORIZED_NORMALIZED_WIN_TIMESERIES_V1"


def _aware(text):
    if not isinstance(text,str):
        raise ValueError("HOLD_TIME_REQUIRED")
    ts=datetime.fromisoformat(text)
    if ts.utcoffset() is None:
        raise ValueError("HOLD_TIMEZONE_REQUIRED")
    return ts


def _normalize(odds):
    if not isinstance(odds,dict) or len(odds)<5:
        raise ValueError("HOLD_INCOMPLETE_WIN_ODDS_FIELD")
    if any((not isinstance(k,str) or not k.isdecimal() or
            type(v) not in (float,int) or
            not math.isfinite(v) or v<=1.0)
           for k,v in odds.items()):
        raise ValueError("HOLD_INVALID_WIN_ODDS")
    n=[int(k) for k in odds]
    if len(set(n))!=len(n):
        raise ValueError("HOLD_NONUNIQUE_HORSE_NUMBERS")
    weights={int(i):1/o for i,o in odds.items()}
    total=sum(weights.values())
    return {i:v/total for i,v in weights.items()}


def intermediate_path_readiness(series):
    """Source-time weighted middle-price curvature of normalized odds.

    This is purely descriptive even with all 3+ clocks; it does not
    estimate additional winner information, dynamics, herding, or
    independently calibrated probabilities.
    """
    if len(series)<3:
        return {
            "status":"HOLD_THREE_DISTINCT_SOURCE_TIMEPOINTS_REQUIRED_FOR_MIDDLE_PATH",
            "intermediate_points":0,
            "additional_winner_forecast_information_verified":False,
        }
    first_t,first_q=series[0]
    mid_t,mid_q=series[(len(series)-1)//2]
    last_t,last_q=series[-1]
    if set(first_q)!=set(mid_q) or set(mid_q)!=set(last_q):
        raise ValueError("HOLD_MIDDLE_ODDS_ROSTER")
    u=(mid_t-first_t)/(last_t-first_t)
    if not 0 < u < 1:
        raise ValueError("HOLD_MIDDLE_TIMESTAMP_NOT_STRICTLY_INTERIOR")
    raw=[
        math.log(mid_q[i]) - (
            (1-u)*math.log(first_q[i])+u*math.log(last_q[i]))
        for i in first_q
    ]
    center=mean(raw)
    curvature=[v-center for v in raw]
    sd=math.sqrt(mean(x*x for x in curvature))
    reversal=sum(
        (math.log(mid_q[i]/first_q[i])*math.log(last_q[i]/mid_q[i]) < 0)
        for i in first_q
    )
    return {
        "status":"SOURCE_TIME_WEIGHTS_AND_MIDDLE_CURVATURE_COMPUTED_NOT_FORECAST_SKILL",
        "intermediate_points":len(series)-2,
        "representative_interior_fraction_elapsed":u,
        "crosshorse_sd_of_centered_intermediate_log_relative_price_curvature":sd,
        "horses_with_direction_reversal_from_first_to_mid_to_last":reversal,
        "source_update_times_verified_by_supplied_input_flag_only":True,
        "additional_winner_forecast_information_verified":False,
        "causal_asynchrony_or_bettor_herding_identified":False,
    }


def race_preflight(r):
    raceid=r.get("race_id")
    if not isinstance(raceid,str) or not raceid:
        raise ValueError("HOLD_RACE_ID_MISSING")
    start=_aware(r.get("post_jst"))
    snaps=r.get("snapshots")
    if not isinstance(snaps,list) or len(snaps)<2:
        return {"race_id":raceid,"status":"HOLD_NEED_AT_LEAST_TWO_PRICE_SNAPSHOTS",
                "snapshot_count":len(snaps) if isinstance(snaps,list) else 0}
    summaries=[]
    original_field=None
    lasttime=None
    for snap in snaps:
        if snap.get("bet_type")!="win":
            raise ValueError("HOLD_MIXED_BET_EVENT_TYPES")
        if snap.get("producer_clock_verified") is not True:
            return {"race_id":raceid,"status":"HOLD_SOURCE_CLOCKS_NOT_VERIFIED",
                    "snapshot_count":len(snaps)}
        published=_aware(snap.get("producer_quote_updated_at_jst"))
        observed=_aware(snap.get("received_at_jst"))
        if (not published<=observed<start or
            published>=start-timedelta(minutes=10)):
            raise ValueError("HOLD_PRESTART_PUBLICATION_TIME_LEAKAGE")
        if lasttime is not None and published<=lasttime:
            raise ValueError("HOLD_NONMONOTONE_QUOTES_OR_DUPLICATE_TIMESTAMP")
        q=_normalize(snap.get("win_odds_by_horse"))
        if original_field is None:
            original_field=set(q)
        elif set(q)!=original_field:
            return {"race_id":raceid,"status":"HOLD_HORSE_ROSTER_CHANGED",
                    "snapshot_count":len(snaps)}
        lasttime=published
        summaries.append((published,q))
    transitions=[]
    for (t0,q0),(t1,q1) in zip(summaries,summaries[1:]):
        d=0.5*sum(abs(q1[i]-q0[i]) for i in q0)
        transitions.append({
            "minutes_between_provider_quote_updates":(t1-t0).total_seconds()/60,
            "relative_price_weight_redistribution_pct_points":d*100,
        })
    return {
        "race_id":raceid,"status":"SOURCE_CLOCK_AND_FULL_FIELD_PASSED",
        "n_horses":len(original_field),"snapshot_count":len(snaps),
        "update_intervals":len(transitions),
        "first_to_last_minutes":(summaries[-1][0]-summaries[0][0]).total_seconds()/60,
        "max_intermediate_relative_quote_TV_pp":max(t["relative_price_weight_redistribution_pct_points"] for t in transitions),
        "first_to_last_relative_quote_TV_pp":50*sum(
            abs(summaries[-1][1][i]-summaries[0][1][i])
            for i in original_field),
        "intermediate_path_curvature_readiness":intermediate_path_readiness(summaries),
        "features_or_verified_outcomes_used":False,
        "win_odds_price_proxy_is_not_true_pool_share":True,
    }


def audit(payload):
    if payload.get("schema")!=SCHEMA:
        raise ValueError("HOLD_SOURCE_TIMESERIES_SCHEMA_MISMATCH")
    origin=payload.get("origin")
    if origin not in ("synthetic","local_operator_authorized_normalized_export"):
        raise ValueError("HOLD_INVALID_SOURCE_OR_UNAUTHORIZED_DISTRIBUTION")
    if origin!="synthetic" and payload.get("operator_confirmed_research_access") is not True:
        raise ValueError("HOLD_RESEARCH_ACCESS_NOT_SELF_ATTESTED")
    if payload.get("raw_records_redistributable") is not False:
        raise ValueError("HOLD_RAW_RECORD_REDISTRIBUTION_NOT_PERMITTED_IN_THIS_WORKFLOW")
    if payload.get("market_family")!="win" or payload.get("normalized_record_family") not in (
            "JV_TS_O1_authorized_local_normalization", "synthetic_win_timeline"):
        raise ValueError("HOLD_INVALID_OR_UNKNOWN_RECORD_FAMILY")
    races=payload.get("races")
    if not isinstance(races,list) or not races:
        raise ValueError("HOLD_NO_RACES")
    ids=[r.get("race_id") for r in races]
    if len(set(ids))!=len(ids):
        raise ValueError("HOLD_DUPLICATE_RACE")
    reports=[race_preflight(r) for r in races]
    passed=[r for r in reports if r["status"]=="SOURCE_CLOCK_AND_FULL_FIELD_PASSED"]
    dates={_aware(r["post_jst"]).date().isoformat() for r in races}
    total_snapshots=sum(r.get("snapshot_count",0) for r in reports)
    return {
        "status": (
            (STATUS_READY_SYN if origin=="synthetic" else STATUS_READY_LOCAL)
            if len(passed)==len(races) and len(races)>=60 and len(dates)>=8
            else STATUS_HOLD
        ),
        "origin":origin,
        "original_record_types_and_bytes_never_exported":True,
        "operator_research_license_attestation_is_not_independent_legal_verification":
            origin!="synthetic",
        "source":payload.get("source_description","no raw records in output"),
        "unique_race_count":len(races),
        "distinct_meeting_dates":len(dates),
        "full_prestart_verified_races":len(passed),
        "full_prestart_three_plus_timeseries_races":sum(
            r["snapshot_count"]>=3 for r in passed),
        "middle_path_sufficient_source_observations_not_causal_identification":True,
        "raw_snapshots_in_input":total_snapshots,
        "future_threshold_minimum_races_60_dates_8_is_engineering_not_power":True,
        "real_future_race_win_and_top3_skill_estimated":False,
        "time_window_requirements":"All source quote times <=10 min before start; two or more complete full-field win snapshots, no scratches or changed runner roster without explicit treatment",
        "failure_status_counts":{
            status:sum(x["status"]==status for x in reports)
            for status in sorted(set(x["status"] for x in reports))
            if status!="SOURCE_CLOCK_AND_FULL_FIELD_PASSED"
        },
        "aggregate_passing_market_motion": {
            "mean_first_last_price_TV_pp":mean(r["first_to_last_relative_quote_TV_pp"] for r in passed) if passed else None,
            "mean_archived_snapshots_per_complete_race":mean(r["snapshot_count"] for r in passed) if passed else None,
            "total_horse_entries_in_passing_races":sum(r["n_horses"] for r in passed),
        },
        "per_race_aggregate_only":reports,
    }


def synthetic_demo(seed=20261023,dates=10,races_per_day=6,n_horses=12):
    rng=random.Random(seed)
    start=datetime.fromisoformat("2026-01-01T13:00:00+09:00")
    races=[]
    for day in range(dates):
        for k in range(races_per_day):
            post=start+timedelta(days=day,minutes=k*20)
            baseline=[rng.uniform(.05,1) for _ in range(n_horses)]
            snapshots=[]
            for mins in (120,60,25):
                prices={str(i+1):round(1.1+30/(baseline[i]*rng.uniform(.90,1.10)),1)
                        for i in range(n_horses)}
                ts=post-timedelta(minutes=mins)
                snapshots.append({
                    "bet_type":"win","producer_clock_verified":True,
                    "producer_quote_updated_at_jst":ts.isoformat(),
                    "received_at_jst":(ts+timedelta(seconds=20)).isoformat(),
                    "win_odds_by_horse":prices,
                })
            races.append({
                "race_id":f"FICTIONAL-{day:03d}-{k:02d}",
                "post_jst":post.isoformat(),
                "snapshots":snapshots,
            })
    return {
        "schema":SCHEMA,"origin":"synthetic",
        "source_description":"fictional data; never a JRA or JRA-VAN record",
        "raw_records_redistributable":False,
        "market_family":"win",
        "normalized_record_family":"synthetic_win_timeline",
        "races":races,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",type=Path)
    ap.add_argument("--demo-synthetic",action="store_true")
    ap.add_argument("--output",type=Path,
                    default=Path("tmp/odds-timeseries-preflight.json"))
    args=ap.parse_args()
    if args.demo_synthetic==bool(args.input):
        raise ValueError("Provide exactly one of --input or --demo-synthetic")
    raw=synthetic_demo() if args.demo_synthetic else json.loads(
        args.input.read_text(encoding="utf-8"))
    report=audit(raw)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "races":report["unique_race_count"],
        "days":report["distinct_meeting_dates"],
        "full":report["full_prestart_verified_races"],
        "snapshots":report["raw_snapshots_in_input"],
        "real_winning_probability_calibrated":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
