"""End-to-end integration tests for the frozen v3.1 pipeline using synthetic races.

This test never writes to the production ledgers or counts as a holdout.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

CARD = """\
|  | 1 | アルファ  **2.0**(1番人気)  500kg(+4) owner | 牡4/鹿 57.0kg 武 豊 | 2026年9月1日 阪神 1勝クラス 2着 12頭1番2番人気 武 豊 57.0kg 1800ダ 1:52.0 良 496kg 3F 37.0 ベータ(0.2) |  |  |  |
|  | 2 | ベータ  **3.0**(2番人気)  470kg(-2) owner | 牝4/栗 56.0kg 西村 淳也 | 2026年8月2日 中京 1勝クラス 4着 14頭2番4番人気 西村 淳也 56.0kg 1900ダ 2:01.0 良 472kg 3F 38.0 デルタ(0.6) |  |  |  |
|  | 3 | ガンマ  **4.0**(3番人気)  490kg(+0) owner | 牡5/黒鹿 58.0kg 幸 英明 | 2026年7月1日 京都 1勝クラス 6着 10頭3番5番人気 幸 英明 58.0kg 1800ダ 1:55.0 良 490kg 3F 38.0 アルファ(1.4) |  |  |  |
|  | 4 | デルタ  **15.0**(4番人気)  456kg(+2) owner | 牡3/鹿 57.0kg 田口 貫太 | 2026年9月1日 阪神 未勝利 1着 16頭2番6番人気 田口 貫太 57.0kg 1800ダ 1:54.0 良 454kg 3F 37.0 ベータ(0.1) |  |  |  |
|  | 5 | 取消馬  **50.0**(5番人気)  440kg(+0) owner | 牡4/鹿 57.0kg 騎手 | 取消 |  |  |  |
"""

RESULT_TEXT = """\
# レース結果2026年10月18日（日曜）4回京都7日 7レース

発走時刻：**13時25分**

| 着順 | 枠 | 馬 番 | 馬名 | 性齢 | 負担 重量 | 騎手名 | タイム |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 |  | 4 | デルタ | 牡3 | 57.0 | 田口 貫太 | 1:52.0 |
| 2 |  | 1 | アルファ | 牡4 | 57.0 | 武 豊 | 1:52.1 |
| 3 |  | 2 | ベータ | 牝4 | 56.0 | 西村 淳也 | 1:52.3 |
| 4 |  | 3 | ガンマ | 牡5 | 58.0 | 幸 英明 | 1:52.5 |
"""

def profile(name, finish, age_class="3歳上1勝クラス"):
    return (
        f"| 2026年9月1日 | 阪神 | {age_class} | ダ1800 | 良 | 16 | 3 | "
        f"{finish} | 武 豊 | 57 | 490 | 1:54.0 |  | {name} |\n"
    )


class V31RealPipelineTests(unittest.TestCase):
    def run_script(self, name, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / name), *map(str, args)],
            cwd=ROOT, capture_output=True, text=True,
        )

    def setup_case(self, base):
        capture = {
            "race": {
                "race_id": "2026-10-18-KYOTO-07",
                "date": "2026-10-18",
                "venue": "京都",
                "race_number": 7,
                "age_scope": "3yo+",
                "scheduled_start_jst": "2026-10-18T13:25:00+09:00",
                "target": {"surface": "ダ", "distance_m": 1800, "class_rank": 1},
            },
            "card": {"url": "https://www.jra.go.jp/JRADB/accessD.html?CNAME=fixture-card", "text": CARD},
            "profiles": {
                str(n): {"url": f"https://www.jra.go.jp/JRADB/accessU.html?CNAME=fixture-horse-{n}",
                         "text": profile(n, 1 if n == 4 else 2,
                                         "3歳未勝利" if n == 4 else "3歳上1勝クラス")}
                for n in range(1, 5)
            },
        }
        (base / "capture.json").write_text(
            json.dumps(capture, ensure_ascii=False), encoding="utf-8"
        )
        r = self.run_script(
            "v31_prepare_snapshot.py", "--capture", base / "capture.json",
            "--observed-at-jst", "2026-10-18T13:05:00+09:00",
            "--output-dir", base
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_script(
            "v31_holdout.py", "freeze", "--race-input", base / "race-input.json",
            "--odds", base / "odds.json",
            "--source-meta", base / "source-capture-meta.json",
            "--quality-map", ROOT / "data/2026-10-12/v3-quality-tier-map.json",
            "--manifest", ROOT / "docs/v31-holdout-freeze.json",
            "--classifier", SCRIPTS / "v31_candidate_channels.py",
            "--observed-at-jst", "2026-10-18T13:06:00+09:00",
            "--output", base / "freeze.json",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        frozen = json.loads((base / "freeze.json").read_text(encoding="utf-8"))
        self.assertEqual(frozen["sets"]["M"], [1, 2, 3])
        self.assertIn(4, frozen["sets"]["U"])
        self.assertIn(4, frozen["sets"]["union"])
        self.assertFalse(frozen["uses_target_race_results"])

        event = {
            "race_id": frozen["race_id"],
            "scheduled_start_jst": frozen["scheduled_start_jst"],
            "status": "FROZEN",
            "freeze_sha256": hashlib.sha256((base / "freeze.json").read_bytes()).hexdigest(),
        }
        (base / "attempt-event.json").write_text(json.dumps(event), encoding="utf-8")
        (base / "attempt-in.json").write_text(json.dumps({
            "version": "v3.1", "entries": [],
        }), encoding="utf-8")
        r = self.run_script(
            "v31_attempt_ledger.py", "register", "--ledger", base / "attempt-in.json",
            "--event", base / "attempt-event.json", "--output", base / "attempts.json",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        return frozen

    def score_case(self, base):
        result_capture = {
            "race_id": "2026-10-18-KYOTO-07",
            "source_url": "https://www.jra.go.jp/JRADB/accessS.html?CNAME=example",
            "observed_at_jst": "2026-10-18T13:35:00+09:00",
            "text": RESULT_TEXT,
        }
        (base / "result-capture.json").write_text(
            json.dumps(result_capture, ensure_ascii=False), encoding="utf-8"
        )
        r = self.run_script(
            "v31_prepare_result.py",
            "--capture", base / "result-capture.json",
            "--output", base / "result.json",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_script(
            "v31_holdout.py", "score", "--freeze", base / "freeze.json",
            "--result", base / "result.json", "--output", base / "score.json",
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads((base / "score.json").read_text(encoding="utf-8"))

    def test_complete_pipeline_with_real_frozen_classifier(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self.setup_case(base)
            scored = self.score_case(base)
            self.assertEqual(scored["M_top3_hits"], 2)
            self.assertEqual(scored["union_top3_hits"], 3)
            self.assertTrue(scored["winner_in_union"])

            ledger = {"schema_version": 1, "version": "v3.1",
                      "target_races": 20, "entries": []}
            (base / "ledger-in.json").write_text(json.dumps(ledger), encoding="utf-8")
            r = self.run_script(
                "v31_holdout.py", "register", "--ledger", base / "ledger-in.json",
                "--freeze", base / "freeze.json", "--score", base / "score.json",
                "--result", base / "result.json",
                "--result-capture", base / "result-capture.json",
                "--attempt-ledger", base / "attempts.json",
                "--output", base / "ledger.json",
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            registered = json.loads((base / "ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(registered["summary"]["races_scored"], 1)

            r = self.run_script(
                "v31_evaluate_holdout.py",
                "--ledger", base / "ledger.json",
                "--attempt-ledger", base / "attempts.json",
                "--contract", ROOT / "docs/v31-holdout-decision-contract.json",
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            decision = json.loads(r.stdout)
            self.assertEqual(decision["decision"]["status"], "INCOMPLETE")
            self.assertEqual(decision["technical_evaluability"]["freeze_success_rate"], 1.0)

    def test_register_rejects_tampered_score_even_if_race_ids_match(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self.setup_case(base)
            self.score_case(base)
            data = json.loads((base / "score.json").read_text(encoding="utf-8"))
            data["union_top3_hits"] = 0
            (base / "score.json").write_text(json.dumps(data), encoding="utf-8")
            (base / "ledger-in.json").write_text(
                json.dumps({"schema_version": 1, "version": "v3.1",
                            "target_races": 20, "entries": []}), encoding="utf-8"
            )
            r = self.run_script(
                "v31_holdout.py", "register",
                "--ledger", base / "ledger-in.json",
                "--freeze", base / "freeze.json",
                "--result", base / "result.json",
                "--result-capture", base / "result-capture.json",
                "--score", base / "score.json",
                "--attempt-ledger", base / "attempts.json",
                "--output", base / "ledger.json",
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("score_union_hits_mismatch", r.stderr)
            self.assertFalse((base / "ledger.json").exists())

    def test_postrace_validation_accepts_real_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self.setup_case(base)
            self.score_case(base)
            r = self.run_script(
                "v31_validate_postrace.py",
                "--freeze", base / "freeze.json",
                "--result", base / "result.json",
                "--result-capture", base / "result-capture.json",
                "--score", base / "score.json",
                "--attempt-ledger", base / "attempts.json",
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            valid = json.loads(r.stdout)
            self.assertTrue(valid["valid"])
            self.assertEqual(valid["union_top3_hits"], 3)

    def test_postrace_validation_rejects_tampered_score(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self.setup_case(base)
            self.score_case(base)
            scored = json.loads((base / "score.json").read_text(encoding="utf-8"))
            scored["union_top3_hits"] = 0
            (base / "score.json").write_text(json.dumps(scored), encoding="utf-8")
            r = self.run_script(
                "v31_validate_postrace.py",
                "--freeze", base / "freeze.json",
                "--result", base / "result.json",
                "--result-capture", base / "result-capture.json",
                "--score", base / "score.json",
                "--attempt-ledger", base / "attempts.json",
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("score_union_hits_mismatch", r.stderr)

    def test_postrace_validation_rejects_tampered_result_capture(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self.setup_case(base)
            self.score_case(base)
            capture = json.loads((base / "result-capture.json").read_text(encoding="utf-8"))
            capture["text"] = capture["text"].replace(
                "| 1 |  | 4 | デルタ", "| 1 |  | 3 | ガンマ"
            )
            (base / "result-capture.json").write_text(
                json.dumps(capture, ensure_ascii=False), encoding="utf-8"
            )
            r = self.run_script(
                "v31_validate_postrace.py",
                "--freeze", base / "freeze.json",
                "--result", base / "result.json",
                "--result-capture", base / "result-capture.json",
                "--score", base / "score.json",
                "--attempt-ledger", base / "attempts.json",
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("result_source_mismatch", r.stderr)

    def test_postrace_validation_rejects_wrong_attempt_hash(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            self.setup_case(base)
            self.score_case(base)
            ledger = json.loads((base / "attempts.json").read_text(encoding="utf-8"))
            ledger["entries"][0]["freeze_sha256"] = "0" * 64
            (base / "attempts.json").write_text(json.dumps(ledger), encoding="utf-8")
            r = self.run_script(
                "v31_validate_postrace.py",
                "--freeze", base / "freeze.json",
                "--result", base / "result.json",
                "--result-capture", base / "result-capture.json",
                "--score", base / "score.json",
                "--attempt-ledger", base / "attempts.json",
            )
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("attempt_freeze_hash_mismatch", r.stderr)


if __name__ == "__main__":
    unittest.main()
