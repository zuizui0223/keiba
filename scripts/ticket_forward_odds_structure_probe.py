#!/usr/bin/env python3
"""Two-page read-only Yahoo/SportsNavi early odds availability probe.

No predictions, purchases or source page redistribution. This probe is NOT
the prospective market freezer: quote coverage and source update timestamps
must still be checked at the protocol's 15–25 minute pre-post window. A
current fetch cannot retroactively certify page validity or source provenance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

try:
    from scripts.ticket_forward_jra_source_probe import TableStructure
except ModuleNotFoundError:
    from ticket_forward_jra_source_probe import TableStructure

RACE_ID = "2603030601"
DATE = "2026-11-23"
TARGETS = {
    "win_place": "https://sports.yahoo.co.jp/keiba/race/odds/tfw/2603030601?ninki=0",
    "wide": "https://sports.yahoo.co.jp/keiba/race/odds/wide/2603030601?ninki=0",
}
UPDATE = re.compile(r"(?P<y>2026)\s*/\s*(?P<m>11)\s*/\s*(?P<d>23)\s+(?P<h>[0-2]?\d):(?P<min>[0-5]\d)\s*更新")
RACEINFO = re.compile(r"2026年\s*11月23日|2026年11月23日|2026/11/23")
PRICE = re.compile(r"^\d{1,4}(?:\.\d+)?$")
NUMBER = re.compile(r"^(?:[1-9]|1[0-8])$")


def strict_target_url(url: str) -> None:
    if url not in TARGETS.values():
        raise ValueError("unsupported_odds_page_url")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "sports.yahoo.co.jp":
        raise ValueError("not_a_supported_source")


def inspect_html(url: str, raw: bytes, observed_at_utc: str) -> dict:
    strict_target_url(url)
    if not isinstance(raw, bytes) or not raw or len(raw) > 3_000_000:
        raise ValueError("invalid_odds_page_bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("unrecognized_odds_page_encoding") from exc
    tables = TableStructure()
    tables.feed(text)
    # Some Yahoo pages embed the update timestamp as text outside a table.
    updates = sorted({
        f"{int(m['y']):04d}-{int(m['m']):02d}-{int(m['d']):02d}"
        f"T{int(m['h']):02d}:{int(m['min']):02d}:00+09:00"
        for m in UPDATE.finditer(text)
    })
    table_shapes = []
    for i, table in enumerate(tables.tables):
        if not table or len(table) < 2:
            continue
        head = [cell[:30] for cell in table[0][:7]]
        num_rows = [
            [n for n in row[:8] if NUMBER.fullmatch(n)]
            for row in table[1:]
        ]
        decimal_rows = sum(
            any(PRICE.fullmatch(cell) for cell in row[:8])
            for row in table[1:]
        )
        table_shapes.append({
            "table_index": i,
            "rows": len(table),
            "max_cols": max(len(row) for row in table),
            "header_cells": head,
            "rows_with_horse_number_tokens": sum(bool(n) for n in num_rows),
            "rows_with_price_number_tokens": decimal_rows,
        })
    return {
        "status": "READ_ONLY_ODDS_STRUCTURE_NOT_FROZEN",
        "source_url": url,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "observed_at_utc": observed_at_utc,
        "upstream_updated_at_jst_detected": updates,
        "race_date_evidence_detected": bool(RACEINFO.search(text)),
        "num_html_tables": len(tables.tables),
        "tables": table_shapes[:12],
        "win_market_verified_complete": False,
        "wide_market_verified_complete": False,
        "market_as_of_within_prepost_window": False,
        "prospective_prediction_count": 0,
    }


def probe(timeout: int) -> dict:
    result = {}
    for name, url in TARGETS.items():
        try:
            req = Request(url, headers={
                "Accept": "text/html",
                "Accept-Language": "ja,en;q=0.7",
                "User-Agent": "Mozilla/5.0 (compatible; keiba-research-readonly/1.0)",
            })
            with urlopen(req, timeout=timeout) as r:
                if r.status != 200 or r.geturl() != url:
                    raise ValueError("odds_source_redirect_or_http_error")
                raw = r.read(3_000_001)
            result[name] = inspect_html(
                url, raw, datetime.now(timezone.utc).isoformat()
            )
        except Exception as exc:
            result[name] = {
                "status": "HOLD_ODDS_SOURCE_UNAVAILABLE_OR_UNRECOGNIZED",
                "source_url": url,
                "error_class": type(exc).__name__,
                "win_market_verified_complete": False,
                "wide_market_verified_complete": False,
                "prospective_prediction_count": 0,
            }
    return {
        "schema_version": 1,
        "race_id": RACE_ID,
        "date": DATE,
        "run_observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "page_count": len(result),
        "source_pages": result,
        "live_forecast": False,
        "protocol_freeze_attempted": False,
        "note": "Only two read-only HTML probes and quote freshness discovery, not the full pre-race 4-file seal.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 30:
        parser.error("invalid_timeout")
    payload = json.dumps(probe(args.timeout), ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(json.dumps({
        "path": str(args.output),
        "status": "ODDS_READONLY_NO_FORECAST",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
