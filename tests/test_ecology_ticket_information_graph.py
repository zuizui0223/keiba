"""Synthetic graph nulls and real nine-race research-only structural diagnostics."""
import math
import unittest

from scripts.ecology_ticket_information_graph import (
    decompose_edges, graph_inputs, joint_transferred_logloss,
    permutation_reference, run_analysis,
)
from scripts.ticket_type_models import predict_tickets


def make_complete_graph(n=9):
    nodes = range(1, n + 1)
    return {(i, j): 1.0 for i in nodes for j in nodes if i < j}


class MarketInformationGraphTests(unittest.TestCase):
    def test_additive_node_signal_uses_no_pair_remainder(self):
        weights = make_complete_graph(9)
        node = {i: (-.25 + i / 10) for i in range(1,10)}
        data = {(i, j): node[i] + node[j] for i,j in weights}
        fitted = decompose_edges(data, weights)
        self.assertAlmostEqual(fitted["R2_node_vs_constant"], 1.0, places=11)
        self.assertLess(fitted["weighted_residual_rms"],1e-12)
        self.assertLess(max(abs(v) for v in fitted["dyadic_residual"].values()),1e-12)
        self.assertLess(max(abs(v) for v in fitted["residual_weighted_sum_orthogonality"].values()),1e-12)

    def test_pair_specific_signal_remains_after_node_projection(self):
        w = make_complete_graph(9)
        y = {e: 0.01*(e[0]+e[1]) + (4 if e == (1,2) else 0) for e in w}
        r = decompose_edges(y, w)
        self.assertTrue(0 < r["R2_node_vs_constant"] < 1)
        self.assertGreater(abs(r["dyadic_residual"][(1,2)]), 0.01)
        self.assertLess(max(abs(v) for v in r["residual_weighted_sum_orthogonality"].values()),1e-10)

    def test_nonuniform_real_pair_weights_and_edge_permutation(self):
        w = make_complete_graph(9)
        y = {e: (0.1*e[0]**2 + 0.3*e[1]) for e in w}
        weight = {e: 0.02 + 1/(e[0]+e[1]) for e in w}
        p = permutation_reference(y,weight,seed=2019,n_perm=49)
        self.assertEqual(p["status"],"DESCRIPTIVE_EDGE_LABEL_PERMUTATION_NOT_A_VOTER_NULL")
        self.assertEqual(p["repetitions"],49)
        self.assertIsNone(p["inferential_p_value"])
        self.assertGreaterEqual(p["actual_node_R2"],0)
        self.assertLessEqual(p["actual_node_R2"],1)
        self.assertGreaterEqual(p["shuffled_q95_node_R2"],p["shuffled_q05_node_R2"])
        with self.assertRaises(ValueError):
            permutation_reference(y,weight,seed=2,n_perm=2)

    def test_joint_order_likelihood_exact_and_zero_edge_correction(self):
        strengths = {i:1/(2+i) for i in range(1,10)}
        frames = {i: min(i,8) for i in strengths}
        base = predict_tickets(strengths,frames)
        residuals = {edge:0. for edge in base["wide"]}
        actual = [1,2,3]
        expected = -math.log(base["trifecta"][tuple(actual)])
        self.assertAlmostEqual(
            joint_transferred_logloss(base,frames,residuals,actual),expected,places=10
        )
        residuals[(1,2)] = 1.5
        self.assertLess(joint_transferred_logloss(base,frames,residuals,actual),expected)
        with self.assertRaises(ValueError):
            joint_transferred_logloss(base,frames,{},actual)
        with self.assertRaises(ValueError):
            joint_transferred_logloss(base,frames,residuals,[99,2,3])

    def test_no_quote_imputation_and_complete_market_graph(self):
        strengths = {i:1/(4+i) for i in range(1,10)}
        frames={i:min(i,8) for i in strengths}
        quotes=[
            {"selection":[i,j],"odds_low":10+i+j,"odds_high":11+i+j}
            for i in strengths for j in strengths if i<j
        ]
        residual, w, base = graph_inputs(strengths,frames,quotes)
        self.assertEqual(len(residual),36)
        self.assertAlmostEqual(sum(w.values()),1.0,places=10)
        self.assertEqual(len(base["trifecta"]),504)
        with self.assertRaises(ValueError):
            graph_inputs(strengths,frames,quotes[:-1])

    def test_real_nine_race_decomposition_separated_from_kin_and_prospective(self):
        data=run_analysis()
        self.assertEqual(len(data["races"]),9)
        self.assertEqual(data["by_date"]["2026-10-12"]["race_count"],5)
        self.assertEqual(data["by_date"]["2026-10-18"]["race_count"],4)
        self.assertFalse(data["prospective_validation"])
        self.assertFalse(data["real_market_time_series_observed"])
        self.assertFalse(data["genealogical_horse_id_join_identified"])
        self.assertFalse(data["information_theory_mutual_information_estimated"])
        for race in data["races"]:
            self.assertEqual(race["pair_count"],race["horse_count"]*(race["horse_count"]-1)//2)
            self.assertTrue(0<=race["weighted_node_explained_fraction_R2"]<=1)
            self.assertLess(race["max_abs_node_orthogonality_error"],1e-9)
            self.assertTrue(all(math.isfinite(z) for z in race["retrospective_correct_order_log_losses"].values()))
            self.assertAlmostEqual(
                race["delta_loss_full_vs_PL"],
                race["delta_loss_node_vs_PL"]+race["delta_loss_pair_added_to_node"],
                places=10
            )
        self.assertGreaterEqual(len(data["source_file_sha256"]),30)


if __name__=="__main__":
    unittest.main()
