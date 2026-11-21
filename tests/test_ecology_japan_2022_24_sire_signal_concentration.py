"""Small exact loss examples for group concentration, not empirical evidence."""
from pathlib import Path
import json
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_24_sire_signal_concentration import sire_summary


def fixture(sizes=(4, 1, 1), values=(3/64, -4/64, -2/64)):
    sires = [f"s{i}" for i, n in enumerate(sizes) for _ in range(n)]
    n = len(sires)
    return pd.DataFrame({
        "horse": [f"h{i}" for i in range(n)],
        "race": [f"r{i}" for i in range(n)],
        "day": pd.date_range("2022-01-01", periods=n),
        "sire_id": sires, "y": np.repeat(.5, n),
    }), np.repeat(values, sizes)


def run_case(p, g, **kw):
    return sire_summary(p, g, draws=99, min_clusters=2, **kw)


class ConcentrationTests(unittest.TestCase):
    def test_size_weighting_and_population_covariance_identity(self):
        r = run_case(*fixture())
        self.assertAlmostEqual(r["horse_equal_gain"], 1/64)
        self.assertAlmostEqual(r["sire_equal_gain"], -1/64)
        self.assertAlmostEqual(r["size_association_gap"], 2/64)
        self.assertAlmostEqual(r["covariance_identity_gap"], 2/64)
        self.assertEqual(r["recorded_sires"], 3)
        self.assertEqual(r["sign_counts"], {"positive": 1, "zero": 0, "negative": 2})

    def test_single_deletion_reweights_remaining_horses(self):
        r = run_case(*fixture())["leave_one_sire_out"]
        self.assertAlmostEqual(r["minimum_remaining_gain"], -3/64)
        self.assertAlmostEqual(r["maximum_remaining_gain"], 2/64)
        self.assertEqual(r["nonpositive_remaining_count"], 1)

    def test_two_group_deletion_can_fail_when_every_single_deletion_stays_positive(self):
        r = run_case(*fixture((1, 1, 1, 1), (3/64, 3/64, 3/64, -4/64)))
        self.assertGreater(r["leave_one_sire_out"]["minimum_remaining_gain"], 0)
        d = r["minimum_joint_deletion"]
        self.assertEqual(d["groups_removed"], 2)
        self.assertEqual(d["horses_removed"], 2)
        self.assertAlmostEqual(d["remaining_gain"], -1/128)

    def test_joint_deletion_counts_exact_zero_as_nonpositive(self):
        r = run_case(*fixture((1, 1, 1), (2/64, 2/64, -2/64)))
        self.assertEqual(r["minimum_joint_deletion"]["groups_removed"], 1)
        self.assertEqual(r["minimum_joint_deletion"]["remaining_gain"], 0)

    def test_all_positive_requires_nonempty_remaining_group(self):
        r = run_case(*fixture((1, 4, 5, 19, 20, 21), (1/32,)*6))
        self.assertAlmostEqual(r["horse_equal_gain"], 1/32)
        self.assertAlmostEqual(r["sire_equal_gain"], 1/32)
        self.assertAlmostEqual(r["size_association_gap"], 0)
        self.assertIsNone(r["minimum_joint_deletion"]["groups_removed"])
        self.assertEqual(r["minimum_joint_deletion"]["status"], "NO_NONEMPTY_NONPOSITIVE_REMAINDER")
        for key, groups, horses in [("1-4", 2, 5), ("5-19", 2, 24), ("20+", 2, 41)]:
            self.assertEqual(r["support_bins"][key]["sires"], groups)
            self.assertEqual(r["support_bins"][key]["horses"], horses)

    def test_gross_mass_shares_do_not_divide_by_small_net_gain(self):
        r = run_case(*fixture())["contribution_mass"]
        self.assertAlmostEqual(r["positive_MSE_mass"], 2/64)
        self.assertAlmostEqual(r["negative_MSE_magnitude"], 1/64)
        self.assertEqual(r["positive_top_shares"]["1"], 1.)
        self.assertAlmostEqual(r["negative_top_shares"]["1"], 2/3)

    def test_absent_sign_mass_has_null_shares(self):
        r = run_case(*fixture((1, 1), (.1, .2)))
        self.assertEqual(r["contribution_mass"]["negative_MSE_magnitude"], 0)
        self.assertTrue(all(x is None for x in r["contribution_mass"]["negative_top_shares"].values()))

    def test_replicated_within_horse_history_cannot_change_group_estimands(self):
        p, _ = fixture((1, 1), (0., 0.))
        a = p.iloc[[0]].copy()
        a["race"] = "extra_a"
        a["day"] = pd.Timestamp("2022-02-01")
        p = pd.concat([p, a], ignore_index=True)
        g = np.array([1/64, -2/64, 3/64])
        r = run_case(p, g)
        q = p.loc[p.horse.eq("h0")].copy()
        q["race"] += "_replicate"
        rr = run_case(pd.concat([p, q], ignore_index=True), np.r_[g, [1/64, 3/64]])
        for key in ["all_horse_gain", "horse_equal_gain", "sire_equal_gain", "size_association_gap"]:
            self.assertAlmostEqual(r[key], rr[key])
        self.assertEqual(r["coverage"], rr["coverage"])

    def test_unknown_fathers_are_not_a_fake_family(self):
        p, g = fixture()
        missing = p.iloc[[0]].copy()
        missing[["horse", "race", "sire_id"]] = ["unknown", "other_race", ""]
        p = pd.concat([p, missing], ignore_index=True)
        r = run_case(p, np.r_[g, .5])
        self.assertEqual(r["recorded_sires"], 3)
        self.assertEqual(r["coverage"]["unknown_sire_horses"], 1)
        self.assertAlmostEqual(r["coverage"]["known_sire_fraction"], 6/7)
        self.assertAlmostEqual(r["horse_equal_gain"], 1/64)
        self.assertAlmostEqual(r["all_horse_gain"], (6/64+.5)/7)

    def test_single_or_no_recorded_group_has_explicit_hold(self):
        p, g = fixture((2,), (.1,))
        r = run_case(p, g)
        self.assertEqual(r["leave_one_sire_out"]["status"], "HOLD_ONE_RECORDED_SIRE")
        p["sire_id"] = ""
        r = run_case(p, g)
        self.assertEqual(r["status"], "HOLD_NO_RECORDED_SIRES")
        self.assertEqual(r["recorded_sires"], 0)
        json.dumps(r, allow_nan=False)

    def test_sire_bootstrap_pairing_matches_scalar_oracle(self):
        r = run_case(*fixture(), seed=11)
        rng = np.random.default_rng(11)
        samples = []
        for _ in range(99):
            sel = rng.integers(3, size=3)
            sizes, means = [4, 1, 1], [3/64, -4/64, -2/64]
            weighted = sum(sizes[i]*means[i] for i in sel)/sum(sizes[i] for i in sel)
            balanced = sum(means[i] for i in sel)/3
            samples.append([weighted, balanced, weighted-balanced])
        for column, key in enumerate(["horse_equal_gain", "sire_equal_gain", "size_association_gap"]):
            np.testing.assert_allclose(r["bootstrap"]["CI95"][key],
                                       np.quantile(np.array(samples)[:, column], [.025, .975]), atol=1e-14)

    def test_all_zero_is_already_nonpositive(self):
        r = run_case(*fixture((1, 1, 1), (0., 0., 0.)))
        self.assertEqual(r["sign_counts"], {"positive": 0, "zero": 3, "negative": 0})
        self.assertEqual(r["minimum_joint_deletion"]["groups_removed"], 0)
        self.assertEqual(r["minimum_joint_deletion"]["status"], "ALREADY_NONPOSITIVE")

    def test_row_order_and_tied_group_labels_do_not_change_minimum_count(self):
        # Equal positive mass, unequal group sizes: remove the larger group first.
        p, g = fixture((1, 2, 1), (1/8, 1/16, -1/8))
        r = run_case(p, g)
        self.assertEqual(r["minimum_joint_deletion"]["groups_removed"], 1)
        self.assertEqual(r["minimum_joint_deletion"]["horses_removed"], 2)
        self.assertEqual(r["minimum_joint_deletion"]["remaining_gain"], 0.)
        p["sire_id"] = p.sire_id.map({"s0":"z", "s1":"a", "s2":"y"})
        order = [3, 1, 0, 2]
        r2 = run_case(p.iloc[order], g[order])
        self.assertEqual(r["minimum_joint_deletion"], r2["minimum_joint_deletion"])

    def test_invalid_losses_or_conflicting_parent_mapping_are_rejected(self):
        p, g = fixture()
        for bad in [g[:-1], np.r_[g[:-1], np.nan], np.r_[g[:-1], 1.01]]:
            with self.assertRaises(ValueError):run_case(p, bad)
        q = p.iloc[[0]].copy()
        q["race"] = "conflicting_parent"
        q["sire_id"] = "other"
        with self.assertRaises(ValueError):run_case(pd.concat([p, q]), np.r_[g, g[0]])


if __name__ == "__main__":
    unittest.main()
