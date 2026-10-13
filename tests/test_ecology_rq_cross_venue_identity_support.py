"""Synthetic only: same-animal cross-venue data-readiness, never a horse effect."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_rq_2026_calendar_overlap import COHORT
from ecology_rq_eagle_farm_external_icc import DATES as EAGLE_DATES
from ecology_rq_cross_venue_identity_support import (
    compare, summarize_cross_venue,
)


def fake_row(hid="FAKE-ANIMAL-ID-ALPHA", name="FAKE EQUINE ALPHA",
             day="2026-02-16", marker=150., distance="1200 metres",
             race_class="FAKE CLASS", ground="Soft"):
    return {
        "horse_id": hid,
        "horse_name": name,
        "day": day,
        "race_number": 1,
        "first_marker_m": marker,
        "first_section_sec": 10.1,
        "distance": distance,
        "class": race_class,
        "ground": ground,
    }


class CrossVenueIdentityAuditTests(unittest.TestCase):
    def test_different_ids_with_same_name_do_not_match(self):
        c = [fake_row(hid="FAKE-ID-ONE", name="EXAMPLE SAME NAME")]
        e = [fake_row(hid="FAKE-ID-TWO", name="EXAMPLE SAME NAME",
                      day="2026-03-07")]
        r = summarize_cross_venue(c, e)
        self.assertEqual(r["valid_named_original_HORSES_IDs_recorded_at_both_venues"], 0)
        self.assertEqual(r["same_name_different_HORSES_ID_never_linked"], 1)
        self.assertEqual(r["status"],
                         "HOLD_NO_VALID_SAME_HORSE_ID_ACROSS_TWO_VENUES")

    def test_same_id_but_different_name_is_blocked_not_personality(self):
        c = [fake_row(name="FAKE ONE")]
        e = [fake_row(name="FAKE TWO", day="2026-03-07")]
        r = summarize_cross_venue(c, e)
        self.assertEqual(r["shared_numeric_ID_cross_venue_name_conflicts_blocked"], 1)
        self.assertEqual(r["valid_named_original_HORSES_IDs_recorded_at_both_venues"], 0)
        self.assertTrue(r["no_raw_horse_names_ids_licences_or_times_exported"])
        raw = json.dumps(r)
        self.assertNotIn("FAKE ONE", raw)
        self.assertNotIn("FAKE TWO", raw)
        self.assertNotIn("FAKE-ANIMAL-ID-ALPHA", raw)
        self.assertNotIn("10.1", raw)

    def test_same_id_on_same_date_two_distant_venues_is_blocked(self):
        c = [fake_row(day="2026-08-29")]
        e = [fake_row(day="2026-08-29")]
        r = summarize_cross_venue(c, e)
        self.assertEqual(r["shared_numeric_ID_same_day_two_venues_conflicts_blocked"], 1)
        self.assertEqual(r["valid_named_original_HORSES_IDs_recorded_at_both_venues"], 0)

    def test_same_animal_but_different_first_marker_is_hold(self):
        c = [fake_row(day="2026-02-16", marker=150)]
        e = [fake_row(day="2026-03-07", marker=200)]
        r = summarize_cross_venue(c, e)
        self.assertEqual(r["valid_named_original_HORSES_IDs_recorded_at_both_venues"], 1)
        self.assertEqual(r["status"],
                         "HOLD_SHARED_HORSE_IDS_BUT_NO_IDENTICAL_FIRST_GPS_MARKER")
        self.assertEqual(
            r["shared_HORSES_IDs_with_any_exact_first_GPS_marker_at_both_venues"], 0)

    def test_matched_marker_distance_class_and_two_dates_each(self):
        c = [fake_row(day=d) for d in ("2026-02-16", "2026-04-09")]
        e = [fake_row(day=d) for d in ("2026-03-07", "2026-04-18")]
        r = summarize_cross_venue(c, e)
        self.assertEqual(r["status"],
                         "EXPLORATORY_CROSS_VENUE_ID_AND_MARKER_DATA_SUPPORT_ONLY")
        self.assertEqual(r[
            "shared_HORSES_IDs_with_any_exact_first_GPS_marker_at_both_venues"], 1)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_exact_first_marker_and_official_distance"], 1)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_exact_marker_distance_and_source_class"], 1)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_2plus_independent_dates_per_venue_same_marker"], 1)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_2plus_dates_per_venue_same_marker_distance"], 1)
        self.assertTrue(r["shared_marker_alone_does_not_verify_same_segment_definition"])
        e[1]["distance"] = "1300 metres"
        r = summarize_cross_venue(c, e)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_2plus_dates_per_venue_same_marker_distance"], 0)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_2plus_independent_dates_per_venue_same_marker"], 1)

    def test_exact_marker_and_distance_without_class_match(self):
        c = [fake_row()]
        e = [fake_row(day="2026-03-07", race_class="OTHER CLASS")]
        r = summarize_cross_venue(c, e)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_exact_first_marker_and_official_distance"], 1)
        self.assertEqual(r[
            "shared_HORSES_IDs_with_exact_marker_distance_and_source_class"], 0)

    def test_source_missingness_is_hold_not_zero_overlap_inference(self):
        def cannon_reader(**kwargs):
            return [fake_row()], {
                d: {"status": "SOURCE_CANNON_PARK_IDS_AND_GPS_AUDITED"}
                for d in COHORT
            }
        def eagle_reader(**kwargs):
            return [fake_row(day="2026-03-07")], {
                d: {"status": ("HOLD_DATE_SOURCE_NOT_RECONCILED"
                              if d == EAGLE_DATES[0] else
                              "SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED")}
                for d in EAGLE_DATES
            }
        out = compare(cannon_reader=cannon_reader, eagle_reader=eagle_reader)
        self.assertEqual(out["status"],
                         "SOURCE_COHORT_INCOMPLETE_HOLD_CROSS_VENUE_INFERENCE")
        self.assertEqual(out["Eagle_source_dates_audited"], 11)
        self.assertEqual(out["Eagle_source_dates_on_HOLD"], [EAGLE_DATES[0]])
        self.assertFalse(out["source_cross_venue_overlap"][
            "zero_shared_IDs_would_not_be_a_zero_biological_effect"] is False)
        self.assertTrue(out["no_raw_individual_data_or_predictions_exported"])

    def test_empty_both_venues_is_explicit_hold(self):
        out = summarize_cross_venue([], [])
        self.assertEqual(out["status"],
                         "HOLD_NO_VALID_SAME_HORSE_ID_ACROSS_TWO_VENUES")
        self.assertTrue(out["zero_shared_IDs_would_not_be_a_zero_biological_effect"])


if __name__ == "__main__":
    unittest.main()
