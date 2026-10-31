#!/usr/bin/env python3
"""Archived displayed SportsNavi 22:25 and PR41 17:42 public-news source."""
from __future__ import annotations
import copy
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
try:
    import numpy as np
except ModuleNotFoundError:
    np=None
if np is not None:
    import keiba_tenno_sportsnavi_2225_public_contrast as m


@unittest.skipIf(np is None,"Original PR41 source freeze requires NumPy")
class PublishedEveningSeventeenOddsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if np is not None:
            cls.report=m.audit()

    def test_source_reported_2225_field_verbatim_pinned_sha(self):
        prices,digest=m._declared_2225()
        self.assertEqual(len(prices),17)
        self.assertEqual(sorted(prices),list(range(1,18)))
        self.assertEqual(prices[7],2.5)
        self.assertEqual(prices[1],2.7)
        self.assertEqual(prices[3],8.8)
        self.assertEqual(prices[11],10.8)
        self.assertEqual(prices[17],10.4)
        self.assertEqual(digest,m.EXPECTED_DISPLAY_FIELD_SHA256)
        self.assertEqual(m.SOURCE_DISPLAYED_UPDATED_AT,
                         "2026-10-31T22:25:00+09:00")
        self.assertIn("sports.yahoo.co.jp",m.SOURCE_PAGE_URL)

    def test_all_17_moves_none_of_136_rank_inversions(self):
        a=self.report
        v=a["cross_public_page_descriptive_price_change"]
        self.assertEqual(a["earlier_all_17_news_horse_prices_changed"],17)
        self.assertEqual(v["strictly_reversed_pair_count"],0)
        self.assertEqual(v["unique_unordered_horse_pairs"],136)
        self.assertTrue(v["full_order_preserved"])
        self.assertTrue(v["top_two_horse_set_preserved"])
        self.assertAlmostEqual(v[
            "normalized_inverse_quote_TV_percentage_points"],
            3.2111564063769875,places=10)
        self.assertAlmostEqual(v[
            "initial_top_two_normalized_quote_index_share"],
            .6404687920475218,places=10)
        self.assertAlmostEqual(v[
            "later_initial_top_two_normalized_quote_index_share"],
            .6091394710635032,places=10)

    def test_all_four_original_shabound_prices_same_2225_quote_diagnostic(self):
        scores=self.report[
            "old_PR41_four_news_models_same_later_public_quoted_price_DIAGNOSTIC_ONLY"]
        self.assertEqual(set(scores),set(m.MODEL_NAMES))
        targets={
            "PUBLIC_news_M0_persistence":3.2111564063769826,
            "PUBLIC_fixed_10pct_uniform_dilution":4.633985266057334,
            "PUBLIC_log_support_power_0p9":2.594695448968824,
            "PUBLIC_log_support_power_1p1":7.771313317352094,
        }
        for label,loss in targets.items():
            self.assertAlmostEqual(scores[label]["TV_percentage_points"],
                                   loss,places=10)
            self.assertGreaterEqual(
                scores[label]["KL_later_vs_article_model_nats"],-1e-12)
        self.assertEqual(self.report[
            "frozen_PR41_pretarget_news_four_model_SHA256"],
            m.EXPECTED_ORIGINAL_NEWS_FREEZE_SHA256)
        self.assertFalse(self.report[
            "new_independently_confirmed_prospective_market_trial"])

    def test_this_price_is_earlier_than_PR41_live_preseal_and_not_future_q2(self):
        a=self.report
        self.assertTrue(a[
            "news_1742_vs_2225_comparison_known_before_PR41_GitHub_SHA_comment"])
        self.assertTrue(a["retrospective_diagnostic_NOT_a_PR41_Nov1_target"])
        self.assertTrue(a["PR41_fixed_Nov1_1445_1505_target_remains_unobserved"])
        self.assertTrue(a["source_updated_at_NOT_an_independent_timestamp_of_web_receipt"])
        self.assertTrue(a["no_legally_acquired_JRA_VAN_original_WIN_source_bytes"])
        self.assertTrue(a["no_future_winner_JRA_bettor_votes_or_betting_returns_read"])
        self.assertTrue(a["PR30_PR37_original_11_models_and_main_sealed_data_unchanged"])

    def test_one_price_mutation_or_time_change_fails_manifest_integrity(self):
        rows=list(m.SPORTSNAVI_2225_FULL_WIN)
        rows[6]=(7,2.51)
        with patch.object(m,"SPORTSNAVI_2225_FULL_WIN",tuple(rows)):
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_SPORTSNAVI_PUBLISHED_2225_VALUES_CHANGED"):
                m._declared_2225()
        with patch.object(m,"SOURCE_DISPLAYED_UPDATED_AT",
                          "2026-11-01T15:30:00+09:00"):
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_SPORTSNAVI_PUBLISHED_2225_VALUES_CHANGED"):
                m._declared_2225()
        with patch.object(m,"SPORTSNAVI_2225_FULL_WIN",
                          ((1,2.7),(7,2.5))):
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_SPORTSNAVI_2225_NOT_COMPLETE_17_WIN"):
                m._declared_2225()

    def test_no_17_horse_or_false_PR41_parent_forecast(self):
        with patch.object(m,"EXPECTED_ORIGINAL_NEWS_FREEZE_SHA256","f"*64):
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_PR41_ORIGINAL_NEWS_FROZEN_FOUR_CHANGED"):
                m.audit()
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_PUBLIC_ODDS_NOT_17_POSITIVE"):
            m._index({1:2.5,7:2.4})
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_PUBLIC_PRICE_INDEX_NOT_FULL_POSITIVE"):
            m._error([.5]*16,[.5]*17)

    def test_deterministic_report_and_json_finite(self):
        self.assertEqual(self.report,m.audit())
        import json
        json.dumps(self.report,allow_nan=False,ensure_ascii=False)


if __name__=="__main__":
    unittest.main()
