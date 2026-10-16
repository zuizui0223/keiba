#!/usr/bin/env python3
"""Descriptive v3.1 comparison with a same-size win-odds shortlist.

Reads a valid pre-result freeze and a separately captured result only AFTER
the race; never changes the frozen shortlist or the formal promotion decision.
This is a secondary descriptive comparator, not a probability/EV estimator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def unique_ints(raw, label: str) -> list[int]:
    require(isinstance(raw, list), f"invalid_{label}")
    out = [int(x) for x in raw]
    require(len(out) == len(set(out)), f"duplicate_{label}")
    return out


def compute(frozen: dict, result: dict) -> dict:
    require(frozen.get("uses_target_race_results") is False,
            "invalid_prerace_freeze")
    race_id = frozen.get("race_id")
    require(isinstance(race_id, str) and bool(race_id), "missing_race_id")
    require(result.get("race_id") == race_id, "race_id_mismatch")
    horses = frozen.get("horses")
    require(isinstance(horses, list) and len(horses) >= 3, "invalid_horses")

    numbers = unique_ints([h["number"] for h in horses], "horse_numbers")
    all_numbers = set(numbers)
    by_number = {int(h["number"]): h for h in horses}
    require(frozen.get("field_size") == len(horses), "field_size_mismatch")

    sets = frozen.get("sets") or {}
    union_list = unique_ints(sets.get("union"), "union")
    market_list = unique_ints(sets.get("M"), "M")
    union = set(union_list)
    market = set(market_list)
    require(union.issubset(all_numbers), "union_unknown_horse")
    require(market.issubset(union), "M_not_subset_of_union")
    k = len(union)
    require(0 < k <= len(horses), "invalid_union_size")
    require(frozen.get("candidate_count") == k, "candidate_count_mismatch")

    ordered = []
    for n in numbers:
        odds = by_number[n].get("frozen_win_odds")
        require(odds is not None, f"missing_frozen_odds:{n}")
        try:
            value = float(odds)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid_frozen_odds:{n}") from exc
        require(math.isfinite(value) and value > 0.0, f"invalid_frozen_odds:{n}")
        ordered.append((value, n))
    ordered.sort()
    market_same_size = [n for _, n in ordered[:k]]

    actual_top3 = unique_ints(result.get("top3"), "top3")
    require(len(actual_top3) == 3 and set(actual_top3).issubset(all_numbers),
            "invalid_top3")

    selected_market = set(market_same_size)
    union_hits = [n for n in actual_top3 if n in union]
    market_hits = [n for n in actual_top3 if n in selected_market]
    cutoff = ordered[k - 1][0]
    before_cutoff = {n for odds, n in ordered if odds < cutoff}
    tied = [n for odds, n in ordered if odds == cutoff]
    tie_slots = k - len(before_cutoff)
    hits_before = len(before_cutoff.intersection(actual_top3))
    hits_tied = len(set(tied).intersection(actual_top3))
    min_tie_hits = max(0, tie_slots - (len(tied) - hits_tied))
    max_tie_hits = min(tie_slots, hits_tied)

    return {
        "schema_version": 1,
        "race_id": race_id,
        "holdout_version": frozen.get("holdout_version"),
        "confirmatory": False,
        "development_and_holdout_descriptive_only": True,
        "comparison": "frozen_v31_union_vs_same_size_win_odds_rank",
        "field_size": len(horses),
        "candidate_count": k,
        "v31_candidate_set": sorted(union),
        "market_same_size": market_same_size,
        "actual_top3": actual_top3,
        "v31_top3_hits": len(union_hits),
        "market_same_size_top3_hits": len(market_hits),
        "v31_minus_market_top3_hits": len(union_hits) - len(market_hits),
        "v31_unique_top3": [n for n in actual_top3 if n in union and n not in selected_market],
        "market_unique_top3": [n for n in actual_top3 if n in selected_market and n not in union],
        "v31_winner_in_candidates": actual_top3[0] in union,
        "market_winner_in_candidates": actual_top3[0] in selected_market,
        "market_cutoff_ties": {
            "cutoff_win_odds": cutoff,
            "tied_horses": tied,
            "slots_filled_from_ties": tie_slots,
            "min_top3_hits": hits_before + min_tie_hits,
            "max_top3_hits": hits_before + max_tie_hits,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        frozen = load(args.freeze)
        result = load(args.result)
        comparison = compute(frozen, result)
        comparison["integrity"] = {
            "freeze_sha256": file_sha256(args.freeze),
            "result_sha256": file_sha256(args.result),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "race_id": comparison["race_id"],
            "v31_top3_hits": comparison["v31_top3_hits"],
            "market_same_size_top3_hits": comparison["market_same_size_top3_hits"],
            "confirmatory": False,
        }, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
