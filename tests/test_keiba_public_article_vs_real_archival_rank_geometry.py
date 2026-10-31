#!/usr/bin/env python3
"""Real archival rank geometry and publisher-time falsification tests."""
from __future__ import annotations

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
    import keiba_public_article_vs_real_archival_rank_geometry as m


@unittest.skipIf(np is None, "NumPy required by original parent Tenno source module")
class PublicArticleVsArchiveRankTests(unittest.TestCase):
    def test_17_original_prices_and_two_identical_later_public_articles(self):
        early,first_digest=m.declared_field()
        late,digest=m._declared_later()
        self.assertEqual(len(early),len(late))
        self.assertEqual(len(late),17)
        self.assertEqual(late[7],2.4)
        self.assertEqual(late[1],2.5)
        self.assertEqual(late[11],11.5)
        self.assertEqual(late[17],11.2)
        self.assertEqual(dict(m.NETKEIBA_1742_FULL_WIN),late)
        self.assertEqual(first_digest,
            "b8f4b1e617b2582c156c88dece77e440d10a39140feaccf35125d896caf1f479")
        self.assertEqual(digest,
            "3b8fc4798664a090963d5e8221029643cf9205934ba7fe7db0cc37a8d1f6e37b")
        self.assertLess(m.CORROBORATING_NEWS_PUBLISHED,m.LATER_REPORTED_ASOF)

    def test_17_runner_quoted_contrast_is_small_with_zero_rank_reversal(self):
        s=m.tenno_public_articles()
        self.assertEqual(s["horse_count"],17)
        self.assertEqual(s["unique_unordered_horse_pairs"],136)
        self.assertEqual(s["individual_display_prices_changed"],13)
        self.assertEqual(s["strictly_reversed_pair_count"],0)
        self.assertEqual(s["horse_ids_whose_ordinal_rank_changed"],0)
        self.assertEqual(s["newly_equal_pair_count"],0)
        self.assertEqual(s["pair_earlier_tie_boundary_within_posthoc_worst_case_shock_count"],5)
        self.assertEqual(s["geometrically_possible_under_uniform_posthoc_bound_but_not_observed"],5)
        self.assertAlmostEqual(
            s["normalized_inverse_quote_TV_percentage_points"],
            .33203550493330486,places=11)
        self.assertAlmostEqual(
            s["later_horse_price_log_shock_max_abs_posthoc"],
            .03419136474827931,places=11)
        self.assertAlmostEqual(
            s["initial_top_two_normalized_quote_index_share"],
            .6430976083661661,places=10)
        self.assertAlmostEqual(
            s["later_initial_top_two_normalized_quote_index_share"],
            .6404687920475218,places=10)
        self.assertTrue(s["top_two_horse_set_preserved"])
        self.assertTrue(s["full_order_preserved"])

    def test_nominal_18_market_update_does_not_follow_from_article_clock(self):
        a=m.tenno_public_articles()
        self.assertTrue(a["nominal_18h_quote_already_published_in_1742_article"])
        self.assertFalse(a["independently_attested_genuine_two_time_JRA_feed"])
        self.assertFalse(a["measured_60min_market_path_identified"])
        self.assertEqual(a["authenticated_original_receipt_count"],0)
        self.assertTrue(a["not_eligible_for_original_PR22_PR30_prospective_score"])

    def test_later_source_malformed_and_subdecimal_tamper_are_rejected(self):
        with patch.object(m, "LATER_FULL_WIN", ((1,2.5),)):
            with self.assertRaisesRegex(ValueError,
                    "HOLD_TENNO_SECOND_ARTICLE_INCOMPLETE"):
                m._declared_later()
        temp=list(m.LATER_FULL_WIN)
        temp[10]=(11,11.51)
        with patch.object(m, "LATER_FULL_WIN", tuple(temp)):
            with self.assertRaisesRegex(ValueError,
                    "HOLD_PUBLIC_ARTICLES_DO_NOT_MATCH"):
                m._declared_later()
        with patch.object(m,"LATER_REPORTED_ASOF",
                          "2026-10-31T17:35:00+09:00"):
            with self.assertRaisesRegex(ValueError,
                    "HOLD_PUBLIC_LATER_ARTICLE_PRICE_FIELD_MUTATED"):
                m._declared_later()

    def test_geometry_allows_real_pair_rank_crossing_without_any_threshold(self):
        b={1:2.0,2:2.1,3:6.0,4:8.0,5:11.0}
        a={1:2.2,2:2.0,3:6.0,4:8.0,5:11.0}
        result=m.rank_contrast(b,a)
        self.assertEqual(result["strictly_reversed_horse_pairs"],[[1,2]])
        self.assertEqual(result["strictly_reversed_pair_count"],1)
        self.assertEqual(result["unique_unordered_horse_pairs"],10)
        self.assertTrue(result[
            "geometric_rank_crossing_NOT_evidence_of_dynamic_market_criticality"])
        self.assertFalse(result["full_order_preserved"])
        self.assertAlmostEqual(result[
            "normalized_inverse_quote_TV_percentage_points"],
            50*sum(abs(1/b[i]/sum(1/x for x in b.values())-
                       1/a[i]/sum(1/x for x in a.values())) for i in b),
            places=10)

    def test_ties_not_counted_as_strict_reversals(self):
        b={1:2.0,2:2.1,3:6.0,4:8.0,5:11.0}
        a={**b,1:2.1}
        r=m.rank_contrast(b,a)
        self.assertEqual(r["strictly_reversed_pair_count"],0)
        self.assertEqual(r["newly_equal_pair_count"],1)

    def test_incomplete_wrong_prices_hold_no_rank_geometry(self):
        b={1:2.0,2:2.1,3:6.0,4:8.0,5:11.0}
        for a in ({**b,3:float("nan")},{**b,2:0},
                  {1:2.0,2:2.1,3:6.0,4:8.0},
                  {**b,3:"6"}):
            with self.subTest(sample=a):
                with self.assertRaisesRegex(ValueError,
                        "HOLD_INCOMPLETE_OR_INVALID_MATCHED_FULL_WIN"):
                    m.rank_contrast(b,a)

    def test_original_oct12_source_sha_and_no_podium_read(self):
        import odds_r8_real_three_time_market as r8
        with patch.object(r8,"verify_official_oct12",
                          side_effect=AssertionError("OUTCOME_LEAK")):
            a=m.archived_kyoto_prices(ROOT)
        self.assertEqual(a["original_distinct_races"],5)
        self.assertEqual(a["original_distinct_meeting_dates"],1)
        self.assertEqual(a["original_source_price_intervals"],6)
        self.assertEqual(
            [(x["race_number"],x["interval"]) for x in a["by_interval"]],
            [(8,"first_to_second"),(9,"first_to_second"),
             (10,"first_to_second"),(11,"first_to_second"),
             (12,"first_to_second"),(8,"second_to_third")])
        self.assertTrue(a["third_point_is_R8_NOT_A_SIXTH_NEW_RACE"])
        for r in a["by_interval"]:
            h=r["diagnostic"]["horse_count"]
            self.assertEqual(r["diagnostic"]["unique_unordered_horse_pairs"],
                             h*(h-1)//2)
            self.assertGreater(r["diagnostic"][
                "initial_sum_inverse_payout_odds_not_stakes"],0)
            self.assertTrue(r["diagnostic"][
                "geometric_rank_crossing_NOT_evidence_of_dynamic_market_criticality"])

    def test_full_audit_does_not_claim_new_prospective_or_mechanism(self):
        a=m.audit(include_archives=False)
        self.assertEqual(a["retrospective_kyoto_archived"],"NOT_RUN")
        self.assertEqual(a["status"],m.STATUS)
        self.assertTrue(a["source_quote_vs_tote_update_clocks_not_conflated"])
        self.assertTrue(a["public_tenno_report_not_a_true_independent_next_price_score"])
        self.assertTrue(a["no_target_JRA_winner_or_finishing_order_used"])
        self.assertTrue(a["no_market_criticality_or_herding_mechanism_identified"])


if __name__=="__main__":
    unittest.main()
