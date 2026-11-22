#!/usr/bin/env python3
"""Paired, equal-horse comparison of recorded sire and dam performance features."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

import ecology_japan_2022_24_family_feature_ablation as ablation
from ecology_japan_2022_24_sire_signal_concentration import (
    ATOL, REFERENCE, REFERENCE_SHA, _periods, _require_parity,
)

PARENTS = ("sire", "dam")
SUPPORT_COLUMNS = [f"{parent}_relative_count" for parent in PARENTS]
FEATURES = {
    **ablation.FEATURES,
    "MS": tuple(c for c in ablation.STRONG_KIN if c != "dam_kin_history"),
    "MD": tuple(c for c in ablation.STRONG_KIN if c != "sire_kin_history"),
}
PRIMARY = ("sire_given_dam", "dam_given_sire", "sire_minus_dam")
COMPARISONS = len(PRIMARY) * (1 + len(ablation.TEST_YEARS))
DRAWS, SEED, MIN_CLUSTERS = 999, 20261122, 30


def fit_factorial(features, y, horses):
    models = ablation.fit_factorial(features, y, horses)
    for name in ("MS", "MD"):
        models[name] = ablation.fit_weighted_ridge(features, y, horses, FEATURES[name],
                                                  alpha=ablation.RIDGE_ALPHA)
    return models


def predict_factorial(models, features):
    predictions = ablation.predict_factorial(models, features)
    for name in ("MS", "MD"):
        predictions[name] = ablation._vector(ablation.predict_weighted_ridge(models[name], features),
                                             len(features), bounded=True)
    return predictions


def _losses(y, predictions):
    if set(predictions) != set(FEATURES):
        raise ValueError("HOLD_INCOMPLETE_PARENT_CHANNEL_MODELS")
    target = ablation._vector(y, len(y), bounded=True)
    return {k: (target - ablation._vector(v, len(y), bounded=True)) ** 2
            for k, v in predictions.items()}


def _decompose(loss):
    terms = {"combined_gain": loss["MC"] - loss["M2"],
             "sire_alone": loss["MC"] - loss["MS"], "dam_alone": loss["MC"] - loss["MD"],
             "sire_given_dam": loss["MD"] - loss["M2"], "dam_given_sire": loss["MS"] - loss["M2"],
             "sire_minus_dam": loss["MD"] - loss["MS"]}
    for side, other in (("sire", "dam"), ("dam", "sire")):
        path = terms[f"{side}_alone"] + terms[f"{other}_given_{side}"]
        if not np.allclose(path, terms["combined_gain"], rtol=0, atol=1e-14):
            raise ValueError("HOLD_PAIRED_PARENT_LOSS_PATH")
    if not np.allclose(terms["sire_given_dam"] - terms["dam_given_sire"], terms["sire_minus_dam"],
                       rtol=0, atol=1e-14):
        raise ValueError("HOLD_PAIRED_PARENT_DIFFERENCE")
    return terms


def paired_loss_terms(y, predictions):
    return _decompose(_losses(y, predictions))


def _period_panel(panel):
    if not isinstance(panel, pd.DataFrame) or not panel.columns.is_unique or "dam_id" not in panel:
        raise ValueError("HOLD_INCOMPLETE_PERIOD_PANEL")
    p = ablation._period_panel(panel)
    p["dam_id"] = ablation.clean_id(panel.dam_id).to_numpy()
    if p.groupby("horse").dam_id.nunique().max() != 1:
        raise ValueError("HOLD_CONFLICTING_DAM_ID")
    return p


def _settings(draws, seed, min_clusters):
    if any(isinstance(v, bool) or not isinstance(v, (int, np.integer))
           for v in (draws, seed, min_clusters)) or draws < 30 or seed < 0 or min_clusters < 2:
        raise ValueError("HOLD_INVALID_BOOTSTRAP_SETTINGS")


def _coverage(p):
    horses = p.drop_duplicates("horse")
    coverage = {}
    for parent in PARENTS:
        ids = horses[f"{parent}_id"]
        known = ids[ids.ne("")]
        sizes = known.value_counts()
        coverage[parent] = {"known_parent_horses": len(known), "unknown_parent_horses": len(ids) - len(known),
                            "recorded_parent_groups": len(sizes),
                            "recorded_singleton_groups": int(sizes.eq(1).sum())}
    return coverage


def _parent_bootstrap(p, parent, coverage, draws, seed, min_clusters):
    # PR70 namespaces singleton horses and resamples sums and sizes of whole groups.
    # Its gate counts all groups, so add unknown singletons to the recorded-group minimum.
    info = coverage[parent]
    minimum = min_clusters + info["unknown_parent_horses"]
    groups = p if parent == "sire" else p.assign(sire_id=p.dam_id)
    result = ablation._sire_bootstrap(groups, draws, seed, minimum)
    result["unknown_parent_singleton_horses"] = result.pop("unknown_sire_singleton_horses")
    result["recorded_parent_groups"] = info["recorded_parent_groups"]
    if result["status"] == "HOLD_TOO_FEW_CLUSTERS":
        result["status"] = "HOLD_TOO_FEW_RECORDED_PARENT_GROUPS"
    return result


def parent_bootstrap(panel, gain, parent, draws=DRAWS, seed=SEED, min_clusters=MIN_CLUSTERS):
    _settings(draws, seed, min_clusters)
    if parent not in PARENTS:
        raise ValueError("HOLD_INVALID_PARENT_SIDE")
    p = _period_panel(panel)
    p["gain"] = ablation._vector(gain, len(p))
    return _parent_bootstrap(p, parent, _coverage(p), draws, seed, min_clusters)


def _uncertainty(p, gain, coverage, draws, seed, min_clusters):
    legacy = ablation._uncertainty(p, gain, draws, seed, min_clusters)
    center = legacy["mean_MSE_gain"]
    two_way = legacy["two_way"]
    if two_way["status"] == "OK":
        del two_way["CI95_bonferroni_8"]
        two_way["CI95_bonferroni_12"] = ablation._interval(
            center, two_way["SE"], NormalDist().inv_cdf(1 - .025 / COMPARISONS))
    scored = p.assign(gain=gain)
    return {"mean_MSE_gain": center, "horses": legacy["horses"], "two_way": two_way,
            **{f"{side}_bootstrap": _parent_bootstrap(scored, side, coverage, draws, seed, min_clusters)
               for side in PARENTS}}


def paired_uncertainty(panel, gain, draws=DRAWS, seed=SEED, min_clusters=MIN_CLUSTERS):
    _settings(draws, seed, min_clusters)
    p = _period_panel(panel)
    return _uncertainty(p, ablation._vector(gain, len(p)), _coverage(p), draws, seed, min_clusters)


def _support_summary(p, support, coverage, panel_index):
    if (not isinstance(support, pd.DataFrame) or not support.columns.is_unique
            or not set(SUPPORT_COLUMNS).issubset(support) or not support.index.equals(panel_index)):
        raise ValueError("HOLD_INCOMPLETE_PARENT_SUPPORT")
    weights = p.weight.to_numpy()

    def cell(mask):
        return {"starts": int(mask.sum()), "horse_equal_share": float(weights[mask].sum())}

    present, by_parent = {}, {}
    for parent, column in zip(PARENTS, SUPPORT_COLUMNS):
        counts = ablation._vector(support[column], len(p))
        if (counts < 0).any() or (np.floor(counts) != counts).any():
            raise ValueError("HOLD_INVALID_PEER_COUNT")
        found = counts > 0
        if (found & p[f"{parent}_id"].eq("").to_numpy()).any():
            raise ValueError("HOLD_UNKNOWN_PARENT_WITH_PEERS")
        present[parent] = found
        by_parent[parent] = {"mean_peer_count": float(np.average(counts, weights=weights)),
                             "bins": {"0": cell(~found), "1": cell(counts == 1),
                                      "2-4": cell((counts >= 2) & (counts <= 4)), "5+": cell(counts >= 5)}}
    sire, dam = present["sire"], present["dam"]
    return {"joint_support": {"neither": cell(~sire & ~dam), "sire_only": cell(sire & ~dam),
                              "dam_only": cell(~sire & dam), "both": cell(sire & dam)},
            "by_parent": by_parent, "parent_coverage": coverage}


def support_summary(panel, support):
    p = _period_panel(panel)
    return _support_summary(p, support, _coverage(p), panel.index)


def summarize_period(panel, predictions, support, draws=DRAWS, min_clusters=MIN_CLUSTERS):
    _settings(draws, SEED, min_clusters)
    p = _period_panel(panel)
    coverage = _coverage(p)
    support_stats = _support_summary(p, support, coverage, panel.index)
    losses = _losses(p.y, predictions)
    terms = _decompose(losses)
    losses["M0"] = (p.y - .5) ** 2
    risks = {k: float(np.average(loss, weights=p.weight)) for k, loss in losses.items()}
    return {"starts": len(p), "horses": int(p.horse.nunique()), "races": int(p.race.nunique()),
            "models": {k: {"MSE": v, "RMSE": float(np.sqrt(v))} for k, v in risks.items()},
            "loss_decomposition_MSE": {k: float(np.average(term, weights=p.weight)) for k, term in terms.items()},
            "primary_uncertainty": {k: _uncertainty(p, terms[k], coverage, draws, SEED, min_clusters)
                                    for k in PRIMARY},
            "support": support_stats}


def _historical_predictions(raw, old, future):
    meta = ablation.old_metadata(raw)
    blocks, labels, horses = [], [], []
    for year in ablation.TRAIN_YEARS:
        targets = old.loc[old.year.eq(year)]
        blocks.append(ablation._strong_features(old.loc[old.year.lt(year)], targets, meta))
        labels.append(targets.y.to_numpy(float))
        horses.append(targets.horse.astype(str).to_numpy())
    train = pd.concat(blocks, ignore_index=True)
    del blocks, targets
    models = fit_factorial(train, np.concatenate(labels), np.concatenate(horses))
    del train, labels, horses
    evaluation = ablation._strong_features(old, future, meta)
    return predict_factorial(models, evaluation), evaluation[SUPPORT_COLUMNS].copy()


def analyze(archive: Path, db: Path):
    ref_bytes = REFERENCE.read_bytes()
    if hashlib.sha256(ref_bytes).hexdigest() != REFERENCE_SHA:
        raise ValueError("HOLD_CHANGED_PR70_REFERENCE")
    reference = json.loads(ref_bytes)
    raw, old, future, _, gate, _ = ablation.load_sources(archive, db)
    if not old.year.lt(2022).all() or set(future.year.unique()) != set(ablation.TEST_YEARS):
        raise ValueError("HOLD_SOURCE_YEAR_SCOPE")
    predictions, support = _historical_predictions(raw, old, future)
    scores = ablation._scores(future, predictions["M1"], predictions["M2"])
    _require_parity(ablation.canonical_parity_scores(scores), reference["strong_all_row_parity"],
                    "strong_all_row_parity")
    mask, qa = ablation.strict_mask_exact_horse_race(raw, future, db, gate["two_event_anchor_horses"])
    _require_parity(qa, reference["strict_source_qa"], "strict_source_qa")
    strict = future.loc[mask].reset_index(drop=True)
    support = support.loc[np.asarray(mask)].reset_index(drop=True)
    predictions = {k: v[mask] for k, v in predictions.items()}
    del raw, old, future
    expected = {"pooled": reference["pooled"], **reference["by_year"]}
    original = {k: predictions[k] for k in ablation.FEATURES}
    for label, panel, pred in _periods(strict, original):
        _require_parity(ablation.summarize_period(panel, pred), expected[label], label)

    results = {label: summarize_period(panel, pred, support.loc[panel.index])
               for label, panel, pred in _periods(strict, predictions)}
    return {"status": "POSTHOC_STRICT_PARENT_PERFORMANCE_CHANNELS",
            "source_A_sha256": ablation.SOURCE_SHA, "source_B_sha256": ablation.SQLITE_SHA,
            "reference_sha256": REFERENCE_SHA, "training_years": list(ablation.TRAIN_YEARS),
            "ridge_alpha": ablation.RIDGE_ALPHA,
            "parity": {"status": "OK", "absolute_tolerance": ATOL, "strong_all_row_scores": True,
                       "strict_source_qa": True, "all_pr70_pooled_and_yearly_statistics": True},
            "pooled": results.pop("pooled"), "by_year": results,
            "uncertainty_settings": {"primary_contrasts": list(PRIMARY), "comparisons": COMPARISONS,
                                     "min_clusters": MIN_CLUSTERS, "min_recorded_parent_groups": MIN_CLUSTERS,
                                     "bootstrap_draws": DRAWS, "seed": SEED},
            "scope": {"retrospective_not_an_independent_prospective_test": True,
                      "performance_features_contain_count_dependent_shrinkage": True,
                      "parent_bootstrap_intervals_are_separate_pointwise_sensitivities": True,
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
