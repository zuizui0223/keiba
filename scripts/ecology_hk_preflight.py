#!/usr/bin/env python3
"""Local preflight for Kaggle gdaley/hkracing-style races.csv + runs.csv.

NO scraping, downloads, copying row data, guessed race timestamps, or
unverified permission claims. The publisher says dates are deliberately
obscured and lists CC0; upstream rights/venue conditions are unverified.
This script emits ONLY aggregate schema-and-feasibility diagnostics.
It does not generate the ecological modelling panel or run H1/H2.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import json
from pathlib import Path

RACE_COLUMNS={
    "race_id","date","venue","surface","distance","going","race_class",
}
RUN_COLUMNS={
    "race_id","horse_id","result","finish_time","position_sec1","jockey_id",
}


def load_csv(path: Path, required: set[str]) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as fd:
        reader=csv.DictReader(fd)
        if not reader.fieldnames:
            raise ValueError(f"empty file/no header: {path.name}")
        if missing:=required-set(reader.fieldnames):
            raise ValueError(f"missing {path.name} columns: {','.join(sorted(missing))}")
        rows=[{k:(v or "").strip() for k,v in r.items()}
              for r in reader]
    if not rows:
        raise ValueError(f"no records: {path.name}")
    return rows


def optional_positive(value: str) -> float | None:
    if value in ("","NA","nan","None","-","--"):
        return None
    try:
        v=float(value)
    except ValueError:
        return None
    return v if 0 < v < float("inf") else None


def optional_rank(value: str) -> int | None:
    number=optional_positive(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def preflight(races_csv: Path, runs_csv: Path) -> dict:
    races=load_csv(races_csv,RACE_COLUMNS)
    runs=load_csv(runs_csv,RUN_COLUMNS)
    race_index={}
    for row in races:
        key=row["race_id"]
        if not key or key in race_index:
            raise ValueError("empty or duplicate races.csv race_id")
        try:
            date.fromisoformat(row["date"])
        except ValueError as exc:
            raise ValueError(f"invalid obfuscated date for race_id={key}") from exc
        race_index[key]=row
    present=set()
    by_horse=defaultdict(list)
    by_race=defaultdict(list)
    unmatched=0
    duplicate=0
    missing_horse_id=0
    for row in runs:
        if not row["horse_id"]:
            missing_horse_id+=1
            continue
        key=(row["race_id"],row["horse_id"])
        if key in present:
            duplicate+=1
            continue
        present.add(key)
        if row["race_id"] not in race_index:
            unmatched+=1
            continue
        by_horse[row["horse_id"]].append(row)
        by_race[row["race_id"]].append(row)
    if duplicate:
        raise ValueError(f"duplicate horse_id×race_id entries: {duplicate}")
    dates={k:v["date"] for k,v in race_index.items()}
    going_counts=Counter()
    surfaces=Counter()
    classes=Counter()
    for race_id, horses in by_race.items():
        race=race_index[race_id]
        going_counts[race["going"] or "MISSING"]+=1
        surfaces[str(race["surface"] or "MISSING")]+=1
        classes[str(race["race_class"] or "MISSING")]+=1
    timed=0
    early=0
    outcome_missing=0
    for starters in by_race.values():
        for row in starters:
            if optional_positive(row["finish_time"]) is not None:
                timed+=1
            else:
                outcome_missing+=1
            if optional_rank(row["position_sec1"]) is not None:
                early+=1

    repeat=0
    changed_rivals=0
    varied_going=0
    two_per_going=0
    first_going=going_counts.most_common(1)[0][0] if going_counts else None
    history_rows_at_least_3=0
    for horse_id, records in by_horse.items():
        if len(records)>=2:
            repeat+=1
        records.sort(key=lambda r:(dates[r["race_id"]],r["race_id"]))
        go=[race_index[r["race_id"]]["going"] for r in records]
        c=Counter(go)
        if len(c)>=2:
            varied_going+=1
        # Pure engineering overlap for most-common raw label vs any other
        # raw label. It does NOT define biologically good vs heavy going.
        if first_going is not None and c[first_going]>=2 and sum(
            n for g,n in c.items() if g!=first_going)>=2:
            two_per_going+=1
        rivals=[]
        for row in records:
            race_id=row["race_id"]
            rivals.append(frozenset(r["horse_id"] for r in by_race[race_id]
                                   if r["horse_id"]!=horse_id))
        if len(records)>=4 and len(set(rivals))>=2:
            changed_rivals+=1
        early_observed=0
        # Only prior records can establish a history for the next start.
        for row in records:
            if early_observed>=3:
                history_rows_at_least_3+=1
            if optional_rank(row["position_sec1"]) is not None:
                early_observed+=1

    # Design overlap must exist WITHIN comparable race strata. The global
    # counts above can dramatically overstate within-horse identifiability.
    strata=defaultdict(list)
    same_obscured_date=0
    earliest_known=0
    horse_date_seen=set()
    for horse_id,records in by_horse.items():
        for row in records:
            rac=race_index[row["race_id"]]
            label=(rac["venue"],rac["surface"],rac["distance"],rac["race_class"])
            strata[(horse_id,label)].append(row)
            hd=(horse_id,rac["date"])
            if hd in horse_date_seen:
                same_obscured_date+=1
            horse_date_seen.add(hd)
    horses_cross_going_in_any_stratum=set()
    horses_repeated_rival_context_in_any_stratum=set()
    stratum_support=Counter()
    for (horse,label),entries in strata.items():
        if len(entries)<4:
            continue
        # Unknown/empty going is NOT a level with measurable condition.
        going_counts_in_stratum=Counter(
            race_index[e["race_id"]]["going"] for e in entries
            if race_index[e["race_id"]]["going"]
        )
        levels=set(going_counts_in_stratum)
        if len(levels)>=2:
            stratum_support["horse_by_stratum_4plus_with_2plus_going_labels"]+=1
        # Require >1 repeated start in at least two environments.
        # A 3:1 exposure imbalance provides weak cross-environment
        # within-horse support and must NOT pass the preregistered H1 gate.
        replicated_going=sum(n>=2 for n in going_counts_in_stratum.values())>=2
        if replicated_going:
            horses_cross_going_in_any_stratum.add(horse)
            stratum_support["horse_by_stratum_2plus_starts_in_2plus_going_labels"]+=1
        rival_sets={
            frozenset(r["horse_id"] for r in by_race[e["race_id"]]
                      if r["horse_id"]!=horse)
            for e in entries
        }
        if len(rival_sets)>=2:
            horses_repeated_rival_context_in_any_stratum.add(horse)
            stratum_support["horse_by_stratum_4plus_with_2plus_opposing_rosters"]+=1
        if replicated_going and len(rival_sets)>=2:
            stratum_support["horse_by_stratum_both_environment_and_rival_overlap"]+=1

    missing_dates=sum(not r["date"] for r in races)
    # Timeline/order is only within the obscured source representation.
    # Never invent a clock hour or claim verified pre-race timestamps.
    return {
        "status":"HOLD_SOURCE_RIGHTS_AND_OBSCURED_DATES",
        "evidence_class":"AGGREGATE_COMPATIBILITY_SCREEN_ONLY",
        "dataset_page":"https://www.kaggle.com/datasets/gdaley/hkracing",
        "publisher_claimed_license":"CC0",
        "upstream_source_rights_verified":False,
        "real_race_dates_verified":False,
        "race_start_time_known":False,
        "generated_model_panel":False,
        "raw_data_republished":False,
        "input_sha256":{
            "races.csv":hashlib.sha256(races_csv.read_bytes()).hexdigest(),
            "runs.csv":hashlib.sha256(runs_csv.read_bytes()).hexdigest(),
        },
        "schema":{
            "races_csv_columns":sorted(races[0]),
            "runs_csv_columns":sorted(runs[0]),
        },
        "counts":{
            "race_rows":len(races),
            "runs_rows":len(runs),
            "races_with_matching_runs":len(by_race),
            "unmatched_run_rows":unmatched,
            "run_rows_without_horse_id":missing_horse_id,
            "valid_matched_horse_starts":sum(map(len,by_race.values())),
            "unique_horses_in_matched_runs":len(by_horse),
            "horses_with_2plus_starts":repeat,
            "horses_with_2plus_distinct_raw_going_labels":varied_going,
            "horses_with_2plus_starts_in_primary_raw_going_vs_others":two_per_going,
            "horses_with_4plus_starts_and_2plus_distinct_opponent_sets":changed_rivals,
            "timed_run_rows":timed,
            "run_rows_with_unavailable_finish_time":outcome_missing,
            "run_rows_with_first_section_position":early,
            "horse_start_rows_with_3plus_prior_early_positions":history_rows_at_least_3,
            "missing_obscured_date_entries":missing_dates,
            "horse_races_sharing_same_obscured_date":same_obscured_date,
            "horses_with_environment_overlap_within_same_venue_surface_distance_class":len(horses_cross_going_in_any_stratum),
            "horses_with_rival_roster_changes_within_same_venue_surface_distance_class":len(horses_repeated_rival_context_in_any_stratum),
            "stratified_support":dict(stratum_support),
        },
        "raw_going_label_race_counts":dict(going_counts),
        "raw_surface_label_race_counts":dict(surfaces),
        "raw_race_class_counts":dict(classes),
        "no_automatic_going_ordinal_map":True,
        "limitations":[
            "Dates are said by dataset publisher to be intentionally obscured; season/time/official event identity cannot be validated.",
            "Publisher CC0 label does not settle original source rights and distributor contract obligations.",
            "A full horse×race history may be present, but no real-data H1/H2 analysis was executed.",
            "Counts of changing opponent sets are necessary but cannot establish a social competition effect.",
            "Stratum overlap holds venue, surface, distance, and race class constant; support counts do not imply causal identification.",
            "Repeated starts on one obfuscated date cannot be chronologically resolved without independently verified race times.",
            "Early position and observed finish times are POST-race outputs only; use strictly prior starts to build predictor histories.",
            "Going labels are unharmonized; no assumption that category spacing is equal or means wet/dry is made.",
            "Raw/individual records are never printed or exported by this tool.",
        ],
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--races",type=Path,required=True)
    parser.add_argument("--runs",type=Path,required=True)
    parser.add_argument("--audit",type=Path,required=True)
    args=parser.parse_args()
    report=preflight(args.races,args.runs)
    args.audit.parent.mkdir(parents=True,exist_ok=True)
    args.audit.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"counts":report["counts"]},ensure_ascii=False))


if __name__=="__main__":
    main()
