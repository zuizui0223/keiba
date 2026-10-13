"""Synthetic source attributes and random-intercept validation for adjusted ICC."""
from __future__ import annotations

import copy
from pathlib import Path
import random
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_covariate_icc import (
    official_covariates,compare,adjusted_race_icc,_complete_sample,
)
from ecology_rq_race_fixed_icc import race_fixed_reml


def invented(n_days=12,seed=711,horse_var=.25,
             rider_var=.23,trainer_var=.12,weight_slope=.09):
    rng=random.Random(seed)
    n_horses=54
    horses=[f"FAKE-HORSE-{j:03}" for j in range(n_horses)]
    ids=["100"+str(j) for j in range(9)]
    coaches=["200"+str(j) for j in range(10)]
    horse_r=rng.choices(range(9),k=n_horses)
    horse_t=[j%10 for j in range(n_horses)]
    horse_b={h:rng.gauss(0,horse_var) for h in horses}
    rider_b={a:rng.gauss(0,rider_var) for a in ids}
    coach_b={a:rng.gauss(0,trainer_var) for a in coaches}
    weights={h:52.0+(j%9)*.5 for j,h in enumerate(horses)}
    data=[]
    for k in range(n_days):
        day=f"2026-03-{k+1:02d}"
        participants=rng.sample(list(range(n_horses)),32)
        for race in range(1,5):
            common=rng.gauss(0,.7)
            for jj in participants[(race-1)*8:race*8]:
                h=horses[jj]
                rider=ids[(horse_r[jj]+k%4)%len(ids)]
                coach=coaches[horse_t[jj]]
                weight=weights[h]+(.5 if (k+jj)%3 else -.5)
                y=(10.4+common+horse_b[h]+rider_b[rider]+coach_b[coach]
                   +weight_slope*(weight-54.)+rng.gauss(0,.13))
                data.append({
                    "day":day,"race_number":race,
                    "horse_id":h,"horse_name":f"Synthetic Name {h}",
                    "first_section_sec":y,"distance":"950 metres",
                    "first_marker_m":150.,"class":"FakeClass",
                    "ground":"Good" if k%2 else "Soft",
                    "weight_kg":weight,
                    "jockey_license_id":rider,
                    "trainer_license_id":coach
                })
    return data


class CovariateSourceAndAdjustmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=invented()

    def test_documented_nested_role_ids_and_riding_weight(self):
        data=b"""<Horses><Horse Id="912"><HorseName>Fake Horse</HorseName>
          <Weight>58.5</Weight>
          <Jockey Id="123"><FullName>Invented Rider</FullName></Jockey>
          <Trainer Id="456"><FullName>Invented Trainer</FullName></Trainer>
        </Horse><Horse Id="913"><HorseName>Other</HorseName>
          <Weight>95.0</Weight><Jockey><FullName>Unknown</FullName></Jockey>
          <Trainer Id="789"><FullName>Other Trainer</FullName></Trainer>
        </Horse></Horses>"""
        parsed,summary=official_covariates(ET.fromstring(data))
        self.assertEqual(parsed["912"],{
            "weight_kg":58.5,"jockey_license_id":"123",
            "trainer_license_id":"456",
        })
        self.assertIsNone(parsed["913"]["weight_kg"])
        self.assertIsNone(parsed["913"]["jockey_license_id"])
        self.assertEqual(summary["counts"]["all_three_documented_and_valid"],1)
        self.assertTrue(summary["age_not_returned_by_this_operation"])
        self.assertNotIn("Invented Rider",str(summary))
        self.assertNotIn("Fake Horse",str(summary))

    def test_zero_license_id_is_not_a_real_jockey_or_trainer(self):
        data=b'<Horses><Horse Id="912"><Weight>58.5</Weight><Jockey Id="0"/><Trainer Id="0"/></Horse></Horses>'
        decoded,s=official_covariates(ET.fromstring(data))
        self.assertIsNone(decoded["912"]["jockey_license_id"])
        self.assertIsNone(decoded["912"]["trainer_license_id"])
        self.assertEqual(s["counts"]["all_three_documented_and_valid"],0)

    def test_duplicate_official_horse_ids_refused(self):
        data=b'<Horses><Horse Id="1"><Weight>59</Weight></Horse><Horse Id="1"><Weight>58</Weight></Horse></Horses>'
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_OR_DUPLICATE"):
            official_covariates(ET.fromstring(data))

    def test_adjustment_is_same_source_cohort_without_age_guessing(self):
        result=compare(self.data)
        self.assertEqual(result["status"],
                         "ORIGINAL_HORSE_SOURCE_EXPLORATORY_COVARIATE_ADJUSTMENT_ONLY")
        self.assertTrue(result["modeled_row_overlap_identical_for_all_models"])
        self.assertAlmostEqual(
            result["same_source_cohort_full_adjustment_minus_unadjusted_ICC_point"],
            result["models"]["weight_jockey_trainer_license"]["conditional_ICC_point"]
            - result["models"]["same_rows_unadjusted_race_HORSES"]["conditional_observational_ICC_point_estimate"],
            places=8
        )
        self.assertTrue(result["delta_is_not_caused_by_nuisance_variables_or_significance"])
        self.assertEqual(result["source_gate"]["valid_complete_case_rows_after_field_filter"],len(self.data))
        self.assertFalse(result["source_real_horse_covariate_support"]["source_carries_age_or_birthdate"])
        self.assertEqual(result["models"]["weight_jockey_trainer_license"]["nuisance_mode"],
                         "weight_jockey_trainer")
        for key in ("weight_within_race","weight_plus_jockey_license",
                    "weight_jockey_trainer_license"):
            fit=result["models"][key]
            self.assertEqual(fit["status"],
                             "EXPLORATORY_ADJUSTED_ICC_MODEL_POINT_ONLY")
            self.assertGreaterEqual(fit["conditional_ICC_point"],0)
            self.assertLessEqual(fit["conditional_ICC_point"],1)
            self.assertTrue(fit["not_confirmatory_robust_inference"])
            self.assertGreater(fit["remaining_restricted_likelihood_dimensions"],55)
            self.assertFalse(fit["ICC_robust_cluster_confidence_interval"] if
                             "ICC_robust_cluster_confidence_interval" in fit else False)
        self.assertGreater(result["source_real_horse_covariate_support"]["HORSES_IDs_with_multiple_jockey_licences"],0)
        self.assertNotIn("FAKE-HORSE",str(result))
        self.assertNotIn("Synthetic Name",str(result))

    def test_weight_adjustment_and_race_common_offset(self):
        data=invented(horse_var=0,rider_var=0,trainer_var=0,weight_slope=.8)
        b=race_fixed_reml(data)
        m=adjusted_race_icc(data,"weight")
        self.assertIn(b["status"],{
            "EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY",
            "EXPLORATORY_RACE_ADJUSTED_ICC_AT_ZERO_BOUNDARY",
        })
        self.assertGreater(b["conditional_observational_ICC_point_estimate"],.15)
        self.assertLess(m["conditional_ICC_point"],b["conditional_observational_ICC_point_estimate"])
        shifted=copy.deepcopy(data)
        for row in shifted:
            if row["day"]=="2026-03-01" and row["race_number"]==1:
                row["first_section_sec"]+=9.126
        m2=adjusted_race_icc(shifted,"weight")
        self.assertAlmostEqual(m["conditional_ICC_point"],m2["conditional_ICC_point"],places=5)

    def test_missing_documented_role_reduces_common_source_sample(self):
        data=copy.deepcopy(self.data)
        data[0]["jockey_license_id"]=None
        data[1]["weight_kg"]=None
        outcome=compare(data)
        self.assertEqual(outcome["source_gate"]["row_exclusions"]["missing_jockey_licence"],1)
        self.assertEqual(outcome["source_gate"]["row_exclusions"]["missing_or_bad_weight"],1)
        self.assertEqual(outcome["source_gate"]["source_candidates"],len(data))
        self.assertTrue(outcome["modeled_row_overlap_identical_for_all_models"])
        self.assertLess(outcome["source_gate"]["valid_complete_case_rows_after_field_filter"],len(data))
        self.assertIn("Good",outcome["source_gate"]["coverage_by_official_race_ground"])
        by=outcome["source_gate"]["coverage_by_original_meeting_date"]
        self.assertEqual(len(by),12)
        self.assertTrue(outcome["source_gate"]["remaining_fraction_of_original_positive_first_section_records"]<1)

    def test_sparse_jockey_trainer_levels_cannot_be_assumed_zero(self):
        data=copy.deepcopy(self.data)
        for r in data:
            r["jockey_license_id"]="999"
            r["trainer_license_id"]="999"
        check=adjusted_race_icc(data,"weight_jockey_trainer")
        self.assertEqual(check["status"],"HOLD_INSUFFICIENT_JOCKEY_LEVEL_SUPPORT")
        self.assertNotIn("conditional_ICC_point",check)

    def test_all_source_covariates_absent_is_explicit_HOLD(self):
        data=copy.deepcopy(self.data)
        for r in data:
            r["weight_kg"]=None
        summary=compare(data)
        self.assertEqual(summary["status"],"HOLD_NO_SOURCE_COMPLETE_COVARIATES")
        self.assertTrue(summary["no_horse_jockey_trainer_IDs_exported"])


if __name__=="__main__":
    unittest.main()
