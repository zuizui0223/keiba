#!/usr/bin/env python3
"""Offline, time-forward pedigree *predictive* screen for first-GPS timing.

This is NOT an estimate of heritability or a betting model. No original
horse-level rows or pedigree identities are emitted by the report.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date
from functools import lru_cache
import json
import math
from pathlib import Path
import random
from statistics import mean

OBS_COLS = {
    "horse_id", "race_id", "race_date", "venue", "first_marker_m",
    "distance_m", "going", "race_class", "early_section_s",
}
PED_COLS = {"horse_id", "sire_id", "dam_id", "known_on"}
LAMBDAS = (0.0, 0.25, 0.5, 1.0)
SHRINK_OWN = 2.0
SHRINK_KIN = 2.0


def read_csv(path: Path, columns: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or columns - set(reader.fieldnames):
            raise ValueError("HOLD_MISSING_COLUMNS:" + ",".join(sorted(columns - set(reader.fieldnames or []))))
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in reader]
    if not rows:
        raise ValueError("HOLD_EMPTY_CSV")
    return rows


def observations(path: Path) -> list[dict]:
    output, seen, races = [], set(), {}
    for record in read_csv(path, OBS_COLS):
        horse, race = record["horse_id"], record["race_id"]
        if not horse or not race or (horse, race) in seen:
            raise ValueError("HOLD_BAD_OR_DUPLICATE_HORSE_RACE_ID")
        seen.add((horse, race))
        day = date.fromisoformat(record["race_date"])
        try:
            seconds = float(record["early_section_s"])
            marker = float(record["first_marker_m"])
            distance = float(record["distance_m"])
        except ValueError as exc:
            raise ValueError("HOLD_BAD_NUMERIC_MEASUREMENT") from exc
        if not (math.isfinite(seconds) and seconds > 0 and
                math.isfinite(marker) and 0 < marker <= distance and
                math.isfinite(distance) and distance > 0):
            raise ValueError("HOLD_NONFINITE_OR_NONPOSITIVE_TIMING_OR_DISTANCE")
        context = (record["venue"], record["first_marker_m"], record["distance_m"],
                   record["going"], record["race_class"])
        if not all(context):
            raise ValueError("HOLD_INCOMPLETE_CONTEXT")
        if race in races and races[race] != (day, context):
            raise ValueError("HOLD_RACE_ID_CONTEXT_INCONSISTENT")
        races[race] = (day, context)
        output.append({"horse": horse, "race": race, "day": day,
                       "context": context, "y": seconds})
    return sorted(output, key=lambda r: (r["day"], r["race"], r["horse"]))


class Pedigree:
    """Numerator relationship A; unknown founder identities are unrelated."""

    def __init__(self, records: dict[str, tuple[str | None, str | None]]):
        nodes = dict(records)
        for sire, dam in list(nodes.values()):
            for parent in (sire, dam):
                if parent and parent not in nodes:
                    nodes[parent] = (None, None)
        done, visiting, order = set(), set(), []

        def visit(horse: str) -> None:
            if horse in done:
                return
            if horse in visiting:
                raise ValueError("HOLD_PEDIGREE_CYCLE")
            visiting.add(horse)
            for parent in nodes[horse]:
                if parent:
                    visit(parent)
            visiting.remove(horse)
            done.add(horse)
            order.append(horse)

        for horse in nodes:
            visit(horse)
        self.nodes = nodes
        self.rank = {horse: i for i, horse in enumerate(order)}
        self.relationship = lru_cache(maxsize=None)(self._relationship)

    def _relationship(self, a: str | None, b: str | None) -> float:
        if a is None or b is None or a not in self.nodes or b not in self.nodes:
            return 0.0
        if a == b:
            sire, dam = self.nodes[a]
            return 1.0 + 0.5 * self.relationship(sire, dam)
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        sire, dam = self.nodes[a]
        return 0.5 * (self.relationship(sire, b) + self.relationship(dam, b))


def pedigree_rows(path: Path) -> list[dict]:
    rows, seen = [], set()
    for row in read_csv(path, PED_COLS):
        horse, sire, dam = row["horse_id"], row["sire_id"] or None, row["dam_id"] or None
        if not horse or horse in seen or horse == sire or horse == dam or (sire and sire == dam):
            raise ValueError("HOLD_PEDIGREE_ID_CONFLICT")
        seen.add(horse)
        rows.append({"horse": horse, "sire": sire, "dam": dam,
                     "known_on": date.fromisoformat(row["known_on"])})
    # Check the whole supplied lineage for cycles even when hidden as-of.
    Pedigree({r["horse"]: (r["sire"], r["dam"]) for r in rows})
    return rows


def asof_pedigree(rows: list[dict], cutoff: date) -> Pedigree:
    return Pedigree({
        r["horse"]: (r["sire"], r["dam"]) for r in rows
        if r["known_on"] < cutoff
    })


def training_profile(history: list[dict], min_context: int = 4):
    by_context = defaultdict(list)
    for row in history:
        by_context[row["context"]].append(row)
    contexts = {}
    residuals = defaultdict(list)
    for key, records in by_context.items():
        # Context mean is exclusively learned from earlier dates.
        if len(records) < min_context or len({r["horse"] for r in records}) < 3:
            continue
        center = mean(r["y"] for r in records)
        contexts[key] = center
        for row in records:
            residuals[(key, row["horse"])].append(row["y"] - center)
    horse_residuals = defaultdict(dict)
    for (context, horse), vals in residuals.items():
        horse_residuals[context][horse] = (mean(vals), len(vals))
    return contexts, horse_residuals


def predict(target: dict, contexts: dict, histories: dict,
            pedigree: Pedigree, weight: float, label_map: dict[str, str] | None = None):
    context, horse = target["context"], target["horse"]
    if context not in contexts:
        return None
    peers = histories.get(context, {})
    own, n_own = peers.get(horse, (0.0, 0))
    primary = contexts[context] + n_own / (n_own + SHRINK_OWN) * own
    ksum, numerator, n_rel = 0.0, 0.0, 0
    for other, (average, count) in peers.items():
        if other == horse:
            continue   # Biological focal's own past MUST NOT enter kin signal.
        a = label_map[horse] if label_map and horse in label_map else horse
        b = label_map[other] if label_map and other in label_map else other
        related = pedigree.relationship(a, b)
        if related >= 0.125:
            ksum += related
            numerator += related * average   # one vote per relative, not per race
            n_rel += 1
    family_signal = numerator / (SHRINK_KIN + ksum)
    expanded = primary + weight * (SHRINK_OWN / (n_own + SHRINK_OWN)) * family_signal
    return {"y": target["y"], "base": primary, "kin": expanded,
            "horse": horse, "day": target["day"],
            "own_prior": bool(n_own), "kin_prior": bool(n_rel),
            "relatives": n_rel}


def evaluate(history: list[dict], future: list[dict],
             pedigree: Pedigree, weight: float,
             label_map: dict[str, str] | None = None) -> list[dict]:
    contexts, horse_means = training_profile(history)
    return [score for row in future
            if (score := predict(row, contexts, horse_means, pedigree,
                                 weight, label_map)) is not None]


def metric(scores: list[dict], key: str) -> float | None:
    if not scores:
        return None
    per_horse = defaultdict(list)
    for r in scores:
        per_horse[r["horse"]].append((r[key] - r["y"]) ** 2)
    return math.sqrt(mean(mean(v) for v in per_horse.values()))


def group_report(scores: list[dict]) -> dict:
    output = {}
    for group, entries in {
        "all": scores,
        "own_history": [s for s in scores if s["own_prior"]],
        "cold_start": [s for s in scores if not s["own_prior"]],
        "kin_exposed": [s for s in scores if s["kin_prior"]],
        "cold_start_kin_exposed": [
            s for s in scores if not s["own_prior"] and s["kin_prior"]],
    }.items():
        m0, m1 = metric(entries, "base"), metric(entries, "kin")
        output[group] = {
            "scored_rows": len(entries),
            "unique_horses": len({e["horse"] for e in entries}),
            "M0_RMSE_s": m0, "M1_RMSE_s": m1,
            "M0_minus_M1_RMSE_gain_s": (m0 - m1 if m0 is not None else None),
        }
    return output


def verify_dates(rows: list[dict]) -> tuple[date, date]:
    dates = sorted({r["day"] for r in rows})
    if len(dates) < 10:
        raise ValueError("HOLD_NEED_10_DISTINCT_DATES_FOR_NESTED_TIME_SPLIT")
    outer = dates[int(0.8 * len(dates))]
    inner_dates = [d for d in dates if d < outer]
    inner = inner_dates[int(0.7 * len(inner_dates))]
    return inner, outer


def screen(observations_csv: Path, pedigree_csv: Path, *, permutations: int = 49,
           min_horses: int = 20) -> dict:
    rows = observations(observations_csv)
    ancestry = pedigree_rows(pedigree_csv)
    inner, outer = verify_dates(rows)
    early, validation = [r for r in rows if r["day"] < inner], [
        r for r in rows if inner <= r["day"] < outer]
    training, test = [r for r in rows if r["day"] < outer], [
        r for r in rows if r["day"] >= outer]
    pedigree_inner = asof_pedigree(ancestry, inner)
    pedigree_outer = asof_pedigree(ancestry, outer)
    inner_scores = {
        weight: evaluate(early, validation, pedigree_inner, weight)
        for weight in LAMBDAS
    }
    # All hyperparameter selection uses past dates, never outer heldout timing.
    if len({s["horse"] for s in inner_scores[0.0]}) < max(5, min_horses // 3):
        selected, inner_status = 0.0, "HOLD_TOO_FEW_INNER_VALIDATION_HORSES"
    else:
        selected, inner_status = min(
            LAMBDAS, key=lambda w: (metric(inner_scores[w], "kin"), w)
        ), "TRAIN_ONLY_SELECTION_COMPLETED"
    scores = evaluate(training, test, pedigree_outer, selected)
    main = group_report(scores)
    eligible = len({s["horse"] for s in scores})
    related_eligible = len({s["horse"] for s in scores if s["kin_prior"]})
    if inner_status != "TRAIN_ONLY_SELECTION_COMPLETED":
        status = "HOLD_INNER_TUNING"
    elif eligible < min_horses:
        status = "HOLD_TOO_FEW_OUTER_HORSES"
    elif related_eligible < max(5, min_horses // 4):
        status = "HOLD_TOO_FEW_RELATED_OUTER_HORSES"
    else:
        status = "EXPLORATORY_TIME_FORWARD_ASSOCIATION_NOT_HERITABILITY"
    rng = random.Random(20261114)
    in_panel = sorted({r["horse"] for r in rows})
    placebos = []
    for _ in range(permutations):
        labels = in_panel[:]
        rng.shuffle(labels)
        mapping = dict(zip(in_panel, labels))
        sham = evaluate(training, test, pedigree_outer, selected, mapping)
        placebos.append(metric(sham, "kin"))
    actual_rmse = main["all"]["M1_RMSE_s"]
    placebo_rmse = [x for x in placebos if x is not None]
    counted = set(pedigree_outer.nodes)
    known = {r["horse"] for r in ancestry if r["known_on"] < outer}
    linked = sum(
        s["kin_prior"] for s in scores
    )
    return {
        "status": status,
        "evidence_class": "OFFLINE_PREDICTIVE_SCREEN_ONLY",
        "outcome": "absolute_first_GPS_section_seconds",
        "not_full_race_time_or_winning_probability": True,
        "not_a_genetic_heritability_or_causal_inference": True,
        "train_date_exclusive_end": outer.isoformat(),
        "inner_validation_start": inner.isoformat(),
        "train_dates": len({r["day"] for r in training}),
        "heldout_dates": len({r["day"] for r in test}),
        "heldout_rows_total": len(test),
        "matched_context_rows": len(scores),
        "inner_status": inner_status,
        "tuned_only_on_earlier_dates_lambda": selected,
        "pedigree_rows_available_as_of_outer_cutoff": len(known),
        "pedigree_nodes_including_unobserved_founders": len(counted),
        "heldout_horses_with_documented_asof_pedigree": len(
            {r["horse"] for r in test if r["horse"] in known}),
        "related_heldout_scored_horses": related_eligible,
        "related_heldout_scored_rows": linked,
        "rmse_equal_weight_per_horse": main,
        "permuted_identity_negative_control": {
            "fixed_seed": 20261114,
            "n_permutations": len(placebo_rmse),
            "fraction_placebo_RMSE_below_or_equal_actual": (
                sum(x <= actual_rmse for x in placebo_rmse) / len(placebo_rmse)
                if placebo_rmse and actual_rmse is not None else None
            ),
            "not_a_calibrated_causal_p_value": True,
        },
        "source_rights_and_horse_identity_requires_independent_audit": True,
        "pedigree_unknown_founders_assumed_unrelated": True,
        "within_context_excludes_future_and_same_day_races": True,
        "limitations": [
            "Selection and own-history shrinkage were fixed or tuned only before the outer cutoff.",
            "Exact venue/marker/distance/going/class contexts may sharply reduce effective sample size.",
            "Shared training, breeder allocation, maternal environment and race-entry selection can mimic genetic effects.",
            "Retrospective known_on metadata cannot independently certify as-of public availability.",
            "A single heldout split and shuffled-pedigree diagnostic do not establish heritability.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--pedigree", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--permutations", type=int, default=49)
    parser.add_argument("--min-horses", type=int, default=20)
    args = parser.parse_args()
    if not 0 <= args.permutations <= 999 or args.min_horses < 5:
        parser.error("bad permutation count or support gate")
    result = screen(args.observations, args.pedigree,
                    permutations=args.permutations, min_horses=args.min_horses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "lambda": result["tuned_only_on_earlier_dates_lambda"],
        "rmse": result["rmse_equal_weight_per_horse"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
