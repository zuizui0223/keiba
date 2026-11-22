#!/usr/bin/env python3
"""Read-only official JRA public-source connectivity preflight.

This does NOT infer betting probabilities or certify full JRA starter rosters.
No cookies, no authentication, no submission, no scraping loop, no publication
of raw JRA page text. It prints only HTTP metadata, content hashes, number of
JRA racecard links and simple date-presence diagnostics. A successful page
fetch is NOT a prospective GitHub seal and is NOT a source-update timestamp.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urljoin, unquote
from urllib.request import Request, urlopen

OFFICIAL_HOSTS = {"jra.jp", "www.jra.go.jp", "app.jra.jp", "sp.jra.jp"}
TARGETS = {
    "jra_program_nov23": "https://jra.jp/keiba/calendar2026/2026/11/1123.html",
    "fukushima_1r_card": (
        "https://www.jra.go.jp/JRADB/accessD.html?"
        "CNAME=pw01dde0103202603060120261123%2FEC"
    ),
    "tokyo_1r_card": (
        "https://app.jra.jp/JRADB/accessD.html?"
        "CNAME=sw01ddd0105202605060120261123%2FA9"
    ),
}


def require_official(url: str) -> None:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in OFFICIAL_HOSTS
            or parts.username or parts.password or parts.port):
        raise ValueError("non_JRA_public_source")


class CardLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = set()
    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs = dict(attrs)
        href = attrs.get("href")
        if href and "accessD.html" in href and "CNAME=" in href:
            self.links.add(href)


def inspect_response(*, requested_url: str, response_url: str,
                     content: bytes, http_status: int, recorded_at_utc: str) -> dict:
    require_official(requested_url)
    require_official(response_url)
    if http_status != 200:
        raise ValueError("official_source_http_not_200")
    if not isinstance(content, bytes) or not content or len(content) > 3_000_000:
        raise ValueError("empty_or_excessive_response")
    decoded = None
    codec = None
    for enc in ("utf-8", "cp932", "shift_jis", "euc-jp"):
        try:
            decoded = content.decode(enc)
            codec = enc
            break
        except UnicodeDecodeError:
            pass
    if decoded is None:
        raise ValueError("unrecognized_JRA_charset")
    parser = CardLinks()
    parser.feed(decoded)
    card_links = set()
    for href in parser.links:
        resolved = urljoin(response_url, href)
        try:
            require_official(resolved)
        except ValueError:
            continue
        card_links.add(resolved)
    return {
        "status": "HTTP_READ_ONLY_NO_FORMAL_EVIDENCE",
        "requested_url": requested_url,
        "response_url": response_url,
        "http_status": http_status,
        "observed_at_utc": recorded_at_utc,
        "raw_sha256": hashlib.sha256(content).hexdigest(),
        "raw_bytes": len(content),
        "codec": codec,
        "html_a_jra_card_link_count": len(card_links),
        "html_a_jra_card_links_sample": sorted(card_links)[:8],
        "raw_has_year_2026": "2026" in decoded,
        "raw_has_racedate_20261123": ("20261123" in decoded or
                                     ("11月23日" in decoded and "2026" in decoded)),
        "source_updated_at_verified": False,
        "official_runner_count_verified": False,
        "live_odds_available": False,
        "server_sealed_before_race": False,
    }


def probe(targets: dict[str, str] = TARGETS, timeout_sec: int = 15) -> dict:
    result = {}
    observed = datetime.now(timezone.utc).isoformat()
    for label, url in targets.items():
        require_official(url)
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; JRA-preflight-readonly/1.0)",
                    "Accept-Language": "ja,en;q=0.5",
                    "Accept": "text/html",
                },
            )
            with urlopen(request, timeout=timeout_sec) as response:
                content = response.read(3_000_001)
                status = response.status
                response_url = response.geturl()
            result[label] = inspect_response(
                requested_url=url, response_url=response_url,
                content=content, http_status=status,
                recorded_at_utc=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:  # source downtime/network block remains HOLD
            result[label] = {
                "status": "HOLD_JRA_DIRECT_FETCH_UNAVAILABLE",
                "requested_url": url,
                "error_class": type(exc).__name__,
                "source_updated_at_verified": False,
                "official_runner_count_verified": False,
                "server_sealed_before_race": False,
            }
    return {
        "schema_version": 1, "task": "public_jra_readonly_connectivity",
        "attempted_at_utc": observed,
        "target_date": "2026-11-23",
        "official_program_status": "PRELIMINARY_PROGRAM",
        "target_count": len(result), "results": result,
        "formal_day_schedule_seal": False, "forecast_count": 0,
        "note": "Connectivity and hash only; no scraped official starter roster or prospective odds freeze",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    p.add_argument("--timeout", type=int, default=12)
    args = p.parse_args()
    if args.timeout not in range(1, 31):
        p.error("invalid_timeout")
    output = probe(timeout_sec=args.timeout)
    body = json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
