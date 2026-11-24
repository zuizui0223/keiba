"""Exact source-channel separation in one observed asynchronous Kyoto8R quote history."""
from copy import deepcopy
import math
import unittest

from scripts.ecology_ticket_market_source_channel_decomposition import (
    effect_splits, js_divergence, price_distribution, weighted_cov, run_analysis,
)
from scripts.ecology_ticket_market_two_snapshot_time import (
    EARLY, LATE, read_market_snapshot,
)
import json


class OneRaceSourceChannelDecompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(EARLY.read_text(encoding="utf-8"))
        cls.l=json.loads(LATE.read_text(encoding="utf-8"))

    def test_two_real_sources_and_counterfactual_mixed_states_are_separated(self):
        r=run_analysis()
        self.assertEqual(r["status"],
            "ONE_RACE_TWO_SOURCE_ARITHMETIC_DECOMPOSITION_NOT_CAUSAL_TIME_SERIES")
        self.assertEqual(r["race_id"],"2608040508")
        self.assertEqual(r["horse_count"],11)
        self.assertEqual(r["pair_count"],55)
        self.assertEqual(r["early_win_wide_update_gap_seconds"],660)
        self.assertEqual(r["later_win_wide_update_gap_seconds"],0)
        self.assertLess(r["max_total_equals_win_plus_wide_delta_error"],1e-10)
        self.assertLess(r["max_fixed_weight_node_delta_additivity_error"],1e-10)
        self.assertLess(r["max_fixed_weight_pair_residual_additivity_error"],1e-10)
        self.assertTrue(r["mixed_states_are_algebraic_counterfactual_combinations_not_joint_observations"])
        self.assertEqual(sum(
            v["observed_both_market_feeds_in_archive"]
            for v in r["four_combinations_relative_to_later_state"].values()),2)
        self.assertEqual(len(r["source_file_sha256"]),2)
        self.assertFalse(r["two_archived_price_states_of_ONE_race_only"] is False)
        self.assertTrue(r["cannot_infer_market_voter_learning_or_threshold"])
        self.assertTrue(r["cannot_infer_horse_behavior_kinship_or_genomic_causality"])

    def test_covariance_source_shares_sum_to_one_not_causality(self):
        r=run_analysis()
        pieces=r["source_price_change_covariance_partition"]
        self.assertAlmostEqual(
            pieces["win_source_covariance_share_of_total_logratio_change"]+
            pieces["wide_source_covariance_share_of_total_logratio_change"],
            1.,places=10
        )
        self.assertGreater(pieces["win_source_standalone_change_sd"],0)
        self.assertGreater(pieces["wide_source_standalone_change_sd"],0)
        self.assertTrue(math.isfinite(pieces["total_change_sd"]))
        self.assertIsNone(r["horse_ID_repeatability_confirmed"]) if "horse_ID_repeatability_confirmed" in r else None

    def test_one_source_only_changed_is_handled_without_fake_dynamic_correlation(self):
        earlier=read_market_snapshot(self.e)
        later=deepcopy(self.e)
        later["checked_at_utc"]="2026-10-12T04:44:00+00:00"
        later["markets"]["win"]["updated_at_jst"]="2026-10-12T13:43:00+09:00"
        for row in later["markets"]["win"]["quotes"]:
            if row["selection"]==[1]:
                row["odds_low"]=row["odds_high"]=row["odds_low"]+1.0
        late=read_market_snapshot(later)
        report=effect_splits(earlier,late)
        pieces=report["source_price_change_covariance_partition"]
        self.assertAlmostEqual(pieces["win_source_covariance_share_of_total_logratio_change"],1,places=10)
        self.assertAlmostEqual(pieces["wide_source_covariance_share_of_total_logratio_change"],0,places=10)
        self.assertIsNone(pieces["win_vs_wide_source_change_correlation"])
        self.assertAlmostEqual(report["max_total_equals_win_plus_wide_delta_error"],0,places=10)

    def test_js_and_market_effective_support_not_true_vote_probability(self):
        e=read_market_snapshot(self.e)
        l=read_market_snapshot(self.l)
        for kind,size in (("win",11),("wide",55)):
            a=price_distribution(e,kind)
            b=price_distribution(l,kind)
            self.assertEqual(len(a),size)
            self.assertAlmostEqual(sum(a.values()),1.,places=10)
            self.assertGreater(js_divergence(a,b),0)
            self.assertAlmostEqual(js_divergence(a,a),0,places=10)
            self.assertAlmostEqual(js_divergence(a,b),js_divergence(b,a),places=10)
        with self.assertRaisesRegex(ValueError,"invalid_js_support"):
            js_divergence({1:1.},{2:1.})

    def test_modified_roster_rejected(self):
        early=read_market_snapshot(self.e)
        newer=read_market_snapshot(self.l)
        newer["frames"][1]=7
        with self.assertRaisesRegex(ValueError,"invalid_race_matching_two_states"):
            effect_splits(early,newer)


if __name__=="__main__":
    unittest.main()
