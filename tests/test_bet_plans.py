import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BetPlanTests(unittest.TestCase):
    def run_plans(self, as_of):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "plans.json"
            run = subprocess.run(
                [sys.executable, "scripts/calculate_plans.py", "--as-of", as_of,
                 "--output", str(output)], cwd=ROOT, text=True, capture_output=True)
            return run, json.loads(output.read_text()) if output.exists() else None

    def test_focused_budgets_and_latest_quote(self):
        run, data = self.run_plans("2026-10-12T12:54:11+09:00")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual([p["ticket_count"] for p in data["plans"].values()], [1, 3, 4])
        self.assertEqual([p["stake_yen"] for p in data["plans"].values()], [100, 300, 400])
        three = data["plans"]["three_tickets"]["tickets"]
        self.assertEqual([t["only_this_hit_net_yen"] for t in three], [420, 600, 350])
        extra = data["plans"]["four_tickets"]["tickets"][-1]
        self.assertEqual(extra["horses"], [6, 14])
        self.assertEqual(extra["odds_low"], 9.3)
        self.assertEqual(extra["payout_low_yen"], 930)
        self.assertEqual(extra["only_this_hit_net_yen"], 530)

    def test_checkpoint_cannot_be_used_before_observation(self):
        run, data = self.run_plans("2026-10-12T12:44:35+09:00")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("future_checkpoint", run.stderr)
        self.assertIsNone(data)

    def test_started_plans_have_no_new_bets(self):
        run, data = self.run_plans("2026-10-12T16:31:00+09:00")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(all(p["stake_yen"] == 0 for p in data["plans"].values()))


if __name__ == "__main__":
    unittest.main()
