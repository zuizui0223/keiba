"""Research-only tests using generated, fabricated races (never real JRA outcomes)."""
import csv
from datetime import date, timedelta
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_panel import REQUIRED, load_panel, lagged_features, audit


def fixture(days=5, horses=4):
    rows = []
    for day in range(days):
        d = date(2026, 1, 1) + timedelta(days=day)
        for idx in range(1, horses + 1):
            rows.append({
                "race_id": f"synthetic_race_{day:03d}",
                "horse_id": f"synthetic_horse_{idx:03d}",
                "race_date_jst": d.isoformat(),
                "race_start_jst": f"{d}T13:00:00+09:00",
                "feature_available_at_jst": f"{d}T12:00:00+09:00",
                "venue": "synthetic-venue",
                "course_surface": "turf",
                "course_distance_m": "1600",
                "track_going": "良" if day % 2 == 0 else "重",
                "class_pre": "synthetic-class",
                "jockey_id": f"synthetic_jockey_{idx:03d}",
                "field_size": str(horses),
                "finish_status": "finished",
                "finishing_position": str(idx),
                "finish_time_s": str(100 + idx + day / 10),
                "first_call_position": str(idx),
                "source_url": "synthetic://fabricated/no-claims",
                "source_license": "synthetic",
            })
    return rows


def write_rows(folder, rows):
    path = Path(folder) / "panel.csv"
    cols = list(REQUIRED) + ["first_call_position"]
    with path.open("w", newline="", encoding="utf-8") as h:
        writer = csv.DictWriter(h, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
    return path


class PanelTests(unittest.TestCase):
    def test_within_horse_audit_and_synthetic_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = load_panel(write_rows(tmp, fixture()))
            enriched = lagged_features(rows)
            result = audit(rows, enriched)
        self.assertEqual(result["horse_start_rows"], 20)
        self.assertEqual(result["unique_races"], 5)
        self.assertEqual(result["unique_horses"], 4)
        self.assertEqual(result["horses_with_2plus_timed_starts_in_each_good_vs_non_good"], 4)
        self.assertEqual(result["status"], "SYNTHETIC_ONLY")
        self.assertTrue(result["ready_gate_is_not_statistical_power_or_hypothesis_support"])

    def test_many_races_with_unchanged_opponent_composition_do_not_identify_h2(self):
        # Everyone meets exactly the same three opponents every day.
        with tempfile.TemporaryDirectory() as tmp:
            loaded = load_panel(write_rows(tmp, fixture(days=12)))
        report = audit(loaded, lagged_features(loaded))
        self.assertGreater(report["h2_rows_with_historical_style_and_opponent_strength"], 0)
        self.assertEqual(report["h2_horses_with_4plus_races_and_2plus_distinct_opponent_style_contexts"], 0)
        self.assertEqual(report["h2_context_identifiability"], "HOLD_NO_REPEATED_WITHIN_HORSE_CONTEXT_VARIATION")

    def test_no_lookahead_and_leave_one_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = load_panel(write_rows(tmp, fixture()))
        out = lagged_features(rows)
        h2_first = next(x for x in out if x["race_date_jst"] == "2026-01-01" and x["horse_id"] == "synthetic_horse_002")
        self.assertEqual(h2_first["prior_starts_count"], 0)
        self.assertIsNone(h2_first["prior_front_runner_score"])
        self.assertIsNone(h2_first["other_front_runner_share"])
        h2_day4 = next(x for x in out if x["race_date_jst"] == "2026-01-04" and x["horse_id"] == "synthetic_horse_002")
        self.assertEqual(h2_day4["prior_starts_count"], 3)
        self.assertAlmostEqual(h2_day4["prior_front_runner_score"], 2 / 3)
        self.assertAlmostEqual(h2_day4["other_front_runner_share"], 1 / 3)
        self.assertAlmostEqual(h2_day4["other_prior_strength_mean"], (1 + 1 / 3 + 0) / 3)
        changed = fixture()
        for row in changed:
            if row["race_date_jst"] == "2026-01-04":
                row["first_call_position"] = str(5 - int(row["first_call_position"]))
                row["finishing_position"] = str(5 - int(row["finishing_position"]))
        with tempfile.TemporaryDirectory() as tmp:
            changed_out = lagged_features(load_panel(write_rows(tmp, changed)))
        changed_day4 = next(x for x in changed_out if x["race_date_jst"] == "2026-01-04" and x["horse_id"] == "synthetic_horse_002")
        self.assertEqual(changed_day4["prior_front_runner_score"], h2_day4["prior_front_runner_score"])
        self.assertEqual(changed_day4["other_front_runner_share"], h2_day4["other_front_runner_share"])
        changed_day5 = next(x for x in changed_out if x["race_date_jst"] == "2026-01-05" and x["horse_id"] == "synthetic_horse_002")
        original_day5 = next(x for x in out if x["race_date_jst"] == "2026-01-05" and x["horse_id"] == "synthetic_horse_002")
        self.assertNotEqual(changed_day5["prior_front_runner_score"], original_day5["prior_front_runner_score"])

    def test_incomplete_roster_never_treated_as_zero_opponents(self):
        rows = [r for r in fixture() if not (r["race_date_jst"] == "2026-01-04" and r["horse_id"] == "synthetic_horse_003")]
        with tempfile.TemporaryDirectory() as tmp:
            enriched = lagged_features(load_panel(write_rows(tmp, rows)))
        h = next(x for x in enriched if x["race_date_jst"] == "2026-01-04" and x["horse_id"] == "synthetic_horse_002")
        self.assertIsNone(h["other_front_runner_share"])
        self.assertIsNone(h["other_prior_strength_mean"])

    def test_future_predictor_rejected(self):
        rows = fixture()
        rows[0]["feature_available_at_jst"] = "2026-01-01T13:01:00+09:00"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "future/at-start"):
                load_panel(write_rows(tmp, rows))

    def test_duplicate_observation_rejected(self):
        rows = fixture()
        rows.append(rows[0].copy())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_panel(write_rows(tmp, rows))

    def test_duplicate_finish_ranks_rejected(self):
        rows = fixture()
        rows[1]["finishing_position"] = rows[0]["finishing_position"]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "duplicate ranks"):
                load_panel(write_rows(tmp, rows))

    def test_race_attribute_contradiction_rejected(self):
        rows = fixture()
        rows[1]["track_going"] = "不良"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "conflicting race-level"):
                load_panel(write_rows(tmp, rows))

    def test_missing_time_does_not_become_zero(self):
        rows = fixture()
        rows[0]["finish_time_s"] = ""
        with tempfile.TemporaryDirectory() as tmp:
            parsed = load_panel(write_rows(tmp, rows))
        self.assertIsNone(parsed[0]["finish_time_s"])
        self.assertEqual(audit(parsed, lagged_features(parsed))["finishers_with_individual_times"], 19)

    def test_mixed_synthetic_real_sources_fail_closed(self):
        rows = fixture()
        rows[0]["source_license"] = "research-approved"
        rows[0]["source_url"] = "https://example.org/authorized-copy"
        with tempfile.TemporaryDirectory() as tmp:
            parsed = load_panel(write_rows(tmp, rows))
        self.assertEqual(audit(parsed, lagged_features(parsed))["status"],
                         "HOLD_MIXED_SYNTHETIC_AND_REAL")

    def test_uncleared_data_rights_hold(self):
        rows = fixture()
        for row in rows:
            row["source_license"] = "unknown"
            row["source_url"] = "https://example.org/rights-pending"
        with tempfile.TemporaryDirectory() as tmp:
            parsed = load_panel(write_rows(tmp, rows))
        self.assertEqual(audit(parsed, lagged_features(parsed))["status"], "HOLD_RIGHTS")

    def test_pending_status_rejects_postrace_results(self):
        rows = fixture()
        rows[0]["finish_status"] = "pending"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "nonfinisher has finishing outcome"):
                load_panel(write_rows(tmp, rows))


if __name__ == "__main__":
    unittest.main()
