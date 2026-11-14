#!/usr/bin/env python3
"""Post hoc kin predictor ablations by immediate lineage and shared management.

Diagnostic ONLY. Same frozen time split and all-kin lambda as
ecology_pedigree_forward.py; no tuned coefficients on test outcomes.
No original individual names, IDs or outcomes are printed/exported.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

from ecology_pedigree_forward import (
    OBS_COLS, pedigree_rows, asof_pedigree, observations,
    read_csv, screen, training_profile, verify_dates, metric,
    SHRINK_KIN, SHRINK_OWN,
)

GROUPS = (
    "all_kin", "full_siblings", "paternal_half_siblings",
    "maternal_half_siblings", "other_related",
    "kin_different_trainer", "kin_different_breeder",
)


def load_metadata(path: Path) -> tuple[dict, dict]:
    rows = read_csv(path, OBS_COLS)
    cols = set(rows[0])
    status = {
        "trainer_id": "PRESENT_BUT_NOT_VERIFIED" if "trainer_id" in cols else "HOLD_ABSENT",
        "breeder_id": "PRESENT_BUT_NOT_VERIFIED" if "breeder_id" in cols else "HOLD_ABSENT",
    }
    return ({
        (r["horse_id"], r["race_id"]): {
            "trainer": r.get("trainer_id", "") or None,
            "breeder": r.get("breeder_id", "") or None,
        }
        for r in rows
    }, status)


def split_type(pedigree, focal: str, other: str) -> str | None:
    if pedigree.relationship(focal, other) < 0.125:
        return None
    fs, fd = pedigree.nodes.get(focal, (None, None))
    os, od = pedigree.nodes.get(other, (None, None))
    sire_match = bool(fs and os and fs == os)
    dam_match = bool(fd and od and fd == od)
    if sire_match and dam_match:
        return "full_siblings"
    # "Half" is only assigned when both NONSHARED parent IDs are known.
    if sire_match and fd and od and fd != od:
        return "paternal_half_siblings"
    if dam_match and fs and os and fs != os:
        return "maternal_half_siblings"
    return "other_related"


def score_one(target, contexts, means, by_profile_rows, pedigree, metadata,
              weight: float):
    key, horse = target["context"], target["horse"]
    if key not in contexts:
        return None
    prior, nown = means.get(key, {}).get(horse, (0.0, 0))
    base = contexts[key] + nown / (nown + SHRINK_OWN) * prior
    record = {"horse": horse, "y": target["y"], "base": base,
              "old": bool(nown)}
    targetmeta = metadata[(horse, target["race"])]
    numerators = {k: 0.0 for k in GROUPS}
    denominators = {k: 0.0 for k in GROUPS}
    support = {k: 0 for k in GROUPS}
    for other, (avg, n_other) in means.get(key, {}).items():
        if other == horse:
            continue
        r = pedigree.relationship(horse, other)
        typ = split_type(pedigree, horse, other)
        if typ is None:
            continue
        shares = ("all_kin", typ)
        for k in shares:
            numerators[k] += r * avg
            denominators[k] += r
            support[k] += 1
        source_rows = by_profile_rows[(key, other)]
        for metadata_key, group in (
            ("trainer", "kin_different_trainer"),
            ("breeder", "kin_different_breeder"),
        ):
            val = targetmeta[metadata_key]
            if val is None:
                continue
            unmatched = [
                row["y"] - contexts[key]
                for row in source_rows
                if metadata[(row["horse"], row["race"])][metadata_key] is not None
                and metadata[(row["horse"], row["race"])][metadata_key] != val
            ]
            if unmatched:
                numerators[group] += r * mean(unmatched)
                denominators[group] += r
                support[group] += 1
    for group in GROUPS:
        family_component = numerators[group] / (SHRINK_KIN + denominators[group])
        record[group] = base + weight * SHRINK_OWN / (nown + SHRINK_OWN) * family_component
        record[group + "_exposed"] = bool(support[group])
        record[group + "_relative_count"] = support[group]
    record["inbreeding_F_from_partial_pedigree"] = pedigree.relationship(horse, horse) - 1
    return record


def audit(observations_file: Path, pedigree_file: Path, *,
          min_horses: int = 20) -> dict:
    base = screen(observations_file, pedigree_file, min_horses=min_horses,
                  permutations=0)
    rows = observations(observations_file)
    _, cutoff = verify_dates(rows)
    metadata, column_status = load_metadata(observations_file)
    pedigree = asof_pedigree(pedigree_rows(pedigree_file), cutoff)
    history = [r for r in rows if r["day"] < cutoff]
    future = [r for r in rows if r["day"] >= cutoff]
    context_means, profiles = training_profile(history)
    by_profile = defaultdict(list)
    for row in history:
        if row["context"] in context_means:
            by_profile[(row["context"], row["horse"])].append(row)
    selected_weight = base["tuned_only_on_earlier_dates_lambda"]
    scored = [
        x for r in future
        if (x := score_one(r, context_means, profiles, by_profile,
                           pedigree, metadata, selected_weight)) is not None
    ]
    stats = {}
    min_support = max(5, min_horses // 4)
    for group in GROUPS:
        exposed = [x for x in scored if x[group + "_exposed"]]
        n_ids = len({x["horse"] for x in exposed})
        base_rmse = metric(exposed, "base")
        alt_rmse = metric(exposed, group)
        status = "EXPLORATORY_DESCRIPTIVE_ONLY" if n_ids >= min_support else "HOLD_LOW_EXPOSURE"
        if group == "kin_different_trainer" and column_status["trainer_id"] == "HOLD_ABSENT":
            status = "HOLD_NO_TRAINER_ID"
        if group == "kin_different_breeder" and column_status["breeder_id"] == "HOLD_ABSENT":
            status = "HOLD_NO_BREEDER_ID"
        stats[group] = {
            "status": status,
            "exposed_scored_rows": len(exposed),
            "exposed_unique_horses": n_ids,
            "M0_RMSE_s_equal_horse_weight": base_rmse,
            "channel_RMSE_s_equal_horse_weight": alt_rmse,
            "M0_minus_channel_gain_s": (
                base_rmse - alt_rmse if base_rmse is not None else None),
            "channel_specific_tuning_on_outer_test": False,
        }
    positive_F = [x["inbreeding_F_from_partial_pedigree"] for x in scored
                  if x["inbreeding_F_from_partial_pedigree"] > 1e-12]
    return {
        "status": ("EXPLORATORY_ABLATION_ONLY_NOT_GENETIC_CAUSATION"
                   if not base["status"].startswith("HOLD")
                   else "HOLD_BASELINE_SOURCE_OR_SUPPORT"),
        "evidence_class": "GENETIC_STRUCTURE_VS_MANAGEMENT_SENSITIVITY_ONLY",
        "original_base_status": base["status"],
        "outer_test_start": cutoff.isoformat(),
        "selected_lambda_in_earlier_validation_only": selected_weight,
        "metadata_availability": column_status,
        "total_scored_rows": len(scored),
        "total_scored_horses": len({x["horse"] for x in scored}),
        "n_scored_rows_with_positive_computed_F": len(positive_F),
        "maximum_observed_computed_F_not_inbreeding_population_estimate":
            max(positive_F) if positive_F else None,
        "channels": stats,
        "limitations": [
            "Pedigree-expected relatedness is NOT DNA similarity or heritability.",
            "Sire/dam half-sib groups require both nonshared parents documented; otherwise other_related.",
            "Each group is compared on its OWN exposed set; compare effect sizes only after checking support.",
            "Relative horses may share breeder, manager, family selection, dam environment and race conditions.",
            "Different-trainer restriction compares documented assigned trainer labels, not certified actual training exposure.",
            "Nested tuning is for all-kin ONLY; subgroup ablations are descriptive and can be underpowered.",
            "Inbreeding F uses documented partial pedigree; zero can mean unknown ancestors.",
        ],
        "no_horse_level_identifiers_or_predictions_exported": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--pedigree", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-horses", type=int, default=20)
    args = parser.parse_args()
    report = audit(args.observations, args.pedigree, min_horses=args.min_horses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
