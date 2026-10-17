"""No fabricated market prices: source audit and frozen M vs prior ordinal judgment."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from shuka2026_compare_own_vs_crowd import (
    SOURCE, measure, validate_source, MARKET_URL,
    OUR_HISTORICAL_QUALITATIVE_RANKS,
)
from shuka2026_market_overlay import source_base


class LiveIntermediateMarketVsPriorQualitativeRanking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.quoted=json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.base=source_base()
        cls.report=measure(cls.quoted,cls.base)

    def test_real_source_seventeen_unique_JRA_names_numbers_and_market(self):
        self.assertEqual(len(self.report["market_intermediate_odds_all_17"]),17)
        self.assertEqual([x["horse_number"] for x in
                          self.report["market_intermediate_odds_all_17"][:3]],
                         [8,13,3])
        self.assertEqual(self.report["odds_source_url"],MARKET_URL)
        self.assertTrue(self.report["original_JRA_win_odds_HTML_NOT_independently_verified"])
        self.assertTrue(self.report["provider_last_update_time_not_available_from_extraction"])
        self.assertTrue(self.report["frozen_v31_market_channel_ACTUALLY_EXECUTED_on_observed_prices"])

    def test_actual_M_channel_top_five_and_shadow_union(self):
        self.assertEqual(self.report["market_M_numbers"],[3,6,8,12,13])
        self.assertEqual(self.report[
            "historical_nonmarket_C1_U_or_rescue_numbers"],[1,3,6,8,9,12])
        self.assertEqual(self.report["market_M_added_only_horse_numbers"],[13])
        self.assertEqual(self.report["historic_only_not_market_M_horse_numbers"],[1,9])
        self.assertEqual(self.report["full_shadow_v31_candidate_union_numbers"],
                         [1,3,6,8,9,12,13])
        self.assertEqual(self.report["full_shadow_v31_candidate_union_size"],7)
        self.assertAlmostEqual(self.report["full_shadow_v31_candidate_fraction"],7/17)
        self.assertTrue(self.report["not_formal_v31_holdout_15_25min_timed_source_freeze"])

    def test_previous_our_pre_odds_top_three_match_crowd_and_biggest_misses(self):
        self.assertEqual(OUR_HISTORICAL_QUALITATIVE_RANKS,[8,13,3,14,4,1,9])
        compare=self.report["earlier_assistant_qualitative_ranks_vs_crowd"]
        self.assertEqual([x["current_market_rank"] for x in compare[:3]],[1,2,3])
        by={x["horse_number"]:x for x in compare}
        self.assertEqual(by[14]["market_rank_minus_earlier_assistant_rank"],4)
        self.assertEqual(by[9]["market_rank_minus_earlier_assistant_rank"],5)
        self.assertEqual(by[14]["current_market_rank"],8)
        self.assertEqual(by[9]["current_market_rank"],12)
        outsiders={z["horse_number"] for z in
                   self.report["market_higher_than_qualitative_shortlist"]}
        self.assertEqual(outsiders,{6,12})
        self.assertTrue(self.report["no_USER_supplied_calibrated_win_probabilities_to_compare"])

    def test_single_quote_breakeven_not_true_win_probability(self):
        m=self.report["market_intermediate_odds_all_17"]
        by={x["horse_number"]:x for x in m}
        self.assertAlmostEqual(by[8]["payout_breakeven_percent_NOT_win_probability"],
                               100/1.2)
        self.assertAlmostEqual(by[14]["payout_breakeven_percent_NOT_win_probability"],
                               100/by[14]["win_odds"])
        self.assertGreater(by[14]["win_odds"],35)
        self.assertGreater(by[9]["win_odds"],60)
        self.assertGreater(self.report[
            "inverse_win_odds_sum_over_17_NOT_probability_calibration"],1)
        self.assertAlmostEqual(
            sum(x["renormalized_odds_weight_percent_NOT_win_probability"] for x in m),
            100.0)
        self.assertTrue(self.report[
            "relative_odds_weight_is_market_concentration_proxy_not_chance"])
        self.assertTrue(self.report["no_measured_positive_expected_value_or_own_fair_odds"])

    def test_false_date_race_url_and_pretend_publisher_update_not_accepted(self):
        for name,value in (
            ("target_race","2026-10-12-KYOTO-11"),
            ("quoted_source_url","https://example.invalid/horse/2026/"),
            ("source_page_last_updated_timestamp","2026-10-17T14:37:00+09:00"),
        ):
            q=copy.deepcopy(self.quoted)
            q[name]=value
            with self.assertRaisesRegex(ValueError,"HOLD_UNVERIFIED_SOURCE"):
                measure(q,self.base)

    def test_before_sale_or_after_race_quote_rejected(self):
        for when in ("2026-10-16T14:34:00+09:00",
                     "2026-10-18T15:40:00+09:00",
                     "2026-10-17T14:36:00",
                     "2026-10-17T14:36:00+00:00"):
            q=copy.deepcopy(self.quoted)
            q["observation_started_at_jst"]=when
            with self.assertRaisesRegex(ValueError,
              "HOLD_NOT_POST_TOTE_SALE_AND_BEFORE_START"):
                measure(q,self.base)

    def test_malformed_price_identity_or_duplicate_horse_fails(self):
        for col,val,message in (
            ("win_odds",float("nan"),"HOLD_INVALID_OR_MISSING"),
            ("win_odds",0.5,"HOLD_INVALID_OR_MISSING"),
            ("name","FAKE HORSE","HOLD_MARKET_NAME"),
            ("number",13,"HOLD_MISSING_DUPLICATE"),
        ):
            q=copy.deepcopy(self.quoted)
            q["horses"][0][col]=val
            if col=="number":
                # Keep the new number's real corresponding JRA name to
                # reach the duplicate-identity gate rather than failing
                # earlier at the official-number/name mismatch gate.
                q["horses"][0]["name"]="ドリームコア"
            with self.assertRaisesRegex(ValueError,message):
                measure(q,self.base)

    def test_stale_publisher_rank_vs_price_not_silently_accepted(self):
        q=copy.deepcopy(self.quoted)
        q["horses"][0]["market_rank"]=6
        with self.assertRaisesRegex(ValueError,"HOLD_PUBLISHER_ODDS_RANK_NOT_CONSISTENT"):
            measure(q,self.base)


if __name__=="__main__":
    unittest.main()
