#!/usr/bin/env python3
"""Independently reconcile a frozen v3.1 prediction, official result, score and attempt.

This validator is observational. It never changes v3.1 candidate membership,
a pre-result freeze, the scoring contract or either ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise ValueError(label)


def _numbers(values, label: str) -> list[int]:
    require(isinstance(values, list), f"invalid_{label}")
    out = [int(v) for v in values]
    require(len(out) == len(set(out)), f"duplicate_{label}")
    return out


def _dt(value: str) -> datetime:
    t = datetime.fromisoformat(value)
    require(t.tzinfo is not None and t.utcoffset() is not None, "naive_freeze_timestamp")
    return t


def validate(freeze_path: Path, result_path: Path, score_path: Path,
             attempts_path: Path) -> dict:
    frozen = load(freeze_path)
    result = load(result_path)
    score = load(score_path)
    attempts = load(attempts_path)

    require(frozen.get("uses_target_race_results") is False, "invalid_prerace_freeze")
    race_id = frozen.get("race_id")
    require(isinstance(race_id, str) and bool(race_id), "missing_race_id")
    for name, document in (("result", result), ("score", score)):
        assert_equal(document.get("race_id"), race_id, f"{name}_race_id_mismatch")
    assert_equal(score.get("holdout_version"), frozen.get("holdout_version"),
                 "score_version_mismatch")

    post = _dt(frozen["scheduled_start_jst"])
    obs = _dt(frozen["freeze_observed_at_jst"])
    market_obs = _dt(frozen["odds_observed_at_jst"])
    require(market_obs <= obs < post, "invalid_freeze_chronology")
    for dt in (obs, market_obs):
        minutes = (post - dt).total_seconds() / 60.0
        require(15.0 <= minutes <= 25.0, "invalid_freeze_window")

    freeze_hash = sha256(freeze_path)
    score_integrity = score.get("integrity") or {}
    assert_equal(score_integrity.get("prerace_freeze_sha256"), freeze_hash,
                 "score_freeze_hash_mismatch")
    assert_equal(score_integrity.get("result_input_sha256"), sha256(result_path),
                 "score_result_hash_mismatch")

    matching_attempts = [
        a for a in attempts.get("entries", [])
        if a.get("race_id") == race_id
    ]
    require(len(matching_attempts) == 1, "attempt_record_missing_or_duplicate")
    attempt = matching_attempts[0]
    assert_equal(attempt.get("status"), "FROZEN", "attempt_not_frozen")
    assert_equal(attempt.get("freeze_sha256"), freeze_hash,
                 "attempt_freeze_hash_mismatch")
    assert_equal(attempt.get("scheduled_start_jst"), frozen["scheduled_start_jst"],
                 "attempt_start_mismatch")
    assert_equal(attempts.get("version"), frozen.get("holdout_version"),
                 "attempt_version_mismatch")

    horses = frozen.get("horses") or []
    numbers = _numbers([h["number"] for h in horses], "horse_numbers")
    by_number = {int(h["number"]): h for h in horses}
    require(len(numbers) >= 3, "insufficient_field")
    sets = frozen.get("sets") or {}
    union = set(_numbers(sets.get("union"), "union"))
    market = set(_numbers(sets.get("M"), "M"))
    require(union.issubset(set(numbers)), "union_unknown_horse")
    require(market.issubset(union), "M_not_subset_of_union")
    require(all(bool(by_number[n].get("union")) for n in union),
            "union_flags_inconsistent")
    require(all(bool(by_number[n].get("M")) for n in market),
            "M_flags_inconsistent")
    assert_equal(frozen.get("field_size"), len(horses), "freeze_field_mismatch")
    assert_equal(frozen.get("candidate_count"), len(union), "freeze_candidates_mismatch")
    require(frozen.get("candidate_fraction") == len(union) / len(horses),
            "freeze_fraction_mismatch")

    top3 = _numbers(result.get("top3"), "result_top3")
    require(len(top3) == 3 and set(top3).issubset(set(numbers)),
            "invalid_result_top3")
    assert_equal(_numbers(score.get("top3"), "score_top3"), top3,
                 "score_top3_mismatch")
    hit_union = [n for n in top3 if n in union]
    hit_m = [n for n in top3 if n in market]
    expected_rescues = [
        {"number": n,
         "channels": [c for c in ("C1", "U", "Q1", "K1", "rescue")
                      if by_number[n].get(c)],
         "captured": n in union}
        for n in top3 if n not in market
    ]

    assert_equal(score.get("winner"), top3[0], "score_winner_mismatch")
    assert_equal(score.get("field_size"), len(numbers), "score_field_mismatch")
    assert_equal(score.get("candidate_count"), len(union), "score_candidates_mismatch")
    assert_equal(score.get("candidate_fraction"), len(union) / len(numbers),
                 "score_fraction_mismatch")
    assert_equal(score.get("union_top3_hits"), len(hit_union), "score_union_hits_mismatch")
    assert_equal(score.get("M_top3_hits"), len(hit_m), "score_M_hits_mismatch")
    assert_equal(score.get("union_top3_hit_numbers"), hit_union,
                 "score_union_hit_numbers_mismatch")
    assert_equal(score.get("M_top3_hit_numbers"), hit_m, "score_M_hit_numbers_mismatch")
    assert_equal(score.get("top3_recall"), len(hit_union) / 3.0,
                 "score_union_recall_mismatch")
    assert_equal(score.get("M_top3_recall"), len(hit_m) / 3.0,
                 "score_M_recall_mismatch")
    assert_equal(score.get("winner_in_union"), top3[0] in union,
                 "score_winner_membership_mismatch")
    assert_equal(score.get("misses"), [n for n in top3 if n not in union],
                 "score_misses_mismatch")
    assert_equal(score.get("non_M_top3_rescues"), expected_rescues,
                 "score_rescues_mismatch")
    return {
        "valid": True,
        "race_id": race_id,
        "freeze_sha256": freeze_hash,
        "score_sha256": sha256(score_path),
        "top3": top3,
        "union_top3_hits": len(hit_union),
        "M_top3_hits": len(hit_m),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("freeze", "result", "score", "attempt-ledger"):
        parser.add_argument("--" + arg, type=Path, required=True)
    args = parser.parse_args()
    try:
        outcome = validate(args.freeze, args.result, args.score, args.attempt_ledger)
        print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
