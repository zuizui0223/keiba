#!/usr/bin/env python3
"""Falsification QA: hard gate is an assumed rule, not observed information."""
from __future__ import annotations

import copy
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
    import keiba_endogenous_threshold_null_bridge as m
    from keiba_coupled_horse_market_pde import vote_market


def row():
    return {
        "race_id":"DEMO_8","race_no":8,"meeting_day":"2026-11-01",
        "first_odds":{i:float(i*2+1) for i in range(1,9)},
        "last_odds":{i:float(i*2+1)*(1.05 if i%2 else .94)
                     for i in range(1,9)},
        "initial_quote_at":"2026-11-01T10:00:00+09:00",
        "latest_quote_at":"2026-11-01T12:00:00+09:00",
        "post_at":"2026-11-01T15:40:00+09:00",
    }


@unittest.skipIf(np is None,"Dedicated numerical CI installs NumPy")
class ThreeSocialLawTests(unittest.TestCase):
    def test_fixed_and_preset_hard_exact_original_voter_model(self):
        q=m.vector([.30,.21,.16,.12,.09,.05,.04,.03])
        signal=m.vector([.15,.10,.18,.12,.08,.09,.14,.14])
        for n in (1,3,5):
            for policy,old in (("fixed","mixed"),
                               ("hard","threshold_mixed")):
                ref=vote_market(q,signal,mode=old,duration_hours=.75,
                                seed=123,steps=4,signal_start_step=n)
                a=m.voter_path(q,signal,policy=policy,
                               duration_hours=.75,seed=123,steps=4,
                               arrival=n)
                np.testing.assert_array_equal(ref["final"],a["final"])
                for x,y in zip(ref["path"],a["path"]):
                    np.testing.assert_array_equal(x,y)
                self.assertEqual(ref["triggered_steps"],
                                 a["hard_gate_active_round_count"])

    def test_hard_discontinuity_was_inserted_continuous_has_no_jump(self):
        c=m.RATE_SCALE_LOG_PER_HOUR
        eps=1e-7
        self.assertEqual(m.herd_exponent(c-eps,"hard"),m.HERD_BASE)
        self.assertEqual(m.herd_exponent(c,"hard"),m.HERD_MAX)
        self.assertAlmostEqual(m.herd_exponent(c+eps,"hard"),m.HERD_MAX)
        self.assertLess(abs(
            m.herd_exponent(c+eps,"smooth")-
            m.herd_exponent(c-eps,"smooth")),1e-5)
        self.assertEqual(m.herd_exponent(c,"fixed"),m.HERD_BASE)
        self.assertTrue(m.HERD_BASE < m.herd_exponent(c,"smooth") <
                        m.HERD_MAX)

    def test_missing_horse_information_never_changes_market(self):
        q0=m.vector([.30,.21,.16,.12,.09,.05,.04,.03])
        a=m.vector([.16,.14,.10,.14,.14,.1,.1,.12])
        b=m.vector([.34,.26,.15,.10,.07,.04,.025,.015])
        for policy in m.RULES:
            one=m.voter_path(q0,a,policy=policy,duration_hours=1.0,
                             arrival=5,seed=42)
            two=m.voter_path(q0,b,policy=policy,duration_hours=1.0,
                             arrival=5,seed=42)
            np.testing.assert_array_equal(one["final"],two["final"])
            self.assertEqual(one["information_available_round_count"],0)
            self.assertAlmostEqual(sum(one["final"]),1.,places=13)

    def test_synthetic_hard_null_can_cross_without_information(self):
        q=m.vector([.30,.20,.16,.12,.09,.055,.045,.03])
        out=m.null_market_scan(q,1.2,seeds=35,seed=33)
        for mode in m.NULL_RULES:
            # Identical ballots but normalized over 1h vs 22h:
            # time denominator itself can produce apparent rate regimes.
            a=out["normalized_1h"][mode]
            b=out["normalized_22h"][mode]
            self.assertGreater(a["null_gate_rounds_total"],0)
            self.assertGreaterEqual(a["null_gate_rounds_total"],
                                    b["null_gate_rounds_total"])
            self.assertGreaterEqual(a["null_runs_with_1plus_gate"],0)
            self.assertLessEqual(a["null_runs_with_1plus_gate"],35)

    def test_regime_pairing_and_future_quote_result_firewall(self):
        p=m.vector([.29,.23,.17,.10,.075,.055,.045,.035])
        base=m.preoutcome_panel(row(),p,distance_m=1800,
                                draws=60,seed=9)
        amended=copy.deepcopy(row())
        amended["last_odds"]={i:float(5+2*i) for i in range(1,9)}
        amended["actual_winner"]=7
        amended["payout"]="$$$"
        z=m.preoutcome_panel(amended,p,distance_m=1800,
                             draws=60,seed=9)
        for c in ("0.0","2.0"):
            for n in m.ARRIVALS:
                for law in m.RULES:
                    x=base["models"][c][n][law]
                    y=z["models"][c][n][law]
                    np.testing.assert_array_equal(x["market"],y["market"])
                    self.assertAlmostEqual(sum(x["rank_forecast"]["win"]),1.)
                    self.assertAlmostEqual(sum(x["rank_forecast"]["top3"]),3.)
        for law in m.RULES:
            x=base["models"]["0.0"][5][law]
            y=base["models"]["2.0"][5][law]
            np.testing.assert_array_equal(x["market"],y["market"])
            self.assertEqual(x["crowd_to_market_TV_pp"],0)
        self.assertTrue(base["no_real_podium_or_later_market_used_by_simulator"])

    def test_invalid_market_signal_or_rate_rejected(self):
        q=[.4,.2,.15,.10,.08,.05,.02]
        with self.assertRaisesRegex(ValueError,"INVALID_SOCIAL_RATE"):
            m.herd_exponent(-.02,"smooth")
        with self.assertRaisesRegex(ValueError,"INVALID_VOTER"):
            m.voter_path(q,q,policy="unknown",duration_hours=1)
        with self.assertRaisesRegex(ValueError,"INVALID_VOTER"):
            m.voter_path(q,q,policy="fixed",duration_hours=0)
        with self.assertRaisesRegex(ValueError,"INVALID_VOTER"):
            m.voter_path(q,q,policy="hard",duration_hours=1,arrival=7)


@unittest.skipUnless(np is not None and (
    ROOT/"data/2026-10-12/v3-normalized-prerace-history.json").exists(),
    "Requires source-locked full checkout, NumPy and saved real market cohort")
class ArchivedNullGateTests(unittest.TestCase):
    def test_six_historical_market_rosters_and_no_outcome_mode(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("ILLEGAL_OFFICIAL_RESULT")) as mock:
            x=m.run_source_locked(draws=40,seeds=5,include_official=False)
            mock.assert_not_called()
        self.assertEqual(x["source_races"],6)
        self.assertEqual(x["source_meeting_dates"],2)
        self.assertEqual(x["horse_race_entries"],84)
        self.assertEqual(x["official_score"],"NOT_COMPUTED")
        self.assertEqual(x["status"],
                         "PREOUTCOME_ONLY_NULL_AND_SYNTHETIC_NO_JRA_RESULTS_LOADED")
        self.assertEqual(set(x["by_source_meeting_date_null"]),
                         {"2026-10-12","2026-10-18"})

    def test_six_real_official_labels_only_after_all_model_paths(self):
        out=m.run_source_locked(draws=40,seeds=5,include_official=True)
        self.assertTrue(out[
            "official_outcomes_read_only_after_all_horse_market_and_null_models"])
        self.assertEqual(set(out["historical_scores"]),set(m.PRIOR_ARMS))
        for arm in m.PRIOR_ARMS:
            r=out["historical_scores"][arm]
            self.assertEqual(set(r),{"0.0","2.0"})
            for crowd in ("0.0","2.0"):
                for arrival in m.ARRIVALS:
                    for law in m.RULES:
                        row=r[crowd][str(arrival)][law]
                        self.assertGreater(row["winner_log_loss"],0)
                        self.assertGreaterEqual(row["top3_brier"],0)
                        if arrival==5:
                            self.assertEqual(
                                row["model_counterfactual_crowd_to_market_TV_pp"],0)
        self.assertEqual(out["official_or_criticality_evidence"],"HOLD")
        self.assertEqual(len(out["date_equal_scores"]),2)


if __name__=="__main__":
    unittest.main()
