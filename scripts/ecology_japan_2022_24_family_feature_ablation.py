#!/usr/bin/env python3
"""Post-hoc 2022–24 ablation of shrunk family performance and explicit counts.

All four ridge fits use the original pre-target historical features. Only
anonymous cohort totals, scores, paired loss differences and intervals leave
the runner. Positive differences mean lower squared prediction loss.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from ecology_japan_archive_forward import SOURCE_SHA, clean_id
from ecology_japan_2022_parent_placebo import SQLITE_SHA, load_sources
from ecology_japan_2022_independent_forward import (
    RIDGE_ALPHA, _scores, fit_weighted_ridge, make_common_features, predict_weighted_ridge,
)
from ecology_japan_2022_joint_strict_strong import (
    ALL_STRONG_KIN, ALL_STRONG_NO_KIN, STRICT_HORSES, STRICT_ROWS, strict_mask_exact_horse_race,
)
from ecology_japan_2022_strong_portable_baseline import (
    STRONG_KIN, STRONG_NO_KIN, extra_features, old_metadata,
)
from ecology_japan_2022_2024_kin_information_moderators import (
    LOCKED_STRICT_KIN, LOCKED_STRICT_MID, LOCKED_STRICT_NO,
)
from ecology_japan_2022_24_dependency_sensitivity import _cluster_variance, _interval

TRAIN_YEARS = (2018, 2019, 2020, 2021)
TEST_YEARS = (2022, 2023, 2024)
COUNTS = ("log_sire_relative_count", "log_dam_relative_count")
PERFORMANCE = ("sire_kin_history", "dam_kin_history")
FEATURES = {
    "M1": STRONG_NO_KIN,
    "MC": tuple(c for c in STRONG_KIN if c not in PERFORMANCE),
    "MP": tuple(c for c in STRONG_KIN if c not in COUNTS),
    "M2": STRONG_KIN,
}
CONDITIONAL = ("performance_given_counts", "counts_given_performance")
COMPARISONS = len(CONDITIONAL) * (1 + len(TEST_YEARS))
DRAWS, SEED, MIN_CLUSTERS = 999, 20261121, 30
CONTEXT = ["horse", "day", "year", "surface", "distance", "stratum", "sire_id", "dam_id"]


def _vector(values, n, bounded=False):
    a = np.asarray(values, dtype=float)
    if a.shape != (n,) or not n or not np.isfinite(a).all():
        raise ValueError("HOLD_INVALID_NUMERIC_VECTOR_OR_LENGTH")
    if bounded and ((a < 0).any() or (a > 1).any()):
        raise ValueError("HOLD_RANK_OR_PREDICTION_OUTSIDE_UNIT_INTERVAL")
    return a


def fit_factorial(features, y, horses):
    y = _vector(y, len(features), bounded=True)
    ids = np.asarray(horses)
    if ids.shape != y.shape or pd.isna(ids).any() or pd.Series(ids).astype(str).str.strip().eq("").any():
        raise ValueError("HOLD_TRAINING_HORSE_IDENTIFIERS")
    if not np.isfinite(features[list(STRONG_KIN)].to_numpy(float)).all():
        raise ValueError("HOLD_NONFINITE_HISTORICAL_FEATURE")
    return {name: fit_weighted_ridge(features, y, ids, cols, alpha=RIDGE_ALPHA)
            for name, cols in FEATURES.items()}


def predict_factorial(models, features):
    return {name: _vector(predict_weighted_ridge(models[name], features), len(features), bounded=True)
            for name in FEATURES}


def _model_losses(y, predictions):
    target = _vector(y, len(y), bounded=True)
    if set(predictions) != set(FEATURES):
        raise ValueError("HOLD_INCOMPLETE_FACTORIAL_MODELS")
    return {key: (target - _vector(predictions[key], len(y), bounded=True)) ** 2
            for key in FEATURES}


def _decompose(loss):
    p_alone = loss["M1"] - loss["MP"]
    c_alone = loss["M1"] - loss["MC"]
    p_given_c = loss["MC"] - loss["M2"]
    c_given_p = loss["MP"] - loss["M2"]
    p_share = (p_alone + p_given_c) / 2
    c_share = (c_alone + c_given_p) / 2
    full = loss["M1"] - loss["M2"]
    if not np.allclose(p_share + c_share, full, rtol=0, atol=1e-14):
        raise ValueError("HOLD_PAIRED_ROW_DECOMPOSITION")
    return {"full_gain": full, "performance_alone": p_alone, "counts_alone": c_alone,
            "performance_given_counts": p_given_c, "counts_given_performance": c_given_p,
            "shapley_performance": p_share, "shapley_counts": c_share}


def paired_loss_terms(y, predictions):
    """Return seven signed, row-paired MSE contrasts in input order."""
    return _decompose(_model_losses(y, predictions))


def _period_panel(panel):
    cols = ["horse", "race", "day", "sire_id", "y"]
    if panel.empty or not set(cols).issubset(panel.columns):
        raise ValueError("HOLD_INCOMPLETE_PERIOD_PANEL")
    p = panel.loc[:, cols].reset_index(drop=True).copy()
    for col in ("horse", "race", "sire_id"):
        p[col] = clean_id(p[col])
    if p.horse.eq("").any() or p.race.eq("").any() or p.duplicated(["horse", "race"]).any():
        raise ValueError("HOLD_MISSING_OR_DUPLICATE_HORSE_RACE_ID")
    if pd.api.types.is_numeric_dtype(p.day):
        raise ValueError("HOLD_AMBIGUOUS_NUMERIC_DATE")
    p["day"] = pd.to_datetime(p.day, errors="coerce", format="mixed").dt.normalize()
    if p.day.isna().any() or p.groupby("race").day.nunique().max() != 1:
        raise ValueError("HOLD_MISSING_OR_CONFLICTING_RACE_DATE")
    if p.groupby("horse").sire_id.nunique().max() != 1:
        raise ValueError("HOLD_CONFLICTING_SIRE_ID")
    p["y"] = _vector(p.y, len(p), bounded=True)
    n = p.horse.nunique()
    p["weight"] = 1 / (n * p.groupby("horse").horse.transform("size"))
    return p


def _sire_bootstrap(p, draws, seed, min_clusters):
    # Collapse to one equally weighted observation per horse before drawing
    # whole families. Separate prefixes keep unknown and known groups distinct.
    horse = p.groupby("horse").agg(gain=("gain", "mean"), sire=("sire_id", "first"))
    missing = horse.sire.eq("")
    family = ("recorded:" + horse.sire).where(~missing, "unknown:" + horse.index)
    groups = horse.groupby(family, sort=True).gain.agg(["sum", "size"])
    n = len(groups)
    summary = {"clusters": n, "unknown_sire_singleton_horses": int(missing.sum()),
               "largest_cluster_horses": int(groups["size"].max())}
    if n < min_clusters:
        return {**summary, "status": "HOLD_TOO_FEW_CLUSTERS"}
    sums = groups["sum"].to_numpy()
    sizes = groups["size"].to_numpy()
    rng = np.random.default_rng(seed)
    reps = np.empty(draws)
    for i in range(draws):
        sample = rng.integers(n, size=n)
        reps[i] = sums[sample].sum() / sizes[sample].sum()
    return {**summary, "status": "OK", "draws": draws, "seed": seed,
            "CI95": np.quantile(reps, [.025, .975]).tolist()}


def _uncertainty(panel, gain, draws, seed, min_clusters):
    if draws < 30 or min_clusters < 2:
        raise ValueError("HOLD_INVALID_DRAW_OR_CLUSTER_MINIMUM")
    p = panel.assign(gain=_vector(gain, len(panel)))
    center = float(np.average(p.gain, weights=p.weight))
    if p.gain.min() == p.gain.max():
        center = float(p.gain.iloc[0])
    p["q"] = p.weight * (p.gain - center)
    nh, vh = _cluster_variance(p, ["horse"])
    nd, vd = _cluster_variance(p, ["day"])
    nhd, vhd = _cluster_variance(p, ["horse", "day"])
    tw = {"horses": nh, "days": nd, "horse_day_intersections": nhd}
    if min(nh, nd) < min_clusters:
        tw["status"] = "HOLD_TOO_FEW_CLUSTERS"
    else:
        variance = vh + vd - vhd
        tw["variance"] = variance
        if variance <= 0:
            tw["status"] = "HOLD_NONPOSITIVE_VARIANCE"
        else:
            se = float(np.sqrt(variance))
            tw.update(status="OK", SE=se, CI95=_interval(center, se, NormalDist().inv_cdf(.975)),
                      CI95_bonferroni_8=_interval(center, se, NormalDist().inv_cdf(1-.025/COMPARISONS)))
    return {"mean_MSE_gain": center, "horses": nh, "two_way": tw,
            "sire_bootstrap": _sire_bootstrap(p, draws, seed, min_clusters)}


def paired_uncertainty(panel, gain, draws=DRAWS, seed=SEED, min_clusters=MIN_CLUSTERS):
    return _uncertainty(_period_panel(panel), gain, draws, seed, min_clusters)


def summarize_period(panel, predictions, draws=DRAWS, min_clusters=MIN_CLUSTERS):
    p = _period_panel(panel)
    losses = _model_losses(p.y, predictions)
    terms = _decompose(losses)
    mean = {k: float(np.average(v, weights=p.weight)) for k, v in terms.items()}
    losses = {"M0": (p.y - .5) ** 2, **losses}
    risk = {k: float(np.average(v, weights=p.weight)) for k, v in losses.items()}
    if not np.allclose([mean["shapley_counts"] + mean["shapley_performance"], risk["M1"] - risk["M2"]],
                       mean["full_gain"], rtol=0, atol=1e-14):
        raise ValueError("HOLD_EQUAL_HORSE_LOSS_DECOMPOSITION")
    return {
        "starts": len(p), "horses": int(p.horse.nunique()), "races": int(p.race.nunique()),
        "models": {k: {"MSE": v, "RMSE": float(np.sqrt(v))} for k, v in risk.items()},
        "loss_decomposition_MSE": mean,
        "conditional_uncertainty": {k: _uncertainty(p, terms[k], draws, SEED, min_clusters)
                                    for k in CONDITIONAL},
    }


def _strong_features(history, targets, meta):
    # Only target identity, dates, parents and race context enter the feature builders.
    context = targets.loc[:, CONTEXT]
    common = make_common_features(history, context)
    extra, _ = extra_features(history, context, meta)
    return pd.concat([common.reset_index(drop=True), extra], axis=1)


def _historical_predictions(raw, old, future):
    meta = old_metadata(raw)
    blocks, labels, horses = [], [], []
    for year in TRAIN_YEARS:
        t = old.loc[old.year == year]
        blocks.append(_strong_features(old.loc[old.year < year], t, meta))
        labels.append(t.y.to_numpy(float))
        horses.append(t.horse.astype(str).to_numpy())
    train = pd.concat(blocks, ignore_index=True)
    del blocks
    models = fit_factorial(train, np.concatenate(labels), np.concatenate(horses))
    del train
    return predict_factorial(models, _strong_features(old, future, meta))


def _check_score(actual, locked):
    if not np.isclose(actual, locked, rtol=0, atol=1e-8):
        raise ValueError("HOLD_LOCKED_RMSE_PARITY")


def canonical_parity_scores(scores):
    """Name legacy endpoints explicitly; its old M0 gain actually used M1."""
    return {
        "starts": scores["rows"], "horses": scores["unique_horses"], "races": scores["races"],
        "RMSE_M0_midpoint": scores["RMSE_unchanged_midpoint"],
        "RMSE_M1_own": scores["RMSE_portable_no_kin"],
        "RMSE_M2_family": scores["RMSE_portable_kin"],
    }


def analyze(archive: Path, db: Path):
    raw, old, future, _, gate, _ = load_sources(archive, db)
    if not old.year.lt(2022).all() or set(future.year.unique()) != set(TEST_YEARS):
        raise ValueError("HOLD_SOURCE_YEAR_SCOPE")
    preds = _historical_predictions(raw, old, future)
    all_scores = _scores(future, preds["M1"], preds["M2"])
    _check_score(all_scores["RMSE_portable_no_kin"], ALL_STRONG_NO_KIN)
    _check_score(all_scores["RMSE_portable_kin"], ALL_STRONG_KIN)
    mask, qa = strict_mask_exact_horse_race(raw, future, db, gate["two_event_anchor_horses"])
    strict = future.loc[mask].reset_index(drop=True)
    if (len(strict) != STRICT_ROWS or strict.horse.nunique() != STRICT_HORSES
            or qa["strict_races"] != 35333 or strict.race.nunique() != 35333):
        raise ValueError("HOLD_STRICT_COHORT_PARITY")
    pred = {k: v[mask] for k, v in preds.items()}
    strict_scores = _scores(strict, pred["M1"], pred["M2"])
    _check_score(strict_scores["RMSE_portable_no_kin"], LOCKED_STRICT_NO)
    _check_score(strict_scores["RMSE_portable_kin"], LOCKED_STRICT_KIN)
    _check_score(strict_scores["RMSE_unchanged_midpoint"], LOCKED_STRICT_MID)
    pooled = summarize_period(strict, pred)
    for name, expected in (("M1", LOCKED_STRICT_NO), ("M2", LOCKED_STRICT_KIN), ("M0", LOCKED_STRICT_MID)):
        _check_score(pooled["models"][name]["RMSE"], expected)
    by_year = {}
    for year in TEST_YEARS:
        select = strict.year.eq(year).to_numpy()
        by_year[str(year)] = summarize_period(strict.loc[select], {k: v[select] for k, v in pred.items()})
    return {
        "status": "POSTHOC_STRICT_FAMILY_FEATURE_ABLATION",
        "source_A_sha256": SOURCE_SHA, "source_B_sha256": SQLITE_SHA,
        "training_years": list(TRAIN_YEARS), "ridge_alpha": RIDGE_ALPHA,
        "performance_features": list(PERFORMANCE), "explicit_count_features": list(COUNTS),
        "strong_all_row_parity": canonical_parity_scores(all_scores), "strict_source_qa": qa,
        "pooled": pooled, "by_year": by_year,
        "uncertainty_settings": {"primary_contrasts": list(CONDITIONAL), "comparisons": COMPARISONS,
                                 "min_clusters": MIN_CLUSTERS, "bootstrap_draws": DRAWS, "seed": SEED},
        "scope": {
            "retrospective_not_an_independent_prospective_test": True,
            "performance_block_contains_count_dependent_shrinkage": True,
            "official_studbook_identity_and_source_publication_times_verified": False,
            "underlying_source_redistribution_rights_verified": False,
            "genetic_causation_heritability_or_fitness_identified": False,
            "raw_records_horse_parent_identifiers_or_individual_predictions_exported": False,
            "sire_bootstrap_intervals_are_pointwise_sensitivity_only": True,
        },
        "interpretation": [
            "Positive paired MSE gains indicate improved equal-horse rank prediction within the period.",
            "The performance features include own-count and peer-count shrinkage.",
            "Order-averaged allocations describe refitted model losses; family associations can reflect rearing and selection.",
            "Intervals condition on the observed cohort and fitted coefficients. The sire bootstrap is a separate sensitivity.",
            "The outcome period was previously examined. Repeat execution demonstrates technical reproducibility.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--sqlite", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.archive, args.sqlite)
    encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "pooled_models": result["pooled"]["models"],
                      "pooled_MSE_gains": result["pooled"]["loss_decomposition_MSE"]}, allow_nan=False))


if __name__ == "__main__":
    main()
