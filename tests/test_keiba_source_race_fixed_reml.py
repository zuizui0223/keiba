"""Synthetic-only REML method tests: Gaussian race contrasts, no outcomes/odds."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys
import unittest
try:
    import numpy as np
except ModuleNotFoundError as err:
    if err.name!="numpy":
        raise
    np=None
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
if np is not None:
    from keiba_source_race_fixed_reml import (
        _helmert,estimate_race_fixed_reml,leave_one_source_date_out_reml,
        REML_STATUS
    )
    from keiba_individual_trait_market_demo import toy_data
    from keiba_race_contrast_trait_posterior import fit_race_contrast_posterior


@unittest.skipIf(np is None,"Dedicated optional NumPy workflow executes numerical test")
class RaceFixedREMlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source,cls.target,_ = toy_data()

    def test_helmert_orthonormality_and_one_mean_eliminated(self):
        for n in (4,5,6,18,30):
            Q=_helmert(n)
            np.testing.assert_allclose(Q@Q.T,np.eye(n-1),atol=1e-14)
            np.testing.assert_allclose(Q@np.ones(n),0,atol=1e-14)
        with self.assertRaises(ValueError):
            _helmert(3)

    def test_fit_from_original_absolute_times_estimates_positive_variance(self):
        result=estimate_race_fixed_reml(self.source,self.target)
        self.assertEqual(result["status"],REML_STATUS)
        self.assertEqual(result["source_summary"]["source_races"],7)
        self.assertEqual(result["source_summary"]["source_horse_count"],6)
        self.assertEqual(result["n_independent_contrast_dimensions"],35)
        self.assertEqual(result["horse_contrast_rank"],5)
        self.assertGreater(result["horse_effect_variance_seconds_squared"],0)
        self.assertGreater(result["independent_absolute_time_error_variance_seconds_squared"],0)
        self.assertGreater(result["conditional_icc_point"],0)
        self.assertLess(result["conditional_icc_point"],1)
        self.assertGreater(result["profile_improvement_vs_zero_horse_variance"],0)
        self.assertEqual(
            [x["label"] for x in result["sensitivity_scenarios"]],
            ["low","central","high"])
        self.assertLessEqual(result["sensitivity_scenarios"][0]["variance_ratio"],
                             result["variance_ratio"])
        self.assertLessEqual(result["variance_ratio"],
                             result["sensitivity_scenarios"][-1]["variance_ratio"])
        self.assertFalse(result["covariance_assumptions"]["population_CI_or_Bayesian_posterior"])
        self.assertFalse(result["covariance_assumptions"]["learned_from_target_race_outcome_or_odds"])

    def test_additive_race_day_shift_does_not_change_reml(self):
        a=estimate_race_fixed_reml(self.source,self.target)
        b=deepcopy(self.source)
        for record in b["records"]:
            d=int(record["race_id"].split("R")[1])
            record["first_section_seconds"]+=5+.13*d
        actual=estimate_race_fixed_reml(b,self.target)
        for field in ("horse_effect_variance_seconds_squared",
                      "independent_absolute_time_error_variance_seconds_squared",
                      "conditional_icc_point","log_variance_ratio"):
            self.assertAlmostEqual(a[field],actual[field],places=7)  # eigenspace numerical tolerance

    def test_new_rem_l_changes_legacy_method_moments_without_adding_odds(self):
        fit=estimate_race_fixed_reml(self.source,self.target)
        legacy=fit_race_contrast_posterior(self.source,self.target)
        self.assertEqual(
            legacy["hyperparameters"]["source"],
            "SOURCE_CONDITIONAL_METHOD_OF_MOMENTS_NOT_REML")
        self.assertNotAlmostEqual(
            fit["independent_absolute_time_error_variance_seconds_squared"],
            legacy["hyperparameters"]["assumed_absolute_time_residual_variance_seconds2"])
        self.assertGreater(
            fit["independent_absolute_time_error_variance_seconds_squared"],0)

    def test_no_stable_horse_effect_returns_explicit_hold(self):
        altered=deepcopy(self.source)
        # Every horse has all six rank noise positions exactly once
        # over six dates. No horse-specific contrast information.
        alter=[]
        for row in altered["records"]:
            d=int(row["race_id"].split("R")[-1])
            if d>6:
                continue
            horse=int(row["horse_id"][-1])-1
            noise=((horse+d)%6-2.5)*.04
            row["first_section_seconds"]=9+.1*d+noise
            alter.append(row)
        altered["records"]=alter
        with self.assertRaisesRegex(ValueError,"HOLD_REML_HORSE_VARIANCE_ZERO_BOUNDARY|HOLD_VARIANCE_RATIO_NUMERIC_SEARCH_BOUNDARY"):
            estimate_race_fixed_reml(altered,self.target)

    def test_order_invariance_and_strict_source_times(self):
        a=estimate_race_fixed_reml(self.source,self.target)
        s=deepcopy(self.source)
        s["records"].reverse()
        b=estimate_race_fixed_reml(s,self.target)
        self.assertAlmostEqual(a["conditional_icc_point"],b["conditional_icc_point"],places=7)
        for bad in ("future","wrongmarker","wrongsource","postscore"):
            src=deepcopy(self.source)
            if bad=="future":
                src["records"][0]["received_at"]="2026-10-27T09:00:00+09:00"
            if bad=="wrongmarker":
                src["records"][0]["first_marker_m"]=200
            if bad=="wrongsource":
                src["source_system"]="SOME_OTHER_PROVIDER"
            if bad=="postscore":
                src["winner"]=src["records"][0]["horse_id"]
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                estimate_race_fixed_reml(src,self.target)

    def test_invalid_profile_envelope_and_posterior_consistency(self):
        with self.assertRaises(ValueError):
            estimate_race_fixed_reml(self.source,self.target,
                                     profile_deviance_tolerance=100)
        with self.assertRaises(ValueError):
            estimate_race_fixed_reml(self.source,self.target,
                                     profile_deviance_tolerance=-1)
        res=estimate_race_fixed_reml(self.source,self.target)
        covariance=fit_race_contrast_posterior(
            self.source,self.target,
            variance_override=(
                res["horse_effect_variance_seconds_squared"],
                res["independent_absolute_time_error_variance_seconds_squared"]))
        self.assertEqual(len(covariance["mean"]),6)
        self.assertEqual(len(covariance["covariance"]),6)
        self.assertTrue(covariance["shared_race_residual_covariance_model"].startswith("orthogonal"))
        self.assertTrue(np.linalg.eigvalsh(covariance["covariance"])[0]>0)


    def test_leave_one_source_date_out_diagnostic_not_claimed_as_population_CI(self):
        r=leave_one_source_date_out_reml(self.source,self.target)
        self.assertEqual(r["source_dates"],7)
        self.assertEqual(r["successful_leave_one_source_date_fits"]+
                         r["HOLD_leave_one_source_date_fits"],7)
        self.assertTrue(
            r["no_confirmatory_significance_or_population_confidence_interval"])
        self.assertTrue(r["no_target_race_outcomes_or_odds_loaded"])
        self.assertEqual(len(r["date_deletion_details"]),7)
        if r["minimum_deletion_icc"] is not None:
            self.assertLessEqual(r["minimum_deletion_icc"],
                                 r["maximum_deletion_icc"])
        bad=deepcopy(self.source)
        bad["records"]=[row for row in bad["records"] if
                        row["race_day"].split("T")[0]<="2026-10-04"]
        with self.assertRaises(ValueError):
            leave_one_source_date_out_reml(bad,self.target)


if __name__=="__main__":
    unittest.main()
