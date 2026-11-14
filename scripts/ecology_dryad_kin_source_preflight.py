#!/usr/bin/env python3
"""Rights-conscious source preflight for the Wilson/Sharman 2022 Dryad release.

Downloads into ephemeral runner memory only; emits no individual observations.
This does NOT run an equine relatedness analysis or claim source readiness.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
import zipfile

DOI = "10.5061/dryad.qbzkh18m0"
BASE = "https://datadryad.org"
META = BASE + "/api/v2/datasets/doi%3A10.5061%2Fdryad.qbzkh18m0"
FILES = {
    "readme": [
        BASE + "/api/v2/files/1885334/download",
        BASE + "/downloads/file_stream/1885334",
    ],
    "archive": [
        BASE + "/api/v2/files/1885332/download",
        BASE + "/downloads/file_stream/1885332",
    ],
}
MAX_META = 2_000_000
MAX_README = 40_000
MAX_ZIP = 25_000_000
MAX_UNPACKED = 500_000_000


def fetch(url: str, limit: int) -> tuple[bytes | None, str]:
    assert url.startswith(BASE + "/") and "@" not in url
    req = urllib.request.Request(url, headers={
        "User-Agent": "keiba-ecology-source-audit/1.0 (research, no republication)",
        "Accept": "application/octet-stream, application/json;q=0.9, */*;q=0.5",
    })
    try:
        with urllib.request.urlopen(req, timeout=35) as res:
            if not res.geturl().startswith("https://"):
                return None, "HOLD_UNSAFE_REDIRECT"
            length = res.headers.get("Content-Length", "")
            if length.isdigit() and int(length) > limit:
                return None, "HOLD_SIZE_LIMIT"
            body = res.read(limit + 1)
            if len(body) > limit:
                return None, "HOLD_SIZE_LIMIT"
            return body, "OK"
    except urllib.error.HTTPError as ex:
        return None, "HOLD_HTTP_" + str(ex.code)
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        # A failure label is enough; do not echo runner network headers/host paths.
        return None, "HOLD_TRANSPORT_" + type(ex).__name__


def choose(urls: list[str], limit: int) -> tuple[bytes | None, list[str]]:
    errors = []
    for url in urls:
        body, state = fetch(url, limit)
        if body is not None:
            return body, errors
        errors.append(state)
    return None, errors


def archive_info(data: bytes) -> dict:
    if not zipfile.is_zipfile(io.BytesIO(data)):
        return {"status": "HOLD_INVALID_ZIP"}
    with zipfile.ZipFile(io.BytesIO(data)) as handle:
        members = [x for x in handle.infolist() if not x.is_dir()]
        total = sum(x.file_size for x in members)
        if total > MAX_UNPACKED or len(members) > 300:
            return {"status": "HOLD_ZIP_BOMB_LIMIT"}
        result = []
        for item in members:
            if item.file_size > MAX_UNPACKED or item.is_dir():
                continue
            suffix = Path(item.filename).suffix.lower()
            record = {
                "filename": Path(item.filename).name[:140],
                "extension": suffix,
                "compressed_bytes": item.compress_size,
                "uncompressed_bytes": item.file_size,
            }
            if suffix in (".csv", ".tsv", ".txt", ".dat", ".ped", ".as", ".r") and item.file_size:
                # Read only the *very first line*, never sample individuals.
                with handle.open(item) as fd:
                    head = fd.readline(1024)
                if b"\x00" not in head:
                    for delim in (",", "\t", " "):
                        fields = head.decode("utf-8-sig", "replace").strip().split(delim)
                        if 3 <= len(fields) <= 75 and all(
                            bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_./()-]{0,48}", f.strip()))
                            for f in fields
                        ):
                            record["header_if_clearly_textual"] = [f.strip() for f in fields]
                            break
            result.append(record)
        return {
            "status": "ARCHIVE_STRUCTURE_OBSERVED_ONLY",
            "archive_sha256": hashlib.sha256(data).hexdigest(),
            "member_count": len(members),
            "total_uncompressed_bytes": total,
            "member_schema": result,
            "no_individual_rows_printed_or_saved": True,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta, meta_status = fetch(META, MAX_META)
    metadata = {"status": meta_status}
    if meta is not None:
        try:
            j = json.loads(meta)
            metadata = {
                "status": "METADATA_AVAILABLE",
                "doi": DOI,
                "id": j.get("id"),
                "versionNumber": j.get("versionNumber"),
                "publicationDate": j.get("publicationDate"),
                "license": j.get("license"),
            }
        except (ValueError, TypeError):
            metadata = {"status": "HOLD_INVALID_JSON"}
    readme, readme_errors = choose(FILES["readme"], MAX_README)
    archive, archive_errors = choose(FILES["archive"], MAX_ZIP)
    report = {
        "audit_utc": datetime.now(timezone.utc).date().isoformat(),
        "doi": DOI,
        "evidence_class": "PUBLIC_SOURCE_STRUCTURE_ONLY_NO_BIOLOGICAL_TEST",
        "metadata": metadata,
        "readme": (
            {"status": "README_DOWNLOAD_AVAILABLE",
             "bytes": len(readme), "sha256": hashlib.sha256(readme).hexdigest()}
            if readme is not None else
            {"status": "HOLD_UNAVAILABLE", "attempt_statuses": readme_errors}
        ),
        "archive": (
            archive_info(archive) if archive is not None else
            {"status": "HOLD_UNAVAILABLE", "attempt_statuses": archive_errors}
        ),
        "source_race_start_clock_confirmed": False,
        "source_horse_id_pedigree_join_confirmed": False,
        "source_data_license_fully_audited": False,
        "focal_first_gps_phenotype_available": False,
        "real_relationship_predictive_gain_estimated": False,
        "no_input_rows_logged_or_committed": True,
    }
    report["status"] = (
        "SCHEMA_PREVIEW_ONLY_NO_KIN_PREDICTION" if
        report["archive"]["status"] == "ARCHIVE_STRUCTURE_OBSERVED_ONLY" else
        "HOLD_SOURCE_DOWNLOAD_OR_SCHEMA"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
