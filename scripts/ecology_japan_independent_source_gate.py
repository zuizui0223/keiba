#!/usr/bin/env python3
"""Conservative horse ID crosswalk: >=2 exact pre-2022 race events in both sources.

Source new lacks horse IDs: shared race results can anchor identity, but do NOT
prove canonical studbook identity. Later outcomes are excluded from ID matching.
All exported output is anonymous aggregate; in-memory ID map is never saved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import unicodedata
import zipfile

import pandas as pd

OLD_SHA = "c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f"
KEYS = ["day", "course", "race_no", "surface", "distance", "rank", "name"]
COURSES = dict(zip(
    ("sapporo", "hakodate", "fukushima", "niigata", "tokyo", "nakayama",
     "chukyo", "kyoto", "hanshin", "kokura"),
    ("札幌", "函館", "福島", "新潟", "東京", "中山",
     "中京", "京都", "阪神", "小倉"),
))
for ja in list(COURSES.values()):
    COURSES[ja.casefold()] = ja


def canonical_name(name: object) -> str:
    if not isinstance(name, str):
        return ""
    return " ".join(unicodedata.normalize("NFKC", name).strip().split()).casefold()


def normalize(frame: pd.DataFrame, kind: str) -> pd.DataFrame:
    if kind == "old":
        mapping = {"date": "day", "racecourse": "course", "race_number": "race_no",
                   "track": "surface", "place": "rank", "horse_name": "name",
                   "distance": "distance", "horse_id": "horse_id"}
    elif kind == "new":
        mapping = {"date": "day", "course": "course", "race": "race_no",
                   "surface": "surface", "finish": "rank", "horse": "name",
                   "distance": "distance"}
    else:
        raise ValueError("UNKNOWN_SOURCE_TYPE")
    if not set(mapping).issubset(frame.columns):
        raise ValueError("HOLD_MISSING_REQUIRED_SOURCE_FIELDS:" + kind)
    out = frame[list(mapping)].rename(columns=mapping).copy()
    out["day"] = pd.to_datetime(out.day, errors="coerce", format="mixed")
    out["year"] = out.day.dt.year
    out["course"] = (out.course.astype(str).str.strip()
                     .str.replace("競馬場", "", regex=False).str.casefold()
                     .map(COURSES))
    surface = out.surface.astype(str).str.strip().str.casefold()
    out["surface"] = surface.map({
        "turf": "turf", "芝": "turf", "dirt": "dirt",
        "ダート": "dirt", "ダ": "dirt"
    })
    out["race_no"] = pd.to_numeric(out.race_no, errors="coerce")
    out["distance"] = pd.to_numeric(out.distance, errors="coerce")
    out["rank"] = pd.to_numeric(out["rank"], errors="coerce")
    out["name"] = out.name.map(canonical_name)
    valid = (out.day.notna() & out.course.notna() & out.surface.notna()
             & out.race_no.between(1, 12) & out.distance.between(600, 3600)
             & out["rank"].between(1, 30) & out["rank"].mod(1).eq(0)
             & out.race_no.mod(1).eq(0) & out.distance.mod(1).eq(0)
             & out.name.ne(""))
    if kind == "old":
        out["horse_id"] = out.horse_id.fillna("").astype(str).str.strip()
        valid &= out.horse_id.ne("")
    out = out[valid].copy()
    for col in ("race_no", "distance", "rank", "year"):
        out[col] = out[col].astype(int)
    return out


def build_anchor_map(original: pd.DataFrame, newer: pd.DataFrame) -> tuple[dict[str, str], dict]:
    old = normalize(original, "old")
    new = normalize(newer, "new")
    old_duplicates = int(old.duplicated(KEYS + ["horse_id"]).sum())
    new_duplicates = int(new.duplicated(KEYS).sum())
    old = old.drop_duplicates(KEYS + ["horse_id"])
    new = new.drop_duplicates(KEYS)
    old_name_ids = old.groupby("name").horse_id.nunique()
    old_id_names = old.groupby("horse_id").name.nunique()
    conflict_names = set(old_name_ids.index[old_name_ids > 1])
    conflict_ids = set(old_id_names.index[old_id_names > 1])
    oa = old[old.year.between(2016, 2021)]
    na = new[new.year.between(2016, 2021)]
    joined = oa[KEYS + ["horse_id"]].merge(na[KEYS], on=KEYS, how="inner")
    joined = joined[~joined.name.isin(conflict_names) & ~joined.horse_id.isin(conflict_ids)]
    # Count distinct matching CALENDAR DATES, not duplicate rows or races.
    per = joined.groupby(["name", "horse_id"], as_index=False).agg(events=("day", "nunique"))
    selected = per[per.events >= 2]
    ambiguous = selected.groupby("name").horse_id.nunique()
    selected = selected[~selected.name.isin(ambiguous.index[ambiguous > 1])]
    crosswalk = dict(zip(selected.name, selected.horse_id))
    if len(crosswalk) != len(selected):
        raise ValueError("HOLD_DUPLICATE_ANCHORED_NAME")
    future = new[new.year.between(2022, 2025)].copy()
    future["anchored"] = future.name.isin(crosswalk)
    year_counts = {}
    for yr, sub in future.groupby("year"):
        cohort = sub[sub.anchored]
        year_counts[str(yr)] = {
            "total_rows": int(len(sub)),
            "anchored_rows": int(len(cohort)),
            "distinct_anchored_horses": int(cohort.name.nunique()),
            "distinct_anchored_races": int(
                cohort[["day", "course", "race_no"]].drop_duplicates().shape[0]
            ),
        }
    report = {
        "status": ("ANCHORED_2022_PLUS_FEASIBILITY_NOT_FORECAST"
                   if len(crosswalk) >= 100 and int(future.anchored.sum()) >= 100
                   else "HOLD_INSUFFICIENT_CROSS_SOURCE_ANCHORS"),
        "identity_rule": "unique original stable horse ID and name; >=2 distinct pre-2022 dates matching venue+race+surface+distance+finish+name",
        "source_old_rows_valid": int(len(old)),
        "source_new_rows_valid": int(len(new)),
        "source_old_names_with_conflicting_ids": len(conflict_names),
        "source_old_ids_with_conflicting_names": len(conflict_ids),
        "source_old_exact_duplicate_rows": old_duplicates,
        "source_new_exact_duplicate_rows": new_duplicates,
        "source_overlap_pre_2022_new_rows": int(len(na)),
        "cross_source_matching_event_rows": int(len(joined)),
        "source_anchor_horses_one_plus": int(len(per)),
        "source_anchor_horses_two_plus": int(len(crosswalk)),
        "future_2022_2025": {
            "total_rows_with_valid_keys": int(len(future)),
            "anchored_rows": int(future.anchored.sum()),
            "distinct_anchored_horses": int(future.loc[future.anchored, "name"].nunique()),
            "by_year": year_counts,
        },
        "source_new_year_counts": {str(k): int(v) for k, v in new.year.value_counts().sort_index().items()},
        "no_individual_names_or_ids_exported": True,
        "no_future_race_outcome_in_crosswalk": True,
        "identity_not_studbook_verified": True,
        "unmatched_future_horses_not_assumed_genetically_unrelated": True,
        "not_JRA_NAR_census": True,
    }
    return crosswalk, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-archive", type=Path, required=True)
    parser.add_argument("--new-jra-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.old_archive.read_bytes()).hexdigest() != OLD_SHA:
        raise ValueError("HOLD_ORIGINAL_SOURCE_SHA_CHANGED")
    with zipfile.ZipFile(args.old_archive) as z, z.open("2010-2021.csv") as fd:
        old = pd.read_csv(fd, dtype=str, usecols=[
            "date", "racecourse", "race_number", "track", "distance",
            "place", "horse_name", "horse_id"], keep_default_na=False)
    new = pd.read_csv(args.new_jra_csv, dtype=str, keep_default_na=False,
                      usecols=["date", "course", "race", "surface", "distance", "finish", "horse"])
    _, report = build_anchor_map(old, new)
    report.update({
        "original_archive_sha256": OLD_SHA,
        "external_csv_sha256": hashlib.sha256(args.new_jra_csv.read_bytes()).hexdigest(),
        "external_csv_source": "https://github.com/whitedogk/jra-condition-app",
        "external_csv_license_not_verified": True,
        "source_new_raw_rows": int(len(new)),
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
