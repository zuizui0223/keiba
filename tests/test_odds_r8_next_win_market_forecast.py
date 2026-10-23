#!/usr/bin/env python3
"""Historical one-race next-WIN market forecast: strict pretarget price isolation."""
from copy import deepcopy
from pathlib import Path
import math
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_r8_next_win_market_forecast import (
    STATUS, audit, source_only_features, construct_advance_forecast,
    evaluate_market_prediction, win_proxy, _permutation_reference,
    NEXT_HORIZON_MINUTES,
)
from odds_real_multirace_archive_audit import SOURCE_SHA
from odds_r8_real_three_time_market import OTHER_SOURCE


class Kyoto8NextWinMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit(permutations=199,seed=20261023)

    def test_prerace_1326_feature_compilation_without_1344_target_file(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)
            source_files=[*SOURCE_SHA[8],OTHER_SOURCE["mid_wide"]]
            for relative,hashval in source_files:
                output=target/relative
                output.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,output)
            self.assertFalse((target/OTHER_SOURCE["late_all"][0]).exists())
            q=source_only_features(target)
            self.assertTrue(q["source_captured_without_future_file"])
            self.assertEqual(q["feature_latest_published"],
                             "2026-10-12T13:26:00+09:00")
            self.assertEqual(q["race_scheduled_post"],"2026-10-12T14:00:00+09:00")
            self.assertEqual(q["prior_earlier_minutes"],65)
            self.assertEqual(q["comparison_horizon_minutes_in_advance"],18)
            self.assertEqual(len(q["last_market_q"]),11)
            self.assertEqual(len(q["wide_extra_horse_node"]),11)
            for beta in (0,.25,-.25):
                pred=construct_advance_forecast(q,beta_node=beta)
                self.assertAlmostEqual(sum(pred.values()),1,places=12)

    def test_three_real_prices_and_model_metrics_match_archived_comparison(self):
        v=self.report
        self.assertEqual(v["status"],STATUS)
        self.assertEqual(v["real_independent_races"],1)
        self.assertEqual(v["comparison_horizon_minutes_retrospective_fixed"],
                         NEXT_HORIZON_MINUTES)
        self.assertEqual(v["source_last_update"],"2026-10-12T13:26:00+09:00")
        self.assertEqual(v["target_source_published"],"2026-10-12T13:44:00+09:00")
        z=v["next_market_price_proxy_scores"]
        self.assertAlmostEqual(
            z["last_win_only"]["normalized_inverse_odds_TV_pp"],
            9.656362948215287,places=10)
        self.assertAlmostEqual(
            z["elapsed_time_scaled_win_momentum"]["normalized_inverse_odds_TV_pp"],
            8.180965354937557,places=10)
        self.assertAlmostEqual(
            z["momentum_plus_wide_node_beta_025"]["normalized_inverse_odds_TV_pp"],
            7.104113542634069,places=10)
        self.assertAlmostEqual(
            z["momentum_plus_wide_node_beta_025"][
                "KL_next_displayed_price_proxy_vs_prediction"],
            .01343535282300255,places=10)

    def test_forecasting_price_distribution_not_race_finish(self):
        v=self.report
        self.assertTrue(v["model_uses_pre_target_win_and_wide_quotes_only"])
        self.assertTrue(
            v["coefficients_are_arbitrary_and_not_trained_or_registered_before_race"])
        self.assertTrue(all(s["not_empirical_winner_probability_log_loss"]
                            for s in v["next_market_price_proxy_scores"].values()))
        self.assertTrue(any("Forecasting later market quotes does not imply" in s
                            for s in v["limitations"]))
        self.assertEqual(len(v["sensitivity_nine_PL_and_conditional_WIDE_mappings"]),9)

    def test_fixed_beta_node_improves_price_only_metric_descriptively(self):
        v=self.report
        self.assertAlmostEqual(v["additional_TV_reduction_vs_momentum_pp"],
                               8.180965354937557-7.104113542634069,places=9)
        self.assertGreater(v["additional_KL_reduction_vs_momentum"],0)
        z=v["next_market_price_proxy_scores"]
        self.assertGreater(
            z["opposite_wide_node_beta_minus025"]["normalized_inverse_odds_TV_pp"],
            z["momentum_plus_wide_node_beta_025"]["normalized_inverse_odds_TV_pp"])
        self.assertLess(
            z["momentum_plus_wide_node_beta_05"]["normalized_inverse_odds_TV_pp"],
            z["momentum_plus_wide_node_beta_025"]["normalized_inverse_odds_TV_pp"])

    def test_source_target_corruption_stops_source_hash_assurance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for spec in [*SOURCE_SHA[8],*OTHER_SOURCE.values()]:
                target=root/spec[0]
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/spec[0],target)
            self.assertEqual(source_only_features(root)["n_horses"],11)
            self.assertEqual(audit(root=root,permutations=99)["real_independent_races"],1)
            path=root/OTHER_SOURCE["late_all"][0]
            path.write_bytes(path.read_bytes()+b" ")
            self.assertEqual(source_only_features(root)["n_horses"],11)
            with self.assertRaisesRegex(ValueError,"HOLD_R8_ARCHIVED_SOURCE_CHANGED"):
                audit(root=root,permutations=99)

    def test_fixed_prequoted_horizon_and_full_horse_roster_gates(self):
        q=source_only_features()
        broken=deepcopy(q)
        broken["comparison_horizon_minutes_in_advance"]=0
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_PREDECLARED_HORIZON"):
            construct_advance_forecast(broken)
        broken=deepcopy(q)
        broken["wide_extra_horse_node"].pop(11)
        with self.assertRaisesRegex(ValueError,"HOLD_CHANGED_MARKET_RUNNER_UNIVERSE"):
            construct_advance_forecast(broken)
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_WIN_QUOTES"):
            win_proxy({1:2,2:3,3:4,4:5,5:-1})

    def test_mathematical_node_label_shuffle_not_formal_significance(self):
        ctrl=self.report["mathematical_horse_label_negative_control"]
        self.assertEqual(ctrl["status"],
                         "EXPLORATORY_WITHIN_ONE_RACE_HORSE_LABEL_SHUFFLE_NOT_P_VALUE")
        self.assertEqual(ctrl["permutations"],199)
        self.assertTrue(0<=ctrl[
            "fraction_label_shuffles_TV_no_worse_than_actual"]<=1)
        self.assertTrue(ctrl["exchangeability_or_significance_not_established"])
        self.assertTrue(ctrl[
            "horse_entries_do_not_constitute_independent_race_replicates"])
        q=source_only_features()
        target=construct_advance_forecast(q)
        x=_permutation_reference(q,target,permutations=99,seed=123)
        y=_permutation_reference(q,target,permutations=99,seed=123)
        self.assertEqual(x,y)

    def test_all_nine_robustness_cases_produce_finite_aggregate_scores(self):
        a=self.report["sensitivity_nine_PL_and_conditional_WIDE_mappings"]
        self.assertEqual(
            set(x["gamma"] for x in a),{.75,1.0,1.25})
        self.assertEqual(
            set(x["WIDE_quote_mapping"] for x in a),
            {"lower","geometric","upper"})
        t=[x["future_market_quote_TV_pp"] for x in a]
        self.assertTrue(all(0<v<100 and math.isfinite(v) for v in t))
        self.assertAlmostEqual(self.report["sensitivity_TV_min_max"][0],min(t))
        self.assertAlmostEqual(self.report["sensitivity_TV_min_max"][1],max(t))


if __name__=="__main__":
    unittest.main()
