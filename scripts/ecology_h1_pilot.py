#!/usr/bin/env python3
"""H1 *pilot* random regression for individual conditional performance.

Uses race-centred individual speed and forward-in-time evaluation, never odds.
Random-slope variance is exploratory; selection bias, jockey and race covariance
require a confirmatory model before any ecological claim. No betting suggestions.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from ecology_panel import audit, lagged_features, load_panel


def relative_performance(rows: list[dict]) -> pd.DataFrame:
    """Create normalized speed contrasts only for complete, timed race rosters."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["race_id"]].append(row)
    records = []
    for group in grouped.values():
        if len(group) < 4 or len(group) != group[0]["field_size"]:
            continue
        if any(r["finish_status"] != "finished" or r["finish_time_s"] is None for r in group):
            continue
        speeds = np.array([r["course_distance_m"] / r["finish_time_s"] for r in group])
        sd = float(np.std(speeds, ddof=0))
        if sd <= 0.01:
            continue
        for row, speed in zip(group, speeds):
            prior = row["prior_strength_score"]
            records.append({
                "horse_id": row["horse_id"], "race_id": row["race_id"],
                "date": row["race_date_jst"], "venue": row["venue"],
                "surface": row["course_surface"],
                "distance_m": row["course_distance_m"],
                "poor": int(row["track_going"] != "良"),
                "prior_strength": float(prior) if prior is not None else np.nan,
                "y": float((speed - speeds.mean()) / sd),
            })
    return pd.DataFrame(records)


def split_dates(df: pd.DataFrame, test_fraction: float = 0.2):
    if not 0 < test_fraction < 0.5:
        raise ValueError("test_fraction must lie in (0,0.5)")
    dates = sorted(df["date"].unique())
    if len(dates) < 8:
        raise ValueError("need >=8 distinct racing dates for forward test")
    cutoff = max(1, min(len(dates) - 1, int(len(dates) * (1 - test_fraction))))
    training = df.loc[df["date"].isin(dates[:cutoff])].copy()
    testing = df.loc[df["date"].isin(dates[cutoff:])].copy()
    if training.empty or testing.empty or training["date"].max() >= testing["date"].min():
        raise ValueError("temporal split failure")
    return training, testing, dates[cutoff]


def horse_exposure_support(frame: pd.DataFrame) -> int:
    grouped = frame.groupby(["horse_id", "poor"]).size().unstack(fill_value=0)
    for key in (0, 1):
        if key not in grouped.columns:
            grouped[key] = 0
    return int(((grouped[0] >= 2) & (grouped[1] >= 2)).sum())


def fit_with_fallback(frame: pd.DataFrame, random_formula: str):
    model = smf.mixedlm(
        "y ~ prior_strength + poor", data=frame,
        groups=frame["horse_id"], re_formula=random_formula
    )
    errors = []
    for method in ("lbfgs", "bfgs", "powell"):
        try:
            result = model.fit(reml=False, method=method, maxiter=1200, disp=False)
            if result.converged and np.isfinite(result.llf):
                return result, method
            errors.append(f"{method}: did not converge")
        except (ValueError, np.linalg.LinAlgError, IndexError) as exc:
            errors.append(f"{method}: {type(exc).__name__}")
    raise RuntimeError("mixed model not converged: " + "; ".join(errors))


def conditional_predict(result, frame: pd.DataFrame, include_slope: bool) -> np.ndarray:
    fixed = np.asarray(result.predict(frame), dtype=float)
    random_effects = result.random_effects
    values = []
    for base, (_, row) in zip(fixed, frame.iterrows()):
        coefficients = random_effects.get(row["horse_id"])
        if coefficients is None:
            values.append(base)
        else:
            a = np.asarray(coefficients, dtype=float)
            values.append(base + a[0] + (a[1] * row["poor"] if include_slope else 0.0))
    temp = frame[["race_id"]].copy()
    temp["prediction"] = values
    # Only known entrant roster is needed for the predicted relative-race centering.
    return (temp["prediction"] - temp.groupby("race_id")["prediction"].transform("mean")).to_numpy()


def score(frame: pd.DataFrame, pred0: np.ndarray, pred1: np.ndarray, bootstrap=500, seed=20261012):
    """Evaluate paired improvements by held-out *race*, not random horse rows."""
    tmp = frame[["race_id", "horse_id", "poor", "y"]].copy()
    tmp["se0"] = (tmp["y"] - pred0) ** 2
    tmp["se1"] = (tmp["y"] - pred1) ** 2
    sums = tmp.groupby("race_id")[["se0", "se1"]].mean()
    if len(sums) < 2:
        raise ValueError("need >=2 heldout races")
    # Race-level MAE/RMSE avoid pseudo-replication when many horses run together.
    rmse0 = float(np.sqrt(tmp["se0"].mean()))
    rmse1 = float(np.sqrt(tmp["se1"].mean()))
    sampled = sums.to_numpy()
    rng = random.Random(seed)
    delta = []
    for _ in range(bootstrap):
        ix = [rng.randrange(len(sampled)) for _ in range(len(sampled))]
        subset = sampled[ix, :]
        delta.append(float(np.sqrt(subset[:, 0].mean()) - np.sqrt(subset[:, 1].mean())))
    ci = np.quantile(delta, [0.025, 0.975]).tolist()
    return {
        "m0_rmse_race_relative_speed_z": rmse0,
        "m1_rmse_race_relative_speed_z": rmse1,
        "m0_minus_m1_rmse_positive_means_m1_better": rmse0 - rmse1,
        "race_block_bootstrap_95pct_interval": ci,
        "test_race_count": int(len(sums)), "test_horse_starts": int(len(tmp)),
        "bootstrap_repetitions": bootstrap,
        "interpretation": "Descriptive held-out predictive comparison only; not causal identification or formal random-slope test.",
    }


def run(path: Path, surface: str, permit_synthetic_demo=False, test_fraction=0.2):
    rows = load_panel(path)
    diag = audit(rows, lagged_features(rows))
    rights = set(r["source_license"] for r in rows)
    only_synthetic = rights == {"synthetic"}
    if permit_synthetic_demo and not only_synthetic:
        raise ValueError("--permit-synthetic-demo is ONLY for wholly synthetic, fabricated panels")
    if only_synthetic and not permit_synthetic_demo:
        raise ValueError("synthetic data are disallowed without explicit demo mode")
    if not only_synthetic and diag["status"] != "DESIGN_READY_NOT_EVIDENCE":
        raise ValueError("readiness/rights gate failed: " + diag["status"])
    enriched = lagged_features(rows)
    frame = relative_performance(enriched)
    if frame.empty:
        raise ValueError("no complete races with individual finish times")
    frame = frame.loc[frame["surface"] == surface].copy()
    frame = frame.dropna(subset=["prior_strength"])
    if frame.empty:
        raise ValueError("no suitable surface-specific, historical-feature rows")
    # This is a *pilot*: course, class, jockey, nonrandom entry and covariance
    # within races are NOT jointly adjusted. Do not interpret as confirmatory.
    train, test, test_start = split_dates(frame, test_fraction)
    support = horse_exposure_support(train)
    required = 4 if only_synthetic else 30
    if support < required:
        raise ValueError(f"training horses with >=2 starts in each going group: {support} < {required}")
    m0, opt0 = fit_with_fallback(train, "1")
    m1, opt1 = fit_with_fallback(train, "1+poor")
    pr0 = conditional_predict(m0, test, include_slope=False)
    pr1 = conditional_predict(m1, test, include_slope=True)
    metrics = score(test, pr0, pr1)
    return {
        "status": "SYNTHETIC_SMOKE_ONLY" if only_synthetic else "EXPLORATORY_PILOT_NOT_HYPOTHESIS_SUPPORT",
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "surface": surface, "predictor_cutoff_rule": "prior_calendar_days_only",
        "split": {"train_max_date": str(train["date"].max()), "test_start_date": str(test_start),
                  "test_max_date": str(test["date"].max()), "train_rows": len(train),
                  "test_rows": len(test), "train_cross_going_horses": support},
        "m0": {"random": "horse intercept", "converged": bool(m0.converged), "optimizer": opt0, "loglik": float(m0.llf)},
        "m1": {"random": "horse intercept + going slope", "converged": bool(m1.converged),
               "optimizer": opt1, "loglik": float(m1.llf),
               "among_horse_slope_sd_point_estimate": float(np.sqrt(max(0, m1.cov_re.iloc[1, 1]))),
               "slope_uncertainty_estimated": False},
        "forward_test": metrics,
        "limitations": [
            "Race-centred z-speed is a relative, observational performance proxy and shares race-level dependence.",
            "Non-finishers and races without full time coverage are excluded: selection bias remains.",
            "This simple pilot lacks confirmatory class/jockey/age, nonrandom entry and clustered uncertainty modelling.",
            "Random-slope variance estimate has no valid confidence interval or boundary-aware test here.",
            "Chronological evaluation includes historical prior results known before each held-out start.",
            "Never report H1 supported/unsupported based solely on this pilot; preregister confirmatory analyses.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--surface", choices=["turf", "dirt"], required=True)
    parser.add_argument("--permit-synthetic-demo", action="store_true")
    parser.add_argument("--test-fraction", type=float, default=0.2)
    args = parser.parse_args()
    result = run(args.input, args.surface, args.permit_synthetic_demo, args.test_fraction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "surface": result["surface"],
                      "heldout_rmse": result["forward_test"]["m1_rmse_race_relative_speed_z"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
