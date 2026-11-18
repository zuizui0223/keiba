#!/usr/bin/env python3
"""Explicitly non-exhaustive CC0 Wikidata Japanese-origin horse pedigree pilot.

Wikidata claims are a SECONDARY source, not an official Japanese register.
Runs small bounded SPARQL queries and emits anonymous aggregate diagnostics.
A failed query is HOLD, never an invented horse count or zero kin effect.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from itertools import combinations
from pathlib import Path
import re
from urllib.parse import urlencode
import urllib.error
import urllib.request

from ecology_japan_registry_pedigree import RegistryPedigree, counts

BASE = "https://query.wikidata.org/sparql"
QID = re.compile(r"Q[1-9][0-9]*$")
ENTITY = re.compile(r"https?://www\.wikidata\.org/entity/(Q[1-9][0-9]*)$")
CLAIM_LIMIT = 5_000_000

# Horse subclasses plus explicit country of origin = Japan.
JAPANESE_ORIGIN = """
SELECT DISTINCT ?horse ?father ?mother WHERE {
  ?horse wdt:P31/wdt:P279* wd:Q726 .
  ?horse wdt:P495 wd:Q17 .
  OPTIONAL { ?horse wdt:P22 ?father . }
  OPTIONAL { ?horse wdt:P25 ?mother . }
}
ORDER BY ?horse
LIMIT {limit}
"""

# Fallback is Japanese-language Wikipedia documented horses, NOT "all Japan".
JAPANESE_ARTICLE = """
PREFIX schema: <http://schema.org/>
SELECT DISTINCT ?horse ?father ?mother WHERE {
  ?article schema:about ?horse; schema:isPartOf <https://ja.wikipedia.org/> .
  ?horse wdt:P31/wdt:P279* wd:Q726 .
  OPTIONAL { ?horse wdt:P22 ?father . }
  OPTIONAL { ?horse wdt:P25 ?mother . }
}
ORDER BY ?horse
LIMIT {limit}
"""


def source_get(query: str) -> list[dict]:
    url = BASE + "?" + urlencode({"query":query, "format":"json"})
    req = urllib.request.Request(url, headers={
        "User-Agent":"keiba-pedigree-research/0.1 (academic demonstration; contacts via GitHub zuizui0223/keiba)",
        "Accept":"application/sparql-results+json",
    })
    with urllib.request.urlopen(req,timeout=40) as f:
        body=f.read(CLAIM_LIMIT+1)
        if len(body)>CLAIM_LIMIT:
            raise ValueError("HOLD_WIKIDATA_RESPONSE_TOO_LARGE")
    payload=json.loads(body)
    return payload["results"]["bindings"]


def entity(value: dict|None) -> str|None:
    if not value:
        return None
    url=value.get("value", "")
    m=ENTITY.fullmatch(url)
    if not m:
        raise ValueError("HOLD_NON_QID_WIKIDATA_PARENT")
    return m.group(1)


def normalize(rows: list[dict]) -> dict[str,dict[str,str]]:
    result={}
    for row in rows:
        horse=entity(row.get("horse"))
        if not horse or not QID.fullmatch(horse):
            raise ValueError("HOLD_NON_QID_HORSE")
        entry={"horse_id":horse,"sire_id":entity(row.get("father")) or "",
               "dam_id":entity(row.get("mother")) or ""}
        if horse in result and result[horse]!=entry:
            raise ValueError("HOLD_CONFLICTING_PARENTS_IN_WIKIDATA")
        result[horse]=entry
    return result


def ancestor_query(ids: list[str]) -> str:
    if not ids or len(ids)>60 or any(not QID.fullmatch(x) for x in ids):
        raise ValueError("HOLD_BAD_ANCESTOR_BATCH")
    values=" ".join("wd:"+x for x in ids)
    return f"""
SELECT DISTINCT ?horse ?father ?mother WHERE {{
  VALUES ?horse {{ {values} }}
  OPTIONAL {{ ?horse wdt:P22 ?father . }}
  OPTIONAL {{ ?horse wdt:P25 ?mother . }}
}}
"""


def source_report(*, max_targets:int=1500,
                  ancestor_generations:int=3, max_requests:int=32) -> dict:
    if not 10<=max_targets<=5000 or not 0<=ancestor_generations<=5 or max_requests<1:
        raise ValueError("HOLD_UNSAFE_PILOT_BOUNDS")
    status=[]
    lane="wikidata_japan_origin_P495_Q17"
    try:
        seeds=normalize(source_get(JAPANESE_ORIGIN.replace("{limit}",str(max_targets))))
    except (TimeoutError,urllib.error.URLError,urllib.error.HTTPError,
            ValueError,KeyError,TypeError,OSError) as ex:
        return {
            "status":"HOLD_WIKIDATA_SOURCE_REQUEST_FAILED",
            "reason_type":type(ex).__name__,
            "source_country_scope":"P495=Japan",
            "actual_horse_or_kin_counts_available":False,
        }
    if not seeds:
        lane="ja_wikipedia_sitelink_not_confirmed_japan_only"
        try:
            seeds=normalize(source_get(JAPANESE_ARTICLE.replace("{limit}",str(max_targets))))
        except (TimeoutError,urllib.error.URLError,urllib.error.HTTPError,
                ValueError,KeyError,TypeError,OSError) as ex:
            return {"status":"HOLD_SECONDARY_SOURCE_REQUEST_FAILED",
                    "reason_type":type(ex).__name__,
                    "actual_horse_or_kin_counts_available":False}
    if not seeds:
        return {"status":"HOLD_WIKIDATA_ZERO_SEED_ITEMS",
                "actual_horse_or_kin_counts_available":False}
    seed_ids=sorted(seeds)
    all_rows=dict(seeds)
    pending={
        x for r in all_rows.values() for x in (r["sire_id"],r["dam_id"])
        if x and x not in all_rows
    }
    requests=0
    completed=0
    ancestor_error=None
    for generation in range(ancestor_generations):
        if not pending:
            completed+=1
            break
        if requests >= max_requests:
            break
        next_pending=set()
        batch_ids=sorted(pending)
        pending=set()
        for offset in range(0,len(batch_ids),50):
            batch=batch_ids[offset:offset+50]
            if requests >= max_requests:
                pending.update(batch_ids[offset:])
                break
            try:
                got=normalize(source_get(ancestor_query(batch)))
            except (TimeoutError,urllib.error.URLError,urllib.error.HTTPError,
                    ValueError,KeyError,TypeError,OSError) as ex:
                # Keep the already verified direct parent relationships in
                # the real subset; do not upgrade missing ancestors to zero.
                ancestor_error={
                    "status":"HOLD_WIKIDATA_ANCESTOR_FETCH_FAILED",
                    "reason_type":type(ex).__name__,
                    "http_status_code":ex.code if isinstance(ex,urllib.error.HTTPError) else None,
                }
                pending.update(batch_ids[offset:])
                break
            requests+=1
            for qid in batch:
                row=got.get(qid,{"horse_id":qid,"sire_id":"","dam_id":""})
                if qid in all_rows and all_rows[qid]!=row:
                    return {"status":"HOLD_ANCESTOR_SOURCE_CONFLICT",
                            "coverage_not_exhaustive":True}
                all_rows[qid]=row
                for parent in (row["sire_id"],row["dam_id"]):
                    if parent and parent not in all_rows:
                        next_pending.add(parent)
        if pending:
            pending.update(next_pending)
            break
        pending=next_pending
        completed+=1
    reg=RegistryPedigree(list(all_rows.values()),cache_size=150000)
    count, _=counts(reg,seed_ids)
    subset=seed_ids[:min(100,len(seed_ids))]
    computed=0
    documented=0
    high=0
    for a,b in combinations(subset,2):
        v=reg.a(a,b)
        computed+=1
        documented+=v>0
        high+=v>=0.125
    return {
        "status":("REAL_CC0_WIKIDATA_SECONDARY_PEDIGREE_SUBSET_ANCESTOR_HOLD"
                  if ancestor_error else
                  "REAL_CC0_WIKIDATA_SECONDARY_PEDIGREE_SUBSET_NOT_JAPAN_COMPLETE"),
        "source":"https://query.wikidata.org/sparql",
        "source_license":"CC0",
        "extraction_date_utc":date.today().isoformat(),
        "seed_selection_rule":lane,
        "max_seed_limit":max_targets,
        "seed_hits_limit":len(seed_ids)==max_targets,
        "no_coverage_fraction_claim":True,
        "ancestor_generations_requested":ancestor_generations,
        "ancestor_batches_executed":requests,
        "ancestor_fetch_error":ancestor_error,
        "ancestor_rows_observed":len(all_rows)-len(seed_ids),
        "ancestry_complete_to_requested_depth":not bool(pending),
        "unexpanded_ancestor_ids":len(pending),
        "known_parentage":count,
        "exact_A_pair_check_first_100_QIDs": {
            "queries":computed,
            "positive_documented_path_pairs":documented,
            "partial_A_at_least_0_125_pairs":high,
            "NOT_all_seed_pairs":True
        },
        "does_not_estimate_heritability_or_racing_forecast":True,
        "not_an_official_JRA_NAR_registry":True,
        "no_unverified_name_joins_or_JBIS_bulk_access":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--max-targets",type=int,default=1500)
    ap.add_argument("--ancestor-generations",type=int,default=3)
    ap.add_argument("--max-requests",type=int,default=32)
    args=ap.parse_args()
    report=source_report(max_targets=args.max_targets,
                         ancestor_generations=args.ancestor_generations,
                         max_requests=args.max_requests)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
