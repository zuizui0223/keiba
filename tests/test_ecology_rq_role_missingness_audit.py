"""Fictional research-source metadata missingness falsification tests."""
from __future__ import annotations
import copy
import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_role_missingness_audit import (
    audit, build_race_strata,has_complete_documented_roles
)


def fake_source_records(*, linked_to_pace=True, seed=20261013):
    """Purely invented horse records; no official source rows."""
    rng=random.Random(seed)
    records=[]
    for d in range(1,13):
        date=f"2026-06-{d:02d}"
        for n in range(1,5):
            race_shift=rng.gauss(0,1.6)
            for index in range(8):
                complete=index<4
                if linked_to_pace:
                    first_sec=10+race_shift+(.19 if complete else -.19)+rng.gauss(0,.035)
                else:
                    first_sec=10+race_shift+rng.gauss(0,.19)
                records.append({
                    "day":date,"race_number":n,
                    "horse_id":f"FICTIONAL-HORSE-{index:03d}",
                    "horse_name":f"Fictional Horse Name {index}",
                    "first_section_sec":first_sec,
                    "first_marker_m":150.0,"distance":"950 metres",
                    "class":"Invented Maiden",
                    "ground":"Good" if d%2 else "Soft",
                    "weight_kg":55.0+index*.5,
                    "jockey_license_id":("122" if complete else None),
                    "trainer_license_id":"355",
                })
    return records


class RoleMissingnessAuditTests(unittest.TestCase):
    def test_source_completeness_strata_and_fake_timing_bias(self):
        sample=fake_source_records()
        source,q=build_race_strata(sample)
        self.assertEqual(len(source),48)
        self.assertEqual(q["races_with_both_complete_and_incomplete_roles"],48)
        self.assertEqual(q["complete_role_rows_in_mixed_races"],192)
        self.assertEqual(q["incomplete_role_rows_in_mixed_races"],192)
        self.assertTrue(has_complete_documented_roles(sample[0]))
        self.assertFalse(has_complete_documented_roles(sample[5]))
        data=audit(sample,permutations=99,seed=42)
        self.assertEqual(data["status"],
                         "EXPLORATORY_ORIGINAL_METADATA_COMPLETENESS_TIMING_ASSOCIATION")
        observed=data["observed_within_race_descriptive"]
        self.assertGreater(observed["equal_race_weighted_complete_minus_incomplete_first_sec"],.32)
        self.assertLess(observed["equal_race_weighted_complete_minus_incomplete_first_sec"],.44)
        self.assertLess(
            data["race_stratified_completeness_label_shuffle_reference"][
                "fraction_absolute_shuffle_diff_at_least_observed"],.05)
        self.assertEqual(data["delete_one_original_meeting_date"]["deleted_dates_refitted"],12)
        self.assertTrue(data["not_mcAR_mar_mnar_identification_or_selection_correction"])
        import json
        encoded=json.dumps(data)
        self.assertNotIn("FICTIONAL-HORSE",encoded)
        self.assertNotIn("Fictional Horse Name",encoded)
        self.assertNotIn('"122"',encoded)

    def test_random_documented_groups_have_no_systematic_measured_pace_difference(self):
        sample=fake_source_records(linked_to_pace=False)
        result=audit(sample,permutations=99)
        point=result["observed_within_race_descriptive"][
            "equal_race_weighted_complete_minus_incomplete_first_sec"]
        self.assertLess(abs(point),.11)
        self.assertTrue(result["source_positive_GPS_rows_not_documenting_licences_are_NOT_zero_pace"])

    def test_common_race_level_time_shift_is_completely_removed(self):
        original=fake_source_records()
        shifted=copy.deepcopy(original)
        for item in shifted:
            if item["day"]=="2026-06-07" and item["race_number"]==3:
                item["first_section_sec"]+=9.543
        a=audit(original,permutations=79)
        b=audit(shifted,permutations=79)
        self.assertAlmostEqual(
            a["observed_within_race_descriptive"][
                "equal_race_weighted_complete_minus_incomplete_first_sec"],
            b["observed_within_race_descriptive"][
                "equal_race_weighted_complete_minus_incomplete_first_sec"],places=10)

    def test_no_within_race_metadata_contrast_returns_hold(self):
        rows=fake_source_records()
        for r in rows:
            r["jockey_license_id"]="122"
        a=audit(rows,permutations=79)
        self.assertEqual(a["status"],"HOLD_TOO_FEW_WITHIN_RACE_SOURCE_METADATA_STATES")
        self.assertEqual(a["original_source_support"][
            "races_with_no_within_race_role_completeness_contrast"],48)
        self.assertNotIn("observed_within_race_descriptive",a)

    def test_whole_race_missing_metadata_is_not_a_within_race_effect(self):
        rows=fake_source_records()
        for r in rows:
            r["jockey_license_id"]=("122" if int(r["race_number"])%2 else None)
            r["first_section_sec"]+=(5 if int(r["race_number"])%2 else -5)
        a=audit(rows,permutations=79)
        self.assertEqual(a["status"],"HOLD_TOO_FEW_WITHIN_RACE_SOURCE_METADATA_STATES")

    def test_source_validation_rejects_repeated_horse_in_same_race(self):
        rows=fake_source_records()
        rows[1]["horse_id"]=rows[0]["horse_id"]
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_INTERNAL_HORSES_ID"):
            audit(rows,permutations=79)

    def test_source_validation_rejects_inconsistent_first_marker(self):
        rows=fake_source_records()
        rows[1]["first_marker_m"]=250.
        with self.assertRaisesRegex(ValueError,"HOLD_UNHOMOGENEOUS_OFFICIAL_RACE_FIRST_SECTION"):
            audit(rows,permutations=79)

    def test_missing_role_weight_or_zero_licence_is_incomplete_not_imputed(self):
        source=fake_source_records()
        row=source[0].copy()
        for altered in (
            {"weight_kg":None},
            {"weight_kg":99.},
            {"jockey_license_id":"0"},
            {"trainer_license_id":"0"},
            {"trainer_license_id":None},
        ):
            item={**row,**altered}
            self.assertFalse(has_complete_documented_roles(item))
        self.assertTrue(has_complete_documented_roles(row))

    def test_few_observed_horses_per_race_do_not_infer_real_nonfinishers(self):
        sample=[r for r in fake_source_records() if not r["horse_id"].endswith("007")]
        a=audit(sample,permutations=79,min_race_telemetry=8)
        self.assertEqual(a["status"],"HOLD_TOO_FEW_WITHIN_RACE_SOURCE_METADATA_STATES")
        self.assertTrue(a["not_a_test_of_unobserved_GPS_outcomes_or_nonfinishers"])


if __name__=="__main__":
    unittest.main()
