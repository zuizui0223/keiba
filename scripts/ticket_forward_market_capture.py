#!/usr/bin/env python3
"""Fail-closed capture of actual Fukushima-1R win+wide quotes, at *fetch time*.

Independent quote parser for Yahoo/SportsNavi's public intermediate market
tables. It is an engineering adapter, NOT an autonomous bettor, forecast
endorsement or source authenticity certificate. The official JRA card is
read for number-sequence alignment, not for price discovery. All 3 sources
must respond before race post. Caller must preserve source rights if
publishing raw pages.

The separately pre-registered forecast freezer must still check manifest,
15–25 minute time window, updates<=10m, receipts<=5m, source hashes and
publish 4 exact pre-race files to GitHub before treating a score as prospective.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

try:
    from scripts.ticket_forward_jra_source_probe import TableStructure
    from scripts.ticket_forward_jra_full_day_readonly import numbered_card_rows
    from scripts.ticket_forward_odds_structure_probe import TARGETS, UPDATE, strict_target_url
    from scripts.ticket_forward_freeze import (
        REPO_ROOT, VERSION, _jst, sha256_bytes, validate_manifest, freeze_forecast,
    )
except ModuleNotFoundError:
    from ticket_forward_jra_source_probe import TableStructure
    from ticket_forward_jra_full_day_readonly import numbered_card_rows
    from ticket_forward_odds_structure_probe import TARGETS, UPDATE, strict_target_url
    from ticket_forward_freeze import (
        REPO_ROOT, VERSION, _jst, sha256_bytes, validate_manifest, freeze_forecast,
    )

VENUE = "福島"
CARD_URL = (
    "https://www.jra.go.jp/JRADB/accessD.html?"
    "CNAME=pw01dde0103202603060120261123%2FEC"
)
START_JST = "2026-11-23T09:45:00+09:00"
RACE_ID = "2026-11-23-FUKUSHIMA-01"
PRICE = re.compile(r"^(\d+(?:\.\d+)?)$")
RANGE = re.compile(r"^(\d+(?:\.\d+)?)\s*[-–〜]\s*(\d+(?:\.\d+)?)$")
HORSE = re.compile(r"^(?:[1-9]|1[0-8])$")
FRAME = re.compile(r"^[1-8]$")
JST = ZoneInfo("Asia/Tokyo")


def _decode(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8")
    except (AttributeError, UnicodeDecodeError) as exc:
        raise ValueError("market_html_not_utf8") from exc
    if len(text) > 3_000_000 or not text:
        raise ValueError("empty_or_excess_market_text")
    if "2026年11月23日" not in text or "福島" not in text:
        raise ValueError("market_page_race_day_identity_not_confirmed")
    return text


def _updated(text: str) -> str:
    found = sorted(set(
        f"{int(m['y']):04d}-{int(m['m']):02d}-{int(m['d']):02d}T"
        f"{int(m['h']):02d}:{int(m['min']):02d}:00+09:00"
        for m in UPDATE.finditer(text)
    ))
    if len(found) != 1:
        raise ValueError("missing_or_ambiguous_source_visible_update")
    return found[0]


def parse_win(raw: bytes) -> tuple[dict[int, int], dict[int, float], str]:
    text = _decode(raw)
    p = TableStructure()
    p.feed(text)
    candidates = [
        table for table in p.tables
        if len(table) >= 10 and len(table[0]) >= 4
        and "馬番" in table[0] and "単勝" in table[0] and "枠番" in table[0]
    ]
    if len(candidates) != 1:
        raise ValueError("win_market_table_not_unique")
    table = candidates[0]
    names = table[0]
    frame_col, number_col, price_col = (
        names.index("枠番"), names.index("馬番"), names.index("単勝")
    )
    frames, prices = {}, {}
    for row in table[1:]:
        if len(row) <= max(frame_col, number_col, price_col):
            raise ValueError("incomplete_win_table_row")
        frame, number, odds = row[frame_col], row[number_col], row[price_col]
        if not FRAME.fullmatch(frame) or not HORSE.fullmatch(number):
            raise ValueError("unparseable_win_horse_frame")
        m = PRICE.fullmatch(odds)
        if not m:
            raise ValueError("invalid_or_censored_win_price")
        horse = int(number)
        val = float(m[1])
        if horse in prices or not math.isfinite(val) or not 1 <= val < 999.9:
            raise ValueError("duplicate_or_censored_win_price")
        frames[horse] = int(frame)
        prices[horse] = val
    n=len(prices)
    if not 9<=n<=18 or set(prices)!=set(range(1,n+1)):
        raise ValueError("win_horse_board_incomplete")
    return frames, prices, _updated(text)


def parse_wide(raw: bytes, n: int) -> tuple[list[dict], str]:
    text = _decode(raw)
    p = TableStructure()
    p.feed(text)
    expected = {(i,j) for i in range(1,n+1) for j in range(i+1,n+1)}
    out = {}
    for table in p.tables:
        if not table or len(table[0]) != 1 or not HORSE.fullmatch(table[0][0]):
            continue
        i = int(table[0][0])
        if i >= n or len(table)!=n-i+1:
            raise ValueError("wide_triangle_table_missing_rows")
        for row in table[1:]:
            if len(row)!=2 or not HORSE.fullmatch(row[0]):
                raise ValueError("invalid_wide_selection")
            j=int(row[0])
            if j <= i:
                raise ValueError("wide_pairs_must_be_upper_triangle")
            key=(i,j)
            if key in out:
                raise ValueError("duplicated_wide_pair")
            m=RANGE.fullmatch(row[1])
            if m is None:
                raise ValueError("invalid_or_censored_wide_price")
            low, high=float(m[1]),float(m[2])
            if not math.isfinite(low) or not math.isfinite(high) or not 1<=low<=high:
                raise ValueError("invalid_wide_price_range")
            out[key]={"selection":[i,j],"odds_low":low,"odds_high":high}
    if set(out)!=expected:
        raise ValueError("incomplete_wide_board_no_imputation")
    return [out[key] for key in sorted(out)], _updated(text)


def parse_sources(*, win_raw: bytes, wide_raw: bytes, card_raw: bytes,
                  observed_win_jst: str, observed_wide_jst: str,
                  manifest: dict) -> tuple[dict, dict]:
    validate_manifest(manifest)
    frames, prices, updated_win=parse_win(win_raw)
    wide, updated_wide=parse_wide(wide_raw,len(prices))
    try:
        official_html=card_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("JRA_card_charset_unreadable") from exc
    if "2026" not in official_html or "福島" not in official_html:
        raise ValueError("JRA_card_wrong_race")
    official_n, _ = numbered_card_rows(official_html)
    if official_n != len(prices):
        raise ValueError("JRA_card_number_rows_disagree_with_market")
    win_observed, wide_observed=_jst(observed_win_jst),_jst(observed_wide_jst)
    if abs((win_observed-wide_observed).total_seconds()) > manifest["win_wide_receipt_gap_seconds"]:
        raise ValueError("market_observations_not_synchronous")
    if max(win_observed,wide_observed) >= _jst(START_JST):
        raise ValueError("post_start_quote_capture")
    # Exact shape required by the frozen ticket-forward-v1 pre-race forecaster.
    capture={
        "schema_version":1,
        "race":{
            "race_id":RACE_ID, "date":"2026-11-23", "venue":VENUE,
            "race_number":1,"scheduled_start_jst":START_JST,
            "horses":[{"number":n,"frame":frames[n]} for n in sorted(frames)],
        },
        "markets":{
            "win":{
                "source_url":TARGETS["win_place"],
                "observed_at_jst":observed_win_jst,
                "updated_at_jst":updated_win,
                "updated_time_basis":"source_visible",
                "raw_page_sha256":sha256_bytes(win_raw),
                "quotes":[
                    {"selection":[n],"odds_low":prices[n],"odds_high":prices[n]}
                    for n in sorted(prices)
                ],
            },
            "wide":{
                "source_url":TARGETS["wide"],
                "observed_at_jst":observed_wide_jst,
                "updated_at_jst":updated_wide,
                "updated_time_basis":"source_visible",
                "raw_page_sha256":sha256_bytes(wide_raw),
                "quotes":wide,
            },
        },
    }
    return capture,{
        "status":"RAW_MARKET_TABLES_PARSED_NOT_FROZEN",
        "horse_count":len(prices),"win_quotes":len(prices),
        "wide_quotes":len(wide),"updated_win_jst":updated_win,
        "updated_wide_jst":updated_wide,
        "JRA_card_sha256":sha256_bytes(card_raw),
        "JRA_numbered_rows":official_n,
        "active_scratch_status_independently_verified":False,
        "source_rights_for_redistribution_verified":False,
    }


def read_one(url: str, *, timeout: int) -> tuple[bytes,str]:
    parts=urlsplit(url)
    if parts.scheme!="https" or parts.hostname not in {
        "www.jra.go.jp","sports.yahoo.co.jp"
    }:
        raise ValueError("source_url_outside_allowlist")
    with urlopen(Request(url, headers={
        "Accept":"text/html","Accept-Language":"ja,en;q=0.7",
        "User-Agent":"Mozilla/5.0 (compatible; keiba-research-limited/1.0)",
    }),timeout=timeout) as r:
        if r.status!=200 or r.geturl()!=url:
            raise ValueError("source_http_or_redirect_error")
        raw=r.read(3_000_001)
    if len(raw)>3_000_000 or not raw:
        raise ValueError("source_response_size_invalid")
    stamp=datetime.now(timezone.utc).astimezone(JST).isoformat(timespec="seconds")
    return raw,stamp


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,default=REPO_ROOT/"docs/betting/ticket-forward-v1-manifest.json")
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--timeout",type=int,default=10)
    p.add_argument("--audit-only",action="store_true",help="inspect 16/120 market coverage without emitting quotes, pages or forecast")
    args=p.parse_args()
    if not 1<=args.timeout<=30:
        p.error("invalid_timeout")
    try:
        manifest=json.loads(args.manifest.read_bytes())
        # One request per target, no background monitoring or retry loop.
        card_raw, card_received = read_one(CARD_URL,timeout=args.timeout)
        win_raw, win_observed=read_one(TARGETS["win_place"],timeout=args.timeout)
        wide_raw, wide_observed=read_one(TARGETS["wide"],timeout=args.timeout)
        capture, evidence=parse_sources(
            win_raw=win_raw,wide_raw=wide_raw,card_raw=card_raw,
            observed_win_jst=win_observed,observed_wide_jst=wide_observed,
            manifest=manifest,
        )
        if args.audit_only:
            print(json.dumps({
                **evidence,
                "status":"LIVE_QUOTES_PARSED_STRUCTURE_ONLY_NOT_FROZEN",
                "observed_win_jst":win_observed,
                "observed_wide_jst":wide_observed,
                "JRA_card_received_jst":card_received,
                "model_market_quote_recency_not_certified":True,
                "raw_source_files_written":False,
                "future_predictions":0,
            },ensure_ascii=False))
            return 0
        if max(_jst(win_observed),_jst(wide_observed)) > _jst(START_JST):
            raise ValueError("after_race_start")
        asof=datetime.now(timezone.utc).astimezone(JST).isoformat(timespec="seconds")
        try:
            from scripts.ticket_forward_freeze import canonical
        except ModuleNotFoundError:
            from ticket_forward_freeze import canonical
        f=freeze_forecast(
            capture,manifest,asof,
            capture_raw=canonical(capture),
            source_pages={"win":win_raw,"wide":wide_raw},
        )
    except (ValueError,KeyError,TypeError,OSError) as exc:
        p.error(str(exc))
    # Only write input source files when the frozen model genuinely accepted
    # ALL gates. The user may need to keep source HTML privately, not publish.
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"capture.json").write_bytes(canonical(capture))
    (args.output_dir/"win-source.txt").write_bytes(win_raw)
    (args.output_dir/"wide-source.txt").write_bytes(wide_raw)
    (args.output_dir/"forecast.json").write_text(
        json.dumps(f,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        **evidence,
        "status":"FROZEN_LOCAL_CANDIDATE_UNATTESTED_ON_GITHUB",
        "forecast_as_of_jst":asof,
        "card_received":card_received,
        "input_source_sha256":f["capture_sha256"],
        "forecast_integrity_sha256":f["integrity_sha256"],
        "locally_written_to":str(args.output_dir),
        "github_server_seal":False,
        "on_platform_bet_placed":False,
    },ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
