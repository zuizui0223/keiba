#!/usr/bin/env python3
"""ONE physical race, TWO separate source-availability research lanes.

A = primary complete WIN×WIDE with PR17 horse + PR19 bettor model
B = predeclared WIN-only secondary with the SAME linked horse/PDE/bettor
    physics, but NO WIDE imputation.

Both may exist for one declared JRA race. They MUST be scored against
the SAME q2 target source/publication/receipt before any within-race
WIDE incremental contrast is interpreted. If source timestamps or
full-field market-only baselines differ, refuse paired comparison.
Otherwise A and B remain distinct availability states, never 2
independent market observations.

Local operator data / verified final card are SELF-DECLARED, not
independently attested by the market provider. The PR22 and PR30
GitHub SHA-only comments use DIFFERENT typed proof records; this
module never posts or fabricates either proof.

All forecasts are created by the earlier freezes. This script only
recomputes local next-market source scores from the original chained
source and existing sealed models; it cannot retrospectively select
source q0/qmid or adjust the model to q2. Missing quote -> HOLD.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path

from keiba_operator_winwide_capture import (
    JST,_check_card,_read_ledger,_write_new_private,
)
from keiba_operator_cohort_bundle import (
    BUNDLE_SCHEMA, score_bundle, _scope,
)
from keiba_win_only_shadow_lane import (
    SCHEMA as B_FREEZE_SCHEMA, verify_win_only, score_win_only,
    SCORE_STATUS as B_SCORE_STATUS, MISSING as B_MISSING,
)
from keiba_private_multirace_winwide_shadow import (
    SCORE_STATUS as A_SCORE_STATUS,
)
from keiba_fixed_denominator_market_campaign import EXPECTED_LEGACY_KIKKA

SCHEMA="KEIBA_DUAL_LANE_SINGLE_RACE_NEXT_MARKET_SCORE_V1"
COHORT_SCHEMA="KEIBA_DUAL_LANE_UNIQUE_RACE_COHORT_V1"
STATUS="DUAL_LANE_A_WIDE_AND_B_WIN_ONLY_LOCAL_ONLY_NOT_AUTHENTICATED"
LANE_A="PRIMARY_FULL_WIN_WIDE"
LANE_B="SECONDARY_WIN_ONLY"
A_MISSING="HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW"


def _local_scored_A(ledger, bundle, asof):
    if bundle is None:
        return None
    if not isinstance(bundle,dict) or bundle.get("schema")!=BUNDLE_SCHEMA:
        raise ValueError("HOLD_DUAL_A_NOT_AN_ORIGINAL_SOURCE_BOUND_BUNDLE")
    return score_bundle(bundle,ledger,asof=asof,
                        operator_confirms_complete=True)


def _local_scored_B(ledger, card, freeze, asof):
    if freeze is None:
        return None
    if (not isinstance(freeze,dict) or
            freeze.get("payload",{}).get("schema")!=B_FREEZE_SCHEMA):
        raise ValueError("HOLD_DUAL_B_NOT_A_TYPE_SAFE_WIN_ONLY_FREEZE")
    verify_win_only(freeze)
    return score_win_only(ledger,card,freeze,asof=asof,
                          operator_declares_capture_complete=True)


def compare_once(ledger,card,*,asof,lane_A_bundle=None,lane_B_freeze=None):
    card=_check_card(card)
    scope=_scope(card)
    if card["slot_id"]==EXPECTED_LEGACY_KIKKA:
        raise ValueError("HOLD_LEGACY_KIKKA_CANNOT_BE_NEW_NEXT_PRICE_EVALUATION")
    if lane_A_bundle is None and lane_B_freeze is None:
        raise ValueError("HOLD_NO_SOURCE_FROZEN_A_OR_B_MARKET_MODEL")
    if lane_A_bundle is not None and (
            lane_A_bundle["card"]!=card or
            lane_A_bundle["registered_cohort"]!=scope):
        raise ValueError("HOLD_DUAL_A_RACE_SCOPE_OR_CARD_CHANGED")
    if lane_B_freeze is not None:
        if (not isinstance(lane_B_freeze,dict) or
                lane_B_freeze.get("payload",{}).get("schema")!=B_FREEZE_SCHEMA):
            raise ValueError("HOLD_DUAL_B_NOT_A_TYPE_SAFE_WIN_ONLY_FREEZE")
        b=verify_win_only(lane_B_freeze)
        if (b["race_id"]!=card["race_id"] or
                b["provider"]!=card["provider"] or
                b["registered_primary_slot_id"]!=card["slot_id"] or
                b["horse_numbers"]!=card["horse_numbers"]):
            raise ValueError("HOLD_DUAL_B_RACE_SCOPE_OR_RUNNERS_CHANGED")
    a=_local_scored_A(ledger,lane_A_bundle,asof)
    b=_local_scored_B(ledger,card,lane_B_freeze,asof)
    a_score=a["local_market_score"] if a is not None else None
    a_good=(a_score is not None and a_score["status"]==A_SCORE_STATUS)
    b_good=(b is not None and b["status"]==B_SCORE_STATUS)
    a_status=(a_score["status"] if a_score is not None else
              "HOLD_FULL_WIDE_NOT_PRETARGET_FROZEN")
    b_status=(b["status"] if b is not None else
              "HOLD_WIN_ONLY_NOT_PRETARGET_FROZEN")
    paired=None
    if a_good and b_good:
        A=lane_A_bundle["freeze"]["payload"]
        B=lane_B_freeze["payload"]
        if (A["race_id"]!=B["race_id"] or
                A["horse_numbers"]!=B["horse_numbers"] or
                A["middle_WIN_quote_published_at"]!=
                    B["source_second_WIN_published"] or
                A["first_WIN_quote_published_at"]!=
                    B["source_first_WIN_published"] or
                A["next_quote_min_published_at"]!=
                    B["target_WIN_window_start"] or
                A["next_quote_max_published_at"]!=
                    B["target_WIN_window_end"] or
                a_score["selected_first_eligible_source_published_at"]!=
                    b["source_target_published"] or
                a_score["selected_source_received_at"]!=
                    b["source_target_received"]):
            raise ValueError("HOLD_DUAL_A_B_DIFFERENT_SOURCE_Q0_QMID_OR_Q2_CLOCK")
        # First verify the EXACT frozen qmid and momentum distributions,
        # not merely equal errors against the same later target. Different
        # original WIN price vectors can accidentally have the same TV/KL
        # scores, which would fabricate a paired WIDE-information contrast.
        for left,right in (
            ("mid_WIN_persistence","WIN_mid_persistence"),
            ("mid_WIN_momentum","WIN_log_momentum"),
        ):
            av=A["candidate_predictions"][left]
            bv=B["fixed_next_quote_model_indices"][right]
            if (len(av)!=len(bv) or any(
                    (u["n"]!=v["n"] or not math.isclose(
                        u["p"],v["p"],rel_tol=0,abs_tol=1e-12))
                    for u,v in zip(av,bv))):
                raise ValueError("HOLD_DUAL_ORIGINAL_WIN_PRICE_VECTORS_NOT_IDENTICAL")
        AS=a_score["all_model_scores"]
        BS=b["model_score_TV_KL"]
        # Shared q0, qmid and q2 entail IDENTICAL zero-information
        # market baselines. If not, mismatched source content is being
        # passed off as a paired WIDE incremental-information experiment.
        for n1,n2 in (
            ("mid_WIN_persistence","WIN_mid_persistence"),
            ("mid_WIN_momentum","WIN_log_momentum"),
        ):
            if (not math.isclose(
                    AS[n1]["next_price_index_TV_pp"],
                    BS[n2]["target_price_index_TV_pp"],abs_tol=1e-8) or
                not math.isclose(
                    AS[n1]["next_price_index_KL_nats"],
                    BS[n2]["target_price_index_KL_nats"],abs_tol=1e-8)):
                raise ValueError("HOLD_DUAL_MARKET_BASELINE_OR_Q2_PROXY_MISMATCH")
        paired={
            "status":"PAIRED_SAME_WIN_q0_qMID_q2_WITH_WIDE_SIGNAL_LOCAL_ONLY",
            "single_actual_source_race_declared":1,
            "predeclared_lanes_are_NOT_independent_race_replicates":True,
            "lane_A_WIDE_benchmark_TV_pp":AS[
                "mid_WIN_momentum_plus_WIDE_node_beta025"][
                    "next_price_index_TV_pp"],
            "lane_B_without_WIDE_momentum_TV_pp":BS[
                "WIN_log_momentum"]["target_price_index_TV_pp"],
            "paired_difference_A_WIDE_minus_B_momentum_TV_pp":
                AS["mid_WIN_momentum_plus_WIDE_node_beta025"][
                    "next_price_index_TV_pp"]-
                BS["WIN_log_momentum"]["target_price_index_TV_pp"],
            "not_an_independent_precommitted_market_information_result":True,
        }
    return {
        "schema":SCHEMA,
        "status":STATUS,
        "race_id":card["race_id"],
        "registered_primary_slot_id":card["slot_id"],
        "scheduled_post_jst":card["scheduled_post_jst"],
        "operator_declared_source_rights_not_external_licensing_proof":
            card["rights_reviewed_by_operator"],
        "primary_grade_26_or_auxiliary_64":scope["primary_scope"],
        "possible_grade_auxiliary_overlap_not_double_counted":
            scope["possible_same_real_grade_auxiliary_race"],
        "lane_A_complete_WIDE_status":a_status,
        "lane_B_separate_WIN_only_status":b_status,
        "lane_A_locally_scored":bool(a_good),
        "lane_B_locally_scored":bool(b_good),
        "one_operator_declared_race_not_two":
            int(a_good or b_good),
        "within_race_A_B_paired_market_index_contrast":paired,
        "full_WIDE_absence_cannot_be_imputed_by_lane_B":True,
        "both_remote_SHA_receipts_must_be_separately_authenticated":True,
        "any_external_GitHub_SHA_proof_actually_verified_by_this_script":False,
        "actual_JRA_source_and_target_independently_authenticated":False,
        "new_independently_proven_prospective_market_trials":0,
        "horse_GPS_human_imitation_or_wager_EV":"HOLD",
    }


def cohort(reports):
    if not isinstance(reports,list) or not reports:
        raise ValueError("HOLD_NO_DUAL_LANE_RACE_REPORTS")
    unique=set()
    slots=set()
    days=set()
    countA=countB=paired=unique_scored=0
    missingA=missingB=0
    effects=[]
    for r in reports:
        if not isinstance(r,dict) or r.get("schema")!=SCHEMA:
            raise ValueError("HOLD_CHANGED_DUAL_LANE_REPORT_SCHEMA")
        rid=r["race_id"]
        slot=r["registered_primary_slot_id"]
        if rid in unique or slot in slots:
            raise ValueError("HOLD_DUPLICATE_JRA_PHYSICAL_RACE_OR_FIXED_SLOT")
        unique.add(rid)
        slots.add(slot)
        days.add(r["scheduled_post_jst"][:10])
        countA+=int(r["lane_A_locally_scored"])
        countB+=int(r["lane_B_locally_scored"])
        unique_scored+=int(r["one_operator_declared_race_not_two"])
        missingA+=int(not r["lane_A_locally_scored"])
        missingB+=int(not r["lane_B_locally_scored"])
        contrast=r["within_race_A_B_paired_market_index_contrast"]
        if contrast:
            paired+=1
            effects.append(contrast[
                "paired_difference_A_WIDE_minus_B_momentum_TV_pp"])
    return {
        "schema":COHORT_SCHEMA,
        "status":"LOCAL_DUAL_LANE_AVAILABILITY_COHORT_NOT_PROSPECTIVE",
        "registered_grade_denominator":26,
        "registered_auxiliary_denominator":64,
        "distinct_operator_declared_real_race_IDs":len(unique),
        "distinct_operator_declared_meeting_dates":len(days),
        "lane_A_full_WIDE_local_scores":countA,
        "lane_B_WIN_only_local_scores":countB,
        "lane_A_missing_or_unfrozen":missingA,
        "lane_B_missing_or_unfrozen":missingB,
        "same_q0_qmid_q2_paired_local_competitions":paired,
        "unique_locally_scored_races_NOT_sum_of_A_and_B":unique_scored,
        "mean_same_target_paired_A_WIDE_minus_B_no_WIDE_TV_pp":
            sum(effects)/len(effects) if effects else None,
        "not_independent_external_market_attestation":True,
        "externally_GitHub_SHA_proved_trials_in_THIS_report":0,
        "certified_independent_new_JRA_market_trials":0,
        "historical_Kikka_M0_M2_v31_untouched":True,
    }


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest="mode",required=True)
    a=s.add_parser("compare")
    a.add_argument("--ledger",required=True,type=Path)
    a.add_argument("--final-card",required=True,type=Path)
    a.add_argument("--as-of",default=None)
    a.add_argument("--A-complete-WIDE-bundle",type=Path)
    a.add_argument("--B-win-only-freeze",type=Path)
    a.add_argument("--private-output",required=True,type=Path)
    b=s.add_parser("cohort")
    b.add_argument("--reports",type=Path,required=True,nargs="+")
    b.add_argument("--private-output",required=True,type=Path)
    args=p.parse_args()
    if args.mode=="compare":
        obj=compare_once(
            args.ledger,_read(args.final_card),
            asof=args.as_of or datetime.now(JST).isoformat(),
            lane_A_bundle=(_read(args.A_complete_WIDE_bundle)
                           if args.A_complete_WIDE_bundle else None),
            lane_B_freeze=(_read(args.B_win_only_freeze)
                           if args.B_win_only_freeze else None))
    else:
        obj=cohort([_read(x) for x in args.reports])
    _write_new_private(args.private_output,obj)
    print(json.dumps({
        "status":obj["status"],
        "independently_verified_new_JRA_market_trials":0,
        "no_automated_market_collection_or_GitHub_POST":True,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
