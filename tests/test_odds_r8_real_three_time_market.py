#!/usr/bin/env python3
"""One real Kyoto8 three-point market path, full matched 55-wide grids."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_r8_real_three_time_market import (
    STATUS, OTHER_SOURCE, audit, collect_pre_race_price_panels,
)
from odds_real_multirace_archive_audit import SOURCE_SHA
from odds_six_race_predictive_increment import OFFICIAL_OCT12


class RealThreePointR8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=audit()

    def test_three_real_times_same_full_field_and_middle_curvature(self):
        r=self.r
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(r["n_horses"],11)
        self.assertEqual(
            [x["label"] for x in r["before_race_quote_snapshots"]],
            ["12:21","13:26","13:44"])
        self.assertAlmostEqual(
            r["time_weighted_middle_curvature"]
            ["representative_interior_fraction_elapsed"],
            65/83,places=12)
        self.assertAlmostEqual(
            r["time_weighted_middle_curvature"]
            ["crosshorse_sd_of_centered_intermediate_log_relative_price_curvature"],
            .14343218216241194,places=10)
        self.assertEqual(
            r["time_weighted_middle_curvature"]
            ["horses_with_direction_reversal_from_first_to_mid_to_last"],1)
        self.assertTrue(r["price_path_three_real_complete_source_timepoints"])

    def test_price_redistribution_accelerates_before_race(self):
        x=self.r["price_redistribution_pp"]
        self.assertAlmostEqual(x["1221_to_1326"],5.368638694568566,places=10)
        self.assertAlmostEqual(x["1326_to_1344"],9.656362948215287,places=10)
        self.assertAlmostEqual(x["1221_to_1344"],14.90540284052265,places=10)
        self.assertGreater(x["1326_to_1344"]/18,x["1221_to_1326"]/65)
        self.assertFalse(
            self.r["time_weighted_middle_curvature"]
            ["additional_winner_forecast_information_verified"])

    def test_winner_and_top3_get_worse_over_three_times(self):
        r=self.r
        self.assertEqual(r["actual_official_top3"],[9,1,7])
        x=r["before_race_quote_snapshots"]
        self.assertEqual([s["winning_horse_9_displayed_win_odds"] for s in x],
                         [4.7,4.9,5.8])
        self.assertAlmostEqual(
            x[0]["proper_outcome_metrics"]["winner_log_loss"],1.7780260329469046,places=10)
        self.assertAlmostEqual(
            x[1]["proper_outcome_metrics"]["winner_log_loss"],1.819892547539915,places=10)
        self.assertAlmostEqual(
            x[2]["proper_outcome_metrics"]["winner_log_loss"],1.9920741463628446,places=10)
        self.assertAlmostEqual(
            x[2]["proper_outcome_metrics"]["top3_binary_brier"],.22815648729973692,places=10)
        self.assertTrue(all(
            x[i+1]["proper_outcome_metrics"]["winner_log_loss"] >
            x[i]["proper_outcome_metrics"]["winner_log_loss"]
            for i in range(2)))
        self.assertTrue(all(
            x[i+1]["proper_outcome_metrics"]["top3_binary_brier"] >
            x[i]["proper_outcome_metrics"]["top3_binary_brier"]
            for i in range(2)))

    def test_two_matching_wide_win_published_minutes_not_atomic(self):
        r=self.r
        self.assertEqual(r["wide_two_time_full_pair_count"],55)
        self.assertTrue(r["win_wide_source_update_minutes_match_at_both_checkpoints"])
        self.assertTrue(r["source_pages_not_an_atomic_combined_tote_snapshot"])
        x=r["win_wide_relative_pair_index_change"]
        self.assertEqual(x["pairs_with_cross_pool_residual_ratio_change_at_least_25pct"],22)
        self.assertAlmostEqual(
            x["mean_absolute_cross_pool_log_ratio_change"],.2083443234352569,places=9)
        self.assertAlmostEqual(x["residual_rank_spearman"],.8313852813852813,places=9)
        self.assertTrue(x["pair_observations_are_not_independent_races"])

    def test_pair_three_eleven_nonconcordant_actual_quotes(self):
        s=self.r["selected_pair_3_11"]
        self.assertTrue(s["different_direction_win_and_pair_price"])
        self.assertEqual(s["before_wide_lower"],2.5)
        self.assertEqual(s["after_wide_lower"],3.3)
        self.assertEqual(s["horse3_win_odds_before_after"],[6.7,6.3])
        self.assertEqual(s["horse11_win_odds_before_after"],[4.9,3.9])

    def test_modifying_archive_bytes_fails_before_comparing_outcomes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for spec in (*SOURCE_SHA[8],*OTHER_SOURCE.values()):
                src=ROOT/spec[0]
                dest=root/spec[0]
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(src,dest)
            official=root/OFFICIAL_OCT12.relative_to(ROOT)
            official.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(OFFICIAL_OCT12,official)
            self.assertEqual(audit(root)["n_horses"],11)
            to_change=root/OTHER_SOURCE["late_all"][0]
            to_change.write_bytes(to_change.read_bytes()+b"\n")
            with self.assertRaisesRegex(ValueError,"HOLD_R8_ARCHIVED_SOURCE_CHANGED"):
                audit(root)

    def test_unseen_future_does_not_enter_source_price_model(self):
        panels, curve, residual, start, _=collect_pre_race_price_panels()
        self.assertEqual(len(panels),3)
        self.assertEqual([p["n_horses"] for p in panels],[11,11,11])
        self.assertEqual(start,"2026-10-12T14:00:00+09:00")
        self.assertEqual(residual["pair_count"],55)
        self.assertEqual(curve["intermediate_points"],1)
        self.assertFalse(residual["contemporaneous_venue_bettor_updating_identified"])
        self.assertTrue(any("One race only" in s for s in self.r["scientific_limitations"]))


if __name__=="__main__":
    unittest.main()
