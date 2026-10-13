"""No gambling predictions; handcrafted examples for official sectional grammar."""
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_rq_thoroughbred_sectional_audit import (
    parse, official_url, duration_s, APPROVED
)


def fictional():
    return ("""Date,RaceNumber,11/10/2026 12:00:00 AM;FAKE VENUE;Invented Handicap;00:00:57.263;FAKE_ROUTE
11/10/2026,1,Animal Alpha;7;150;19.38;00:00:10.50;350;19.69;00:00:10.33
11/10/2026,1,Animal Beta;2;150;0;00:00:00.000;350;0;00:00:00.000
11/10/2026,1,Animal Gamma;3;150;19.22;00:00:10.55;350;0;00:00:00.000
""").encode("utf-8")


class RQSectionalTests(unittest.TestCase):
    def test_sectional_parser_does_not_infer_individual_outcome_from_header(self):
        r=parse(fictional(),"FICTIONAL")
        self.assertEqual(r["race_counts"]["race_headers"],1)
        self.assertEqual(r["race_counts"]["horse_rows"],3)
        self.assertEqual(r["quality"]["all_zero_telemetry_rows"],1)
        self.assertEqual(r["quality"]["partial_zero_or_invalid_telemetry_rows"],1)
        self.assertEqual(r["quality"]["complete_positive_telemetry_rows"],1)
        self.assertTrue(r["race_header_time_not_individual_horse_time"])
        self.assertFalse(r["telemetry_zero_means_dnf"])
        self.assertFalse(r["has_stable_horse_id"])
        self.assertFalse(r["has_verified_true_starter_status"])
        self.assertFalse(r["has_verified_individual_finish_time"])
        self.assertFalse(r["unverified_index_assumed_cloth"])
        self.assertEqual(r["races_by_race_header"][0]["race_level_time_seconds_not_horse_outcome"],57.263)
        self.assertEqual(r["races_by_race_header"][0]["positive_telemetry_rows"],2)
        self.assertFalse(r["raw_file_republished"])

    def test_source_header_uses_mmdd_in_february_and_runner_uses_ddmm(self):
        raw = ("""Date,RaceNumber,2/16/2026 12:00:00 AM;Ladbrokes Cannon Park-Professional-2026-02-16;Test race;00:00:57.263;CRNS_950m_TRACK
16/02/2026,1,Fictional Horse;3;150;19.38;00:00:10.50;350;19.69;00:00:10.33
""").encode("utf-8")
        result=parse(raw)
        self.assertEqual(result["race_counts"]["source_dates"],["2026-02-16"])
        self.assertEqual(result["quality"]["vendor_header_date_confirmed_by_vendor_ISO_venue_label"],1)

    def test_ambiguous_single_digit_source_header_has_iso_resolution(self):
        raw = ("""Date,RaceNumber,9/04/2026 12:00:00 AM;2026-04-09 Ladbrokes Cannon Park QLD - Professional;Test race;00:00:57.263;CRNS_950m_TRACK
09/04/2026,1,Fictional Horse;3;150;19.38;00:00:10.50;350;19.69;00:00:10.33
""").encode("utf-8")
        self.assertEqual(parse(raw)["race_counts"]["source_dates"],["2026-04-09"])
        wrong=raw.replace(b"2026-04-09 Ladbrokes",b"2026-09-04 Ladbrokes")
        with self.assertRaisesRegex(ValueError,"HOLD_VENDOR_HEADER_DATE_CONFLICTS_WITH_VENUE_ISO"):
            parse(wrong)

    def test_invalid_vendor_header_and_runner_dates_never_coerce(self):
        raw = ("""Date,RaceNumber,2/16/2026 12:00:00 AM;Ladbrokes Cannon Park-Professional-2026-02-16;Test race;00:00:57.263;CRNS_950m_TRACK
17/02/2026,1,Fictional Horse;3;150;19.38;00:00:10.50;350;19.69;00:00:10.33
""").encode("utf-8")
        with self.assertRaisesRegex(ValueError,"race date|DATE|date",):
            parse(raw)

    def test_missing_telemetry_is_not_speed_zero(self):
        raw=fictional().replace(
            b"350;19.69;00:00:10.33",b"350;19.69;00:00:00.000")
        r=parse(raw)
        self.assertEqual(r["quality"]["inconsistent_zero_signal_and_time"],1)
        self.assertEqual(r["quality"]["partial_zero_or_invalid_telemetry_rows"],2)

    def test_malformed_triplets_refused(self):
        bad=fictional().replace(b";350;19.69;00:00:10.33",
                                 b";350;19.69")
        with self.assertRaisesRegex(ValueError, "HOLD_UNEXPECTED_SECTION_TRIPLE"):
            parse(bad)

    def test_nonincreasing_distance_markers_refused(self):
        bad=fictional().replace(b";350;19.69;00:00:10.33",
                                 b";100;19.69;00:00:10.33")
        with self.assertRaisesRegex(ValueError, "HOLD_INVALID_SECTION_TRIPLE"):
            parse(bad)

    def test_header_winner_time_does_not_imply_focal_finish_time(self):
        self.assertAlmostEqual(duration_s("00:01:14.877"),74.877)
        self.assertIsNone(duration_s("not a measurement"))

    def test_duplicate_horse_in_race_refused(self):
        rows=fictional().decode("utf-8").splitlines()
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_HORSE_NAME"):
            parse(("\n".join(rows+[rows[1]])+"\n").encode("utf-8"))

    def test_cannot_fetch_unapproved_urls(self):
        with self.assertRaisesRegex(ValueError,"HOLD_NON_ALLOWLISTED"):
            official_url("https://evil.example.com/filename.csv")
        # 5 fixed original Cannon Park cohorts + 7 locked 2026
        # calendar additions, plus one separate Eagle Farm comparator.
        self.assertEqual(len(APPROVED),13)
        self.assertIn("20260216_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260216-cairns"))
        self.assertIn("20260312_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260312-cairns"))
        self.assertIn("20260326_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260326-cairns"))
        self.assertIn("20260404_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260404-cairns"))
        self.assertIn("20260409_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260409-cairns"))
        self.assertIn("20260723_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260723-cairns"))
        self.assertIn("20260828_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260828-cairns"))
        self.assertIn("20260515_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260515-cairns"))
        self.assertIn("20260529_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260529-cairns"))
        self.assertIn("20260822_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260822-cairns"))
        self.assertIn("20260829_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20260829-cairns"))
        self.assertIn("20261011_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20261011-cairns"))

    def test_same_day_horse_name_zero_in_one_race_and_positive_in_another(self):
        raw = ("""Date,RaceNumber,11/10/2026 12:00:00 AM;FAKE VENUE;Race One;00:00:55.000;FAKE
11/10/2026,1,Example Horse;3;150;0;00:00:00.000;350;0;00:00:00.000
Date,RaceNumber,11/10/2026 12:00:00 AM;FAKE VENUE;Race Two;00:00:56.000;FAKE
11/10/2026,2,Example Horse;3;150;18.3;00:00:10.33;350;19.2;00:00:10.83
""").encode("utf-8")
        report = parse(raw)
        self.assertEqual(report["race_counts"]["horse_names_repeated_in_different_races_same_day"],1)
        self.assertEqual(report["race_counts"]["same_day_repeated_names_both_zero_and_nonzero_telemetry"],1)
        self.assertFalse(report["telemetry_zero_means_dnf"])

    def test_race_numbers_do_not_silently_join_wrong_header(self):
        bad = fictional().replace(b"\n11/10/2026,1,Animal Beta",
                                  b"\n11/10/2026,2,Animal Beta")
        with self.assertRaisesRegex(ValueError,"HOLD_RACE_NUMBER_TO_HEADER"):
            parse(bad)

    def test_little_variation_does_not_become_h1_or_h2_support(self):
        r=parse(fictional())
        self.assertEqual(r["status"],
                         "REAL_HORSE_SECTIONAL_STRUCTURE_AUDIT_NOT_H1_H2_EVIDENCE")
        self.assertFalse(r["has_position_at_sections"])
        self.assertTrue(any("not a documented stable" in x for x in r["limitations"]))


if __name__ == "__main__":
    unittest.main()
