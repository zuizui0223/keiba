#!/usr/bin/env python3
"""PRIVATE official-race-roster vs RQ GPS sectional identity gate.

NO inference that a horse name, numbered sectional field, or all-zero
telemetry row identifies an official race starter or biological individual.
Requires a separately VERIFIED, authorized official starter/result export.
Runs locally and writes only aggregate counts (never horse names/IDs).
A successful syntactic join is NOT proof the source itself is correct.

Output remains HOLD for H1/H2 until longitudinal stable IDs, outcomes
and within-horse exposures are independently established.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unicodedata

from ecology_rq_thoroughbred_sectional_audit import (
    parse, finite_number, duration_s, vendor_header_date,
)


REQUIRED = (
    "race_date", "race_number", "official_race_id", "official_horse_id",
    "horse_name", "start_status", "finish_status", "source_url"
)
START_STATUSES = {"started","not_started","unknown"}
FINISH_STATUSES = {"finished","did_not_finish","not_applicable","unknown"}


def canon_name(name: str) -> str:
    """Conservative unicode/case/space normalization; no fuzzy guessed IDs."""
    return " ".join(unicodedata.normalize("NFKC", name).casefold().split())


def sections_in_memory(raw: bytes) -> list[dict]:
    # Strict first pass assures race-number/header, timing and layout.
    parse(raw)
    seen_headers={}
    current=None
    sectionals=[]
    for rawline in raw.decode("utf-8-sig").splitlines():
        text=rawline.strip()
        if not text:
            continue
        cells=text.split(",",2)
        if len(cells)!=3:
            raise ValueError("HOLD_UNEXPECTED_SECTIONAL_CELLS")
        day, race, packed = [x.strip() for x in cells]
        tokens=[t.strip() for t in packed.split(";")]
        if day=="Date" and race=="RaceNumber":
            current,_=vendor_header_date(tokens)
            continue
        if current is None:
            raise ValueError("HOLD_RACE_HEADER_ABSENT")
        d=datetime.strptime(day,"%d/%m/%Y").date().isoformat()
        if d != current:
            raise ValueError("HOLD_VENDOR_HEADER_RACE_DATE_MISMATCH")
        name=tokens[0]
        n=int(race)
        triples=[tokens[i:i+3] for i in range(2,len(tokens),3)]
        all_zero=all(
            finite_number(tr[1])==0 and duration_s(tr[2])==0
            for tr in triples
        )
        has_positive=any(
            finite_number(tr[1]) is not None
            and finite_number(tr[1])>0
            and duration_s(tr[2]) is not None
            and duration_s(tr[2])>0
            for tr in triples
        )
        sectionals.append({
            "race_date":d,"race_number":n,"horse_name":name,
            "name_normalized":canon_name(name),
            "gps_all_zero":bool(all_zero),"gps_positive":bool(has_positive),
        })
    return sectionals


def official_roster_rows(path:Path) -> list[dict]:
    with path.open(newline="",encoding="utf-8-sig") as fd:
        reader=csv.DictReader(fd)
        if not reader.fieldnames or set(REQUIRED)-set(reader.fieldnames):
            raise ValueError("HOLD_OFFICIAL_RESULT_EXPORT_COLUMNS_MISSING")
        results=[]
        seen=set()
        for lineno,row in enumerate(reader,start=2):
            try:
                dt=datetime.strptime(row["race_date"],"%Y-%m-%d").date().isoformat()
                number=int(row["race_number"])
            except (ValueError,TypeError) as ex:
                raise ValueError(f"HOLD_ROSTER_IDENTITY_INVALID_LINE_{lineno}") from ex
            h_id=row["official_horse_id"].strip()
            r_id=row["official_race_id"].strip()
            name=row["horse_name"].strip()
            start=row["start_status"].strip().lower()
            finish=row["finish_status"].strip().lower()
            url=row["source_url"].strip()
            if (not h_id or not r_id or not name or number<1
                    or start not in START_STATUSES
                    or finish not in FINISH_STATUSES
                    or not url.startswith("https://")):
                raise ValueError(f"HOLD_ROSTER_PROVENANCE_OR_STATUS_LINE_{lineno}")
            if start=="not_started" and finish not in ("not_applicable","unknown"):
                raise ValueError("HOLD_NONSTARTER_FINISH_STATUS_CONTRADICTION")
            if start=="started" and finish=="not_applicable":
                raise ValueError("HOLD_STARTER_FINISH_STATUS_CONTRADICTION")
            key=(dt,number,r_id,h_id)
            if key in seen:
                raise ValueError("HOLD_DUPLICATE_OFFICIAL_HORSE_ID_IN_RACE")
            seen.add(key)
            results.append({
                "race_date":dt,"race_number":number,
                "official_race_id":r_id,"official_horse_id":h_id,
                "name_normalized":canon_name(name),
                "start_status":start,"finish_status":finish,
            })
    if not results:
        raise ValueError("HOLD_EMPTY_OFFICIAL_ROSTER")
    return results


def audit(sectional_raw:bytes, roster: list[dict]) -> dict:
    gps=sections_in_memory(sectional_raw)
    by_name_day=defaultdict(list)
    by_gps=defaultdict(list)
    for item in gps:
        by_name_day[(item["race_date"],item["name_normalized"])].append(item)
        by_gps[(item["race_date"],item["race_number"],item["name_normalized"])].append(item)
    # A name appearing in different race headers on the same meeting day
    # cannot safely be elevated to permanent horse identity.
    unsafe_names={
        key for key,rows in by_name_day.items()
        if len({x["race_number"] for x in rows})>1
    }
    by_roster=defaultdict(list)
    all_official_races=defaultdict(set)
    for row in roster:
        key=(row["race_date"],row["race_number"],row["name_normalized"])
        by_roster[key].append(row)
        all_official_races[(row["race_date"],row["race_number"])].add(row["official_race_id"])
    invalid_race_identifiers=sum(len(ids)!=1 for ids in all_official_races.values())
    # One and only one official race ID is required per race date and number.
    stats=Counter()
    id_consistency=defaultdict(set)
    for item in gps:
        stats["sectional_horse_rows"]+=1
        name_day=(item["race_date"],item["name_normalized"])
        if name_day in unsafe_names:
            stats["blocked_same_day_duplicate_name"]+=1
            continue
        key=(item["race_date"],item["race_number"],item["name_normalized"])
        if len(by_gps[key])!=1:
            stats["blocked_duplicate_gps_same_race_name"]+=1
            continue
        official=by_roster.get(key,[])
        if len(official)==0:
            stats["not_matched_to_official_roster"]+=1
            continue
        if len(official)!=1:
            stats["blocked_ambiguous_official_name_match"]+=1
            continue
        row=official[0]
        id_consistency[(row["race_date"],row["name_normalized"])].add(row["official_horse_id"])
        stats["unique_syntactic_official_name_matches"]+=1
        stats["match_official_start_"+row["start_status"]]+=1
        stats["match_official_finish_"+row["finish_status"]]+=1
        if item["gps_all_zero"]:
            stats["matched_all_zero_gps"]+=1
            stats["zero_gps_official_start_"+row["start_status"]]+=1
        elif item["gps_positive"]:
            stats["matched_positive_gps"]+=1
    stats["official_roster_rows"]=len(roster)
    stats["official_races_with_conflicting_ids"]=invalid_race_identifiers
    stats["same_day_names_in_multiple_race_headers"]=len(unsafe_names)
    stats["same_day_name_mapped_to_multiple_official_horse_ids"]=sum(
        len(ids)>1 for ids in id_consistency.values()
    )
    unsafe=(stats["same_day_names_in_multiple_race_headers"]>0
            or stats["blocked_ambiguous_official_name_match"]>0
            or stats["official_races_with_conflicting_ids"]>0
            or stats["same_day_name_mapped_to_multiple_official_horse_ids"]>0)
    return {
        "status":"HOLD_OFFICIAL_EQUIVALENCE_AND_LONGITUDINAL_VALIDATION",
        "scope":"a candidate identity-crosswalk compatibility screen, NOT a horse H1/H2 panel",
        "source_sha256":hashlib.sha256(sectional_raw).hexdigest(),
        "counts":dict(stats),
        "ambiguous_identity_or_duplicate_contexts":unsafe,
        "unverified_name_and_number_were_not_upgraded_to_biological_ID":True,
        "all_zero_gps_not_assumed_dnf":True,
        "no_individual_raw_records_exported":True,
        "manual_source_rights_and_roster_validity_review_required":True,
        "limitations":[
            "Caller must independently verify the uploaded official roster export and result/status metadata.",
            "A same-race exact name join is only provisional; names and race numbers are not biological IDs.",
            "Same-day repeated names across race headings are blocked, not selected by favorable telemetry.",
            "No fuzzy matching or guessing missing HORSES IDs; ambiguous cases remain unmatched.",
            "Zero GPS sections cannot establish whether an animal actually started or finished.",
            "The source heading race-level duration is not converted into an individual horse finish time.",
            "Longitudinal within-horse environmental replication and rival completeness still need independent checks.",
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sectionals",type=Path,required=True)
    p.add_argument("--official-roster",type=Path,required=True)
    p.add_argument("--audit",type=Path,required=True)
    args=p.parse_args()
    data=args.sectionals.read_bytes()
    official=official_roster_rows(args.official_roster)
    result=audit(data,official)
    args.audit.parent.mkdir(parents=True,exist_ok=True)
    args.audit.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"counts":result["counts"]},ensure_ascii=False))


if __name__=="__main__":
    main()
