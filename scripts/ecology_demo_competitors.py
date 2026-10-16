#!/usr/bin/env python3
"""Fabricate a changing-field racehorse panel for H2 software checks.

This code can plant an interaction OR a zero-effect, confounded scenario; it does NOT
model real Japanese racehorses, identify a causal mechanism, or produce bets.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import random
from ecology_panel import REQUIRED


def fabricate_competition(n_days=100, n_horses=48, runners=12, seed=512,
                           interaction=-0.9, assortment=0.0,
                           going_style_effect=0.0) -> list[dict]:
    if n_days < 24 or n_horses < 2*runners or not 4 <= runners <= 18:
        raise ValueError("requires >=24 days, >=2×field-size population and 4-18 runners")
    if not 0.0 <= assortment <= 1.0:
        raise ValueError("assortment must be in [0, 1]")
    rng = random.Random(seed)
    horse_ids = [f"FAKE-COMP-H{i:03d}" for i in range(n_horses)]
    # Stable personality proxies and intrinsic ability are drawn independently.
    pace = {h: rng.uniform(0.08, 0.94) for h in horse_ids}
    ability = {h: rng.gauss(0, 0.25) for h in horse_ids}
    rows = []
    for day in range(n_days):
        d = date(2000, 5, 1) + timedelta(days=day)
        if assortment == 0:
            entrant_ids = rng.sample(horse_ids, runners)
        else:
            # Deliberate non-random field entry: early-style animals are
            # preferentially entered on some dates, late-style on others.
            # This creates social assortment WITHOUT causal rival effects.
            high_target = day % 2 == 0
            candidates = list(horse_ids)
            entrant_ids = []
            for _ in range(runners):
                weights = [
                    (1-assortment) + assortment * (
                        1.0 if (pace[h] >= 0.5) == high_target else 0.05
                    )
                    for h in candidates
                ]
                picked = rng.choices(candidates,weights=weights,k=1)[0]
                entrant_ids.append(picked)
                candidates.remove(picked)
        early = {h: pace[h] + rng.gauss(0, 0.10) for h in entrant_ids}
        order = sorted(entrant_ids, key=lambda h: -early[h])
        call = {h: ix + 1 for ix, h in enumerate(order)}
        ground = "重" if day % 2 else "良"
        # The imposed response is an *illustrative generator parameter*, not
        # an ecological estimate. Other race entrants are varied each date.
        speeds = {}
        for h in entrant_ids:
            other_front_fraction = sum(pace[k] >= 0.68 for k in entrant_ids if k != h)/(runners-1)
            interaction_part = interaction * (pace[h]-0.5) * (other_front_fraction-0.35)
            confounded_ground_response = (
                going_style_effect * (pace[h]-0.5) *
                (1 if ground == "重" else -1)
            )
            speeds[h] = (16.0 + 0.48*ability[h] + 0.12*(pace[h]-0.5)
                         + interaction_part + confounded_ground_response
                         + rng.gauss(0,0.065))
        finish_order = sorted(entrant_ids, key=lambda h: -speeds[h])
        finish = {h: rank+1 for rank,h in enumerate(finish_order)}
        for i,h in enumerate(entrant_ids):
            rows.append({
                "race_id": f"FAKE-COMP-R{day:04d}",
                "horse_id": h,
                "race_date_jst": d.isoformat(),
                "race_start_jst": f"{d}T15:00:00+09:00",
                "feature_available_at_jst": f"{d}T12:00:00+09:00",
                "venue": "FICTIONAL-COMPETITION-COURSE",
                "course_surface": "turf",
                "course_distance_m": "1600",
                "track_going": ground,
                "class_pre": "FICTIONAL-COMPETITION-CLASS",
                "jockey_id": f"FAKE-JOCKEY-{i:02d}",
                "field_size": str(runners),
                "finish_status": "finished",
                "finishing_position": str(finish[h]),
                "finish_time_s": f"{1600/speeds[h]:.7f}",
                "first_call_position": str(call[h]),
                "source_url": "synthetic://generated/fictional-changing-rivals",
                "source_license": "synthetic",
            })
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--days",type=int,default=100)
    p.add_argument("--horses",type=int,default=48)
    p.add_argument("--runners",type=int,default=12)
    p.add_argument("--seed",type=int,default=512)
    p.add_argument("--interaction",type=float,default=-0.9)
    p.add_argument("--assortment",type=float,default=0.0,
                   help="0=random entry; >0 deliberately nonrandom field membership")
    p.add_argument("--going-style-effect",type=float,default=0.0,
                   help="Different style responses to going, not a rival effect")
    args=p.parse_args()
    rows=fabricate_competition(
        args.days,args.horses,args.runners,args.seed,args.interaction,
        args.assortment,args.going_style_effect)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=list(REQUIRED)+["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"FABRICATED ONLY: {len(rows)} rows / {args.days} changing-field fake races; {args.output}")


if __name__ == "__main__":
    main()
