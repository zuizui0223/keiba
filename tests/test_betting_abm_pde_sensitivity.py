#!/usr/bin/env python3
"""Scientific-status and numerical invariants for synthetic betting ABM/PDE."""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from betting_abm_pde_sensitivity import (
    SNAPSHOT, exact_top3, first_passage, paired_delta, pde_gaussian_check,
    ranked, races_from_snapshot, scenario,
)


class TestBettingABMPDE(unittest.TestCase):
    def test_probability_mass_and_uniform_baseline(self):
        for n in (3, 8, 17):
            p = exact_top3(np.ones(n) * 5)
            for k, ps in enumerate(p, 1):
                np.testing.assert_allclose(ps, np.ones(n) * k / n, atol=1e-12)
                self.assertAlmostEqual(sum(ps), k, places=10)

    def test_odds_validation(self):
        for odds in ([1.2, 0.0, 3.0], [1.2, np.nan, 3.0], [1.2, 5]):
            with self.assertRaises(ValueError):
                exact_top3(odds)

    def test_crossing_time_matches_gumbel_order_without_pace_or_crowd(self):
        rng = np.random.default_rng(9)
        latent = rng.gumbel(size=(900, 8)) + np.log(np.arange(1, 9))[None, :]
        zero_pace = np.zeros_like(latent)
        times = first_passage(latent, zero_pace, 1600, 0.0)
        np.testing.assert_array_equal(np.argsort(times, axis=1),
                                      np.argsort(-latent, axis=1))

    def test_paired_difference_identical_outcomes_is_zero(self):
        order = np.tile([0, 2, 1, 3], (100, 1))
        for k in (1, 2, 3):
            out = paired_delta(order, order, 1, k)
            self.assertEqual(out["difference_percentage_points"], 0)
            self.assertEqual(out["monte_carlo_ci95_pp"], [0, 0])

    def test_synthetic_probabilities_and_determinism(self):
        odds = [2.1, 4.4, 6.6, 12.5, 27.0]
        a = scenario(odds, 1400, draws=350, seed=123)
        b = scenario(odds, 1400, draws=350, seed=123)
        self.assertEqual(a, b)
        for col in ("no_pack_win_pct", "strong_win_pct"):
            self.assertAlmostEqual(sum(h[col] for h in a["horses"]), 100, places=9)
        for col in ("market_top3_pct", "strong_top3_pct"):
            self.assertAlmostEqual(sum(h[col] for h in a["horses"]), 300, places=9)
        self.assertIn("NOT_CALIBRATED", a["status"])

    def test_pde_conservation(self):
        p = pde_gaussian_check()
        self.assertAlmostEqual(p["total_mass"], 1.0, places=10)
        self.assertTrue(p["nonnegative"])
        self.assertAlmostEqual(p["mean_m"], p["expected_mean_m"], delta=0.1)
        self.assertLess(p["l1_error_against_gaussian"], 0.025)

    def test_archive_is_nine_races_not_historical_behavior_panel(self):
        races = list(races_from_snapshot(SNAPSHOT))
        self.assertEqual(len(races), 9)
        self.assertEqual(sum(len(horses) for _, horses, _ in races), 117)
        self.assertTrue(all(distance >= 1000 for _, _, distance in races))
        observed_fields = set().union(*(h.keys() for _, horses, _ in races for h in horses))
        for missing in ("horse_id", "prior_sectional_time_s",
                        "running_style", "prior_finish_time_s"):
            self.assertNotIn(missing, observed_fields)

    def test_no_horse_specific_empirical_parameters_claimed(self):
        archive = list(races_from_snapshot(SNAPSHOT, "京都", 11))
        self.assertEqual(len(archive), 1)
        race, horses, distance = archive[0]
        out = scenario([h["win_odds"] for h in horses],
                       distance, draws=150, seed=21)
        self.assertEqual(out["n_horses"], 17)
        self.assertIn("synthetic", out["assumptions"]["speed"])
        self.assertEqual(out["assumptions"]["space"], "1D, no lanes or jockeys")


if __name__ == "__main__":
    unittest.main()
