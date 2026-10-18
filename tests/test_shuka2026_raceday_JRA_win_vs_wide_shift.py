"""Falsify inappropriate comparisons of official race-day and prior public pools.

Actual original JRA win quotes and 136/136 public pair pool prices
remain source-date stamped, no target race result used. Tests
show precise moving odds and historical market rank differences,
but do not infer win, top3 or betting expected-value probabilities.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from shuka2026_raceday_JRA_win_vs_wide_shift import (
    RACE_DAY, SATURDAY, verify, compare, SOURCE_TIMESTAMP,
)
from shuka2026_market_overlay import source_base


class RaceDayActualJraVersusSaturdayPublicPoolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.today=json.loads(RACE_DAY.read_text(encoding="utf-8"))
        cls.yesterday=json.loads(SATURDAY.read_text(encoding="utf-8"))
        cls.base=source_base()
        cls.q=compare(cls.today,cls.yesterday,cls.base)

    def test_official_JRA_explicit_price_timestamp_plus_all17_names(self):
        q=self.q
        self.assertEqual(q["official_JRA_odds_publication_jst"],
                         "2026-10-18T11:42:00+09:00")
        self.assertEqual(SOURCE_TIMESTAMP,q["official_JRA_odds_publication_jst"])
        self.assertTrue(q["genuine_JRA_official_seventeen_horses_verified"])
        self.assertTrue(q["JRA_and_SportsNavi_17_win_quotes_exactly_match_on_these_saved_pages"])
        self.assertEqual(q["current_Kyoto_turf_going"],"良")
        self.assertTrue(q["SUNDAY_SportsNavi_pool_page_quote_publication_time_UNKNOWN"])
        self.assertTrue(q["multi_pool_sources_may_have_been_refreshed_at_different_times"])

    def test_frozen_market_M_and_historical_candidate_union_unmodified(self):
        q=self.q
        self.assertEqual(q["frozen_v31_market_M_on_JRA_official_priced_five"],
                         [3,6,8,12,13])
        self.assertEqual(q["frozen_v31_last_Saturday_M_on_public_actual_five"],
                         [3,6,8,12,13])
        self.assertFalse(q["frozen_v31_market_M_CHANGED"])
        self.assertEqual(q["frozen_v31_original_nonmarket_six"],
                         [1,3,6,8,9,12])
        self.assertEqual(q["frozen_v31_market_plus_history_shadow_union"],
                         [1,3,6,8,9,12,13])
        self.assertAlmostEqual(q["frozen_v31_shadow_candidate_fraction"],7/17)
        self.assertTrue(q["frozen_v31_thresholds_or_model_weights_NOT_changed"])

    def test_14_wide_vs_3_reversal_while_same_market_M(self):
        q=self.q
        self.assertEqual(q["WATCH_wide_8_14_vs_8_3_event_order_reversal"],
             "PRIOR_14_WIDE_MORE_POPULAR_THAN_3_BUT_SUNDAY_3_WIDE_MORE_POPULAR")
        c={tuple(x["horse_numbers"]):x for x in q["selected_pair_market_change"]}
        a=c[(8,14)];b=c[(3,8)]
        self.assertEqual((a["SATURDAY_wide_rank_among_all136"],
                          b["SATURDAY_wide_rank_among_all136"]),(4,6))
        self.assertEqual((a["SUNDAY_wide_rank_among_all136"],
                          b["SUNDAY_wide_rank_among_all136"]),(7,5))
        self.assertEqual(a["SATURDAY_wide_payout_quote_range"],[4.4,4.8])
        self.assertEqual(a["SUNDAY_wide_payout_quote_range"],[7.5,8.2])
        self.assertEqual(b["SUNDAY_wide_payout_quote_range"],[6.3,7])
        self.assertEqual(a["SATURDAY_quinella_rank_among_all136"],6)
        self.assertEqual(a["SUNDAY_quinella_rank_among_all136"],7)

    def test_9_horse_public_odds_shorten_while_not_calibrated_favorite(self):
        q=self.q
        moves={x["horse_number"]:x for x in q[
            "actual_17_official_win_market_vs_Saturday"]}
        self.assertEqual(moves[9]["saturday_15_37_win_odds"],77.6)
        self.assertEqual(moves[9]["sunday_JRA_11_42_win_odds"],60.6)
        self.assertLess(moves[9][
            "percent_change_in_payout_odds_NOT_change_in_win_probability"],-20)
        self.assertEqual(moves[9]["saturday_market_win_rank"],12)
        self.assertEqual(moves[9]["sunday_official_JRA_market_win_rank"],11)
        self.assertEqual(moves[14]["sunday_official_JRA_market_win_rank"],9)
        self.assertEqual(moves[14]["saturday_market_win_rank"],8)
        self.assertEqual(moves[8]["saturday_15_37_win_odds"],1.2)
        self.assertEqual(moves[8]["sunday_JRA_11_42_win_odds"],1.4)
        self.assertTrue(q["no_ASSISTANT_or_USER_supplied_calibrated_win_top3_or_top2_probabilities"])

    def test_8_9_wide_odds_shorten_relative_to_yesterday(self):
        c={tuple(x["horse_numbers"]):x for x in self.q["selected_pair_market_change"]}
        x=c[(8,9)]
        self.assertEqual(x["SATURDAY_wide_payout_quote_range"],[14.5,15.9])
        self.assertEqual(x["SUNDAY_wide_payout_quote_range"],[12.7,13.8])
        self.assertLess(x["low_end_wide_odds_percent_change_NOT_probability"],0)
        self.assertEqual(x["SUNDAY_wide_rank_among_all136"],13)

    def test_own_earlier_ordinal_rank_vs_public_JRA_day_of_race(self):
        ranked=self.q["earlier_vs_Sunday_assistant_opinion_rank"]
        self.assertEqual([x["horse_number"] for x in ranked],[8,13,3,14,4,1,9])
        self.assertEqual([x["actual_Sunday_JRA_market_rank"] for x in ranked],
                         [1,2,4,9,6,7,11])
        self.assertEqual(ranked[3]["market_minus_assistant_rank"],5)
        self.assertEqual(ranked[6]["market_minus_assistant_rank"],4)
        partners=self.q["SUNDAY_8_fixed_partner_rank_per_16_other_horses"]
        old=self.q["SATURDAY_8_fixed_partner_rank_per_16_other_horses"]
        self.assertGreater(partners["14"]["wide_partner_rank_16"],
                           partners["3"]["wide_partner_rank_16"])
        self.assertLess(old["14"]["wide_partner_rank_16"],
                        old["3"]["wide_partner_rank_16"])

    def test_validated_both_136_pair_pools_and_partial_three_horse(self):
        day,wide,quin,old,trio,oldpair=verify(self.today,self.yesterday,self.base)
        self.assertEqual(len(day),17)
        self.assertEqual(len(wide),136)
        self.assertEqual(len(quin),136)
        self.assertEqual(len(oldpair["wide"]),136)
        self.assertEqual(len(oldpair["quinella"]),136)
        self.assertTrue(0<len(trio)<680)
        self.assertNotIn("source_actual_three_horse_odds_all_680",self.q)

    def test_real_odds_are_not_a_positive_expected_value_argument(self):
        q=self.q
        self.assertTrue(q["no_positive_expected_value_proof"])
        self.assertTrue(q["no_wagers_or_orders_executed"])
        self.assertTrue(q["not_formal_15_to_25min_JRA_pre_start_holdout"])
        self.assertTrue(q["not_prospectively_validated_better_than_market"])
        self.assertGreater(q["Sunday_reciprocal_odds_sum_NOT_a_probability_model"],1)
        self.assertNotIn("true_win_probability",json.dumps(q))

    def test_fake_official_timestamp_future_and_changed_source_URL_rejected(self):
        for key,value,expected in (
            ("publisher_explicit_update_timestamp_jst","2026-10-18T15:45:00+09:00",
             "HOLD_JRA_OFFICIAL_QUOTE_PUBLICATION_TIME_NOT_VERIFIED"),
            ("publisher_explicit_update_timestamp_jst","2026-10-18T11:45:00+09:00",
             "HOLD_JRA_OFFICIAL_QUOTE_PUBLICATION_TIME_NOT_VERIFIED"),
            ("source_url","https://fake.odds.invalid/",
             "HOLD_JRA_OFFICIAL_QUOTE_PUBLICATION_TIME_NOT_VERIFIED"),
        ):
            fake=copy.deepcopy(self.today)
            fake["first_party_JRA_win"][key]=value
            with self.assertRaisesRegex(ValueError,expected):
                compare(fake,self.yesterday,self.base)

    def test_one_JRA_price_corruption_or_name_change_rejected(self):
        fake=copy.deepcopy(self.today)
        fake["first_party_JRA_win"]["displayed_official_win_prices_all_17"][0][
            "official_displayed_win_odds"]=31.3
        # Retain this runner's market rank; otherwise the earlier
        # anti-mismatched-rank guard correctly fires before checking
        # JRA-vs-third-party quote identity.
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_JRA_AND_THIRD_PARTY_QUOTES"):
            compare(fake,self.yesterday,self.base)
        fake=copy.deepcopy(self.today)
        fake["first_party_JRA_win"]["displayed_official_win_prices_all_17"][0][
            "horse_name"]="FICTIONAL HORSE"
        with self.assertRaisesRegex(ValueError,"HOLD_ORIGINAL_OFFICIAL_HORSE"):
            compare(fake,self.yesterday,self.base)

    def test_incomplete_and_duplicate_wide_pair_market_HOLD(self):
        fake=copy.deepcopy(self.today)
        fake["separately_refreshed_SportsNavi"]["wide_odds_all_136"].pop()
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_COMPLETE_17_CHOOSE_2"):
            compare(fake,self.yesterday,self.base)
        fake=copy.deepcopy(self.today)
        v=fake["separately_refreshed_SportsNavi"]["wide_odds_all_136"]
        v[-1]["horse_numbers"]=v[0]["horse_numbers"]
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_PUBLIC_MARKET_PAIR"):
            compare(fake,self.yesterday,self.base)

    def test_fake_synchronized_quote_publication_claim_rejected(self):
        fake=copy.deepcopy(self.today)
        fake["separately_refreshed_SportsNavi"]["source_pages_NOT_atomic_cross_pool_snapshot"]=False
        with self.assertRaisesRegex(ValueError,"HOLD_UNRECONCILED_PUBLIC_WIDE"):
            compare(fake,self.yesterday,self.base)

    def test_do_not_rewrite_previous_qualitative_rank_later(self):
        fake=copy.deepcopy(self.yesterday)
        fake["observation_started_jst"]="2026-10-18T11:42:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_PREVIOUSLY_ARCHIVED_SATURDAY"):
            compare(self.today,fake,self.base)


if __name__=="__main__":
    unittest.main()
