#!/usr/bin/env python3
"""Post-hoc source-locked 2022-24 balanced horse-context and observation audit.

Three-year balanced: retain (horse, coarse turf/dirt + 400m band) observed in
ALL 2022, 2023, 2024; fix each horse's context weights at 2022 values. Track
signed gate-versus-family MSE advantage (positive favors 2022 gate MG).
Separately compare 2022 error differences for those with/without 2024 source
records. Reappearance is OBSERVED PARTICIPATION, not survival or fitness.
No source individual records leave the CI machine; only anonymous aggregates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_24_matched_context import _validated_panel

STATUS = "POSTHOC_BALANCED_THREE_YEAR_HORSE_CONTEXT_AND_FUTURE_PARTICIPATION_NOT_CAUSAL"
OWN_NAMES = ("0-3", "4-7", "8-15", "16+")


def validate_panels(panels: dict[int, pd.DataFrame]) -> dict[int, pd.DataFrame]:
    if set(panels) != {2022, 2023, 2024}:
        raise ValueError("HOLD_REQUIRED_THREE_LOCKED_YEARS")
    out = {}
    for yr in (2022, 2023, 2024):
        original = panels[yr]
        if "own_bin" not in original.columns:
            raise ValueError("HOLD_SOURCE_A_OWN_INFO_BIN_MISSING")
        z = _validated_panel(original, str(yr))
        if not z.day.dt.year.eq(yr).all():
            raise ValueError("HOLD_INCORRECT_SOURCE_OUTCOME_YEAR")
        z["own_bin"] = original["own_bin"].reset_index(drop=True).astype(str)
        if not z.own_bin.isin(OWN_NAMES).all():
            raise ValueError("HOLD_UNKNOWN_FROZEN_OWN_HISTORY_BIN")
        if z.groupby("horse", observed=True).own_bin.nunique().max() != 1:
            raise ValueError("HOLD_2021_FOCAL_OWN_HISTORY_BIN_NOT_STABLE_WITHIN_YEAR")
        out[yr] = z
    all_bins = pd.concat([p.loc[:, ["horse", "own_bin"]] for p in out.values()])
    if all_bins.groupby("horse", observed=True).own_bin.nunique().max() != 1:
        raise ValueError("HOLD_2021_FOCAL_OWN_HISTORY_BIN_NOT_STABLE_ACROSS_YEARS")
    return out


def _quantile_pair(reps: np.ndarray) -> list[float]:
    return [float(x) for x in np.quantile(reps, [.025, .975])]


def balanced_three_year(panels: dict[int, pd.DataFrame], *,
                        draws: int = 399, min_horses: int = 30,
                        seed: int = 20221121) -> dict:
    """One and the same horse/context sample for all three successive years."""
    p = validate_panels(panels)
    if draws < 10 or min_horses < 2:
        raise ValueError("HOLD_INVALID_SYNTHETIC_GATES")
    by_year = []
    for yr in (2022, 2023, 2024):
        g = p[yr].groupby(["horse", "stratum"], observed=True, sort=False).agg(
            mean_gain=("gain", "mean"), starts=("gain", "size")).reset_index()
        by_year.append(g.rename(columns={
            "mean_gain": "gain_" + str(yr),
            "starts": "starts_" + str(yr),
        }))
    cells = by_year[0].merge(by_year[1], on=["horse", "stratum"],
                             how="inner", validate="one_to_one").merge(
        by_year[2], on=["horse", "stratum"],
        how="inner", validate="one_to_one")
    n = int(cells.horse.nunique())
    common_2022_2024 = set(p[2022].horse) & set(p[2024].horse)
    common_all = set(p[2022].horse) & set(p[2023].horse) & set(p[2024].horse)
    summary = {
        "status": STATUS,
        "years": [2022, 2023, 2024],
        "year_start_counts": {str(y): len(p[y]) for y in p},
        "year_observed_horse_counts": {str(y): int(p[y].horse.nunique()) for y in p},
        "horses_observed_all_three_years_any_context": len(common_all),
        "horses_observed_2022_and_2024_any_context": len(common_2022_2024),
        "balanced_horses_same_context_all_three_years": n,
        "balanced_horse_context_cells": len(cells),
        "balanced_coverage_of_three_year_reappearing_horses": n / len(common_all) if common_all else 0.,
        "balanced_start_counts": {str(y): int(cells["starts_" + str(y)].sum()) for y in p},
        "balanced_start_fractions_all_starts": {
            str(y): float(cells["starts_" + str(y)].sum() / len(p[y])) if n else 0.
            for y in p
        },
        "uses_same_horses_and_same_strata_for_all_three_contrasts": True,
        "horses_only_selected_after_observing_all_three_years": True,
        "subsequent_observation_not_survival_retirement_or_fitness": True,
        "unchanged_2022_context_weights_for_2023_and_2024": True,
        "each_horse_equal_weight": True,
        "no_2024_unobserved_horse_outcomes_imputed": True,
        "source_horse_race_or_individual_gain_values_never_exported": True,
    }
    if n < min_horses:
        return {**summary, "status": "HOLD_BALANCED_THREE_YEAR_COMMON_CONTEXT_SUPPORT"}
    cells["w2022"] = (
        cells.starts_2022 / cells.groupby("horse", observed=True).starts_2022.transform("sum")
    )
    for yr in (2022, 2023, 2024):
        cells["weighted_" + str(yr)] = cells.w2022 * cells["gain_" + str(yr)]
    horse = cells.groupby("horse", observed=True)[[
        "weighted_2022", "weighted_2023", "weighted_2024"]].sum()
    vals = {yr: horse["weighted_" + str(yr)].to_numpy(float)
            for yr in (2022, 2023, 2024)}
    d12 = vals[2023] - vals[2022]
    d23 = vals[2024] - vals[2023]
    d13 = vals[2024] - vals[2022]
    if not np.allclose(d12 + d23, d13, rtol=0, atol=1e-12):
        raise ValueError("HOLD_BALANCED_FIXED_HORSE_CONTEXT_NO_TELESCOPING")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(draws, n))
    boot = {
        "2022_to_2023": _quantile_pair(d12[indices].mean(axis=1)),
        "2023_to_2024": _quantile_pair(d23[indices].mean(axis=1)),
        "2022_to_2024": _quantile_pair(d13[indices].mean(axis=1))
    }
    return {
        **summary,
        "year_gate_over_M2_horse_equal_MSE_difference_at_fixed_2022_mix": {
            str(y): float(vals[y].mean()) for y in vals
        },
        "same_horse_context_year_difference": {
            "2022_to_2023": float(d12.mean()),
            "2023_to_2024": float(d23.mean()),
            "2022_to_2024": float(d13.mean())
        },
        "paired_horse_399_resampling_95pct_sensitivity_intervals": boot,
        "within_horse_first_versus_second_year_difference_sign_reversals_fraction": float(
            np.mean(d12 * d23 < -1e-16)),
        "balanced_2022_to_2024_difference_equals_sum_of_two_steps": True,
        "all_three_years_2023_and_2024_already_inspected_NOT_independent": True,
        "inferences_exclude_context_changes_and_observation_selection": True,
        "horse_only_bootstrap_does_not_model_race_day_dependence": True,
    }


def continuation_selection_2022(panels: dict[int, pd.DataFrame], *,
                                draws: int = 399, min_group: int = 30,
                                seed: int = 20221122) -> dict:
    """2022 horse-equal discrepancy by *future* 2024 observed participation.

    Negative/positive difference indicates descriptive informative sampling
    of a prediction error, not causal dropout, retirement or selective survival.
    """
    p = validate_panels(panels)
    first = p[2022]
    later_ids = set(p[2024].horse.astype(str))
    tab = first.groupby("horse", observed=True, sort=False).agg(
        own_bin=("own_bin", "first"),
        mean_gain=("gain", "mean"),
        starts=("gain", "size"),
        date_count=("day", "nunique")
    ).reset_index()
    tab["in_2024"] = tab.horse.isin(later_ids)
    a = tab.loc[tab.in_2024]
    b = tab.loc[~tab.in_2024]
    out = {
        "status": "POSTHOC_2022_GAIN_VS_2024_OBSERVED_PARTICIPATION_NOT_CAUSAL",
        "2022_horses": int(len(tab)),
        "2022_horses_observed_again_in_2024": int(len(a)),
        "2022_horses_without_2024_record": int(len(b)),
        "fraction_2022_horses_observed_again_in_2024": float(len(a) / len(tab)),
        "2022_observed_participant_set_2024_is_posthoc": True,
        "horse_equal_weight_within_2022_no_conflation_with_start_weight": True,
        "source_2024_records_missing_do_NOT_mean_dead_or_retired": True,
        "no_causal_ability_inference_from_retention": True,
        "no_source_horse_IDs_individual_predictions_or_rows_exported": True
    }
    if min(len(a), len(b)) < min_group:
        return {**out, "status": "HOLD_2024_PARTICIPATION_GROUP_TOO_SMALL"}
    x = a.mean_gain.to_numpy(float)
    y = b.mean_gain.to_numpy(float)
    diff = float(x.mean() - y.mean())
    rng = np.random.default_rng(seed)
    # Resample the two future-defined observed groups separately.
    boots = np.empty(draws)
    for i in range(draws):
        boots[i] = (
            x[rng.integers(0, len(x), len(x))].mean()
            - y[rng.integers(0, len(y), len(y))].mean()
        )
    cells = {}
    standardizable = True
    for binname in OWN_NAMES:
        aa = a.loc[a.own_bin.eq(binname)]
        bb = b.loc[b.own_bin.eq(binname)]
        size_a, size_b = len(aa), len(bb)
        eligible = size_a >= min_group and size_b >= min_group
        cells[binname] = {
            "status": ("POSTHOC_GROUP_OBSERVED" if eligible
                       else "HOLD_INSUFFICIENT_GROUP_SUPPORT"),
            "2022_horses_observed_again_in_2024": size_a,
            "2022_horses_without_2024_record": size_b,
            "fraction_in_this_own_history_bin_observed_again_in_2024": (
                size_a / (size_a + size_b) if size_a + size_b else None),
        }
        if eligible:
            cells[binname].update({
                "2022_mean_MG_advantage_later_participants": float(aa.mean_gain.mean()),
                "2022_mean_MG_advantage_not_observed_again": float(bb.mean_gain.mean()),
                "2022_mean_MG_advantage_selection_contrast": float(
                    aa.mean_gain.mean() - bb.mean_gain.mean()),
                "2022_share_among_future_participants": float(size_a / len(a)),
                "2022_share_among_future_nonparticipants": float(size_b / len(b)),
            })
        else:
            standardizable = False

    result = {
        **out,
        "2022_MG_over_M2_mean_horse_equal_all": float(tab.mean_gain.mean()),
        "2022_MG_over_M2_mean_horse_equal_later_observed": float(x.mean()),
        "2022_MG_over_M2_mean_horse_equal_not_observed_later": float(y.mean()),
        "2022_future_participation_selection_contrast_later_minus_not": diff,
        "horse_group_stratified_399_bootstrap_95pct": _quantile_pair(boots),
        "frozen_pre2022_own_history_bin_4cell_selection": cells,
    }
    if standardizable:
        # Exact twofold descriptive accounting of mean model-gain gap
        # into 2022 OWN-history mix and within-bin gap. Not causal.
        c = list(cells.values())
        comp = sum((v["2022_share_among_future_participants"] -
                    v["2022_share_among_future_nonparticipants"]) *
                   v["2022_mean_MG_advantage_not_observed_again"] for v in c)
        within = sum(v["2022_share_among_future_participants"] *
                     v["2022_mean_MG_advantage_selection_contrast"] for v in c)
        if abs((comp + within) - diff) > 1e-12:
            raise ValueError("HOLD_OBSERVATION_SELECTION_EXACT_BINS")
        result["2022_own_info_bin_composition_component"] = float(comp)
        result["within_2022_own_info_bin_participation_selection_component"] = float(within)
        result["composition_plus_within_exact"] = True
    else:
        result["2022_own_info_bin_full_standardization_status"] = (
            "HOLD_SPARSE_OR_MISSING_2022_OWN_INFO_BIN")
    return result


def analyze(archive: Path, sqlite: Path) -> dict:
    from ecology_japan_2022_24_gate_shift_decomposition import (
        load_sources, predictions_stronger_old_history, strict_mask_exact_horse_race,
        fixed_sourceA_context, select_rule_with_2022_only, gate_mask,
        switch_prediction, year_fixed_comparison, EXPECTED_YEAR_SCORES,
        PREVIOUS_RULE, SOURCE_A_SHA, SQLITE_SHA, STRICT_ROWS, STRICT_HORSES
    )
    raw, old, f, _, gate, _ = load_sources(archive, sqlite)
    no_kin_all, kin_all, _, _ = predictions_stronger_old_history(raw, old, f)
    locked_mask, source_qa = strict_mask_exact_horse_race(
        raw, f, sqlite, gate["two_event_anchor_horses"])
    t = f.loc[locked_mask].reset_index(drop=True)
    if len(t) != STRICT_ROWS or t.horse.nunique() != STRICT_HORSES or source_qa["strict_races"] != 35333:
        raise ValueError("HOLD_ORIGINAL_STRICT_COHORT_DRIFT")
    no_kin = np.asarray(no_kin_all, float)[locked_mask]
    kin = np.asarray(kin_all, float)[locked_mask]
    context, _ = fixed_sourceA_context(old, t)
    flag22 = t.year.eq(2022).to_numpy()
    rule, choice = select_rule_with_2022_only(
        t.loc[flag22].reset_index(drop=True),
        context.loc[flag22].reset_index(drop=True),
        no_kin[flag22], kin[flag22])
    if choice["selected_rule_name"] != PREVIOUS_RULE:
        raise ValueError("HOLD_2022_GATE_RESELECTED")
    panels = {}
    for yr in (2022, 2023, 2024):
        ix = t.year.eq(yr).to_numpy()
        cur = t.loc[ix].reset_index(drop=True)
        historical = context.loc[ix].reset_index(drop=True)
        applied = gate_mask(historical, rule)
        gate_predictions = switch_prediction(no_kin[ix], kin[ix], applied)
        scores = year_fixed_comparison(
            cur, no_kin[ix], kin[ix], applied, with_ci=False)
        expected = EXPECTED_YEAR_SCORES[str(yr)]
        if scores["starts"] != expected["starts"]:
            raise ValueError("HOLD_LOCKED_YEAR_STARTS_DRIFT")
        for name, key in (("M0", "RMSE_midpoint"),
                          ("M1", "RMSE_own_M1"),
                          ("M2", "RMSE_always_family_M2"),
                          ("gate", "RMSE_2022_chosen_gate")):
            if abs(scores[key] - expected[name]) > 1e-8:
                raise ValueError("HOLD_LOCKED_YEAR_MODEL_SCORE_" + str(yr) + "_" + name)
        y = cur.y.to_numpy(float)
        gp = np.asarray(gate_predictions, float)
        pp = kin[ix]
        if not all(np.isfinite(v).all() and ((v >= 0) & (v <= 1)).all()
                   for v in (y, gp, pp)):
            raise ValueError("HOLD_NONFINITE_NORMALIZED_OUTCOME_OR_PREDICTION")
        arr = cur.loc[:, ["horse", "race", "day", "stratum"]].copy()
        arr["gain"] = (y - pp) ** 2 - (y - gp) ** 2
        arr["own_bin"] = historical.own_record_count_bin.reset_index(drop=True)
        panels[yr] = arr
    balanced = balanced_three_year(panels)
    selection = continuation_selection_2022(panels)
    if balanced["horses_observed_2022_and_2024_any_context"] != 5163:
        raise ValueError("HOLD_LOCKED_2022_TO_2024_5163_COHORT_CHANGED")
    if balanced["year_start_counts"] != {"2022":120381,"2023":80939,"2024":42827}:
        raise ValueError("HOLD_2022_2023_2024_ORIGINAL_STARTS_CHANGED")
    return {
        "status": STATUS,
        "source_A_sha256": SOURCE_A_SHA,
        "source_B_sha256": SQLITE_SHA,
        "original_strict_horses": STRICT_HORSES,
        "original_strict_starts": STRICT_ROWS,
        "original_strict_races": 35333,
        "original_frozen_gate_name": choice["selected_rule_name"],
        "frozen_2018_21_model_2022_chosen_rule_and_2022_24_year_scores_preserved": True,
        "three_year_balanced_horse_context": balanced,
        "2022_observation_selection_by_future_2024_presence": selection,
        "all_years_posthoc_inspected_not_confirmatory": True,
        "source_A_B_true_known_on_timestamp_unverified": True,
        "bloodline_A_genome_G_MSTN_market_odd_time_series_not_linked": True,
        "coarse_context_not_equal_full_race_rival_or_individual_biology": True,
        "no_private_individual_source_records_written": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--aggregate-out", type=Path, required=True)
    args = parser.parse_args()
    r = analyze(args.archive, args.sqlite)
    args.aggregate_out.parent.mkdir(parents=True, exist_ok=True)
    args.aggregate_out.write_text(
        json.dumps(r, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8"
    )
    print(json.dumps(r, ensure_ascii=False, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
