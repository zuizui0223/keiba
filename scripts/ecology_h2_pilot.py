#!/usr/bin/env python3
"""H2 exploratory competition-context interaction: mixed-model software pilot.

Compares a baseline horse-level random-intercept model to a model adding
own historical running style × OTHER entrants' historical front-running share.
All predictors use strictly earlier calendar days. Race-relative outcome is
post-race descriptive, never an individual fitness measure or betting input.

This is not a causal estimator or a confirmatory ecological test.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_h1_pilot import (
    conditional_predict, fit_with_fallback, relative_performance,
    score, split_dates,
)
from ecology_panel import audit, lagged_features, load_panel


FEATURES = (
    "prior_front_runner_score", "other_front_runner_share",
    "prior_strength_score", "other_prior_strength_mean",
)
BASE_FORMULA = "y ~ own_ability_c + other_ability_c + front_c + opponent_c"
INTERACTION_FORMULA = BASE_FORMULA + " + front_c:opponent_c"


def competition_frame(enriched: list[dict], surface="turf") -> pd.DataFrame:
    outcome = relative_performance(enriched)
    if outcome.empty:
        raise ValueError("no race-complete individual time outcomes")
    feature_rows = [
        {"race_id": row["race_id"], "horse_id": row["horse_id"],
         **{key: row[key] for key in FEATURES}}
        for row in enriched
    ]
    features = pd.DataFrame(feature_rows)
    frame = outcome.merge(features, how="left",
                          on=["race_id", "horse_id"], validate="one_to_one")
    frame = frame[frame["surface"] == surface].copy()
    if frame.empty:
        raise ValueError("no matching surface")
    # Strict: discard entire races unless every horse has a previously measured
    # style and both own/rival strength. Avoid distorted within-race contrasts.
    total = frame.groupby("race_id").size()
    complete = frame.dropna(subset=list(FEATURES)).groupby("race_id").size()
    valid_races = set(complete[complete == total.reindex(complete.index)].index)
    frame = frame.loc[frame["race_id"].isin(valid_races)].copy()
    if frame.empty:
        raise ValueError("H2 HOLD: no races with full pre-race historical coverage")
    # The response is measured in a postrace race-relative way and will never
    # enter predictor histories for the same or earlier race.
    frame["y"] = frame["y"] - frame.groupby("race_id")["y"].transform("mean")
    frame["poor"] = frame["poor"].astype(int)
    return frame.sort_values(["date","race_id","horse_id"]).reset_index(drop=True)


def horse_context_support(frame: pd.DataFrame, min_starts: int = 4) -> int:
    contexts = frame.groupby("horse_id")["other_front_runner_share"]
    eligible = 0
    for _, values in contexts:
        if len(values) >= min_starts and values.round(6).nunique() >= 2:
            eligible += 1
    return eligible


def freeze_scaling(train: pd.DataFrame, test: pd.DataFrame):
    """Center ALL explanatory variables using only training-date means."""
    dictionary = {
        "front_c": "prior_front_runner_score",
        "opponent_c": "other_front_runner_share",
        "own_ability_c": "prior_strength_score",
        "other_ability_c": "other_prior_strength_mean",
    }
    frozen_means = {new: float(train[old].mean())
                    for new, old in dictionary.items()}
    outputs = []
    for df in (train, test):
        result = df.copy()
        for name, original in dictionary.items():
            result[name] = result[original].astype(float) - frozen_means[name]
        outputs.append(result)
    return outputs[0], outputs[1], frozen_means


def run(path: Path, surface: str="turf", permit_synthetic_demo: bool=False,
        test_fraction: float=0.2) -> dict:
    rows = load_panel(path)
    rights = {r["source_license"] for r in rows}
    only_synthetic = rights == {"synthetic"}
    if "synthetic" in rights and not only_synthetic:
        raise ValueError("mixed fabricated/real source records are forbidden")
    if only_synthetic and not permit_synthetic_demo:
        raise ValueError("synthetic-only panel: supply --permit-synthetic-demo to run a software demo")
    if permit_synthetic_demo and not only_synthetic:
        raise ValueError("--permit-synthetic-demo refuses all actual historical data")
    if rights.intersection({"unknown", "uncleared", "restricted"}):
        raise ValueError("H2 HOLD: unreviewed or restricted source permissions")
    enriched = lagged_features(rows)
    diag = audit(rows, enriched)
    frame = competition_frame(enriched, surface)
    train, test, start_date = split_dates(frame, test_fraction)
    support = horse_context_support(train)
    threshold = 8 if only_synthetic else 30
    if support < threshold:
        raise ValueError(
            f"H2 HOLD: insufficient within-horse changes in competitor composition "
            f"({support} training horses; need {threshold})"
        )
    if train["race_id"].nunique() < 20 or test["race_id"].nunique() < 4:
        raise ValueError("H2 HOLD: <20 training races or <4 future test races")
    if train["other_front_runner_share"].std() < 1e-8:
        raise ValueError("H2 HOLD: opponent-context variation is zero")
    train, test, means = freeze_scaling(train, test)
    m0, method0 = fit_with_fallback(train, "1", BASE_FORMULA)
    m1, method1 = fit_with_fallback(train, "1", INTERACTION_FORMULA)
    p0 = conditional_predict(m0, test, include_slope=False)
    p1 = conditional_predict(m1, test, include_slope=False)
    metrics = score(test, p0, p1, bootstrap=500, seed=20261012)
    interaction_beta = float(m1.fe_params["front_c:opponent_c"])
    return {
        "status": ("SYNTHETIC_H2_SMOKE_ONLY" if only_synthetic
                   else "EXPLORATORY_H2_PILOT_NOT_HYPOTHESIS_SUPPORT"),
        "data_provenance": {
            "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "licenses_observed": sorted(rights),
            "source_rights_independently_verified": False,
            "pre_race_features": "strict prior calendar dates only",
        },
        "surface": surface,
        "h2_overlap": {
            "all_panel_horses_with_context_variation":
                diag["h2_horses_with_4plus_races_and_2plus_distinct_opponent_style_contexts"],
            "training_horses_with_4plus_distinct_context_exposures": support,
            "train_horse_count": int(train["horse_id"].nunique()),
            "train_races": int(train["race_id"].nunique()),
            "future_test_races": int(test["race_id"].nunique()),
            "train_max_date": str(train["date"].max()),
            "test_start_date": str(start_date),
            "test_max_date": str(test["date"].max()),
            "complete_history_coverage_required_per_race": True,
        },
        "preprocessing": {
            "training_only_feature_centering": means,
            "leave_one_out_opponents": True,
            "postrace_target_is_race_relative_z_speed": True,
        },
        "m0": {
            "formula": BASE_FORMULA, "horse_effect": "random intercept",
            "converged": bool(m0.converged), "optimizer": method0,
            "loglik": float(m0.llf),
        },
        "m1": {
            "formula": INTERACTION_FORMULA, "horse_effect": "random intercept",
            "converged": bool(m1.converged), "optimizer": method1,
            "loglik": float(m1.llf),
            "style_by_opponent_context_beta_point_estimate": interaction_beta,
            "beta_valid_clustered_ci_or_causal_pvalue": False,
        },
        "forward_test": metrics,
        "limitations": [
            "Beta is descriptive only; race+horse crossed dependence and selection are not fully identified.",
            "No robust beta CI, causal p-value, randomization or competition mechanism is identified.",
            "Outcome is normalized within race, so effects concern relative competition performance.",
            "Race roster and finishing times must be complete: selection bias remains.",
            "Even if synthetic data recover the planted parameter, this is no evidence for horse ecology.",
            "Race-block bootstrap of held-out prediction is not a causal effect CI.",
            "Past results inform future predictors only; the held-out period is not an untouched external dataset.",
            "Competitor share computed leave-one-out is mechanically dependent on focal style for finite fields.",
        ],
    }


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--surface", choices=["turf","dirt"],default="turf")
    p.add_argument("--permit-synthetic-demo",action="store_true")
    p.add_argument("--test-fraction",type=float,default=0.2)
    args=p.parse_args()
    result=run(args.input,args.surface,args.permit_synthetic_demo,args.test_fraction)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
                      "training_horses_with_repeated_contexts":
                          result["h2_overlap"]["training_horses_with_4plus_distinct_context_exposures"],
                      "style_context_interaction_beta":
                          result["m1"]["style_by_opponent_context_beta_point_estimate"],
                      "heldout_delta_RMSE":
                          result["forward_test"]["m0_minus_m1_rmse_positive_means_m1_better"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
