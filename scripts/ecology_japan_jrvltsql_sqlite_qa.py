#!/usr/bin/env python3
"""READ-ONLY audit of a user-authorized JRA-VAN jrvltsql SQLite export.

DO NOT scrape/download JRA/JBIS; do not publish horse master, horse IDs,
licensed race rows or genetic pedigree. Check the actual expected JRVLTSQL
NL_RA, NL_SE, NL_UM, NL_SK, NL_HN table/column contract and quantitative
bridge/completeness coverage. Do NOT infer publication-known timestamps from
JV-Data MakeDate (date only and possibly later updated).
This is a source-readiness gate, NOT the 2027 model training adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

TABLE_COLUMNS = {
    "NL_RA": {
        "Year", "MonthDay", "JyoCD", "Kaiji", "Nichiji", "RaceNum",
        "Kyori", "TrackCD", "HassoTime", "SyussoTosu", "NyusenTosu",
        "MakeDate",
    },
    "NL_SE": {
        "Year", "MonthDay", "JyoCD", "Kaiji", "Nichiji", "RaceNum",
        "KettoNum", "Umaban", "KisyuCode", "ChokyosiCode",
        "KakuteiJyuni", "NyusenJyuni", "IJyoCD", "SexCD", "Barei",
        "MakeDate",
    },
    "NL_UM": {"KettoNum", "MakeDate", "BirthDate", "SexCD"},
    "NL_SK": {"KettoNum", "FNum", "MNum", "MakeDate"},
    "NL_HN": {"HansyokuNum", "KettoNum", "MakeDate"},
}
KEY6 = ("Year", "MonthDay", "JyoCD", "Kaiji", "Nichiji", "RaceNum")
ORIGIN = "miyamamoto/jrvltsql:src/database/schema.py"
DATE_ONLY_FIELDS_CANNOT_CERTIFY_KNOWN_ON = ("MakeDate", "Year", "MonthDay")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for block in iter(lambda: fd.read(2*1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def nonblank(col: str) -> str:
    """Only internal hard-coded column names; empty/all-zero IDs are unknown."""
    allowed = {"KettoNum", "HansyokuNum", "FNum", "MNum"}
    if col not in allowed:
        raise ValueError("HOLD_UNSAFE_OR_UNKNOWN_SQL_COLUMN")
    return f"(TRIM(COALESCE({col},'')) <> '' AND REPLACE(TRIM(COALESCE({col},'')),'0','') <> '')"


def audit(path: Path, *, capture_jra_known_on_certified: bool=False):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("HOLD_MISSING_AUTHORIZED_LOCAL_JRAVAN_SQLITE")
    if capture_jra_known_on_certified:
        # Source schema has no per-event publication-known time. A separately
        # attested ingestion/snapshot log would be essential. Do not accept
        # a user-supplied Boolean as independent authorization or evidence.
        raise ValueError("HOLD_EXTERNAL_PROVIDER_KNOWNON_ATTESTATION_NOT_AVAILABLE")
    uri=path.resolve().as_uri()+"?mode=ro"
    con=sqlite3.connect(uri,uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        names={
            row[0] for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        schema={}
        missing={}
        for table,cols in TABLE_COLUMNS.items():
            if table not in names:
                schema[table]={"present":False}
                missing[table]=["TABLE_ABSENT"]
                continue
            actual={
                str(x[1]) for x in con.execute(f'PRAGMA table_info("{table}")')
            }
            absent=sorted(cols-actual)
            schema[table]={
                "present":True,
                "expected_columns_present":len(cols)-len(absent),
                "expected_columns_total":len(cols),
                "missing_expected_columns":absent,
            }
            if absent:
                missing[table]=absent
        result={
            "status":"HOLD_JRAVAN_SQLITE_SCHEMA_INCOMPLETE" if missing else
                     "JRAVAN_SQLITE_SCHEMA_FOUND_NO_CERTIFIED_KNOWNON",
            "source_sqlite_sha256":sha256(path),
            "source_file_bytes":path.stat().st_size,
            "upstream_expected_contract":ORIGIN,
            "required_table_schema_qa":schema,
            "missing_source_schema":missing,
            "source_owned_license_rights_independently_verified":False,
            "snapshot_result_known_at_jst_present_in_source_contract":False,
            "JV_Data_MakeDate_is_NOT_result_publication_timestamp":True,
            "historical_entry_known_at_jst_present_in_source_contract":False,
            "training_allowed_before_approved_timestamp_snapshot":False,
            "full_JRA_NAR_complete_pedigree_claim_allowed":False,
            "no_row_level_horse_race_IDs_or_names_exported":True,
        }
        if missing:
            return result
        counts={}
        for name in TABLE_COLUMNS:
            counts[name]=int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
        result["table_rows"]=counts
        if not all(counts.values()):
            result["status"]="HOLD_JRAVAN_SQLITE_EMPTY_REQUIRED_TABLE"
            return result

        # Real source-key identity joins; never assume breeding code equals
        # blood-registration ID. All materialized values remain in SQLite.
        source_match=con.execute("""
            SELECT
              COUNT(*) AS result_rows,
              SUM(CASE WHEN um.KettoNum IS NOT NULL THEN 1 ELSE 0 END) AS in_master,
              SUM(CASE WHEN sk.KettoNum IS NOT NULL THEN 1 ELSE 0 END) AS in_progeny
            FROM NL_SE AS se
            LEFT JOIN NL_UM AS um ON se.KettoNum=um.KettoNum
            LEFT JOIN NL_SK AS sk ON se.KettoNum=sk.KettoNum
        """).fetchone()
        result["horse_record_coverage"]={
            "NL_SE_results_total":int(source_match[0]),
            "NL_SE_results_with_NL_UM_master":int(source_match[1]),
            "NL_SE_results_with_NL_SK_parent_master":int(source_match[2]),
        }
        code_qa=con.execute("""
            SELECT
              COUNT(*) AS progeny_rows,
              SUM(CASE WHEN REPLACE(TRIM(COALESCE(FNum,'')),'0','') <> ''
                       THEN 1 ELSE 0 END) AS sire_breeding_ID_known,
              SUM(CASE WHEN REPLACE(TRIM(COALESCE(MNum,'')),'0','') <> ''
                       THEN 1 ELSE 0 END) AS dam_breeding_ID_known,
              SUM(CASE WHEN REPLACE(TRIM(COALESCE(FNum,'')),'0','') <> ''
                        AND REPLACE(TRIM(COALESCE(MNum,'')),'0','') <> ''
                       THEN 1 ELSE 0 END) AS both
            FROM NL_SK
        """).fetchone()
        result["progeny_parent_ID_coverage"]={
            "NL_SK_progeny":int(code_qa[0]),
            "documented_sire_breeding_ID":int(code_qa[1]),
            "documented_dam_breeding_ID":int(code_qa[2]),
            "documented_both_parent_breeding_IDs":int(code_qa[3]),
        }
        # No public names or identifiers. Detect ambiguous blood->breeding
        # reversals and exact breeding->horse coverage with NL_HN.
        bridges=con.execute("""
            SELECT
              SUM(CASE WHEN hns.HansyokuNum IS NOT NULL
                            AND REPLACE(TRIM(COALESCE(hns.KettoNum,'')),'0','')<>'' THEN 1 ELSE 0 END),
              SUM(CASE WHEN hnd.HansyokuNum IS NOT NULL
                            AND REPLACE(TRIM(COALESCE(hnd.KettoNum,'')),'0','')<>'' THEN 1 ELSE 0 END)
            FROM NL_SK AS sk
            LEFT JOIN NL_HN hns ON sk.FNum=hns.HansyokuNum
            LEFT JOIN NL_HN hnd ON sk.MNum=hnd.HansyokuNum
        """).fetchone()
        b_duplicates=con.execute("""
            SELECT COUNT(*) FROM (
              SELECT KettoNum FROM NL_HN
              WHERE REPLACE(TRIM(COALESCE(KettoNum,'')),'0','')<>''
              GROUP BY KettoNum HAVING COUNT(DISTINCT HansyokuNum)>1
            )
        """).fetchone()[0]
        result["typed_parent_namespace_bridge"]={
            "sire_breeding_ID_joined_to_HN_with_blood_ID":int(bridges[0]),
            "dam_breeding_ID_joined_to_HN_with_blood_ID":int(bridges[1]),
            "distinct_blood_ID_with_multiple_HN_breeding_IDs":int(b_duplicates),
            "must_keep_unmapped_parent_as_B_namespace":True,
            "cannot_join_unverified_blood_and_breeding_ID_by_value":True,
        }

        # Race-level completeness, *not* proof of an official census:
        # require at least 2 unique, 1..N consecutive final ranks with
        # agreed RA declared starter count. The result table includes some
        # official exceptions that must be quarantined separately.
        race=con.execute("""
            SELECT
              COUNT(*) AS race_table_rows,
              SUM(CASE WHEN x.n IS NOT NULL THEN 1 ELSE 0 END),
              SUM(CASE WHEN x.n >= 2 AND x.n <= 30
                            AND x.n=ra.SyussoTosu
                            AND x.n_pos=x.n AND x.distinct_pos=x.n
                            AND x.min_pos=1 AND x.max_pos=x.n
                       THEN 1 ELSE 0 END)
            FROM NL_RA ra
            LEFT JOIN (
                SELECT Year,MonthDay,JyoCD,Kaiji,Nichiji,RaceNum,
                  COUNT(*) AS n,
                  SUM(CASE WHEN KakuteiJyuni BETWEEN 1 AND 30
                           THEN 1 ELSE 0 END) AS n_pos,
                  COUNT(DISTINCT CASE WHEN KakuteiJyuni BETWEEN 1 AND 30
                                      THEN KakuteiJyuni END) AS distinct_pos,
                  MIN(CASE WHEN KakuteiJyuni BETWEEN 1 AND 30
                           THEN KakuteiJyuni END) AS min_pos,
                  MAX(CASE WHEN KakuteiJyuni BETWEEN 1 AND 30
                           THEN KakuteiJyuni END) AS max_pos
                FROM NL_SE
                GROUP BY Year,MonthDay,JyoCD,Kaiji,Nichiji,RaceNum
            ) x
            ON ra.Year=x.Year AND ra.MonthDay=x.MonthDay
               AND ra.JyoCD=x.JyoCD AND ra.Kaiji=x.Kaiji
               AND ra.Nichiji=x.Nichiji AND ra.RaceNum=x.RaceNum
        """).fetchone()
        result["race_result_completeness_QA"]={
            "RA_race_rows":int(race[0]),
            "RA_races_with_SE_horse_result_rows":int(race[1]),
            "RA_races_with_consecutive_complete_final_ranks_and_starter_count":int(race[2]),
            "RA_SE_same_source_only_not_independent_official_certification":True,
        }
        # Schema is adequate for an ID-and-finish QA, but MakeDate on its
        # own CANNOT tell what was available before the race forecast.
        result["status"]="HOLD_NO_EXTERNAL_ENTRY_AND_RESULT_PUBLISHED_AT_TIMESTAMPS"
        return result
    finally:
        con.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--authorized-local-db",type=Path,required=True)
    p.add_argument("--aggregate-only-out",type=Path,required=True)
    args=p.parse_args()
    r=audit(args.authorized_local_db)
    args.aggregate_only_out.parent.mkdir(parents=True,exist_ok=True)
    args.aggregate_only_out.write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
