#!/usr/bin/env python3
"""Offline Japanese Meisho name / race owner / pedigree time-forward contrast.

NEVER run on publicly copied proprietary racing rows. Requires licensed
horse-race records, genuine stable horse IDs, and pre-race owner snapshots.
Output is anonymous aggregate scored errors, NOT heritability or betting.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
from itertools import product
import json
from pathlib import Path
from statistics import mean

from ecology_pedigree_forward import (
    LAMBDAS, SHRINK_KIN, SHRINK_OWN, asof_pedigree,
    metric, observations, pedigree_rows, read_csv, training_profile, verify_dates,
)

EXTRA = {"horse_name", "owner_id", "owner_known_on"}
PREFIX = "メイショウ"
CHANNELS = ("name", "owner", "kin")


def load_race_asof(path: Path) -> list[dict]:
    measured = observations(path)
    lookup = {}
    for row in read_csv(path, EXTRA):
        key = (row["horse_id"], row["race_id"])
        if key in lookup:
            raise ValueError("HOLD_DUPLICATE_METADATA_ID")
        if not all(row.get(k) for k in EXTRA):
            raise ValueError("HOLD_MISSING_OWNER_OR_NAME_ASOF")
        lookup[key] = row
    for row in measured:
        source = lookup[row["horse"], row["race"]]
        checked_at = date.fromisoformat(source["owner_known_on"])
        if checked_at >= row["day"]:
            raise ValueError("HOLD_OWNER_SOURCE_NOT_KNOWN_BEFORE_RACE_DATE")
        row["owner"] = source["owner_id"]
        row["name"] = source["horse_name"]
        row["meisho"] = source["horse_name"].startswith(PREFIX)
    return measured


def frozen_features(train: list[dict], targets: list[dict], pedigree) -> list[dict]:
    centers, by_horse = training_profile(train)
    peer_rows = defaultdict(list)
    all_seen = {r["horse"] for r in train}
    for r in train:
        if r["context"] in centers:
            peer_rows[(r["context"], r["horse"])].append(r)
    output = []
    for t in targets:
        c, horse = t["context"], t["horse"]
        if c not in centers:
            continue
        own, nown = by_horse.get(c, {}).get(horse, (0.0, 0))
        base = centers[c] + nown / (nown + SHRINK_OWN) * own
        numer = {channel: 0.0 for channel in CHANNELS}
        denom = {channel: 0.0 for channel in CHANNELS}
        support = {channel: 0 for channel in CHANNELS}
        for other, (peer_mean, _) in by_horse.get(c, {}).items():
            if other == horse:
                continue
            history = peer_rows[(c, other)]
            # A horse's historical memberships, not its present-day owner,
            # define prior owner-group evidence.
            channels = {
                "name": ([h["y"] - centers[c] for h in history
                         if t["meisho"] and h["meisho"]], 1.0),
                "owner": ([h["y"] - centers[c] for h in history
                          if h["owner"] == t["owner"]], 1.0),
                "kin": ([h["y"] - centers[c] for h in history],
                        pedigree.relationship(horse, other)),
            }
            for channel, (values, w) in channels.items():
                if not values or w < (0.125 if channel == "kin" else 1.0):
                    continue
                numer[channel] += w * mean(values)
                denom[channel] += w
                support[channel] += 1
        factor = SHRINK_OWN / (nown + SHRINK_OWN)
        output.append({
            "y": t["y"], "horse": horse, "race": t["race"], "base": base,
            "meisho": t["meisho"], "cold": horse not in all_seen,
            **{channel: factor * numer[channel] / (SHRINK_KIN + denom[channel])
               for channel in CHANNELS},
            **{channel + "_exposed": support[channel] > 0 for channel in CHANNELS},
        })
    return output


def mse_rmse(scores: list[dict], weights: tuple[float, float, float]) -> float | None:
    wn, wo, wk = weights
    return metric([
        {**r, "prediction":r["base"] + wn * r["name"] +
         wo * r["owner"] + wk * r["kin"]}
        for r in scores
    ], "prediction")


def choose_weights(inner: list[dict]) -> dict[str, tuple[float, float, float]]:
    options = {
        "M0": [(0.0,0.0,0.0)],
        "M_name": [(v,0.0,0.0) for v in LAMBDAS],
        "M_owner": [(0.0,v,0.0) for v in LAMBDAS],
        "M_kin": [(0.0,0.0,v) for v in LAMBDAS],
        "M_owner_plus_kin": [(0.0,a,b) for a,b in product(LAMBDAS,LAMBDAS)],
    }
    return {
        k: min(candidates, key=lambda w:(mse_rmse(inner,w),w))
        for k,candidates in options.items()
    }


def stats(scores: list[dict], weights: dict) -> dict:
    values = {key:mse_rmse(scores,w) for key,w in weights.items()}
    baseline = values["M0"]
    return {
        "scored_rows": len(scores),
        "unique_horses":len({r["horse"] for r in scores}),
        "same_heldout_rows_all_models":True,
        "equal_horse_weight_RMSE_seconds":values,
        "gain_relative_M0":{
            k:(baseline-v if baseline is not None and v is not None else None)
            for k,v in values.items() if k!="M0"
        },
    }


def analyze(observations_file: Path, pedigree_file: Path, *,
            min_horses: int = 20) -> dict:
    rows = load_race_asof(observations_file)
    parentage = pedigree_rows(pedigree_file)
    inner_cutoff, outer_cutoff = verify_dates(rows)
    early = [r for r in rows if r["day"] < inner_cutoff]
    validation = [r for r in rows if inner_cutoff <= r["day"] < outer_cutoff]
    train = [r for r in rows if r["day"] < outer_cutoff]
    future = [r for r in rows if r["day"] >= outer_cutoff]
    inner = frozen_features(early, validation, asof_pedigree(parentage, inner_cutoff))
    if len({r["horse"] for r in inner}) < max(5, min_horses // 3):
        return {
            "status":"HOLD_INSUFFICIENT_INNER_VALIDATION_HORSES",
            "inner_scored_horses":len({r["horse"] for r in inner}),
            "all_models_on_same_future_rows":False,
            "no_real_horse_kin_claim":True,
        }
    selected = choose_weights(inner)
    outer = frozen_features(train, future, asof_pedigree(parentage, outer_cutoff))
    n_horses = len({r["horse"] for r in outer})
    has_kin = len({r["horse"] for r in outer if r["kin_exposed"]})
    n_prefix = len({r["horse"] for r in outer if r["meisho"]})
    if n_horses < min_horses:
        status = "HOLD_OUTER_SUPPORT"
    elif has_kin < max(5, min_horses // 4):
        status = "HOLD_INSUFFICIENT_REAL_KIN_EXPOSURE"
    else:
        status = "EXPLORATORY_OUT_OF_TIME_NAME_OWNER_KIN_SCORE_NOT_CAUSAL"
    return {
        "status":status,
        "outcome":"absolute_early_GPS_seconds_not_win_or_odds",
        "inner_validation_begin":inner_cutoff.isoformat(),
        "frozen_test_begin":outer_cutoff.isoformat(),
        "inner_tuning_only_no_future_feedback":True,
        "selected_weights_name_owner_kin":{k:list(w) for k,w in selected.items()},
        "heldout_rows_total":len(future),
        "heldout_context_supported_rows":len(outer),
        "heldout_context_supported_horses":n_horses,
        "heldout_named_meisho_horses":n_prefix,
        "heldout_horses_with_related_training_history":has_kin,
        "heldout_horses_with_owner_training_history":
            len({r["horse"] for r in outer if r["owner_exposed"]}),
        "heldout_horses_with_meisho_named_training_history":
            len({r["horse"] for r in outer if r["name_exposed"]}),
        "results":{
            "all":stats(outer,selected),
            "named_meisho":stats([r for r in outer if r["meisho"]], selected),
            "first_observed":stats([r for r in outer if r["cold"]],selected),
            "meisho_first_observed":stats(
                [r for r in outer if r["cold"] and r["meisho"]],selected),
        },
        "source_requirements":{
            "raw_race_data_reuse_license_must_be_verified":True,
            "verified_original_horse_ids_and_pedigree_ids_must_match":True,
            "owner_id_is_event_specific_verified_pre_race":True,
            "Japanese_horse_name_as_recorded_at_source_date":True,
            "historical_owners_not_inferred_from_current_JBIS_profile":True,
            "missing_GPS_and_confirmed_starters_audit_still_required":True,
        },
        "not_a_genetic_causal_test_or_heritability":True,
        "not_a_calibrated_winning_probability":True,
        "no_individual_horse_ids_outcomes_or_predictions_exported":True,
        "limitations":[
            "All models share the exact heldout context-supported target rows; exposure strata differ.",
            "Name prefix, owner and kin signals can be collinear; even conditional RMSE gains are observational.",
            "A is expected relatedness from only recorded parents, not genomic G.",
            "Frozen one-horizon split with tune-only-inner validation, no race/horse cluster CI yet.",
            "Inclusion of only GPS-positive observations may induce strong outcome selection.",
        ],
    }


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--observations",type=Path,required=True)
    ap.add_argument("--pedigree",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--min-horses",type=int,default=20)
    args=ap.parse_args()
    result=analyze(args.observations,args.pedigree,min_horses=args.min_horses)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
