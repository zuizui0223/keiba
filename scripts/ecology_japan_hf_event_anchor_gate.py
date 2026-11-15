#!/usr/bin/env python3
"""Source identity: exact normalized name plus two corroborating historical races.

The newer SQLite source uses another horse-ID namespace. Match ONLY horses
with unique names on both sides and >=2 exact pre-2022 date, rank, distance
events on distinct calendar dates. Later outcomes NEVER establish identity.
The private map is ephemeral. No names or individual scores are exported.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import unicodedata
import zipfile

import pandas as pd
from ecology_japan_hf_sqlite_source_gate import parse_horse_history, OLD_SHA


def norm_name(name):
    if not isinstance(name,str):
        return ""
    return " ".join(unicodedata.normalize("NFKC",name).strip().split()).casefold()


def _source_record_shape(raw):
    """Only field TYPES/lengths; never return a source value or identifier."""
    out=Counter()
    if not raw:
        out["EMPTY_JSON_HISTORY"]+=1
        return out
    try:
        tree=json.loads(raw)
    except (TypeError,ValueError):
        out["UNREADABLE_JSON_HISTORY"]+=1
        return out
    out["root_type_"+type(tree).__name__]+=1
    if isinstance(tree,list):
        out["root_length_0" if not tree else "root_length_positive"]+=1
        root=tree[0] if tree else None
        out["first_type_"+type(root).__name__]+=1
        if isinstance(root,list):
            out["first_list_length_"+str(min(len(root),1000))]+=1
            if root and isinstance(root[0],list):
                record=root[0]
            else:
                record=root
        else:
            record=root
        out["leaf_type_"+type(record).__name__]+=1
        if isinstance(record,list):
            out["leaf_list_length_"+str(min(len(record),200))]+=1
            if len(record)>17:
                out["r_date_type_"+type(record[17]).__name__]+=1
                out["r_date_char_length_"+str(min(len(str(record[17])),40))]+=1
                out["r_date_chars_all_digits"]+=str(record[17]).isdigit()
                out["rank_index_12_is_digit"]+=str(record[12]).isdigit()
                out["distance_index_5_is_digit"]+=str(record[5]).isdigit()
    return out


def anchor_name_histories(old:pd.DataFrame, horse_records):
    required={"horse_id","horse_name","date","place","distance"}
    if not required.issubset(old.columns):
        raise ValueError("HOLD_OLD_SCHEMA_REQUIRED_FOR_EVENT_ANCHOR")
    x=old[list(required)].copy()
    x["name"]=x.horse_name.map(norm_name)
    x["horse_id"]=x.horse_id.fillna("").astype(str).str.strip()
    x["day"]=pd.to_datetime(x.date,errors="coerce",format="mixed").dt.strftime("%Y%m%d")
    x["rank"]=pd.to_numeric(x.place,errors="coerce")
    x["dist"]=pd.to_numeric(x.distance.astype(str).str.strip().str.replace(r"(?i)m$","",regex=True),errors="coerce")
    valid=(x.day.notna()&x.name.ne("")&x.horse_id.ne("")
           &x["rank"].between(1,30)&x["rank"].mod(1).eq(0)&x.dist.between(600,4000)
           &x.day.lt("20220101"))
    x=x[valid].copy()
    name_ids=x.groupby("name").horse_id.nunique()
    id_names=x.groupby("horse_id").name.nunique()
    bad_names=set(name_ids.index[name_ids>1])
    bad_ids=set(id_names.index[id_names>1])
    x=x[~x.name.isin(bad_names)&~x.horse_id.isin(bad_ids)]
    name_to_id=dict(x[["name","horse_id"]].drop_duplicates().itertuples(index=False,name=None))
    history=defaultdict(set)
    for hid,day,rank,meters in x[["horse_id","day","rank","dist"]].itertuples(index=False,name=None):
        history[hid].add((day,int(rank),int(meters)))
    def iterator():
        return horse_records() if callable(horse_records) else iter(horse_records)
    name_to_newids=defaultdict(set)
    for hid,name,raw in iterator():
        normalized=norm_name(name)
        if normalized in name_to_id:
            name_to_newids[normalized].add(str(hid))
    ambiguous={n for n,ids in name_to_newids.items() if len(ids)>1}
    confirmed={}
    one=0
    later_counts=Counter()
    bad_history=0
    probe=Counter()
    shape_examples=0
    for hid,name,raw in iterator():
        normalized=norm_name(name)
        if normalized not in name_to_id or normalized in ambiguous:
            continue
        probe["candidate_histories_total"]+=1
        if shape_examples<500:
            probe.update(_source_record_shape(raw))
            shape_examples+=1
        try:
            records=parse_horse_history(raw)
        except (TypeError,ValueError,KeyError):
            bad_history+=1
            continue
        old_id=name_to_id[normalized]
        probe["candidate_histories_with_parsed_races"]+=bool(records)
        pre=[r for r in records if r[0]<"20220101"]
        probe["candidate_histories_with_pre2022_parsed_races"]+=bool(pre)
        probe["candidate_parsed_races_total"]+=len(records)
        probe["candidate_parsed_pre2022_races_total"]+=len(pre)
        # Compare granularity progressively to locate a wrong source field.
        hist=history[old_id]
        old_days={v[0] for v in hist}
        new_days={v[0] for v in pre}
        probe["candidate_pre2022_dates_matching_old"]+=bool(new_days & old_days)
        old_daydist={(v[0],v[2]) for v in hist}
        old_dayrank={(v[0],v[1]) for v in hist}
        probe["candidate_pre2022_day_distance_matching_old"]+=bool(old_daydist & {(v[0],v[2]) for v in pre})
        probe["candidate_pre2022_day_rank_matching_old"]+=bool(old_dayrank & {(v[0],v[1]) for v in pre})
        dates={r[0] for r in set(pre).intersection(hist)}
        if dates:
            one+=1
        if len(dates)<2:
            continue
        confirmed[str(hid)]=old_id
        later_counts.update(r[0][:4] for r in records if "2022"<=r[0][:4]<="2025")
    return confirmed,{
        "status":("CROSS_SOURCE_TWO_EVENT_NAME_IDENTITY_CANDIDATE_NOT_STUDBOOK"
                  if len(confirmed)>=100 and sum(later_counts.values())>=100
                  else "HOLD_INSUFFICIENT_TWO_EVENT_ALIASES_OR_FUTURE_HISTORY"),
        "source_old_unique_names":len(name_to_id),
        "old_names_with_multiple_ids":len(bad_names),
        "old_ids_with_multiple_names":len(bad_ids),
        "new_name_label_overlap":len(name_to_newids),
        "new_names_with_multiple_ids":len(ambiguous),
        "at_least_one_matching_historical_race_horses":one,
        "two_event_anchor_horses":len(confirmed),
        "independent_future_rows_on_anchors":sum(later_counts.values()),
        "future_by_year":dict(later_counts),
        "candidate_histories_unparseable":bad_history,
        "source_shape_probe":dict(probe),
        "only_pre2022_results_used_for_anchoring":True,
        "not_official_studbook_ID_crosswalk":True,
        "no_names_IDs_or_source_records_exported":True,
        "new_horses_without_historical_anchors_are_not_included":True,
        "future_results_not_visited_during_identity_selection":True,
        "not_all_JRA_NAR_horses":True,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--db",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if hashlib.sha256(args.archive.read_bytes()).hexdigest()!=OLD_SHA:
        raise ValueError("HOLD_OLD_SOURCE_SHA_CHANGED")
    with zipfile.ZipFile(args.archive) as z,z.open("2010-2021.csv") as fd:
        old=pd.read_csv(fd,dtype=str,keep_default_na=False,
                        usecols=["horse_id","horse_name","date","place","distance"])
    con=sqlite3.connect(f"file:{args.db}?mode=ro",uri=True)
    def get_rows():
        return con.execute("SELECT hid,name,races FROM horse")
    _,report=anchor_name_histories(old,get_rows)
    con.close()
    report.update({
        "original_archive_sha256":OLD_SHA,
        "independent_sqlite_sha256":"7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9",
        "independent_source_url":"https://huggingface.co/datasets/KBlueLeaf/jp-racing-horse",
        "independent_license_label":"apache-2.0",
        "underlying_source_rights_verified":False,
        "independent_source_date_max":"2025-03-27",
    })
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
