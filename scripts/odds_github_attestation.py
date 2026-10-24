#!/usr/bin/env python3
"""GitHub-server-created-at proof for a private WIN/WIDE shadow freeze SHA.

Only a SHA-256 of the complete already frozen probability payload, the
race ID, the declared post time, and local feature/lock timestamps are
dispatched. No original licensed odds and no predictions are uploaded.

A GitHub workflow_dispatch run is only available after this workflow
has been added to the repository DEFAULT branch. Merely opening a draft
PR does not make this tool operational for a real prospective study.

The first independently fetched SUCCESSFUL workflow run for a race must
be the FIRST recorded attempt for that race (including failed attempts).
The server-side run.created_at must fall between the local source
receipt/forecast freeze and post time minus the safety buffer. The
receipt's digest must match the original local shadow freeze. Later
replacements are rejected to prevent cherry-picking.

These controls establish at most the prior existence of the digest, NOT
whether licensed source markets were true, independent model calibration,
betting profit, or v3.1 20-race formal holdout status.

CLI:
  python scripts/odds_github_attestation.py dispatch \
    --freeze private/freeze.json --output private/dispatch.json
  # On default branch only: use GitHub Actions UI / gh workflow run with
  # dispatch.json's four safe inputs. Never upload freeze.json itself.
  python scripts/odds_github_attestation.py verify-live \
    --freeze private/freeze.json --repo zuizui0223/keiba --run-id 12345 \
    --result private/result.json --output private/proof-and-score.json
  python scripts/odds_github_attestation.py demo \
    --output tmp/synthetic-offline-proof.json

verify-live uses GitHub CLI to INDEPENDENTLY fetch the workflow run,
commitment artifact and the workflow run list. Local fixture checking
always returns HOLD and never certifies remote time.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from odds_shadow_freeze_score import (
    score_sealed, synthetic_demo, build_freeze, verify_seal,
)

SCHEMA = "KEIBA_GITHUB_DISPATCH_SHA_PRESEAL_RECEIPT_V1"
WORKFLOW_NAME = "odds-shadow-attest.yml"
WORKFLOW_PATH = ".github/workflows/" + WORKFLOW_NAME
REPOSITORY = "zuizui0223/keiba"
DEFAULT_BRANCH = "main"
MIN_PREPOST_MINUTES = 10
ARTIFACT_PREFIX = "winwide-sha-commitment-"
RACE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,95}$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
STATUS_OFFLINE = "HOLD_OFFLINE_RECEIPT_IS_NOT_INDEPENDENT_GITHUB_EVIDENCE"
STATUS_REMOTE = "GITHUB_SERVER_PRESTART_SHA_COMMITMENT_VERIFIED_ONLY"
SCORE_STATUS = "SHADOW_SCORE_WITH_REMOTE_HASH_COMMITMENT_NOT_V31_FORMAL_HOLDOUT"


def _aware(stamp):
    if not isinstance(stamp, str):
        raise ValueError("HOLD_ATTESTATION_TIMESTAMP_TYPE")
    value = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("HOLD_ATTESTATION_TIMEZONE")
    return value


def _race_id(value):
    if not isinstance(value, str) or not RACE_ID_RE.fullmatch(value):
        raise ValueError("HOLD_UNSAFE_OR_INVALID_RACE_ID")
    return value


def _sha(value):
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ValueError("HOLD_SHA256_DIGEST_MALFORMED")
    return value


def dispatch_inputs(freeze):
    """Safe manifest of FOUR strings. No full probabilities or provider quotes."""
    payload = verify_seal(freeze)
    return {
        "race_id": _race_id(payload["race_id"]),
        "seal_sha256": _sha(freeze["seal_sha256_of_canonical_payload"]),
        "scheduled_post_jst": payload["scheduled_post_jst"],
        "last_source_received_jst": payload["last_source_received_at_jst"],
    }


def prepare_dispatch(freeze):
    inputs = dispatch_inputs(freeze)
    return {
        "status":"PREPARED_ONLY_NO_GITHUB_DISPATCH_HAS_OCCURRED",
        "workflow_id":WORKFLOW_NAME,
        "repo":REPOSITORY,
        "ref":DEFAULT_BRANCH,
        "inputs":inputs,
        "raw_provider_odds_or_probability_rows_included":False,
        "external_prestart_evidence_present":False,
        "manual_dispatch_needed":True,
    }


def runner_receipt(*, repo, run_id, run_attempt, event, workflow_ref,
                   inputs):
    """Called inside a real workflow; environment fields are not external proof."""
    _race_id(inputs.get("race_id"))
    _sha(inputs.get("seal_sha256"))
    post = _aware(inputs.get("scheduled_post_jst"))
    source_rx = _aware(inputs.get("last_source_received_jst"))
    if (repo != REPOSITORY or event != "workflow_dispatch"
            or not isinstance(run_id, int) or run_id <= 0
            or run_attempt != 1
            or workflow_ref !=
               f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/{DEFAULT_BRANCH}"
            or source_rx >= post-timedelta(minutes=MIN_PREPOST_MINUTES)):
        raise ValueError("HOLD_NOT_DEFAULT_BRANCH_DISPATCH_OR_PRESTART_TIME")
    return {
        "schema":SCHEMA,
        "repo":repo,
        "workflow_path":WORKFLOW_PATH,
        "workflow_ref":workflow_ref,
        "event":event,
        "run_id":run_id,
        "run_attempt":run_attempt,
        "submitted_commitment_inputs":dict(inputs),
        "artifact_name":ARTIFACT_PREFIX+str(run_id),
        "contains_only_digest_and_nonsecret_race_time_metadata":True,
        "external_created_at_NOT_INCLUDED_MUST_FETCH_GITHUB_API":True,
        "local_receipt_alone_does_not_prove_prepost_submission":True,
    }


def _check_api_and_record(freeze, receipt, run, other_runs):
    """Check data fetched from official GitHub API and immutable v4 artifact.

    This routine is also unit-tested with invented JSON; only verify-live
    independently retrieves those objects and may assert remote proof.
    """
    payload = verify_seal(freeze)
    info = dispatch_inputs(freeze)
    if receipt.get("schema") != SCHEMA:
        raise ValueError("HOLD_REMOTE_RECEIPT_SCHEMA")
    if (receipt.get("repo") != REPOSITORY
            or receipt.get("workflow_path") != WORKFLOW_PATH
            or receipt.get("event") != "workflow_dispatch"
            or receipt.get("run_attempt") != 1
            or receipt.get("workflow_ref") !=
               f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/{DEFAULT_BRANCH}"
            or receipt.get("submitted_commitment_inputs") != info
            or receipt.get("artifact_name") !=
               ARTIFACT_PREFIX + str(receipt.get("run_id"))):
        raise ValueError("HOLD_REMOTE_COMMITMENT_INPUT_MISMATCH")
    runid = receipt.get("run_id")
    if (type(runid) is not int or runid < 1
            or run.get("id") != runid
            or run.get("event") != "workflow_dispatch"
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
            or run.get("run_attempt") != 1
            or run.get("head_branch") != DEFAULT_BRANCH
            or run.get("path") !=
               f"{WORKFLOW_PATH}@refs/heads/{DEFAULT_BRANCH}"
            or run.get("display_title") !=
               f"odds-preseal/{info['race_id']}"
            or run.get("repository", {}).get("full_name") != REPOSITORY):
        raise ValueError("HOLD_GITHUB_RUN_METADATA_DOES_NOT_MATCH_SUBMISSION")
    server_created = _aware(run["created_at"])
    source_received = _aware(payload["last_source_received_at_jst"])
    locally_sealed = _aware(payload["local_prediction_recorded_at_jst"])
    start = _aware(payload["scheduled_post_jst"])
    if not (source_received <= locally_sealed <= server_created
            < start - timedelta(minutes=MIN_PREPOST_MINUTES)):
        raise ValueError("HOLD_NOT_GITHUB_SERVER_PRESTART_SHA_CREATION")
    if not isinstance(other_runs, list):
        raise ValueError("HOLD_GITHUB_RUN_LIST_NOT_INDEPENDENTLY_CHECKED")
    if not any(x.get("id") == runid for x in other_runs):
        raise ValueError("HOLD_COMMITTED_RUN_ABSENT_FROM_GITHUB_LIST")
    if len({x.get("id") for x in other_runs}) != len(other_runs):
        raise ValueError("HOLD_DUPLICATE_RUN_IDS_IN_GITHUB_LIST")
    # Prevent submission of several sealed alternatives for the same race
    # and reporting only the successful one retrospectively.
    earlier = [
        x for x in other_runs if (
            x.get("display_title") == f"odds-preseal/{info['race_id']}"
            and x.get("event") == "workflow_dispatch"
            and x.get("id") != runid and
            (_aware(x["created_at"]),x["id"]) <
            (server_created,runid))
    ]
    if earlier:
        raise ValueError("HOLD_EARLIER_SAME_RACE_DISPATCH_WAS_ALREADY_SUBMITTED")
    return {
        "status": STATUS_REMOTE,
        "race_id":info["race_id"],
        "sha256_of_sealed_prediction": info["seal_sha256"],
        "github_server_workflow_created_at":server_created.isoformat(),
        "scheduled_post":start.isoformat(),
        "safe_margin_minutes_from_github_created_to_post":
            (start-server_created).total_seconds()/60,
        "run_id":runid,
        "workflow_run_url":run["html_url"],
        "commitment_artifact_name":receipt["artifact_name"],
        "trusted_external_claim_limited_to_digest_preexistence":True,
        "true_win_place_calibration_not_established":True,
        "model_coefficient_choices_not_independently_validated":True,
        "does_not_append_to_v31_holdout":True,
    }


def inspect_fixture(freeze, receipt, run, other_runs):
    """Checks coherence only. NEVER claims the fake JSON is remotely trusted."""
    structural = _check_api_and_record(freeze, receipt, run, other_runs)
    return {
        **structural,
        "status":STATUS_OFFLINE,
        "fixtures_can_be_fabricated_no_remote_evidence":True,
        "independent_fetch_performed":False,
    }


def _gh_json(*argv):
    try:
        proc = subprocess.run(
            ["gh", *argv], check=True, text=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise ValueError(
            "HOLD_GITHUB_CLI_INDEPENDENT_FETCH_FAILED: "
            + str(exc)) from exc
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("HOLD_GITHUB_API_NONJSON_RESPONSE") from exc


def _fetch_workflow_run_list(repo):
    """Fail closed on incomplete pagination: earlier same-race run might be hidden."""
    collected = []
    for page in range(1,21):
        uri = (f"/repos/{repo}/actions/workflows/{WORKFLOW_NAME}/runs"
               f"?event=workflow_dispatch&per_page=100&page={page}")
        data = _gh_json("api", uri)
        subset = data.get("workflow_runs")
        if not isinstance(subset, list):
            raise ValueError("HOLD_INVALID_GITHUB_WORKFLOW_RUN_LIST")
        collected.extend(subset)
        if len(subset) < 100:
            return collected
    raise ValueError("HOLD_GITHUB_WORKFLOW_RUN_LIST_EXCEEDED_AUDIT_LIMIT")


def verify_live(freeze, *, repo, run_id, result=None):
    if repo != REPOSITORY or type(run_id) is not int or run_id < 1:
        raise ValueError("HOLD_UNKNOWN_ATTESTATION_REPOSITORY_OR_RUN")
    # Both GitHub server records and artifact must be acquired afresh
    # by GitHub CLI; caller cannot provide a fixture API JSON here.
    run = _gh_json("api", f"/repos/{repo}/actions/runs/{run_id}")
    all_runs = _fetch_workflow_run_list(repo)
    with tempfile.TemporaryDirectory() as temporary:
        try:
            subprocess.run(
                ["gh","run","download",str(run_id),"--repo",repo,
                 "--name",ARTIFACT_PREFIX+str(run_id),"--dir",temporary],
                check=True, text=True,capture_output=True)
        except (FileNotFoundError,subprocess.CalledProcessError) as exc:
            raise ValueError(
                "HOLD_GITHUB_COMMITMENT_ARTIFACT_CANNOT_BE_INDEPENDENTLY_READ"
            ) from exc
        artifacts = list(Path(temporary).rglob("commitment.json"))
        if len(artifacts) != 1:
            raise ValueError("HOLD_GITHUB_COMMITMENT_ARTIFACT_MISSING_OR_DUPLICATE")
        receipt = json.loads(artifacts[0].read_text(encoding="utf-8"))
    proof = _check_api_and_record(freeze,receipt,run,all_runs)
    if result is None:
        return proof
    from odds_shadow_freeze_score import score_sealed
    scored = score_sealed(freeze,result)
    return {
        **proof,
        "status":"GITHUB_SHA_PRESTART_VERIFIED_SHADOW_SCORED_NOT_V31_HOLDOUT",
        "postrace_shadow_scoring":scored,
        "formal_v31_promotion_or_prospective_calibration_not_claimed":True,
    }


def _write(path, data):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",
                 encoding="utf-8")


def demo():
    source,_=synthetic_demo()
    freeze=build_freeze(source)
    payload=freeze["payload"]
    # Fictional 2030 GitHub run; proof must be HOLD offline.
    inputs=dispatch_inputs(freeze)
    run_id=314159
    record=runner_receipt(
        repo=REPOSITORY,run_id=run_id,run_attempt=1,
        event="workflow_dispatch",
        workflow_ref=f"{REPOSITORY}/{WORKFLOW_PATH}@refs/heads/main",
        inputs=inputs)
    run={
        "id":run_id,"run_attempt":1,"event":"workflow_dispatch",
        "status":"completed","conclusion":"success","head_branch":"main",
        "repository":{"full_name":REPOSITORY},
        "path":f"{WORKFLOW_PATH}@refs/heads/main",
        "display_title":f"odds-preseal/{inputs['race_id']}",
        "created_at":"2030-01-01T04:32:00Z",
        "html_url":f"https://github.com/{REPOSITORY}/actions/runs/{run_id}",
    }
    return inspect_fixture(freeze,record,run,[run])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    cmd=ap.add_subparsers(dest="command",required=True)
    s=cmd.add_parser("dispatch")
    s.add_argument("--freeze",type=Path,required=True)
    s.add_argument("--output",type=Path,required=True)
    r=cmd.add_parser("runner")
    r.add_argument("--output",type=Path,required=True)
    v=cmd.add_parser("verify-live")
    v.add_argument("--freeze",type=Path,required=True)
    v.add_argument("--repo",default=REPOSITORY)
    v.add_argument("--run-id",type=int,required=True)
    v.add_argument("--result",type=Path)
    v.add_argument("--output",type=Path,required=True)
    d=cmd.add_parser("demo")
    d.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.command=="dispatch":
        freeze=json.loads(args.freeze.read_text(encoding="utf-8"))
        val=prepare_dispatch(freeze)
    elif args.command=="runner":
        ctx=os.environ
        val=runner_receipt(
            repo=ctx.get("GITHUB_REPOSITORY"),
            run_id=int(ctx.get("GITHUB_RUN_ID","0")),
            run_attempt=int(ctx.get("GITHUB_RUN_ATTEMPT","0")),
            event=ctx.get("GITHUB_EVENT_NAME"),
            workflow_ref=ctx.get("GITHUB_WORKFLOW_REF"),
            inputs={
                "race_id":ctx.get("SEAL_RACE_ID"),
                "seal_sha256":ctx.get("SEAL_SHA256"),
                "scheduled_post_jst":ctx.get("SEAL_POST_JST"),
                "last_source_received_jst":ctx.get("SEAL_RECEIVED_JST"),
            },
        )
    elif args.command=="verify-live":
        freeze=json.loads(args.freeze.read_text(encoding="utf-8"))
        result=(json.loads(args.result.read_text(encoding="utf-8"))
                if args.result is not None else None)
        val=verify_live(freeze,repo=args.repo,run_id=args.run_id,result=result)
    else:
        val=demo()
    _write(args.output,val)
    print(json.dumps({
        "status":val["status"],
        "race_id":val.get("race_id") or val.get("inputs",{}).get("race_id"),
        "remote_time_independently_verified":
            val["status"] in (STATUS_REMOTE,
                              "GITHUB_SHA_PRESTART_VERIFIED_SHADOW_SCORED_NOT_V31_HOLDOUT"),
        "formal_v31_holdout":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
