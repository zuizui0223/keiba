"""Result-blind prospective universe, chronological day plans and missing-quote attempts."""
import copy
import json
from pathlib import Path
import unittest

from scripts.ticket_forward_freeze import REPO_ROOT, canonical
from scripts.ticket_forward_universe import (
    new_attempt_ledger, plan_day, record_attempt, register_day
)


def synthetic_schedule(date="2026-11-28", count=13):
    import datetime
    start = datetime.datetime.fromisoformat(f"{date}T10:00:00+09:00")
    races = []
    for i in range(count):
        t = start + datetime.timedelta(minutes=15 * i)
        races.append({
            "race_id": f"{date}-TOKYO-{i+1:02d}" if i < 12 else f"{date}-KYOTO-01",
            "venue": "東京" if i < 12 else "京都",
            "race_number": i + 1 if i < 12 else 1,
            "date": date,
            "scheduled_start_jst": t.isoformat(),
            "surface": "芝" if i % 2 else "ダ",
            "declared_runner_count": 10,
            "status": "RUNNING",
        })
    return {
        "schema_version": 1, "schedule_date": date,
        "source_url": "https://www.jra.go.jp/keiba/calendar/?synthetic=yes",
        "source_text_sha256": "a"*64,
        "captured_at_jst": f"{date}T09:30:00+09:00",
        "races": races,
    }


class FutureUniverseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (REPO_ROOT/"docs/betting/ticket-forward-v1-manifest.json").read_text())

    def test_first_ten_from_complete_schedule_before_earliest_start(self):
        source = synthetic_schedule()
        planned = plan_day(source, self.manifest, schedule_raw=canonical(source))
        self.assertEqual(planned["eligible_races_before_cap"], 13)
        self.assertEqual(planned["raw_schedule_count"], 13)
        self.assertEqual(len(planned["included_first_ten"]), 10)
        self.assertEqual(planned["included_first_ten"][0]["race_number"], 1)
        self.assertEqual(planned["included_first_ten"][-1]["race_number"], 10)
        self.assertEqual(planned["status"], "PRE_RACE_SCHEDULE_PLAN_UNATTESTED")
        ledger = new_attempt_ledger(self.manifest)
        self.assertEqual(len(ledger["attempts"]), 0)
        updated = register_day(ledger, planned, self.manifest)
        self.assertEqual(len(updated["attempts"]), 10)
        self.assertEqual(len(ledger["attempts"]), 0)
        self.assertEqual(updated["day_plans"][0]["plan_sha256"], updated["attempts"][0]["plan_sha256"])
        with self.assertRaises(ValueError):
            register_day(updated, planned, self.manifest)

    def test_plan_day_excludes_ineligible_without_looking_at_results(self):
        source = synthetic_schedule()
        source["races"][0]["status"] = "CANCELLED"
        source["races"][1]["surface"] = "障"
        source["races"][2]["declared_runner_count"] = 8
        planned = plan_day(source, self.manifest, schedule_raw=canonical(source))
        self.assertEqual(planned["eligible_races_before_cap"], 10)
        self.assertEqual(len(planned["included_first_ten"]), 10)
        self.assertEqual(planned["included_first_ten"][0]["race_number"], 4)
        self.assertEqual(planned["included_first_ten"][-1]["venue"], "京都")

    def test_hold_recorded_before_next_attempt_and_cannot_be_overwritten(self):
        source = synthetic_schedule()
        planned = plan_day(source, self.manifest, schedule_raw=canonical(source))
        ledger = register_day(new_attempt_ledger(self.manifest), planned, self.manifest)
        first, second = ledger["attempts"][0]["race_id"], ledger["attempts"][1]["race_id"]
        with self.assertRaises(ValueError):
            record_attempt(ledger, {"race_id": second, "status": "HOLD_NO_WIN_WIDE_SNAPSHOT"})
        next_ledger = record_attempt(ledger, {"race_id": first, "status": "HOLD_NO_WIN_WIDE_SNAPSHOT"})
        self.assertEqual(len(ledger["events"]), 0)
        self.assertEqual(next_ledger["events"][0]["status"], "HOLD_NO_WIN_WIDE_SNAPSHOT")
        with self.assertRaises(ValueError):
            record_attempt(next_ledger, {"race_id": first, "status": "HOLD_NO_WIN_WIDE_SNAPSHOT"})
        with self.assertRaises(ValueError):
            record_attempt(next_ledger, {"race_id": second, "status": "SUBMITTED_FOR_GITHUB_PROOF"})
        frozen = record_attempt(next_ledger, {
            "race_id": second, "status": "SUBMITTED_FOR_GITHUB_PROOF",
            "forecast_sha256": "b"*64,
            "github_run_id": 123456,
            "github_committed_path": f"holdout/ticket-forward-v1/{second}/forecast.json"
        })
        self.assertEqual(len(frozen["events"]), 2)
        self.assertEqual(frozen["events"][-1]["status"], "SUBMITTED_FOR_GITHUB_PROOF")
        with self.assertRaises(ValueError):
            record_attempt(frozen, {"race_id": "other-race", "status": "HOLD_STALE_QUOTE"})

    def test_refuses_schedule_after_results_or_from_untrusted_site(self):
        c = synthetic_schedule()
        c["races"][0]["top3"] = [1, 2, 3]
        with self.assertRaises(ValueError):
            plan_day(c, self.manifest, schedule_raw=canonical(c))
        c = synthetic_schedule()
        c["captured_at_jst"] = "2026-11-28T12:00:00+09:00"
        with self.assertRaises(ValueError):
            plan_day(c, self.manifest, schedule_raw=canonical(c))
        c = synthetic_schedule()
        c["source_url"] = "https://fake-jra.example/races"
        with self.assertRaises(ValueError):
            plan_day(c, self.manifest, schedule_raw=canonical(c))
        c = synthetic_schedule(date="2026-10-18")
        with self.assertRaises(ValueError):
            plan_day(c, self.manifest, schedule_raw=canonical(c))

    def test_different_days_append_and_no_retroactive_reordering(self):
        ledger = new_attempt_ledger(self.manifest)
        dates = ["2026-11-28", "2026-11-29", "2026-12-05"]
        for i, date in enumerate(dates):
            day = synthetic_schedule(date)
            plan = plan_day(day, self.manifest, schedule_raw=canonical(day))
            ledger = register_day(ledger, plan, self.manifest)
            self.assertEqual(len(ledger["attempts"]), (i+1)*10)
            self.assertEqual(len(ledger["day_plans"]), i+1)
        with self.assertRaises(ValueError):
            register_day(ledger, plan, self.manifest)
        with self.assertRaises(ValueError):
            plan_day(synthetic_schedule("2026-10-18"), self.manifest, schedule_raw=b"{}")


if __name__ == "__main__":
    unittest.main()
