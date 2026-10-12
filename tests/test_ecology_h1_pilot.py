"""Synthetic H1 pilot tests: correct time split, relative outcome, and guarded fitting.

All records are generated from a random seed. They are NOT JRA data.
"""
import csv
from datetime import date, timedelta
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_panel import REQUIRED, load_panel, lagged_features
from ecology_h1_pilot import relative_performance, run, split_dates, within_between_from_training


def make_synthetic_panel(days=26, n=12, seed=88):
    rng = random.Random(seed)
    result = []
    for day in range(days):
        dt = date(2026, 1, 1) + timedelta(days=day)
        poor = day % 2
        speed = []
        for i in range(n):
            individual_baseline = 0.45 * (i / (n-1) - 0.5)
            individual_going_effect = 0.5 * ((i * 7) % n / (n-1) - 0.5)
            speed.append(15.0 + individual_baseline + poor * individual_going_effect + rng.gauss(0, 0.07))
        rank = {i: 1 + sum(v > speed[i] for v in speed) for i in range(n)}
        for i in range(n):
            result.append({
                "race_id": f"fake_{day:03d}", "horse_id": f"fake_h{i:03d}",
                "race_date_jst": dt.isoformat(), "race_start_jst": f"{dt}T15:00:00+09:00",
                "feature_available_at_jst": f"{dt}T12:00:00+09:00",
                "venue": "synthetic-track", "course_surface": "turf",
                "course_distance_m": "1600", "track_going": "重" if poor else "良",
                "class_pre": "synthetic-only", "jockey_id": f"fake_j{i:03d}",
                "field_size": str(n), "finish_status": "finished",
                "finishing_position": str(rank[i]),
                "finish_time_s": f"{1600/speed[i]:.7f}",
                "first_call_position": str((i * 7 % n) + 1),
                "source_url": "synthetic://not-for-empirical-use",
                "source_license": "synthetic",
            })
    return result


def make_csv(folder, rows):
    path = Path(folder) / "fabricated.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(REQUIRED) + ["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)
    return path


class H1PilotTests(unittest.TestCase):
    def test_race_relative_outcome_has_zero_mean_per_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = lagged_features(load_panel(make_csv(tmp, make_synthetic_panel(days=5))))
        frame = relative_performance(rows)
        self.assertEqual(len(frame), 5 * 12)
        self.assertLess(frame.groupby("race_id")["y"].mean().abs().max(), 1e-10)
        self.assertEqual(set(frame["poor"].unique()), {0, 1})

    def test_full_timed_roster_required(self):
        rows = make_synthetic_panel(days=5)
        rows[0]["finish_time_s"] = ""
        with tempfile.TemporaryDirectory() as tmp:
            loaded = lagged_features(load_panel(make_csv(tmp, rows)))
        frame = relative_performance(loaded)
        self.assertEqual(len(frame), 4 * 12)
        self.assertNotIn("fake_000", set(frame["race_id"]))

    def test_forward_split_and_synthetic_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_csv(tmp, make_synthetic_panel())
            frame = relative_performance(lagged_features(load_panel(path))).dropna(subset=["prior_strength"])
            train, test, _ = split_dates(frame)
            self.assertLess(train["date"].max(), test["date"].min())
            with self.assertRaisesRegex(ValueError, "synthetic"):
                run(path, "turf")

    def test_between_exposure_uses_training_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_csv(tmp, make_synthetic_panel())
            df = relative_performance(lagged_features(load_panel(path))).dropna(subset=["prior_strength"])
        train, test, _ = split_dates(df)
        tr, te, formula, _ = within_between_from_training(train, test)
        alternate = test.copy()
        alternate["poor"] = 1 - alternate["poor"]
        _, te_alt, _, _ = within_between_from_training(train, alternate)
        # Held-out conditions are known pre-race; horse baselines may not learn them.
        base = te["poor"] - te["within_poor"]
        base_alt = te_alt["poor"] - te_alt["within_poor"]
        self.assertTrue((base.to_numpy() == base_alt.to_numpy()).all())
        self.assertIn("within_poor", formula)

    def test_fit_only_marked_synthetic_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = make_csv(tmp, make_synthetic_panel())
            output = run(path, "turf", permit_synthetic_demo=True)
        self.assertEqual(output["status"], "SYNTHETIC_SMOKE_ONLY")
        self.assertTrue(output["m0"]["converged"])
        self.assertTrue(output["m1"]["converged"])
        self.assertGreaterEqual(output["split"]["train_cross_going_horses"], 4)
        self.assertTrue(math.isfinite(output["forward_test"]["m1_rmse_race_relative_speed_z"]))
        self.assertEqual(len(output["forward_test"]["race_block_bootstrap_95pct_interval"]), 2)
        self.assertFalse(output["m1"]["slope_uncertainty_estimated"])


if __name__ == "__main__":
    unittest.main()
