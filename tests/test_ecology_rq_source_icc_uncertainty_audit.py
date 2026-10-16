"""Wholly fictional two-venue source data and critical source-HOLD checks."""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_source_icc_uncertainty_audit import (
    SOURCE_LOCK,source_model_audit
)


def fake_source(venue:str, missing_date:bool=False):
    rng=random.Random(81)
    source_dates=SOURCE_LOCK[venue]["dates"]
    marker=150. if venue=="cannon" else 200.
    status=("SOURCE_CANNON_PARK_IDS_AND_GPS_AUDITED"
            if venue=="cannon" else
            "SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED")
    rows=[]
    manifest={}
    horse_effect={f"INVENTED-HORSE-{race}-{i}":rng.gauss(0,.25)
                  for race in range(1,5) for i in range(6)}
    for k,day in enumerate(source_dates):
        manifest[day]={
            "status":status,
            "original_source_SHA256_only":{"gps_sectionals":"FICTITIOUS"},
            "source_sha256":{"gps_sectionals":"FICTITIOUS"},
            "positive_first_GPS_candidates":24,
            "first_positive_GPS_source_HORSES_ID_matches":24,
        }
        if missing_date and k==4:
            manifest[day]={"status":"HOLD_DATE_SOURCE_NOT_RECONCILED",
                            "not_counted_as_zero_participation":True}
            continue
        for race in range(1,5):
            race_shift=rng.gauss(0,.30)
            for h in range(6):
                animal=f"INVENTED-HORSE-{race}-{h}"
                y=10+race_shift+horse_effect[animal]+rng.gauss(0,.13)
                rows.append({
                    "day":day,"race_number":race,
                    "horse_id":animal,"horse_name":"Fictional "+animal,
                    "distance":"950 metres",
                    "class":"invented class",
                    "ground":"Good","first_marker_m":marker,
                    "first_section_sec":y,
                })
    return rows,manifest


def source_reader(kind:str,missing=False):
    def go(**kwargs):
        return fake_source(kind,missing_date=missing)
    return go


class ModelConditionalOriginalSourceTest(unittest.TestCase):
    def test_one_venue_source_hold_never_cherry_picks_11_dates(self):
        out=source_model_audit(
            "cannon",reader=source_reader("cannon",missing=True),
            fitted_draws=99,zero_draws=99
        )
        self.assertEqual(out["status"],"HOLD_INCOMPLETE_LOCKED_VENUE_SOURCE_COHORT")
        self.assertEqual(len(out["source_date_HOLD_not_auto_excluded"]),1)
        self.assertTrue(out["model_conditional_MC_was_not_run_on_partial_source_cohort"])
        self.assertNotIn("pooled_first_section_source_model_conditional_sampling",out)
        self.assertTrue(out["not_a_zero_or_negative_horse_ICC"])

    def test_cannon_model_and_marker_gate_are_source_aware(self):
        out=source_model_audit(
            "cannon",reader=source_reader("cannon"),
            fitted_draws=99,zero_draws=99
        )
        self.assertEqual(out["status"],
                         "SOURCE_CONDITIONAL_GAUSSIAN_UNCERTAINTY_AUDITED_NOT_BIOLOGICAL_REPLICATION")
        self.assertEqual(out["source_dates_fully_audited"],12)
        self.assertEqual(out["source_date_HOLD_not_auto_excluded"],[])
        self.assertTrue(out["simulation_was_posthoc_to_positive_initial_ICCs"])
        p=out["pooled_first_section_source_model_conditional_sampling"]
        self.assertEqual(p["status"],
                         "EXPLORATORY_CONDITIONAL_GAUSSIAN_SOURCE_DESIGN_SAMPLING_ONLY")
        self.assertGreater(p["observed_original_race_FE_conditional_ICC"],.4)
        mk=out["first_GPS_marker_specific_model_conditional_sampling"]
        self.assertEqual(set(mk),{"150","250"})
        self.assertTrue(mk["250"]["status"].startswith("HOLD_"))
        self.assertEqual(mk["150"]["status"],p["status"])
        self.assertTrue(out["source_site_marker_mismatch_precludes_interpreting_pooled_Cannon_Eagle_as_same_trait"])
        self.assertTrue(out["no_original_horse_rider_trainer_IDs_names_or_GPS_values_exported"])
        serialized=json.dumps(out)
        self.assertNotIn("INVENTED-HORSE",serialized)
        self.assertNotIn("Fictional ",serialized)

    def test_eagle_200_marker_not_comparable_to_cannon_150(self):
        out=source_model_audit(
            "eagle",reader=source_reader("eagle"),
            fitted_draws=99,zero_draws=99,seed=987
        )
        marker=out["first_GPS_marker_specific_model_conditional_sampling"]
        self.assertTrue(marker["100"]["status"].startswith("HOLD_"))
        self.assertEqual(marker["200"]["status"],
                         "EXPLORATORY_CONDITIONAL_GAUSSIAN_SOURCE_DESIGN_SAMPLING_ONLY")
        self.assertEqual(out["venue"],"Eagle Farm")
        self.assertFalse(out["H1_random_ground_slopes_estimated"])
        self.assertFalse(out["H2_causal_social_interaction_estimated"])

    def test_source_venue_not_freeform_and_dates_not_chosen_by_results(self):
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED_SOURCE_RACECOURSE"):
            source_model_audit(
                "Arbitrary Track",reader=source_reader("cannon"),
                fitted_draws=99,zero_draws=99)
        source=source_reader("cannon")
        def incomplete(**kwargs):
            rows,manifest=source(**kwargs)
            manifest.pop(next(iter(manifest)))
            return rows,manifest
        with self.assertRaisesRegex(ValueError,"HOLD_DATE_MANIFEST_NOT_MATCHING"):
            source_model_audit(
                "cannon",reader=incomplete,fitted_draws=99,zero_draws=99)


if __name__=="__main__":
    unittest.main()
