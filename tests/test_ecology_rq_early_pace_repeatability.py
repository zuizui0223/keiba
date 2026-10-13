"""No actual race records: testing within-race early-pacing repeatability logic."""
import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_early_pace_repeatability import (
    prepare, pairs, randomization_reference, heldout_early_pace, analyze
)


def invented(n_dates=12, class_change=False, random_per_date=False, seed=514):
    rng=random.Random(seed)
    output=[]
    for day in range(n_dates):
        d=f"2026-{1+day//28:02d}-{1+day%28:02d}"
        for race in (1,2):
            shifts=[.09*i for i in range(6)]
            if random_per_date:
                rng.shuffle(shifts)
            for index in range(6):
                hid=f"FABRICATED-HORSE-{race}-{index}"
                sec=9.6+shifts[index]+.01*(day%3)
                output.append({
                    "horse_id":hid,
                    "horse_name":f"Invented Name {race} {index}",
                    "day":d,
                    "race_number":race,
                    "distance":"950 metres",
                    "first_marker_m":150.,
                    "first_section_sec":sec,
                    "class":"Class A" if not class_change or day<6 else "Class B",
                })
    return output


class RepeatabilityTests(unittest.TestCase):
    def test_stable_early_pace_relative_to_own_race_peers_is_detectable(self):
        frame,quality=prepare(invented())
        self.assertEqual(len(frame),144)
        self.assertEqual(quality["races_with_at_least_4_positive_first_intervals"],24)
        self.assertEqual(quality["positive_first_section_rows_retained"],144)
        p=pairs(frame,strict_class=False)
        self.assertEqual(p["horse_IDs_with_at_least_2_different_date_measurements_same_distance_marker_and_optional_class"],12)
        self.assertEqual(p["different_date_observation_pairs"],12*66)
        self.assertGreater(p["equal_stratum_weighted_pair_product_seconds_squared"],0)
        empirical=randomization_reference(frame,strict_class=False,
                                          permutations=99,seed=123)
        self.assertEqual(empirical["status"],"EXPLORATORY_IDENTITY_PERMUTATION_REFERENCE_ONLY")
        self.assertLess(empirical["fraction_null_at_least_observed"],.05)
        self.assertFalse(empirical["permutation_reference_is_causal_or_preregistered"])
        report=heldout_early_pace(frame,strict_class=False)
        self.assertEqual(report["status"],"EXPLORATORY_PAST_ID_PROFILE_RELATIVE_EARLY_PACE_HELDOUT")
        self.assertGreater(report["RMSE_gain_sec_positive_means_persistent_identity_predicts_better"],0)
        self.assertTrue(report["target_uses_contemporaneous_other_timed_runners_after_race"])
        self.assertTrue(report["not_a_real_time_prediction_or_causal_inference"])

    def test_race_class_matching_can_eliminate_between_class_persistence(self):
        frame,_=prepare(invented(class_change=True))
        p=pairs(frame,strict_class=True)
        self.assertEqual(p["repeated_horse_by_course_strata"],24)
        cross=heldout_early_pace(frame,strict_class=True)
        # Heldout from Class B with >1 earlier Class B visits;
        # within-period corroboration is not a contrast of A vs B.
        self.assertTrue(cross["train_date_end"]<cross["heldout_date_start"])
        x=analyze(invented(class_change=True),permutations=79)
        self.assertEqual(x["status"],"REAL_EQUINE_EARLY_PACE_REPRODUCIBILITY_EXPLORATORY_NOT_H1_H2")
        self.assertFalse(x["independent_real_horse_effect_supported_H1"])
        self.assertFalse(x["independent_real_horse_effect_supported_H2"])
        self.assertTrue(x["not_yet_standard_ICC_or_random_slope_variance"])

    def test_no_trait_consistency_is_not_an_ecological_claim(self):
        null=invented(random_per_date=True)
        data=analyze(null,permutations=99)
        self.assertEqual(data["status"],"REAL_EQUINE_EARLY_PACE_REPRODUCIBILITY_EXPLORATORY_NOT_H1_H2")
        self.assertFalse(data["independent_real_horse_effect_supported_H1"])

    def test_inconsistent_same_race_marker_rejected(self):
        rows=invented()
        rows[0]["first_marker_m"]=250.
        with self.assertRaisesRegex(ValueError,"HOLD_INCONSISTENT_FIRST_SECTION_MARKER"):
            prepare(rows)

    def test_multiple_races_same_horse_same_day_rejected(self):
        rows=invented()
        rows[6]["horse_id"]=rows[0]["horse_id"]
        with self.assertRaisesRegex(ValueError,"HOLD_SAME_HORSES_ID_REPEATED_WITHIN_DATE"):
            prepare(rows)

    def test_inconsistent_biological_identity_and_source_missingness_block(self):
        rows=invented()
        rows[0]["horse_name"]="not the same horse"
        with self.assertRaisesRegex(ValueError,"HOLD_HORSES_ID_NAME_CHANGED"):
            analyze(rows,permutations=79)
        rows=invented()
        rows[0]["first_section_sec"]=0
        with self.assertRaisesRegex(ValueError,"HOLD_FIRST_SECTION_UNAVAILABLE"):
            prepare(rows)

    def test_small_observed_race_does_not_claim_source_roster_complete(self):
        all_rows=invented()
        keep=[r for r in all_rows if r["horse_id"] in {
            "FABRICATED-HORSE-1-0","FABRICATED-HORSE-1-1"
        }]
        rows,info=prepare(keep)
        self.assertEqual(len(rows),0)
        self.assertFalse(info["complete_verified_official_starter_rosters"])
        result=analyze(keep,permutations=79)
        self.assertIn("HOLD",result["status"])


if __name__=="__main__":
    unittest.main()
