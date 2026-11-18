#!/usr/bin/env python3
"""Per-race aggregate-only Github-server-time forecast commitment.

Commands:
  bundle : join ONLY PUBLIC-AGGREGATE fields of locally frozen source receipt,
           pre-race source adapter QA, and frozen M0/M1/M2 forecast commitment.
  inspect: ensure immutable source/adapter/forecast SHA links and chronology,
           still HOLD until an actual verified GitHub push run exists.
  attest : verify GitHub Actions PUSH server created_at and head SHA before the
           future race, using ONLY the fixed api.github.com REST endpoint.
  open   : post-race check original private manifests and forecast against
           the exact already-committed bundle; does not rerun/retrain a model.

No raw licensed horse records, horse/race identifiers, trainer identifiers,
source DB paths or horse-level predictions may appear in the public bundle.
A GitHub PUSH run timestamp proves the *aggregate commitment file* existed
before the declared race start, not JRA publication time or source license.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import quote

SOURCE_SCHEMA = "JRA_LOCAL_SQLITE_ASOF_RECEIPT_V1"
ADAPTER_SCHEMA = "JRA_2027_PRIVATE_PRE_POST_SNAPSHOT_CSV_ADAPTER_V1"
FORECAST_SCHEMA = "JRA_2027_H1_PREDICTION_COMMITMENT_V1"
BUNDLE_SCHEMA = "JRA_2027_GITHUB_PRE_RACE_AGGREGATE_COMMITMENT_V1"
PRODUCTION_WORKFLOW_PATH = ".github/workflows/ecology-japan-2027-immutable-push-attestation.yml"
SYNTHETIC_REHEARSAL_WORKFLOW_PATH = ".github/workflows/ecology-japan-2027-server-rehearsal.yml"
JST = timezone(timedelta(hours=9))
REQUIRED_SHA = re.compile(r"^[0-9a-f]{64}$")
TARGET_FROM = datetime(2027, 1, 1, tzinfo=JST)
TARGET_TO = datetime(2027, 7, 1, tzinfo=JST)

SOURCE_FIELDS = (
    "schema", "capture_phase", "capture_started_utc",
    "capture_finished_utc", "capture_finished_jst",
    "target_race_start_jst", "private_snapshot_sha256",
    "local_clock_injected_for_synthetic_test",
    "local_clock_NOT_external_timestamp_proof",
    "MakeDate_NOT_actual_provider_publish_time",
    "must_commit_aggregate_receipt_before_target_start_for_independent_review",
)
ADAPTER_FIELDS = (
    "schema","status","source_pre_receipt_SHA256",
    "source_pre_private_snapshot_SHA256","private_track_map_SHA256",
    "private_normalized_CSV_SHA256",
    "declared_source_entrant_count","first_observed_entry_known_at_jst",
    "earliest_target_start_at_jst",
    "input_certifies_provider_publication_timestamp",
    "synthetic_test_only","privacy_no_source_horse_IDs_names_or_race_rows_in_public",
)
FORECAST_FIELDS = (
    "schema","status","target","earliest_target_start_at_jst",
    "asof_at_jst","frozen_at_utc","races","starts","unique_horses",
    "input_SHA256","private_prediction_file_SHA256",
    "no_2027_target_results_used","no_horse_or_race_IDs_in_public_manifest",
    "local_timestamp_and_digest_alone_NOT_trusted_external_proof",
)
BUNDLE_FIELDS = (
    "schema","status","manifest_input_file_sha256","source_capture",
    "private_pre_normalization_aggregate","frozen_prediction_commitment",
    "not_jra_provider_publish_time","not_official_race_schedule_attestation",
    "not_evidence_of_genetic_causation_or_wager_profit",
    "no_identifying_horse_or_race_rows_embedded",
)


def _bytes(path:Path) -> bytes:
    if not path.is_file() or path.stat().st_size>512*1024:
        raise ValueError("HOLD_COMMITMENT_MANIFEST_MISSING_OR_TOO_LARGE")
    return path.read_bytes()


def _sha(data:bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path:Path) -> str:
    if not path.is_file():
        raise ValueError("HOLD_MISSING_PRIVATE_COMMITTED_SOURCE_FILE")
    h=hashlib.sha256()
    with path.open("rb") as fd:
        for block in iter(lambda:fd.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def _sha_check(value) -> str:
    if not isinstance(value,str) or not REQUIRED_SHA.fullmatch(value):
        raise ValueError("HOLD_INVALID_OR_MISSING_SOURCE_OR_PREDICTION_SHA")
    return value


def _json_bytes(data:bytes) -> dict:
    def reject_duplicate_keys(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:
                raise ValueError("HOLD_DUPLICATE_AGGREGATE_JSON_KEY")
            obj[key]=value
        return obj
    try:
        obj=json.loads(data,object_pairs_hook=reject_duplicate_keys)
    except (ValueError,TypeError,UnicodeError) as exc:
        if isinstance(exc,ValueError) and str(exc)==(
                "HOLD_DUPLICATE_AGGREGATE_JSON_KEY"):
            raise
        raise ValueError("HOLD_INVALID_AGGREGATE_JSON") from None
    if not isinstance(obj,dict):
        raise ValueError("HOLD_NOT_AGGREGATE_MANIFEST_OBJECT")
    return obj


def _time(value:str) -> datetime:
    try:
        t=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (TypeError,AttributeError,ValueError):
        raise ValueError("HOLD_MISSING_OR_INVALID_COMMITMENT_TIME") from None
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("HOLD_COMMITMENT_TIME_MUST_HAVE_EXPLICIT_OFFSET")
    return t.astimezone(timezone.utc)


def _local_jst(value:str) -> datetime:
    try:
        t=datetime.fromisoformat(value)
    except (TypeError,ValueError):
        raise ValueError("HOLD_INVALID_RACE_START_JST") from None
    if t.tzinfo is None or t.utcoffset()!=timedelta(hours=9):
        raise ValueError("HOLD_TARGET_RACE_TIME_MUST_BE_EXPLICIT_JST")
    return t


def _only(obj:dict,fields:tuple[str,...]):
    absent=set(fields)-set(obj)
    if absent:
        # Do not serialize unexpected original data on error.
        raise ValueError("HOLD_REQUIRED_AGGREGATE_FIELD_MISSING")
    return {field:obj[field] for field in fields}


def _integer(value) -> int:
    if type(value) is not int or value<1 or value>30:
        raise ValueError("HOLD_EXPECT_VALID_ONE_RACE_COMPLETE_ENTRANT_COUNT")
    return value


def build_bundle(source:bytes, adapter:bytes, forecast:bytes,
                 *, allow_synthetic:bool=False) -> dict:
    """Bundler whitelists fields; no raw source row can be included."""
    s=_only(_json_bytes(source),SOURCE_FIELDS)
    a=_only(_json_bytes(adapter),ADAPTER_FIELDS)
    f=_only(_json_bytes(forecast),FORECAST_FIELDS)
    bundle={
        "schema":BUNDLE_SCHEMA,
        "status":"AGGREGATE_COMMITMENT_UNATTESTED_UNTIL_GITHUB_PUSH",
        "manifest_input_file_sha256":{
            "source_receipt":_sha(source),
            "pre_adapter_summary":_sha(adapter),
            "forecast_commitment":_sha(forecast),
        },
        "source_capture":s,
        "private_pre_normalization_aggregate":a,
        "frozen_prediction_commitment":f,
        "not_jra_provider_publish_time":True,
        "not_official_race_schedule_attestation":True,
        "not_evidence_of_genetic_causation_or_wager_profit":True,
        "no_identifying_horse_or_race_rows_embedded":True,
    }
    validate_bundle(bundle,allow_synthetic=allow_synthetic)
    return bundle


def validate_bundle(bundle:dict, *, allow_synthetic:bool=False):
    """Same rules apply to public bundle and synthetic test bundles."""
    if not isinstance(bundle,dict) or set(bundle)!=set(BUNDLE_FIELDS):
        raise ValueError("HOLD_BUNDLE_UNKNOWN_OR_MISSING_FIELDS_PRIVACY_GATE")
    if bundle["schema"]!=BUNDLE_SCHEMA or bundle["status"]!=(
            "AGGREGATE_COMMITMENT_UNATTESTED_UNTIL_GITHUB_PUSH"):
        raise ValueError("HOLD_BUNDLE_SCHEMA_OR_STATUS")
    dig=bundle["manifest_input_file_sha256"]
    if type(dig) is not dict or set(dig)!={
            "source_receipt","pre_adapter_summary","forecast_commitment"}:
        raise ValueError("HOLD_SOURCE_MANIFEST_DIGEST_FIELDS")
    for value in dig.values():
        _sha_check(value)
    s,a,f=(bundle["source_capture"],
           bundle["private_pre_normalization_aggregate"],
           bundle["frozen_prediction_commitment"])
    if (not isinstance(s,dict) or set(s)!=set(SOURCE_FIELDS)
            or not isinstance(a,dict) or set(a)!=set(ADAPTER_FIELDS)
            or not isinstance(f,dict) or set(f)!=set(FORECAST_FIELDS)):
        raise ValueError("HOLD_NESTED_AGGREGATE_WHITELIST_NOT_EXACT")
    if s["schema"]!=SOURCE_SCHEMA or s["capture_phase"]!="pre_race":
        raise ValueError("HOLD_REQUIRED_PRE_RACE_RECEIPT")
    if a["schema"]!=ADAPTER_SCHEMA or a["status"]!=(
            "PRIVATE_PRE_RACE_EXTRACTED_LOCAL_FIRST_OBSERVED_NOT_PROVIDER_ATTESTED"):
        raise ValueError("HOLD_REQUIRED_PRE_RACE_ADAPTER")
    if (f["schema"]!=FORECAST_SCHEMA or
            f["status"]!="PRIVATE_PRE_RACE_FORECAST_COMMITTED_UNSCORED" or
            f["target"]!="JRA_2027_JAN_JUN_FLAT_ONLY"):
        raise ValueError("HOLD_UNFROZEN_2027_FORECAST_COMMITMENT")
    for flag in (
            "local_clock_NOT_external_timestamp_proof",
            "MakeDate_NOT_actual_provider_publish_time",
            "must_commit_aggregate_receipt_before_target_start_for_independent_review"):
        if s[flag] is not True:
            raise ValueError("HOLD_SOURCE_RECEIPT_MISSING_TEMPORAL_DISCLOSURE")
    if (a["input_certifies_provider_publication_timestamp"] is not False or
            a["privacy_no_source_horse_IDs_names_or_race_rows_in_public"] is not True or
            f["no_2027_target_results_used"] is not True or
            f["no_horse_or_race_IDs_in_public_manifest"] is not True or
            f["local_timestamp_and_digest_alone_NOT_trusted_external_proof"] is not True or
            any(bundle[q] is not True for q in BUNDLE_FIELDS[-4:])):
        raise ValueError("HOLD_UNSAFE_OR_FALSE_PROVENANCE_DISCLOSURE")
    if not allow_synthetic and (
            s["local_clock_injected_for_synthetic_test"] is not False
            or a["synthetic_test_only"] is not False):
        raise ValueError("HOLD_SYNTHETIC_CLOCK_OR_SOURCE_IN_REAL_COMMITMENT")
    for k in ("private_snapshot_sha256",):
        _sha_check(s[k])
    for k in ("source_pre_receipt_SHA256",
              "source_pre_private_snapshot_SHA256","private_track_map_SHA256"):
        _sha_check(a[k])
    if (a["source_pre_receipt_SHA256"]!=dig["source_receipt"]
            or a["source_pre_private_snapshot_SHA256"]!=s["private_snapshot_sha256"]):
        raise ValueError("HOLD_SOURCE_ADAPTER_RECEIPT_SHA_NOT_SAME")
    normalized=a["private_normalized_CSV_SHA256"]
    inputs=f["input_SHA256"]
    if (type(normalized) is not dict or set(normalized)!={"entries","parents"}
            or type(inputs) is not dict or
            set(inputs)!={"entries","parents","history","model"}):
        raise ValueError("HOLD_PRIVATE_SOURCE_MODEL_SHA_SCHEMA")
    for d in (normalized,inputs):
        for sha in d.values():
            _sha_check(sha)
    _sha_check(f["private_prediction_file_SHA256"])
    if normalized["entries"]!=inputs["entries"] or normalized["parents"]!=inputs["parents"]:
        raise ValueError("HOLD_SOURCE_TO_FORECAST_ENTRIES_OR_PARENTS_DRIFT")
    n=_integer(a["declared_source_entrant_count"])
    if (_integer(f["races"])!=1 or _integer(f["starts"])!=n
            or _integer(f["unique_horses"])!=n or n<2):
        raise ValueError("HOLD_BUNDLE_CANNOT_CERTIFY_MULTIPLE_OR_PARTIAL_RACES")
    start=_local_jst(s["target_race_start_jst"])
    if (start!=_local_jst(a["earliest_target_start_at_jst"])
            or start!=_local_jst(f["earliest_target_start_at_jst"])
            or not TARGET_FROM<=start<TARGET_TO):
        raise ValueError("HOLD_TARGET_RACE_START_OR_FUTURE_WINDOW_MISMATCH")
    t0=_time(s["capture_started_utc"])
    t1=_time(s["capture_finished_utc"])
    if _time(s["capture_finished_jst"])!=t1:
        raise ValueError("HOLD_CAPTURE_FINISHED_UTC_JST_CONFLICT")
    first=_time(a["first_observed_entry_known_at_jst"])
    asof=_time(f["asof_at_jst"])
    freeze=_time(f["frozen_at_utc"])
    if first!=t1+timedelta(seconds=1):
        raise ValueError("HOLD_SOURCE_LOCAL_FIRST_SEEN_BOUND_INCORRECT")
    if not (t0<=t1<first<=asof<=freeze<start.astimezone(timezone.utc)):
        raise ValueError("HOLD_SOURCE_TO_FORECAST_PRE_RACE_TIME_ORDER")
    return {
        "status":"PUBLIC_AGGREGATE_LINKAGE_CHECKED_NO_EXTERNAL_GITHUB_TIME_YET",
        "first_race_start_jst":start.isoformat(),
        "source_receipt_sha256":dig["source_receipt"],
        "private_prediction_sha256":f["private_prediction_file_SHA256"],
        "starts":n,
        "races":1,
        "external_pre_race_timestamp_verified":False,
        "official_data_and_provider_publication_not_verified":True,
    }


def attest_run(bundle:dict, run:dict, *, repo:str, sha:str,
               allow_synthetic:bool=False) -> dict:
    """Pure checker for a verified REST response. Test fakes NOT evidence."""
    prev=validate_bundle(bundle,allow_synthetic=allow_synthetic)
    if (run.get("event")!="push"
            or run.get("head_sha")!=sha
            or run.get("repository",{}).get("full_name")!=repo
            or type(run.get("id")) is not int):
        raise ValueError("HOLD_GITHUB_PUSH_REPO_OR_CHECKOUT_SHA_MISMATCH")
    # GitHub Actions reruns inherit the original run's created_at: accepting
    # run_attempt > 1 would let a post-race rerun appear pre-race.
    if type(run.get("run_attempt")) is not int or run["run_attempt"]!=1:
        raise ValueError("HOLD_GITHUB_RERUN_CANNOT_ATTEST_NEW_PRE_RACE_PLEDGE")
    expected=(PRODUCTION_WORKFLOW_PATH,) if not allow_synthetic else (
        PRODUCTION_WORKFLOW_PATH,SYNTHETIC_REHEARSAL_WORKFLOW_PATH)
    if run.get("path") not in expected:
        raise ValueError("HOLD_GITHUB_UNTRUSTED_WORKFLOW_PATH")
    server=_time(run.get("created_at"))
    begin=_time(bundle["frozen_prediction_commitment"]["frozen_at_utc"])
    target=_time(bundle["source_capture"]["target_race_start_jst"])
    if not begin<=server<target:
        raise ValueError("HOLD_GITHUB_SERVER_RUN_CREATED_AFTER_RACE_OR_PRE_FORECAST")
    return {
        **prev,
        "status":"GITHUB_PUSH_SERVER_TIME_BEFORE_DECLARED_RACE_VERIFIED_CONDITIONAL",
        "github_repository":repo,
        "github_commit_sha":sha,
        "github_run_id":run["id"],
        "github_push_run_created_at_utc":server.isoformat(),
        "external_pre_race_timestamp_verified":True,
        "local_source_possession_and_jra_publish_time_not_verified":True,
        "real_2027_prediction_proficiency_or_genetic_claim_NOT_ESTABLISHED":True,
    }


def open_originals(bundle:dict, *, source:bytes,adapter:bytes,forecast:bytes,
                   private_predictions:bytes,allow_synthetic:bool=False,
                   opened_private_file_sha256:dict|None=None) -> dict:
    """Private AFTER-race opening against immutable bundle; no source export."""
    q=validate_bundle(bundle,allow_synthetic=allow_synthetic)
    for k,data in (
            ("source_receipt",source),
            ("pre_adapter_summary",adapter),
            ("forecast_commitment",forecast)):
        if _sha(data)!=bundle["manifest_input_file_sha256"][k]:
            raise ValueError("HOLD_OPENED_ORIGINAL_AGGREGATE_MANIFEST_SHA_DRIFT")
    forecast_obj=_json_bytes(forecast)
    private_obj=_json_bytes(private_predictions)
    if forecast_obj["private_prediction_file_SHA256"]!=_sha(private_predictions):
        raise ValueError("HOLD_OPENED_PRIVATE_FORECAST_SHA_DRIFT")
    if private_obj.get("target_outcomes_included") is not False:
        raise ValueError("HOLD_OPENED_PRIVATE_FORECAST_HAS_TARGET_LABELS")
    if private_obj.get("model_spec_sha256")!=(
            bundle["frozen_prediction_commitment"]["input_SHA256"]["model"]):
        raise ValueError("HOLD_OPENED_PRIVATE_FORECAST_MODEL_HASH_DRIFT")
    if opened_private_file_sha256 is not None:
        if type(opened_private_file_sha256) is not dict or set(opened_private_file_sha256)!={
                "source_snapshot","entries","parents","history","model"}:
            raise ValueError("HOLD_PRIVATE_SOURCE_FILE_OPENING_FIELDS")
        expected={
            "source_snapshot":bundle["source_capture"]["private_snapshot_sha256"],
            **bundle["frozen_prediction_commitment"]["input_SHA256"],
        }
        for name in expected:
            if _sha_check(opened_private_file_sha256[name])!=expected[name]:
                raise ValueError("HOLD_OPENED_PRIVATE_SOURCE_OR_MODEL_SHA_DRIFT")
    return {
        "status":("ALL_PRIVATE_SOURCE_AND_FORECAST_SHA_OPENED_NOT_TIME_ATTESTED"
                  if opened_private_file_sha256 is not None else
                  "ORIGINAL_PRIVATE_FORECAST_AND_SOURCE_MANIFEST_SHA_OPENING_PASSED"),
        "all_private_source_and_model_bytes_opened":bool(
            opened_private_file_sha256 is not None),
        "private_prediction_file_SHA256":_sha(private_predictions),
        "aggregate_bundle_timing_independently_attested_here":False,
        "licensed_source_accuracy_or_racing_outcomes_scored_here":False,
        "no_horse_names_or_IDs_exported":True,
    }


def content_addressed_bundle_filename(bundle:dict) -> str:
    """Opaque identifier binds the whole whitelisted aggregate content."""
    if not isinstance(bundle,dict) or bundle.get("schema")!=BUNDLE_SCHEMA:
        raise ValueError("HOLD_BAD_AGGREGATE_BUNDLE_FOR_CONTENT_ADDRESS")
    original=json.dumps(bundle,sort_keys=True,ensure_ascii=False,
                        separators=(",",":"),allow_nan=False).encode("utf-8")
    return _sha(original)[:32]+".json"


def _write_new(path:Path,value:dict):
    if path.exists():
        raise ValueError("HOLD_NEVER_OVERWRITE_PUBLIC_PRE_RACE_COMMITMENT")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        f.write(json.dumps(value,sort_keys=True,ensure_ascii=False,
                           indent=2,allow_nan=False)+"\n")


def _fetch_current_run() -> tuple[dict,str,str]:
    if os.environ.get("GITHUB_EVENT_NAME")!="push":
        raise ValueError("HOLD_NOT_A_GITHUB_PUSH_EVENT")
    repo=os.environ.get("GITHUB_REPOSITORY","")
    sha=os.environ.get("GITHUB_SHA","")
    run_id=os.environ.get("GITHUB_RUN_ID","")
    if (not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repo)
            or not re.fullmatch(r"[0-9a-f]{40}",sha)
            or not run_id.isdigit()):
        raise ValueError("HOLD_NOT_A_GENUINE_GITHUB_ACTIONS_RUN_CONTEXT")
    url=f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
    headers={"Accept":"application/vnd.github+json",
             "User-Agent":"JRA-public-commitment-attestation/1.0",
             "X-GitHub-Api-Version":"2022-11-28"}
    token=os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=12) as response:
        payload=response.read(512*1024)
    obj=_json_bytes(payload)
    if obj.get("id")!=int(run_id):
        raise ValueError("HOLD_GITHUB_RUN_ID_NOT_MATCH_API")
    return obj,repo,sha


def attest_original_server_file(bundle_raw:bytes,*,commit_sha:str,
                                run_id:int,relative_path:str,
                                github_json_get=None,
                                allow_synthetic:bool=False):
    """Later independent audit: server-held bundle BY exact original Git SHA.

    A successfully completed FIRST production push run is required. Verify
    original commit's exact byte content, opaque content address and server
    run metadata. Does not access private racehorse data nor source JRA.
    """
    repo="zuizui0223/keiba"
    if (not re.fullmatch(r"[0-9a-f]{40}",commit_sha)
            or commit_sha=="0"*40
            or type(run_id) is not int or run_id<1):
        raise ValueError("HOLD_INVALID_ORIGINAL_GITHUB_COMMIT_OR_RUN")
    if not re.fullmatch(r"docs/commitments/2027/[0-9a-f]{32}\.json",
                        relative_path):
        raise ValueError("HOLD_ORIGINAL_COMMITMENT_NOT_OPAQUE_ALLOWED_PATH")
    bundle=_json_bytes(bundle_raw)
    if relative_path.rsplit("/",1)[-1]!=content_addressed_bundle_filename(bundle):
        raise ValueError("HOLD_ORIGINAL_SERVER_FILE_CONTENT_ADDRESS_DRIFT")
    validate_bundle(bundle,allow_synthetic=allow_synthetic)
    base="https://api.github.com/repos/"+repo+"/"
    url_run=base+"actions/runs/"+str(run_id)
    url_contents=base+"contents/"+quote(relative_path,safe="/")+"?ref="+commit_sha

    def real_get(url):
        if not url.startswith(base):
            raise ValueError("HOLD_OUTBOUND_HOST_NOT_FIXED_TO_GITHUB")
        headers={"Accept":"application/vnd.github+json",
                 "User-Agent":"JRA-immutable-commit-original/1.0",
                 "X-GitHub-Api-Version":"2022-11-28"}
        token=os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"]="Bearer "+token
        req=urllib.request.Request(url,headers=headers)
        with urllib.request.urlopen(req,timeout=15) as response:
            payload=response.read(1024*1024+1)
        if len(payload)>1024*1024:
            raise ValueError("HOLD_GITHUB_ORIGINAL_CONTENT_RESPONSE_TOO_LARGE")
        return _json_bytes(payload)

    getter=github_json_get if github_json_get is not None else real_get
    run=getter(url_run)
    if type(run) is not dict or run.get("id")!=run_id:
        raise ValueError("HOLD_GITHUB_ORIGINAL_RUN_ID_DRIFT")
    if (run.get("status")!="completed" or run.get("conclusion")!="success"):
        raise ValueError("HOLD_ORIGINAL_GITHUB_PRODUCTION_ATTESTATION_NOT_SUCCESS")
    att=attest_run(bundle,run,repo=repo,sha=commit_sha,
                   allow_synthetic=allow_synthetic)
    returned=getter(url_contents)
    if (type(returned) is not dict or returned.get("type")!="file"
            or returned.get("encoding")!="base64"
            or returned.get("path")!=relative_path):
        raise ValueError("HOLD_GITHUB_CONTENTS_NOT_EXACT_TARGET_BLOB")
    try:
        original=base64.b64decode(returned["content"],validate=False)
    except (ValueError,KeyError,TypeError):
        raise ValueError("HOLD_GITHUB_ORIGINAL_BLOB_CANNOT_BE_DECODED") from None
    if len(original)>512*1024 or original!=bundle_raw:
        raise ValueError("HOLD_GITHUB_ORIGINAL_BUNDLE_BYTES_CHANGED")
    # GitHub contents API SHA is a git-blob digest; verify independently.
    git_blob_sha=hashlib.sha1(
        ("blob "+str(len(original))+"\0").encode()+original
    ).hexdigest()
    if returned.get("sha")!=git_blob_sha:
        raise ValueError("HOLD_GITHUB_ORIGINAL_GIT_BLOB_SHA_DRIFT")
    return {
        "status":("SYNTHETIC_ONLY_GITHUB_ORIGINAL_API_PROVENANCE_REHEARSAL"
                  if allow_synthetic else
                  "ORIGINAL_GITHUB_PRE_RACE_COMMIT_AND_SUCCESSFUL_RUN_VERIFIED"),
        "git_original_sha":commit_sha,
        "github_server_created_at_utc":att[
            "github_push_run_created_at_utc"],
        "github_original_run_id":run_id,
        "original_bundle_bytes_SHA256":_sha(original),
        "original_git_blob_SHA1":git_blob_sha,
        "published_pledge_past_race_proof_only_conditional":True,
        "source_JRA_publication_time_NOT_attested":True,
        "authorized_source_private_history_not_opened_here":True,
        "no_identifiable_licensed_horse_rows_returned":True,
        "real_future_predicted_effect_NOT_established":True,
    }


def _cli():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="operation",required=True)
    package=sub.add_parser("bundle",help="Whitelist aggregates; never horse IDs")
    package.add_argument("--pre-source-receipt",type=Path,required=True)
    package.add_argument("--pre-adapter-summary",type=Path,required=True)
    package.add_argument("--forecast-public-commitment",type=Path,required=True)
    dest=package.add_mutually_exclusive_group(required=True)
    dest.add_argument("--bundle-out",type=Path)
    dest.add_argument("--commit-directory",type=Path,
                      help="Write anonymous SHA-derived filename to 2027 commitment directory")
    inspect=sub.add_parser("inspect",help="No external proof")
    inspect.add_argument("--bundle",type=Path,required=True)
    attest=sub.add_parser("attest-push",help="Only real GitHub Actions push")
    attest.add_argument("--bundle",type=Path,required=True)
    orig=sub.add_parser("verify-original",help="Verify the original GitHub server-held pledge by exact SHA after race")
    orig.add_argument("--original-commit-sha",required=True)
    orig.add_argument("--original-run-id",required=True,type=int)
    orig.add_argument("--original-bundle",type=Path,required=True)
    orig.add_argument("--aggregate-out",type=Path,required=True)
    opening=sub.add_parser("open-private",help="Postrace verify private bytes")
    opening.add_argument("--bundle",type=Path,required=True)
    opening.add_argument("--pre-source-receipt",type=Path,required=True)
    opening.add_argument("--pre-adapter-summary",type=Path,required=True)
    opening.add_argument("--forecast-public-commitment",type=Path,required=True)
    opening.add_argument("--private-forecast",type=Path,required=True)
    opening.add_argument("--private-source-snapshot",type=Path,required=True)
    opening.add_argument("--private-entries",type=Path,required=True)
    opening.add_argument("--private-parents",type=Path,required=True)
    opening.add_argument("--private-history",type=Path,required=True)
    opening.add_argument("--private-model",type=Path,required=True)
    opening.add_argument("--result-aggregate",type=Path,required=True)
    args=p.parse_args()
    if args.operation=="bundle":
        b=build_bundle(_bytes(args.pre_source_receipt),
                       _bytes(args.pre_adapter_summary),
                       _bytes(args.forecast_public_commitment))
        if args.commit_directory is not None:
            # Opaque, deterministic filename binds to the whole aggregate
            # content; no horse/race name or provider IDs in public path.
            out=args.commit_directory/content_addressed_bundle_filename(b)
        else:
            out=args.bundle_out
        _write_new(out,b)
        result={**validate_bundle(b),"aggregate_commitment_path":str(out)}
    elif args.operation=="inspect":
        result=validate_bundle(_json_bytes(_bytes(args.bundle)))
    elif args.operation=="attest-push":
        run,repo,sha=_fetch_current_run()
        result=attest_run(_json_bytes(_bytes(args.bundle)),run,repo=repo,sha=sha)
    elif args.operation=="verify-original":
        raw=_bytes(args.original_bundle)
        name=content_addressed_bundle_filename(_json_bytes(raw))
        result=attest_original_server_file(
            raw,commit_sha=args.original_commit_sha,
            run_id=args.original_run_id,
            relative_path="docs/commitments/2027/"+name)
        _write_new(args.aggregate_out,result)
    else:
        result=open_originals(
            _json_bytes(_bytes(args.bundle)),
            source=_bytes(args.pre_source_receipt),
            adapter=_bytes(args.pre_adapter_summary),
            forecast=_bytes(args.forecast_public_commitment),
            private_predictions=_bytes(args.private_forecast),
            opened_private_file_sha256={
                "source_snapshot":_sha_file(args.private_source_snapshot),
                "entries":_sha_file(args.private_entries),
                "parents":_sha_file(args.private_parents),
                "history":_sha_file(args.private_history),
                "model":_sha_file(args.private_model),
            })
        _write_new(args.result_aggregate,result)
    print(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2))


if __name__=="__main__":
    _cli()
