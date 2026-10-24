#!/usr/bin/env python3
"""Tests for a *descriptive* complete-market win–wide pair hierarchy."""
import math
import sys
import unittest
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_pair_hierarchy_decomposition import (
    STATUS, audit, complete_graph_decompose,
    permutation_edge_label_reference,
)


class PairHierarchyDecompositionTests(unittest.TestCase):
    @staticmethod
    def pure_additive_fixture():
        node={1:-.30,2:.22,3:.10,4:.05,5:-.12,6:.05}
        return {pair:.33+node[pair[0]]+node[pair[1]]
                for pair in combinations(node,2)},node

    def test_exact_complete_graph_horse_additive_signal(self):
        pairs,true=self.pure_additive_fixture()
        r=complete_graph_decompose(pairs)
        self.assertEqual(r["status"],
                         "COMPLETE_GRAPH_HORSE_ADDITIVE_DESCRIPTIVE_DECOMPOSITION")
        self.assertEqual((r["n"],r["m"]),(6,15))
        self.assertAlmostEqual(r["intercept"],.33,places=12)
        self.assertAlmostEqual(
            r["explained_fraction_of_edge_change_variance"],1.0,places=12)
        self.assertAlmostEqual(
            r["leave_one_pair_out_relative_squared_error_reduction"],1.0,places=12)
        self.assertAlmostEqual(r["node_effects_sum_constraint"],0,places=12)
        self.assertAlmostEqual(
            r["max_abs_pair_model_residual_sum_per_horse"],0,places=12)
        for i,effect in true.items():
            self.assertAlmostEqual(r["node_effects"][i],effect,places=12)

    def test_pair_specific_deviation_remains_after_horse_terms(self):
        y,node=self.pure_additive_fixture()
        y[(1,2)]+=.8
        r=complete_graph_decompose(y)
        self.assertLess(
            r["explained_fraction_of_edge_change_variance"],1.0)
        self.assertGreater(
            r["pair_residual_fraction_of_edge_change_variance"],0.01)
        self.assertNotAlmostEqual(r["pair_model_residuals"][(1,2)],0)
        self.assertAlmostEqual(
            r["node_effects_sum_constraint"],0,places=12)
        self.assertLess(r["max_abs_pair_model_residual_sum_per_horse"],1e-12)

    def test_global_shift_changes_only_intercept_not_horse_or_pair_residual(self):
        y,node=self.pure_additive_fixture()
        y[(2,3)]-=.12
        z={k:v+4 for k,v in y.items()}
        r0,r1=complete_graph_decompose(y),complete_graph_decompose(z)
        self.assertAlmostEqual(r1["intercept"]-r0["intercept"],4,places=12)
        self.assertEqual(set(r1["pair_model_residuals"]),set(r0["pair_model_residuals"]))
        for edge in y:
            self.assertAlmostEqual(
                r1["pair_model_residuals"][edge],
                r0["pair_model_residuals"][edge],places=12)
        for horse in node:
            self.assertAlmostEqual(r1["node_effects"][horse],
                                   r0["node_effects"][horse],places=12)

    def test_race_label_permutation_cannot_change_graph_fit(self):
        y,node=self.pure_additive_fixture()
        y[(2,4)]+=.41
        rename={1:20,2:12,3:7,4:19,5:10,6:2}
        p={tuple(sorted(rename[i] for i in pair)):v for pair,v in y.items()}
        a,b=complete_graph_decompose(y),complete_graph_decompose(p)
        self.assertAlmostEqual(
            a["explained_fraction_of_edge_change_variance"],
            b["explained_fraction_of_edge_change_variance"],places=12)
        self.assertAlmostEqual(
            a["leave_one_pair_out_relative_squared_error_reduction"],
            b["leave_one_pair_out_relative_squared_error_reduction"],places=12)

    def test_bad_or_noncomplete_graph_refused(self):
        y,node=self.pure_additive_fixture()
        del y[(1,2)]
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_COMPLETE"):
            complete_graph_decompose(y)
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_UNORDERED_PAIR_KEY"):
            complete_graph_decompose({**y,(4,4):2})
        fresh,_=self.pure_additive_fixture()
        fresh[(1,2)]=float("nan")
        with self.assertRaisesRegex(ValueError,"HOLD_NONFINITE"):
            complete_graph_decompose(fresh)
        fresh,_=self.pure_additive_fixture()
        for k in fresh:fresh[k]=.5
        self.assertEqual(
            complete_graph_decompose(fresh)["status"],
            "HOLD_NO_EDGE_LEVEL_VARIANCE_TO_DECOMPOSE")

    def test_edge_permutation_reference_repeatable_and_not_formal_p_value(self):
        y,node=self.pure_additive_fixture()
        z=permutation_edge_label_reference(y,repetitions=199,seed=555)
        self.assertEqual(z,permutation_edge_label_reference(y,repetitions=199,seed=555))
        self.assertTrue(z["no_formal_statistical_significance_or_causal_identification"])
        self.assertTrue(z["exchangeability_of_edges_not_defensible_without_model"])
        self.assertEqual(z["repetitions"],199)
        self.assertLess(z["reference_mean_node_fit_fraction"],.8)
        self.assertLess(
            z["reference_quantiles_05_50_95"][2],1.0)
        with self.assertRaisesRegex(ValueError,"HOLD_TOO_FEW_PERMUTATION"):
            permutation_edge_label_reference(y,repetitions=10)

    def test_real_r8_55_pairs_73percent_node_fit_and_nonzero_3_11(self):
        r=audit(permutations=199,seed=20261023)
        self.assertEqual(r["status"],STATUS)
        self.assertEqual(r["number_of_real_independent_races"],2)
        a=r["selected_r8"]
        self.assertEqual((a["n_horses"],a["number_of_overlapping_wide_events"]),(11,55))
        self.assertTrue(a["full_bet_quote_pages_same_provider_and_reported_update_minute"])
        self.assertTrue(a["source_quote_update_minute_not_atomic_tote_transaction_time"])
        self.assertAlmostEqual(
            a["fraction_edge_change_variance_explained_by_additive_horse_terms"],
            .7264335920434639,places=9)
        self.assertAlmostEqual(
            a["selected_3_11_decomposition"]["raw_pair_change"],
            -.5427743236439119,places=9)
        self.assertAlmostEqual(
            a["selected_3_11_decomposition"]["remaining_pair_change"],
            -.32902423057925506,places=9)
        self.assertGreater(a["leave_one_pair_out_relative_squared_error_reduction"],.5)
        self.assertLess(a["leave_one_pair_out_relative_squared_error_reduction"],.7)
        self.assertLess(abs(a["numerical_invariants"]["node_effects_sum"]),1e-11)
        self.assertLess(
            a["numerical_invariants"]["largest_absolute_per_horse_sum_of_pair_residuals"],
            1e-10)
        self.assertEqual(
            a["largest_pair_specific_residuals_relative_to_additive_model"][0]["pair"],
            [6,10])
        self.assertEqual(a["scientific_gates"]["independent_edge_replicates"],
                         "HOLD_PAIRS_SHARE_HORSES")

    def test_real_shuka_136_overshadowed_by_provider_lag_warning(self):
        r=audit(permutations=199,seed=2)
        a,b=r["other_shuka_lower_provenance_comparisons"]
        self.assertEqual(a["n_horses"],17)
        self.assertEqual(a["number_of_overlapping_wide_events"],136)
        self.assertAlmostEqual(
            a["fraction_edge_change_variance_explained_by_additive_horse_terms"],
            .4913870655929783,places=9)
        self.assertAlmostEqual(
            b["fraction_edge_change_variance_explained_by_additive_horse_terms"],
            .7810090647607459,places=9)
        self.assertFalse(a["full_bet_quote_pages_same_provider_and_reported_update_minute"])
        self.assertFalse(b["full_bet_quote_pages_same_provider_and_reported_update_minute"])
        self.assertTrue(r["pair_sample_sizes_are_not_independent_replicates"])
        self.assertTrue(any("not future race result" in s.lower()
                            for s in r["claims_not_supported"]))
        self.assertEqual(
            r["selected_r8"]["permutation_reference"]["status"],
            "ASSUMPTION_HEAVY_FIXED_EDGE_LABEL_PERMUTATION_REFERENCE_NOT_P_VALUE")


if __name__=="__main__":
    unittest.main()
