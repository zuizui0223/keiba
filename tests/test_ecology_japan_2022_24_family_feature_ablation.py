"""Fictional loss/feature cases; no empirical result is manufactured here."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_japan_2022_24_family_feature_ablation import (
    fit_factorial, predict_factorial, paired_loss_terms,
    paired_uncertainty, summarize_period,
)
from ecology_japan_2022_strong_portable_baseline import STRONG_NO_KIN, STRONG_KIN
from ecology_japan_2022_independent_forward import fit_weighted_ridge, predict_weighted_ridge


def design():
    rng = np.random.default_rng(44)
    x = pd.DataFrame(rng.normal(size=(80, len(STRONG_KIN))), columns=STRONG_KIN)
    y = np.clip(.5 + .12*x.own_mean + .05*x.sire_kin_history, 0, 1).to_numpy()
    return x, y, np.repeat(np.arange(20).astype(str), 4)


def panel():
    return pd.DataFrame({
        "horse": ["a", "a", "a", "b", "c", "d"],
        "race": ["r1", "r2", "r3", "r1", "r2", "r3"],
        "day": pd.to_datetime(["2022-01-01", "2022-02-01", "2022-03-01",
                               "2022-01-01", "2022-02-01", "2022-03-01"]),
        "sire_id": ["s1", "s1", "s1", "s1", "", ""],
        "y": [0., .2, .4, .6, .8, 1.],
    })


class FeatureAblationTests(unittest.TestCase):
    def test_endpoints_reproduce_existing_ridge_with_original_column_order(self):
        x, y, h = design()
        models = fit_factorial(x, y, h)
        p = predict_factorial(models, x)
        for name, columns in (("M1", STRONG_NO_KIN), ("M2", STRONG_KIN)):
            original = fit_weighted_ridge(x, y, h, columns, alpha=100.)
            np.testing.assert_allclose(p[name], predict_weighted_ridge(original, x), atol=1e-13)

    def test_excluded_features_cannot_change_intermediate_predictions(self):
        x, y, h = design()
        models = fit_factorial(x, y, h)
        p = predict_factorial(models, x)
        changed_p = x.copy()
        changed_p[["sire_kin_history", "dam_kin_history"]] += 100
        changed_c = x.copy()
        changed_c[["log_sire_relative_count", "log_dam_relative_count"]] += 100
        np.testing.assert_allclose(p["MC"], predict_factorial(models, changed_p)["MC"], atol=1e-14, rtol=0)
        np.testing.assert_allclose(p["MP"], predict_factorial(models, changed_c)["MP"], atol=1e-14, rtol=0)
        self.assertGreater(np.max(np.abs(p["M2"] - predict_factorial(models, changed_p)["M2"])), .01)

    def test_loss_decomposition_has_hand_checked_signed_values(self):
        p = {"M1": np.array([.5]), "MC": np.array([.4]),
             "MP": np.array([.3]), "M2": np.array([.6])}
        d = paired_loss_terms(np.array([0.]), p)
        expected = {"full_gain": -.11, "performance_alone": .16, "counts_alone": .09,
                    "performance_given_counts": -.20, "counts_given_performance": -.27,
                    "shapley_performance": -.02, "shapley_counts": -.09}
        for key, value in expected.items():
            self.assertAlmostEqual(float(d[key][0]), value, places=14)

    def test_each_horse_gets_one_vote_despite_repeated_starts(self):
        d = panel()
        gains = np.array([.1, .1, .1, -.1, .2, -.2])
        r = paired_uncertainty(d, gains, draws=99, min_clusters=2)
        self.assertAlmostEqual(r["mean_MSE_gain"], 0., places=14)
        self.assertEqual(r["horses"], 4)
        self.assertEqual(r["sire_bootstrap"]["clusters"], 3)
        self.assertEqual(r["sire_bootstrap"]["unknown_sire_singleton_horses"], 2)
        self.assertEqual(r["sire_bootstrap"]["largest_cluster_horses"], 2)

    def test_shapley_sum_and_endpoint_risk_agree_after_weighting(self):
        d = panel()
        p = {"M1": np.repeat(.5, len(d)), "MC": np.repeat(.4, len(d)),
             "MP": np.repeat(.6, len(d)), "M2": np.repeat(.7, len(d))}
        r = summarize_period(d, p, draws=99, min_clusters=2)
        self.assertAlmostEqual(r["models"]["M1"]["MSE"], .11666666666666667)
        self.assertAlmostEqual(r["models"]["M2"]["MSE"], .09666666666666666)
        q = r["loss_decomposition_MSE"]
        self.assertAlmostEqual(q["full_gain"], .02)
        self.assertAlmostEqual(q["shapley_performance"] + q["shapley_counts"], q["full_gain"])

    def test_low_cluster_support_reports_hold_without_fabricating_interval(self):
        r = paired_uncertainty(panel(), np.arange(6)/10, draws=99)
        self.assertEqual(r["two_way"]["status"], "HOLD_TOO_FEW_CLUSTERS")
        self.assertEqual(r["sire_bootstrap"]["status"], "HOLD_TOO_FEW_CLUSTERS")
        self.assertNotIn("CI95", r["two_way"])

    def test_nonpositive_two_way_variance_remains_hold(self):
        r = paired_uncertainty(panel(), np.zeros(6), draws=99, min_clusters=2)
        self.assertEqual(r["two_way"]["status"], "HOLD_NONPOSITIVE_VARIANCE")

    def test_resampling_is_seeded_and_invariant_to_row_order(self):
        d = panel()
        g = np.array([.1, .4, -.2, .3, .2, -.5])
        a = paired_uncertainty(d, g, draws=99, min_clusters=2)
        order = [5, 2, 0, 4, 1, 3]
        b = paired_uncertainty(d.iloc[order], g[order], draws=99, min_clusters=2)
        np.testing.assert_allclose(a["sire_bootstrap"]["CI95"], b["sire_bootstrap"]["CI95"], atol=1e-15)

    def test_positive_two_way_interval_matches_independent_numeric_oracle(self):
        r = paired_uncertainty(panel(), np.array([.1, .4, -.2, .3, .2, -.5]),
                               draws=99, min_clusters=2)
        theta, se = .025, .22942409783339382
        self.assertAlmostEqual(r["mean_MSE_gain"], theta)
        for key, z in (("CI95", 1.959963984540054),
                       ("CI95_bonferroni_8", 2.734368786533176)):
            np.testing.assert_allclose(r["two_way"][key],
                                       [theta-z*se, theta+z*se], atol=1e-14)

    def test_whole_sire_bootstrap_uses_total_horses_not_equal_family_means(self):
        sizes = [1, 2, 3, 4, 5]
        values = [-.4, -.1, .2, .5, .8]
        sires = [f"s{i}" for i, n in enumerate(sizes) for _ in range(n)]
        gain = np.repeat(values, sizes)
        n = len(gain)
        d = pd.DataFrame({"horse": [f"h{i}" for i in range(n)],
                          "race": [f"r{i}" for i in range(n)],
                          "day": pd.date_range("2022-01-01", periods=n),
                          "sire_id": sires, "y": np.repeat(.5, n)})
        r = paired_uncertainty(d, gain, draws=99, seed=11, min_clusters=2)
        rng = np.random.default_rng(11)
        oracle = []
        for _ in range(99):
            selected = rng.integers(0, 5, size=5)
            numerator = sum(sizes[i]*values[i] for i in selected)
            denominator = sum(sizes[i] for i in selected)
            oracle.append(numerator/denominator)
        np.testing.assert_allclose(r["sire_bootstrap"]["CI95"],
                                   np.quantile(oracle, [.025, .975]), atol=1e-14)

    def test_same_horse_day_multiple_starts_share_intersection_cluster(self):
        d = panel()
        d.loc[[1, 4], "day"] = pd.Timestamp("2022-01-01")
        r = paired_uncertainty(d, np.array([.1, .4, -.2, .3, .2, -.5]),
                               draws=99, min_clusters=2)
        # Independent rational arithmetic: 31/960 + 9/100 - 41/1280.
        half_width = 1.959963984540054 * np.sqrt(.09026041666666666)
        np.testing.assert_allclose(r["two_way"]["CI95"],
                                   [.025-half_width, .025+half_width], atol=1e-14)

    def test_duplicate_or_conflicting_source_rows_are_rejected(self):
        for mutate in ("duplicate", "sire", "day", "missing_day"):
            d = panel()
            if mutate == "duplicate":
                d.loc[1, ["race", "day"]] = d.loc[0, ["race", "day"]]
            elif mutate == "sire":
                d.loc[1, "sire_id"] = "conflict"
            elif mutate == "day":
                d.loc[3, "day"] = pd.Timestamp("2022-04-01")
            else:
                d.loc[0, "day"] = pd.NaT
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                paired_uncertainty(d, np.zeros(6), draws=99, min_clusters=2)

    def test_invalid_prediction_alignment_and_nonfinite_values_are_rejected(self):
        for bad in (np.array([np.nan]), np.array([1.1]), np.array([.2, .3])):
            p = {"M1": np.array([.5]), "MC": np.array([.4]),
                 "MP": np.array([.3]), "M2": bad}
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                paired_loss_terms(np.array([0.]), p)


if __name__ == "__main__":
    unittest.main()
