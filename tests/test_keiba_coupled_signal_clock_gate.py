#!/usr/bin/env python3
"""Source arrival -> earliest permissible voter-information round, local only."""
from __future__ import annotations
import copy
from datetime import datetime,timedelta,timezone
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import keiba_coupled_signal_clock_gate as gate
try:
    import numpy as np
    from keiba_coupled_horse_market_pde import vote_market
except ModuleNotFoundError:
    np=None


def panel(signal="2026-11-01T12:30:00+09:00"):
    return {
        "schema":gate.CLOCK_SCHEMA,
        "externally_authenticated_by_third_party":False,
        "first_win_quote_published_at":"2026-11-01T11:58:00+09:00",
        "first_win_quote_received_at":"2026-11-01T12:00:00+09:00",
        "later_win_quote_published_at":"2026-11-01T12:59:00+09:00",
        "later_win_quote_received_at":"2026-11-01T13:00:00+09:00",
        "local_forecast_created_at":"2026-11-01T13:05:00+09:00",
        "scheduled_post_at":"2026-11-01T15:00:00+09:00",
        "horse_signal_published_at":"2026-11-01T11:30:00+09:00",
        "horse_signal_received_at":signal,
    }


class SourceClockUnitTest(unittest.TestCase):
    def test_exact_round_start_and_epsilon_after_are_causally_distinct(self):
        expected={
          "2026-11-01T11:55:00+09:00":1,
          "2026-11-01T12:00:00+09:00":1,
          "2026-11-01T12:00:01+09:00":2,
          "2026-11-01T12:15:00+09:00":2,
          "2026-11-01T12:15:01+09:00":3,
          "2026-11-01T12:30:00+09:00":3,
          "2026-11-01T12:30:01+09:00":4,
          "2026-11-01T12:45:00+09:00":4,
          "2026-11-01T12:45:01+09:00":5,
          "2026-11-01T13:00:00+09:00":5,
          "2026-11-01T13:03:00+09:00":5,
        }
        for t,n in expected.items():
            with self.subTest(timestamp=t):
                obj=gate.source_clock_to_voter_round(panel(t))
                self.assertEqual(obj["signal_first_visible_voter_round"],n)
                self.assertEqual(obj["signal_available_round_count"],
                                 max(0,5-n))
                self.assertFalse(obj["independent_external_clock_validation"])

    def test_quote_received_after_forecast_or_publication_times_invalid(self):
        for k,t in (
            ("first_win_quote_received_at","2026-11-01T13:01:00+09:00"),
            ("later_win_quote_received_at","2026-11-01T13:07:00+09:00"),
            ("local_forecast_created_at","2026-11-01T14:55:00+09:00"),
            ("later_win_quote_published_at","2026-11-01T11:30:00+09:00"),
        ):
            obj=panel()
            obj[k]=t
            with self.subTest(clock=k):
                with self.assertRaisesRegex(ValueError,"QUOTE_RECEPTION_CLOCKS"):
                    gate.source_clock_to_voter_round(obj)

    def test_receiving_signal_before_original_publication_rejected(self):
        obj=panel("2026-11-01T12:00:00+09:00")
        obj["horse_signal_published_at"]="2026-11-01T12:01:00+09:00"
        with self.assertRaisesRegex(ValueError,"PRECEDES_PUBLICATION"):
            gate.source_clock_to_voter_round(obj)

    def test_signal_from_future_after_forecast_cannot_set_earlier_round(self):
        obj=panel("2026-11-01T13:06:00+09:00")
        with self.assertRaisesRegex(ValueError,"NOT_KNOWN_AT_LOCAL_FORECAST"):
            gate.source_clock_to_voter_round(obj)

    def test_local_receipt_is_not_self_attested_external_proof(self):
        obj=panel()
        obj["externally_authenticated_by_third_party"]=True
        with self.assertRaisesRegex(ValueError,"SELF_ASSERTED_EXTERNAL"):
            gate.source_clock_to_voter_round(obj)
        obj=panel()
        obj["first_win_quote_received_at"]="2026-11-01T12:00:00"
        with self.assertRaisesRegex(ValueError,"NAIVE"):
            gate.source_clock_to_voter_round(obj)

    def test_status_never_promotes_to_empirical_threshold(self):
        x=gate.source_clock_to_voter_round(panel())
        self.assertEqual(x["status"],gate.STATUS)
        self.assertTrue(x["no_real_critical_price_or_biological_phase_identified"])
        self.assertFalse(x["actual_human_bet_timestamps_observed"])


@unittest.skipIf(np is None,"Needs optional numerical voter simulator")
class ClockToVoterCouplingTest(unittest.TestCase):
    def test_real_clock_mapping_changes_only_permitted_voter_rounds(self):
        q0=[.35,.24,.15,.10,.06,.04,.035,.025]
        x=[.11,.10,.12,.16,.14,.12,.13,.12]
        y=[.30,.22,.15,.10,.08,.06,.05,.04]
        late_round=gate.source_clock_to_voter_round(panel())[
            "signal_first_visible_voter_round"]
        self.assertEqual(late_round,3)
        for k in ("information","mixed","threshold_mixed"):
            a=vote_market(q0,x,mode=k,duration_hours=1.0,
                          seed=100,signal_start_step=late_round)
            b=vote_market(q0,y,mode=k,duration_hours=1.0,
                          seed=100,signal_start_step=late_round)
            for i in range(3):
                np.testing.assert_array_equal(a["path"][i],b["path"][i])
        never=gate.source_clock_to_voter_round(panel(
            "2026-11-01T12:59:50+09:00"))["signal_first_visible_voter_round"]
        self.assertEqual(never,5)
        a=vote_market(q0,x,mode="information",duration_hours=1,
                      seed=92,signal_start_step=never)
        b=vote_market(q0,y,mode="information",duration_hours=1,
                      seed=92,signal_start_step=never)
        np.testing.assert_array_equal(a["final"],b["final"])


if __name__=="__main__":
    unittest.main()
