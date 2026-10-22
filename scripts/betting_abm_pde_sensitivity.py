#!/usr/bin/env python3
"""Synthetic win/place ABM and PDE numerical check.

The archived win-odds Plackett-Luce model supplies the baseline ranking
distribution. Pace and crowding are invented scenarios, NOT fitted horses'
traits or a validated wagering strategy. PDE checks numerical conservation;
it is not a horse-level winning-probability model.

Run from repository root:
 python scripts/betting_abm_pde_sensitivity.py --venue 京都 --race 11 --runs 10000
 python scripts/betting_abm_pde_sensitivity.py --all-races --runs 1000
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/2026-10-18/ticket-odds-snapshot.json"


def exact_top3(odds):
    """Exact PL win/top2/top3 probabilities; each position is unique."""
    odds = np.asarray(odds, dtype=float)
    if odds.ndim != 1 or len(odds) < 3 or np.any(odds <= 1) or not np.all(np.isfinite(odds)):
        raise ValueError("Need >=3 positive finite decimal win odds")
    w = 1 / odds
    total = float(w.sum())
    p1 = w / total
    p2 = p1.copy()
    p3 = p1.copy()
    for i in range(len(w)):
        for j in range(len(w)):
            if i == j:
                continue
            p_ji = w[j] / total * w[i] / (total - w[j])
            p2[i] += p_ji
            p3[i] += p_ji
            for k in range(len(w)):
                if k != i and k != j:
                    p3[i] += (w[j] / total * w[k] / (total - w[j])
                              * w[i] / (total - w[j] - w[k]))
    return p1, p2, p3


def first_passage(latent, pace, distance_m, crowd_penalty_mps,
                  *, delta_t=1.0, radius_m=6.0, max_time=200.0):
    """One-dimensional agents; interpolated finish times, not fixed-time ranks."""
    latent = np.asarray(latent, dtype=float)
    pace = np.asarray(pace, dtype=float)
    if latent.ndim != 2 or latent.shape != pace.shape:
        raise ValueError("latent and pace arrays must have identical 2-D shape")
    if distance_m <= 0 or crowd_penalty_mps < 0 or delta_t <= 0 or radius_m <= 0:
        raise ValueError("Invalid model parameters")
    pos = np.zeros_like(latent)
    arrival = np.full_like(latent, np.inf)
    nominal_time = distance_m / 16.8
    for step in range(int(math.ceil(max_time / delta_t))):
        active = ~np.isfinite(arrival)
        if not active.any():
            break
        if crowd_penalty_mps:
            active_pos = np.where(active, pos, np.inf)
            order = np.argsort(active_pos, axis=1, kind="stable")
            sorted_pos = np.take_along_axis(active_pos, order, axis=1)
            with np.errstate(invalid="ignore"):
                gap = sorted_pos[:, 1:] - sorted_pos[:, :-1]
            near = np.isfinite(gap) & (gap > 0) & (gap < radius_m)
            sorted_penalty = np.zeros_like(sorted_pos)
            sorted_penalty[:, :-1] = (crowd_penalty_mps
                                    * np.exp(-np.where(near, gap, 0.0) / radius_m) * near)
            crowding = np.zeros_like(pos)
            np.put_along_axis(crowding, order, sorted_penalty, axis=1)
        else:
            crowding = 0.0
        phase = (step + 0.5) * delta_t / nominal_time
        speed = (16.8 + 0.10 * latent
                 + pace * math.cos(2 * math.pi * phase) - crowding)
        if np.any(speed[active] <= 0):
            raise ValueError("Synthetic nonpositive speed")
        crossed = active & (pos + speed * delta_t >= distance_m)
        arrival[crossed] = (step * delta_t
                            + (distance_m - pos[crossed]) / speed[crossed])
        pos[active] += speed[active] * delta_t
    if not np.all(np.isfinite(arrival)):
        raise ValueError("Agents failed to finish; do not impute placements")
    return arrival


def ranked(arrival):
    order = np.argsort(arrival, axis=1)
    draws, n = order.shape
    return (order, [np.bincount(order[:, :k].ravel(), minlength=n) / draws
                    for k in (1, 2, 3)])


def paired_delta(order0, order1, horse_idx, topk):
    reference = np.any(order0[:, :topk] == horse_idx, axis=1)
    treatment = np.any(order1[:, :topk] == horse_idx, axis=1)
    paired = treatment.astype(int) - reference.astype(int)
    mean = float(paired.mean())
    se = float(paired.std(ddof=1) / math.sqrt(len(paired)))
    return {"difference_percentage_points": 100 * mean,
            "monte_carlo_ci95_pp": [100 * (mean - 1.96 * se), 100 * (mean + 1.96 * se)],
            "changed_outcome_fraction": float(np.mean(paired != 0))}


def scenario(odds, distance_m, *, draws=10000, seed=20261023,
             pace_sd_mps=0.32):
    odds = np.asarray(odds, dtype=float)
    exact = exact_top3(odds)
    if draws < 10 or pace_sd_mps < 0:
        raise ValueError("Invalid simulation size or pace SD")
    rng = np.random.default_rng(seed)
    latent = np.log(1.0 / odds)[None, :] + rng.gumbel(size=(draws, len(odds)))
    pace = rng.normal(0, pace_sd_mps, size=(draws, len(odds)))
    orders, probabilities = {}, {}
    for name, strength in (("no_pack", 0.0), ("weak", 0.08), ("strong", 0.20)):
        orders[name], probabilities[name] = ranked(
            first_passage(latent, pace, distance_m, strength))
    f = int(np.argmin(odds))
    horses = []
    for i in range(len(odds)):
        horses.append({
            "index": i,
            "win_odds": float(odds[i]),
            "market_win_pct": float(100 * exact[0][i]),
            "market_top2_pct": float(100 * exact[1][i]),
            "market_top3_pct": float(100 * exact[2][i]),
            **{name + "_win_pct": float(100 * probabilities[name][0][i])
               for name in probabilities},
            **{name + "_top3_pct": float(100 * probabilities[name][2][i])
               for name in probabilities},
            "paired_strong_minus_no_pack_win": paired_delta(
                orders["no_pack"], orders["strong"], i, 1),
            "paired_strong_minus_no_pack_top3": paired_delta(
                orders["no_pack"], orders["strong"], i, 3),
        })
    return {"status": "SYNTHETIC_MARKET_REFERENCE_NOT_CALIBRATED_HORSE_PROBABILITIES",
            "draws_per_scenario": draws, "seed": seed,
            "distance_m": distance_m, "n_horses": len(odds),
            "market_overround": float(np.sum(1 / odds)),
            "favorite_index": f, "horses": horses,
            "assumptions": {
                "ability": "log(inverse saved win odds) + IID Gumbel",
                "speed": "16.8 + 0.10*ability + synthetic cosine pace - crowd penalty (m/s)",
                "pace_sd_mps": pace_sd_mps,
                "penalties_mps": [0.0, 0.08, 0.20],
                "radius_m": 6.0, "space": "1D, no lanes or jockeys",
            },
            "uncertainty_scope": "Paired intervals quantify MC noise only, not parameter uncertainty or horse skill calibration."}


def pde_gaussian_check(*, dx=0.5, dt=0.025, duration=40.0, drift=0.5, diffusion=3.0):
    """Conservative finite-volume Fokker-Planck vs Gaussian analytic solution."""
    if dt * (abs(drift) / dx + 2 * diffusion / (dx * dx)) > 1:
        raise ValueError("Unstable explicit PDE step")
    x = np.arange(-200.0, 200.0 + dx / 2, dx)
    initial_sd = 10.0
    density = np.exp(-x*x / (2 * initial_sd**2))
    density /= np.sum(density) * dx
    for _ in range(round(duration / dt)):
        flux = np.zeros(len(x) + 1)
        flux[1:-1] = drift * density[:-1] - diffusion * np.diff(density) / dx
        density -= dt * np.diff(flux) / dx
    sd = math.sqrt(initial_sd**2 + 2 * diffusion * duration)
    truth = np.exp(-0.5 * ((x - drift * duration)/sd)**2) / (sd * math.sqrt(2*math.pi))
    mass = float(density.sum() * dx)
    return {
        "total_mass": mass,
        "mean_m": float(np.sum(x * density) * dx / mass),
        "expected_mean_m": drift * duration,
        "l1_error_against_gaussian": float(np.sum(np.abs(density - truth)) * dx),
        "nonnegative": bool(np.all(density >= -1e-12)),
        "scope": "PDE mathematical validation only; not win/place probabilities",
    }


def races_from_snapshot(path, venue=None, race=None):
    snapshot = json.loads(Path(path).read_text(encoding="utf-8"))
    if snapshot.get("status") != "exploratory_market_snapshot_not_v31_holdout":
        raise ValueError("Expected explicitly marked exploratory archive")
    for r in snapshot["races"]:
        if venue is not None and (r["venue"] != venue or r["race"] != race):
            continue
        horses = r["horses"]
        if r["runner_count"] != len(horses):
            raise ValueError("Missing runners")
        if len(set(h["number"] for h in horses)) != len(horses):
            raise ValueError("Duplicate horse number")
        import re
        m = re.search(r"(\d+)m", r["course"])
        if not m:
            raise ValueError("Missing official course distance")
        yield r, horses, float(m.group(1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--odds-json", type=Path, default=SNAPSHOT)
    parser.add_argument("--venue", default="京都")
    parser.add_argument("--race", type=int, default=11)
    parser.add_argument("--all-races", action="store_true")
    parser.add_argument("--runs", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--output", type=Path, default=Path("tmp/abm-pde"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    entries = []
    rows = []
    selected = list(races_from_snapshot(
        args.odds_json, None if args.all_races else args.venue,
        None if args.all_races else args.race))
    if not selected:
        raise ValueError("Requested race not in archived snapshot")
    for offset, (race, horses, distance) in enumerate(selected):
        result = scenario([h["win_odds"] for h in horses], distance,
                          draws=args.runs, seed=args.seed + offset)
        result["race"] = race["venue"] + str(race["race"]) + "R"
        result["source_race_id"] = race["race_id"]
        for h, estimate in zip(horses, result.pop("horses")):
            rows.append({**{"race_id": race["race_id"], "venue": race["venue"],
                           "race": race["race"], "horse_no": h["number"],
                           "horse_name": h["name"]}, **estimate})
        result["favorite"] = rows[-len(horses) + result["favorite_index"]]
        entries.append(result)
    summary = {"status": "SYNTHETIC_ONLY_NOT_VALIDATED_WIN_OR_PLACE_FORECAST",
               "source": str(args.odds_json),
               "selected_races": len(entries),
               "pde": pde_gaussian_check(),
               "races": entries}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.output / "horses.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v
                          for k, v in row.items()} for row in rows)
    print(json.dumps({"status": summary["status"], "races": len(entries),
                      "draws_per_scenario": args.runs, "pde": summary["pde"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
