"""End-to-end checks of the time and money calculations, using frozen inputs."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AS_OF = "2026-10-12T12:45:00+09:00"


class AnalysisTests(unittest.TestCase):
    def run_report(self, as_of=AS_OF, mutate=None):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            data = base / "data"
            data.mkdir()
            for source in sorted((ROOT / "data/2026-10-12").glob("kyoto_*.json")):
                race = json.loads(source.read_text())
                if mutate:
                    mutate(race)
                (data / source.name).write_text(json.dumps(race, ensure_ascii=False))
            output = base / "report"
            process = subprocess.run(
                [sys.executable, str(ROOT / "scripts/analyze.py"),
                 "--data", str(data), "--output", str(output), "--as-of", as_of],
                capture_output=True, text=True,
            )
            report = output / "analysis.json"
            content = json.loads(report.read_text()) if report.exists() else None
            markdown = (output / "report.md").read_text() if report.exists() else ""
            return process, content, markdown

    def test_full_roster_and_priority_budget(self):
        process, report, markdown = self.run_report()
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(report["horse_count"], 95)
        self.assertEqual(report["portfolios"]["all"]["ticket_count"], 15)
        self.assertEqual(report["portfolios"]["all"]["stake_yen"], 1500)
        self.assertEqual(report["portfolios"]["priority"]["ticket_count"], 6)
        self.assertEqual(report["portfolios"]["priority"]["stake_yen"], 600)
        self.assertIn("今日の的中確率ではありません", markdown)

    def test_one_hit_can_still_lose_money(self):
        process, report, _ = self.run_report()
        self.assertEqual(process.returncode, 0, process.stderr)
        row = next(t for t in report["portfolios"]["priority"]["tickets"]
                   if t["race"] == 11 and t["horses"] == [1, 9])
        self.assertEqual(row["payout_low_yen"], 570)
        self.assertEqual(row["only_this_hit_net_yen"], -30)
        self.assertAlmostEqual(row["break_even_hit_probability"], 1 / 5.7, places=10)

    def test_shared_axis_cannot_make_three_wide_tickets_win(self):
        process, report, _ = self.run_report()
        self.assertEqual(process.returncode, 0, process.stderr)
        risk = next(r for r in report["portfolios"]["priority"]["race_scenarios"]
                    if r["race"] == 11)
        self.assertEqual(risk["common_axes"], [9])
        self.assertEqual(risk["max_simultaneous_winners"], 2)
        self.assertEqual(risk["distinct_top3_sets_enumerated"], 816)
        self.assertEqual(risk["axis_absent_max_return_yen"], 0)

    def test_all_started_races_have_no_new_candidate_tickets(self):
        process, report, _ = self.run_report("2026-10-12T16:31:00+09:00")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(report["portfolios"]["all"]["ticket_count"], 0)
        self.assertEqual(report["portfolios"]["priority"]["stake_yen"], 0)

    def test_future_snapshot_is_rejected(self):
        process, _, _ = self.run_report("2026-10-12T12:00:00+09:00")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("future_observation", process.stderr)

    def test_distance_count_cannot_exceed_course_count(self):
        def mutate(race):
            if race["race"] == 11:
                race["horses"][0]["kyoto_distance_record"] = [999, 0, 0, 0]
        process, _, _ = self.run_report(mutate=mutate)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("distance_exceeds_course", process.stderr)

    def test_naive_analysis_time_is_rejected(self):
        process, _, _ = self.run_report("2026-10-12T12:45:00")
        self.assertNotEqual(process.returncode, 0)
        self.assertIn("timezone_required", process.stderr)

    def test_unknown_course_is_not_zero_percent(self):
        process, report, _ = self.run_report()
        self.assertEqual(process.returncode, 0, process.stderr)
        maiden = next(r for r in report["races"] if r["race"] == 6)
        self.assertTrue(all(h["course_summary"]["top3_rate"] is None
                            for h in maiden["horses"]))
        self.assertTrue(all(h["course_summary"]["starts"] is None
                            for h in maiden["horses"]))


if __name__ == "__main__":
    unittest.main()
