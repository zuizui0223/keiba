"""Fictional original-source records: Gaussian ICC uncertainty calibration checks."""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_rq_icc_parametric_uncertainty import audit,markers


def fake_races(*, horse_sigma=.30,error_sigma=.20,seed=902,days=12):
    rng=random.Random(seed)
    horses=[f"SIMULATED-ANIMAL-{i:03d}" for i in range(55)]
    effects={horse:rng.gauss(0,horse_sigma) for horse in horses}
    out=[]
    for j in range(days):
        day=f"2026-05-{j+1:02d}"
        selected=rng.sample(horses,32)
        for r in range(1,5):
            race=rng.gauss(0,1.0)
            group=selected[8*(r-1):8*r]
            for horse in group:
                value=9.7+race+effects[horse]+rng.gauss(0,error_sigma)
                out.append({
                    "day":day,"race_number":r,
                    "horse_id":horse,"horse_name":"Fictional Name "+horse,
                    "distance":"950 metres","first_marker_m":150.0,
                    "class":"fictional", "ground":"Good",
                    "first_section_sec":value,
                })
    return out


class ConditionalGaussianSourceSamplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.positive=fake_races()

    def test_model_point_is_independently_recovered_and_null_is_smaller(self):
        result=audit(self.positive,fitted_draws=99,zero_variance_draws=99,
                     seed=20261014)
        self.assertEqual(
            result["status"],
            "EXPLORATORY_CONDITIONAL_GAUSSIAN_SOURCE_DESIGN_SAMPLING_ONLY",
        )
        point=result["observed_original_race_FE_conditional_ICC"]
        self.assertGreater(point,.3)
        self.assertTrue(result["independent_eigenprofile_original_point_reproduced"])
        self.assertLess(result["maximum_absolute_point_disagreement_original_vs_independent"],
                        1e-5)
        self.assertEqual(result["source_race_contrasts"],336)
        sample=result["fitted_Gaussian_model_parametric_sampling"]
        null=result["zero_horse_component_Gaussian_null_simulation"]
        self.assertEqual(sample["replicate_fit_count"],99)
        self.assertEqual(null["replicate_fit_count"],99)
        self.assertLess(null["point_estimator_mean"],point)
        self.assertTrue(null["fraction_is_NOT_credible_frequentist_ecological_p_value"])
        q=sample["point_estimator_quantiles_025_05_50_95_975"]
        self.assertEqual(q,sorted(q))
        self.assertLess(q[0],point)
        self.assertGreater(q[-1],point)
        self.assertFalse(result["H1_ground_slope_or_H2_social_effect_identified"])
        self.assertTrue(sample["interval_is_sampling_distribution_not_robust_95pct_CI"])
        self.assertTrue(result["no_animal_ID_name_GPS_record_or_licence_emitted"])
        encoded=json.dumps(result)
        self.assertNotIn("SIMULATED-ANIMAL",encoded)
        self.assertNotIn("Fictional Name",encoded)

    def test_random_source_simulation_is_reproducible(self):
        one=audit(self.positive,fitted_draws=99,
                  zero_variance_draws=99,seed=1993)
        two=audit(self.positive,fitted_draws=99,
                  zero_variance_draws=99,seed=1993)
        self.assertEqual(one,two)

    def test_common_race_time_shift_does_not_change_source_results(self):
        shifted=copy.deepcopy(self.positive)
        for r in shifted:
            if r["day"]=="2026-05-03" and r["race_number"]==3:
                r["first_section_sec"]+=11.789
        first=audit(self.positive,fitted_draws=99,
                    zero_variance_draws=99,seed=211)
        second=audit(shifted,fitted_draws=99,
                     zero_variance_draws=99,seed=211)
        self.assertAlmostEqual(
            first["observed_original_race_FE_conditional_ICC"],
            second["observed_original_race_FE_conditional_ICC"],places=6)
        self.assertAlmostEqual(
            first["fitted_Gaussian_model_parametric_sampling"]["point_estimator_mean"],
            second["fitted_Gaussian_model_parametric_sampling"]["point_estimator_mean"],
            places=6)

    def test_source_observational_no_horse_variance_does_not_become_H1(self):
        fabricated_null=fake_races(horse_sigma=0,error_sigma=.2,seed=902)
        out=audit(fabricated_null,fitted_draws=99,
                  zero_variance_draws=99)
        self.assertTrue(out["not_a_robust_confidence_interval_or_confirmatory_test"])
        self.assertFalse(out["H1_ground_slope_or_H2_social_effect_identified"])
        if "observed_original_race_FE_conditional_ICC" in out:
            self.assertLess(
                out["observed_original_race_FE_conditional_ICC"],.30)

    def test_absent_marker_has_explicit_hold_not_zero_ICC(self):
        groups=markers(self.positive,marker_values=(150,200),
                       fitted_draws=99,null_draws=99)
        self.assertEqual(set(groups),{"150","200"})
        self.assertEqual(
            groups["150"]["status"],
            "EXPLORATORY_CONDITIONAL_GAUSSIAN_SOURCE_DESIGN_SAMPLING_ONLY")
        self.assertTrue(groups["200"]["status"].startswith("HOLD_"))
        self.assertNotIn("observed_original_race_FE_conditional_ICC",groups["200"])

    def test_insufficient_repeated_animals_are_an_inference_hold(self):
        unique=copy.deepcopy(self.positive)
        for idx,row in enumerate(unique):
            row["horse_id"]=f"UNIQUE-FAKE-{idx}"
            row["horse_name"]=f"Unique fictional name {idx}"
        result=audit(unique,fitted_draws=99,zero_variance_draws=99)
        self.assertEqual(
            result["status"],"HOLD_ORIGINAL_SOURCE_DESIGN_NOT_IDENTIFIABLE")
        self.assertNotIn("fitted_Gaussian_model_parametric_sampling",result)

    def test_source_simulation_rejects_extreme_trial_counts(self):
        with self.assertRaisesRegex(ValueError,"HOLD_PARAMETRIC_SOURCE_MC_REPLICATES"):
            audit(self.positive,fitted_draws=5,zero_variance_draws=99)
        with self.assertRaisesRegex(ValueError,"HOLD_PARAMETRIC_SOURCE_MC_REPLICATES"):
            audit(self.positive,fitted_draws=99,zero_variance_draws=5000)
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_OR_TOO_MANY"):
            markers(self.positive,marker_values=(150,150))


if __name__=="__main__":
    unittest.main()
