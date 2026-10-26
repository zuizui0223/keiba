#!/usr/bin/env python3
"""Two-phase PRIVATE multi-race full-WIN/WIDE next-market shadow protocol.

FREEZE inputs: exactly first WIN, middle WIN, same-source-minute complete
middle WIDE, optional rights-reviewed pre-early WIN past-horse records.
Not a bookmaker API, JRA downloader, stock trading tool or race outcome
forecast. No next WIN target, winner, returns, or bettor count can enter.

FREEZE generates market-only persistence/momentum/WIDE-node and integrates
PR17 nonlocal horse-first-passage ABM -> PR19 continuous informed voter ABM
with WIDE residual delivered ONCE as part of horse signal (plus cyclic
wrong-horse control). ALL candidate vectors are protected by canonical
SHA256 before the next quote file is ever opened.

SCORE reads a different target series and chooses the FIRST eligible
complete WIN price snapshot under a locked predeclared horizon/window.
Target series completeness and all local times are SELF-DECLARED, not
independent historical proof. A Draft GitHub PR cannot activate the
existing SHA-only GitHub workflow (not installed on main). Neither local
SHA nor local score is a certified prospective experiment.

COHORT groups race-level local shadow scores and gives race/date-equal
paired comparisons. Regardless of the sample count, no participant-level
stake flow, true win probability, information arrival or betting edge is
inferred. Only authentic external clock receipts + new future race dates
can justify stronger claims.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
from statistics import mean

import numpy as np

from odds_shadow_freeze_score import (
    _normalized_odds,_wide_prices,_aware,_seal,_canonical,
)
from odds_cross_pool_global_async import relative_pair_indices
from odds_pair_hierarchy_decomposition import complete_graph_decompose
from keiba_nonlocal_horse_pde_bettor_bridge import finish_pair
from keiba_endogenous_threshold_null_bridge import voter_path
from keiba_independent_horse_asof_preflight import verify_offline_source

FEATURE_SCHEMA="KEIBA_PRIVATE_TWO_WIN_ONE_FULL_WIDE_FEATURE_V1"
TARGET_SCHEMA="KEIBA_PRIVATE_LATER_WIN_RECEIPT_STREAM_V1"
FREEZE_SCHEMA="KEIBA_LOCAL_NEXT_WIN_MARKET_SHADOW_FREEZE_V1"
SCORE_SCHEMA="KEIBA_LOCAL_NEXT_WIN_MARKET_SCORE_V1"
ROOT=Path(__file__).resolve().parents[1]
FREEZE_STATUS="LOCAL_SHA_ONLY_NOT_INDEPENDENT_GITHUB_PRESEAL"
SCORE_STATUS="LOCAL_SOURCE_SCOPED_NEXT_MARKET_SCORE_NOT_PROSPECTIVE_VERIFIED"
COHORT_STATUS="LOCAL_NEXT_MARKET_COHORT_NOT_PROSPECTIVE_AUTHENTICATED"
BETTOR_POLICY="smooth"
HORSE_CROWD_COEFFICIENT=2.0
WIDE_HORSE_BETA=0.25
N_VOTER_ROUNDS=4
SOURCE_FIELDS={
    "schema","provenance","operator_confirmed_research_rights",
    "race_id","scheduled_post_jst","race_distance_m","provider",
    "model_coefficient_lock_at_jst","local_forecast_created_at_jst",
    "horizon_minutes","target_window_minutes","first_win","middle_win",
    "middle_wide",
}
PANEL_WIN_FIELDS={
    "market","provider","source_clock_verified","source_updated_at_jst",
    "received_at_jst","odds_by_horse_number",
}
PANEL_WIDE_FIELDS={
    "market","provider","source_clock_verified","source_updated_at_jst",
    "received_at_jst","pairs",
}
MODEL_BENCHMARKS=(
    "mid_WIN_persistence",
    "mid_WIN_momentum",
    "mid_WIN_momentum_plus_WIDE_node_beta025",
)
HORSE_PRIOR_NAMES=("market_qmid","authorized_past_form")
ARRIVALS=(1,3,5)
SIGNAL_VARIANTS=("horse_signal","horse_signal_plus_WIDE",
                 "horse_signal_plus_rotated_WIDE_placebo")


def _validate_panel(panel,fields,provider,event):
    if not isinstance(panel,dict) or set(panel)!=fields:
        raise ValueError("HOLD_UNEXPECTED_MARKET_PANEL_FIELDS")
    if (panel["market"]!=event or panel["provider"]!=provider or
            panel["source_clock_verified"] is not True):
        raise ValueError("HOLD_INCONSISTENT_MARKET_PROVIDER_OR_EVENT")
    pub=_aware(panel["source_updated_at_jst"])
    rx=_aware(panel["received_at_jst"])
    if pub>rx:
        raise ValueError("HOLD_MARKET_QUOTE_RECEIVED_BEFORE_PUBLICATION")
    return pub,rx


def _normalize(q):
    p=np.asarray(q,dtype=float)
    if (p.ndim!=1 or p.size<5 or not np.all(np.isfinite(p)) or
            np.any(p<=0)):
        raise ValueError("HOLD_NONPOSITIVE_FULL_FIELD_MARKET")
    return p/p.sum()


def _market_prices(panel):
    return _normalized_odds(panel["odds_by_horse_number"])


def _sorted_price_proxy(odds,ids):
    return _normalize([1/odds[i] for i in ids])


def _rank_score(p,ids):
    if len(p)!=len(ids) or not np.isclose(np.sum(p),1.,atol=1e-10):
        raise ValueError("HOLD_RANK_PREDICTION_NONNORMALIZED")
    return [{"n":int(i),"p":float(x)} for i,x in zip(ids,p)]


def _freeze_source(doc,*, source_bytes, history_bytes=None,history_receipt=None,
                   horse_draws=120,horse_seed=20261025):
    if not isinstance(doc,dict) or set(doc)!=SOURCE_FIELDS:
        raise ValueError("HOLD_FEATURE_SCHEMA_UNKNOWN_OR_EXTRA_FUTURE_FIELDS")
    if doc["schema"]!=FEATURE_SCHEMA or doc["provenance"] not in (
        "synthetic_test","authorized_private_local_export",
        "historical_replay_unattested"):
        raise ValueError("HOLD_FEATURE_PROVENANCE_OR_SCHEMA")
    if (doc["provenance"]=="authorized_private_local_export" and
            doc["operator_confirmed_research_rights"] is not True):
        raise ValueError("HOLD_MARKET_EXPORT_RIGHTS_NOT_REVIEWED")
    if doc["provenance"]!="authorized_private_local_export" and (
            doc["operator_confirmed_research_rights"] is not False):
        raise ValueError("HOLD_DEMO_PROVENANCE_MUST_NOT_IMPLY_REAL_RIGHTS")
    if (type(horse_draws) is not int or horse_draws<40 or
            type(horse_seed) is not int or horse_seed<0):
        raise ValueError("HOLD_UNDECLARED_HORSE_MONTE_CARLO_SETTINGS")
    race=doc["race_id"]
    provider=doc["provider"]
    if (not isinstance(race,str) or not race or len(race)>95 or
            not isinstance(provider,str) or not provider or
            type(doc["race_distance_m"]) is not int or
            not 800<=doc["race_distance_m"]<=5000):
        raise ValueError("HOLD_BAD_RACE_ID_PROVIDER_OR_DISTANCE")
    first,middle,wide=(doc[k] for k in ("first_win","middle_win",
                                       "middle_wide"))
    t0,r0=_validate_panel(first,PANEL_WIN_FIELDS,provider,"win")
    t1,r1=_validate_panel(middle,PANEL_WIN_FIELDS,provider,"win")
    tw,rw=_validate_panel(wide,PANEL_WIDE_FIELDS,provider,"wide")
    post=_aware(doc["scheduled_post_jst"])
    lock=_aware(doc["model_coefficient_lock_at_jst"])
    freeze_at=_aware(doc["local_forecast_created_at_jst"])
    horizon=doc["horizon_minutes"]
    width=doc["target_window_minutes"]
    if (type(horizon) is not int or not 5<=horizon<=90 or
            type(width) is not int or not 0<=width<=15):
        raise ValueError("HOLD_UNSUPPORTED_NEXT_MARKET_HORIZON")
    target_first=t1+timedelta(minutes=horizon)
    target_last=target_first+timedelta(minutes=width)
    if not (lock<=t0<=r0<t1 and t1.replace(second=0,microsecond=0)==tw.replace(second=0,microsecond=0) and tw<=r1 and tw<=rw and max(r1,rw)<=freeze_at<target_first
            and target_last<post-timedelta(minutes=10)):
        raise ValueError("HOLD_MARKET_SOURCE_CLOCK_LEAKAGE_OR_LATE_FREEZE")
    original=_market_prices(first)
    newer=_market_prices(middle)
    if set(original)!=set(newer):
        raise ValueError("HOLD_CHANGED_HORSE_ROSTER_DURING_PRESTART")
    ids=sorted(original)
    if len(ids)>30:
        raise ValueError("HOLD_TOO_MANY_HORSES")
    complete_pairs=_wide_prices(wide["pairs"],set(ids))
    if len(complete_pairs)!=len(ids)*(len(ids)-1)//2:
        raise ValueError("HOLD_NOT_COMPLETE_MIDDLE_WIDE_MARKET")
    # These are payout quote indices, never true win probabilities or
    # winner labels. All 55/136/... WIDE events overlap within a race.
    graph=complete_graph_decompose(relative_pair_indices({
        "label":"mid_WIDE_received_before_local_freeze",
        "win":newer,"wide":complete_pairs,
    })["pair_residual"])
    if graph["status"] not in (
        "COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION",
        "HOLD_NO_EDGE_LEVEL_VARIANCE_TO_DECOMPOSE",
    ):
        raise ValueError("HOLD_WIDE_NODE_DECOMPOSITION")
    q0=_sorted_price_proxy(original,ids)
    qmid=_sorted_price_proxy(newer,ids)
    node=np.asarray([graph["node_effects"][i] for i in ids])
    if not np.all(np.isfinite(node)):
        raise ValueError("HOLD_NONFINITE_CROSSPOOL_HORSE_NODES")
    previous=(t1-t0).total_seconds()/60
    log_move=np.log(qmid/q0)
    moment=_normalize(qmid*np.exp((horizon/previous)*log_move))
    tilted=_normalize(moment*np.exp(WIDE_HORSE_BETA*(node-node.max())))
    candidates={
        "mid_WIN_persistence":qmid,
        "mid_WIN_momentum":moment,
        "mid_WIN_momentum_plus_WIDE_node_beta025":tilted,
    }
    if (history_bytes is None)!=(history_receipt is None):
        raise ValueError("HOLD_INCOMPLETE_OPTIONAL_HORSE_HISTORY_SOURCE")
    physical_priors={"market_qmid":qmid}
    hsha=None
    if history_bytes is not None:
        # Validate source *before first quote*, source-rights declaration
        # and complete matching official horse-name/number mapping.
        # This is STILL only local clocks; never externally attested.
        row={
            "race_id":race,"meeting_day":post.date().isoformat(),
            "first_odds":original,"last_odds":newer,
            "initial_quote_at":t0.isoformat(),
            "latest_quote_at":t1.isoformat(),
            "initial_quote_received_at_jst":r0.isoformat(),
            "latest_quote_received_at_jst":r1.isoformat(),
            "local_forecast_generated_at_jst":freeze_at.isoformat(),
            "post_at":post.isoformat(),
        }
        verified=verify_offline_source(history_bytes,history_receipt,row)
        hsha=verified["source_sha256"]
        physical_priors["authorized_past_form"]=_normalize(
            verified["horse_history_prior"])
    duration=horizon/60.
    for arm,prior in physical_priors.items():
        result=finish_pair(prior,distance_m=doc["race_distance_m"],
                           draws=horse_draws,seed=horse_seed,
                           crowd_coefficient=HORSE_CROWD_COEFFICIENT)
        signal=_normalize(result["scenarios"]["nonlocal_crowd"]["win"])
        for release in ARRIVALS:
            for variant in SIGNAL_VARIANTS:
                if variant=="horse_signal":
                    used=signal
                else:
                    residual=(node if variant=="horse_signal_plus_WIDE"
                              else np.roll(node,1))
                    used=_normalize(signal*np.exp(
                        WIDE_HORSE_BETA*(residual-residual.max())))
                voted=voter_path(qmid,used,policy=BETTOR_POLICY,
                                 duration_hours=duration,arrival=release,
                                 seed=horse_seed+390)["final"]
                name=f"coupled_{arm}_{variant}_round{release}"
                candidates[name]=_normalize(voted)
        # If signal is not delivered within the horizon, WIDE identity
        # and horse signal are *forbidden* from changing synthetic votes.
        noinfo=[
            candidates[f"coupled_{arm}_{var}_round5"]
            for var in SIGNAL_VARIANTS
        ]
        if any(not np.array_equal(noinfo[0],x) for x in noinfo[1:]):
            raise ValueError("HOLD_FUTURE_INFORMATION_REACHED_PAST_VOTERS")
    expected=3+9*len(physical_priors)
    if set(MODEL_BENCHMARKS)-set(candidates) or len(candidates)!=expected:
        raise ValueError("HOLD_PREDECLARED_FULL_MODEL_UNIVERSE_CHANGED")
    model_scores={
        name:_rank_score(pred,ids)
        for name,pred in sorted(candidates.items())
    }
    payload={
        "schema":FREEZE_SCHEMA,"status":FREEZE_STATUS,
        "race_id":race,"scheduled_post_jst":post.isoformat(),
        "source_provenance":doc["provenance"],
        "provider":provider,"horse_numbers":ids,
        "model_code_scope":"PR21_PHYSICAL_NONLOCAL_AND_SMOOTH_VOTER_LOCAL_NEXT_MARKET",
        "source_sha256_local_only":sha256(source_bytes).hexdigest(),
        "optional_horse_history_sha256_local_only":hsha,
        "first_WIN_quote_published_at":t0.isoformat(),
        "first_WIN_quote_received_at":r0.isoformat(),
        "middle_WIN_quote_published_at":t1.isoformat(),
        "middle_WIN_quote_received_at":r1.isoformat(),
        "middle_WIDE_quote_published_at":tw.isoformat(),
        "middle_WIDE_quote_received_at":rw.isoformat(),
        "model_coefficient_lock_at":lock.isoformat(),
        "local_freeze_created_at":freeze_at.isoformat(),
        "next_quote_min_published_at":target_first.isoformat(),
        "next_quote_max_published_at":target_last.isoformat(),
        "next_quote_selection_rule":"FIRST_COMPLETE_WIN_SNAPSHOT_IN_DECLARED_WINDOW",
        "target_horizon_minutes":horizon,"target_window_minutes":width,
        "horse_draws":horse_draws,"horse_seed":horse_seed,
        "social_rule":BETTOR_POLICY,
        "crowd_coefficient_hypothetical_m2ps":HORSE_CROWD_COEFFICIENT,
        "wide_node_beta_fixed":WIDE_HORSE_BETA,
        "primary_predeclared_metric":"next_win_relative_quote_index_TV_pp",
        "secondary_predeclared_metric":"next_quote_index_KL_nats",
        "candidate_predictions":model_scores,
        "raw_WIN_WIDE_prices_not_exported_in_freeze":True,
        "has_only_local_self_declared_time_proof":True,
        "external_GitHub_server_preseal_verified":False,
        "not_a_true_win_probability_or_betting_return":True,
        "v31_and_Kikka_presealed_M0_M2_unchanged":True,
    }
    seal=_seal(payload)
    return {
        "seal_sha256_of_canonical_payload":seal,"payload":payload,
        "SHA_only_existing_dispatch_inputs_NOT_SENT":{
            "race_id":race,"seal_sha256":seal,
            "scheduled_post_jst":post.isoformat(),
            "last_source_received_jst":max(r0,r1,rw).isoformat(),
        },
        "external_prestart_proof_status":
            "HOLD_WORKFLOW_NOT_INSTALLED_ON_DEFAULT_BRANCH_AND_NOT_DISPATCHED",
    }


def freeze_source_bytes(feature_bytes,*,history_bytes=None,
                        history_receipt=None,horse_draws=120,
                        horse_seed=20261025):
    if not isinstance(feature_bytes,bytes):
        raise ValueError("HOLD_PRIVATE_SOURCE_BYTES_MISSING")
    features=json.loads(feature_bytes.decode("utf-8"))
    return _freeze_source(
        features,source_bytes=feature_bytes,
        history_bytes=history_bytes,history_receipt=history_receipt,
        horse_draws=horse_draws,horse_seed=horse_seed)


def verify_freeze(freeze):
    if (not isinstance(freeze,dict) or
            not isinstance(freeze.get("payload"),dict)):
        raise ValueError("HOLD_MISSING_LOCAL_SHA_FREEZE")
    payload=freeze["payload"]
    if (payload.get("schema")!=FREEZE_SCHEMA or
            payload.get("status")!=FREEZE_STATUS or
            _seal(payload)!=freeze.get("seal_sha256_of_canonical_payload")):
        raise ValueError("HOLD_PRETARGET_FORECAST_HASH_OR_SCHEMA_MISMATCH")
    models=payload["candidate_predictions"]
    ids=payload["horse_numbers"]
    expected=3+9*(1+int(payload[
        "optional_horse_history_sha256_local_only"] is not None))
    if (set(MODEL_BENCHMARKS)-set(models) or len(models)!=expected or
            not 5<=len(ids)<=30 or ids!=sorted(set(ids))):
        raise ValueError("HOLD_CHANGED_FROZEN_RACE_OR_PREDICTION_UNIVERSE")
    for rows in models.values():
        if ([x["n"] for x in rows]!=ids or
                not np.isclose(sum(x["p"] for x in rows),1,atol=1e-9)
                or any(type(x["p"]) not in (int,float) or
                       not math.isfinite(x["p"]) or x["p"]<=0 for x in rows)):
            raise ValueError("HOLD_CORRUPT_FROZEN_MARKET_PROBABILITY")
    return payload


def score_target(freeze,target):
    """Score the FIRST eligible quote from a SEPARATE received quote stream.

    Local capture completeness is not independently attested, and this
    function CANNOT promote its score to prospective evidence.
    """
    frozen=verify_freeze(freeze)
    if not isinstance(target,dict) or set(target)!={
        "schema","race_id","provider","snapshots",
        "operator_declares_complete_capture_stream"}:
        raise ValueError("HOLD_TARGET_SERIES_OR_EXTRA_SOURCE_FIELDS")
    if (target["schema"]!=TARGET_SCHEMA or
            target["race_id"]!=frozen["race_id"] or
            target["provider"]!=frozen["provider"] or
            target["operator_declares_complete_capture_stream"] is not True):
        raise ValueError("HOLD_TARGET_STREAM_RACE_PROVIDER_OR_COMPLETENESS")
    snaps=target["snapshots"]
    if not isinstance(snaps,list) or not 1<=len(snaps)<=300:
        raise ValueError("HOLD_TARGET_STREAM_UNAVAILABLE")
    boundary=_aware(frozen["local_freeze_created_at"])
    min_t=_aware(frozen["next_quote_min_published_at"])
    max_t=_aware(frozen["next_quote_max_published_at"])
    scheduled=_aware(frozen["scheduled_post_jst"])
    prev_pub=_aware(frozen["middle_WIN_quote_published_at"])
    prev_rx=_aware(frozen["middle_WIN_quote_received_at"])
    eligible=[]
    previous_receipt=boundary
    for snap in snaps:
        if not isinstance(snap,dict) or set(snap)!=PANEL_WIN_FIELDS:
            raise ValueError("HOLD_INVALID_FUTURE_WIN_PANEL_SOURCE")
        pub,rx=_validate_panel(snap,PANEL_WIN_FIELDS,
                               frozen["provider"],"win")
        if not (prev_pub<pub<=rx and rx>prev_rx and rx>=previous_receipt
                and rx<scheduled-timedelta(minutes=10)):
            raise ValueError("HOLD_TARGET_SNAPSHOT_CLOCK_TIME_TRAVEL")
        prices=_market_prices(snap)
        if set(prices)!=set(frozen["horse_numbers"]):
            raise ValueError("HOLD_TARGET_HORSE_FIELD_OR_SCRATCH_DRIFT")
        if min_t<=pub<=max_t:
            eligible.append((pub,rx,prices))
        prev_pub=pub
        previous_receipt=rx
    if not eligible:
        return {
            "schema":SCORE_SCHEMA,
            "status":"HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW",
            "race_id":frozen["race_id"],
            "source_series_snapshot_count":len(snaps),
            "external_preseal_authenticated":False,
            "not_a_prospective_scored_forecast":True,
        }
    pub,rx,prices=min(eligible,key=lambda v:(v[0],v[1]))
    ids=frozen["horse_numbers"]
    observed=_sorted_price_proxy(prices,ids)
    outcomes={}
    for name,rows in sorted(frozen["candidate_predictions"].items()):
        pred=np.asarray([x["p"] for x in rows],dtype=float)
        outcomes[name]={
            "next_price_index_TV_pp":float(
                50*np.abs(pred-observed).sum()),
            "next_price_index_KL_nats":float(
                np.sum(observed*np.log(observed/pred))),
        }
    return {
        "schema":SCORE_SCHEMA,"status":SCORE_STATUS,
        "race_id":frozen["race_id"],
        "scheduled_post_jst":frozen["scheduled_post_jst"],
        "sealed_prediction_sha256":
            freeze["seal_sha256_of_canonical_payload"],
        "selected_first_eligible_source_published_at":pub.isoformat(),
        "selected_source_received_at":rx.isoformat(),
        "source_series_snapshot_count":len(snaps),
        "n_horses":len(ids),
        "all_model_scores":outcomes,
        "replay_future_market_used_only_as_target":True,
        "external_preseal_authenticated":False,
        "capture_stream_independently_complete":False,
        "operator_declares_capture_complete_without_independent_proof":True,
        "not_a_prospective_scored_forecast":True,
        "never_used_official_race_finish_or_betting_payout":True,
    }


def score_cohort(reports):
    if not isinstance(reports,list) or not reports:
        raise ValueError("HOLD_NO_PRIVATE_SHADOW_SCORE_REPORTS")
    keys=set()
    valid=[]
    held=[]
    for row in reports:
        if row.get("schema")!=SCORE_SCHEMA:
            raise ValueError("HOLD_UNRECOGNIZED_NEXT_PRICE_SCORE_SCHEMA")
        if row.get("status")=="HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW":
            held.append(row["race_id"])
            continue
        if (row.get("status")!=SCORE_STATUS or
                row.get("external_preseal_authenticated") is not False or
                row.get("capture_stream_independently_complete") is not False):
            raise ValueError("HOLD_UNSUPPORTED_COHORT_CERTIFICATION_STATUS")
        key=(row["race_id"],
             row["selected_first_eligible_source_published_at"])
        if key in keys:
            raise ValueError("HOLD_DUPLICATE_ACTUAL_NEXT_MARKET_TARGET")
        keys.add(key)
        valid.append(row)
    days=sorted({row["scheduled_post_jst"][:10] for row in valid})
    all_models=sorted({name for r in valid for name in r["all_model_scores"]})
    per={}
    for model in all_models:
        data=[r for r in valid if model in r["all_model_scores"]]
        if not data:
            continue
        per[model]={
            "real_races_with_this_fixed_model":len(data),
            "distinct_meeting_dates":len({r["scheduled_post_jst"][:10]
                                         for r in data}),
            "mean_race_equal_TV_pp":mean(
                r["all_model_scores"][model]["next_price_index_TV_pp"]
                for r in data),
            "mean_race_equal_KL_nats":mean(
                r["all_model_scores"][model]["next_price_index_KL_nats"]
                for r in data),
        }
        paired=[r for r in data if
                "mid_WIN_persistence" in r["all_model_scores"]]
        per[model]["paired_delta_TV_vs_market_persistence_pp"]=(
            mean(r["all_model_scores"][model][
                "next_price_index_TV_pp"]-
                r["all_model_scores"]["mid_WIN_persistence"][
                    "next_price_index_TV_pp"] for r in paired)
            if paired else None)
        dates=sorted({r["scheduled_post_jst"][:10] for r in paired})
        per[model]["mean_meeting_date_equal_paired_delta_TV_pp"]=(
            mean(mean(r["all_model_scores"][model][
                "next_price_index_TV_pp"]-
                r["all_model_scores"]["mid_WIN_persistence"][
                    "next_price_index_TV_pp"] for r in paired
                    if r["scheduled_post_jst"].startswith(day))
                 for day in dates)
            if dates else None)
    return {
        "status":COHORT_STATUS,
        "submitted_private_score_files":len(reports),
        "scored_real_market_intervals":len(valid),
        "missing_eligible_target_holds":len(held),
        "distinct_meeting_dates":len(days),
        "minimum_development_sample_guard_60_races_8_dates_met":(
            len(valid)>=60 and len(days)>=8),
        "external_preseal_proofs_verified":0,
        "prospective_evaluation_certified":False,
        "real_HorseGPS_actual_bettor_flow_available":False,
        "one_market_interval_is_the_independent_unit_not_horses_or_WIDE_pairs":True,
        "by_prespecified_model":per,
        "future_market_predictive_advantage":"HOLD_UNATTESTED",
        "not_a_real_market_phase_transition_or_wagering_ROI":True,
    }


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,
                               allow_nan=False)+"\n",encoding="utf-8")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest="action",required=True)
    a=subs.add_parser("freeze")
    a.add_argument("--source",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--history-source",type=Path)
    a.add_argument("--history-receipt",type=Path)
    a.add_argument("--horse-draws",type=int,default=120)
    a.add_argument("--seed",type=int,default=20261025)
    b=subs.add_parser("score")
    b.add_argument("--freeze",type=Path,required=True)
    b.add_argument("--target-series",type=Path,required=True)
    b.add_argument("--output",type=Path,required=True)
    c=subs.add_parser("cohort")
    c.add_argument("--scores",type=Path,nargs="+",required=True)
    c.add_argument("--output",type=Path,required=True)
    z=p.parse_args()
    if z.action=="freeze":
        result=freeze_source_bytes(
            z.source.read_bytes(),
            history_bytes=(z.history_source.read_bytes()
                           if z.history_source else None),
            history_receipt=(_read_json(z.history_receipt)
                             if z.history_receipt else None),
            horse_draws=z.horse_draws,horse_seed=z.seed)
        summary={"local_only":True,"race_id":result["payload"]["race_id"],
                 "seal_sha256":result["seal_sha256_of_canonical_payload"],
                 "model_count":len(result["payload"]["candidate_predictions"]),
                 "external_receipt_verified":False}
    elif z.action=="score":
        result=score_target(_read_json(z.freeze),
                            _read_json(z.target_series))
        summary={"status":result["status"],
                 "race_id":result["race_id"],
                 "not_prospective_verified":True}
    else:
        result=score_cohort([_read_json(k) for k in z.scores])
        summary={"status":result["status"],
                 "races":result["scored_real_market_intervals"],
                 "dates":result["distinct_meeting_dates"],
                 "prospective_verified":False}
    _write_json(z.output,result)
    print(json.dumps(summary,ensure_ascii=False))


if __name__=="__main__":
    main()
