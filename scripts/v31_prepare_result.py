#!/usr/bin/env python3
"""Prepare a source-backed v3.1 result.json from captured official JRA result text."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


RACE_ID_RE = re.compile(
    r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})-KYOTO-(?P<race>\d{2})$"
)
PAGE_ID_RE = re.compile(
    r"レース結果\s*(?P<y>\d{4})年(?P<m>\d{1,2})月(?P<d>\d{1,2})日"
    r"[\s\S]*?京都[\s\S]*?(?P<race>\d{1,2})レース"
)
TOP_ROW_RE = re.compile(
    r"^\|\s*(?P<rank>[123])\s*\|[^|]*\|\s*(?P<number>\d+)\s*\|",
    re.MULTILINE,
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_aware_iso(value: str, label: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid_datetime:{label}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"naive_datetime:{label}")
    return dt


def _validate_jra_url(value: str) -> None:
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"www.jra.go.jp", "jra.go.jp"}
        or not parsed.path.startswith("/JRADB/accessS.html")
    ):
        raise ValueError("non_jra_result_source")


def _race_identity(race_id: str) -> tuple[int, int, int, int]:
    match = RACE_ID_RE.fullmatch(race_id or "")
    if not match:
        raise ValueError("invalid_race_id")
    return tuple(int(match.group(k)) for k in ("y", "m", "d", "race"))


def _page_identity(text: str) -> tuple[int, int, int, int]:
    match = PAGE_ID_RE.search(text)
    if not match:
        raise ValueError("result_page_identity_missing")
    return tuple(int(match.group(k)) for k in ("y", "m", "d", "race"))


def _parse_top3(text: str) -> list[int]:
    by_rank: dict[int, int] = {}
    for match in TOP_ROW_RE.finditer(text):
        rank = int(match.group("rank"))
        number = int(match.group("number"))
        if rank in by_rank:
            raise ValueError("duplicate_result_rank")
        by_rank[rank] = number
    if set(by_rank) != {1, 2, 3}:
        raise ValueError("result_top3_incomplete")
    top3 = [by_rank[i] for i in (1, 2, 3)]
    if len(set(top3)) != 3:
        raise ValueError("duplicate_result_horse")
    return top3


def prepare(capture: dict) -> dict:
    race_id = capture.get("race_id")
    source_url = capture.get("source_url")
    observed_at_jst = capture.get("observed_at_jst")
    text = capture.get("text")

    if not isinstance(source_url, str):
        raise ValueError("missing_result_source_url")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("missing_result_source_text")
    if not isinstance(observed_at_jst, str):
        raise ValueError("missing_result_observed_at")
    parse_aware_iso(observed_at_jst, "observed_at_jst")
    _validate_jra_url(source_url)

    expected = _race_identity(race_id)
    observed = _page_identity(text)
    if expected != observed:
        raise ValueError("result_page_race_mismatch")

    return {
        "schema_version": 1,
        "race_id": race_id,
        "top3": _parse_top3(text),
        "source": {
            "provider": "JRA",
            "url": source_url,
            "observed_at_jst": observed_at_jst,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        write_json(args.output, prepare(read_json(args.capture)))
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
