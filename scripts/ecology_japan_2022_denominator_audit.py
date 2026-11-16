#!/usr/bin/env python3
"""Second-source 2022-2024 race-denominator audit and strict-complete-race score.

Post-hoc sensitivity, never overwrite source-locked 255484-row primary result.
Race.horses ranks and Horse.races ranks must match the same new horse ID.
Only fully enumerated races with consecutive 1..N classified ranks and
N == horse-history declared runners are eligible for STRICT score.
The lower-support consecutively ranked subset is reported separately as
a conditional proxy, not official-certified finishers.

No horse names, IDs, individual results, crosswalks or predictions are exported.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

from ecology_japan_2022_parent_placebo import (
    load_sources, SQLITE_SHA, PRIMARY_ROWS, PRIMARY_HORSES,
    PRIMARY_RMSE_NO_KIN, PRIMARY_RMSE_KIN
)
from ecology_japan_hf_event_anchor_gate import anchor_name_histories
from ecology_japan_2022_independent_forward import (
    FEATURE_NO_KIN, FEATURE_KIN, RIDGE_ALPHA,
    fit_weighted_ridge, make_common_features, predict_weighted_ridge,
    _scores, _pooled_ci
)


def decode_race_horses(raw):
    """The published schema is often one outer list around horse entries."""
    if raw is None or raw == "":
        return None, "EMPTY_RACE_HORSE_LIST"
    try:
        arr = json.loads(raw)
    except (TypeError, ValueError):
        return None, "INVALID_RACE_HORSE_JSON"
    if (isinstance(arr, list) and len(arr) == 1
            and isinstance(arr[0], list)
            and arr[0] and isinstance(arr[0][0], list)):
        arr = arr[0]
    if not isinstance(arr, list):
        return None, "INVALID_RACE_HORSE_SHAPE"
    if not arr:
        return None, "EMPTY_RACE_HORSE_LIST"
    if any(not isinstance(x, list) or len(x) < 2 for x in arr):
        return None, "INVALID_RACE_HORSE_RECORD"
    return arr, "OK"


def audit_race_entries(raw, declared_n):
    """Audit flat rank/ID entries; keep all identifiers transient in memory."""
    arr, shape = decode_race_horses(raw)
    if arr is None:
        return {"status": shape, "n": 0, "positive_rank_count": 0}, {}
    if not isinstance(declared_n, (int, np.integer)):
        return {"status": "DECLARED_FIELD_MISSING", "n": len(arr)}, {}
    ids = [str(x[0]).strip() for x in arr]
    if any(not v or v.lower() in {"none", "nan"} for v in ids):
        return {"status": "EMPTY_SOURCE_HORSE_ID", "n": len(arr)}, {}
    if len(set(ids)) != len(ids):
        return {"status": "DUPLICATE_SOURCE_HORSE_ID", "n": len(arr)}, {}
    ranks = []
    for x in arr:
        try:
            v = int(x[1])
            if isinstance(x[1], float) and not x[1].is_integer():
                raise ValueError()
            if isinstance(x[1], str) and str(v) != x[1].strip():
                raise ValueError()
        except (ValueError, TypeError, OverflowError):
            return {"status": "INVALID_CLASSIFIED_RANK", "n": len(arr)}, {}
        ranks.append(v)
    positive = [r for r in ranks if r > 0]
    q = {
        "n": len(arr), "n_declared": int(declared_n),
        "positive_rank_count": len(positive),
        "unclassified_rank_count": len(arr) - len(positive)
    }
    out = dict(zip(ids, ranks))
    if len(positive) < 2 or any(v > 30 for v in positive):
        return dict(q, status="TOO_FEW_OR_OUTSIDE_CLASSIFIED_RANKS"), out
    if len(set(positive)) != len(positive):
        return dict(q, status="TIED_OR_DUPLICATED_RANKS"), out
    if sorted(positive) != list(range(1, len(positive) + 1)):
        return dict(q, status="GAPPED_CLASSIFIED_RANKS"), out
    if len(arr) > declared_n:
        return dict(q, status="ENTRY_COUNT_ABOVE_DECLARED"), out
    q["classified_n"] = len(positive)
    if len(arr) == declared_n and len(positive) == declared_n:
        return dict(q, status="STRICT_COMPLETE_CLASSIFIED_RACE"), out
    if len(positive) < declared_n:
        return dict(q, status="CLASSIFIED_PROXY_INCOMPLETE_DECLARED"), out
    return dict(q, status="UNRESOLVED_RACE_DENOMINATOR"), out


def one_observation_original_baselines(old, future):
    """Refit original models exactly, refuse even tiny score drift."""
    trainings = []
    for year in (2018, 2019, 2020, 2021):
        h = old[old.year < year]
        t = old[old.year == year]
        feats = make_common_features(h, t)
        trainings.append((t, feats))
    x = pd.concat([z[1] for z in trainings], ignore_index=True)
    y = np.concatenate([z[0].y.to_numpy() for z in trainings])
    horse = np.concatenate([
        z[0].horse.astype(str).to_numpy() for z in trainings
    ])
    a = fit_weighted_ridge(x, y, horse, FEATURE_NO_KIN, alpha=RIDGE_ALPHA)
    b = fit_weighted_ridge(x, y, horse, FEATURE_KIN, alpha=RIDGE_ALPHA)
    f = make_common_features(old, future)
    p0 = predict_weighted_ridge(a, f)
    p1 = predict_weighted_ridge(b, f)
    result = _scores(future, p0, p1)
    if (len(future) != PRIMARY_ROWS or future.horse.nunique() != PRIMARY_HORSES
            or abs(result["RMSE_portable_no_kin"] - PRIMARY_RMSE_NO_KIN) > 1e-8
            or abs(result["RMSE_portable_kin"] - PRIMARY_RMSE_KIN) > 1e-8):
        raise ValueError("HOLD_FROZEN_ORIGINAL_PREDICTION_PARITY")
    return p0, p1, result


def analyze(archive, sqlite_file):
    raw, old, future, _, identity, _ = load_sources(archive, sqlite_file)
    p0, p1, original_score = one_observation_original_baselines(old, future)
    race_counts = future.groupby("race", sort=False).source_declared_field_size.nunique()
    inconsistent = int((race_counts != 1).sum())
    if inconsistent:
        raise ValueError("HOLD_NONUNIQUE_DECLARED_FIELD_PER_RACE")
    race_field = future.groupby("race", sort=False).source_declared_field_size.first()

    con = sqlite3.connect(f"file:{sqlite_file}?mode=ro", uri=True)
    try:
        old_anchor = raw[["horse_id", "horse_name", "date", "place", "distance"]]
        source_dates = {
            str(rid): day
            for rid, day in con.execute("SELECT rid,date FROM race")
        }
        def new_horses():
            return con.execute("SELECT hid,name,races FROM horse")
        crosswalk, cross_quality = anchor_name_histories(
            old_anchor, new_horses, race_dates=source_dates
        )
        if cross_quality["two_event_anchor_horses"] != identity["two_event_anchor_horses"]:
            raise ValueError("HOLD_TWO_EVENT_CROSSWALK_REPRO")
        reverse = {}
        for new_id, old_id in crosswalk.items():
            if old_id in reverse:
                raise ValueError("HOLD_NONINJECTIVE_TWO_SOURCE_CROSSWALK")
            reverse[old_id] = str(new_id)
        future_new_ids = future.horse.astype(str).map(reverse)
        if future_new_ids.isna().any():
            raise ValueError("HOLD_HORSE_CROSSWALK_INCOMPLETE")
        match_ids = {str(v) for v in race_field.index}
        statuses = {}
        ranks_by_race = {}
        counters = Counter()
        for rid, raw_horses in con.execute(
            "SELECT rid,horses FROM race WHERE substr(date,1,4) BETWEEN '2022' AND '2024'"
        ):
            key = str(rid)
            if key not in match_ids:
                continue
            record, ranking = audit_race_entries(
                raw_horses, int(race_field.loc[key])
            )
            statuses[key] = record
            ranks_by_race[key] = ranking
            counters[record["status"]] += 1
        if len(statuses) != len(race_field):
            missing = len(race_field) - len(statuses)
            raise ValueError(f"HOLD_MISSING_SOURCE_RACE_HORSES_{missing}")
        full = {"STRICT_COMPLETE_CLASSIFIED_RACE"}
        proxy = full | {"CLASSIFIED_PROXY_INCOMPLETE_DECLARED"}
        matched = []
        problems = Counter()
        proxy_denominators = []
        for rid, newid, source_y, ndecl in zip(
            future.race, future_new_ids, future.y,
            future.source_declared_field_size
        ):
            stat = statuses[str(rid)]
            rank = ranks_by_race[str(rid)].get(str(newid))
            if rank is None:
                problems["missing_exact_source_horse_from_Race.horses"] += 1
                matched.append(False)
                proxy_denominators.append(0)
                continue
            target_rank = 1 + source_y * (ndecl - 1)
            if not np.isclose(rank, target_rank, atol=1e-9):
                problems["conflicting_exact_source_horse_rank"] += 1
                matched.append(False)
                proxy_denominators.append(0)
                continue
            if stat["status"] not in proxy or rank < 1:
                problems["rank_matches_but_race_not_audit_eligible"] += 1
                matched.append(False)
                proxy_denominators.append(0)
                continue
            matched.append(True)
            proxy_denominators.append(stat["classified_n"])
        future = future.copy()
        future["source_horse_and_rank_matched"] = matched
        future["strict_complete"] = (
            future.race.map({r: v["status"] in full for r, v in statuses.items()})
            & future.source_horse_and_rank_matched
        )
        future["proxy_classified"] = (
            future.race.map({r: v["status"] in proxy for r, v in statuses.items()})
            & future.source_horse_and_rank_matched
        )
        future["proxy_denom"] = proxy_denominators
        if not any(future.strict_complete):
            return {
                "status": "HOLD_NO_STRICT_COMPLETE_RACE_ROWS",
                "source_sha256": SQLITE_SHA,
                "original_frozen": original_score,
                "race_quality_counts": dict(counters),
                "runner_identity_rank_quality": dict(problems),
                "total_frozen_races": len(race_field),
                "no_raw_horse_or_race_records_exported": True
            }
        def score_view(mask, *, change_denominator=False):
            idx = np.flatnonzero(mask.to_numpy(dtype=bool))
            if len(idx) < 2:
                return {"status": "HOLD_LT2_ELIGIBLE_ROWS", "rows": len(idx)}
            t = future.iloc[idx].copy()
            if change_denominator:
                rank = 1 + t.y.to_numpy(float) * (
                    t.source_declared_field_size.to_numpy(float)-1
                )
                new_den = t.proxy_denom.to_numpy(float)
                if any(new_den < 2) or any(rank > new_den):
                    return {"status": "HOLD_PROXY_RANK_DENOMINATOR_CONFLICT"}
                t["y"] = (rank - 1) / (new_den-1)
            s = _scores(t, p0[idx], p1[idx])
            s["status"] = "SCORED_CONDITIONAL_COHORT"
            s["uses_proxy_denominator_not_studbook_certified"] = bool(change_denominator)
            s["by_year"] = {
                str(year): _scores(t.loc[t.year==year], p0[idx][t.year.eq(year)],
                                   p1[idx][t.year.eq(year)])
                for year in (2022, 2023, 2024)
                if t.year.eq(year).any()
            }
            if s["unique_horses"] >= 100 and s["rows"] >= 1000:
                s["single_way_bootstrap"] = _pooled_ci(t, p0[idx], p1[idx], B=399)
            return s
        return {
            "status": "REAL_SOURCE_2022_2024_RACE_HORSES_DENOMINATOR_AUDIT_NOT_GENETIC_CAUSATION",
            "source_archive_sha256": "c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f",
            "source_sqlite_sha256": SQLITE_SHA,
            "pre2022_two_event_crosswalk": int(identity["two_event_anchor_horses"]),
            "original_frozen": original_score,
            "counts": {
                "frozen_rows": len(future),
                "frozen_horses": int(future.horse.nunique()),
                "frozen_races": len(race_field),
                "race_qualification": dict(counters),
                "source_horse_rank_failures": dict(problems),
                "rows_matched_to_Race.horses_exact_identity_and_rank":
                    int(future.source_horse_and_rank_matched.sum()),
                "rows_strict_complete": int(future.strict_complete.sum()),
                "rows_classified_proxy": int(future.proxy_classified.sum()),
                "strict_complete_races": int(future.loc[future.strict_complete,"race"].nunique()),
            },
            "strict_complete": score_view(future.strict_complete),
            "classified_proxy": score_view(
                future.proxy_classified, change_denominator=True
            ),
            "method_notes": [
                "Post-hoc sensitivity; source releases and original coefficient families locked.",
                "Strict race requires unique Race.horses IDs, integer consecutive ranks 1..N, and N equals independently recorded Horse.races declared count.",
                "Matched Horse.races entry must have identical new-source horse ID and rank in Race.horses.",
                "Incomplete classified proxy redefines denominator to the consecutive classified rank count and is not official-census certified.",
                "No held-out label enters old-source regression or horse identity crosswalk.",
                "No official pre-race odds, nationally comprehensive pedigree or individual DNA is inferred.",
                "Underlying racing data source-rights remain unverified."
            ],
            "no_raw_horse_or_race_records_exported": True
        }
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--sqlite",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=analyze(args.archive,args.sqlite)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "counts":result.get("counts"),
        "strict_complete":result.get("strict_complete"),
        "classified_proxy":result.get("classified_proxy"),
    },ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
