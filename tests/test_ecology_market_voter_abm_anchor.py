"""Separate real source and fictitious continuation for vote-feedback tests."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_market_voter_abm_anchor import one_batch,run_one,simulate

SNAP=Path(__file__).resolve().parents[1]/"data/2026-10-18/ticket-odds-snapshot.json"


class EcologicalMarketVoterABMTests(unittest.TestCase):
    def test_cumulative_pool_conserves_fictional_bets(self):
        q=[.6,.25,.15]
        before=[600,250,150]
        after=one_batch(q,before,1,None,None,seed=11,n=300)
        self.assertEqual(sum(after),1300)
        self.assertTrue(all(x>=y for x,y in zip(after,before)))
        self.assertEqual(before,[600,250,150])

    def test_stochastic_trajectory_reproducible_with_fixed_seed(self):
        p=[.5,.35,.15]
        a=run_one(p,"smooth_strong_following",seed=12,steps=8)
        b=run_one(p,"smooth_strong_following",seed=12,steps=8)
        self.assertEqual(a,b)
        self.assertEqual(a["simulated_final_pool"],3000)

    def test_threshold_uses_same_initial_observations_not_real_future_quotes(self):
        p=[.5,.35,.15]
        a=run_one(p,"threshold_following",seed=20,steps=8)
        b=run_one(p,"objective_only",seed=20,steps=8)
        self.assertEqual(a["simulated_final_pool"],b["simulated_final_pool"])
        self.assertTrue(a["effective_support_horses"]>0)
        self.assertNotEqual(a,b)

    def test_unknown_scenario_fails_and_pool_mass_validated(self):
        with self.assertRaisesRegex(ValueError,"SCENARIO"):
            run_one([.5,.3,.2],"genetic_causation",seed=0)
        with self.assertRaisesRegex(ValueError,"POOL"):
            one_batch([.5,.3,.2],[0,1,3],0,None,None,seed=1)

    def test_nine_REAL_input_markets_fictional_votes_not_empirical_herding(self):
        x=simulate(SNAP,repetitions=4)
        self.assertEqual(x["status"],
            "REAL_NINE_INITIAL_SUPPORT_STATES_SYNTHETIC_FUTURE_VOTER_ABM")
        self.assertEqual(x["observed_races"],9)
        self.assertEqual(x["observed_horse_price_rows"],117)
        self.assertEqual(len(x["market_regime_sensitivity"]),4)
        self.assertTrue(x["no_actual_odds_time_series_or_ticket_counts_observed"])
        self.assertTrue(x["no_genotype_or_pedigree_information_in_initial_market"])
        self.assertTrue(x["no_real_market_social_herding_or_critical_threshold_detected"])
        for r in x["market_regime_sensitivity"].values():
            self.assertEqual(r["fictional_trajectories"],36)
            self.assertEqual(r["fictional_final_tickets"],6000)
        self.assertNotIn("メイショウ",str(x))
        self.assertNotIn("horse_id",str(x))

    def test_neutral_feedback_not_a_real_critical_threshold_estimate(self):
        q=[.7,.2,.1]
        a=run_one(q,"proportional_following",seed=100,steps=10)
        b=run_one(q,"smooth_strong_following",seed=100,steps=10)
        self.assertGreater(a["effective_support_horses"],0)
        self.assertGreater(b["effective_support_horses"],0)


if __name__=="__main__":
    unittest.main()
