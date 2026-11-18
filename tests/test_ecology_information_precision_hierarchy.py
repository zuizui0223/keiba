"""Actual-source aggregate parity and analytic (NOT empirical) information model tests."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ecology_information_precision_hierarchy import (
    INPUTS, MODEL_TAG, MODEL_PARAMS, gaussian_information_value,
    conditional_gaussian_family_gain, extract_real_evidence, analytic_grid,
    _count, _finite_positive, main,
)


def toy(*, own=0, family=4, lag=30, loading=.4):
    p=MODEL_PARAMS
    return gaussian_information_value(
        n_own=own,n_family=family,kin_lag_days=lag,
        prior_var=p["prior_latent_variance"],
        own_noise_per_observation=p[
            "individual_measurement_noise_variance_per_observation"],
        family_noise_per_record=p[
            "family_proxy_measurement_noise_variance_per_record"],
        family_loading=loading,
        age_decay_scale_days=p["family_information_age_decay_scale_days"],
    )


class InformationPrecisionModelTests(unittest.TestCase):
    def test_family_information_decreases_with_more_own_history(self):
        x=[toy(own=n)["ideal_variance_improvement"] for n in (0,1,3,10,30)]
        self.assertTrue(all(a>b>0 for a,b in zip(x,x[1:])))
        self.assertGreater(x[0]/x[-1],10)

    def test_family_information_decreases_with_staleness(self):
        x=[toy(lag=age)["ideal_variance_improvement"] for age in (0,30,365,1460)]
        self.assertTrue(all(a>b>0 for a,b in zip(x,x[1:])))
        self.assertGreater(toy(lag=0)["family_proxy_precision"],
                           toy(lag=1460)["family_proxy_precision"])

    def test_family_record_count_makes_ideal_information_non_decreasing(self):
        x=[toy(family=n)["ideal_variance_improvement"] for n in (0,1,4,20)]
        self.assertEqual(x[0],0.0)
        self.assertTrue(all(a<b for a,b in zip(x,x[1:])))

    def test_zero_family_loading_is_no_genetic_effect_assertion(self):
        a=toy(own=3,loading=0)
        self.assertEqual(a["family_proxy_precision"],0.0)
        self.assertEqual(a["ideal_variance_improvement"],0.0)
        self.assertTrue(a["no_source_relatedness_A_or_genomic_G_assumed"])

    def test_mutual_information_has_exact_gaussian_formula(self):
        a=toy(own=1)
        self.assertAlmostEqual(a["ideal_conditional_information_nats"],
            0.5*math.log(
                a["latent_variance_with_own_only"] /
                a["latent_variance_with_own_plus_family_proxy"]))
        self.assertGreater(a["ideal_conditional_information_nats"],0)

    def test_invalid_noise_variances_and_negative_observation_counts_hold(self):
        with self.assertRaisesRegex(ValueError,"INFORMATION_COUNT"):
            toy(own=-1)
        with self.assertRaisesRegex(ValueError,"INFORMATION_COUNT"):
            toy(family=1.0)
        with self.assertRaisesRegex(ValueError,"NONPOSITIVE_OR_NONFINITE"):
            gaussian_information_value(
                n_own=1,n_family=1,kin_lag_days=0,prior_var=1,
                own_noise_per_observation=0,family_noise_per_record=1,
                family_loading=.4,age_decay_scale_days=365)
        with self.assertRaisesRegex(ValueError,"NONPOSITIVE_OR_NONFINITE"):
            toy(lag=-1)
        with self.assertRaisesRegex(ValueError,"NONFINITE_FAMILY_LOADING"):
            toy(loading=float("nan"))

    def test_correlated_gaussian_noise_has_zero_conditional_family_gain(self):
        # K = 0.5*O + independent measurement noise. K correlates with
        # theta, but has ZERO conditional information after observing O.
        a=conditional_gaussian_family_gain(
            prior_var=1,own_error_var=1,family_error_var=1,
            family_loading=.5,correlated_measurement_errors=.5)
        self.assertAlmostEqual(
            a["ideal_additional_family_variance_improvement"],0,places=14)
        self.assertTrue(a[
            "correlated_errors_may_represent_shared_context_NOT_genetic_proof"])

    def test_independent_correlated_gaussian_matches_precision_model(self):
        a=conditional_gaussian_family_gain(
            prior_var=1,own_error_var=1,family_error_var=1,
            family_loading=.5,correlated_measurement_errors=0)
        b=gaussian_information_value(
            n_own=1,n_family=1,kin_lag_days=0,
            prior_var=1,own_noise_per_observation=1,
            family_noise_per_record=1,family_loading=.5,
            age_decay_scale_days=365)
        self.assertAlmostEqual(
            a["ideal_additional_family_variance_improvement"],
            b["ideal_variance_improvement"],places=14)

    def test_illegal_noise_covariance_cannot_create_false_variance(self):
        with self.assertRaisesRegex(ValueError,"INVALID_CORRELATED_NOISE"):
            conditional_gaussian_family_gain(
                prior_var=1,own_error_var=1,family_error_var=1,
                family_loading=.5,correlated_measurement_errors=1.0)

    def test_analytic_grid_not_misnamed_actual_race_forecast(self):
        g=analytic_grid()
        self.assertEqual(g["status"],MODEL_TAG)
        self.assertEqual(len(g["Gaussian_conditional_precision_grid"]),15)
        self.assertTrue(g["dimensionless_no_horse_OR_market_data_fitted"])
        self.assertTrue(g["family_signal_loading_is_NOT_pedigree_A_or_genomic_G"])
        self.assertTrue(g["conditional_information_nats_is_NOT_observed_market_information_flow"])


class SourceLockedInformationEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observed=extract_real_evidence(ROOT)

    def test_real_2026_posthoc_fourway_dominant_own_history(self):
        o=self.observed["Japan_2026_one_selected_posthoc_cohort"]
        self.assertEqual(o["observed_starts"],480)
        self.assertEqual(o["observed_horses"],232)
        for label in ("ordinary","strong"):
            q=o["ordinary_and_strong_model_contrasts"][label]
            self.assertGreater(
                q["updated_focal_own_history_only_RMSE_gain_with_family_fixed"],
                q["updated_relative_history_only_RMSE_gain_with_own_fixed"])
            self.assertGreater(
                q["own_only_gain_to_family_only_gain_ratio_DESCRIPTIVE"],18)
        self.assertLess(o["ordinary_and_strong_model_contrasts"]["ordinary"][
            "full_updated_family_increment_over_updated_no_family_RMSE"],0)

    def test_kin_alone_update_is_not_guaranteed_useful_increment(self):
        o=self.observed["Japan_2026_one_selected_posthoc_cohort"]
        self.assertLess(o["same_sample_original_source_2026_kin_increment"],0)
        self.assertTrue(o["family_freshness_comparison_does_NOT_establish_kin_deployable_value"])
        self.assertTrue(o["subgroup_and_model_selection_already_inspected"])

    def test_strict_2024_baseline_failure_not_erased(self):
        o=self.observed["Japan_2022_2024_separate_period"]
        self.assertTrue(o["strict_2024_midpoint_better_than_family_RMSE"])
        self.assertAlmostEqual(o["strict_race_with_strong_own_history_family_increment_RMSE"],
                               .00026157978169816243,places=13)
        self.assertEqual(o["strict_race_with_strong_own_history_observed_starts"],244147)

    def test_parent_randomization_19_was_posthoc_not_p_less_than_005(self):
        o=self.observed["Japan_2022_2024_separate_period"]
        self.assertEqual(o["controls_exceeding_true_increment"],0)
        self.assertEqual(o["parent_shuffled_controls"],19)
        self.assertEqual(o["minimum_one_sided_plus_one_p_no_confirmatory_test"],.05)
        self.assertTrue(o["posthoc_reanalysis_same_period_not_independent_replication"])

    def test_market_real_nine_cross_section_not_actual_vote_herding(self):
        m=self.observed["market_real_cross_section_not_trajectory"]
        self.assertEqual((m["race_count"],m["horse_quotes"]),(9,117))
        self.assertGreater(m["max_field_normalized_effective_horses"],.7)
        self.assertLess(m["min_field_normalized_effective_horses"],.2)
        self.assertFalse(m["time_trajectory_measured"])
        self.assertFalse(m["actual_votes_or_market_social_contagion_identified"])

    def test_genome_G_not_id_joined_to_race_performance(self):
        g=self.observed["genomic_G_coverage"]
        self.assertEqual(g["anonymous_horses"],370)
        self.assertEqual(g["autosomal_QCed_SNPs"],353249)
        self.assertEqual(g["sample_pairs"],68265)
        self.assertFalse(g["same_registered_horse_linked_to_race_performance"])

    def test_status_tampering_does_not_promote_market_herding(self):
        import ecology_information_precision_hierarchy as module
        real=module._load_aggregate
        def altered(root,key):
            obj,sha=real(root,key)
            if key=="market":
                obj=copy.deepcopy(obj)
                obj["herding_time_evolution_observed"]=True
            return obj,sha
        with patch.object(module,"_load_aggregate",side_effect=altered):
            with self.assertRaisesRegex(ValueError,"FALSE_MEASURED_MARKET_FEEDBACK"):
                extract_real_evidence(ROOT)

    def test_status_tampering_does_not_promote_anonymous_DNA_join(self):
        import ecology_information_precision_hierarchy as module
        real=module._load_aggregate
        def altered(root,key):
            obj,sha=real(root,key)
            if key=="integrated":
                obj=copy.deepcopy(obj)
                obj["real_observations"]["Japan_genomic_G"][
                    "same_registered_horse_IDs_matched_to_racing_data"]=True
            return obj,sha
        with patch.object(module,"_load_aggregate",side_effect=altered):
            with self.assertRaisesRegex(ValueError,"JOINT_GENOTYPE_HORSE_ID"):
                extract_real_evidence(ROOT)

    def test_2026_horse_cohort_must_not_silently_expand(self):
        import ecology_information_precision_hierarchy as module
        real=module._load_aggregate
        def altered(root,key):
            obj,sha=real(root,key)
            if key=="factorial":
                obj=copy.deepcopy(obj)
                obj["combined_from_successful_aggregated_job_stdout"][
                    "same_2026_focals_and_dates"]=[500,233,260,42]
            return obj,sha
        with patch.object(module,"_load_aggregate",side_effect=altered):
            with self.assertRaisesRegex(ValueError,"EMPIRICAL_COHORT_DRIFT"):
                extract_real_evidence(ROOT)

    def test_cli_outputs_only_aggregates_toy_grid_and_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"information-model.json"
            with patch.object(sys,"argv",["module","--repo-root",str(ROOT),
                                          "--output",str(path)]):
                import contextlib,io
                with contextlib.redirect_stdout(io.StringIO()):
                    main()
            data=json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["status"],
                "OBSERVED_AGGREGATE_PARITY_PLUS_ANALYTIC_SYNTHETIC_INFORMATION_MODEL")
            self.assertTrue(data["scientific_interpretation"][
                "real_heritable_effect_or_MSTN_genotype_link_is_HOLD"])
            self.assertFalse(data["observational_evidence"][
                "market_real_cross_section_not_trajectory"]["time_trajectory_measured"])
            self.assertEqual(len(data["theoretical_counterfactual"][
                "Gaussian_conditional_precision_grid"]),15)
            self.assertTrue(data["scientific_interpretation"][
                "human_odds_ABM_and_horse_performance_are_separate_processes"])


if __name__ == "__main__":
    unittest.main()
