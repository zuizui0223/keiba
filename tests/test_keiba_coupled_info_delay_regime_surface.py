#!/usr/bin/env python3
"""Nonlinear horse intensity x delayed bettor information numerical controls."""
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
    import keiba_coupled_info_delay_regime_surface as m
    from keiba_coupled_horse_market_pde import vote_market
    from odds_coherent_hierarchy_rank_bridge import joint_rank_probability
    from itertools import combinations


def sample():
    return {
        "race_id":"TEST_8","race_no":8,"meeting_day":"2026-10-25",
        "first_odds":{i:float(i*2+1) for i in range(1,9)},
        "last_odds":{i:float(i*2+1)*(1.05 if i%2 else .94)
                     for i in range(1,9)},
        "initial_quote_at":"2026-10-25T10:00:00+09:00",
        "latest_quote_at":"2026-10-25T12:00:00+09:00",
        "post_at":"2026-10-25T15:40:00+09:00",
    }


@unittest.skipIf(np is None,"Dedicated numerical CI installs NumPy")
class DelayRegimeUnitTests(unittest.TestCase):
    def test_original_voter_model_unchanged_when_signal_round_default_is_1(self):
        q0=[.28,.21,.17,.12,.09,.06,.04,.03]
        signal=[.15,.13,.16,.14,.11,.10,.09,.12]
        for kind in m.VOTER_TYPES:
            a=vote_market(q0,signal,mode=kind,duration_hours=1.5,seed=42)
            b=vote_market(q0,signal,mode=kind,duration_hours=1.5,
                          seed=42,signal_start_step=1)
            np.testing.assert_array_equal(a["final"],b["final"])
            self.assertEqual(a["triggered_steps"],b["triggered_steps"])
        with self.assertRaisesRegex(ValueError,"INVALID_HORSE_SIGNAL"):
            vote_market(q0,signal,mode="information",duration_hours=1,
                        signal_start_step=0)
        with self.assertRaisesRegex(ValueError,"INVALID_HORSE_SIGNAL"):
            vote_market(q0,signal,mode="information",duration_hours=1,
                        signal_start_step=6)

    def test_never_released_information_cannot_reach_any_voter(self):
        q0=[.35,.24,.15,.10,.06,.04,.035,.025]
        s1=[.1,.1,.1,.1,.1,.1,.2,.2]
        s2=[.3,.2,.1,.1,.1,.1,.05,.05]
        for kind in m.VOTER_TYPES:
            a=vote_market(q0,s1,mode=kind,seed=92,duration_hours=1,
                signal_start_step=5)
            b=vote_market(q0,s2,mode=kind,seed=92,duration_hours=1,
                signal_start_step=5)
            np.testing.assert_array_equal(a["final"],b["final"])
            self.assertEqual(a["information_visible_round_count"],0)
        # An information-only bettor without the signal is exactly a q0
        # independent voter under common random uniforms.
        x=vote_market(q0,s1,mode="information",seed=92,duration_hours=1,
                signal_start_step=5)
        y=vote_market(q0,s1,mode="independent",seed=92,duration_hours=1)
        np.testing.assert_array_equal(x["final"],y["final"])

    def test_before_signal_path_is_identical_under_early_and_delayed_release(self):
        q0=[.35,.24,.15,.10,.06,.04,.035,.025]
        signal=[.1,.1,.1,.1,.1,.1,.2,.2]
        for kind in ("information","mixed","threshold_mixed"):
            early=vote_market(q0,signal,mode=kind,seed=41,
                              duration_hours=1.0,signal_start_step=1)
            late=vote_market(q0,signal,mode=kind,seed=41,
                             duration_hours=1.0,signal_start_step=3)
            # the late model cannot receive signal in the first two rounds.
            for p in late["path"][:3]:
                self.assertAlmostEqual(sum(p),1,places=13)
            neutral=vote_market(q0,signal,mode=kind,seed=41,
                                duration_hours=1.0,signal_start_step=5)
            for step in range(3):
                np.testing.assert_array_equal(late["path"][step],
                                              neutral["path"][step])
            self.assertEqual(late["information_visible_round_count"],2)
            self.assertEqual(early["information_visible_round_count"],4)

    def test_full_strength_arrival_grid_shared_horse_draws_and_zero_information_null(self):
        row=sample()
        p=m.vector([.32,.24,.17,.10,.07,.045,.035,.02])
        r=m.prepare_regimes(row,p,distance_m=1400,draws=50,seed=9)
        self.assertEqual(len(r["regimes"]),len(m.CROWD_STRENGTH_GRID))
        c0=r["regimes"][m._key(0)]
        self.assertAlmostEqual(c0["horse_win_TV_from_c0_pp"],0,places=12)
        for c in m.CROWD_STRENGTH_GRID:
            case=r["regimes"][m._key(c)]
            for step in m.SIGNAL_START_ROUNDS:
                for mode in m.VOTER_TYPES:
                    s=case["market_by_arrival"][step][mode]
                    self.assertAlmostEqual(sum(s["forecast"]["win"]),1,places=11)
                    self.assertAlmostEqual(sum(s["forecast"]["top3"]),3,places=11)
                    if step==5 or mode in ("independent","herding"):
                        self.assertEqual(s["crowd_to_market_TV_pp"],0)
        self.assertTrue(r["no_actual_finish_or_later_price_used_by_agents"])

    def test_later_quote_and_target_outcome_do_not_change_any_regime_prediction(self):
        row=sample()
        prior=[.29,.22,.17,.11,.08,.06,.04,.03]
        a=m.prepare_regimes(row,prior,distance_m=1400,draws=40,seed=17)
        later=copy.deepcopy(row)
        later["last_odds"]={i:float(i*4+3) for i in range(1,9)}
        later["actual_top3"]=[6,1,2]
        later["payout"]=999999
        b=m.prepare_regimes(later,prior,distance_m=1400,draws=40,seed=17)
        for c in m.CROWD_STRENGTH_GRID:
            aa=a["regimes"][m._key(c)]
            bb=b["regimes"][m._key(c)]
            np.testing.assert_array_equal(aa["animal_WIN"],bb["animal_WIN"])
            for arrival in m.SIGNAL_START_ROUNDS:
                for mode in m.VOTER_TYPES:
                    np.testing.assert_array_equal(
                        aa["market_by_arrival"][arrival][mode]["market"],
                        bb["market_by_arrival"][arrival][mode]["market"])

    def test_ordered_finish_ticket_universe_uses_one_coherent_PL(self):
        market=m.vector([5,3,2,6,4,1,1])
        p=m.win_top3_from_market(market)
        ids=list(range(1,8))
        odds={i:float(1/z) for i,z in zip(ids,market)}
        joint=joint_rank_probability(odds,{i:0. for i in ids},
                           {x:0. for x in combinations(ids,2)})
        for j,i in enumerate(ids):
            self.assertAlmostEqual(p["win"][j],joint["win"][i],places=11)
            self.assertAlmostEqual(p["top3"][j],joint["top3"][i],places=11)
        self.assertAlmostEqual(sum(joint["both_top3_pair"].values()),3.,places=10)
        self.assertAlmostEqual(sum(joint["unordered_top3_trio"].values()),1.,places=10)
        self.assertAlmostEqual(sum(joint["ordered_top3_trifecta"].values()),1.,places=10)

    def test_c0_physical_drift_pde_analytic_reference_separates_grid_error(self):
        p=[.30,.25,.17,.12,.08,.05,.03]
        x=m.pde_density_and_agent_check(p,strength=0,particles=600,
                                        seed=22,duration_s=12)
        self.assertAlmostEqual(x["min_horse_probability_mass"],1,places=10)
        self.assertIsNotNone(x["analytic_no_interaction_PDE_CDF_max_error"])
        self.assertLess(x["analytic_no_interaction_PDE_CDF_max_error"],.07)
        crowd=m.pde_density_and_agent_check(p,strength=8,particles=600,
                                             seed=22,duration_s=12)
        self.assertIsNone(crowd["analytic_no_interaction_PDE_CDF_max_error"])
        self.assertTrue(crowd["nonnegative_density"])
        self.assertTrue(0<=crowd[
            "mean_abs_interhorse_position_correlation_particle"]<=1)
        self.assertAlmostEqual(crowd["min_horse_probability_mass"],1,places=9)


@unittest.skipUnless(np is not None and (
    ROOT/"data/2026-10-12/v3-normalized-prerace-history.json").exists(),
    "Requires complete source-locked archive and NumPy")
class RealHistoricalCohortTests(unittest.TestCase):
    def test_preoutcome_mode_never_requests_postrace_official_results(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("ILLEGAL_RESULT_READ")):
            q=m.audit(draws=40,pde_particles=250,include_official=False)
        self.assertEqual(q["status"],
                         "PREOUTCOME_COMPUTATION_ONLY_NO_JRA_RESULT_OPENED")
        self.assertEqual(q["official_scores"],"NOT_COMPUTED")
        self.assertEqual(q["horse_race_entries"],84)
        self.assertFalse(q["not_a_discovered_biological_or_market_critical_point"]
                         is False)

    def test_historical_six_race_proper_scoring_does_not_fit_regime_from_outcome(self):
        q=m.audit(draws=40,pde_particles=250,include_official=True)
        self.assertEqual(q["independent_real_races"],6)
        self.assertEqual(q["independent_meeting_dates"],2)
        self.assertEqual(set(q["physical_crowd_intensity_response"]),
                         set(m.PRIOR_ARMS))
        self.assertEqual(len(q["mean_equal_race_scores"]["initial_market"]),
                         len(m.CROWD_STRENGTH_GRID))
        for arm in m.PRIOR_ARMS:
            for c in m.CROWD_STRENGTH_GRID:
                for arrival in m.SIGNAL_START_ROUNDS:
                    for mode in m.VOTER_TYPES:
                        x=q["mean_equal_race_scores"][arm][m._key(c)][
                            str(arrival)][mode]
                        self.assertTrue(x["winner_log_loss"]>0)
                        self.assertTrue(x["top3_brier"]>=0)
                        if arrival==5 or mode in ("independent","herding"):
                            self.assertEqual(
                                x["counterfactual_crowd_to_market_TV_pp"],0)
            for st in m.PDE_STRENGTH_GRID:
                p=q["PDE_one_representative_race_not_empirical_GPS"][arm][m._key(st)]
                self.assertAlmostEqual(p["min_horse_probability_mass"],1,places=8)
                self.assertTrue(p["CFL_upper_bound"] < .95)
        self.assertEqual(q["market_or_biological_threshold_inference"],"HOLD")
        self.assertTrue(q["official_outcomes_scored_only_after_all_regimes_frozen_in_memory"])


if __name__=="__main__":
    unittest.main()
