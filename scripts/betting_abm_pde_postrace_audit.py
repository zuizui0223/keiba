#!/usr/bin/env python3
"""Nine-race retrospective official-result scoring, separated from v3.1 holdout.

Scores the original market-only exact PL baseline and explicitly fictitious
ABM crowding scenarios against official JRA top-3 results. The race outcome
file is loaded ONLY for scoring. It is never used to tune abilities, crowding,
pace or odds. No prospective result or return-on-bet inference is permitted.

From repository root:
 python scripts/betting_abm_pde_postrace_audit.py --market-only
 python scripts/betting_abm_pde_postrace_audit.py --runs 10000
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
from urllib.parse import urlparse

import numpy as np

from betting_abm_pde_sensitivity import SNAPSHOT, exact_top3, races_from_snapshot, scenario

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "docs/evidence/betting-20261018-official-top3-postrace.json"

STATUS = "POSTRACE_DESCRIPTIVE_NOT_VALIDATED_FORECAST_OR_V31_HOLDOUT"


def load_results(path: Path) -> dict[str, dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("status") != "RETROSPECTIVE_OFFICIAL_JRA_RESULTS_NOT_A_PROSPECTIVE_HOLDOUT":
        raise ValueError("postrace_provenance_status_missing")
    if not doc.get("observed_outcomes_not_allowed_as_model_features"):
        raise ValueError("postrace_feature_leakage_contract_missing")
    if doc.get("race_date") != "2026-10-18":
        raise ValueError("unexpected_results_date")
    records = doc["races"]
    indexed = {}
    for row in records:
        rid = row["race_id"]
        first3 = row["finish_order_top3"]
        parsed = urlparse(row["official_results_url"])
        if (parsed.scheme != "https" or parsed.hostname not in
                {"www.jra.go.jp", "app.jra.jp", "jra.jp"}):
            raise ValueError("invalid_official_source")
        if rid in indexed or not isinstance(first3, list) or len(first3) != 3:
            raise ValueError("duplicate_race_or_invalid_podium")
        if len(set(first3)) != 3 or any(not isinstance(h, int) for h in first3):
            raise ValueError("duplicate_or_noninteger_podium")
        indexed[rid] = row
    return indexed


def probability_score(win, top3, runner_numbers, actual_top3):
    """Proper race-level categorical win log loss and mean per-horse Top3 Brier."""
    win = np.asarray(win, dtype=float)
    top3 = np.asarray(top3, dtype=float)
    n = len(runner_numbers)
    if (win.shape != (n,) or top3.shape != (n,) or n < 3
            or not np.all(np.isfinite(win)) or not np.all(np.isfinite(top3))
            or np.any(win < 0) or np.any(top3 < 0) or np.any(top3 > 1)
            or not np.isclose(win.sum(), 1, atol=1e-6)
            or not np.isclose(top3.sum(), 3, atol=1e-6)):
        raise ValueError("invalid_probability_mass")
    if len(runner_numbers) != len(set(runner_numbers)) or len(actual_top3) != 3:
        raise ValueError("duplicate_runner_or_bad_podium")
    if len(set(actual_top3)) != 3 or not set(actual_top3).issubset(runner_numbers):
        raise ValueError("actual_podium_not_in_scheduled_runners")
    winner_index = runner_numbers.index(actual_top3[0])
    truth = np.asarray([1.0 if h in actual_top3 else 0.0 for h in runner_numbers])
    clip = 1e-12
    return {
        "winner_log_loss": float(-np.log(max(clip, win[winner_index]))),
        "winner_multiclass_brier": float(np.sum(
            (win - (np.arange(n) == winner_index)) ** 2)),
        "top3_binary_brier_mean_horse": float(np.mean((top3 - truth)**2)),
        "top3_binary_log_loss_mean_horse": float(-np.mean(
            truth * np.log(np.clip(top3, clip, 1.0))
            + (1-truth) * np.log(np.clip(1-top3, clip, 1.0)))),
        "realized_winner_model_probability_pct": float(win[winner_index]*100),
    }


def evaluate(*, odds_path=SNAPSHOT, results_path=RESULTS,
             runs=10000, seed=20261023, market_only=False):
    # Odds snapshot is the ONLY inputs to all predictors. Official postrace
    # observations are applied strictly *after* predictions have been created.
    archive = json.loads(Path(odds_path).read_text(encoding="utf-8"))
    observed_at = datetime.fromisoformat(archive["observed_window_end_jst"])
    if observed_at.utcoffset() is None:
        raise ValueError("odds_time_must_include_offset")
    data = list(races_from_snapshot(odds_path))
    records = load_results(Path(results_path))
    if set(records) != {r["race_id"] for r, _, _ in data}:
        raise ValueError("result_races_do_not_match_pre_race_snapshot")
    if not market_only and runs < 10:
        raise ValueError("too_few_synthetic_draws")
    outputs = []
    for race_index, (race, horses, distance) in enumerate(data):
        if observed_at >= datetime.fromisoformat(race["scheduled_post_jst"]):
            raise ValueError("odds_snapshot_not_pre_start")
        win, _, top3 = exact_top3([h["win_odds"] for h in horses])
        n = len(horses)
        forecasts = {
            "uniform": (np.full(n, 1/n), np.full(n, 3/n)),
            "market_PL": (win, top3),
        }
        if not market_only:
            # Outcomes are neither read nor passed to the ABM call.
            abm = scenario([h["win_odds"] for h in horses], distance,
                           draws=runs, seed=seed + race_index)
            for label in ("no_pack", "weak", "strong"):
                forecasts["synthetic_ABM_" + label] = (
                    np.asarray([h[label + "_win_pct"]/100 for h in abm["horses"]]),
                    np.asarray([h[label + "_top3_pct"]/100 for h in abm["horses"]]))
        outcome = records[race["race_id"]]
        horse_numbers = [h["number"] for h in horses]
        top3_nums = outcome["finish_order_top3"]
        ranked_odds3 = sorted(horses, key=lambda h: h["win_odds"])[:3]
        outputs.append({
            "race_id": race["race_id"],
            "race": race["venue"] + str(race["race"]) + "R",
            "scheduled_post_jst": race["scheduled_post_jst"],
            "scored_horses": n,
            "actual_top3": top3_nums,
            "results_source_url": outcome["official_results_url"],
            "market_top3_overlap": sum(h["number"] in top3_nums for h in ranked_odds3),
            "model_scores": {
                label: probability_score(a, b, horse_numbers, top3_nums)
                for label, (a, b) in forecasts.items()
            },
        })
    names = list(outputs[0]["model_scores"])
    metrics = ("winner_log_loss", "winner_multiclass_brier",
               "top3_binary_brier_mean_horse",
               "top3_binary_log_loss_mean_horse")
    means = {
        name: {metric: float(np.mean([r["model_scores"][name][metric]
                                     for r in outputs])) for metric in metrics}
        for name in names
    }
    market = means["market_PL"]
    for name in names:
        means[name]["difference_from_market_lower_is_better"] = {
            metric: means[name][metric] - market[metric]
            for metric in metrics
        }
    return {
        "status": STATUS,
        "method": "Market-only Plackett–Luce exact, independent hypothetical ABM first passages; postrace labels ONLY for scoring",
        "pre_race_odds_observed_at_jst": archive["observed_window_end_jst"],
        "observation_source": "2026-10-18 Yahoo intermediary odds saved before race, unverified upstream timestamp and final price",
        "outcome_source": "JRA official postrace results, independently checked on 2026-10-23",
        "race_count": len(outputs),
        "total_horse_entries": sum(r["scored_horses"] for r in outputs),
        "market_odds_top3_hits_of_total": {
            "hits": sum(r["market_top3_overlap"] for r in outputs),
            "top3_slots": 3 * len(outputs),
        },
        "simulation_repetitions_per_race_and_scenario": None if market_only else runs,
        "simulation_seed": None if market_only else seed,
        "scoring": "Race-average log loss/Brier scores; no per-horse pseudo-replication; Top3 is a binary event for each runner",
        "overall_mean_by_model": means,
        "per_race": outputs,
        "limitations": [
            "Not preregistered or held out: the archived race sample was already chosen for a different retrospective ticket audit.",
            "No odds or model parameter refitting was performed on these race outcomes.",
            "9 races from one calendar date cannot establish transfer, calibration or probability improvement.",
            "ABM inputs depend solely on saved odds and fabricated pace/crowding; no empirical individual trait, running lane, GPS or rival interaction is fitted.",
            "The 10,000 draws quantify model Monte Carlo precision, not forecast calibration or source uncertainty.",
            "Do not append these retrospective results to the v3.1 20-race formal holdout ledger.",
            "No actual returns, payout optimization, adaptive stake allocation or positive betting expectation is estimated.",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--odds", type=Path, default=SNAPSHOT)
    ap.add_argument("--official", type=Path, default=RESULTS)
    ap.add_argument("--runs", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--market-only", action="store_true")
    ap.add_argument("--output", type=Path, default=Path("tmp/abm-postrace-audit.json"))
    args = ap.parse_args()
    result = evaluate(odds_path=args.odds, results_path=args.official,
                      runs=args.runs, seed=args.seed, market_only=args.market_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "races": result["race_count"],
                      "horse_entries": result["total_horse_entries"],
                      "top3_hits": result["market_odds_top3_hits_of_total"],
                      "scores": result["overall_mean_by_model"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
