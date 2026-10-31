#!/usr/bin/env python3
"""Kyoto R8 (3 full quotes) vs Tenno (5 partial reports) model-free checks."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_kyotoR8_crossrace_quantized_rate_null as m
    import odds_r8_real_three_time_market as legacy


@unittest.skipIf(np is None, "NumPy required by original SHA-locked R8 parser")
class CrossRaceQuantizedTurningRateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if np is None:
            return
        cls.report=m.audit()

    def test_original_sha_locked_real_r8_source_horse_field_and_receipt(self):
        a=m.source_locked_r8_records(ROOT)
        self.assertEqual(len(a),3)
        self.assertEqual(
            [x["source_reported_jst"] for x in a],
            list(m.R8_EXPECTED_CLOCKS))
        self.assertTrue(all(len(x["prices"])==11 for x in a))
        self.assertTrue(all(x["original_11_horses_full_field"] for x in a))
        self.assertTrue(all(x["source_bytes_Git_blob_SHA_verified_by_original_module"]
                            for x in a))
        self.assertEqual(
            [[x["prices"][3],x["prices"][10],x["prices"][11]]
             for x in a],
            [[7.7,18.3,5.3],[6.7,16.8,4.9],[6.3,12.8,3.9]])

    def test_real_55_horse_pairs_nonmonotone_two_under_wide_rounding_union(self):
        q=self.report["archived_kyoto_R8"]["by_quantization_assumption"]
        self.assertEqual(
            [q[key]["strict_nonmonotone_pair_count"] for key in
             m.QUANTIZATION_SCHEMES],
            [3,3,2])
        self.assertEqual(
            q["nearest_tenth_hypothetical"]["nonmonotone_horse_pairs"],
            [[3,10],[3,11],[5,9]])
        self.assertEqual(
            q["truncate_tenth_hypothetical"]["nonmonotone_horse_pairs"],
            [[3,10],[3,11],[5,9]])
        self.assertEqual(
            q["union_of_both_conservative"]["nonmonotone_horse_pairs"],
            [[3,10],[3,11]])
        for d in q.values():
            self.assertEqual(d["reported_pair_count_dependent_within_one_race"],55)
            self.assertEqual(len(d["all_pairwise_interval_rate_and_monotonicity_results"]),55)
            self.assertTrue(d["all_admit_continuous_movement_with_sufficient_speed"])
            self.assertTrue(all(x["n_original_price_sample_points"]==3
                                for x in d["all_pairwise_interval_rate_and_monotonicity_results"]))

    def test_source_conditional_sharp_continuous_rate_frontier_not_tipping(self):
        q=self.report["archived_kyoto_R8"]["by_quantization_assumption"]
        expected=[2.066971569638208,2.0580773976512563,2.03199683310827]
        for (name,row),target in zip(q.items(),expected):
            self.assertAlmostEqual(
                row["largest_minimum_continuous_logratio_speed_per_reported_hour"],
                target,places=8,msg=name)
            self.assertEqual(row["pair_with_largest_required_continuous_rate"],
                             [6,8])
            self.assertEqual(row["pairwise_continuous_speed_caps_hypothetical_not_calibrated"]["3.0"],0)
            self.assertGreater(row["pairwise_continuous_speed_caps_hypothetical_not_calibrated"]["0.1"],0)
        q_union=q["union_of_both_conservative"]
        for record in q_union["all_pairwise_interval_rate_and_monotonicity_results"]:
            w=record["minimum_continuous_rate_witness"]
            self.assertTrue(w["piecewise_linear_continuous_interpolant_feasible"])
            self.assertTrue(w["smooth_movement_suffices_without_discontinuous_jump"])
            self.assertTrue(w["rate_is_not_true_tote_transaction_speed"])

    def test_parent_tenno_partial_shares_wider_rounding_method_not_new_market(self):
        q=self.report["editorial_tenno_top_five_only"]["by_quantization_assumption"]
        self.assertEqual([q[k]["strict_nonmonotone_pair_count"]
                          for k in m.QUANTIZATION_SCHEMES],[8,8,6])
        self.assertEqual(len(q["union_of_both_conservative"]["nonmonotone_horse_pairs"]),6)
        self.assertEqual(self.report["two_distinct_source_races_not_pooled_for_p_value"],2)
        self.assertEqual(self.report["R8_original_source_full_field_horse_count"],11)
        self.assertEqual(self.report["R8_original_source_full_field_price_points"],3)
        self.assertEqual(self.report["archived_kyoto_R8"]["sample_count"],[3]*11)
        self.assertEqual(self.report["editorial_tenno_top_five_only"]["sample_count"],
                         [5,5,5,5,4])

    def test_joint_11_horse_C2_smooth_price_and_normalized_M0_simplex(self):
        d=self.report["R8_joint_full_horse_continuous_C2_counterexample"]
        self.assertEqual(d["original_distinct_horses"],11)
        self.assertEqual(d["original_reported_knot_count"],3)
        self.assertLess(d["full_source_displayed_WIN_prices_exactly_interpolated_max_error"],
                        1e-10)
        self.assertTrue(d["same_joint_all_horses_C2_price_and_M0_simplex_path_exists"])
        self.assertTrue(d["no_discrete_jump_or_herding_necessarily_implied"])
        self.assertTrue(d["not_an_empirically_validated_smooth_stochastic_market_model"])
        for v in d["at_knots_price_indices_mass"]+d["at_segment_midpoints_price_indices_mass"]:
            self.assertAlmostEqual(v,1,places=12)

    def test_existing_seven_price_models_use_exact_same_R8_q2_target(self):
        r=self.report["R8_retrospective_PR36_same_one_target_7_model_crosscheck"]
        self.assertEqual(r["original_later_1344_WIN_target_count"],1)
        self.assertTrue(r["archived_original_target_known_before_model_code"])
        self.assertEqual(r["model_candidate_count"],7)
        self.assertEqual(
            r["price_rank_reversal_pairs_between_1326_and_1344"],7)
        self.assertAlmostEqual(
            r["actual_same_next_market_index_TV_pp"],
            9.656362948215287,places=9)
        self.assertAlmostEqual(
            r["persistence_target_price_index_TV_pp"],
            9.656362948215287,places=9)
        self.assertAlmostEqual(
            r["plain_log_momentum_target_price_index_TV_pp"],
            8.180965354937557,places=9)
        self.assertAlmostEqual(
            r["continuous_gain_target_price_index_TV_pp"],
            8.657104883763182,places=9)
        self.assertAlmostEqual(
            r["imposed_hard_price_gain_target_price_index_TV_pp"],
            r["plain_log_momentum_target_price_index_TV_pp"],places=12)
        self.assertTrue(r["nonmonotone_certificate_not_an_explanatory_variable_in_7_models"])
        self.assertFalse(r["model_succeeded_prospectively_or_found_true_criticality"])
        self.assertFalse(r["actual_JRA_race_result_or_bettor_stakes_read"])
        self.assertEqual(len(r["original_unchanged_all_seven_scores"]),7)

    def test_lipschitz_lower_bound_is_sharp_on_synthetic_forced_valley(self):
        t=["2026-10-31T10:00:00+09:00",
           "2026-10-31T11:00:00+09:00",
           "2026-10-31T12:00:00+09:00"]
        s=[{"source_reported_at_NOT_verified_provider_clock":dt,
            "lower":v,"upper":v} for dt,v in zip(t,[0,1,0])]
        w=m.minimum_continuous_logratio_rate(s)
        self.assertAlmostEqual(
            w["minimal_conditional_max_abs_logratio_speed_per_reported_hour"],
            1,places=12)
        self.assertTrue(w["piecewise_linear_continuous_interpolant_feasible"])
        self.assertTrue(w["smooth_movement_suffices_without_discontinuous_jump"])
        self.assertAlmostEqual(w["latent_values_constructively_feasible"][1],
                               1.,places=9)
        too_slow=.9
        self.assertGreater(
            w["minimal_conditional_max_abs_logratio_speed_per_reported_hour"],
            too_slow)

    def test_wrong_time_or_missing_runner_rejected_no_fabrication(self):
        a=m.source_locked_r8_records(ROOT)
        lost=copy.deepcopy(a)
        lost[1]["prices"].pop(11)
        with self.assertRaisesRegex(ValueError,"HOLD_JOINT_SMOOTH_INCOMPLETE_ROSTER"):
            m.full_field_C2_smooth_construct(lost)
        with patch.object(m,"collect_pre_race_price_panels",
                          side_effect=ValueError("HOLD_ARCHIVED_SOURCE_SHA_CHANGED")):
            with self.assertRaisesRegex(ValueError,"HOLD_ARCHIVED_SOURCE_SHA_CHANGED"):
                m.source_locked_r8_records(ROOT)

    def test_no_official_finish_label_loaded_even_if_import_available(self):
        with patch.object(legacy,"verify_official_oct12",
                          side_effect=AssertionError("HOLD_RESULT_LEAK")):
            result=m.audit(ROOT)
        self.assertFalse(result["original_JRA_race_outcome_or_betting_payout_read"])
        self.assertFalse(result["real_bettor_stakes_or_an_independent_GPS_horse_skill_used"])
        self.assertTrue(result["no_real_exogenous_news_or_herding_inferred_from_curvature"])
        self.assertEqual(result["independently_new_prospective_market_q2_trials"],0)
        self.assertTrue(result["PR37_original_eleven_models_and_sealed_v31_unchanged"])

    def test_report_is_reproducible_and_json_serializable_without_nan(self):
        self.assertEqual(self.report,m.audit())
        json.dumps(self.report,allow_nan=False,ensure_ascii=False)
        self.assertEqual(self.report["source_race_id"],m.R8_RACE_ID)


if __name__=="__main__":
    unittest.main()
