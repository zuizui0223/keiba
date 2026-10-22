#!/usr/bin/env python3
"""Synthetic-only threshold scoring: strict prestart and date-blocked tests."""
import copy
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from odds_threshold_forward_eval import (
    STATUS_HOLD, STATUS_SYN, demo_panel, evaluate, forecast, load_panel,
    order_probabilities,
)


class ForwardThresholdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.synthetic = demo_panel(seed=700, dates=15, races_per_day=5, n=10)

    def test_known_joint_model_mass(self):
        q, p = order_probabilities([1, 2, 3, 5, 8, 11])
        self.assertAlmostEqual(sum(q), 1)
        self.assertAlmostEqual(sum(p), 3)
        self.assertTrue(all(0 < v < 1 for v in p))

    def test_one_race_is_hard_hold_not_discovered_threshold(self):
        panel = copy.deepcopy(self.synthetic)
        panel["races"] = panel["races"][:1]
        result = evaluate(panel)
        self.assertEqual(result["status"], STATUS_HOLD)
        self.assertEqual(result["race_count"], 1)
        self.assertEqual(result["independent_start_dates"], 1)

    def test_synthetic_forward_runs_and_keeps_train_test_split(self):
        x = evaluate(self.synthetic)
        self.assertEqual(x["status"], STATUS_SYN)
        self.assertTrue(x["data_provenance_synthetic"])
        self.assertLess(x["train_max_date"], x["future_min_date"])
        self.assertEqual(x["training_race_count"]+x["future_race_count"], 75)
        self.assertEqual(set(x["future_race_avg_scores"]),
                         {"market_latest_only", "train_selected_smooth_path",
                          "train_selected_threshold_path"})
        t = x["training_only_selected_parameters"]["train_selected_threshold_path"]
        self.assertIn(t["early_odds_at_least"], (5.0, 10.0, 20.0, 50.0))

    def test_future_outcomes_never_choose_training_parameters(self):
        x = evaluate(self.synthetic)
        replaced = copy.deepcopy(self.synthetic)
        cutoff = x["train_max_date"]
        for race in replaced["races"]:
            if race["post_jst"][:10] > cutoff:
                actual = set(race["official_top3"])
                fake = [i for i in race["early_win"]["odds"] if i not in actual][:3]
                race["official_top3"] = fake
        y = evaluate(replaced)
        self.assertEqual(x["training_only_selected_parameters"],
                         y["training_only_selected_parameters"])
        self.assertNotEqual(
            x["future_race_avg_scores"]["market_latest_only"]["winner_log_loss"],
            y["future_race_avg_scores"]["market_latest_only"]["winner_log_loss"])

    def test_prestart_and_source_timestamp_rules(self):
        variants = [
            lambda r: r["latest_win"].update(provider_published_at_jst=r["post_jst"]),
            lambda r: r["latest_win"].update(provider_timestamp_verified=False),
            lambda r: r["latest_win"].update(market="wide"),
            lambda r: r.update(
                official_top3_verified_at_jst=r["early_win"]["provider_published_at_jst"]),
            lambda r: r["latest_win"]["odds"].pop("1"),
        ]
        for modify in variants:
            s = copy.deepcopy(self.synthetic)
            modify(s["races"][0])
            with self.assertRaises(ValueError):
                evaluate(s)

    def test_source_rights_gate(self):
        s = copy.deepcopy(self.synthetic)
        s["provenance"] = "unknown"
        with self.assertRaisesRegex(ValueError, "HOLD_UNVERIFIED_RESEARCH_SOURCE_RIGHTS"):
            evaluate(s)
        s = copy.deepcopy(self.synthetic)
        s["schema"] = "WRONG"
        with self.assertRaisesRegex(ValueError, "HOLD_SCHEMA_MISMATCH"):
            evaluate(s)

    def test_baseline_is_latest_normalized_market_not_postrace(self):
        rows, _ = load_panel(self.synthetic)
        r = rows[0]
        p, t = forecast(r, beta=0, threshold=None)
        self.assertAlmostEqual(sum(p), 1)
        self.assertAlmostEqual(sum(t), 3)
        self.assertTrue(all(abs(a-b) < 1e-12 for a, b in zip(p, r["latest_q"])))


if __name__ == "__main__":
    unittest.main()
