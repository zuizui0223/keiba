#!/usr/bin/env python3
"""Second historical date: 2026-10-18 (four complete win+wide boards).

Replays the identical win-PL + coherent wide pair-residual tilt implemented for
2026-10-12. Scores 10/18 public JRA top-three *after* the forecast calculation.
This is a calendar-day-separated historical sensitivity check, NOT prospective
independent validation: the model was designed on 2026-11-22 and the archived
intermediary quote's upstream update timestamp is unavailable.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    from scripts.ticket_type_models import KINDS, _time, event_selection, predict_tickets
    from scripts.ticket_type_historical_audit import ROOT, read_json, score_binary_events
    from scripts.ticket_wide_cross_market import (
        EXPLORATORY_ALPHAS, PRIMARY_ALPHA, tilt_wide_joint
    )
except ModuleNotFoundError:
    from ticket_type_models import KINDS, _time, event_selection, predict_tickets
    from ticket_type_historical_audit import ROOT, read_json, score_binary_events
    from ticket_wide_cross_market import (
        EXPLORATORY_ALPHAS, PRIMARY_ALPHA, tilt_wide_joint
    )

DATE = "2026-10-18"
SAVED_SNAPSHOT_PATH = ROOT / "data" / DATE / "ticket-odds-snapshot.json"
OFFICIAL_TOP3_PATH = ROOT / "docs" / "evidence" / "ticket-type-20261018-official-top3.json"


def extract_eligible_snapshot(source: dict, horse_race: dict) -> dict | None:
    """Select complete win+wide markets using *prices alone*, not results."""
    n = horse_race["runner_count"]
    runners = horse_race["horses"]
    wide = horse_race["wide"]
    if not isinstance(wide, list) or len(wide) != n * (n - 1) // 2:
        return None  # HOLD missing wide board, regardless of later finishing order
    if len(runners) != n or not 8 <= n <= 18:
        raise ValueError("race_field_mismatch")
    seen_numbers, strengths, frames = set(), {}, {}
    for h in runners:
        num = h["number"]
        frame = h["frame"]
        odd = h["win_odds"]
        if (type(num) is not int or num in seen_numbers or type(frame) is not int or
                not 1 <= num <= 18 or not 1 <= frame <= 8):
            raise ValueError("invalid_horse_or_frame")
        if isinstance(odd, bool) or not isinstance(odd, (float, int)) or not math.isfinite(odd) or odd < 1:
            raise ValueError("invalid_win_odds")
        seen_numbers.add(num)
        strengths[num] = 1.0 / odd
        frames[num] = frame
    if any(h.get("number") not in strengths for h in runners):
        raise ValueError("runner_mismatch")
    # 2026-10-18 source only states it received an intermediary view at 12:31,
    # not the original JRA time of each win/wide quote. Do not invent synchrony.
    received_start = _time(source["observed_window_start_jst"])
    received_end = _time(source["observed_window_end_jst"])
    start = _time(horse_race["scheduled_post_jst"])
    if (received_start > received_end or received_end >= start or
            (received_end - received_start).total_seconds() > 60):
        raise ValueError("quotes_observed_after_start_or_receipt_window_invalid")
    quotes = []
    seen_pairs = set()
    for item in wide:
        pair = item["horses"]
        if (len(pair) != 2 or any(type(x) is not int for x in pair) or
                pair[0] == pair[1] or not set(pair) <= seen_numbers):
            raise ValueError("invalid_wide_pair")
        key = tuple(sorted(pair))
        if key in seen_pairs:
            raise ValueError("duplicate_wide_price")
        seen_pairs.add(key)
        odds_low, odds_high = item["odds_low"], item["odds_high"]
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or
               not math.isfinite(x) or x < 1 for x in (odds_low, odds_high)):
            raise ValueError("invalid_wide_odds")
        if odds_low > odds_high:
            raise ValueError("wide_odds_range_inverted")
        quotes.append({"selection": list(pair), "odds_low": odds_low, "odds_high": odds_high})
    if len(seen_pairs) != n * (n - 1) // 2:
        raise ValueError("not_all_wide_pairs_present")
    if source.get("upstream_quote_updated_at_jst") is not None:
        raise ValueError("market_timestamp_contract_changed_requires_review")
    if horse_race.get("win_place_upstream_updated_at") or horse_race.get("wide_upstream_updated_at"):
        raise ValueError("race_market_timestamp_contract_changed_requires_review")
    return {
        "race_id": horse_race["race_id"],
        "venue": horse_race["venue"],
        "race": horse_race["race"],
        "start_jst": horse_race["scheduled_post_jst"],
        "received_start": received_start.isoformat(),
        "received_end": received_end.isoformat(),
        "strengths": strengths,
        "frames": frames,
        "wide_quotes": quotes,
        "runner_count": n,
        "quote_update_timestamp_verified": False,
    }


def eligible_four_market_only(source: dict) -> tuple[list[dict], dict]:
    if source.get("status") != "exploratory_market_snapshot_not_v31_holdout":
        raise ValueError("unknown_source_status")
    if source.get("schema_version") != 1:
        raise ValueError("unknown_source_schema")
    if not source.get("races") or source.get("upstream_quote_updated_at_jst") is not None:
        raise ValueError("changed_source_provenance")
    included = []
    excluded = []
    seen = set()
    for r in source["races"]:
        race_id = r["race_id"]
        if race_id in seen or r["date"] != DATE:
            raise ValueError("duplicate_or_different_date")
        seen.add(race_id)
        eligible = extract_eligible_snapshot(source, r)
        if eligible is None:
            excluded.append({"race_id": race_id, "reason": "HOLD_NO_COMPLETE_WIDE_BOARD"})
        else:
            included.append(eligible)
    if len(included) != 4 or len(excluded) != 5:
        raise ValueError("eligibility_universe_changed")
    return included, {"total_races": len(source["races"]), "included": len(included),
                      "excluded": excluded, "criterion": "complete market quotes before seeing official outcomes"}


def score_one(snapshot: dict, top3: list[int]) -> dict:
    if len(top3) != 3 or len(set(top3)) != 3 or not set(top3) <= set(snapshot["strengths"]):
        raise ValueError("invalid_official_top3")
    base = predict_tickets(snapshot["strengths"], snapshot["frames"])
    analyses = {}
    for position in ("low", "geometric", "high"):
        for alpha in EXPLORATORY_ALPHAS:
            post = tilt_wide_joint(
                snapshot["strengths"], snapshot["frames"], snapshot["wide_quotes"],
                odds_position=position, alpha=alpha
            )
            if post["ticket_types"] is None:
                raise ValueError("eligible_complete_market_unexpected_hold")
            tickets = {}
            for kind in KINDS:
                winners = set(event_selection(kind, tuple(top3), snapshot["frames"]))
                b = score_binary_events(base[kind], winners)
                a = score_binary_events(post["ticket_types"][kind], winners)
                tickets[kind] = {
                    "brier_after_minus_PL": a["brier_mean_per_ticket"] - b["brier_mean_per_ticket"],
                    "logloss_after_minus_PL": a["binary_log_loss_mean_per_ticket"] - b["binary_log_loss_mean_per_ticket"],
                    "baseline_brier": b["brier_mean_per_ticket"],
                    "after_brier": a["brier_mean_per_ticket"],
                }
            triple = tuple(top3)
            tickets["ordered_top3_logloss_delta"] = math.log(
                base["trifecta"][triple] / post["ticket_types"]["trifecta"][triple]
            )
            analyses[f"{position}:alpha={alpha:g}"] = {
                "score": tickets,
                "kl_posterior_prior": post["kl_posterior_vs_prior_nats"],
            }
    return {
        "race_id": snapshot["race_id"], "venue": snapshot["venue"],
        "race": snapshot["race"], "runner_count": snapshot["runner_count"],
        "observed_time_end": snapshot["received_end"],
        "start_jst": snapshot["start_jst"],
        "official_top3": top3,
        "quote_update_timestamp_verified": False,
        "analyses": analyses,
    }


def run_second_date() -> dict:
    hashes = {}
    source = read_json(SAVED_SNAPSHOT_PATH, hashes)
    eligible, counts = eligible_four_market_only(source)
    official = read_json(OFFICIAL_TOP3_PATH, hashes)
    if official["race_date"] != DATE or official["freeze_design_status"] != "POSTHOC_NOT_PROSPECTIVE":
        raise ValueError("result_provenance_changed")
    targets = {x["race_id"]: x for x in official["official_results"]}
    if len(targets) != len(official["official_results"]) or set(targets) != {x["race_id"] for x in eligible}:
        raise ValueError("outcome_coverage_not_exact")
    race_reports = []
    for race in eligible:
        result = targets[race["race_id"]]
        if (result["source_type"] != "JRA_official" or
            result["venue"] != race["venue"] or result["race"] != race["race"] or
            not result["source_url"].startswith(("https://jra.jp/JRADB/", "https://app.jra.jp/JRADB/"))):
            raise ValueError("untrusted_or_mismatched_result_source")
        race_reports.append(score_one(race, result["top3"]))
    primary = "geometric:alpha=0.5"
    summary = {}
    for kind in KINDS:
        rows = [x["analyses"][primary]["score"][kind] for x in race_reports]
        ds = [r["brier_after_minus_PL"] for r in rows]
        ls = [r["logloss_after_minus_PL"] for r in rows]
        summary[kind] = {
            "races": len(ds),
            "mean_delta_brier_after_minus_PL": math.fsum(ds) / len(ds),
            "mean_delta_binary_logloss_after_minus_PL": math.fsum(ls) / len(ls),
            "improve": sum(v < -1e-12 for v in ds),
            "harm": sum(v > 1e-12 for v in ds),
            "tie": sum(abs(v) <= 1e-12 for v in ds),
        }
    joint = [x["analyses"][primary]["score"]["ordered_top3_logloss_delta"] for x in race_reports]
    return {
        "status": "SECOND_DATE_RETROSPECTIVE_NOT_PROSPECTIVE",
        "design_frozen_before_result": False,
        "quote_upstream_times_verified": False,
        "market_prices_from_final_payout": False,
        "no_retrospective_selection_from_results": True,
        "positive_expected_value_established": False,
        "independent_date_after_initial_source": True,
        "date": DATE,
        "alpha_posthoc": PRIMARY_ALPHA,
        "market_only_eligibility": counts,
        "primary_summary": summary,
        "joint_ordered_top3_logloss_delta_mean": math.fsum(joint) / len(joint),
        "source_sha256": dict(sorted(hashes.items())),
        "races": race_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run_second_date()
    except (ValueError, KeyError, TypeError, ZeroDivisionError, OverflowError) as exc:
        parser.error(str(exc))
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
