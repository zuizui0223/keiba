#!/usr/bin/env python3
"""2022 horse information model gain across observed 2023/2024 source-record paths.

Only a retrospective, source-conditional observational design: the four future
states are *source record presence*, never survival, retirement, migration or
fitness. The 2022 MG gate was selected using outcomes already inspected.
The original horse IDs, model coefficients, source hashes, MSE and year scores
are frozen. Individual horses, sires, races and predictions never leave CI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ecology_japan_2022_observation_selection_dependence import (
    BINS, EXPECTED, STATUS as PARENT_STATUS,
    _validated_2022_panel, selection_dependency_audit,
)

STATUS = "POSTHOC_OBSERVED_2022_TO_2023_2024_SOURCE_PATH_AND_OPPORTUNITY_NOT_CAUSAL"
STATES = ("neither_2023_nor_2024", "2023_only", "2024_only", "both_2023_and_2024")
EXPECTED_STATES = {
    "neither_2023_nor_2024": 4035, "2023_only": 3557,
    "2024_only": 61, "both_2023_and_2024": 5102,
}


def _state(h23: bool, h24: bool) -> str:
    if h23 and h24:
        return "both_2023_and_2024"
    if h23:
        return "2023_only"
    if h24:
        return "2024_only"
    return "neither_2023_nor_2024"


def _opportunity_standardization(horse: pd.DataFrame, mask: np.ndarray,
                                 dims: tuple[str, ...],
                                 *, min_group: int = 30) -> dict:
    """Full 2022 source-record group-composition standardization, no outcomes refit."""
    selected = horse.loc[mask]
    if len(selected) == 0:
        return {"status": "HOLD_EMPTY_2022_OBSERVED_COHORT"}
    groups = selected.groupby(list(dims)+["observed2024"],
                              observed=True, dropna=False).gain.agg(
                                  ["size", "mean"]).reset_index()
    support = selected.groupby(list(dims), observed=True, dropna=False).size()
    bad = 0
    details = []
    estimated = 0.0
    for key, group_total in support.items():
        key = key if isinstance(key, tuple) else (key,)
        sel = np.ones(len(groups), dtype=bool)
        for dim, val in zip(dims, key):
            sel &= groups[dim].eq(val).to_numpy()
        cell = groups.loc[sel]
        if len(cell) != 2 or set(cell.observed2024.astype(bool)) != {False,True}:
            bad += 1
            continue
        entries = cell.set_index("observed2024")
        small = int(entries["size"].min())
        if small < min_group:
            bad += 1
            continue
        estimated += (float(group_total)/len(selected) *
                      float(entries.loc[True,"mean"]-entries.loc[False,"mean"]))
        details.append(small)
    qa = {
        "scope": ("all_2022" if mask.all() else "2022_horses_with_2023_source_record"),
        "history_and_observation_opportunity_dimensions": list(dims),
        "horse_count": int(len(selected)),
        "planned_nonempty_strata": int(len(support)),
        "strata_with_insufficient_or_missing_future_2024_group": int(bad),
        "minimum_future_group_horses_in_eligible_strata": min(details) if details else None,
        "target_standardization_to_all_2022_horses_in_this_scope": True,
        "2022_last_record_and_2022_number_of_starts_are_post_event_observation_proxies": True,
        "no_causal_adjustment_or_future_prediction": True,
    }
    if bad:
        return {**qa,"status":"HOLD_OPPORTUNITY_STANDARDIZATION_SPARSE_STRATA"}
    return {
        **qa, "status":"POSTHOC_ALL_2022_OPPORTUNITY_STANDARDIZED_ASSOCIATION",
        "2024_observed_minus_unobserved_MG_vs_M2_gain":float(estimated),
    }


def analyze_paths(p22: pd.DataFrame, observed_2023: set[str],
                  observed_2024: set[str], *, expected_states=None,
                  sire_draws: int = 999, source_lock: bool = False,
                  all_valid_2024_source_ids: set[str] | None = None) -> dict:
    """All population assertions enforced before any candidate inference."""
    p = _validated_2022_panel(p22)
    ids23 = set(str(x) for x in observed_2023)
    ids24 = set(str(x) for x in observed_2024)
    h = p.groupby("horse",observed=True,sort=False).agg(
        gain=("gain","mean"), own_bin=("own_bin","first"),
        n2022=("race","size"), final_2022_day=("day","max")
    ).reset_index()
    h["observed2023"] = h.horse.isin(ids23)
    h["observed2024"] = h.horse.isin(ids24)
    h["path"] = [_state(a,b) for a,b in zip(h.observed2023,h.observed2024)]
    h["last_2022_half"] = np.where(
        h.final_2022_day.dt.month.le(6), "Jan-Jun", "Jul-Dec")
    h["recorded_2022_starts_bin"] = np.where(h.n2022.le(4), "1-4", "5+")
    counts = h.path.value_counts()
    states = {}
    for state in STATES:
        n = int(counts.get(state,0))
        states[state] = {"2022_horses":n,
                         "2022_horse_equal_mean_gain_MG_vs_M2": (
                             float(h.loc[h.path.eq(state),"gain"].mean()) if n else None)}
    n = len(h)
    n23 = int(h.observed2023.sum())
    n24 = int(h.observed2024.sum())
    if expected_states is not None:
        if {k:v["2022_horses"] for k,v in states.items()} != expected_states:
            raise ValueError("HOLD_ORIGINAL_2022_2023_2024_HORSE_MEMBERSHIP_CHANGED")
    if source_lock:
        if n != 12755 or n24 != 5163 or n23 != 8659:
            raise ValueError("HOLD_PRIOR_2022_FUTURE_OBSERVATION_MEMBERSHIP_DRIFT")
        if int(states["both_2023_and_2024"]["2022_horses"]) != 5102:
            raise ValueError("HOLD_LOCKED_THREE_YEAR_ID_OVERLAP_DRIFT")
    mean1 = float(h.loc[h.observed2024,"gain"].mean())
    mean0 = float(h.loc[~h.observed2024,"gain"].mean())
    if source_lock and abs((mean1-mean0)-EXPECTED["contrast"]) > 1e-10:
        raise ValueError("HOLD_PREVIOUSLY_REPRODUCED_2022_MG_M2_GAP_CHANGED")
    # Exactly partition the previously observed 2024 gap by whether a 2023
    # source record was present. This is arithmetic, not mediation/causality.
    comp = 0.0
    within = 0.0
    for flag23 in (False,True):
        sub = h.loc[h.observed2023.eq(flag23)]
        is24 = sub.observed2024
        if not is24.any() or is24.all():
            raise ValueError("HOLD_2023_PATH_LACKS_2024_GROUP_OVERLAP")
        n_11 = int((h.observed2023.eq(flag23) & h.observed2024).sum())
        n_10 = int((h.observed2023.eq(flag23) & ~h.observed2024).sum())
        base = float(sub.loc[~is24,"gain"].mean())
        new = float(sub.loc[is24,"gain"].mean())
        w_present = n_11/n24
        w_absent = n_10/(n-n24)
        comp += (w_present-w_absent)*base
        within += w_present*(new-base)
    if abs(comp+within-(mean1-mean0))>1e-12:
        raise ValueError("HOLD_2023_PATH_EXACT_TWO_TERM_IDENTITY")
    # Three comparisons on the same 2022 records, with no 2023/2024 outcomes
    # used in the score. Independent sire/day sensitivities reused unchanged.
    full2023 = selection_dependency_audit(
        p, ids23, sire_draws=sire_draws)
    full2024 = selection_dependency_audit(
        p, ids24, expected=EXPECTED if source_lock else None, sire_draws=sire_draws)
    subset23 = p.loc[p.horse.isin(ids23)].reset_index(drop=True)
    conditional = selection_dependency_audit(
        subset23, ids24, sire_draws=sire_draws)
    if full2024["status"] != PARENT_STATUS:
        raise ValueError("HOLD_2024_PRIOR_DEPENDENCE_PARENT_STATUS_CHANGED")
    if full2023["with_2024_observed_record"] != n23:
        raise ValueError("HOLD_2023_COHORT_RECOUNT_CHANGED")
    if (conditional["2022_horses"] != n23 or
            conditional["with_2024_observed_record"] != states["both_2023_and_2024"]["2022_horses"]):
        raise ValueError("HOLD_2024_CONDITIONAL_ON_2023_ID_COHORT_CHANGED")
    out = {
        "status": STATUS,
        "same_source_2022_horses": n,
        "original_2022_starts": len(p),
        "observed_2023_count": n23,
        "observed_2024_count": n24,
        "four_source_record_paths":states,
        "2024_gap_ref_2023_status_composition_MSE_component":float(comp),
        "2024_gap_within_2023_status_MSE_component":float(within),
        "components_sum_to_prior_2024_gap":True,
        "2024_gap": mean1-mean0,
        "2022_score_never_uses_2023_2024_rank_outcomes":True,
        "year_2023_source_record_not_survival_or_studbook_status":True,
        "path_2024_only_small_group_is_descriptive":True,
        "year_2023_record_observation_sensitivity":full2023,
        "year_2024_record_observation_sensitivity":full2024,
        "year_2024_observation_conditioned_on_2023_record":conditional,
        "2022_observation_opportunity_sensitivity": {},
        "not_independent_prospective_confirmation":True,
        "not_causal_survival_retirement_aging_or_breeding_selection":True,
        "no_private_horse_parent_race_day_or_model_prediction_rows_exported":True,
    }
    if all_valid_2024_source_ids is not None:
        valid = set(str(x) for x in all_valid_2024_source_ids)
        if ids24 - valid:
            raise ValueError("HOLD_STRICT_2024_IDS_NOT_IN_BROADER_VALID_SOURCE")
        broad = h.horse.isin(valid)
        stages = {
            "strict_2024": h.observed2024.to_numpy(bool),
            "2024_valid_joined_source_but_not_strict": (
                broad.to_numpy(bool) & ~h.observed2024.to_numpy(bool)),
            "no_valid_joined_2024_outcome_in_broader_source": (
                ~broad.to_numpy(bool)),
        }
        detail = {}
        for label, flag in stages.items():
            selected = h.loc[flag]
            detail[label] = {
                "2022_horses":int(flag.sum()),
                "2022_horse_equal_MG_vs_M2_gain": (
                    float(selected.gain.mean()) if len(selected) else None),
            }
        if sum(z["2022_horses"] for z in detail.values()) != n:
            raise ValueError("HOLD_BROADER_SOURCE_2024_COVERAGE_DOES_NOT_PARTITION")
        if detail["strict_2024"]["2022_horses"] != n24:
            raise ValueError("HOLD_STRICT_2024_BROADER_SOURCE_COUNT_DRIFT")
        out["broader_valid_source_vs_strict_2024_record_coverage"] = {
            "status": "POSTHOC_BROADER_JOINED_ELIGIBLE_OUTCOMES_NOT_RAW_SOURCE_ALL_RACES",
            "source_B_parse_validation_and_race_eligibility_still_applies": True,
            "absence_of_valid_record_does_not_certify_no_raw_race_or_retirement": True,
            "three_record_coverage_groups": detail,
            "strict_2024_absent_split_exact": True,
        }
    for label, mask in (("all_2022",np.ones(n,bool)),
                        ("2023_observed_2022",h.observed2023.to_numpy(bool))):
        for dims in (("own_bin","last_2022_half"),
                     ("own_bin","recorded_2022_starts_bin"),
                     ("own_bin","last_2022_half","recorded_2022_starts_bin")):
            name = label+"__"+"__".join(dims)
            out["2022_observation_opportunity_sensitivity"][name] = (
                _opportunity_standardization(h,mask,dims))
    return out


def run(archive: Path, sqlite: Path) -> dict:
    from ecology_japan_2022_24_gate_shift_decomposition import (
        load_sources, predictions_stronger_old_history,
        strict_mask_exact_horse_race, fixed_sourceA_context,
        select_rule_with_2022_only, gate_mask, switch_prediction,
        year_fixed_comparison, EXPECTED_YEAR_SCORES, PREVIOUS_RULE,
        SOURCE_A_SHA, SQLITE_SHA, STRICT_HORSES, STRICT_ROWS,
    )
    raw,old,f,_,gate,_=load_sources(archive,sqlite)
    p1,p2,_,_=predictions_stronger_old_history(raw,old,f)
    mask,sourceqa=strict_mask_exact_horse_race(
        raw,f,sqlite,gate["two_event_anchor_horses"])
    t=f.loc[mask].reset_index(drop=True)
    if (len(t)!=STRICT_ROWS or t.horse.nunique()!=STRICT_HORSES
            or sourceqa["strict_races"]!=35333):
        raise ValueError("HOLD_SOURCE_STRICT_2022_24_COHORT_PARITY")
    p1,p2=np.asarray(p1,float)[mask],np.asarray(p2,float)[mask]
    ctx,_=fixed_sourceA_context(old,t)
    y22=t.year.eq(2022).to_numpy(bool)
    rule,chosen=select_rule_with_2022_only(
        t.loc[y22].reset_index(drop=True),
        ctx.loc[y22].reset_index(drop=True),p1[y22],p2[y22])
    if chosen["selected_rule_name"]!=PREVIOUS_RULE:
        raise ValueError("HOLD_2022_SELECTED_GATE_DRIFT")
    for year in (2022,2023,2024):
        year_idx=t.year.eq(year).to_numpy(bool)
        cur=t.loc[year_idx].reset_index(drop=True)
        flags=gate_mask(ctx.loc[year_idx].reset_index(drop=True),rule)
        score=year_fixed_comparison(cur,p1[year_idx],p2[year_idx],flags,with_ci=False)
        expected=EXPECTED_YEAR_SCORES[str(year)]
        if score["starts"]!=expected["starts"]:
            raise ValueError("HOLD_ORIGINAL_YEAR_SCOPE_DRIFT")
        for k, col in (("M0","RMSE_midpoint"),("M1","RMSE_own_M1"),
                       ("M2","RMSE_always_family_M2"),("gate","RMSE_2022_chosen_gate")):
            if abs(score[col]-expected[k])>1e-8:
                raise ValueError("HOLD_ORIGINAL_YEAR_MODEL_RMSE_DRIFT_"+str(year))
    cur=t.loc[y22,["horse","race","day","sire_id"]].reset_index(drop=True)
    yy=t.loc[y22].y.to_numpy(float)
    mg=switch_prediction(p1[y22],p2[y22],
                         gate_mask(ctx.loc[y22].reset_index(drop=True),rule))
    cur["gain"]=(yy-p2[y22])**2-(yy-mg)**2
    cur["own_bin"]=ctx.loc[y22,"own_record_count_bin"].reset_index(drop=True)
    d=analyze_paths(cur,set(t.loc[t.year.eq(2023)].horse.astype(str)),
                    set(t.loc[t.year.eq(2024)].horse.astype(str)),
                    expected_states=EXPECTED_STATES, source_lock=True,
                    all_valid_2024_source_ids=set(f.loc[f.year.eq(2024)].horse.astype(str)))
    if len(cur)!=120381 or len(t)!=244147:
        raise ValueError("HOLD_UNCHANGED_2022_24_STARTS")
    return {
        **d,
        "source_A_SHA256":SOURCE_A_SHA,
        "source_B_SHA256":SQLITE_SHA,
        "original_strict_horses":STRICT_HORSES,
        "original_strict_starts":STRICT_ROWS,
        "original_strict_races":35333,
        "frozen_2018_21_ridge_2022_gate_and_all_2022_24_year_errors":True,
        "no_official_studbook_or_verified_known_on_time":True,
        "no_genomic_A_G_MSTN_or_time_stamped_odds_link":True,
        "source_A_B_individual_records_not_redistributed":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",type=Path,required=True)
    ap.add_argument("--sqlite",type=Path,required=True)
    ap.add_argument("--aggregate-out",type=Path,required=True)
    a=ap.parse_args()
    z=run(a.archive,a.sqlite)
    a.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
    a.aggregate_out.write_text(json.dumps(z,ensure_ascii=False,sort_keys=True,
                                          allow_nan=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(z,ensure_ascii=False,sort_keys=True,allow_nan=False))


if __name__=="__main__":
    main()
