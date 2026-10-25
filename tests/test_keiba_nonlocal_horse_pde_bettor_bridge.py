#!/usr/bin/env python3
"""Unit and archival tests for shared nonlocal horse ABM/PDE/bettor law."""
from __future__ import annotations
from pathlib import Path
import math
import sys
import unittest
from unittest.mock import patch
try:
    import numpy as np
except ModuleNotFoundError:
    np=None  # Generic and frozen-v3.1 test suites intentionally omit NumPy.

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_nonlocal_horse_pde_bettor_bridge as m


def demo_row():
    return {"race_id":"SIMULATED_2026","race_no":11,
            "meeting_day":"2026-10-25",
            "first_odds":{i:float(2*i+1) for i in range(1,9)},
            "last_odds":{i:float(2*i+1)*(1.1 if i%2 else .95)
                         for i in range(1,9)},
            "initial_quote_at":"2026-10-25T10:00:00+09:00",
            "latest_quote_at":"2026-10-25T12:00:00+09:00",
            "post_at":"2026-10-25T15:40:00+09:00"}


@unittest.skipIf(np is None, "NumPy belongs to the dedicated horse-physics CI")
class NonlocalMathematicalTests(unittest.TestCase):
    def test_kernel_is_anisotropic_bounded_and_has_no_self_effect(self):
        gaps=np.asarray([-3.,0.,2.,8.,9.])
        got=m.ahead_kernel(gaps)
        self.assertEqual(got[0],0)
        self.assertEqual(got[1],0)
        self.assertGreater(got[2],0)
        self.assertGreater(got[3],0)
        self.assertEqual(got[4],0)
        x=np.tile([0.,2.,4.,6.,8.,10.,12.,14.],(30,1))
        penalty=m.crowd_density_agent(x)
        self.assertGreater(penalty[0,0],0)
        self.assertEqual(penalty[0,-1],0)
        perm=[7,2,4,0,1,5,6,3]
        new=m.crowd_density_agent(x[:,perm])
        np.testing.assert_allclose(new,penalty[:,perm],rtol=0,atol=1e-15)

    def test_sampled_finish_counterfactuals_share_noise(self):
        prior=[.32,.24,.17,.10,.07,.045,.035,.02]
        a=m.finish_pair(prior,distance_m=1600,draws=550,
                        seed=42,crowd_coefficient=3.)
        b=m.finish_pair(prior,distance_m=1600,draws=550,
                        seed=42,crowd_coefficient=3.)
        self.assertEqual(a["paired_prob_winner_difference"],
                         b["paired_prob_winner_difference"])
        for key in m.CROWD_SCENARIOS:
            for typ,total in (("win",1.),("top3",3.)):
                np.testing.assert_array_equal(
                    a["scenarios"][key][typ],b["scenarios"][key][typ])
                self.assertAlmostEqual(sum(a["scenarios"][key][typ]),
                                       total,places=12)
        self.assertGreater(a["paired_prob_any_first_three_order_difference"],0)
        self.assertGreater(a["paired_prob_winner_difference"],0)
        c=m.finish_pair(prior,distance_m=1600,draws=90,
                        seed=3,crowd_coefficient=0.)
        for typ in ("win","top3","ordered_top3"):
            np.testing.assert_array_equal(c["scenarios"]["no_crowd"][typ],
                                          c["scenarios"]["nonlocal_crowd"][typ])

    def test_nonlinear_crowd_is_not_uniform_global_temperature(self):
        X=np.asarray([[0.,.1,.3,.6,3.,4.,10.,12.]])
        q=m.crowd_density_agent(X)
        self.assertGreater(float(np.max(q)-np.min(q)),.04)
        self.assertEqual(float(q[0,-1]),0.)

    def test_mass_nonnegativity_and_KS_same_law_without_crowd(self):
        r=m.pde_density_and_agent_check(
            [.4,.24,.14,.1,.05,.04,.03],strength=0,
            particles=3500,seed=44)
        self.assertTrue(r["nonnegative_density"])
        self.assertAlmostEqual(r["min_horse_probability_mass"],1.,places=9)
        self.assertAlmostEqual(r["max_horse_probability_mass"],1.,places=9)
        self.assertLess(r["max_KS_particle_to_PDE"],.055)
        self.assertTrue(r["PDE_conditions_on_fixed_logprior_drift_without_Gumbel"])

    def test_matched_nonlocal_particle_and_factorized_pde(self):
        r=m.pde_density_and_agent_check(
            [.32,.24,.18,.12,.07,.045,.025],
            strength=3.,particles=2500,seed=122)
        self.assertTrue(r["closure_is_not_exact_for_finite_correlated_horses"])
        self.assertTrue(r["nonnegative_density"])
        self.assertAlmostEqual(r["min_horse_probability_mass"],1,places=9)
        self.assertLess(r["max_KS_particle_to_PDE"],.105)
        self.assertEqual(r["particle_outside_grid_total_over_species"],0)

    def test_pde_rejects_unstable_CFL_and_bad_kernel(self):
        with self.assertRaisesRegex(ValueError,"UNSTABLE"):
            m.pde_density_and_agent_check(
                [.2]*6,dx=.1,dt=1.,particles=200)
        with self.assertRaisesRegex(ValueError,"NONPOSITIVE_KERNEL"):
            m.ahead_kernel([1,2],decay=0)

    def test_paired_voter_null_modes_do_not_react_to_horse_crowding(self):
        a=m.coupled_prestart(demo_row(),
                             [.35,.23,.16,.10,.065,.045,.03,.02],
                             distance_m=2000,draws=500,seed=84)
        for mode in ("independent","herding"):
            np.testing.assert_array_equal(
                a["by_crowd_and_vote"]["no_crowd"][mode]["market"],
                a["by_crowd_and_vote"]["nonlocal_crowd"][mode]["market"])
        for crowd in m.CROWD_SCENARIOS:
            for mode in m.VOTER_TYPES:
                p=a["by_crowd_and_vote"][crowd][mode]["prediction"]
                self.assertAlmostEqual(sum(p["win"]),1,places=10)
                self.assertAlmostEqual(sum(p["top3"]),3,places=10)
        self.assertTrue(a["no_official_outcome_read"])
        t=a["physical_to_market_transmission"]
        self.assertGreater(t["horse_win_distribution_shift_TV_pp"],0)
        self.assertTrue(t["null_information_voter_effect_identically_zero"])
        self.assertEqual(t["market_price_index_shift_TV_pp"]["independent"],0)
        self.assertEqual(t["market_price_index_shift_TV_pp"]["herding"],0)

    def test_frozen_horse_prior_does_not_depend_on_market_quote(self):
        row=demo_row()
        prior=[.2,.2,.18,.14,.12,.08,.05,.03]
        a=m.coupled_prestart(row,prior,distance_m=1400,draws=100,seed=21)
        altered={**row,"first_odds":{i:float(2*i+20)
                        for i in range(1,9)}}
        b=m.coupled_prestart(altered,prior,distance_m=1400,
                             draws=100,seed=21)
        for c in m.CROWD_SCENARIOS:
            np.testing.assert_array_equal(
                a["horse_scenario"]["scenarios"][c]["win"],
                b["horse_scenario"]["scenarios"][c]["win"])
        self.assertFalse(np.allclose(a["market_q0"],b["market_q0"]))
        # Later quote should be outcome-only, never a simulated information signal.
        other={**row,"last_odds":{i:float(7+i*2) for i in range(1,9)},
               "winner":7,"official_results_top3":[7,1,5]}
        d=m.coupled_prestart(other,prior,distance_m=1400,draws=100,seed=21)
        for c in m.CROWD_SCENARIOS:
            for mode in m.VOTER_TYPES:
                np.testing.assert_array_equal(
                    a["by_crowd_and_vote"][c][mode]["market"],
                    d["by_crowd_and_vote"][c][mode]["market"])


@unittest.skipUnless(np is not None and (ROOT/"data/2026-10-12/v3-normalized-prerace-history.json").exists(),
                     "Full historical source-locked checkout needed")
class RealArchiveTests(unittest.TestCase):
    def test_six_races_particle_pde_and_model_event_scores(self):
        z=m.archived_six_race_audit(draws=80,pde_particles=750,seed=20261025)
        self.assertEqual(z["official_races"],6)
        self.assertEqual(z["meeting_dates"],2)
        self.assertEqual(z["horse_race_entries"],84)
        self.assertAlmostEqual(
            z["baseline_observed_later_WIN_M0"]["win_log_loss"],
            1.696959293802405,places=9)
        self.assertTrue(z["same_kernel_and_diffusion_for_agent_and_PDE"])
        for arm in m.PRIOR_ARMS:
            d=z["nonlocal_particle_PDE_diagnostics"][arm]
            self.assertAlmostEqual(d["pde_mass_min"],1,places=8)
            self.assertAlmostEqual(d["pde_mass_max"],1,places=8)
            self.assertLess(d["max_KS_all_six"],.115)
            self.assertEqual(set(z["mean_race_equal_scores"][arm]),
                             set(m.CROWD_SCENARIOS))
            for crowd in m.CROWD_SCENARIOS:
                self.assertEqual(set(z["mean_race_equal_scores"][arm][crowd]),
                                 set(m.VOTER_TYPES))
        self.assertEqual(z["real_successful_forward_threshold_or_bet_EV"],"HOLD")
        self.assertTrue(z["no_result_used_for_mechanism_selection"])
        for arm in m.PRIOR_ARMS:
            t=z["physical_interaction_to_bettor_market_transmission"][arm]
            self.assertGreater(t["mean_horse_WIN_probability_TV_shift_pp"],0)
            self.assertEqual(t["voter_market_response_TV_pp"]["independent"],0)
            self.assertEqual(t["voter_market_response_TV_pp"]["herding"],0)


if __name__=="__main__":
    unittest.main()
