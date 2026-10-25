#!/usr/bin/env python3
"""Join LIVE GitHub PR22 SHA-time verification to the locked JRA 26 slots.

NO GitHub writes: this script GETs live GitHub server comments via
keiba_nextprice_pr_comment_attestation.verify_live and only with private
SHA-sealed forecasts supplied explicitly. Scores remain PR22 price-index
TV/KL, NOT outcome probabilities or wagering returns.

This resolves an essential gap in PR24: the campaign denominator currently
cannot ingest the independent PR23 GitHub receipt. A file containing a
self-declared receipt is NEVER accepted as a trusted proof; the only
live path calls verify_live(freeze), which acquires the latest GitHub REST
records independently and checks whether comment.created_at preceded
the NEXT quote target, not merely horse-race post.

Even for authenticated GitHub SHA posts, this report cannot certify
that source odds/horse histories are true, received before the frozen
clock, or the target WIN stream is complete. Consequently the formally
proven prospective market-prediction cohort count remains ZERO until
independent source/target capture attestation is also established.
Never push any private freeze, odds panel or horse history to GitHub.

No new market observations or actual submissions are created by this tool.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
from statistics import mean

from keiba_fixed_denominator_market_campaign import (
    ROOT, campaign, _locked_universe, _metadata, _scores,
    _aware, _sha, EXPECTED_LEGACY_KIKKA, EXPECTED_SLOTS,
    LOCKED_MARKET_HORIZON_MINUTES,
    LOCKED_MARKET_TARGET_WINDOW_MINUTES,
)
from keiba_private_multirace_winwide_shadow import (
    verify_freeze, SCORE_STATUS,
)
from keiba_nextprice_pr_comment_attestation import (
    verify_live, bind_scored_next_market_to_proof, STATUS_REMOTE,
)

STATUS="FIXED_COHORT_LIVE_GITHUB_SHA_CLAIM_ONLY_TARGET_CAPTURE_UNATTESTED"
REMOTE_PROOF_DISABLED="NOT_SUBMITTED_OR_NO_AUTHORIZED_PRIVATE_FREEZE"
REMOTE_PROOF_READY="GITHUB_COMMENT_SERVER_TIME_PRE_NEXT_PRICE_VERIFIED"
TARGET_SCORE_LOCAL="NEXT_PRICE_TARGET_LOCALLY_SCORED_NOT_INDEPENDENTLY_CAPTURE_ATTESTED"
MISSING_TARGET_LOCAL="TARGET_WINDOW_MISSING_LOCAL_SELF_DECLARATION"
PRIMARY="next_price_index_TV_pp"
MODEL_EXPOSURES=(
    "mid_WIN_persistence",
    "mid_WIN_momentum",
    "mid_WIN_momentum_plus_WIDE_node_beta025",
    "coupled_market_qmid_horse_signal_round1",
    "coupled_market_qmid_horse_signal_plus_WIDE_round1",
    "coupled_market_qmid_horse_signal_plus_rotated_WIDE_placebo_round1",
)


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _bundle_private_safely(metadata, frozen, *, asof):
    """Map a private freeze to exactly one already-registered future slot.

    Does not accept a SHA-only manifest, synthetic history replay, or
    invented race names as new official JRA rows. All source-card fields
    must match the locally declared verified card metadata. Neither
    receipt nor SHA by itself proves those card fields were authentic.
    """
    payload=verify_freeze(frozen)
    if payload.get("source_provenance")!="authorized_private_local_export":
        raise ValueError("HOLD_REMOTE_CAMPAIGN_REPLAY_NOT_AUTHORIZED_TO_BE_LIVE")
    rid=payload["race_id"]
    candidates=[
        (slot,meta) for slot,meta in metadata.items()
        if meta["official_race_id"]==rid
    ]
    if len(candidates)!=1:
        raise ValueError("HOLD_REMOTE_SHA_RACE_MISSING_REGISTERED_CARD_ID")
    slot,meta=candidates[0]
    if slot==EXPECTED_LEGACY_KIKKA:
        raise ValueError("HOLD_LEGACY_KIKKA_IS_NOT_NEXT_MARKET_SHA_COHORT")
    if meta["capture_stage"] not in (
        "local_SHA_frozen","next_quote_local_scored",
        "next_quote_window_missing",
    ):
        raise ValueError("HOLD_CAMPAIGN_STAGE_DID_NOT_LOCK_A_MODEL")
    if (payload["provider"]!=meta["quote_provider_name"]
            or _aware(payload["scheduled_post_jst"])!=
               _aware(meta["scheduled_post_jst"])
            or payload["target_horizon_minutes"]!=
               LOCKED_MARKET_HORIZON_MINUTES
            or payload["target_window_minutes"]!=
               LOCKED_MARKET_TARGET_WINDOW_MINUTES
            or payload["source_provenance"]!="authorized_private_local_export"
            or payload.get("has_only_local_self_declared_time_proof") is not True
            or payload.get("external_GitHub_server_preseal_verified") is not False
            or payload["local_freeze_created_at"] is None
            or _aware(payload["local_freeze_created_at"])>_aware(asof)):
        raise ValueError("HOLD_REMOTE_PROOF_RACE_WINDOW_SOURCE_OR_LOCAL_FREEZE")
    _sha(frozen["seal_sha256_of_canonical_payload"])
    if frozen["seal_sha256_of_canonical_payload"]!=meta["local_frozen_model_sha256"]:
        raise ValueError("HOLD_REGISTERED_SHA_DIFFERENT_FROM_PRIVATE_FROZEN_MODEL")
    return slot,payload


def audit_live(root=ROOT, *, asof, local_receipts,private_scores=None,
               private_freezes=None):
    """Direct remote GET only; never accept user-supplied API proof JSON."""
    if local_receipts is None:
        raise ValueError("HOLD_PRIVATE_26_SLOT_METADATA_REQUIRED_FOR_LIVE_PROOF")
    private_scores=private_scores if private_scores is not None else []
    private_freezes=private_freezes if private_freezes is not None else []
    now=_aware(asof)
    # Reuse every original fail-closed PR24 gate: SHA-locked 26 slots,
    # source-card crosswalk, official post, missing target and score time.
    existing=campaign(root,asof=asof,
                      local_receipts=local_receipts,private_scores=private_scores)
    events,_=_locked_universe(root)
    metadata=_metadata(local_receipts,events)
    scored=_scores(private_scores,metadata)
    proof_for_slot={}
    seen_remote_ids=set()
    sha_seen=set()
    for frozen in private_freezes:
        slot,payload=_bundle_private_safely(metadata,frozen,asof=asof)
        if slot in proof_for_slot:
            raise ValueError("HOLD_SECOND_FROZEN_MODEL_FOR_SAME_REGISTERED_RACE")
        sha=frozen["seal_sha256_of_canonical_payload"]
        if sha in sha_seen:
            raise ValueError("HOLD_SAME_PRIVATE_MODEL_SHA_REUSED_ACROSS_RACES")
        sha_seen.add(sha)
        proof=verify_live(frozen)  # independent GitHub CLI REST retrieval
        if (not isinstance(proof,dict)
                or proof.get("status")!=STATUS_REMOTE
                or proof.get("external_sha_pre_target_verified") is not True
                or proof.get("independent_GitHub_API_fetch_performed") is not True
                or proof.get("race_id")!=payload["race_id"]
                or proof.get("sha256_of_full_private_frozen_model")!=sha
                or _aware(proof["race_post_at"])!=
                   _aware(payload["scheduled_post_jst"])
                or _aware(proof["target_market_window_begins_at"])!=
                   _aware(payload["next_quote_min_published_at"])
                or _aware(proof["github_server_comment_created_at_claim"])>now):
            raise ValueError("HOLD_GITHUB_SHA_RECEIPT_INVALID_OR_AFTER_ASOF")
        cid=proof.get("github_comment_id")
        if type(cid) is not int or cid in seen_remote_ids or cid<1:
            raise ValueError("HOLD_REMOTE_COMMENT_ID_REUSED_OR_MISSING")
        seen_remote_ids.add(cid)
        score=scored.get(slot)
        if score is not None and score["status"]==SCORE_STATUS:
            # Live proof matched directly to a private saved next-price
            # score, including SHA and target update AFTER GitHub timestamp.
            bound=bind_scored_next_market_to_proof(proof,score)
            assert bound["source_receipts_independently_verified"] is False
            target_status=TARGET_SCORE_LOCAL
        elif score is not None:
            target_status=MISSING_TARGET_LOCAL
        else:
            target_status="NEXT_PRICE_NOT_LOCALLY_SCORED"
        proof_for_slot[slot]={
            "source_race_id":payload["race_id"],
            "github_comment_id":cid,
            "github_comment_url":proof["github_comment_url"],
            "github_server_created_at":proof[
                "github_server_comment_created_at_claim"],
            "external_SHA_time_before_next_quote_verified":True,
            "next_quote_target_capture_status":target_status,
            "private_source_receipt_independently_verified":False,
            "full_next_quote_capture_independently_verified":False,
            "no_actual_winner_or_wager_data_used":True,
        }
    for item in existing["registered_slot_readiness"]:
        evidence=proof_for_slot.get(item["slot_id"])
        item["external_SHA_creation_time_verified_by_this_campaign"]=bool(evidence)
        if evidence:
            item["github_sha_receipt"]=evidence
            item["capture_state"] += "_PLUS_REMOTE_SHA_PRENEXT_PRICE"
        else:
            item["github_sha_receipt"]={
                "status":REMOTE_PROOF_DISABLED,
                "external_SHA_time_before_next_quote_verified":False,
            }
    existing["status"]=STATUS
    existing["remotely_SHA_pre_next_price_verified_intervals"]=len(proof_for_slot)
    existing["remotely_SHA_verified_and_locally_next_price_scored"]=sum(
        v["next_quote_target_capture_status"]==TARGET_SCORE_LOCAL
        for v in proof_for_slot.values())
    existing["next_market_SHA_comment_proven_solely_by_independent_GitHub_GET"] = True
    existing["live_sha_proof_does_NOT_authenticate_market_capture"]=True
    existing["prospective_market_outcome_validation_certified"]=False
    # The locked 26 G1-G3 races are NOT a large independent training cohort.
    # A server proof of digest preexistence is necessary but insufficient
    # for fully independently attested true prices, volume or market skill.
    existing["new_independent_real_prospective_quote_trials_confirmed"]=0
    existing["real_world_information_arrival_or_regime_criticality"]="HOLD"
    if (len(existing["registered_slot_readiness"])!=EXPECTED_SLOTS
            or existing["registered_next_price_candidate_slots_excluding_old_Kikka"]
               !=EXPECTED_SLOTS-1):
        raise ValueError("HOLD_REMOTE_CAMPAIGN_DENOMINATOR_CHANGED")
    return existing


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--as-of",required=True)
    ap.add_argument("--receipts",required=True,type=Path)
    ap.add_argument("--scores",type=Path,nargs="*",default=[])
    ap.add_argument("--private-freezes",type=Path,nargs="*",default=[])
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    result=audit_live(
        asof=args.as_of,
        local_receipts=_read_json(args.receipts),
        private_scores=[_read_json(p) for p in args.scores],
        private_freezes=[_read_json(p) for p in args.private_freezes],
    )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,
                                      allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "fixed_slots":result["registered_flat_G1_G2_G3_slots_including_Kikka"],
        "live_GitHub_sha_receipts":
            result["remotely_SHA_pre_next_price_verified_intervals"],
        "fully_independent_prospective_market_trials":
            result["new_independent_real_prospective_quote_trials_confirmed"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
