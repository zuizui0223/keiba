#!/usr/bin/env python3
"""Recorded-sire concentration of the fixed MC-minus-M2 squared prediction loss."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import ecology_japan_2022_24_family_feature_ablation as ablation

REFERENCE = (Path(__file__).resolve().parents[1] / "docs" / "evidence"
             / "japan-2022-24-family-feature-ablation-20261121.json")
REFERENCE_SHA = "66c0e45fa3870b5ee3350ca21fb28cfe5e3331cfa835d7207dc39d7ed2dee619"
PRIMARY = "performance_given_counts"
ESTIMANDS = ("horse_equal_gain", "sire_equal_gain", "size_association_gap")
ATOL = 1e-12


def _sign_counts(totals):
    return {"positive": int((totals > 0).sum()), "zero": int((totals == 0).sum()),
            "negative": int((totals < 0).sum())}


def _top_shares(magnitudes):
    ranked = sorted(magnitudes, reverse=True)
    mass = sum(ranked)
    return {str(k): float(sum(ranked[:k]) / mass) if mass else None for k in (1, 5, 10)}


def _deletion_summaries(totals, sizes):
    # The inputs are exact sums of the observed floating-point horse means.
    # This avoids losing a tiny remainder to rounding when a large group is removed.
    ranked = sorted(zip(totals, map(int, sizes)), reverse=True)
    total, horses = sum(totals), int(sizes.sum())
    if len(ranked) > 1:
        remaining = [(total - t) / (horses - n) for t, n in ranked]
        single = {"status": "OK", "minimum_remaining_gain": float(min(remaining)),
                  "maximum_remaining_gain": float(max(remaining)),
                  "nonpositive_remaining_count": sum(value <= 0 for value in remaining)}
    else:
        single = {"status": "HOLD_ONE_RECORDED_SIRE" if ranked else "HOLD_NO_RECORDED_SIRES",
                  "minimum_remaining_gain": None, "maximum_remaining_gain": None,
                  "nonpositive_remaining_count": None}

    failure = "NO_NONEMPTY_NONPOSITIVE_REMAINDER" if ranked else "HOLD_NO_RECORDED_SIRES"
    joint = {"status": failure, "groups_removed": None, "horses_removed": None,
             "remaining_gain": None}
    if ranked and total <= 0:
        joint.update(status="ALREADY_NONPOSITIVE", groups_removed=0, horses_removed=0,
                     remaining_gain=float(total / horses))
    else:
        remaining_mass, removed_horses = total, 0
        for k, (t, n) in enumerate(ranked[:-1], 1):
            remaining_mass -= t
            removed_horses += n
            if remaining_mass <= 0:
                joint.update(status="OK", groups_removed=k, horses_removed=removed_horses,
                             remaining_gain=float(remaining_mass / (horses - removed_horses)))
                break
    return single, joint


def _bootstrap(totals, sizes, means, draws, seed, min_clusters):
    n = len(sizes)
    result = {"clusters": n, "draws": int(draws), "seed": int(seed),
              "min_clusters": int(min_clusters)}
    if n < min_clusters:
        return {**result, "status": "HOLD_TOO_FEW_CLUSTERS", "CI95": None}
    rng = np.random.default_rng(seed)
    samples = np.empty((draws, len(ESTIMANDS)))
    for i in range(draws):
        sel = rng.integers(n, size=n)
        weighted = totals[sel].sum() / sizes[sel].sum()
        balanced = means[sel].mean()
        samples[i] = weighted, balanced, weighted - balanced
    limits = np.quantile(samples, [.025, .975], axis=0).T.tolist()
    return {**result, "status": "OK", "CI95": dict(zip(ESTIMANDS, limits))}


def sire_summary(panel, gain, draws=ablation.DRAWS, seed=ablation.SEED,
                 min_clusters=ablation.MIN_CLUSTERS):
    """Recompute horse means and recorded-sire weights within one supplied period."""
    if (not isinstance(draws, (int, np.integer)) or draws < 30
            or not isinstance(min_clusters, (int, np.integer)) or min_clusters < 2
            or isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0):
        raise ValueError("HOLD_INVALID_BOOTSTRAP_SETTINGS")
    if not isinstance(panel, pd.DataFrame) or not panel.columns.is_unique:
        raise ValueError("HOLD_INVALID_PERIOD_PANEL")
    p = ablation._period_panel(panel)
    p["gain"] = ablation._vector(gain, len(p))
    if p.gain.abs().gt(1).any():
        raise ValueError("HOLD_PAIRED_LOSS_DIFFERENCE_OUTSIDE_UNIT_RANGE")
    horse = p.groupby("horse").agg(gain=("gain", "mean"), sire=("sire_id", "first"))
    known = horse.loc[horse.sire.ne("")].copy()
    known["mass"] = known.gain.map(Fraction.from_float)
    groups = known.groupby("sire", sort=True).mass.agg(["sum", "size"])
    exact = groups["sum"].tolist()
    sizes = groups["size"].to_numpy(dtype=int)
    totals = np.asarray(exact, dtype=float)
    means = totals / sizes
    n = len(known)
    weighted = float(sum(exact) / n) if n else None
    balanced = float(means.mean()) if n else None
    gap = weighted - balanced if n else None
    identity = (float(np.mean((sizes - sizes.mean()) * (means - balanced)) / sizes.mean())
                if n else None)
    if n and not math.isclose(gap, identity, rel_tol=0, abs_tol=1e-14):
        raise ValueError("HOLD_GROUP_SIZE_COVARIANCE_IDENTITY")

    bins = {}
    for label, sel in (("1-4", sizes <= 4), ("5-19", (sizes >= 5) & (sizes < 20)),
                       ("20+", sizes >= 20)):
        horses = int(sizes[sel].sum())
        bins[label] = {"sires": int(sel.sum()), "horses": horses,
                       "sign_counts": _sign_counts(totals[sel]),
                       "horse_equal_gain": math.fsum(totals[sel]) / horses if horses else None,
                       "sire_equal_gain": float(means[sel].mean()) if horses else None}
    positive = [t for t in exact if t > 0]
    negative = [-t for t in exact if t < 0]
    single, joint = _deletion_summaries(exact, sizes)
    return {
        "status": "OK" if n else "HOLD_NO_RECORDED_SIRES",
        "starts": len(p), "horses": len(horse), "races": int(p.race.nunique()),
        "recorded_sires": len(groups),
        "coverage": {"total_horses": len(horse), "known_sire_horses": n,
                     "unknown_sire_horses": len(horse) - n, "known_sire_fraction": n / len(horse)},
        "all_horse_gain": float(horse.gain.mean()),
        "horse_equal_gain": weighted, "sire_equal_gain": balanced,
        "size_association_gap": gap, "covariance_identity_gap": identity,
        "sign_counts": _sign_counts(totals), "support_bins": bins,
        "contribution_mass": {
            "positive_total": float(sum(positive)), "negative_total_magnitude": float(sum(negative)),
            "positive_MSE_mass": float(sum(positive) / n) if n else None,
            "negative_MSE_magnitude": float(sum(negative) / n) if n else None,
            "positive_top_shares": _top_shares(positive), "negative_top_shares": _top_shares(negative),
        },
        "leave_one_sire_out": single, "minimum_joint_deletion": joint,
        "bootstrap": _bootstrap(totals, sizes, means, draws, seed, min_clusters),
    }


def _require_parity(actual, locked, path):
    """Match every frozen key, count, status and numerical endpoint."""
    if isinstance(locked, dict):
        if isinstance(actual, dict) and actual.keys() == locked.keys():
            for key in locked:
                _require_parity(actual[key], locked[key], f"{path}.{key}")
            return
    elif isinstance(locked, list):
        if isinstance(actual, list) and len(actual) == len(locked):
            for i, (value, expected) in enumerate(zip(actual, locked)):
                _require_parity(value, expected, f"{path}[{i}]")
            return
    elif isinstance(locked, float):
        if math.isclose(actual, locked, rel_tol=0, abs_tol=ATOL):
            return
    elif actual == locked:
        return
    raise ValueError(f"HOLD_PR70_PARITY: {path}")


def _periods(strict, predictions):
    yield "pooled", strict, predictions
    for year in ablation.TEST_YEARS:
        mask = strict.year.eq(year).to_numpy()
        yield str(year), strict.loc[mask], {key: value[mask] for key, value in predictions.items()}


def analyze(archive: Path, db: Path):
    reference_bytes = REFERENCE.read_bytes()
    if hashlib.sha256(reference_bytes).hexdigest() != REFERENCE_SHA:
        raise ValueError("HOLD_CHANGED_PR70_REFERENCE")
    reference = json.loads(reference_bytes)
    raw, old, future, _, gate, _ = ablation.load_sources(archive, db)
    if not old.year.lt(2022).all() or set(future.year.unique()) != set(ablation.TEST_YEARS):
        raise ValueError("HOLD_SOURCE_YEAR_SCOPE")
    predictions = ablation._historical_predictions(raw, old, future)
    scores = ablation._scores(future, predictions["M1"], predictions["M2"])
    _require_parity(ablation.canonical_parity_scores(scores), reference["strong_all_row_parity"],
                    "strong_all_row_parity")
    mask, qa = ablation.strict_mask_exact_horse_race(raw, future, db, gate["two_event_anchor_horses"])
    _require_parity(qa, reference["strict_source_qa"], "strict_source_qa")
    strict = future.loc[mask].reset_index(drop=True)
    predictions = {key: values[mask] for key, values in predictions.items()}
    del raw, old, future
    expected = {"pooled": reference["pooled"], **reference["by_year"]}
    for label, panel, pred in _periods(strict, predictions):
        _require_parity(ablation.summarize_period(panel, pred), expected[label], label)

    result = {}
    for label, panel, pred in _periods(strict, predictions):
        gain = ablation.paired_loss_terms(panel.y, pred)[PRIMARY]
        period = sire_summary(panel, gain)
        if period["coverage"]["unknown_sire_horses"] != 0:
            raise ValueError("HOLD_CHANGED_RECORDED_SIRE_COVERAGE")
        benchmark = expected[label]["conditional_uncertainty"][PRIMARY]
        _require_parity(period["horse_equal_gain"], benchmark["mean_MSE_gain"], f"{label}.gain")
        _require_parity(period["bootstrap"]["CI95"]["horse_equal_gain"],
                        benchmark["sire_bootstrap"]["CI95"], f"{label}.sire_bootstrap")
        result[label] = period
    return {
        "status": "POSTHOC_STRICT_SIRE_SIGNAL_CONCENTRATION",
        "source_A_sha256": ablation.SOURCE_SHA, "source_B_sha256": ablation.SQLITE_SHA,
        "reference_sha256": REFERENCE_SHA, "primary_contrast": PRIMARY,
        "training_years": list(ablation.TRAIN_YEARS), "ridge_alpha": ablation.RIDGE_ALPHA,
        "parity": {"status": "OK", "absolute_tolerance": ATOL,
                   "strong_all_row_scores": True, "strict_source_qa": True,
                   "all_pr70_pooled_and_yearly_statistics": True,
                   "known_sire_horse_equal_intervals": True},
        "pooled": result.pop("pooled"), "by_year": result,
        "bootstrap_settings": {"draws": ablation.DRAWS, "seed": ablation.SEED,
                               "min_clusters": ablation.MIN_CLUSTERS},
        "scope": {
            "posthoc_fixed_fit_diagnostic": True, "unknown_sires_excluded_from_group_estimands": True,
            "group_size_counts_evaluated_horses": True,
            "minimum_joint_deletion_is_outcome_selected_worst_case": True,
            "horses_removed_minimized_separately": False,
            "sire_bootstrap_intervals_are_pointwise_sensitivity_only": True,
            "official_studbook_identity_and_source_publication_times_verified": False,
            "underlying_source_redistribution_rights_verified": False,
            "genetic_causation_heritability_or_fitness_identified": False,
            "raw_records_horse_parent_identifiers_or_individual_predictions_exported": False,
        },
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
    print(json.dumps({"status": result["status"], "recorded_sires": result["pooled"]["recorded_sires"]}))


if __name__ == "__main__":
    main()
