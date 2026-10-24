#!/usr/bin/env python3
"""Recalculate PRESEALED market/path WIN Top3 trio predictions from source bytes.

The 2026-10-25 Kikka source/freeze files remain PRIVATE and are not
committed to this repository. The source is a two-time public odds
snapshot obtained prestart; each is an index of 1 / quoted WIN odds.

Checks:
  - canonical SHA of the immutable frozen payload,
  - file SHA-256 of the exact private source JSON bytes,
  - source and frozen horse rosters / race ID / clocks,
  - bitwise reproducibility of all three model probability arrays by
    re-running the pre-specified pure forecasting code,
  - no realized podium or JRA official outcome loaded.

The SHA's external PRESTART existence requires separate GitHub comment
or workflow server audit; hashes alone cannot establish chronology.
No raw odds, horse-level probabilities or individual triple rows leave
this script's aggregated output.

CLI:
 python scripts/odds_private_source_replay_audit.py \
   --source private/two_win_snapshots.json \
   --freeze private/sealed_prediction.json \
   --output private/replay-audit.json
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from odds_public_two_point_freeze import (
    INPUT_SCHEMA, FREEZE_SCHEMA, MODELS, freeze, verify_freeze
)

STATUS = "PRIVATE_SOURCE_TO_SEALED_FORECAST_REPLAY_MATCH_NO_POSTRACE_OUTCOMES"


def audit(source_bytes, frozen, *, expected_sha=None, expected_source_sha=None):
    if not isinstance(source_bytes,bytes):
        raise ValueError("HOLD_PRIVATE_SOURCE_MUST_BE_RAW_FILE_BYTES")
    source_sha=sha256(source_bytes).hexdigest()
    if expected_source_sha is not None and source_sha!=expected_source_sha:
        raise ValueError("HOLD_PRECOMMITTED_PRIVATE_SOURCE_SHA_CHANGED")
    try:
        src=json.loads(source_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("HOLD_UNPARSABLE_PRIVATE_SOURCE") from exc
    if src.get("schema")!=INPUT_SCHEMA:
        raise ValueError("HOLD_DIFFERENT_PUBLIC_MARKET_QUOTE_SCHEMA")
    registered=verify_freeze(frozen)
    if expected_sha is not None and frozen["seal_sha256_of_payload"]!=expected_sha:
        raise ValueError("HOLD_PRECOMMITTED_FORECAST_SHA_CHANGED")
    if registered.get("source_private_input_sha256")!=source_sha:
        raise ValueError("HOLD_ORIGINAL_SOURCE_SHA_NOT_LINKED_TO_FORECAST")
    if registered.get("outcome_loaded_before_freeze") is not False:
        raise ValueError("HOLD_OUTCOME_LEAKED_IN_SEALED_FORECAST")
    # Reproduce from exactly the same original bytes, local reported freeze
    # time and the published pre-specified model. NO result or target file.
    copied=freeze(
        src,
        generated_at_jst=registered["local_freeze_generated_at_jst"],
        source_file_sha=source_sha,
    )
    if (copied["seal_sha256_of_payload"]!=frozen["seal_sha256_of_payload"]
            or copied["payload"]!=registered):
        raise ValueError("HOLD_FORECAST_NOT_REPRODUCIBLE_FROM_ITS_MARKET_SOURCE")
    for name,beta,threshold in MODELS:
        p=copied["payload"]["predictions"][name]
        if (len(p["win"])!=len(registered["roster_horse_numbers"])
                or len(p["top3"])!=len(registered["roster_horse_numbers"])):
            raise ValueError("HOLD_REPLAY_INCOMPLETE_SINGLE_HORSE_MARGINALS")
    return {
        "status":STATUS,
        "race_id":registered["race_id"],
        "scheduled_post_jst":registered["post_jst"],
        "source_raw_file_sha256":source_sha,
        "canonical_forecast_payload_sha256":frozen[
            "seal_sha256_of_payload"],
        "matching_original_source_bytes_and_presealed_forecast":True,
        "all_models_recreated_by_same_precommitted_formula":True,
        "full_horse_count":len(registered["roster_horse_numbers"]),
        "full_unordered_top3_combination_count":len(
            copied["payload"]["predictions"][MODELS[0][0]]["trio"]),
        "model_names_in_original_precommit_order":[m[0] for m in MODELS],
        "all_three_joint_rank_distributions_identically_recomputed":True,
        "official_result_read_before_or_during_replay":False,
        "GitHub_server_prestart_evidence_fetched":False,
        "raw_odds_or_individual_probability_values_exported":False,
        "does_not_promote_to_formal_v31_holdout":True,
        "limitations":[
            "This replays mathematical consistency of exact source bytes and the previously sealed models; source-provider correctness must be independently checked.",
            "No external GitHub comment or workflow created_at is verified by this tool.",
            "No future win/place/trio outcome or wager profitability has been checked.",
            "The precommitted +0.25 and exploratory initial 10x terms were not learned in an independent real market training cohort.",
        ],
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--expected-sha")
    ap.add_argument("--expected-source-sha")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    data=audit(
        args.source.read_bytes(),
        json.loads(args.freeze.read_text(encoding="utf-8")),
        expected_sha=args.expected_sha,
        expected_source_sha=args.expected_source_sha,
    )
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":data["status"],
        "race":data["race_id"],
        "horse_count":data["full_horse_count"],
        "trio_count":data["full_unordered_top3_combination_count"],
        "identically_recomputed":True,
        "official_result_used":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
