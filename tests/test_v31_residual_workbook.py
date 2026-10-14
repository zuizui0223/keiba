"""Residual audit templates based only on validated, immutable v3.1 evidence."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def save(path: Path, obj: dict):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ResidualAuditTests(unittest.TestCase):
    def run_script(self, name: str, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / name), *map(str, args)],
            cwd=ROOT, text=True, capture_output=True,
        )

    def make_case(self, directory: Path, result_top3=None):
        result_top3 = result_top3 or [5, 1, 2]
        race_id = "2026-10-18-KYOTO-07"
        source_horses = [
            {
                "number": n, "name": f"馬{n}", "age": 3 if n == 5 else 4,
                "career_starts_before_target": 6 if n == 5 else 10,
                "last4": [{
                    "date": "2026-09-01", "venue": "阪神", "surface": "ダ",
                    "distance_m": 1800, "class_rank": 1, "finish": n,
                    "margin_sec": 0.1 * n,
                }],
                "full_history_before_target": [{
                    "date": "2026-09-01", "venue": "阪神", "surface": "ダ",
                    "distance_m": 1800, "class_rank": 1, "finish": n,
                    "race_name": "1勝クラス", "jockey": "騎手",
                }],
            }
            for n in range(1, 7)
        ]
        save(directory/"race-input.json", {
            "race_id": race_id, "horses": source_horses,
        })
        save(directory/"source-meta.json", {
            "race_id": race_id,
            "card_sha256": "abc123",
            "active_horse_numbers": [1,2,3,4,5,6],
            "uses_target_race_results": False,
        })
        odds = [2.0,3.0,4.0,10.0,15.0,20.0]
        horses = []
        for n in range(1,7):
            m = n <= 3
            c = n == 4
            horses.append({
                "number":n, "name":f"馬{n}", "frozen_win_odds":odds[n-1],
                "M":m,"C1":c,"U":False,"Q1":False,"K1":False,
                "rescue":False,"union":m or c,
                "K_wins":0,"K_top3":0,
                "uncertainty_flags":["first_exact_distance"] if n == 5 else [],
            })
        save(directory/"freeze.json", {
            "race_id": race_id, "holdout_version": "v3.1",
            "date":"2026-10-18", "venue":"京都",
            "scheduled_start_jst":"2026-10-18T13:25:00+09:00",
            "freeze_observed_at_jst":"2026-10-18T13:05:00+09:00",
            "odds_observed_at_jst":"2026-10-18T13:04:00+09:00",
            "uses_target_race_results":False,
            "field_size":6,"candidate_count":4,"candidate_fraction":4/6,
            "sets":{
                "M":[1,2,3],"C1":[4],"U":[],"Q1":[],"K1":[],
                "rescue":[],"union":[1,2,3,4],
            },
            "horses":horses,
            "integrity":{
                "race_input_sha256":file_sha(directory/"race-input.json"),
                "source_capture_meta_sha256":file_sha(directory/"source-meta.json"),
            },
        })
        save(directory/"result.json", {
            "race_id":race_id,"top3":result_top3,
        })
        run = self.run_script(
            "v31_holdout.py","score","--freeze",directory/"freeze.json",
            "--result",directory/"result.json","--output",directory/"score.json",
        )
        self.assertEqual(run.returncode,0,run.stderr)
        save(directory/"attempts.json",{
            "version":"v3.1","entries":[{
                "race_id":race_id,"status":"FROZEN",
                "scheduled_start_jst":"2026-10-18T13:25:00+09:00",
                "freeze_sha256":file_sha(directory/"freeze.json"),
            }],
        })
        return directory

    def audit(self, directory):
        return self.run_script(
            "v31_residual_workbook.py",
            "--freeze",directory/"freeze.json",
            "--result",directory/"result.json",
            "--score",directory/"score.json",
            "--attempt-ledger",directory/"attempts.json",
            "--race-input",directory/"race-input.json",
            "--source-meta",directory/"source-meta.json",
            "--output",directory/"residual.json",
        )

    def test_one_miss_remains_unreviewed_not_posthoc_explained(self):
        with tempfile.TemporaryDirectory() as td:
            base=self.make_case(Path(td))
            run=self.audit(base)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads((base/"residual.json").read_text(encoding="utf-8"))
            self.assertFalse(data["affects_formal_score"])
            self.assertEqual(data["coverage"]["union_top3_hits"],2)
            self.assertEqual(data["coverage"]["union_miss_count"],1)
            self.assertEqual(data["coverage"]["non_top3_union_candidates"],2)
            miss=data["misses"][0]
            self.assertEqual(miss["horse_number"],5)
            self.assertEqual(miss["actual_finish"],1)
            self.assertEqual(miss["frozen_market_rank"],5)
            self.assertEqual(miss["frozen_win_odds"],15.0)
            self.assertEqual(miss["frozen_membership"]["union"],False)
            self.assertEqual(miss["pre_race_history"]["career_starts_before_target"],6)
            self.assertEqual(miss["review"]["classification"],"UNREVIEWED")
            self.assertIsNone(miss["review"]["unexplained_remainder"])
            self.assertIn("first_exact_distance", miss["uncertainty_flags"])
            self.assertEqual(len(miss["pre_race_history"]["last4"]),1)

    def test_no_miss_still_records_candidate_burden(self):
        with tempfile.TemporaryDirectory() as td:
            base=self.make_case(Path(td),[1,2,3])
            run=self.audit(base)
            self.assertEqual(run.returncode,0,run.stderr)
            data=json.loads((base/"residual.json").read_text(encoding="utf-8"))
            self.assertEqual(data["misses"],[])
            self.assertEqual(data["coverage"]["union_miss_count"],0)
            self.assertEqual(data["coverage"]["non_top3_union_candidates"],1)

    def test_rejects_tampered_score_before_writing_report(self):
        with tempfile.TemporaryDirectory() as td:
            base=self.make_case(Path(td))
            path=base/"score.json"
            score=json.loads(path.read_text(encoding="utf-8"))
            score["union_top3_hits"]=3
            save(path,score)
            run=self.audit(base)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("score_union_hits_mismatch",run.stderr)
            self.assertFalse((base/"residual.json").exists())

    def test_rejects_modified_pre_race_history_after_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            base=self.make_case(Path(td))
            path=base/"race-input.json"
            raw=json.loads(path.read_text(encoding="utf-8"))
            raw["horses"][4]["career_starts_before_target"]=5
            save(path,raw)
            run=self.audit(base)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("race_input_hash_mismatch",run.stderr)

    def test_rejects_modified_source_capture_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            base=self.make_case(Path(td))
            path=base/"source-meta.json"
            raw=json.loads(path.read_text(encoding="utf-8"))
            raw["card_sha256"]="altered"
            save(path,raw)
            run=self.audit(base)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("source_meta_hash_mismatch",run.stderr)


if __name__=="__main__":
    unittest.main()
