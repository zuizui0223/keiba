#!/usr/bin/env python3
"""Post-hoc 2022 information-selection contrast: horse x date and sire sensitivity.

Compare recorded 2022 MG-vs-M2 squared-rank-error difference among horses
WITH versus WITHOUT a 2024 record in the same strict source-B collection.
Reproduces the frozen 2022 model, cohort and previous point estimates first.
A later source record is not biological survival, retirement or fitness.

This deliberately reports only population aggregates; private source records,
official horse identifiers, parent IDs and individual predictions stay in CI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_24_dependency_sensitivity import (
    _cluster_variance, _interval,
)

STATUS = "POSTHOC_2022_FUTURE_OBSERVATION_HORSE_DAY_SIRE_INFO_STRATIFIED_NOT_CAUSAL"
BINS = ("0-3", "4-7", "8-15", "16+")
CRIT95 = 1.959963984540054
CRIT2 = 2.241402727604947  # 2-sided Bonferroni alpha .05 / 2 estimands
EXPECTED = {
    "n2022": 12755,
    "present2024": 5163,
    "absent2024": 7592,
    "mean_all": 0.00004799390375970815,
    "mean_present": -0.00002946697610885394,
    "mean_absent": 0.00010067179137316787,
    "contrast": -0.0001301387674820218,
    "composition": -0.00003182718071070432,
    "within": -0.0000983115867713175,
}


def _validated_2022_panel(panel: pd.DataFrame) -> pd.DataFrame:
    required = {"horse", "race", "day", "gain", "own_bin", "sire_id"}
    if not required.issubset(panel.columns) or len(panel) == 0:
        raise ValueError("HOLD_2022_OBSERVATION_REQUIRED_COLUMNS")
    d = panel.loc[:, ["horse", "race", "day", "gain", "own_bin", "sire_id"]].copy()
    for col in ("horse", "race", "own_bin"):
        if d[col].isna().any():
            raise ValueError("HOLD_2022_OBSERVATION_MISSING_" + col)
        d[col] = d[col].astype(str)
        if d[col].str.strip().eq("").any() or d[col].isin(("nan", "None")).any():
            raise ValueError("HOLD_2022_OBSERVATION_INVALID_" + col)
    if not d.own_bin.isin(BINS).all():
        raise ValueError("HOLD_2022_OBSERVATION_UNKNOWN_HISTORICAL_BIN")
    d["day"] = pd.to_datetime(d.day, errors="coerce")
    d["gain"] = pd.to_numeric(d.gain, errors="coerce")
    if (d.day.isna().any() or not d.day.dt.year.eq(2022).all()
            or not np.isfinite(d.gain.to_numpy(float)).all()
            or d.gain.abs().gt(1.000000001).any()):
        raise ValueError("HOLD_2022_OBSERVATION_BAD_DATE_OR_SIGNED_MSE")
    if d.duplicated(["race", "horse"]).any():
        raise ValueError("HOLD_2022_OBSERVATION_DUPLICATED_HORSE_RACE")
    if d.groupby("race", observed=True).day.nunique().max() != 1:
        raise ValueError("HOLD_2022_OBSERVATION_RACE_MULTIPLE_DAYS")
    d["sire_id"] = d.sire_id.fillna("").astype(str)
    d.loc[d.sire_id.isin(("nan", "None", "NULL", "0")), "sire_id"] = ""
    if d.groupby("horse", observed=True).own_bin.nunique().max() != 1:
        raise ValueError("HOLD_2022_OBSERVATION_HISTORICAL_BIN_CONFLICT")
    if d.groupby("horse", observed=True).sire_id.nunique().max() != 1:
        raise ValueError("HOLD_2022_OBSERVATION_SIRE_ID_CONFLICT")
    return d


def _inference(rows: pd.DataFrame, field: str, point: float, *,
               min_days: int, min_horses: int) -> dict:
    p = rows.loc[:, ["horse", "day", field]].rename(columns={field: "q"})
    nh, vh = _cluster_variance(p, ["horse"])
    nd, vd = _cluster_variance(p, ["day"])
    nhi, vhi = _cluster_variance(p, ["horse", "day"])
    if not (np.isfinite(vh) and np.isfinite(vd) and np.isfinite(vhi)):
        raise ValueError("HOLD_2022_OBSERVATION_NONFINITE_SANDWICH_COMPONENT")
    if abs(float(p.q.sum())) > 1e-10:
        raise ValueError("HOLD_2022_OBSERVATION_UNCENTERED_SCORE")
    info = {
        "point_MSE_gain_present_minus_absent": float(point),
        "horse_clusters": nh,
        "calendar_day_clusters": nd,
        "horse_day_intersections": nhi,
        "horse_CR0_se": float(np.sqrt(max(0.0, vh))),
        "horse_day_sandwich_formula": "V_horse + V_calendar_day - V_horse_x_calendar_day",
        "linearization_conditions_on_observed_future_groups_and_2022_bin_counts": True,
    }
    if nh < min_horses or nd < min_days or nhi < min_horses:
        info["two_way_status"] = "HOLD_CLUSTER_SUPPORT"
        return info
    var = vh + vd - vhi
    info["two_way_CR0_variance"] = float(var)
    if not np.isfinite(var) or var <= 1e-24:
        info["two_way_status"] = "HOLD_NONPOSITIVE_SANDWICH_VARIANCE"
        return info
    se = float(np.sqrt(var))
    info.update({
        "two_way_status": "POSTHOC_HORSE_BY_CALENDAR_DAY_CR0_SENSITIVITY",
        "two_way_CR0_se": se,
        "two_way_normal_95pct_sensitivity_interval": _interval(point, se, CRIT95),
        "bonferroni_two_estimands_simultaneous_95pct_interval": _interval(point, se, CRIT2),
        "two_way_interval_contains_zero": bool(abs(point) <= CRIT95 * se),
        "two_estimands_bonferroni_contains_zero": bool(abs(point) <= CRIT2 * se),
    })
    return info


def _sire_bootstrap(horse: pd.DataFrame, bin_weights: dict[str, float], *,
                    draws: int, seed: int, min_sires: int,
                    min_bin_horses: int) -> dict:
    g = horse.copy()
    g["sire_cluster"] = np.where(
        g.sire_id.eq(""),
        "UNKNOWN_SIRE_SINGLETON:" + g.horse,
        "KNOWN_SOURCE_A_SIRE:" + g.sire_id
    )
    n_sires = int(g.sire_cluster.nunique())
    out = {
        "status": "POSTHOC_SIRE_CLUSTER_SOURCE_A_NOT_GENETIC_CAUSATION",
        "recorded_sire_plus_missing_singleton_clusters": n_sires,
        "missing_sire_horses_as_separate_singletons": int(g.sire_id.eq("").sum()),
        "largest_observed_sire_cluster_horses": int(g.sire_cluster.value_counts().max()),
        "source_A_sire_records_are_not_complete_pedigree_A_or_genomic_G": True,
        "unstratified_whole_sire_clusters_resampled": True,
        "fixed_target_2022_historical_bin_weights": True,
    }
    if n_sires < min_sires:
        return {**out, "status": "HOLD_TOO_FEW_PATERNAL_CLUSTERS"}
    # One group contributes to BOTH future-record states; never split sibs.
    agg = g.groupby(["sire_cluster", "in2024", "own_bin"], observed=True).mean_gain.agg(
        ["sum", "size"]).reset_index()
    parents = sorted(g.sire_cluster.unique())
    keys = [(b, f) for b in BINS for f in (False, True)]
    ci = {key: idx for idx, key in enumerate(keys)}
    groups = {name: idx for idx, name in enumerate(parents)}
    sizes = np.zeros((n_sires, len(keys)), dtype=float)
    sums = np.zeros_like(sizes)
    for row in agg.itertuples(index=False):
        group = groups[row.sire_cluster]
        column = ci[(row.own_bin, bool(row.in2024))]
        sizes[group, column] = row.size
        sums[group, column] = row.sum
    rng = np.random.default_rng(seed)
    vals = []
    invalid = 0
    for _ in range(draws):
        idx = rng.integers(0, n_sires, size=n_sires)
        n = sizes[idx].sum(axis=0)
        s = sums[idx].sum(axis=0)
        if (n < min_bin_horses).any():
            invalid += 1
            continue
        means = s / n
        nc = n.reshape(len(BINS), 2)
        mc = means.reshape(len(BINS), 2)
        unadjusted = (
            np.sum(s[1::2]) / np.sum(n[1::2])
            - np.sum(s[0::2]) / np.sum(n[0::2])
        )
        adjusted = float(sum(
            bin_weights[b] * (mc[i, 1] - mc[i, 0])
            for i, b in enumerate(BINS)
        ))
        vals.append((unadjusted, adjusted))
    out.update({
        "requested_whole_sire_resamples": draws,
        "invalid_resamples_due_to_missing_bin_support": invalid,
    })
    if len(vals) < .99 * draws:
        return {**out, "status": "HOLD_SIRE_BOOTSTRAP_UNSTABLE_GROUP_BIN_SUPPORT"}
    v = np.asarray(vals, float)
    for i, name in enumerate(("unadjusted", "2022_own_bin_standardized")):
        lo, hi = np.quantile(v[:, i], [.025, .975])
        out[name] = {
            "percentile_95pct_sensitivity_interval": [float(lo), float(hi)],
            "interval_contains_zero": bool(lo <= 0 <= hi),
        }
    return out


def selection_dependency_audit(
    panel_2022: pd.DataFrame, present2024: set[str], *,
    expected: dict | None = None, min_group: int = 30,
    min_days: int = 30, min_sires: int = 30,
    sire_draws: int = 999, seed: int = 20221124,
) -> dict:
    """One fixed retrospective cohort, with unadjusted and history-adjusted gaps."""
    d = _validated_2022_panel(panel_2022)
    if (min_group < 2 or min_days < 2 or min_sires < 2
            or sire_draws < 30):
        raise ValueError("HOLD_2022_OBSERVATION_INVALID_SUPPORT_GATE")
    observed_set = set(str(x) for x in present2024)
    horse = d.groupby("horse", observed=True, sort=False).agg(
        own_bin=("own_bin", "first"), sire_id=("sire_id", "first"),
        mean_gain=("gain", "mean"), starts=("gain", "size")
    ).reset_index()
    horse["in2024"] = horse.horse.isin(observed_set)
    n1 = int(horse.in2024.sum())
    n0 = len(horse) - n1
    base = {
        "status": STATUS,
        "2022_horses": int(len(horse)),
        "2022_starts": int(len(d)),
        "with_2024_observed_record": n1,
        "without_2024_observed_record": n0,
        "2022_observation_only_no_2024_outcome_values": True,
        "future_group_2024_known_only_retrospectively": True,
        "not_retirement_mortality_breeding_fitness_or_genetic_selection": True,
        "no_private_individual_horse_race_sire_date_or_prediction_rows_exported": True,
    }
    if min(n1, n0) < min_group:
        return {**base, "status": "HOLD_FUTURE_OBSERVATION_GROUP_SUPPORT"}
    m1 = float(horse.loc[horse.in2024, "mean_gain"].mean())
    m0 = float(horse.loc[~horse.in2024, "mean_gain"].mean())
    all_mean = float(horse.mean_gain.mean())
    delta = m1 - m0
    if expected:
        for key, computed in (
            ("n2022", len(horse)), ("present2024", n1), ("absent2024", n0),
            ("mean_all", all_mean), ("mean_present", m1),
            ("mean_absent", m0), ("contrast", delta)
        ):
            if abs(computed - expected[key]) > (0 if key in (
                    "n2022", "present2024", "absent2024") else 1e-10):
                raise ValueError("HOLD_PREVIOUS_SOURCE_LOCKED_SELECTION_RESULT_DRIFT_" + key)
    # Fixed target: all 2022 horses, not the later-selected 2024 subset.
    counts = horse.groupby(["own_bin", "in2024"], observed=True).mean_gain.agg(
        ["size", "mean"]).reset_index()
    groups = {}
    for b in BINS:
        group = {}
        for flag in (False, True):
            matching = counts[(counts.own_bin == b) & (counts.in2024 == flag)]
            if len(matching) != 1:
                return {**base, "status": "HOLD_MISSING_ONE_OF_FOUR_HISTORICAL_BINS"}
            v = matching.iloc[0]
            group[flag] = {"n": int(v["size"]), "mean": float(v["mean"])}
            if group[flag]["n"] < min_group:
                return {**base, "status": "HOLD_HISTORICAL_BIN_GROUP_SUPPORT"}
        groups[b] = group
    target = {
        b: float(sum(groups[b][z]["n"] for z in (False, True)) / len(horse))
        for b in BINS
    }
    standardized = float(sum(
        target[b] * (groups[b][True]["mean"] - groups[b][False]["mean"])
        for b in BINS
    ))
    composition = float(sum(
        (groups[b][True]["n"]/n1 - groups[b][False]["n"]/n0)
        * groups[b][False]["mean"]
        for b in BINS
    ))
    within = float(sum(
        (groups[b][True]["n"]/n1)
        * (groups[b][True]["mean"] - groups[b][False]["mean"])
        for b in BINS
    ))
    if abs((composition+within)-delta) > 1e-12:
        raise ValueError("HOLD_2022_OBSERVATION_BIN_DECOMPOSITION_NOT_EXACT")
    if expected and (
        abs(composition-expected["composition"]) > 1e-10
        or abs(within-expected["within"]) > 1e-10
    ):
        raise ValueError("HOLD_PREVIOUS_SOURCE_LOCKED_FOUR_BIN_DECOMP_DRIFT")
    expanded = d.merge(
        horse[["horse", "in2024", "starts"]], on="horse", how="left",
        validate="many_to_one"
    )
    if len(expanded) != len(d) or expanded.in2024.isna().any():
        raise ValueError("HOLD_2022_OBSERVATION_HORSE_JOIN_DRIFT")
    weights = 1.0 / expanded.starts.to_numpy(float)
    gflag = expanded.in2024.to_numpy(bool)
    yy = expanded.gain.to_numpy(float)
    q0 = np.where(
        gflag,
        (yy - m1) * weights / n1,
        -(yy - m0) * weights / n0
    )
    q1 = np.empty(len(expanded), dtype=float)
    for b in BINS:
        mask = expanded.own_bin.eq(b).to_numpy(bool)
        for flag in (False, True):
            ix = mask & (gflag == flag)
            ng = groups[b][flag]["n"]
            mg = groups[b][flag]["mean"]
            sign = 1.0 if flag else -1.0
            q1[ix] = sign * target[b] * (yy[ix] - mg) * weights[ix] / ng
    expanded["q_unadjusted"] = q0
    expanded["q_own_bin_standardized"] = q1
    if abs(float(q0.sum())) > 1e-10 or abs(float(q1.sum())) > 1e-10:
        raise ValueError("HOLD_2022_OBSERVATION_INFLUENCE_SUM_NOT_ZERO")
    boot = _sire_bootstrap(
        horse, target, draws=sire_draws, seed=seed,
        min_sires=min_sires, min_bin_horses=max(2, min_group//10)
    )
    return {
        **base,
        "2022_recorded_horses_model_MSE_gain_mean_all": all_mean,
        "2022_model_gain_with_2024_record": m1,
        "2022_model_gain_without_2024_record": m0,
        "MG_vs_always_M2_positive_means_MG_better": True,
        "unadjusted_future_observed_minus_unobserved": delta,
        "2022_historical_own_count_bin_standardized_gap": standardized,
        "standardized_to_all_2022_horses_not_future_selected_group": True,
        "four_2021_history_bin_composition_component": composition,
        "within_2021_history_bin_component_at_future_observed_shares": within,
        "composition_plus_within_equals_unadjusted_exact": True,
        "four_bin_horse_support": {
            b: {
                "2022_horses_with_later_record": groups[b][True]["n"],
                "2022_horses_without_later_record": groups[b][False]["n"],
                "all_2022_horse_target_weight": target[b]
            } for b in BINS
        },
        "unadjusted_horse_by_2022_day": _inference(
            expanded, "q_unadjusted", delta,
            min_days=min_days, min_horses=min_group
        ),
        "historical_bin_standardized_horse_by_2022_day": _inference(
            expanded, "q_own_bin_standardized", standardized,
            min_days=min_days, min_horses=min_group
        ),
        "recorded_sire_group_resampling": boot,
        "history_standardization_does_not_identify_causal_selection": True,
        "horse_day_and_sire_sensitivities_are_separate_not_a_joint_three_way_CI": True,
        "two_retrospectively_selected_estimands_bonferroni_cannot_correct_all_exploration": True,
    }


def analyze(archive: Path, sqlite: Path) -> dict:
    from ecology_japan_2022_24_gate_shift_decomposition import (
        load_sources, predictions_stronger_old_history,
        strict_mask_exact_horse_race, fixed_sourceA_context,
        select_rule_with_2022_only, gate_mask, switch_prediction,
        year_fixed_comparison, EXPECTED_YEAR_SCORES,
        PREVIOUS_RULE, SOURCE_A_SHA, SQLITE_SHA, STRICT_ROWS, STRICT_HORSES
    )
    raw, old, f, _, gate, _ = load_sources(archive, sqlite)
    no_kin, kin, _, _ = predictions_stronger_old_history(raw, old, f)
    mask, qa = strict_mask_exact_horse_race(raw, f, sqlite,
                                           gate["two_event_anchor_horses"])
    t = f.loc[mask].reset_index(drop=True)
    if (len(t) != STRICT_ROWS or t.horse.nunique() != STRICT_HORSES
            or qa["strict_races"] != 35333):
        raise ValueError("HOLD_2022_OBSERVATION_SOURCE_COHORT_CHANGED")
    no_kin, kin = np.asarray(no_kin, float)[mask], np.asarray(kin, float)[mask]
    ctx, _ = fixed_sourceA_context(old, t)
    is22 = t.year.eq(2022).to_numpy()
    rule, chosen = select_rule_with_2022_only(
        t.loc[is22].reset_index(drop=True),
        ctx.loc[is22].reset_index(drop=True), no_kin[is22], kin[is22]
    )
    if chosen["selected_rule_name"] != PREVIOUS_RULE:
        raise ValueError("HOLD_2022_OBSERVATION_GATE_RULE_CHANGED")
    for yr in (2022, 2023, 2024):
        flags = t.year.eq(yr).to_numpy()
        part = t.loc[flags].reset_index(drop=True)
        applied = gate_mask(ctx.loc[flags].reset_index(drop=True), rule)
        scores = year_fixed_comparison(
            part, no_kin[flags], kin[flags], applied, with_ci=False
        )
        original = EXPECTED_YEAR_SCORES[str(yr)]
        if scores["starts"] != original["starts"]:
            raise ValueError("HOLD_2022_OBSERVATION_YEAR_STARTS_CHANGED")
        for k, col in (("M0", "RMSE_midpoint"),
                       ("M1", "RMSE_own_M1"),
                       ("M2", "RMSE_always_family_M2"),
                       ("gate", "RMSE_2022_chosen_gate")):
            if abs(scores[col] - original[k]) > 1e-8:
                raise ValueError("HOLD_2022_OBSERVATION_YEAR_SCORE_CHANGED_"+str(yr)+"_"+k)
    p22 = t.loc[is22, ["horse", "race", "day", "sire_id"]].reset_index(drop=True)
    mg22 = switch_prediction(
        no_kin[is22], kin[is22],
        gate_mask(ctx.loc[is22].reset_index(drop=True), rule)
    )
    yy = t.loc[is22, "y"].to_numpy(float)
    p22["gain"] = (yy - kin[is22])**2 - (yy - mg22)**2
    p22["own_bin"] = ctx.loc[is22, "own_record_count_bin"].reset_index(drop=True)
    later = set(t.loc[t.year.eq(2024), "horse"].astype(str))
    result = selection_dependency_audit(p22, later, expected=EXPECTED)
    if (result["status"] != STATUS or result["2022_starts"] != 120381):
        raise ValueError("HOLD_2022_OBSERVATION_LOCKED_SOURCE_DENOMINATOR")
    return {
        **result,
        "source_A_SHA256": SOURCE_A_SHA,
        "source_B_SHA256": SQLITE_SHA,
        "full_strict_horses": STRICT_HORSES,
        "full_strict_starts": STRICT_ROWS,
        "full_strict_races": 35333,
        "2022_chosen_rule_and_2018_21_fixed_model_preserved": True,
        "all_original_year_model_errors_reproduced": True,
        "2024_MG_and_M2_worse_than_unchanged_midpoint_M0": True,
        "official_JRA_studbook_IDs_or_true_known_on_unverified": True,
        "genomic_G_full_pedigree_A_and_real_market_odds_not_linked": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sqlite", type=Path, required=True)
    parser.add_argument("--aggregate-out", type=Path, required=True)
    args = parser.parse_args()
    summary = analyze(args.archive, args.sqlite)
    args.aggregate_out.parent.mkdir(parents=True, exist_ok=True)
    args.aggregate_out.write_text(json.dumps(summary, ensure_ascii=False,
                                allow_nan=False, sort_keys=True, indent=2)+"\n",
                                encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
