#!/usr/bin/env python3
"""Nine price-index model assumptions reused on five real race podiums."""
import math
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from odds_five_race_market_assumption_sensitivity import (
    STATUS, GAMMAS, MAPPINGS, CHECK_MODELS, REPORT_METRICS,
    audit,
)


class FiveRaceWinWideAssumptionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=audit()

    def test_nine_regimes_reuse_only_five_races_from_one_date(self):
        a=self.out
        self.assertEqual(a["status"],STATUS)
        self.assertEqual(a["actual_independent_races"],5)
        self.assertEqual(a["actual_independent_meeting_dates"],1)
        self.assertEqual(a["full_WIN_horse_entries"],67)
        self.assertEqual(a["full_WIDE_pair_entries"],439)
        self.assertEqual(a["assumption_regimes_not_independent_realizations"],9)
        self.assertEqual(len(a["assumption_details"]),9)
        self.assertTrue(a["official_results_only_loaded_after_all_prestart_forecasts"])
        self.assertTrue(a["WIDE_payout_low_high_are_different_conditional_cases_not_sampling_CI"])

    def test_baseline_proper_scores_unchanged_across_all_nine_assumptions(self):
        regimes=self.out["assumption_details"]
        self.assertEqual(
            set(r["residual_PL_popularity_exponent_assumed"] for r in regimes),
            set(GAMMAS))
        self.assertEqual(
            set(r["WIDE_conditional_payout_price_mapping_assumed"] for r in regimes),
            set(MAPPINGS))
        for group in ("all_five","same_publisher_update_minute_three"):
            first=regimes[0]["cohorts"][group]["PL_baseline_scores"]
            for reg in regimes[1:]:
                curr=reg["cohorts"][group]["PL_baseline_scores"]
                for metric in REPORT_METRICS:
                    self.assertAlmostEqual(curr[metric],first[metric],places=10)
            if group=="all_five":
                self.assertAlmostEqual(first["win_categorical_log_loss"],
                                       1.9213897386345196,places=10)
                self.assertAlmostEqual(first["top3_per_horse_binary_brier"],
                                       .1299077756824236,places=10)
                self.assertAlmostEqual(first["unordered_top3_trio_log_loss"],
                                       4.248422957002073,places=10)

    def test_model_score_sensitivity_is_computed_without_threshold_fit(self):
        spans=self.out["sign_stability_by_group_model_and_proper_score"]
        self.assertEqual(set(spans),{
            "all_five","same_publisher_update_minute_three"})
        for group in spans.values():
            self.assertEqual(set(group),set(CHECK_MODELS))
            for model, scores in group.items():
                self.assertEqual(set(scores),set(REPORT_METRICS))
                for metric, s in scores.items():
                    self.assertTrue(math.isfinite(s["min_assumption_specific_delta"]))
                    self.assertTrue(math.isfinite(s["max_assumption_specific_delta"]))
                    self.assertLessEqual(s["min_assumption_specific_delta"],
                                         s["max_assumption_specific_delta"])
                    self.assertTrue(0<=s["cases_out_of_nine_model_better_than_PL"]<=9)
                    self.assertIsInstance(
                        s["sign_stable_across_nine_assumptions"],bool)
        baseline=next(x for x in self.out["assumption_details"]
                      if x["residual_PL_popularity_exponent_assumed"]==1.0
                      and x["WIDE_conditional_payout_price_mapping_assumed"]=="lower")
        deltas=baseline["cohorts"]["all_five"][
            "fixed_beta_model_minus_PL_score_deltas"]
        self.assertLess(
            deltas["pair_specific_positive_half"]["win_categorical_log_loss"],0)
        self.assertGreater(
            deltas["pair_specific_positive_half"]["unordered_top3_trio_log_loss"],0)
        print("FIVE_RACE_ASSUMPTION_QA " + json.dumps({
            name:{
                model:{
                    metric:{
                        "min":round(values["min_assumption_specific_delta"],6),
                        "max":round(values["max_assumption_specific_delta"],6),
                        "better_than_PL_out_of_9":
                            values["cases_out_of_nine_model_better_than_PL"],
                    } for metric,values in scores.items()
                } for model,scores in group.items()
            } for name,group in spans.items()
        },sort_keys=True))

    def test_models_are_unfitted_and_no_future_win_claim(self):
        params=self.out["fixed_coefficients_not_fit_to_podiums"]
        self.assertEqual(params["pair_specific_positive_half"],(0.0,0.5))
        self.assertEqual(params["horse_node_negative_half"],(-0.5,0.0))
        self.assertTrue(any("cannot determine a robust" in s
                            for s in self.out["limitations"]))
        self.assertTrue(any("not independent tests" in s
                            for s in self.out["limitations"]))


if __name__=="__main__":
    unittest.main()
