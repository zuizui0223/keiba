#!/usr/bin/env python3
"""Read-only 2026-11-23 JRA full-day card roster *metadata* preflight.

Discover all 24 official racecard hrefs from JRA's own navigation, read each
once and identify only contiguous numbered horse rows in a page table.
Do NOT infer a missing number, backfill third-party counts, use future results,
collect odds, publish original page content, or certify a formal forward freeze.

Designed for one public-source preflight; no credentials, purchases or retry loops.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from time import sleep
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen
from html.parser import HTMLParser

try:
    from scripts.ticket_forward_jra_source_probe import (
        TARGETS, CardLinks, require_official, numeric_table_shapes
    )
    from scripts.ticket_forward_program_preflight import audit_preliminary_program
except ModuleNotFoundError:
    from ticket_forward_jra_source_probe import (
        TARGETS, CardLinks, require_official, numeric_table_shapes
    )
    from ticket_forward_program_preflight import audit_preliminary_program

CNAME = re.compile(
    r"^(?P<prefix>pw01dde01|sw01ddd01)(?P<course>03|05)"
    r"2026(?P<meeting>03|05)(?P<meeting_day>06)"
    r"(?P<race>0[1-9]|1[0-2])20261123/[0-9A-F]{2}$"
)
EXPECTED_CODES = {"03": ("福島", "FUKUSHIMA"),
                  "05": ("東京", "TOKYO")}


def card_key(url: str) -> tuple[str, int] | None:
    require_official(url)
    parts = urlsplit(url)
    if parts.path != "/JRADB/accessD.html":
        return None
    params = parse_qs(parts.query)
    if set(params) != {"CNAME"} or len(params["CNAME"]) != 1:
        return None
    matched = CNAME.fullmatch(params["CNAME"][0])
    if not matched or matched["course"] != matched["meeting"]:
        return None
    return EXPECTED_CODES[matched["course"]][0], int(matched["race"])


def discover_day_links(page_pairs: list[tuple[str, str]]) -> dict[tuple[str, int], str]:
    """Only links present on the *official* JRA anchor pages; no URL guessing."""
    if len(page_pairs) != 2:
        raise ValueError("two_official_anchor_pages_required")
    mapping = {}
    for source_url, text in page_pairs:
        require_official(source_url)
        anchors = CardLinks()
        anchors.feed(text)
        for raw in anchors.links:
            from urllib.parse import urljoin
            full = urljoin(source_url, raw)
            try:
                key = card_key(full)
            except ValueError:
                continue
            if key is None:
                continue
            if key in mapping and mapping[key] != full:
                # Same card can have multiple mobile/desktop variants:
                # retain source from first official anchor, but do not blend.
                continue
            mapping[key] = full
    return mapping


def numbered_card_rows(html: str) -> tuple[int | None, list[dict]]:
    """Identify a horse-number column only with a full 1..N sequence.

    This tests *declared numbered rows*, not active-runner status or scratches.
    """
    shapes = numeric_table_shapes(html)
    candidates = []
    for table in shapes:
        for col in table["numeric_columns"]:
            n = col["unique"]
            if (col["column"] == 1 and 5 <= n <= 18 and
                    col["integer_cell_count"] == n and col["min"] == 1 and
                    col["max"] == n and col["contiguous_from_one"] and
                    table["html_row_count"] == n + 1):
                candidates.append(n)
    distinct = set(candidates)
    return (next(iter(distinct)) if len(distinct) == 1 else None), shapes


def get_official_text(url: str, timeout: int = 10) -> tuple[str, bytes, str]:
    require_official(url)
    request = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Keiba-readonly-source-audit/1.0)",
        "Accept": "text/html",
        "Accept-Language": "ja,en;q=0.6",
    })
    with urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        require_official(final_url)
        if response.status != 200:
            raise ValueError("JRA_http_error")
        raw = response.read(3_000_001)
    if not raw or len(raw) > 3_000_000:
        raise ValueError("JRA_empty_or_large_response")
    for encoding in ("utf-8", "cp932", "shift_jis", "euc-jp"):
        try:
            return raw.decode(encoding), raw, final_url
        except UnicodeDecodeError:
            pass
    raise ValueError("JRA_text_charset_unknown")


def audit_day(read, stage: dict) -> dict:
    """Use injected fetcher read(url)->(text,raw,final_url) for deterministic tests."""
    staged = audit_preliminary_program(stage)
    if staged["status"] != "HOLD_AWAITING_OFFICIAL_24_CARD_COUNTS_AND_PRE_FIRST_RACE_PROOF":
        raise ValueError("unexpected_program_stage")
    anchors = []
    anchor_hashes = {}
    for name in ("fukushima_1r_card", "tokyo_1r_card"):
        url = TARGETS[name]
        text, raw, final = read(url)
        require_official(final)
        if card_key(final) not in {("福島",1),("東京",1)}:
            raise ValueError("official_anchor_wrong_race")
        anchor_hashes[name] = hashlib.sha256(raw).hexdigest()
        anchors.append((final, text))
    links = discover_day_links(anchors)
    expected = {(r["venue"], r["race_number"]) for r in stage["races"]}
    if set(links) != expected:
        return {
            "status": "HOLD_UNDISCOVERED_OFFICIAL_CARD_LINKS",
            "expected_cards": len(expected), "discovered_cards": len(links),
            "missing": sorted(f"{v}-{n}" for v,n in expected - set(links)),
            "future_forecast_count": 0,
        }
    rows = []
    provisional = {(r["venue"],r["race_number"]):r for r in stage["races"]}
    for venue, number in sorted(links, key=lambda x:(provisional[x]["scheduled_start_jst"],x[0],x[1])):
        url = links[(venue, number)]
        try:
            text, raw, final = read(url)
            if card_key(final) != (venue, number) or "20261123" not in final:
                raise ValueError("official_card_redirect_wrong_race")
            if ("2026" not in text or venue not in text):
                raise ValueError("official_card_body_identity_missing")
            n, shape = numbered_card_rows(text)
            status = "OFFICIAL_NUMBER_SEQUENCE_EXTRACTED" if n is not None else "HOLD_NO_UNIQUE_NUMBER_SEQUENCE"
            rows.append({
                "race_id":provisional[(venue,number)]["race_id"],
                "venue":venue,"race_number":number,
                "official_url":final,"observed_at_utc":datetime.now(timezone.utc).isoformat(),
                "raw_page_sha256":hashlib.sha256(raw).hexdigest(),
                "raw_byte_count":len(raw),
                "strict_numbered_horse_rows":n,
                "third_party_preliminary_count":provisional[(venue,number)]["third_party_displayed_runner_count"],
                "count_agrees_with_third_party_staging":
                    n == provisional[(venue,number)]["third_party_displayed_runner_count"] if n else None,
                "parse_status":status,
                "scratch_and_active_runners_independently_verified":False,
            })
        except Exception as exc:
            rows.append({
                "race_id": provisional[(venue,number)]["race_id"],
                "venue":venue,"race_number":number,"official_url":url,
                "parse_status":"HOLD_CARD_FETCH_OR_PARSER",
                "error_class":type(exc).__name__,
                "strict_numbered_horse_rows":None,
                "scratch_and_active_runners_independently_verified":False,
            })
    success = sum(row["parse_status"]=="OFFICIAL_NUMBER_SEQUENCE_EXTRACTED" for row in rows)
    disagreements = [r for r in rows if r.get("count_agrees_with_third_party_staging") is False]
    return {
        "schema_version":1,
        "status": "READ_ONLY_ROSTER_METADATA_NOT_A_FORMAL_PRE_RACE_SEAL" if success==24
                  else "HOLD_INCOMPLETE_OFFICIAL_CARD_ROSTER_PARSE",
        "source_program_status":"JRA_PUBLISHED_PROGRAM_ONLY",
        "target_date":"2026-11-23",
        "expected_cards":24,
        "official_card_links_discovered":len(links),
        "number_sequence_card_count":success,
        "preliminary_count_disagreement_count":len(disagreements),
        "preliminary_count_disagreements":[{
            "race_id":r["race_id"],"official_number_rows":r["strict_numbered_horse_rows"],
            "third_party_preliminary_count":r["third_party_preliminary_count"]
        } for r in disagreements],
        "raw_html_redistributed":False,
        "official_program_day_git_server_seal":False,
        "official_quote_update_times_verified":False,
        "actual_runner_scratch_status_verified":False,
        "future_prospective_forecasts":0,
        "first_two_anchor_raw_sha256":anchor_hashes,
        "races":rows,
        "note":"Read-only JRA horse-number table shapes. This is not a full official day card seal or a quote snapshot.",
    }


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--staging",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--timeout",type=int,default=10)
    args=p.parse_args()
    if not 1<=args.timeout<=30:
        p.error("invalid_timeout")
    try:
        stage=json.loads(args.staging.read_text(encoding="utf-8"))
        attempt=0
        def reader(url):
            nonlocal attempt
            if attempt:
                sleep(.25)
            attempt+=1
            return get_official_text(url,timeout=args.timeout)
        report=audit_day(reader,stage)
    except (ValueError,KeyError,OSError,TypeError) as exc:
        p.error(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "expected":report["expected_cards"],
        "discovered":report.get("official_card_links_discovered",report.get("discovered_cards")),
        "number_sequence_parsed":report.get("number_sequence_card_count",0),
        "third_party_disagreement_count":report.get("preliminary_count_disagreement_count"),
        "future_prospective_forecasts":0,
    },ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
