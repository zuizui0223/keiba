"""Nonlinear favorite–longshot negative control for observed ticket-market nodes."""
import math
import unittest

from scripts.ecology_ticket_market_temperature_null import (
    BETA_GRID, compare_models, nonlinear_curve, pl_wide_marginal, run_analysis,
)
from scripts.ticket_type_models import predict_tickets


def synthetic(n=9):
    strengths={i:1.0/(1.5 + i*i/8.) for i in range(1,n+1)}
    frames={i:min(i,8) for i in strengths}
    pl=predict_tickets(strengths,frames)
    weights={e: v/3 for e,v in pl["wide"].items()}
    curve=nonlinear_curve(strengths,pl["wide"])
    return strengths,frames,pl,weights,curve


class NonlinearFavoriteLongshotNullTests(unittest.TestCase):
    def test_temperature_one_matches_reference_PL_and_pair_mass(self):
        strengths,frames,pl,weights,curve=synthetic(9)
        beta_one=pl_wide_marginal(strengths,1.0)
        self.assertEqual(set(beta_one),set(pl["wide"]))
        self.assertAlmostEqual(sum(beta_one.values()),3,places=10)
        for e,p in pl["wide"].items():
            self.assertAlmostEqual(beta_one[e],p,places=11)
            self.assertAlmostEqual(curve[1.0][e],0.0,places=11)
        with self.assertRaises(ValueError):
            pl_wide_marginal(strengths,-1)

    def test_pure_global_temperature_signal_has_perfect_heldout_fit(self):
        _,_,_,weights,curve=synthetic(10)
        beta=1.35
        values={e:curve[beta][e]+0.23 for e in weights}
        stats=compare_models(values,weights,curve)
        self.assertAlmostEqual(stats["beta_in_sample"],beta)
        self.assertAlmostEqual(stats["temperature_in_sample_R2"],1.0,places=9)
        self.assertAlmostEqual(stats["temperature_heldout_edge_R2"],1.0,places=9)
        self.assertGreater(stats["temperature_heldout_edge_R2"],stats["node_heldout_edge_R2"])
        self.assertAlmostEqual(stats["temperature_plus_node_heldout_edge_R2"],1.0,places=8)
        self.assertFalse(stats["biological_individual_trait_identified"])

    def test_true_additive_horse_node_structure_beats_temperature_control(self):
        _,_,_,weights,curve=synthetic(9)
        node={i:math.sin(i*3.2)*0.6 for i in range(1,10)}
        values={(i,j):node[i]+node[j] for (i,j) in weights}
        stats=compare_models(values,weights,curve)
        self.assertAlmostEqual(stats["node_heldout_edge_R2"],1.0,places=9)
        self.assertLess(stats["temperature_heldout_edge_R2"],0.95)
        self.assertGreater(stats["node_vs_temperature_heldout_delta_R2"],0.05)

    def test_market_normalization_adds_constant_only_and_cannot_leak_loo(self):
        _,_,_,weights,curve=synthetic(9)
        values={e:curve[1.2][e]+0.02*((e[0]*17+e[1]*3)%7)
                for e in weights}
        original=compare_models(values,weights,curve)
        shifted=compare_models({e: v+8.20 for e,v in values.items()},
                               weights,curve)
        for key in (
            "node_heldout_edge_R2","temperature_heldout_edge_R2",
            "temperature_plus_node_heldout_edge_R2",
            "temperature_plus_node_vs_temperature_heldout_delta_R2",
            "node_vs_temperature_heldout_delta_R2",
        ):
            self.assertAlmostEqual(original[key],shifted[key],places=8)
        self.assertEqual(original["beta_in_sample"],shifted["beta_in_sample"])

    def test_wrong_graph_or_missing_pairs_fails_closed(self):
        _,_,_,weights,curve=synthetic(9)
        values={e:curve[1.25][e] for e in weights}
        with self.assertRaises(ValueError):
            compare_models(values,weights,{1.0:{}})
        with self.assertRaises(ValueError):
            compare_models(values,{k:v for k,v in weights.items() if k!=(1,2)},curve)
        with self.assertRaises(ValueError):
            nonlinear_curve({1:-1.0,2:1.0},{(1,2):.4})

    def test_real_nine_race_results_source_and_no_genetic_claim(self):
        out=run_analysis()
        self.assertEqual(out["status"],
                         "SAME_NINE_ARCHIVED_RACES_EXPLORATORY_NEGATIVE_CONTROL")
        self.assertEqual(len(out["races"]),9)
        self.assertEqual(out["groups"]["2026-10-12"]["race_count"],5)
        self.assertEqual(out["groups"]["2026-10-18"]["race_count"],4)
        self.assertFalse(out["strict_race_level_independent_validation"])
        self.assertFalse(out["outcome_labels_used"])
        self.assertFalse(out["voter_behavior_or_biological_interaction_identified"])
        self.assertFalse(out["same_horse_kinship_genome_join_available"])
        self.assertEqual(len(out["beta_grid"]),31)
        for r in out["races"]:
            self.assertEqual(r["complete_pair_count"],
                             r["runner_count"]*(r["runner_count"]-1)//2)
            self.assertTrue(0 <= r["node_in_sample_R2"] <= 1)
            self.assertTrue(0 <= r["temperature_in_sample_R2"] <= 1+1e-10)
            self.assertTrue(math.isfinite(r["node_heldout_edge_R2"]))
            self.assertTrue(math.isfinite(r["temperature_heldout_edge_R2"]))
            self.assertTrue(math.isfinite(r["temperature_plus_node_heldout_edge_R2"]))
            self.assertAlmostEqual(
                r["temperature_plus_node_vs_temperature_heldout_delta_R2"],
                r["temperature_plus_node_heldout_edge_R2"]-
                r["temperature_heldout_edge_R2"],places=10
            )
        self.assertGreaterEqual(len(out["input_file_sha256"]),30)


if __name__=="__main__":
    unittest.main()
