#!/usr/bin/env python3
"""Result-only JRA source parser for prospective ticket scoring (no forecast access).

Fail closed unless the archived official result text identifies the same date,
venue and race number and has distinct 1/2/3 ranks. This parser expects the
readable, line-preserved JRA page capture format used by the existing
v31_prepare_result preparer. It must not guess from a pasted summary or odds.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

VENUE_CODES = {
    "TOKYO": "東京", "KYOTO": "京都", "FUKUSHIMA": "福島",
    "NAKAYAMA": "中山", "HANSHIN": "阪神",
    "CHUKYO": "中京", "NIIGATA": "新潟",
    "SAPPORO": "札幌", "HAKODATE": "函館",
    "KOKURA": "小倉",
}
RACE_ID = re.compile(
    r"^(?P<date>20\d{2}-\d{2}-\d{2})-"
    r"(?P<venue>TOKYO|KYOTO|FUKUSHIMA|NAKAYAMA|HANSHIN|CHUKYO|NIIGATA|SAPPORO|HAKODATE|KOKURA)-"
    r"(?P<race>0[1-9]|1[0-2])$"
)
PAGE_HEADER = re.compile(
    r"レース結果\s*(?P<year>20\d{2})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日"
    r"[\s\S]{0,160}?(?P<venue>東京|京都|福島|中山|阪神|中京|新潟|札幌|函館|小倉)"
    r"[\s\S]{0,160}?(?P<race>\d{1,2})レース"
)
TOP_RESULT_ROW = re.compile(
    r"^\|\s*(?P<finish>[123])\s*\|[^|]*\|\s*(?P<horse>[1-9]|1[0-8])\s*\|",
    re.MULTILINE,
)
OFFICIAL_HOSTS = {"www.jra.go.jp", "jra.go.jp", "jra.jp", "app.jra.jp"}


def validate_jra_result_url(value: str):
    if not isinstance(value, str):
        raise ValueError("result_url_invalid")
    url = urlsplit(value)
    if (url.scheme != "https" or url.hostname not in OFFICIAL_HOSTS
            or url.username or url.password or url.port
            or url.path != "/JRADB/accessS.html"):
        raise ValueError("result_url_not_official_JRA")


def parse_result_source(*, race_id: str, source_url: str,
                        source_text: bytes) -> dict:
    validate_jra_result_url(source_url)
    match = RACE_ID.fullmatch(race_id or "")
    if not match:
        raise ValueError("result_race_id_not_standard")
    if not isinstance(source_text, bytes) or not source_text:
        raise ValueError("missing_result_original_text")
    try:
        text = source_text.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("non_utf8_result_source") from exc
    page = PAGE_HEADER.search(text)
    if not page:
        raise ValueError("result_page_identity_missing")
    page_day = f"{int(page['year']):04d}-{int(page['month']):02d}-{int(page['day']):02d}"
    if (page_day != match["date"] or page["venue"] != VENUE_CODES[match["venue"]]
            or int(page["race"]) != int(match["race"])):
        raise ValueError("result_page_race_identity_mismatch")
    by_rank: dict[int, int] = {}
    for row in TOP_RESULT_ROW.finditer(text):
        rank = int(row["finish"])
        horse = int(row["horse"])
        if rank in by_rank:
            raise ValueError("result_duplicate_rank_or_dead_heat")
        by_rank[rank] = horse
    if set(by_rank) != {1, 2, 3}:
        raise ValueError("result_top_three_not_complete")
    top3 = [by_rank[i] for i in (1, 2, 3)]
    if len(set(top3)) != 3:
        raise ValueError("result_duplicate_horse")
    return {
        "race_id": race_id,
        "source_url": source_url,
        "source_text_sha256": hashlib.sha256(source_text).hexdigest(),
        "top3": top3,
        "status": "JRA_TEXT_PARSED_DISTINCT_TOP3_WITH_IDENTITY",
        "original_page_authenticity_independently_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--race-id", required=True)
    parser.add_argument("--official-url", required=True)
    parser.add_argument("--source-text", type=Path, required=True)
    parser.add_argument("--observed-at-jst", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        from scripts.ticket_forward_freeze import _jst
    except ModuleNotFoundError:
        from ticket_forward_freeze import _jst
    try:
        _jst(args.observed_at_jst)
        actual = parse_result_source(
            race_id=args.race_id, source_url=args.official_url,
            source_text=args.source_text.read_bytes()
        )
    except (ValueError, OSError, TypeError) as error:
        parser.error(str(error))
    result = {k: actual[k] for k in (
        "race_id", "source_url", "source_text_sha256", "top3"
    )}
    result["observed_at_jst"] = args.observed_at_jst
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                     ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "race_id": args.race_id,
        "status": "JRA_TEXT_PARSED_FOR_RESULT_ONLY",
        "source_sha256": actual["source_text_sha256"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
