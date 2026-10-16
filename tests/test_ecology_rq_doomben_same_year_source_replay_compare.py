"""Synthetic source-only Doomben rerun availability and provenance audit tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_doomben_2025_marker_extension import (
    LOCKED_DATES,DATES_2025,PREVIOUS_2026_DATES
)
from ecology_rq_doomben_same_year_source_replay_compare import (
    compare,SOURCE_FIELDS,NUMERIC_OK,HOLD,
)


def invented_source_report(missing=None):
    missing=set(missing or ())
    status={}
    for day in LOCKED_DATES:
        if day in missing:
            status[day]={
                "status":"HOLD_DATE_SOURCE_NOT_RECONCILED",
                "error_code":"HOLD_INCOMPLETE_OR_TRUNCATED_OFFICIAL_HTTP_RESPONSE",
                "not_counted_as_zero_participation":True,
            }
        else:
            status[day]={
                "status":"OFFICIAL_2025_OR_2026_DOOMBEN_SOURCE_ID_GPS_AUDITED",
                "original_first_party_meeting_race_GPS_source_SHA256":{
                    "meeting_xml_sha256":"a"*64,
                    "race_xml_sha256":"b"*64,
                    "gps_csv_sha256":"c"*64,
                },
                "original_horse_roster_combined_SHA256":"d"*64,
                "original_horse_roster_response_count":6,
                "original_positive_first_GPS_HORSES_ID_rows":23,
                "numeric_race_IDs_returned":6,
                "original_race_numbers_requested":[1,2,3,4,5,6],
            }
    cells={}
    for year in (2025,2026):
        for marker in (150,200):
            for stricter in (False,True):
                key=f"{year}_{marker}m_same_distance"+(
                    "_and_Class" if stricter else "")
                cells[key]={
                    "status":HOLD,
                    "comparison_population":{
                        "scored_anonymous_distinct_original_HORSES_IDs":9,
                        "scored_anonymous_original_future_rows":11,
                    },
                }
    return {
        "original_source_calendar":{
            "fixed_2025_date_count":len(DATES_2025),
            "fixed_2026_date_count":len(PREVIOUS_2026_DATES),
            "original_locked_source_dates_successful":len(LOCKED_DATES)-len(missing),
            "original_source_HOLD_dates":sorted(missing),
        },
        "source_manifest":status,
        "comparisons_by_year_marker_context":cells,
        "no_individual_horse_names_IDs_role_IDs_section_times_or_predictions_exported":True,
    }


def give_supported_year_profile(r,*,num_id=21,num_rows=21):
    s=r["comparisons_by_year_marker_context"]["2025_150m_same_distance"]
    s["status"]=NUMERIC_OK
    s["comparison_population"]={
        "scored_anonymous_distinct_original_HORSES_IDs":num_id,
        "scored_anonymous_original_future_rows":num_rows,
    }
    s["equal_horse_RMSE_seconds"]={
        "zero":.24,"own":.21,
        "other_horses_same_marker_and_distance":.245,
        "OTHER_minus_OWN_positive_horse_history_better":.035,
    }


class SameYearOriginalSourceReplayAudit(unittest.TestCase):
    def test_two_identical_complete_source_runs_do_not_generate_false_change(self):
        a=invented_source_report()
        z=compare(a,copy.deepcopy(a),a_sha256="a"*64,b_sha256="b"*64)
        self.assertEqual(z["status"],
            "SOURCE_RUNS_AGREE_ON_AVAILABLE_SCIENTIFIC_NUMERIC_GATES_ONLY")
        self.assertEqual(z["shared_original_source_success_dates"],42)
        self.assertEqual(z[
            "shared_success_source_component_equality_counts"][
            "original_horse_roster_combined_SHA256"],42)
        self.assertEqual(z["dates_only_runA_read_successfully"],[])
        self.assertEqual(z["dates_only_runB_read_successfully"],[])

    def test_opposite_source_unavailability_breaks_numeric_replication(self):
        shared_fail=["2025-01-22","2025-05-28","2025-08-27","2026-08-26"]
        a=invented_source_report(shared_fail+["2025-07-12"])
        b=invented_source_report(shared_fail+["2025-03-19"])
        give_supported_year_profile(a)
        b["comparisons_by_year_marker_context"][
            "2025_150m_same_distance"]["comparison_population"]={
                "scored_anonymous_distinct_original_HORSES_IDs":17,
                "scored_anonymous_original_future_rows":18,
            }
        z=compare(a,b,a_sha256="a"*64,b_sha256="b"*64)
        self.assertEqual(z["status"],
            "HOLD_DOOMBEN_WITHIN_YEAR_SCORE_NOT_ROBUST_TO_SOURCE_AVAILABILITY")
        self.assertEqual(z["shared_original_source_success_dates"],36)
        self.assertEqual(z["dates_only_runA_read_successfully"],["2025-03-19"])
        self.assertEqual(z["dates_only_runB_read_successfully"],["2025-07-12"])
        self.assertEqual(z[
            "shared_success_source_component_equality_counts"][
            "original_horse_roster_combined_SHA256"],36)
        comparison=z["original_year_marker_class_context_gate_sensitivity"][
            "2025_150m_same_distance"]
        self.assertEqual(comparison["runA_original_HORSES_IDs"],21)
        self.assertEqual(comparison["runB_original_HORSES_IDs"],17)
        self.assertIsNone(comparison["runB_numeric_GAIN_if_supported"])
        self.assertFalse(comparison[
            "same_source_population_supported_across_two_runs"])
        dump=json.dumps(z)
        for forbidden in ("FAKE-HORSE","REAL-RUNNER",
                          '"horse_name":','"horse_id":','"individual_GPS_time":'):
            self.assertNotIn(forbidden,dump)

    def test_shared_source_roster_drift_is_detected_not_named_biology(self):
        a=invented_source_report()
        b=copy.deepcopy(a)
        target="2025-07-12"
        b["source_manifest"][target]["original_horse_roster_combined_SHA256"]="e"*64
        z=compare(a,b,a_sha256="a"*64,b_sha256="b"*64)
        self.assertEqual(z["status"],
                         "HOLD_DOOMBEN_WITHIN_YEAR_SCORE_NOT_ROBUST_TO_SOURCE_AVAILABILITY")
        self.assertIn(target,z["shared_dates_with_changed_original_source_fingerprints_or_counts"])
        self.assertEqual(z["shared_success_source_component_equality_counts"][
            "original_horse_roster_combined_SHA256"],41)

    def test_missing_source_date_count_rejected_not_imputed(self):
        a=invented_source_report()
        a["source_manifest"].pop("2026-10-05")
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_MATCHING_ORIGINAL_SOURCE"):
            compare(a,invented_source_report(),a_sha256="a"*64,b_sha256="b"*64)

    def test_unsupported_horse_profile_numeric_gain_is_rejected(self):
        a=invented_source_report()
        b=copy.deepcopy(a)
        a["comparisons_by_year_marker_context"][
            "2025_150m_same_distance"]["equal_horse_RMSE_seconds"]={"own":.02}
        with self.assertRaisesRegex(ValueError,"HOLD_EMITTED_UNSUPPORTED"):
            compare(a,b,a_sha256="a"*64,b_sha256="b"*64)

    def test_false_supported_model_with_seventeen_horses_rejected(self):
        a=invented_source_report()
        b=copy.deepcopy(a)
        give_supported_year_profile(a,num_id=17)
        with self.assertRaisesRegex(ValueError,"HOLD_NUMERIC_SCORE_WITHOUT"):
            compare(a,b,a_sha256="a"*64,b_sha256="b"*64)

    def test_pinned_public_aggregate_keeps_both_real_source_gate_states(self):
        evidence_path=Path(__file__).resolve().parents[1]/"docs"/"evidence"/(
            "rq-doomben-same-year-rerun-availability-20261015.json")
        real=json.loads(evidence_path.read_text(encoding="utf-8"))
        runA,runB=real["replays"]
        self.assertEqual(runA["github_run_id"],38696624349)
        self.assertEqual(runB["github_run_id"],38696711022)
        self.assertEqual(runA["within_2025_first_150m_same_distance"][
            "distinct_horse_ids"],21)
        self.assertEqual(runB["within_2025_first_150m_same_distance"][
            "distinct_horse_ids"],17)
        self.assertEqual(runA["within_2025_first_150m_same_distance"]["status"],NUMERIC_OK)
        self.assertEqual(runB["within_2025_first_150m_same_distance"]["status"],HOLD)
        self.assertIsNone(runB["within_2025_first_150m_same_distance"][
            "other_minus_own_seconds"])
        self.assertAlmostEqual(runA["within_2025_first_150m_same_distance"][
            "RMSE_seconds"]["other"]-runA["within_2025_first_150m_same_distance"][
            "RMSE_seconds"]["own"],
            runA["within_2025_first_150m_same_distance"][
                "other_minus_own_seconds"],places=12)
        self.assertEqual(real["same_date_source_comparability"][
            "both_successful_original_dates"],36)
        self.assertEqual(real["source_available_and_scientific_hold"]["status"],
            "HOLD_DOOMBEN_WITHIN_YEAR_SCORE_NOT_ROBUST_TO_SOURCE_AVAILABILITY")
        self.assertTrue(real["source_available_and_scientific_hold"][
            "single_successful_numeric_estimate_cannot_be_called_replicated"])
        public=json.dumps(real)
        self.assertNotIn('"horse_name":',public)
        self.assertNotIn('"horse_id":',public)
        self.assertNotIn('"jockey_license_id":',public)
        self.assertNotIn('"first_section_sec":',public)

    def test_two_source_complete_real_reruns_same_23_horses_and_24_future_rows(self):
        pinned=Path(__file__).resolve().parents[1]/"docs"/"evidence"/(
            "rq-doomben-same-year-rerun-availability-20261015.json")
        r=json.loads(pinned.read_text(encoding="utf-8"))
        complete=r["source_complete_matched_replays"]
        one,two=complete["source_replay_C"],complete["source_replay_D"]
        self.assertEqual(one["github_run_id"],38697565949)
        self.assertEqual(two["github_run_id"],38697629972)
        self.assertEqual(one["original_source_dates_successful"],38)
        self.assertEqual(two["original_source_dates_successful"],38)
        self.assertEqual(one["anonymized_aggregate_sha256"],
                         two["anonymized_aggregate_sha256"])
        self.assertTrue(complete["all_38_successful_original_source_manifest_entries_equal"])
        self.assertTrue(complete["all_8_scoring_comparison_aggregates_equal"])
        primary=complete["within_year_2025_150m_same_distance"]
        self.assertEqual(primary["status"],NUMERIC_OK)
        self.assertEqual(primary["distinct_horse_ids"],23)
        self.assertEqual(primary["future_rows"],24)
        self.assertAlmostEqual(
            primary["equal_horse_RMSE_seconds"]["other"]-
            primary["equal_horse_RMSE_seconds"]["own"],
            primary["OTHER_minus_OWN_gain_seconds"],places=12)
        self.assertTrue(primary["OTHER_minus_OWN_gain_seconds"]>0)
        limits=complete["scientific_interpretation"]
        self.assertFalse(limits["independent_animal_population_or_experiment"])
        self.assertFalse(limits["source_availability_invariant_under_all_reruns"])
        self.assertFalse(limits["stable_intrinsic_personality_or_yearly_decay_identified"])

    def test_shared_source_incomplete_digest_cannot_be_called_equal(self):
        a=invented_source_report()
        b=copy.deepcopy(a)
        a["source_manifest"]["2025-07-12"][
            "original_first_party_meeting_race_GPS_source_SHA256"].pop("gps_csv_sha256")
        with self.assertRaisesRegex(ValueError,"HOLD_INCOMPLETE_ORIGINAL_SOURCE_HASHES"):
            compare(a,b,a_sha256="a"*64,b_sha256="b"*64)


if __name__=="__main__":
    unittest.main()
