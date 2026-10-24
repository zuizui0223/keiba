#!/usr/bin/env python3
"""Coherent six-per-trio rank distributions from price-index layers only."""
import math
import sys
import unittest
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_coherent_hierarchy_rank_bridge import (
    STATUS, audit, joint_rank_probability,
)
from odds_threshold_forward_eval import order_probabilities


class CoherentMarketHierarchyRankingTests(unittest.TestCase):
    @staticmethod
    def sample(n=7):
        odds={i:float(1.2+i*2) for i in range(1,n+1)}
        node={i:0.0 for i in odds}
        pair={k:0.0 for k in combinations(odds,2)}
        return odds,node,pair

    def test_zero_betas_exactly_recover_pl_market_win_and_top3(self):
        odds,node,pair=self.sample(8)
        result=joint_rank_probability(odds,node,pair,
                                      beta_horse=0,beta_pair=0)
        pwin,ptop=order_probabilities([1/odds[i] for i in odds])
        for i,win,top in zip(odds,pwin,ptop):
            self.assertAlmostEqual(result["win"][i],win,places=12)
            self.assertAlmostEqual(result["top3"][i],top,places=12)
        self.assertEqual(result["n_ordered_rankings"],8*7*6)
        self.assertTrue(result["probabilities_properly_normalized_and_joint_rank_coherent"])

    def test_complete_coherent_marginal_masses_and_constraints(self):
        odds,node,pair=self.sample(8)
        node[1]=.8;node[2]=-.8
        pair[(1,2)]=.7;pair[(3,4)]=-.5
        r=joint_rank_probability(odds,node,pair,beta_horse=.8,beta_pair=.7)
        self.assertAlmostEqual(sum(r["win"].values()),1,places=10)
        self.assertAlmostEqual(sum(r["top2"].values()),2,places=10)
        self.assertAlmostEqual(sum(r["top3"].values()),3,places=10)
        self.assertAlmostEqual(sum(r["both_top3_pair"].values()),3,places=10)
        self.assertAlmostEqual(sum(r["unordered_top3_trio"].values()),1,places=10)
        self.assertAlmostEqual(sum(r["ordered_firsttwo_exacta"].values()),1,places=10)
        self.assertAlmostEqual(sum(r["ordered_top3_trifecta"].values()),1,places=10)
        self.assertEqual(len(r["ordered_top3_trifecta"]),8*7*6)
        for i in odds:
            self.assertAlmostEqual(
                r["top3"][i],
                sum(v for trio,v in r["unordered_top3_trio"].items()
                    if i in trio),places=10)
        for i,j in combinations(odds,2):
            self.assertAlmostEqual(
                r["both_top3_pair"][(i,j)],
                sum(v for trio,v in r["unordered_top3_trio"].items()
                    if i in trio and j in trio),places=10)
        for triple, p in r["unordered_top3_trio"].items():
            from itertools import permutations
            self.assertAlmostEqual(
                p,
                sum(r["ordered_top3_trifecta"][ordered] for ordered in permutations(triple)),
                places=10)
        for (a, b), p in r["ordered_firsttwo_exacta"].items():
            self.assertAlmostEqual(
                p,
                sum(prob for (i,j,k),prob in r["ordered_top3_trifecta"].items()
                    if i==a and j==b),
                places=10)
        for i in odds:
            self.assertAlmostEqual(
                sum(v for (first, second),v in r["ordered_firsttwo_exacta"].items()
                    if first == i),
                r["win"][i],places=10)
            self.assertAlmostEqual(
                sum(v for (first, second),v in r["ordered_firsttwo_exacta"].items()
                    if second == i),
                r["top2"][i] - r["win"][i],places=10)
        self.assertEqual(r["status"],STATUS)

    def test_coherent_node_boost_changes_horse_marginal(self):
        odds,node,pair=self.sample(8)
        odds={i:10.0 for i in odds}
        a=joint_rank_probability(odds,node,pair)
        node[1]=.8
        b=joint_rank_probability(odds,node,pair,beta_horse=1,beta_pair=0)
        self.assertGreater(b["top3"][1],a["top3"][1])
        self.assertGreater(b["win"][1],a["win"][1])
        self.assertAlmostEqual(sum(b["top3"].values()),3)

    def test_coherent_pair_boost_increases_joint_pair_event(self):
        odds,node,pair=self.sample(8)
        odds={i:10.0 for i in odds}
        a=joint_rank_probability(odds,node,pair)
        pair[(1,2)]=1
        b=joint_rank_probability(odds,node,pair,beta_pair=1)
        self.assertGreater(b["both_top3_pair"][(1,2)],
                           a["both_top3_pair"][(1,2)])
        self.assertAlmostEqual(sum(b["both_top3_pair"].values()),3)

    def test_uniform_additive_node_or_pair_shift_changes_nothing(self):
        odds,node,pair=self.sample(7)
        a=joint_rank_probability(odds,node,pair)
        node={i:2.0 for i in node}
        pair={k:-.8 for k in pair}
        b=joint_rank_probability(odds,node,pair,beta_horse=.9,beta_pair=1.2)
        for i in odds:
            self.assertAlmostEqual(a["win"][i],b["win"][i],places=12)
            self.assertAlmostEqual(a["top3"][i],b["top3"][i],places=12)

    def test_invalid_horse_roster_or_incomplete_pair_indices_rejected(self):
        odds,node,pair=self.sample(7)
        del pair[(1,2)]
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_ODDS_OR_HIERARCHICAL"):
            joint_rank_probability(odds,node,pair)
        pair={(a,b):0.0 for a,b in combinations(odds,2)}
        node[7]=float("nan")
        with self.assertRaisesRegex(ValueError,"HOLD_NONFINITE_HIERARCHY"):
            joint_rank_probability(odds,node,pair)
        node[7]=0.0
        with self.assertRaisesRegex(ValueError,"HOLD_UNBOUNDED_HYPOTHETICAL_BETA"):
            joint_rank_probability(odds,node,pair,beta_pair=999)

    def test_real_r8_market_baseline_and_hypothetical_coherent_scenarios(self):
        report=audit()
        self.assertEqual(report["status"],STATUS)
        self.assertEqual(report["only_independent_empirical_races"],1)
        self.assertAlmostEqual(
            report["observed_graph_price_index_horse_layer_fit_R2"],
            .7264335920434639,places=9)
        self.assertTrue(report["all_two_layer_coefficients_are_hypothetical_not_estimated"])
        self.assertEqual(report["formal_future_win_top3_forecast_skill"],
                         "HOLD_NO_PROSPECTIVE_HORSE_PANEL_AND_FREEZE")
        scenarios=report["scenarios"]
        base=scenarios["market_PL_exact"]
        self.assertEqual(base["chosen_coefficients"],{"horse":0.0,"pair":0.0})
        self.assertAlmostEqual(base["market_shift_in_win_probability_distribution_TV"],0,places=11)
        self.assertAlmostEqual(base["market_shift_in_top3_horse_marginals_TV"],0,places=11)
        self.assertAlmostEqual(base["market_shift_in_both_top3_pair_probabilities_TV"],0,places=11)
        for scenario in scenarios.values():
            self.assertEqual(scenario["top_win_price_rank_horse_number"],11)
            self.assertAlmostEqual(scenario["mass"]["one_first_place"],1,places=10)
            self.assertAlmostEqual(scenario["mass"]["two_first_two_places"],2,places=10)
            self.assertAlmostEqual(scenario["mass"]["three_top3_inclusions"],3,places=10)
            self.assertAlmostEqual(scenario["mass"]["three_successful_wide_pairs"],3,places=10)
            self.assertAlmostEqual(scenario["mass"]["one_unordered_trio"],1,places=10)
            self.assertAlmostEqual(scenario["mass"]["one_ordered_trifecta"],1,places=10)
        self.assertNotAlmostEqual(
            scenarios["hypothetical_two_layer"]["pair_3_11_both_top3_probability"],
            base["pair_3_11_both_top3_probability"],places=8)


if __name__=="__main__":
    unittest.main()
