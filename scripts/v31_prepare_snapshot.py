#!/usr/bin/env python3
"""Prepare deterministic v3.1 race-input and odds snapshots from captured JRA text.

Input is a JSON capture containing one JRA race-card text plus one JRA horse-profile
text per active runner. The script never fetches the web itself and never reads the
target-race result. It filters every profile row to dates strictly before target date.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_aware_iso(value: str, label: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid_datetime:{label}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"naive_datetime:{label}")
    return dt


def class_rank(text: str | None) -> int | None:
    text = text or ""
    if "3勝" in text:
        return 3
    if "2勝" in text:
        return 2
    if "1勝" in text:
        return 1
    if "未勝利" in text or "新馬" in text:
        return 0
    if re.search(r"(?:^|\s)OP(?:\s|$)", text) or "オープン" in text:
        return 4
    return None


def _margin_from_cell(cell: str) -> float | None:
    matches = list(re.finditer(r"\(([-+]?\d+(?:\.\d+)?)\)", cell))
    return float(matches[-1].group(1)) if matches else None


def parse_recent_start(cell: str) -> dict | None:
    cell = cell.strip()
    if not cell or "JRAへ転入" in cell:
        return None
    head = re.search(
        r"(?P<y>\d{4})年(?P<m>\d{1,2})月(?P<d>\d{1,2})日\s+"
        r"(?P<venue>\S+)\s+(?P<race>.+?)\s+(?P<finish>\d+)着\s+",
        cell,
    )
    course = re.search(r"\s(?P<distance>\d{3,4})(?P<surface>ダ|芝)\s", cell)
    if not head or not course:
        return None
    date = f"{head.group('y')}-{int(head.group('m')):02d}-{int(head.group('d')):02d}"
    finish = int(head.group("finish"))
    return {
        "date": date,
        "venue": head.group("venue"),
        "race_name": head.group("race").strip(),
        "finish": finish,
        "distance_m": int(course.group("distance")),
        "surface": course.group("surface"),
        "class_rank": class_rank(head.group("race")),
        "margin_sec": _margin_from_cell(cell),
        "is_win": finish == 1,
        "raw": cell,
    }


def parse_card(text: str) -> tuple[list[dict], list[int]]:
    horses, scratched, seen = [], [], set()
    for line in text.splitlines():
        if not re.match(r"^\|\s*\|\s*\d+\s*\|", line):
            continue
        cols = [part.strip() for part in line.split("|")]
        if len(cols) < 6:
            continue
        try:
            number = int(cols[2])
        except ValueError:
            continue
        if number in seen:
            raise ValueError(f"duplicate_card_horse:{number}")
        seen.add(number)
        if "取消" in line or "除外" in line:
            scratched.append(number)
            continue
        info, sex_age = cols[3], cols[4]
        name_match = re.match(r"^(.+?)\s+\*\*", info)
        odds_match = re.search(r"\*\*([0-9]+(?:\.[0-9]+)?)\*\*", info)
        body_match = re.search(r"(\d+)kg\(([+-]?\d+)\)", info)
        age_match = re.search(r"(?:牡|牝|せん)(\d+)", sex_age)
        jockey_match = re.search(r"kg\s+(.+?)\s*$", sex_age)
        if not name_match:
            raise ValueError(f"missing_horse_name:{number}")
        if not odds_match:
            raise ValueError(f"missing_current_win_odds:{number}")
        if not age_match:
            raise ValueError(f"missing_age:{number}")
        last4 = [parse_recent_start(cell) for cell in cols[5:9]]
        horses.append({
            "number": number,
            "name": name_match.group(1).strip(),
            "age": int(age_match.group(1)),
            "body_weight_kg": int(body_match.group(1)) if body_match else None,
            "body_weight_change_kg": int(body_match.group(2)) if body_match else None,
            "current_jockey": jockey_match.group(1).strip() if jockey_match else None,
            "current_win_odds": float(odds_match.group(1)),
            "last4": [x for x in last4 if x is not None],
        })
    if not horses:
        raise ValueError("no_active_horses_parsed")
    return sorted(horses, key=lambda x: x["number"]), sorted(scratched)


def parse_profile(text: str, target_date: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        if not re.match(r"^\s*\|\s*20\d{2}年\d{1,2}月\d{1,2}日\s*\|", line):
            continue
        cols = [part.strip() for part in line.split("|")]
        if len(cols) < 15:
            continue
        dm = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", cols[1])
        course = re.match(r"(芝|ダ)(\d+)", cols[4])
        if not dm or not course or not cols[8].isdigit():
            continue
        date = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
        if date >= target_date:
            continue
        rt_match = re.search(r"[-+]?\d+(?:\.\d+)?", cols[13] if len(cols) > 13 else "")
        body_match = re.search(r"\d+", cols[11] if len(cols) > 11 else "")
        weight_match = re.search(r"\d+(?:\.\d+)?", cols[10] if len(cols) > 10 else "")
        rows.append({
            "date": date,
            "venue": cols[2],
            "race_name": cols[3],
            "surface": course.group(1),
            "distance_m": int(course.group(2)),
            "going": cols[5],
            "field_size": int(cols[6]) if cols[6].isdigit() else None,
            "popularity": int(cols[7]) if cols[7].isdigit() else None,
            "finish": int(cols[8]),
            "jockey": cols[9] or None,
            "weight_kg": float(weight_match.group(0)) if weight_match else None,
            "body_weight_kg": int(body_match.group(0)) if body_match else None,
            "time": cols[12] or None,
            "rt": float(rt_match.group(0)) if rt_match else None,
            "class_rank": class_rank(cols[3]),
        })
    return sorted(rows, key=lambda x: x["date"], reverse=True)


def prepare(capture: dict, observed_at_jst: str) -> tuple[dict, dict, dict]:
    race = capture["race"]
    if race.get("venue") != "京都":
        raise ValueError("ineligible_venue")
    observed = parse_aware_iso(observed_at_jst, "observed_at_jst")
    scheduled = parse_aware_iso(race["scheduled_start_jst"], "scheduled_start_jst")
    if observed >= scheduled:
        raise ValueError("snapshot_not_prerace")
    card = capture["card"]
    card_horses, scratched = parse_card(card["text"])
    profiles = capture.get("profiles", {})
    normalized = []
    profile_meta = {}
    for horse in card_horses:
        key = str(horse["number"])
        if key not in profiles:
            raise ValueError(f"missing_profile:{horse['number']}")
        profile = profiles[key]
        history = parse_profile(profile["text"], race["date"])
        row = {k: v for k, v in horse.items() if k != "current_win_odds"}
        row["career_starts_before_target"] = len(history)
        row["profile_url"] = profile.get("url")
        row["full_history_before_target"] = history
        normalized.append(row)
        profile_meta[key] = {
            "url": profile.get("url"),
            "sha256": sha256_text(profile["text"]),
            "history_rows_before_target": len(history),
        }
    race_input = {
        "race_id": race["race_id"],
        "date": race["date"],
        "venue": race["venue"],
        "race_number": race["race_number"],
        "age_scope": race["age_scope"],
        "scheduled_start_jst": race["scheduled_start_jst"],
        "target": race["target"],
        "horses": normalized,
    }
    odds = {
        "observed_at_jst": observed_at_jst,
        "horses": [
            {"number": h["number"], "win_odds": h["current_win_odds"]}
            for h in card_horses
        ],
    }
    meta = {
        "schema_version": 1,
        "race_id": race["race_id"],
        "observed_at_jst": observed_at_jst,
        "card_url": card.get("url"),
        "card_sha256": sha256_text(card["text"]),
        "active_horse_numbers": [h["number"] for h in card_horses],
        "scratched_or_excluded_numbers": scratched,
        "profiles": profile_meta,
        "uses_target_race_results": False,
    }
    return race_input, odds, meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--observed-at-jst", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        race_input, odds, meta = prepare(read_json(args.capture), args.observed_at_jst)
        write_json(args.output_dir / "race-input.json", race_input)
        write_json(args.output_dir / "odds.json", odds)
        write_json(args.output_dir / "source-capture-meta.json", meta)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
