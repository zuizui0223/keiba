"""Synthetic read-only JRA-VAN/jrvltsql source SQL contract QA only."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_jrvltsql_sqlite_qa import audit, sha256


RACE_KEYS=("Year","MonthDay","JyoCD","Kaiji","Nichiji","RaceNum")

def create_fictional_db(path:Path, *, omit=None, omit_column=None, empty=False):
    with sqlite3.connect(path) as con:
        ddl={
            "NL_RA": """
                CREATE TABLE NL_RA (
                  Year INTEGER,MonthDay INTEGER,JyoCD TEXT,Kaiji INTEGER,
                  Nichiji INTEGER,RaceNum INTEGER,Kyori INTEGER,TrackCD TEXT,
                  HassoTime TEXT,SyussoTosu INTEGER,NyusenTosu INTEGER,
                  MakeDate TEXT
                )
            """,
            "NL_SE": """
                CREATE TABLE NL_SE (
                  Year INTEGER,MonthDay INTEGER,JyoCD TEXT,Kaiji INTEGER,
                  Nichiji INTEGER,RaceNum INTEGER,KettoNum TEXT,Umaban INTEGER,
                  KisyuCode TEXT,ChokyosiCode TEXT,KakuteiJyuni INTEGER,
                  NyusenJyuni INTEGER,IJyoCD TEXT,SexCD TEXT,Barei INTEGER,
                  MakeDate TEXT
                )
            """,
            "NL_UM": """
                CREATE TABLE NL_UM (
                    KettoNum TEXT,MakeDate TEXT,BirthDate TEXT,SexCD TEXT
                )
            """,
            "NL_SK": """
                CREATE TABLE NL_SK (
                    KettoNum TEXT,FNum TEXT,MNum TEXT,MakeDate TEXT
                )
            """,
            "NL_HN": """
                CREATE TABLE NL_HN (
                    HansyokuNum TEXT,KettoNum TEXT,MakeDate TEXT
                )
            """,
        }
        for table,sql in ddl.items():
            if table == omit:
                continue
            if table == omit_column:
                sql=sql.replace(",MakeDate TEXT", "")
            con.execute(sql)
        if empty or omit or omit_column:
            return
        for idx in (1,2,3):
            hid=f"200000000{idx}"
            con.execute(
                "INSERT INTO NL_UM VALUES(?,?,?,?)",
                (hid,"20220102","20200301","1")
            )
            con.execute(
                "INSERT INTO NL_SK VALUES(?,?,?,?)",
                (hid,"8000000001","8000000002","20220102")
            )
        con.execute(
            "INSERT INTO NL_HN VALUES(?,?,?)",
            ("8000000001","3000000001","20220102")
        )
        con.execute(
            "INSERT INTO NL_HN VALUES(?,?,?)",
            ("8000000002","3000000002","20220102")
        )
        for race_no,ranks in ((1,(1,2,3)),(2,(1,1,3))):
            con.execute(
                "INSERT INTO NL_RA VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (2024,501,"05",1,1,race_no,1600,"11","1515",3,3,"20240502")
            )
            for idx,rank in enumerate(ranks,start=1):
                con.execute(
                    "INSERT INTO NL_SE VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (2024,501,"05",1,1,race_no,f"200000000{idx}",idx,
                     f"J:{idx}",f"T:{idx}",rank,rank,"0","1",4,"20240502")
                )
        con.commit()


class JrvltsqlReadOnlyQATests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"licensed_fictional_jrvltsql.sqlite"

    def test_real_table_names_ids_progeny_and_complete_ranks(self):
        create_fictional_db(self.path)
        out=audit(self.path)
        self.assertEqual(out["status"],
             "HOLD_NO_EXTERNAL_ENTRY_AND_RESULT_PUBLISHED_AT_TIMESTAMPS")
        self.assertEqual(out["table_rows"]["NL_SE"],6)
        self.assertEqual(out["horse_record_coverage"]["NL_SE_results_with_NL_UM_master"],6)
        self.assertEqual(out["horse_record_coverage"]["NL_SE_results_with_NL_SK_parent_master"],6)
        self.assertEqual(out["progeny_parent_ID_coverage"]["documented_both_parent_breeding_IDs"],3)
        self.assertEqual(out["typed_parent_namespace_bridge"][
            "sire_breeding_ID_joined_to_HN_with_blood_ID"],3)
        self.assertEqual(out["typed_parent_namespace_bridge"][
            "dam_breeding_ID_joined_to_HN_with_blood_ID"],3)
        self.assertEqual(out["race_result_completeness_QA"][
            "RA_races_with_consecutive_complete_final_ranks_and_starter_count"],1)
        self.assertTrue(out["JV_Data_MakeDate_is_NOT_result_publication_timestamp"])
        self.assertFalse(out["training_allowed_before_approved_timestamp_snapshot"])

    def test_no_racing_names_horse_IDs_or_ancestry_exported(self):
        create_fictional_db(self.path)
        out=audit(self.path)
        dump=json.dumps(out,ensure_ascii=False)
        self.assertNotIn("2000000001",dump)
        self.assertNotIn("3000000001",dump)
        self.assertNotIn("8000000001",dump)
        self.assertNotIn("J:1",dump)
        self.assertTrue(out["no_row_level_horse_race_IDs_or_names_exported"])

    def test_read_only_sqlite_no_tables_or_source_modified(self):
        create_fictional_db(self.path)
        digest_before=sha256(self.path)
        a=audit(self.path)
        self.assertEqual(sha256(self.path),digest_before)
        self.assertEqual(a["source_sqlite_sha256"],digest_before)

    def test_missing_blood_to_breeding_table_is_hold(self):
        create_fictional_db(self.path,omit="NL_HN")
        result=audit(self.path)
        self.assertEqual(result["status"],"HOLD_JRAVAN_SQLITE_SCHEMA_INCOMPLETE")
        self.assertIn("NL_HN",result["missing_source_schema"])
        self.assertNotIn("horse_record_coverage",result)

    def test_missing_make_date_cannot_claim_knownon(self):
        create_fictional_db(self.path,omit_column="NL_SK")
        result=audit(self.path)
        self.assertEqual(result["status"],"HOLD_JRAVAN_SQLITE_SCHEMA_INCOMPLETE")
        self.assertIn("MakeDate",result["missing_source_schema"]["NL_SK"])

    def test_empty_source_with_schema_is_hold(self):
        create_fictional_db(self.path,empty=True)
        result=audit(self.path)
        self.assertEqual(result["status"],"HOLD_JRAVAN_SQLITE_EMPTY_REQUIRED_TABLE")

    def test_external_knownon_approval_not_asserted_via_flag(self):
        create_fictional_db(self.path)
        with self.assertRaisesRegex(ValueError,"ATTESTATION_NOT_AVAILABLE"):
            audit(self.path,capture_jra_known_on_certified=True)

    def test_no_real_source_path_rejected(self):
        with self.assertRaisesRegex(ValueError,"MISSING_AUTHORIZED_LOCAL_JRAVAN"):
            audit(self.path)

    def test_expected_columns_schema_is_explicit_jrvltsql(self):
        create_fictional_db(self.path)
        a=audit(self.path)
        self.assertEqual(
            a["required_table_schema_qa"]["NL_SK"]["expected_columns_present"],
            a["required_table_schema_qa"]["NL_SK"]["expected_columns_total"])
        self.assertEqual(a["upstream_expected_contract"],
                         "miyamamoto/jrvltsql:src/database/schema.py")

if __name__=="__main__":
    unittest.main()
