#!/usr/bin/env python3
"""Separate predeclared WIN-ONLY next-price lane on the same fixed race slots.

The full WIN(2 snapshots) + all WIDE(nC2) source-time lane remains the
PRIMARY PR22/PR28 hypothesis. JRA-VAN historical 0B41/0B42 series
does not contain WIDE; synchronous WIDE can only be an additionally
legally captured real-time all-bets quote. NEVER fabricate WIDE from
historical WIN or silently label it "complete".

This is a SEPARATE SUPPLEMENTARY LANE, specified 2026-10-28 BEFORE the
first proposed Oct31/Nov1 meetings. It uses two full-field WIN source
snapshots, the PR17 nonlocal horse ABM and PR19 smooth staged bettor ABM,
then tests the *next* full-field relative WIN quote index. It uses the
same predeclared +15..20 min target window as the full-WIDE lane.

WIN-only agent input here is qmid-derived synthetic ability; without
independent horse GPS/past-history receipts it is NOT an independent
horse-skill signal. The 0/2 m2ps horse crowding, Gumbel innovations and
voter mechanism are stipulated toy assumptions, NOT fitted JRA dynamics.

Every freeze SHAs its original source-chain HEAD, final official-card
claim, complete roster, physical distance, code-file SHA list and all
six market-index candidate forecast distributions. The source/cards are
LOCAL DECLARATIONS: this module NEVER POSTs a PR22 GitHub SHA comment
and does not claim actual pretarget remote attestation. A local SHA is
not an independently timestamped prediction.

Full-WIDE eligible, WIN-only eligible and neither-observed remain distinct
data-availability STATES on the ORIGINAL 26/64 slots; the exact same
physical race cannot become two independent market validation samples.
Official finishing order, payouts, real ballots and GPS are never read.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timedelta
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

from keiba_operator_winwide_capture import (
    ROOT,JST,_aware,_check_card,_read_ledger,_dump,_write_new_private
)
from keiba_fixed_denominator_market_campaign import (
    LOCKED_MARKET_HORIZON_MINUTES,LOCKED_MARKET_TARGET_WINDOW_MINUTES
)
from keiba_nonlocal_horse_pde_bettor_bridge import (
    finish_pair, pde_density_and_agent_check,
)
from keiba_endogenous_threshold_null_bridge import voter_path
from odds_shadow_freeze_score import _normalized_odds,_seal

SCHEMA="KEIBA_SEPARATE_WIN_ONLY_NEXT_MARKET_FREEZE_V1"
TARGET_SCHEMA="KEIBA_SEPARATE_WIN_ONLY_NEXT_MARKET_LOCAL_SCORE_V1"
STATUS="WIN_ONLY_SECONDARY_LOCAL_MODEL_SHA_NOT_PROSPECTIVE_VERIFIED"
SCORE_STATUS="WIN_ONLY_SECONDARY_NEXT_PRICE_LOCALLY_SCORED_NOT_AUTHENTICATED"
MISSING="HOLD_WIN_ONLY_TARGET_WINDOW_UNOBSERVED"
MODEL_NAMES=(
    "WIN_mid_persistence",
    "WIN_log_momentum",
    "WIN_horse_ABM_smooth_info_round1",
    "WIN_horse_ABM_smooth_info_round3",
    "WIN_horse_ABM_smooth_info_round5",
    "WIN_horse_ABM_shifted_signal_placebo_round1",
)
CODE_FILES=(
    "scripts/keiba_win_only_shadow_lane.py",
    "scripts/keiba_operator_winwide_capture.py",
    "scripts/keiba_nonlocal_horse_pde_bettor_bridge.py",
    "scripts/keiba_endogenous_threshold_null_bridge.py",
    "scripts/keiba_coupled_horse_market_pde.py",
    "scripts/odds_threshold_regime_bridge.py",
    "scripts/odds_shadow_freeze_score.py",
    "scripts/odds_coherent_hierarchy_rank_bridge.py",
)
HYPOTHETICAL_CROWD_C=2.0
HYPOTHETICAL_DRAW_SEED=20261028
DEFAULT_DRAWS=120
PDE_DIAGNOSTIC_PARTICLES=600
PDE_DIAGNOSTIC_DURATION_S=12.0


def _normalize(a):
    v=np.asarray(a,dtype=float)
    if (v.ndim!=1 or v.size<5 or not np.all(np.isfinite(v))
            or np.any(v<=0)):
        raise ValueError("HOLD_WIN_ONLY_NOT_A_POSITIVE_FULL_FIELD")
    return v/v.sum()


def _model_code_manifest(root=ROOT):
    """Actual on-disk code contents, never a self-reported commit label."""
    result={}
    for rel in CODE_FILES:
        p=Path(root)/rel
        raw=p.read_bytes()
        result[rel]=sha256(raw).hexdigest()
    return result


def _first_two_full_win(ledger,card,*,frozen_at):
    """Deterministic first two source-updated, locally acquired WIN vectors.

    Never skip an incomplete/mismatched full-field quote to select a
    favorable later observation. WIDE may be absent or present, but is
    NEVER read as a feature in this secondary research lane.
    """
    card=_check_card(card)
    e=_read_ledger(ledger)
    if not e:
        raise ValueError("HOLD_WIN_ONLY_NO_LOCALLY_CAPTURED_SOURCE_EVENTS")
    cutoff=_aware(frozen_at)
    if any(_aware(x["captured_at_jst"])>cutoff for x in e):
        raise ValueError("HOLD_WIN_ONLY_EVENT_OBSERVED_AFTER_CLAIMED_FREEZE")
    card_rx=_aware(card["source_card_received_at_jst"])
    all_win=[]
    for event in e:
        s=event["captured_source"]
        r=_aware(event["captured_at_jst"])
        if (s["race_id"]!=card["race_id"] or
                s["provider"]!=card["provider"] or
                s["provenance"]!=card["provenance"] or
                s["rights_reviewed_by_operator"]!=
                   card["rights_reviewed_by_operator"]):
            raise ValueError("HOLD_WIN_ONLY_CAPTURE_DIFFERENT_CARD_OR_SOURCE")
        if r<card_rx:
            continue
        if s["market"]=="win":
            prices=_normalized_odds(s["odds_by_horse_number"])
            if set(prices)!=set(card["horse_numbers"]):
                raise ValueError("HOLD_WIN_ONLY_INCOMPLETE_OR_SCRATCHED_HORSE_FIELD")
            all_win.append((event,prices))
    if len(all_win)<2:
        raise ValueError("HOLD_WIN_ONLY_NEEDS_TWO_FULL_WIN_SOURCE_UPDATES")
    ordered=sorted(all_win,key=lambda z:(
        _aware(z[0]["captured_source"]["source_updated_at_jst"]),
        _aware(z[0]["captured_at_jst"])))
    first,quotes_first=ordered[0]
    first_t=_aware(first["captured_source"]["source_updated_at_jst"])
    usable=[v for v in ordered[1:]
            if _aware(v[0]["captured_source"]["source_updated_at_jst"])>first_t]
    if not usable:
        raise ValueError("HOLD_WIN_ONLY_NO_LATER_DISTINCT_WIN_UPDATE")
    second,quotes_second=usable[0]
    second_t=_aware(second["captured_source"]["source_updated_at_jst"])
    rx1=_aware(first["captured_at_jst"])
    rx2=_aware(second["captured_at_jst"])
    post=_aware(card["scheduled_post_jst"])
    start=second_t+timedelta(minutes=LOCKED_MARKET_HORIZON_MINUTES)
    end=start+timedelta(minutes=LOCKED_MARKET_TARGET_WINDOW_MINUTES)
    if not (card_rx<=first_t<=rx1<second_t<=rx2<=cutoff<start<end<
            post-timedelta(minutes=10)):
        raise ValueError("HOLD_WIN_ONLY_MISSED_PRETARGET_FREEZE_OR_BAD_CLOCK")
    return {
        "card":card,"all_events":e,
        "first":first,"second":second,
        "prices_first":quotes_first,"prices_second":quotes_second,
        "first_t":first_t,"second_t":second_t,
        "rx1":rx1,"rx2":rx2,
        "freeze_at":cutoff,"post":post,
        "target_start":start,"target_end":end,
    }


def prepare_win_only(ledger,card,*,frozen_at_jst=None,
                     horse_draws=DEFAULT_DRAWS,
                     seed=HYPOTHETICAL_DRAW_SEED):
    if (type(horse_draws) is not int or horse_draws<40
            or type(seed) is not int or seed<0):
        raise ValueError("HOLD_WIN_ONLY_INVALID_PREDECLARED_MONTE_CARLO")
    time=frozen_at_jst or datetime.now(JST).isoformat()
    state=_first_two_full_win(ledger,card,frozen_at=time)
    c=state["card"]
    ids=c["horse_numbers"]
    prices0=state["prices_first"]
    prices1=state["prices_second"]
    q0=_normalize([1/prices0[i] for i in ids])
    qmid=_normalize([1/prices1[i] for i in ids])
    elapsed=(state["second_t"]-state["first_t"]).total_seconds()/60
    if elapsed<=0:
        raise ValueError("HOLD_WIN_ONLY_NO_POSITIVE_SOURCE_TIME_LAG")
    projected=_normalize(qmid*np.exp(
        (LOCKED_MARKET_HORIZON_MINUTES/elapsed)*np.log(qmid/q0)))
    physics=finish_pair(qmid,distance_m=c["race_distance_m"],
                        draws=horse_draws,seed=seed,
                        crowd_coefficient=HYPOTHETICAL_CROWD_C)
    signal=_normalize(physics["scenarios"]["nonlocal_crowd"]["win"])
    # Apply the exact same K, c and D physical law to the other half
    # of the PR17 model: the 12-s fixed-drift *factorized marginal PDE*
    # diagnostic. It is NOT a fitted JRA trajectory or a rank forecast;
    # include its mass/CDF closure warning in the same pretarget SHA.
    pde=pde_density_and_agent_check(
        qmid,strength=HYPOTHETICAL_CROWD_C,
        particles=PDE_DIAGNOSTIC_PARTICLES,
        duration_s=PDE_DIAGNOSTIC_DURATION_S,
        seed=seed+177)
    if (not pde["nonnegative_density"] or
            abs(pde["min_horse_probability_mass"]-1.)>1e-8 or
            abs(pde["max_horse_probability_mass"]-1.)>1e-8):
        raise ValueError("HOLD_WIN_ONLY_LINKED_HORSE_PDE_MASS_CONSERVATION")
    horizon_hours=LOCKED_MARKET_HORIZON_MINUTES/60
    candidates={
        MODEL_NAMES[0]:qmid,
        MODEL_NAMES[1]:projected,
    }
    for release in (1,3,5):
        quote=voter_path(qmid,signal,policy="smooth",
                         duration_hours=horizon_hours,arrival=release,
                         seed=seed+390)["final"]
        candidates[f"WIN_horse_ABM_smooth_info_round{release}"]=_normalize(quote)
    # If the horse signal does not arrive during any of four rounds,
    # changing simulated horse physiology cannot reach bettor decisions.
    # This is a necessary causal negative control (bitwise same uniform).
    uninformed=voter_path(qmid,qmid,policy="smooth",
                          duration_hours=horizon_hours,arrival=5,
                          seed=seed+390)["final"]
    if not np.array_equal(candidates[
            "WIN_horse_ABM_smooth_info_round5"],_normalize(uninformed)):
        raise ValueError("HOLD_WIN_ONLY_UNRELEASED_HORSE_INFORMATION_LEAKED")
    placebo=voter_path(qmid,np.roll(signal,1),policy="smooth",
                       duration_hours=horizon_hours,arrival=1,
                       seed=seed+390)["final"]
    candidates[MODEL_NAMES[-1]]=_normalize(placebo)
    if set(candidates)!=set(MODEL_NAMES):
        raise ValueError("HOLD_WIN_ONLY_CANDIDATE_MODEL_UNIVERSE_CHANGED")
    rows={
        name:[{"n":i,"p":float(v)} for i,v in zip(ids,candidates[name])]
        for name in MODEL_NAMES
    }
    for probs in rows.values():
        if not math.isclose(sum(x["p"] for x in probs),
                            1.,abs_tol=1e-10):
            raise ValueError("HOLD_WIN_ONLY_MODEL_INDEX_NOT_NORMALIZED")
    source_events=state["all_events"]
    original_card_sha=sha256(_dump(c).encode("utf-8")).hexdigest()
    source_sha=source_events[-1]["event_sha256"]
    payload={
        "schema":SCHEMA,"status":STATUS,
        "research_lane":"SECONDARY_SEPARATE_WIN_ONLY_NOT_FULL_WIDE",
        "registered_primary_slot_id":c["slot_id"],
        "race_id":c["race_id"],"provider":c["provider"],
        "card_operator_provenance":c["provenance"],
        "operator_rights_confirmed_locally_only":
            c["rights_reviewed_by_operator"],
        "final_card_SHA256":original_card_sha,
        "original_local_capture_chain_prefix_SHA256":source_sha,
        "original_capture_prefix_length":len(source_events),
        "horse_numbers":list(ids),
        "hypothetical_physical_distance_m":c["race_distance_m"],
        "source_first_WIN_published":state["first_t"].isoformat(),
        "source_first_WIN_received":state["rx1"].isoformat(),
        "source_second_WIN_published":state["second_t"].isoformat(),
        "source_second_WIN_received":state["rx2"].isoformat(),
        "local_freeze_created":state["freeze_at"].isoformat(),
        "target_WIN_window_start":state["target_start"].isoformat(),
        "target_WIN_window_end":state["target_end"].isoformat(),
        "scheduled_post":state["post"].isoformat(),
        "model_code_content_SHA256":_model_code_manifest(),
        "model_draws":horse_draws,"model_seed":seed,
        "physical_crowding_c_m2ps_HYPOTHETICAL":HYPOTHETICAL_CROWD_C,
        "linked_horse_marginal_PDE_numeric_diagnostic":{
            "same_physical_K_c_D_as_first_passage_ABM":True,
            "particle_PDE_max_CDF_gap_synthetic_only":
                pde["max_KS_particle_to_PDE"],
            "horse_density_mass_min":pde["min_horse_probability_mass"],
            "horse_density_mass_max":pde["max_horse_probability_mass"],
            "short_residual_process_duration_s":PDE_DIAGNOSTIC_DURATION_S,
            "particle_replica_count_not_real_races":PDE_DIAGNOSTIC_PARTICLES,
            "factorized_closure_ignores_finite_horse_correlations":True,
            "not_empirically_validated_JRA_horse_PDE":True,
        },
        "past_horse_records_independent_asof_available":False,
        "full_WIDE_grid_used_as_signal":False,
        "actual_JRA_bettor_vote_amounts_observed":False,
        "fixed_next_quote_model_indices":rows,
        "source_and_clock_claim_not_externally_authenticated":True,
        "no_actual_win_probability_or_bet_EV_inferred":True,
        "no_horse_podium_or_race_results_read":True,
    }
    freeze={
        "payload":payload,
        "seal_sha256_of_canonical_payload":_seal(payload),
        "external_GitHub_comment_created_at_verified":False,
        "live_external_sha_posted_by_this_tool":False,
    }
    verify_win_only(freeze)
    return freeze


def verify_win_only(freeze):
    if (not isinstance(freeze,dict) or set(freeze)!={
            "payload","seal_sha256_of_canonical_payload",
            "external_GitHub_comment_created_at_verified",
            "live_external_sha_posted_by_this_tool"}):
        raise ValueError("HOLD_WIN_ONLY_FROZEN_SCHEMA_EXTRA_OR_MISSING")
    p=freeze["payload"]
    if (p.get("schema")!=SCHEMA or p.get("status")!=STATUS or
            _seal(p)!=freeze["seal_sha256_of_canonical_payload"] or
            p.get("research_lane")!="SECONDARY_SEPARATE_WIN_ONLY_NOT_FULL_WIDE"):
        raise ValueError("HOLD_WIN_ONLY_MODEL_SHA_OR_SCHEMA_TAMPERED")
    if (freeze["external_GitHub_comment_created_at_verified"] is not False
            or freeze["live_external_sha_posted_by_this_tool"] is not False):
        raise ValueError("HOLD_WIN_ONLY_CANNOT_SELF_ASSERT_REMOTE_PRESEAL")
    if (not isinstance(p.get("model_code_content_SHA256"),dict) or
            set(p["model_code_content_SHA256"])!=set(CODE_FILES) or
            any(type(h) is not str or len(h)!=64 or
                any(v not in "0123456789abcdef" for v in h)
                for h in p["model_code_content_SHA256"].values())):
        raise ValueError("HOLD_WIN_ONLY_MISSING_MODEL_CODE_FINGERPRINT")
    models=p.get("fixed_next_quote_model_indices")
    ids=p.get("horse_numbers")
    if (not isinstance(models,dict) or set(models)!=set(MODEL_NAMES)
            or ids!=sorted(set(ids)) or not 5<=len(ids)<=30):
        raise ValueError("HOLD_WIN_ONLY_MODELS_OR_HORSE_NUMBER_FIELD_CHANGED")
    for lst in models.values():
        if (not isinstance(lst,list) or [r["n"] for r in lst]!=ids or
                not math.isclose(sum(r["p"] for r in lst),1.,abs_tol=1e-9)
                or any(not math.isfinite(r["p"]) or
                       r["p"]<=0 for r in lst)):
            raise ValueError("HOLD_WIN_ONLY_NOT_A_FULL_FIELD_MARKET_FORECAST")
    return p


def score_win_only(ledger,card,freeze,*,asof,
                   operator_declares_capture_complete):
    p=verify_win_only(freeze)
    c=_check_card(card)
    if operator_declares_capture_complete is not True:
        raise ValueError("HOLD_WIN_ONLY_TARGET_STREAM_COMPLETENESS_NOT_CONFIRMED")
    if (p["race_id"]!=c["race_id"] or
            p["provider"]!=c["provider"] or
            p["registered_primary_slot_id"]!=c["slot_id"] or
            p["final_card_SHA256"]!=sha256(_dump(c).encode("utf-8")).hexdigest()):
        raise ValueError("HOLD_WIN_ONLY_CHANGED_FINAL_CARD_AFTER_FREEZE")
    if p["model_code_content_SHA256"]!=_model_code_manifest():
        raise ValueError("HOLD_WIN_ONLY_MODEL_CODE_CHANGED_USE_ORIGINAL_CODE_VERSION")
    entries=_read_ledger(ledger)
    n=p["original_capture_prefix_length"]
    if (type(n) is not int or n<=0 or len(entries)<n or
            entries[n-1]["event_sha256"]!=
              p["original_local_capture_chain_prefix_SHA256"]):
        raise ValueError("HOLD_WIN_ONLY_SOURCE_CHAIN_CHANGED_AFTER_FREEZE")
    clock=_aware(asof)
    finish=_aware(p["target_WIN_window_end"])
    post=_aware(p["scheduled_post"])
    if clock<finish:
        raise ValueError("HOLD_WIN_ONLY_PREDECLARED_TARGET_WINDOW_NOT_CLOSED")
    boundary=_aware(p["local_freeze_created"])
    mid=_aware(p["source_second_WIN_published"])
    start=_aware(p["target_WIN_window_start"])
    latest=[]
    for e in entries[n:]:
        s=e["captured_source"]
        rx=_aware(e["captured_at_jst"])
        pub=_aware(s["source_updated_at_jst"])
        if (s["race_id"]!=p["race_id"] or
                s["provider"]!=p["provider"] or
                s["provenance"]!=p["card_operator_provenance"]):
            raise ValueError("HOLD_WIN_ONLY_FUTURE_QUOTE_SOURCE_CHANGED")
        if rx>clock or rx<=boundary or s["market"]!="win":
            continue
        prices=_normalized_odds(s["odds_by_horse_number"])
        if set(prices)!=set(p["horse_numbers"]):
            raise ValueError("HOLD_WIN_ONLY_TARGET_HORSE_FIELD_INCOMPLETE")
        if (pub<=mid or pub>rx or rx>=post-timedelta(minutes=10)):
            raise ValueError("HOLD_WIN_ONLY_FUTURE_TARGET_CLOCK_OUTSIDE_SOURCE_CONTRACT")
        if start<=pub<=finish:
            latest.append((pub,rx,prices))
    if not latest:
        if clock<post:
            raise ValueError("HOLD_WIN_ONLY_NO_FINAL_MISSING_TARGET_CLAIM_BEFORE_POST")
        return {
            "schema":TARGET_SCHEMA,"status":MISSING,
            "race_id":p["race_id"],"primary_slot_id":p["registered_primary_slot_id"],
            "local_frozen_model_sha256":freeze["seal_sha256_of_canonical_payload"],
            "outcome_missing_but_slot_retained":True,
            "new_independently_proven_next_market_trial":False,
        }
    chosen=min(latest,key=lambda z:(z[0],z[1]))
    target=_normalize([1/chosen[2][i] for i in p["horse_numbers"]])
    results={}
    for label,model in p["fixed_next_quote_model_indices"].items():
        pred=np.asarray([x["p"] for x in model])
        results[label]={
            "target_price_index_TV_pp":float(50*np.abs(pred-target).sum()),
            "target_price_index_KL_nats":float(
                np.sum(target*np.log(target/pred))),
        }
    return {
        "schema":TARGET_SCHEMA,"status":SCORE_STATUS,
        "race_id":p["race_id"],"primary_slot_id":p["registered_primary_slot_id"],
        "source_target_published":chosen[0].isoformat(),
        "source_target_received":chosen[1].isoformat(),
        "local_frozen_model_sha256":freeze["seal_sha256_of_canonical_payload"],
        "locally_scored_declared_market_target_intervals":1,
        "independently_confirmed_real_market_intervals":0,
        "operator_source_provenance":p["card_operator_provenance"],
        "synthetic_source_is_not_a_real_JRA_market_observation":
            p["card_operator_provenance"]=="synthetic_test",
        "not_an_independent_fully_authenticated_prospective_trial":True,
        "full_WIDE_absent_or_unused_no_imputation":True,
        "scored_next_market_price_index_only_not_horse_finish":True,
        "new_independently_proven_next_market_trial":False,
        "model_score_TV_KL":results,
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    f=sub.add_parser("freeze")
    f.add_argument("--ledger",required=True,type=Path)
    f.add_argument("--final-card",required=True,type=Path)
    f.add_argument("--private-output",required=True,type=Path)
    f.add_argument("--horse-draws",type=int,default=DEFAULT_DRAWS)
    f.add_argument("--seed",type=int,default=HYPOTHETICAL_DRAW_SEED)
    sc=sub.add_parser("score")
    sc.add_argument("--ledger",required=True,type=Path)
    sc.add_argument("--final-card",required=True,type=Path)
    sc.add_argument("--private-freeze",required=True,type=Path)
    sc.add_argument("--private-output",required=True,type=Path)
    sc.add_argument("--operator-confirms-complete-capture",action="store_true")
    a=parser.parse_args()
    if a.command=="freeze":
        result=prepare_win_only(a.ledger,_read(a.final_card),
                                horse_draws=a.horse_draws,seed=a.seed)
    else:
        result=score_win_only(
            a.ledger,_read(a.final_card),_read(a.private_freeze),
            asof=datetime.now(JST).isoformat(),
            operator_declares_capture_complete=
                a.operator_confirms_complete_capture)
    _write_new_private(a.private_output,result)
    print(json.dumps({
        "status":result["payload"]["status"] if a.command=="freeze" else result["status"],
        "research_lane":"WIN_ONLY_SECONDARY",
        "remote_pre_next_market_sha_posted":False,
        "new_prospective_price_trial_fully_authenticated":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
