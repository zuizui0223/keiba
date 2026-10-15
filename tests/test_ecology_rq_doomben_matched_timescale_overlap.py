"""FAKE horse IDs, race timings, Class and dates only.

Falsification of same-horse two-timescale 2025-vs-2026
context overlap: no real Racing Queensland animal records are
included in this test or checked into the repository.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))

from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_doomben_matched_timescale_overlap import (
    FIXED_MARKER, MIN_MATCHED_HORSE_IDS,
    PRIMARY_STATUS, paired_timescale_support, evaluate,
)
from test_ecology_rq_doomben_within_year_history import (
    fictional_annual_records
)
from test_ecology_rq_doomben_2025_marker_extension import fake_soap,fake_gps


class SameHorsesAcrossTwoPredictionHorizons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_source=fictional_annual_records(
            ids=32,source_days=8,
        )
        cls.fake_relative,_=prepare(cls.fake_source,min_race_telemetry=4)

    def test_planted_stable_individuals_have_supported_both_scored_horizons(self):
        result=paired_timescale_support(self.fake_relative,marker=150.,
                                        strict_class=False)
        self.assertEqual(result["status"],
            "EXPLORATORY_MATCHED_SOURCE_ID_TIMESCALE_CONTEXTS_NOT_CAUSAL")
        self.assertEqual(
            result["common_original_HORSES_IDs_with_identical_marker_and_distance_optional_class"],32)
        self.assertEqual(
            result["common_horse_by_exact_measurement_context_strata"],32)
        self.assertEqual(result["same_HORSES_ID_original_2025_scored_rows"],224)
        self.assertEqual(result["same_HORSES_ID_original_2026_scored_rows"],256)
        self.assertEqual(result["distinct_2025_later_meeting_dates"],7)
        self.assertEqual(result["distinct_2026_later_meeting_dates"],8)
        a=result["conditional_equal_ID_weighted_RMSE_seconds"]
        self.assertGreater(a["2025_other_minus_own_gain"],.01)
        self.assertGreater(a["2026_other_minus_own_gain"],.01)
        self.assertTrue(result[
            "not_a_identified_year_effect_or_within_horse_phenotypic_change"])
        self.assertTrue(result[
            "no_original_horse_name_ID_or_individual_GPS_outcome_exported"])
        encoded=json.dumps(result)
        for forbidden in (
            "FAKE-ANIMAL","FICTIONAL-HORSE","SYNTH CLASS A",
            '"horse_id":','"horse_name":','"first_section_sec":'
        ):
            self.assertNotIn(forbidden,encoded)

    def test_flipped_future_animal_effect_fails_yearforward_while_within_positive(self):
        rows=fictional_annual_records(
            ids=32,source_days=8,flip_2026=True,
        )
        relative,_=prepare(rows,min_race_telemetry=4)
        q=paired_timescale_support(relative)
        self.assertEqual(q["status"],
            "EXPLORATORY_MATCHED_SOURCE_ID_TIMESCALE_CONTEXTS_NOT_CAUSAL")
        errors=q["conditional_equal_ID_weighted_RMSE_seconds"]
        self.assertGreater(errors["2025_other_minus_own_gain"],0)
        self.assertLess(errors["2026_other_minus_own_gain"],0)
        self.assertTrue(q[
            "not_a_identified_year_effect_or_within_horse_phenotypic_change"])

    def test_only_sixteen_shared_early_gps_animals_hold_not_an_effect_of_zero(self):
        rows=fictional_annual_records(ids=16,source_days=8)
        relative,_=prepare(rows)
        q=paired_timescale_support(relative)
        self.assertEqual(q["status"],PRIMARY_STATUS)
        self.assertEqual(q[
            "common_original_HORSES_IDs_with_identical_marker_and_distance_optional_class"],16)
        self.assertNotIn("conditional_equal_ID_weighted_RMSE_seconds",q)
        self.assertTrue(q[
            "no_original_horse_name_ID_or_individual_GPS_outcome_exported"])

    def test_sixteen_2025_future_dates_not_invented_and_source_gates_fail(self):
        rows=fictional_annual_records(ids=32,source_days=4)
        relative,_=prepare(rows)
        q=paired_timescale_support(relative)
        self.assertEqual(q["status"],PRIMARY_STATUS)
        self.assertEqual(q["distinct_2025_later_meeting_dates"],3)
        self.assertNotIn("conditional_equal_ID_weighted_RMSE_seconds",q)

    def test_changed_original_class_in_second_year_is_not_same_trait(self):
        altered=copy.deepcopy(self.fake_source)
        for row in altered:
            if row["day"].startswith("2026-"):
                row["class"]="SYNTH CLASS B"
        relative,_=prepare(altered)
        broad=paired_timescale_support(relative,strict_class=False)
        strict=paired_timescale_support(relative,strict_class=True)
        self.assertEqual(broad["status"],
            "EXPLORATORY_MATCHED_SOURCE_ID_TIMESCALE_CONTEXTS_NOT_CAUSAL")
        self.assertEqual(strict["status"],PRIMARY_STATUS)
        self.assertEqual(strict[
            "common_original_HORSES_IDs_with_identical_marker_and_distance_optional_class"],0)
        self.assertNotIn("conditional_equal_ID_weighted_RMSE_seconds",strict)

    def test_changed_2026_gps_marker_never_interpolated_into_150m(self):
        altered=copy.deepcopy(self.fake_source)
        for row in altered:
            if row["day"].startswith("2026-"):
                row["first_marker_m"]=200.
        relative,_=prepare(altered)
        q=paired_timescale_support(relative,marker=150.)
        self.assertEqual(q["status"],PRIMARY_STATUS)
        self.assertEqual(q[
            "common_original_HORSES_IDs_with_identical_marker_and_distance_optional_class"],0)
        self.assertNotIn("conditional_equal_ID_weighted_RMSE_seconds",q)

    def test_chronological_input_order_change_does_not_change_overlap(self):
        a=paired_timescale_support(self.fake_relative)
        b=paired_timescale_support(list(reversed(self.fake_relative)))
        self.assertEqual(a,b)

    def test_unapproved_source_marker_does_not_expand_after_outcomes(self):
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED_POSTHOC_GPS_FIRST_MARKER"):
            paired_timescale_support(self.fake_relative,marker=200.)

    def test_source_adapter_locks_exact_42_original_dates_and_avoids_IDs(self):
        q=evaluate(soap=fake_soap,gps=fake_gps,
                   source_error_mode="raise")
        self.assertEqual(q["original_locked_2025_dates"],23)
        self.assertEqual(q["original_locked_2026_dates"],19)
        self.assertEqual(q["original_source_dates_successfully_read"],42)
        self.assertEqual(q["original_source_dates_HOLD"],[])
        self.assertTrue(q[
            "no_original_animal_ID_name_licence_time_or_predictions_published"])
        self.assertTrue(q["NOT_ageing_H1_H2_heritability_personality_or_wagering"])
        self.assertNotIn("FAKE-HORSE",json.dumps(q))


if __name__=="__main__":
    unittest.main()
