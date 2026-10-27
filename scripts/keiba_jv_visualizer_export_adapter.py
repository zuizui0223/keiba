#!/usr/bin/env python3
"""Convert rights-reviewed Jv Odds Visualizer per-time CSV to PR25 snapshots.

The published JV Odds Visualizer CSV documentation specifies:
  line 1: 17 race metadata columns;
  line 2: empty;
  line 3: tab title;
  line 4: table headers;
  lines 5+: table values; UTF-8 with BOM and CRLF.
See https://keiba.ryuzee.com/jv-odds-visualizer/manual/09-export.html .

IMPORTANT:
- The CSV race header DOES NOT authenticate which specific odds time was
  selected in the application. --selected-source-updated-at MUST be an
  honest, independently source-checked, explicit offset-aware timestamp.
- This bridge supports only one-time WIN tab "単複" with headers "馬番"
  and "単勝", and WIDE *pair-list* tabs with "組" and either explicitly
  named low/high columns or one textual range column. Matrix or history
  graph tabs, ambiguous columns and inconsistent pair/runner sets HOLD.
  Real vendor file column names beyond the 4-row envelope have not yet
  been independently confirmed by an authentic user-provided export.
- A filled "着順"/"払戻"/"的中" or any postrace target labels explicitly
  DISQUALIFY a CSV from supplying a pretarget forecast input.
- Compare original first-row DATE/VENUE/RACE NUMBER/POST/DISTANCE/HEADCOUNT
  against a local operator-declared confirmed final card; the race CODE
  stays separate from official JRA ID and is never silently remapped.
- Writes only one normalized private CAPTURE_SCHEMA source. Append it
  with keiba_operator_winwide_capture.py append (which stamps the
  *actual local reception at append time*). No GitHub post/API calls,
  downloaded JRA data, or claims of third-party market timestamps.
- If WIDE is unavailable, emit ONLY a WIN snapshot for the predeclared
  secondary WIN-only lane; NEVER impute WIDE odds or declare lane A scored.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from datetime import date, datetime, timedelta
import io
import json
import math
from pathlib import Path
import re

from keiba_operator_winwide_capture import (
    CAPTURE_SCHEMA, CAPTURE_VENDOR_SCHEMA,
    _check_card, _verify_capture_payload,
    _write_new_private, _aware, _dump,
)
from odds_shadow_freeze_score import _normalized_odds, _wide_prices

STATUS="JRA_VAN_VISUALIZER_CSV_LOCAL_EXPORT_NOT_REMOTE_CAPTURE_PROOF"
EXPECTED_METADATA_FIELDS=17
TAB_WIN="単複"
PRICE_RANGE_RE=re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*[-‐‑–—－〜～~]\s*(\d+(?:\.\d+)?)\s*$")
PAIR_RE=re.compile(r"^\s*(\d+)\s*[-‐‑–—－〜～~]\s*(\d+)\s*$")
RACE_CODE_RE=re.compile(r"^\d{16}$")
WIN_ODDS_COL="単勝"
WIN_RUNNER_COL="馬番"
PAIR_COL="組"
LEAK_COLS=("着順","払戻","的中","確定着順","確定払戻")
WIDE_RANGE_HEADERS=("オッズ","ワイドオッズ","範囲")
WIDE_LOW_HEADER_CANDIDATES=("下限","オッズ下限","ワイド下限")
WIDE_HIGH_HEADER_CANDIDATES=("上限","オッズ上限","ワイド上限")


def _decode_csv(data):
    if not isinstance(data,bytes) or len(data)>5_000_000:
        raise ValueError("HOLD_VISUALIZER_SOURCE_BYTES_OR_SIZE")
    try:
        decoded=data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("HOLD_VISUALIZER_CSV_NOT_UTF8_OR_BOM") from exc
    if "\0" in decoded:
        raise ValueError("HOLD_VISUALIZER_CSV_BINARY_CONTENT")
    try:
        records=list(csv.reader(io.StringIO(decoded,newline="")))
    except csv.Error as exc:
        raise ValueError("HOLD_VISUALIZER_MALFORMED_CSV_RECORD") from exc
    if (len(records)<5 or len(records)>1000 or
            len(records[0])!=EXPECTED_METADATA_FIELDS or
            any(v.strip() for v in records[1]) or
            len(records[2])!=1 or not records[2][0].strip()):
        raise ValueError("HOLD_VISUALIZER_EXPECTED_RACE_HEADER_BLANK_TAB_COLUMNS")
    headers=[x.strip() for x in records[3]]
    if not headers or len(set(headers))!=len(headers):
        raise ValueError("HOLD_VISUALIZER_DUPLICATE_OR_EMPTY_TABLE_HEADERS")
    if any(not x for x in headers):
        raise ValueError("HOLD_VISUALIZER_DUPLICATE_OR_EMPTY_TABLE_HEADERS")
    rows=[]
    for record in records[4:]:
        if not any(x.strip() for x in record):
            continue
        if len(record)!=len(headers):
            raise ValueError("HOLD_VISUALIZER_INCOMPLETE_OR_EXTRA_CSV_COLUMNS")
        rows.append(dict(zip(headers,(x.strip() for x in record))))
    if not rows:
        raise ValueError("HOLD_VISUALIZER_ZERO_MARKET_PRICE_ROWS")
    for row in rows:
        if any(row.get(c,"") not in ("","-","－") for c in LEAK_COLS):
            raise ValueError("HOLD_VISUALIZER_POSTRACE_FINISH_OR_PAYOUT_PRESENT")
    return records[0],records[2][0].strip(),headers,rows


def _race_header_meta(first):
    race_code=first[0].strip()
    if not RACE_CODE_RE.fullmatch(race_code):
        raise ValueError("HOLD_VISUALIZER_INVALID_16_DIGIT_SOURCE_RACE_CODE")
    try:
        day=date.fromisoformat(first[1].strip().replace("/","-"))
        race_no=int(first[4].strip())
        distance=int(first[10].strip())
        entrants=int(first[14].strip())
    except (ValueError,IndexError) as exc:
        raise ValueError("HOLD_VISUALIZER_INVALID_RACE_META") from exc
    if (race_code[:8]!=day.strftime("%Y%m%d") or
            not 1<=race_no<=12 or race_code[-2:]!=f"{race_no:02d}" or
            not 800<=distance<=5000 or not 5<=entrants<=30):
        raise ValueError("HOLD_VISUALIZER_RACE_META_INCONSISTENT")
    announced_post=first[5].strip()
    if not re.fullmatch(r"\d{1,2}:\d{2}",announced_post):
        raise ValueError("HOLD_VISUALIZER_POST_CLOCK_MISSING")
    return {
        "export_race_code_not_assumed_JRA_ID":race_code,
        "date":day.isoformat(),
        "venue":first[3].strip(),
        "race_number":race_no,
        "post_HHMM":announced_post,
        "track":first[9].strip(),
        "distance_m":distance,
        "headcount":entrants,
    }


def _validate_meta(meta,card):
    c=_check_card(card)
    post=_aware(c["scheduled_post_jst"])
    venue=c["slot_id"].split("|")[1]
    if (meta["date"]!=post.date().isoformat()
            or meta["venue"]!=venue
            or meta["race_number"]!=c["race_number"]
            or meta["post_HHMM"]!=post.strftime("%H:%M")
            or meta["distance_m"]!=c["race_distance_m"]
            or meta["headcount"]!=len(c["horse_numbers"])):
        raise ValueError("HOLD_VISUALIZER_SOURCE_RACE_NOT_CONFIRMED_CARD")
    return c


def _float_quoted(x):
    if not isinstance(x,str) or not re.fullmatch(r"\d+(?:\.\d+)?",x):
        raise ValueError("HOLD_VISUALIZER_ODDS_NOT_CANONICAL_DECIMAL")
    v=float(x)
    if not math.isfinite(v) or v<=1:
        raise ValueError("HOLD_VISUALIZER_NONPOSITIVE_OR_UNAVAILABLE_ODDS")
    return v


def _wide_col_map(headers, low_header,high_header,range_header):
    if PAIR_COL not in headers:
        raise ValueError("HOLD_VISUALIZER_WIDE_PAIR_LIST_REQUIRED_NOT_MATRIX")
    explicit=[v for v in (low_header,high_header,range_header) if v is not None]
    if explicit:
        if range_header is not None and (low_header is not None or high_header is not None):
            raise ValueError("HOLD_VISUALIZER_AMBIGUOUS_WIDE_PRICE_SCHEMA")
        if (range_header is None)!=(low_header is not None and high_header is not None):
            raise ValueError("HOLD_VISUALIZER_INCOMPLETE_WIDE_PRICE_COLUMN_MAPPING")
        if any(x not in headers for x in explicit):
            raise ValueError("HOLD_VISUALIZER_USER_DECLARED_WIDE_COLUMN_ABSENT")
        return low_header,high_header,range_header
    lows=[z for z in WIDE_LOW_HEADER_CANDIDATES if z in headers]
    highs=[z for z in WIDE_HIGH_HEADER_CANDIDATES if z in headers]
    ranges=[z for z in WIDE_RANGE_HEADERS if z in headers]
    if len(lows)==len(highs)==1 and not ranges:
        return lows[0],highs[0],None
    if not lows and not highs and len(ranges)==1:
        return None,None,ranges[0]
    raise ValueError("HOLD_VISUALIZER_WIDE_ODDS_COLUMN_FORMAT_UNVERIFIED")


def _parse_win(headers,rows,ids):
    if not {WIN_RUNNER_COL,WIN_ODDS_COL}.issubset(headers):
        raise ValueError("HOLD_VISUALIZER_WIN_ONE_TIME_TABLE_COLUMNS_MISSING")
    out={}
    for row in rows:
        n=row[WIN_RUNNER_COL]
        if not re.fullmatch(r"[1-9]\d*",n):
            raise ValueError("HOLD_VISUALIZER_NONCANONICAL_HORSE_NUMBER")
        if n in out:
            raise ValueError("HOLD_VISUALIZER_DUPLICATE_WIN_HORSE_NUMBER")
        out[n]=_float_quoted(row[WIN_ODDS_COL])
    _normalized_odds(out)
    if {int(x) for x in out}!=set(ids):
        raise ValueError("HOLD_VISUALIZER_FULL_WIN_RUNNER_FIELD_NOT_MATCH_CARD")
    return out


def _parse_wide(headers,rows,ids,*,low_header=None,high_header=None,
                range_header=None):
    low_col,high_col,range_col=_wide_col_map(
        headers,low_header,high_header,range_header)
    output=[]
    for row in rows:
        parsed=PAIR_RE.fullmatch(row[PAIR_COL])
        if not parsed:
            raise ValueError("HOLD_VISUALIZER_INVALID_WIDE_PAIR_TEXT")
        x,y=map(int,parsed.groups())
        if range_col is not None:
            match=PRICE_RANGE_RE.fullmatch(row[range_col])
            if not match:
                raise ValueError("HOLD_VISUALIZER_UNPARSABLE_WIDE_ODDS_RANGE")
            lo,hi=map(float,match.groups())
        else:
            lo,hi=_float_quoted(row[low_col]),_float_quoted(row[high_col])
        if (not math.isfinite(lo) or not math.isfinite(hi) or
                not 1<lo<=hi):
            raise ValueError("HOLD_VISUALIZER_BAD_WIDE_ODDS_INTERVAL")
        output.append({"selection":[x,y],"odds_low":lo,"odds_high":hi})
    _wide_prices(output,set(ids))  # exactly n(n-1)/2 distinct edges
    return output


def adapt_one_export(raw,card,*,market,source_updated_at_jst,
                     provider,source_url,low_col=None,high_col=None,
                     range_col=None):
    meta_row,tab,headers,rows=_decode_csv(raw)
    header=_race_header_meta(meta_row)
    card=_validate_meta(header,card)
    pub=_aware(source_updated_at_jst)
    post=_aware(card["scheduled_post_jst"])
    # Friday presales for Saturday racing can be legitimate. The
    # exported race metadata DATE remains the race date, but the selected
    # WIN quote may have an earlier published time. Do not wrongly force
    # them to share a calendar date. Never infer publication from export.
    if not (post-timedelta(days=2)<=pub<
            post-timedelta(minutes=10)):
        raise ValueError("HOLD_VISUALIZER_QUOTE_TIME_NOT_BEFORE_POST")
    if not isinstance(provider,str) or provider!=card["provider"]:
        raise ValueError("HOLD_VISUALIZER_PROVIDER_DIFFERENT_FROM_CARD")
    if market not in ("win","wide"):
        raise ValueError("HOLD_VISUALIZER_MARKET_NOT_SUPPORTED")
    if market=="win":
        if tab!=TAB_WIN:
            raise ValueError("HOLD_VISUALIZER_ONLY_ONE_TIME_WIN_TAB_SUPPORTED")
        data={"odds_by_horse_number":_parse_win(headers,rows,card["horse_numbers"])}
    else:
        if "ワイド" not in tab:
            raise ValueError("HOLD_VISUALIZER_NOT_A_WIDE_PAIR_LIST_TAB")
        data={"pairs":_parse_wide(headers,rows,card["horse_numbers"],
                low_header=low_col,high_header=high_col,
                range_header=range_col)}
    export_link={
        "schema":CAPTURE_VENDOR_SCHEMA,
        "vendor":"Jv Odds Visualizer",
        "raw_csv_sha256":sha256(raw).hexdigest(),
        "original_race_code":header["export_race_code_not_assumed_JRA_ID"],
        "selected_table_tab":tab,
        "wide_low_col":low_col if market=="wide" else None,
        "wide_high_col":high_col if market=="wide" else None,
        "wide_range_col":range_col if market=="wide" else None,
        "quote_publication_time_embedded_in_csv":False,
        "local_reception_time_embedded_in_csv":False,
    }
    source={
        "schema":CAPTURE_SCHEMA,
        "race_id":card["race_id"],
        "provider":provider,
        "market":market,
        "source_updated_at_jst":pub.isoformat(),
        "source_url":source_url,
        "source_clock_declared_verified":True,
        "rights_reviewed_by_operator":card["rights_reviewed_by_operator"],
        "provenance":card["provenance"],
        "original_vendor_export":export_link,
        **data,
    }
    _verify_capture_payload(source)
    audit={
        "status":STATUS,
        "selected_csv_tab":tab,
        "original_vendor_export_bytes_SHA256_local_only":
            sha256(raw).hexdigest(),
        "normalized_private_snapshot_SHA256_local_only":
            sha256(_dump(source).encode("utf-8")).hexdigest(),
        "raw_vendor_export_byte_digest_in_normalized_capture_and_later_chain":True,
        "raw_vendor_export_bytes_not_stored_in_public_model":True,
        "append_requires_original_csv_and_final_card_reparse":True,
        "JvOddsVisualizer_16digit_race_code":header[
            "export_race_code_not_assumed_JRA_ID"],
        "operator_provided_source_update_clock_NOT_from_csv_header":True,
        "full_card_runner_count":len(card["horse_numbers"]),
        "full_win_n" :len(data.get("odds_by_horse_number",{})),
        "full_wide_n_pairs":len(data.get("pairs",[])),
        "source_clock_and_reception_independently_attested":False,
        "license_or_total_bettor_vote_amount_authenticated":False,
        "not_prospective_until_new_local_capture_and_remote_sha":True,
        "export_may_be_historical_replay_source_not_actual_receipt":True,
    }
    return source,audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv",type=Path,required=True)
    parser.add_argument("--final-card",type=Path,required=True)
    parser.add_argument("--market",required=True,choices=("win","wide"))
    parser.add_argument("--source-updated-at-jst",required=True)
    parser.add_argument("--provider",required=True)
    parser.add_argument("--source-url",required=True)
    parser.add_argument("--wide-low-col")
    parser.add_argument("--wide-high-col")
    parser.add_argument("--wide-range-col")
    parser.add_argument("--private-output",type=Path,required=True)
    parser.add_argument("--private-audit",type=Path)
    args=parser.parse_args()
    card=json.loads(args.final_card.read_text(encoding="utf-8"))
    norm,report=adapt_one_export(
        args.csv.read_bytes(),card,market=args.market,
        source_updated_at_jst=args.source_updated_at_jst,
        provider=args.provider,source_url=args.source_url,
        low_col=args.wide_low_col,high_col=args.wide_high_col,
        range_col=args.wide_range_col)
    _write_new_private(args.private_output,norm)
    if args.private_audit is not None:
        _write_new_private(args.private_audit,report)
    print(json.dumps({
        "status":report["status"],"market":args.market,
        "rows":report["full_win_n"] or report["full_wide_n_pairs"],
        "local_reception_time_not_yet_stamped":True,
        "github_pre_target_proof":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
