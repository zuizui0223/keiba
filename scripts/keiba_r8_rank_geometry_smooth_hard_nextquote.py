#!/usr/bin/env python3
"""R8 price-only continuous/hard rank movement versus no-information voter ABM.

ACTUAL locked archival R8 early & middle full WIN quotes: 2026-10-12 12:21,
13:26. Build EVERY 13:44 market-index candidate from early/middle only.
Only after candidate freeze verification, open source SHA-locked 13:44
full WIN target and compute price prediction TV/KL, not finishing order.

Forecast set (parameters externally inherited/fixed, NOT fitted to q2):
  latest-WIN-index persistence
  smooth uncapped log-odds momentum k=1
  continuous saturating momentum gain r/(r+0.10/h)
  hard gate full momentum iff r>=0.10/h, else persist
  PR19 original fixed/smooth/hard bettor ABM WITHOUT ANY horse signal,
  30 paired seeds per rule, all synthetic, 4 rounds, 250 votes each.

The analytic gates in the two momentum models ARE NOT PR19 bettor
herding exponents: compare them as distinct price-only extrapolations.
PR19 fixed/smooth/hard original ABM is separately replayed as an
information-free negative control. Score only ONE archived target;
seeds are numerical repetitions, not 30 independent market examples.
No horse GPS, bettor stakes, threshold parameter inference, genuine
future prospective receipts, betting EV, race results or winner labels.

All code and forecast SHA generated LONG AFTER the original Oct12 target;
even if target bytes are opened only after candidates in execution, this
is RETROSPECTIVE verification and cannot substantiate predictive skill.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from odds_r8_next_win_market_forecast import (
    source_only_features, win_proxy, aware, NEXT_HORIZON_MINUTES, SOURCE_RACE,
)
from keiba_r8_threepoint_conditional_shadow import validate_later_quote
from keiba_endogenous_threshold_null_bridge import (
    RATE_SCALE_LOG_PER_HOUR, voter_path,
)
from keiba_public_article_vs_real_archival_rank_geometry import rank_contrast

ROOT=Path(__file__).resolve().parents[1]
STATUS="R8_ONE_ARCHIVED_TARGET_PRICE_ONLY_SMOOTH_HARD_RETROSPECTIVE"
MODEL_NAMES=(
    "WIN_latest_persistence",
    "WIN_full_log_momentum_beta1",
    "WIN_continuous_momentum_gain_r_over_rplus010",
    "WIN_hard_gate_momentum_r_ge_010_per_hour",
    "uninformed_PR19_fixed_ABM",
    "uninformed_PR19_smooth_ABM",
    "uninformed_PR19_hard_ABM",
)
VOTER_MODELS={
    "uninformed_PR19_fixed_ABM":"fixed",
    "uninformed_PR19_smooth_ABM":"smooth",
    "uninformed_PR19_hard_ABM":"hard",
}
SEEDS=30
FIXED_SEED=20261031
POLICY_SCALE=RATE_SCALE_LOG_PER_HOUR
HORIZON_MIN=NEXT_HORIZON_MINUTES


def _positive_simplex(x):
    y=np.asarray(x,dtype=float)
    if (y.ndim!=1 or len(y)<5 or
            not np.all(np.isfinite(y)) or np.any(y<=0)):
        raise ValueError("HOLD_R8_NOT_COMPLETE_POSITIVE_MARKET_VECTOR")
    return y/y.sum()


def _tilt(q,log_change,multiplier):
    q=_positive_simplex(q)
    log_change=np.asarray(log_change,dtype=float)
    if (log_change.shape!=q.shape or not math.isfinite(multiplier)
            or multiplier<0 or multiplier>2 or
            not np.all(np.isfinite(log_change))):
        raise ValueError("HOLD_R8_INVALID_PRICE_MOMENTUM_SHAPE")
    logw=np.log(q)+multiplier*log_change
    z=np.exp(logw-np.max(logw))
    return _positive_simplex(z)


def _seal(payload):
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,
                   separators=(",",":"),allow_nan=False).encode("utf-8")
    return sha256(raw).hexdigest()


def _indexed_rows(v,ids):
    p=_positive_simplex(v)
    if len(p)!=len(ids):
        raise ValueError("HOLD_R8_UNKNOWN_HORSE_ROSTER")
    return [{"n":int(i),"p":float(x)} for i,x in zip(ids,p)]


def freeze_1326_only(root=ROOT,*,n_seeds=SEEDS,seed=FIXED_SEED):
    """PR21 source_only_features reads only 12:21+13:26 and its WIDE grid.

    No 13:44 target file, postrace podium or live final market can be
    accessed by this function. The WIDE feature is verified but NOT
    USED in the price-only forecast arms.
    """
    if (type(n_seeds) is not int or not 2<=n_seeds<=100 or
            type(seed) is not int or seed<0):
        raise ValueError("HOLD_R8_INVALID_PREDECLARED_ARTIFICIAL_SEEDS")
    f=source_only_features(root)
    ids=sorted(f["last_market_q"])
    if (f["race_id"]!=SOURCE_RACE or len(ids)!=11 or
            set(f["earlier_market_q"])!=set(ids)):
        raise ValueError("HOLD_R8_REWRITTEN_SOURCE_RUNNERS")
    q0=_positive_simplex([f["earlier_market_q"][i] for i in ids])
    q1=_positive_simplex([f["last_market_q"][i] for i in ids])
    t0=aware(f["feature_first_published"])
    t1=aware(f["feature_latest_published"])
    mid_rx=aware(f["feature_later_market_received"])
    t2=t1+timedelta(minutes=HORIZON_MIN)
    post=aware(f["race_scheduled_post"])
    if not (t0<t1<=mid_rx<t2<post):
        raise ValueError("HOLD_R8_CANNOT_FORM_PRETARGET_PRICE_CANDIDATES")
    hours=(t1-t0).total_seconds()/3600.
    if hours<=0:
        raise ValueError("HOLD_R8_PRICE_SOURCE_TIME_NOT_POSITIVE")
    # Original PR19 pace normalization and threshold unit: per hour.
    rate=float(np.max(np.abs(np.log(q1/q0)))/hours)
    momentum=np.log(q1/q0)*(HORIZON_MIN/60.)/hours
    gain_smooth=rate/(rate+POLICY_SCALE)
    gain_hard=1.0 if rate>=POLICY_SCALE else 0.0
    named={
        MODEL_NAMES[0]:q1,
        MODEL_NAMES[1]:_tilt(q1,momentum,1.0),
        MODEL_NAMES[2]:_tilt(q1,momentum,gain_smooth),
        MODEL_NAMES[3]:_tilt(q1,momentum,gain_hard),
    }
    all_seed_paths={label:[] for label in VOTER_MODELS}
    noinfo_gates={label:[] for label in VOTER_MODELS}
    # Replay the exact PR19 social policies with zero new horse signal.
    for k in range(n_seeds):
        s=seed+1009*k
        for label,policy in VOTER_MODELS.items():
            path=voter_path(
                q1,q1,policy=policy,arrival=5,seed=s,
                duration_hours=HORIZON_MIN/60.)
            if path["information_available_round_count"]!=0:
                raise ValueError("HOLD_UNOBSERVED_HORSE_SIGNAL_IN_NULL_MARKET")
            all_seed_paths[label].append(_indexed_rows(path["final"],ids))
            noinfo_gates[label].append(
                int(path["hard_gate_active_round_count"]))
    rows={name:_indexed_rows(v,ids) for name,v in named.items()}
    if set(rows)|set(all_seed_paths)!=set(MODEL_NAMES):
        raise ValueError("HOLD_R8_CANDIDATE_MODEL_UNIVERSE_CHANGED")
    manifest={
        "status":STATUS,
        "research_unit":SOURCE_RACE,
        "one_original_source_race":True,
        "training_or_parameter_fit_to_later_quote":False,
        "feature_source_first_published":t0.isoformat(),
        "feature_source_second_published":t1.isoformat(),
        "feature_source_second_received":mid_rx.isoformat(),
        "target_original_source_expected":t2.isoformat(),
        "target_original_source_scheduled_post":post.isoformat(),
        "source_only_shalocked_original_WIDE_median_not_as_feature":True,
        "forecast_indices_only_initial_and_middle_WIN":{
            "horse_numbers":ids,
            "source_early_M0_index":_indexed_rows(q0,ids),
            "source_middle_M0_index":_indexed_rows(q1,ids),
        },
        "predeclared_method_constants":{
            "horizon_minutes":HORIZON_MIN,
            "rate_threshold_log_index_per_hour":POLICY_SCALE,
            "forecast_full_momentum_multiplier":1.0,
            "continuous_gain_formula":"r/(r+0.10)",
            "hard_gain_formula":"1 if r>=0.10 else 0",
            "uninformed_voter_duration_hours":HORIZON_MIN/60.,
            "synthetic_prior_stakes_from_original_PR19":3000,
            "synthetic_votes_per_round_from_original_PR19":250,
            "synthetic_rounds_from_original_PR19":4,
            "synthetic_voter_seed_start":seed,
            "synthetic_voter_seeds_per_policy":n_seeds,
        },
        "observed_source_first_to_second_max_rate_log_index_per_hour":rate,
        "imposed_continuous_price_projection_gain":gain_smooth,
        "imposed_hard_price_projection_gain":gain_hard,
        "fixed_market_only_candidates":rows,
        "no_information_original_PR19_vote_paths_by_seed":all_seed_paths,
        "no_information_original_PR19_hard_gate_events_by_seed":noinfo_gates,
        "no_independent_horse_signal_or_real_voter_flow":True,
        "no_target_quote_or_horse_finish_result_consulted_before_freeze":True,
        "retrospective_original_target_already_in_past_at_GitHub_PR_creation":True,
        "no_genuine_pretarget_SHA_commit_or_external_source_receipt":True,
    }
    result={
        "freeze_payload":manifest,
        "local_replay_SHA256_not_pretarget":_seal(manifest),
        "external_SHA_pre_target_attested":False,
    }
    verify_freeze(result)
    return result


def verify_freeze(frozen):
    if (not isinstance(frozen,dict) or set(frozen)!={
            "freeze_payload","local_replay_SHA256_not_pretarget",
            "external_SHA_pre_target_attested"} or
            frozen["external_SHA_pre_target_attested"] is not False):
        raise ValueError("HOLD_R8_INVALID_RETROSPECTIVE_FROZEN_SCHEMA")
    p=frozen["freeze_payload"]
    if (p.get("status")!=STATUS or p.get("research_unit")!=SOURCE_RACE or
            frozen["local_replay_SHA256_not_pretarget"]!=_seal(p)):
        raise ValueError("HOLD_R8_RETROSPECTIVE_MODEL_SHA_TAMPERED")
    c=p.get("fixed_market_only_candidates")
    s=p.get("no_information_original_PR19_vote_paths_by_seed")
    if (not isinstance(c,dict) or not isinstance(s,dict) or
            set(c)!=set(MODEL_NAMES[:4]) or
            set(s)!=set(VOTER_MODELS)):
        raise ValueError("HOLD_R8_FROZEN_CANDIDATE_NAMES_CHANGED")
    ids=p["forecast_indices_only_initial_and_middle_WIN"]["horse_numbers"]
    n=p["predeclared_method_constants"]["synthetic_voter_seeds_per_policy"]
    for rows in list(c.values())+[
            path for lst in s.values() for path in lst]:
        if ([v["n"] for v in rows]!=ids or
                any(type(v["p"]) not in (float,int) or
                    not math.isfinite(v["p"]) or v["p"]<=0 for v in rows)
                or not math.isclose(sum(v["p"] for v in rows),1,
                                     abs_tol=1e-10)):
            raise ValueError("HOLD_R8_FROZEN_CANDIDATE_INVALID_SIMPLEX")
    if (set(p["no_information_original_PR19_hard_gate_events_by_seed"])
            !=set(s) or any(len(lst)!=n for lst in s.values())
            or any(len(lst)!=n for lst in
                   p["no_information_original_PR19_hard_gate_events_by_seed"].values())):
        raise ValueError("HOLD_R8_SYNTHETIC_REPLICA_MULTIPLIED")
    return p


def _TV(x,y):
    return float(50*np.sum(np.abs(_positive_simplex(x)-_positive_simplex(y))))


def _KL(p,q):
    p=_positive_simplex(p)
    q=_positive_simplex(q)
    return float(np.sum(p*np.log(p/q)))


def score_original_later_quote(root=ROOT,*,frozen=None,n_seeds=SEEDS,
                               seed=FIXED_SEED):
    """Only AFTER all candidate vectors exist read genuine archival 13:44."""
    frozen=frozen if frozen is not None else freeze_1326_only(
        root,n_seeds=n_seeds,seed=seed)
    payload=verify_freeze(frozen)
    ids=payload["forecast_indices_only_initial_and_middle_WIN"]["horse_numbers"]
    prepared={
        "mid_received":aware(payload["feature_source_second_received"]),
        "nominal_next_market_publication":
            aware(payload["target_original_source_expected"]),
        "official_post":aware(payload["target_original_source_scheduled_post"]),
        "ids":ids,
    }
    # This helper independently enforces original source blob SHA, same
    # provider, all 11 horses, intended 13:44 clock, and prestart receipt.
    late=validate_later_quote(root,prepared=prepared)
    target=_positive_simplex([1/late[i] for i in ids])
    base=np.asarray([
        x["p"] for x in payload["fixed_market_only_candidates"][
            MODEL_NAMES[0]]],dtype=float)
    base_error=_TV(base,target)
    scores={}
    for name,rows in payload["fixed_market_only_candidates"].items():
        v=np.asarray([x["p"] for x in rows],dtype=float)
        scores[name]={
            "one_real_target_index_TV_pp":_TV(v,target),
            "one_real_target_index_KL_nats":_KL(target,v),
            "delta_TV_vs_same_one_persistence_target_pp":
                _TV(v,target)-base_error,
            "one_forecast_not_repeated_market_draw":True,
        }
    for name,seed_rows in payload["no_information_original_PR19_vote_paths_by_seed"].items():
        errors=[_TV([x["p"] for x in rows],target) for rows in seed_rows]
        kls=[_KL(target,[x["p"] for x in rows]) for rows in seed_rows]
        gates=payload["no_information_original_PR19_hard_gate_events_by_seed"][name]
        scores[name]={
            "mean_one_target_TV_over_only_synthetic_seeds_pp":mean(errors),
            "min_one_target_TV_over_only_synthetic_seeds_pp":min(errors),
            "max_one_target_TV_over_only_synthetic_seeds_pp":max(errors),
            "mean_one_target_KL_over_only_synthetic_seeds_nats":mean(kls),
            "mean_delta_TV_vs_same_one_persistence_target_pp":
                mean(errors)-base_error,
            "mean_hard_gate_rounds_with_no_new_information":mean(gates),
            "null_paths_with_any_hard_gate":sum(x>0 for x in gates),
            "artificial_seeds_are_not_new_independent_market_targets":True,
        }
    if set(scores)!=set(MODEL_NAMES):
        raise ValueError("HOLD_R8_AFTER_TARGET_SCORE_UNDECLARED_MODEL")
    # Real original source gives the actual R8 13:26 -> 13:44
    # price-rank crossing. No market threshold mechanism is inferred.
    quote_mid={
        ids[j]:1/p for j,p in enumerate(
            [row["p"] for row in payload[
                "forecast_indices_only_initial_and_middle_WIN"][
                    "source_middle_M0_index"]])
    }
    geometry=rank_contrast(quote_mid,late)
    return {
        "status":STATUS,
        "source_race":SOURCE_RACE,
        "original_source_target_published":
            payload["target_original_source_expected"],
        "original_source_target_horse_count":len(ids),
        "independent_real_target_market_intervals":1,
        "independent_real_target_horse_races":1,
        "new_prospective_verified_target_intervals":0,
        "old_2026_Oct12_target_was_known_long_before_current_GitHub_code":True,
        "calibration_training_on_target":False,
        "local_model_replay_SHA_not_pretarget":
            frozen["local_replay_SHA256_not_pretarget"],
        "target_value_sha_or_contents_not_read_before_candidate_creation":True,
        "target_price_rank_geometry":{
            "actually_reversed_pairs":geometry["strictly_reversed_pair_count"],
            "actual_relative_index_TV_pp":
                geometry["normalized_inverse_quote_TV_percentage_points"],
            "posthoc_possible_pairs_not_actual_reversals":
                geometry[
                    "pair_earlier_tie_boundary_within_posthoc_worst_case_shock_count"],
        },
        "actual_JRA_race_result_or_bettor_stakes_read":False,
        "real_horse_GPS_or_independent_horse_ability_used":False,
        "model_selection_or_criticality_from_one_target":"HOLD",
        "by_predeclared_price_model":scores,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretarget-only",action="store_true")
    parser.add_argument("--seeds",type=int,default=SEEDS)
    parser.add_argument("--output",type=Path,default=Path(
        "tmp/r8-price-geometry-smooth-hard-retro.json"))
    args=parser.parse_args()
    frozen=freeze_1326_only(n_seeds=args.seeds)
    score=(score_original_later_quote(frozen=frozen)
           if not args.pretarget_only else None)
    report={"freeze":frozen,"retrospective_score":score}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,
                                      indent=2,allow_nan=False)+"\n",
                           encoding="utf-8")
    print("SOURCE_ONLY_MODEL_LOCAL_SHA_NOT_REAL_PRETARGET",
          frozen["local_replay_SHA256_not_pretarget"])
    if score is not None:
        for label,d in score["by_predeclared_price_model"].items():
            v=d.get("one_real_target_index_TV_pp",
                    d.get("mean_one_target_TV_over_only_synthetic_seeds_pp"))
            print("R8_ONE_RETRO_NEXT_MARKET_TARGET",label,v)
        print("PRICE_MODEL_CAN_NOT_IDENTIFY_SOCIAL_TIPPING",True)
    else:
        print("TARGET_FILE_NEVER_OPENED",True)


if __name__=="__main__":
    main()
