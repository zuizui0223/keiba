"""Exact conditional covariance of the within-race horse random intercept.

These tests are fully fabricated: 6 toy horses, 7 toy races.
This is NOT the main RQ race-fixed REML ICC and not JRA personality.
"""
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
    from keiba_race_contrast_trait_posterior import (
        fit_race_contrast_posterior, draw_joint_effects
    )
    from keiba_individual_trait_market_demo import toy_data


@unittest.skipIf(np is None, "NumPy optional scientific tests run in dedicated CI")
class ContrastPosteriorSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source,cls.target,_ = toy_data()

    def fit(self, source=None, target=None, override=(.15,.06)):
        return fit_race_contrast_posterior(
            source or self.source,target or self.target,
            variance_override=override)

    def test_closed_form_complete_same_horse_roster_covariance(self):
        # With n=6 same horses each of R=7 independent race contrasts:
        # V = var_difference*(I-J/n) + a2*J/n.
        a2,e2=.15,.06
        R=7
        n=6
        got=self.fit()
        cov=np.asarray(got["covariance"])
        d=1/(1/a2+R/e2)
        J=np.ones((n,n))/n
        expected=d*(np.eye(n)-J)+a2*J
        np.testing.assert_allclose(cov,expected,atol=1e-12,rtol=1e-11)
        self.assertGreater(cov[0,1],0)
        self.assertGreater(got["max_absolute_offdiagonal_effect_correlation"],.8)
        self.assertEqual(got["historical_horses_in_joint_fit"],6)
        self.assertEqual(got["historical_race_count"],7)
        self.assertEqual(got["source_race_sizes"],[6]*7)
        self.assertTrue(got["global_mean_unidentified_by_within_race_contrasts"])
        for a in range(n):
            for b in range(a+1,n):
                self.assertAlmostEqual(
                    got["pair_effect_variance"][f"TOY_H{a+1}|TOY_H{b+1}"],
                    2*d,places=12)
        self.assertGreater(2*cov[0,0],2*d)

    def test_theoretical_posterior_mean_from_orthogonal_centering(self):
        a2,e2=.15,.06
        R=7
        fit=self.fit()
        by={}
        for row in self.source["records"]:
            by.setdefault(row["race_id"],[]).append(row)
        sufficient=np.zeros(6)
        for rows in by.values():
            times=np.array([z["first_section_seconds"] for z in rows])
            sufficient+=times-times.mean()
        k=a2/(e2+R*a2)
        expected=k*sufficient
        np.testing.assert_allclose(fit["mean"],expected,atol=1e-12)

    def test_race_intercept_shifts_never_change_posterior(self):
        base=self.fit()
        altered=deepcopy(self.source)
        for row in altered["records"]:
            day=int(row["race_id"].split("R")[-1])
            row["first_section_seconds"]+=2.+.03*day
        second=self.fit(source=altered)
        np.testing.assert_allclose(base["mean"],second["mean"],atol=1e-12)
        np.testing.assert_allclose(base["covariance"],second["covariance"],atol=1e-12)

    def test_permutation_of_all_horse_ids_is_equivariant(self):
        base=self.fit()
        remap={h:f"OTHER_{h}" for h in self.target["horse_ids"]}
        source=deepcopy(self.source)
        target=deepcopy(self.target)
        target["horse_ids"]=[remap[h] for h in reversed(target["horse_ids"])]
        for rec in source["records"]:
            rec["horse_id"]=remap[rec["horse_id"]]
        changed=self.fit(source=source,target=target)
        np.testing.assert_allclose(changed["mean"],base["mean"][::-1],atol=1e-12)
        np.testing.assert_allclose(changed["covariance"],
                                   np.asarray(base["covariance"])[::-1,::-1],
                                   atol=1e-12)

    def test_joint_draws_keep_covariance_and_constant_scenarios_collapse(self):
        fit=self.fit()
        a=draw_joint_effects(fit,draws=64,seed=101)
        b=draw_joint_effects(fit,draws=64,seed=101)
        np.testing.assert_array_equal(a,b)
        zero=draw_joint_effects(fit,draws=64,seed=101,enabled=False)
        np.testing.assert_allclose(zero,np.broadcast_to(fit["mean"],(64,6)))
        # The global intercept has covariance a2 along its mean mode.
        self.assertGreater(np.corrcoef(a.T)[0,1],.55)
        self.assertGreater(np.std(a[:,0]),0)
        np.testing.assert_array_equal(zero[0],zero[-1])

    def test_default_source_estimated_moments_labeled_not_rem_l(self):
        got=fit_race_contrast_posterior(self.source,self.target)
        self.assertEqual(
            got["hyperparameters"]["source"],
            "SOURCE_CONDITIONAL_METHOD_OF_MOMENTS_NOT_REML")
        self.assertTrue(got["not_original_RQ_REML_fit"])
        self.assertTrue(got["no_independent_real_market_source_proof"])
        self.assertGreater(got["hyperparameters"]["horse_between_variance_seconds2"],0)
        self.assertEqual(len(got["covariance"]),6)

    def test_invalid_or_future_inputs_fail(self):
        for override in ((0,.1),(.1,0),(-1,.2),(.1,-.2),(.1,),("bad",.2)):
            with self.subTest(override=override),self.assertRaises(ValueError):
                self.fit(override=override)
        altered=deepcopy(self.source)
        altered["records"][0]["source_system"]="UNRELATED_GPS_PROVIDER"
        with self.assertRaises(ValueError):
            self.fit(source=altered)
        altered=deepcopy(self.source)
        altered["records"][0]["received_at"]="2026-10-27T11:00:00+09:00"
        with self.assertRaises(ValueError):
            self.fit(source=altered)
        altered=deepcopy(self.source)
        altered["rights_checked_locally"]=False
        with self.assertRaises(ValueError):
            self.fit(source=altered)

    def test_joint_draw_validates_covariance_positive_definite(self):
        got=self.fit()
        modified=deepcopy(got)
        modified["covariance"][0][0]=-1.
        with self.assertRaises(ValueError):
            draw_joint_effects(modified,draws=5,seed=1)
        with self.assertRaises(ValueError):
            draw_joint_effects(got,draws=65,seed=1)


if __name__=="__main__":
    unittest.main()
