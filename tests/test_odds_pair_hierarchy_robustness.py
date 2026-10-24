#!/usr/bin/env python3
"""Full-source sensitivity of pair hierarchy to quoted WIDE ranges and PL gamma."""
import copy
from itertools import combinations
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_pair_hierarchy_robustness import (
    STATUS, GAMMAS, QUOTE_MAPPINGS,
    audit, quote_mode, _to_full_pair_prices, synthetic_node_pair_noise,
    _time_panel_from_immutable_sources,
)
from odds_cross_pool_global_async import relative_pair_indices
from odds_pair_hierarchy_decomposition import complete_graph_decompose


class PairRobustnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x=audit(synthetic_draws=200,seed=20261023)

    def test_actual_full_archived_conditional_WIDE_ranges_present(self):
        earlier,later,before,after=_time_panel_from_immutable_sources()
        self.assertEqual(set(earlier),set(later))
        self.assertEqual(set(earlier),set(range(1,12)))
        self.assertEqual(len(before),55)
        self.assertEqual(len(after),55)
        self.assertTrue(all(
            q["odds_low"]<=q["odds_high"] for q in before+after))

    def test_wide_upper_is_conditional_payout_not_measurement_error(self):
        row={"selection":[3,11],"odds_low":2.5,"odds_high":2.7}
        self.assertEqual(quote_mode(row,mode="lower"),2.5)
        self.assertEqual(quote_mode(row,mode="upper"),2.7)
        self.assertAlmostEqual(
            quote_mode(row,mode="geometric"),math.sqrt(2.5*2.7),places=10)
        with self.assertRaisesRegex(ValueError,"HOLD_UNRECOGNIZED"):
            quote_mode(row,mode="median")
        with self.assertRaisesRegex(ValueError,"HOLD_BAD_WIDE_QUOTE_RANGE"):
            quote_mode({"odds_low":4.1,"odds_high":2.3},mode="upper")

    def test_missing_or_duplicate_WIDE_pair_fails_closed(self):
        _,_,source,_=_time_panel_from_immutable_sources()
        self.assertEqual(len(_to_full_pair_prices(source,11,"lower")),55)
        broken=copy.deepcopy(source)
        broken.pop()
        with self.assertRaisesRegex(ValueError,"HOLD_INCOMPLETE_ALL_WIDE"):
            _to_full_pair_prices(broken,11,"lower")
        broken=copy.deepcopy(source)
        broken.append(copy.deepcopy(source[0]))
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_WIDE"):
            _to_full_pair_prices(broken,11,"lower")

    def test_baseline_three_component_fits_match_prior_frozen_result(self):
        report=self.x
        self.assertEqual(report["status"],STATUS)
        self.assertEqual(report["number_of_independent_races"],1)
        self.assertEqual(report["n_price_mapping_scenarios"],9)
        ref=report["direct_PL_gamma1_lower_quote_decompositions"]
        self.assertAlmostEqual(ref["wide_raw_only"],.5824157332724196,places=9)
        self.assertAlmostEqual(ref["PL_model_pair_index_only"],
                               .9998856979637192,places=9)
        self.assertAlmostEqual(ref["wide_minus_PL_relative_index"],
                               .7264335920434639,places=9)
        self.assertTrue(
            report["wide_lower_upper_are_conditioned_payout_bounds_not_measurement_uncertainty"])
        self.assertTrue(report["geometric_mapping_is_not_observable_actual_wide_payout"])

    def test_9_scenarios_exhibit_large_R2_assumption_sensitivity(self):
        r=self.x
        self.assertEqual(set(GAMMAS),{.75,1.0,1.25})
        self.assertEqual(set(QUOTE_MAPPINGS),{"lower","upper","geometric"})
        self.assertAlmostEqual(
            r["wide_minus_PL_horse_node_R2_min"],.5554154393806627,places=9)
        self.assertAlmostEqual(
            r["wide_minus_PL_horse_node_R2_max"],.8137343323755677,places=9)
        self.assertLess(r["wide_minus_PL_leave_edge_out_R2_min"],.4)
        self.assertGreater(r["wide_minus_PL_leave_edge_out_R2_max"],.7)
        self.assertTrue(all(row["n_overlapping_pairs"]==55
                            for row in r["scenarios"]))

    def test_selected_pair_residual_sign_survives_but_size_varies(self):
        z=self.x["pair_residual_sign_stability"]
        for key in ("3-11","6-10"):
            self.assertTrue(z[key]["all_nine_assumptions_have_same_sign"])
        self.assertLess(z["3-11"]["maximum_signed_log_pair_residual"],0)
        self.assertGreater(z["6-10"]["minimum_signed_log_pair_residual"],0)
        self.assertLess(z["3-11"]["minimum_signed_log_pair_residual"],-.35)
        self.assertGreater(z["6-10"]["maximum_signed_log_pair_residual"],.41)

    def test_market_node_vs_pair_index_fit_is_mathematical_not_predictive(self):
        baseline=next(
            r for r in self.x["scenarios"]
            if r["PL_gamma_hypothetical"]==1.0 and
               r["wide_quote_range_mapping_counterfactual"]=="lower")
        for component in (
            "wide_raw_only","PL_model_pair_index_only",
            "wide_minus_PL_relative_index"):
            self.assertTrue(
                baseline[component]["horse_node_associated_terms_are_not_bettor_information"])
            self.assertLessEqual(
                baseline[component]["horse_node_explained_fraction_of_pair_change_variance"],1)
        self.assertTrue(any("No forward independent race result" in x
                            for x in self.x["inference_limits"]))

    def test_synthetic_independent_edges_differ_from_shared_horse_shocks(self):
        a=self.x["invented_noise_reference"]
        b=synthetic_node_pair_noise(draws=200,seed=20261023)
        self.assertEqual(a,b)
        self.assertTrue(a["cannot_interpret_as_pvalue_or_empirical_noise_baseline"])
        independent=a["results"]["independent_edge_shocks"]["mean_horse_node_R2"]
        shared=a["results"]["shared_horse_shocks_plus_edges"]["mean_horse_node_R2"]
        self.assertLess(independent,.35)
        self.assertGreater(shared,.55)
        self.assertGreater(shared,independent+.2)

    def test_invalid_noise_parameters_fail(self):
        with self.assertRaises(ValueError):
            synthetic_node_pair_noise(draws=50)
        with self.assertRaises(ValueError):
            synthetic_node_pair_noise(node_sd=-1)
        with self.assertRaises(ValueError):
            synthetic_node_pair_noise(edge_sd=0)


if __name__=="__main__":
    unittest.main()
