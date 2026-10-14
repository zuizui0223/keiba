"""Only FICTIONAL Thoroughbred test rows. No individual original RQ values."""
from __future__ import annotations

import copy
from datetime import date, timedelta
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_rq_rider_switch_consistency import (
    GAP_CUTOFF_DAYS, analyze, pair_records, rider_label_shuffled_time_reference,
    source_timed_panel, summarize_pairs,
)


def synthetic_races(*, horses=32, days=10, seed=20261014, horse_effect=True,
                    jockey_change=True, trainer_documented=True):
    rng=random.Random(seed)
    start=date(2026,1,5)
    ids=[f"INVENTED-HORSE-{i:04d}" for i in range(horses)]
    trait={hid:rng.gauss(0,.45) if horse_effect else 0. for hid in ids}
    rows=[]
    for di in range(days):
        day=(start+timedelta(days=28*di)).isoformat()
        shuffled=ids[:]
        rng.shuffle(shuffled)
        for race in range(1,1+horses//8):
            race_shift=rng.gauss(0,0.4)
            for hid in shuffled[(race-1)*8:race*8]:
                i=int(hid.rsplit("-",1)[1])
                # Two consecutive dates share source-declared jockey;
                # later dates change declared rider for every horse.
                jockey=100+i*11+(di//2 if jockey_change else 0)
                rows.append({
                    "day":day,
                    "race_number":race,
                    "horse_id":hid,
                    "horse_name":f"FAKE-NAME-{i}",
                    "first_section_sec":10.+race_shift+trait[hid]+rng.gauss(0,.08),
                    "first_marker_m":150.,
                    "distance":"1100 metres",
                    "class":"FICTIONAL Class A",
                    "ground":"Good" if di%2 else "Soft",
                    "jockey_license_id":str(jockey),
                    "trainer_license_id":str(500+i%5)
                           if trainer_documented else None,
                    "weight_kg":54.0,
                })
    return rows


class RiderChangeSourceConsistencyTests(unittest.TestCase):
    def test_numeric_jockey_changes_on_many_repeat_horses(self):
        sample=synthetic_races()
        out=analyze(sample,permutations=59)
        broad=out["same_official_race_distance_and_exact_first_GPS_marker"]
        switched=broad["status_by_rider_pair_condition"]["switched"]
        self.assertEqual(switched["status"],"EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY")
        self.assertEqual(switched["distinct_official_HORSES_IDs"],32)
        self.assertGreater(switched["within_horse_cross_date_pairs"],32)
        self.assertGreater(switched[
            "equal_horse_stratum_mean_pair_product_seconds_squared"],0.01)
        self.assertTrue(broad["status_by_rider_pair_condition"]["same"][
            "within_horse_cross_date_pairs"]>0)
        self.assertTrue(broad["status_by_rider_pair_condition"]["switched_same_trainer"][
            "within_horse_cross_date_pairs"]>0)
        null=out["changed_declared_jockey_within_race_outcome_shuffle_reference"]
        self.assertEqual(null["status"],
            "EXPLORATORY_WITHIN_ORIGINAL_RACE_OUTCOME_SHUFFLE_REFERENCE_ONLY")
        self.assertEqual(null["reference_iterations"],59)
        self.assertGreater(
            switched["equal_horse_stratum_mean_pair_product_seconds_squared"],
            null["reference_mean_seconds_squared"])
        self.assertFalse(out["causal_jockey_or_evolutionary_or_heritability_claim_supported"])
        self.assertFalse(out["horse_going_H1_ground_random_slope_fitted"])
        self.assertFalse(out["horse_competitor_H2_interaction_fitted"])
        encoded=json.dumps(out)
        for bad in ("FAKE-NAME","INVENTED-HORSE","FICTIONAL Class A",
                    '"jockey_id"','"trainer_id"','"first_section_sec"'):
            self.assertNotIn(bad,encoded)

    def test_nonrandom_null_no_horse_effect_does_not_force_large_phenotype_product(self):
        out=analyze(synthetic_races(horse_effect=False),permutations=59)
        s=out["same_official_race_distance_and_exact_first_GPS_marker"][
            "status_by_rider_pair_condition"]["switched"]
        self.assertEqual(s["status"],"EXPLORATORY_OBSERVATIONAL_PAIR_PRODUCT_ONLY")
        self.assertLess(abs(s[
            "equal_horse_stratum_mean_pair_product_seconds_squared"]),.02)

    def test_declared_rider_constant_returns_hold_not_zero(self):
        out=analyze(synthetic_races(jockey_change=False),permutations=59)
        changed=out["same_official_race_distance_and_exact_first_GPS_marker"][
            "status_by_rider_pair_condition"]["switched"]
        self.assertEqual(changed["distinct_official_HORSES_IDs"],0)
        self.assertNotIn("equal_horse_stratum_mean_pair_product_seconds_squared",changed)
        self.assertEqual(out["changed_declared_jockey_within_race_outcome_shuffle_reference"][
            "status"],"HOLD_RIDER_SWITCH_PAIR_SUPPORT_BELOW_PREDECLARED_MINIMUM")

    def test_missing_jockey_on_three_peers_does_not_recompute_race_mean(self):
        small=synthetic_races(horses=8,days=2)
        target=small[0]
        first_day=target["day"]
        for r in small:
            if r["day"]==first_day and r is not target:
                r["jockey_license_id"]=None
        enriched,q=source_timed_panel(small)
        self.assertEqual(q["source_rows_with_valid_original_Jockey_Id"],9)
        self.assertEqual(q["source_GPS_rows_after_race_minimum"],16)
        self.assertTrue(q["rider_incomplete_peers_retained_in_race_baseline"])
        expected=target["first_section_sec"]-sum(
            r["first_section_sec"] for r in small
            if r["day"]==first_day and r is not target
        )/7
        ours=next(r for r in enriched
                  if r["day"]==first_day and r["horse_id"]==target["horse_id"])
        self.assertAlmostEqual(ours["relative_seconds"],expected,places=10)

    def test_strict_class_removes_cross_class_pairs(self):
        rows=synthetic_races()
        for r in rows:
            if r["day"]>= "2026-05-01":
                r["class"]="FICTIONAL Class B"
        out=analyze(rows,permutations=59)
        total=out["same_official_race_distance_and_exact_first_GPS_marker"][
            "status_by_rider_pair_condition"]["switched"]["within_horse_cross_date_pairs"]
        strict=out["also_same_original_race_Class"][
            "status_by_rider_pair_condition"]["switched"]["within_horse_cross_date_pairs"]
        self.assertGreater(total,strict)
        self.assertTrue(out["also_same_original_race_Class"][
            "original_source_class_also_matched"])

    def test_invalid_source_jockey_ids_do_not_get_imputed_from_names(self):
        rows=synthetic_races()
        for row in rows:
            row["jockey_license_id"]="0" if row["day"]<"2026-05-01" else "invalid"
        out=analyze(rows,permutations=59)
        s=out["same_official_race_distance_and_exact_first_GPS_marker"][
            "status_by_rider_pair_condition"]["switched"]
        self.assertEqual(s["within_horse_cross_date_pairs"],0)
        self.assertEqual(out["source_coverage"][
            "source_rows_with_valid_original_Jockey_Id"],0)
        self.assertNotIn("equal_horse_stratum_mean_pair_product_seconds_squared",s)

    def test_same_trainer_screen_requires_documented_original_id(self):
        no_trainer=analyze(synthetic_races(trainer_documented=False),permutations=59)
        broad=no_trainer["same_official_race_distance_and_exact_first_GPS_marker"][
            "status_by_rider_pair_condition"]
        self.assertGreater(broad["switched"]["within_horse_cross_date_pairs"],0)
        self.assertEqual(
            broad["switched_same_trainer"]["within_horse_cross_date_pairs"],0)
        self.assertEqual(broad["switched_same_trainer"]["status"],
                         "HOLD_INSUFFICIENT_WITHIN_ID_CROSS_DATE_RIDER_PAIR_SUPPORT")

    def test_numerical_pair_held_below_twenty_horse_support(self):
        rows=synthetic_races(horses=16)
        out=analyze(rows,permutations=59)
        s=out["same_official_race_distance_and_exact_first_GPS_marker"][
            "status_by_rider_pair_condition"]["switched"]
        self.assertEqual(s["distinct_official_HORSES_IDs"],16)
        self.assertEqual(s["status"],
                         "HOLD_INSUFFICIENT_WITHIN_ID_CROSS_DATE_RIDER_PAIR_SUPPORT")
        self.assertNotIn("equal_horse_stratum_mean_pair_product_seconds_squared",s)

    def test_id_name_conflict_fails_closed(self):
        rows=synthetic_races()
        target=rows[-1]
        target["horse_name"]="CONFLICT-NEW-NAME"
        with self.assertRaisesRegex(ValueError,"HOLD_HORSES_ID_NAME_CONSISTENCY"):
            analyze(rows,permutations=59)

    def test_duplicate_source_horse_and_day_fails_closed(self):
        rows=synthetic_races()
        rows.append(copy.deepcopy(rows[0]))
        with self.assertRaisesRegex(ValueError,"HOLD_SAME_HORSES_ID_REPEATED_WITHIN_DATE"):
            analyze(rows,permutations=59)

    def test_shuffling_rider_metadata_is_not_the_reference(self):
        timed,_=source_timed_panel(synthetic_races())
        report=rider_label_shuffled_time_reference(timed,permutations=59)
        self.assertTrue(report["not_randomized_jockey_assignment"])
        self.assertTrue(report["not_causal_or_preregistered_significance"])
        self.assertGreater(report["reference_iterations"],50)

    def test_90_day_gap_is_fixed_and_descriptive_not_inferred_slope(self):
        self.assertEqual(GAP_CUTOFF_DAYS,90)
        timed,_=source_timed_panel(synthetic_races())
        pairs=pair_records(timed,strict_class=False)
        short=summarize_pairs(pairs,"switched_gap_at_most_90d")
        long=summarize_pairs(pairs,"switched_gap_over_90d")
        self.assertGreater(short["within_horse_cross_date_pairs"],0)
        self.assertGreater(long["within_horse_cross_date_pairs"],0)
        self.assertTrue(short["no_original_horse_rider_trainer_identifiers_exported"])


if __name__=="__main__":
    unittest.main()
