#!/usr/bin/env python3
"""Test whether same-count recorded kin histories beat unrelated historical peers.

Historical posthoc results only. Aggregate outputs contain no animal identities.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
from statistics import NormalDist

import numpy as np
import pandas as pd

import ecology_japan_2022_24_family_feature_ablation as ablation
import ecology_japan_2022_24_parent_performance_channels as channels
import ecology_japan_2022_24_equal_peer_information as equal
from ecology_japan_2022_24_sire_signal_concentration import (
    ATOL, REFERENCE, REFERENCE_SHA, _periods, _require_parity,
)
from ecology_japan_balanced_parent_history import replace_performance
from ecology_japan_unrelated_peer_control import prepare_unrelated_block, unrelated_performance


PR73_REFERENCE = REFERENCE.with_name("japan-2022-24-equal-peer-information-20261122.json")
PR73_SHA256 = "d24ba47a6a618411cbdc14e728d6de18a20602bfb7533a73cbf491ca1a8d4c01"
PRIMARY = ("sire_over_unrelated", "dam_over_unrelated")
COMPARISONS = len(PRIMARY) * (1 + len(ablation.TEST_YEARS))


def _control_blocks(old, strict, true_blocks, evaluation_block):
    prepared = []
    for year, true_block in zip(ablation.TRAIN_YEARS, true_blocks, strict=True):
        target = old.loc[old.year.eq(year)]
        history = old.loc[old.year.lt(year)]
        prepared.append(prepare_unrelated_block(history, target.loc[:, ablation.CONTEXT],
                                               true_block, cutoff_year=year))
    prepared_eval = prepare_unrelated_block(old, strict.loc[:, ablation.CONTEXT],
                                            evaluation_block, cutoff_year=2022)
    return prepared, prepared_eval


def _control_losses(train, labels, horses, evaluation, observed, train_blocks, eval_block):
    losses = np.empty((len(equal.SEEDS), len(observed)), dtype=float)
    for i, seed in enumerate(equal.SEEDS):
        pseudo_train = pd.concat([unrelated_performance(block, seed=seed) for block in train_blocks],
                                 ignore_index=True)
        pseudo_eval = unrelated_performance(eval_block, seed=seed)
        training_features = replace_performance(train, pseudo_train)
        evaluation_features = replace_performance(evaluation, pseudo_eval)
        fitted = ablation.fit_weighted_ridge(training_features, labels, horses,
                                              channels.FEATURES["MS"], alpha=ablation.RIDGE_ALPHA)
        preds = ablation.predict_weighted_ridge(fitted, evaluation_features)
        losses[i] = equal._squared_loss(observed, preds)
    return losses


def summarize_period(panel, full_preds, balanced_losses, control_losses, reference,
                     *, draws=channels.DRAWS, min_clusters=channels.MIN_CLUSTERS):
    """Separate per-row loss variation from 32 draw-level Monte Carlo precision."""
    channels._settings(draws, channels.SEED, min_clusters)
    p = channels._period_panel(panel)
    n = len(p)
    w = p.weight.to_numpy()
    loss = {k: np.asarray(v, dtype=float) for k, v in balanced_losses.items()}
    loss["N"] = np.asarray(control_losses, dtype=float)
    if set(loss) != {"MS", "MD", "N"}:
        raise ValueError("HOLD_INCOMPLETE_TRUE_AND_UNRELATED_MODELS")
    if any(v.shape != (len(equal.SEEDS), n) or not np.isfinite(v).all()
           or (v < 0).any() or (v > 1).any() for v in loss.values()):
        raise ValueError("HOLD_INVALID_DRAW_LOSS_MATRICES")
    before = channels._losses(p.y, full_preds)
    n_mean = loss["N"].mean(axis=0)
    terms = {"sire_over_unrelated": (loss["N"] - loss["MS"]).mean(axis=0),
             "dam_over_unrelated": (loss["N"] - loss["MD"]).mean(axis=0)}
    per_seed = {key: np.average(loss["N"] - loss[side], weights=w, axis=1)
                for key, side in zip(PRIMARY, ("MS", "MD"))}
    # The same negative control cancels exactly in the difference.
    same_seed_parent_advantage = per_seed["sire_over_unrelated"] - per_seed["dam_over_unrelated"]
    expected_parent_advantage = np.average(loss["MD"] - loss["MS"], weights=w, axis=1)
    if not np.allclose(same_seed_parent_advantage, expected_parent_advantage, rtol=0, atol=1e-12):
        raise ValueError("HOLD_UNRELATED_PAIRED_CONTRAST_IDENTITY")
    expected_per_seed = reference["per_draw"]
    if len(expected_per_seed) != len(equal.SEEDS):
        raise ValueError("HOLD_PR73_DRAW_COUNT")
    for i, seed in enumerate(equal.SEEDS):
        if (expected_per_seed[i]["seed"] != seed or
                not np.isclose(same_seed_parent_advantage[i],
                               expected_per_seed[i]["balanced_sire_advantage"], atol=ATOL, rtol=0)):
            raise ValueError("HOLD_PR73_DRAW_IDENTITY")
    mean_sire_adv = float(np.average(terms[PRIMARY[0]], weights=w))
    mean_dam_adv = float(np.average(terms[PRIMARY[1]], weights=w))
    if not np.isclose(mean_sire_adv - mean_dam_adv,
                      reference["mean_MSE_contrasts"]["balanced_sire_advantage"], atol=ATOL, rtol=0):
        raise ValueError("HOLD_PR73_PARENT_CONTRAST_IDENTITY")
    coverage = channels._coverage(p)

    def risk(v):
        mse = float(np.average(v, weights=w))
        return {"MSE": mse, "RMSE": float(np.sqrt(mse))}

    risks = {"M0": risk((p.y.to_numpy()-.5)**2), "MC": risk(before["MC"]),
             "unrelated_N": risk(n_mean),
             "true_equal_sire_MS": risk(loss["MS"].mean(axis=0)),
             "true_equal_dam_MD": risk(loss["MD"].mean(axis=0))}
    for actual, expected in (("M0","M0"), ("MC","MC")):
        if not np.isclose(risks[actual]["MSE"], reference["full_models"][expected]["MSE"],
                          atol=ATOL, rtol=0):
            raise ValueError("HOLD_PR73_MODEL_RISK_PARITY")
    for actual, expected in (("true_equal_sire_MS","MS"), ("true_equal_dam_MD","MD")):
        if not np.isclose(risks[actual]["MSE"], reference["balanced_models"][expected]["MSE"],
                          atol=ATOL, rtol=0):
            raise ValueError("HOLD_PR73_EQUAL_MODEL_RISK_PARITY")
    monte_carlo = {}
    for key, vals in per_seed.items():
        sd = float(vals.std(ddof=1))
        avg = float(vals.mean())
        if not np.isclose(avg, np.average(terms[key], weights=w), atol=ATOL, rtol=0):
            raise ValueError("HOLD_DRAW_TO_ROW_MEAN_DISAGREEMENT")
        monte_carlo[key] = {"mean": avg, "SD": sd, "MCSE": sd/np.sqrt(len(equal.SEEDS)),
                            "min": float(vals.min()), "max": float(vals.max())}
    out = {
        "starts": n, "horses": int(p.horse.nunique()), "races": int(p.race.nunique()),
        "models": risks,
        "mean_MSE_contrasts": {
            **{k: float(np.average(terms[k], weights=w)) for k in PRIMARY},
            "unrelated_over_MC": risks["MC"]["MSE"] - risks["unrelated_N"]["MSE"],
            "kin_identity_difference_check": mean_sire_adv - mean_dam_adv,
        },
        "primary_uncertainty": {key: equal._uncertainty(p, terms[key], coverage, draws, min_clusters)
                                for key in PRIMARY},
        "monte_carlo": monte_carlo,
        "per_draw": [{"seed": seed, **{k: float(v[i]) for k, v in per_seed.items()}}
                     for i, seed in enumerate(equal.SEEDS)],
        "support": reference["support"],
    }
    for key in PRIMARY:
        ci = out["primary_uncertainty"][key]["two_way"]
        if "CI95_bonferroni_8" in ci and ci["status"] == "OK":
            z = NormalDist().inv_cdf(1 - .025 / COMPARISONS)
            estimate = out["mean_MSE_contrasts"][key]
            if not np.allclose(ci["CI95_bonferroni_8"],
                               [estimate-z*ci["SE"], estimate+z*ci["SE"]], atol=ATOL, rtol=0):
                raise ValueError("HOLD_UNRELATED_MULTIPLICITY_CALCULATION")
    return out


def analyze(archive: Path, sqlite: Path) -> dict:
    ref70 = equal._reference(REFERENCE, REFERENCE_SHA, "PR70")
    ref72 = equal._reference(equal.PARENT_REFERENCE, equal.PARENT_REFERENCE_SHA, "PR72")
    ref73 = equal._reference(PR73_REFERENCE, PR73_SHA256, "PR73")
    raw, old, future, _, gate, _ = ablation.load_sources(archive, sqlite)
    if not old.year.lt(2022).all() or set(future.year.unique()) != set(ablation.TEST_YEARS):
        raise ValueError("HOLD_SOURCE_YEAR_SCOPE")
    train, labels, horses, evaluation = equal._base_matrices(old, future, ablation.old_metadata(raw))
    models = channels.fit_factorial(train, labels, horses)
    full = channels.predict_factorial(models, evaluation)
    all_scores = ablation._scores(future, full["M1"], full["M2"])
    _require_parity(ablation.canonical_parity_scores(all_scores), ref70["strong_all_row_parity"],
                    "PR70.all_rows")
    strict_mask, qa = ablation.strict_mask_exact_horse_race(
        raw, future, sqlite, gate["two_event_anchor_horses"])
    _require_parity(qa, ref70["strict_source_qa"], "PR70.strict_qa")
    strict = future.loc[strict_mask].reset_index(drop=True)
    full = {k: v[strict_mask] for k, v in full.items()}
    evaluation = evaluation.loc[np.asarray(strict_mask)].reset_index(drop=True)
    support = evaluation[channels.SUPPORT_COLUMNS]
    del raw, future
    for label, panel, pred in _periods(strict, full):
        legacy = {name: pred[name] for name in ablation.FEATURES}
        for reference, actual, name in (
            (ref70, ablation.summarize_period(panel, legacy), "PR70"),
            (ref72, channels.summarize_period(panel, pred, support.loc[panel.index]), "PR72"),
        ):
            expected = reference[label] if label == "pooled" else reference["by_year"][label]
            _require_parity(actual, expected, f"{name}.{label}")
    train_blocks, evaluation_block = equal._prepare_blocks(old, strict, train, evaluation)
    true_losses = equal._draw_losses(train, labels, horses, evaluation, strict.y,
                                     train_blocks, evaluation_block)
    # Before running ANY new null model, reproduce the exact 32-draw original
    # side-by-side results, all periods, intervals, support and per-seed values.
    for label, panel, pred in _periods(strict, full):
        subset = true_losses if label == "pooled" else {k: v[:, panel.index] for k, v in true_losses.items()}
        reference = ref73[label] if label == "pooled" else ref73["by_year"][label]
        actual = equal.summarize_period(panel, pred, subset, support.loc[panel.index],
                                        pd.Series(evaluation_block.k, index=strict.index).loc[panel.index])
        _require_parity(actual, reference, f"PR73.{label}")
    false_train, false_eval = _control_blocks(old, strict, train_blocks, evaluation_block)
    del old
    false_losses = _control_losses(train, labels, horses, evaluation, strict.y, false_train, false_eval)
    del train, evaluation, false_train, false_eval, train_blocks, evaluation_block
    results = {}
    for label, panel, pred in _periods(strict, full):
        subset = true_losses if label == "pooled" else {k: v[:, panel.index] for k, v in true_losses.items()}
        pseudo = false_losses if label == "pooled" else false_losses[:, panel.index]
        reference = ref73[label] if label == "pooled" else ref73["by_year"][label]
        results[label] = summarize_period(panel, pred, subset, pseudo, reference)
    return {
        "status": "POSTHOC_STRICT_UNRELATED_PEER_NEGATIVE_CONTROL",
        "source_A_sha256": ablation.SOURCE_SHA, "source_B_sha256": ablation.SQLITE_SHA,
        "pr70_reference_sha256": REFERENCE_SHA, "pr72_reference_sha256": equal.PARENT_REFERENCE_SHA,
        "pr73_reference_sha256": PR73_SHA256, "seeds": list(equal.SEEDS),
        "training_years": list(ablation.TRAIN_YEARS), "evaluation_cutoff_year": 2022,
        "parent_exclusion": "sire OR dam shared; exclude focal and missing historical parent identifiers",
        "placebo_choice": "global hash random ranking plus focal hash circular offset",
        "parity": {"status": "OK", "tolerance": ATOL,
                   "pr70_all_rows_and_strict": True, "pr70_and_pr72_all_periods": True,
                   "pr73_all_periods_including_32_draws": True,
                   "same_k_and_original_count_covariates": True},
        "pooled": results.pop("pooled"), "by_year": results,
        "uncertainty_settings": {"primary": list(PRIMARY), "comparisons": COMPARISONS,
                                 "bootstrap_draws": channels.DRAWS, "seed": channels.SEED,
                                 "min_recorded_parent_groups": channels.MIN_CLUSTERS},
        "scope": {"historical_outcomes_already_inspected": True,
                  "fixed_draw_conditioned_evaluation_intervals": True,
                  "pseudo_peers_matched_on_history_age_trainer_and_cohort": False,
                  "no_common_sire_or_dam_means_genetically_unrelated": False,
                  "genetic_causation_maternal_effect_heritability_or_fitness_identified": False,
                  "official_registry_publication_times_or_source_redistribution_rights_verified": False,
                  "raw_records_horse_parent_ids_or_predictions_exported": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--sqlite", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.archive, args.sqlite)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n",
                           encoding="utf-8")
    print(result["status"])


if __name__ == "__main__":
    main()
