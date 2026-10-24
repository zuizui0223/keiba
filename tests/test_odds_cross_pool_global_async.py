#!/usr/bin/env python3
"""Cross-pool overlapping pair index tests; one race is NOT 136 experiments."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from shuka2026_odds_information_hierarchy import load_snapshots, read_locked
from odds_cross_pool_global_async import (
    STATUS, audit, compare, relative_pair_indices, _rank_corr,
)


class CrossPoolQuoteIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=load_snapshots(read_locked())
        cls.panels=[relative_pair_indices(s) for s in cls.original if "wide" in s]

    def test_complete_136_pairs_and_pair_indices_normalized(self):
        self.assertEqual(len(self.panels),3)
        for p in self.panels:
            self.assertEqual(len(p["pair_residual"]),136)
            self.assertAlmostEqual(
                sum(p["observed_relative_pair_index"].values()),1.0,places=11)
            self.assertAlmostEqual(
                sum(p["model_pair_index"].values()),1.0,places=11)
            self.assertFalse(p["source_pool_time_aligned"])

    def test_archived_relative_mismatch_moves_in_two_time_windows(self):
        x=compare(self.panels[0],self.panels[1])
        y=compare(self.panels[1],self.panels[2])
        self.assertEqual(
            x["pairs_with_cross_pool_residual_ratio_change_at_least_25pct"],27)
        self.assertEqual(
            y["pairs_with_cross_pool_residual_ratio_change_at_least_25pct"],0)
        self.assertAlmostEqual(
            x["mean_absolute_cross_pool_log_ratio_change"],
            0.13068114592278568,delta=1e-8)
        self.assertAlmostEqual(
            y["mean_absolute_cross_pool_log_ratio_change"],
            0.01938988742544159,delta=1e-8)
        self.assertAlmostEqual(x["residual_rank_spearman"],.95852774,delta=.0001)
        self.assertAlmostEqual(y["residual_rank_spearman"],.99824913,delta=.0001)
        self.assertEqual(
            x["largest_abs_cross_pool_residual_changes"][0]["pair"],[8,14])
        self.assertTrue(x["pair_observations_are_not_independent_races"])
        self.assertTrue(x["25pct_log_ratio_cutoff_is_descriptive_not_predictive_threshold"])

    def test_pair_reordering_or_missing_pair_is_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            _rank_corr({(1,2):.4},{(1,3):.4})
        bad=copy.deepcopy(self.panels[2])
        bad["pair_residual"].pop((8,14))
        with self.assertRaisesRegex(ValueError,"HOLD_UNMATCHED_PAIRS"):
            compare(self.panels[1],bad)
        source=copy.deepcopy(self.original[1])
        source["wide"].pop((8,14))
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_FULL_WIDE_GRID"):
            relative_pair_indices(source)

    def test_scientific_status_not_upgraded(self):
        r=audit()
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(len(r["cross_pool_pair_contrasts"]),2)
        self.assertFalse(r["underlying_per_pool_quote_update_times_verified"])
        self.assertTrue(r["pair_index_is_not_event_probability"])
        self.assertEqual(r["scientific_conclusion"],
                         "DESCRIPTIVE_NON_IDENTIFICATION_NOT_FORECAST_ABILITY")


if __name__=="__main__":
    unittest.main()
