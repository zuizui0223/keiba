"""One observed Kyoto8R dual-snapshot market time audit; no social learning claim."""
from copy import deepcopy
import json
import math
import unittest

from scripts.ecology_ticket_market_two_snapshot_time import (
    EARLY,LATE,RACE_ID,read_market_snapshot,report_two_snapshots,run_analysis,
)


class TwoArchivedMarketStatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=json.loads(EARLY.read_text(encoding="utf-8"))
        cls.second=json.loads(LATE.read_text(encoding="utf-8"))

    def test_both_before_start_but_early_two_markets_asynchronous(self):
        earlier=read_market_snapshot(self.first)
        later=read_market_snapshot(self.second)
        self.assertEqual(earlier["race_id"],RACE_ID)
        self.assertEqual(earlier["start_jst"],later["start_jst"])
        self.assertEqual(earlier["frames"],later["frames"])
        self.assertEqual(len(earlier["win_odds"]),11)
        self.assertEqual(len(earlier["edge_y"]),55)
        self.assertEqual(len(later["edge_y"]),55)
        self.assertEqual(earlier["source_win_wide_update_gap_seconds"],660)
        self.assertEqual(later["source_win_wide_update_gap_seconds"],0)
        self.assertLess(earlier["receipt_jst"],later["receipt_jst"])
        self.assertLess(later["receipt_jst"],later["start_jst"])

    def test_full_reanalysis_measures_not_invents_repeatability(self):
        o=run_analysis(n_permutations=49)
        self.assertEqual(o["status"],
            "ONE_RACE_TWO_ARCHIVED_PRICE_STATES_EARLY_MARKETS_ASYNCHRONOUS")
        self.assertEqual(o["horse_count"],11)
        self.assertEqual(o["full_wide_pairs"],55)
        self.assertEqual(o["horse_node_label_shuffle_reference"]["shuffles"],49)
        self.assertTrue(math.isfinite(o["same_race_11_horse_numbered_node_correlation"]))
        self.assertTrue(math.isfinite(o["same_race_55_dyadic_residual_correlation"]))
        self.assertTrue(math.isfinite(o["source_update_change_node_R2_weighted_late"]))
        self.assertFalse(o["synchronized_early_win_wide_market_state"])
        self.assertFalse(o["actual_voter_or_horse_learning_identified"])
        self.assertFalse(o["model_frozen_before_2026_10_12"])
        self.assertFalse(o["racing_outcomes_used"])
        self.assertEqual(len(o["source_file_sha256"]),2)

    def test_invalid_time_or_race_cannot_promote_old_state(self):
        a=deepcopy(self.first)
        a["race_id"]="wrong"
        with self.assertRaisesRegex(ValueError,"snapshot_wrong_race"):
            read_market_snapshot(a)
        a=deepcopy(self.first)
        a["checked_at_utc"]="2026-10-12T06:30:00+00:00"
        with self.assertRaisesRegex(ValueError,"snapshot_not_before_race_start"):
            read_market_snapshot(a)
        a=deepcopy(self.first)
        a["markets"]["win"]["updated_at_jst"]="2026-10-12T13:48:00+09:00"
        with self.assertRaisesRegex(ValueError,"post_receipt"):
            read_market_snapshot(a)

    def test_missing_market_pair_and_runner_field_rejected(self):
        a=deepcopy(self.first)
        a["horse_frames"].pop("1")
        with self.assertRaisesRegex(ValueError,"snapshot_missing_runner_or_market"):
            read_market_snapshot(a)
        a=deepcopy(self.first)
        a["markets"]["wide"]["quotes"].pop()
        with self.assertRaises(ValueError):
            read_market_snapshot(a)

    def test_same_source_not_valid_later_historical_observation(self):
        other=deepcopy(self.first)
        with self.assertRaisesRegex(ValueError,"not_same_roster_in_two_prior_price_states"):
            report_two_snapshots(self.first,other,n_permutations=49)
        with self.assertRaisesRegex(ValueError,"invalid_descriptive_permutation_count"):
            report_two_snapshots(self.first,self.second,n_permutations=2)


if __name__=="__main__":
    unittest.main()
