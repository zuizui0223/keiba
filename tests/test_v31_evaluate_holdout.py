import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v31_evaluate_holdout.py"


class V31EvaluationTests(unittest.TestCase):
    def run_eval(self, ledger, contract=None, attempt_ledger=None):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            ledger_path = base / "ledger.json"
            attempt_path = base / "attempts.json"
            contract_path = base / "contract.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            if contract is None:
                contract = {
                    "version": "v3.1",
                    "target_races": 20,
                    "alpha": 0.05,
                    "max_candidate_fraction": 0.65,
                    "min_freeze_success_rate": 0.80,
                }
            if attempt_ledger is None:
                entries = []
                for i, entry in enumerate(ledger.get("entries", []), start=1):
                    entries.append({
                        "attempt_index": i,
                        "race_id": entry.get("race_id", f"r{i}"),
                        "scheduled_start_jst": f"2026-10-{17 + ((i-1)//5):02d}T{10 + ((i-1)%5):02d}:00:00+09:00",
                        "status": "FROZEN",
                        "freeze_sha256": "a" * 64,
                    })
                attempt_ledger = {"version":"v3.1","entries":entries}
            attempt_path.write_text(json.dumps(attempt_ledger), encoding="utf-8")
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--ledger", str(ledger_path),
                 "--attempt-ledger", str(attempt_path), "--contract", str(contract_path)],
                text=True, capture_output=True,
            )
            return run, json.loads(run.stdout) if run.stdout.strip().startswith("{") else None

    def test_single_race_random_addition_tail_is_exact(self):
        ledger = {
            "version":"v3.1","target_races":1,
            "entries":[{
                "field_size":7,"M_candidate_count":3,"candidate_count":4,
                "M_top3_hits":2,"union_top3_hits":3,
                "winner_in_union":True
            }]
        }
        run, out = self.run_eval(ledger, {
            "version":"v3.1","target_races":1,"alpha":0.05,"max_candidate_fraction":0.65
        })
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertAlmostEqual(out["random_addition"]["p_value_one_sided"], 0.25)
        self.assertAlmostEqual(out["random_addition"]["expected_additional_hits"], 0.25)
        self.assertEqual(out["observed"]["additional_top3_hits_over_M"], 1)

    def test_twenty_strong_rescues_pass_preregistered_decision(self):
        entries=[]
        for i in range(20):
            entries.append({
                "race_id":f"r{i+1}","field_size":10,"M_candidate_count":3,
                "candidate_count":4,"M_top3_hits":2,"union_top3_hits":3,
                "winner_in_union":True
            })
        ledger={"version":"v3.1","target_races":20,"entries":entries}
        run,out=self.run_eval(ledger)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(out["decision"]["status"],"PROMOTE")
        self.assertLessEqual(out["random_addition"]["p_value_one_sided"],0.05)
        self.assertLessEqual(out["observed"]["candidate_fraction"],0.65)

    def test_significant_but_too_broad_is_not_promoted(self):
        entries=[]
        for i in range(20):
            entries.append({
                "race_id":f"r{i+1}","field_size":10,"M_candidate_count":3,
                "candidate_count":8,"M_top3_hits":2,"union_top3_hits":3,
                "winner_in_union":True
            })
        ledger={"version":"v3.1","target_races":20,"entries":entries}
        run,out=self.run_eval(ledger)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(out["decision"]["status"],"NO_PROMOTION")
        self.assertIn("candidate_fraction_above_ceiling",out["decision"]["reasons"])

    def test_incomplete_ledger_has_no_formal_decision(self):
        ledger={"version":"v3.1","target_races":20,"entries":[{
            "race_id":"r1","field_size":10,"M_candidate_count":3,"candidate_count":4,
            "M_top3_hits":2,"union_top3_hits":3,"winner_in_union":True
        }]}
        run,out=self.run_eval(ledger)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(out["decision"]["status"],"INCOMPLETE")
        self.assertEqual(out["observed"]["races_scored"],1)

    def test_low_freeze_success_rate_blocks_promotion(self):
        entries=[]
        for i in range(20):
            entries.append({
                "race_id":f"r{i+1}","field_size":10,"M_candidate_count":3,
                "candidate_count":4,"M_top3_hits":2,"union_top3_hits":3,
                "winner_in_union":True
            })
        attempts=[]
        frozen_i=0
        for i in range(26):
            if i in {3,7,11,15,19,23}:
                attempts.append({
                    "attempt_index":i+1,"race_id":f"fail{i+1}",
                    "scheduled_start_jst":f"2026-11-{i+1:02d}T10:00:00+09:00",
                    "status":"PRE_RESULT_DATA_FAILURE","failure_reason":"missing_profile"
                })
            else:
                frozen_i += 1
                attempts.append({
                    "attempt_index":i+1,"race_id":f"r{frozen_i}",
                    "scheduled_start_jst":f"2026-11-{i+1:02d}T10:00:00+09:00",
                    "status":"FROZEN","freeze_sha256":"a"*64
                })
                if frozen_i == 20:
                    break
        ledger={"version":"v3.1","target_races":20,"entries":entries}
        run,out=self.run_eval(ledger, attempt_ledger={"version":"v3.1","entries":attempts})
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(out["decision"]["status"],"NO_PROMOTION")
        self.assertIn("freeze_success_rate_below_floor",out["decision"]["reasons"])
        self.assertLess(out["technical_evaluability"]["freeze_success_rate"],0.80)

    def test_exact_eighty_percent_freeze_success_rate_can_promote(self):
        entries=[]
        for i in range(20):
            entries.append({
                "race_id":f"r{i+1}","field_size":10,"M_candidate_count":3,
                "candidate_count":4,"M_top3_hits":2,"union_top3_hits":3,
                "winner_in_union":True
            })
        attempts=[]
        frozen_i=0
        for i in range(25):
            if i in {4,9,14,19,24}:
                attempts.append({
                    "attempt_index":i+1,"race_id":f"fail{i+1}",
                    "scheduled_start_jst":f"2026-11-{i+1:02d}T10:00:00+09:00",
                    "status":"PRE_RESULT_DATA_FAILURE","failure_reason":"missing_profile"
                })
            else:
                frozen_i += 1
                attempts.append({
                    "attempt_index":i+1,"race_id":f"r{frozen_i}",
                    "scheduled_start_jst":f"2026-11-{i+1:02d}T10:00:00+09:00",
                    "status":"FROZEN","freeze_sha256":"a"*64
                })
        ledger={"version":"v3.1","target_races":20,"entries":entries}
        run,out=self.run_eval(ledger, attempt_ledger={"version":"v3.1","entries":attempts})
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(out["technical_evaluability"]["freeze_success_rate"],0.80)
        self.assertEqual(out["decision"]["status"],"PROMOTE")

    def test_scored_races_must_match_first_frozen_attempts(self):
        ledger={"version":"v3.1","target_races":1,"entries":[{
            "race_id":"r2","field_size":7,"M_candidate_count":3,"candidate_count":4,
            "M_top3_hits":2,"union_top3_hits":3,"winner_in_union":True
        }]}
        attempts={"version":"v3.1","entries":[{
            "attempt_index":1,"race_id":"r1","scheduled_start_jst":"2026-11-01T10:00:00+09:00",
            "status":"FROZEN","freeze_sha256":"a"*64
        }]}
        run,out=self.run_eval(
            ledger,
            {"version":"v3.1","target_races":1,"alpha":0.05,
             "max_candidate_fraction":0.65,"min_freeze_success_rate":0.80},
            attempts
        )
        self.assertNotEqual(run.returncode,0)
        self.assertIn("scored_frozen_sequence_mismatch",run.stderr)

    def test_invalid_nested_counts_are_rejected(self):
        ledger={"version":"v3.1","target_races":1,"entries":[{
            "race_id":"r1","field_size":10,"M_candidate_count":5,"candidate_count":4,
            "M_top3_hits":2,"union_top3_hits":3,"winner_in_union":True
        }]}
        run,out=self.run_eval(ledger, {
            "version":"v3.1","target_races":1,"alpha":0.05,"max_candidate_fraction":0.65
        })
        self.assertNotEqual(run.returncode,0)
        self.assertIn("invalid_candidate_nesting",run.stderr)


if __name__ == "__main__":
    unittest.main()
