"""Fictional-only 2027 universe sealed-forecast/replay tests.

No real JRA-VAN source, registered horse ID, live racing result, 2027 race
forecast or official scheduled-race universe appears in these tests.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parent))

from ecology_japan_2027_point_in_time_ledger import (
    freeze, canonical_bytes,
)
from ecology_japan_2027_github_push_attestation import (
    SOURCE_SCHEMA, ADAPTER_SCHEMA,
    _sha, build_bundle, content_addressed_bundle_filename,
)
from ecology_japan_2027_immutable_universe_pledge import (
    make_pledge,content_addressed_filename,_validated_pledge,
    attest_original_universe,check_current_universe_push,sealed_score,
    WORKFLOW_PATH,SCHEMA,REPO,_universe
)
from test_ecology_japan_2027_point_in_time_ledger import (
    fictional, completed_results, fake_sha, ASOF, CLOCK
)


def fake():
    entries,parents,history,model=fictional()
    only_race=entries[0]["race_id"]
    entries=[v for v in entries if v["race_id"]==only_race]
    private,manifest=freeze(
        entries,parents,history,model,
        asof=ASOF,clock=CLOCK,source_sha=fake_sha())
    private_raw=canonical_bytes(private)
    manifest_raw=canonical_bytes(manifest)
    src={
        "schema":SOURCE_SCHEMA,"capture_phase":"pre_race",
        "capture_started_utc":"2027-01-08T08:58:00+00:00",
        "capture_finished_utc":"2027-01-08T08:59:00+00:00",
        "capture_finished_jst":"2027-01-08T17:59:00+09:00",
        "target_race_start_jst":manifest["earliest_target_start_at_jst"],
        "private_snapshot_sha256":"1"*64,
        "local_clock_injected_for_synthetic_test":True,
        "local_clock_NOT_external_timestamp_proof":True,
        "MakeDate_NOT_actual_provider_publish_time":True,
        "must_commit_aggregate_receipt_before_target_start_for_independent_review":True,
    }
    src_raw=canonical_bytes(src)
    ada={
        "schema":ADAPTER_SCHEMA,
        "status":"PRIVATE_PRE_RACE_EXTRACTED_LOCAL_FIRST_OBSERVED_NOT_PROVIDER_ATTESTED",
        "source_pre_receipt_SHA256":_sha(src_raw),
        "source_pre_private_snapshot_SHA256":"1"*64,
        "private_track_map_SHA256":"2"*64,
        "private_normalized_CSV_SHA256":{
            "entries":fake_sha()["entries"],"parents":fake_sha()["parents"]},
        "declared_source_entrant_count":3,
        "first_observed_entry_known_at_jst":"2027-01-08T17:59:01+09:00",
        "earliest_target_start_at_jst":manifest["earliest_target_start_at_jst"],
        "input_certifies_provider_publication_timestamp":False,
        "synthetic_test_only":True,
        "privacy_no_source_horse_IDs_names_or_race_rows_in_public":True,
    }
    bundle=build_bundle(src_raw,canonical_bytes(ada),
                        manifest_raw,allow_synthetic=True)
    bundle_raw=canonical_bytes(bundle)
    schedule=(
        "race_id,race_start_at_jst,eligibility_known_at_jst\n"
        f"{only_race},2027-01-09T15:15:00+09:00,"
        "2027-01-08T17:30:00+09:00\n"
    ).encode("utf-8")
    return {
        "private":private_raw,"forecast_manifest":manifest_raw,
        "bundle":bundle_raw,"bundle_obj":bundle,"schedule":schedule,
        "results":completed_results(entries),
        "eligible_race":only_race,
    }


COMMIT_FORECAST="ab"*20
COMMIT_UNIVERSE="cd"*20
RUN_FORECAST=4510001
RUN_UNIVERSE=4510002
RUN_DATE_UNIVERSE="2027-01-09T01:00:00Z"
RUN_DATE_FORECAST="2027-01-09T02:00:00Z"


def original_github_get(scenario, pledge_raw, *, missing_file=False):
    fc_path=("docs/commitments/2027/"
             +content_addressed_bundle_filename(scenario["bundle_obj"]))
    uv_obj=json.loads(pledge_raw)
    uv_path="docs/commitments/2027-universe/"+content_addressed_filename(uv_obj)
    blobs={
        (COMMIT_UNIVERSE,uv_path):pledge_raw,
        (COMMIT_FORECAST,fc_path):scenario["bundle"],
    }
    def fake_github(url):
        if url.endswith(f"/actions/runs/{RUN_UNIVERSE}"):
            return {
                "id":RUN_UNIVERSE,
                "run_attempt":1,"status":"completed","conclusion":"success",
                "path":WORKFLOW_PATH,
                "event":"push","head_sha":COMMIT_UNIVERSE,
                "repository":{"full_name":REPO},
                "created_at":RUN_DATE_UNIVERSE,
            }
        if url.endswith(f"/actions/runs/{RUN_FORECAST}"):
            return {
                "id":RUN_FORECAST,
                "run_attempt":1,"status":"completed","conclusion":"success",
                "path":".github/workflows/ecology-japan-2027-immutable-push-attestation.yml",
                "event":"push","head_sha":COMMIT_FORECAST,
                "repository":{"full_name":REPO},
                "created_at":RUN_DATE_FORECAST,
            }
        if "/contents/" in url:
            for (sha,path),raw in blobs.items():
                if f"/contents/{path}?ref={sha}" in url:
                    if missing_file and path==uv_path:
                        raise ValueError("FAKE_FILE_UNAVAILABLE")
                    git_sha=hashlib.sha1(
                        ("blob "+str(len(raw))+"\0").encode()+raw
                    ).hexdigest()
                    return {
                        "type":"file","encoding":"base64","path":path,
                        "sha":git_sha,
                        "content":base64.b64encode(raw).decode(),
                    }
        raise ValueError("FAKE_GITHUB_UNEXPECTED_REQUEST")
    return fake_github,uv_path,fc_path


class ImmutableDenominatorTests(unittest.TestCase):
    def setUp(self):
        self.fx=fake()
        self.pledge=make_pledge(
            self.fx["schedule"],self.fx["private"],
            self.fx["forecast_manifest"],self.fx["bundle"],
            allow_synthetic=True)
        self.raw=canonical_bytes(self.pledge)
        self.github,self.uv_path,self.fc_path=original_github_get(self.fx,self.raw)

    def post(self, *, schedule=None,pledge=None,github=None,results=None,
             bundle=None,private=None,manifest=None):
        return sealed_score(
            schedule if schedule is not None else self.fx["schedule"],
            private if private is not None else self.fx["private"],
            manifest if manifest is not None else self.fx["forecast_manifest"],
            bundle if bundle is not None else self.fx["bundle"],
            pledge if pledge is not None else self.raw,
            results if results is not None else self.fx["results"],
            universe_commit_sha=COMMIT_UNIVERSE,universe_run_id=RUN_UNIVERSE,
            universe_path=self.uv_path,
            forecast_commit_sha=COMMIT_FORECAST,forecast_run_id=RUN_FORECAST,
            forecast_path=self.fc_path,github_json_get=github or self.github,
            allow_synthetic=True)

    def test_private_schedule_forecast_bundle_hashes_and_privacy(self):
        p=self.pledge
        self.assertEqual(p["schema"],SCHEMA)
        self.assertEqual(p["forecast_races"],1)
        self.assertEqual(p["forecast_starts"],3)
        self.assertEqual(p["pretarget_eligible_races_declared"],1)
        self.assertEqual(p["pretarget_eligible_races_not_forecast"],0)
        self.assertEqual(p["pre_race_private_prediction_sha256"],
                         _sha(self.fx["private"]))
        self.assertEqual(p["private_eligible_universe_csv_sha256"],
                         _sha(self.fx["schedule"]))
        for s in ("JRA:FAKE","H:111","B:FAKE7","predictions",
                  "KettoNum","race_id","horse_id"):
            self.assertNotIn(s,json.dumps(p))
        self.assertEqual(content_addressed_filename(p),
                         self.uv_path.rsplit("/",1)[-1])

    def test_synthetic_only_original_commit_and_complete_forecast_open(self):
        r=self.post()
        self.assertEqual(
            r["status"],"SYNTHETIC_REHEARSAL_ONLY_NOT_REAL_LICENSED_JRA_FORECAST")
        self.assertTrue(r["original_forecast_source_bundle_verified_on_Github_pre_race"])
        self.assertTrue(r["original_private_schedule_hash_bound_on_Github_pre_race"])
        self.assertEqual(r["frozen_denominator_audit"]["frozen_races"],1)
        self.assertEqual(r["frozen_denominator_audit"]["frozen_starts"],3)
        self.assertFalse(r["source_JRA_schedule_completeness_independently_certified"])
        self.assertFalse(r["real_2027_model_ability_or_genetics_proven"])

    def test_valid_extra_source_eligible_race_is_visible_not_discarded(self):
        s=self.fx["schedule"]+(
            b"JRA:FAKE_EXTRA,2027-01-10T15:15:00+09:00,"
            b"2027-01-08T17:30:00+09:00\n")
        p=make_pledge(s,self.fx["private"],self.fx["forecast_manifest"],
                      self.fx["bundle"],allow_synthetic=True)
        raw=canonical_bytes(p)
        gh,up,fp=original_github_get(self.fx,raw)
        r=sealed_score(
            s,self.fx["private"],self.fx["forecast_manifest"],
            self.fx["bundle"],raw,self.fx["results"],
            universe_commit_sha=COMMIT_UNIVERSE,universe_run_id=RUN_UNIVERSE,
            universe_path=up,forecast_commit_sha=COMMIT_FORECAST,
            forecast_run_id=RUN_FORECAST,forecast_path=fp,
            github_json_get=gh,allow_synthetic=True)
        self.assertEqual(p["pretarget_eligible_races_not_forecast"],1)
        self.assertEqual(r["frozen_denominator_audit"][
            "source_eligible_race_universe_coverage"]["eligible_races_without_a_frozen_prediction"],1)
        self.assertIsNone(r["frozen_denominator_audit"]["MSE_gain_bounds"][
            "M1_minus_M2_full_frozen_population_MSE"]["min_feasible_MSE_difference"])
        self.assertEqual(r["frozen_denominator_audit"]["MSE_gain_bounds"][
            "M1_minus_M2_full_frozen_population_MSE"]["status"],
            "HOLD_MISSING_FORECASTS_IN_SUPPLIED_SOURCE_UNIVERSE")

    def test_changed_private_universe_after_pushing_is_rejected(self):
        bad=self.fx["schedule"].replace(
            b"17:30:00",b"17:31:00")
        with self.assertRaisesRegex(ValueError,"PLEDGE_BYTES_CHANGED"):
            self.post(schedule=bad)

    def test_modifying_private_forecast_after_original_pledge_rejected(self):
        x=json.loads(self.fx["private"])
        x["predictions"][0]["M1"]=.777
        with self.assertRaisesRegex(ValueError,"PREDICTION_BYTES_NOT_FROZEN_SHA"):
            self.post(private=canonical_bytes(x))

    def test_original_forecast_manifest_byte_mutation_is_rejected(self):
        altered=self.fx["forecast_manifest"]+b" "
        with self.assertRaisesRegex(ValueError,"MANIFEST_SHA_NOT_MATCHED"):
            self.post(manifest=altered)

    def test_forecast_bundle_changed_even_if_structurally_valid_holds(self):
        altered=self.fx["bundle"]+b" "
        with self.assertRaisesRegex(ValueError,"PLEDGE_BYTES_CHANGED"):
            self.post(bundle=altered)

    def test_wrong_original_git_blob_sha_rejected(self):
        orig=self.github
        def broken(url):
            x=orig(url)
            if "/contents/" in url and "2027-universe" in url:
                return {**x,"sha":"0"*40}
            return x
        with self.assertRaisesRegex(ValueError,"GIT_BLOB_DRIFT"):
            self.post(github=broken)

    def test_forged_pre_race_github_push_attempt_fails(self):
        orig=self.github
        def replay(url):
            x=orig(url)
            if url.endswith(f"/actions/runs/{RUN_UNIVERSE}"):
                return {**x,"run_attempt":2}
            return x
        with self.assertRaisesRegex(ValueError,"PUSH_RUN_NOT_TRUSTED"):
            self.post(github=replay)

    def test_wrong_eligible_universe_workflow_fails(self):
        orig=self.github
        def wrong(url):
            x=orig(url)
            if url.endswith(f"/actions/runs/{RUN_UNIVERSE}"):
                return {**x,"path":".github/workflows/other.yml"}
            return x
        with self.assertRaisesRegex(ValueError,"PUSH_RUN_NOT_TRUSTED"):
            self.post(github=wrong)

    def test_push_created_after_first_eligible_race_fails(self):
        orig=self.github
        def late(url):
            x=orig(url)
            if url.endswith(f"/actions/runs/{RUN_UNIVERSE}"):
                return {**x,"created_at":"2027-01-09T07:00:00Z"}
            return x
        with self.assertRaisesRegex(ValueError,"NOT_BEFORE_FIRST_ELIGIBLE_RACE"):
            self.post(github=late)

    def test_original_forecast_server_success_is_required(self):
        orig=self.github
        def failed(url):
            x=orig(url)
            if url.endswith(f"/actions/runs/{RUN_FORECAST}"):
                return {**x,"conclusion":"failure"}
            return x
        with self.assertRaisesRegex(ValueError,"ATTESTATION_NOT_SUCCESS"):
            self.post(github=failed)

    def test_mock_github_rest_is_forbidden_in_production(self):
        with self.assertRaisesRegex(ValueError,"FAKE_REST_NOT_ALLOWED"):
            sealed_score(
                self.fx["schedule"],self.fx["private"],
                self.fx["forecast_manifest"],self.fx["bundle"],
                self.raw,self.fx["results"],
                universe_commit_sha=COMMIT_UNIVERSE,universe_run_id=RUN_UNIVERSE,
                universe_path=self.uv_path,
                forecast_commit_sha=COMMIT_FORECAST,forecast_run_id=RUN_FORECAST,
                forecast_path=self.fc_path,github_json_get=self.github)

    def test_synthetic_rehearsal_bundle_is_rejected_in_real_mode(self):
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_CLOCK_OR_SOURCE"):
            make_pledge(
                self.fx["schedule"],self.fx["private"],
                self.fx["forecast_manifest"],self.fx["bundle"])

    def test_late_schedule_eligibility_at_freeze_holds(self):
        s=self.fx["schedule"].replace(
            b"17:30:00",b"21:00:00")
        with self.assertRaisesRegex(ValueError,"TARGET_UNIVERSE_DUPLICATE_LATE"):
            make_pledge(
                s,self.fx["private"],self.fx["forecast_manifest"],
                self.fx["bundle"],allow_synthetic=True)

    def test_missing_forecasted_race_from_universe_rejected(self):
        s=(
            b"race_id,race_start_at_jst,eligibility_known_at_jst\n"
            b"JRA:OTHER_RACE,2027-01-09T15:15:00+09:00,"
            b"2027-01-08T17:30:00+09:00\n")
        with self.assertRaisesRegex(ValueError,"FORECAST_OUTSIDE_DECLARED_RACE_UNIVERSE"):
            make_pledge(s,self.fx["private"],
                        self.fx["forecast_manifest"],self.fx["bundle"],
                        allow_synthetic=True)

    def test_raw_private_schedule_not_public_and_pseudocertification_rejected(self):
        forbidden={**self.pledge,"horse_id":"H:NOT_ALLOWED"}
        with self.assertRaisesRegex(ValueError,"UNWHITELISTED_FIELDS"):
            _validated_pledge(forbidden,allow_synthetic=True)
        dangerous={**self.pledge,
                   "official_race_universe_completeness_not_certified":False}
        with self.assertRaisesRegex(ValueError,"FALSE_PROVENANCE_FLAG"):
            _validated_pledge(dangerous,allow_synthetic=True)

    def test_wrong_original_content_address_filename_fails(self):
        with self.assertRaisesRegex(ValueError,"ORIGINAL_COMMIT_RUN_OR_FILENAME"):
            attest_original_universe(
                self.raw,original_commit_sha=COMMIT_UNIVERSE,
                original_run_id=RUN_UNIVERSE,
                relative_path="docs/commitments/2027-universe/"+"0"*32+".json",
                github_json_get=self.github,allow_synthetic=True)

    def test_dnf_still_has_unidentified_population_MSE(self):
        outcomes=copy.deepcopy(self.fx["results"])
        outcomes[0]["finish_status"]="DNF"
        outcomes[0]["finish_rank"]=""
        r=self.post(results=outcomes)
        self.assertIsNone(r["frozen_denominator_audit"]["MSE_gain_bounds"][
            "M1_minus_M2_full_frozen_population_MSE"]["min_feasible_MSE_difference"])

    def test_current_workflow_cannot_certify_its_own_future_completion(self):
        r={
            "id":RUN_UNIVERSE,"head_sha":COMMIT_UNIVERSE,
            "event":"push","run_attempt":1,
            "path":WORKFLOW_PATH,"repository":{"full_name":REPO},
            "created_at":RUN_DATE_UNIVERSE,
            "status":"in_progress","conclusion":None,
        }
        out=check_current_universe_push(
            # This intentionally synthetic pledge is rejected by production.
            {**self.pledge,"synthetic_rehearsal_only":False},
            r,repo=REPO,sha=COMMIT_UNIVERSE)
        self.assertTrue(
            out["workflow_must_complete_success_and_verify_exact_original_blob_later"])
        self.assertFalse(out["official_source_ID_and_complete_schedule_not_certified"] is False)


if __name__=="__main__":
    unittest.main()
