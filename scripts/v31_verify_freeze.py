#!/usr/bin/env python3
"""Verify that the frozen v3.1 holdout contract still matches repository files."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


FROZEN_PATHS = {
    "protocol": "docs/v31-candidate-generation-protocol.md",
    "classifier": "scripts/v31_candidate_channels.py",
    "tests": "tests/test_v31_candidate_channels.py",
    "holdout_wrapper": "scripts/v31_holdout.py",
    "holdout_tests": "tests/test_v31_holdout.py",
    "operations": "docs/v31-holdout-operations.md",
    "snapshot_preparer": "scripts/v31_prepare_snapshot.py",
    "snapshot_preparer_tests": "tests/test_v31_prepare_snapshot.py",
    "evaluator": "scripts/v31_evaluate_holdout.py",
    "evaluator_tests": "tests/test_v31_evaluate_holdout.py",
    "decision_contract": "docs/v31-holdout-decision-contract.json",
    "attempt_ledger_tool": "scripts/v31_attempt_ledger.py",
    "attempt_ledger_tests": "tests/test_v31_attempt_ledger.py",
    "postrace_validator": "scripts/v31_validate_postrace.py",
    "pipeline_integration_tests": "tests/test_v31_pipeline_integration.py",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify_repo(root: Path) -> dict:
    manifest_path = root / "docs/v31-holdout-freeze.json"
    ledger_path = root / "docs/v31-holdout-ledger.json"
    attempt_ledger_path = root / "docs/v31-holdout-attempt-ledger.json"
    quality_path = root / "data/2026-10-12/v3-quality-tier-map.json"

    manifest = read_json(manifest_path)
    ledger = read_json(ledger_path)
    attempt_ledger = read_json(attempt_ledger_path)
    quality = read_json(quality_path)

    if manifest.get("status") != "frozen_for_prospective_holdout":
        raise ValueError("manifest_not_frozen")

    frozen = manifest.get("frozen_blobs", {})
    checked = {}
    for key, relative in FROZEN_PATHS.items():
        expected = frozen.get(key)
        if expected is None:
            continue
        path = root / relative
        if not path.exists():
            raise ValueError(f"frozen_file_missing:{key}")
        actual = git_blob_sha(path)
        checked[key] = actual
        if actual != expected:
            raise ValueError(f"frozen_blob_mismatch:{key}:{actual}")

    tiers = quality.get("tiers", quality)
    baseline = manifest.get("metadata_inputs", {}).get("quality_tier_baseline", {})
    for race_name, expected in baseline.items():
        if tiers.get(race_name) != expected:
            raise ValueError(f"quality_baseline_changed:{race_name}")

    manifest_blob = git_blob_sha(manifest_path)
    if ledger.get("manifest_blob_sha") != manifest_blob:
        raise ValueError("ledger_manifest_mismatch")
    if attempt_ledger.get("manifest_blob_sha") != manifest_blob:
        raise ValueError("attempt_ledger_manifest_mismatch")
    if ledger.get("version") != manifest.get("version"):
        raise ValueError("ledger_version_mismatch")
    if attempt_ledger.get("version") != manifest.get("version"):
        raise ValueError("attempt_ledger_version_mismatch")
    if int(ledger.get("target_races", -1)) != int(manifest.get("holdout_target_races", -2)):
        raise ValueError("ledger_target_races_mismatch")

    manifest_eligibility = manifest.get("eligibility", {})
    ledger_eligibility = ledger.get("eligibility", {})
    for key in ("venue", "min_class_rank", "exclude_2yo_only"):
        if key in manifest_eligibility and ledger_eligibility.get(key) != manifest_eligibility.get(key):
            raise ValueError(f"ledger_eligibility_mismatch:{key}")

    entries = list(ledger.get("entries", []))
    if len(entries) > int(manifest.get("holdout_target_races", 20)):
        raise ValueError("ledger_over_target")

    return {
        "valid": True,
        "version": manifest.get("version"),
        "manifest_blob_sha": manifest_blob,
        "ledger_entries": len(entries),
        "holdout_target_races": manifest.get("holdout_target_races"),
        "checked_frozen_blobs": checked,
        "quality_baseline_count": len(baseline),
        "quality_tier_count": len(tiers),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        result = verify_repo(args.repo_root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
