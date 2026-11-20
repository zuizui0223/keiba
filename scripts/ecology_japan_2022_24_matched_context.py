#!/usr/bin/env python3
"""Post-hoc matched-horse, matched-context audit of 2022 -> 2024 kin-gate drift.

Never re-fit previously frozen 2018-21 model, 2022 gate, or source identities.
Common support is observed same horse x (surface, 400-m distance band) in both
years. All evidence is retrospective and cannot prove selection, aging or genes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

STATUS = "POSTHOC_2022_24_MATCHED_HORSE_COMMON_CONTEXT_NOT_CAUSAL"
REQUIRED = ("horse", "race", "day", "stratum", "gain")


def _validated_panel(panel: pd.DataFrame, label: str) -> pd.DataFrame:
    if any(k not in panel.columns for k in REQUIRED) or not len(panel):
        raise ValueError("HOLD_MISSING_MATCHED_CONTEXT_PANEL_" + label)
    d = panel.loc[:, REQUIRED].copy()
    for key in ("horse", "race", "stratum"):
        d[key] = d[key].astype(str)
        if d[key].str.strip().eq("").any() or d[key].isin(("nan", "None")).any():
            raise ValueError("HOLD_INVALID_MATCHED_CONTEXT_ID_" + key)
    d["day"] = pd.to_datetime(d["day"], errors="coerce")
    d["gain"] = pd.to_numeric(d["gain"], errors="coerce")
    if d.day.isna().any() or not np.isfinite(d.gain.to_numpy(float)).all():
        raise ValueError("HOLD_NONFINITE_MATCHED_CONTEXT_DATE_OR_GAIN")
    if d.duplicated(["horse", "race"]).any():
        raise ValueError("HOLD_DUPLICATED_HORSE_RACE_SCORE")
    if (d.gain.abs() > 1.0 + 1e-10).any():
        raise ValueError("HOLD_OUT_OF_RANGE_NORMALIZED_RANK_LOSS_GAIN")
    return d


def matched_context_audit(first: pd.DataFrame, later: pd.DataFrame,
                          *, min_matched_horses: int = 30,
                          draws: int = 399, seed: int = 20221120) -> dict:
    """Horse-equal MSE-gain contrast with each horse's 2022 stratum weights.

    Native-mix contrast is also separated exactly into 2022-reference
    context composition and common-stratum conditional error change.
    Neither change is causal; overlapping horses/contexts are post-selected.
    """
    a = _validated_panel(first, "2022")
    b = _validated_panel(later, "2024")
    if draws < 10 or min_matched_horses < 2:
        raise ValueError("HOLD_INVALID_REPRODUCIBILITY_GATES")
    ha, hb = set(a.horse), set(b.horse)
    common_horses = ha & hb

    def collapse(d):
        return d.groupby(["horse", "stratum"], observed=True, sort=False).agg(
            mean_gain=("gain", "mean"), starts=("gain", "size")
        ).reset_index()

    cells = collapse(a).merge(
        collapse(b), on=["horse", "stratum"], how="inner",
        suffixes=("_22", "_24"), validate="one_to_one")
    n = int(cells.horse.nunique())
    core = {
        "status": STATUS,
        "source_years": [2022, 2024],
        "strata": "turf_or_dirt_and_400m_distance_band_as_in_frozen_source_B",
        "2022_observed_horses": len(ha),
        "2024_observed_horses": len(hb),
        "same_candidate_horses_both_years_all_contexts": len(common_horses),
        "matched_horses_with_at_least_one_common_context": n,
        "horse_context_pairs_observed_both_years": len(cells),
        "fraction_of_2022_to_2024_matched_horses_with_common_context": (
            n / len(common_horses) if common_horses else 0.),
        "common_context_2022_starts": int(cells.starts_22.sum()) if n else 0,
        "common_context_2024_starts": int(cells.starts_24.sum()) if n else 0,
        "common_context_2022_starts_fraction_of_all": (
            int(cells.starts_22.sum()) / len(a) if n else 0.),
        "common_context_2024_starts_fraction_of_all": (
            int(cells.starts_24.sum()) / len(b) if n else 0.),
        "2022_gate_and_2024_gate_not_reestimated": True,
        "context_defined_from_observed_race_not_causal_experimental_assignment": True,
        "cohort_selected_using_future_year_and_context_overlap": True,
        "same_coarse_context_NOT_same_rivals_jockey_trainer_going_or_age": True,
        "paired_horse_resampling_NOT_race_day_two_way_cluster_CI": True,
        "no_individual_horse_ID_race_ID_day_or_gain_exported": True,
    }
    if n < min_matched_horses:
        return {
            **core,
            "status": "HOLD_MATCHED_HORSE_COMMON_CONTEXT_INSUFFICIENT_SUPPORT",
            "min_matched_horses": min_matched_horses,
        }

    cells["weight_22"] = cells.starts_22 / cells.groupby("horse").starts_22.transform("sum")
    cells["weight_24"] = cells.starts_24 / cells.groupby("horse").starts_24.transform("sum")
    cells["first_component"] = cells.weight_22 * cells.mean_gain_22
    cells["later_same_2022_mix"] = cells.weight_22 * cells.mean_gain_24
    cells["later_native_mix"] = cells.weight_24 * cells.mean_gain_24
    cells["context_mix_component"] = (cells.weight_24-cells.weight_22) * cells.mean_gain_22
    cells["within_context_component"] = cells.weight_24 * (cells.mean_gain_24-cells.mean_gain_22)
    horse = cells.groupby("horse", observed=True, sort=False)[[
        "first_component", "later_same_2022_mix", "later_native_mix",
        "context_mix_component", "within_context_component"]].sum()
    baseline = horse.first_component.to_numpy(float)
    standardized = horse.later_same_2022_mix.to_numpy(float)
    later_native = horse.later_native_mix.to_numpy(float)
    mix = horse.context_mix_component.to_numpy(float)
    within = horse.within_context_component.to_numpy(float)
    paired = standardized - baseline
    native = later_native - baseline
    if not np.allclose(native, mix+within, rtol=0, atol=1e-12):
        raise ValueError("HOLD_MATCHED_CONTEXT_EXACT_IDENTITY_FAILED")
    if not np.isfinite(paired).all():
        raise ValueError("HOLD_NONFINITE_MATCHED_CONTEXT_PAIRED_GAIN")
    rng = np.random.default_rng(seed)
    reps = np.empty(draws, dtype=float)
    for i in range(draws):
        reps[i] = paired[rng.integers(0, n, n)].mean()

    return {
        **core,
        "status": STATUS,
        "2022_common_context_horse_equal_mean_gain_gate_over_M2": float(baseline.mean()),
        "2024_common_context_2022_mix_standardized_mean_gain_gate_over_M2": float(standardized.mean()),
        "2024_common_context_native_mix_mean_gain_gate_over_M2": float(later_native.mean()),
        "paired_same_horse_same_context_2022_mix_standardized_year_change": float(paired.mean()),
        "paired_horse_oneway_399_resampling_95pct": [float(x) for x in np.quantile(reps, [.025, .975])],
        "common_context_native_mix_year_change": float(native.mean()),
        "2022_reference_within_horse_context_mix_component": float(mix.mean()),
        "within_common_context_component_at_2024_mix": float(within.mean()),
        "native_mix_decomposition_exact": bool(
            np.isclose(native.mean(), mix.mean()+within.mean(), rtol=0, atol=1e-12)),
        "horses_with_multiple_common_contexts": int((cells.groupby("horse").size()>1).sum()),
        "not_independent_confirmation_of_earlier_2024_selection_year_failure": True,
    }


def analyze(archive: Path, sqlite: Path) -> dict:
    from ecology_japan_2022_24_gate_shift_decomposition import (
        load_sources, predictions_stronger_old_history, strict_mask_exact_horse_race,
        fixed_sourceA_context, select_rule_with_2022_only, gate_mask,
        switch_prediction, year_fixed_comparison, EXPECTED_YEAR_SCORES,
        PREVIOUS_RULE, SOURCE_A_SHA, SQLITE_SHA, STRICT_ROWS, STRICT_HORSES,
    )
    raw, old, f, _, gate, _ = load_sources(archive, sqlite)
    p1_all, p2_all, _, _ = predictions_stronger_old_history(raw, old, f)
    strict, source_qa = strict_mask_exact_horse_race(
        raw, f, sqlite, gate["two_event_anchor_horses"])
    t = f.loc[strict].reset_index(drop=True)
    if len(t) != STRICT_ROWS or t.horse.nunique() != STRICT_HORSES or source_qa["strict_races"] != 35333:
        raise ValueError("HOLD_STRICT_ORIGINAL_SOURCE_COHORT_PARITY")
    if not {"horse", "race", "day", "stratum", "y", "year"}.issubset(t.columns):
        raise ValueError("HOLD_ORIGINAL_STRATUM_OR_SCORE_COLUMN_MISSING")
    p1 = np.asarray(p1_all, float)[strict]
    p2 = np.asarray(p2_all, float)[strict]
    ctx, _ = fixed_sourceA_context(old, t)
    is22 = t.year.eq(2022).to_numpy()
    rule, choice = select_rule_with_2022_only(
        t.loc[is22].reset_index(drop=True), ctx.loc[is22].reset_index(drop=True),
        p1[is22], p2[is22])
    if choice["selected_rule_name"] != PREVIOUS_RULE:
        raise ValueError("HOLD_FROZEN_GATE_RULE_CHANGED")
    by_year = {}
    for year in (2022, 2024):
        iy = t.year.eq(year).to_numpy()
        yy = t.loc[iy].reset_index(drop=True)
        cy = ctx.loc[iy].reset_index(drop=True)
        apply_gate = gate_mask(cy, rule)
        pg = switch_prediction(p1[iy], p2[iy], apply_gate)
        score = year_fixed_comparison(yy, p1[iy], p2[iy], apply_gate, with_ci=False)
        for key, reference in (("M0", "RMSE_midpoint"), ("M1", "RMSE_own_M1"),
                               ("M2", "RMSE_always_family_M2"),
                               ("gate", "RMSE_2022_chosen_gate")):
            if abs(score[reference] - EXPECTED_YEAR_SCORES[str(year)][key]) > 1e-8:
                raise ValueError("HOLD_PREVIOUSLY_LOCKED_YEAR_SCORE_CHANGED")
        if score["starts"] != EXPECTED_YEAR_SCORES[str(year)]["starts"]:
            raise ValueError("HOLD_PREVIOUSLY_LOCKED_YEAR_STARTS_CHANGED")
        outcome = yy.y.to_numpy(float)
        if not (np.isfinite(outcome).all() and np.isfinite(pg).all() and np.isfinite(p2[iy]).all()):
            raise ValueError("HOLD_NONFINITE_RANK_SCORE")
        if any(np.any((v < 0) | (v > 1)) for v in (outcome, pg, p2[iy])):
            raise ValueError("HOLD_OUT_OF_BOUNDS_RANK_SCORE")
        d = (outcome - p2[iy])**2 - (outcome-pg)**2
        panel = yy.loc[:, ["horse", "race", "day", "stratum"]].copy()
        panel["gain"] = d
        by_year[year] = panel
    result = matched_context_audit(by_year[2022], by_year[2024])
    if result["same_candidate_horses_both_years_all_contexts"] != 5163:
        raise ValueError("HOLD_MATCHED_2022_2024_5163_HORSES_CHANGED")
    return {
        **result,
        "source_A_SHA256": SOURCE_A_SHA,
        "source_B_SHA256": SQLITE_SHA,
        "original_strict_2022_24_starts": STRICT_ROWS,
        "original_strict_2022_24_horses": STRICT_HORSES,
        "original_strict_2022_24_races": 35333,
        "source_B_2022_2024_starts": {str(k):len(v) for k,v in by_year.items()},
        "frozen_pre2022_trained_model_and_2022_selected_rule_verified": True,
        "no_future_2024_scores_used_for_model_fitting_or_rule_selection": True,
        "2024_results_previously_inspected_NOT_external_holdout": True,
        "no_pedigree_A_genomic_G_MSTN_or_market_timing_link": True,
        "no_real_animal_fitness_survival_or_causal_age_measurement": True,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--sqlite", type=Path, required=True)
    p.add_argument("--aggregate-out", type=Path, required=True)
    a = p.parse_args()
    output = analyze(a.archive, a.sqlite)
    a.aggregate_out.parent.mkdir(parents=True, exist_ok=True)
    a.aggregate_out.write_text(json.dumps(output, ensure_ascii=False, indent=2,
                                         sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
