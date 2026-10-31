#!/usr/bin/env python3
"""Prestart single-source M0 fragility tests. No result or q2 inputs."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import keiba_tenno_20261101_m0_rank_stability as m


class PublishedQuoteRankStabilityTests(unittest.TestCase):
    def test_reuse_exact_parent_source_not_renumbered_or_overwritten(self):
        odds, digest = m.declared_field()
        self.assertEqual(len(odds), 17)
        self.assertEqual(odds[7], 2.4)
        self.assertEqual(odds[1], 2.5)
        self.assertEqual(digest, m.PINNED_DECLARED_FIELD_SHA256)
        self.assertEqual(len(list(__import__("itertools").combinations(odds, 2))),
                         136)

    def test_detect_original_price_change_even_if_ranking_stays_same(self):
        odds, _ = m.declared_field()
        fake = dict(odds)
        fake[7] = 2.41
        with patch.object(m, "_field", return_value=fake):
            with self.assertRaisesRegex(ValueError,
                                        "HOLD_PRESTART_DECLARED_FIELD_CHANGED"):
                m.declared_field()

    def test_exact_17_competitor_extrema_and_probability_mass(self):
        odds, _ = m.declared_field()
        delta = .05
        b = m.bounded_index(odds, delta)
        w = {i:1/odds[i] for i in odds}
        self.assertAlmostEqual(sum(x["M0_at_reported_quote"]
                                   for x in b.values()), 1.0, places=12)
        for i in odds:
            lo = w[i]*math.exp(-delta) / (
                w[i]*math.exp(-delta) +
                sum(w[j]*math.exp(delta) for j in odds if j != i))
            hi = w[i]*math.exp(delta) / (
                w[i]*math.exp(delta) +
                sum(w[j]*math.exp(-delta) for j in odds if j != i))
            self.assertAlmostEqual(
                b[str(i)]["exact_min_if_all_other_quotes_move_oppositely"],
                lo, places=12)
            self.assertAlmostEqual(
                b[str(i)]["exact_max_if_all_other_quotes_move_oppositely"],
                hi, places=12)
        self.assertAlmostEqual(
            b["7"]["exact_min_if_all_other_quotes_move_oppositely"],
            .3064558777114801, places=12)
        self.assertAlmostEqual(
            b["7"]["exact_max_if_all_other_quotes_move_oppositely"],
            .35052300641096046, places=12)

    def test_symmetrical_2pct_log_shock_crossing_not_phase_transition(self):
        odds, _ = m.declared_field()
        margin = .5*math.log(2.5/2.4)
        self.assertAlmostEqual(margin, .0204109972601276, places=12)
        self.assertFalse(any(
            set(p["horse_numbers_baseline_order"]) == {1,7}
            for p in m.pair_robustness(odds, .02)))
        self.assertTrue(any(
            set(p["horse_numbers_baseline_order"]) == {1,7}
            for p in m.pair_robustness(odds, .025)))
        self.assertEqual(m.pair_robustness(odds, 0), [])
        self.assertEqual(len(m.pair_robustness(odds, .025)), 2)
        self.assertEqual(len(m.pair_robustness(odds, .05)), 6)

    def test_robust_top_two_set_even_though_internal_order_can_flip(self):
        odds, _ = m.declared_field()
        x = m.top_group(odds, 2, .05)
        self.assertEqual(x["horse_numbers_baseline_top_k"], [1,7])
        self.assertTrue(
            x["strict_top_k_set_invariant_for_all_declared_shocks"])
        self.assertAlmostEqual(
            x["smallest_symmetric_absolute_log_price_shock_for_boundary_tie"],
            .5*math.log(9.8/2.5), places=12)
        self.assertFalse(m.top_group(odds, 1, .05)[
            "strict_top_k_set_invariant_for_all_declared_shocks"])
        self.assertTrue(m.top_group(odds, 3, .05)[
            "strict_top_k_set_invariant_for_all_declared_shocks"])
        self.assertFalse(m.top_group(odds, 3, .10)[
            "strict_top_k_set_invariant_for_all_declared_shocks"])

    def test_no_market_mechanism_or_real_predictive_edge_claimed(self):
        a = m.audit()
        self.assertEqual(a, m.audit())
        self.assertEqual(a["horse_count"], 17)
        self.assertEqual(a["unique_rank_pairs"], 136)
        self.assertEqual(a["status"], m.STATUS)
        self.assertTrue(a["price_rank_crossing_is_NOT_dynamic_market_tipping"])
        self.assertTrue(a["shock_is_counterfactual_not_observed_time_series"])
        self.assertTrue(a["only_one_source_reported_WIN_quote_timestamp"])
        self.assertFalse(a["official_target_race_results_used"])
        self.assertFalse(a["independent_future_quote_for_scoring_available"])
        self.assertEqual(a["real_asof_authenticated_source_receipt_count"], 0)
        self.assertEqual(
            [x["ambiguous_or_reversible_rank_pair_count"]
             for x in a["hypothetical_shock_scenarios"]], [0,0,2,6,11])
        self.assertFalse(a["hypothetical_shock_scenarios"][3][
            "top_group_set_invariance"]["1"][
                "strict_top_k_set_invariant_for_all_declared_shocks"])
        self.assertTrue(a["hypothetical_shock_scenarios"][3][
            "top_group_set_invariance"]["2"][
                "strict_top_k_set_invariant_for_all_declared_shocks"])
        json.dumps(a, allow_nan=False, ensure_ascii=False)

    def test_fail_closed_on_invalid_shocks_and_runner_incompleteness(self):
        odds, _ = m.declared_field()
        for d in (float("nan"), float("inf"), -1e-3, .501, "0.05"):
            with self.subTest(delta=str(d)):
                with self.assertRaisesRegex(ValueError,
                                            "HOLD_UNDECLARED_PRICE_SHOCK_BOUNDS"):
                    m.bounded_index(odds, d)
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_NOT_THE_SEALED_17_HORSE_FIELD"):
            m.bounded_index({7:2.4,1:2.5}, .05)
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_TOP_GROUP_SIZE"):
            m.top_group(odds, 17, .05)

    def test_json_output_is_standard_and_leakage_free(self):
        with tempfile.TemporaryDirectory() as root:
            import subprocess
            target = Path(root)/"rank.json"
            run = subprocess.run([
                sys.executable,
                str(ROOT/"scripts"/"keiba_tenno_20261101_m0_rank_stability.py"),
                "--output", str(target)
            ], check=True, text=True, capture_output=True)
            output = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(output, m.audit())
            self.assertIn("NO_REAL_Q2_AND_NO_DYNAMIC_TIPPING_INFERENCE True",
                          run.stdout)


if __name__ == "__main__":
    unittest.main()
