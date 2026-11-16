#!/usr/bin/env python3
"""Post-hoc, source-separated parent-ID placebo controls for Japan 2022-24.

Pairwise sire/dam labels are shuffled together within pre-2022 birth cohort,
circuit and parent-missingness strata. Only old-source outcomes train models;
no heldout ranks are used for the mapping, coefficients or features.
The original no-kin and real-kin scores are source-locked, not reoptimized.
No horse names, IDs, source rows, predictions or pedigrees are exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

import numpy as np
import pandas as pd

from ecology_japan_archive_forward import COLS, SOURCE_SHA, clean_id, prepare_frame
from ecology_japan_hf_event_anchor_gate import anchor_name_histories
from ecology_japan_2022_independent_forward import (
    FEATURE_NO_KIN, FEATURE_KIN, RIDGE_ALPHA, _peer, _scores,
    fit_weighted_ridge, make_common_features,
    parse_independent_history, predict_weighted_ridge,
)

SQLITE_SHA = "7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9"
PRIMARY_ROWS = 255484
PRIMARY_HORSES = 12919
PRIMARY_RMSE_NO_KIN = 0.31277751588017505
PRIMARY_RMSE_KIN = 0.3124550620307501
PERM_SEED_START = 2026111600


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_parent_table(source: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    """One original parent pair per horse; pre-2022 metadata only."""
    parents = source[["horse", "sire_id", "dam_id"]].astype(str).drop_duplicates()
    if parents.horse.duplicated().any():
        raise ValueError("HOLD_CONFLICTING_SOURCE_PARENT_IDS")
    parents = parents.sort_values("horse").reset_index(drop=True)
    first = source.sort_values(["day", "horse"]).drop_duplicates("horse")
    first = first[["horse", "year", "circuit"]].copy()
    first["horse"] = first.horse.astype(str)
    first["circuit"] = first.circuit.astype(str)

    # The first dated old-source observation defines cohort. Missing/invalid
    # age is quarantined in its own group rather than treated as age zero.
    age = pd.DataFrame({
        "horse": clean_id(raw.horse_id),
        "day": pd.to_datetime(raw.date, format="mixed", errors="coerce"),
        "age": pd.to_numeric(raw.age, errors="coerce"),
    })
    age = age[age.horse.ne("") & age.day.notna()]
    age = age.sort_values(["day", "horse"], kind="mergesort")
    age = age.drop_duplicates("horse").set_index("horse").age
    meta = parents.merge(first, on="horse", how="left", validate="one_to_one")
    a = pd.to_numeric(meta.horse.map(age), errors="coerce")
    ok = a.between(1, 15) & meta.year.notna()
    byear = (meta.year.to_numpy(dtype=float) - a.to_numpy(dtype=float))
    meta["birth_bin"] = np.where(ok, np.floor(byear / 5), -999).astype(int)
    meta["circuit"] = meta.circuit.fillna("UNKNOWN").astype(str)
    meta["sire_known"] = meta.sire_id.ne("")
    meta["dam_known"] = meta.dam_id.ne("")
    if len(meta) != len(parents) or meta[["year", "circuit"]].isna().any().any():
        raise ValueError("HOLD_INCOMPLETE_PRE2022_COHORT_META")
    return meta


def shuffle_parent_pairs(parents: pd.DataFrame, seed: int):
    """Move sire/dam PAIRS, not each independently; preserve unknown patterns."""
    required = {"horse", "sire_id", "dam_id", "birth_bin",
                "circuit", "sire_known", "dam_known"}
    if not required.issubset(parents.columns):
        raise ValueError("HOLD_MISSING_PARENT_SHUFFLE_COLUMNS")
    if parents.horse.duplicated().any():
        raise ValueError("HOLD_DUPLICATE_HORSES_FOR_SHUFFLE")
    p = parents.reset_index(drop=True)
    original = p[["sire_id", "dam_id"]].to_numpy(dtype=object)
    shuffled = original.copy()
    groups = p.groupby(
        ["birth_bin", "circuit", "sire_known", "dam_known"],
        sort=True, dropna=False,
    ).indices
    rng = np.random.default_rng(seed)
    swapped_cells = 0
    for indices in groups.values():
        if len(indices) < 2:
            continue
        take = rng.permutation(indices)
        shuffled[indices] = original[take]
        swapped_cells += len(indices)
    out = pd.DataFrame(shuffled, columns=["sire_id", "dam_id"])
    out.insert(0, "horse", p.horse.to_numpy(dtype=str))
    if not np.array_equal(out.sire_id.ne("").to_numpy(), p.sire_known.to_numpy()):
        raise ValueError("HOLD_SHAM_CHANGED_SIRE_COVERAGE")
    if not np.array_equal(out.dam_id.ne("").to_numpy(), p.dam_known.to_numpy()):
        raise ValueError("HOLD_SHAM_CHANGED_DAM_COVERAGE")
    # The complete sire/dam pair multiset, including unknowns, is invariant.
    if Counter(map(tuple, shuffled)) != Counter(map(tuple, original)):
        raise ValueError("HOLD_SHAM_CHANGED_PARENT_PAIR_FREQUENCIES")
    return out.set_index("horse"), {
        "seed": int(seed),
        "horses_total": len(p),
        "horses_in_permutable_strata": int(swapped_cells),
        "fraction_sire_ID_changed": float(np.mean(shuffled[:, 0] != original[:, 0])),
        "fraction_dam_ID_changed": float(np.mean(shuffled[:, 1] != original[:, 1])),
        "strata": len(groups),
    }


def profile_history(h: pd.DataFrame) -> pd.DataFrame:
    """One horse-by-surface/distance cell: matches _peer's within-horse mean."""
    a = (h.groupby(["horse", "stratum"], observed=True).y
         .mean().rename("y").reset_index())
    a["horse"] = a.horse.astype(str)
    a["stratum"] = a.stratum.astype(str)
    return a


def with_parent_map(profile: pd.DataFrame, targets: pd.DataFrame,
                    base: pd.DataFrame, mapping: pd.DataFrame):
    """Rebuild only parent-specific covariates using a fixed pseudo-pedigree.

    The baseline covariates and all labels are identical across permutations.
    Excluding focal horse in _peer is identical to the original model.
    """
    mm = mapping[["sire_id", "dam_id"]]
    ph = profile[["horse", "stratum", "y"]].copy()
    tt = targets[["horse", "stratum"]].copy().reset_index(drop=True)
    tt["horse"] = tt.horse.astype(str)
    tt["stratum"] = tt.stratum.astype(str)
    for col in ("sire_id", "dam_id"):
        ph[col] = ph.horse.map(mm[col])
        tt[col] = tt.horse.map(mm[col])
        if ph[col].isna().any() or tt[col].isna().any():
            raise ValueError("HOLD_SHAM_PARENT_MAPPING_INCOMPLETE")
    ss, sn = _peer(ph, tt, "sire_id")
    ds, dn = _peer(ph, tt, "dam_id")
    own_n = np.expm1(base["log_own_count"].to_numpy(float))
    scale = 5.0 / (own_n + 5.0)
    new = base.copy()
    new["sire_kin_history"] = scale * ss / (8.0 + sn)
    new["dam_kin_history"] = scale * ds / (8.0 + dn)
    new["log_sire_relative_count"] = np.log1p(sn)
    new["log_dam_relative_count"] = np.log1p(dn)
    return new


def load_sources(archive: Path, db: Path):
    if sha256_file(archive) != SOURCE_SHA or sha256_file(db) != SQLITE_SHA:
        raise ValueError("HOLD_CHANGED_OR_UNVERIFIED_DATA_SOURCE_SHA")
    with zipfile.ZipFile(archive) as z, z.open("2010-2021.csv") as fd:
        raw = pd.read_csv(fd, usecols=COLS, dtype=str, keep_default_na=False)
    old, qa = prepare_frame(raw)
    old["stratum"] = (old.surface.astype(str) + ":" +
                      (old.distance // 400).astype(int).astype(str))
    parents = old[["horse", "sire_id", "dam_id"]].astype(str).drop_duplicates()
    if parents.horse.duplicated().any():
        raise ValueError("HOLD_PRE2022_CONFLICTING_PARENT_IDS")
    parent_lookup = parents.set_index("horse")
    pre = raw[["horse_id", "horse_name", "date", "place", "distance"]].copy()
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        race_index = {
            str(rid): (date, distance, int(course))
            for rid, date, distance, course in con.execute(
                "SELECT rid,date,distance,course FROM race"
            )
        }
        def rows():
            return con.execute("SELECT hid,name,races FROM horse")
        crosswalk, identity = anchor_name_histories(
            pre, rows, race_dates={k: v[0] for k, v in race_index.items()}
        )
        if identity["status"] != (
            "CROSS_SOURCE_TWO_EVENT_NAME_IDENTITY_CANDIDATE_NOT_STUDBOOK"
        ):
            raise ValueError("HOLD_TWO_PRE2022_EVENT_IDENTITY_GATE")
        future = []
        qa_event = Counter()
        for new_id, raw_history in con.execute("SELECT hid,races FROM horse"):
            old_id = crosswalk.get(str(new_id))
            if old_id not in parent_lookup.index:
                continue
            events, report = parse_independent_history(raw_history, race_index)
            qa_event.update(report)
            pair = parent_lookup.loc[old_id]
            for e in events:
                if not (2022 <= e["year"] <= 2024):
                    continue
                e.update({
                    "horse": old_id,
                    "sire_id": pair.sire_id,
                    "dam_id": pair.dam_id,
                    "race": e["race_id"],
                })
                future.append(e)
    finally:
        con.close()
    if not future:
        raise ValueError("HOLD_NO_ELIGIBLE_INDEPENDENT_OUTCOMES")
    f = pd.DataFrame(future).sort_values(
        ["day", "race", "horse"]
    ).reset_index(drop=True)
    if f.duplicated(["race", "horse"]).any():
        raise ValueError("HOLD_DUPLICATE_INDEPENDENT_RACE_HORSE")
    if len(f) != PRIMARY_ROWS or f.horse.nunique() != PRIMARY_HORSES:
        raise ValueError("HOLD_INDEPENDENT_COHORT_NOT_FROZEN")
    return raw, old, f, qa, identity, qa_event


def analyze(archive: Path, db: Path, seeds: list[int]):
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("HOLD_INVALID_PLACEBO_SEEDS")
    raw, old, future, qa, identity, qa_event = load_sources(archive, db)
    parents = make_parent_table(old, raw)
    blocks = []
    for year in (2018, 2019, 2020, 2021):
        history = old[old.year < year]
        target = old[old.year == year]
        base = make_common_features(history, target)
        blocks.append({
            "year": year, "target": target, "base": base,
            "profile": profile_history(history)
        })
    x = pd.concat([b["base"] for b in blocks], ignore_index=True)
    y = np.concatenate([b["target"].y.to_numpy() for b in blocks])
    horses = np.concatenate([
        b["target"].horse.astype(str).to_numpy() for b in blocks
    ])
    no_kin_model = fit_weighted_ridge(
        x, y, horses, FEATURE_NO_KIN, alpha=RIDGE_ALPHA
    )
    real_model = fit_weighted_ridge(
        x, y, horses, FEATURE_KIN, alpha=RIDGE_ALPHA
    )
    x_future = make_common_features(old, future)
    p0 = predict_weighted_ridge(no_kin_model, x_future)
    p_true = predict_weighted_ridge(real_model, x_future)
    primary = _scores(future, p0, p_true)
    if (abs(primary["RMSE_portable_no_kin"] - PRIMARY_RMSE_NO_KIN) > 1e-8
            or abs(primary["RMSE_portable_kin"] - PRIMARY_RMSE_KIN) > 1e-8):
        raise ValueError("HOLD_ORIGINAL_2022_2024_SCORE_NOT_REPRODUCED")
    ptrue_map = parents.set_index("horse")[["sire_id", "dam_id"]]
    # Parity: preaggregated profile must reproduce the original true-parent
    # signals exactly; otherwise the placebo distribution is not comparable.
    x_check = with_parent_map(
        profile_history(old), future, x_future, ptrue_map
    )
    for col in FEATURE_KIN:
        if not np.allclose(
            x_check[col].to_numpy(float),
            x_future[col].to_numpy(float),
            atol=1e-10, rtol=1e-10,
        ):
            raise ValueError("HOLD_TRUE_PARENT_FEATURE_PARITY")
    test_profile = profile_history(old)
    sham_results = []
    for seed in seeds:
        mapping, changes = shuffle_parent_pairs(parents, seed)
        if changes["fraction_sire_ID_changed"] < .2:
            raise ValueError("HOLD_SHAM_NOT_MOVING_ENOUGH_PARENT_IDS")
        perm_training = pd.concat([
            with_parent_map(b["profile"], b["target"], b["base"], mapping)
            for b in blocks
        ], ignore_index=True)
        fitted = fit_weighted_ridge(
            perm_training, y, horses, FEATURE_KIN, alpha=RIDGE_ALPHA
        )
        perm_future = with_parent_map(
            test_profile, future, x_future, mapping
        )
        pred = predict_weighted_ridge(fitted, perm_future)
        score = _scores(future, p0, pred)
        sham_results.append({
            "seed": seed,
            "RMSE_portable_placebo_parent_history":
                score["RMSE_portable_kin"],
            "no_kin_minus_placebo_gain": score["M0_minus_kin_gain"],
            "parent_shuffling": changes,
        })
        print(json.dumps({
            "stage": "PLACEBO_FINISHED",
            "seed": seed,
            "gain": score["M0_minus_kin_gain"],
        }), flush=True)
    gains = np.asarray([
        z["no_kin_minus_placebo_gain"] for z in sham_results
    ], dtype=float)
    real_gain = primary["M0_minus_kin_gain"]
    return {
        "status": "POSTHOC_REAL_SOURCE_2022_2024_PARENT_PAIR_PLACEBO_NOT_GENETIC_CAUSATION",
        "old_archive_sha256": SOURCE_SHA,
        "independent_sqlite_sha256": SQLITE_SHA,
        "parent_shuffling_protocol": {
            "frozen_before_shuffling": [
                "2010-2021 archive",
                "2022-2024 heldout rows and original scores",
                "model alpha and covariates",
            ],
            "within": [
                "five-year approximate birth cohort",
                "first recorded JRA or NAR circuit",
                "sire-known / dam-known flags",
            ],
            "parents_permuted_together": True,
            "only_pre2022_metadata_used": True,
            "same_mapping_applied_to_pre2022_training_and_future_targets": True,
            "independent_seed_count": len(seeds),
            "not_preregistered": True,
            "exploratory_posthoc_negative_control": True,
        },
        "identity_gate": {
            "two_event_anchor_horses":
                identity["two_event_anchor_horses"],
            "pre2022_history_only": True,
        },
        "frozen_primary": {
            "rows": len(future),
            "horses": int(future.horse.nunique()),
            "races": int(future.race.nunique()),
            "RMSE_no_kin": primary["RMSE_portable_no_kin"],
            "RMSE_real_kin": primary["RMSE_portable_kin"],
            "real_no_kin_minus_kin_gain": real_gain,
        },
        "negative_controls": {
            "n": len(seeds),
            "mean_placebo_gain": float(np.mean(gains)),
            "median_placebo_gain": float(np.median(gains)),
            "range_placebo_gain": [
                float(np.min(gains)), float(np.max(gains))
            ],
            "percentile_95_placebo_gain":
                np.quantile(gains, [.025, .975]).tolist(),
            "number_placebos_meeting_or_exceeding_real_gain":
                int(np.count_nonzero(gains >= real_gain)),
            "one_sided_monte_carlo_p_with_plus_one":
                float((1 + np.count_nonzero(gains >= real_gain)) /
                      (len(gains) + 1)),
            "per_seed_aggregate_only": sham_results,
        },
        "caveats": [
            "This is a post-hoc falsification of an observed result.",
            "Shared parents may encode stable farm, trainer, cohort, and selection effects; neither actual kin gain nor placebo rejection estimates genetic causality.",
            "The selected horses already had >=2 pre-2022 matched races and do not represent national JRA/NAR registration.",
            "Original races use fully classified finishers, future source uses declared field size; outcome denominator harmonization remains HOLD.",
            "The new source's underlying rights are not independently verified; original source redistribution license is unknown.",
            "Do not merge anonymous 370-sample genomic G or Wikipedia A with this cohort, or infer market-betting profitability.",
        ],
        "no_horse_names_ids_raw_rows_or_predictions_exported": True,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--sqlite", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--permutations", type=int, default=19)
    args = ap.parse_args()
    if not 1 <= args.permutations <= 199:
        raise ValueError("HOLD_PERMUTATION_COUNT_OUT_OF_RANGE")
    seeds = list(range(
        PERM_SEED_START, PERM_SEED_START + args.permutations
    ))
    result = analyze(args.archive, args.sqlite, seeds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": result["status"],
        "source_sha256": result["independent_sqlite_sha256"],
        "n_horses": result["frozen_primary"]["horses"],
        "primary_gain": result["frozen_primary"]["real_no_kin_minus_kin_gain"],
        "placebo_n": result["negative_controls"]["n"],
        "placebo_mean_gain": result["negative_controls"]["mean_placebo_gain"],
        "placebo_max_gain": result["negative_controls"]["range_placebo_gain"][1],
        "one_sided_p": result["negative_controls"][
            "one_sided_monte_carlo_p_with_plus_one"
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
