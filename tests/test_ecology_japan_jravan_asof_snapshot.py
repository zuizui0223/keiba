"""Fictional-only JRA-VAN snapshot receipt, temporal and SHA-chain tests."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_jravan_asof_snapshot import (
    capture, receipt_verify, delta_aggregate, SCHEMA
)
from ecology_japan_jrvltsql_sqlite_qa import sha256
from test_ecology_japan_jrvltsql_sqlite_qa import create_fictional_db

JST=timezone(timedelta(hours=9))
RACE="2027-01-09T15:15:00+09:00"


def clock_at(*values):
    iterator=iter(values)
    return lambda:next(iterator)


def stamp(day,hour,minute):
    return datetime(2027,1,day,hour,minute,tzinfo=JST)


class SnapshotReceiptTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory(prefix="jra-snapshot-synthetic-")
        self.addCleanup(self.work.cleanup)
        self.root=Path(self.work.name)
        self.source=self.root/"synthetic_authorized_input.sqlite"
        create_fictional_db(self.source)

    def receipt(self, n, **kwargs):
        priv=self.root/(str(n)+".private.sqlite")
        pub=self.root/(str(n)+".aggregate.json")
        role=kwargs.pop("phase","pre_race")
        when=kwargs.pop("race_start_jst",RACE if role!="master" else None)
        if "clock" not in kwargs:
            kwargs["clock"]=clock_at(stamp(9,12,0),stamp(9,12,1))
        manifest=capture(
            self.source,priv,pub,phase=role,race_start_jst=when,
            **kwargs
        )
        return priv,pub,manifest

    def test_pre_race_receipt_sha_backups_and_no_source_mutation(self):
        old=sha256(self.source)
        private,public,manifest=self.receipt(1)
        self.assertEqual(sha256(self.source),old)
        self.assertEqual(manifest["schema"],SCHEMA)
        self.assertEqual(manifest["private_snapshot_sha256"],sha256(private))
        self.assertTrue(manifest["capture_finished_utc"].endswith("+00:00"))
        self.assertTrue(manifest["source_was_opened_read_only"])
        self.assertTrue(manifest["local_clock_injected_for_synthetic_test"])
        self.assertTrue(manifest["local_clock_NOT_external_timestamp_proof"])
        self.assertFalse(manifest["source_schema_and_coverage_aggregate"][
            "training_allowed_before_approved_timestamp_snapshot"
        ])
        verified=receipt_verify(private,public)
        self.assertEqual(
            verified["status"],
            "LOCAL_SQLITE_RECEIPT_DIGEST_MATCHES_NOT_EXTERNALLY_TIME_ATTESTED"
        )

    def test_public_manifest_has_no_private_horse_race_IDs_or_paths(self):
        private,public,manifest=self.receipt(1)
        dumped=public.read_text()
        for key in ("2000000001","3000000001","8000000001",
                    "synthetic_authorized_input.sqlite",str(private)):
            self.assertNotIn(key,dumped)
        self.assertTrue(manifest[
            "no_horse_ids_names_race_rows_or_individual_predictions_in_receipt"
        ])

    def test_file_mode_only_owner_may_read_private_backup(self):
        private,public,_=self.receipt(1)
        self.assertEqual(private.stat().st_mode & 0o777,0o600)

    def test_mutating_private_snapshot_detected_by_digest(self):
        private,public,_=self.receipt(1)
        with sqlite3.connect(private) as con:
            con.execute("UPDATE NL_RA SET SyussoTosu=99 WHERE RaceNum=1")
            con.commit()
        with self.assertRaisesRegex(ValueError,"HASH_DRIFT"):
            receipt_verify(private,public)

    def test_no_overwrite_prior_snapshot_or_receipt(self):
        private,public,_=self.receipt(1)
        with self.assertRaisesRegex(ValueError,"NO_OVERWRITE"):
            self.receipt(1)
        self.assertTrue(private.is_file())
        self.assertTrue(public.is_file())

    def test_pre_race_capture_must_finish_strictly_before_start(self):
        with self.assertRaisesRegex(ValueError,"NOT_FINISHED_BEFORE_RACE"):
            self.receipt(1,clock=clock_at(stamp(9,14,0),stamp(9,15,15)))
        self.assertFalse((self.root/"1.private.sqlite").exists())
        self.assertFalse((self.root/"1.aggregate.json").exists())

    def test_pre_race_cannot_start_after_target(self):
        with self.assertRaisesRegex(ValueError,"NOT_STARTED_BEFORE_RACE"):
            self.receipt(1,clock=clock_at(stamp(9,15,16),stamp(9,15,17)))

    def test_post_race_cannot_claim_prestart_capture(self):
        with self.assertRaisesRegex(ValueError,"NOT_STARTED_AFTER_RACE"):
            self.receipt(1,phase="post_race",clock=clock_at(
                stamp(9,14,30),stamp(9,16,30)
            ))

    def test_post_race_after_start_has_no_claim_of_result_publication(self):
        _,_,manifest=self.receipt(1,phase="post_race",clock=clock_at(
            stamp(9,17,0),stamp(9,17,1)
        ))
        self.assertTrue(manifest["receiver_possession_not_JRA_publication"])
        self.assertTrue(manifest["MakeDate_NOT_actual_provider_publish_time"])

    def test_master_cannot_claim_target_start(self):
        with self.assertRaisesRegex(ValueError,"MASTER_RECEIPT_HAS_RACE_START"):
            self.receipt(1,phase="master",race_start_jst=RACE)

    def test_time_zone_required_for_target(self):
        with self.assertRaisesRegex(ValueError,"NOT_EXPLICIT_JST"):
            self.receipt(1,race_start_jst="2027-01-09T15:15:00")

    def test_receipt_chain_counts_changed_and_inserted_rows(self):
        p0,m0,_=self.receipt(1,clock=clock_at(stamp(9,12,0),stamp(9,12,1)))
        with sqlite3.connect(self.source) as db:
            db.execute(
                "UPDATE NL_SE SET KakuteiJyuni=2 WHERE RaceNum=1 AND Umaban=1"
            )
            db.execute(
                "INSERT INTO NL_HN VALUES(?,?,?)",
                ("8000000003","3000000003","20240501")
            )
            db.commit()
        p1,m1,after=self.receipt(
            2,phase="post_race",clock=clock_at(stamp(9,17,0),stamp(9,17,1)),
            previous_private=p0,previous_receipt=m0
        )
        self.assertEqual(
            after["prior_source_table_deltas_counts_only"]["NL_SE"]["changed"],1
        )
        self.assertEqual(
            after["prior_source_table_deltas_counts_only"]["NL_HN"]["inserted"],1
        )
        self.assertTrue(after["previous_receipt_sha256"])
        v=receipt_verify(p1,m1,prev_manifest=m0)
        self.assertTrue(v["prior_receipt_chain_present"])

    def test_captured_delta_excludes_removed_source_rows(self):
        p0,m0,_=self.receipt(1)
        with sqlite3.connect(self.source) as db:
            db.execute("DELETE FROM NL_HN WHERE HansyokuNum='8000000001'")
            db.commit()
        p1,m1,m=self.receipt(2,phase="post_race",clock=clock_at(
            stamp(9,17,0),stamp(9,17,1)
        ),previous_receipt=m0,previous_private=p0)
        self.assertEqual(m["prior_source_table_deltas_counts_only"][
            "NL_HN"]["removed"],1)

    def test_earlier_receipt_digest_tampering_refused(self):
        p0,m0,_=self.receipt(1)
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE NL_SE SET KakuteiJyuni=3 WHERE RaceNum=1 AND Umaban=1")
            db.commit()
        p1,m1,_=self.receipt(2,phase="post_race",clock=clock_at(
            stamp(9,17,0),stamp(9,17,1)
        ),previous_receipt=m0,previous_private=p0)
        m0.write_text(m0.read_text()+" ")
        with self.assertRaisesRegex(ValueError,"PREVIOUS_RECEIPT_HASH_DRIFT"):
            receipt_verify(p1,m1,prev_manifest=m0)

    def test_chain_requires_previous_private_and_manifest_together(self):
        p0,m0,_=self.receipt(1)
        with self.assertRaisesRegex(ValueError,"MUST_PAIR"):
            self.receipt(2,phase="post_race",clock=clock_at(
                stamp(9,17,0),stamp(9,17,1)
            ),previous_receipt=m0)

    def test_previous_receipt_must_be_older(self):
        p0,m0,_=self.receipt(1,clock=clock_at(
            stamp(9,12,0),stamp(9,12,1)
        ))
        with self.assertRaisesRegex(ValueError,"TIME_NOT_EARLIER"):
            self.receipt(2,clock=clock_at(
                stamp(9,11,59),stamp(9,12,0)
            ),previous_receipt=m0,previous_private=p0)

    def test_previous_snapshot_mutation_fails_before_delta(self):
        p0,m0,_=self.receipt(1)
        with sqlite3.connect(p0) as db:
            db.execute("UPDATE NL_RA SET SyussoTosu=18 WHERE RaceNum=2")
            db.commit()
        with self.assertRaisesRegex(ValueError,"HASH_DRIFT"):
            self.receipt(2,phase="post_race",clock=clock_at(
                stamp(9,17,0),stamp(9,17,1)
            ),previous_receipt=m0,previous_private=p0)

    def test_three_stage_chain_pre_post_master_preserves_each_snapshot(self):
        p0,m0,_=self.receipt(1,clock=clock_at(
            stamp(9,12,0),stamp(9,12,1)
        ))
        p1,m1,_=self.receipt(2,phase="post_race",clock=clock_at(
            stamp(9,17,0),stamp(9,17,1)
        ),previous_receipt=m0,previous_private=p0)
        p2,m2,r=self.receipt(3,phase="master",clock=clock_at(
            stamp(9,18,0),stamp(9,18,1)
        ),previous_receipt=m1,previous_private=p1)
        self.assertIsNotNone(r["previous_receipt_sha256"])
        self.assertTrue(r["only_immediate_previous_snapshot_verified_on_new_capture"])
        self.assertTrue(receipt_verify(p2,m2,prev_manifest=m1)[
            "prior_receipt_chain_present"])
        # The prior link must itself be verified separately; the most recent
        # manifest cannot attest all earlier ancestors without their files.
        self.assertTrue(receipt_verify(p1,m1,prev_manifest=m0)[
            "prior_receipt_chain_present"])
        with self.assertRaisesRegex(ValueError,"PREVIOUS_RECEIPT_REQUIRED_FOR_CHAIN"):
            receipt_verify(p2,m2)

    def test_capture_rejects_private_path_inside_git_checkout(self):
        # Prevent accidentally uploading private JRA data into public repo.
        from ecology_japan_jravan_asof_snapshot import _safe_private_output
        in_checkout=Path.cwd()/"DO_NOT_CREATE_CAPTURE_IN_REPO.sqlite"
        if not (Path.cwd()/".git").exists():
            self.skipTest("Git checkout only")
        with self.assertRaisesRegex(ValueError,"INSIDE_GIT_TREE"):
            _safe_private_output(self.source,in_checkout,
                                 self.root/"public-aggregate-only.json")
        self.assertFalse(in_checkout.exists())

    def test_chain_with_unchanged_source_reports_zero_revisions(self):
        p0,m0,_=self.receipt(1)
        _,_,m=self.receipt(2,phase="post_race",clock=clock_at(
            stamp(9,17,0),stamp(9,17,1)
        ),previous_receipt=m0,previous_private=p0)
        self.assertEqual(m["prior_source_table_deltas_counts_only"]["NL_SE"][
            "changed"],0)
        self.assertEqual(m["prior_source_table_deltas_counts_only"]["NL_SE"][
            "unchanged"],6)

    def test_future_target_does_not_make_fake_2018_knownon(self):
        _,_,m=self.receipt(1)
        self.assertFalse(m["source_schema_and_coverage_aggregate"][
            "historical_entry_known_at_jst_present_in_source_contract"
        ])
        self.assertTrue(m[
            "must_commit_aggregate_receipt_before_target_start_for_independent_review"
        ])
        self.assertTrue(m["2027_real_race_knowntime_or_genetic_effect_NOT_established"])

    def test_clock_callback_is_explicitly_synthetic_not_a_trusted_attestor(self):
        _,_,m=self.receipt(1)
        self.assertTrue(m["local_clock_injected_for_synthetic_test"])
        self.assertTrue(m["local_clock_NOT_external_timestamp_proof"])


if __name__=="__main__":
    unittest.main()
