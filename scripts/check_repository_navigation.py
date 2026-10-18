#!/usr/bin/env python3
"""Validate research-first repo navigation without changing any research result.

This checker is deliberately stdlib-only. It checks the two-track source map,
the EXISTING frozen v3.1 classifier Git blob, original scientific claim
categories, and relative Markdown links after archiving the old README.

It must not read actual source horse IDs/GPS timing rows, change frozen
prediction rules, fetch the network, or call GitHub APIs.
"""
from __future__ import annotations

import argparse
from hashlib import sha1
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "docs/repository-map.json"
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\n]+)\)")
TRACKS = ("ecology", "betting")
STATUSES = {
    "OBSERVED_SOURCE_CONDITIONAL",
    "OBSERVED_NONTRANSFER",
    "HOLD_NONIDENTIFIABLE",
    "HOLD_SOURCE_COVERAGE",
    "HOLD_SOURCE_PROVENANCE",
    "HOLD_MEASUREMENT",
    "SIMULATION_ONLY",
    "UNTESTED",
}
SCIENTIFIC_GUARDS = {
    "R2": "OBSERVED_SOURCE_CONDITIONAL",
    "R5": "OBSERVED_NONTRANSFER",
    "R6": "HOLD_NONIDENTIFIABLE",
    "R7": "HOLD_NONIDENTIFIABLE",
    "R8": "HOLD_NONIDENTIFIABLE",
    "R9": "SIMULATION_ONLY",
    "R10": "HOLD_SOURCE_PROVENANCE",
    "R11": "HOLD_MEASUREMENT",
}
NAVIGATION_DOCS = [
    "README.md",
    "docs/research/README.md",
    "docs/research/EVIDENCE_MATRIX.md",
    "docs/research/REPRODUCIBILITY.md",
    "docs/research/ROADMAP.md",
    "docs/betting/README.md",
    "docs/archive/README-main-before-reorganization-20261018.md",
]


def git_blob_sha(data: bytes) -> str:
    """Git's blob SHA-1, NOT the ordinary SHA-1 of raw file bytes."""
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def _repo_file(root: Path, raw_path: str) -> tuple[Path | None, str | None]:
    if not isinstance(raw_path, str) or not raw_path or raw_path.startswith("/"):
        return None, f"not a repository-relative path: {raw_path!r}"
    if urlsplit(raw_path).scheme or "://" in raw_path:
        return None, f"external URL cannot substitute for source file: {raw_path}"
    base = root.resolve()
    resolved = (base / raw_path).resolve()
    if not resolved.is_relative_to(base):
        return None, f"path escapes repository root: {raw_path}"
    if not resolved.is_file():
        return None, f"missing indexed repository file: {raw_path}"
    return resolved, None


def manifest_errors(manifest: dict, root: Path) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("unsupported repository map schema")
    if manifest.get("primary_track") != "ecology":
        errors.append("ecology must remain the main research entrypoint")
    tracks = manifest.get("tracks", {})
    if not isinstance(tracks, dict) or set(tracks) != set(TRACKS):
        return errors + ["research and betting must have exactly two separate tracks"]

    def check_file(label: str, path: str) -> Path | None:
        valid, err = _repo_file(root, path)
        if err:
            errors.append(f"{label}: {err}")
        return valid

    for track in TRACKS:
        entry = tracks[track]
        if not isinstance(entry, dict):
            errors.append(f"malformed {track} track")
            continue
        for key, raw in entry.items():
            if key in ("test_prefix", "separate_draft_pr"):
                continue
            if isinstance(raw, str):
                check_file(f"{track}.{key}", raw)
            elif isinstance(raw, list):
                for idx, f in enumerate(raw):
                    check_file(f"{track}.{key}[{idx}]", f)
            else:
                errors.append(f"{track}.{key} unexpected value type")
    ecology = tracks["ecology"]
    betting = tracks["betting"]
    if ecology.get("test_prefix") != "test_ecology_":
        errors.append("ecological test prefix was silently changed")
    if not isinstance(betting.get("separate_draft_pr"), str) or not betting[
        "separate_draft_pr"
    ].startswith("https://github.com/zuizui0223/keiba/pull/"):
        errors.append("betting draft PR must remain a separately linked reference")
    if any(not path.startswith("scripts/ecology_") for path in ecology["code_examples"]):
        errors.append("ecology code examples contain non-ecology model scripts")
    if not betting.get("classifier", "").startswith("scripts/v31_"):
        errors.append("betting classifier is no longer in the frozen betting suite")

    if not isinstance(manifest.get("scientific_status_categories"), list):
        errors.append("scientific status category list is not a list")
    elif set(manifest["scientific_status_categories"]) != STATUSES:
        errors.append("scientific statuses were changed without updating gates")
    records = manifest.get("research_evidence", [])
    if not isinstance(records, list):
        return errors + ["research_evidence must be a list"]
    seen_ids: set[str] = set()
    found: dict[str, str] = {}
    for row in records:
        evidence_id = row.get("id") if isinstance(row, dict) else None
        status = row.get("status") if isinstance(row, dict) else None
        if not evidence_id or evidence_id in seen_ids:
            errors.append(f"duplicate or missing research evidence ID: {evidence_id!r}")
        else:
            seen_ids.add(evidence_id)
        if status not in STATUSES:
            errors.append(f"unsupported scientific evidence status {evidence_id}: {status}")
        else:
            found[evidence_id] = status
        if isinstance(row, dict):
            check_file(f"research evidence {evidence_id}", row.get("primary_document"))
    for key, expected_status in SCIENTIFIC_GUARDS.items():
        if found.get(key) != expected_status:
            errors.append(
                f"{key} was silently promoted from {expected_status} "
                f"to {found.get(key)!r}"
            )
    if len(seen_ids) != len(records):
        errors.append("research evidence ID count differs from row count")

    archive = manifest.get("legacy_full_readme")
    if archive != "docs/archive/README-main-before-reorganization-20261018.md":
        errors.append("full legacy root README archive is not retained")
    valid_archive = check_file("legacy archive", archive)
    if valid_archive and len(valid_archive.read_text(encoding="utf-8")) < 9000:
        errors.append("archived former root README appears truncated")

    freeze = manifest.get("protected_frozen_v31", {})
    classifier_path = freeze.get("classifier_path")
    manifest_path = freeze.get("frozen_manifest_path")
    code = check_file("frozen betting classifier", classifier_path)
    locked = check_file("original frozen v3.1 manifest", manifest_path)
    if code and locked:
        digest = git_blob_sha(code.read_bytes())
        locked_json = json.loads(locked.read_text(encoding="utf-8"))
        declared = locked_json.get("frozen_blobs", {}).get("classifier")
        catalog = freeze.get("expected_git_blob_sha_at_index_creation")
        if digest != declared or digest != catalog:
            errors.append(
                "FROZEN_V31_CLASSIFIER_SHA_CHANGED: current Git blob, original "
                "holdout manifest and reorganization index must agree"
            )
    if freeze.get("no_current_retraining_or_threshold_change") is not True:
        errors.append("repository cleanup must never imply model retuning")

    return errors


def markdown_errors(text: str, source: Path, root: Path) -> list[str]:
    errors: list[str] = []
    base = root.resolve()
    for match in LINK_RE.finditer(text):
        raw_link = match.group(1).strip().split(maxsplit=1)[0]
        # Markdown titles following a target are uncommon; support no
        # network URLs or anchor checks in this static-source audit.
        if raw_link.startswith(("#", "mailto:", "//")):
            continue
        parsed = urlsplit(raw_link)
        if parsed.scheme:
            continue
        target_value = unquote(parsed.path)
        if not target_value:
            continue
        target = (source.parent / target_value).resolve()
        if not target.is_relative_to(base):
            errors.append(f"{source.relative_to(base)}: path escapes repo {raw_link}")
        elif not target.exists():
            errors.append(f"{source.relative_to(base)}: broken link {raw_link}")
    return errors


def navigation_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for path in NAVIGATION_DOCS:
        current, invalid = _repo_file(root, path)
        if invalid:
            errors.append(invalid)
        elif current:
            errors += markdown_errors(current.read_text(encoding="utf-8"), current, root)
    landing = root / "README.md"
    if landing.is_file():
        text = landing.read_text(encoding="utf-8")
        if len(text) > 5000:
            errors.append("root README grew past the 5000-character navigation cap")
        for required in (
            "docs/research/README.md",
            "docs/betting/README.md",
            "docs/research/EVIDENCE_MATRIX.md",
            "docs/archive/README-main-before-reorganization-20261018.md",
            "H1",
            "H2",
            "HOLD",
        ):
            if required not in text:
                errors.append(f"root README missing research-first pointer: {required}")
    return errors


def repository_errors(root: Path) -> list[str]:
    map_path = root / MANIFEST
    if not map_path.is_file():
        return [f"missing repository map: {MANIFEST}"]
    try:
        metadata = json.loads(map_path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        return [f"invalid repository navigation JSON: {exc}"]
    return manifest_errors(metadata, root) + navigation_errors(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=ROOT,
        help="Root of local checkout, default parent of scripts/",
    )
    args = parser.parse_args()
    errors = repository_errors(args.root.resolve())
    if errors:
        print("REPOSITORY_NAVIGATION_HOLD",len(errors),file=sys.stderr)
        for error in errors:
            print(" -",error,file=sys.stderr)
        return 1
    manifest = json.loads((args.root / MANIFEST).read_text(encoding="utf-8"))
    print(json.dumps({
        "status":"RESEARCH_FIRST_NAVIGATION_AND_FROZEN_BETTING_RULES_PASS",
        "primary_track":manifest["primary_track"],
        "tracked_scientific_claims":len(manifest["research_evidence"]),
        "navigation_documents_checked":len(NAVIGATION_DOCS),
        "protected_v31_classifier_git_blob":
            manifest["protected_frozen_v31"][
                "expected_git_blob_sha_at_index_creation"],
        "no_source_data_or_betting_rules_modified":True,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
