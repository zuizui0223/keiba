#!/usr/bin/env python3
"""WIN-only parallel lane, separate from original complete-WIDE 12 models."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
if np is not None:
    import keiba_win_only_shadow_lane as m
    import keiba_operator_winwide_capture as capture
    from test_keiba_operator_winwide_capture import card,win,wide,DATE


@unittest.skipIf(np is None,"Numerical horse agents require NumPy")
class SeparateWINOnlyFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger=Path(self.tmp.name)/"private"/"event_chain"
        self.card=card()

    def write(self,source,when):
        return capture.append_capture(
            self.ledger,source,captured_at_jst=DATE+when+"+09:00")

    def two_WIN(self):
        self.write(win(10),"T10:02:00")
        self.write(win(11,scale=1.1),"T11:01:00")

    def frozen(self):
        return m.prepare_win_only(
            self.ledger,self.card,frozen_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=55,seed=33)

    def next_WIN(self,*,minute=17):
        self.write(win(11,minute,scale=1.2),
                   f"T11:{minute+1:02d}:00")

    def test_no_WIDE_still_generates_six_source_locked_market_candidates(self):
        self.two_WIN()
        f=self.frozen()
        p=m.verify_win_only(f)
        self.assertEqual(p["schema"],m.SCHEMA)
        self.assertEqual(p["research_lane"],
                         "SECONDARY_SEPARATE_WIN_ONLY_NOT_FULL_WIDE")
        self.assertEqual(set(p["fixed_next_quote_model_indices"]),
                         set(m.MODEL_NAMES))
        self.assertEqual(p["horse_numbers"],list(range(1,7)))
        self.assertEqual(p["target_WIN_window_start"],
                         DATE+"T11:15:00+09:00")
        self.assertEqual(p["target_WIN_window_end"],
                         DATE+"T11:20:00+09:00")
        self.assertFalse(p["full_WIDE_grid_used_as_signal"])
        self.assertFalse(p["past_horse_records_independent_asof_available"])
        self.assertFalse(f["external_GitHub_comment_created_at_verified"])
        self.assertEqual(
            p["original_local_capture_chain_prefix_SHA256"],
            capture._read_ledger(self.ledger)[-1]["event_sha256"])
        self.assertEqual(
            set(p["model_code_content_SHA256"]),set(m.CODE_FILES))
        for label,vector in p["fixed_next_quote_model_indices"].items():
            self.assertEqual([r["n"] for r in vector],list(range(1,7)))
            self.assertAlmostEqual(sum(r["p"] for r in vector),1,places=11,
                                   msg=label)

    def test_complete_WIDE_requirement_in_old_study_is_not_diluted(self):
        self.two_WIN()
        with self.assertRaisesRegex(ValueError,"NO_SAME_SOURCE_MINUTE"):
            capture.prepare_feature_from_ledger(
                self.ledger,self.card,
                freeze_at_jst=DATE+"T11:03:00+09:00")
        # A partial WIDE list is accepted as a raw local record but
        # MUST NOT be fabricated into the 15-pair complete-graph source.
        w=wide()
        w["pairs"].pop()
        self.write(w,"T11:02:00")
        f=self.frozen()
        self.assertFalse(f["payload"]["full_WIDE_grid_used_as_signal"])
        with self.assertRaisesRegex(ValueError,"NOT_ALL_PAIRS"):
            capture.prepare_feature_from_ledger(
                self.ledger,self.card,
                freeze_at_jst=DATE+"T11:03:00+09:00")

    def test_separate_later_quote_scored_without_github_or_horse_podium(self):
        self.two_WIN()
        f=self.frozen()
        earlier_sha=f["seal_sha256_of_canonical_payload"]
        self.next_WIN()
        out=m.score_win_only(
            self.ledger,self.card,f,asof=DATE+"T11:21:00+09:00",
            operator_declares_capture_complete=True)
        self.assertEqual(out["status"],m.SCORE_STATUS)
        self.assertEqual(out["source_target_published"],
                         DATE+"T11:17:00+09:00")
        self.assertEqual(out["local_frozen_model_sha256"],earlier_sha)
        self.assertEqual(len(out["model_score_TV_KL"]),6)
        self.assertFalse(out["new_independently_proven_next_market_trial"])
        for v in out["model_score_TV_KL"].values():
            self.assertTrue(v["target_price_index_TV_pp"]>=0)
            self.assertTrue(v["target_price_index_KL_nats"]>=-1e-12)

    def test_missing_target_stays_missing_after_post_not_imputed(self):
        self.two_WIN()
        f=self.frozen()
        with self.assertRaisesRegex(ValueError,"WINDOW_NOT_CLOSED"):
            m.score_win_only(
                self.ledger,self.card,f,asof=DATE+"T11:17:00+09:00",
                operator_declares_capture_complete=True)
        with self.assertRaisesRegex(ValueError,"NO_FINAL_MISSING"):
            m.score_win_only(
                self.ledger,self.card,f,asof=DATE+"T11:25:00+09:00",
                operator_declares_capture_complete=True)
        self.next_WIN(minute=24)
        outcome=m.score_win_only(
            self.ledger,self.card,f,asof=DATE+"T15:46:00+09:00",
            operator_declares_capture_complete=True)
        self.assertEqual(outcome["status"],m.MISSING)
        self.assertTrue(outcome["outcome_missing_but_slot_retained"])
        self.assertFalse(outcome["new_independently_proven_next_market_trial"])

    def test_changed_card_physical_distance_and_entire_chain_are_rejected(self):
        self.two_WIN()
        f=self.frozen()
        self.next_WIN()
        for key,value in (
            ("race_distance_m",1800),
            ("slot_id","2026-10-31|京都|R11"),
            ("source_card_url","https://example.org/testing/altered"),
            ("horse_numbers",[1,2,3,4,5,7]),
        ):
            altered=copy.deepcopy(self.card)
            altered[key]=value
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,"CHANGED_FINAL_CARD"):
                    m.score_win_only(
                        self.ledger,altered,f,
                        asof=DATE+"T11:21:00+09:00",
                        operator_declares_capture_complete=True)
        first=sorted(self.ledger.glob("*.json"))[0]
        before=json.loads(first.read_text(encoding="utf-8"))
        before["captured_source"]["odds_by_horse_number"]["1"]=123.
        first.write_text(json.dumps(before),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"HASH_OR_FILENAME"):
            m.score_win_only(
                self.ledger,self.card,f,
                asof=DATE+"T11:21:00+09:00",
                operator_declares_capture_complete=True)

    def test_changed_frozen_market_forecast_or_code_fingerprint_rejected(self):
        self.two_WIN()
        f=self.frozen()
        corrupted=copy.deepcopy(f)
        corrupted["payload"]["fixed_next_quote_model_indices"][
            "WIN_mid_persistence"][0]["p"]+=.10
        with self.assertRaisesRegex(ValueError,"SHA_OR_SCHEMA"):
            m.verify_win_only(corrupted)
        corrupted=copy.deepcopy(f)
        corrupted["payload"]["model_code_content_SHA256"][
            m.CODE_FILES[0]]="f"*64
        # Rehashing the prediction document alone does not grant rights to
        # retrofit the model code after the prior hash was published.
        from odds_shadow_freeze_score import _seal
        corrupted["seal_sha256_of_canonical_payload"]=_seal(
            corrupted["payload"])
        self.next_WIN()
        with self.assertRaisesRegex(ValueError,"MODEL_CODE_CHANGED"):
            m.score_win_only(
                self.ledger,self.card,corrupted,
                asof=DATE+"T11:21:00+09:00",
                operator_declares_capture_complete=True)

    def test_target_after_freeze_and_exact_first_eligible_source_update(self):
        self.two_WIN()
        f=self.frozen()
        # This is in the frozen +15..20 min window.
        self.next_WIN(minute=18)
        self.next_WIN(minute=19)
        r=m.score_win_only(
            self.ledger,self.card,f,
            asof=DATE+"T11:22:00+09:00",
            operator_declares_capture_complete=True)
        self.assertEqual(r["source_target_published"],
                         DATE+"T11:18:00+09:00")

    def test_no_winner_payout_leak_and_incomplete_runner_hard_stop(self):
        self.two_WIN()
        with self.assertRaisesRegex(ValueError,"FUTURE"):
            fake=win(11,scale=1.2)
            fake["true_finisher"]=3
            self.write(fake,"T11:02:00")
        path=self.ledger
        self.assertEqual(len(capture._read_ledger(path)),2)
        bad=win(11,minute=17,scale=1.2)
        bad["odds_by_horse_number"].pop("1")
        self.write(bad,"T11:18:00")
        # The honest source card cannot be silently matched to an
        # incomplete full-field quote even if missing a single runner.
        with self.assertRaisesRegex(ValueError,"HORSE_FIELD_INCOMPLETE"):
            m.score_win_only(
                self.ledger,self.card,self.frozen(),
                asof=DATE+"T11:21:00+09:00",
                operator_declares_capture_complete=True)

    def test_no_false_remote_or_silent_model_improvement_claim(self):
        self.two_WIN()
        f=self.frozen()
        f["external_GitHub_comment_created_at_verified"]=True
        with self.assertRaisesRegex(ValueError,"CANNOT_SELF_ASSERT_REMOTE"):
            m.verify_win_only(f)


if __name__=="__main__":
    unittest.main()
