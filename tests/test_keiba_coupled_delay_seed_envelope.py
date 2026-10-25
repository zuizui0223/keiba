#!/usr/bin/env python3
"""Monte Carlo seed repetition must never masquerade as real race replication."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_coupled_delay_seed_envelope as m


def row():
    return {
        "race_id":"FAKE_8","race_no":8,"meeting_day":"2026-10-25",
        "first_odds":{i:float(i*2+1) for i in range(1,9)},
        "last_odds":{i:float(i*2+1)*(1.05 if i%2 else .94)
                     for i in range(1,9)},
        "initial_quote_at":"2026-10-25T10:00:00+09:00",
        "latest_quote_at":"2026-10-25T12:00:00+09:00",
        "post_at":"2026-10-25T15:40:00+09:00",
    }


@unittest.skipIf(np is None,"Dedicated NumPy workflow required")
class SeedPureTests(unittest.TestCase):
    def test_exact_pair_counterfactual_same_seed_and_zero_when_no_information(self):
        p=[.33,.23,.17,.10,.065,.045,.035,.025]
        a=m.individual_causal_response(row(),p,distance_m=1600,
                                       draws=100,seed=42)
        b=m.individual_causal_response(row(),p,distance_m=1600,
                                       draws=100,seed=42)
        self.assertEqual(a,b)
        self.assertEqual(a[5],0)
        self.assertGreaterEqual(a[1],0)
        self.assertGreaterEqual(a[3],0)

    def test_future_quote_and_winner_cannot_change_any_signal_response(self):
        p=[.33,.23,.17,.10,.065,.045,.035,.025]
        x=row()
        a=m.individual_causal_response(x,p,distance_m=1400,draws=70,seed=9)
        future={**x,"last_odds":{i:float(i+9) for i in range(1,9)},
                "future_winner":2,"payout":900000}
        b=m.individual_causal_response(future,p,distance_m=1400,
                                        draws=70,seed=9)
        self.assertEqual(a,b)


@unittest.skipUnless(np is not None and (
    ROOT/"data/2026-10-12/v3-normalized-prerace-history.json").exists(),
    "Full source-locked history checkout needed")
class SameRaceRealArchivesTests(unittest.TestCase):
    def test_repeating_synthetic_seeds_is_not_new_independent_races(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("OFFICIAL_RESULT_LEAK")):
            r=m.audit(seed_count=2,draws=60,seed=20261025)
        self.assertEqual(r["real_races"],6)
        self.assertEqual(r["real_meeting_dates"],2)
        self.assertEqual(r["synthetic_seed_repeat_count"],2)
        self.assertTrue(r["same_real_races_reused_for_seed_repetitions"])
        self.assertTrue(r["no_official_outcomes_read"])
        self.assertEqual(set(r["by_horse_initial_prior"]),{
            "initial_market","historical_form"})
        for arm in r["by_horse_initial_prior"].values():
            self.assertEqual(arm["seed_repetitions_any_no_info_response"],0)
            no=arm["ranges"]["mean_six_races_market_TV_no_info_pp"]
            self.assertEqual(no["maximum_across_seeds"],0)
            self.assertTrue(0<=arm["seed_repetitions_early_exceeds_delayed"]<=2)


if __name__=="__main__":
    unittest.main()
