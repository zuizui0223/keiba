#!/usr/bin/env python3
"""Create strictly FABRICATED race-history rows to exercise the research pipeline.

Every record is fictional and marked source_license=synthetic. No official JRA
data, inferred winners, or real horse identifiers are included.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import random

from ecology_panel import REQUIRED


def fabricate(n_horses: int = 16, n_days: int = 26, seed: int = 88) -> list[dict]:
    if not 8 <= n_horses <= 30 or n_days < 16:
        raise ValueError("synthetic generator needs 8-30 horses and >=16 race days")
    rng = random.Random(seed)
    output = []
    for day in range(n_days):
        dt = date(2000, 1, 1) + timedelta(days=day)
        poor = day % 2
        speeds = []
        for i in range(n_horses):
            horse_base = 0.45 * (i / (n_horses - 1) - 0.5)
            horse_slope = 0.5 * ((i * 7) % n_horses / (n_horses - 1) - 0.5)
            speeds.append(15.0 + horse_base + poor * horse_slope + rng.gauss(0, 0.07))
        ranks = {i: 1 + sum(v > speeds[i] for v in speeds) for i in range(n_horses)}
        for i in range(n_horses):
            output.append({
                "race_id": f"FABRICATED-{day:03d}",
                "horse_id": f"NOT-REAL-HORSE-{i:03d}",
                "race_date_jst": dt.isoformat(),
                "race_start_jst": f"{dt}T15:00:00+09:00",
                "feature_available_at_jst": f"{dt}T12:00:00+09:00",
                "venue": "FICTIONAL",
                "course_surface": "turf",
                "course_distance_m": 1600,
                "track_going": "重" if poor else "良",
                "class_pre": "FICTIONAL",
                "jockey_id": f"NOT-REAL-JOCKEY-{i:03d}",
                "field_size": n_horses,
                "finish_status": "finished",
                "finishing_position": ranks[i],
                "finish_time_s": f"{1600/speeds[i]:.7f}",
                "first_call_position": 1 + (i * 7) % n_horses,
                "source_url": "synthetic://random-fabrication/no-empirical-use",
                "source_license": "synthetic",
            })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--days", type=int, default=26)
    parser.add_argument("--horses", type=int, default=16)
    parser.add_argument("--seed", type=int, default=88)
    args = parser.parse_args()
    rows = fabricate(args.horses, args.days, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(REQUIRED) + ["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"FABRICATED ONLY: {len(rows)} rows / {args.days} fake races; {args.output}")


if __name__ == "__main__":
    main()
