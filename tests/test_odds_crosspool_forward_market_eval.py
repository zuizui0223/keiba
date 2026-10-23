#!/usr/bin/env python3
"""Future-date next-market WIN/WIDE: synthetic-only chronology and license gates."""
from copy import deepcopy
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_crosspool_forward_market_eval import (
    SCHEMA, STATUS_HOLD, STATUS_SYN, STATUS_LOCAL,
    COEFF_GRID, ODDS_BANDS, _forecast, evaluate, synthetic_panel,
    prepare_feature_before_future, prepare_target_for_scoring,
)


class ForwardWinWideMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.null=synthetic_panel(seed=20261023,dates=12,
                                 races_per_day=6,planted_wide_beta=0)
        cls.signal=synthetic_panel(seed=20261023,dates=12,
                                   races_per_day=6,planted_wide_beta=.5)

    def test_two_price_targets_have_strict_source_clock_order(self):
        r=self.signal["races"][0]
        f=prepare_feature_before_future(r)
        q=prepare_target_for_scoring(r,f)
        self.assertEqual(f["comparison_horizon_minutes_in_advance"],18)
        self.assertEqual(f["prior_earlier_minutes"],65)
        self.assertEqual(f["n_horses"],11)
        self.assertEqual(len(f["wide_extra_horse_node"]),11)
        self.assertEqual(len(q),11)
        self.assertAlmostEqual(sum(q.values()),1.0)
        self.assertNotIn("target_win",str(f))
        self.assertFalse(any("top3" in k for k in f))
        pred=_forecast(f,bm=1,bn=.5)
        self.assertAlmostEqual(sum(pred.values()),1.0)

    def test_only_train_dates_tune_wide_node(self):
        x=evaluate(self.signal,seed=38)
        self.assertEqual(x["status"],STATUS_SYN)
        self.assertLess(x["train_max_date"],x["future_min_date"])
        self.assertEqual(x["train_race_count"]+x["future_race_count"],72)
        self.assertGreaterEqual(x["future_meeting_days"],4)
        self.assertEqual(set(x["training_only_selected"]),{"smooth","threshold"})
        self.assertIn(x["training_only_selected"]["smooth"]["wide_node_beta"],
                      COEFF_GRID)
        self.assertIn(x["training_only_selected"]["threshold"]
                      ["earlier_win_odds_threshold"],ODDS_BANDS)
        self.assertTrue(x["not_a_race_winner_probability_score"])
        self.assertFalse(x["real_market_source_license_legal_verification_performed"])

    def test_null_and_positive_planted_future_moving_shares(self):
        null=evaluate(self.null,seed=38)
        sig=evaluate(self.signal,seed=38)
        self.assertEqual(null["status"],STATUS_SYN)
        self.assertEqual(sig["status"],STATUS_SYN)
        for response in (null,sig):
            scores=response["future_equal_race_market_price_index_scores"]
            self.assertEqual(set(scores),{
                "current_win_quote_only","elapsed_time_momentum_only",
                "train_selected_wide_horse_node",
                "train_selected_threshold_wide_node",
                "negative_control_shuffled_WIDE_nodes",
            })
            self.assertTrue(all(math.isfinite(value) for
                measure in scores.values() for value in measure.values()))
        self.assertLess(
            sig["future_equal_race_market_price_index_scores"]
               ["train_selected_wide_horse_node"]["market_index_KL"],
            sig["future_equal_race_market_price_index_scores"]
               ["elapsed_time_momentum_only"]["market_index_KL"])

    def test_future_outcomes_cannot_change_selected_coefficients(self):
        a=evaluate(self.signal,seed=222)
        altered=deepcopy(self.signal)
        cutoff=a["train_max_date"]
        for row in altered["races"]:
            if row["post_jst"][:10]>cutoff:
                target=row["target_win"]["odds"]
                row["target_win"]["odds"]={
                    k:float(v)*(.8 if int(k)%2 else 1.2)
                    for k,v in target.items()
                }
        b=evaluate(altered,seed=222)
        self.assertEqual(a["training_only_selected"],b["training_only_selected"])
        self.assertNotEqual(
            a["future_equal_race_market_price_index_scores"],
            b["future_equal_race_market_price_index_scores"])
        f=prepare_feature_before_future(self.signal["races"][-1])
        changed=prepare_feature_before_future(altered["races"][-1])
        self.assertEqual(f,changed)

    def test_future_publication_timestamp_cannot_set_horizon_after_event(self):
        altered=deepcopy(self.signal)
        altered["races"][0]["target_horizon_minutes_predeclared"]=15
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_TARGET_NOT_AT_PREDECLARED"):
            evaluate(altered)
        altered=deepcopy(self.signal)
        altered["races"][0].pop("target_horizon_minutes_predeclared")
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_PREDECLARED"):
            evaluate(altered)
        altered=deepcopy(self.signal)
        altered["races"][0]["target_win"]["source_update_time"]=(
            altered["races"][0]["post_jst"])
        with self.assertRaisesRegex(ValueError,"HOLD_QUOTE_NOT_AVAILABLE"):
            evaluate(altered)

    def test_cross_pool_atomic_clock_not_assumed(self):
        altered=deepcopy(self.signal)
        altered["races"][0]["mid_wide"]["source_update_time"]=(
            altered["races"][0]["early_win"]["source_update_time"])
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_PRESTART_MATCHED"):
            evaluate(altered)
        altered=deepcopy(self.signal)
        altered["races"][0]["mid_wide"]["provider"]="OTHER"
        with self.assertRaisesRegex(ValueError,"HOLD_PROVIDER_SWITCH"):
            evaluate(altered)
        altered=deepcopy(self.signal)
        altered["races"][0]["mid_wide"]["provider_time_verified"]=False
        with self.assertRaisesRegex(ValueError,"HOLD_WRONG_BET_TYPE_OR_UNVERIFIED"):
            evaluate(altered)

    def test_bad_full_wide_grid_and_horse_field_rejected(self):
        altered=deepcopy(self.signal)
        altered["races"][0]["mid_wide"]["pairs"].pop()
        with self.assertRaisesRegex(ValueError,"HOLD_INCOMPLETE_WIDE"):
            evaluate(altered)
        altered=deepcopy(self.signal)
        altered["races"][0]["mid_win"]["odds"].pop("1")
        with self.assertRaisesRegex(ValueError,"HOLD_CHANGED_OR_INCOMPLETE"):
            evaluate(altered)

    def test_minimum_real_race_and_date_gate(self):
        subset=deepcopy(self.signal)
        subset["races"]=subset["races"][:12]
        x=evaluate(subset)
        self.assertEqual(x["status"],STATUS_HOLD)
        self.assertEqual(x["actual_distinct_races"],12)
        self.assertEqual(x["distinct_meeting_dates"],2)

    def test_local_rights_self_attestation_does_not_certify_license(self):
        t=deepcopy(self.signal)
        t["provenance"]="authorized_local_operator"
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_LICENSE"):
            evaluate(t)
        t["license_self_attested"]=True
        x=evaluate(t)
        self.assertEqual(x["status"],STATUS_LOCAL)
        self.assertFalse(x["real_market_source_license_legal_verification_performed"])
        t["raw_records_redistributable"]=True
        with self.assertRaisesRegex(ValueError,"HOLD_NO_SOURCE_RIGHTS"):
            evaluate(t)

    def test_no_real_JRA_quotes_are_needed_for_synthetic_demo(self):
        self.assertEqual(self.null["schema"],SCHEMA)
        self.assertEqual(self.null["provenance"],"synthetic")
        self.assertTrue(all(
            row["mid_win"]["provider"]=="FICTIONAL_IDENTICAL_PROVIDER"
            for row in self.null["races"]))
        self.assertFalse(self.null["raw_records_redistributable"])


if __name__=="__main__":
    unittest.main()
