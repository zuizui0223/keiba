#!/usr/bin/env python3
"""PRIVATE operator capture -> unified horse/bettor freeze -> cohort audit.

Integrates PR25 legal source snapshots, PR22 next-market model, PR23 SHA
comment preparation, and PR24 26-grade/64-auxiliary fixed-denominator cohort.

There is NO real data download, GitHub comment POST, unattended polling,
automated wager or publicly stored licensed quote/horse identity table.

Manual workflow:
  PREPARE = validate first WIN + middle WIN/WIDE source chain + FINAL card,
            select earliest eligible middle update, run existing nonlocal
            horse ABM -> smooth staged voter ABM, freeze 12 models, bind
            race to a pre-registered 26-grade OR 64-number slot, and for
            an operator-authorized source create safe SHA-only PR22 comment
            text; NEVER post it automatically.
  SCORE = reopen the same private freeze/ledger, prove the pre-freeze chain
          prefix is still byte-identical, process *later* observed WIN
          snapshots, score ONLY the locked 15-to-20-minute future target,
          and preserve an absent target as a missing observation.
  AUDIT = score one source-linked pre-registered race without accepting
          extra score fields, claims of remote SHA attestation or a changed
          candidate model set.

The PR23 GitHub receipt is checked INDEPENDENTLY, via verify-live on
explicit user request outside this module. SHA text created locally is
NOT externally timestamped. A locally scored market quote is never
reported as independently certified complete; official podium and
payouts are entirely absent.

IMPORTANT: PR24's 26 graded-race denominator and its distinct auxiliary
64 planned race-number slots may overlap. For a graded race, the
*graded* slot is the primary label; report provisional auxiliary overlap
only as a duplicate physical race, never as a second independent trial.
For an auxiliary-only race preserve the 64-slot original denominator and
do NOT insert it fraudulently into the 26-grade roster.

Local hash-chain files may all be rewritten by an adversary; their local
clock is not authenticated. No source licensing beyond operator assertion
is implied. The original 2026 菊花賞 preseal and v3.1 formal ledger stay
unmodified; no new genuine future observations have been obtained.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from keiba_operator_winwide_capture import (
    ROOT, JST, _read_ledger, _check_card, freeze_private_from_ledger,
    score_private_from_ledger, _write_new_private, _dump,
)
from keiba_fixed_denominator_market_campaign import (
    _locked_universe, _aware, campaign, RECEIPT_SCHEMA,
    EXPECTED_LEGACY_KIKKA,
    LOCKED_MARKET_HORIZON_MINUTES,
    LOCKED_MARKET_TARGET_WINDOW_MINUTES,
)
from keiba_secondary_64_market_slots import defined_slots
from keiba_private_multirace_winwide_shadow import (
    verify_freeze, SCORE_SCHEMA, SCORE_STATUS,
)
from keiba_nextprice_pr_comment_attestation import (
    prepare_comment, STATUS_PREPARED,
)
from odds_shadow_freeze_score import _seal

BUNDLE_SCHEMA="KEIBA_OPERATOR_PRIVATE_NEXT_MARKET_COHORT_BUNDLE_V1"
BUNDLE_SCORED_SCHEMA="KEIBA_OPERATOR_PRIVATE_NEXT_MARKET_COHORT_SCORE_V1"
BUNDLE_STATUS="LOCAL_FULL_WIN_WIDE_FREEZE_WITH_FIXED_COHORT_SLOT"
SCORE_STATUS_LOCAL="LOCAL_NEXT_MARKET_PRICE_ONLY_WITH_FIXED_COHORT_SLOT"
MISSING="HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW"
HOLD_SOURCE="SOURCE_RIGHTS_RECEPTION_AND_TARGET_CAPTURE_NOT_EXTERNALLY_VERIFIED"
CAPTURE_BINDING_SCHEMA="KEIBA_FROZEN_SOURCE_CHAIN_AND_FINAL_CARD_BINDING_V1"
CAPTURE_BINDING_FIELDS={
    "schema", "operator_final_card_sha256",
    "private_capture_chain_prefix_sha256", "local_chain_prefix_length",
    "actual_horse_physics_distance_m", "final_runner_numbers",
}


def _card_digest(card):
    """Canonical private-card hash, never the contents of a public SHA comment."""
    return sha256(_dump(card).encode("utf-8")).hexdigest()


def _anchor_original_inputs(freeze, card, ledger_events, selected_feature):
    """Bind ALL pre-freeze raw capture events and the official-card claim.

    Previously the PR22 prediction SHA committed only to normalized market
    feature rows and forecast vectors. The source URLs and card distance
    remained outside that digest in a mutable local wrapper. Here the
    complete operator input chain head, original declared final card and
    actual horse-physics distance enter the SAME pre-next-price SHA.

    This is a hash integrity binding, NOT a third-party source/timestamp
    attestation and NOT evidence of true measured horse movement.
    """
    payload=verify_freeze(freeze)
    if not ledger_events or "operator_source_card_chain_binding" in payload:
        raise ValueError("HOLD_ALREADY_BOUND_OR_EMPTY_SOURCE_CHAIN")
    if (payload["race_id"]!=card["race_id"] or
        payload["provider"]!=card["provider"] or
        payload["horse_numbers"]!=card["horse_numbers"] or
        payload["source_sha256_local_only"]!=
            sha256(_dump(selected_feature).encode("utf-8")).hexdigest()):
        raise ValueError("HOLD_SELECTED_MODEL_INPUTS_NOT_FROM_DECLARED_SOURCE")
    binding={
        "schema":CAPTURE_BINDING_SCHEMA,
        "operator_final_card_sha256":_card_digest(card),
        "private_capture_chain_prefix_sha256":ledger_events[-1]["event_sha256"],
        "local_chain_prefix_length":len(ledger_events),
        "actual_horse_physics_distance_m":card["race_distance_m"],
        "final_runner_numbers":list(card["horse_numbers"]),
    }
    payload["operator_source_card_chain_binding"]=binding
    digest=_seal(payload)
    freeze["seal_sha256_of_canonical_payload"]=digest
    # This nested summary is a PREPARATION AID only; it is not submitted.
    freeze["SHA_only_existing_dispatch_inputs_NOT_SENT"]["seal_sha256"]=digest
    verify_freeze(freeze)
    return binding


def _check_bound_card(freeze,card):
    payload=verify_freeze(freeze)
    b=payload.get("operator_source_card_chain_binding")
    if (not isinstance(b,dict) or set(b)!=CAPTURE_BINDING_FIELDS or
        b["schema"]!=CAPTURE_BINDING_SCHEMA or
        b["operator_final_card_sha256"]!=_card_digest(card) or
        b["actual_horse_physics_distance_m"]!=card["race_distance_m"] or
        b["final_runner_numbers"]!=card["horse_numbers"] or
        b["final_runner_numbers"]!=payload["horse_numbers"] or
        type(b["local_chain_prefix_length"]) is not int or
        b["local_chain_prefix_length"]<1):
        raise ValueError("HOLD_CARD_CHAIN_AND_PHYSICAL_MODEL_NOT_SAME_SEAL")
    if (freeze.get("SHA_only_existing_dispatch_inputs_NOT_SENT",{}).get(
           "seal_sha256")!=freeze["seal_sha256_of_canonical_payload"]):
        raise ValueError("HOLD_PUBLIC_SHA_PREPARATION_NOT_SAME_FROZEN_MODEL")
    return b


def _receipt(card,freeze,stage):
    """The EXACT PR24 receipt schema; never invent an official race ID."""
    source=verify_freeze(freeze)
    _check_bound_card(freeze,card)
    if source["race_id"]!=card["race_id"]:
        raise ValueError("HOLD_CARD_RACE_AND_FREEZE_ID_MISMATCH")
    if stage not in ("local_SHA_frozen","next_quote_local_scored",
                     "next_quote_window_missing"):
        raise ValueError("HOLD_INVALID_NEXT_MARKET_COHORT_STAGE")
    if (source["target_horizon_minutes"]!=LOCKED_MARKET_HORIZON_MINUTES
            or source["target_window_minutes"]!=
               LOCKED_MARKET_TARGET_WINDOW_MINUTES
            or source["provider"]!=card["provider"]
            or _aware(source["scheduled_post_jst"])!=
               _aware(card["scheduled_post_jst"])):
        raise ValueError("HOLD_POST_PROVIDER_OR_HORIZON_CHANGED")
    return {
        "slot_id":card["slot_id"],
        "official_race_id":card["race_id"],
        "scheduled_post_jst":card["scheduled_post_jst"],
        "racecard_source_url":card["source_card_url"],
        "racecard_received_at_jst":card["source_card_received_at_jst"],
        "quote_provider_name":card["provider"],
        "source_rights_checked_locally":card["rights_reviewed_by_operator"],
        "capture_stage":stage,
        "local_frozen_model_sha256":
            freeze["seal_sha256_of_canonical_payload"],
        "target_horizon_minutes":LOCKED_MARKET_HORIZON_MINUTES,
        "target_window_minutes":LOCKED_MARKET_TARGET_WINDOW_MINUTES,
    }


def _scope(card):
    core,_=_locked_universe(ROOT)
    aux=defined_slots(ROOT)
    primary=card["slot_id"]
    original={z["slot_id"] for z in core if z["slot_id"]!=EXPECTED_LEGACY_KIKKA}
    secondary={z["slot_id"] for z in aux}
    if primary==EXPECTED_LEGACY_KIKKA or primary not in (original|secondary):
        raise ValueError("HOLD_NOT_REGISTERED_AS_ELIGIBLE_NEXT_MARKET_RACE")
    grade=[z for z in core if z["slot_id"] in original and
           z["scheduled_date_jst"]==
           _aware(card["scheduled_post_jst"]).date().isoformat() and
           z["venue"]==primary.split("|")[1]]
    matching_aux=f"{_aware(card['scheduled_post_jst']).date()}|"+(
        primary.split("|")[1])+f"|R{card['race_number']:02d}"
    possible_grade_duplicate=matching_aux in secondary and bool(
        grade and any(z["slot_id"]==primary for z in grade))
    if primary in original:
        cohort="FROZEN_GRADED_26_PRIMARY"
    else:
        cohort="FROZEN_AUXILIARY_64_PRIMARY"
        # A grade on that date/venue MAY overlap the numbered race, but
        # cannot be inferred just by the date/venue alone.
        possible_grade_duplicate=(card["race_number"]==11 and bool(grade))
    return {
        "primary_scope":cohort,
        "primary_slot_id":primary,
        "registered_graded_slots":26,
        "registered_auxiliary_slots":64,
        "possible_same_real_grade_auxiliary_race":possible_grade_duplicate,
        "both_registries_are_NOT_additively_independent":True,
        "future_independent_real_market_observation_confirmed":False,
    }


def _cohort_diagnostic(card,freeze,*,stage,score=None,asof=None):
    scope=_scope(card)
    if scope["primary_scope"]=="FROZEN_GRADED_26_PRIMARY":
        meta={"schema":RECEIPT_SCHEMA,
              "entries":[_receipt(card,freeze,stage)]}
        result=campaign(
            ROOT, asof=asof or datetime.now(JST).isoformat(),
            local_receipts=meta,
            private_scores=[score] if score is not None else [])
        assert len(result["registered_slot_readiness"])==26
        return {
            "scope":"graded_26",
            "original_fixed_denominator":26,
            "candidate_next_price_slots_not_including_Kikka":25,
            "local_candidate_price_scores":
                result["locally_scored_next_price_intervals_unattested"],
            "locally_missing_window_slots":
                result["missing_locked_next_quote_target_intervals"],
            "server_SHA_pretarget_verified":0,
            "fully_independent_prospective_confirmed":False,
            "possible_grade_auxiliary_overlap":
                scope["possible_same_real_grade_auxiliary_race"],
        }
    else:
        # PR24's graded registry does not accept an auxiliary R## slot.
        # Preserve that as a SEPARATE scope rather than forging a grade ID.
        status=score.get("status") if score is not None else None
        return {
            "scope":"auxiliary_64",
            "original_fixed_denominator":64,
            "one_local_next_price_score":int(status==SCORE_STATUS),
            "one_missing_predeclared_quote_window":int(status==MISSING),
            "graded_registry_26_unchanged":True,
            "server_SHA_pretarget_verified":0,
            "fully_independent_prospective_confirmed":False,
            "possible_grade_auxiliary_overlap":
                scope["possible_same_real_grade_auxiliary_race"],
        }


def prepare_bundle(ledger,card,*,frozen_at_jst=None,
                   horse_draws=120,seed=20261026):
    card=_check_card(card)
    # Verify the race belongs to a future predeclared source-fixed scope.
    scope=_scope(card)
    output=freeze_private_from_ledger(
        ledger,card,freeze_at_jst=frozen_at_jst,
        horse_draws=horse_draws,horse_seed=seed)
    freeze=output["freeze"]
    all_events=_read_ledger(ledger)
    if not all_events:
        raise ValueError("HOLD_EMPTY_LOCAL_SOURCE_CAPTURE")
    latest=all_events[-1]["event_sha256"]
    # Crucial: include the original source-chain and final-card digests in
    # the externally publishable forecast's *own* SHA, not just in a local
    # wrapper which could be relabeled after a remote comment is posted.
    _anchor_original_inputs(freeze,card,all_events,output["feature"])
    receipt=_receipt(card,freeze,"local_SHA_frozen")
    manifest=None
    if card["provenance"]=="authorized_private_local_export":
        manifest=prepare_comment(freeze)
        if (manifest["status"]!=STATUS_PREPARED
                or manifest["remote_sha_publication_confirmed"]):
            raise ValueError("HOLD_PREPARED_SHA_ONLY_COMMENT_WRONG_STATE")
    report={
        "schema":BUNDLE_SCHEMA,
        "status":BUNDLE_STATUS,
        "card":card,
        "freeze":freeze,
        "registered_cohort":scope,
        "capture_ledger_prefix_events":len(all_events),
        "capture_ledger_prefix_head_SHA256":latest,
        "private_PR24_metadata_receipt":{
            "schema":RECEIPT_SCHEMA,"entries":[receipt]},
        "public_SHA_only_comment_not_posted":manifest,
        "private_frozen_source_price_may_not_be_published_to_public_GitHub":True,
        "new_actual_source_and_target_independently_attested":False,
        "external_GitHub_comment_created_at_verified":False,
        "genuinely_prospective_market_trial_counted":False,
    }
    # A false proof flag cannot be created merely by bundling files.
    if report["capture_ledger_prefix_head_SHA256"]!=latest:
        raise ValueError("HOLD_CAPTURE_LEDGER_PREFIX_INCONSISTENCY")
    return report


def _validate_bundle_and_prefix(bundle,ledger):
    if not isinstance(bundle,dict) or bundle.get("schema")!=BUNDLE_SCHEMA:
        raise ValueError("HOLD_PRIVATE_OPERATOR_BUNDLE_SCHEMA")
    frozen=bundle["freeze"]
    payload=verify_freeze(frozen)
    card=_check_card(bundle["card"])
    anchored=_check_bound_card(frozen,card)
    if (payload["race_id"]!=card["race_id"]
            or payload["provider"]!=card["provider"]
            or payload["scheduled_post_jst"]!=
               _aware(card["scheduled_post_jst"]).isoformat()):
        raise ValueError("HOLD_CARD_VS_PRIVATE_SHA_FREEZE_CHANGED")
    current=_read_ledger(ledger)
    n=bundle["capture_ledger_prefix_events"]
    if (type(n) is not int or n<=0 or len(current)<n
            or n!=anchored["local_chain_prefix_length"] or
            bundle["capture_ledger_prefix_head_SHA256"]!=
                anchored["private_capture_chain_prefix_sha256"] or
            current[n-1]["event_sha256"]!=
               bundle["capture_ledger_prefix_head_SHA256"]):
        raise ValueError("HOLD_EARLY_CAPTURE_SOURCE_CHAIN_CHANGED_AFTER_FREEZE")
    if (bundle["private_PR24_metadata_receipt"] !={
        "schema":RECEIPT_SCHEMA,
        "entries":[_receipt(card,frozen,"local_SHA_frozen")]}):
        raise ValueError("HOLD_OPERATOR_REGISTRY_METADATA_OR_SOURCE_SHA_MODIFIED")
    return card,frozen,current


def score_bundle(bundle,ledger,*,asof,operator_confirms_complete):
    card,frozen,events=_validate_bundle_and_prefix(bundle,ledger)
    now=_aware(asof)
    post=_aware(card["scheduled_post_jst"])
    if now<_aware(frozen["payload"]["next_quote_max_published_at"]):
        raise ValueError("HOLD_FORECAST_TARGET_WINDOW_NOT_YET_CLOSED")
    if operator_confirms_complete is not True:
        raise ValueError("HOLD_OPERATOR_DID_NOT_ASSERT_NEXT_QUOTE_STREAM_COMPLETENESS")
    try:
        scored=score_private_from_ledger(
            ledger,frozen,operator_declares_complete=True,
            scoring_at_jst=now.isoformat())["local_operator_capture_score"]
    except ValueError as error:
        if "HOLD_NO_POST_FREEZE_WIN_SNAPSHOTS_YET" not in str(error):
            raise
        if now<post:
            raise ValueError("HOLD_NO_FINAL_MISSING_TARGET_CLAIM_BEFORE_POST") from error
        scored={
            "schema":SCORE_SCHEMA,"status":MISSING,
            "race_id":card["race_id"],
            "external_preseal_authenticated":False,
        }
    if scored["status"]==MISSING and now<post:
        raise ValueError("HOLD_NO_FINAL_MISSING_TARGET_CLAIM_BEFORE_POST")
    if scored["status"] not in (SCORE_STATUS,MISSING):
        raise ValueError("HOLD_NO_VALID_NEXT_QUOTE_SCORE_OR_MISSING_STATUS")
    if scored.get("external_preseal_authenticated") is not False:
        raise ValueError("HOLD_LOCAL_NEXT_QUOTE_CANNOT_SELF_ATTEST")
    stage=("next_quote_local_scored" if scored["status"]==SCORE_STATUS
           else "next_quote_window_missing")
    return {
        "schema":BUNDLE_SCORED_SCHEMA,
        "status":SCORE_STATUS_LOCAL if stage=="next_quote_local_scored"
                 else "HOLD_NO_QUOTE_IN_LOCKED_NEXT_MARKET_WINDOW",
        "race_id":card["race_id"],
        "primary_registered_slot":card["slot_id"],
        "original_freeze_SHA256":frozen[
            "seal_sha256_of_canonical_payload"],
        "frozen_input_capture_chain_prefix_unchanged":True,
        "source_stream_locally_complete_asserted_by_operator_only":True,
        "private_PR24_updated_metadata_receipt":{
            "schema":RECEIPT_SCHEMA,
            "entries":[_receipt(card,frozen,stage)]},
        "local_market_score":scored,
        "cohort_audit":_cohort_diagnostic(
            card,frozen,stage=stage,score=scored,asof=now.isoformat()),
        "independent_GitHub_SHA_pretarget_proof":False,
        "source_and_later_target_independently_complete":False,
        "actual_horse_win_proper_score_or_betting_return_computed":False,
        "new_independent_real_prospective_quote_trials_confirmed":0,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="action",required=True)
    f=sub.add_parser("prepare")
    f.add_argument("--private-ledger",required=True,type=Path)
    f.add_argument("--confirmed-card",required=True,type=Path)
    f.add_argument("--private-output",required=True,type=Path)
    f.add_argument("--horse-draws",type=int,default=120)
    f.add_argument("--seed",type=int,default=20261026)
    sc=sub.add_parser("score")
    sc.add_argument("--private-ledger",required=True,type=Path)
    sc.add_argument("--private-bundle",required=True,type=Path)
    sc.add_argument("--private-output",required=True,type=Path)
    sc.add_argument("--operator-confirms-complete-capture",action="store_true")
    args=ap.parse_args()
    from keiba_operator_winwide_capture import _write_new_private
    if args.action=="prepare":
        data=prepare_bundle(
            args.private_ledger,
            json.loads(args.confirmed_card.read_text(encoding="utf-8")),
            horse_draws=args.horse_draws,seed=args.seed)
    else:
        data=score_bundle(
            json.loads(args.private_bundle.read_text(encoding="utf-8")),
            args.private_ledger,asof=datetime.now(JST).isoformat(),
            operator_confirms_complete=args.operator_confirms_complete_capture)
    _write_new_private(args.private_output,data)
    print(json.dumps({
        "status":data["status"],
        "new_prospective_verified_market_trials":0,
        "GitHub_comment_automatically_submitted":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
