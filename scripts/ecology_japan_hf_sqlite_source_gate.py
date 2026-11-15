#!/usr/bin/env python3
"""Historical SQLite source feasibility: exact ID AND two pre-2022 racing events.

Hugging Face data lists Apache-2.0, but third-party underlying racing data
rights are not independently verified. No horse rows, names or IDs exported.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import zipfile

import pandas as pd

OLD_SHA="c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f"
DATE_RE=re.compile(r"^\d{8}$")


def normalize_date(raw):
    digits=re.sub(r"[^0-9]","",str(raw))
    ymd=digits[:8]
    if len(ymd)==8 and DATE_RE.fullmatch(ymd) and 19000101<=int(ymd)<=21001231:
        return ymd
    return None


def parse_horse_history(raw, race_dates=None):
    if not raw:
        return []
    data=json.loads(raw)
    if (isinstance(data,list) and data and isinstance(data[0],list)
            and data[0] and isinstance(data[0][0],(list,dict))):
        data=data[0]
    if not isinstance(data,list):
        return []
    records=[]
    for r in data:
        if not isinstance(r,list) or len(r)<17:
            continue
        embedded=normalize_date(r[17]) if len(r)>=18 else None
        if race_dates is not None:
            # In the actual published SQLite, horse.races has 17 fields:
            # its full date lives in race.date, joined by race.rid.
            from_race=normalize_date(race_dates.get(str(r[0]).strip())) if str(r[0]).strip() in race_dates else None
            if not from_race or (embedded and embedded!=from_race):
                continue
            day=from_race
        else:
            day=embedded
        if not day:
            continue
        try:
            place=int(r[12]);distance=int(r[5])
            if day and 1<=place<=30 and 600<=distance<=4000:
                records.append((day,place,distance))
        except (ValueError,TypeError):
            pass
    return records


def matched_event_dates(original:set, independent:list) -> int:
    return len({x[0] for x in set(independent).intersection(original)})


def old_profiles(archive:Path):
    with zipfile.ZipFile(archive) as z,z.open("2010-2021.csv") as fd:
        df=pd.read_csv(fd,dtype=str,keep_default_na=False,
                       usecols=["horse_id","date","place","distance"])
    df["day"]=pd.to_datetime(df.date,format="mixed",errors="coerce").dt.strftime("%Y%m%d")
    df["rank"]=pd.to_numeric(df.place,errors="coerce")
    df["distance_num"]=pd.to_numeric(df.distance.astype(str).str.strip().str.replace(r"(?i)m$","",regex=True),errors="coerce")
    df=df[df.day.notna() & df["rank"].between(1,30) & df.distance_num.between(600,4000)
          & df["rank"].mod(1).eq(0)]
    data=defaultdict(set)
    for hid,day,place,meters in df[["horse_id","day","rank","distance_num"]].itertuples(index=False,name=None):
        if hid and hid!="0":
            data[hid].add((day,int(place),int(meters)))
    return data


def inspect_database(db:Path, archive:Path):
    old=old_profiles(archive)
    con=sqlite3.connect(f"file:{db}?mode=ro",uri=True)
    tables={r[0].lower():r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"horse","race"}.issubset(tables):
        return {"status":"HOLD_SOURCE_REQUIRED_TABLE_MISSING","tables":sorted(tables)}
    horse,race=tables["horse"],tables["race"]
    col_h=[r[1] for r in con.execute(f'PRAGMA table_info("{horse}")')]
    col_r=[r[1] for r in con.execute(f'PRAGMA table_info("{race}")')]
    n_h=con.execute(f'SELECT count(*) FROM "{horse}"').fetchone()[0]
    n_r=con.execute(f'SELECT count(*) FROM "{race}"').fetchone()[0]
    dmin,dmax=con.execute(f'SELECT min(date),max(date) FROM "{race}"').fetchone()
    n_later=con.execute(f'SELECT count(*) FROM "{race}" WHERE substr(date,1,4) BETWEEN "2022" AND "2025"').fetchone()[0]
    if not {"hid","races"}.issubset(col_h):
        return {"status":"HOLD_SOURCE_HORSE_HISTORY_SCHEMA_UNSUPPORTED",
                "horse_columns":col_h,"race_columns":col_r,
                "horse_rows":n_h,"race_rows":n_r}
    matched_ids=anchored_two=post2021_horses=post2021_rows=bad_history=0
    year_counter=Counter()
    for hid,raw in con.execute(f'SELECT hid,races FROM "{horse}"'):
        if hid not in old:
            continue
        matched_ids+=1
        try:
            history=parse_horse_history(raw)
        except (TypeError,ValueError,KeyError):
            bad_history+=1
            continue
        if matched_event_dates(old[hid],history)<2:
            continue
        anchored_two+=1
        future=[r for r in history if "2022"<=r[0][:4]<="2025"]
        if future:
            post2021_horses+=1
            post2021_rows+=len(future)
            year_counter.update(r[0][:4] for r in future)
    con.close()
    return {
        "status":("INDEPENDENT_2022_PLUS_ID_AND_HISTORY_COHORT_CANDIDATE"
                  if anchored_two>=100 and post2021_rows>=100
                  else "HOLD_TOO_FEW_VALIDATED_HISTORICAL_ID_ANCHORS"),
        "source":"https://huggingface.co/datasets/KBlueLeaf/jp-racing-horse",
        "source_license_label":"apache-2.0",
        "underlying_racing_data_rights_independently_verified":False,
        "horse_table_rows":n_h,"race_table_rows":n_r,
        "race_date_min":str(dmin),"race_date_max":str(dmax),
        "race_rows_2022_to_2025":n_later,
        "horse_columns":col_h,"race_columns":col_r,
        "historical_original_horse_ids":len(old),
        "exact_horse_id_overlap":matched_ids,
        "horse_id_overlap_with_two_pre2022_matching_date_rank_distance_results":anchored_two,
        "validated_old_horses_with_post2021_history":post2021_horses,
        "post2021_independent_race_history_rows_on_validated_old_horses":post2021_rows,
        "post2021_validated_rows_by_year":dict(year_counter),
        "parse_failures_in_overlapping_horse_histories":bad_history,
        "no_future_outcome_used_to_choose_id_alignment":True,
        "source_relatedness_fields_missing_or_unverified":True,
        "raw_individual_horse_ids_names_outcomes_exported":False,
        "all_horses_JRA_NAR_census_confirmed":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--db",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if hashlib.sha256(args.archive.read_bytes()).hexdigest()!=OLD_SHA:
        raise ValueError("HOLD_ORIGINAL_ARCHIVE_SHA_CHANGED")
    result=inspect_database(args.db,args.archive)
    h=hashlib.sha256()
    with args.db.open("rb") as fd:
        for block in iter(lambda:fd.read(4*1024*1024),b""):
            h.update(block)
    result["new_binary_sha256"]=h.hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
