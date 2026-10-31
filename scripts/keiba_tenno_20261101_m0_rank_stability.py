#!/usr/bin/env python3
"""Deterministic M0 price-rank fragility: NOT a market-cascade threshold.

Uses ONLY the source-reported 2026-10-31 17:00 single-WIN prices already
sealed as quoted field on the parent Tenno Sho exploratory branch. No next
odds, real vote volumes, wager payouts, race results, or physical GPS.

Counterfactual assumption: every displayed odds o_i is multiplied by
exp(u_i), independently, with |u_i| <= delta. This is a *mathematical
stress envelope*, NOT a fitted forecast/market uncertainty interval.
The exact resulting M0 normalized reciprocal-price index is computed;
pair rank can reverse iff 2*delta >= abs(log(o_i/o_j)). This "rank
crossing" is not a phase transition, a biological tipping point, or
evidence that herding or information arrived.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

from keiba_tenno_20261101_public_market_shadow import (
    _field, RACE, MARKET_SOURCE_REPORTED_CLOCK, SOURCE_ODDS_URL
)

STATUS = "DETERMINISTIC_SINGLE_SNAPSHOT_M0_LOG_PRICE_ENVELOPE_ONLY"
# SHA of the canonical source-declared field: DOES NOT authenticate the
# public source publisher's as-of timestamp or an original vendor file.
PINNED_DECLARED_FIELD_SHA256 = (
    "b8f4b1e617b2582c156c88dece77e440d10a39140feaccf35125d896caf1f479"
)
LOG_ODDS_PERTURBATIONS = (0.0, 0.01, 0.025, 0.05, 0.10)
KEY_HORSES = (1, 7, 3, 17, 11)
TOP_GROUP_SIZES = (1, 2, 3, 5)


def declared_field():
    odds = _field()
    manifest = {
        "race": RACE,
        "market_source_reported_clock": MARKET_SOURCE_REPORTED_CLOCK,
        "market_source_url": SOURCE_ODDS_URL,
        "full_field": [[i, repr(float(odds[i]))] for i in sorted(odds)],
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    if digest != PINNED_DECLARED_FIELD_SHA256:
        raise ValueError("HOLD_PRESTART_DECLARED_FIELD_CHANGED_OR_RENUMBERED")
    return odds, digest


def bounded_index(odds, delta):
    """Exact marginal extrema of q_i = exp(-u_i)/o_i / sum_j exp(-u_j)/o_j."""
    if (not isinstance(delta, (int, float)) or
            not math.isfinite(delta) or delta < 0 or delta > 0.5):
        raise ValueError("HOLD_UNDECLARED_PRICE_SHOCK_BOUNDS")
    if len(odds) != 17 or set(odds) != set(range(1, 18)):
        raise ValueError("HOLD_NOT_THE_SEALED_17_HORSE_FIELD")
    w = {i: 1.0 / odds[i] for i in sorted(odds)}
    total = sum(w.values())
    a, b = math.exp(-delta), math.exp(delta)
    result = {}
    for i in sorted(odds):
        own, others = w[i], total - w[i]
        lo = own*a/(own*a + others*b)
        hi = own*b/(own*b + others*a)
        base = own/total
        if not (0.0 <= lo <= base <= hi <= 1.0):
            raise ValueError("HOLD_M0_ENVELOPE_INVALID")
        result[str(i)] = {
            "M0_at_reported_quote": base,
            "exact_min_if_all_other_quotes_move_oppositely": lo,
            "exact_max_if_all_other_quotes_move_oppositely": hi,
        }
    return result


def pair_robustness(odds, delta):
    """Every pair checked once; <= marks tie *possible*, not observed."""
    ordered = sorted(odds, key=lambda i: (odds[i], i))
    pairs = []
    for i, j in combinations(ordered, 2):
        margin = .5 * abs(math.log(odds[j]/odds[i]))
        if delta >= margin:
            pairs.append({
                "horse_numbers_baseline_order": [i, j],
                "smallest_symmetric_absolute_log_price_shock_for_tie":
                    margin,
            })
    if len(pairs) > 136:
        raise ValueError("HOLD_DUPLICATE_HORSE_PAIR")
    return pairs


def top_group(odds, k, delta):
    """Exact sufficient and necessary strict top-k set rank separation."""
    ordered = sorted(odds, key=lambda i: (odds[i], i))
    if not (1 <= k < len(ordered)):
        raise ValueError("HOLD_INVALID_TOP_GROUP_SIZE")
    inner_worst = odds[ordered[k-1]]
    outer_best = odds[ordered[k]]
    margin = .5*math.log(outer_best/inner_worst)
    return {
        "horse_numbers_baseline_top_k": sorted(ordered[:k]),
        "strict_top_k_set_invariant_for_all_declared_shocks":
            delta < margin,
        "smallest_symmetric_absolute_log_price_shock_for_boundary_tie":
            margin,
    }


def audit():
    odds, digest = declared_field()
    nominal = bounded_index(odds, 0)
    baseline_sorted = sorted(odds, key=lambda i: (odds[i], i))
    ranked_scenarios = []
    for delta in LOG_ODDS_PERTURBATIONS:
        uncertain = pair_robustness(odds, delta)
        bound = bounded_index(odds, delta)
        ranked_scenarios.append({
            "hypothetical_max_abs_log_odds_shock_per_horse": delta,
            "ambiguous_or_reversible_rank_pair_count": len(uncertain),
            "strictly_order_robust_rank_pair_count": 136-len(uncertain),
            "potentially_reversible_or_tied_pairs": uncertain,
            "selected_individual_M0_index_exact_counterfactual_bounds":
                {str(i): bound[str(i)] for i in KEY_HORSES},
            "top_group_set_invariance": {
                str(k): top_group(odds, k, delta) for k in TOP_GROUP_SIZES
            },
        })
    lead = baseline_sorted[0]
    runner_up = baseline_sorted[1]
    if (lead, runner_up) != (7, 1):
        raise ValueError("HOLD_REPORTED_TWO_FAVORITES_CHANGED")
    return {
        "status": STATUS,
        "source_declared_race": RACE,
        "source_reported_at_not_independently_authenticated":
            MARKET_SOURCE_REPORTED_CLOCK,
        "source_publisher_url": SOURCE_ODDS_URL,
        "pinned_source_declared_field_sha256_not_vendor_bytes": digest,
        "horse_count": len(odds),
        "unique_rank_pairs": len(odds)*(len(odds)-1)//2,
        "baseline_M0_leading_two": [
            {"number": i, "source_quoted_single_WIN_odds": odds[i],
             "M0_relative_support_not_true_win_probability":
                 nominal[str(i)]["M0_at_reported_quote"]}
            for i in (lead, runner_up)
        ],
        "two_favorite_comparison": {
            "baseline_leader": lead,
            "baseline_runner_up": runner_up,
            "two_sided_symmetric_log_price_shock_for_tie":
                .5*math.log(odds[runner_up]/odds[lead]),
            "if_only_leader_odds_rise_required_multiplier_for_tie":
                odds[runner_up]/odds[lead],
            "if_only_runner_up_odds_fall_required_multiplier_for_tie":
                odds[lead]/odds[runner_up],
        },
        "hypothetical_shock_scenarios": ranked_scenarios,
        "shock_is_counterfactual_not_observed_time_series": True,
        "price_rank_crossing_is_NOT_dynamic_market_tipping": True,
        "only_one_source_reported_WIN_quote_timestamp": True,
        "real_bettor_volume_herding_and_information_timing_unobserved": True,
        "real_asof_authenticated_source_receipt_count": 0,
        "official_target_race_results_used": False,
        "independent_future_quote_for_scoring_available": False,
        "this_does_not_modify_parent_prestart_forecast_or_formal_v31_ledger":
            True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path,
                   default=Path("tmp/tenno-20261101-m0-price-rank-envelope.json"))
    args = p.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print("DECLARED_SOURCE_FIELD_SHA256",
          result["pinned_source_declared_field_sha256_not_vendor_bytes"])
    print("TWO_FAVORITE_LOG_SHOCK_TIE",
          result["two_favorite_comparison"][
              "two_sided_symmetric_log_price_shock_for_tie"])
    for scenario in result["hypothetical_shock_scenarios"]:
        print("HYPOTHETICAL_DELTA_PAIR_FRAGILITY",
              scenario["hypothetical_max_abs_log_odds_shock_per_horse"],
              scenario["ambiguous_or_reversible_rank_pair_count"],
              "TOP2_STABLE",
              scenario["top_group_set_invariance"]["2"][
                  "strict_top_k_set_invariant_for_all_declared_shocks"])
    print("NO_REAL_Q2_AND_NO_DYNAMIC_TIPPING_INFERENCE", True)


if __name__ == "__main__":
    main()
