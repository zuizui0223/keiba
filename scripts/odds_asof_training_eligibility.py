#!/usr/bin/env python3
"""Event-time as-of leakage audit for historical WIN/WIDE research.

A prior race result may train a model for a target only if its OFFICIAL
result had already been independently captured and verified before the
target's last necessary feature source was received. The current
repository's 2026-10-12 Kyoto 8-12R market samples were all acquired
at 13:27:xx JST, BEFORE Kyoto 8R's 14:00 post. Therefore NONE of
the five real races may be used to learn from another's realized outcome
for those saved market decisions. Race number ordering is NOT as-of
training evidence.

The 2026-10-12 official-results-final.json verified_at_jst records
23:46:27 JST: a conservative *documented availability* bound, NOT
JRA's first-publication time. A later verification can undercount
available training but can never establish an earlier availability.

No odds- or race-outcome model is fitted here. This script does NOT
create a valid retrospective prospective holdout. Actual model code
was written after the races; no pre-result freeze existed then.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from odds_five_race_joint_market_score import (
    pre_race_forecasts, WIDE_SOURCE,
)
from odds_real_multirace_archive_audit import SOURCE_SHA
from odds_six_race_predictive_increment import (
    OFFICIAL_OCT12_BLOB_SHA, verify_official_oct12,
)

ROOT = Path(__file__).resolve().parents[1]
STATUS = "REAL_20261012_ALL_FIVE_PRESTART_MARKETS_NOT_PREQUEL_TO_ANY_RECORDED_RESULT"
SYNTHETIC_STATUS = "ASOF_EVENT_AVAILABILITY_RULES_DEMONSTRATION_NOT_REAL_HOLDOUT"


def _aware(x: str) -> datetime:
    if not isinstance(x, str):
        raise ValueError("HOLD_NONSTRING_TIME")
    v = datetime.fromisoformat(x)
    if v.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_TIMESTAMP")
    return v


def training_graph(forecast_events: list[dict], result_events: list[dict]) -> dict:
    """Return admissible prior *race IDs*, never actual outcome labels.

    Forecast event fields:
      race_id, quote_published_at, last_required_feature_received_at,
      scheduled_post_jst, feature_source_verified=true.
    Result event fields:
      race_id, scheduled_post_jst, independent_official_result_verified_at,
      official_source_verified=true.

    The *receiver clock* controls availability. A displayed quote's update
    time alone does not prove the analyst could access it then.
    """
    if not forecast_events:
        raise ValueError("HOLD_EMPTY_PRESTART_FORECAST_EVENTS")
    if not isinstance(result_events, list):
        raise ValueError("HOLD_RESULT_EVENT_TYPE")
    fids = [f.get("race_id") for f in forecast_events]
    rids = [r.get("race_id") for r in result_events]
    if (any(not isinstance(x, str) or not x for x in fids + rids)
            or len(set(fids)) != len(fids)
            or len(set(rids)) != len(rids)):
        raise ValueError("HOLD_DUPLICATE_OR_MISSING_RACE_ID")
    results = {}
    for r in result_events:
        if r.get("official_source_verified") is not True:
            raise ValueError("HOLD_UNVERIFIED_RESULT_PROVENANCE")
        published_post = _aware(r["scheduled_post_jst"])
        available = _aware(r["independent_official_result_verified_at"])
        if not published_post < available:
            raise ValueError("HOLD_RESULT_VERIFIED_BEFORE_RACE_START")
        results[r["race_id"]] = {
            "post": published_post,
            "documented_available": available,
        }
    forecasts = {}
    for f in forecast_events:
        if f.get("feature_source_verified") is not True:
            raise ValueError("HOLD_UNVERIFIED_FEATURE_SOURCE")
        published = _aware(f["quote_published_at"])
        received = _aware(f["last_required_feature_received_at"])
        post = _aware(f["scheduled_post_jst"])
        if not published <= received < post:
            raise ValueError("HOLD_FEATURE_NOT_RECEIVED_BEFORE_RACE_START")
        forecasts[f["race_id"]] = {
            "quote_pub": published, "asof": received, "post": post,
        }
        # Defensively reject result / forecast source post contradictions.
        if f["race_id"] in results and post != results[f["race_id"]]["post"]:
            raise ValueError("HOLD_POST_TIME_DISAGREES_BETWEEN_EVENT_SOURCES")
    output = []
    for rid in sorted(forecasts, key=lambda z:(
            forecasts[z]["asof"], z)):
        current = forecasts[rid]
        can_use = []
        for prior, r in results.items():
            if (prior != rid
                    and r["post"] < current["asof"]
                    and r["post"] < current["post"]
                    and r["documented_available"] < current["asof"]):
                can_use.append(prior)
        available_ids = sorted(can_use)
        output.append({
            "race_id": rid,
            "asof_last_feature_received_at": current["asof"].isoformat(),
            "last_quote_source_published_at": current["quote_pub"].isoformat(),
            "scheduled_post_at": current["post"].isoformat(),
            "known_prior_official_result_ids": available_ids,
            "n_admissible_historical_training_results": len(available_ids),
            "could_fit_a_result_based_beta_from_saved_prior_races":
                len(available_ids) >= 2,
        })
    return {
        "method": "STRICT_DOCUMENTED_ASOF_NOT_RACE_NUMBER_BACKTEST",
        "race_count": len(output),
        "distinct_result_ids": len(results),
        "available_training_relationships": sum(
            len(row["known_prior_official_result_ids"]) for row in output),
        "targets_with_any_documented_prior_outcomes": sum(
            bool(row["known_prior_official_result_ids"]) for row in output),
        "targets_with_at_least_two_documented_training_outcomes": sum(
            row["could_fit_a_result_based_beta_from_saved_prior_races"]
            for row in output),
        "per_race": output,
        "no_real_future_holdout_created": True,
        "result_verification_is_conservative_upper_bound_on_first_publication":
            True,
    }


def audit(root=ROOT) -> dict:
    # Every source-snapshot and raw quote hash is validated by the existing
    # pre-result-only feature builder. Its outputs are built before results.
    forecasts = pre_race_forecasts(root)
    events = []
    for f in forecasts:
        quote_last = max(
            _aware(f["win_page_source_updated_at"]),
            _aware(f["wide_page_source_updated_at"]))
        events.append({
            "race_id": f["race_id"],
            "scheduled_post_jst": f["scheduled_post"],
            "quote_published_at": quote_last.isoformat(),
            "last_required_feature_received_at": f["last_page_received_at"],
            "feature_source_verified": True,
        })
    # Now open the verified postrace result source. The capture timestamp
    # is the only time this archive safely supports for result availability.
    official, available = verify_official_oct12(root)
    outcomes = []
    for f in forecasts:
        result = official["races"][str(f["race_no"])]
        if not result["complete_top3"] or result["source_type"] != "JRA_official":
            raise ValueError("HOLD_INCOMPLETE_OFFICIAL_RESULT")
        outcomes.append({
            "race_id": f["race_id"],
            "scheduled_post_jst": f["scheduled_post"],
            "independent_official_result_verified_at": available.isoformat(),
            "official_source_verified": True,
        })
    graph = training_graph(events, outcomes)
    if graph["race_count"] != 5 or graph["available_training_relationships"] != 0:
        raise ValueError("HOLD_ARCHIVED_COHORT_ASOF_EXPECTATION_CHANGED")
    latest_receipt = max(_aware(x["last_required_feature_received_at"])
                         for x in events)
    earliest_start = min(_aware(x["scheduled_post_jst"]) for x in events)
    if not latest_receipt < earliest_start:
        raise ValueError("HOLD_ARCHIVED_FIVE_MARKETS_NO_LONGER_ALL_PRESTART")
    return {
        "status": STATUS,
        "meeting_date": "2026-10-12",
        "source_result_git_blob": OFFICIAL_OCT12_BLOB_SHA,
        "win_price_source_pinned_races": sorted(SOURCE_SHA),
        "wide_price_source_pinned_races": sorted(WIDE_SOURCE),
        "last_full_win_wide_market_received_at": latest_receipt.isoformat(),
        "earliest_scheduled_race_post": earliest_start.isoformat(),
        "minutes_between_last_market_receive_and_first_race_post":
            (earliest_start - latest_receipt).total_seconds() / 60,
        "official_result_verified_at_not_original_jra_publish_time":
            available.isoformat(),
        "earliest_official_result_cannot_exist_before_first_race_post":
            True,
        "all_five_forecast_features_available_before_any_of_five_races_started":
            True,
        "result_available_for_same_day_other_race_model_fit": False,
        "within_meeting_training_graph": graph,
        "scientific_interpretation": [
            "A retrospective random train/test split across these five races is physically time-inconsistent at the observed 13:27 predictor cutoff.",
            "A race number smaller than the target does not prove its result existed before the target's quote was captured.",
            "The archived 23:46 official verification is a safe recorded-availability bound, not the first publication time.",
            "Across-day future experiments are possible if predictors are locked and source-aligned, but none exists for this same-day cohort.",
            "No model was prospectively frozen before the 2026-10-12 races; do not relabel retrospective simulations as a preregistered holdout.",
        ],
    }


def demo():
    """Three artificial races validate admissibility without real result data."""
    return training_graph(
        [
            {"race_id": "SYNTH-A", "quote_published_at": "2026-01-01T11:40+09:00",
             "last_required_feature_received_at": "2026-01-01T12:00+09:00",
             "scheduled_post_jst": "2026-01-01T14:00+09:00",
             "feature_source_verified": True},
            {"race_id": "SYNTH-B", "quote_published_at": "2026-01-01T13:30+09:00",
             "last_required_feature_received_at": "2026-01-01T13:35+09:00",
             "scheduled_post_jst": "2026-01-01T15:00+09:00",
             "feature_source_verified": True},
            {"race_id": "SYNTH-C", "quote_published_at": "2026-01-02T12:00+09:00",
             "last_required_feature_received_at": "2026-01-02T12:15+09:00",
             "scheduled_post_jst": "2026-01-02T15:00+09:00",
             "feature_source_verified": True},
        ],
        [
            {"race_id": "SYNTH-A", "scheduled_post_jst": "2026-01-01T14:00+09:00",
             "independent_official_result_verified_at": "2026-01-01T14:20+09:00",
             "official_source_verified": True},
            {"race_id": "SYNTH-B", "scheduled_post_jst": "2026-01-01T15:00+09:00",
             "independent_official_result_verified_at": "2026-01-01T15:20+09:00",
             "official_source_verified": True},
            {"race_id": "SYNTH-C", "scheduled_post_jst": "2026-01-02T15:00+09:00",
             "independent_official_result_verified_at": "2026-01-02T15:20+09:00",
             "official_source_verified": True},
        ],
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--demo", action="store_true")
    p.add_argument("--output", type=Path,
                   default=Path("tmp/odds-asof-training-eligibility.json"))
    args = p.parse_args()
    data = demo() if args.demo else audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({
        "status": SYNTHETIC_STATUS if args.demo else STATUS,
        "races": data["race_count"] if args.demo else data[
            "within_meeting_training_graph"]["race_count"],
        "admissible_result_to_forecast_training_relations":
            data["available_training_relationships"] if args.demo else
            data["within_meeting_training_graph"][
                "available_training_relationships"],
        "synthetic": args.demo,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
