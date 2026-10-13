import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "v31_verify_freeze.py"

FIXTURE_PATHS = [
    "docs/v31-holdout-freeze.json",
    "docs/v31-holdout-ledger.json",
    "docs/v31-holdout-attempt-ledger.json",
    "docs/v31-candidate-generation-protocol.md",
    "docs/v31-holdout-operations.md",
    "scripts/v31_candidate_channels.py",
    "tests/test_v31_candidate_channels.py",
    "scripts/v31_holdout.py",
    "tests/test_v31_holdout.py",
    "scripts/v31_prepare_snapshot.py",
    "tests/test_v31_prepare_snapshot.py",
    "scripts/v31_evaluate_holdout.py",
    "tests/test_v31_evaluate_holdout.py",
    "scripts/v31_attempt_ledger.py",
    "tests/test_v31_attempt_ledger.py",
    "docs/v31-holdout-decision-contract.json",
    "data/2026-10-12/v3-quality-tier-map.json",
]


class V31FreezeIntegrityTests(unittest.TestCase):
    def run_verify(self, root: Path):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo-root", str(root)],
            text=True,
            capture_output=True,
        )

    def copy_fixture(self, target: Path):
        for relative in FIXTURE_PATHS:
            src = ROOT / relative
            dst = target / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def test_current_repo_matches_freeze_manifest(self):
        run = self.run_verify(ROOT)
        self.assertEqual(run.returncode, 0, run.stderr)
        payload = json.loads(run.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["version"], "v3.1")
        self.assertEqual(payload["ledger_entries"], 0)

    def test_mutated_frozen_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_fixture(root)
            path = root / "scripts/v31_holdout.py"
            path.write_text(path.read_text(encoding="utf-8") + "\n# mutation\n", encoding="utf-8")
            run = self.run_verify(root)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("frozen_blob_mismatch:holdout_wrapper", run.stderr)

    def test_mutated_decision_contract_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_fixture(root)
            path = root / "docs/v31-holdout-decision-contract.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["primary_test"]["alpha"] = 0.1
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            run = self.run_verify(root)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("frozen_blob_mismatch:decision_contract", run.stderr)

    def test_changed_quality_baseline_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_fixture(root)
            path = root / "data/2026-10-12/v3-quality-tier-map.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["tiers"]["NZT"] = "GI"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            run = self.run_verify(root)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("quality_baseline_changed:NZT", run.stderr)

    def test_attempt_ledger_manifest_pointer_is_rejected_when_changed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_fixture(root)
            path = root / "docs/v31-holdout-attempt-ledger.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["manifest_blob_sha"] = "0" * 40
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            run = self.run_verify(root)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("attempt_ledger_manifest_mismatch", run.stderr)

    def test_ledger_manifest_pointer_is_rejected_when_changed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.copy_fixture(root)
            path = root / "docs/v31-holdout-ledger.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["manifest_blob_sha"] = "0" * 40
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            run = self.run_verify(root)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("ledger_manifest_mismatch", run.stderr)


if __name__ == "__main__":
    unittest.main()
