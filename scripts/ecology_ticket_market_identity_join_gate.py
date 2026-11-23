#!/usr/bin/env python3
"""Identity coverage of the nine-race win+wide ecology market sample.

This is a data-linkage GATE, not a pedigree or biological result.
Oct12 five Kyoto racecards sometimes cite an individual Yahoo horse
directory page; these source-specific 10-digit tokens are only
UNVERIFIED CANDIDATE identity keys, not confirmed JRA/NAR registry IDs.
Oct18 nine-race quote archive stores names/horse numbers but has no
equivalent certified registered horse ID or pedigree/G sample key.

Do not join by names alone, invent horse IDs from race numbers, link
genotypes by owner's prefixes, or use later race outcomes as features.
Disclose counts and source hashes, never the horse names or tokens.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

try:
    from scripts.ticket_type_historical_audit import ROOT, SOURCE_DATE, TARGET_RACES
    from scripts.ticket_wide_second_day import SAVED_SNAPSHOT_PATH
except (ImportError, ModuleNotFoundError):
    from ticket_type_historical_audit import ROOT, SOURCE_DATE, TARGET_RACES
    from ticket_wide_second_day import SAVED_SNAPSHOT_PATH

DIR_PATH=re.compile(r"^/keiba/directory/horse/([0-9]{10})/?$")
STATUS="HOLD_UNVERIFIED_DIRECTORY_ID_PARTIAL_COVERAGE_NO_CROSS_DATE_MARKET_GENETICS_JOIN"


def directory_candidate(url: str) -> str | None:
    if not isinstance(url,str):
        return None
    p=urlsplit(url)
    if (p.scheme!="https" or p.hostname!="sports.yahoo.co.jp" or
            p.username or p.password or p.port or p.query or p.fragment):
        return None
    m=DIR_PATH.fullmatch(p.path)
    return m.group(1) if m else None


def audit_card(card:dict, race:int)->tuple[dict,list[str]]:
    if card.get("race")!=race or card.get("date")!=SOURCE_DATE:
        raise ValueError("racecard_identity_mismatch")
    horses=card.get("horses")
    if not isinstance(horses,list) or len(horses)<8:
        raise ValueError("missing_racecard_horses")
    seen=set()
    candidates=[]
    for horse in horses:
        n=horse.get("number")
        if type(n) is not int or n in seen:
            raise ValueError("invalid_or_duplicate_horse_number")
        seen.add(n)
        refs={
            identity for ref in horse.get("evidence_urls",[])
            if (identity:=directory_candidate(ref)) is not None
        }
        if len(refs)>1:
            raise ValueError("multiple_directory_identity_candidates")
        if refs:
            candidates.append(next(iter(refs)))
    if len(set(candidates))!=len(candidates):
        raise ValueError("directory_token_reused_within_race")
    return {
        "race_number":race,
        "horses":len(horses),
        "with_one_directory_candidate":len(candidates),
        "without_directory_candidate":len(horses)-len(candidates),
        "source_identifier_kind":"Yahoo_horse_directory_10digit_UNVERIFIED",
    },candidates


def audit_all()->dict:
    out=[]
    hashes={}
    seen=[]
    for r in TARGET_RACES:
        path=ROOT/"data"/SOURCE_DATE/f"kyoto_{r:02d}.json"
        raw=path.read_bytes()
        hashes[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
        card=json.loads(raw)
        summary,candidates=audit_card(card,r)
        out.append(summary)
        seen+=candidates
    raw=SAVED_SNAPSHOT_PATH.read_bytes()
    hashes[str(SAVED_SNAPSHOT_PATH.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
    later=json.loads(raw)
    if len(later.get("races",[]))!=9:
        raise ValueError("later_race_count_changed")
    all_horses=[h for race in later["races"] for h in race["horses"]]
    stable_rows=sum(bool(h.get("horse_id") or h.get("registry_id"))
                    for h in all_horses)
    candidate_rows=sum(bool(h.get("directory_id") or h.get("directory_url"))
                       for h in all_horses)
    n12=sum(x["horses"] for x in out)
    with_candidate=sum(x["with_one_directory_candidate"] for x in out)
    return {
        "schema_version":1,
        "status":STATUS,
        "Oct12_Kyoto_five_races":{
            "race_count":len(out),
            "horse_rows":n12,
            "directory_ID_candidate_rows":with_candidate,
            "missing_directory_candidate_rows":n12-with_candidate,
            "unique_directory_ID_candidates":len(set(seen)),
            "candidate_tokens_reused_across_racecards":len(seen)-len(set(seen)),
            "by_race":out,
            "not_confirmed_JRA_registered_horse_IDs":True,
        },
        "Oct18_9_race_quote_archive":{
            "race_count":9,
            "horse_quote_rows":len(all_horses),
            "rows_with_explicit_stable_registry_ID":stable_rows,
            "rows_with_explicit_directory_ID_or_URL":candidate_rows,
            "name_to_ID_lookup_without_verified_source_forbidden":True,
        },
        "actual_verified_same_horse_ID_between_market_dates":0,
        "cross_date_registered_ID_join_possible_from_current_quote_sources":False,
        "genomic_G_or_pedigree_A_same_individual_verified_join":False,
        "multi_race_individual_node_repeatability_identified":False,
        "uses_anonymous_aggregate_only":True,
        "source_file_sha256":dict(sorted(hashes.items())),
        "next_required_step":"Obtain authoritative registry horse ID/source and known-on timestamp for BOTH dates, verify pedigree/genotype identity mapping separately and compare repeated starts, not a name-only fuzzy join.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    try:
        out=audit_all()
    except (OSError,ValueError,TypeError,KeyError) as e:
        p.error(str(e))
    payload=json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(payload,encoding="utf-8")
    else:
        print(payload,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
