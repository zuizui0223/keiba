#!/usr/bin/env python3
"""Capture private authorized JRA-VAN SQLite state with aggregate SHA receipts.

NO JRA/JBIS API calls, scraping, implicit data license or public horse rows.
Consistent sqlite3 online backup; source opened read-only, dest outside repo.
Public manifest = hash, source QA and row-delta counts only. The local clock
is not external proof of pre-race capture: commit a manifest BEFORE racing
and independently attest receipt timestamps. This tool never converts
MakeDate to source-published or result-known-at timestamps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta

from ecology_japan_jrvltsql_sqlite_qa import (
    TABLE_COLUMNS, audit as source_qa, sha256
)
from ecology_japan_2027_official_knownon_preflight import local_jst

JST_ZONE = timezone(timedelta(hours=9))
SCHEMA = "JRA_LOCAL_SQLITE_ASOF_RECEIPT_V1"
KEYS = {
    "NL_RA": ("Year","MonthDay","JyoCD","Kaiji","Nichiji","RaceNum"),
    "NL_SE": ("Year","MonthDay","JyoCD","Kaiji","Nichiji","RaceNum","Umaban","KettoNum"),
    "NL_UM": ("KettoNum",),
    "NL_SK": ("KettoNum",),
    "NL_HN": ("HansyokuNum",),
}
PHASES = ("pre_race", "post_race", "master")


def _utc(value:datetime) -> datetime:
    if not isinstance(value,datetime) or value.tzinfo is None:
        raise ValueError("HOLD_CAPTURE_CLOCK_NOT_AWARE")
    return value.astimezone(timezone.utc)


def _now(clock=None):
    # A clock callback is accepted ONLY for deterministic fictional tests.
    return _utc(clock() if clock is not None else datetime.now(timezone.utc))


def _inside_git(path:Path) -> bool:
    # Check ancestry, not just pwd: a private backup must never enter git.
    p=path.resolve()
    cwd=Path.cwd().resolve()
    for ancestor in (cwd,*cwd.parents):
        if (ancestor/".git").exists() and p.is_relative_to(ancestor):
            return True
    return False


def _safe_private_output(source:Path, private:Path, public:Path):
    if source.resolve()==private.resolve():
        raise ValueError("HOLD_CAPTURE_SOURCE_AND_DESTINATION_IDENTICAL")
    if private.resolve()==public.resolve():
        raise ValueError("HOLD_PRIVATE_SNAPSHOT_AND_PUBLIC_MANIFEST_SAME_PATH")
    if _inside_git(private):
        raise ValueError("HOLD_PRIVATE_SQLITE_DESTINATION_INSIDE_GIT_TREE")
    if private.exists() or public.exists():
        raise ValueError("HOLD_NO_OVERWRITE_PRIOR_RECEIPT_OR_SNAPSHOT")
    private.parent.mkdir(parents=True,exist_ok=True)
    public.parent.mkdir(parents=True,exist_ok=True)


def _schema_columns(conn, name):
    exists=conn.execute("SELECT COUNT(*) FROM sqlite_master "
                        "WHERE type='table' AND name=?",(name,)).fetchone()[0]
    if not exists:
        return None
    return [str(r[1]) for r in conn.execute(f'PRAGMA table_info("{name}")')]


def _ordered_rows(conn,table,cols):
    idx=[cols.index(col) for col in KEYS[table]]
    order=", ".join('"'+col+'" COLLATE BINARY' if col in ("JyoCD","KettoNum","HansyokuNum") else '"'+col+'"' for col in KEYS[table])
    last=None
    cursor=conn.execute(f'SELECT * FROM "{table}" ORDER BY {order}')
    for row in cursor:
        key=tuple(row[i] for i in idx)
        if any(x is None or (isinstance(x,str) and not x.strip()) for x in key):
            raise ValueError("HOLD_NULL_OR_BLANK_PRIMARY_SOURCE_KEY")
        if key==last:
            raise ValueError("HOLD_DUPLICATE_PRIMARY_SOURCE_KEY")
        last=key
        yield key,tuple(row)


def _next(it):
    return next(it,None)


def _diff_table(before,after,name):
    cols0=_schema_columns(before,name)
    cols1=_schema_columns(after,name)
    if cols0 is None or cols1 is None:
        return {"status":"HOLD_MISSING_TABLE_IN_CHANGE_COMPARISON"}
    if cols0!=cols1 or not set(KEYS[name]).issubset(cols0):
        raise ValueError("HOLD_SCHEMA_DRIFT_IN_PRIVATE_SNAPSHOT_DIFF")
    i0=iter(_ordered_rows(before,name,cols0))
    i1=iter(_ordered_rows(after,name,cols1))
    a,b=_next(i0),_next(i1)
    out={"inserted":0,"changed":0,"removed":0,"unchanged":0}
    while a is not None or b is not None:
        if a is None:
            out["inserted"]+=1
            b=_next(i1)
        elif b is None:
            out["removed"]+=1
            a=_next(i0)
        elif a[0]==b[0]:
            out["unchanged" if a[1]==b[1] else "changed"]+=1
            a,b=_next(i0),_next(i1)
        elif a[0]<b[0]:
            out["removed"]+=1
            a=_next(i0)
        else:
            out["inserted"]+=1
            b=_next(i1)
    out["status"]="COUNTED_BY_COMPOSITE_SOURCE_KEYS_NOT_PROVIDER_REVISION_CERTIFICATION"
    return out


def delta_aggregate(prior:Path,new:Path):
    """Streaming source-record diff; only counts are returned."""
    result={}
    with sqlite3.connect(prior.resolve().as_uri()+"?mode=ro",uri=True) as old:
        with sqlite3.connect(new.resolve().as_uri()+"?mode=ro",uri=True) as current:
            old.execute("PRAGMA query_only=ON")
            current.execute("PRAGMA query_only=ON")
            for name in KEYS:
                result[name]=_diff_table(old,current,name)
    return result


def receipt_verify(snapshot:Path, manifest_path:Path, *,
                   prev_manifest:Path|None=None):
    if not snapshot.is_file() or not manifest_path.is_file():
        raise ValueError("HOLD_MISSING_LOCAL_RECEIPT_OR_PRIVATE_SNAPSHOT")
    r=json.loads(manifest_path.read_text(encoding="utf-8"))
    if r.get("schema")!=SCHEMA:
        raise ValueError("HOLD_RECEIPT_SCHEMA_MISMATCH")
    if sha256(snapshot)!=r.get("private_snapshot_sha256"):
        raise ValueError("HOLD_PRIVATE_SQLITE_SNAPSHOT_HASH_DRIFT")
    if snapshot.stat().st_size!=r.get("private_snapshot_bytes"):
        raise ValueError("HOLD_PRIVATE_SQLITE_SNAPSHOT_SIZE_DRIFT")
    if r.get("previous_receipt_sha256") is not None:
        if prev_manifest is None or not prev_manifest.is_file():
            raise ValueError("HOLD_PREVIOUS_RECEIPT_REQUIRED_FOR_CHAIN")
        if sha256(prev_manifest)!=r["previous_receipt_sha256"]:
            raise ValueError("HOLD_PREVIOUS_RECEIPT_HASH_DRIFT")
        prev=json.loads(prev_manifest.read_text(encoding="utf-8"))
        if prev.get("schema")!=SCHEMA:
            raise ValueError("HOLD_PREVIOUS_RECEIPT_SCHEMA")
    return {
        "status":"LOCAL_SQLITE_RECEIPT_DIGEST_MATCHES_NOT_EXTERNALLY_TIME_ATTESTED",
        "snapshot_sha256":r["private_snapshot_sha256"],
        "prior_receipt_chain_present":bool(r.get("previous_receipt_sha256")),
        "independent_pre_race_public_commit_verified":False,
        "no_horse_IDs_or_race_rows_in_output":True,
    }


def capture(source:Path, private:Path, public:Path, *,
            phase:str, race_start_jst:str|None=None,
            previous_receipt:Path|None=None,
            previous_private:Path|None=None,
            clock=None):
    """Capture consistent source image and output only an aggregate receipt.

    Never trust the optional test-only callback as a real wall-clock attestor.
    Real CLI has no --clock argument; it uses actual observed local time.
    """
    if phase not in PHASES:
        raise ValueError("HOLD_UNKNOWN_CAPTURE_PHASE")
    if phase=="master" and race_start_jst:
        raise ValueError("HOLD_MASTER_RECEIPT_HAS_RACE_START")
    if phase!="master" and not race_start_jst:
        raise ValueError("HOLD_RACE_PHASE_WITHOUT_EXPLICIT_TARGET_START_JST")
    start=local_jst(race_start_jst) if race_start_jst else None
    if (previous_receipt is None)!=(previous_private is None):
        raise ValueError("HOLD_PRIOR_RECEIPT_AND_PRIVATE_SNAPSHOT_MUST_PAIR")
    if not source.is_file() or source.stat().st_size==0:
        raise ValueError("HOLD_MISSING_AUTHORIZED_LOCAL_JRAVAN_SQLITE")
    _safe_private_output(source,private,public)
    t0=_now(clock)
    if start is not None:
        if phase=="pre_race" and not t0<start:
            raise ValueError("HOLD_PRE_RACE_CAPTURE_NOT_STARTED_BEFORE_RACE")
        if phase=="post_race" and not t0>start:
            raise ValueError("HOLD_POST_RACE_CAPTURE_NOT_STARTED_AFTER_RACE")
    prev=None
    previous_hash=None
    if previous_receipt is not None:
        receipt_verify(previous_private,previous_receipt)
        prev=json.loads(previous_receipt.read_text(encoding="utf-8"))
        previous_hash=sha256(previous_receipt)
        if not _utc(datetime.fromisoformat(prev["capture_finished_utc"]))<t0:
            raise ValueError("HOLD_PRIOR_RECEIPT_TIME_NOT_EARLIER")
    # Secure temporary private file: never expose or upload to GitHub.
    fd,tmp_name=tempfile.mkstemp(prefix=".jra-private-backup-",suffix=".sqlite",
                                dir=str(private.parent))
    os.close(fd)
    tmp=Path(tmp_name)
    try:
        with sqlite3.connect(source.resolve().as_uri()+"?mode=ro",uri=True,
                             timeout=30) as src:
            src.execute("PRAGMA query_only=ON")
            v0=src.execute("PRAGMA data_version").fetchone()[0]
            with sqlite3.connect(tmp) as dest:
                src.backup(dest,pages=256,sleep=0.05)
                integrity=dest.execute("PRAGMA quick_check(1)").fetchone()[0]
                if integrity!="ok":
                    raise ValueError("HOLD_CAPTURED_SQLITE_INTEGRITY_CHECK")
            v1=src.execute("PRAGMA data_version").fetchone()[0]
            if v0!=v1:
                raise ValueError("HOLD_SOURCE_CHANGED_DURING_PRIVATE_BACKUP")
        qa=source_qa(tmp)
        delta=(delta_aggregate(previous_private,tmp)
               if previous_private is not None else None)
        t1=_now(clock)
        if t1<t0:
            raise ValueError("HOLD_CAPTURE_CLOCK_MOVED_BACKWARD")
        if phase=="pre_race" and not t1<start:
            raise ValueError("HOLD_PRE_RACE_BACKUP_NOT_FINISHED_BEFORE_RACE")
        if phase=="post_race" and not t1>start:
            raise ValueError("HOLD_POST_RACE_BACKUP_NOT_AFTER_RACE")
        snapshot_sha=sha256(tmp)
        manifest={
            "schema":SCHEMA,
            "status":"LOCAL_SNAPSHOT_RECEIVED_NO_INDEPENDENT_PUBLIC_TIME_ATTESTATION",
            "capture_phase":phase,
            "capture_started_utc":t0.isoformat(),
            "capture_finished_utc":t1.isoformat(),
            "capture_finished_jst":t1.astimezone(JST_ZONE).isoformat(),
            "target_race_start_jst":start.isoformat() if start else None,
            "private_snapshot_sha256":snapshot_sha,
            "private_snapshot_bytes":tmp.stat().st_size,
            "previous_receipt_sha256":previous_hash,
            "prior_source_table_deltas_counts_only":delta,
            "source_schema_and_coverage_aggregate":qa,
            "source_was_opened_read_only":True,
            "private_copy_uses_consistent_sqlite_backup":True,
            "no_source_change_seen_by_sqlite_data_version":True,
            "local_clock_injected_for_synthetic_test":bool(clock is not None),
            "local_clock_NOT_external_timestamp_proof":True,
            "must_commit_aggregate_receipt_before_target_start_for_independent_review":True,
            "MakeDate_NOT_actual_provider_publish_time":True,
            "receiver_possession_not_JRA_publication":True,
            "not_authenticated_provider_and_no_license_assumed":True,
            "no_horse_ids_names_race_rows_or_individual_predictions_in_receipt":True,
            "2027_real_race_knowntime_or_genetic_effect_NOT_established":True,
        }
        # Only after every gate passes do the atomic private rename and
        # immutable public receipt write occur. No source data in the latter.
        os.replace(tmp,private)
        os.chmod(private,0o600)
        try:
            with public.open("xb") as f:
                f.write((json.dumps(manifest,ensure_ascii=False,indent=2,
                                    sort_keys=True,allow_nan=False)+"\n").encode("utf-8"))
        except Exception:
            # A private backup can remain for forensic recovery, but the
            # unmatched manifest must NOT be declared an audited capture.
            raise
        return manifest
    finally:
        if tmp.exists():
            tmp.unlink()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest="command",required=True)
    ca=sub.add_parser("capture")
    ca.add_argument("--authorized-local-db",type=Path,required=True)
    ca.add_argument("--private-snapshot-out",type=Path,required=True)
    ca.add_argument("--public-receipt-out",type=Path,required=True)
    ca.add_argument("--phase",required=True,choices=PHASES)
    ca.add_argument("--race-start-jst")
    ca.add_argument("--previous-receipt",type=Path)
    ca.add_argument("--previous-private-snapshot",type=Path)
    ver=sub.add_parser("verify")
    ver.add_argument("--private-snapshot",type=Path,required=True)
    ver.add_argument("--public-receipt",type=Path,required=True)
    ver.add_argument("--previous-receipt",type=Path)
    args=ap.parse_args()
    if args.command=="capture":
        m=capture(args.authorized_local_db,args.private_snapshot_out,
                  args.public_receipt_out,phase=args.phase,
                  race_start_jst=args.race_start_jst,
                  previous_receipt=args.previous_receipt,
                  previous_private=args.previous_private_snapshot)
        print(json.dumps(m,ensure_ascii=False,indent=2))
    else:
        print(json.dumps(receipt_verify(
            args.private_snapshot,args.public_receipt,
            prev_manifest=args.previous_receipt
        ),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
