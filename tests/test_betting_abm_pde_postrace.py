#!/usr/bin/env python3
"""Nine-race official-result retrospective scorer and toy PDE-particle bridge."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
except ModuleNotFoundError:
    np = None  # The dedicated numerical CI installs NumPy; generic CI stays stdlib-only.

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
if np is not None:
    from betting_abm_pde_postrace_audit import (
        RESULTS, STATUS, evaluate, load_results, probability_score,
    )
    from betting_abm_pde_particle_bridge import (
        STATUS as PDE_STATUS, compare_particle_density,
    )


@unittest.skipIf(np is None, "numerical add-on requires NumPy in dedicated CI")
class TestPostraceAuditAndBridge(unittest.TestCase):
    def test_nine_races_have_unique_real_podium_numbers_and_sources(self):
        res = load_results(RESULTS)
        self.assertEqual(len(res), 9)
        self.assertEqual(len({r["official_results_url"] for r in res.values()}), 9)

    def test_market_only_fixed_reference_and_timing_gate(self):
        x = evaluate(market_only=True)
        self.assertEqual(x["status"], STATUS)
        self.assertEqual(x["race_count"], 9)
        self.assertEqual(x["total_horse_entries"], 117)
        self.assertEqual(x["market_odds_top3_hits_of_total"],
                         {"hits": 17, "top3_slots": 27})
        sc = x["overall_mean_by_model"]
        self.assertEqual(set(sc), {"uniform", "market_PL"})
        self.assertAlmostEqual(sc["market_PL"]["winner_log_loss"],
                               1.9118761430864737, places=8)
        self.assertAlmostEqual(sc["uniform"]["winner_log_loss"],
                               2.5370368049504455, places=8)
        self.assertAlmostEqual(sc["market_PL"]["top3_binary_brier_mean_horse"],
                               0.13643337754830498, places=8)
        self.assertAlmostEqual(sc["uniform"]["top3_binary_brier_mean_horse"],
                               0.18125537485930032, places=8)
        self.assertLess(sc["market_PL"]["winner_log_loss"],
                        sc["uniform"]["winner_log_loss"])

    def test_probabilities_reject_wrong_mass(self):
        with self.assertRaisesRegex(ValueError, "invalid_probability_mass"):
            probability_score([.5,.5,.5],[1,1,1],[1,2,3],[1,2,3])

    def test_no_performance_leakage_from_results_into_abm_features(self):
        x = evaluate(runs=75, seed=40)
        y = evaluate(runs=75, seed=40)
        self.assertEqual(x, y)
        self.assertEqual(x["simulation_repetitions_per_race_and_scenario"], 75)
        self.assertIn("synthetic_ABM_strong", x["overall_mean_by_model"])
        for row in x["per_race"]:
            self.assertEqual(len(row["actual_top3"]), 3)
            self.assertEqual(len(row["model_scores"]), 5)

    def test_invalid_results_source_and_outcomes_hard_fail(self):
        source = json.loads(RESULTS.read_text(encoding="utf-8"))
        for change in (
                lambda j: j["races"][0].update(finish_order_top3=[7, 7, 3]),
                lambda j: j["races"][0].update(finish_order_top3=[7, 8, 99]),
                lambda j: j["races"][0].update(official_results_url="https://example.com/a"),
                lambda j: j.update(status="PROSPECTIVE_HOLDOUT")):
            edited = json.loads(json.dumps(source))
            change(edited)
            with tempfile.TemporaryDirectory() as t:
                p = Path(t) / "results.json"
                p.write_text(json.dumps(edited), encoding="utf-8")
                with self.assertRaises(ValueError):
                    evaluate(results_path=p, market_only=True)

    def test_too_late_odds_hard_fail(self):
        from betting_abm_pde_sensitivity import SNAPSHOT
        archive = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        archive["observed_window_end_jst"] = "2026-10-18T13:16:00+09:00"
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "late_odds.json"
            p.write_text(json.dumps(archive), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not_pre_start"):
                evaluate(odds_path=p, market_only=True)

    def test_independent_particle_pde_consistency(self):
        s = compare_particle_density(particles=20000, seed=31)
        self.assertEqual(s["status"], PDE_STATUS)
        self.assertAlmostEqual(s["pde_mass"], 1.0, places=9)
        self.assertAlmostEqual(s["abm_mass_on_grid"], 1.0, places=8)
        self.assertEqual(s["out_of_domain_particles"], 0)
        self.assertTrue(s["pde_nonnegative"])
        self.assertLess(s["kolmogorov_cdf_error"], 0.03)
        self.assertLess(s["l1_error_abm_vs_pde_density"], 0.14)
        self.assertLess(s["l1_error_pde_vs_analytic_gaussian"], 0.03)
        self.assertAlmostEqual(s["abm_mean_m"], s["expected_mean_m"], delta=0.28)
        self.assertAlmostEqual(s["pde_mean_m"], s["expected_mean_m"], delta=0.25)

    def test_reverse_drift_and_stability(self):
        v = compare_particle_density(particles=2000, seed=2, drift=-0.4)
        self.assertLess(v["abm_mean_m"], 0)
        self.assertLess(v["pde_mean_m"], 0)
        with self.assertRaises(ValueError):
            compare_particle_density(dt=0.5)
        with self.assertRaises(ValueError):
            compare_particle_density(diffusion=-0.5)
        with self.assertRaises(ValueError):
            compare_particle_density(particles=20)


if __name__ == "__main__":
    unittest.main()
