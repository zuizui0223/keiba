#!/usr/bin/env python3
"""Falsify equating cumulative odds memory with bettor imitation."""
import copy
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from odds_market_accounting_null import (
    STATUS, audit, conditional_identification, flow_witness,
    negative_control,
)
from shuka2026_odds_information_hierarchy import read_locked, load_snapshots, share


class AccountingVsHerdingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots = load_snapshots(read_locked())

    def test_exact_simplex_bound_is_sharp_for_known_toy(self):
        q0 = {1: .6, 2: .3, 3: .1}
        q1 = {1: .48, 2: .4, 3: .12}
        estimate = conditional_identification(q0, q1)
        self.assertAlmostEqual(
            estimate["minimum_new_fraction_of_final_pool_conditional_on_exact_share_proxy"],
            .2)
        self.assertAlmostEqual(
            estimate["minimum_new_to_previous_pool_ratio_conditional"], .25)
        new = flow_witness(q0, q1, .2)
        self.assertAlmostEqual(new[1], 0)
        self.assertAlmostEqual(new[2], .8)
        self.assertAlmostEqual(new[3], .2)
        with self.assertRaisesRegex(ValueError, "HOLD_FLOW_REQUIRES_NEGATIVE"):
            flow_witness(q0, q1, .199)
        alternate = flow_witness(q0, q1, .6)
        self.assertNotEqual(alternate, new)
        for idx in q0:
            self.assertAlmostEqual(q1[idx], .4*q0[idx] + .6*alternate[idx])
        self.assertAlmostEqual(sum(alternate.values()), 1)

    def test_all_three_actual_quote_proxy_bounds_and_caveat(self):
        v = audit(paths=20, seed=40)
        self.assertEqual(v["status"], STATUS)
        intervals = v["observed_intervals_conditional_on_proxy"]
        self.assertEqual(len(intervals), 3)
        expected = [5.633341553531956, 17.202998646422618,
                    2.7504690333371107]
        for row, actual in zip(intervals, expected):
            self.assertAlmostEqual(
                100*row["minimum_new_fraction_of_final_pool_conditional_on_exact_share_proxy"],
                actual, delta=.000001)
            self.assertGreaterEqual(
                row["minimum_new_fraction_of_final_pool_conditional_on_exact_share_proxy"],
                row["total_variation_share_fraction"]-1e-12)
            w = row["three_distinct_feasible_unobserved_flow_explanations"]
            self.assertNotEqual(
                w["near_minimum"]["synthetic_new_share_favorite"],
                w["all_new"]["synthetic_new_share_favorite"])
        self.assertTrue(v["earliest_capture_is_not_opening_odds"])
        self.assertIn("not verified actual JRA pool", v["source_not_atomic_and_odds_not_actual_pool_shares"])
        self.assertEqual(
            v["inference_decision"]["actual_new_pool_fraction"],
            "HOLD_TOTAL_SALES_NOT_OBSERVED")
        self.assertFalse(v["inference_decision"]["jra_direct_accounting_inverted"])

    def test_source_switch_keeps_identification_conditional(self):
        v = audit(paths=12)
        q = v["observed_intervals_conditional_on_proxy"]
        self.assertFalse(q[0]["source_change"])
        self.assertTrue(q[1]["source_change"])
        self.assertFalse(q[2]["source_change"])
        self.assertTrue(all(row["cannot_estimate_actual_sales_or_herding"] for row in q))

    def test_independent_uniform_votes_still_preserve_prior_rank(self):
        p = share(self.snapshots[0]["win"])
        v = negative_control(p, paths=100, seed=33, prior_votes=10000,
                             newly_cast_votes=1600)
        self.assertFalse(v["observed_market_actual_turnover_inferred"])
        self.assertAlmostEqual(
            v["mechanical_fraction_of_initial_votes_retained"],
            10000/11600, places=12)
        null = v["results"]["independent_uniform_new_votes"]
        self.assertGreater(null["mean_across_horse_prior_vs_final_share_Pearson"], .99)
        self.assertGreater(null["fraction_final_market_top5_membership_unchanged"], .95)
        self.assertAlmostEqual(
            null["mean_favorite_relative_weight_pct"],
            v["assumed_no_herding_uniform_expected_favorite_pct"],
            delta=.8)

    def test_synthetic_mechanisms_are_reproducible_but_not_estimated(self):
        p = share(self.snapshots[0]["win"])
        a = negative_control(p, paths=35, seed=8, newly_cast_votes=120)
        b = negative_control(p, paths=35, seed=8, newly_cast_votes=120)
        self.assertEqual(a,b)
        self.assertNotEqual(
            a["results"]["independent_uniform_new_votes"]["mean_favorite_relative_weight_pct"],
            a["results"]["herding_onto_current_popularity"]["mean_favorite_relative_weight_pct"])

    def test_broken_market_vectors_and_flow_weights_fail(self):
        q0={1:.6,2:.3,3:.1}
        q1={1:.48,2:.4,3:.12}
        for broken in ({1:.6,2:.2,3:.1}, {1:.6,2:.3,3:-.1}):
            with self.assertRaises(ValueError):
                conditional_identification(broken,q1)
        with self.assertRaises(ValueError):
            conditional_identification(q0,{1:.5,2:.5,4:0})
        with self.assertRaises(ValueError):
            flow_witness(q0,q1,0)
        with self.assertRaises(ValueError):
            negative_control(q0,paths=1)

    def test_no_actual_outcomes_or_formal_holdout(self):
        v = audit(paths=10)
        self.assertEqual(v["inference_decision"]["winner_top3_threshold_predictiveness"],
                         "HOLD_SINGLE_RACE_NO_PROSPECTIVE_TEST")
        self.assertEqual(v["inference_decision"]["social_herding_causal_effect"],
                         "HOLD_NONIDENTIFIED_FROM_CUMULATIVE_PRICES")
        self.assertFalse(v["inference_decision"]["v31_frozen_thresholds_changed"])


if __name__=="__main__":
    unittest.main()
