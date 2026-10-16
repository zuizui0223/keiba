#!/usr/bin/env python3
"""Audit historical horse×race records and build strictly lagged competition features.

Research-only. No scraping, bets, imputed individual starts, or causal inference.
Pure Python standard library; input is an authorized longitudinal CSV export.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
import statistics

JST = timezone(timedelta(hours=9))
GOING = {"良", "稍重", "重", "不良"}
SURFACES = {"turf", "dirt"}
REQUIRED = (
    "race_id", "horse_id", "race_date_jst", "race_start_jst", "venue",
    "course_surface", "course_distance_m", "track_going", "class_pre",
    "jockey_id", "field_size", "finish_status", "finishing_position",
    "finish_time_s", "source_url", "source_license",
    "feature_available_at_jst",
)
OPTIONAL = ("first_call_position", "age_at_start", "prior_rest_days")


def as_time(value: str) -> datetime:
    try:
        t = datetime.fromisoformat(value)
    except ValueError as e:
        raise ValueError("bad ISO datetime: " + value) from e
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("timezone required: " + value)
    return t.astimezone(JST)


def integer(value: str, field: str, optional: bool = False) -> int | None:
    if optional and value == "":
        return None
    try:
        number = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{field}: expected integer, got {value!r}") from e
    return number


def positive_float(value: str, field: str, optional: bool = False) -> float | None:
    if optional and value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{field}: expected number, got {value!r}") from e
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field}: must be finite and positive")
    return number


def parse_row(raw: dict[str, str], line: int) -> dict:
    for field in REQUIRED:
        if field not in raw:
            raise ValueError(f"missing column: {field}")
    for field in REQUIRED:
        if raw[field] is None:
            raise ValueError(f"null cell: {field} line {line}")
    race_id, horse_id = raw["race_id"].strip(), raw["horse_id"].strip()
    if not race_id or not horse_id or not raw["venue"].strip():
        raise ValueError(f"missing identity / venue on line {line}")
    if not raw["class_pre"].strip() or not raw["jockey_id"].strip():
        raise ValueError(f"missing pre-race class/jockey line {line}")
    start = as_time(raw["race_start_jst"])
    cutoff = as_time(raw["feature_available_at_jst"])
    race_date = date.fromisoformat(raw["race_date_jst"])
    if race_date != start.date():
        raise ValueError(f"race date/time mismatch line {line}")
    if cutoff >= start:
        raise ValueError(f"future/at-start predictor snapshot line {line}")
    surface = raw["course_surface"]
    going = raw["track_going"]
    if surface not in SURFACES or going not in GOING:
        raise ValueError(f"unknown surface/going line {line}: {surface}/{going}")
    distance = integer(raw["course_distance_m"], "course_distance_m")
    field_size = integer(raw["field_size"], "field_size")
    if distance < 600 or field_size < 2:
        raise ValueError(f"invalid distance/field size line {line}")
    status = raw["finish_status"]
    if status not in {"finished", "did_not_finish", "pending"}:
        raise ValueError(f"unknown finish_status line {line}")
    pos = integer(raw["finishing_position"], "finishing_position", optional=True)
    seconds = positive_float(raw["finish_time_s"], "finish_time_s", optional=True)
    first = integer(raw.get("first_call_position", "") or "", "first_call_position", optional=True)
    age = integer(raw.get("age_at_start", "") or "", "age_at_start", optional=True)
    rest = integer(raw.get("prior_rest_days", "") or "", "prior_rest_days", optional=True)
    if age is not None and not 1 <= age <= 40:
        raise ValueError(f"implausible age line {line}")
    if rest is not None and rest < 0:
        raise ValueError(f"negative rest days line {line}")
    if (pos is not None and not 1 <= pos <= field_size) or (
        first is not None and not 1 <= first <= field_size
    ):
        raise ValueError(f"position exceeds field line {line}")
    if status != "finished" and (pos is not None or seconds is not None):
        raise ValueError(f"nonfinisher has finishing outcome line {line}")
    if status == "finished" and pos is None:
        raise ValueError(f"finisher missing placing line {line}")
    source_url = raw["source_url"].strip()
    license_name = raw["source_license"].strip().lower()
    if not (source_url.startswith("https://") or source_url.startswith("synthetic://")):
        raise ValueError(f"source URL not HTTPS/synthetic line {line}")
    if not license_name:
        raise ValueError(f"missing source rights provenance line {line}")
    return {
        "race_id": race_id, "horse_id": horse_id,
        "race_date_jst": race_date.isoformat(), "race_start_jst": start.isoformat(),
        "venue": raw["venue"].strip(), "course_surface": surface,
        "course_distance_m": distance, "track_going": going, "class_pre": raw["class_pre"].strip(),
        "jockey_id": raw["jockey_id"].strip(), "field_size": field_size,
        "finish_status": status, "finishing_position": pos, "finish_time_s": seconds,
        "first_call_position": first, "age_at_start": age, "prior_rest_days": rest,
        "feature_available_at_jst": cutoff.isoformat(), "source_url": source_url,
        "source_license": license_name,
    }


def load_panel(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise ValueError("empty panel")
        if missing := set(REQUIRED) - set(reader.fieldnames):
            raise ValueError("missing required columns: " + ", ".join(sorted(missing)))
        rows = [parse_row(raw, index) for index, raw in enumerate(reader, start=2)]
    if not rows:
        raise ValueError("no horse-race records")
    seen: set[tuple[str, str]] = set()
    by_race: dict[str, list[dict]] = defaultdict(list)
    horse_day: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["race_id"], row["horse_id"])
        if key in seen:
            raise ValueError(f"duplicate horse×race key {key}")
        seen.add(key)
        day_key = (row["horse_id"], row["race_date_jst"])
        if day_key in horse_day:
            raise ValueError(f"same horse appears in multiple races on same day {day_key}")
        horse_day.add(day_key)
        by_race[row["race_id"]].append(row)
    race_attrs = ("race_date_jst", "race_start_jst", "venue", "course_surface",
                  "course_distance_m", "track_going", "class_pre", "field_size")
    for race_id, group in by_race.items():
        for attr in race_attrs:
            if len({r[attr] for r in group}) != 1:
                raise ValueError(f"conflicting race-level {attr} in {race_id}")
        if len(group) > group[0]["field_size"]:
            raise ValueError(f"too many runners in {race_id}")
        ranks = [r["finishing_position"] for r in group if r["finishing_position"] is not None]
        if len(set(ranks)) != len(ranks):
            raise ValueError(f"duplicate ranks in {race_id}; dead heats need dedicated handling")
    return sorted(rows, key=lambda r: (r["race_date_jst"], r["race_start_jst"], r["race_id"], r["horse_id"]))


def _strength(row: dict) -> float | None:
    if row["finish_status"] != "finished":
        return None
    return (row["field_size"] - row["finishing_position"]) / (row["field_size"] - 1)


def _style(row: dict) -> float | None:
    p = row["first_call_position"]
    if p is None:
        return None
    return (row["field_size"] - p) / (row["field_size"] - 1)


def lagged_features(
    rows: list[dict], history_window: int = 5, min_prior_starts: int = 3,
    min_competitor_fraction: float = 0.8, front_threshold: float = 0.7,
) -> list[dict]:
    """Never uses races from same/future calendar day to build predictors."""
    if history_window < min_prior_starts or min_prior_starts < 1:
        raise ValueError("history_window must be >= min_prior_starts >= 1")
    if not 0 < min_competitor_fraction <= 1:
        raise ValueError("min_competitor_fraction out of range")
    hist: dict[str, list[dict]] = defaultdict(list)
    by_day: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_day[row["race_date_jst"]].append(row)
    output: list[dict] = []
    for day in sorted(by_day):
        current = by_day[day]
        profile = {}
        for row in current:
            old = hist[row["horse_id"]]
            styles = [v for r in old if (v := _style(r)) is not None][-history_window:]
            speeds = [v for r in old if (v := _strength(r)) is not None][-history_window:]
            profile[row["horse_id"]] = {
                "prior_starts_count": len(old),
                "prior_style_sample_size": len(styles),
                "prior_front_runner_score": statistics.mean(styles) if len(styles) >= min_prior_starts else None,
                "prior_strength_sample_size": len(speeds),
                "prior_strength_score": statistics.mean(speeds) if len(speeds) >= min_prior_starts else None,
            }
        by_race: dict[str, list[dict]] = defaultdict(list)
        for row in current:
            by_race[row["race_id"]].append(row)
        for group in by_race.values():
            # No future result is consulted: only pre-day horse profiles.
            for row in group:
                other = [profile[r["horse_id"]] for r in group if r["horse_id"] != row["horse_id"]]
                n_others = row["field_size"] - 1
                # Incomplete roster cannot be interpreted as zero front-runners.
                roster_complete = len(group) == row["field_size"]
                s = [p["prior_front_runner_score"] for p in other if p["prior_front_runner_score"] is not None]
                a = [p["prior_strength_score"] for p in other if p["prior_strength_score"] is not None]
                style_ok = roster_complete and len(s) / n_others >= min_competitor_fraction
                strength_ok = roster_complete and len(a) / n_others >= min_competitor_fraction
                this = {
                    **row, **profile[row["horse_id"]],
                    "other_front_runner_share": (
                        sum(v >= front_threshold for v in s) / len(s) if style_ok else None
                    ),
                    "other_prior_strength_mean": statistics.mean(a) if strength_ok else None,
                    "competitor_style_known": len(s),
                    "competitor_strength_known": len(a),
                    "competitor_count": n_others,
                    "lagged_feature_rule": "strict_prior_calendar_dates_only",
                }
                output.append(this)
        for row in current:
            hist[row["horse_id"]].append(row)
    return sorted(output, key=lambda r: (r["race_start_jst"], r["race_id"], r["horse_id"]))


def audit(rows: list[dict], features: list[dict]) -> dict:
    by_race: dict[str, list[dict]] = defaultdict(list)
    by_horse: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_race[row["race_id"]].append(row)
        if row["finish_status"] == "finished" and row["finish_time_s"] is not None:
            by_horse[row["horse_id"]].append(row)
    good = lambda row: row["track_going"] == "良"
    eligible = []
    for horse, starts in by_horse.items():
        c = Counter(good(r) for r in starts)
        if c[True] >= 2 and c[False] >= 2:
            eligible.append(horse)
    by_going_races = Counter("良" if group[0]["track_going"] == "良" else "非良" for group in by_race.values())
    full = sum(len(g) == g[0]["field_size"] for g in by_race.values())
    observed = sum(r["finish_status"] == "finished" and r["finish_time_s"] is not None for r in rows)
    h2 = sum(
        f["prior_front_runner_score"] is not None
        and f["other_front_runner_share"] is not None
        and f["other_prior_strength_mean"] is not None
        and f["finish_status"] == "finished"
        for f in features
    )
    # H2 needs within-horse exposure to different *competitor compositions*.
    # Many races with the same opponent mix do not identify this interaction.
    h2_contexts = defaultdict(list)
    for f in features:
        if (f["finish_status"] == "finished"
                and f["prior_front_runner_score"] is not None
                and f["other_front_runner_share"] is not None
                and f["other_prior_strength_mean"] is not None):
            h2_contexts[f["horse_id"]].append(f["other_front_runner_share"])
    h2_horses_varied = sum(
        len(v) >= 4 and len({round(x, 6) for x in v}) >= 2
        for v in h2_contexts.values()
    )
    licenses = Counter(r["source_license"] for r in rows)
    synthetic = "synthetic" in licenses
    mixed_sources = synthetic and len(licenses) > 1
    license_hold = any(s in ("unknown", "uncleared", "restricted") for s in licenses)
    design = (
        len(eligible) >= 30 and len({r["race_date_jst"] for r in rows}) >= 15
        and by_going_races["良"] >= 10 and by_going_races["非良"] >= 10
        and full == len(by_race) and observed >= 200
    )
    status = ("HOLD_MIXED_SYNTHETIC_AND_REAL" if mixed_sources else
              "SYNTHETIC_ONLY" if synthetic else
              "HOLD_RIGHTS" if license_hold else
              "DESIGN_READY_NOT_EVIDENCE" if design else "HOLD_INSUFFICIENT_LONGITUDINAL_SUPPORT")
    return {
        "status": status,
        "evidence_class": "data_readiness_diagnostic_only",
        "horse_start_rows": len(rows), "unique_races": len(by_race),
        "unique_dates": len({r["race_date_jst"] for r in rows}),
        "unique_horses": len({r["horse_id"] for r in rows}),
        "unique_venues": len({r["venue"] for r in rows}),
        "fully_recorded_race_rosters": full,
        "finishers_with_individual_times": observed,
        "horses_with_2plus_total_timed_starts": sum(len(s) >= 2 for s in by_horse.values()),
        "horses_with_2plus_timed_starts_in_each_good_vs_non_good": len(eligible),
        "race_count_by_ground_binary": dict(by_going_races),
        "h2_rows_with_historical_style_and_opponent_strength": h2,
        "h2_horses_with_4plus_races_and_2plus_distinct_opponent_style_contexts": h2_horses_varied,
        "h2_context_identifiability": (
            "PRELIMINARY_CONTEXT_OVERLAP" if h2_horses_varied >= 30
            else "HOLD_NO_REPEATED_WITHIN_HORSE_CONTEXT_VARIATION"
        ),
        "source_license_counts": dict(licenses),
        "ready_gate_is_not_statistical_power_or_hypothesis_support": True,
        "notes": [
            "Operational thresholds only: >=30 cross-going repeated horses, >=15 days, "
            ">=10 races in each going group, >=200 timed outcomes, complete rosters.",
            "Going is grouped as 良 vs 非良; no equal spacing among the four Japanese categories.",
            "H1 needs additional age/class/jockey/entry-selection adjustment before confirmatory inference.",
            "H2 historical style scores are proxies, not observed causal interference.",
            "H2 repeated context variation is necessary but insufficient; competitor selection remains confounded.",
            "Horse-by-day block prevents leakage from races on the target calendar date.",
        ],
    }


def export_features(path: Path, features: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(features[0])
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for row in features:
            writer.writerow({key: "" if val is None else val for key, val in row.items()})


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True, help="Authorized horse × race CSV")
    p.add_argument("--audit", type=Path, required=True, help="Write data-readiness JSON")
    p.add_argument("--features", type=Path, help="Write strictly lagged feature CSV")
    args = p.parse_args()
    rows = load_panel(args.input)
    features = lagged_features(rows)
    report = audit(rows, features)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.features:
        export_features(args.features, features)
    print(json.dumps({"status": report["status"], "horses": report["unique_horses"],
                      "races": report["unique_races"], "timed": report["finishers_with_individual_times"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
