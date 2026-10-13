#!/usr/bin/env python3
"""Read-only, one-or-two-meeting parser for official Queensland THOROUGHBRED sectionals.

The official CSV is NOT a regular rectangular CSV: "Date,RaceNumber," rows
introduce race metadata; each following horse has one semicolon-packed cell
with a name, apparent cloth/index and repeated [distance, value, split time]
triples. The *meaning* of the intermediate numeric values is not verified.

Research provenance and safety:
* Source: Racing Queensland's own thoroughbred-sectionals downloadable CSV.
* This parses actual HORSES, unlike the greyhound cross-species pilot.
* An all-zero GPS row means unavailable telemetry, NOT DNF or withdrawn.
* Metadata winner/race time is NOT a focal animal's individual finish time.
* Name is NOT a verified stable HORSES horse_id or race starter identity.
* We never claim H1/H2 supported, or generate a betting prediction.
* Only aggregates are written to JSON; runner rows never enter GitHub.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, date
import hashlib
import json
import math
from pathlib import Path
import re
import urllib.parse
import urllib.request

HOST = "www.racingqueensland.com.au"
ROOT = f"https://{HOST}/RacingFile.ashx"
# This is an explicitly short read-only pilot, never a bulk-harvesting API.
APPROVED = {
    "20261011-cairns": "20261011_Ladbrokes_Cannon_Park_T.csv",
    "20261010-eagle-farm": "20261010_Eagle_Farm_T.csv",
    "20260829-cairns": "20260829_Ladbrokes_Cannon_Park_T.csv",
    "20260515-cairns": "20260515_Ladbrokes_Cannon_Park_T.csv",
    "20260529-cairns": "20260529_Ladbrokes_Cannon_Park_T.csv",
    "20260822-cairns": "20260822_Ladbrokes_Cannon_Park_T.csv",
}
MAX_BYTES = 1_800_000
DURATION = re.compile(r"^(?P<hours>\d{2}):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d(?:\.\d{1,3})?)$")
HEADER_TIME = re.compile(r"^\d\d/\d\d/\d{4} 12:00:00 AM$")
RACE_DATE = re.compile(r"^\d\d/\d\d/\d{4}$")


def official_url(name: str) -> str:
    if name not in APPROVED:
        raise ValueError("HOLD_NON_ALLOWLISTED_OFFICIAL_SOURCE")
    return ROOT + "?" + urllib.parse.urlencode({"path": "/Sectional/" + APPROVED[name]})


def fetch_official(name: str) -> tuple[bytes, str]:
    url = official_url(name)
    request = urllib.request.Request(url, headers={
        "User-Agent": "keiba-ecology/0.1 (+https://github.com/zuizui0223/keiba; research audit)",
        "Accept": "text/plain,text/csv,*/*",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        final = urllib.parse.urlparse(response.geturl())
        if final.scheme != "https" or final.netloc.lower() != HOST:
            raise ValueError("HOLD_OFFICIAL_URL_REDIRECT_UNTRUSTED")
        raw = response.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("HOLD_OFFICIAL_FILE_TOO_LARGE_OR_EMPTY")
    return raw, url


def duration_s(text: str) -> float | None:
    m = DURATION.fullmatch(text.strip())
    if not m:
        return None
    return (int(m["hours"]) * 3600 +
            int(m["minutes"]) * 60 + float(m["seconds"]))


def finite_number(text: str) -> float | None:
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def parse(raw: bytes, declared_source: str = "local") -> dict:
    if len(raw) > MAX_BYTES:
        raise ValueError("HOLD_INPUT_EXCEEDS_SIZE_LIMIT")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ValueError("HOLD_UNKNOWN_TEXT_ENCODING") from e
    races = {}
    entries = []
    errors = Counter()
    seen = set()
    active = None
    for lineno, full_line in enumerate(text.splitlines(), 1):
        line = full_line.strip()
        if not line:
            continue
        parts = line.split(",", 2)
        if len(parts) < 3:
            raise ValueError(f"HOLD_UNEXPECTED_CSV_LAYOUT_LINE_{lineno}")
        a, b, blob = [v.strip() for v in parts]
        tokens = [v.strip() for v in blob.split(";")]
        if a == "Date" and b == "RaceNumber":
            if len(tokens) != 5 or not HEADER_TIME.fullmatch(tokens[0]):
                raise ValueError(f"HOLD_UNEXPECTED_RACE_HEADER_LINE_{lineno}")
            try:
                day = datetime.strptime(tokens[0][:10], "%d/%m/%Y").date().isoformat()
            except ValueError as e:
                raise ValueError("HOLD_INVALID_SOURCE_HEADER_DATE") from e
            if not tokens[1] or not tokens[2] or not tokens[4]:
                raise ValueError("HOLD_RACE_HEADER_MISSING_LABEL")
            key = (day, tokens[1], tokens[2])
            if key in races:
                raise ValueError("HOLD_DUPLICATE_RACE_HEADER")
            official_race_time = duration_s(tokens[3])
            races[key] = {
                "day": day, "venue_label": tokens[1],
                "race_title": tokens[2], "race_time_seconds_race_level": official_race_time,
                "route_code": tokens[4], "horse_rows": 0,
                "telemetry_rows": 0, "all_zero_rows": 0,
                "partial_zero_rows": 0,
            }
            active = key
            continue
        if not RACE_DATE.fullmatch(a) or not b.isdecimal() or active is None:
            raise ValueError(f"HOLD_UNEXPECTED_RUNNER_HEADER_LINE_{lineno}")
        try:
            day = datetime.strptime(a, "%d/%m/%Y").date().isoformat()
        except ValueError as e:
            raise ValueError(f"HOLD_BAD_RACE_DATE_LINE_{lineno}") from e
        if day != active[0]:
            raise ValueError("HOLD_RUN_DATE_DISAGREES_WITH_HEADER")
        if len(tokens) < 5 or (len(tokens) - 2) % 3:
            raise ValueError(f"HOLD_UNEXPECTED_SECTION_TRIPLE_LAYOUT_LINE_{lineno}")
        horse_name = tokens[0]
        cloth_number = tokens[1]
        if not horse_name or not cloth_number.isdecimal():
            raise ValueError("HOLD_HORSE_NAME_OR_CLOTH_MISSING")
        ident = (active, int(b), horse_name)
        if ident in seen:
            raise ValueError("HOLD_DUPLICATE_HORSE_NAME_IN_RACE_HEADER")
        seen.add(ident)
        triple_count = (len(tokens) - 2) // 3
        previous_marker = -1.
        measurements = []
        for i in range(triple_count):
            dm, reported_value, section_duration = tokens[2+3*i:5+3*i]
            distance_m = finite_number(dm)
            signal_value = finite_number(reported_value)
            secs = duration_s(section_duration)
            if (distance_m is None or signal_value is None or secs is None or
                    distance_m <= previous_marker or secs < 0):
                raise ValueError(f"HOLD_INVALID_SECTION_TRIPLE_LINE_{lineno}")
            previous_marker = distance_m
            if (secs == 0 and signal_value != 0) or (secs > 0 and signal_value == 0):
                errors["inconsistent_zero_signal_and_time"] += 1
            measurements.append((distance_m, signal_value, secs))
        has_signal = [signal > 0 and sec > 0 for _, signal, sec in measurements]
        all_zero = all(signal == 0 and sec == 0 for _, signal, sec in measurements)
        partially_missing = any(not ok for ok in has_signal) and not all_zero
        if all_zero:
            errors["all_zero_telemetry_rows"] += 1
        if partially_missing:
            errors["partial_zero_or_invalid_telemetry_rows"] += 1
        if sum(has_signal) == triple_count:
            errors["complete_positive_telemetry_rows"] += 1
        if not any(has_signal):
            errors["no_positive_section_rows"] += 1
        if any(signal < 0 for _, signal, _ in measurements):
            errors["negative_reported_section_signal"] += 1
        match_race = (active, int(b))
        entry = {
            "day": day, "race_number": int(b), "header": active,
            "horse_name": horse_name, "unverified_cloth_number": int(cloth_number),
            "interval_count": triple_count,
            "positive_interval_count": sum(has_signal),
            "all_zero_telemetry": all_zero,
            "partial_telemetry": partially_missing,
            "last_distance_marker_m_not_verified_finish_distance": measurements[-1][0],
        }
        entries.append(entry)
        race = races[active]
        race["horse_rows"] += 1
        race["telemetry_rows"] += int(any(has_signal))
        race["all_zero_rows"] += int(all_zero)
        race["partial_zero_rows"] += int(partially_missing)
    if not races or not entries:
        raise ValueError("HOLD_NO_PARSED_RACES_OR_HORSES")
    # The vendor header lacks an explicit RaceNumber value, so ensure
    # one race-number block maps to one race heading and vice versa.
    by_heading = defaultdict(set)
    by_number = defaultdict(set)
    by_day_name = defaultdict(list)
    for entry in entries:
        by_heading[entry["header"]].add(entry["race_number"])
        by_number[(entry["day"], entry["race_number"])].add(entry["header"])
        by_day_name[(entry["day"], entry["horse_name"])].append(entry)
    if any(len(nums) != 1 for nums in by_heading.values()) or any(
        len(headers) != 1 for headers in by_number.values()
    ):
        raise ValueError("HOLD_RACE_NUMBER_TO_HEADER_NOT_ONE_TO_ONE")
    duplicate_day_names = [
        items for items in by_day_name.values() if len(items) > 1
    ]
    conflicting_telemetry_day_names = sum(
        any(e["all_zero_telemetry"] for e in group)
        and any(not e["all_zero_telemetry"] for e in group)
        for group in duplicate_day_names
    )
    # Some vendors publish route codes rather than full race distances, and
    # values 0 can mean no tracker, not necessarily a nonfinisher.
    return {
        "status": "REAL_HORSE_SECTIONAL_STRUCTURE_AUDIT_NOT_H1_H2_EVIDENCE",
        "source_label": declared_source,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_file_republished": False,
        "has_stable_horse_id": False,
        "has_verified_individual_finish_time": False,
        "has_verified_true_starter_status": False,
        "has_position_at_sections": False,
        "telemetry_zero_means_dnf": False,
        "unverified_index_assumed_cloth": False,
        "race_header_time_not_individual_horse_time": True,
        "race_counts": {
            "race_headers": len(races),
            "horse_rows": len(entries),
            "different_horse_names": len(set(e["horse_name"] for e in entries)),
            "source_dates": sorted(set(e["day"] for e in entries)),
            "horse_names_repeated_in_different_races_same_day": len(duplicate_day_names),
            "same_day_repeated_names_both_zero_and_nonzero_telemetry": conflicting_telemetry_day_names,
            "unverified_races_with_positive_telemetry": sum(
                r["telemetry_rows"] > 0 for r in races.values()
            ),
        },
        "quality": dict(errors),
        "races_by_race_header": [
            {"day":r["day"], "race_header_title":r["race_title"],
             "race_level_time_seconds_not_horse_outcome":r["race_time_seconds_race_level"],
             "route_code_not_verified_distance":r["route_code"],
             "horse_rows":r["horse_rows"],"positive_telemetry_rows":r["telemetry_rows"],
             "all_zero_rows":r["all_zero_rows"],"partial_zero_rows":r["partial_zero_rows"]}
            for r in races.values()
        ],
        "limitations": [
            "This official CSV has one string of semicolon triples per named horse, not normalized horse×race outcomes.",
            "Reported interval signal units and first numeric horse-row identifier are unverified.",
            "An all-zero sectional string cannot be classified as DNF, scratch, actual starter, or sensor failure without an independent official result.",
            "Header time is a race-level reference, not an individual horse finish time.",
            "CSV horse name is not a documented stable HORSES internal horse_id.",
            "Repeated same-day horse names and mixed telemetry status across races make the zero=nonfinisher inference especially unsafe.",
            "No chronological lag features, performance reaction norms, or contemporary opponent characteristics are derived.",
            "Race code last marker is not assumed to match officially scheduled race distance.",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input", type=Path, help="Local official sectional CSV")
    src.add_argument("--fetch-official", choices=sorted(APPROVED),
                     help="Fetch one allowlisted historical meeting from the RQ website")
    p.add_argument("--audit", type=Path, required=True, help="Aggregate JSON, never rows")
    args = p.parse_args()
    if args.fetch_official:
        raw, url = fetch_official(args.fetch_official)
        label = url
    else:
        raw, label = args.input.read_bytes(), str(args.input)
    summary = parse(raw, label)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "source_sha256": summary["source_sha256"],
        "counts": summary["race_counts"], "quality": summary["quality"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
