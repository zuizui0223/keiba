#!/usr/bin/env python3
"""Bounded Wikimedia-ID cross-check for Japanese racehorse missing dams.

This supplements, does not replace, the Wikipedia article pedigree.
Only exact ja.wikipedia page title -> Wikidata QID mapping and unique
nondeprecated P22/P25 statements. Never infer IDs from text names.
This is a *targeted* secondary-source audit, NOT a complete national
registry and NOT an official genealogical verification.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import random
import re
import time
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

from ecology_japan_wikipedia_large import prepare_infoboxes,PREFIX
from ecology_japan_registry_pedigree import RegistryPedigree

WIKI="https://ja.wikipedia.org/w/api.php"
WD="https://www.wikidata.org/w/api.php"
UA="keiba-wikipedia-parentage-audit/0.1 (+https://github.com/zuizui0223/keiba)"
QID=re.compile(r"^Q[1-9][0-9]*$")
FAIL_CLASSES=(HTTPError,URLError,TimeoutError,OSError,ValueError,KeyError,TypeError)


def selection(boxes:dict, *, limit:int=200, seed:int=20261114) -> list[str]:
    if not 1<=limit<=250:
        raise ValueError("HOLD_INVALID_SECONDARY_SOURCE_SAMPLE_LIMIT")
    # Over-sample Meisho by design, then randomly select articles whose
    # Japanese infobox lacks a uniquely linked mother. Nonrepresentative!
    full,meta,_=prepare_infoboxes(boxes)
    meisho=sorted(meta["meisho_titles"])
    elig=[name for name in meta["article_titles"]
          if name not in meisho and full.recorded[PREFIX+name][1] is None]
    random.Random(seed).shuffle(elig)
    return (meisho+elig)[:limit]


def json_get(endpoint:str, params:dict, *, maxbytes:int=5_000_000) -> dict:
    if endpoint not in (WIKI,WD):
        raise ValueError("HOLD_UNSUPPORTED_WIKIMEDIA_ENDPOINT")
    # HTTP bounded, no non-Wikimedia redirects accepted.
    request=Request(endpoint+"?"+urlencode(params), headers={
        "User-Agent":UA,"Accept":"application/json"
    })
    with urlopen(request,timeout=32) as res:
        if not res.geturl().startswith("https://") or ("wikipedia.org" not in res.geturl() and "wikidata.org" not in res.geturl()):
            raise ValueError("HOLD_UNSAFE_SOURCE_REDIRECT")
        payload=res.read(maxbytes+1)
        if len(payload)>maxbytes:
            raise ValueError("HOLD_RESPONSE_TOO_LARGE")
    answer=json.loads(payload)
    if not isinstance(answer,dict) or "error" in answer:
        raise ValueError("HOLD_WIKIMEDIA_API_ERROR")
    return answer


def parse_pageprops(data:dict) -> dict[str,str]:
    out={}
    pages=data.get("query",{}).get("pages",{})
    if isinstance(pages,list):
        pages={str(i):p for i,p in enumerate(pages)}
    for page in pages.values():
        if page.get("missing") is not None:
            continue
        name=page.get("title")
        qid=page.get("pageprops",{}).get("wikibase_item")
        if name and qid and QID.fullmatch(qid) and name not in out:
            out[name]=qid
    return out


def parse_parent_claims(entity:dict, prop:str) -> str|None:
    ranked=[]
    for c in entity.get("claims",{}).get(prop,[]):
        if c.get("rank")=="deprecated":
            continue
        snak=c.get("mainsnak",{})
        if snak.get("snaktype")!="value":
            continue
        val=snak.get("datavalue",{}).get("value",{})
        qid=val.get("id") if isinstance(val,dict) else None
        if qid and QID.fullmatch(qid):
            ranked.append((c.get("rank")=="preferred",qid))
    if not ranked:
        return None
    preferred={qid for pref,qid in ranked if pref}
    candidates=preferred if preferred else {qid for _,qid in ranked}
    if len(candidates)!=1:
        raise ValueError("HOLD_AMBIGUOUS_MULTIPLE_PARENTS_"+prop)
    return next(iter(candidates))


def run(boxes:dict, *, limit:int=200,batch:int=25,max_requests:int=20) -> dict:
    if not 1<=batch<=50 or max_requests<2 or max_requests>30:
        raise ValueError("HOLD_UNSAFE_REQUEST_LIMIT")
    chosen=selection(boxes,limit=limit)
    full,_,_=prepare_infoboxes(boxes)
    qid_map={}
    parents={}
    attempts=0
    failures=Counter()
    fetched=0
    # Two FIRST-PARTY Wikimedia APIs per batch: ja-Wikipedia pageprops,
    # then Wikidata's verified QID claim record. No web search/name matches.
    for i in range(0,len(chosen),batch):
        titles=chosen[i:i+batch]
        if attempts+2 > max_requests:
            failures["HOLD_REQUEST_BUDGET_EXHAUSTED"]+=len(titles)
            break
        attempts+=1
        try:
            x=json_get(WIKI,{"action":"query","prop":"pageprops",
                           "ppprop":"wikibase_item","titles":"|".join(titles),
                           "redirects":1,"format":"json","maxlag":5})
            qid_map.update(parse_pageprops(x))
        except FAIL_CLASSES as exc:
            failures["HOLD_PAGEPROPS_"+type(exc).__name__]+=len(titles)
            break
        qids=sorted(set(qid_map[t] for t in titles if t in qid_map))
        if not qids:
            continue
        attempts+=1
        try:
            y=json_get(WD,{"action":"wbgetentities","ids":"|".join(qids),
                           "props":"claims","format":"json","maxlag":5})
        except FAIL_CLASSES as exc:
            failures["HOLD_WIKIDATA_CLAIMS_"+type(exc).__name__]+=len(titles)
            break
        entities=y.get("entities",{})
        for t in titles:
            qid=qid_map.get(t)
            if not qid or qid not in entities:
                continue
            entity=entities[qid]
            try:
                s=parse_parent_claims(entity,"P22")
                d=parse_parent_claims(entity,"P25")
            except ValueError:
                failures["HOLD_AMBIGUOUS_PARENTS"]+=1
                continue
            parents[t]=(s,d)
            fetched+=1
        time.sleep(0.25)
    qid_to_title={qid:t for t,qid in qid_map.items()}
    conflicts=Counter()
    repaired=Counter()
    wd_rows=[]
    for title,(s,d) in parents.items():
        wiki_s,wiki_d=full.recorded[PREFIX+title]
        if s and wiki_s:
            # Only call source agreement when the linked article itself
            # has an independently retrieved Wikidata QID.
            wiki_parent=wiki_s[len(PREFIX):]
            mapped=qid_map.get(wiki_parent)
            if mapped and mapped!=s:
                conflicts["sire_disagreement_in_two_exact_ID_sources"]+=1
        if d and wiki_d:
            wiki_parent=wiki_d[len(PREFIX):]
            mapped=qid_map.get(wiki_parent)
            if mapped and mapped!=d:
                conflicts["dam_disagreement_in_two_exact_ID_sources"]+=1
        repaired["wikidata_sire_when_infobox_sire_missing"]+=bool(s and not wiki_s)
        repaired["wikidata_dam_when_infobox_dam_missing"]+=bool(d and not wiki_d)
        wd_rows.append({"horse_id":qid_map[title],"sire_id":s or "","dam_id":d or ""})
    wd_graph=RegistryPedigree(wd_rows) if wd_rows else None
    qid_ids=sorted(r["horse_id"] for r in wd_rows)
    groups=defaultdict(set)
    positive_sire_pairs=positive_dam_pairs=0
    for r in wd_rows:
        if r["sire_id"]:groups[("sire",r["sire_id"])].add(r["horse_id"])
        if r["dam_id"]:groups[("dam",r["dam_id"])].add(r["horse_id"])
    for (typ,par),ids in groups.items():
        n=len(ids)
        if typ=="sire":positive_sire_pairs+=n*(n-1)//2
        else:positive_dam_pairs+=n*(n-1)//2
    # Meisho subset is explicitly targeted, not a random sample.
    meisho={t for t in chosen if t.startswith("メイショウ")}
    checked_meisho=[t for t in parents if t in meisho]
    return {
        "status":("SECONDARY_WIKIDATA_ACTUAL_PARENT_QIDS_PARTIAL_SAMPLE"
                  if fetched>0 else "HOLD_NO_RETRIEVED_WIKIDATA_PARENT_DATA"),
        "source":"Wikimedia ja.wikipedia pageprops and Wikidata wbgetentities",
        "source_license":"Wikidata CC0; Wikipedia article title source CC BY-SA",
        "selection":"ALL Meisho named articles up to sample limit, then deterministic sample of Wikipedia infoboxes lacking direct mother page links",
        "sampled_titles":len(chosen),
        "meisho_titles_in_sample":len(meisho),
        "unique_article_pageprops_qids":len(qid_map),
        "parsed_Wikidata_horse_entities":fetched,
        "meisho_entities_with_Wikidata_parent_record":len(checked_meisho),
        "requests_sent":attempts,
        "request_budget":max_requests,
        "failures":dict(failures),
        "Wikidata_documented_sire_claims":sum(bool(s) for s,d in parents.values()),
        "Wikidata_documented_dam_claims":sum(bool(d) for s,d in parents.values()),
        "additional_parent_claims_where_Wikipedia_infobox_missing":dict(repaired),
        "direct_source_conflicts":dict(conflicts),
        "within_same_sample_shared_sire_pairs":positive_sire_pairs,
        "within_same_sample_shared_dam_pairs":positive_dam_pairs,
        "no_Wikidata_and_article_title_P22_P25_edges_joined_to_all_5878":True,
        "source_conflicts_do_not_auto_overwrite_official_or_article_parents":True,
        "no_JRA_NAR_complete_census_or_biological_heritability_estimated":True,
        "no_individual_ids_or_rows_in_output":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--infobox-json",type=Path,required=True)
    p.add_argument("--summary",type=Path,required=True)
    p.add_argument("--max-titles",type=int,default=200)
    p.add_argument("--max-requests",type=int,default=20)
    opts=p.parse_args()
    result=run(json.loads(opts.infobox_json.read_text(encoding="utf-8")),
               limit=opts.max_titles,max_requests=opts.max_requests)
    opts.summary.parent.mkdir(parents=True,exist_ok=True)
    opts.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
