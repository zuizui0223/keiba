#!/usr/bin/env python3
"""Sensitivity summary for archived 2026-10-12/18 *posthoc* coherent wide tilts.

This script never selects alpha or quote endpoint based on results. It reports
all 3 nonzero alphas x 3 quote positions for both already-inspected dates.
A variant that succeeds only for one outcome, one date or one ticket type
is not a validated predictive gain.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    from scripts.ticket_type_models import KINDS
except ModuleNotFoundError:
    from ticket_type_models import KINDS

POSITIONS = ("low", "geometric", "high")
ALPHAS = (0.25, 0.5, 1.0)
TOL = 1e-12


def summarize(first: dict, second: dict) -> dict:
    if (first.get("status") != "RETROSPECTIVE_DEVELOPMENT_NO_PROSPECTIVE_SKILL_CLAIM" or
            second.get("status") != "SECOND_DATE_RETROSPECTIVE_NOT_PROSPECTIVE" or
            first.get("pre_registered_before_outcome") is not False or
            second.get("design_frozen_before_result") is not False or
            len(first["races"]) != 5 or len(second["races"]) != 4):
        raise ValueError("invalid_or_claimed_prospective_input")
    reports = {}
    for kind in KINDS:
        by_date = {}
        for date, source, score_key in (
            ("2026-10-12", first, "scores"),
            ("2026-10-18", second, "score"),
        ):
            rows = []
            for position in POSITIONS:
                for alpha in ALPHAS:
                    key = f"{position}:alpha={alpha:g}"
                    deltas = [
                        race["analyses"][key][score_key][kind]["brier_after_minus_PL"]
                        for race in source["races"]
                    ]
                    logdeltas = [
                        race["analyses"][key][score_key][kind]["logloss_after_minus_PL"]
                        for race in source["races"]
                    ]
                    if any(not isinstance(d, (int, float)) or not math.isfinite(d)
                           for d in deltas + logdeltas):
                        raise ValueError("nonfinite_sensitivity")
                    rows.append({
                        "quote_position": position,
                        "alpha": alpha,
                        "n_races": len(deltas),
                        "mean_delta_brier_after_minus_PL": math.fsum(deltas)/len(deltas),
                        "mean_delta_binary_logloss_after_minus_PL": math.fsum(logdeltas)/len(logdeltas),
                        "improve_races": sum(d < -TOL for d in deltas),
                    })
            by_date[date] = rows
        normal = next(r for r in by_date["2026-10-12"] if r["alpha"] == 0.5 and r["quote_position"] == "geometric")
        later = next(r for r in by_date["2026-10-18"] if r["alpha"] == 0.5 and r["quote_position"] == "geometric")
        reports[kind] = {
            "primary_20261012_delta": normal["mean_delta_brier_after_minus_PL"],
            "primary_20261018_delta": later["mean_delta_brier_after_minus_PL"],
            "alpha_price_grid": by_date,
            "n_positive_brier_change_configs_20261012": sum(
                r["mean_delta_brier_after_minus_PL"] > TOL for r in by_date["2026-10-12"]),
            "n_positive_brier_change_configs_20261018": sum(
                r["mean_delta_brier_after_minus_PL"] > TOL for r in by_date["2026-10-18"]),
            "n_configs_each_day": len(POSITIONS) * len(ALPHAS),
            "same_primary_direction_across_both_dates": (
                normal["mean_delta_brier_after_minus_PL"] *
                later["mean_delta_brier_after_minus_PL"] > TOL * TOL
            ),
        }
    return {
        "status": "POSTHOC_SENSITIVITY_NOT_INDEPENDENT_EVIDENCE",
        "dates": ["2026-10-12", "2026-10-18"],
        "race_count_by_date": {"2026-10-12": 5, "2026-10-18": 4},
        "alpha_grid_not_optimised": list(ALPHAS),
        "price_range_positions": list(POSITIONS),
        "hypothesis_test_p_value_produced": False,
        "market_inefficiency_established": False,
        "ticket_types": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = summarize(
            json.loads(args.first.read_text(encoding="utf-8")),
            json.loads(args.second.read_text(encoding="utf-8")),
        )
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    result = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
