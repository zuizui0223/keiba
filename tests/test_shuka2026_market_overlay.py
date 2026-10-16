"""Synthetic ONLY price rows; never use invented odds as real Shuka Sho odds.

Checks exactly locked v3.1 market_channel on official JRA 17-runner
horse-number crosswalk, source temporal gates and candidate coverage.
"""
from __future__ import annotations

import copy
from datetime import datetime
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from shuka2026_market_overlay import (
    source_base,scenario_bounds,run_market_overlay,
    validate_actual_JRA_win_odds_snapshot,
)


def fake_after_sale(top_numbers:list[int], *,
                    first_actual_sale_time:str="2026-10-16T18:35:00+09:00"):
    """Clearly FICTIONAL unit-test odds; not a real future or current market."""
    top=set(top_numbers)
    return {
        "schema":"JRA_OFFICIAL_SHUKA2026_ACTUAL_WIN_ODDS_V1",
        "race_id":"2026-10-18-KYOTO-11",
        "quote_type":"actual_displayed_win_odds",
        "is_pre_race":True,
        "source_url":"https://www.jra.go.jp/JRADB/accessO.html?CNAME=FICTIONAL-TEST-NOT-REAL",
        "observed_at_jst":first_actual_sale_time,
        "horses":[
            {"number":n,"win_odds":5.0 if n in top else 90.+n}
            for n in range(1,18)
        ],
        "fake_test_fixture_is_not_a_real_2026_JRA_source":True,
    }


class ActualJRAOddsConditionalV31Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.historical=source_base()

    def test_must_not_invent_real_m_before_any_quote(self):
        result=run_market_overlay(self.historical)
        self.assertEqual(result["status"],
            "HOLD_UNTIL_ACTUAL_JRA_WIN_ODDS_ARE_AVAILABLE")
        self.assertIsNone(result["market_M_numbers"])
        self.assertIsNone(result["full_union_candidate_numbers"])
        self.assertEqual(result["historical_C1_U_Q1_AND_K1_candidates"],
                         [1,3,6,8,9,12])
        self.assertEqual(result["JRA_2026_GI_first_advance_sale_opens_at_JST"],
                         "2026-10-16T18:30:00+09:00")
        self.assertTrue(result["formal_20_race_v31_holdout_score_NOT_modified"])

    def test_nominal_market_five_union_between_6_and_11(self):
        scenario=scenario_bounds()
        self.assertEqual(scenario["frozen_M_nominal_top_quarter_count_without_ties"],5)
        self.assertEqual(scenario["nominal_M_no_ties_final_union_min"],6)
        self.assertEqual(scenario["nominal_M_no_ties_final_union_max"],11)
        self.assertEqual(scenario["maximum_candidate_count_below_or_equal_65pct"],11)
        self.assertEqual(scenario["source_field_size"],17)

    def test_synthetic_market_all_five_historical_six_keeps_six(self):
        result=run_market_overlay(
            self.historical,fake_after_sale([1,3,6,8,9])
        )
        self.assertEqual(result["market_M_numbers"],[1,3,6,8,9])
        self.assertEqual(result["full_union_candidate_numbers"],
                         [1,3,6,8,9,12])
        self.assertEqual(result["full_union_size"],6)
        self.assertEqual(result["market_M_only_not_historical_candidates"],[])
        self.assertFalse(result["candidate_rate_above_65pct"])
        self.assertTrue(result["snapshot_independent_source_text_byte_VERIFICATION_NOT_DONE"])
        self.assertIsNone(result.get("calibrated_win_probability"))

    def test_synthetic_market_zero_overlap_yields_eleven_at_64_7pct(self):
        result=run_market_overlay(
            self.historical,fake_after_sale([2,4,5,7,10])
        )
        self.assertEqual(result["market_M_numbers"],[2,4,5,7,10])
        self.assertEqual(result["full_union_candidate_numbers"],
                         [1,2,3,4,5,6,7,8,9,10,12])
        self.assertEqual(result["full_union_size"],11)
        self.assertAlmostEqual(result["candidate_fraction"],11/17)
        self.assertFalse(result["candidate_rate_above_65pct"])

    def test_synthetic_market_one_overlap_means_ten_of_seventeen(self):
        result=run_market_overlay(
            self.historical,fake_after_sale([2,4,5,7,8])
        )
        self.assertEqual(result["overlap_M_with_history_count"],1)
        self.assertEqual(result["full_union_size"],10)
        self.assertAlmostEqual(result["candidate_fraction"],10/17)

    def test_synthetic_six_way_cutoff_tie_can_overshoot_65percent(self):
        result=run_market_overlay(
            self.historical,fake_after_sale([2,4,5,7,10,11])
        )
        self.assertEqual(result["market_M_size_including_ties"],6)
        self.assertEqual(result["full_union_size"],12)
        self.assertAlmostEqual(result["candidate_fraction"],12/17)
        self.assertTrue(result["candidate_rate_above_65pct"])
        self.assertTrue(result["no_claim_betting_expectation_or_calibrated_horse_probabilities"])
        summary=scenario_bounds()["all_possible_M_size_support_not_market_prediction"]
        m6=next(x for x in summary if x["market_M_size_including_cutoff_ties"]==6)
        self.assertEqual(m6[
            "required_MIN_overlap_with_six_existing_candidates_to_keep_union_le_65pct"],1)

    def test_before_real_sale_friday_afternoon_is_HOLD(self):
        with self.assertRaisesRegex(ValueError,
            "HOLD_JRA_NOT_IN_REAL_ADVANCE_OR_RACE_SALE_WINDOW"):
            validate_actual_JRA_win_odds_snapshot(
                fake_after_sale([1,2,3,4,5],
                    first_actual_sale_time="2026-10-16T14:34:00+09:00")
            )

    def test_saturday_sale_break_is_HOLD_and_new_session_accepts(self):
        with self.assertRaisesRegex(ValueError,
            "HOLD_JRA_NOT_IN_REAL_ADVANCE_OR_RACE_SALE_WINDOW"):
            validate_actual_JRA_win_odds_snapshot(
                fake_after_sale([1,2,3,4,5],
                    first_actual_sale_time="2026-10-17T18:00:00+09:00")
            )
        t,_=validate_actual_JRA_win_odds_snapshot(
            fake_after_sale([1,2,3,4,5],
                first_actual_sale_time="2026-10-17T19:30:00+09:00")
        )
        self.assertEqual(t.hour,19)

    def test_full_valid_prices_in_actual_fixed_window_are_still_shadow(self):
        fake=fake_after_sale([1,2,3,4,5],
            first_actual_sale_time="2026-10-18T15:20:00+09:00")
        r=run_market_overlay(self.historical,fake)
        self.assertTrue(r[
            "shadow_only_not_a_formal_holdout_freeze_even_if_15_25min_before_start"])
        self.assertFalse(r["formal_20_race_v31_holdout_score_NOT_modified"] is False)

    def test_real_price_input_must_have_all_17_numbers_once(self):
        x=fake_after_sale([1,3,6,8,9])
        x["horses"][0]["number"]=2
        with self.assertRaisesRegex(ValueError,
            "HOLD_DUPLICATE_OR_MISSING_JRA_RUNNER_IN_ACTUAL_ODDS"):
            validate_actual_JRA_win_odds_snapshot(x)
        x=fake_after_sale([1,3,6,8,9])
        x["horses"].pop()
        with self.assertRaisesRegex(ValueError,
            "HOLD_INCOMPLETE_17_RUNNER_ACTUAL_WIN_ODDS"):
            validate_actual_JRA_win_odds_snapshot(x)

    def test_false_market_source_missing_times_or_guessed_prices_fail(self):
        for key, value, message in (
            ("source_url","https://example.invalid/odds",
             "HOLD_ORIGINAL_WIN_ODDS_URL_NOT_OFFICIAL_JRA"),
            ("observed_at_jst","2026-10-16T18:35:00",
             "HOLD_MARKET_TIMESTAMP_NOT_JST_OFFSET_AWARE"),
            ("quote_type","forecast_win_odds",
             "HOLD_NOT_CORRECT_RACE_OR_PRE_RESULT_OFFICIAL_WIN_MARKET"),
            ("race_id","2026-10-12-KYOTO-11",
             "HOLD_NOT_CORRECT_RACE_OR_PRE_RESULT_OFFICIAL_WIN_MARKET"),
        ):
            z=fake_after_sale([1,3,6,8,9])
            z[key]=value
            with self.assertRaisesRegex(ValueError,message):
                validate_actual_JRA_win_odds_snapshot(z)

    def test_nan_infinite_or_below_one_price_are_rejected(self):
        for value in (float("nan"),float("inf"),0.4,None):
            z=fake_after_sale([1,3,6,8,9])
            z["horses"][0]["win_odds"]=value
            with self.assertRaisesRegex(ValueError,"HOLD_UNOBSERVED_WIN_ODDS_VALUE"):
                validate_actual_JRA_win_odds_snapshot(z)

    def test_candidate_union_does_not_encode_fake_probabilities(self):
        result=run_market_overlay(
            self.historical,fake_after_sale([2,4,5,7,10])
        )
        self.assertTrue(result["no_claim_betting_expectation_or_calibrated_horse_probabilities"])
        thresholds=result["reciprocal_ODDS_as_mathematical_breakeven_not_win_probability"]
        self.assertAlmostEqual(thresholds["2"],1/5)
        self.assertNotIn("expected_value",result)
        self.assertIsNone(result.get("confidence_interval"))


if __name__=="__main__":
    unittest.main()
