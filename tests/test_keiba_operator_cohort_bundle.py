#!/usr/bin/env python3
"""26/64 registered market slot with safe PR23 SHA-only manifest and q2 score.

Synthetic only. All test "authorized" records are fabricated local fixtures
and MUST NOT be submitted to the real PR22 GitHub comment thread.
"""
from __future__ import annotations

import copy
from hashlib import sha256
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

    def test_same_displayed_source_minute_with_distinct_seconds_is_accepted(self):
        # WIN and WIDE page updates can display the same minute while
        # their underlying publication seconds are NOT simultaneous.
        with tempfile.TemporaryDirectory() as t:
            ledger=Path(t)/"private"/"seconds"
            for original,at in self.sources:
                src=copy.deepcopy(original)
                if src["market"]=="win" and "T11:00:" in src["source_updated_at_jst"]:
                    src["source_updated_at_jst"]=DATE+"T11:00:04+09:00"
                if src["market"]=="wide":
                    src["source_updated_at_jst"]=DATE+"T11:00:39+09:00"
                op.append_capture(ledger,src,captured_at_jst=DATE+at+"+09:00")
            x=m.prepare_bundle(ledger,self.c,
                               frozen_at_jst=DATE+"T11:03:00+09:00",
                               horse_draws=40)
            p=x["freeze"]["payload"]
            self.assertEqual(p["middle_WIN_quote_published_at"],
                             DATE+"T11:00:04+09:00")
            self.assertEqual(p["middle_WIDE_quote_published_at"],
                             DATE+"T11:00:39+09:00")
            self.assertEqual(p["next_quote_min_published_at"],
                             DATE+"T11:15:04+09:00")
            self.assertFalse(x["external_GitHub_comment_created_at_verified"])

    def test_gh_precommit_sha_binds_all_original_capture_urls_and_final_card(self):
        bundle=self.prepare()
        freeze=bundle["freeze"]
        payload=freeze["payload"]
        lock=payload["operator_source_card_chain_binding"]
        self.assertEqual(lock["schema"],m.CAPTURE_BINDING_SCHEMA)
        self.assertEqual(lock["local_chain_prefix_length"],3)
        self.assertEqual(lock["private_capture_chain_prefix_sha256"],
                         op._read_ledger(self.ledger)[-1]["event_sha256"])
        self.assertEqual(lock["operator_final_card_sha256"],
                         sha256(op._dump(self.c).encode("utf-8")).hexdigest())
        self.assertEqual(lock["actual_horse_physics_distance_m"],1400)
        self.assertEqual(lock["final_runner_numbers"],list(range(1,7)))
        # The GitHub-public message contains ONLY the digest; that digest
        # covers the original source-chain head, full declared card and
        # physical horse model input, although not independent source proof.
        public=bundle["public_SHA_only_comment_not_posted"][
            "body_to_post_once_in_PR22_comment"]
        self.assertIn(freeze["seal_sha256_of_canonical_payload"],public)
        self.assertNotIn(lock["private_capture_chain_prefix_sha256"],public)
        self.assertNotIn(self.c["source_card_url"],public)
        self.assertEqual(
            freeze["SHA_only_existing_dispatch_inputs_NOT_SENT"]["seal_sha256"],
            freeze["seal_sha256_of_canonical_payload"])

    def test_final_card_distance_horse_identity_or_url_cannot_change_postfreeze(self):
        bundle=self.prepare()
        self.add_future(17)
        for field,value in (
            ("race_distance_m",1800),
            ("horse_numbers",[1,2,3,4,5,7]),
            ("source_card_url","https://example.org/another-card"),
            ("slot_id","2026-10-31|京都|R11"),
        ):
            with self.subTest(field=field):
                altered=copy.deepcopy(bundle)
                altered["card"][field]=value
                with self.assertRaisesRegex(
                        ValueError,"CARD_CHAIN_AND_PHYSICAL_MODEL_NOT_SAME_SEAL"):
                    m.score_bundle(altered,self.ledger,
                                   asof=DATE+"T11:21:00+09:00",
                                   operator_confirms_complete=True)

    def test_physical_distance_and_source_card_digest_change_public_sha(self):
        left=self.prepare()
        other=copy.deepcopy(self.c)
        other["race_distance_m"]=1800
        right=self.prepare(card_override=other)
        self.assertNotEqual(
            left["freeze"]["seal_sha256_of_canonical_payload"],
            right["freeze"]["seal_sha256_of_canonical_payload"])
        self.assertNotEqual(
            left["freeze"]["payload"]["operator_source_card_chain_binding"][
                "operator_final_card_sha256"],
            right["freeze"]["payload"]["operator_source_card_chain_binding"][
                "operator_final_card_sha256"])
        self.assertEqual(
            left["registered_cohort"]["primary_slot_id"],
            right["registered_cohort"]["primary_slot_id"])

    def test_replacing_complete_local_event_chain_is_detected_by_frozen_source_sha(self):
        from keiba_operator_winwide_capture import _read_ledger
        orig=self.prepare()
        before=_read_ledger(self.ledger)
        # Deliberately rewrite ENTIRE LOCAL chain to be self-consistent.
        # Ordinary file-hash validation passes, but the PREVIOUSLY frozen
        # SHA still binds the ORIGINAL head and must reject new provenance.
        altered=copy.deepcopy(before)
        altered[0]["captured_source"]["odds_by_horse_number"]["1"]=91.
        old=list(self.ledger.glob("*.json"))
        for file in old:
            file.unlink()
        prev="0"*64
        for ix,e in enumerate(altered,1):
            e["previous_event_sha256"]=prev
            e["event_sha256"]=op._sha({k:v for k,v in e.items()
                                      if k!="event_sha256"})
            fn=self.ledger/f"{ix:06d}-{e['event_sha256'][:12]}.json"
            fn.write_text(json.dumps(e,ensure_ascii=False,indent=2)+"\n",
                          encoding="utf-8")
            prev=e["event_sha256"]
        self.assertEqual(len(_read_ledger(self.ledger)),3)
        self.add_future(17)
        with self.assertRaisesRegex(ValueError,"EARLY_CAPTURE_SOURCE_CHAIN_CHANGED"):
            m.score_bundle(orig,self.ledger,
                           asof=DATE+"T11:21:00+09:00",
                           operator_confirms_complete=True)

    def test_pretarget_intermediate_win_received_before_freeze_not_scored_as_future(self):
        # One full WIN update can occur between selected middle WIN/WIDE
        # and local freeze. It is NOT a future observation and must not
        # make postfreeze scoring fail because received < freeze clock.
        v=win(11,1,scale=1.15)
        v["provenance"]="authorized_private_local_export"
        v["rights_reviewed_by_operator"]=True
        op.append_capture(self.ledger,v,
                          captured_at_jst=DATE+"T11:02:30+09:00")
        orig=self.prepare()
        self.assertEqual(orig["capture_ledger_prefix_events"],4)
        self.add_future(17)
        scored=m.score_bundle(orig,self.ledger,
                              asof=DATE+"T11:21:00+09:00",
                              operator_confirms_complete=True)
        self.assertEqual(scored["local_market_score"]["status"],m.SCORE_STATUS)
        self.assertEqual(scored["cohort_audit"]["local_candidate_price_scores"],1)
        self.assertTrue(scored["frozen_input_capture_chain_prefix_unchanged"])

    def test_core_aux_same_actual_race_id_cannot_be_counted_twice(self):
        grade=self.prepare()
        aux_card=copy.deepcopy(self.c)
        aux_card["slot_id"]="2026-10-31|京都|R11"
        aux=self.prepare(card_override=aux_card)
        self.assertNotEqual(
            grade["freeze"]["seal_sha256_of_canonical_payload"],
            aux["freeze"]["seal_sha256_of_canonical_payload"])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_PHYSICAL_RACE_ID"):
            m.audit_distinct_private_bundles([grade,aux])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_PHYSICAL_RACE_ID"):
            m.audit_distinct_private_bundles([grade,copy.deepcopy(grade)])
        single=m.audit_distinct_private_bundles([grade])
        self.assertEqual(single["distinct_operator_declared_race_ids"],1)
        self.assertEqual(single["registered_grade_denominator_preserved"],26)
        self.assertEqual(single["registered_auxiliary_numbered_slot_denominator_preserved"],64)
        self.assertEqual(single["possible_grade_auxiliary_overlaps_to_check_with_real_ids"],1)
        self.assertEqual(single["independently_authenticated_next_market_capture_trials"],0)

    def test_mutated_public_sha_only_comment_body_is_not_valid_for_next_market_score(self):
        original=self.prepare()
        self.add_future(17)
        b=copy.deepcopy(original)
        b["public_SHA_only_comment_not_posted"]["body_to_post_once_in_PR22_comment"]+=(
            "\\nAN_UNDISCLOSED_DIFFERENT_PREDICTION")
        with self.assertRaisesRegex(ValueError,"PUBLIC_SHA_COMMENT_BODY_NOT_SAME"):
            m.score_bundle(b,self.ledger,
                           asof=DATE+"T11:21:00+09:00",
                           operator_confirms_complete=True)
        with self.assertRaisesRegex(ValueError,"PUBLIC_SHA_COMMENT_BODY_NOT_SAME"):
            m.audit_distinct_private_bundles([b])

    def test_bundle_cannot_self_claim_external_SHA_attestation(self):
        b=self.prepare()
        b["external_GitHub_comment_created_at_verified"]=True
        with self.assertRaisesRegex(ValueError,"FALSELY_CLAIMS_EXTERNAL_PROOF"):
            m.audit_distinct_private_bundles([b])
        with self.assertRaisesRegex(ValueError,"FALSELY_CLAIMS_EXTERNAL_PROOF"):
            m.score_bundle(b,self.ledger,
                           asof=DATE+"T11:21:00+09:00",
                           operator_confirms_complete=True)

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
        with self.assertRaisesRegex(ValueError,"ORIGINAL_KIKKA"):
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
