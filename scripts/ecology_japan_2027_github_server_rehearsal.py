#!/usr/bin/env python3
"""Use REAL GitHub server API run metadata with FICTIONAL future race manifests.

This CI rehearsal verifies remote REST connectivity, event=push, run_attempt=1,
workflow path and actual GitHub-run created_at. No source JRA records, horse
identities, actual 2027 forecasts or source-publication times are used.
The scripted manifest deliberately carries synthetic_test_only=True and
local_clock_injected_for_synthetic_test=True. Production validation MUST reject.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import urllib.request

from ecology_japan_2027_github_push_attestation import (
    SOURCE_SCHEMA, ADAPTER_SCHEMA, FORECAST_SCHEMA,
    SYNTHETIC_REHEARSAL_WORKFLOW_PATH,
    _sha, _fetch_current_run, build_bundle, attest_run, validate_bundle
)

TARGET="2027-01-09T15:15:00+09:00"
FINISHED="2026-11-17T09:01:00+09:00"
SOURCE_START="2026-11-16T23:59:00+00:00"
SOURCE_FINISHED="2026-11-17T00:01:00+00:00"
FIRST_SEEN="2026-11-17T09:01:01+09:00"
FORECAST_ASOF="2026-11-17T09:02:00+09:00"
FORECAST_FROZEN="2026-11-17T01:04:00+00:00"


def fake_bytes(obj):
    return (json.dumps(obj,sort_keys=True,
            separators=(",",":"),ensure_ascii=False)+"\n").encode("utf-8")


def dummy_pretarget_aggregate():
    src={
        "schema":SOURCE_SCHEMA,"capture_phase":"pre_race",
        "capture_started_utc":SOURCE_START,
        "capture_finished_utc":SOURCE_FINISHED,
        "capture_finished_jst":FINISHED,
        "target_race_start_jst":TARGET,
        "private_snapshot_sha256":"1"*64,
        "local_clock_injected_for_synthetic_test":True,
        "local_clock_NOT_external_timestamp_proof":True,
        "MakeDate_NOT_actual_provider_publish_time":True,
        "must_commit_aggregate_receipt_before_target_start_for_independent_review":True,
    }
    source=fake_bytes(src)
    adapter={
        "schema":ADAPTER_SCHEMA,
        "status":"PRIVATE_PRE_RACE_EXTRACTED_LOCAL_FIRST_OBSERVED_NOT_PROVIDER_ATTESTED",
        "source_pre_receipt_SHA256":_sha(source),
        "source_pre_private_snapshot_SHA256":"1"*64,
        "private_track_map_SHA256":"2"*64,
        "private_normalized_CSV_SHA256":{"entries":"3"*64,"parents":"4"*64},
        "declared_source_entrant_count":3,
        "first_observed_entry_known_at_jst":FIRST_SEEN,
        "earliest_target_start_at_jst":TARGET,
        "input_certifies_provider_publication_timestamp":False,
        "synthetic_test_only":True,
        "privacy_no_source_horse_IDs_names_or_race_rows_in_public":True,
    }
    fore={
        "schema":FORECAST_SCHEMA,
        "status":"PRIVATE_PRE_RACE_FORECAST_COMMITTED_UNSCORED",
        "target":"JRA_2027_JAN_JUN_FLAT_ONLY",
        "earliest_target_start_at_jst":TARGET,
        "asof_at_jst":FORECAST_ASOF,
        "frozen_at_utc":FORECAST_FROZEN,
        "races":1,"starts":3,"unique_horses":3,
        "input_SHA256":{
            "entries":"3"*64,"parents":"4"*64,
            "history":"5"*64,"model":"6"*64},
        "private_prediction_file_SHA256":"7"*64,
        "no_2027_target_results_used":True,
        "no_horse_or_race_IDs_in_public_manifest":True,
        "local_timestamp_and_digest_alone_NOT_trusted_external_proof":True,
    }
    return build_bundle(source,fake_bytes(adapter),fake_bytes(fore),
                        allow_synthetic=True)


def verify_actual_original_script_git_blob(repo,sha):
    """Real REST contents fetch from the EXACT push commit, no horse data."""
    if repo!="zuizui0223/keiba":
        raise ValueError("HOLD_REHEARSAL_WRONG_REPOSITORY")
    filename="scripts/ecology_japan_2027_github_server_rehearsal.py"
    local=Path(__file__).read_bytes()
    url=f"https://api.github.com/repos/{repo}/contents/{filename}?ref={sha}"
    headers={
        "Accept":"application/vnd.github+json",
        "User-Agent":"JRA-real-server-source-only-rehearsal/1.0",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    token=os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"]="Bearer "+token
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),
                                timeout=12) as response:
        raw=response.read(1024*1024)
    response=json.loads(raw)
    if (response.get("path")!=filename or response.get("type")!="file"
            or response.get("encoding")!="base64"):
        raise ValueError("HOLD_REHEARSAL_GITHUB_FILE_RESPONSE_INVALID")
    actual=base64.b64decode(response["content"])
    if actual!=local:
        raise ValueError("HOLD_ACTUAL_ORIGINAL_GITHUB_SHA_BLOB_NOT_EQUAL_LOCAL_CODE")
    blob=hashlib.sha1(
        ("blob "+str(len(actual))+"\0").encode()+actual
    ).hexdigest()
    if response.get("sha")!=blob:
        raise ValueError("HOLD_GITHUB_ORIGINAL_CONTENTS_BLOB_SHA_DRIFT")
    return {"original_git_blob_verified_by_real_GitHub_REST":True,
            "exact_original_repo_source_file_SHA256":
                hashlib.sha256(actual).hexdigest(),
            "no_racehorse_or_forecast_source_downloaded":True}


def run_rehearsal():
    bundle=dummy_pretarget_aggregate()
    run,repo,sha=_fetch_current_run()
    if run.get("path")!=SYNTHETIC_REHEARSAL_WORKFLOW_PATH:
        raise ValueError("HOLD_REHEARSAL_NOT_FROM_DECLARED_STAGING_WORKFLOW")
    # Fail closed: this fake capture can NEVER be promoted to real proof.
    try:
        validate_bundle(bundle,allow_synthetic=False)
    except ValueError as exc:
        if "HOLD_SYNTHETIC_CLOCK_OR_SOURCE" not in str(exc):
            raise
    else:
        raise AssertionError("HOLD_SYNTHETIC_SOURCE_INCORRECTLY_PASSING_PRODUCTION")
    evidence=attest_run(bundle,run,repo=repo,sha=sha,
                        allow_synthetic=True)
    original_blob=verify_actual_original_script_git_blob(repo,sha)
    if not evidence["external_pre_race_timestamp_verified"]:
        raise ValueError("HOLD_ACTUAL_GITHUB_SERVER_TIME_NOT_VERIFIED")
    if evidence["github_commit_sha"]!=sha:
        raise ValueError("HOLD_GITHUB_RUN_COMMIT_DRIFT")
    # A deliberately truthful and limited status: source and 2027 race fake.
    return {
        "status":"SYNTHETIC_ONLY_REAL_GITHUB_PUSH_API_CONNECTED_NOT_2027_RACE_EVIDENCE",
        "source_is_fictional":True,
        "real_github_event":"push",
        "real_github_run_id":evidence["github_run_id"],
        "real_github_head_sha":sha,
        "real_github_server_run_created_at_utc":
            evidence["github_push_run_created_at_utc"],
        "github_workflow_path":SYNTHETIC_REHEARSAL_WORKFLOW_PATH,
        "run_attempt":run["run_attempt"],
        "simulated_target_start_not_actual_JRA_schedule":TARGET,
        "synthetic_capture_refused_by_production_gate":True,
        "no_real_JRA_VAN_or_2027_race_data_used":True,
        "no_real_forecast_or_genetic_result":True,
        "source_published_at_time_NOT_verified":True,
        **original_blob,
    }


if __name__=="__main__":
    print(json.dumps(run_rehearsal(),sort_keys=True,
                     ensure_ascii=False,indent=2))
