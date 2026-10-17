"""Actual public Saturday intermediate pools plus poisoned synthetic source inputs.

All prices are archived third-party intermediate quotes, not a locked
15–25 minute holdout snapshot, official JRA original odds HTML,
calibrated win/placing probabilities, or guaranteed payment quotes.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"scripts"))
from shuka2026_multipool_valuation_gap import (
    NEW_SNAPSHOT, EARLIER_SINGLE_SNAPSHOT,
    audited,
)
from shuka2026_market_overlay import source_base


class PublicWinWideQuinellaSnapshotCohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new=json.loads(NEW_SNAPSHOT.read_text(encoding="utf-8"))
        cls.old=json.loads(EARLIER_SINGLE_SNAPSHOT.read_text(encoding="utf-8"))
        cls.base=source_base()
        cls.result=audited(cls.new,cls.old,cls.base)

    def test_all_17_and_both_complete_136_pair_pools(self):
        self.assertEqual(len(self.new["win_prices_all_17"]),17)
        self.assertEqual(len(self.new["wide_pair_all_136"]),136)
        self.assertEqual(len(self.new["quinella_pair_all_136"]),136)
        self.assertEqual(len(self.new["selected_trio_three_horse_quotes_only"]),5)
        self.assertTrue(self.result["not_a_simultaneously_locked_cross_pool_price_vector"])
        self.assertEqual(self.result["source_later_reported_update_timestamp"],"UNKNOWN")

    def test_frozen_v31_market_selection_stays_7_of_17(self):
        self.assertEqual(self.result["exact_frozen_v31_market_M_top5"],[3,6,8,12,13])
        self.assertEqual(self.result["exact_frozen_v31_nonmarket_six"],[1,3,6,8,9,12])
        self.assertEqual(self.result["market_shadow_union"],[1,3,6,8,9,12,13])
        self.assertAlmostEqual(self.result["market_shadow_union_fraction"],7/17)
        self.assertTrue(self.result["not_v31_formal_prerace_holdout_15_to_25min_window"])

    def test_specific_pool_disagreement_for_wide_vs_win_vs_quinella(self):
        v=self.result["pair_event_rank_inversion"]
        self.assertFalse(v["14_more_favored_than_3_in_WIN_market"])
        self.assertTrue(v["14_more_favored_than_3_in_WIDE_given_pairing_8"])
        self.assertFalse(v["14_more_favored_than_3_in_QUINELLA_given_pairing_8"])
        self.assertEqual(v["14_wide_pair8_global_rank"],4)
        self.assertEqual(v["3_wide_pair8_global_rank"],6)
        self.assertEqual(v["9_wide_pair8_global_rank"],15)
        self.assertEqual(v["14_quinella_pair8_global_rank"],6)
        self.assertEqual(v["3_quinella_pair8_global_rank"],4)
        q={tuple(x["pair"]):x for x in self.result["selected_pair_quotes"]}
        self.assertAlmostEqual(q[(8,14)]["wide_two_horses_top_three"]["low"],4.4)
        self.assertAlmostEqual(q[(8,14)]["quinella_two_horses_top_two_unordered"]["odds"],16.3)
        self.assertAlmostEqual(q[(8,9)]["wide_two_horses_top_three"]["low"],14.5)
        self.assertAlmostEqual(q[(8,3)]["wide_two_horses_top_three"]["low"],6.4)
        self.assertEqual(q[(8,13)]["quinella_two_horses_top_two_unordered"]["rank"],1)

    def test_subjective_rank_14_and_9_still_above_win_crowd_rank(self):
        rows={x["number"]:x for x in self.result[
            "prior_assistant_vs_later_win_market_rank"]}
        self.assertEqual((rows[8]["market_win_rank"],rows[8]["market_minus_our_rank"]),(1,0))
        self.assertEqual((rows[13]["market_win_rank"],rows[13]["market_minus_our_rank"]),(2,0))
        self.assertEqual((rows[3]["market_win_rank"],rows[3]["market_minus_our_rank"]),(3,0))
        self.assertEqual(rows[14]["market_minus_our_rank"],4)
        self.assertEqual(rows[9]["market_minus_our_rank"],5)
        self.assertTrue(self.result[
            "prior_assistant_ordinal_ranks_NOT_user_supplied_calibrated_probabilities"])

    def test_horse_price_drift_does_not_fake_personality_or_probability(self):
        drifts={x["horse_number"]:x for x in self.result[
            "first_win_rank_vs_later_win_rank_changes_all_17"]}
        self.assertAlmostEqual(drifts[8]["earlier_win"],1.2)
        self.assertAlmostEqual(drifts[8]["later_win"],1.2)
        self.assertAlmostEqual(drifts[14]["earlier_win"],41.9)
        self.assertAlmostEqual(drifts[14]["later_win"],43.6)
        self.assertEqual(drifts[14]["earlier_win_rank"],8)
        self.assertEqual(drifts[14]["later_win_rank"],8)
        self.assertEqual(drifts[9]["earlier_market_rank"],12)
        self.assertEqual(drifts[9]["later_win_rank"],12)
        self.assertLess(self.result[
            "largest_watched_8_13_3_14_9_absolute_win_odds_pct_change"],10)
        self.assertTrue(self.result["no_positive_expected_value_recommendation"])

    def test_selected_trifecta_pools_are_partial_not_full(self):
        t={tuple(x["triple_unordered_horse_numbers"]):x for x in self.result[
            "selected_three_horse_quotes_partial_pool_ONLY"]}
        self.assertEqual(t[(8,13,14)]["rank_among_trifectas"],9)
        self.assertAlmostEqual(t[(8,13,14)]["quoted_trio_odds"],31.3)
        self.assertEqual(t[(3,8,13)]["rank_among_trifectas"],2)
        self.assertEqual(t[(3,8,14)]["rank_among_trifectas"],16)

    def test_quote_missing_136_or_duplicate_pair_is_HOLD(self):
        q=copy.deepcopy(self.new)
        q["wide_pair_all_136"].pop()
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_COMPLETE_17_CHOOSE_2"):
            audited(q,self.old,self.base)
        q=copy.deepcopy(self.new)
        q["wide_pair_all_136"][1]["horse_numbers"]=(
            q["wide_pair_all_136"][0]["horse_numbers"]
        )
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_PUBLIC_MARKET_PAIR"):
            audited(q,self.old,self.base)

    def test_nonfinite_wide_range_and_below_one_quinella_block_analysis(self):
        q=copy.deepcopy(self.new)
        q["wide_pair_all_136"][0]["quoted_odds_min"]=float("nan")
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_PUBLIC_WIDE_ODDS_RANGE"):
            audited(q,self.old,self.base)
        q=copy.deepcopy(self.new)
        q["quinella_pair_all_136"][0]["quoted_odds"]=0.5
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_PUBLIC_QUINELLA_ODDS"):
            audited(q,self.old,self.base)

    def test_changed_win_odds_without_changing_market_rank_rejected(self):
        q=copy.deepcopy(self.new)
        # Publish a 50x inflated top-ranked candidate without
        # changing the publisher's popularity ordering; fail.
        candidate=next(x for x in q["win_prices_all_17"]
                       if x["horse_number"]==8)
        candidate["win_odds"]=50.0
        with self.assertRaisesRegex(ValueError,"HOLD_PUBLIC_WIN_RANK_INCONSISTENT"):
            audited(q,self.old,self.base)

    def test_horse_name_source_and_trio_coverage_must_not_be_invented(self):
        q=copy.deepcopy(self.new)
        q["win_prices_all_17"][0]["name"]="FAKE NOT JRA"
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_OR_WRONG_JRA_RACE_HORSE_NAMES"):
            audited(q,self.old,self.base)
        q=copy.deepcopy(self.new)
        q["data_quality"]["selected_three_horse_ranks_only_no_full_680_claim"]=False
        with self.assertRaisesRegex(ValueError,"HOLD_DONT_MISREPRESENT_PARTIAL_TRIO"):
            audited(q,self.old,self.base)
        q=copy.deepcopy(self.new)
        q["source_provider_reported_last_update_not_available"]=False
        with self.assertRaisesRegex(ValueError,"HOLD_INTERMEDIATE_SOURCE_PROVENANCE"):
            audited(q,self.old,self.base)


if __name__=="__main__":
    unittest.main()
