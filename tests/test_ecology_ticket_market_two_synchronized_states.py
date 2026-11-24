"""Exact 13:26 vs 13:44 source-update-aligned market research gates."""
from copy import deepcopy
import json
import math
import unittest

from scripts.ecology_ticket_market_two_synchronized_states import (
    TFW, WIDE, LATE, reconstruct_early_pair, analysis,
)
from scripts.ecology_ticket_market_two_snapshot_time import read_market_snapshot


class TwoSynchronizedKyoto8RStatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tfw=json.loads(TFW.read_text(encoding="utf-8"))
        cls.wide=json.loads(WIDE.read_text(encoding="utf-8"))
        cls.late=json.loads(LATE.read_text(encoding="utf-8"))

    def test_original_two_price_page_receipt_gap_and_aligned_source_updates(self):
        raw,report=reconstruct_early_pair(self.tfw,self.wide,self.late)
        self.assertEqual(report["earlier_market_source_updated_at"],
                         "2026-10-12T13:26:00+09:00")
        self.assertAlmostEqual(report["win_wide_receipt_gap_seconds"],.242753,places=4)
        self.assertEqual(report["win_wide_source_update_gap_seconds"],0)
        self.assertEqual(report["quotes_win"],11)
        self.assertEqual(report["quotes_wide"],55)
        self.assertFalse(report["raw_html_archived_in_this_analysis"])
        interpreted=read_market_snapshot(raw)
        later=read_market_snapshot(self.late)
        self.assertEqual(interpreted["source_win_wide_update_gap_seconds"],0)
        self.assertEqual(later["source_win_wide_update_gap_seconds"],0)
        self.assertEqual(interpreted["frames"],later["frames"])

    def test_source_aligned_main_reanalysis_and_old_async_sensitivity(self):
        out=analysis()
        self.assertEqual(out["status"],
            "ONE_KYOTO_R8_TWO_SOURCE_TIMESTAMP_ALIGNED_MARKET_STATES_OBSERVED_NOT_CAUSAL")
        self.assertEqual(out["source_timestamp_aligned_quote_update_states"],2)
        self.assertEqual(out["actual_source_updated_elapsed_minutes"],18)
        self.assertTrue(out["earlier_and_later_market_roster_equal"])
        self.assertEqual(len(out["source_file_sha256"]),4)
        compare=out["observed_primary_snapshot_comparison"]
        self.assertEqual(compare["status"],
                         "ONE_RACE_TWO_ARCHIVED_SYNCHRONIZED_SOURCE_UPDATED_PRICE_STATES")
        self.assertTrue(compare["synchronized_early_win_wide_market_state"])
        self.assertEqual(compare["early_win_wide_source_update_gap_seconds"],0)
        self.assertEqual(compare["late_win_wide_source_update_gap_seconds"],0)
        self.assertTrue(math.isfinite(compare["same_race_11_horse_numbered_node_correlation"]))
        self.assertTrue(math.isfinite(compare["same_race_55_dyadic_residual_correlation"]))
        self.assertEqual(out["asynchronous_early_source_sensitivity"]
                         ["early_win_wide_update_gap_seconds"],660)
        self.assertFalse(out["three_archived_price_bundles_form_strict_monotone_source_time_series"])
        self.assertTrue(out["older_mid_state_should_not_be_interpreted_as_clean_time_intermediate"])
        self.assertEqual(len(out["recorded_quote_source_update_time_regressions"]),1)
        regression=out["recorded_quote_source_update_time_regressions"][0]
        self.assertEqual(regression["source_kind"],"win")
        self.assertEqual(regression["source_update_change_minutes"],-4.0)
        self.assertEqual(
            out["three_receipt_order_source_update_time_changes_minutes"]["wide"][0]
            ["source_update_change_minutes"],7.0
        )
        effects=out["arithmetic_source_channel_splits"]
        self.assertLess(effects["max_total_equals_win_plus_wide_delta_error"],1e-10)
        self.assertLess(effects["max_fixed_weight_node_delta_additivity_error"],1e-10)
        self.assertTrue(effects["mixed_states_are_algebraic_counterfactual_combinations_not_joint_observations"])
        self.assertFalse(out["independent_two_race_or_named_individual_repeatability"])
        self.assertTrue(out["posthoc_after_inspecting_old_2026_10_12_race_outcome"])
        self.assertTrue(out["nonlinear_social_feedback_threshold_not_identified"])

    def test_not_allow_reconstructed_source_timestamp_mismatch(self):
        changed=deepcopy(self.tfw)
        changed["updated_at_jst"]="2026-10-12T13:21:00+09:00"
        with self.assertRaisesRegex(ValueError,"early_source_market_not_update_time_aligned"):
            reconstruct_early_pair(changed,self.wide,self.late)
        changed=deepcopy(self.wide)
        changed["observed_at_jst"]="2026-10-12T13:30:00+09:00"
        with self.assertRaisesRegex(ValueError,"early_market_receipts_or_updates_invalid"):
            reconstruct_early_pair(self.tfw,changed,self.late)

    def test_missing_horse_number_or_price_is_hold(self):
        corrupted=deepcopy(self.tfw)
        corrupted["quotes"]["win"].pop()
        with self.assertRaisesRegex(ValueError,"early_win_or_wide_board_incomplete"):
            reconstruct_early_pair(corrupted,self.wide,self.late)
        corrupted=deepcopy(self.wide)
        corrupted["quotes"]["wide"].pop()
        with self.assertRaisesRegex(ValueError,"early_win_or_wide_board_incomplete"):
            reconstruct_early_pair(self.tfw,corrupted,self.late)
        corrupted=deepcopy(self.tfw)
        corrupted["horses"][0]["number"]=2
        with self.assertRaisesRegex(ValueError,"early_horse_frames_inconsistent"):
            reconstruct_early_pair(corrupted,self.wide,self.late)

    def test_fake_source_host_or_html_digest_is_rejected(self):
        corrupted=deepcopy(self.tfw)
        corrupted["url"]="https://evil.example/keiba/race/odds/tfw/2608040508"
        with self.assertRaisesRegex(ValueError,"untrusted_early_source_url"):
            reconstruct_early_pair(corrupted,self.wide,self.late)
        corrupted=deepcopy(self.wide)
        corrupted["html_sha256"]="0"
        with self.assertRaisesRegex(ValueError,"source_html_hash_not_recorded"):
            reconstruct_early_pair(self.tfw,corrupted,self.late)


if __name__=="__main__":
    unittest.main()
