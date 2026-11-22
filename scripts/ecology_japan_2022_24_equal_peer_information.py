#!/usr/bin/env python3
"""Refit the two parent-performance models over 32 matched equal-peer draws."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

import ecology_japan_2022_24_family_feature_ablation as ablation
import ecology_japan_2022_24_parent_performance_channels as channels
from ecology_japan_2022_24_sire_signal_concentration import (
    ATOL, REFERENCE, REFERENCE_SHA, _periods, _require_parity,
)
from ecology_japan_balanced_parent_history import (
    balanced_performance, prepare_peer_block, replace_performance,
)


PARENT_REFERENCE = REFERENCE.with_name("japan-2022-24-parent-performance-channels-20261122.json")
PARENT_REFERENCE_SHA = "18caad41d66257cc064de13051fbf65241493f869960cff2d05d7fde2968657f"
SEEDS = tuple(range(2026112200, 2026112232))
PRIMARY = ("balanced_sire_advantage", "change_in_sire_advantage")
COMPARISONS = len(PRIMARY) * (1 + len(ablation.TEST_YEARS))
SIDES = ("MS", "MD")


def _squared_loss(y, prediction):
    observed = ablation._vector(y, len(y), bounded=True)
    fitted = ablation._vector(prediction, len(y), bounded=True)
    return (observed - fitted) ** 2


def _balanced_support(k, weights):
    def cell(mask):
        return {"starts": int(mask.sum()), "horse_equal_share": float(weights[mask].sum())}

    return {"mean_peer_count": float(np.average(k, weights=weights)),
            "bins": {"0": cell(k == 0), "1": cell(k == 1),
                     "2-4": cell((k >= 2) & (k <= 4)), "5+": cell(k >= 5)}}


def _uncertainty(p, gain, coverage, draws, min_clusters):
    result = channels._uncertainty(p, gain, coverage, draws, channels.SEED, min_clusters)
    tw = result["two_way"]
    if tw["status"] == "OK":
        del tw["CI95_bonferroni_12"]
        tw["CI95_bonferroni_8"] = ablation._interval(
            result["mean_MSE_gain"], tw["SE"], NormalDist().inv_cdf(1 - .025 / COMPARISONS))
    return result


def summarize_period(panel, full_predictions, draw_losses, support, selected_counts, *,
                     draws=channels.DRAWS, min_clusters=channels.MIN_CLUSTERS):
    """Score each horse equally after averaging losses across the fixed refits."""
    channels._settings(draws, channels.SEED, min_clusters)
    p = channels._period_panel(panel)
    full = channels._losses(p.y, full_predictions)
    full["M0"] = (p.y.to_numpy() - .5) ** 2
    if set(draw_losses) != set(SIDES):
        raise ValueError("HOLD_INCOMPLETE_BALANCED_MODELS")
    matrices = {key: np.asarray(draw_losses[key], dtype=float) for key in SIDES}
    for matrix in matrices.values():
        if (matrix.shape != (len(SEEDS), len(p)) or not np.isfinite(matrix).all()
                or (matrix < 0).any() or (matrix > 1).any()):
            raise ValueError("HOLD_INVALID_BALANCED_DRAW_LOSSES")

    coverage = channels._coverage(p)
    support_stats = channels._support_summary(p, support, coverage, panel.index)
    if not isinstance(selected_counts, pd.Series) or not selected_counts.index.equals(panel.index):
        raise ValueError("HOLD_MISALIGNED_SELECTED_PEER_COUNTS")
    k = ablation._vector(selected_counts, len(p))
    if not np.array_equal(k, support[channels.SUPPORT_COLUMNS].to_numpy(float).min(axis=1)):
        raise ValueError("HOLD_SELECTED_PEER_COUNT_PARITY")
    weights = p.weight.to_numpy()
    support_stats["balanced"] = _balanced_support(k, weights)

    balanced = {name: matrices[name].mean(axis=0) for name in SIDES}
    f = full["MD"] - full["MS"]
    b = np.zeros(len(p))
    b_draws = np.empty(len(SEEDS))
    for i, (ms, md) in enumerate(zip(matrices["MS"], matrices["MD"])):
        paired = md - ms
        b += paired
        b_draws[i] = np.average(paired, weights=weights)
    b /= len(SEEDS)
    terms = {"full_sire_advantage": f, "balanced_sire_advantage": b, "change_in_sire_advantage": f - b,
             "sire_loss_increase": balanced["MS"] - full["MS"],
             "dam_loss_increase": balanced["MD"] - full["MD"]}
    side_difference = terms["sire_loss_increase"] - terms["dam_loss_increase"]
    if not np.allclose(terms["change_in_sire_advantage"], side_difference, rtol=0, atol=1e-14):
        raise ValueError("HOLD_PAIRED_LOSS_IDENTITY")
    contrasts = {key: float(np.average(value, weights=weights)) for key, value in terms.items()}

    def risks(losses):
        mean = {name: float(np.average(loss, weights=weights)) for name, loss in losses.items()}
        return {name: {"MSE": mse, "RMSE": float(np.sqrt(mse))} for name, mse in mean.items()}

    # Pair each draw across both models and all starts; reuse these same horse weights.
    whole_draws = {"balanced_sire_advantage": b_draws,
                   "change_in_sire_advantage": contrasts["full_sire_advantage"] - b_draws}
    mc = {}
    for key, values in whole_draws.items():
        sd = float(values.std(ddof=1))
        mc[key] = {"mean": float(values.mean()), "SD": sd, "MCSE": sd/np.sqrt(len(SEEDS)),
                   "min": float(values.min()), "max": float(values.max())}
        if not np.isclose(mc[key]["mean"], contrasts[key], rtol=0, atol=1e-14):
            raise ValueError("HOLD_PAIRED_DRAW_MEAN")
    return {"starts": len(p), "horses": int(p.horse.nunique()), "races": int(p.race.nunique()),
            "full_models": risks(full), "balanced_models": risks(balanced),
            "mean_MSE_contrasts": contrasts,
            "primary_uncertainty": {key: _uncertainty(p, terms[key], coverage, draws, min_clusters)
                                    for key in PRIMARY},
            "monte_carlo": mc, "per_draw": [{"seed": seed, **{key: float(v[i]) for key, v in whole_draws.items()}}
                                            for i, seed in enumerate(SEEDS)],
            "support": support_stats}


def _reference(path, digest, label):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError(f"HOLD_CHANGED_{label}_REFERENCE")
    return json.loads(content)


def _base_matrices(old, future, meta):
    blocks, labels, horses = [], [], []
    for year in ablation.TRAIN_YEARS:
        targets = old.loc[old.year.eq(year)]
        context = targets.loc[:, ablation.CONTEXT]
        blocks.append(ablation._strong_features(old.loc[old.year.lt(year)], context, meta))
        labels.append(targets.y.to_numpy(float))
        horses.append(targets.horse.astype(str).to_numpy())
    train = pd.concat(blocks, ignore_index=True)
    del blocks
    evaluation = ablation._strong_features(old, future.loc[:, ablation.CONTEXT], meta)
    return train, np.concatenate(labels), np.concatenate(horses), evaluation


def _prepare_blocks(old, strict, train, evaluation):
    def checked(history, targets, base, cutoff):
        block = prepare_peer_block(history, targets.loc[:, ablation.CONTEXT], cutoff_year=cutoff)
        if not np.array_equal(block.counts.to_numpy(), base[channels.SUPPORT_COLUMNS].to_numpy()):
            raise ValueError("HOLD_NATIVE_PEER_COUNT_PARITY")
        return block

    blocks = []
    offset = 0
    for year in ablation.TRAIN_YEARS:
        targets = old.loc[old.year.eq(year)]
        end = offset + len(targets)
        blocks.append(checked(old.loc[old.year.lt(year)], targets, train.iloc[offset:end], year))
        offset = end
    return blocks, checked(old, strict, evaluation, ablation.TEST_YEARS[0])


def _draw_losses(train, labels, horses, evaluation, observed, training_blocks, evaluation_block):
    losses = {name: np.empty((len(SEEDS), len(observed))) for name in SIDES}
    for i, seed in enumerate(SEEDS):
        performance = pd.concat([balanced_performance(block, seed=seed) for block in training_blocks],
                                ignore_index=True)
        sampled_train = replace_performance(train, performance)
        sampled_eval = replace_performance(evaluation, balanced_performance(evaluation_block, seed=seed))
        for name in SIDES:
            model = ablation.fit_weighted_ridge(sampled_train, labels, horses, channels.FEATURES[name],
                                                alpha=ablation.RIDGE_ALPHA)
            losses[name][i] = _squared_loss(observed, ablation.predict_weighted_ridge(model, sampled_eval))
        del sampled_train, sampled_eval, performance
    return losses


def analyze(archive: Path, db: Path) -> dict:
    ref70 = _reference(REFERENCE, REFERENCE_SHA, "PR70")
    ref72 = _reference(PARENT_REFERENCE, PARENT_REFERENCE_SHA, "PR72")
    raw, old, future, _, gate, _ = ablation.load_sources(archive, db)
    if not old.year.lt(2022).all() or set(future.year.unique()) != set(ablation.TEST_YEARS):
        raise ValueError("HOLD_SOURCE_YEAR_SCOPE")
    train, labels, horses, evaluation = _base_matrices(old, future, ablation.old_metadata(raw))
    models = channels.fit_factorial(train, labels, horses)
    full = channels.predict_factorial(models, evaluation)
    scores = ablation._scores(future, full["M1"], full["M2"])
    _require_parity(ablation.canonical_parity_scores(scores), ref70["strong_all_row_parity"], "all_rows")
    mask, qa = ablation.strict_mask_exact_horse_race(raw, future, db, gate["two_event_anchor_horses"])
    _require_parity(qa, ref70["strict_source_qa"], "strict_source_qa")
    strict = future.loc[mask].reset_index(drop=True)
    full = {name: values[mask] for name, values in full.items()}
    evaluation = evaluation.loc[np.asarray(mask)].reset_index(drop=True)
    support = evaluation[channels.SUPPORT_COLUMNS]
    del raw, future
    for label, panel, pred in _periods(strict, full):
        legacy = {name: pred[name] for name in ablation.FEATURES}
        for ref, actual, tag in (
            (ref70, ablation.summarize_period(panel, legacy), "PR70"),
            (ref72, channels.summarize_period(panel, pred, support.loc[panel.index]), "PR72"),
        ):
            expected = ref[label] if label == "pooled" else ref["by_year"][label]
            _require_parity(actual, expected, f"{tag}.{label}")

    training_blocks, eval_block = _prepare_blocks(old, strict, train, evaluation)
    del old
    losses = _draw_losses(train, labels, horses, evaluation, strict.y, training_blocks, eval_block)
    selected = pd.Series(eval_block.k, index=strict.index)
    del training_blocks, eval_block, train, evaluation
    results = {}
    for label, panel, pred in _periods(strict, full):
        period_losses = losses if label == "pooled" else {k: v[:, panel.index] for k, v in losses.items()}
        results[label] = summarize_period(panel, pred, period_losses, support.loc[panel.index],
                                          selected.loc[panel.index])
    return {"status": "POSTHOC_STRICT_EQUAL_PEER_INFORMATION",
            "source_A_sha256": ablation.SOURCE_SHA, "source_B_sha256": ablation.SQLITE_SHA,
            "pr70_reference_sha256": REFERENCE_SHA, "pr72_reference_sha256": PARENT_REFERENCE_SHA,
            "training_years": list(ablation.TRAIN_YEARS), "evaluation_cutoff_year": 2022,
            "ridge_alpha": ablation.RIDGE_ALPHA, "seeds": list(SEEDS),
            "parity": {"status": "OK", "absolute_tolerance": ATOL, "strong_all_row_scores": True,
                       "strict_source_qa": True, "all_pr70_pooled_and_yearly_statistics": True,
                       "all_pr72_pooled_and_yearly_statistics": True, "all_native_peer_counts": True},
            "pooled": results.pop("pooled"), "by_year": results,
            "uncertainty_settings": {"primary_contrasts": list(PRIMARY), "comparisons": COMPARISONS,
                                     "min_clusters": channels.MIN_CLUSTERS,
                                     "min_recorded_parent_groups": channels.MIN_CLUSTERS,
                                     "bootstrap_draws": channels.DRAWS, "seed": channels.SEED},
            "scope": {"retrospective_not_an_independent_prospective_test": True,
                      "evaluation_intervals_condition_on_the_32_draws_and_fits": True,
                      "parent_bootstrap_intervals_are_separate_pointwise_sensitivities": True,
                      "monte_carlo_precision_is_conditional_on_observed_records": True,
                      "genetic_causation_heritability_maternal_effect_or_fitness_identified": False,
                      "official_studbook_identity_and_source_publication_times_verified": False,
                      "underlying_source_redistribution_rights_verified": False,
                      "raw_records_horse_parent_identifiers_or_individual_predictions_exported": False}}


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
    print(result["status"])


if __name__ == "__main__":
    main()
