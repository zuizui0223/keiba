"""Deterministic fake-horse validation for exact race-FE random-intercept ICC.

No real racing animals, outcomes, odds or source identities are used.
"""
from __future__ import annotations

import copy
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_race_fixed_icc import (
    race_fixed_reml, delete_date_sensitivity, analyze,
    source_race_identity_shuffle_reference
)


def fake_race_records(sigma_h=0.35, sigma_e=0.13, seed=512):
    rng=random.Random(seed)
    horses=[f"INVENTED-HORSE-{j:03d}" for j in range(80)]
    effect={h:rng.gauss(0,sigma_h) for h in horses}
    rows=[]
    for d in range(12):
        day=f"2026-01-{d+1:02d}"
        participants=rng.sample(horses,32)
        for race in range(1,5):
            race_shift=rng.gauss(0,1.2)
            for horse in participants[(race-1)*8:race*8]:
                y=(10.0+race_shift+effect[horse]+rng.gauss(0,sigma_e))
                rows.append({
                    "day":day,"race_number":race,
                    "horse_id":horse,"horse_name":f"Fake Name {horse}",
                    "first_section_sec":y,"distance":"950 metres",
                    "class":"Class A" if d%3 else "Class B",
                    "ground":"Good" if d%3 else "Heavy",
                    "first_marker_m":150.0
                })
    return rows


class ExactRaceFixedICC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.positive=fake_race_records()
        cls.zero=fake_race_records(sigma_h=0)

    def test_known_horse_variance_recovered_as_conditionally_positive_icc(self):
        fit=race_fixed_reml(self.positive,4)
        self.assertEqual(
            fit["status"],"EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY")
        self.assertEqual(fit["source_rows"],384)
        self.assertEqual(fit["original_races"],48)
        self.assertEqual(fit["original_date_clusters"],12)
        self.assertEqual(fit["race_fixed_effect_contrast_observations"],336)
        self.assertGreater(fit["conditional_observational_ICC_point_estimate"],0.5)
        self.assertLessEqual(fit["conditional_observational_ICC_point_estimate"],1)
        self.assertTrue(fit["race_intercepts_adjust_for_shared_ground_class_distance_and_other_race_factors"])
        self.assertFalse(fit["formal_hypothesis_p_value_provided"])
        self.assertFalse(fit["robust_ICC_confidence_interval_provided"])

    def test_null_no_horse_effect_does_not_create_large_icc(self):
        f=race_fixed_reml(self.zero,4)
        self.assertLess(f["conditional_observational_ICC_point_estimate"],.3)
        self.assertFalse(f["not_confirmatory_inference_or_genetic_heritability"] is False)

    def test_arbitrarily_slower_whole_race_is_exactly_eliminated(self):
        shifted=copy.deepcopy(self.positive)
        for row in shifted:
            if row["day"]=="2026-01-03" and row["race_number"]==1:
                row["first_section_sec"]+=15.123
        a=race_fixed_reml(self.positive,4)
        b=race_fixed_reml(shifted,4)
        self.assertAlmostEqual(
            a["conditional_observational_ICC_point_estimate"],
            b["conditional_observational_ICC_point_estimate"],places=6)
        self.assertAlmostEqual(
            a["horse_variance_component_sec_squared"],
            b["horse_variance_component_sec_squared"],places=6)

    def test_shuffle_horse_identity_within_race_reduces_persistence(self):
        moved=copy.deepcopy(self.positive)
        rng=random.Random(456)
        by_race={}
        for i,r in enumerate(moved):
            by_race.setdefault((r["day"],r["race_number"]),[]).append(i)
        for indices in by_race.values():
            identities=[(moved[i]["horse_id"],moved[i]["horse_name"])
                        for i in indices]
            rng.shuffle(identities)
            for index,(hid,name) in zip(indices,identities):
                moved[index]["horse_id"]=hid
                moved[index]["horse_name"]=name
        f=race_fixed_reml(moved,4)
        self.assertLess(f["conditional_observational_ICC_point_estimate"],.3)

    def test_actual_race_identity_shuffle_negative_control_is_only_exploratory(self):
        result=source_race_identity_shuffle_reference(
            self.positive,permutations=59,seed=20261013)
        self.assertEqual(result["status"],
                         "EXPLORATORY_RACE_CONDITIONED_HORSE_ID_REASSIGNMENT_REFERENCE")
        self.assertEqual(result["valid_within_race_identity_shuffle_models"],59)
        self.assertGreater(result["original_conditional_ICC"],.5)
        self.assertLess(result["shuffle_reference_mean_conditional_ICC"],.25)
        self.assertLess(result["fraction_shuffled_ICC_at_least_original"],.05)
        self.assertTrue(result["this_fraction_is_not_confirmatory_p_value"])
        import json
        self.assertNotIn("INVENTED-HORSE",json.dumps(result))

    def test_insufficient_repeated_source_ids_results_in_hold(self):
        unique=copy.deepcopy(self.positive)
        for i,row in enumerate(unique):
            row["horse_id"]=f"UNIQUE-HORSE-{i}"
            row["horse_name"]=f"UNIQUE-NAME-{i}"
        result=race_fixed_reml(unique,4)
        self.assertEqual(
            result["status"],"HOLD_INSUFFICIENT_REPEATED_HORSES_OR_RACES_FOR_ICC")
        self.assertNotIn("conditional_observational_ICC_point_estimate",result)

    def test_six_plus_observed_gps_and_delete_one_meeting(self):
        r=race_fixed_reml(self.positive,6)
        self.assertEqual(r["status"],"EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY")
        delete=delete_date_sensitivity(self.positive,4)
        self.assertEqual(delete["status"],
                         "EXPLORATORY_ONE_DATE_DELETION_STABILITY_NOT_CONFIDENCE_INTERVAL")
        self.assertEqual(delete["deleted_meeting_dates"],12)
        self.assertTrue(delete["not_a_jackknife_variance_or_uncertainty_interval"])
        self.assertGreater(delete["minimum_conditional_ICC_point"],0)
        self.assertLess(delete["maximum_conditional_ICC_point"],1)

    def test_exact_observational_model_does_not_confuse_heritability(self):
        r=analyze(self.positive)
        self.assertEqual(r["status"],
                         "EXPLORATORY_REAL_THOROUGHBRED_RACE_FE_HORSE_RE_ICC_DIAGNOSTIC")
        self.assertTrue(r["not_H1_or_H2_or_causal_or_heritability"])
        self.assertTrue(r["requires_confirmed_starter_roster_true_individual_results_and_jockey_weight_adjustment"])
        import json
        result=json.dumps(r)
        self.assertNotIn("INVENTED-HORSE",result)
        self.assertNotIn("Fake Name",result)


if __name__=="__main__":
    unittest.main()
