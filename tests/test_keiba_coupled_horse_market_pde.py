#!/usr/bin/env python3
"""Regression tests for the coupled synthetic horse/market/PDE mechanism."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import numpy as np
except ImportError:
    np = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
if np is not None:
    import keiba_coupled_horse_market_pde as m


def demo_row():
    return {
        "race_id": "SYNTHETIC", "race_no": 8, "meeting_day": "2026-10-12",
        "first_odds": {1: 2.9, 2: 5.3, 3: 8.5, 4: 12.0, 5: 22.0, 6: 35.0},
        "last_odds": {1: 3.1, 2: 5.1, 3: 8.9, 4: 10.8, 5: 21.0, 6: 40.0},
        "initial_quote_at": "2026-10-12T12:00:00+09:00",
        "latest_quote_at": "2026-10-12T13:00:00+09:00",
        "post_at": "2026-10-12T15:00:00+09:00",
    }


@unittest.skipIf(np is None, "Numerical coupled tests run with NumPy in dedicated CI")
class CoupledPureMathTest(unittest.TestCase):
    def test_sde_two_mechanisms_share_crowd_counterfactual_inputs(self):
        q = m.vector([.4, .2, .16, .1, .08, .06])
        a = m.brownian_horse_ensemble(q, 1400, draws=120, seed=52)
        b = m.brownian_horse_ensemble(q, 1400, draws=120, seed=52)
        for mode in ("no_pack", "weak"):
            for event, mass in (("win", 1), ("top3", 3)):
                np.testing.assert_array_equal(a[mode][event], b[mode][event])
                self.assertAlmostEqual(sum(a[mode][event]), mass, places=12)
        self.assertEqual(a["physics"]["diffusion_m2_per_s"], m.DIFFUSION_M2_PER_S)

    def test_sde_zero_noise_order_is_ability_order(self):
        latent = np.asarray([[-3, -2, -1, 0, 1, 2]]*2, dtype=float)
        pace = np.zeros_like(latent)
        initial = np.zeros_like(latent)
        noise = np.zeros((65, 2, 6))
        arrive = m._finish_times(latent, pace, initial, noise,
                                 distance_m=1000, dt_s=2, crowd_mps=0)
        np.testing.assert_array_equal(np.argsort(arrive, axis=1),
                                      np.asarray([[5, 4, 3, 2, 1, 0]]*2))

    def test_market_agent_pool_conservation_and_modes(self):
        q = [.40, .20, .15, .10, .09, .06]
        sig = [.22, .20, .19, .15, .14, .10]
        for mode in m.MIXED_MODES:
            out = m.vote_market(q, sig, mode=mode, duration_hours=1.0,
                                seed=30, steps=5,
                                synthetic_prior_stakes=1000,
                                synthetic_votes_per_step=100)
            self.assertEqual(len(out["path"]), 6)
            self.assertEqual(out["new_vote_count_assumption"], 500)
            self.assertTrue(all(abs(p.sum()-1) < 1e-12 for p in out["path"]))
        no_stakes = m.vote_market(q, sig, mode="information",
                duration_hours=1, seed=9, synthetic_votes_per_step=0)
        np.testing.assert_allclose(no_stakes["final"], m.vector(q), atol=1e-14)

    def test_paired_voter_randomness_cancels_for_same_policy_distribution(self):
        q = [.40, .20, .15, .10, .09, .06]
        a = m.vote_market(q, q, mode="independent", duration_hours=1.,
                          seed=137, steps=4)
        b = m.vote_market(q, q, mode="information", duration_hours=1.,
                          seed=137, steps=4)
        for x, y in zip(a["path"], b["path"]):
            np.testing.assert_array_equal(x, y)

    def test_bad_market_inputs_rejected(self):
        with self.assertRaisesRegex(ValueError, "MARKET_HORSE_MISMATCH"):
            m.vote_market([1,2,3,4,5], [1,2,3,4,5,6], mode="information",
                          duration_hours=1)
        with self.assertRaisesRegex(ValueError, "MARKET_MODE"):
            m.vote_market([1,2,3,4,5], [1,2,3,4,5], mode="unknown",
                          duration_hours=1)

    def test_full_coupling_probability_mass_and_price_vs_outcome_separation(self):
        x = m.couple_prestart(demo_row(), distance_m=1400, draws=90,
                              seed=40, votes_per_step=100)
        self.assertEqual(set(x["predictions"]), set(m.REPORT_MODELS))
        self.assertEqual(x["horse_entries"], 6)
        self.assertTrue(x["not_an_independent_horse_ability_estimate"])
        self.assertTrue(x["event_probability_no_double_count"])
        for name, p in x["predictions"].items():
            self.assertAlmostEqual(sum(p["win"]), 1, places=9, msg=name)
            self.assertAlmostEqual(sum(p["top3"]), 3, places=9, msg=name)
        self.assertTrue(all("M3_initial10_speed010" in x["market_paths"][k]["M0_to_M3"]
                            for k in m.MIXED_MODES))
        for k in m.MIXED_MODES:
            joint=x["market_paths"][k]["joint_all_ticket_events"]
            self.assertAlmostEqual(sum(joint["win"].values()), 1, places=10)
            self.assertAlmostEqual(sum(joint["top2"].values()), 2, places=10)
            self.assertAlmostEqual(sum(joint["top3"].values()), 3, places=10)
            self.assertAlmostEqual(sum(joint["both_top3_pair"].values()), 3, places=10)
            self.assertAlmostEqual(sum(joint["unordered_top3_trio"].values()), 1, places=10)
            self.assertAlmostEqual(sum(joint["ordered_firsttwo_exacta"].values()), 1, places=10)
            self.assertAlmostEqual(sum(joint["ordered_top3_trifecta"].values()), 1, places=10)

    def test_same_early_price_and_horse_state_ignore_later_quote_for_simulation(self):
        row = demo_row()
        a = m.couple_prestart(row, distance_m=1200, draws=80,
                               seed=19, votes_per_step=90)
        later = dict(row["last_odds"])
        later[3] *= 1.7
        later[5] *= .8
        row2 = {**row, "last_odds": later,
                "winner": 5, "official_top3": [5, 3, 1], "payout": 9999}
        b = m.couple_prestart(row2, distance_m=1200, draws=80,
                               seed=19, votes_per_step=90)
        np.testing.assert_array_equal(a["horse_signal"], b["horse_signal"])
        for k in m.MIXED_MODES:
            np.testing.assert_array_equal(a["market_paths"][k]["final"],
                                          b["market_paths"][k]["final"])
            self.assertNotEqual(
                a["market_paths"][k]["TV_to_archived_later_quote_pp"],
                b["market_paths"][k]["TV_to_archived_later_quote_pp"])
        self.assertNotEqual(a["predictions"]["observed_M0"],
                            b["predictions"]["observed_M0"])

    def test_determinism_of_three_link_joint_flow(self):
        a = m.couple_prestart(demo_row(), distance_m=1200,
                              draws=80, seed=20)
        b = m.couple_prestart(demo_row(), distance_m=1200,
                              draws=80, seed=20)
        for label in m.REPORT_MODELS:
            self.assertEqual(a["predictions"][label],
                             b["predictions"][label])
        for mode in m.MIXED_MODES:
            np.testing.assert_array_equal(a["market_paths"][mode]["final"],
                                          b["market_paths"][mode]["final"])

    def test_invalid_timestamps_and_roster_do_not_enter_model(self):
        row = demo_row()
        row["latest_quote_at"] = row["post_at"]
        with self.assertRaisesRegex(ValueError, "TOO_LATE"):
            m.couple_prestart(row, distance_m=1200, draws=80)
        row = demo_row()
        row["last_odds"].pop(1)
        with self.assertRaisesRegex(ValueError, "FULL_FIELD"):
            m.couple_prestart(row, distance_m=1200, draws=80)


@unittest.skipIf(np is None or not (ROOT/"data/2026-10-12/kyoto_08.json").exists(),
                 "Full source-locked checkout and NumPy required")
class RealArchiveCouplingTest(unittest.TestCase):
    def test_real_six_race_prestart_firewall_and_shared_PDE(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("POSTRACE_LABEL_LEAK")):
            a = m.audit(prestart_only=True, draws=60, seed=20261025)
        self.assertEqual(a["cohort"]["races"], 6)
        self.assertEqual(a["cohort"]["meeting_dates"], 2)
        self.assertEqual(a["cohort"]["horse_race_entries"], 84)
        self.assertEqual(a["postrace"], "NOT_COMPUTED")
        self.assertAlmostEqual(a["physics_SDE_to_PDE"]["pde_mass"], 1, places=8)
        self.assertLess(a["physics_SDE_to_PDE"]["max_CDF_gap"], .06)
        self.assertEqual(a["horse_abm"]["legacy_P9_reused_unmodified"], True)
        self.assertEqual(a["real_calibrated_forecast_advantage"], "HOLD")

    def test_seed_sensitivity_has_no_independent_new_races(self):
        from keiba_coupled_seed_sensitivity import sensitivity
        report = sensitivity(n_seeds=2, draws=40, first_seed=20261025)
        self.assertEqual(report["real_independent_races"], 6)
        self.assertEqual(report["synthetic_seed_repetitions_not_new_independent_trials"], 2)
        self.assertTrue(report["any_score_advantage_is_retrospective_and_unvalidated"])
        self.assertEqual(len(report["seeds"]), 2)

    def test_real_results_only_score_after_all_forecasts_generated(self):
        report = m.audit(draws=60, seed=20261025)
        z = report["postrace"]
        self.assertEqual(z["status"],
                         "RETROSPECTIVE_SIX_REAL_OUTCOMES_ONLY_NOT_PROSPECTIVE")
        self.assertAlmostEqual(z["mean_race_equal_winner_log_loss"]["observed_M0"],
                               1.696959293802405, places=8)
        self.assertAlmostEqual(z["mean_race_equal_winner_log_loss"]["observed_M1"],
                               1.696681573413395, places=8)
        self.assertTrue(z["no_parameter_tuning_to_any_of_six_actual_winners"])
        tickets=z["mean_coherent_ticket_scores_race_equal"]
        self.assertEqual(set(tickets), {"observed_M0", *m.MIXED_MODES})
        self.assertGreater(tickets["observed_M0"]["unordered_trio_log_loss"], 0)
        self.assertTrue(report["all_ticket_markets"]["sourced_from_same_ordered_finish_distribution"])
        for a in m.REPORT_MODELS:
            self.assertGreater(z["mean_race_equal_winner_log_loss"][a], 0)


if __name__ == "__main__":
    unittest.main()
