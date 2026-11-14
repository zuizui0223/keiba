#!/usr/bin/env python3
"""Falsification stress test: genuine family signal vs common-stable confounding.

ALL DATA ARE FABRICATED. Simulations demonstrate identifiability failure;
no numerical result is evidence about real Thoroughbred genetics.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import random
from statistics import mean
import tempfile

from ecology_pedigree_forward import screen
from ecology_pedigree_ablation import audit

SCENARIOS = ("family_signal", "shared_trainer_only", "independent_trainer_only")


def fabricate(root: Path, scenario: str, seed: int) -> tuple[Path, Path]:
    if scenario not in SCENARIOS:
        raise ValueError("UNKNOWN_SYNTHETIC_SCENARIO")
    rng = random.Random(seed)
    records, parents = [], []
    # 8 fabricated sire families, 8 offspring each. 4 in training, 2 first
    # encountered in inner validation, 2 only in the later outer test.
    for family in range(8):
        sire = f"SYNTH-SIRE-{family}"
        for child in range(8):
            horse = f"SYNTH-HORSE-{family}-{child}"
            dam = f"SYNTH-DAM-{family}-{child}"
            if scenario == "shared_trainer_only":
                trainer = family
            else:
                # The sire and stable partitions cross in a deterministic pattern.
                trainer = (family * 3 + child * 5) % 8
            latent_family = 0.25 * (family - 3.5)
            latent_stable = 0.25 * (trainer - 3.5)
            if scenario == "family_signal":
                true_effect = latent_family + 0.035 * (trainer - 3.5)
            else:
                true_effect = latent_stable
            horse_noise = rng.gauss(0, 0.04)
            start = 0 if child < 4 else (12 if child < 6 else 17)
            parents.append({
                "horse_id": horse, "sire_id": sire, "dam_id": dam,
                "known_on": "1990-01-01"
            })
            for day in range(start, 20):
                when = (date(2026, 1, 1) + timedelta(days=day)).isoformat()
                records.append({
                    "horse_id": horse,
                    "race_id": f"SYNTH-RACE-{day}-{child % 4}",
                    "race_date": when,
                    "venue": "SYNTHETIC-TRACK",
                    "first_marker_m": "150",
                    "distance_m": "1200",
                    "going": "Good",
                    "race_class": "SIMULATED",
                    "early_section_s": f"{11 + true_effect + horse_noise + rng.gauss(0, 0.095):.8f}",
                    "trainer_id": f"SYNTH-STABLE-{trainer}",
                    "breeder_id": f"SYNTH-BREEDER-{trainer}",
                })
    observations_csv = root / "fabricated_pacing.csv"
    pedigree_csv = root / "fabricated_parents.csv"
    for path, rows in ((observations_csv, records), (pedigree_csv, parents)):
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return observations_csv, pedigree_csv


def run(seeds: tuple[int, ...] = (101, 202, 303)) -> dict:
    scenarios = {}
    for scenario in SCENARIOS:
        comparisons = []
        cross_trainer = []
        chosen_weights = []
        for seed in seeds:
            with tempfile.TemporaryDirectory() as directory:
                observations, parents = fabricate(Path(directory), scenario, seed)
                main = screen(observations, parents, permutations=0, min_horses=10)
                detail = audit(observations, parents, min_horses=10)
            if main["status"].startswith("HOLD") or detail["status"].startswith("HOLD"):
                return {
                    "status": "HOLD_SYNTHETIC_DESIGN_SUPPORT",
                    "failed_scenario": scenario,
                    "not_real_horse_data": True,
                }
            cold = main["rmse_equal_weight_per_horse"]["cold_start_kin_exposed"]
            comparisons.append(cold["M0_minus_M1_RMSE_gain_s"])
            chosen_weights.append(main["tuned_only_on_earlier_dates_lambda"])
            cross_trainer.append(
                detail["channels"]["kin_different_trainer"]["exposed_unique_horses"]
            )
        scenarios[scenario] = {
            "n_synthetic_seeds": len(seeds),
            "mean_cold_start_kin_RMSE_gain_seconds": mean(comparisons),
            "positive_gain_seed_count": sum(x > 0 for x in comparisons),
            "zero_lambda_seed_count": sum(x == 0 for x in chosen_weights),
            "mean_cross_trainer_kin_exposed_horses": mean(cross_trainer),
        }
    return {
        "status": "SYNTHETIC_IDENTIFIABILITY_STRESS_ONLY",
        "scenario_definitions": {
            "family_signal": "fabricated shared sire effect plus weak crossed trainer",
            "shared_trainer_only": "NO causal genetic effect; sire family perfectly aligned to trainer",
            "independent_trainer_only": "NO causal genetic effect; trainers cross sire families",
        },
        "scenarios": scenarios,
        "source_license": "synthetic",
        "biological_genetic_effect_estimated": False,
        "not_heritability_or_evidence_of_horse_breeding_traits": True,
        "no_real_horse_rows_or_individual_ids_exported": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
