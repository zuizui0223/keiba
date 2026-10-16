"""Synthetic-only tests for source-conditional chronological horse profile scores."""
from __future__ import annotations

import copy
from datetime import date,timedelta
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_rq_rider_forward_check import (
    analyze_forward, forward_records, summarize_forward,
)
from ecology_rq_rider_switch_consistency import source_timed_panel


def fake_races(*,horses=32,days=10,seed=20261014,effects=True):
    """Fictitious horses and source-nominated riders, no official horse data."""
    rng=random.Random(seed)
    original=[f"FAKE-HORSE-{i:03d}" for i in range(horses)]
    horse_effect={h:rng.gauss(0,.45) if effects else 0. for h in original}
    data=[]
    for di in range(days):
        day=(date(2026,1,3)+timedelta(days=25*di)).isoformat()
        entrants=original[:]
        rng.shuffle(entrants)
        for rac in range(1,1+horses//8):
            shift=rng.gauss(0,.6)
            for h in entrants[(rac-1)*8:rac*8]:
                n=int(h[-3:])
                data.append({
                    "day":day,"race_number":rac,
                    "horse_id":h,"horse_name":f"FICTIONAL NAME {n:03d}",
                    "first_section_sec":10.0+shift+horse_effect[h]+rng.gauss(0,.08),
                    "first_marker_m":150.,
                    "distance":"1100 metres",
                    "class":"FABRICATED Class A",
                    "ground":"Good" if di%2 else "Soft",
                    "jockey_license_id":str(20000+n*20+di),
                    "trainer_license_id":str(30000+n%6),
                    "weight_kg":55.0,
                })
    return data


class PastOnlyDocumentedRiderCheckTests(unittest.TestCase):
    def test_stable_fake_horse_signal_is_forecast_from_earlier_dates_only(self):
        original=fake_races()
        panel,quality=source_timed_panel(original)
        report=analyze_forward(panel)
        broad=report["contexts"]["same_original_distance_and_first_GPS_marker"]
        fresh=broad["source_cohorts"]["new_documented_rider"]
        self.assertEqual(fresh["status"],
                         "EXPLORATORY_HORSE_PROFILE_CHRONOLOGICAL_SOURCE_CHECK_ONLY")
        self.assertEqual(fresh["original_animal_IDs_with_out_of_date_predictions"],32)
        self.assertEqual(fresh["out_of_date_matched_source_rows_scored"],288)
        self.assertEqual(fresh["distinct_future_source_meeting_dates_scored"],9)
        self.assertEqual(fresh["distinct_same_animal_marker_distance_contexts_scored"],32)
        self.assertGreater(fresh[
            "equal_horse_weighted_RMSE_reduction_seconds_positive_if_persistent"],.01)
        self.assertLess(
            fresh["equal_horse_weighted_past_horse_MAE_seconds"],
            fresh["equal_horse_weighted_zero_benchmark_MAE_seconds"])
        self.assertTrue(fresh["not_a_valid_out_of_sample_rider_causal_effect_or_significance"])
        self.assertFalse(report["not_H1_H2_heritability_actual_final_riders_or_wagering"] is False)
        json_text=json.dumps(report)
        for forbidden in ("FAKE-HORSE","FICTIONAL NAME","FABRICATED Class A",
                          '"horse_id"','"jockey_license_id"','"first_section_sec"'):
            self.assertNotIn(forbidden,json_text)

    def test_fixed_shrinkage_uses_only_one_past_record(self):
        base={
            "horse_id":"PRIVATE-SYNTH","distance":"1200 metres",
            "marker":150.,"race_class":"FAKE CLASS","race_number":1,
            "trainer_id":"T-ONE",
        }
        timed=[
            {**base,"day":"2026-01-01","relative_seconds":.6,"jockey_id":"J-ONE"},
            {**base,"day":"2026-02-01","relative_seconds":.6,"jockey_id":"J-TWO"},
        ]
        out=forward_records(timed)
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]["day"],"2026-02-01")
        self.assertFalse(out[0]["previous_same_documented_jockey"])
        self.assertAlmostEqual(out[0]["profile_squared_error"],(.6-.6/3)**2)
        self.assertAlmostEqual(out[0]["zero_squared_error"],.6**2)

    def test_later_performance_cannot_change_earlier_predictions(self):
        panel,_=source_timed_panel(fake_races())
        before=forward_records(panel)
        altered=copy.deepcopy(panel)
        newest=max(r["day"] for r in altered)
        for r in altered:
            if r["day"]==newest:
                r["relative_seconds"]+=500.
        after=forward_records(altered)
        early_before=[x for x in before if x["day"]<newest]
        early_after=[x for x in after if x["day"]<newest]
        self.assertEqual(early_before,early_after)
        self.assertNotEqual(before,after)

    def test_date_row_order_does_not_create_future_leakage(self):
        panel,_=source_timed_panel(fake_races())
        original=analyze_forward(panel)
        opposite=analyze_forward(list(reversed(panel)))
        self.assertEqual(original,opposite)

    def test_no_rider_documents_means_explicit_hold_not_zero_gain(self):
        raw=fake_races()
        for r in raw:
            r["jockey_license_id"]=None
        panel,_=source_timed_panel(raw)
        scores=analyze_forward(panel)
        switched=scores["contexts"]["same_original_distance_and_first_GPS_marker"][
            "source_cohorts"]["new_documented_rider"]
        self.assertEqual(switched["status"],
                         "HOLD_INSUFFICIENT_PRIOR_SOURCE_MATCH_AND_FUTURE_CHANGED_RIDER_SUPPORT")
        self.assertEqual(switched["out_of_date_matched_source_rows_scored"],0)
        self.assertNotIn(
            "equal_horse_weighted_RMSE_reduction_seconds_positive_if_persistent",
            switched)

    def test_same_documented_rider_not_false_novel_rider(self):
        raw=fake_races()
        for r in raw:
            horse_index=int(r["horse_id"].rsplit("-",1)[1])
            r["jockey_license_id"]=str(3000+horse_index)
        panel,_=source_timed_panel(raw)
        report=analyze_forward(panel)
        cohorts=report["contexts"]["same_original_distance_and_first_GPS_marker"][
            "source_cohorts"]
        self.assertEqual(cohorts["new_documented_rider"]["out_of_date_matched_source_rows_scored"],0)
        self.assertEqual(cohorts["previously_seen_documented_rider"][
            "out_of_date_matched_source_rows_scored"],288)
        self.assertNotIn(
            "equal_horse_weighted_RMSE_reduction_seconds_positive_if_persistent",
            cohorts["new_documented_rider"])

    def test_unknown_historical_jockey_never_proves_actual_new_rider(self):
        raw=fake_races()
        first_day=min(r["day"] for r in raw)
        for r in raw:
            if r["day"]==first_day:
                r["jockey_license_id"]=None
        panel,_=source_timed_panel(raw)
        result=analyze_forward(panel)["contexts"][
            "same_original_distance_and_first_GPS_marker"]["source_cohorts"][
                "new_documented_rider"]
        self.assertEqual(result["original_animal_IDs_with_out_of_date_predictions"],32)
        self.assertEqual(result["out_of_date_matched_source_rows_scored"],256)
        self.assertEqual(result["future_rows_with_unknown_at_least_one_past_jockey_ID"],256)
        self.assertTrue(result["source_selection_requires_at_least_one_known_prior_jockey"])

    def test_class_changes_can_force_strict_class_hold(self):
        raw=fake_races()
        for r in raw:
            if r["day"]>="2026-05-01":
                r["class"]="FABRICATED Class B"
        panel,_=source_timed_panel(raw)
        report=analyze_forward(panel)
        broad=report["contexts"]["same_original_distance_and_first_GPS_marker"][
            "source_cohorts"]["new_documented_rider"]
        strict=report["contexts"]["also_same_original_race_Class"][
            "source_cohorts"]["new_documented_rider"]
        self.assertEqual(broad["status"],
                         "EXPLORATORY_HORSE_PROFILE_CHRONOLOGICAL_SOURCE_CHECK_ONLY")
        self.assertLess(strict["out_of_date_matched_source_rows_scored"],
                        broad["out_of_date_matched_source_rows_scored"])

    def test_under_20_horses_suppresses_numeric_gain_not_zero(self):
        raw=fake_races(horses=16)
        panel,_=source_timed_panel(raw)
        value=analyze_forward(panel)["contexts"][
            "same_original_distance_and_first_GPS_marker"]["source_cohorts"][
                "new_documented_rider"]
        self.assertEqual(value["original_animal_IDs_with_out_of_date_predictions"],16)
        self.assertEqual(value["status"],
                         "HOLD_INSUFFICIENT_PRIOR_SOURCE_MATCH_AND_FUTURE_CHANGED_RIDER_SUPPORT")
        self.assertNotIn(
            "equal_horse_weighted_RMSE_reduction_seconds_positive_if_persistent",value)

    def test_trainer_source_subgroup_requires_original_known_trainer(self):
        raw=fake_races()
        for r in raw:
            r["trainer_license_id"]=None
        panel,_=source_timed_panel(raw)
        cohorts=analyze_forward(panel)["contexts"][
            "same_original_distance_and_first_GPS_marker"]["source_cohorts"]
        self.assertEqual(cohorts["new_documented_rider"][
            "out_of_date_matched_source_rows_scored"],288)
        self.assertEqual(cohorts[
            "new_documented_rider_and_same_documented_trainer"][
            "out_of_date_matched_source_rows_scored"],0)

    def test_source_level_score_is_not_a_horse_specific_published_trajectory(self):
        panel,_=source_timed_panel(fake_races())
        summary=analyze_forward(panel)
        self.assertTrue(summary[
            "no_original_IDs_licence_IDs_timing_predictions_or_history_exported"])
        self.assertTrue(summary["source_chronological_evaluation_in_memory_only"])
        values=json.dumps(summary)
        self.assertNotIn("PRIVATE-SYNTH",values)
        self.assertNotIn("FAKE-HORSE",values)


if __name__=="__main__":
    unittest.main()
