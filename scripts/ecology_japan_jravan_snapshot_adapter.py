#!/usr/bin/env python3
"""Adapt TWO private captured jrvltsql SQLite versions to private 2027 CSVs.

PRE: entries and B:-typed parent master only from complete pre-race snapshot.
POST: final 1..N result rows only from a SHA-linked later snapshot.

The conservative known-at timestamps are local *observed finished-backup*
times + one second, NOT source-published event times. Only for future
prospective races with these pre/post snapshots; retrospective 2018-24
timestamps CANNOT be reconstructed. Never publish horse/race rows, source
table files, or predict any outcome. No provider API/scraping.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import sqlite3

from ecology_japan_jravan_asof_snapshot import (
    SCHEMA as RECEIPT_SCHEMA, receipt_verify, sha256
)
from ecology_japan_2027_official_knownon_preflight import (
    local_jst, ENTRY_REQUIRED, PARENT_REQUIRED, HISTORY_REQUIRED
)
from ecology_japan_2027_point_in_time_ledger import _private_destination

JRA_TRACK_SURFACE = ("turf","dirt")
KEY = ("Year","MonthDay","JyoCD","Kaiji","Nichiji","RaceNum")
PRE_COLUMNS = (
    "KettoNum","Umaban","KisyuCode","ChokyosiCode",
    "SexCD","Barei","KakuteiJyuni"
)
POST_COLUMNS = PRE_COLUMNS+("IJyoCD",)
SCHEMA = "JRA_2027_PRIVATE_PRE_POST_SNAPSHOT_CSV_ADAPTER_V1"


def _race_key(raw:str):
    parts=str(raw).split(",")
    if len(parts)!=6:
        raise ValueError("HOLD_JRA_SIX_PART_SOURCE_RACE_KEY_REQUIRED")
    year,monthday,jyo,kaiji,nichiji,race_num=(
        parts[0],parts[1],parts[2],parts[3],parts[4],parts[5]
    )
    if not (len(year)==4 and year.isdigit() and
            monthday.isdigit() and jyo.isdigit() and
            kaiji.isdigit() and nichiji.isdigit() and race_num.isdigit()):
        raise ValueError("HOLD_JRA_UNTYPED_SOURCE_RACE_KEY")
    return (int(year),int(monthday),jyo.zfill(2),
            int(kaiji),int(nichiji),int(race_num))


def _read_receipt(db:Path,manifest_path:Path,expected_role:str,
                  *,previous_manifest:Path|None=None,
                  allow_synthetic_clock:bool=False):
    receipt_verify(db,manifest_path,prev_manifest=previous_manifest)
    rec=json.loads(manifest_path.read_text(encoding="utf-8"))
    if rec.get("schema")!=RECEIPT_SCHEMA or rec.get("capture_phase")!=expected_role:
        raise ValueError("HOLD_WRONG_SOURCE_CAPTURE_ROLE")
    if rec.get("local_clock_injected_for_synthetic_test") and not allow_synthetic_clock:
        raise ValueError("HOLD_SYNTHETIC_CLOCK_NOT_ACCEPTED_AS_SOURCE")
    if rec.get("source_schema_and_coverage_aggregate",{}).get(
            "missing_source_schema",{"UNKNOWN":1}
    ):
        raise ValueError("HOLD_SOURCE_REQUIRED_TABLE_SCHEMA_INCOMPLETE")
    finished=local_jst(rec["capture_finished_jst"])
    start=local_jst(rec["target_race_start_jst"])
    if expected_role=="pre_race" and not finished<start:
        raise ValueError("HOLD_PRE_ENTRY_SNAPSHOT_AFTER_START")
    if expected_role=="post_race" and not finished>start:
        raise ValueError("HOLD_POST_RESULT_SNAPSHOT_BEFORE_START")
    return rec,finished,start


def _fields(con,table):
    rows=con.execute(f'PRAGMA table_info("{table}")').fetchall()
    return {row[1] for row in rows}


def _select_race(con,table,key,fields):
    if not set(KEY).issubset(_fields(con,table)):
        raise ValueError("HOLD_SOURCE_RACE_KEYS_ABSENT")
    if not set(fields).issubset(_fields(con,table)):
        raise ValueError("HOLD_SOURCE_ENTRANT_OR_RESULT_COLUMN_MISSING")
    where=" AND ".join('"'+x+'"=?' for x in KEY)
    cols=", ".join('"'+x+'"' for x in fields)
    return con.execute(f'SELECT {cols} FROM "{table}" WHERE {where}',
                       tuple(key)).fetchall()


def _racing_start(ra, key):
    year,mmdd,jyo,k,n,rnum=key
    day=f"{year:04d}-{mmdd//100:02d}-{mmdd%100:02d}"
    raw=str(ra["HassoTime"]).strip()
    if len(raw)!=4 or not raw.isdigit():
        raise ValueError("HOLD_SOURCE_RACE_START_TIME_UNCERTIFIED")
    hour,minute=int(raw[:2]),int(raw[2:])
    if hour>23 or minute>59:
        raise ValueError("HOLD_SOURCE_BAD_RACE_START_HHMM")
    return local_jst(day+f"T{hour:02d}:{minute:02d}:00+09:00")


def _reg(raw, *, parent=False):
    s=str(raw or "").strip()
    if parent and (not s or all(c=="0" for c in s)):
        return ""
    if len(s)!=10 or not s.isascii() or not s.isdigit() or s=="0000000000":
        raise ValueError("HOLD_INVALID_SOURCE_BLOOD_OR_BREEDING_ID")
    return ("B:" if parent else "H:")+s


def _track_map(path:Path):
    d=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(d,dict) or not d:
        raise ValueError("HOLD_MISSING_AUTHORITATIVE_TRACK_SURFACE_MAP")
    out={}
    for k,v in d.items():
        if not isinstance(k,str) or not k.isdigit() or v not in JRA_TRACK_SURFACE:
            raise ValueError("HOLD_INVALID_TRACK_SURFACE_MAPPING")
        out[k]=v
    return out


def _pre_data(con,key,track_map,rec,done,start):
    con.row_factory=sqlite3.Row
    ra=_select_race(con,"NL_RA",key,
                    ("Kyori","TrackCD","HassoTime","SyussoTosu"))
    if len(ra)!=1:
        raise ValueError("HOLD_EXPECT_EXACT_ONE_PRE_RACE_HEADER")
    ra=ra[0]
    actual=_racing_start(ra,key)
    if actual!=start:
        raise ValueError("HOLD_RECEIPT_RACE_START_MISMATCH_OFFICIAL_RA")
    available=done+timedelta(seconds=1)
    if not available<start:
        raise ValueError("HOLD_PRE_ENTRY_FIRST_OBSERVED_AFTER_RACE_START")
    track=str(ra["TrackCD"]).strip()
    if track not in track_map:
        raise ValueError("HOLD_UNMAPPED_SOURCE_TRACK_SURFACE_CODE")
    surface=track_map[track]
    try:
        distance=int(ra["Kyori"])
        declared=int(ra["SyussoTosu"])
    except (TypeError,ValueError):
        raise ValueError("HOLD_RACE_CONDITIONS_MISSING") from None
    if not 600<=distance<=4000 or not 2<=declared<=30:
        raise ValueError("HOLD_DECLARED_SOURCE_ENTRANT_OR_DISTANCE_RANGE")
    entrants=_select_race(con,"NL_SE",key,PRE_COLUMNS)
    if len(entrants)!=declared:
        raise ValueError("HOLD_PRE_RACE_ENTRANTS_NOT_COMPLETE_DECLARED_FIELD")
    ids=set()
    horses=[]
    for row in entrants:
        horse=_reg(row["KettoNum"])
        if horse in ids:
            raise ValueError("HOLD_DUPLICATE_SOURCE_BLOOD_REGISTRY_HORSE")
        ids.add(horse)
        try:
            number=int(row["Umaban"])
            age=int(row["Barei"])
            final=int(row["KakuteiJyuni"] or 0)
        except (TypeError,ValueError):
            raise ValueError("HOLD_INVALID_PRE_RACE_AGE_NUMBER_RANK") from None
        if not 1<=number<=declared or not 2<=age<=20:
            raise ValueError("HOLD_INVALID_PRE_RACE_AGE_OR_HORSE_NUMBER")
        if final>0:
            # Source C had final results in the supposedly PRE-race snapshot.
            # This indicates leakage, incorrect start time, or data fabrication.
            raise ValueError("HOLD_FINAL_RANK_ALREADY_IN_PRE_RACE_SNAPSHOT")
        code=str(row["SexCD"]).strip()
        sex={"1":"M","2":"F","3":"G","0":"U"}.get(code)
        if sex is None:
            raise ValueError("HOLD_UNKNOWN_SOURCE_SEX_CODE")
        jockey=str(row["KisyuCode"] or "").strip()
        trainer=str(row["ChokyosiCode"] or "").strip()
        if not (jockey and trainer):
            raise ValueError("HOLD_MISSING_SOURCE_PRE_RACE_RIDER_OR_TRAINER")
        horses.append({
            "_raw_id":horse[2:],"_number":number,
            "horse_id":horse,"race_id":"JRA:"+"-".join([
                str(key[0]),str(key[1]).zfill(4),key[2],
                str(key[3]),str(key[4]),str(key[5])]),
            "race_start_at_jst":start.isoformat(),
            "entry_known_at_jst":available.isoformat(),
            "course_id":"JRA_JYO:"+key[2],
            "surface":surface,"distance_m":str(distance),
            "sex":sex,"age":str(age),
            "jockey_id":"JRA_KISYU:"+jockey,
            "trainer_id":"JRA_CHOKYOSI:"+trainer
        })
    if len({h["_number"] for h in horses})!=declared:
        raise ValueError("HOLD_DUPLICATE_UMABAN_IN_SOURCE_ENTRANTS")

    if not set(("KettoNum","FNum","MNum")).issubset(_fields(con,"NL_SK")):
        raise ValueError("HOLD_SOURCE_PROGENY_PARENT_COLUMNS_ABSENT")
    parents=[]
    for horse in horses:
        sk=con.execute(
            "SELECT FNum,MNum FROM NL_SK WHERE KettoNum=?",
            (horse["_raw_id"],)
        ).fetchall()
        if len(sk)>1:
            raise ValueError("HOLD_DUPLICATE_PROGENY_MASTER_ID")
        sire=_reg(sk[0]["FNum"],parent=True) if sk else ""
        dam=_reg(sk[0]["MNum"],parent=True) if sk else ""
        if sire and dam and sire==dam:
            raise ValueError("HOLD_SAME_PARENT_SIRE_AND_DAM")
        if "KettoNum" not in _fields(con,"NL_UM"):
            raise ValueError("HOLD_NO_BLOOD_ID_HORSE_MASTER_COLUMN")
        um=con.execute(
            "SELECT COUNT(*) FROM NL_UM WHERE KettoNum=?",
            (horse["_raw_id"],)
        ).fetchone()[0]
        if um!=1:
            raise ValueError("HOLD_HORSE_NOT_IN_UNIQUE_OFFICIAL_UM_MASTER")
        parents.append({
            "horse_id":horse["horse_id"],
            "sire_id":sire,"dam_id":dam,
            "pedigree_master_known_at_jst":done.isoformat(),
        })
    # Private output no source-local join helpers, umaban or horse name.
    fields=[{k:h[k] for k in ENTRY_REQUIRED} for h in horses]
    return horses,fields,parents


def pre_aggregate(pre_snapshot:Path, pre_receipt:Path,track_map_path:Path,
                  source_race_key:str,*,allow_synthetic_clock=False):
    pre,finish,start=_read_receipt(
        pre_snapshot,pre_receipt,"pre_race",
        allow_synthetic_clock=allow_synthetic_clock
    )
    tracks=_track_map(track_map_path)
    key=_race_key(source_race_key)
    with sqlite3.connect(pre_snapshot.resolve().as_uri()+"?mode=ro",
                         uri=True) as conn:
        conn.execute("PRAGMA query_only=ON")
        horses,entries,parents=_pre_data(conn,key,tracks,pre,finish,start)
    summary={
        "schema":SCHEMA,
        "status":"PRIVATE_PRE_RACE_EXTRACTED_LOCAL_FIRST_OBSERVED_NOT_PROVIDER_ATTESTED",
        "source_pre_receipt_SHA256":sha256(pre_receipt),
        "source_pre_private_snapshot_SHA256":pre["private_snapshot_sha256"],
        "private_track_map_SHA256":sha256(track_map_path),
        "declared_source_entrant_count":len(entries),
        "known_sire_IDs":sum(bool(p["sire_id"]) for p in parents),
        "known_dam_IDs":sum(bool(p["dam_id"]) for p in parents),
        "first_observed_entry_known_at_jst":entries[0]["entry_known_at_jst"],
        "earliest_target_start_at_jst":start.isoformat(),
        "input_certifies_provider_publication_timestamp":False,
        "first_observed_receipt_time_not_historic_source_publication":True,
        "pre_race_event_first_seen_at_local_receipt_only":True,
        "no_actual_forecasts_or_genetic_results_generated":True,
        "privacy_no_source_horse_IDs_names_or_race_rows_in_public":True,
        "synthetic_test_only":bool(allow_synthetic_clock),
    }
    return entries,parents,summary


def post_aggregate(pre_snapshot:Path,pre_receipt:Path,
                   post_snapshot:Path,post_receipt:Path,
                   track_map_path:Path, source_race_key:str,
                   *,allow_synthetic_clock=False):
    entries,parents,pre_qa=pre_aggregate(
        pre_snapshot,pre_receipt,track_map_path,source_race_key,
        allow_synthetic_clock=allow_synthetic_clock)
    post,finished,start=_read_receipt(
        post_snapshot,post_receipt,"post_race",
        previous_manifest=pre_receipt,
        allow_synthetic_clock=allow_synthetic_clock
    )
    if post["previous_receipt_sha256"]!=sha256(pre_receipt):
        raise ValueError("HOLD_POST_RECEIPT_NOT_CHAINED_TO_PRE_RACE_SNAPSHOT")
    if start!=local_jst(pre_qa["earliest_target_start_at_jst"]):
        raise ValueError("HOLD_PRE_POST_SOURCE_TARGET_RACE_TIME_CONFLICT")
    key=_race_key(source_race_key)
    by_horse={e["horse_id"]:e for e in entries}
    if not finished>start:
        raise ValueError("HOLD_POST_RACE_CAPTURE_BEFORE_START")
    with sqlite3.connect(post_snapshot.resolve().as_uri()+"?mode=ro",uri=True) as conn:
        conn.row_factory=sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        ra=_select_race(conn,"NL_RA",key,("HassoTime","Kyori","TrackCD","SyussoTosu"))
        if len(ra)!=1:
            raise ValueError("HOLD_POST_RACE_HEADER_MISSING_OR_DUPLICATED")
        if _racing_start(ra[0],key)!=start:
            raise ValueError("HOLD_POST_RACE_START_CHANGED_FROM_FROZEN_ENTRY")
        if str(ra[0]["Kyori"])!=entries[0]["distance_m"]:
            raise ValueError("HOLD_POST_RACE_DISTANCE_CHANGED")
        track=_track_map(track_map_path)
        if track.get(str(ra[0]["TrackCD"]).strip())!=entries[0]["surface"]:
            raise ValueError("HOLD_POST_RACE_SURFACE_CHANGED")
        postrows=_select_race(conn,"NL_SE",key,POST_COLUMNS)
    if len(postrows)!=len(entries) or int(ra[0]["SyussoTosu"])!=len(entries):
        raise ValueError("HOLD_POST_RACE_ENTRANT_COUNT_CHANGED")
    ranks=[]
    final=[]
    seen=set()
    for row in postrows:
        horse=_reg(row["KettoNum"])
        if horse not in by_horse or horse in seen:
            raise ValueError("HOLD_POST_RACE_HORSE_ID_NOT_IN_PRE_RACE_SNAPSHOT")
        seen.add(horse)
        if str(row["KisyuCode"] or "").strip()!=by_horse[horse]["jockey_id"].split(":",1)[1]:
            raise ValueError("HOLD_POST_RACE_RIDER_CHANGED_FROM_PRE_RACE")
        if str(row["ChokyosiCode"] or "").strip()!=by_horse[horse]["trainer_id"].split(":",1)[1]:
            raise ValueError("HOLD_POST_RACE_TRAINER_CHANGED_FROM_PRE_RACE")
        if str(row["IJyoCD"] or "").strip() not in ("","0"):
            raise ValueError("HOLD_POST_RACE_DNF_OR_NONSTANDARD_STATUS")
        try:
            rank=int(row["KakuteiJyuni"])
        except (TypeError,ValueError):
            raise ValueError("HOLD_POST_RACE_NOT_ALL_FINAL_RANKS") from None
        ranks.append(rank)
        final.append({
            "race_id":by_horse[horse]["race_id"],
            "horse_id":horse,
            "race_start_at_jst":start.isoformat(),
            "result_known_at_jst":(finished+timedelta(seconds=1)).isoformat(),
            "finish_rank":str(rank),
            "classified_field_size":str(len(entries)),
            "finish_status":"CLASSIFIED",
        })
    if sorted(ranks)!=list(range(1,len(entries)+1)):
        raise ValueError("HOLD_TIED_GAPPED_OR_INVALID_FINAL_SOURCE_RANKS")
    summary={
        **pre_qa,
        "status":"PRIVATE_POST_RACE_EXTRACTED_LOCAL_FIRST_OBSERVED_NOT_PROVIDER_ATTESTED",
        "post_receipt_SHA256":sha256(post_receipt),
        "post_snapshot_sha256":post["private_snapshot_sha256"],
        "source_confirmed_complete_starter_and_final_rank_count":len(final),
        "result_first_observed_jst":final[0]["result_known_at_jst"],
        "source_records_were_captured_in_two_separate_snapshot_roles":True,
        "no_2027_outcome_predicted_by_adapter":True,
    }
    return final,summary


def _write_private_csv(path:Path,columns:tuple[str,...],rows:list[dict]):
    _private_destination(path)
    if path.exists():
        raise ValueError("HOLD_NEVER_OVERWRITE_PRIVATE_SOURCE_EXPORT")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8",newline="") as fd:
        os=None
        writer=csv.DictWriter(fd,fieldnames=columns,extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    path.chmod(0o600)


def _write_public(path:Path,qa:dict, private_outputs:dict):
    if path.exists():
        raise ValueError("HOLD_NEVER_OVERWRITE_PUBLIC_SOURCE_QA")
    m={**qa,
       "private_normalized_CSV_SHA256":{
            k:sha256(p) for k,p in private_outputs.items()
       },
       "public_receipt_must_be_externally_time_committed_before_race":True,
       "source_licensing_and_received_at_clock_not_third_party_attested":True,
    }
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
                    encoding="utf-8")
    return m


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="command",required=True)
    pre=sub.add_parser("pre")
    post=sub.add_parser("post")
    for x in (pre,post):
        x.add_argument("--pre-snapshot",type=Path,required=True)
        x.add_argument("--pre-receipt",type=Path,required=True)
        x.add_argument("--track-surface-map",type=Path,required=True)
        x.add_argument("--source-race-key",required=True)
        x.add_argument("--public-summary-out",type=Path,required=True)
    pre.add_argument("--private-entries-out",type=Path,required=True)
    pre.add_argument("--private-parents-out",type=Path,required=True)
    post.add_argument("--post-snapshot",type=Path,required=True)
    post.add_argument("--post-receipt",type=Path,required=True)
    post.add_argument("--private-results-out",type=Path,required=True)
    a=ap.parse_args()
    if a.command=="pre":
        entries,parents,s=pre_aggregate(
            a.pre_snapshot,a.pre_receipt,a.track_surface_map,a.source_race_key)
        _write_private_csv(a.private_entries_out,ENTRY_REQUIRED,entries)
        _write_private_csv(a.private_parents_out,PARENT_REQUIRED,parents)
        m=_write_public(a.public_summary_out,s,{
            "entries":a.private_entries_out,"parents":a.private_parents_out
        })
    else:
        rows,s=post_aggregate(
            a.pre_snapshot,a.pre_receipt,a.post_snapshot,a.post_receipt,
            a.track_surface_map,a.source_race_key)
        _write_private_csv(a.private_results_out,HISTORY_REQUIRED,rows)
        m=_write_public(a.public_summary_out,s,{
            "results":a.private_results_out
        })
    print(json.dumps(m,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
