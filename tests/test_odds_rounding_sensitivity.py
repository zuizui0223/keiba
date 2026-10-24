#!/usr/bin/env python3
"""Hypothetical quote rounding falsification; no actual flow recovered."""
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from shuka2026_odds_information_hierarchy import load_snapshots,read_locked
from odds_rounding_sensitivity import (
    STATUS,audit,hypothetical_share_intervals,interval_lower_bound
)


class RoundoffSensitivityTests(unittest.TestCase):
    def test_known_true_shares_inside_hypothetical_floor_envelope(self):
        q={1:.5,2:.3,3:.2}
        odds={i:math.floor((.8/v)*10+1e-12)/10 for i,v in q.items()}
        z=hypothetical_share_intervals(odds)
        self.assertEqual(z["status"],"HYPOTHETICAL_DISPLAY_FLOOR_SIMPLEX_FEASIBLE")
        for horse in q:
            bounds=z["source_share_intervals"][horse]
            self.assertLessEqual(bounds["lower"]-1e-12,q[horse])
            self.assertGreaterEqual(bounds["upper"]+1e-12,q[horse])
        self.assertTrue(z["not_actual_bet_shares_or_certified_jra_inverse"])

    def test_incompatible_hypothesis_emits_hold_not_fake_share(self):
        z=hypothetical_share_intervals({1:9.9,2:9.9,3:9.9})
        self.assertEqual(z["status"],"HOLD_DISPLAY_FLOOR_HYPOTHESIS_INCOMPATIBLE_WITH_TOTAL_POOL")
        self.assertIsNone(z["source_share_intervals"])

    def test_expected_four_snapshots_are_individually_feasible(self):
        s=load_snapshots(read_locked())
        self.assertEqual(len(s),4)
        for item in s:
            bounds=hypothetical_share_intervals(item["win"])
            self.assertLess(bounds["sum_lower"],1.0)
            self.assertGreater(bounds["sum_upper"],1.0)
            self.assertLess(bounds["direct_normalized_inverse_odds_proxy_coordinates_inside_floor_intervals"],17)

    def test_proxy_and_floor_bound_differ_conservatively(self):
        z=audit()
        self.assertEqual(z["status"],STATUS)
        self.assertTrue(z["display_rounding_rule_is_NOT_VERIFIED"])
        self.assertFalse(z["actual_pool_totals_observed"])
        self.assertEqual(len(z["transitions"]),3)
        expect_proxy=[.056333415535319564,.17202998646422618,.027504690333371107]
        expect_hypothetical=[.057923497267759694,.19873417721518982,.02031340684852012]
        for row,a,b in zip(z["transitions"],expect_proxy,expect_hypothetical):
            self.assertAlmostEqual(row["proxy_lambda_min_exact_if_proxy_were_true"],a,places=9)
            q=row["alternative_hypothetical_floor_conservative"]
            self.assertAlmostEqual(
                q["necessary_minimum_lambda_regardless_of_unobserved_rounding"],
                b,places=9)
            self.assertTrue(q["bound_not_proven_sharp"])
            self.assertTrue(q["not_a_lower_bound_on_real_JRA_wager_turnover"])
        self.assertTrue(z["transitions"][1]["provider_changed"])

    def test_broken_prices_fail_and_cross_horse_universe_rejected(self):
        for odds in ({1:1.6,2:2.6,3:1.0},
                     {1:1.6,2:2.65,3:4.0},
                     {1:1.6,2:float("nan"),3:4.0}):
            with self.assertRaises(ValueError):
                hypothetical_share_intervals(odds)
        s=load_snapshots(read_locked())
        a=hypothetical_share_intervals(s[0]["win"])
        b=hypothetical_share_intervals(s[1]["win"])
        b["source_share_intervals"].pop(17)
        with self.assertRaisesRegex(ValueError,"HOLD_DIFFERENT_HORSE_SETS"):
            interval_lower_bound(a,b)

    def test_rate_perturbation_and_not_real_turnover(self):
        snaps=load_snapshots(read_locked())
        a=hypothetical_share_intervals(snaps[0]["win"],rate=.8,tick=.1)
        b=hypothetical_share_intervals(snaps[0]["win"],rate=.6,tick=.1)
        self.assertEqual(a["status"],"HYPOTHETICAL_DISPLAY_FLOOR_SIMPLEX_FEASIBLE")
        self.assertEqual(b["status"],"HOLD_DISPLAY_FLOOR_HYPOTHESIS_INCOMPATIBLE_WITH_TOTAL_POOL")


if __name__=="__main__":
    unittest.main()
