import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v31_evaluate_holdout.py"


class V31EvaluationTests(unittest.TestCase):
    def run_eval(self, ledger, contract=None):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            ledger_path = base / "ledger.json"
            contract_path = base / "contract.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            if contract is None:
                contract = {
                    "version": "v3.1",
                    "target_races": 20,
                    "alpha": 0.05,
                    "max_candidate_fraction": 0.65,
                }
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--ledger", str(ledger_path),
                 "--contract", str(contract_path)],
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
