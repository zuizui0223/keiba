"""Synthetic pre/post captured JRA-VAN SQLite to PRIVATE 2027 ledger CSVs."""
from __future__ import annotations
import csv
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_jravan_snapshot_adapter import (
    pre_aggregate, post_aggregate, _write_private_csv, _write_public,
    _track_map, _reg, _race_key
)
from ecology_japan_jravan_asof_snapshot import capture, sha256
from ecology_japan_2027_official_knownon_preflight import (
    ENTRY_REQUIRED, PARENT_REQUIRED, HISTORY_REQUIRED, read_csv
)
from test_ecology_japan_jrvltsql_sqlite_qa import create_fictional_db

JST=timezone(timedelta(hours=9))
SOURCE_RACE="2027,109,05,1,1,1"
START="2027-01-09T15:15:00+09:00"


def stamp(hour,minute):
    return datetime(2027,1,9,hour,minute,tzinfo=JST)


def fake_clock(t0,t1):
    times=iter((t0,t1))
    return lambda:next(times)


def populated_future_source(path):
    create_fictional_db(path)
    with sqlite3.connect(path) as con:
        con.execute("DELETE FROM NL_RA WHERE RaceNum=2")
        con.execute("DELETE FROM NL_SE WHERE RaceNum=2")
        con.execute(
            "UPDATE NL_RA SET Year=2027,MonthDay=109,HassoTime='1515' "
            "WHERE RaceNum=1"
        )
        con.execute(
            "UPDATE NL_SE SET Year=2027,MonthDay=109, "
            "KakuteiJyuni=0,NyusenJyuni=0 WHERE RaceNum=1"
        )
        con.commit()


class PrePostAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="synthetic-JRA-prepost-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/"synthetic_source.sqlite"
        populated_future_source(self.source)
        self.track=self.root/"source_approved_track_map.json"
        self.track.write_text('{"11":"turf"}',encoding="utf-8")

    def captured_pre(self):
        priv=self.root/"pre_private.sqlite"
        pub=self.root/"pre_summary.json"
        capture(self.source,priv,pub,phase="pre_race",race_start_jst=START,
                clock=fake_clock(stamp(12,0),stamp(12,1)))
        return priv,pub

    def captured_post(self,pre_snapshot,pre_receipt):
        priv=self.root/"post_private.sqlite"
        pub=self.root/"post_summary.json"
        with sqlite3.connect(self.source) as con:
            con.execute(
                "UPDATE NL_SE SET KakuteiJyuni=Umaban,NyusenJyuni=Umaban "
                "WHERE RaceNum=1"
            )
            con.commit()
        capture(self.source,priv,pub,phase="post_race",race_start_jst=START,
                clock=fake_clock(stamp(17,0),stamp(17,1)),
                previous_private=pre_snapshot,
                previous_receipt=pre_receipt)
        return priv,pub

    def pre(self):
        p,m=self.captured_pre()
        return pre_aggregate(p,m,self.track,SOURCE_RACE,
                             allow_synthetic_clock=True),p,m

    def test_pre_complete_typed_official_entrant_and_parent_records(self):
        (rows,parents,meta),p,m=self.pre()
        self.assertEqual(len(rows),3)
        self.assertEqual(len(parents),3)
        self.assertEqual(meta["declared_source_entrant_count"],3)
        self.assertEqual(meta["known_sire_IDs"],3)
        self.assertEqual(meta["known_dam_IDs"],3)
        self.assertEqual(set(rows[0]),set(ENTRY_REQUIRED))
        self.assertEqual(set(parents[0]),set(PARENT_REQUIRED))
        self.assertEqual(rows[0]["entry_known_at_jst"],
                         "2027-01-09T12:01:01+09:00")
        self.assertEqual(parents[0]["pedigree_master_known_at_jst"],
                         "2027-01-09T12:01:00+09:00")
        self.assertEqual(rows[0]["surface"],"turf")
        self.assertEqual(rows[0]["distance_m"],"1600")
        self.assertTrue(rows[0]["horse_id"].startswith("H:"))
        self.assertTrue(parents[0]["sire_id"].startswith("B:"))
        self.assertFalse(meta["input_certifies_provider_publication_timestamp"])

    def test_post_complete_result_exact_snapshot_chain(self):
        (entries,parents,meta),pre,pre_m=self.pre()
        post,post_m=self.captured_post(pre,pre_m)
        rows,summary=post_aggregate(
            pre,pre_m,post,post_m,self.track,SOURCE_RACE,
            allow_synthetic_clock=True)
        self.assertEqual(len(rows),3)
        self.assertEqual(set(rows[0]),set(HISTORY_REQUIRED))
        self.assertEqual(sorted(int(r["finish_rank"]) for r in rows),[1,2,3])
        self.assertEqual(rows[0]["result_known_at_jst"],
                         "2027-01-09T17:01:01+09:00")
        self.assertTrue(summary[
            "source_records_were_captured_in_two_separate_snapshot_roles"])
        self.assertEqual(summary["source_pre_receipt_SHA256"],sha256(pre_m))
        self.assertEqual(summary["post_receipt_SHA256"],sha256(post_m))

    def test_missing_track_map_code_hard_hold_not_guess_surface(self):
        pre,receipt=self.captured_pre()
        self.track.write_text('{"21":"dirt"}',encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"UNMAPPED_SOURCE_TRACK"):
            pre_aggregate(pre,receipt,self.track,SOURCE_RACE,
                          allow_synthetic_clock=True)

    def test_no_untyped_or_numeric_parent_ID_equivalence(self):
        self.assertEqual(_reg("8000000001",parent=True),"B:8000000001")
        self.assertEqual(_reg("8000000001",parent=False),"H:8000000001")
        self.assertEqual(_reg("0000000000",parent=True),"")
        with self.assertRaisesRegex(ValueError,"INVALID_SOURCE_BLOOD"):
            _reg("SHORT",parent=False)

    def test_pre_capture_with_2027_final_rank_is_temporal_HOLD(self):
        with sqlite3.connect(self.source) as con:
            con.execute(
                "UPDATE NL_SE SET KakuteiJyuni=1 WHERE RaceNum=1 AND Umaban=1")
            con.commit()
        pre,receipt=self.captured_pre()
        with self.assertRaisesRegex(ValueError,"FINAL_RANK_ALREADY_IN_PRE"):
            pre_aggregate(pre,receipt,self.track,SOURCE_RACE,
                          allow_synthetic_clock=True)

    def test_pre_capture_with_arrival_rank_is_temporal_HOLD(self):
        with sqlite3.connect(self.source) as con:
            con.execute("UPDATE NL_SE SET NyusenJyuni=1 WHERE RaceNum=1 AND Umaban=1")
            con.commit()
        pre,receipt=self.captured_pre()
        with self.assertRaisesRegex(ValueError,"FINAL_RANK_ALREADY_IN_PRE"):
            pre_aggregate(pre,receipt,self.track,SOURCE_RACE,
                          allow_synthetic_clock=True)

    def test_source_declared_field_cannot_omit_runner(self):
        with sqlite3.connect(self.source) as con:
            con.execute("UPDATE NL_RA SET SyussoTosu=4 WHERE RaceNum=1")
            con.commit()
        pre,receipt=self.captured_pre()
        with self.assertRaisesRegex(ValueError,"ENTRANTS_NOT_COMPLETE"):
            pre_aggregate(pre,receipt,self.track,SOURCE_RACE,
                          allow_synthetic_clock=True)

    def test_pre_snapshot_horse_master_must_contain_each_child(self):
        with sqlite3.connect(self.source) as con:
            con.execute("DELETE FROM NL_UM WHERE KettoNum='2000000001'")
            con.commit()
        pre,receipt=self.captured_pre()
        with self.assertRaisesRegex(ValueError,"HORSE_NOT_IN_UNIQUE_OFFICIAL"):
            pre_aggregate(pre,receipt,self.track,SOURCE_RACE,
                          allow_synthetic_clock=True)

    def test_synthetic_clock_cannot_masquerade_as_actual_evidence(self):
        pre,receipt=self.captured_pre()
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_CLOCK_NOT_ACCEPTED"):
            pre_aggregate(pre,receipt,self.track,SOURCE_RACE)

    def test_pre_receipt_start_must_equal_actual_source_header(self):
        with sqlite3.connect(self.source) as con:
            con.execute("UPDATE NL_RA SET HassoTime='1520' WHERE RaceNum=1")
            con.commit()
        pre,receipt=self.captured_pre()
        with self.assertRaisesRegex(ValueError,"RACE_START_MISMATCH"):
            pre_aggregate(pre,receipt,self.track,SOURCE_RACE,
                          allow_synthetic_clock=True)

    def test_post_result_ties_or_rank_gaps_cannot_get_2027_scores(self):
        (rows,parents,meta),pre,pre_m=self.pre()
        post,post_m=self.captured_post(pre,pre_m)
        with sqlite3.connect(post) as con:
            con.execute(
                "UPDATE NL_SE SET KakuteiJyuni=1 WHERE RaceNum=1 AND Umaban=2"
            )
            con.commit()
        with self.assertRaisesRegex(ValueError,"HASH_DRIFT"):
            post_aggregate(pre,pre_m,post,post_m,self.track,SOURCE_RACE,
                           allow_synthetic_clock=True)

    def test_post_result_attested_source_tie_holds_without_mutating_snapshot(self):
        (rows,parents,meta),pre,pre_m=self.pre()
        with sqlite3.connect(self.source) as con:
            con.execute("UPDATE NL_SE SET KakuteiJyuni=1,NyusenJyuni=1 WHERE RaceNum=1")
            con.commit()
        post=self.root/"post_private.sqlite"
        post_m=self.root/"post_summary.json"
        capture(self.source,post,post_m,phase="post_race",race_start_jst=START,
                clock=fake_clock(stamp(17,0),stamp(17,1)),
                previous_private=pre,previous_receipt=pre_m)
        with self.assertRaisesRegex(ValueError,"TIED_GAPPED_OR_INVALID"):
            post_aggregate(pre,pre_m,post,post_m,self.track,SOURCE_RACE,
                           allow_synthetic_clock=True)

    def test_post_rider_replacement_is_not_silently_carried_over(self):
        (rows,parents,meta),pre,pre_m=self.pre()
        with sqlite3.connect(self.source) as con:
            con.execute(
                "UPDATE NL_SE SET KakuteiJyuni=Umaban,NyusenJyuni=Umaban,"
                "KisyuCode='00999' WHERE RaceNum=1 AND Umaban=1"
            )
            con.commit()
        post=self.root/"post_private.sqlite"
        post_m=self.root/"post_summary.json"
        capture(self.source,post,post_m,phase="post_race",race_start_jst=START,
                clock=fake_clock(stamp(17,0),stamp(17,1)),
                previous_private=pre,previous_receipt=pre_m)
        with self.assertRaisesRegex(ValueError,"RIDER_CHANGED"):
            post_aggregate(pre,pre_m,post,post_m,self.track,SOURCE_RACE,
                           allow_synthetic_clock=True)

    def test_unchained_post_receipt_rejected(self):
        (rows,parents,meta),pre,pre_m=self.pre()
        with sqlite3.connect(self.source) as con:
            con.execute(
                "UPDATE NL_SE SET KakuteiJyuni=Umaban,NyusenJyuni=Umaban WHERE RaceNum=1"
            )
            con.commit()
        post=self.root/"post_private.sqlite"
        post_m=self.root/"post_summary.json"
        capture(self.source,post,post_m,phase="post_race",race_start_jst=START,
                clock=fake_clock(stamp(17,0),stamp(17,1)))
        with self.assertRaisesRegex(ValueError,"POST_RECEIPT_NOT_CHAINED"):
            post_aggregate(pre,pre_m,post,post_m,self.track,SOURCE_RACE,
                           allow_synthetic_clock=True)

    def test_private_CSVs_do_not_leak_to_public_summary(self):
        (entries,parents,meta),pre,pre_m=self.pre()
        e_path=self.root/"private_entries.csv"
        p_path=self.root/"private_parent_master.csv"
        summary=self.root/"public_aggregates.json"
        _write_private_csv(e_path,ENTRY_REQUIRED,entries)
        _write_private_csv(p_path,PARENT_REQUIRED,parents)
        public=_write_public(summary,meta,{"entries":e_path,"parents":p_path})
        self.assertEqual(len(read_csv(e_path,ENTRY_REQUIRED)),3)
        self.assertEqual(len(read_csv(p_path,PARENT_REQUIRED)),3)
        self.assertEqual(e_path.stat().st_mode & 0o777,0o600)
        dump=summary.read_text(encoding="utf-8")
        self.assertNotIn("2000000001",dump)
        self.assertNotIn("8000000001",dump)
        self.assertTrue(public["privacy_no_source_horse_IDs_names_or_race_rows_in_public"])
        self.assertIn("entries",public["private_normalized_CSV_SHA256"])

    def test_no_overwrite_private_CSV_output(self):
        (entries,parents,meta),pre,pre_m=self.pre()
        e_path=self.root/"existing_private.csv"
        _write_private_csv(e_path,ENTRY_REQUIRED,entries)
        with self.assertRaisesRegex(ValueError,"NEVER_OVERWRITE"):
            _write_private_csv(e_path,ENTRY_REQUIRED,entries)

    def test_unknown_source_race_key_not_selected_by_name(self):
        with self.assertRaisesRegex(ValueError,"SIX_PART"):
            _race_key("Tokyo Meisho 1R")
        with self.assertRaisesRegex(ValueError,"UNTYPED_SOURCE"):
            _race_key("2027,abc,05,1,1,1")


if __name__=="__main__":
    unittest.main()
