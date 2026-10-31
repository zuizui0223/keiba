#!/usr/bin/env python3
"""Quantization V-turn tests and non-identification controls for PR38 sources."""
from __future__ import annotations

import copy
import math
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
    import keiba_tenno_quantized_nonmonotone_identification as m


@unittest.skipIf(np is None,"Parent Tenno modules need NumPy for linked model")
class QuantizedPriceNonmonotonicityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if np is None:
            return
        cls.original,cls.sha=m._blog_reported_quotes()
        cls.report=m.audit()

    def test_no_new_original_quote_or_full_field_source(self):
        a=self.report
        self.assertEqual(a["original_PR38_blog_declared_SHA_not_receipt"],
                         m.PINNED_BLOG_DECLARED_PARTIAL_SHA256)
        self.assertEqual(a["five_reported_partial_timepoints_not_tote_transaction_times"],5)
        self.assertEqual(a["distinct_reported_horse_ids"],[1,3,7,11,17])
        self.assertEqual(a["ten_originally_reported_horse_pairs_not_independent_trials"],10)
        self.assertFalse(a["actual_bettor_volume_or_independently_time_attested_JRA_source"])
        self.assertFalse(a["original_race_outcome_or_wager_payout_used"])
        self.assertEqual(a["new_remote_SHA_verified_prospective_trials"],0)
        self.assertTrue(a["original_PR37_eleven_models_and_sealed_v31_unchanged"])

    def test_correct_exact_bounds_for_nearest_truncate_union(self):
        expected={
            "nearest_tenth_hypothetical":(0.04000533461369942,
                                         0.12014431184206321),
            "truncate_tenth_hypothetical":(0.03922071315328133,
                                          0.11778303565638346),
            "union_of_both_conservative":(0.01980262729617973,
                                          0.13883644485421576),
        }
        for scheme,(lo,hi) in expected.items():
            with self.subTest(scheme=scheme):
                v=m._pair_log_bounds(2.6,2.4,scheme)
                self.assertAlmostEqual(v["lower"],lo,places=10)
                self.assertAlmostEqual(v["upper"],hi,places=10)
                self.assertGreater(v["displayed_center"],v["lower"])
                self.assertLess(v["displayed_center"],v["upper"])

    def test_nonmonotonicity_robust_horse_pair_counts_and_missing_17(self):
        expected={
            "nearest_tenth_hypothetical":8,
            "truncate_tenth_hypothetical":8,
            "union_of_both_conservative":6,
        }
        for label,n in expected.items():
            q=self.report["quantization_sensitivity"][label]
            self.assertEqual(q["n_tested_pairs_not_independent_races"],10)
            self.assertEqual(q["count_pairs_necessarily_nonmonotone"],n)
            self.assertEqual(len(q["all_pairwise_interval_feasibility_results"]),10)
            for d in q["all_pairwise_interval_feasibility_results"]:
                self.assertEqual(d["source_horse_observation_count"],
                                 4 if 17 in d["pair"] else 5)
                self.assertEqual(d["strict_global_nonmonotonicity_mathematically_required"],
                    not(d["nondecreasing_latent_path_feasible"] or
                        d["nonincreasing_latent_path_feasible"]))
                self.assertTrue(d["market_nonmonotonicity_does_not_identify_social_feedback"])

    def test_horse_one_and_seven_necessary_valley_under_three_display_schemes(self):
        q=self.report["strict_v_shape_witness_horses_1_and_7"]
        expected={
            "nearest_tenth_hypothetical":(0.1512309697239239,
                                         0.03846628082779642),
            "truncate_tenth_hypothetical":(0.14842000511827322,
                                          0.03774028790736027),
            "union_of_both_conservative":(0.11161029027887775,
                                          0.00165667689886549),
        }
        for label,(down,up) in expected.items():
            with self.subTest(label=label):
                a=q[label]
                self.assertEqual(a["reported_times"],["08:09","12:07","13:08"])
                self.assertAlmostEqual(a["minimum_guaranteed_decline_logratio"],
                                       down,places=9)
                self.assertAlmostEqual(a["minimum_guaranteed_rebound_logratio"],
                                       up,places=9)
                self.assertAlmostEqual(
                    a["minimum_two_interval_total_logratio_variation"],
                    down+up,places=9)
                self.assertAlmostEqual(
                    a["min_necessary_decline_logratio_per_reported_hour_conditional"],
                    down/(238/60),places=9)
                self.assertAlmostEqual(
                    a["min_necessary_rebound_logratio_per_reported_hour_conditional"],
                    up/(61/60),places=9)
                self.assertTrue(a["no_intrainterval_behavior_observed"])

    def test_three_mechanisms_all_fit_same_center_without_identifying_phi(self):
        d=self.report[
            "three_observationally_equivalent_mechanism_constructions"]
        self.assertTrue(d["all_three_structures_fit_at_observation_points_not_model_comparison"])
        self.assertEqual(d["n_actual_displayed_points_not_independent_races"],5)
        self.assertTrue(d["observational_equivalence_without_restrictions_on_innovations"])
        self.assertLessEqual(d["smooth_time_varying_drift_C2_interpolant"][
            "max_error_at_editorial_points"],1e-12)
        self.assertEqual(d["discrete_exogenous_step_construction"][
            "max_error_at_editorial_points"],0)
        self.assertEqual(set(d["feedback_AR1_with_unrestricted_exogenous_innovations"]),
                         {"0","0.5","0.9"} if "0" in d["feedback_AR1_with_unrestricted_exogenous_innovations"] else {"0.0","0.5","0.9"})
        for p in d["feedback_AR1_with_unrestricted_exogenous_innovations"].values():
            self.assertLessEqual(p["max_error_at_editorial_points"],1e-12)
            self.assertTrue(p["feedback_parameter_is_ARBITRARY_not_calibrated"])

    def test_strict_monotone_feasibility_rejects_only_constant_direction(self):
        rows=self.report["quantization_sensitivity"][
            "union_of_both_conservative"]["all_pairwise_interval_feasibility_results"]
        d=next(x for x in rows if x["pair"]==[1,7])
        self.assertFalse(d["nondecreasing_latent_path_feasible"])
        self.assertFalse(d["nonincreasing_latent_path_feasible"])
        self.assertTrue(d["strict_global_nonmonotonicity_mathematically_required"])
        self.assertTrue(d["consecutive_strict_valley_witnesses"])
        self.assertTrue(self.report[
            "strict_monotone_drift_rejected_but_smooth_nonmonotone_possible"])
        self.assertTrue(self.report[
            "external_news_event_and_bettor_feedback_not_separated"])

    def test_future_result_or_future_market_import_not_allowed(self):
        with patch.object(m,"_blog_reported_quotes",
                          side_effect=ValueError("HOLD_SOURCED_BLOG_BAD")):
            with self.assertRaisesRegex(ValueError,"HOLD_SOURCED_BLOG_BAD"):
                m.audit()
        with self.assertRaisesRegex(ValueError,"HOLD_UNSUPPORTED_QUANTIZATION"):
            m._pair_log_bounds(2.5,2.9,"invalid")
        with self.assertRaisesRegex(ValueError,"HOLD_UNSUPPORTED_QUANTIZATION"):
            m._pair_log_bounds(float("nan"),2.9,
                               "nearest_tenth_hypothetical")
        bad=copy.deepcopy(self.original)
        bad[1]["source_reported_jst"]=bad[0]["source_reported_jst"]
        with self.assertRaisesRegex(ValueError,
                                    "HOLD_EDITORIAL_SOURCE_TIME_ORDER_CHANGED"):
            m._pair_samples(bad,1,7,"nearest_tenth_hypothetical")

    def test_smooth_fit_quintic_is_c2_at_knots(self):
        x=[0.0,1.0,3.0]
        v=[.2,-.3,.4]
        for t,expected in zip(x,v):
            self.assertAlmostEqual(m._smooth_value(x,v,t),expected,places=12)
        self.assertAlmostEqual(m._smooth_value(x,v,.5),
                               -.05,places=12)
        eps=1e-4
        left=(m._smooth_value(x,v,1.0)-m._smooth_value(x,v,1.0-eps))/eps
        right=(m._smooth_value(x,v,1.0+eps)-m._smooth_value(x,v,1.0))/eps
        self.assertLess(abs(left),1e-6)
        self.assertLess(abs(right),1e-6)


if __name__=="__main__":
    unittest.main()
