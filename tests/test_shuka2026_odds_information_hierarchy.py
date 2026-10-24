#!/usr/bin/env python3
"""Tests for archived Japanese tote dynamics; no leakage to betting v3.1."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from shuka2026_odds_information_hierarchy import (
    SOURCE, STATUS, audit, read_locked, load_snapshots, adjacent_summary,
    win_snapshot_summary, wide_snapshot_summary, cross_pool_signs,
    pl_pair_top3_index, synthetic_bettor_abm, share,
)


class OddsHierarchyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded = read_locked()
        cls.snaps = load_snapshots(cls.loaded)

    def test_four_archives_and_timestamp_provenance(self):
        self.assertEqual(len(self.snaps), 4)
        self.assertEqual([s["label"] for s in self.snaps],
                         ["sat_1437", "sat_1537", "sun_1142", "sun_1218"])
        self.assertEqual(self.snaps[2]["timestamp_kind"],
                         "JRA_first_party_explicit_win_update_only")
        self.assertEqual(len(self.snaps[2]["wide"]), 136)
        self.assertEqual(set(self.snaps[0]["win"]), set(range(1,18)))

    def test_locked_source_sha_rejects_archive_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            for rel, _ in SOURCE.values():
                destination = root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, destination)
            self.assertEqual(read_locked(root), self.loaded)
            p = root / SOURCE["early"][0]
            p.write_bytes(p.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "HOLD_CHANGED_ARCHIVED_SOURCE"):
                read_locked(root)

    def test_win_probabilities_are_normalized_price_weights(self):
        for s in self.snaps:
            p = share(s["win"])
            self.assertAlmostEqual(sum(p.values()), 1, places=13)
            self.assertTrue(all(x > 0 for x in p.values()))
        first = win_snapshot_summary(self.snaps[0])
        last = win_snapshot_summary(self.snaps[-1])
        self.assertAlmostEqual(
            first["favorite_relative_weight_pct_not_win_probability"],
            63.5849459321, places=7)
        self.assertAlmostEqual(
            last["favorite_relative_weight_pct_not_win_probability"],
            56.2813442132, places=7)
        self.assertEqual(set(first["market_top5_horse_numbers"]),
                         set(last["market_top5_horse_numbers"]))

    def test_overnight_20pct_quotes_are_not_predictive_threshold(self):
        z = [adjacent_summary(self.snaps[i], self.snaps[i+1])
             for i in range(3)]
        self.assertEqual([s["different_20pct_or_more_quote_horses"]
                          for s in z], [0,6,0])
        self.assertAlmostEqual(
            z[1]["relative_share_total_variation_pp"], 7.582, delta=0.005)
        self.assertTrue(all(x["market_top5_membership_unchanged"] for x in z))
        self.assertTrue(z[1]["mixed_provider_or_timestamp_semantics"])
        self.assertFalse(z[0]["mixed_provider_or_timestamp_semantics"])
        self.assertFalse(z[2]["mixed_provider_or_timestamp_semantics"])
        self.assertTrue(all(b["not_a_predictive_threshold"]
                            for x in z for b in x["prior_quote_bands"]))

    def test_exact_PL_pair_index_and_136_pair_price_grid(self):
        for s in self.snaps[1:]:
            model = pl_pair_top3_index(s["win"])
            self.assertEqual(len(model), 136)
            self.assertAlmostEqual(sum(model.values()), 1, places=12)
            self.assertAlmostEqual(
                wide_snapshot_summary(s)["highlighted_pairs"]["8-14"]
                ["win_PL_both_top3_model_probability"],
                model[(8,14)]*3, places=12)

    def test_cross_pool_ranking_flips_despite_win_support(self):
        v = cross_pool_signs(self.snaps)
        self.assertTrue(v["horse_14_stronger_in_win_but_pair_8_14_weaker_in_wide"])
        self.assertTrue(v["relative_wide_pair_ranking_reversal"])
        self.assertAlmostEqual(
            v["horse_14_win_quote_change_pct"], -18.8073394495, delta=0.1)
        self.assertAlmostEqual(
            v["wide_8_14_lower_quote_change_pct"], 77.27272727, delta=0.0001)
        self.assertGreater(v["pair_8_14_relative_weight_over_3_8_before"], 1)
        self.assertLess(v["pair_8_14_relative_weight_over_3_8_after"], 1)
        self.assertTrue(v["no_proof_of_bettor_information_causality"])

    def test_corrupt_or_missing_pair_quotes_fail(self):
        altered = copy.deepcopy(self.loaded)
        altered["sat"]["wide_pair_all_136"][0]["horse_numbers"] = [8,8]
        with self.assertRaisesRegex(ValueError, "HOLD_PAIR_ID_DUPLICATE"):
            load_snapshots(altered)
        altered = copy.deepcopy(self.loaded)
        altered["sat"]["wide_pair_all_136"].pop()
        with self.assertRaisesRegex(ValueError, "HOLD_INCOMPLETE_136"):
            load_snapshots(altered)
        altered = copy.deepcopy(self.loaded)
        altered["sat"]["win_prices_all_17"][0]["win_odds"] = -1
        with self.assertRaisesRegex(ValueError, "HOLD_DUPLICATED_OR_INVALID"):
            load_snapshots(altered)

    def test_cannot_include_after_race_or_wrong_timestamp(self):
        altered = copy.deepcopy(self.loaded)
        altered["morning"]["first_party_JRA_win"][
            "publisher_explicit_update_timestamp_jst"] = "2026-10-18T16:50:00+09:00"
        with self.assertRaisesRegex(ValueError, "HOLD_NOT_CHRONOLOGICAL"):
            load_snapshots(altered)
        altered = copy.deepcopy(self.loaded)
        altered["noon"]["official_jra_win_published_at_jst"] = (
            "2026-10-18T12:18:00")
        with self.assertRaisesRegex(ValueError, "HOLD_NOT_CHRONOLOGICAL"):
            load_snapshots(altered)

    def test_synthetic_bettor_mechanism_is_reproducible_but_not_fitted(self):
        q = list(share(self.snaps[0]["win"]).values())
        x = synthetic_bettor_abm(q, repeats=30, seed=208)
        y = synthetic_bettor_abm(q, repeats=30, seed=208)
        self.assertEqual(x, y)
        self.assertIn("SYNTHETIC", x["status"])
        self.assertIn("HOLD", x["causal_identification"])
        self.assertNotEqual(
            x["results"]["herding_only"]["mean_relative_share_turnover_pp"],
            x["results"]["information_only"]["mean_relative_share_turnover_pp"])
        self.assertEqual(x["simulated_random_bettor_paths_not_actual_races"], 30)

    def test_inference_gate_and_no_postrace_outcome_training(self):
        x = audit(paths=12, seed=33)
        self.assertEqual(x["status"], STATUS)
        self.assertTrue(x["early_quote_is_not_opening_odds"])
        self.assertEqual(x["snapshot_count"], 4)
        self.assertEqual(len(x["wide_market_windows"]), 3)
        self.assertEqual(x["inference_gates"]["forecast_skill_threshold"],
                         "HOLD_NO_INDEPENDENT_RACE_LEVEL_PROSPECTIVE_HOLDOUT")
        self.assertFalse(
            x["inference_gates"]["backtest_outcomes_used_in_model_fitting"])
        self.assertFalse(x["inference_gates"]["old_v31_thresholds_modified"])
        self.assertFalse(x["inference_gates"]["cross_pool_atomically_aligned"])


if __name__ == "__main__":
    unittest.main()
