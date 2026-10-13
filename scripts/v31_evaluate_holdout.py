#!/usr/bin/env python3
"""Evaluate a completed v3.1 holdout against a frozen random-addition baseline."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def hypergeom_pmf(population: int, successes: int, draws: int) -> dict[int, float]:
    if population < 0 or successes < 0 or draws < 0:
        raise ValueError("invalid_hypergeom_parameters")
    if successes > population or draws > population:
        raise ValueError("invalid_hypergeom_parameters")
    if population == 0:
        if successes == 0 and draws == 0:
            return {0: 1.0}
        raise ValueError("invalid_hypergeom_parameters")
    lo = max(0, draws - (population - successes))
    hi = min(draws, successes)
    denom = math.comb(population, draws)
    return {
        x: (math.comb(successes, x) * math.comb(population - successes, draws - x)) / denom
        for x in range(lo, hi + 1)
    }


def convolve(a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
    out: dict[int, float] = {}
    for i, pa in a.items():
        for j, pb in b.items():
            out[i + j] = out.get(i + j, 0.0) + pa * pb
    return out


def evaluate(ledger: dict, contract: dict) -> dict:
    if ledger.get("version") != contract.get("version"):
        raise ValueError("version_mismatch")
    target_races = int(contract["target_races"])
    entries = list(ledger.get("entries", []))
    if len(entries) > target_races:
        raise ValueError("ledger_over_target")

    total_field = 0
    total_m = 0
    total_union = 0
    total_m_hits = 0
    total_union_hits = 0
    expected_extra_hits = 0.0
    distribution = {0: 1.0}

    per_race = []
    for index, entry in enumerate(entries, start=1):
        field = int(entry["field_size"])
        m_count = int(entry["M_candidate_count"])
        union_count = int(entry["candidate_count"])
        m_hits = int(entry["M_top3_hits"])
        union_hits = int(entry["union_top3_hits"])

        if not (0 <= m_count <= union_count <= field):
            raise ValueError(f"invalid_candidate_nesting:{index}")
        if not (0 <= m_hits <= union_hits <= 3):
            raise ValueError(f"invalid_hit_nesting:{index}")
        if m_hits > m_count or union_hits > union_count:
            raise ValueError(f"hits_exceed_candidates:{index}")

        non_m_population = field - m_count
        added_draws = union_count - m_count
        non_m_top3 = 3 - m_hits
        observed_extra = union_hits - m_hits
        if not (0 <= non_m_top3 <= non_m_population):
            raise ValueError(f"invalid_non_m_top3:{index}")
        if not (0 <= added_draws <= non_m_population):
            raise ValueError(f"invalid_added_candidates:{index}")
        if not (0 <= observed_extra <= min(added_draws, non_m_top3)):
            raise ValueError(f"invalid_observed_rescues:{index}")

        pmf = hypergeom_pmf(non_m_population, non_m_top3, added_draws)
        distribution = convolve(distribution, pmf)
        expected = (
            added_draws * non_m_top3 / non_m_population
            if non_m_population else 0.0
        )
        expected_extra_hits += expected
        total_field += field
        total_m += m_count
        total_union += union_count
        total_m_hits += m_hits
        total_union_hits += union_hits

        per_race.append({
            "index": index,
            "race_id": entry.get("race_id"),
            "non_m_population": non_m_population,
            "added_candidates": added_draws,
            "non_m_top3_slots": non_m_top3,
            "observed_additional_hits": observed_extra,
            "expected_additional_hits_random": expected,
        })

    observed_extra_total = total_union_hits - total_m_hits
    p_value = sum(
        probability for rescued, probability in distribution.items()
        if rescued >= observed_extra_total
    )
    p_value = min(1.0, max(0.0, p_value))

    races_scored = len(entries)
    candidate_fraction = total_union / total_field if total_field else None
    union_recall = total_union_hits / (3 * races_scored) if races_scored else None
    m_recall = total_m_hits / (3 * races_scored) if races_scored else None
    added_candidates = total_union - total_m
    added_per_hit = (
        added_candidates / observed_extra_total if observed_extra_total > 0 else None
    )

    observed = {
        "races_scored": races_scored,
        "starter_count": total_field,
        "M_candidate_count": total_m,
        "union_candidate_count": total_union,
        "candidate_fraction": candidate_fraction,
        "M_top3_hits": total_m_hits,
        "union_top3_hits": total_union_hits,
        "M_top3_recall": m_recall,
        "union_top3_recall": union_recall,
        "additional_top3_hits_over_M": observed_extra_total,
        "added_candidates_over_M": added_candidates,
        "added_candidates_per_additional_top3_hit": added_per_hit,
    }
    random_addition = {
        "null": "Within each race, choose the same number of added non-M candidates uniformly at random from all non-M runners, conditional on the observed number of top-three finishers outside M.",
        "expected_additional_hits": expected_extra_hits,
        "observed_additional_hits": observed_extra_total,
        "p_value_one_sided": p_value,
        "total_distribution": {
            str(k): v for k, v in sorted(distribution.items())
        },
    }

    if races_scored < target_races:
        decision = {
            "status": "INCOMPLETE",
            "formal": False,
            "reasons": [f"races_scored_{races_scored}_of_{target_races}"],
        }
    else:
        alpha = float(contract["alpha"])
        ceiling = float(contract["max_candidate_fraction"])
        reasons = []
        if p_value > alpha:
            reasons.append("random_addition_p_above_alpha")
        if candidate_fraction is None or candidate_fraction > ceiling:
            reasons.append("candidate_fraction_above_ceiling")
        decision = {
            "status": "PROMOTE" if not reasons else "NO_PROMOTION",
            "formal": True,
            "reasons": reasons,
            "alpha": alpha,
            "max_candidate_fraction": ceiling,
        }

    return {
        "schema_version": 1,
        "version": ledger.get("version"),
        "contract": contract,
        "observed": observed,
        "random_addition": random_addition,
        "per_race": per_race,
        "decision": decision,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate(read_json(args.ledger), read_json(args.contract))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
