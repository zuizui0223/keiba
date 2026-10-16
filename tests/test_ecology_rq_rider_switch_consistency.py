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


    def test_source_date_and_going_rider_coverage_is_aggregate_only(self):
        timed,coverage=source_timed_panel(synthetic_races())
        self.assertEqual(len(timed),320)
        dates=coverage["numeric_Jockey_ID_coverage_by_original_meeting_date"]
        self.assertEqual(len(dates),10)
        self.assertTrue(all(x["GPS_records"]==32 for x in dates.values()))
        self.assertTrue(all(x["with_numeric_Jockey_ID"]==32 for x in dates.values()))
        self.assertTrue(all(x["observed_source_coverage_fraction"]==1.
                            for x in dates.values()))
        self.assertEqual(sum(x["GPS_records"] for x in coverage[
            "numeric_Jockey_ID_coverage_by_official_source_going"].values()),320)
        self.assertTrue(coverage[
            "coverage_is_conditional_on_positive_GPS_not_all_actual_starters"])
        dumped=json.dumps(coverage)
        self.assertNotIn("INVENTED-HORSE",dumped)
        self.assertNotIn("FAKE-NAME",dumped)

    def test_positive_planted_horse_repeatability_survives_every_source_date_drop(self):
        result=analyze(synthetic_races(),permutations=59)
        influence=result[
            "post_hoc_leave_one_original_meeting_and_anonymous_animal_influence"]
        self.assertEqual(influence["status"],
                         "POST_HOC_SOURCE_CONDITIONAL_INFLUENCE_DIAGNOSTIC_ONLY")
        date_a=influence["date_deletion"]
        self.assertEqual(date_a["number_of_deletions_attempted"],10)
        self.assertEqual(date_a["refits_on_HOLD"],0)
        self.assertEqual(date_a["positive_refits"],10)
        self.assertGreater(date_a["minimum_refitted_pair_product_seconds_squared"],0)
        self.assertTrue(date_a["not_a_confidence_interval_or_p_value"])
        self.assertEqual(len(date_a["source_date_keyed_anonymous_support"]),10)
        identity=influence["horse_ID_deletion_ANON_AGGREGATES_ONLY"]
        self.assertEqual(identity["number_of_deletions_attempted"],32)
        self.assertEqual(identity["numeric_refits_meeting_original_support_gate"],32)
        self.assertEqual(identity["positive_refits"],32)
        self.assertGreater(identity["minimum_refitted_pair_product_seconds_squared"],0)
        self.assertTrue(influence[
            "same_GPS_peer_reference_kept_fixed_after_horse_deletion"])
        self.assertTrue(identity[
            "only_aggregate_deletion_range_not_any_original_HORSES_ID"])
        dumped=json.dumps(influence)
        for forbidden in ("INVENTED-HORSE","FAKE-NAME","FICTIONAL Class",
                          '"jockey_id"','"trainer_id"'):
            self.assertNotIn(forbidden,dumped)

    def test_influence_drops_below_support_not_interpreted_as_zero(self):
        rows=synthetic_races(horses=32,days=10)
        days=sorted({r["day"] for r in rows})
        for r in rows:
            index=int(r["horse_id"].rsplit("-",1)[1])
            dayindex=days.index(r["day"])
            if index<22:
                if dayindex not in (0,1):
                    r["jockey_license_id"]=None
                else:
                    r["jockey_license_id"]=str(20000+index*10+dayindex)
            else:
                if dayindex<2:
                    r["jockey_license_id"]=None
        result=analyze(rows,permutations=59)
        influence=result[
            "post_hoc_leave_one_original_meeting_and_anonymous_animal_influence"]
        self.assertEqual(influence["status"],
                         "POST_HOC_SOURCE_CONDITIONAL_INFLUENCE_DIAGNOSTIC_ONLY")
        by_date=influence["date_deletion"]
        self.assertEqual(by_date["status"],
                         "HOLD_AT_LEAST_ONE_DELETION_INSUFFICIENT_SUPPORT")
        self.assertGreaterEqual(by_date["refits_on_HOLD"],2)
        self.assertNotIn("minimum_refitted_pair_product_seconds_squared",by_date)
        self.assertNotIn("maximum_refitted_pair_product_seconds_squared",by_date)
        day0=by_date["source_date_keyed_anonymous_support"][days[0]]
        self.assertEqual(day0["status"],
                         "HOLD_INSUFFICIENT_WITHIN_ID_CROSS_DATE_RIDER_PAIR_SUPPORT")
        self.assertNotIn("mean_pair_product_seconds_squared",day0)
        self.assertGreater(by_date["numeric_refits_meeting_original_support_gate"],0)

    def test_when_main_rider_pair_support_fails_influence_fails_closed(self):
        result=analyze(synthetic_races(horses=16),permutations=59)
        influence=result[
            "post_hoc_leave_one_original_meeting_and_anonymous_animal_influence"]
        self.assertEqual(influence["status"],
                         "HOLD_PRIMARY_SWITCHED_RIDER_PAIR_SUPPORT_INSUFFICIENT")
        self.assertNotIn("date_deletion",influence)
        self.assertNotIn("horse_ID_deletion_ANON_AGGREGATES_ONLY",influence)
        self.assertTrue(influence["not_a_confidence_interval_or_independent_cohort"])

    def test_source_HTTP_error_diagnostics_expose_only_status_not_URL(self):
        from urllib.error import HTTPError
        from ecology_rq_rider_switch_consistency import safe_original_source_error_category
        example=HTTPError("https://example.invalid/?id=SECRET-FAKE-HORSE",
                          429,"SECRET-RESPONSE-TEXT",None,None)
        result=safe_original_source_error_category(example)
        self.assertEqual(result["source_error_http_status_if_available"],429)
        self.assertTrue(result["source_http_rate_limited_429"])
        self.assertFalse(result["source_http_upstream_5xx"])
        self.assertNotIn("SECRET",json.dumps(result))
        self.assertTrue(result["source_unavailable_is_not_zero_animal_response"])
        server=safe_original_source_error_category(HTTPError(
            "https://example.invalid/?id=SECRET",503,"",None,None))
        self.assertTrue(server["source_http_upstream_5xx"])
        self.assertFalse(server["source_http_rate_limited_429"])
        timeout=safe_original_source_error_category(TimeoutError("SECRET URL"))
        self.assertIsNone(timeout["source_error_http_status_if_available"])



if __name__=="__main__":
    unittest.main()
