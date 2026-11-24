#!/usr/bin/env python3
"""Coherent wide-odds residual transfer into all eight ticket distributions.

Research-only. Observed wide odds are NOT calibrated pari-mutuel probabilities;
normalizing inverse quoted prices yields only a baseline proxy. The shrinkage
parameter alpha=0.5 is a *posthoc development design*, not a calibrated value.

For each pair i,j, compare Q_ij (wide market proxy) to P_ij (win-only PL).
For top-three ordering (i,j,k), tilt its PL probability by:
  exp((alpha/3) * [log(Q_ij/P_ij) + log(Q_ik/P_ik) + log(Q_jk/P_jk)])
then renormalize across ALL ordered top-three outcomes. The output remains a
single valid joint distribution, so every ticket type is internally coherent.
No outcomes are read during forecast; no purchases or expected ROI.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations, permutations
import hashlib
import json
import math
from pathlib import Path

try:
    from scripts.ticket_type_models import KINDS, event_selection, predict_tickets, _time
    from scripts.ticket_type_historical_audit import (
        ROOT, TARGET_RACES, SOURCE_DATE, direct_own_market,
        market_race, read_json, score_binary_events,
    )
except ModuleNotFoundError:  # invoking as python scripts/ticket_wide_cross_market.py
    from ticket_type_models import KINDS, event_selection, predict_tickets, _time
    from ticket_type_historical_audit import (
        ROOT, TARGET_RACES, SOURCE_DATE, direct_own_market,
        market_race, read_json, score_binary_events,
    )

PRIMARY_ALPHA = 0.5
EXPLORATORY_ALPHAS = (0.0, 0.25, 0.5, 1.0)
MAX_WIN_WIDE_RECEIPT_GAP_SECONDS = 90


def tilt_wide_joint(strengths: dict[int, float], frames: dict[int, int],
                    wide_quotes: list[dict], *, alpha: float = PRIMARY_ALPHA,
                    odds_position: str = "geometric") -> dict:
    """Return a coherent eight-type distribution and audit metadata.

    No partial quote imputation. Conditional on complete and valid quote board.
    """
    if isinstance(alpha, bool) or not isinstance(alpha, (float, int)) or not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("alpha_out_of_bounds")
    base = predict_tickets(strengths, frames)
    if set(base) != set(KINDS) or len(strengths) < 8:
        raise ValueError("requires_full_eight_type_race")
    implied, quote_status = direct_own_market(
        wide_quotes, "wide", set(base["wide"]), odds_position=odds_position
    )
    if not implied:
        return {
            "status": quote_status["status"],
            "reason": "wide_prices_not_complete_and_valid",
            "ticket_types": None,
            "wide_quote_status": quote_status,
        }
    lifts = {key: math.log(implied[key] / p) for key, p in base["wide"].items()}
    if not all(math.isfinite(v) for v in lifts.values()):
        raise ValueError("nonfinite_pair_lifts")
    nums = sorted(strengths)
    vals = {n: float(strengths[n]) for n in nums}
    if any(not math.isfinite(v) or v <= 0 for v in vals.values()):
        raise ValueError("invalid_strength")
    scale = max(vals.values())
    weights = {n: val / scale for n, val in vals.items()}
    total = math.fsum(weights.values())
    terms = []
    for i, j, k in permutations(nums, 3):
        original = (weights[i] / total *
                    weights[j] / (total - weights[i]) *
                    weights[k] / (total - weights[i] - weights[j]))
        pairs = (tuple(sorted((i, j))), tuple(sorted((i, k))), tuple(sorted((j, k))))
        adjustment = (alpha / 3) * math.fsum(lifts[pair] for pair in pairs)
        terms.append(((i, j, k), original, original * math.exp(adjustment)))
    normalizer = math.fsum(weight for _, _, weight in terms)
    if not math.isfinite(normalizer) or normalizer <= 0:
        raise ValueError("invalid_tilt_normalizer")
    output = {kind: defaultdict(float) for kind in KINDS}
    kl_posterior_prior = 0.0
    for ordering, prior_prob, unnormalized in terms:
        p = unnormalized / normalizer
        kl_posterior_prior += p * math.log(p / prior_prob)
        for kind in KINDS:
            for selection in event_selection(kind, ordering, frames):
                output[kind][selection] += p
    result = {kind: dict(dist) for kind, dist in output.items()}
    expected_mass = {"place": 3.0, "wide": 3.0}
    for kind in KINDS:
        if set(result[kind]) != set(base[kind]):
            raise ValueError("ticket_support_changed")
        wanted = expected_mass.get(kind, 1.0)
        if not math.isclose(math.fsum(result[kind].values()), wanted, abs_tol=1e-10, rel_tol=1e-10):
            raise ValueError(f"marginal_incoherence:{kind}")
    return {
        "status": "AVAILABLE_UNCALIBRATED_POSTHOC_DEVELOPMENT",
        "alpha": float(alpha),
        "price_position": odds_position,
        "wide_quote_status": quote_status,
        "kl_posterior_vs_prior_nats": kl_posterior_prior,
        "max_abs_wide_market_pair_log_lift": max(abs(v) for v in lifts.values()),
        "mean_abs_wide_market_pair_log_lift":
            math.fsum(abs(v) for v in lifts.values()) / len(lifts),
        "ticket_types": result,
    }


def market_quote_time_guard(snapshot: dict) -> float:
    times = snapshot.get("market_observation_times")
    if not isinstance(times, dict) or not {"win", "wide"} <= set(times):
        raise ValueError("missing_market_observation_times")
    win_observed, wide_observed = _time(times["win"]), _time(times["wide"])
    cutoff, start = _time(snapshot["receipt_as_of"]), _time(snapshot["start_jst"])
    if not win_observed <= cutoff < start or not wide_observed <= cutoff:
        raise ValueError("market_quote_time_leakage")
    gap = abs((win_observed - wide_observed).total_seconds())
    if gap > MAX_WIN_WIDE_RECEIPT_GAP_SECONDS:
        raise ValueError("cross_market_quotes_not_synchronous")
    return gap


def _actual_selections(top3: list[int], frames: dict[int, int], kind: str) -> set:
    return set(event_selection(kind, tuple(top3), frames))


def audit_one(race_number: int, official: dict, hashes: dict) -> dict:
    snapshot = market_race(race_number, hashes)
    gap = market_quote_time_guard(snapshot)
    actual = official["races"][str(race_number)]
    if actual["source_type"] != "JRA_official" or not actual["complete_top3"]:
        raise ValueError("official_result_invalid")
    top3 = actual["positions"]
    if len(top3) != 3 or len(set(top3)) != 3 or not set(top3) <= set(snapshot["win_odds"]):
        raise ValueError("invalid_official_top3")
    strengths = {n: 1 / odd for n, odd in snapshot["win_odds"].items()}
    base = predict_tickets(strengths, snapshot["frames"])
    analyses = {}
    for position in ("low", "geometric", "high"):
        for alpha in EXPLORATORY_ALPHAS:
            tilted = tilt_wide_joint(
                strengths, snapshot["frames"], snapshot["markets"]["wide"],
                alpha=alpha, odds_position=position
            )
            if tilted["ticket_types"] is None:
                raise ValueError("historical_full_wide_board_unexpected_hold")
            if alpha == 0:
                for kind in KINDS:
                    error = max(abs(p - tilted["ticket_types"][kind][key])
                                for key, p in base[kind].items())
                    if error > 1e-11:
                        raise ValueError(f"alpha_zero_fails_to_reproduce_PL:{kind}")
            results = {}
            for kind in KINDS:
                winners = _actual_selections(top3, snapshot["frames"], kind)
                baseline = score_binary_events(base[kind], winners)
                after = score_binary_events(tilted["ticket_types"][kind], winners)
                results[kind] = {
                    "brier_after_minus_PL": after["brier_mean_per_ticket"] - baseline["brier_mean_per_ticket"],
                    "logloss_after_minus_PL": after["binary_log_loss_mean_per_ticket"] - baseline["binary_log_loss_mean_per_ticket"],
                    "brier_PL": baseline["brier_mean_per_ticket"],
                    "brier_after": after["brier_mean_per_ticket"],
                }
            # Exact top-three log-score is a proper scoring rule for joint finish order.
            triple = tuple(top3)
            results["exact_order_log_loss_delta"] = math.log(
                base["trifecta"][triple] / tilted["ticket_types"]["trifecta"][triple]
            )
            key = f"{position}:alpha={alpha:g}"
            analyses[key] = {
                "kl_posterior_vs_prior_nats": tilted["kl_posterior_vs_prior_nats"],
                "max_abs_pair_log_lift": tilted["max_abs_wide_market_pair_log_lift"],
                "mean_abs_pair_log_lift": tilted["mean_abs_wide_market_pair_log_lift"],
                "scores": results,
            }
    return {
        "race": race_number,
        "runner_count": len(strengths),
        "win_wide_observation_gap_sec": gap,
        "official_top3": top3,
        "snapshot_receipt_jst": snapshot["receipt_as_of"],
        "analyses": analyses,
    }


def run_audit() -> dict:
    source_sha256 = {}
    official = read_json(ROOT / "data" / SOURCE_DATE / "official-results-final.json", source_sha256)
    if official["date"] != SOURCE_DATE or official["status"] != "official_top3_complete_7_to_12":
        raise ValueError("official_results_mismatch")
    races = [audit_one(n, official, source_sha256) for n in TARGET_RACES]
    primary = "geometric:alpha=0.5"
    summary = {}
    for kind in KINDS:
        vals = [r["analyses"][primary]["scores"][kind] for r in races]
        differences = [v["brier_after_minus_PL"] for v in vals]
        summary[kind] = {
            "races": len(vals),
            "mean_delta_brier_after_minus_PL": math.fsum(differences) / len(vals),
            "mean_delta_binary_logloss_after_minus_PL": math.fsum(
                v["logloss_after_minus_PL"] for v in vals
            ) / len(vals),
            "races_tilt_improves_brier": sum(d < -1e-12 for d in differences),
            "races_tilt_harms_brier": sum(d > 1e-12 for d in differences),
            "races_tilt_equal_brier": sum(abs(d) <= 1e-12 for d in differences),
        }
    triple_logloss = [r["analyses"][primary]["scores"]["exact_order_log_loss_delta"] for r in races]
    return {
        "schema_version": 1,
        "status": "RETROSPECTIVE_DEVELOPMENT_NO_PROSPECTIVE_SKILL_CLAIM",
        "data_scope": "2026-10-12 Kyoto 8R-12R, same-day observed win+wide price snapshots",
        "forecast_inputs": ["win_odds", "wide_quotes", "horse_to_frame", "snapshot_timestamps"],
        "result_usage": "scoring only, no learning",
        "market_probabilities_calibrated": False,
        "pre_registered_before_outcome": False,
        "independent_period_validation": False,
        "positive_expected_value_established": False,
        "primary_posthoc_alpha": PRIMARY_ALPHA,
        "design": "joint PL tilt by pair-wise wide price log residual, spread over each top-three triangle",
        "caveat": (
            "Both inputs are market quotes; wide inverse-odds proxy is not an independent or "
            "calibrated probability. A gain is not evidence of market inefficiency or profitable wagers."
        ),
        "primary_equal_race_summary": summary,
        "primary_exact_order_logloss_delta_mean": math.fsum(triple_logloss) / len(triple_logloss),
        "races": races,
        "input_file_sha256": dict(sorted(source_sha256.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Output JSON, default stdout")
    args = parser.parse_args()
    try:
        report = run_audit()
    except (ValueError, KeyError, TypeError, OverflowError, ZeroDivisionError) as exc:
        parser.error(str(exc))
    body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
