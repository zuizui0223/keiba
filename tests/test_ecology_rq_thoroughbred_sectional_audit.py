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
        self.assertEqual(len(APPROVED),2)
        self.assertIn("20261011_Ladbrokes_Cannon_Park_T.csv",
                      official_url("20261011-cairns"))

    def test_little_variation_does_not_become_h1_or_h2_support(self):
        r=parse(fictional())
        self.assertEqual(r["status"],
                         "REAL_HORSE_SECTIONAL_STRUCTURE_AUDIT_NOT_H1_H2_EVIDENCE")
        self.assertFalse(r["has_position_at_sections"])
        self.assertTrue(any("not a documented stable" in x for x in r["limitations"]))


if __name__ == "__main__":
    unittest.main()
