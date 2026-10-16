"""Explicitly fake-data tests for the publicly sourced cross-species benchmark."""
import csv
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_greyhound_open_pilot import (
    FIELDS, PINNED_BLOB_SHA1, analysis, git_blob_hash, groups, read
)


def invented_csv():
    result = []
    for day in range(1, 16):
        dt = f"2001-01-{day:02d}"
        for d in ("FAKE-DOG-1", "FAKE-DOG-2", "FAKE-DOG-3"):
            result.append({
                "date": dt, "track": "FAKE-TRACK-1",
                "race": f"Race {day:02d}", "greyhound": d,
                "box": "2" if day % 2 == 0 else "7",
                "split_50m_sec": str(3.9 + (day % 2)*.04),
                "position_50m": "1",
                "rail_distance_50m_m": "-.2" if day == 1 else "2.1",
                "top_speed_kmh": "67.1", "finish_position": "2",
            })
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(FIELDS), lineterminator="\n")
    writer.writeheader()
    writer.writerows(result)
    return buf.getvalue().encode("utf-8")


class RealAnalogueTests(unittest.TestCase):
    def test_pilot_does_not_claim_racehorse_inference(self):
        out = analysis(invented_csv(), bootstrap=100)
        self.assertEqual(out["status"], "UNPINNED_INPUT_DESCRIPTIVE_ONLY")
        self.assertFalse(out["source"]["matches_pinned_source"])
        self.assertEqual(out["data_quality"]["rows"], 45)
        self.assertEqual(out["data_quality"]["distinct_source_races"], 15)
        self.assertEqual(out["full"]["dog_venue_strata"], 3)
        self.assertAlmostEqual(out["full"]["mean_outer_minus_inner_sec"], 0.04)
        self.assertIn("H1 or H2 established among racehorses", out["not_claimed"])
        self.assertFalse(out["full"]["bootstrap_is_causal_uncertainty"])
        self.assertEqual(out["animal"], "racing greyhound (NOT Thoroughbred horse)")

    def test_cutoff_computed_on_dates_not_random_horse_rows(self):
        out = analysis(invented_csv(), bootstrap=100)
        self.assertEqual(out["method"]["cutoff_date"], "2001-01-13")
        self.assertEqual(out["early_dates"]["dog_venue_strata"], 3)
        self.assertEqual(out["late_dates"]["dog_venue_strata"], 0)

    def test_duplicate_dog_on_same_date_race_held(self):
        records = invented_csv().decode("utf-8").splitlines()
        with self.assertRaisesRegex(ValueError, "HOLD_DUPLICATE_GREYHOUND_RUN"):
            read(("\n".join(records + [records[1]])+"\n").encode("utf-8"))

    def test_implausible_split_and_negative_rail_not_recoded_to_zero(self):
        records = invented_csv().decode("utf-8").splitlines()
        head = records[0].split(",")
        row = records[1].split(",")
        row[head.index("split_50m_sec")] = "29.25"
        records[1] = ",".join(row)
        _, diag = read(("\n".join(records)+"\n").encode("utf-8"))
        self.assertEqual(diag["split_outside_exploratory_range"], 1)
        self.assertEqual(diag["negative_reported_rail"], 3)

    def test_git_blob_sha_is_content_derived(self):
        a = git_blob_hash(invented_csv())
        self.assertEqual(len(a), 40)
        self.assertNotEqual(a, PINNED_BLOB_SHA1)
        self.assertNotEqual(a, git_blob_hash(invented_csv()+b"\n"))

    def test_within_dog_does_not_mix_venues(self):
        data = [
            {"dog_name":"DOG","track":"T1","box":1,"split_sec":3.9},
            {"dog_name":"DOG","track":"T1","box":2,"split_sec":3.9},
            {"dog_name":"DOG","track":"T2","box":7,"split_sec":4.2},
            {"dog_name":"DOG","track":"T2","box":8,"split_sec":4.2},
        ]
        self.assertEqual(groups(data), [])

    def test_bootstrap_guardrails(self):
        with self.assertRaisesRegex(ValueError, "bootstrap"):
            analysis(invented_csv(), bootstrap=2)


if __name__ == "__main__":
    unittest.main()
