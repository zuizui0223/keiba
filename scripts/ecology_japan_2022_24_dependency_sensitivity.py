#!/usr/bin/env python3
"""Dependence sensitivity of source-locked 2022–24 MG vs M2 prediction loss.

The same 4,636 horse x matched context, three-year cohort is kept fixed.
Effects are retrospective, post hoc, and non-causal.  The two-way
horse×calendar-day CR0 inclusion/exclusion is a linearization sensitivity
for the *selected cohort*, not confirmatory inference.  A sire-cluster
bootstrap separately addresses a partially observed paternal grouping.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_24_balanced_three_year import (
    validate_panels, balanced_three_year, STATUS as OLD_STATUS
)

STATUS = "POSTHOC_THREE_YEAR_HORSE_RACE_DAY_SIRE_DEPENDENCE_SENSITIVITY_NOT_CAUSAL"
PAIRS = ((2022, 2023), (2023, 2024), (2022, 2024))
EXPECTED = {
    "2022_to_2023": 0.0000497807024055271,
    "2023_to_2024": -0.0001208239070101967,
    "2022_to_2024": -0.00007104320460466962,
}
MULTIPLICITY_CRITICAL_Z = 2.3939797998185104  # normal quantile 1 - .05/(2*3)


def _family_map(p: dict[int, pd.DataFrame]) -> pd.Series:
    pieces = []
    for year in (2022, 2023, 2024):
        a = p[year]
        if "sire_id" not in a.columns:
            raise ValueError("HOLD_SIRE_SOURCE_A_PARENT_ID_ABSENT")
        z = a.loc[:, ["horse", "sire_id"]].copy()
        z["horse"] = z.horse.astype(str)
        z["sire_id"] = z.sire_id.fillna("").astype(str)
        z.loc[z.sire_id.isin(("nan", "None", "0", "NULL")), "sire_id"] = ""
        pieces.append(z.drop_duplicates())
    s = pd.concat(pieces, ignore_index=True).drop_duplicates()
    if s.groupby("horse", observed=True).sire_id.nunique().max() != 1:
        raise ValueError("HOLD_SOURCE_A_SIRE_CHANGED_WITHIN_HORSE")
    # Unknown sire is not its own biological sire family: retain one per horse.
    s["sire_cluster"] = np.where(
        s.sire_id.eq(""),
        "UNRESOLVED_SINGLETON:" + s.horse,
        "RECORDED_SIRE:" + s.sire_id
    )
    return s.drop_duplicates("horse").set_index("horse").sire_cluster


def _cluster_variance(scores: pd.DataFrame, cols: list[str]) -> tuple[int, float]:
    n = scores.groupby(cols, observed=True, sort=False).q.sum()
    if len(n) < 2:
        return len(n), float("nan")
    return len(n), float((len(n) / (len(n) - 1)) * np.dot(n.to_numpy(float), n.to_numpy(float)))


def _interval(center: float, se: float, z: float) -> list[float]:
    return [float(center-z*se), float(center+z*se)]


def dependency_audit(panels: dict[int, pd.DataFrame], *, min_horses: int = 30,
                     min_days: int = 30, min_sires: int = 30,
                     draws: int = 999, seed: int = 20221123) -> dict:
    """One fixed-cohort estimator, then horse/day, sire and multiplicity tests.

    Keep the old three-year inclusion, horse weights, and all denominators.
    Parent-cluster resampling is independent from the horse×date sandwich;
    no unjustified three-way variance formula is attempted.
    """
    p = validate_panels(panels)
    if draws < 30 or min_days < 2 or min_sires < 2 or min_horses < 2:
        raise ValueError("HOLD_DEPENDENCE_MIN_CLUSTER_OR_DRAW_GATE")
    family = _family_map(p)
    counts = {}
    for year in (2022, 2023, 2024):
        c = p[year].groupby(["horse", "stratum"], observed=True).size()
        counts[year] = c.rename("starts_" + str(year)).reset_index()
    cells = counts[2022].merge(counts[2023], on=["horse", "stratum"],
                               how="inner", validate="one_to_one")
    cells = cells.merge(counts[2024], on=["horse", "stratum"],
                        how="inner", validate="one_to_one")
    n_horses = int(cells.horse.nunique())
    if n_horses < min_horses:
        return {"status": "HOLD_DEPENDENCE_BALANCED_HORSE_SUPPORT",
                "balanced_horses": n_horses}
    if not cells.horse.isin(family.index).all():
        raise ValueError("HOLD_MISSING_FROZEN_SIRE_LABEL")
    # Each horse's 2022 context mix is kept identical in 2023 and 2024.
    cells["mix22"] = cells.starts_2022 / cells.groupby(
        "horse", observed=True).starts_2022.transform("sum")
    obs_list = []
    for year in (2022, 2023, 2024):
        a = p[year].merge(
            cells[["horse", "stratum", "mix22", "starts_" + str(year)]],
            on=["horse", "stratum"], how="inner", validate="many_to_one", sort=False)
        if len(a) != int(cells["starts_" + str(year)].sum()):
            raise ValueError("HOLD_CHANGED_BALANCED_CONTEXT_START_COUNTS")
        if a.duplicated(["race", "horse"]).any():
            raise ValueError("HOLD_DUPLICATE_PRIVATE_RACE_HORSE")
        a["year"] = year
        a["weight"] = a.mix22 / (a["starts_" + str(year)] * n_horses)
        a["sire_cluster"] = a.horse.map(family)
        if a.sire_cluster.isna().any():
            raise ValueError("HOLD_NO_SIRE_CLUSTER_FOR_MATCHED_HORSE")
        obs_list.append(a[["horse", "day", "race", "stratum", "year",
                           "gain", "weight", "sire_cluster"]])
    obs = pd.concat(obs_list, ignore_index=True)
    if obs.groupby("race", observed=True).day.nunique().max() != 1:
        raise ValueError("HOLD_RACE_MULTIPLE_CALENDAR_DAYS")
    # In a fixed horse-equal population each year carries exactly unit weight.
    year_w = obs.groupby("year").weight.sum()
    if any(abs(float(year_w[y]) - 1.0) > 1e-10 for y in (2022, 2023, 2024)):
        raise ValueError("HOLD_BALANCED_WEIGHT_SUM_NOT_ONE")
    sire_by_horse = obs[["horse", "sire_cluster"]].drop_duplicates()
    if sire_by_horse.horse.duplicated().any():
        raise ValueError("HOLD_DUPLICATE_HORSE_SIRE_CLUSTER")
    family_counts = sire_by_horse.sire_cluster.value_counts()
    unknown_count = int(sire_by_horse.sire_cluster.str.startswith(
        "UNRESOLVED_SINGLETON:").sum())
    results = {}
    for i, (first, later) in enumerate(PAIRS):
        key = f"{first}_to_{later}"
        d = obs.loc[obs.year.isin((first, later))].copy()
        d["signed_weighted_gain"] = np.where(
            d.year.eq(later), d.weight*d.gain, -d.weight*d.gain)
        estimate = float(d.signed_weighted_gain.sum())
        if abs(estimate-EXPECTED[key]) > 1e-10 and n_horses == 4636:
            raise ValueError("HOLD_LOCKED_THREE_YEAR_NUMERIC_SCORE_DRIFT_" + key)
        # Estimating-equation score centered so EACH horse contributes
        # (horse_delta - global mean_delta) / N. The centering mass for
        # each horse is the positive later-year row weight, summing to 1/N.
        d["q"] = d.signed_weighted_gain - np.where(
            d.year.eq(later), estimate*d.weight, 0.)
        if abs(float(d.q.sum())) > 1e-10:
            raise ValueError("HOLD_TWO_WAY_HORSE_DAY_SCORE_NOT_CENTERED")
        nh, vh = _cluster_variance(d, ["horse"])
        nd, vd = _cluster_variance(d, ["day"])
        nhd, vhd = _cluster_variance(d, ["horse", "day"])
        g = d.groupby("horse", observed=True).signed_weighted_gain.sum()
        # The horse-only CR0 sandwich must agree with the sample SE of the
        # fixed-cohort paired horse differences.
        expected_h = float((n_horses/(n_horses-1))*np.dot(
            (g-g.mean()).to_numpy(float), (g-g.mean()).to_numpy(float)))
        if not np.isclose(vh, expected_h, rtol=1e-8, atol=1e-16):
            raise ValueError("HOLD_HORSE_CLUSTER_INFLUENCE_PARITY")
        check = {
            "matched_horses": nh,
            "matched_calendar_days": nd,
            "horse_x_day_intersections": nhd,
            "point_change_MSE_MG_vs_M2": estimate,
            "positive_means_MG_over_always_M2": True,
            "horse_CR0_se": float(np.sqrt(vh)),
            "horse_CR0_normal_95pct_sensitivity_interval":
                _interval(estimate, float(np.sqrt(vh)), 1.959963984540054),
            "horse_day_two_way_formula": "V_horse + V_calendar_day - V_horse_x_calendar_day",
            "two_way_CGM_sensitivity_only_not_an_independent_prospective_test": True,
        }
        if nd < min_days or nh < min_horses or nhd < min_horses:
            check["two_way_status"] = "HOLD_TOO_FEW_DEPENDENCE_CLUSTERS"
        else:
            var = vh + vd - vhd
            check["day_only_CR0_se"] = float(np.sqrt(vd))
            check["two_way_raw_variance"] = float(var)
            if var <= 1e-24 or not np.isfinite(var):
                check["two_way_status"] = "HOLD_NONPOSITIVE_TWO_WAY_SANDWICH_VARIANCE"
            else:
                se = float(np.sqrt(var))
                check.update({
                    "two_way_status": "POSTHOC_TWO_WAY_HORSE_AND_CALENDAR_DAY_SANDWICH",
                    "two_way_horse_date_CR0_se": se,
                    "two_way_normal_95pct_sensitivity_interval":
                        _interval(estimate, se, 1.959963984540054),
                    "bonferroni_3contrasts_normal_familywise_95pct_interval":
                        _interval(estimate, se, MULTIPLICITY_CRITICAL_Z),
                    "two_way_95pct_includes_zero": bool(abs(estimate)<=1.959963984540054*se),
                    "bonferroni_familywise_95pct_includes_zero": bool(
                        abs(estimate) <= MULTIPLICITY_CRITICAL_Z*se)
                })
        horse_gain = (g*n_horses).rename("horse_delta").to_frame()
        horse_gain["sire"] = horse_gain.index.map(family)
        if horse_gain.sire.isna().any():
            raise ValueError("HOLD_SIRE_JOIN_AFTER_FIXED_HORSE_ESTIMATOR")
        cs = horse_gain.groupby("sire", observed=True).horse_delta.agg(
            ["size", "sum"])
        n_families = len(cs)
        check.update({
            "sire_clusters_recorded_plus_unresolved_singletons": n_families,
            "unresolved_sire_horses_as_individual_singletons": unknown_count,
            "largest_observed_paternal_group_horses": int(cs["size"].max()),
        })
        if n_families < min_sires:
            check["sire_cluster_bootstrap_status"] = "HOLD_TOO_FEW_SIRE_CLUSTERS"
        else:
            rng = np.random.default_rng(seed+i)
            sizes = cs["size"].to_numpy(int)
            totals = cs["sum"].to_numpy(float)
            reps = np.empty(draws, float)
            for b in range(draws):
                selected = rng.integers(0, n_families, size=n_families)
                reps[b] = float(totals[selected].sum()/sizes[selected].sum())
            check.update({
                "sire_cluster_bootstrap_status": "POSTHOC_RECORDED_SIRE_CLUSTER_WITH_UNKNOWN_SINGLETONS",
                "sire_cluster_ratio_bootstrap_draws": draws,
                "sire_cluster_95pct_percentile_sensitivity_interval": [
                    float(v) for v in np.quantile(reps,[.025,.975])],
                "sire_cluster_interval_includes_zero": bool(
                    np.quantile(reps,.025) <= 0 <= np.quantile(reps,.975)),
            })
        results[key] = check
    if abs(sum(results[k]["point_change_MSE_MG_vs_M2"]
               for k in ("2022_to_2023", "2023_to_2024")) -
           results["2022_to_2024"]["point_change_MSE_MG_vs_M2"]) > 1e-12:
        raise ValueError("HOLD_3YEAR_TELESCOPING_CHANGED")
    return {
        "status": STATUS,
        "balanced_horses": n_horses,
        "balanced_context_cells": len(cells),
        "race_starts_by_year": {str(y):int((obs.year==y).sum())
                               for y in (2022,2023,2024)},
        "full_three_year_old_differences_preserved": True,
        "three_previously_examined_contrasts_bonferroni_corrected": True,
        "known_sire_cluster_cannot_substitute_genomic_G_or_complete_pedigree_A": True,
        "all_2022_2024_outcomes_already_inspected_POSTHOC": True,
        "no_sire_horse_day_race_or_individual_effects_exported": True,
        "results": results,
    }


def analyze(archive: Path, sqlite: Path) -> dict:
    from ecology_japan_2022_24_gate_shift_decomposition import (
        load_sources, predictions_stronger_old_history, strict_mask_exact_horse_race,
        fixed_sourceA_context, select_rule_with_2022_only, gate_mask,
        switch_prediction, year_fixed_comparison, EXPECTED_YEAR_SCORES,
        PREVIOUS_RULE, SOURCE_A_SHA, SQLITE_SHA, STRICT_ROWS, STRICT_HORSES
    )
    raw, old, f, _, gate, _ = load_sources(archive, sqlite)
    model1, model2, _, _ = predictions_stronger_old_history(raw, old, f)
    mask, qa = strict_mask_exact_horse_race(
        raw, f, sqlite, gate["two_event_anchor_horses"])
    t = f.loc[mask].reset_index(drop=True)
    if len(t)!=STRICT_ROWS or t.horse.nunique()!=STRICT_HORSES or qa["strict_races"]!=35333:
        raise ValueError("HOLD_PRIOR_STRICT_SOURCE_SCOPE_CHANGED")
    m1, m2 = np.asarray(model1)[mask], np.asarray(model2)[mask]
    ctx,_ = fixed_sourceA_context(old, t)
    iy22 = t.year.eq(2022).to_numpy()
    rule,choice = select_rule_with_2022_only(
        t.loc[iy22].reset_index(drop=True),
        ctx.loc[iy22].reset_index(drop=True),m1[iy22],m2[iy22])
    if choice["selected_rule_name"]!=PREVIOUS_RULE:
        raise ValueError("HOLD_FROZEN_2022_GATE_DRIFT")
    panels = {}
    for year in (2022, 2023, 2024):
        flag = t.year.eq(year).to_numpy()
        yy = t.loc[flag].reset_index(drop=True)
        cc = ctx.loc[flag].reset_index(drop=True)
        choose = gate_mask(cc, rule)
        mg = switch_prediction(m1[flag],m2[flag],choose)
        score=year_fixed_comparison(yy,m1[flag],m2[flag],choose,with_ci=False)
        for k,col in (("M0","RMSE_midpoint"),("M1","RMSE_own_M1"),
                      ("M2","RMSE_always_family_M2"),("gate","RMSE_2022_chosen_gate")):
            if abs(score[col]-EXPECTED_YEAR_SCORES[str(year)][k])>1e-8:
                raise ValueError("HOLD_PRIOR_YEAR_SCORE_PARITY_"+str(year)+"_"+k)
        if not {"horse","race","day","stratum","sire_id","y"}.issubset(yy.columns):
            raise ValueError("HOLD_SOURCE_A_SIRE_OR_OUTCOME_ABSENT")
        z = yy.loc[:,["horse","race","day","stratum","sire_id"]].copy()
        z["gain"]=(yy.y.to_numpy(float)-m2[flag])**2 - (
            yy.y.to_numpy(float)-mg)**2
        z["own_bin"]=cc.own_record_count_bin.reset_index(drop=True)
        panels[year]=z
    parent=balanced_three_year(panels)
    if parent["status"]!=OLD_STATUS:
        raise ValueError("HOLD_BALANCED_PREVIOUS_THREE_YEAR_GATE")
    if parent["balanced_horses_same_context_all_three_years"]!=4636:
        raise ValueError("HOLD_PRIOR_4636_BALANCED_HORSE_IDS")
    result=dependency_audit(panels)
    if result["balanced_horses"]!=4636 or result["balanced_context_cells"]!=5895:
        raise ValueError("HOLD_PRIOR_MATCHED_CONTEXT_COUNT_CHANGED")
    return {
        **result,
        "source_A_SHA256": SOURCE_A_SHA,
        "source_B_SHA256": SQLITE_SHA,
        "source_strict_starts": STRICT_ROWS,
        "source_strict_horses": STRICT_HORSES,
        "source_strict_races": 35333,
        "prior_anonymous_balanced_three_year_verified": True,
        "model_coefficients_old_M1_M2_2022_MG_frozen": True,
        "year_2024_baseline_M0_still_beats_M2_and_MG": True,
        "no_official_studbook_ID_verification_or_animal_fitness": True,
        "inference_does_not_establish_adaptive_genetics_or_market_learning": True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--sqlite",type=Path,required=True)
    p.add_argument("--aggregate-out",type=Path,required=True)
    a=p.parse_args()
    j=analyze(a.archive,a.sqlite)
    a.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
    a.aggregate_out.write_text(json.dumps(j,ensure_ascii=False,indent=2,
                       sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(j,ensure_ascii=False,allow_nan=False),flush=True)


if __name__=="__main__":
    main()
