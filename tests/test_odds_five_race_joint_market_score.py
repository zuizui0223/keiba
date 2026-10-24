#!/usr/bin/env python3
"""Postrace five-race complete WIN/WIDE forecasts: no outcome or source leak."""
from copy import deepcopy
from itertools import combinations
from pathlib import Path
import math
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from odds_real_multirace_archive_audit import SOURCE_SHA
from odds_five_race_joint_market_score import (
    STATUS, WIDE_SOURCE, SCENARIOS, METRICS, pre_race_forecasts,
    score_ranking, aggregate_scored_races, audit, _strict_wide_range,
)


class FiveRaceCompleteWinWideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictions=pre_race_forecasts()
        cls.outcomes=audit()

    def test_five_real_races_67_win_runners_439_complete_wide(self):
        x=self.outcomes
        self.assertEqual(x["status"],STATUS)
        self.assertEqual(x["independent_real_races"],5)
        self.assertEqual(x["number_of_meeting_dates"],1)
        self.assertEqual(x["horse_race_entries"],67)
        self.assertEqual(x["full_bet_pairs_not_independent_samples"],439)
        self.assertEqual(x["same_minute_win_wide_races"],3)
        self.assertEqual(x["one_minute_source_update_gap_races"],2)
        self.assertEqual([r["race_no"] for r in x["per_race"]],[8,9,10,11,12])
        self.assertEqual([r["wide_pair_count"] for r in x["per_race"]],
                         [55,66,45,153,120])
        self.assertEqual([r["n_horses"] for r in x["per_race"]],
                         [11,12,10,18,16])
        self.assertEqual([r["official_top3"] for r in x["per_race"]],
                         [[9,1,7],[4,3,12],[5,2,9],[1,4,9],[10,12,9]])

    def test_no_official_outcomes_needed_to_construct_predictions(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)
            for r in range(8,13):
                for rel,source_sha in (*SOURCE_SHA[r],WIDE_SOURCE[r]):
                    dst=target/rel
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(ROOT/rel,dst)
            # The official result is intentionally absent.
            self.assertFalse(
                (target/"data/2026-10-12/official-results-final.json").exists())
            forecasts=pre_race_forecasts(target)
            self.assertEqual(len(forecasts),5)
            self.assertTrue(all("official_top3" not in str(row) for row in forecasts))
            with self.assertRaises((FileNotFoundError,ValueError)):
                audit(target)

    def test_win_top3_wide_trio_mass_stays_coherent_in_every_forecast(self):
        for race in self.predictions:
            n=race["n_horses"]
            self.assertEqual(len(race["forecasts"]),5)
            self.assertLessEqual(race["source_page_update_minute_gap"],1.0)
            for model in race["forecasts"].values():
                self.assertAlmostEqual(sum(model["win"].values()),1,places=9)
                self.assertAlmostEqual(sum(model["top2"].values()),2,places=9)
                self.assertAlmostEqual(sum(model["top3"].values()),3,places=9)
                self.assertAlmostEqual(sum(model["both_top3_pair"].values()),3,places=9)
                self.assertAlmostEqual(sum(model["unordered_top3_trio"].values()),1,
                                       places=9)
                self.assertAlmostEqual(sum(model["ordered_top3_trifecta"].values()),1,
                                       places=9)
                self.assertEqual(len(model["both_top3_pair"]),n*(n-1)//2)
                self.assertEqual(len(model["ordered_top3_trifecta"]),n*(n-1)*(n-2))
                self.assertTrue(model["probabilities_properly_normalized_and_joint_rank_coherent"])

    def test_beta_zero_mathematically_identical_to_original_pl(self):
        from odds_threshold_forward_eval import order_probabilities
        for race in self.predictions:
            odds={i:1/v for i,v in race["forecasts"]["win_PL_baseline"]["win"].items()}
            order=sorted(odds)
            win,top=order_probabilities([1/odds[i] for i in order])
            prediction=race["forecasts"]["win_PL_baseline"]
            for i,w,p in zip(order,win,top):
                self.assertAlmostEqual(prediction["win"][i],w,places=10)
                self.assertAlmostEqual(prediction["top3"][i],p,places=10)

    def test_scores_proper_and_averaged_at_race_not_pair_level(self):
        results=self.outcomes["cohort_means"]
        self.assertEqual(
            results["all_five_one_meeting_day"]["actual_independent_races"],5)
        self.assertEqual(
            results["same_source_update_minute_three_races"]["actual_independent_races"],3)
        self.assertEqual(
            results["one_minute_mismatch_two_races"]["actual_independent_races"],2)
        for group in results.values():
            for v in group["mean_scores_by_model"].values():
                for metric in METRICS:
                    self.assertTrue(math.isfinite(v[metric]))
                    self.assertGreaterEqual(v[metric],0)
                self.assertTrue(all(math.isfinite(z) for z in
                                    v["delta_vs_PL_lower_is_better"].values()))
        self.assertTrue(self.outcomes["raw_official_result_input_not_part_of_predictor"])
        self.assertTrue(self.outcomes["outcome_scores_are_retrospective_not_frozen_or_prospective"])
        self.assertEqual(self.outcomes["coefficients_hypothetical_not_selected_on_outcomes"]
                         ["win_PL_baseline"],{"horse_node_beta":0.0,"pair_residual_beta":0.0})

    def test_official_outcome_changes_scores_but_not_predictions(self):
        prepared=deepcopy(self.predictions)
        base=prepared[0]["forecasts"]["win_PL_baseline"]
        a=score_ranking(base,[9,1,7])
        b=score_ranking(base,[1,9,7])
        self.assertNotEqual(a["win_categorical_log_loss"],
                            b["win_categorical_log_loss"])
        self.assertEqual(prepared,self.predictions)
        self.assertEqual(a["top3_per_horse_binary_brier"],
                         b["top3_per_horse_binary_brier"])
        with self.assertRaisesRegex(ValueError,"HOLD_OFFICIAL_FINISH"):
            score_ranking(base,[9,9,7])
        with self.assertRaisesRegex(ValueError,"HOLD_OFFICIAL_FINISH"):
            score_ranking(base,[9,1,99])

    def test_leave_one_real_race_influence_can_change_metric_conclusion(self):
        v=self.outcomes["one_race_deletion_influence_not_independent_test"]
        a=v["win_categorical_log_loss"]["pair_specific_positive_half"]
        self.assertEqual(a["n_real_races_model_score_better_than_market"],4)
        self.assertEqual(a["n_leave_one_race_out_deltas_below_zero"],5)
        self.assertLess(a["race_equal_mean_delta"],0)
        self.assertFalse(a["sign_switches_when_one_race_removed"])
        b=v["top3_per_horse_binary_brier"]["pair_specific_positive_half"]
        self.assertTrue(b["sign_switches_when_one_race_removed"])
        self.assertLess(b["race_equal_mean_delta"],0)
        self.assertGreater(
            b["leave_one_race_out_race_equal_mean_deltas"]["10"],0)
        self.assertTrue(b["not_future_meeting_day_performance"])
        c=v["unordered_top3_trio_log_loss"]["pair_specific_positive_half"]
        self.assertGreater(c["race_equal_mean_delta"],0)

    def test_missing_WIDE_pair_or_impossible_high_low_rejected(self):
        roster=set(range(1,6))
        items=[
            {"selection":[a,b],"odds_low":5.0,"odds_high":6.0}
            for a,b in combinations(roster,2)]
        prices=_strict_wide_range(items,roster)
        self.assertEqual(len(prices),10)
        with self.assertRaisesRegex(ValueError,"HOLD_WIDE_QUOTE_PAIRS_INCOMPLETE"):
            _strict_wide_range(items[:-1],roster)
        broken=deepcopy(items)
        broken[0]["odds_high"]=1.2
        with self.assertRaisesRegex(ValueError,"HOLD_WIDE_QUOTE_RANGE_INVALID"):
            _strict_wide_range(broken,roster)

    def test_price_mismatch_minutes_recorded_not_disguised(self):
        self.assertEqual(
            [q["page_same_publisher_update_minute"] for q in self.outcomes["per_race"]],
            [True,False,True,False,True])
        for row in self.outcomes["per_race"]:
            self.assertTrue(row["win_page_source_updated_at"].startswith("2026-10-12"))
            self.assertTrue(row["wide_page_source_updated_at"].startswith("2026-10-12"))
            self.assertTrue(row["official_jra_source"].startswith("https://"))
        self.assertTrue(any("not prove atomic" in s for s in
                            self.outcomes["scientific_limitations"]))


if __name__=="__main__":
    unittest.main()
