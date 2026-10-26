"""Synthetic uncertainty-propagation tests; no real horse/odds data.

Dedicated CI installs NumPy and runs all tests; generic CI may
legitimately skip this optional scientific test module.
"""
from __future__ import annotations

from pathlib import Path
import math
import sys
import unittest

try:
    import numpy as np
except ModuleNotFoundError as exc:
    if exc.name != "numpy":
        raise
    np = None

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
if np is not None:
    from keiba_trait_uncertainty_ensemble import propagate_individual_uncertainty
    from keiba_individual_trait_market_demo import toy_data
    from keiba_individual_trait_to_market_cascade import (
        layered_vote_market, initial_market_proxy, objective_horse_prior,
        repeatable_traits,
    )


@unittest.skipIf(np is None, "NumPy scientific dependency is installed by dedicated workflow")
class TraitUncertaintySyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source,cls.target,cls.first=toy_data()

    def _run(self,**options):
        params={"posterior_draws":8,"physical_mc_draws":50,"seed":123}
        params.update(options)
        return propagate_individual_uncertainty(
            self.source,self.target,observed_first_odds=self.first,
            **params)

    def test_posterior_sampling_propagates_beyond_point_estimate(self):
        r=self._run()
        self.assertTrue(r["posterior_sampling_enabled"])
        self.assertTrue(r["trait_posterior_independence_ignores_shared_peer_denominator"])
        self.assertEqual(r["n_horses"],6)
        self.assertEqual(r["n_repeatable_horses"],6)
        self.assertEqual(r["posterior_draws"],8)
        self.assertGreater(r["scenario_market_difference_TV_pp"]["q95_across_scenario_draws"],0)
        self.assertGreater(max(r["prior_across_trait_sd"]),0)
        self.assertFalse(np.array_equal(
            r["plug_in_objective_prior"],r["expected_objective_prior_under_trait_error"]))
        for field in ("plug_in_objective_prior",
                      "expected_objective_prior_under_trait_error",
                      "expected_physical_win_signal_without_crowding",
                      "expected_physical_win_signal_with_crowding",
                      "expected_final_market_no_crowding",
                      "expected_final_market_with_crowding",
                      "initial_market_proxy"):
            with self.subTest(field=field):
                self.assertAlmostEqual(sum(r[field]),1.,places=10)
        self.assertFalse(r["has_outcome_data"])
        self.assertFalse(r["true_JRA_bettor_stakes"])

    def test_plug_in_posterior_collapses_draw_to_draw_trait_spread(self):
        r=self._run(include_posterior_error=False)
        self.assertFalse(r["posterior_sampling_enabled"])
        np.testing.assert_allclose(r["prior_across_trait_sd"],0,atol=1e-13)
        np.testing.assert_allclose(
            r["expected_objective_prior_under_trait_error"],
            r["plug_in_objective_prior"],atol=1e-13)
        self.assertAlmostEqual(r["scenario_market_difference_TV_pp"]
                                   ["sd_across_scenario_draws"],0,places=10)

    def test_public_information_absence_is_a_strict_negative_control(self):
        r=self._run(information_release_round=5)
        self.assertTrue(r["never_released_pairs_bitwise_identical"])
        self.assertAlmostEqual(r["market_TV_between_ensemble_mean_scenarios_pp"],0)
        self.assertEqual(r["scenario_market_difference_TV_pp"]["q95_across_scenario_draws"],0)
        self.assertGreater(r["scenario_physical_signal_TV_pp"]["mean"],0)

    def test_reproducibility_and_seed_sensitivity(self):
        a=self._run()
        b=self._run()
        self.assertEqual(a,b)
        c=propagate_individual_uncertainty(
            self.source,self.target,observed_first_odds=self.first,
            posterior_draws=8,physical_mc_draws=50,seed=124)
        self.assertNotEqual(a["expected_final_market_with_crowding"],
                            c["expected_final_market_with_crowding"])

    def test_initial_market_is_separate_from_horse_traits(self):
        a=self._run()
        odds_reversed=dict(zip(self.target["horse_ids"],
                               reversed(list(self.first.values()))))
        b=propagate_individual_uncertainty(
            self.source,self.target,observed_first_odds=odds_reversed,
            posterior_draws=8,physical_mc_draws=50,seed=123)
        self.assertEqual(a["expected_objective_prior_under_trait_error"],
                         b["expected_objective_prior_under_trait_error"])
        self.assertEqual(a["expected_physical_win_signal_with_crowding"],
                         b["expected_physical_win_signal_with_crowding"])
        self.assertNotEqual(a["initial_market_proxy"],b["initial_market_proxy"])

    def test_informed_agents_dont_double_count_initial_objective_prior(self):
        ids=self.target["horse_ids"]
        q=initial_market_proxy(dict(zip(ids,[2.,4.,5.,7.,9.,12.])),ids)
        trait=repeatable_traits(self.source,self.target)
        objective=objective_horse_prior(trait)
        only_info={"fundamental":0.,"herding":0.,"informed":1.}
        announced=layered_vote_market(
            q,objective,objective,voter_shares=only_info,
            release_step=1,seed=123,rounds=4)
        kept_private=layered_vote_market(
            q,objective,objective,voter_shares=only_info,
            release_step=5,seed=123,rounds=4)
        for x,y in zip(announced["path"],kept_private["path"]):
            np.testing.assert_array_equal(x,y)

    def test_partial_pde_uses_sampled_objective_prior(self):
        r=self._run(pde_particles=100,pde_draws=1)
        self.assertEqual(r["pde_diagnostic_ensemble_draws"],1)
        self.assertEqual(len(r["pde_diagnostics"]),1)
        self.assertGreaterEqual(r["scenario_physical_signal_TV_pp"]["mean"],0)

    def test_invalid_parameters_and_source_late_info_fail_closed(self):
        for opts in ({"posterior_draws":1},
                     {"posterior_draws":65},
                     {"physical_mc_draws":15},
                     {"pde_particles":100,"pde_draws":0},
                     {"pde_draws":4},
                     {"information_release_round":6},
                     {"include_posterior_error":0}):
            with self.subTest(opts=opts),self.assertRaises(ValueError):
                self._run(**opts)
        from copy import deepcopy
        r=deepcopy(self.source)
        r["records"][0]["received_at"]="2026-10-27T09:00:00+09:00"
        with self.assertRaises(ValueError):
            propagate_individual_uncertainty(
                r,self.target,observed_first_odds=self.first,
                posterior_draws=3,physical_mc_draws=40)


    def test_increasing_herding_layer_changes_theoretical_gain_not_critical_price(self):
        fractions=[
            {"fundamental":.60,"herding":.20,"informed":.20},
            {"fundamental":.45,"herding":.35,"informed":.20},
            {"fundamental":.25,"herding":.50,"informed":.25},
            {"fundamental":.15,"herding":.60,"informed":.25}
        ]
        r=self._run(voter_shares_by_round=fractions)
        self.assertTrue(r["voter_shares_time_schedule_used"])
        trace=r["uniform_equilibrium_gain_trace_not_real_criticality"]
        gains=[z["uniform_null_local_gain"] for z in trace]
        self.assertEqual(len(trace),4)
        self.assertEqual([z["herding_fraction_assumed"] for z in trace],
                         [.20,.35,.50,.60])
        self.assertTrue(all(0<g<1 for g in gains))
        self.assertGreater(gains[-1],gains[0])


    def test_source_matched_correlated_posterior_reaches_market_and_pde(self):
        r=self._run(posterior_covariance_mode="race_contrast_covariance",
                    pde_particles=100,pde_draws=1)
        self.assertTrue(r["conditional_race_contrast_covariance_used"])
        self.assertFalse(
            r["trait_posterior_independence_ignores_shared_peer_denominator"])
        self.assertTrue(r["posterior_sampling_enabled"])
        self.assertEqual(r["trait_posterior_covariance_mode"],
                         "race_contrast_covariance")
        cov=r["race_contrast_covariance_summary"]
        self.assertEqual(
            cov["shared_race_residual_covariance_model"],
            "orthogonal_n_minus_1_contrasts")
        self.assertGreater(
            cov["max_absolute_offdiagonal_effect_correlation"],0)
        self.assertGreater(cov["relative_trait_pair_variance_min"],0)
        self.assertEqual(r["pde_diagnostic_ensemble_draws"],1)
        self.assertFalse(
            r["variance_hyperparameter_estimation_uncertainty_included"])
        for k in ("expected_objective_prior_under_trait_error",
                  "expected_physical_win_signal_with_crowding",
                  "expected_final_market_with_crowding"):
            self.assertAlmostEqual(sum(r[k]),1,places=11)
        a=self._run(posterior_covariance_mode="race_contrast_covariance",
                    pde_particles=100,pde_draws=1)
        self.assertEqual(r,a)

    def test_independent_vs_joint_contrast_do_not_silently_mix_trait_models(self):
        a=self._run()
        b=self._run(posterior_covariance_mode="race_contrast_covariance")
        self.assertFalse(a["conditional_race_contrast_covariance_used"])
        self.assertIsNone(a["race_contrast_covariance_summary"])
        self.assertTrue(b["conditional_race_contrast_covariance_used"])
        self.assertNotEqual(
            a["expected_objective_prior_under_trait_error"],
            b["expected_objective_prior_under_trait_error"])
        # Both use the SAME initial market, which cannot modify the
        # horse prior and was already an aggregation of social opinions.
        self.assertEqual(a["initial_market_proxy"],b["initial_market_proxy"])
        self.assertEqual(a["n_horses"],b["n_horses"])

    def test_covariance_model_respects_no_news_and_posterior_mean_controls(self):
        outcome=self._run(posterior_covariance_mode="race_contrast_covariance",
                          information_release_round=5)
        self.assertTrue(outcome["never_released_pairs_bitwise_identical"])
        self.assertEqual(
            outcome["scenario_market_difference_TV_pp"]["mean"],0.0)
        noerror=self._run(
            posterior_covariance_mode="race_contrast_covariance",
            include_posterior_error=False)
        self.assertAlmostEqual(max(noerror["prior_across_trait_sd"]),0.0,
                               places=12)
        self.assertEqual(noerror["trait_posterior_covariance_mode"],
                         "race_contrast_covariance")

    def test_invalid_joint_mode_fails_closed_without_substituting_independent(self):
        with self.assertRaises(ValueError):
            self._run(posterior_covariance_mode="not_a_valid_posterior")


    def test_race_contrast_diagonal_control_isolates_cross_horse_covariance(self):
        diag=self._run(
            posterior_covariance_mode="race_contrast_marginal_independent")
        joint=self._run(
            posterior_covariance_mode="race_contrast_covariance")
        self.assertTrue(diag["conditional_race_contrast_likelihood_used"])
        self.assertTrue(joint["conditional_race_contrast_likelihood_used"])
        self.assertFalse(diag["conditional_race_contrast_covariance_used"])
        self.assertTrue(joint["conditional_race_contrast_covariance_used"])
        self.assertTrue(
            diag["trait_posterior_independence_ignores_shared_peer_denominator"])
        self.assertFalse(
            joint["trait_posterior_independence_ignores_shared_peer_denominator"])
        # Same *fitted* horse means, same fitted marginal uncertainties:
        # sampling distribution differs ONLY in its off-diagonal
        # covariance, not in pointwise horse ability or prior context.
        self.assertEqual(diag["plug_in_objective_prior"],
                         joint["plug_in_objective_prior"])
        self.assertEqual(
            diag["race_contrast_covariance_summary"],
            joint["race_contrast_covariance_summary"])
        self.assertNotEqual(
            diag["expected_objective_prior_under_trait_error"],
            joint["expected_objective_prior_under_trait_error"])
        self.assertEqual(diag["initial_market_proxy"],
                         joint["initial_market_proxy"])
        self.assertFalse(diag["has_outcome_data"])
        self.assertFalse(joint["has_outcome_data"])


    def test_source_reml_joint_horse_posterior_reaches_physical_and_bettors(self):
        x=self._run(posterior_covariance_mode="race_contrast_covariance",
                    source_variance_fit_mode="source_reml",
                    reml_profile_scenario="central",
                    pde_particles=100,pde_draws=1)
        self.assertEqual(x["source_variance_fit_mode"],"source_reml")
        self.assertTrue(x["conditional_race_contrast_covariance_used"])
        summary=x["race_contrast_covariance_summary"]
        self.assertTrue(summary["hyperparameters"]
                        ["source_only_orthogonal_race_contrast_reml"])
        self.assertFalse(summary["hyperparameters"]
                         ["hyperparameter_estimation_error_integrated"])
        self.assertEqual(x["reml_profile_scenario"],"central")
        self.assertGreater(summary["source_reml_profile_diagnostic"]
                           ["profile_improvement_vs_zero_horse_variance"],0)
        self.assertEqual(x["pde_diagnostic_ensemble_draws"],1)
        self.assertAlmostEqual(sum(x["expected_final_market_with_crowding"]),1)
        self.assertFalse(x["has_outcome_data"])

    def test_source_reml_profile_scenarios_are_sensitivity_not_CI(self):
        out={}
        for case in ("low","central","high"):
            out[case]=self._run(
                posterior_covariance_mode="race_contrast_covariance",
                source_variance_fit_mode="source_reml",
                reml_profile_scenario=case)
        ratios=[out[k]["race_contrast_covariance_summary"]["hyperparameters"]
                ["horse_between_variance_seconds2"]/
                out[k]["race_contrast_covariance_summary"]["hyperparameters"]
                ["assumed_absolute_time_residual_variance_seconds2"]
                for k in ("low","central","high")]
        self.assertLessEqual(ratios[0],ratios[1])
        self.assertLessEqual(ratios[1],ratios[2])
        self.assertFalse(out["central"]
                         ["variance_hyperparameter_estimation_uncertainty_included"])
        self.assertEqual(out["central"]["actual_market_predictive_superiority"],
                         "HOLD")
        self.assertNotEqual(
            out["low"]["plug_in_objective_prior"],
            out["high"]["plug_in_objective_prior"])

    def test_reml_same_marginals_diagonal_and_covariance_scenarios(self):
        diag=self._run(posterior_covariance_mode=
                       "race_contrast_marginal_independent",
                       source_variance_fit_mode="source_reml")
        joint=self._run(posterior_covariance_mode="race_contrast_covariance",
                        source_variance_fit_mode="source_reml")
        self.assertEqual(diag["plug_in_objective_prior"],
                         joint["plug_in_objective_prior"])
        self.assertEqual(diag["race_contrast_covariance_summary"],
                         joint["race_contrast_covariance_summary"])
        self.assertNotEqual(diag["expected_objective_prior_under_trait_error"],
                            joint["expected_objective_prior_under_trait_error"])

    def test_reml_keeps_early_market_and_no_information_counterfactual(self):
        x=self._run(posterior_covariance_mode="race_contrast_covariance",
                    source_variance_fit_mode="source_reml",
                    information_release_round=5)
        self.assertTrue(x["never_released_pairs_bitwise_identical"])
        self.assertAlmostEqual(
            x["scenario_market_difference_TV_pp"]["mean"],0.,places=12)
        with self.assertRaises(ValueError):
            self._run(source_variance_fit_mode="source_reml")
        with self.assertRaises(ValueError):
            self._run(
                posterior_covariance_mode="race_contrast_covariance",
                source_variance_fit_mode="source_reml",
                reml_profile_scenario="chosen_using_future_winner")


if __name__=="__main__":
    unittest.main()
