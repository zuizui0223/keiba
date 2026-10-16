#!/usr/bin/env python3
"""REAL but CROSS-SPECIES ecological-method benchmark: greyhound first 50 m.

Pinned source: Australian Racing Open Data (PandaVision), ODC-BY 1.0,
https://github.com/brucem1967/au-racing-open-data

Upstream source: Racing Queensland open-data published GPS records.
This is NOT a Thoroughbred dataset and does not test horse H1/H2.
Names are not permanent unique individual IDs; this is exploratory.

The narrowly defined descriptive statistic is, within dog-name and
venue, mean first-50m split for OUTER box 5-8 minus INNER box 1-4.
At least two plausible timed runs per category are required.
No random assignment, race class, start-distance, complete race roster,
or horse physiological plasticity is assumed. Do not interpret as causal.

No raw/source data are committed by this program. Optional pinned
download uses a source blob hash and prints only aggregate summaries.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import random
import urllib.request


PINNED_REPO = "brucem1967/au-racing-open-data"
PINNED_COMMIT = "4337848a4a3df181db3be2a75118c878270e0a58"
PINNED_BLOB_SHA1 = "8ef2f4c426e8f1f3e52830044d276ce57b03ba1f"
PINNED_URL = (
    f"https://raw.githubusercontent.com/{PINNED_REPO}/{PINNED_COMMIT}/"
    "datasets/greyhound_sectionals_qld/greyhound_sectionals_qld.csv"
)
ATTRIBUTION = "Australian Racing Open Data (PandaVision), ODC-BY 1.0"
FIELDS = (
    "date", "track", "race", "greyhound", "box", "split_50m_sec",
    "position_50m", "rail_distance_50m_m", "top_speed_kmh", "finish_position",
)


def git_blob_hash(raw: bytes) -> str:
    """SHA1 in Git's blob framing; provenance, not cryptographic security."""
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def number(value: str) -> float | None:
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None
    return v if math.isfinite(v) else None


def read(raw: bytes) -> tuple[list[dict], dict]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not reader.fieldnames or (missing := set(FIELDS) - set(reader.fieldnames)):
        raise ValueError("HOLD_MISSING_SOURCE_COLUMNS: " + str(missing if reader.fieldnames else set(FIELDS)))
    runs = []
    quality = Counter()
    seen = set()
    all_dates = set()
    race_counts = Counter()
    for row in reader:
        quality["rows"] += 1
        rid = (row["date"], row["track"], row["race"])
        animal = row["greyhound"]
        if any(not x for x in (*rid, animal)):
            raise ValueError("HOLD_INCOMPLETE_OBSERVATION_IDENTITY")
        key = (*rid, animal)
        if key in seen:
            raise ValueError("HOLD_DUPLICATE_GREYHOUND_RUN")
        seen.add(key)
        try:
            date.fromisoformat(row["date"])
        except ValueError as exc:
            raise ValueError("HOLD_INVALID_DATE") from exc
        all_dates.add(row["date"])
        race_counts[rid] += 1
        box = number(row["box"])
        split = number(row["split_50m_sec"])
        rail = number(row["rail_distance_50m_m"])
        if rail is None:
            quality["missing_rail"] += 1
        elif rail < 0:
            # Signed reported values are not silently recoded to 0.
            quality["negative_reported_rail"] += 1
        if split is None:
            quality["missing_split"] += 1
        if split is not None and not (2.4 < split < 7.0):
            # Exploratory, visibly data-inspected plausibility screen.
            quality["split_outside_exploratory_range"] += 1
        if box is None or not (1 <= box <= 8 and box.is_integer()):
            quality["unusable_start_box"] += 1
        if split is not None and 2.4 < split < 7.0 and box is not None and (
            1 <= box <= 8 and box.is_integer()
        ):
            quality["valid_box_and_split"] += 1
            runs.append({
                "date": row["date"], "track": row["track"], "race": row["race"],
                "dog_name": animal, "box": int(box), "split_sec": split,
            })
    if not runs:
        raise ValueError("HOLD_NO_VALID_TIMED_RUNS")
    quality["distinct_source_races"] = len(race_counts)
    quality["distinct_source_dates"] = len(all_dates)
    quality["unique_source_dog_names"] = len(set(r["dog_name"] for r in runs))
    quality["source_races_with_exactly_8_gps_rows"] = sum(
        count == 8 for count in race_counts.values()
    )
    quality["source_races_with_more_than_8_gps_rows"] = sum(
        count > 8 for count in race_counts.values()
    )
    quality["source_race_row_count_histogram"] = dict(sorted(Counter(
        race_counts.values()).items()
    ))
    return runs, dict(quality)


def groups(runs: list[dict], min_each: int = 2) -> list[dict]:
    if min_each < 2:
        raise ValueError("Need at least two inner and two outer replicates")
    combined = defaultdict(lambda: {"inner": [], "outer": []})
    for row in runs:
        key = (row["dog_name"], row["track"])
        side = "inner" if row["box"] <= 4 else "outer"
        combined[key][side].append(row["split_sec"])
    out = []
    for (name, venue), sides in combined.items():
        a, b = sides["inner"], sides["outer"]
        if len(a) >= min_each and len(b) >= min_each:
            out.append({
                "dog_name": name, "venue": venue,
                "n_inner": len(a), "n_outer": len(b),
                "difference_outer_minus_inner_sec": sum(b) / len(b) - sum(a) / len(a),
            })
    return out


def descriptive(effects: list[dict], bootstrap=1000, seed=20261013) -> dict:
    if not effects:
        return {"dog_venue_strata": 0, "unique_dog_names": 0,
                "mean_outer_minus_inner_sec": None,
                "descriptive_dog_name_cluster_bootstrap_95pct": None}
    ds = [e["difference_outer_minus_inner_sec"] for e in effects]
    strata_by_dog = defaultdict(list)
    for e in effects:
        strata_by_dog[e["dog_name"]].append(e["difference_outer_minus_inner_sec"])
    dog_values = list(strata_by_dog.values())
    m = len(dog_values)
    rng = random.Random(seed)
    boot = []
    for _ in range(bootstrap):
        total, n = 0.0, 0
        for __ in range(m):
            sampled = dog_values[rng.randrange(m)]
            total += sum(sampled)
            n += len(sampled)
        boot.append(total / n)
    boot.sort()
    return {
        "dog_venue_strata": len(effects),
        "unique_dog_names": len(strata_by_dog),
        "mean_outer_minus_inner_sec": sum(ds) / len(ds),
        "fraction_strata_outer_slower": sum(d > 0 for d in ds) / len(ds),
        "descriptive_dog_name_cluster_bootstrap_95pct": [
            boot[int(.025 * (len(boot) - 1))],
            boot[int(.975 * (len(boot) - 1))],
        ],
        "bootstrap_resamples": bootstrap,
        "bootstrap_is_causal_uncertainty": False,
    }


def analysis(raw: bytes, bootstrap: int = 1000) -> dict:
    if bootstrap < 100:
        raise ValueError("bootstrap requires >=100 resamples for reporting")
    hash_sha1 = git_blob_hash(raw)
    matches = hash_sha1 == PINNED_BLOB_SHA1
    runs, quality = read(raw)
    dates = sorted({r["date"] for r in runs})
    if len(dates) < 2:
        raise ValueError("HOLD_TOO_FEW_OBSERVATION_DATES")
    cutoff = dates[int(.8 * len(dates))]
    whole = groups(runs)
    early = groups([r for r in runs if r["date"] < cutoff])
    late = groups([r for r in runs if r["date"] >= cutoff])
    tracks = sorted({r["track"] for r in runs})
    return {
        "status": ("REAL_GREYHOUND_OBSERVATIONAL_BENCHMARK_NOT_HORSE_EVIDENCE"
                   if matches else "UNPINNED_INPUT_DESCRIPTIVE_ONLY"),
        "source": {
            "repository": f"https://github.com/{PINNED_REPO}",
            "pinned_commit": PINNED_COMMIT,
            "pinned_blob_sha1": PINNED_BLOB_SHA1,
            "actual_blob_sha1": hash_sha1,
            "matches_pinned_source": matches,
            "dataset_license": "ODC-BY 1.0",
            "attribution": ATTRIBUTION,
            "upstream": "Racing Queensland publicly released sectionals",
            "no_raw_runner_records_written": True,
        },
        "animal": "racing greyhound (NOT Thoroughbred horse)",
        "data_quality": quality,
        "method": {
            "measurement": "first 50 m GPS split seconds",
            "pre_race_exposure": "start box <=4 inner, >=5 outer",
            "longitudinal_unit": "dog name x track (name not verified permanent ID)",
            "minimum_exposure_repeats_each": 2,
            "data_inspected_exploratory_split_filter_sec": "(2.4, 7.0)",
            "target": "mean outer box split minus inner box split, seconds",
            "split_time_window": "date cutoff at 80pct of distinct GPS dates",
            "cutoff_date": cutoff,
            "causal_design": False,
        },
        "full": descriptive(whole, bootstrap=bootstrap),
        "early_dates": descriptive(early, bootstrap=bootstrap),
        "late_dates": descriptive(late, bootstrap=bootstrap),
        "track_specific": {
            t: descriptive([e for e in whole if e["venue"] == t], bootstrap=bootstrap)
            for t in tracks
        },
        "not_claimed": [
            "H1 or H2 established among racehorses",
            "random assignment to starting boxes",
            "valid unique individual ID from dog name",
            "all starters recorded or complete rival composition",
            "full-distance race speed or physiological plasticity",
            "controlled race-distance, class, jockey/trainer, weather, fatigue",
            "causal effect of lane/turn geometry or direct animal competition",
            "confirmed adaptive or genetic differences",
        ],
        "interpretation": (
            "A real-data cross-species repeat-exposure FEASIBILITY and "
            "within-name-within-venue descriptive association. No causal or "
            "evolutionary inference; no horse race record enters analysis. "
            "Field coverage is uneven and dog names can be reused."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    inp = parser.add_mutually_exclusive_group(required=True)
    inp.add_argument("--input", type=Path, help="Local copy of the licensed CSV")
    inp.add_argument("--fetch-pinned", action="store_true",
                     help="Fetch exactly the pinned third-party ODC-BY data file")
    parser.add_argument("--require-pinned", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()
    if args.fetch_pinned:
        with urllib.request.urlopen(PINNED_URL, timeout=40) as response:
            raw = response.read(5_000_000)
        if not raw or len(raw) >= 5_000_000:
            raise ValueError("HOLD_PINNED_DOWNLOAD_SIZE")
    else:
        raw = args.input.read_bytes()
    if args.require_pinned and git_blob_hash(raw) != PINNED_BLOB_SHA1:
        raise ValueError("HOLD_INPUT_NOT_EXACT_PINNED_SOURCE_BLOB")
    output = analysis(raw, bootstrap=args.bootstrap)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status": output["status"],
        "source_commit": output["source"]["pinned_commit"],
        "source_blob_verified": output["source"]["matches_pinned_source"],
        "counts": {
            k: output["data_quality"][k] for k in (
                "rows", "distinct_source_races", "unique_source_dog_names",
                "split_outside_exploratory_range", "missing_rail"
            )
        },
        "full": output["full"], "early": output["early_dates"],
        "late": output["late_dates"], "track_specific": output["track_specific"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
