#!/usr/bin/env python3
"""Fictional-only original-commit replay for the seasonal allocation study.

No network client, production publication workflow, official source
verification or real timestamp attestation. An injected fictional server
response is required. Private fitted inputs are reopened, not published.
"""
from __future__ import annotations
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import re
from ecology_japan_2027_context_allocation_kernel import (
    START, SEEDS, digest, fields, count, require, time, verify, score,
)
from ecology_japan_2027_context_history_fit import fit, CAL_YEARS, VAL_YEARS

SCHEMA="FICTIONAL_CONTEXT_SEASONAL_PLEDGE_V1"
REPO="zuizui0223/keiba"
# Intentionally not an installed production workflow or actual commit path.
MOCK_WORKFLOW="fictional/context-seasonal-prewindow-push.yml"
MOCK_DIRECTORY="fictional/context-pledges"
HASH_FIELDS={"private_bundle_sha256","registry_sha256","components_sha256",
             "weights_sha256","predictions_sha256","history_sha256","parents_sha256",
             "fit_receipt_sha256"}
COUNT_FIELDS={"horses","prediction_rows","known_sire_horses",
              "zero_observed_eligible_history_horses","verified_unraced_horses"}
PUBLIC_FIELDS=HASH_FIELDS|COUNT_FIELDS|{
    "schema","status","cutoff_jst","frozen_at_jst","window_start_jst",
    "calibration_years","validation_years","code_commit",
    "real_observations","external_attestation_verified"}
HEX64=re.compile(r"[0-9a-f]{64}")
HEX40=re.compile(r"[0-9a-f]{40}")

def sha64(s):
    require(type(s) is str and HEX64.fullmatch(s) is not None,"HASH_SCHEMA")
    return s

def sha40(s):
    require(type(s) is str and HEX40.fullmatch(s) is not None and s!="0"*40,"GIT_SHA")
    return s

def canonical(obj):
    return (json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n").encode()

def blob_sha(raw):
    return hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()

def validate_public(p):
    fields(p,PUBLIC_FIELDS)
    require(p["schema"]==SCHEMA and p["status"]=="SYNTHETIC_ONLY_UNATTESTED"
            and p["real_observations"]==0 and p["external_attestation_verified"] is False,"SYNTHETIC_ONLY")
    for k in HASH_FIELDS:sha64(p[k])
    sha40(p["code_commit"])
    for k in COUNT_FIELDS:count(p[k])
    require(p["horses"]>0 and p["prediction_rows"]==len(SEEDS)*p["horses"],"PLEDGE_DENOMINATOR")
    require(all(p[k]<=p["horses"] for k in COUNT_FIELDS-{"prediction_rows"}),"PLEDGE_COUNT")
    require(p["verified_unraced_horses"]<=p["zero_observed_eligible_history_horses"],"PLEDGE_UNRACED_COUNT")
    require(p["calibration_years"]==list(CAL_YEARS) and p["validation_years"]==list(VAL_YEARS),"PLEDGE_TRAINING_YEARS")
    require(time(p["cutoff_jst"])<=time(p["frozen_at_jst"])<START and time(p["window_start_jst"])==START,"PLEDGE_TIME")
    return p

def build_pledge(private,receipt,fitted,*,code_commit):
    """Aggregate whitelist; no individual data in public pledge."""
    verify(private,receipt)
    fields(fitted,{"status","real_observations","history_sha256","parents_sha256",
                   "freeze_receipt","calibration_years","validation_years","results"})
    require(fitted["status"]=="SYNTHETIC_ONLY_FITTED_REHEARSAL" and fitted["real_observations"]==0
            and fitted["freeze_receipt"]==receipt,"FIT_RECEIPT")
    p={k:receipt[k] for k in (HASH_FIELDS-{"history_sha256","parents_sha256","fit_receipt_sha256"})|COUNT_FIELDS}
    p.update(schema=SCHEMA,status="SYNTHETIC_ONLY_UNATTESTED",
             cutoff_jst=private["cutoff_jst"],frozen_at_jst=private["frozen_at_jst"],
             window_start_jst=START.isoformat(),history_sha256=fitted["history_sha256"],
             parents_sha256=fitted["parents_sha256"],fit_receipt_sha256=digest(fitted),
             calibration_years=fitted["calibration_years"],validation_years=fitted["validation_years"],
             code_commit=code_commit,real_observations=0,external_attestation_verified=False)
    return validate_public(p)

def filename(p):
    return MOCK_DIRECTORY+"/"+hashlib.sha256(canonical(validate_public(p))).hexdigest()+".json"

def server_time(s):
    try:t=datetime.fromisoformat(s.replace("Z","+00:00"))
    except (ValueError,TypeError,AttributeError):raise ValueError("HOLD_SERVER_TIME") from None
    require(t.tzinfo is not None and t.utcoffset()==timezone.utc.utcoffset(t),"SERVER_TIME")
    return t

def replay_original(pledge,*,commit,run_id,relative_path,github_json_get):
    """Rehearse the exact original server blob, first push and new-file checks.

    Only caller-injected fixture responses; no real HTTP. Commit ancestry
    and API fields are assertions of the mock server, not actual proof.
    """
    p=validate_public(pledge);sha40(commit);count(run_id,1)
    require(callable(github_json_get),"MOCK_SERVER_REQUIRED")
    require(relative_path==filename(p),"CONTENT_ADDRESS")
    base="https://api.github.com/repos/"+REPO+"/"
    run=github_json_get(base+"actions/runs/"+str(run_id))
    require(type(run) is dict and run.get("id")==run_id and run.get("head_sha")==commit
            and run.get("event")=="push" and type(run.get("run_attempt")) is int and run["run_attempt"]==1
            and run.get("status")=="completed" and run.get("conclusion")=="success"
            and run.get("path")==MOCK_WORKFLOW
            and run.get("repository",{}).get("full_name")==REPO
            and run.get("head_repository",{}).get("full_name")==REPO,"ORIGINAL_PUSH")
    created=server_time(run.get("created_at"))
    require(time(p["frozen_at_jst"])<=created<START,"ORIGINAL_PREWINDOW")
    co=github_json_get(base+"commits/"+commit)
    require(type(co) is dict and co.get("sha")==commit and type(co.get("parents")) is list
            and len(co["parents"])==1,"ORIGINAL_COMMIT")
    parent=sha40(co["parents"][0].get("sha"))
    require(parent!=commit,"PARENT_SELF")
    # Verify code commit belongs to ancestry of the new pledge commit's parent
    # according to a separate mock compare response; never equate pledge and code.
    compare=github_json_get(base+"compare/"+p["code_commit"]+"..."+parent)
    require(type(compare) is dict and compare.get("status") in {"ahead","identical"}
            and compare.get("merge_base_commit",{}).get("sha")==p["code_commit"],"CODE_ANCESTRY")
    # The mocked changes list is required to be complete and contain exactly
    # one added pledge, not a rename, overwrite or arbitrary code change.
    require(co.get("files")==[{"filename":relative_path,"status":"added"}],"NEW_FILE_ONLY")
    returned=github_json_get(base+"contents/"+relative_path+"?ref="+commit)
    require(type(returned) is dict and returned.get("type")=="file"
            and returned.get("encoding")=="base64" and returned.get("path")==relative_path,"ORIGINAL_FILE")
    try:raw=base64.b64decode(returned["content"],validate=True)
    except (KeyError,TypeError,ValueError,binascii.Error):raise ValueError("HOLD_ORIGINAL_BYTES") from None
    require(raw==canonical(p) and returned.get("sha")==blob_sha(raw),"ORIGINAL_BLOB")
    return {"status":"FICTIONAL_ORIGINAL_PUSH_REPLAY_ONLY","real_observations":0,
            "external_attestation_verified":False,"mock_original_commit":commit,
            "mock_original_run_id":run_id,"mock_server_created_at_utc":created.isoformat(),
            "original_pledge_sha256":hashlib.sha256(raw).hexdigest()}

def reopen(private,receipt,fitted,pledge,history,parents,*,commit,run_id,relative_path,github_json_get):
    """Re-fit from identical prepared inputs; reject changes before scoring."""
    att=replay_original(pledge,commit=commit,run_id=run_id,relative_path=relative_path,github_json_get=github_json_get)
    require(build_pledge(private,receipt,fitted,code_commit=pledge["code_commit"])==pledge,"PLEDGE_DRIFT")
    require(digest(history)==pledge["history_sha256"] and digest(parents)==pledge["parents_sha256"],"INPUT_HASH_DRIFT")
    p,q,f=fit(history,parents,private["registry"],cutoff_jst=private["cutoff_jst"],frozen_at_jst=private["frozen_at_jst"])
    require((p,q,f)==(private,receipt,fitted),"REFIT_DRIFT")
    return att

def replay_and_score(private,receipt,fitted,pledge,history,parents,races,entries,results,
                     *,commit,run_id,relative_path,github_json_get,scored_at_jst):
    att=reopen(private,receipt,fitted,pledge,history,parents,commit=commit,run_id=run_id,
               relative_path=relative_path,github_json_get=github_json_get)
    z=score(private,receipt,races,entries,results,scored_at_jst=scored_at_jst)
    return {"status":"FICTIONAL_END_TO_END_ORIGINAL_REPLAY_SCORE","real_observations":0,
            "external_attestation_verified":False,"replay":att,"score":z}
