#!/usr/bin/env python3
"""Published partial odds: never invent 17-horse market states or bettor shocks."""
from __future__ import annotations
import copy
import math
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
if np is not None:
    import keiba_tenno_partial_article_timepath as m


@unittest.skipIf(np is None,"Original full-field SHA-locked Tenno modules require NumPy")
class EditorialPartialMarketTests(unittest.TestCase):
    def test_five_blog_partial_rows_pinned_by_declared_content_sha(self):
        rows,digest=m._blog_reported_quotes()
        self.assertEqual(digest,m.PINNED_BLOG_DECLARED_PARTIAL_SHA256)
        self.assertEqual([len(r["prices"]) for r in rows],[4,5,5,5,5])
        self.assertNotIn(17,rows[0]["prices"])
        self.assertEqual(rows[0]["prices"][1],2.6)
        self.assertEqual(rows[0]["prices"][7],2.6)
        self.assertEqual(rows[2]["prices"][1],2.5)
        self.assertEqual(rows[2]["prices"][7],2.9)
        self.assertTrue(all(not r["source_updated_at_independently_proven"]
                            for r in rows))
        self.assertTrue(all(not r["all_17_prices_observed"]
                            for r in rows))

    def test_article_path_7_reported_points_never_seven_authorized_snapshots(self):
        a=m.audit()
        self.assertEqual(a["publisher_self_reported_timepoints_not_provider_attested"],7)
        self.assertEqual(a["one_mutable_blog_partial_timepoints"],5)
        self.assertEqual(a["different_editorial_full_field_timepoints"],2)
        self.assertEqual([z["reported_horses_at_this_time_NOT_imputed"]
                          for z in a["by_timepoint_1_vs_7"]],[4,5,5,5,5,17,17])
        self.assertEqual([z["full_17_runner_qM0_eligible"]
                          for z in a["by_timepoint_1_vs_7"]],
                         [False]*5+[True]*2)
        self.assertEqual(a["new_genuinely_pretarget_SHA_verified_price_score_count"],0)
        self.assertTrue(a["missing_partial_runners_NOT_imputed_and_NOT_renormalized"])
        self.assertTrue(a["source_updates_publications_NOT_independently_time_attested"])
        self.assertTrue(a["no_real_bettor_votes_original_JRA_GPS_or_official_target_result_used"])
        self.assertEqual(a["criticality_self_reinforcement_or_betting_EV"],"HOLD")

    def test_early_tie_and_two_strict_seven_one_switches(self):
        a=m.audit()
        self.assertEqual([z["displayed_favorite_between_1_and_7"]
                          for z in a["by_timepoint_1_vs_7"]],
                         ["TIE","7","1","1","7","7","7"])
        d=a["by_adjacent_publication_timepoint_interval"]
        self.assertEqual(len(d),6)
        self.assertEqual([x["strictly_reversed_displayed_pairs"] for x in d],
                         [[],[[1,7]],[[11,17]],[[1,7]],[],[]])
        self.assertEqual(a["strict_price_pair_reversals_over_reported_intervals"],3)
        self.assertEqual(a["reported_1_vs_7_strict_reversal_interval_count"],2)
        self.assertEqual([x["compared_pair_count_ONLY_common_reported_horses"]
                          for x in d],[6,10,10,10,10,136])
        self.assertEqual([x["full_17_runner_market_TV"] for x in d],
                         ["UNAVAILABLE_PARTIAL"]*5+["AVAILABLE_ONLY_FULL_FIELD"])

    def test_rounding_uncertainty_leaves_only_one_guaranteed_pair_flip(self):
        a=m.audit()
        s=a["by_timepoint_1_vs_7"]
        self.assertEqual([z["pair_log_ratio_and_rounding"][
            "robust_sign_under_decimal_rounding"] for z in s],
            ["uncertain_or_rounded_tie",
             "positive","negative",
             "uncertain_or_rounded_tie",
             "uncertain_or_rounded_tie",
             "uncertain_or_rounded_tie",
             "uncertain_or_rounded_tie"])
        self.assertEqual([z[
            "number_1_vs_7_opposite_sign_robust_under_nearest_tenth_rounding"]
             for z in a["by_adjacent_publication_timepoint_interval"]],
                         [False,True,False,False,False,False])
        self.assertEqual(a[
            "robust_1_vs_7_reversal_under_conservative_one_decimal_rounding"],1)
        self.assertAlmostEqual(
            s[1]["pair_log_ratio_and_rounding"]["displayed_log_odds_ratio"],
            math.log(2.6/2.4),places=12)
        self.assertAlmostEqual(
            s[2]["pair_log_ratio_and_rounding"]["displayed_log_odds_ratio"],
            math.log(2.5/2.9),places=12)

    def test_existing_sha_locked_full_market_reused_only_at_17_and_1742(self):
        a=m.audit()
        self.assertEqual(a["parent_declared_full_17h_SHA256_not_original_vendor"],
             "b8f4b1e617b2582c156c88dece77e440d10a39140feaccf35125d896caf1f479")
        self.assertEqual(a["later_declared_full_1742_SHA256_not_original_vendor"],
             "3b8fc4798664a090963d5e8221029643cf9205934ba7fe7db0cc37a8d1f6e37b")
        self.assertAlmostEqual(a["full_17runner_1700_to_1742_index_TV_pp_ONLY"][
            "original_17_full_source_and_later_full_source_diff"],
            .3320355049333152,places=10)
        self.assertEqual(a["full_17runner_1700_to_1742_index_TV_pp_ONLY"][
            "full_17_pair_rank_reversals"],0)
        self.assertTrue(a["full_17runner_1700_to_1742_index_TV_pp_ONLY"][
            "source_times_not_a_certified_time_interval"])

    def test_blog_changes_or_unsupported_partial_field_HOLD(self):
        rows=list(m.BLOG_PARTIAL)
        bad=list(rows[2][1])
        bad[0]=(1,2.51)
        rows[2]=(rows[2][0],tuple(bad))
        with patch.object(m,"BLOG_PARTIAL",tuple(rows)):
            with self.assertRaisesRegex(ValueError,
                    "HOLD_BLOG_REPORTED_PARTIAL_OR_TIMESTAMP_TAMPERED"):
                m._blog_reported_quotes()
        with patch.object(m,"BLOG_PARTIAL",m.BLOG_PARTIAL[:-1]):
            with self.assertRaisesRegex(ValueError,
                    "HOLD_PARTIAL_HORSE_DENOMINATOR_CHANGED|HOLD_BLOG_REPORTED_PARTIAL_OR_TIMESTAMP_TAMPERED"):
                m._blog_reported_quotes()
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_PARTIAL_QUOTE_FIELD_NOT_REAL_POSITIVE"):
            m._quoted_subset({1:2.4,7:float("nan")})
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_PARTIAL_QUOTE_FIELD_NOT_REAL_POSITIVE"):
            m._quoted_subset({1:2.4,7:"2.6"})

    def test_noon_independent_crosscheck_not_mixed_as_same_update(self):
        a=m.audit()
        self.assertTrue(a["independent_noon_context_reported_1_2p5_and_7_2p9"])
        self.assertEqual(a["independent_noon_context_URL"],
                         "https://spread-sports.jp/archives/402071")
        self.assertFalse(any("12:00" in z["reported_jst"]
                 for z in a["by_timepoint_1_vs_7"]))
        self.assertTrue(a["reported_large_bet_events_NOT_assumed_observed_transactions"])

    def test_nonmonotonic_article_times_and_missing_full_field_hold(self):
        x,y=m._blog_reported_quotes()
        # Distinct timestamp ordering; no retro-fitted observation.
        bad=copy.deepcopy(x[1])
        bad["source_reported_jst"]=x[0]["source_reported_jst"]
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_NONPOSITIVE_ARTICLE_REPORTED_INTERVAL"):
            m._interval(x[0],bad)
        with patch.object(m,"declared_field",
                          return_value=({1:2.5,7:2.4},"f"*64)):
            with self.assertRaisesRegex(ValueError,
                                    "HOLD_ORIGINAL_LATER_PUBLIC_ALL_17_REQUIRED"):
                m.audit()


if __name__=="__main__":
    unittest.main()
