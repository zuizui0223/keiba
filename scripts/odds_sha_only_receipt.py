#!/usr/bin/env python3
"""No-dependencies GitHub Actions receiver for a SHA-only race prediction.

This script has NO dependency on betting models, JRA data, odds snapshots,
Python packages or private files. It is deployable independently to main.

workflow_dispatch supplies only:
  race_id, seal_sha256, scheduled_post_jst, last_source_received_jst

The artifact created by this script is NOT proof on its own. An
independent verifier must fetch this artifact, the GitHub API's
workflow_run.created_at and the prior workflow runs on the official
GitHub server, then compare them with the private sealed prediction.
The first attempted submission for each race wins. A second submission
is not an acceptable replacement.

Nothing here asserts forecast skill or writes to v3.1's formal ledger.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re

SCHEMA="KEIBA_GITHUB_DISPATCH_SHA_PRESEAL_RECEIPT_V1"
REPOSITORY="zuizui0223/keiba"
WORKFLOW_PATH=".github/workflows/odds-shadow-attest.yml"
DEFAULT_BRANCH="main"
ARTIFACT_PREFIX="winwide-sha-commitment-"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,95}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")


def _time(value):
    if not isinstance(value,str):
        raise ValueError("HOLD_TIMESTAMP_REQUIRED")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("HOLD_EXPLICIT_TIMEZONE_REQUIRED")
    return dt


def receive(*, repo, run_id, attempt, event, workflow_ref, inputs):
    if (not isinstance(inputs,dict) or
            not isinstance(inputs.get("race_id"),str) or
            not _ID.fullmatch(inputs["race_id"]) or
            not isinstance(inputs.get("seal_sha256"),str) or
            not _HASH.fullmatch(inputs["seal_sha256"])):
        raise ValueError("HOLD_UNSAFE_RACE_ID_OR_INVALID_SHA")
    if set(inputs)!={
            "race_id","seal_sha256","scheduled_post_jst",
            "last_source_received_jst"}:
        raise ValueError("HOLD_EXTRA_DISPATCH_INPUT_FIELDS")
    post=_time(inputs["scheduled_post_jst"])
    last_received=_time(inputs["last_source_received_jst"])
    if last_received >= post-timedelta(minutes=10):
        raise ValueError("HOLD_INPUT_SOURCE_AFTER_PREPOST_CUTOFF")
    if (repo!=REPOSITORY or event!="workflow_dispatch"
            or type(run_id) is not int or run_id<1
            or attempt!=1 or workflow_ref!=
            f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/{DEFAULT_BRANCH}"):
        raise ValueError("HOLD_DISPATCH_NOT_DEFAULT_BRANCH_OR_FIRST_ATTEMPT")
    return {
        "schema":SCHEMA,
        "repo":repo,
        "workflow_path":WORKFLOW_PATH,
        "workflow_ref":workflow_ref,
        "event":"workflow_dispatch",
        "run_id":run_id,
        "run_attempt":1,
        "submitted_commitment_inputs":dict(inputs),
        "artifact_name":ARTIFACT_PREFIX+str(run_id),
        "contains_only_digest_and_nonsecret_race_time_metadata":True,
        "external_created_at_NOT_INCLUDED_MUST_FETCH_GITHUB_API":True,
        "local_receipt_alone_does_not_prove_prepost_submission":True,
    }


def receive_environment(environ):
    keys=("SEAL_RACE_ID","SEAL_SHA256","SEAL_POST_JST","SEAL_RECEIVED_JST")
    if not all(k in environ for k in keys):
        raise ValueError("HOLD_MISSING_SHA_ONLY_GITHUB_INPUT")
    return receive(
        repo=environ.get("GITHUB_REPOSITORY"),
        run_id=int(environ.get("GITHUB_RUN_ID","0")),
        attempt=int(environ.get("GITHUB_RUN_ATTEMPT","0")),
        event=environ.get("GITHUB_EVENT_NAME"),
        workflow_ref=environ.get("GITHUB_WORKFLOW_REF"),
        inputs={
            "race_id":environ["SEAL_RACE_ID"],
            "seal_sha256":environ["SEAL_SHA256"],
            "scheduled_post_jst":environ["SEAL_POST_JST"],
            "last_source_received_jst":environ["SEAL_RECEIVED_JST"],
        },
    )


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("runner",))
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    out=receive_environment(os.environ)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status":"SHA_ONLY_RECEIPT_WRITTEN_REMOTE_TIME_NOT_YET_VERIFIED",
        "run_id":out["run_id"],
        "race_id":out["submitted_commitment_inputs"]["race_id"],
        "independent_GitHub_server_timestamp_verified":False,
    }))


if __name__=="__main__":
    main()
