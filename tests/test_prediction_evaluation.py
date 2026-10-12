import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PredictionEvaluationTests(unittest.TestCase):
    def test_frozen_marks_against_partial_official_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "eval.json"
            run = subprocess.run(
                [
                    sys.executable,
                    "scripts/evaluate_prediction_postmortem.py",
                    "--output",
                    str(out),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads(out.read_text())
            self.assertEqual(data["races_scored"], 4)
            self.assertEqual(data["winner_in_core_count"], 4)
            self.assertEqual(data["top2_both_in_core_count"], 3)
            self.assertEqual(data["complete_top3_races"], 3)
            self.assertEqual(data["complete_top3_all_candidates_count"], 3)
            self.assertEqual(data["any_saved_wide_hit_count"], 3)

            rows = {r["race"]: r for r in data["rows"]}
            self.assertEqual(rows[9]["winner_mark"], "◎")
            self.assertTrue(rows[9]["any_saved_wide_hit_confirmed"])
            self.assertTrue(rows[10]["any_saved_wide_hit_confirmed"])
            self.assertFalse(rows[8]["any_saved_wide_hit_confirmed"])


if __name__ == "__main__":
    unittest.main()
