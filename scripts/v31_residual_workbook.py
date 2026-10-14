#!/usr/bin/env python3
"""Generate a descriptive residual-evidence workbook for a validated v3.1 race.

Never change a frozen prediction, result, score or holdout ledger. Every missed
top-three horse starts as UNREVIEWED; this script does not infer a causal
explanation from knowing the race result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from v31_validate_postrace import validate as validate_postrace


CHANNELS = ("M", "C1", "U", "Q1", "K1", "rescue", "union")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def market_ranks(horses: list[dict]) -> dict[int, int | None]:
    """Competition ranks from *frozen pre-race* win odds; never final odds."""
    odds = {}
    for horse in horses:
        n = int(horse["number"])
        value = horse.get("frozen_win_odds")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            odds[n] = None
        else:
            odds[n] = float(value)
    valid = [value for value in odds.values() if value is not None]
    return {
        n: (1 + sum(other < value for other in valid) if value is not None else None)
        for n, value in odds.items()
    }


def workbook(freeze_path: Path, result_path: Path, score_path: Path,
             attempt_path: Path, race_input_path: Path,
             source_meta_path: Path) -> dict:
    verified = validate_postrace(freeze_path, result_path, score_path, attempt_path)
    frozen = read_json(freeze_path)
    race_input = read_json(race_input_path)
    source_meta = read_json(source_meta_path)
    score = read_json(score_path)

    integrity = frozen.get("integrity") or {}
    require(
        integrity.get("race_input_sha256") == sha256_file(race_input_path),
        "race_input_hash_mismatch",
    )
    require(
        integrity.get("source_capture_meta_sha256") == sha256_file(source_meta_path),
        "source_meta_hash_mismatch",
    )
    race_id = verified["race_id"]
    require(race_input.get("race_id") == race_id, "race_input_race_id_mismatch")
    require(source_meta.get("race_id") == race_id, "source_meta_race_id_mismatch")
    require(source_meta.get("uses_target_race_results") is False,
            "source_meta_result_contamination")

    frozen_horses = frozen["horses"]
    source_horses = race_input["horses"]
    by_frozen = {int(row["number"]): row for row in frozen_horses}
    by_source = {int(row["number"]): row for row in source_horses}
    require(
        len(by_source) == len(source_horses)
        and set(by_frozen) == set(by_source),
        "source_horse_set_mismatch",
    )

    top3 = [int(n) for n in score["top3"]]
    ranks = market_ranks(frozen_horses)
    union = {int(n) for n in frozen["sets"]["union"]}
    misses = []
    for number in [int(n) for n in score["misses"]]:
        form = by_source[number]
        prediction = by_frozen[number]
        misses.append({
            "horse_number": number,
            "horse_name": prediction.get("name") or form.get("name"),
            "actual_finish": top3.index(number) + 1,
            "frozen_win_odds": prediction.get("frozen_win_odds"),
            "frozen_market_rank": ranks[number],
            "frozen_membership": {
                key: bool(prediction.get(key)) for key in CHANNELS
            },
            "uncertainty_flags": list(prediction.get("uncertainty_flags") or []),
            "frozen_course_counts": {
                "K_wins": prediction.get("K_wins"),
                "K_top3": prediction.get("K_top3"),
            },
            "pre_race_history": {
                "age": form.get("age"),
                "career_starts_before_target": form.get(
                    "career_starts_before_target"
                ),
                "last4": form.get("last4", []),
                "full_history_before_target": form.get(
                    "full_history_before_target", []
                ),
                "profile_url": form.get("profile_url"),
            },
            "postrace_context": {
                "official_sectional_seconds": None,
                "verified_trip_or_interference": None,
                "source_url": None,
            },
            "review": {
                "classification": "UNREVIEWED",
                "allowed_categories": [
                    "DATA", "REPRESENTATION", "THRESHOLD",
                    "STATE_STOCHASTIC", "UNRESOLVED",
                ],
                "supporting_evidence": [],
                "alternative_explanations": [],
                "unexplained_remainder": None,
                "reviewed_at": None,
            },
        })

    union_hits = int(score["union_top3_hits"])
    require(len(misses) == 3 - union_hits, "miss_count_mismatch")
    report = {
        "schema_version": 1,
        "kind": "v3.1_postrace_residual_workbook",
        "race_id": race_id,
        "holdout_version": frozen.get("holdout_version"),
        "affects_formal_score": False,
        "review_status": "PENDING_EVIDENCE_REVIEW" if misses else "NO_UNION_MISS",
        "evidence_order": [
            "immutable_frozen_pre_race_input",
            "independently_verified_pre_race_sources",
            "official_target_race_result_and_sectionals",
            "postrace_comments_as_supplementary_context",
        ],
        "result_source_attestation": "NOT_VERIFIED_BY_WORKBOOK_GENERATOR",
        "coverage": {
            "field_size": len(frozen_horses),
            "union_candidate_count": len(union),
            "candidate_fraction": frozen.get("candidate_fraction"),
            "union_top3_hits": union_hits,
            "M_top3_hits": int(score["M_top3_hits"]),
            "union_miss_count": len(misses),
            "non_top3_union_candidates": len(union) - union_hits,
        },
        "input_integrity": {
            "prerace_freeze_sha256": sha256_file(freeze_path),
            "race_input_sha256": sha256_file(race_input_path),
            "source_capture_meta_sha256": sha256_file(source_meta_path),
            "result_input_sha256": sha256_file(result_path),
            "formal_score_sha256": sha256_file(score_path),
        },
        "misses": misses,
        "interpretation_limit": (
            "An unexpected outcome is not a causal diagnosis. An UNREVIEWED "
            "miss must not be assigned to pace, health, condition or randomness "
            "without specific supporting evidence. The formal score and "
            "holdout denominator must remain unchanged."
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("freeze", "result", "score", "attempt-ledger",
                "race-input", "source-meta", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = workbook(
            args.freeze, args.result, args.score, args.attempt_ledger,
            args.race_input, args.source_meta,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "race_id": report["race_id"],
            "union_miss_count": report["coverage"]["union_miss_count"],
            "review_status": report["review_status"],
        }, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError,
            json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
