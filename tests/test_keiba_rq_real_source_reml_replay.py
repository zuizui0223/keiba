"""Fictitious source-wide 12-date RQ replay tests, never real identifiers.

The scientific source retrieval test runs separately in its dedicated
GitHub workflow. The tests are 24 fabricated horses on the SAME 12
source-preselected days, not selected by eventual result.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

try:
    import numpy as np
except ModuleNotFoundError as exc:
    if exc.name!="numpy": raise
    np=None

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
HAS_PINNED_MAIN=False
if np is not None:
    try:
        from keiba_rq_real_source_reml_replay import (
            replay,_fit_new_reml,_frozen_fingerprints,SCHEMA,
            SOURCE_STATUS,COHORT,
            _previously_locked_out_of_date_horse_vs_other_horse)
        HAS_PINNED_MAIN=True
    except ModuleNotFoundError as exc:
        if exc.name not in {
            "ecology_rq_2026_calendar_overlap",
            "ecology_rq_cross_venue_identity_support",
            "ecology_rq_eagle_farm_external_icc",
            "ecology_rq_early_pace_repeatability",
            "ecology_rq_race_fixed_icc",
            "ecology_rq_single_race_id_probe",
            "ecology_rq_thoroughbred_sectional_audit",
            "ecology_rq_multigoing_h1_preflight",
            "ecology_rq_covariate_icc",
            "ecology_rq_official_id_crosswalk",
        }:raise

def fictional_cohort():
    days=list(COHORT)
    horses=[f"FABHORSE-{i:02d}" for i in range(24)]
    records=[]
    manifest={}
    baseline={"schema":"racing-queensland-original-horse-source-fingerprint-v1",
              "per_date":{}}
    for ind,day in enumerate(days):
        for i,h in enumerate(horses):
            value=(10.0+.03*ind+.49*math.sin(.37*i)
                  +.065*math.cos(.91*i+1.33*ind))
            records.append({
                "horse_id":h, "horse_name":f"FABRICATED_{i:02d}",
                "day":day, "race_number":4,
                "distance":"1400", "first_marker_m":150.,
                "first_section_sec":value, "class":"TOY_OPEN",
                "ground":"Good"})
        original={
          "verified_positive_first_GPS_HORSES_ID_matches":24,
          "meeting_XML_SHA256":"1"*64,
          "race_XML_SHA256":"2"*64,
          "gps_CSV_SHA256":"3"*64,
          "combined_original_GetHorsesForRace_roster_SHA256":"4"*64,
          "number_of_original_HORSES_roster_responses_hashed":1
        }
        baseline["per_date"][day]=original
        manifest[day]={
          "status":SOURCE_STATUS,"positive_first_GPS_candidates":24,
          "original_source_SHA256_only":{
            "meeting_xml_sha256":"1"*64,
            "race_xml_sha256":"2"*64,
            "gps_csv_sha256":"3"*64,
          },
          "original_horse_roster_sha256_combined":"4"*64,
          "original_horse_roster_response_count":1
        }
    return records,manifest,baseline


@unittest.skipUnless(HAS_PINNED_MAIN,
                     "Source-pinned original ecology modules required; dedicated real-source CI loads them")
class RealSourceREMLReplaySyntheticUnitTests(unittest.TestCase):
    def test_independent_24_horse_real_method_12day_replay_produces_valid_anonymous_numbers(self):
        rows,manifest,baseline=fictional_cohort()
        result=replay(reader=lambda:(rows,manifest),baseline=baseline)
        self.assertEqual(result["schema"],SCHEMA)
        self.assertEqual(
            result["status"],
            "SYNTHETIC_FIXTURE_NUMERIC_METHOD_REPLAY_NOT_REAL_HORSE_DATA")
        self.assertEqual(result["original_calendar_date_count"],12)
        self.assertTrue(result["source_collector_is_injected_test_fixture"])
        self.assertNotIn("OBSERVED_REAL",result["status"])
        self.assertEqual(
            result["original_20261014_source_component_match"]
            ["fully_matched_dates"],12)
        self.assertLess(
            result["independent_algorithm_absolute_numerical_differences"]
            ["conditional_icc_abs_difference"],1e-5)
        self.assertEqual(
            result["new_same_original_horse_race_source"]
            ["original_meeting_dates"],12)
        self.assertTrue(result["did_NOT_use_actual_future_target_prices_or_race_finishes"])
        forward=result[
          "same_original_20261014_design_horse_vs_other_history_on_current_source"]
        self.assertTrue(forward["same_locked_old_shrinkage_n_over_n_plus_2"])
        self.assertTrue(forward["no_animal_IDs_or_records_exported"])
        self.assertEqual(forward["source_timed_rows"],288)
        marker=result["prelocked_marker_specific_source_icc_sensitivity"]
        self.assertEqual(marker["marker_selection_m"],[150,250])
        self.assertEqual(
            marker["results"]["150"]["status"],
            "EXPLORATORY_FIXED_MARKER_OBSERVED_SOURCE_VERSION")
        self.assertEqual(
            marker["results"]["150"]["source_rows_in_min_four_eligible_races"],288)
        self.assertEqual(
            marker["results"]["250"]["status"],
            "HOLD_NO_SOURCE_GPS_ROWS_AT_LOCKED_MARKER")
        self.assertNotIn(
            "conditional_icc_current_source_only",marker["results"]["250"])
        output=json.dumps(result)
        self.assertNotIn("FABHORSE-",output)
        self.assertNotIn("FABRICATED_",output)
        self.assertNotIn('"first_section_sec"',output)
        self.assertGreater(
            result["new_same_original_horse_race_source"]
            ["conditional_icc_point"],0)
        absolute=result[
            "original_absolute_first_GPS_timing_frozen_cohort_out_of_date_comparison"]
        self.assertEqual(
            set(absolute),{"same_distance_and_GPS_marker",
                           "additionally_same_original_class"})
        self.assertTrue(all(
            d["status"]=="HOLD_ORIGINAL_HORSE_HISTORY_EVIDENCE_GATE"
            for d in absolute.values()))
        nulls=result[
            "within_race_history_identity_shuffle_source_conditional_null"]
        self.assertEqual(
            set(nulls),
            {"same_distance_and_GPS_marker",
             "additionally_same_original_class"})
        # The basic 24-horse input has no verified source-declared
        # jockey IDs; original eligibility correctly cannot construct
        # the candidate set, and neither can the permutation null.
        self.assertTrue(all(
            n["status"]=="HOLD_ORIGINAL_CONTEXT_DID_NOT_PASS_EVIDENCE_GATE"
            for n in nulls.values()))
        deletion=result["original_source_date_deletion_sensitivity"]
        self.assertEqual(deletion["original_dates_deletion_attempted"],12)
        self.assertEqual(
            deletion["successful_reml_delete_one_original_source_date"]+
            deletion["source_dates_with_variance_hold"],12)
        self.assertTrue(
            deletion["not_a_jackknife_95pct_CI_or_a_preregistered_replication"])
        if deletion["successful_reml_delete_one_original_source_date"]:
            self.assertLessEqual(deletion["minimum_source_deleted_ICC"],
                                 deletion["maximum_source_deleted_ICC"])
        else:
            self.assertIsNone(deletion["minimum_source_deleted_ICC"])
            self.assertIsNone(deletion["maximum_source_deleted_ICC"])
            self.assertEqual(deletion["status"],
                             "HOLD_INSUFFICIENT_DATE_DELETE_VARIANCE_FITS")

    def test_omitted_locked_date_returns_HOLD_not_11day_optimistic_ICC(self):
        rows,manifest,baseline=fictional_cohort()
        day=list(COHORT)[-1]
        manifest[day]["status"]="HOLD_UPSTREAM_NOT_AVAILABLE"
        result=replay(reader=lambda:(rows,manifest),baseline=baseline)
        self.assertEqual(result["status"],
          "HOLD_INCOMPLETE_ORIGINAL_12DATE_LIVE_RQ_COHORT")
        self.assertNotIn("new_same_original_horse_race_source",result)
        self.assertEqual(result["current_source_dates_HOLD"],[day])

    def test_source_roster_or_GPS_SHA_drift_blocks_old_20261014_repro_claim(self):
        rows,manifest,baseline=fictional_cohort()
        manifest[list(COHORT)[0]]["original_horse_roster_sha256_combined"]="f"*64
        result=replay(reader=lambda:(rows,manifest),baseline=baseline)
        self.assertEqual(result["status"],
          "SYNTHETIC_FIXTURE_SOURCE_EDITION_CHANGED_HOLD")
        self.assertEqual(
            result["original_20261014_source_component_match"]
            ["fully_matched_dates"],11)
        self.assertFalse(result["source_fingerprints_unchanged_since_20261014"])
        self.assertTrue(
            result["original_20261014_source_component_match"]
            ["components_by_original_date"][list(COHORT)[0]]
            ["comparison_to_frozen_source"]["original_horse_roster"] is False)

    def test_mathematical_model_invariant_to_same_day_common_time_offset(self):
        rows,_,_=fictional_cohort()
        old=_fit_new_reml(rows)
        updated=deepcopy(rows)
        dates={day:i for i,day in enumerate(COHORT)}
        for r in updated:
            r["first_section_sec"]+=.17*dates[r["day"]]
        new=_fit_new_reml(updated)
        for field in ("horse_variance_seconds_squared",
                      "independent_noise_variance_seconds_squared",
                      "conditional_icc_point"):
            self.assertAlmostEqual(old[field],new[field],places=6)

    def test_incomplete_eligibility_returns_explicit_hold(self):
        rows,_,_=fictional_cohort()
        subset=[r for r in rows if r["day"]==list(COHORT)[0]]
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_REAL_REML_ELIGIBILITY"):
            _fit_new_reml(subset)
        # Same horse source self-consistency validator rejects repeat
        # within the same race and same source day.
        original=deepcopy(rows)
        original.append(original[0].copy())
        with self.assertRaises(ValueError):
            _fit_new_reml(original)

    def test_broken_baseline_source_record_cannot_claim_replay(self):
        rows,manifest,baseline=fictional_cohort()
        baseline["per_date"].pop(list(COHORT)[0])
        with self.assertRaises(ValueError):
            replay(reader=lambda:(rows,manifest),baseline=baseline)


    def test_previous_locked_own_vs_other_horse_history_on_fabricated_12days(self):
        rows,manifest,baseline=fictional_cohort()
        date_order={day:index for index,day in enumerate(COHORT)}
        for row in rows:
            idx=int(row["horse_id"].split("-")[1])
            row["jockey_license_id"]=str(5000+date_order[row["day"]])
            row["trainer_license_id"]=str(6000+idx%3)
        result=replay(reader=lambda:(rows,manifest),baseline=baseline)
        self.assertEqual(result["status"],
                         "SYNTHETIC_FIXTURE_NUMERIC_METHOD_REPLAY_NOT_REAL_HORSE_DATA")
        old=result[
          "same_original_20261014_design_horse_vs_other_history_on_current_source"]
        broad=old["contexts"]["same_official_distance_and_exact_GPS_marker"]
        a=broad["historical_other_horses_same_context"]
        self.assertEqual(a["status"],
                         "EXPLORATORY_IDENTICAL_FUTURE_HORSES_ROLE_CONTEXT_COMPARISON_ONLY")
        self.assertEqual(a["distinct_original_HORSES_IDs"],24)
        self.assertEqual(a["matched_chronological_future_source_rows"],264)
        self.assertEqual(a["distinct_future_original_source_dates"],11)
        self.assertTrue(a["same_future_rows_for_each_compared_predictor"])
        self.assertGreater(a["past_other_horse_minus_focal_horse_RMSE_sec"],0)
        safe=json.dumps(old,ensure_ascii=False)
        self.assertNotIn("FABHORSE-",safe)
        self.assertNotIn("FABRICATED_",safe)
        self.assertNotIn('"jockey_license_id"',safe)
        self.assertTrue(old["not_absolute_horse_speed_or_prestart_market_prediction"])


if __name__=="__main__":unittest.main()
