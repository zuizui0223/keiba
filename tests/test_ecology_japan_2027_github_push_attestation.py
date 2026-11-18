"""Fictional-only GitHub pre-race source/forecast attestation unit tests."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2027_github_push_attestation import (
    SOURCE_SCHEMA, ADAPTER_SCHEMA, FORECAST_SCHEMA, BUNDLE_SCHEMA,
    _sha, build_bundle, validate_bundle, attest_run, open_originals,
    _write_new, _fetch_current_run
)

SOURCE_START="2027-01-09T11:59:00+09:00"
SOURCE_FINISH="2027-01-09T12:01:00+09:00"
SOURCE_FINISH_UTC="2027-01-09T03:01:00+00:00"
SOURCE_START_UTC="2027-01-09T02:59:00+00:00"
FIRST_OBSERVED="2027-01-09T12:01:01+09:00"
FORECAST_ASOF="2027-01-09T12:02:00+09:00"
FORECAST_FREEZE="2027-01-09T03:04:00+00:00"
RUN_CREATED="2027-01-09T03:05:00Z"
RACE_START="2027-01-09T15:15:00+09:00"
EXPECTED_SHA="ab"*20
REPO="zuizui0223/keiba"


def dump(x):
    return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")


def fixture(synthetic=True):
    raw_private={
        "target_outcomes_included":False,
        "model_spec_sha256":"d"*64,
        "private_horse_level_predictions":True,
        "predictions":[{"horse_id":"H:SYN001","race_id":"JRA:SYN","M0":.5,"M1":.4,"M2":.3}]
    }
    private=dump(raw_private)
    source={
        "schema":SOURCE_SCHEMA,
        "capture_phase":"pre_race",
        "capture_started_utc":SOURCE_START_UTC,
        "capture_finished_utc":SOURCE_FINISH_UTC,
        "capture_finished_jst":SOURCE_FINISH,
        "target_race_start_jst":RACE_START,
        "private_snapshot_sha256":"1"*64,
        "local_clock_injected_for_synthetic_test":synthetic,
        "local_clock_NOT_external_timestamp_proof":True,
        "MakeDate_NOT_actual_provider_publish_time":True,
        "must_commit_aggregate_receipt_before_target_start_for_independent_review":True,
    }
    src=dump(source)
    adapter={
        "schema":ADAPTER_SCHEMA,
        "status":"PRIVATE_PRE_RACE_EXTRACTED_LOCAL_FIRST_OBSERVED_NOT_PROVIDER_ATTESTED",
        "source_pre_receipt_SHA256":_sha(src),
        "source_pre_private_snapshot_SHA256":source["private_snapshot_sha256"],
        "private_track_map_SHA256":"2"*64,
        "private_normalized_CSV_SHA256":{
            "entries":"3"*64,"parents":"4"*64},
        "declared_source_entrant_count":3,
        "first_observed_entry_known_at_jst":FIRST_OBSERVED,
        "earliest_target_start_at_jst":RACE_START,
        "input_certifies_provider_publication_timestamp":False,
        "synthetic_test_only":synthetic,
        "privacy_no_source_horse_IDs_names_or_race_rows_in_public":True,
    }
    ada=dump(adapter)
    forecast={
        "schema":FORECAST_SCHEMA,
        "status":"PRIVATE_PRE_RACE_FORECAST_COMMITTED_UNSCORED",
        "target":"JRA_2027_JAN_JUN_FLAT_ONLY",
        "earliest_target_start_at_jst":RACE_START,
        "asof_at_jst":FORECAST_ASOF,
        "frozen_at_utc":FORECAST_FREEZE,
        "races":1,"starts":3,"unique_horses":3,
        "input_SHA256":{
            "entries":"3"*64,"parents":"4"*64,"history":"5"*64,"model":"d"*64
        },
        "private_prediction_file_SHA256":_sha(private),
        "no_2027_target_results_used":True,
        "no_horse_or_race_IDs_in_public_manifest":True,
        "local_timestamp_and_digest_alone_NOT_trusted_external_proof":True,
    }
    fore=dump(forecast)
    return src,ada,fore,private


def fake_run(created=RUN_CREATED, *, event="push", head_sha=EXPECTED_SHA,
             repo=REPO):
    return {
        "id":1234567890,
        "event":event,
        "head_sha":head_sha,
        "repository":{"full_name":repo},
        "created_at":created,
        "status":"completed","conclusion":"success",
    }


class PreRaceServerAttestationTests(unittest.TestCase):
    def setUp(self):
        self.src,self.ada,self.fore,self.private=fixture()

    def bundle(self):
        return build_bundle(self.src,self.ada,self.fore,allow_synthetic=True)

    def test_manifest_whitelist_never_embeds_private_horse_identifiers(self):
        b=self.bundle()
        self.assertEqual(b["schema"],BUNDLE_SCHEMA)
        serialized=json.dumps(b,ensure_ascii=False)
        for sensitive in ("H:SYN001","JRA:SYN","horse_id",
                          "private_horse_level_predictions",
                          "predictions"):
            self.assertNotIn(sensitive,serialized)
        self.assertEqual(b["source_capture"]["private_snapshot_sha256"],"1"*64)
        self.assertEqual(b["frozen_prediction_commitment"]["starts"],3)

    def test_before_race_git_server_creation_is_conditional_external_gate(self):
        att=attest_run(self.bundle(),fake_run(),repo=REPO,sha=EXPECTED_SHA,
                       allow_synthetic=True)
        self.assertEqual(
            att["status"],
            "GITHUB_PUSH_SERVER_TIME_BEFORE_DECLARED_RACE_VERIFIED_CONDITIONAL")
        self.assertTrue(att["external_pre_race_timestamp_verified"])
        self.assertTrue(att["local_source_possession_and_jra_publish_time_not_verified"])

    def test_source_synthetic_clock_cannot_pass_real_attestation(self):
        b=self.bundle()
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_CLOCK_OR_SOURCE"):
            validate_bundle(b)
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_CLOCK_OR_SOURCE"):
            attest_run(b,fake_run(),repo=REPO,sha=EXPECTED_SHA)

    def test_non_synthetic_flags_allow_validation_but_still_need_server_run(self):
        a,b,c,d=fixture(synthetic=False)
        x=build_bundle(a,b,c)
        result=validate_bundle(x)
        self.assertFalse(result["external_pre_race_timestamp_verified"])
        self.assertIn("UNATTESTED",x["status"])
        self.assertNotIn("github_run_id",result)

    def test_github_run_after_declared_race_must_fail(self):
        with self.assertRaisesRegex(ValueError,"GITHUB_SERVER_RUN_CREATED_AFTER_RACE"):
            attest_run(self.bundle(),fake_run("2027-01-09T06:15:00Z"),
                       repo=REPO,sha=EXPECTED_SHA,allow_synthetic=True)

    def test_github_run_created_before_forecast_freeze_must_fail(self):
        with self.assertRaisesRegex(ValueError,"GITHUB_SERVER_RUN_CREATED_AFTER_RACE"):
            attest_run(self.bundle(),fake_run("2027-01-09T03:03:59Z"),
                       repo=REPO,sha=EXPECTED_SHA,allow_synthetic=True)

    def test_never_accept_retroactive_manual_dispatch_or_pull_request(self):
        for event in ("workflow_dispatch","pull_request","schedule","issue_comment"):
            with self.subTest(event=event):
                with self.assertRaisesRegex(ValueError,"GITHUB_PUSH_REPO"):
                    attest_run(self.bundle(),fake_run(event=event),
                               repo=REPO,sha=EXPECTED_SHA,allow_synthetic=True)

    def test_github_repo_and_exact_committed_head_sha_required(self):
        for bad in (fake_run(head_sha="c"*40),fake_run(repo="other/keiba")):
            with self.assertRaisesRegex(ValueError,"GITHUB_PUSH_REPO"):
                attest_run(self.bundle(),bad,repo=REPO,sha=EXPECTED_SHA,
                           allow_synthetic=True)

    def test_bundle_rejects_future_2026_instead_of_2027(self):
        s=json.loads(self.src)
        a=json.loads(self.ada)
        f=json.loads(self.fore)
        for v,key in ((s,"target_race_start_jst"),
                      (a,"earliest_target_start_at_jst"),
                      (f,"earliest_target_start_at_jst")):
            v[key]="2026-01-09T15:15:00+09:00"
        a["source_pre_receipt_SHA256"]=_sha(dump(s))
        with self.assertRaisesRegex(ValueError,"FUTURE_WINDOW"):
            build_bundle(dump(s),dump(a),dump(f),allow_synthetic=True)

    def test_bundle_rejects_wrong_pre_snapshot_digest(self):
        a=json.loads(self.ada)
        a["source_pre_private_snapshot_SHA256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SOURCE_ADAPTER_RECEIPT_SHA"):
            build_bundle(self.src,dump(a),self.fore,allow_synthetic=True)

    def test_bundle_rejects_source_receipt_file_digest_changed(self):
        a=json.loads(self.ada)
        a["source_pre_receipt_SHA256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SOURCE_ADAPTER_RECEIPT_SHA"):
            build_bundle(self.src,dump(a),self.fore,allow_synthetic=True)

    def test_mismatched_private_entry_hash_cannot_be_committed(self):
        f=json.loads(self.fore)
        f["input_SHA256"]["entries"]="e"*64
        with self.assertRaisesRegex(ValueError,"ENTRIES_OR_PARENTS_DRIFT"):
            build_bundle(self.src,self.ada,dump(f),allow_synthetic=True)

    def test_parent_master_hash_changed_fails(self):
        f=json.loads(self.fore)
        f["input_SHA256"]["parents"]="e"*64
        with self.assertRaisesRegex(ValueError,"ENTRIES_OR_PARENTS_DRIFT"):
            build_bundle(self.src,self.ada,dump(f),allow_synthetic=True)

    def test_one_source_receipt_cannot_attest_multiple_races(self):
        f=json.loads(self.fore)
        f["races"]=2
        with self.assertRaisesRegex(ValueError,"MULTIPLE_OR_PARTIAL_RACES"):
            build_bundle(self.src,self.ada,dump(f),allow_synthetic=True)

    def test_incomplete_entrant_count_and_horse_count_fail(self):
        for key,value in (("starts",2),("unique_horses",2)):
            with self.subTest(key=key):
                f=json.loads(self.fore)
                f[key]=value
                with self.assertRaisesRegex(ValueError,"MULTIPLE_OR_PARTIAL_RACES"):
                    build_bundle(self.src,self.ada,dump(f),allow_synthetic=True)

    def test_exact_first_observed_source_time_is_required(self):
        a=json.loads(self.ada)
        a["first_observed_entry_known_at_jst"]=SOURCE_FINISH
        with self.assertRaisesRegex(ValueError,"FIRST_SEEN_BOUND"):
            build_bundle(self.src,dump(a),self.fore,allow_synthetic=True)

    def test_forecast_freeze_before_first_observed_source_fails(self):
        f=json.loads(self.fore)
        f["frozen_at_utc"]="2027-01-09T03:00:00+00:00"
        with self.assertRaisesRegex(ValueError,"TIME_ORDER"):
            build_bundle(self.src,self.ada,dump(f),allow_synthetic=True)

    def test_jra_publication_time_is_never_inferred_from_receipt(self):
        b=self.bundle()
        a=b["private_pre_normalization_aggregate"]
        a["input_certifies_provider_publication_timestamp"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_PROVENANCE"):
            validate_bundle(b,allow_synthetic=True)

    def test_never_allow_extra_identifying_fields_in_bundle(self):
        b=self.bundle()
        b["horse_name"]="SYNTHETIC_HORSE"
        with self.assertRaisesRegex(ValueError,"UNKNOWN_OR_MISSING_FIELDS"):
            validate_bundle(b,allow_synthetic=True)
        b=self.bundle()
        b["source_capture"]["NL_SE_names"]=["SYNTHETIC"]
        with self.assertRaisesRegex(ValueError,"WHITELIST_NOT_EXACT"):
            validate_bundle(b,allow_synthetic=True)

    def test_postrace_private_forecast_sha_opening_success(self):
        b=self.bundle()
        opened=open_originals(
            b,source=self.src,adapter=self.ada,forecast=self.fore,
            private_predictions=self.private,allow_synthetic=True)
        self.assertEqual(opened["status"],
            "ORIGINAL_PRIVATE_FORECAST_AND_SOURCE_MANIFEST_SHA_OPENING_PASSED")
        self.assertFalse(opened["aggregate_bundle_timing_independently_attested_here"])

    def test_postrace_modified_horse_prediction_fails_digest(self):
        b=self.bundle()
        bad=json.loads(self.private)
        bad["predictions"][0]["M2"]=.9
        with self.assertRaisesRegex(ValueError,"FORECAST_SHA_DRIFT"):
            open_originals(b,source=self.src,adapter=self.ada,
                           forecast=self.fore,private_predictions=dump(bad),
                           allow_synthetic=True)

    def test_postrace_modified_original_manifest_fails_digest(self):
        b=self.bundle()
        bad=self.fore+b" \n"
        with self.assertRaisesRegex(ValueError,"AGGREGATE_MANIFEST_SHA_DRIFT"):
            open_originals(b,source=self.src,adapter=self.ada,forecast=bad,
                           private_predictions=self.private,allow_synthetic=True)

    def test_postrace_private_model_hash_can_not_be_swapped(self):
        b=self.bundle()
        bad=json.loads(self.private)
        bad["model_spec_sha256"]="0"*64
        f=json.loads(self.fore)
        f["private_prediction_file_SHA256"]=_sha(dump(bad))
        fake=self.bundle()
        fake["frozen_prediction_commitment"]["private_prediction_file_SHA256"]=_sha(dump(bad))
        # The ORIGINAL byte digest of the public forecast MUST also change;
        # this is not a valid opening of the previously committed bundle.
        with self.assertRaisesRegex(ValueError,"AGGREGATE_MANIFEST_SHA_DRIFT"):
            open_originals(fake,source=self.src,adapter=self.ada,
                           forecast=dump(f),private_predictions=dump(bad),
                           allow_synthetic=True)

    def test_public_bundle_file_write_is_no_overwrite(self):
        b=self.bundle()
        with tempfile.TemporaryDirectory() as tmp:
            from ecology_japan_2027_github_push_attestation import _write_new
            p=Path(tmp)/"blind_sha_commit.json"
            _write_new(p,b)
            with self.assertRaisesRegex(ValueError,"NEVER_OVERWRITE"):
                _write_new(p,b)
            self.assertNotIn("H:SYN",p.read_text(encoding="utf-8"))

    def test_real_github_attestation_requires_push_environment(self):
        from unittest.mock import patch
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaisesRegex(ValueError,"NOT_A_GITHUB_PUSH"):
                _fetch_current_run()


if __name__=="__main__":
    unittest.main()
