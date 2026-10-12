#!/usr/bin/env python3
"""H2 within-individual falsification pilot: rival context versus assortment.

RESEARCH SOFTWARE ONLY. Not a causal social plasticity estimate, not a
horse-racing forecast, and not empirical evidence without an authorized
multi-year horse×race panel. All comparison features are pre-race history.

Design: horse fixed intercepts + strictly within-horse changes in
opponent composition, while a horse's style trait is frozen from TRAINING
records. Standard errors are clustered on horse and race for an
*approximate descriptive interval*, not a valid causal p-value.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from ecology_h1_pilot import score, split_dates
from ecology_h2_pilot import competition_frame, horse_context_support
from ecology_panel import audit, lagged_features, load_panel

BASE_FEATURES = (
    "prior_strength_score",
    "other_prior_strength_mean",
    "prior_front_runner_score",
)

def check_rights(rows: list[dict], synthetic_demo: bool) -> bool:
    licenses = {r["source_license"] for r in rows}
    synthetic = licenses == {"synthetic"}
    if "synthetic" in licenses and not synthetic:
        raise ValueError("HOLD_MIXED_SYNTHETIC_AND_REAL")
    if any(v in licenses for v in ("unknown", "uncleared", "restricted")):
        raise ValueError("HOLD_RIGHTS: source permission not demonstrated")
    if synthetic and not synthetic_demo:
        raise ValueError("synthetic panel may only run with --permit-synthetic-demo")
    if synthetic_demo and not synthetic:
        raise ValueError("--permit-synthetic-demo refuses any non-synthetic source")
    return synthetic


def add_total_field_fraction(frame: pd.DataFrame, threshold: float = 0.7) -> pd.DataFrame:
    """Sensitivity: full-field share, not leave-one-out share.

    Only valid because competition_frame requires every entrant's prior
    style to be nonmissing (there are complete rosters).
    """
    result = frame.copy()
    n = result.groupby("race_id")["horse_id"].transform("size").astype(float)
    own_front = (result["prior_front_runner_score"] >= threshold).astype(float)
    result["total_front_runner_share"] = (
        result["other_front_runner_share"] * (n - 1) + own_front
    ) / n
    return result


def construct_context(
    train: pd.DataFrame, test: pd.DataFrame,
    exposure: str = "other_front_runner_share",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Fit all individual mean components on earlier training dates only."""
    if exposure not in ("other_front_runner_share", "total_front_runner_share"):
        raise ValueError("unknown context exposure")
    if train[exposure].isna().any() or test[exposure].isna().any():
        raise ValueError("missing context values")
    style_mean = train.groupby("horse_id")["prior_front_runner_score"].mean()
    context_mean = train.groupby("horse_id")[exposure].mean()
    style_grand = float(train["prior_front_runner_score"].mean())
    context_grand = float(train[exposure].mean())
    if not np.isfinite([style_grand, context_grand]).all():
        raise ValueError("nonfinite prior means")
    offsets = {
        column: float(train[column].mean()) for column in BASE_FEATURES
    }
    prepared = []
    for orig in (train, test):
        frame = orig.copy()
        horse_context = frame["horse_id"].map(context_mean).fillna(context_grand)
        horse_style = frame["horse_id"].map(style_mean).fillna(style_grand)
        # Individual social environment mean: BETWEEN animals; absorbed by
        # horse fixed effects. The deviation is a WITHIN-animal comparison.
        frame["context_within"] = frame[exposure] - horse_context
        frame["context_between"] = horse_context - context_grand
        frame["horse_style_trait"] = horse_style - style_grand
        frame["style_x_context_within"] = (
            frame["horse_style_trait"] * frame["context_within"]
        )
        # Rival composition may covary with going. Without this control,
        # a horse-style × ground-response effect (H1) could look like H2.
        frame["style_x_poor_going"] = frame["horse_style_trait"] * frame["poor"]
        for col in BASE_FEATURES:
            frame["c_" + col] = frame[col] - offsets[col]
        prepared.append(frame)
    meta = {
        "exposure": exposure,
        "style_trait": "horse mean of earlier style scores, TRAIN ONLY",
        "within_component": "opponent_share - horse's TRAINING exposure mean",
        "between_component": "horse's TRAINING exposure mean - training grand mean",
        "style_grand_training": style_grand,
        "context_grand_training": context_grand,
        "feature_centers_training_only": offsets,
        "training_horse_means_frozen_for_future": True,
        "unseen_horse_uses_training_grand_mean": True,
    }
    return prepared[0], prepared[1], meta


def build_matrix(
    training: pd.DataFrame, testing: pd.DataFrame, interaction: bool,
) -> tuple[np.ndarray, np.ndarray, list[str], int]:
    """Horse fixed effects; unseen horse IDs receive no learned horse effect."""
    numeric = [
        "c_prior_strength_score", "c_other_prior_strength_mean",
        "c_prior_front_runner_score", "context_within",
        "poor", "style_x_poor_going",
    ]
    if interaction:
        numeric.append("style_x_context_within")
    ids = sorted(training["horse_id"].unique().tolist())
    lookup = {v: i for i, v in enumerate(ids)}
    if not ids:
        raise ValueError("no training horses")
    def make(d):
        num = d[numeric].to_numpy(dtype=float)
        horse = np.zeros((len(d), len(ids)), dtype=float)
        for ix, val in enumerate(d["horse_id"]):
            if val in lookup:
                horse[ix, lookup[val]] = 1.0
        mat = np.column_stack([num, horse])
        if not np.isfinite(mat).all():
            raise ValueError("nonfinite model matrix")
        return mat
    return (make(training), make(testing),
            numeric + [f"horse_fixed:{x}" for x in ids],
            int((~testing["horse_id"].isin(ids)).sum()))


def _race_center_predict(raw: np.ndarray, test: pd.DataFrame) -> np.ndarray:
    frame = pd.DataFrame({"race_id": test["race_id"].to_numpy(),
                          "p": np.asarray(raw, dtype=float)})
    if not np.isfinite(frame["p"]).all():
        raise ValueError("nonfinite prediction")
    return (frame["p"] - frame.groupby("race_id")["p"].transform("mean")).to_numpy()


def _fit_ols(
    train: pd.DataFrame, test: pd.DataFrame, interaction: bool,
) -> tuple[dict, np.ndarray]:
    x_train, x_test, names, unseen = build_matrix(train, test, interaction)
    # Explicit horse intercepts so the rival-context coefficient is informed
    # by repeated within-horse contrasts, not just between-horse selection.
    if np.linalg.matrix_rank(x_train) < x_train.shape[1]:
        raise ValueError("HOLD_RANK_DEFICIENT: predictors/horse contrasts not identifiable")
    ols = sm.OLS(train["y"].to_numpy(dtype=float), x_train).fit()
    pred = _race_center_predict(x_test @ ols.params, test)
    result = {
        "formula": "y ~ previous ability + opponent previous ability + recent style "
                   "+ within-horse opponent context + horse fixed intercepts "
                   "+ poor going + frozen horse style × poor going"
                   + (" + frozen horse style × within context" if interaction else ""),
        "training_ols_r_squared": float(ols.rsquared),
        "unseen_test_horse_start_rows": unseen,
        "train_parameters": len(names),
        "within_horse_context_use": True,
        "ground_by_style_competing_interaction_controlled": True,
    }
    if interaction:
        index = names.index("style_x_context_within")
        result["interaction_beta_descriptive"] = float(ols.params[index])
        # Two-way cluster-robust covariance (horse and race). Standard error
        # is approximate and cannot correct for nonrandom competitive entry.
        groups = np.column_stack([
            pd.factorize(train["horse_id"])[0],
            pd.factorize(train["race_id"])[0],
        ])
        robust = ols.get_robustcov_results(
            cov_type="cluster", groups=groups, use_t=False,
        )
        se = float(robust.bse[index])
        if not np.isfinite(se) or se <= 0:
            raise ValueError("HOLD_TWO_WAY_COVARIANCE_NOT_ESTIMABLE")
        estimate = float(ols.params[index])
        result["two_way_horse_race_cluster_nominal_se"] = se
        result["two_way_cluster_nominal_95pct_interval"] = [
            estimate - 1.96*se, estimate + 1.96*se
        ]
        result["ci_is_causal_or_confirmatory"] = False
        result["multiway_cluster_note"] = (
            "Descriptive approximation conditional on selection/model; "
            "not a causal social-plasticity interval or a multiple-testing correction."
        )
    return result, pred


def _assortment(train: pd.DataFrame, min_starts=4) -> dict:
    grouped = train.groupby("horse_id").agg(
        n=("race_id","size"),
        style=("prior_front_runner_score","mean"),
        context=("other_front_runner_share","mean"),
    )
    good = grouped[grouped["n"] >= min_starts]
    if len(good) < 3:
        return {"horses": len(good), "style_context_mean_correlation": None}
    x = good["style"].to_numpy()
    y = good["context"].to_numpy()
    if np.std(x) <= 1e-12 or np.std(y) <= 1e-12:
        corr = None
    else:
        corr = float(np.corrcoef(x, y)[0,1])
    return {
        "horses": len(good),
        "style_context_mean_correlation": corr,
        "interpretation": (
            "Descriptive between-horse association; not proof that horses "
            "select their rivals or that rivals cause a response."
        )
    }


def run(
    path: Path, surface="turf", permit_synthetic_demo=False, test_fraction=0.2,
    threshold: float=0.7,
) -> dict:
    if threshold != 0.7:
        # The historical feature builder currently hardcodes 0.7. A different
        # threshold needs regeneration, not relabelling a saved feature.
        raise ValueError("current pilot supports front threshold 0.7 only")
    rows = load_panel(path)
    synthetic = check_rights(rows, permit_synthetic_demo)
    enriched = lagged_features(rows)
    diag = audit(rows, enriched)
    if not synthetic and diag["status"] != "DESIGN_READY_NOT_EVIDENCE":
        raise ValueError("HOLD_AUDIT: " + diag["status"])
    frame = add_total_field_fraction(competition_frame(enriched, surface), threshold)
    train0, test0, start = split_dates(frame, test_fraction)
    if train0["race_id"].nunique() < 20 or test0["race_id"].nunique() < 4:
        raise ValueError("HOLD_TOO_FEW_TRAIN_OR_TEST_RACES")
    support = horse_context_support(train0)
    if support < (8 if synthetic else 30):
        raise ValueError("HOLD_INSUFFICIENT_WITHIN_HORSE_RIVAL_TURNOVER")
    if train0["prior_front_runner_score"].std() < 1e-8:
        raise ValueError("HOLD_NO_STYLE_VARIANCE")
    variants = {}
    for exposure, key in (
        ("other_front_runner_share","leave_one_out_other_horses"),
        ("total_front_runner_share","full_race_field"),
    ):
        train, test, transform = construct_context(train0, test0, exposure)
        if train["context_within"].std() < 1e-7:
            raise ValueError(f"HOLD_NO_INDIVIDUAL_CONTEXT_VARIATION:{exposure}")
        model0, p0 = _fit_ols(train, test, interaction=False)
        model1, p1 = _fit_ols(train, test, interaction=True)
        metrics = score(test, p0, p1, bootstrap=500, seed=20261012)
        variants[key] = {
            "preprocessing": transform,
            "baseline": model0, "interaction": model1,
            "forward_test": metrics,
        }
    signs = [np.sign(v["interaction"]["interaction_beta_descriptive"])
             for v in variants.values()]
    return {
        "status": ("SYNTHETIC_H2_WITHIN_HORSE_DEMO_ONLY" if synthetic
                   else "EXPLORATORY_H2_SENSITIVITY_NOT_ECOLOGICAL_SUPPORT"),
        "hypothesis": "social plasticity vs nonrandom social assortment",
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "surface": surface,
        "source_license_status": "synthetic" if synthetic else "not independently verified",
        "strict_pre_race_predictors": True,
        "data_support": {
            "training_horses_with_repeated_rival_contexts": support,
            "train_races": int(train0["race_id"].nunique()),
            "future_test_races": int(test0["race_id"].nunique()),
            "train_date_max": str(train0["date"].max()),
            "test_date_min": str(start),
            "focal_and_rival_style_profiles_historical_only": True,
        },
        "descriptive_between_horse_assortment": _assortment(train0),
        "context_definitions": variants,
        "leave_one_out_vs_full_field_beta_sign_agreement": (
            bool(signs[0] == signs[1]) if all(v != 0 for v in signs) else None
        ),
        "not_inferred": [
            "H2 supported/rejected on any real racehorse cohort",
            "Causal social plasticity or experimental competition effect",
            "Evolutionary or ecological fitness and genetic adaptation",
            "Licensed data usage rights based on a CSV text label",
            "Validated population generalization, horse welfare or wager returns",
        ],
        "confounding_and_limitations": [
            "Horse fixed effects remove time-invariant horse differences but not "
            "time-varying selective entry, jockey assignments, class, tactics or fitness.",
            "Binary going and horse-style×going are included as competing explanations; "
            "complex race-day weather, surface and venue interactions remain unadjusted.",
            "Compositional share of rivals and focal style are mathematically coupled; "
            "full-field exposure sensitivity probes but does not eliminate the coupling.",
            "Two-way cluster uncertainty approximates race and horse dependence; "
            "it cannot by itself justify causal or confirmatory inference.",
            "The reference racing day has just one race in the synthetic generator; "
            "held-out prediction is not preregistered external ecological validation.",
            "Individual speed has been standardized within each race, so estimand "
            "describes conditional relative performance rather than absolute pace.",
            "Between-horse mean context correlation is only descriptive assortment.",
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--surface",choices=("turf","dirt"),default="turf")
    p.add_argument("--permit-synthetic-demo",action="store_true")
    p.add_argument("--test-fraction",type=float,default=0.2)
    args=p.parse_args()
    out=run(args.input,args.surface,args.permit_synthetic_demo,args.test_fraction)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "support":out["data_support"]["training_horses_with_repeated_rival_contexts"],
        "loo_beta":out["context_definitions"]["leave_one_out_other_horses"]["interaction"]["interaction_beta_descriptive"],
        "all_beta":out["context_definitions"]["full_race_field"]["interaction"]["interaction_beta_descriptive"],
    },ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
