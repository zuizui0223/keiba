#!/usr/bin/env python3
"""2026 third-source racing rank feasibility and source-A family history score.

A = 2010-21 archive with horse/sire/dam ID and racing history.
B = HF SQLite with source-B horse IDs and 1990-2025/03 race histories.
C = whitedogk public JRA CSV (date, horse name, rank, race condition).

A->B identity: exact name + >=2 PRE-2022 dated rank+distance events.
B->C identity: exact name + >=2 dated rank+distance+surface events
in 2023-2024 ONLY. 2025/2026 outcome NEVER used to establish an ID.

Only 2026 races with unique horse labels and ranks exactly 1..N are scored.
Age/sex/recency uses only source-A pre-2022 historical record.
No individual names, IDs, outcomes, or predictions are serialized.
All raw third-party data are transient and deleted before artifact upload.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

import numpy as np
import pandas as pd

from ecology_japan_archive_forward import COLS, SOURCE_SHA, prepare_frame
from ecology_japan_hf_event_anchor_gate import anchor_name_histories, norm_name
from ecology_japan_2022_independent_forward import (
    FEATURE_NO_KIN, FEATURE_KIN, RIDGE_ALPHA, parse_independent_history,
    make_common_features, fit_weighted_ridge, predict_weighted_ridge,
    _scores, _pooled_ci,
)
from ecology_japan_2022_strong_portable_baseline import (
    old_metadata, extra_features, STRONG_NO_KIN, STRONG_KIN
)

SQLITE_SHA = "7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9"
JRA_CSV_SHA = "ca14ff253018433e8e14bc583628f85ca909195d5e4edb42c6d1e2ade939ba6f"
MIN_HORSES = 30
MIN_ROWS = 100
MIN_DATES = 30
SURFACE = {"芝": "turf", "ダート": "dirt", "ダ": "dirt",
           "turf": "turf", "dirt": "dirt"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load_jra_csv(path: Path):
    if sha256(path) != JRA_CSV_SHA:
        raise ValueError("HOLD_THIRD_SOURCE_CSV_HASH_NOT_LOCKED")
    required = ["date", "course", "surface", "distance", "race",
                "finish", "horse"]
    c = pd.read_csv(path, dtype=str, keep_default_na=False)
    if not set(required).issubset(c.columns):
        raise ValueError("HOLD_THIRD_SOURCE_COLUMNS")
    c = c[required].copy()
    c["day"] = pd.to_datetime(c.date, format="%Y-%m-%d", errors="coerce")
    c["year"] = c.day.dt.year.fillna(0).astype(int)
    c["normalized_name"] = c.horse.map(norm_name)
    c["distance"] = pd.to_numeric(c.distance, errors="coerce")
    c["rank"] = pd.to_numeric(c.finish, errors="coerce")
    c["race_no"] = pd.to_numeric(c.race, errors="coerce")
    c["surf"] = c.surface.str.strip().map(SURFACE)
    c["venue"] = c.course.astype(str).str.strip()
    c["race_key"] = c.day.dt.strftime("%Y-%m-%d").fillna("") + "|" + c.venue + "|" + c.race_no.fillna(-1).astype(int).astype(str)
    valid = (c.day.notna() & c.normalized_name.ne("")
             & c.venue.ne("") & c.race_no.between(1, 12)
             & c.distance.between(600, 4000)
             & c.surf.notna() & c["rank"].between(1,30)
             & c["rank"].mod(1).eq(0))
    c = c.loc[valid].reset_index(drop=True)
    qa = {
        "csv_sha256": JRA_CSV_SHA,
        "valid_rows": len(c),
        "date_min": str(c.day.min().date()) if len(c) else None,
        "date_max": str(c.day.max().date()) if len(c) else None,
        "valid_rows_by_year": {str(k): int(v) for k,v in c.year.value_counts().sort_index().items()},
        "horse_id_column_present": False,
        "sire_dam_id_column_present": False,
        "csv_source_rights_verified": False,
    }
    return c, qa


def event_key(day, distance, surface, rank):
    if surface not in ("turf", "dirt") or int(rank) < 1:
        raise ValueError("HOLD_BAD_HISTORIC_EVENT")
    return (str(day), int(distance), str(surface), int(rank))


def match_hf_to_public_names(b_horse_events, public_events):
    """Only PRE2025 event intersections; does NOT inspect target outcomes.

    b_horse_events: old horse ID -> (unique normalized name, event-set).
    public_events: normalized name -> event-set.
    """
    matches = {}
    support = Counter()
    ambiguous = set()
    seen_name = {}
    for oldid, (name, b_events) in b_horse_events.items():
        if not name or name not in public_events:
            continue
        if name in seen_name and seen_name[name] != oldid:
            ambiguous.add(name)
        seen_name[name] = oldid
    for oldid, (name, b_events) in b_horse_events.items():
        if not name or name in ambiguous:
            continue
        c_events = public_events.get(name, set())
        if not c_events:
            continue
        overlap = b_events.intersection(c_events)
        unique_days = len({e[0] for e in overlap})
        if unique_days:
            support["at_least_one_day"] += 1
        if unique_days >= 2:
            matches[name] = oldid
            support["two_day_horses"] += 1
            support["two_day_events"] += len(overlap)
    support["ambiguous_normalized_names"] = len(ambiguous)
    return matches, dict(support)


def accepted_2026_races(c):
    """Require fully enumerated classified 1..N source-C races."""
    d = c[c.year.eq(2026)].copy()
    d = d[d.day.le(pd.Timestamp("2026-11-17"))].copy()
    kept = []
    status = Counter()
    for race, g in d.groupby("race_key", sort=False):
        n = len(g)
        if not 2 <= n <= 30:
            status["field_outside_2_30"] += 1
            continue
        if (g.normalized_name.duplicated().any()
                or g.surf.nunique() != 1
                or g.distance.nunique() != 1
                or g.venue.nunique() != 1):
            status["duplicate_or_conflicting_race"] += 1
            continue
        if sorted(g["rank"].astype(int).tolist()) != list(range(1, n+1)):
            status["incomplete_tied_or_gapped_results"] += 1
            continue
        status["source_complete_races"] += 1
        kept.append(g)
    if kept:
        ok = pd.concat(kept, ignore_index=True).sort_values(
            ["day", "race_key", "rank"], kind="mergesort"
        ).reset_index(drop=True)
    else:
        ok = d.iloc[0:0].copy()
    return ok, dict(status)


def three_source_cohort(a_path: Path, b_path: Path, c_path: Path):
    if sha256(a_path) != SOURCE_SHA or sha256(b_path) != SQLITE_SHA:
        raise ValueError("HOLD_OLD_OR_INTERMEDIATE_SOURCE_HASH")
    c, c_quality = load_jra_csv(c_path)
    if c.empty:
        return None, {"status": "HOLD_EMPTY_THIRD_SOURCE", "sourceC": c_quality}
    # Hard eligibility for the bridging events: do not admit 2025/26 labels.
    pre2025 = c[c.year.isin((2023, 2024))]
    cevents = defaultdict(set)
    for day, distance, surf, rank, name in pre2025[
        ["day","distance","surf","rank","normalized_name"]
    ].itertuples(index=False, name=None):
        cevents[name].add(event_key(day.date().isoformat(),distance,surf,rank))
    with zipfile.ZipFile(a_path) as z, z.open("2010-2021.csv") as fd:
        raw = pd.read_csv(fd, usecols=COLS, dtype=str, keep_default_na=False)
    old, qa = prepare_frame(raw)
    old["stratum"] = (old.surface.astype(str) + ":" +
                      (old.distance // 400).astype(int).astype(str))
    parents = old[["horse","sire_id","dam_id"]].astype(str).drop_duplicates()
    if parents.horse.duplicated().any():
        raise ValueError("HOLD_CONFLICTING_PRE2022_PARENTS")
    parent_lookup = parents.set_index("horse")
    con = sqlite3.connect(f"file:{b_path}?mode=ro", uri=True)
    try:
        b_lookup = {
            str(rid): (date, dist, int(surf))
            for rid, date, dist, surf in con.execute(
                "SELECT rid,date,distance,course FROM race"
            )
        }
        def historical_b():
            return con.execute("SELECT hid,name,races FROM horse")
        old_crosswalk, first_quality = anchor_name_histories(
            raw[["horse_id","horse_name","date","place","distance"]],
            historical_b,
            race_dates={r:v[0] for r,v in b_lookup.items()}
        )
        if first_quality["status"] != (
                "CROSS_SOURCE_TWO_EVENT_NAME_IDENTITY_CANDIDATE_NOT_STUDBOOK"):
            return None, {
                "status": "HOLD_PRE2022_TWO_EVENT_IDENTITY",
                "sourceC": c_quality, "sourceA_to_B": first_quality
            }
        b_events = {}
        bad_hist = Counter()
        for new_hid, name, hist in con.execute("SELECT hid,name,races FROM horse"):
            oldid = old_crosswalk.get(str(new_hid))
            if oldid not in parent_lookup.index:
                continue
            try:
                values, _ = parse_independent_history(hist, b_lookup)
            except (ValueError, TypeError, KeyError):
                bad_hist["unparsed_intermediate_horse"] += 1
                continue
            events = set()
            for h in values:
                if h["year"] not in (2023, 2024):
                    continue
                n = h["source_declared_field_size"]
                rank = int(round(1 + h["y"] * (n-1)))
                events.add(event_key(h["day"].date().isoformat(),
                                     h["distance"], h["surface"], rank))
            b_events[oldid] = (norm_name(name), events)
    finally:
        con.close()
    bridge, second_quality = match_hf_to_public_names(b_events, cevents)
    complete_c, race_quality = accepted_2026_races(c)
    complete_c["old_horse"] = complete_c.normalized_name.map(bridge)
    linked = complete_c[complete_c.old_horse.notna()].copy()
    linked = linked.sort_values(["day","race_key","old_horse"]).reset_index(drop=True)
    if linked.duplicated(["race_key","old_horse"]).any():
        raise ValueError("HOLD_DUPLICATE_SOURCE_C_2026_MAPPED_HORSE_RACE")
    qa = {
        "status": "THREE_SOURCE_LINKAGE_2026_FEASIBILITY",
        "sourceA_full_sha256": SOURCE_SHA,
        "sourceB_full_sha256": SQLITE_SHA,
        "sourceC_full_sha256": JRA_CSV_SHA,
        "sourceC": c_quality,
        "sourceA_to_B": {
            "two_pre2022_event_horses": first_quality["two_event_anchor_horses"],
            "ambiguous_labels_old": first_quality["old_names_with_multiple_ids"],
            "ambiguous_labels_B": first_quality["new_names_with_multiple_ids"],
            "used_2025_or_2026_results_for_ID": False,
        },
        "sourceB_to_C": second_quality,
        "sourceC_2026_race_quality": race_quality,
        "sourceC_2026_valid_complete_race_rows": len(complete_c),
        "sourceC_2026_linked_rows": len(linked),
        "sourceC_2026_linked_horses": int(linked.old_horse.nunique()),
        "sourceC_2026_linked_distinct_dates": int(linked.day.nunique()),
        "sourceC_2026_linked_races": int(linked.race_key.nunique()),
        "thresholds": {
            "min_2026_horses": MIN_HORSES,
            "min_2026_rows": MIN_ROWS,
            "min_2026_distinct_race_dates": MIN_DATES,
            "fixed_before_2026_scoring": True
        },
        "rights_of_original_racing_records_unverified": True,
        "no_names_IDs_or_individual_races_exported": True,
    }
    if (linked.old_horse.nunique() < MIN_HORSES or len(linked) < MIN_ROWS
            or linked.day.nunique() < MIN_DATES):
        qa["status"] = "HOLD_SPARSE_2026_ANCHORED_COHORT"
        return None, qa
    # Create only the eligible focal targets, including source-A parent IDs.
    f = linked.copy()
    f["horse"] = f.old_horse.astype(str)
    f["race"] = f.race_key
    f["surface"] = f.surf
    f["year"] = 2026
    f["stratum"] = f.surface.astype(str) + ":" + (f.distance // 400).astype(int).astype(str)
    race_n = complete_c.groupby("race_key").size()
    f["field"] = f.race.map(race_n).astype(int)
    f["y"] = (f["rank"].to_numpy(float) - 1) / (f["field"].to_numpy(float)-1)
    f["sire_id"] = f.horse.map(parent_lookup.sire_id)
    f["dam_id"] = f.horse.map(parent_lookup.dam_id)
    if f[["sire_id", "dam_id"]].isna().any().any():
        raise ValueError("HOLD_2026_SOURCE_A_PARENT_LINK_INCOMPLETE")
    return (raw, old, f), qa


def score_model_family(old, f, raw, *, strong):
    train = []
    metadata = old_metadata(raw) if strong else None
    for yr in (2018, 2019, 2020, 2021):
        hist = old[old.year < yr]
        target = old[old.year == yr]
        feats = make_common_features(hist, target)
        if strong:
            extras, _ = extra_features(hist, target, metadata)
            feats = pd.concat([feats.reset_index(drop=True), extras], axis=1)
        train.append((target, feats))
    x = pd.concat([features for target, features in train], ignore_index=True)
    y = np.concatenate([target.y.to_numpy(float) for target,features in train])
    horses = np.concatenate([
        target.horse.astype(str).to_numpy() for target,features in train
    ])
    cov0 = STRONG_NO_KIN if strong else FEATURE_NO_KIN
    cov1 = STRONG_KIN if strong else FEATURE_KIN
    model0 = fit_weighted_ridge(x,y,horses,cov0,alpha=RIDGE_ALPHA)
    model1 = fit_weighted_ridge(x,y,horses,cov1,alpha=RIDGE_ALPHA)
    xfuture = make_common_features(old,f)
    if strong:
        more,_ = extra_features(old,f,metadata)
        xfuture = pd.concat([xfuture.reset_index(drop=True), more], axis=1)
    p0 = predict_weighted_ridge(model0,xfuture)
    p1 = predict_weighted_ridge(model1,xfuture)
    out = _scores(f,p0,p1)
    if out["unique_horses"] >= 30 and out["rows"] >= 100:
        out["one_way_399_bootstrap"] = _pooled_ci(f,p0,p1,B=399)
    return out


def analyze(a_path:Path,b_path:Path,c_path:Path):
    payload,gate = three_source_cohort(a_path,b_path,c_path)
    if payload is None:
        return gate
    raw,old,f=payload
    ordinary=score_model_family(old,f,raw,strong=False)
    stronger=score_model_family(old,f,raw,strong=True)
    return {
        **gate,
        "status": "SOURCE_SEPARATED_2026_RETROSPECTIVE_HOLDOUT_NOT_STUDBOOK",
        "outcomes_2026_scored_only_after_fixed_two_stage_2024_identity":True,
        "sourceA_2018_2021_training_only":True,
        "sourceA_kin_not_full_pedigree_A_or_genome_G":True,
        "2026_ordinary":ordinary,
        "2026_strong_pretarget":stronger,
        "scope_limits":[
            "Retrospective new 2026 source release, not live prospective collection",
            "Surviving old-source runners only; excludes 2022+ debuting horses",
            "C source has no official unique horse ID; exact two-event historical anchor not studbook-certified",
            "2026 new CSV may be incomplete and derived from shared JRA upstream website",
            "Race ranks normalized by complete classified finisher set in source C; may differ from actual entrant field",
            "Cross-source license and data reuse rights not independently cleared",
            "Family sharing cannot identify additive genetics versus breeding environment",
            "No odds, probability calibration, betting profit, national JRA+NAR census or new genomic analysis"
        ],
        "no_names_IDs_or_individual_races_exported":True
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive",type=Path,required=True)
    ap.add_argument("--sqlite",type=Path,required=True)
    ap.add_argument("--jra-csv",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    r=analyze(args.archive,args.sqlite,args.jra_csv)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
