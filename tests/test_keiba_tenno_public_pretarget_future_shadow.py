#!/usr/bin/env python3
"""News-only Oct31 freeze, fixed Nov1 future q2: synthetic target tests only."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
try:
    import numpy as np
except ModuleNotFoundError:
    np=None
if np is not None:
    import keiba_tenno_public_pretarget_future_shadow as m
    import keiba_operator_winwide_capture as cap


@unittest.skipIf(np is None,"Parent original price-field module requires NumPy")
class TennoPublicNewsFutureFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if np is not None:
            cls.frozen=m.freeze()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger=Path(self.temp.name)/"private"/"manual"
        self.card={
            "schema":cap.CARD_SCHEMA,
            "slot_id":m.SLOT,
            "race_id":"TEST_ONLY_TENNO_20261101_11",
            "provider":m.TARGET_PROVIDER,
            "race_number":11,
            "scheduled_post_jst":m.POST,
            "race_distance_m":2000,
            "horse_numbers":list(range(1,18)),
            "source_card_url":"https://example.org/synthetic/card",
            "source_card_published_at_jst":
                "2026-10-29T14:03:00+09:00",
            "source_card_received_at_jst":
                "2026-10-31T20:00:00+09:00",
            "declared_final_entrant_list":True,
            "rights_reviewed_by_operator":False,
            "provenance":"synthetic_test",
        }

    def write(self,minutes="14:49",*,price_factor=1.,missing=None,
              timestamp="14:48"):
        original={x["n"]:x["displayed_WIN_odds"] for x in
                  self.frozen["payload"]["17_full_public_article_reported_odds"]}
        prices={str(i):float(original[i]*(1+price_factor*(i-9)*.002))
                for i in original if i!=missing}
        source={
            "schema":cap.CAPTURE_SCHEMA,
            "race_id":self.card["race_id"],
            "provider":m.TARGET_PROVIDER,
            "market":"win",
            "source_updated_at_jst":
                "2026-11-01T"+timestamp+":00+09:00",
            "source_url":"https://example.org/synthetic/authorized-feed",
            "source_clock_declared_verified":True,
            "rights_reviewed_by_operator":False,
            "provenance":"synthetic_test",
            "odds_by_horse_number":prices,
        }
        return cap.append_capture(
            self.ledger,source,
            captured_at_jst="2026-11-01T"+minutes+":00+09:00")

    def score(self,at="2026-11-01T15:11:00+09:00",confirmed=True,
              card=None,frozen=None):
        return m.score_local(self.ledger,card or self.card,
                             frozen or self.frozen,
                             asof=at,operator_confirms_full_capture=confirmed)

    def test_news_field_four_models_exact_17_positive_not_true_probabilities(self):
        p=m.verify_freeze(self.frozen)
        self.assertEqual(len(p["17_full_public_article_reported_odds"]),17)
        self.assertEqual(p["17_full_public_article_reported_odds"][6]["n"],7)
        self.assertEqual(p["17_full_public_article_reported_odds"][6][
            "displayed_WIN_odds"],2.4)
        self.assertEqual(p["17_full_public_article_reported_odds"][0][
            "displayed_WIN_odds"],2.5)
        self.assertEqual(p["model_universe_predeclared"],list(m.MODEL_NAMES))
        self.assertEqual(p["source_identical_18h_editorial_manifest_sha256_not_vendor"],
            "3b8fc4798664a090963d5e8221029643cf9205934ba7fe7db0cc37a8d1f6e37b")
        self.assertTrue(p["different_public_news_vs_later_licensed_provider"])
        self.assertTrue(p["PR30_PR37_11_physically_coupled_models_NOT_promoted_or_altered"])
        self.assertFalse(self.frozen["external_GitHub_public_SHA_comment_verified"])
        self.assertEqual(set(p["code_file_content_sha256"]),set(m.CODE_FILES))
        for rows in p["frozen_price_index_forecasts"].values():
            self.assertEqual([x["n"] for x in rows],list(range(1,18)))
            self.assertAlmostEqual(sum(x["p"] for x in rows),1,places=12)

    def test_freeze_is_deterministic_and_target_never_loaded(self):
        with patch.object(m,"_read_ledger",
                          side_effect=AssertionError("TARGET_LEAK_IN_FREEZE")):
            a=m.freeze()
        self.assertEqual(a,self.frozen)
        self.assertEqual(m._sha(a["payload"]),
                         a["sha256_of_canonical_frozen_payload"])
        self.assertEqual(a["payload"]["target_source_update_window_start_jst"],
                         "2026-11-01T14:45:00+09:00")
        self.assertEqual(a["payload"]["target_source_update_window_end_jst"],
                         "2026-11-01T15:05:00+09:00")
        self.assertEqual(a["payload"]["target_local_receipt_cutoff_jst"],
                         "2026-11-01T15:15:00+09:00")

    def test_no_cherry_pick_target_and_same_source_horse_roster(self):
        self.write(timestamp="14:48",minutes="14:49",price_factor=1.)
        self.write(timestamp="14:50",minutes="14:51",price_factor=15.)
        result=self.score()
        self.assertEqual(result["status"],m.SCORED_STATUS)
        self.assertEqual(result["selected_first_eligible_full_WIN_published"],
                         "2026-11-01T14:48:00+09:00")
        self.assertTrue(result["one_market_target_for_all_four_models"])
        self.assertEqual(result["observed_eligible_next_win_targets"],1)
        self.assertEqual(set(result[
            "target_price_index_TV_KL_by_all_four_fixed_models"]),
            set(m.MODEL_NAMES))
        self.assertFalse(result["new_independently_verified_JRA_market_trial"])
        self.assertTrue(result[
            "full_target_stream_completeness_claim_not_independently_verified"])
        for score in result[
                "target_price_index_TV_KL_by_all_four_fixed_models"].values():
            self.assertGreaterEqual(score["full_17_relative_display_WIN_TV_pp"],0)
            self.assertGreaterEqual(score[
                "next_display_quote_index_KL_nats"],-1e-11)

    def test_missing_future_target_stays_hold_and_cannot_be_scored_early(self):
        with self.assertRaisesRegex(ValueError,"WINDOW_NOT_CLOSED"):
            self.score(at="2026-11-01T15:04:00+09:00")
        with self.assertRaisesRegex(ValueError,
                                    "FINAL_STATUS_BEFORE_POST"):
            self.score()
        out=self.score(at="2026-11-01T15:41:00+09:00")
        self.assertEqual(out["status"],m.MISSING_STATUS)
        self.assertEqual(out["observed_eligible_next_win_targets"],0)
        self.assertTrue(out["target_missing_not_zero_price_error"])
        self.assertFalse(out["new_independently_verified_JRA_market_trial"])

    def test_incomplete_17_runner_target_does_not_select_later_good_one(self):
        self.write(timestamp="14:47",minutes="14:48",missing=2)
        self.write(timestamp="14:50",minutes="14:51")
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_NEWS_TARGET_INCOMPLETE_WIN_FIELD"):
            self.score()

    def test_target_publication_outside_window_missing_no_substitution(self):
        self.write(timestamp="14:42",minutes="14:43")
        self.write(timestamp="15:06",minutes="15:07",price_factor=0.4)
        out=self.score(at="2026-11-01T15:41:00+09:00")
        self.assertEqual(out["status"],m.MISSING_STATUS)

    def test_source_after_cutoff_is_rejected(self):
        self.write(timestamp="14:49",minutes="15:16")
        with self.assertRaisesRegex(ValueError,"AFTER_LOCKED_CUTOFF"):
            self.score(at="2026-11-01T15:18:00+09:00")

    def test_wrong_official_card_or_provider_stays_hold(self):
        self.write()
        for key,value in (
            ("slot_id","2026-10-31|京都|ファンタジーS"),
            ("race_number",10),
            ("race_distance_m",1800),
            ("horse_numbers",list(range(1,17))),
            ("provider","OTHER_JRA_PUBLIC_NEWS"),
        ):
            bad=copy.deepcopy(self.card)
            bad[key]=value
            with self.subTest(key=key):
                with self.assertRaisesRegex(ValueError,
                                            "CARD_DATE_VS_REGISTERED_SLOT|CARD_SLOT_FIELD_SOURCE_MISMATCH"):
                    self.score(card=bad)

    def test_unconfirmed_provider_stream_and_wrong_received_time_hold(self):
        self.write()
        with self.assertRaisesRegex(ValueError,
                                    "COMPLETENESS_NOT_DECLARED"):
            self.score(confirmed=False)
        with self.assertRaisesRegex(ValueError,
                                    "RECEIPT_AFTER_SCORING_CLOCK"):
            self._bad_clock()
 
    def _bad_clock(self):
        # Scoring clock passes quote window but precedes a late reception.
        self.write(timestamp="14:55",minutes="15:12")
        return self.score(at="2026-11-01T15:07:00+09:00")

    def test_forged_four_model_vector_rehashed_still_rejected(self):
        bad=copy.deepcopy(self.frozen)
        bad["payload"]["frozen_price_index_forecasts"][
            "PUBLIC_news_M0_persistence"][0]["p"]+=.01
        with self.assertRaisesRegex(ValueError,
                                    "CANONICAL|SOURCE_CODE_OR_CLOCK_CHANGED"):
            m.verify_freeze(bad)
        bad["sha256_of_canonical_frozen_payload"]=m._sha(bad["payload"])
        with self.assertRaisesRegex(ValueError,
                "FROZEN_MODEL_ROSTER_OR_MASS|NEWS_MODEL_VECTOR_NOT_FROM_PINNED_SOURCE"):
            m.verify_freeze(bad)

    def test_synthetic_source_and_article_change_not_original_receipt(self):
        r=m.score_local if hasattr(m,"score_local") else None
        self.assertIsNotNone(r)
        self.assertFalse(self.frozen["public_news_is_not_original_tote_source"] is False)
        self.assertTrue(self.frozen["payload"][
            "actual_future_JRA_quote_or_licence_acquired_by_script"] is False)


if __name__=="__main__":
    unittest.main()
