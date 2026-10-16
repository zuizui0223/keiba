import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v31_attempt_ledger.py"


class AttemptLedgerTests(unittest.TestCase):
    def run_cmd(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True,
            capture_output=True,
        )

    def base_ledger(self):
        return {
            "schema_version": 1,
            "version": "v3.1",
            "status": "collecting",
            "entries": [],
            "summary": {
                "eligible_attempts": 0,
                "frozen_attempts": 0,
                "pre_result_data_failures": 0,
                "freeze_success_rate": None,
            },
        }

    def test_register_frozen_attempt_updates_success_rate(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            ledger=base/"ledger.json"
            out=base/"out.json"
            ledger.write_text(json.dumps(self.base_ledger()), encoding="utf-8")
            event={
                "race_id":"2026-10-17-KYOTO-07",
                "scheduled_start_jst":"2026-10-17T13:15:00+09:00",
                "status":"FROZEN",
                "freeze_sha256":"a"*64,
            }
            (base/"event.json").write_text(json.dumps(event), encoding="utf-8")
            run=self.run_cmd("register","--ledger",ledger,"--event",base/"event.json","--output",out)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads(out.read_text())
            self.assertEqual(data["summary"]["eligible_attempts"],1)
            self.assertEqual(data["summary"]["frozen_attempts"],1)
            self.assertEqual(data["summary"]["pre_result_data_failures"],0)
            self.assertEqual(data["summary"]["freeze_success_rate"],1.0)

    def test_register_data_failure_requires_reason(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            ledger=base/"ledger.json"
            out=base/"out.json"
            ledger.write_text(json.dumps(self.base_ledger()), encoding="utf-8")
            event={
                "race_id":"2026-10-17-KYOTO-07",
                "scheduled_start_jst":"2026-10-17T13:15:00+09:00",
                "status":"PRE_RESULT_DATA_FAILURE",
            }
            (base/"event.json").write_text(json.dumps(event), encoding="utf-8")
            run=self.run_cmd("register","--ledger",ledger,"--event",base/"event.json","--output",out)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("missing_failure_reason",run.stderr)

    def test_duplicate_race_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            ledger_data=self.base_ledger()
            ledger_data["entries"]=[{
                "attempt_index":1,
                "race_id":"2026-10-17-KYOTO-07",
                "scheduled_start_jst":"2026-10-17T13:15:00+09:00",
                "status":"PRE_RESULT_DATA_FAILURE",
                "failure_reason":"missing_profile",
            }]
            ledger=base/"ledger.json"
            out=base/"out.json"
            ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
            event={
                "race_id":"2026-10-17-KYOTO-07",
                "scheduled_start_jst":"2026-10-17T13:15:00+09:00",
                "status":"FROZEN",
                "freeze_sha256":"a"*64,
            }
            (base/"event.json").write_text(json.dumps(event), encoding="utf-8")
            run=self.run_cmd("register","--ledger",ledger,"--event",base/"event.json","--output",out)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("duplicate_attempt_race",run.stderr)

    def test_backfill_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            ledger_data=self.base_ledger()
            ledger_data["entries"]=[{
                "attempt_index":1,
                "race_id":"2026-10-17-KYOTO-08",
                "scheduled_start_jst":"2026-10-17T13:45:00+09:00",
                "status":"FROZEN",
                "freeze_sha256":"a"*64,
            }]
            ledger=base/"ledger.json"
            out=base/"out.json"
            ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
            event={
                "race_id":"2026-10-17-KYOTO-07",
                "scheduled_start_jst":"2026-10-17T13:15:00+09:00",
                "status":"PRE_RESULT_DATA_FAILURE",
                "failure_reason":"missing_profile",
            }
            (base/"event.json").write_text(json.dumps(event), encoding="utf-8")
            run=self.run_cmd("register","--ledger",ledger,"--event",base/"event.json","--output",out)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("attempt_backfill_forbidden",run.stderr)

    def test_summary_counts_mixed_attempts(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            ledger_data=self.base_ledger()
            ledger_data["entries"]=[
                {
                    "attempt_index":1,
                    "race_id":"r1",
                    "scheduled_start_jst":"2026-10-17T13:15:00+09:00",
                    "status":"FROZEN",
                    "freeze_sha256":"a"*64,
                },
                {
                    "attempt_index":2,
                    "race_id":"r2",
                    "scheduled_start_jst":"2026-10-17T13:45:00+09:00",
                    "status":"PRE_RESULT_DATA_FAILURE",
                    "failure_reason":"odds_window_missed",
                },
            ]
            ledger=base/"ledger.json"
            out=base/"out.json"
            ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
            event={
                "race_id":"r3",
                "scheduled_start_jst":"2026-10-17T14:50:00+09:00",
                "status":"FROZEN",
                "freeze_sha256":"b"*64,
            }
            (base/"event.json").write_text(json.dumps(event), encoding="utf-8")
            run=self.run_cmd("register","--ledger",ledger,"--event",base/"event.json","--output",out)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads(out.read_text())
            self.assertEqual(data["summary"]["eligible_attempts"],3)
            self.assertEqual(data["summary"]["frozen_attempts"],2)
            self.assertEqual(data["summary"]["pre_result_data_failures"],1)
            self.assertAlmostEqual(data["summary"]["freeze_success_rate"],2/3)


if __name__ == "__main__":
    unittest.main()
