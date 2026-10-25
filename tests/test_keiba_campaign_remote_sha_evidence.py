#!/usr/bin/env python3
"""A fake GitHub JSON blob is never independent server-timestamp evidence."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
if np is not None:
    import keiba_campaign_remote_sha_evidence as bridge
    import keiba_fixed_denominator_market_campaign as campaign
    import keiba_private_multirace_winwide_shadow as shadow
    from test_keiba_private_multirace_winwide_shadow import (
        source as source_template, as_bytes, target as target_template,
    )

SLOT="2026-10-31|京都|ファンタジーS"
RACE_ID="SYNTHETIC_JRA_2026_10_31"
ASOF="2026-10-31T16:00:00+09:00"
UNTIL="2026-10-25T23:18:00+09:00"


def sample():
    """Synthetic, explicitly NOT authentic future JRA capture."""
    doc=source_template()
    doc=json.loads(json.dumps(doc).replace(
        "2026-11-07","2026-10-31"))
    doc["race_id"]=RACE_ID
    doc["scheduled_post_jst"]="2026-10-31T15:40:00+09:00"
    doc["provider"]="SYNTHETIC_PROVIDER_NEVER_REAL_JRA"
    doc["provenance"]="authorized_private_local_export"
    doc["operator_confirmed_research_rights"]=True
    doc["horizon_minutes"]=15
    doc["target_window_minutes"]=5
    for x in ("first_win","middle_win","middle_wide"):
        doc[x]["provider"]=doc["provider"]
    frozen=shadow.freeze_source_bytes(as_bytes(doc),horse_draws=40,
                                       horse_seed=19)
    quote=target_template(doc,first_at="2026-10-31T11:15:00+09:00")
    scored=shadow.score_target(frozen,quote)
    meta={
        "schema":campaign.RECEIPT_SCHEMA,
        "entries":[{
            "slot_id":SLOT,
            "official_race_id":RACE_ID,
            "scheduled_post_jst":doc["scheduled_post_jst"],
            "racecard_source_url":"https://example.org/fictional-race-card",
            "racecard_received_at_jst":"2026-10-30T13:00:00+09:00",
            "quote_provider_name":doc["provider"],
            "source_rights_checked_locally":True,
            "capture_stage":"next_quote_local_scored",
            "local_frozen_model_sha256":
                frozen["seal_sha256_of_canonical_payload"],
            "target_horizon_minutes":15,
            "target_window_minutes":5,
        }],
    }
    proof={
        "status":bridge.STATUS_REMOTE,
        "external_sha_pre_target_verified":True,
        "independent_GitHub_API_fetch_performed":True,
        "race_id":RACE_ID,
        "sha256_of_full_private_frozen_model":
            frozen["seal_sha256_of_canonical_payload"],
        "race_post_at":doc["scheduled_post_jst"],
        "target_market_window_begins_at":
            frozen["payload"]["next_quote_min_published_at"],
        "github_server_comment_created_at_claim":
            "2026-10-31T11:10:00+09:00",
        "github_comment_id":12345,
        "github_comment_url":
            "https://github.com/zuizui0223/keiba/pull/22#issuecomment-12345",
    }
    return meta,frozen,scored,proof


@unittest.skipIf(np is None,"Dedicated numerical CI installs NumPy")
class RemoteCampaignProofIntegration(unittest.TestCase):
    def test_all_26_slots_preserved_without_private_future_files(self):
        without={"schema":campaign.RECEIPT_SCHEMA,"entries":[]}
        with patch.object(bridge,"verify_live",
                          side_effect=AssertionError("NO_API_FOR_EMPTY_LIST")):
            r=bridge.audit_live(asof=UNTIL,local_receipts=without)
        self.assertEqual(r["registered_flat_G1_G2_G3_slots_including_Kikka"],26)
        self.assertEqual(r["registered_next_price_candidate_slots_excluding_old_Kikka"],25)
        self.assertEqual(len(r["registered_slot_readiness"]),26)
        self.assertEqual(r["remotely_SHA_pre_next_price_verified_intervals"],0)
        self.assertEqual(r["locally_scored_next_price_intervals_unattested"],0)
        self.assertEqual(r["new_independent_real_prospective_quote_trials_confirmed"],0)
        self.assertEqual(r["registered_slot_readiness"][0]["capture_state"],
                         "PRIOR_KIKKA_OUTCOME_PRESEAL_UNVERIFIED_NOT_NEXT_MARKET")
        self.assertTrue(all(not z["external_SHA_creation_time_verified_by_this_campaign"]
                            for z in r["registered_slot_readiness"]))

    def test_fake_server_proof_tests_structural_mapping_only_not_real_evidence(self):
        meta,frozen,score,remote=sample()
        # Mock is confined to the unittest process. It is not an actual
        # GitHub GET or a newly authenticated future observation.
        with patch.object(bridge,"verify_live",return_value=remote) as fake:
            x=bridge.audit_live(asof=ASOF,local_receipts=meta,
                                private_scores=[score],
                                private_freezes=[frozen])
            fake.assert_called_once()
        self.assertEqual(x["registered_flat_G1_G2_G3_slots_including_Kikka"],26)
        self.assertEqual(x["remotely_SHA_pre_next_price_verified_intervals"],1)
        self.assertEqual(x["remotely_SHA_verified_and_locally_next_price_scored"],1)
        self.assertFalse(x["prospective_market_outcome_validation_certified"])
        self.assertEqual(x["new_independent_real_prospective_quote_trials_confirmed"],0)
        self.assertEqual(x["locally_scored_next_price_intervals_unattested"],1)
        self.assertFalse(x["real_market_criticality_horse_GPS_or_bettor_contagion"]!="HOLD")
        first=next(z for z in x["registered_slot_readiness"] if z["slot_id"]==SLOT)
        self.assertTrue(first["external_SHA_creation_time_verified_by_this_campaign"])
        self.assertEqual(first["github_sha_receipt"]["next_quote_target_capture_status"],
                         bridge.TARGET_SCORE_LOCAL)
        self.assertFalse(first["github_sha_receipt"][
            "private_source_receipt_independently_verified"])
        self.assertEqual(x["registered_slot_readiness"][0]["capture_state"],
                         "PRIOR_KIKKA_OUTCOME_PRESEAL_UNVERIFIED_NOT_NEXT_MARKET")

    def test_unverified_fixture_status_cannot_be_promoted(self):
        meta,frozen,score,remote=sample()
        for change in (
            {"status":"HOLD_OFFLINE_GITHUB_COMMENT_FIXTURE_NOT_SERVER_ATTESTATION"},
            {"external_sha_pre_target_verified":False},
            {"independent_GitHub_API_fetch_performed":False},
            {"sha256_of_full_private_frozen_model":"f"*64},
            {"race_id":"OTHER_RACE"},
            {"target_market_window_begins_at":"2026-10-31T11:16:00+09:00"},
            {"github_comment_id":None},
            {"github_server_comment_created_at_claim":"2026-10-31T17:00:00+09:00"},
        ):
            bad={**remote,**change}
            with self.subTest(change=change):
                with patch.object(bridge,"verify_live",return_value=bad):
                    with self.assertRaises(ValueError):
                        bridge.audit_live(
                            asof=ASOF,local_receipts=meta,
                            private_scores=[score],private_freezes=[frozen])

    def test_github_CLI_failure_fails_closed_without_partial_success(self):
        meta,frozen,score,remote=sample()
        with patch.object(bridge,"verify_live",side_effect=ValueError(
                "HOLD_CANNOT_FETCH_GITHUB_SERVER_COMMENTS_INDEPENDENTLY")):
            with self.assertRaisesRegex(ValueError,"CANNOT_FETCH_GITHUB"):
                bridge.audit_live(asof=ASOF,local_receipts=meta,
                                  private_scores=[score],
                                  private_freezes=[frozen])

    def test_registry_horizon_immutable_and_sha_mismatch_refused(self):
        meta,frozen,score,remote=sample()
        corrupt=copy.deepcopy(meta)
        corrupt["entries"][0]["local_frozen_model_sha256"]="0"*64
        with patch.object(bridge,"verify_live",return_value=remote):
            with self.assertRaisesRegex(ValueError,"SHA"):
                bridge.audit_live(asof=ASOF,local_receipts=corrupt,
                                  private_scores=[score],
                                  private_freezes=[frozen])
        corrupt=copy.deepcopy(meta)
        corrupt["entries"][0]["target_horizon_minutes"]=18
        with self.assertRaisesRegex(ValueError,"CHANGED_PREDECLARED"):
            bridge.audit_live(asof=ASOF,local_receipts=corrupt,
                              private_scores=[score],
                              private_freezes=[frozen])
        corrupt=copy.deepcopy(meta)
        corrupt["entries"][0]["scheduled_post_jst"]="2026-10-31T15:42:00+09:00"
        with patch.object(bridge,"verify_live",return_value=remote):
            with self.assertRaises(ValueError):
                bridge.audit_live(asof=ASOF,local_receipts=corrupt,
                                  private_freezes=[frozen])

    def test_original_2026_Kikka_cannot_enter_new_market_denominator(self):
        meta,frozen,score,remote=sample()
        changed=copy.deepcopy(meta)
        changed["entries"][0]["slot_id"]=campaign.EXPECTED_LEGACY_KIKKA
        with self.assertRaisesRegex(ValueError,"UNREGISTERED_DUPLICATE_OR_PAST"):
            bridge.audit_live(asof=ASOF,local_receipts=changed,
                              private_freezes=[frozen])

    def test_repeated_same_frozen_prediction_does_not_count_two_races(self):
        meta,frozen,score,remote=sample()
        with patch.object(bridge,"verify_live",return_value=remote):
            with self.assertRaisesRegex(ValueError,"SECOND_FROZEN_MODEL"):
                bridge.audit_live(asof=ASOF,local_receipts=meta,
                                  private_scores=[score],
                                  private_freezes=[frozen,copy.deepcopy(frozen)])

    def test_authorized_local_freeze_without_eligible_target_counts_proof_not_score(self):
        meta,frozen,score,remote=sample()
        original=copy.deepcopy(meta)
        original["entries"][0]["capture_stage"]="local_SHA_frozen"
        with patch.object(bridge,"verify_live",return_value=remote):
            x=bridge.audit_live(asof=ASOF,local_receipts=original,
                                private_freezes=[frozen])
        self.assertEqual(x["remotely_SHA_pre_next_price_verified_intervals"],1)
        self.assertEqual(x["remotely_SHA_verified_and_locally_next_price_scored"],0)
        self.assertEqual(x["new_independent_real_prospective_quote_trials_confirmed"],0)
        first=next(z for z in x["registered_slot_readiness"] if z["slot_id"]==SLOT)
        self.assertEqual(first["github_sha_receipt"]["next_quote_target_capture_status"],
                         "NEXT_PRICE_NOT_LOCALLY_SCORED")

    def test_target_published_before_pretended_commitment_must_fail(self):
        meta,frozen,score,remote=sample()
        postprice={**remote,
                   "github_server_comment_created_at_claim":
                        "2026-10-31T11:16:00+09:00"}
        with patch.object(bridge,"verify_live",return_value=postprice):
            with self.assertRaisesRegex(ValueError,"PUBLISHED_BEFORE_GITHUB"):
                bridge.audit_live(asof=ASOF,local_receipts=meta,
                                  private_scores=[score],private_freezes=[frozen])

    def test_future_asof_cannot_evaluate_receipt_just_to_increase_count(self):
        meta,frozen,score,remote=sample()
        with patch.object(bridge,"verify_live",return_value=remote):
            with self.assertRaisesRegex(ValueError,"RECEIVED_AFTER_ASOF"):
                bridge.audit_live(asof=UNTIL,local_receipts=meta,
                                  private_scores=[score],private_freezes=[frozen])


if __name__=="__main__":
    unittest.main()
