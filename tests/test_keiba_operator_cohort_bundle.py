#!/usr/bin/env python3
"""26/64 registered market slot with safe PR23 SHA-only manifest and q2 score.

Synthetic only. All test "authorized" records are fabricated local fixtures
and MUST NOT be submitted to the real PR22 GitHub comment thread.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
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
    import keiba_operator_cohort_bundle as m
    import keiba_operator_winwide_capture as op
    from test_keiba_operator_winwide_capture import card,win,wide,DATE


@unittest.skipIf(np is None,"The same numerical PR17/PR19 environment must exist")
class SyntheticCaptureToCampaignIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger=Path(self.temp.name)/"private"/"event_chain"
        self.c=card()
        self.c["provenance"]="authorized_private_local_export"
        self.c["rights_reviewed_by_operator"]=True
        self.sources=[]
        for d,t in (
            (win(10),"T10:02:00"),
            (win(11,scale=1.1),"T11:01:00"),
            (wide(),"T11:02:00"),
        ):
            d["provenance"]="authorized_private_local_export"
            d["rights_reviewed_by_operator"]=True
            self.sources.append((d,t))
        for d,t in self.sources:
            op.append_capture(self.ledger,d,
                              captured_at_jst=DATE+t+"+09:00")

    def prepare(self,*,card_override=None):
        return m.prepare_bundle(self.ledger,card_override or self.c,
                                frozen_at_jst=DATE+"T11:03:00+09:00",
                                horse_draws=45,seed=20261026)

    def add_future(self,minute=17):
        v=win(11,minute,scale=1.2)
        v["provenance"]="authorized_private_local_export"
        v["rights_reviewed_by_operator"]=True
        op.append_capture(self.ledger,v,
                          captured_at_jst=DATE+f"T11:{minute+1:02d}:00+09:00")

    def test_one_command_freezes_same_12_models_and_sha_only_safe_comment(self):
        x=self.prepare()
        self.assertEqual(x["schema"],m.BUNDLE_SCHEMA)
        self.assertEqual(x["status"],m.BUNDLE_STATUS)
        self.assertEqual(len(x["freeze"]["payload"]["candidate_predictions"]),12)
        self.assertEqual(x["registered_cohort"]["primary_scope"],
                         "FROZEN_GRADED_26_PRIMARY")
        self.assertTrue(x["registered_cohort"][
            "possible_same_real_grade_auxiliary_race"])
        self.assertEqual(x["capture_ledger_prefix_events"],3)
        self.assertEqual(x["capture_ledger_prefix_head_SHA256"],
                         op._read_ledger(self.ledger)[2]["event_sha256"])
        safe=x["public_SHA_only_comment_not_posted"]
        self.assertEqual(safe["status"],"PREPARED_PUBLIC_SHA_ONLY_COMMENT_NOT_POSTED")
        self.assertFalse(safe["remote_sha_publication_confirmed"])
        body=safe["body_to_post_once_in_PR22_comment"]
        self.assertIn(x["freeze"]["seal_sha256_of_canonical_payload"],body)
        self.assertNotIn("odds_by_horse_number",body)
        self.assertFalse(x["external_GitHub_comment_created_at_verified"])
        self.assertFalse(x["genuinely_prospective_market_trial_counted"])

    def test_later_winner_or_quote_cannot_rewrite_frozen_sha(self):
        x=self.prepare()
        old=x["freeze"]["seal_sha256_of_canonical_payload"]
        self.add_future(17)
        self.assertEqual(x["freeze"]["seal_sha256_of_canonical_payload"],old)
        out=m.score_bundle(x,self.ledger,
                           asof=DATE+"T11:21:00+09:00",
                           operator_confirms_complete=True)
        self.assertEqual(out["schema"],m.BUNDLE_SCORED_SCHEMA)
        self.assertEqual(out["status"],m.SCORE_STATUS_LOCAL)
        self.assertEqual(out["original_freeze_SHA256"],old)
        self.assertEqual(out["local_market_score"]["status"],m.SCORE_STATUS)
        self.assertTrue(out["frozen_input_capture_chain_prefix_unchanged"])
        self.assertEqual(out["cohort_audit"]["original_fixed_denominator"],26)
        self.assertEqual(out["cohort_audit"]["local_candidate_price_scores"],1)
        self.assertEqual(out["new_independent_real_prospective_quote_trials_confirmed"],0)
        self.assertEqual(out["private_PR24_updated_metadata_receipt"][
            "entries"][0]["capture_stage"],"next_quote_local_scored")

    def test_missing_target_before_window_or_before_race_cannot_be_finalized(self):
        x=self.prepare()
        with self.assertRaisesRegex(ValueError,"TARGET_WINDOW_NOT_YET_CLOSED"):
            m.score_bundle(x,self.ledger,asof=DATE+"T11:17:00+09:00",
                           operator_confirms_complete=True)
        with self.assertRaisesRegex(ValueError,"NO_FINAL_MISSING_TARGET"):
            m.score_bundle(x,self.ledger,asof=DATE+"T11:30:00+09:00",
                           operator_confirms_complete=True)
        final=m.score_bundle(x,self.ledger,
                             asof=DATE+"T15:46:00+09:00",
                             operator_confirms_complete=True)
        self.assertEqual(final["status"],
                         "HOLD_NO_QUOTE_IN_LOCKED_NEXT_MARKET_WINDOW")
        self.assertEqual(final["cohort_audit"]["locally_missing_window_slots"],1)
        self.assertEqual(final["new_independent_real_prospective_quote_trials_confirmed"],0)

    def test_late_outside_window_quote_is_explicit_missing_not_selected(self):
        frozen=self.prepare()
        self.add_future(24)
        with self.assertRaisesRegex(ValueError,"NO_FINAL_MISSING_TARGET"):
            m.score_bundle(frozen,self.ledger,
                           asof=DATE+"T11:26:00+09:00",
                           operator_confirms_complete=True)
        after=m.score_bundle(frozen,self.ledger,
                             asof=DATE+"T15:46:00+09:00",
                             operator_confirms_complete=True)
        self.assertEqual(after["status"],
                         "HOLD_NO_QUOTE_IN_LOCKED_NEXT_MARKET_WINDOW")

    def test_additional_future_source_can_not_hide_pre_freeze_source_changes(self):
        x=self.prepare()
        self.add_future(17)
        first=sorted(self.ledger.glob("*.json"))[0]
        obj=json.loads(first.read_text(encoding="utf-8"))
        obj["captured_source"]["odds_by_horse_number"]["1"]=999.
        first.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"HASH_OR_FILENAME"):
            m.score_bundle(x,self.ledger,
                           asof=DATE+"T11:25:00+09:00",
                           operator_confirms_complete=True)

    def test_no_self_attested_GitHub_proof_claim_in_operator_bundle(self):
        x=self.prepare()
        self.add_future(17)
        out=m.score_bundle(x,self.ledger,
                           asof=DATE+"T11:21:00+09:00",
                           operator_confirms_complete=True)
        self.assertFalse(out["independent_GitHub_SHA_pretarget_proof"])
        self.assertFalse(out["source_and_later_target_independently_complete"])
        self.assertFalse(out["actual_horse_win_proper_score_or_betting_return_computed"])
        self.assertTrue(out["cohort_audit"][
            "possible_grade_auxiliary_overlap"])

    def test_unregistered_card_banned_even_with_full_valid_market(self):
        c=copy.deepcopy(self.c)
        c["slot_id"]="2026-10-31|東京|R10"
        with self.assertRaises(ValueError):
            self.prepare(card_override=c)

    def test_auxiliary_numbered_slot_is_never_forged_into_graded_26(self):
        c=copy.deepcopy(self.c)
        c["slot_id"]="2026-10-31|京都|R11"
        x=self.prepare(card_override=c)
        self.assertEqual(x["registered_cohort"]["primary_scope"],
                         "FROZEN_AUXILIARY_64_PRIMARY")
        self.add_future(17)
        z=m.score_bundle(x,self.ledger,
                         asof=DATE+"T11:21:00+09:00",
                         operator_confirms_complete=True)
        self.assertEqual(z["cohort_audit"]["scope"],"auxiliary_64")
        self.assertEqual(z["cohort_audit"]["original_fixed_denominator"],64)
        self.assertTrue(z["cohort_audit"]["possible_grade_auxiliary_overlap"])
        self.assertTrue(z["cohort_audit"]["graded_registry_26_unchanged"])
        self.assertEqual(z["new_independent_real_prospective_quote_trials_confirmed"],0)

    def test_original_Kikka_graded_slot_is_not_next_market_candidate(self):
        c=copy.deepcopy(self.c)
        c["slot_id"]=m.EXPECTED_LEGACY_KIKKA
        with self.assertRaisesRegex(ValueError,"NOT_REGISTERED"):
            self.prepare(card_override=c)

    def test_operator_without_rights_can_replay_synthetic_but_not_submit_GitHub(self):
        with tempfile.TemporaryDirectory() as t:
            another=Path(t)/"private"/"mock"
            for d,timestamp in (
                (win(10),"T10:02:00"),
                (win(11,scale=1.1),"T11:01:00"),
                (wide(),"T11:02:00"),
            ):
                op.append_capture(another,d,captured_at_jst=DATE+timestamp+"+09:00")
            x=m.prepare_bundle(another,card(),
                               frozen_at_jst=DATE+"T11:03:00+09:00",
                               horse_draws=40)
        self.assertIsNone(x["public_SHA_only_comment_not_posted"])
        self.assertFalse(x["external_GitHub_comment_created_at_verified"])
        self.assertFalse(x["genuinely_prospective_market_trial_counted"])

    def test_replacing_bundle_sha_before_score_fails_closed(self):
        x=self.prepare()
        x["private_PR24_metadata_receipt"]["entries"][0][
            "local_frozen_model_sha256"]="f"*64
        self.add_future(17)
        with self.assertRaisesRegex(ValueError,"METADATA_OR_SOURCE_SHA_MODIFIED"):
            m.score_bundle(x,self.ledger,
                           asof=DATE+"T11:21:00+09:00",
                           operator_confirms_complete=True)


if __name__=="__main__":
    unittest.main()
