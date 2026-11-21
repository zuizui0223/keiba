#!/usr/bin/env python3
"""Immutable 2027 eligible-race denominator pledge; not licensed JRA evidence.

Make a PUBLIC, privacy-whitelisted hash pledge from a PRIVATE full target-race
universe CSV, PRIVATE already-frozen M0/M1/M2 predictions and an ALREADY
EXISTING aggregate source/forecast bundle. Publish one opaque pledge by a NEW
GitHub push, then verify its ORIGINAL Git blob + server-created push time, not
an editable local/commit timestamp. An independent post-race process opens
BOTH original forecast and original universe bundles before it invokes the
existing frozen-denominator and missing-rank-bounds scorer.

Official race-list completeness, source publication and legal permission
remain unverified. No private horse/race IDs, source rows or per-horse
predictions are written to a public file. Synthetic tests are distinct.
"""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import quote

from ecology_japan_2027_github_push_attestation import (
    _json_bytes, _sha, _sha_check, _time, _local_jst,
    validate_bundle, attest_original_server_file,
    BUNDLE_SCHEMA, PRODUCTION_WORKFLOW_PATH,
)
from ecology_japan_2027_point_in_time_ledger import (
    canonical_bytes, digest_bytes, SCHEMA as FORECAST_SCHEMA,
)
from ecology_japan_2027_denominator_rank_bounds import (
    audit_universe, _csv as read_private_result_csv,
    RACE_UNIVERSE_FIELDS, _schedule_contract, START, END,
)

SCHEMA="JRA_2027_PRIVATE_RACE_UNIVERSE_HASH_PLEDGE_V1"
STATUS="PRE_RACE_AGGREGATE_RACE_UNIVERSE_COMMITMENT_UNATTESTED"
WORKFLOW_PATH=".github/workflows/ecology-japan-2027-immutable-universe-push.yml"
REPO="zuizui0223/keiba"
PLEDGE_DIR="docs/commitments/2027-universe"
FILE_REGEX=re.compile(r"docs/commitments/2027-universe/[0-9a-f]{32}\.json")
COMMIT_REGEX=re.compile(r"[0-9a-f]{40}")
FIELDS=(
    "schema","status","private_eligible_universe_csv_sha256",
    "pre_race_private_prediction_sha256",
    "forecast_aggregate_manifest_bytes_sha256",
    "original_forecast_bundle_bytes_sha256",
    "forecast_source_bundled_schema",
    "forecast_races","forecast_starts","forecast_unique_horses",
    "pretarget_eligible_races_declared","pretarget_eligible_races_not_forecast",
    "first_frozen_race_start_jst","first_declared_race_start_jst",
    "forecast_asof_at_jst","forecast_frozen_at_utc",
    "local_universe_clock_not_external_publication_proof",
    "official_race_universe_completeness_not_certified",
    "source_publication_and_licensing_not_verified",
    "raw_race_horse_parent_identifiers_not_published",
    "target_outcomes_absent_in_forecast",
    "independent_new_Github_push_created_at_required",
    "synthetic_rehearsal_only",
)


def _universe(raw:bytes) -> list[dict]:
    if not isinstance(raw,bytes) or not raw or len(raw)>2_000_000:
        raise ValueError("HOLD_PRIVATE_UNIVERSE_MISSING_OR_TOO_LARGE")
    try:
        data=raw.decode("utf-8-sig")
        reader=csv.DictReader(io.StringIO(data,newline=""))
        if reader.fieldnames!=list(RACE_UNIVERSE_FIELDS):
            raise ValueError("HOLD_PRIVATE_UNIVERSE_EXACT_CSV_HEADER")
        records=list(reader)
    except UnicodeDecodeError:
        raise ValueError("HOLD_PRIVATE_UNIVERSE_NOT_UTF8") from None
    if not 1<=len(records)<=500:
        raise ValueError("HOLD_PRIVATE_UNIVERSE_NONEMPTY_MAX500_RACES")
    for record in records:
        if None in record or any(not isinstance(record.get(k),str) or
                                 not record[k].strip()
                                 for k in RACE_UNIVERSE_FIELDS):
            raise ValueError("HOLD_PRIVATE_UNIVERSE_MISSING_FIELD")
        if set(record)!=set(RACE_UNIVERSE_FIELDS):
            raise ValueError("HOLD_PRIVATE_UNIVERSE_EXTRA_FIELD")
    return records


def _validated_pledge(p:dict,*, allow_synthetic:bool=False) -> dict:
    if type(p) is not dict or set(p)!=set(FIELDS):
        raise ValueError("HOLD_RACE_UNIVERSE_PLEDGE_UNWHITELISTED_FIELDS")
    if p["schema"]!=SCHEMA or p["status"]!=STATUS:
        raise ValueError("HOLD_UNIVERSE_PLEDGE_SCHEMA_OR_STATUS")
    if p["forecast_source_bundled_schema"]!=BUNDLE_SCHEMA:
        raise ValueError("HOLD_NO_PREEXISTING_SOURCE_FORECAST_BUNDLE")
    for name in (
        "private_eligible_universe_csv_sha256",
        "pre_race_private_prediction_sha256",
        "forecast_aggregate_manifest_bytes_sha256",
        "original_forecast_bundle_bytes_sha256",
    ):
        _sha_check(p[name])
    for key in ("forecast_races","forecast_starts","forecast_unique_horses",
                "pretarget_eligible_races_declared",
                "pretarget_eligible_races_not_forecast"):
        if type(p[key]) is not int or p[key]<0:
            raise ValueError("HOLD_UNIVERSE_PLEDGE_NONINTEGER_DENOMINATOR")
    if not (p["forecast_races"]==1
            and 2<=p["forecast_starts"]<=30
            and p["forecast_unique_horses"]==p["forecast_starts"]
            and p["pretarget_eligible_races_declared"]>=p["forecast_races"]
            and p["pretarget_eligible_races_not_forecast"]==(
                p["pretarget_eligible_races_declared"]-p["forecast_races"])
            and p["pretarget_eligible_races_declared"]<=500):
        raise ValueError("HOLD_UNIVERSE_PLEDGE_COUNT_RELATIONSHIP")
    for key in (
        "local_universe_clock_not_external_publication_proof",
        "official_race_universe_completeness_not_certified",
        "source_publication_and_licensing_not_verified",
        "raw_race_horse_parent_identifiers_not_published",
        "target_outcomes_absent_in_forecast",
        "independent_new_Github_push_created_at_required",
    ):
        if p[key] is not True:
            raise ValueError("HOLD_UNIVERSE_PLEDGE_FALSE_PROVENANCE_FLAG")
    if type(p["synthetic_rehearsal_only"]) is not bool or (
        p["synthetic_rehearsal_only"] and not allow_synthetic
    ):
        raise ValueError("HOLD_SYNTHETIC_UNIVERSE_PLEDGE_NOT_PRODUCTION")
    first=_local_jst(p["first_frozen_race_start_jst"])
    earliest=_local_jst(p["first_declared_race_start_jst"])
    asof=_local_jst(p["forecast_asof_at_jst"])
    freeze=_time(p["forecast_frozen_at_utc"])
    if not (START<=earliest<=first<END and
            asof<=freeze<earliest.astimezone(timezone.utc)):
        raise ValueError("HOLD_UNIVERSE_PLEDGE_TIMELINE")
    return {"first_declared_race":earliest,"first_frozen_race":first,
            "forecast_frozen":freeze}


def _private_parity(universe_raw:bytes, private_raw:bytes,
                    forecast_manifest_raw:bytes,
                    existing_bundle_raw:bytes,
                    *, allow_synthetic:bool=False) -> tuple[dict,dict,list[dict]]:
    """Recompute exact bytes; ID-sensitive fields never enter public pledge."""
    schedule=_universe(universe_raw)
    private=_json_bytes(private_raw)
    manifest=_json_bytes(forecast_manifest_raw)
    original=_json_bytes(existing_bundle_raw)
    validate_bundle(original,allow_synthetic=allow_synthetic)
    if manifest.get("schema")!=FORECAST_SCHEMA or manifest.get("status")!=(
        "PRIVATE_PRE_RACE_FORECAST_COMMITTED_UNSCORED"):
        raise ValueError("HOLD_FORECAST_NOT_PRE_RACE_FROZEN")
    if private.get("schema")!=FORECAST_SCHEMA or private.get(
        "target_outcomes_included") is not False:
        raise ValueError("HOLD_PRIVATE_FORECAST_CONTAINS_TARGET_LABELS")
    if digest_bytes(private_raw)!=manifest.get("private_prediction_file_SHA256"):
        raise ValueError("HOLD_PRIVATE_PREDICTION_BYTES_NOT_FROZEN_SHA")
    if _sha(forecast_manifest_raw)!=original.get(
        "manifest_input_file_sha256",{}).get("forecast_commitment"):
        raise ValueError("HOLD_ORIGINAL_FORECAST_BUNDLE_MANIFEST_SHA_NOT_MATCHED")
    source_manifest=original["frozen_prediction_commitment"]
    keys=("races","starts","unique_horses","asof_at_jst",
          "frozen_at_utc","earliest_target_start_at_jst",
          "private_prediction_file_SHA256")
    if any(source_manifest.get(k)!=manifest.get(k) for k in keys):
        raise ValueError("HOLD_GITHUB_FORECAST_BUNDLE_HORSE_DENOMINATOR_OR_TIME_DRIFT")
    if (private.get("model_spec_sha256")!=
            manifest.get("input_SHA256",{}).get("model")
            or private.get("asof_at_jst")!=manifest["asof_at_jst"]
            or private.get("frozen_at_utc")!=manifest["frozen_at_utc"]):
        raise ValueError("HOLD_PRIVATE_FORECAST_MODEL_OR_FROZEN_TIME_DRIFT")
    pred=private.get("predictions")
    if not isinstance(pred,list) or len(pred)!=manifest["starts"]:
        raise ValueError("HOLD_PRIVATE_FORECAST_PREDICTION_COUNT_DRIFT")
    ids=set()
    starts=set()
    horses=set()
    for p in pred:
        if not isinstance(p,dict) or not all(
            p.get(k) for k in ("race_id","horse_id","race_start_at_jst")
        ):
            raise ValueError("HOLD_PRIVATE_FORECAST_MISSING_RACE_OR_HORSE")
        ids.add(p["race_id"])
        starts.add(p["race_start_at_jst"])
        horses.add(p["horse_id"])
    if not (len(ids)==manifest["races"]==1
            and len(starts)==1
            and len(horses)==manifest["unique_horses"]
            and min(starts)==manifest["earliest_target_start_at_jst"]):
        raise ValueError("HOLD_PRIVATE_FORECAST_COUNTS_OR_STARTS_INCONSISTENT")
    by_race={r:[p for p in pred if p["race_id"]==r] for r in ids}
    coverage=_schedule_contract(
        schedule,by_race,_local_jst(manifest["asof_at_jst"])
    )
    if not coverage["provided_source_eligible_race_universe"]:
        raise ValueError("HOLD_PRIVATE_PRETARGET_RACE_UNIVERSE_ABSENT")
    first_declared=min(local["race_start_at_jst"] for local in schedule)
    pledge={
        "schema":SCHEMA,"status":STATUS,
        "private_eligible_universe_csv_sha256":_sha(universe_raw),
        "pre_race_private_prediction_sha256":_sha(private_raw),
        "forecast_aggregate_manifest_bytes_sha256":_sha(forecast_manifest_raw),
        "original_forecast_bundle_bytes_sha256":_sha(existing_bundle_raw),
        "forecast_source_bundled_schema":BUNDLE_SCHEMA,
        "forecast_races":manifest["races"],
        "forecast_starts":manifest["starts"],
        "forecast_unique_horses":manifest["unique_horses"],
        "pretarget_eligible_races_declared":coverage["eligible_races_declared"],
        "pretarget_eligible_races_not_forecast":
            coverage["eligible_races_without_a_frozen_prediction"],
        "first_frozen_race_start_jst":
            manifest["earliest_target_start_at_jst"],
        "first_declared_race_start_jst":first_declared,
        "forecast_asof_at_jst":manifest["asof_at_jst"],
        "forecast_frozen_at_utc":manifest["frozen_at_utc"],
        "local_universe_clock_not_external_publication_proof":True,
        "official_race_universe_completeness_not_certified":True,
        "source_publication_and_licensing_not_verified":True,
        "raw_race_horse_parent_identifiers_not_published":True,
        "target_outcomes_absent_in_forecast":True,
        "independent_new_Github_push_created_at_required":True,
        "synthetic_rehearsal_only":bool(allow_synthetic),
    }
    _validated_pledge(pledge,allow_synthetic=allow_synthetic)
    return pledge,private,schedule


def make_pledge(universe_raw:bytes,private_raw:bytes,
                forecast_manifest_raw:bytes,existing_bundle_raw:bytes,
                *, allow_synthetic:bool=False)->dict:
    p,_,_=_private_parity(
        universe_raw,private_raw,forecast_manifest_raw,
        existing_bundle_raw,allow_synthetic=allow_synthetic)
    return p


def content_addressed_filename(pledge:dict) -> str:
    _validated_pledge(pledge,allow_synthetic=True)
    b=json.dumps(pledge,sort_keys=True,ensure_ascii=False,
                 separators=(",",":"),allow_nan=False).encode("utf-8")
    return _sha(b)[:32]+".json"


def _github_get_json(url:str) -> dict:
    prefix=f"https://api.github.com/repos/{REPO}/"
    if not url.startswith(prefix):
        raise ValueError("HOLD_GITHUB_UNIVERSE_OUTBOUND_ORIGIN_NOT_FIXED")
    headers={
        "Accept":"application/vnd.github+json",
        "User-Agent":"2027-race-universe-original-commit-verifier",
        "X-GitHub-Api-Version":"2022-11-28",
    }
    token=os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=15) as response:
        raw=response.read(1_000_001)
    if len(raw)>1_000_000:
        raise ValueError("HOLD_GITHUB_UNIVERSE_RESPONSE_OVERSIZED")
    return _json_bytes(raw)


def attest_original_universe(pledge_raw:bytes, *, original_commit_sha:str,
                             original_run_id:int,relative_path:str,
                             github_json_get=None,allow_synthetic:bool=False)->dict:
    """Real mode is fixed to GitHub REST, original SHA and first PUSH only."""
    if github_json_get is not None and not allow_synthetic:
        raise ValueError("HOLD_FAKE_GITHUB_REST_IN_PRODUCTION")
    pledge=_json_bytes(pledge_raw)
    times=_validated_pledge(pledge,allow_synthetic=allow_synthetic)
    if (not isinstance(original_commit_sha,str)
            or not COMMIT_REGEX.fullmatch(original_commit_sha)
            or original_commit_sha=="0"*40
            or type(original_run_id) is not int or original_run_id<1
            or not isinstance(relative_path,str)
            or not FILE_REGEX.fullmatch(relative_path)
            or relative_path.rsplit("/",1)[-1]!=content_addressed_filename(pledge)):
        raise ValueError("HOLD_UNIVERSE_ORIGINAL_COMMIT_RUN_OR_FILENAME")
    base=f"https://api.github.com/repos/{REPO}/"
    getter=github_json_get or _github_get_json
    run=getter(base+"actions/runs/"+str(original_run_id))
    if (type(run) is not dict or run.get("id")!=original_run_id
            or run.get("head_sha")!=original_commit_sha
            or run.get("event")!="push"
            or run.get("repository",{}).get("full_name")!=REPO
            or run.get("path")!=WORKFLOW_PATH
            or run.get("run_attempt")!=1
            or run.get("status")!="completed" or run.get("conclusion")!="success"):
        raise ValueError("HOLD_UNIVERSE_ORIGINAL_PUSH_RUN_NOT_TRUSTED")
    server=_time(run["created_at"])
    if not times["forecast_frozen"]<=server<times["first_declared_race"].astimezone(timezone.utc):
        raise ValueError("HOLD_ORIGINAL_GITHUB_SERVER_PUSH_NOT_BEFORE_FIRST_ELIGIBLE_RACE")
    url=base+"contents/"+quote(relative_path,safe="/")+"?ref="+original_commit_sha
    item=getter(url)
    if (type(item) is not dict or item.get("type")!="file"
            or item.get("encoding")!="base64"
            or item.get("path")!=relative_path):
        raise ValueError("HOLD_UNIVERSE_GITHUB_ORIGINAL_BLOB_OR_PATH_NOT_SAME")
    try:
        raw=base64.b64decode(item["content"])
    except (TypeError,KeyError,ValueError):
        raise ValueError("HOLD_UNIVERSE_ORIGINAL_BLOB_NOT_DECODABLE") from None
    git_sha=hashlib.sha1(
        ("blob "+str(len(raw))+"\0").encode()+raw
    ).hexdigest()
    if raw!=pledge_raw or item.get("sha")!=git_sha or len(raw)>512_000:
        raise ValueError("HOLD_UNIVERSE_ORIGINAL_COMMITTED_BYTES_OR_GIT_BLOB_DRIFT")
    return {
        "status":("SYNTHETIC_UNIVERSE_SERVER_ATTESTATION_TEST_ONLY"
                  if allow_synthetic else
                  "GITHUB_ORIGINAL_UNIVERSE_PUSH_SERVER_TIME_AND_GIT_BLOB_VERIFIED"),
        "universe_pledge_original_bytes_sha256":_sha(raw),
        "universe_pledge_original_git_blob_SHA1":git_sha,
        "universe_pledge_original_commit_sha":original_commit_sha,
        "universe_pledge_original_run_id":original_run_id,
        "universe_pledge_original_run_server_created_at_utc":server.isoformat(),
        "original_race_universe_csv_digest_only_not_horse_IDs":True,
        "provider_source_timestamp_or_schedule_completeness_NOT_attested":True,
        "race_outcome_or_genetic_effect_NOT_established":True,
    }


def sealed_score(private_universe_raw:bytes,private_forecast_raw:bytes,
                 forecast_manifest_raw:bytes,forecast_bundle_raw:bytes,
                 universe_pledge_raw:bytes, results:list[dict], *,
                 universe_commit_sha:str,universe_run_id:int,universe_path:str,
                 forecast_commit_sha:str,forecast_run_id:int,forecast_path:str,
                 github_json_get=None, allow_synthetic:bool=False) -> dict:
    """Post-race re-open BOTH original GitHub commitments, then frozen scorer."""
    if github_json_get is not None and not allow_synthetic:
        raise ValueError("HOLD_FAKE_REST_NOT_ALLOWED_IN_REAL_SCORING")
    pledge,private,schedule=_private_parity(
        private_universe_raw,private_forecast_raw,
        forecast_manifest_raw,forecast_bundle_raw,
        allow_synthetic=allow_synthetic)
    if canonical_bytes(pledge)!=universe_pledge_raw:
        raise ValueError("HOLD_ORIGINAL_PRETARGET_UNIVERSE_PLEDGE_BYTES_CHANGED")
    proof=attest_original_universe(
        universe_pledge_raw,original_commit_sha=universe_commit_sha,
        original_run_id=universe_run_id,relative_path=universe_path,
        github_json_get=github_json_get,allow_synthetic=allow_synthetic)
    # This separate pre-race server proof already checks a model/source
    # linked GitHub blob and exact original PUSH run.
    original=attest_original_server_file(
        forecast_bundle_raw,commit_sha=forecast_commit_sha,
        run_id=forecast_run_id,relative_path=forecast_path,
        github_json_get=github_json_get,allow_synthetic=allow_synthetic)
    if original["original_bundle_bytes_SHA256"]!=pledge["original_forecast_bundle_bytes_sha256"]:
        raise ValueError("HOLD_PLEDGED_FORECAST_BUNDLE_NOT_ORIGINAL_GITHUB_OBJECT")
    # Private race list must be OPENED against the original pre-race SHA
    # before any future result is used in audit_universe.
    from ecology_japan_2027_denominator_rank_bounds import audit_universe
    report=audit_universe(private,_json_bytes(forecast_manifest_raw),
                          results,expected_races=schedule)
    return {
        "status":(
            "SYNTHETIC_REHEARSAL_ONLY_NOT_REAL_LICENSED_JRA_FORECAST"
            if allow_synthetic else
            "HOLD_OFFICIAL_ELIGIBLE_RACE_UNIVERSE_AND_PROVIDER_PUBLISH_TIMES_UNVERIFIED"
        ),
        "original_forecast_source_bundle_verified_on_Github_pre_race":True,
        "original_private_schedule_hash_bound_on_Github_pre_race":True,
        "source_JRA_schedule_completeness_independently_certified":False,
        "provider_result_publish_times_independently_certified":False,
        "real_2027_model_ability_or_genetics_proven":False,
        "universe_pledge_original_run_id":universe_run_id,
        "forecast_pledge_original_run_id":forecast_run_id,
        "public_schedule_hash_sha256":pledge["private_eligible_universe_csv_sha256"],
        "frozen_denominator_audit":report,
        "no_race_horse_ids_or_private_predictions_exported":True,
    }


def main():
    a=argparse.ArgumentParser(description=__doc__)
    sub=a.add_subparsers(dest="command",required=True)
    build=sub.add_parser("build",help="Create new aggregate-only pre-race pledge")
    build.add_argument("--private-universe",type=Path,required=True)
    build.add_argument("--private-forecast",type=Path,required=True)
    build.add_argument("--forecast-public-manifest",type=Path,required=True)
    build.add_argument("--original-forecast-bundle",type=Path,required=True)
    build.add_argument("--pledge-directory",type=Path,required=True)
    verify=sub.add_parser("verify-original",help="Server-recheck exact original immutable pledge")
    verify.add_argument("--original-pledge-file",type=Path,required=True)
    verify.add_argument("--original-commit-sha",required=True)
    verify.add_argument("--original-run-id",type=int,required=True)
    verify.add_argument("--original-relative-path",required=True)
    scored=sub.add_parser("sealed-score",help="Open two original pledges before later results")
    for p,flag in (
        ("private_universe","--private-universe"),
        ("private_forecast","--private-forecast"),
        ("forecast_public_manifest","--forecast-public-manifest"),
        ("original_forecast_bundle","--original-forecast-bundle"),
        ("original_universe_pledge","--original-universe-pledge"),
        ("published_results","--published-results"),
    ):
        scored.add_argument(flag,required=True,type=Path,dest=p)
    for name in ("universe_commit_sha","universe_run_id","universe_path",
                 "forecast_commit_sha","forecast_run_id","forecast_path"):
        scored.add_argument("--"+name.replace("_","-"),required=True,
                            type=int if name.endswith("_run_id") else str)
    scored.add_argument("--aggregate-out",type=Path,required=True)
    opt=a.parse_args()
    if opt.command=="build":
        pledge=make_pledge(
            opt.private_universe.read_bytes(),opt.private_forecast.read_bytes(),
            opt.forecast_public_manifest.read_bytes(),
            opt.original_forecast_bundle.read_bytes())
        file=opt.pledge_directory/content_addressed_filename(pledge)
        if opt.pledge_directory.as_posix().rstrip("/")!=PLEDGE_DIR:
            raise ValueError("HOLD_PUBLIC_PLEDGE_MUST_USE_ALLOWLISTED_REPO_DIRECTORY")
        file.parent.mkdir(parents=True,exist_ok=True)
        with file.open("xb") as fd:
            fd.write(canonical_bytes(pledge))
        print(json.dumps({"status":"UNATTESTED_NEW_PUBLIC_PLEDGE_CREATED_MUST_PUSH",
                          "public_pledge_relative_path":file.as_posix(),
                          "file_sha256":_sha(file.read_bytes()),
                          "no_source_or_2027_prediction_claim":True},sort_keys=True))
    elif opt.command=="verify-original":
        out=attest_original_universe(
            opt.original_pledge_file.read_bytes(),
            original_commit_sha=opt.original_commit_sha,
            original_run_id=opt.original_run_id,
            relative_path=opt.original_relative_path)
        print(json.dumps(out,sort_keys=True))
    else:
        out=sealed_score(
            opt.private_universe.read_bytes(),
            opt.private_forecast.read_bytes(),
            opt.forecast_public_manifest.read_bytes(),
            opt.original_forecast_bundle.read_bytes(),
            opt.original_universe_pledge.read_bytes(),
            read_private_result_csv(opt.published_results),
            universe_commit_sha=opt.universe_commit_sha,
            universe_run_id=opt.universe_run_id,
            universe_path=opt.universe_path,
            forecast_commit_sha=opt.forecast_commit_sha,
            forecast_run_id=opt.forecast_run_id,
            forecast_path=opt.forecast_path)
        opt.aggregate_out.parent.mkdir(parents=True,exist_ok=True)
        opt.aggregate_out.write_bytes(canonical_bytes(out))
        print(json.dumps(out,ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
