"""Tests for the descriptive v3.1 equal-cardinality market comparator."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v31_equal_market_shadow.py"


def sample():
    freeze = {
        "schema_version": 1,
        "holdout_version": "v3.1",
        "race_id": "2026-10-17-KYOTO-07",
        "uses_target_race_results": False,
        "field_size": 6,
        "candidate_count": 4,
        "sets": {
            "M": [1, 2, 3],
            "C1": [], "U": [6], "rescue": [],
            "union": [1, 2, 3, 6],
        },
        "horses": [
            {"number": 1, "frozen_win_odds": 1.5},
            {"number": 2, "frozen_win_odds": 2.0},
            {"number": 3, "frozen_win_odds": 4.0},
            {"number": 4, "frozen_win_odds": 5.0},
            {"number": 5, "frozen_win_odds": 6.0},
            {"number": 6, "frozen_win_odds": 7.0},
        ],
    }
    result = {"race_id": freeze["race_id"], "top3": [6, 5, 1]}
    return freeze, result


class MarketShadowTests(unittest.TestCase):
    def run_case(self, freeze, result):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            fp=folder/"freeze.json";rp=folder/"result.json";op=folder/"shadow.json"
            fp.write_text(json.dumps(freeze, ensure_ascii=False), encoding="utf-8")
            rp.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            cmd=[sys.executable,str(SCRIPT),"--freeze",str(fp),
                 "--result",str(rp),"--output",str(op)]
            process=subprocess.run(cmd,text=True,capture_output=True)
            return process, json.loads(op.read_text()) if op.exists() else None

    def test_equal_size_market_comparator_reports_unique_rescues(self):
        freeze,result=sample()
        p,x=self.run_case(freeze,result)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(x["field_size"],6)
        self.assertEqual(x["candidate_count"],4)
        self.assertEqual(x["market_same_size"],[1,2,3,4])
        self.assertEqual(x["v31_candidate_set"],[1,2,3,6])
        self.assertEqual(x["actual_top3"],[6,5,1])
        self.assertEqual(x["v31_top3_hits"],2)
        self.assertEqual(x["market_same_size_top3_hits"],1)
        self.assertEqual(x["v31_minus_market_top3_hits"],1)
        self.assertEqual(x["v31_unique_top3"],[6])
        self.assertEqual(x["market_unique_top3"],[])
        self.assertTrue(x["v31_winner_in_candidates"])
        self.assertFalse(x["market_winner_in_candidates"])
        self.assertEqual(x["market_cutoff_ties"]["min_top3_hits"],1)
        self.assertEqual(x["market_cutoff_ties"]["max_top3_hits"],1)

    def test_market_cutoff_tie_sensitivity(self):
        freeze,result=sample()
        for i,n in enumerate([4,5,6],start=3):
            freeze["horses"][i]["frozen_win_odds"]=5.0
        result["top3"]=[5,6,1]
        p,x=self.run_case(freeze,result)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(x["market_same_size"],[1,2,3,4])
        self.assertEqual(x["market_cutoff_ties"]["tied_horses"],[4,5,6])
        self.assertEqual(x["market_cutoff_ties"]["min_top3_hits"],1)
        self.assertEqual(x["market_cutoff_ties"]["max_top3_hits"],2)

    def test_missing_frozen_odds_fails_closed(self):
        freeze,result=sample()
        del freeze["horses"][5]["frozen_win_odds"]
        p,x=self.run_case(freeze,result)
        self.assertNotEqual(p.returncode,0)
        self.assertIsNone(x)
        self.assertIn("missing_frozen_odds:6",p.stderr)

    def test_result_race_id_mismatch_fails_closed(self):
        freeze,result=sample()
        result["race_id"]="not_the_race"
        p,x=self.run_case(freeze,result)
        self.assertNotEqual(p.returncode,0)
        self.assertIsNone(x)
        self.assertIn("race_id_mismatch",p.stderr)

    def test_candidate_or_top3_duplicates_rejected(self):
        freeze,result=sample()
        freeze["sets"]["union"]=[1,2,2,6]
        p,x=self.run_case(freeze,result)
        self.assertNotEqual(p.returncode,0)
        self.assertIn("duplicate_union",p.stderr)
        freeze,result=sample()
        result["top3"]=[1,1,5]
        p,x=self.run_case(freeze,result)
        self.assertNotEqual(p.returncode,0)
        self.assertIn("invalid_top3",p.stderr)

    def test_shadow_does_not_write_into_inputs(self):
        freeze,result=sample()
        p,x=self.run_case(freeze,result)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse(x["confirmatory"])
        self.assertTrue(x["development_and_holdout_descriptive_only"])
        self.assertRegex(x["integrity"]["freeze_sha256"],r"^[0-9a-f]{64}$")
        self.assertRegex(x["integrity"]["result_sha256"],r"^[0-9a-f]{64}$")


if __name__=="__main__":
    unittest.main()
