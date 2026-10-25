#!/usr/bin/env python3
"""Monte Carlo seed-sensitivity of one already-fixed coupled toy mechanism.

Repeated seeds are NOT new independent JRA races or validation samples.
The same six results are reused; no fitted parameters or threshold selection.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean

from keiba_coupled_horse_market_pde import audit

STATUS = "REPEATED_SYNTHETIC_SEEDS_SAME_SIX_RACES_NOT_PROSPECTIVE_VALIDATION"


def sensitivity(*, n_seeds=7, draws=120, first_seed=20261025):
    if n_seeds < 2 or draws < 40:
        raise ValueError("HOLD_TOO_FEW_SYNTHETIC_SEEDS_OR_DRAWS")
    recorded = []
    for j in range(n_seeds):
        seed = first_seed + 1009*j
        report = audit(draws=draws, seed=seed)
        scores = report["postrace"]["mean_race_equal_winner_log_loss"]
        places = report["postrace"]["mean_race_equal_Top3_brier"]
        tv = report["market_abm"]["mean_TV_to_actual_later_quote_pp"]
        recorded.append({
            "seed": seed,
            "threshold_minus_observed_M0_win_LL":
                scores["market_threshold_mixed"] - scores["observed_M0"],
            "information_minus_observed_M0_win_LL":
                scores["market_information"] - scores["observed_M0"],
            "mixed_minus_observed_M0_win_LL":
                scores["market_mixed"] - scores["observed_M0"],
            "threshold_minus_observed_M0_Top3_brier":
                places["market_threshold_mixed"] - places["observed_M0"],
            "threshold_market_TV_to_observed_latest_pp": tv["threshold_mixed"],
            "independent_market_TV_to_observed_latest_pp": tv["independent"],
            "triggered_threshold_steps": report["market_abm"][
                "threshold_triggered_steps_sum"],
        })
    fields = [k for k in recorded[0] if k != "seed"]
    summary = {name: {
        "mean": mean(row[name] for row in recorded),
        "min": min(row[name] for row in recorded),
        "max": max(row[name] for row in recorded),
    } for name in fields}
    return {
        "status": STATUS,
        "real_independent_races": 6,
        "real_meeting_dates": 2,
        "synthetic_seed_repetitions_not_new_independent_trials": n_seeds,
        "draws_per_race_per_horse_model": draws,
        "hypothetical_parameters_unchanged_across_seeds": True,
        "any_score_advantage_is_retrospective_and_unvalidated": True,
        "range_across_synthetic_seeds": summary,
        "threshold_lower_win_loss_than_market_in_n_seed_trials": sum(
            r["threshold_minus_observed_M0_win_LL"] < 0 for r in recorded),
        "seeds": [r["seed"] for r in recorded],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=7)
    parser.add_argument("--draws", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--output", type=Path,
                        default=Path("tmp/coupled-seed-sensitivity.json"))
    args = parser.parse_args()
    result = sensitivity(n_seeds=args.seeds, draws=args.draws,
                         first_seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)
                           + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
          "winner_logloss_delta_range": result["range_across_synthetic_seeds"][
              "threshold_minus_observed_M0_win_LL"],
          "seed_trials_better": result[
              "threshold_lower_win_loss_than_market_in_n_seed_trials"],
          "seeds": args.seeds}, ensure_ascii=False))


if __name__ == "__main__":
    main()
