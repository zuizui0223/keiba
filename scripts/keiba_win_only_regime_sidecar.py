#!/usr/bin/env python3
"""Prospective-ready WIN-only regime SIDE-CAR attached to PR30's original 6.

The original PR30 WIN-only freeze is immutable: six candidate vectors and
its source/card/code SHA stay exactly as they were. This *new*, separately
hashed B+ companion adds FIVE fixed candidates for the SAME race/target:
  1 continuous log-momentum gain r/(r+0.10/h)
  2 hard log-momentum gate 1{r>=0.10/h}
  3 PR19 no-information voter ABMs: fixed, smooth, hard feedback.

Price gates are NOT PR19 social-feedback gates. All rates use *actual*
first/middle quote source-update clock spacing and market-index log changes.
The prior PR30 15-minute target horizon, first-two-full-WIN selection,
fixed card, and source-chain SHA remain unchanged.

No true horse GPS/stakes/podium or legitimate JRA feed is acquired. Parent
PR30 physically linked horse ABM, marginal PDE and informed voter ABM
candidate vectors are preserved and scored AGAINST THE SAME target.
New candidates use PR19's original voter_path with arrival=5 (never
released): no independent horse signal, three stipulated laws, thirty
paired artificial seeds. Not thirty independent source observations.

Two independent freezes (parent and sidecar) require distinct external
GitHub SHA-only receipts BEFORE q2 for any remotely time-witnessed
comparison. This module generates neither a comment nor a live receipt;
all local results, including fixture scores, remain UNATTESTED.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from keiba_operator_winwide_capture import (
    ROOT, JST, _aware, _check_card, _read_ledger, _dump,
    _write_new_private,
)
from keiba_win_only_shadow_lane import (
    _first_two_full_win, _model_code_manifest,
    _normalize, verify_win_only, score_win_only,
    MODEL_NAMES as PARENT_MODELS, MISSING as PARENT_MISSING,
    SCORE_STATUS as PARENT_SCORE_STATUS,
)
from odds_shadow_freeze_score import _normalized_odds
from keiba_endogenous_threshold_null_bridge import (
    voter_path, RATE_SCALE_LOG_PER_HOUR,
)
from keiba_fixed_denominator_market_campaign import (
    LOCKED_MARKET_HORIZON_MINUTES,
)

SCHEMA="KEIBA_WIN_ONLY_REGIME_COMPANION_FREEZE_V1"
SCORE_SCHEMA="KEIBA_WIN_ONLY_REGIME_COMPANION_LOCAL_SCORE_V1"
STATUS="B_PLUS_SEPARATE_SOURCE_CHAIN_COMPANION_NO_EXTERNAL_PRESEAL"
SCORED_STATUS="B_PLUS_LOCAL_SAME_RACE_TARGET_NOT_SOURCE_AUTHENTICATED"
MISSING_STATUS="HOLD_B_PLUS_ORIGINAL_WIN_TARGET_UNOBSERVED"
SEEDS=30
SEED=20261031
CODE_FILES=(
    "scripts/keiba_win_only_regime_sidecar.py",
    "scripts/keiba_win_only_shadow_lane.py",
    "scripts/keiba_endogenous_threshold_null_bridge.py",
    "scripts/keiba_operator_winwide_capture.py",
    "scripts/odds_shadow_freeze_score.py",
)
MODELS=(
    "WIN_continuous_momentum_gain_r_over_rplus010",
    "WIN_hard_gate_momentum_r_ge_010_per_hour",
    "uninformed_PR19_fixed_ABM",
    "uninformed_PR19_smooth_ABM",
    "uninformed_PR19_hard_ABM",
)
VOTER_POLICIES={
    "uninformed_PR19_fixed_ABM":"fixed",
    "uninformed_PR19_smooth_ABM":"smooth",
    "uninformed_PR19_hard_ABM":"hard",
}


def _canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,
                      separators=(",",":"),allow_nan=False)


def _seal(obj):
    return sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _code_manifest(root=ROOT):
    return {rel:sha256((Path(root)/rel).read_bytes()).hexdigest()
            for rel in CODE_FILES}


def _vector(rows, ids):
    if (not isinstance(rows,list) or
            [r.get("n") for r in rows if isinstance(r,dict)]!=ids or
            any(not isinstance(r,dict) or set(r)!={"n","p"} or
                    type(r["p"]) not in (int,float)
                for r in rows)):
        raise ValueError("HOLD_BPLUS_MODEL_ROSTER_OR_SCHEMA")
    v=np.asarray([r["p"] for r in rows],dtype=float)
    if (np.any(v<=0) or not np.all(np.isfinite(v)) or
            not math.isclose(float(v.sum()),1.,abs_tol=1e-10)):
        raise ValueError("HOLD_BPLUS_INVALID_FULL_FIELD_SIMPLEX")
    return v


def _rows(v, ids):
    v=_normalize(v)
    if len(v)!=len(ids):
        raise ValueError("HOLD_BPLUS_PRICE_HORSE_ID_MISMATCH")
    return [{"n":i,"p":float(q)} for i,q in zip(ids,v)]


def _project(q1, log_velocity, gain):
    if (not math.isfinite(gain) or not 0<=gain<=1 or
            len(log_velocity)!=len(q1)):
        raise ValueError("HOLD_BPLUS_INVALID_GAIN")
    logw=np.log(q1)+gain*log_velocity
    return _normalize(np.exp(logw-np.max(logw)))


def freeze_companion(ledger,card,parent,*,freeze_at_jst=None,
                     seed=SEED,synthetic_seeds=SEEDS):
    """Must be made before q2. Injections are test-only local clock claims."""
    if type(seed) is not int or seed!=SEED or (
            type(synthetic_seeds) is not int or synthetic_seeds!=SEEDS):
        raise ValueError("HOLD_BPLUS_CHANGING_PREDECLARED_SEEDS")
    p=verify_win_only(parent)
    c=_check_card(card)
    if p["model_code_content_SHA256"]!=_model_code_manifest():
        raise ValueError("HOLD_BPLUS_PARENT_MODEL_CODE_CHANGED")
    if (p["race_id"]!=c["race_id"] or
            p["provider"]!=c["provider"] or
            p["final_card_SHA256"]!=sha256(_dump(c).encode("utf-8")).hexdigest()
            or p["horse_numbers"]!=c["horse_numbers"]):
        raise ValueError("HOLD_BPLUS_PARENT_FINAL_CARD_CHANGED")
    now=_aware(freeze_at_jst or datetime.now(JST).isoformat())
    parent_clock=_aware(p["local_freeze_created"])
    start=_aware(p["target_WIN_window_start"])
    if not parent_clock<=now<start:
        raise ValueError("HOLD_BPLUS_COMPANION_AFTER_TARGET_OR_BEFORE_PARENT")
    s=_first_two_full_win(ledger,c,frozen_at=now.isoformat())
    if (len(s["all_events"])!=p["original_capture_prefix_length"] or
            s["all_events"][-1]["event_sha256"]!=
              p["original_local_capture_chain_prefix_SHA256"] or
            s["first_t"].isoformat()!=p["source_first_WIN_published"] or
            s["second_t"].isoformat()!=p["source_second_WIN_published"] or
            s["target_start"].isoformat()!=p["target_WIN_window_start"] or
            s["target_end"].isoformat()!=p["target_WIN_window_end"] or
            s["rx1"].isoformat()!=p["source_first_WIN_received"] or
            s["rx2"].isoformat()!=p["source_second_WIN_received"]):
        raise ValueError("HOLD_BPLUS_NOT_SAME_ORIGINAL_PR30_CAPTURE_CHAIN")
    ids=p["horse_numbers"]
    q0=_normalize([1/s["prices_first"][i] for i in ids])
    q1=_normalize([1/s["prices_second"][i] for i in ids])
    parent_q1=_vector(p["fixed_next_quote_model_indices"][
        "WIN_mid_persistence"],ids)
    if not np.allclose(q1,parent_q1,rtol=0,atol=1e-12):
        raise ValueError("HOLD_BPLUS_PARENT_PERSISTENCE_INCONSISTENT")
    hours=(s["second_t"]-s["first_t"]).total_seconds()/3600
    if hours<=0:
        raise ValueError("HOLD_BPLUS_INVALID_INITIAL_SOURCE_CLOCK_RATE")
    rate=float(np.max(np.abs(np.log(q1/q0)))/hours)
    velocity=np.log(q1/q0)*(
        LOCKED_MARKET_HORIZON_MINUTES/60.)/hours
    reference_momentum=_project(q1,velocity,1.0)
    parent_momentum=_vector(p["fixed_next_quote_model_indices"][
        "WIN_log_momentum"],ids)
    if not np.allclose(reference_momentum,parent_momentum,rtol=0,atol=1e-12):
        raise ValueError("HOLD_BPLUS_PARENT_MOMENTUM_INCONSISTENT")
    alpha_smooth=rate/(rate+RATE_SCALE_LOG_PER_HOUR)
    alpha_hard=1.0 if rate>=RATE_SCALE_LOG_PER_HOUR else 0.0
    candidates={
        MODELS[0]:_rows(_project(q1,velocity,alpha_smooth),ids),
        MODELS[1]:_rows(_project(q1,velocity,alpha_hard),ids),
    }
    nulls={name:[] for name in VOTER_POLICIES}
    noinfo_switches={name:[] for name in VOTER_POLICIES}
    for j in range(SEEDS):
        k=seed+1009*j
        for name,policy in VOTER_POLICIES.items():
            sim=voter_path(q1,q1,policy=policy,arrival=5,seed=k,
                           duration_hours=LOCKED_MARKET_HORIZON_MINUTES/60.)
            if sim["information_available_round_count"]!=0:
                raise ValueError("HOLD_BPLUS_HORSE_SIGNAL_REACHED_UNINFORMED")
            nulls[name].append(_rows(sim["final"],ids))
            noinfo_switches[name].append(
                int(sim["hard_gate_active_round_count"]))
    payload={
        "schema":SCHEMA,"status":STATUS,
        "source_race_id":p["race_id"],"registered_slot_id":
            p["registered_primary_slot_id"],
        "source_provider":p["provider"],
        "source_provenance":p["card_operator_provenance"],
        "operator_rights_reviewed_locally_only":
            p["operator_rights_confirmed_locally_only"],
        "parent_original_six_model_freeze_SHA256":
            parent["seal_sha256_of_canonical_payload"],
        "original_source_chain_head_SHA256":
            p["original_local_capture_chain_prefix_SHA256"],
        "original_source_chain_event_count":
            p["original_capture_prefix_length"],
        "original_final_card_SHA256":p["final_card_SHA256"],
        "horse_numbers":list(ids),
        "source_first_WIN_published":p["source_first_WIN_published"],
        "source_first_WIN_received":p["source_first_WIN_received"],
        "source_second_WIN_published":p["source_second_WIN_published"],
        "source_second_WIN_received":p["source_second_WIN_received"],
        "original_parent_freeze_clock":p["local_freeze_created"],
        "sidecar_local_freeze_clock":now.isoformat(),
        "target_WIN_window_start":p["target_WIN_window_start"],
        "target_WIN_window_end":p["target_WIN_window_end"],
        "scheduled_post":p["scheduled_post"],
        "code_file_SHA256":_code_manifest(),
        "fixed_price_change_rate_log_index_per_hour":rate,
        "fixed_rate_scale_log_index_per_hour":RATE_SCALE_LOG_PER_HOUR,
        "fixed_continuous_alpha":alpha_smooth,
        "fixed_hard_alpha":alpha_hard,
        "fixed_model_seed":SEED,
        "fixed_synthetic_vote_seeds":SEEDS,
        "fixed_target_horizon_minutes":LOCKED_MARKET_HORIZON_MINUTES,
        "sidecar_price_candidate_indices":candidates,
        "sidecar_no_new_horse_signal_vote_paths":nulls,
        "sidecar_no_new_horse_signal_hard_gate_counts":noinfo_switches,
        "one_original_market_target_same_as_PR30":True,
        "original_six_models_not_replaced":list(PARENT_MODELS),
        "no_actual_bettor_votes_horse_GPS_or_podium_consumed":True,
        "price_gate_distinct_from_bettor_feedback_gate":True,
        "not_eligible_as_prospective_until_distinct_remote_SHA":True,
    }
    frozen={
        "schema":SCHEMA,
        "payload":payload,
        "sidecar_local_SHA256_not_remote_receipt":_seal(payload),
        "external_pre_target_GitHub_SHA_proven":False,
    }
    verify_companion(frozen)
    return frozen


def verify_companion(frozen):
    if (not isinstance(frozen,dict) or set(frozen)!={
            "schema","payload","sidecar_local_SHA256_not_remote_receipt",
            "external_pre_target_GitHub_SHA_proven"} or
            frozen["schema"]!=SCHEMA or
            frozen["external_pre_target_GitHub_SHA_proven"] is not False):
        raise ValueError("HOLD_BPLUS_COMPANION_SCHEMA_OR_FALSE_REMOTE_CLAIM")
    p=frozen["payload"]
    if (p.get("schema")!=SCHEMA or p.get("status")!=STATUS or
            _seal(p)!=frozen["sidecar_local_SHA256_not_remote_receipt"]):
        raise ValueError("HOLD_BPLUS_COMPANION_SHA_OR_PAYLOAD_CHANGED")
    ids=p.get("horse_numbers")
    candidates=p.get("sidecar_price_candidate_indices")
    paths=p.get("sidecar_no_new_horse_signal_vote_paths")
    counts=p.get("sidecar_no_new_horse_signal_hard_gate_counts")
    if (type(ids) is not list or not 5<=len(ids)<=30 or
            ids!=sorted(set(ids)) or
            not isinstance(candidates,dict) or
            set(candidates)!=set(MODELS[:2]) or
            not isinstance(paths,dict) or
            set(paths)!=set(VOTER_POLICIES) or
            not isinstance(counts,dict) or
            set(counts)!=set(VOTER_POLICIES)):
        raise ValueError("HOLD_BPLUS_COMPANION_MODEL_OR_ROSTER_CHANGED")
    for rows in candidates.values():
        _vector(rows,ids)
    for name in VOTER_POLICIES:
        if (len(paths[name])!=SEEDS or len(counts[name])!=SEEDS or
                any(type(x) is not int or not 0<=x<=4 for x in counts[name])):
            raise ValueError("HOLD_BPLUS_NOINFO_SEED_COUNT_CHANGED")
        for rows in paths[name]:
            _vector(rows,ids)
    if (p["fixed_model_seed"]!=SEED or
            p["fixed_synthetic_vote_seeds"]!=SEEDS or
            p["fixed_target_horizon_minutes"]!=LOCKED_MARKET_HORIZON_MINUTES or
            p["fixed_rate_scale_log_index_per_hour"]!=RATE_SCALE_LOG_PER_HOUR or
            p["original_six_models_not_replaced"]!=list(PARENT_MODELS) or
            p["one_original_market_target_same_as_PR30"] is not True or
            p["no_actual_bettor_votes_horse_GPS_or_podium_consumed"] is not True or
            p["price_gate_distinct_from_bettor_feedback_gate"] is not True):
        raise ValueError("HOLD_BPLUS_COMPANION_RULES_NOT_PREDECLARED")
    return p


def _metric(pred,target):
    a=_normalize(pred);b=_normalize(target)
    return {
        "TV_pp":float(50*np.abs(a-b).sum()),
        "KL_later_target_vs_model_nats":float(np.sum(b*np.log(b/a))),
    }


def score_companion(ledger,card,parent,frozen,*,asof,
                    operator_declares_capture_complete):
    """No q2 read until parent score has verified target/card/source chain."""
    p=verify_companion(frozen)
    original=verify_win_only(parent)
    if p["parent_original_six_model_freeze_SHA256"]!=parent[
            "seal_sha256_of_canonical_payload"]:
        raise ValueError("HOLD_BPLUS_DIFFERENT_PARENT_SIX_MODEL_SHA")
    if (p["original_source_chain_head_SHA256"]!=
            original["original_local_capture_chain_prefix_SHA256"] or
            p["original_final_card_SHA256"]!=original["final_card_SHA256"] or
            p["source_race_id"]!=original["race_id"] or
            p["registered_slot_id"]!=original["registered_primary_slot_id"] or
            p["source_provider"]!=original["provider"] or
            p["horse_numbers"]!=original["horse_numbers"] or
            p["target_WIN_window_start"]!=original["target_WIN_window_start"] or
            p["target_WIN_window_end"]!=original["target_WIN_window_end"] or
            p["source_first_WIN_published"]!=original["source_first_WIN_published"] or
            p["source_second_WIN_published"]!=original["source_second_WIN_published"]):
        raise ValueError("HOLD_BPLUS_PARENT_SOURCE_TARGET_OR_ROSTER_MISMATCH")
    if p["code_file_SHA256"]!=_code_manifest():
        raise ValueError("HOLD_BPLUS_SIDECAR_OR_PARENT_CODE_CHANGED")
    # Exactly one target, same ledger, target window and source controls
    # as the ORIGINAL SIX-MODEL PR30 lane. Do not invent a second target.
    origin=score_win_only(ledger,card,parent,asof=asof,
              operator_declares_capture_complete=
                  operator_declares_capture_complete)
    if origin["status"]==PARENT_MISSING:
        return {
            "schema":SCORE_SCHEMA,"status":MISSING_STATUS,
            "race_id":p["source_race_id"],
            "parent_original_six_model_SHA256":
                p["parent_original_six_model_freeze_SHA256"],
            "sidecar_local_SHA256":
                frozen["sidecar_local_SHA256_not_remote_receipt"],
            "one_original_market_target_observed":False,
            "unobserved_original_target_not_imputed":True,
            "new_independently_proven_next_market_trial":False,
        }
    if origin["status"]!=PARENT_SCORE_STATUS:
        raise ValueError("HOLD_BPLUS_PARENT_TARGET_NOT_LOCALLY_SCORED")
    events=_read_ledger(ledger)
    t=origin["source_target_published"]
    receipt=origin["source_target_received"]
    matched=[e["captured_source"] for e in events
             if e["captured_source"]["market"]=="win" and
                e["captured_source"]["source_updated_at_jst"]==t and
                e["captured_at_jst"]==receipt and
                e["captured_source"]["provider"]==p["source_provider"] and
                e["captured_source"]["race_id"]==p["source_race_id"]]
    if len(matched)!=1:
        raise ValueError("HOLD_BPLUS_CANNOT_RECONSTRUCT_SAME_EXACT_Q2_CAPTURE")
    prices=_normalized_odds(matched[0]["odds_by_horse_number"])
    ids=p["horse_numbers"]
    if set(prices)!=set(ids):
        raise ValueError("HOLD_BPLUS_TARGET_ROSTER_INCOMPLETE")
    q2=_normalize([1/prices[i] for i in ids])
    b1=_vector(original["fixed_next_quote_model_indices"][
        "WIN_mid_persistence"],ids)
    bm=_vector(original["fixed_next_quote_model_indices"][
        "WIN_log_momentum"],ids)
    for label,model in (("WIN_mid_persistence",b1),
                        ("WIN_log_momentum",bm)):
        benchmark=origin["model_score_TV_KL"][label]
        score=_metric(model,q2)
        if (not math.isclose(score["TV_pp"],
                   benchmark["target_price_index_TV_pp"],abs_tol=1e-10) or
            not math.isclose(score["KL_later_target_vs_model_nats"],
                   benchmark["target_price_index_KL_nats"],abs_tol=1e-10)):
            raise ValueError("HOLD_BPLUS_PARENT_AND_SIDECAR_TARGET_DISAGREE")
    extension={}
    for name,rows in p["sidecar_price_candidate_indices"].items():
        extension[name]=_metric(_vector(rows,ids),q2)
    for name,paths in p["sidecar_no_new_horse_signal_vote_paths"].items():
        entries=[_metric(_vector(rows,ids),q2) for rows in paths]
        switches=p["sidecar_no_new_horse_signal_hard_gate_counts"][name]
        extension[name]={
            "mean_TV_pp_over_artificial_seeds":mean(x["TV_pp"] for x in entries),
            "min_TV_pp_over_artificial_seeds":min(x["TV_pp"] for x in entries),
            "max_TV_pp_over_artificial_seeds":max(x["TV_pp"] for x in entries),
            "mean_KL_later_target_vs_model_nats_over_artificial_seeds":
                mean(x["KL_later_target_vs_model_nats"] for x in entries),
            "mean_assumed_hard_gate_rounds_without_new_horse_information":
                mean(switches),
            "synthetic_seed_count_NOT_independent_races":len(entries),
        }
    return {
        "schema":SCORE_SCHEMA,
        "status":SCORED_STATUS,
        "race_id":p["source_race_id"],
        "registered_slot_id":p["registered_slot_id"],
        "source_target_published":t,
        "source_target_received":receipt,
        "one_original_market_target_observed":True,
        "original_PR30_six_model_scores_unchanged":
            origin["model_score_TV_KL"],
        "five_additional_companion_models_same_original_q2":extension,
        "same_target_persistence_TV_pp":
            origin["model_score_TV_KL"]["WIN_mid_persistence"][
                "target_price_index_TV_pp"],
        "parent_original_six_model_SHA256":
            p["parent_original_six_model_freeze_SHA256"],
        "sidecar_local_SHA256":
            frozen["sidecar_local_SHA256_not_remote_receipt"],
        "total_models_same_one_race":len(PARENT_MODELS)+len(MODELS),
        "independent_race_count_not_six_plus_five":1,
        "genuine_external_SHA_verification_of_both_freezes":False,
        "original_source_and_target_completeness_only_locally_declared":True,
        "one_market_target_CANNOT_IDENTIFY_REAL_THRESHOLD_OR_HERDING":True,
        "no_real_stakes_horse_GPS_win_probabilities_or_bet_ROI":True,
        "new_independently_proven_next_market_trial":False,
    }


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    a=sub.add_parser("freeze")
    a.add_argument("--ledger",type=Path,required=True)
    a.add_argument("--final-card",type=Path,required=True)
    a.add_argument("--original-win-only-freeze",type=Path,required=True)
    a.add_argument("--private-output",type=Path,required=True)
    b=sub.add_parser("score")
    b.add_argument("--ledger",type=Path,required=True)
    b.add_argument("--final-card",type=Path,required=True)
    b.add_argument("--original-win-only-freeze",type=Path,required=True)
    b.add_argument("--sidecar-freeze",type=Path,required=True)
    b.add_argument("--operator-confirms-complete-capture",
                   action="store_true")
    b.add_argument("--private-output",type=Path,required=True)
    args=parser.parse_args()
    c=_load(args.final_card)
    parent=_load(args.original_win_only_freeze)
    if args.command=="freeze":
        data=freeze_companion(args.ledger,c,parent)
    else:
        data=score_companion(args.ledger,c,parent,_load(args.sidecar_freeze),
             asof=datetime.now(JST).isoformat(),
             operator_declares_capture_complete=
                 args.operator_confirms_complete_capture)
    _write_new_private(args.private_output,data)
    print(json.dumps({
        "race_id":data.get("race_id",data.get("payload",{}).get("source_race_id")),
        "status":data.get("status",data.get("payload",{}).get("status")),
        "real_remote_verified":False,
        "parent_six_unchanged":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
