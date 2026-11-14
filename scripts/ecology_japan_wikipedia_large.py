#!/usr/bin/env python3
"""Large *real* ja-Wikipedia racehorse article pedigree audit.

Input: licensed CC BY-SA Japanese Wikipedia {{競走馬}} infobox JSON produced by
Sheep Meadow Road Games' fetch_ja_wikipedia.py (external MIT-with-credit).
No JBIS/JRA/VAN bulk content, no guessed name/romanisation joins.
The "Japan born" subset is only infobox 国 explicitly indicating Japan; it is
NOT the full Japanese racing registry or the full population of Japan-born horses.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
import time

from ecology_japan_registry_pedigree import RegistryPedigree, counts

LINK = re.compile(r"\[\[\s*([^\[\]\|#]+)(?:#[^\]\|]+)?(?:\|[^\]]*)?\]\]")
YEAR = re.compile(r"(?<!\d)(1[6789]\d\d|20[012]\d)(?!\d)")
PREFIX = "JA-WIKI:"
JP = re.compile(r"日本|\bJPN\b|\bJapan\b",re.IGNORECASE)


def canonical_title(raw: str) -> str | None:
    """One explicit wiki page target; no text-only parent name inference."""
    if not isinstance(raw,str) or len(raw)>3000:
        return None
    links = LINK.findall(raw)
    if len(links)!=1:
        return None
    name=links[0].replace("_"," ").strip()
    if not name or len(name)>160 or ":" in name:
        return None
    return name


def parse_year(raw) -> int | None:
    if not isinstance(raw,str):
        return None
    y=YEAR.search(raw)
    return int(y.group(1)) if y else None


def class_japan(raw) -> bool:
    return isinstance(raw,str) and bool(JP.search(raw))


def prepare_infoboxes(raw: dict) -> tuple[RegistryPedigree,dict,dict]:
    if not isinstance(raw,dict) or not raw:
        raise ValueError("HOLD_NO_JAPANESE_WIKIPEDIA_INFOBOXES")
    rows={}
    titles={}
    for title,infobox in raw.items():
        if not isinstance(title,str) or not isinstance(infobox,dict):
            raise ValueError("HOLD_BAD_INFOBOX_ROW")
        title=title.replace("_"," ").strip()
        if not title or ":" in title or title in rows:
            raise ValueError("HOLD_BAD_OR_DUPLICATED_ARTICLE_TITLE")
        rows[title]=infobox
    removed=Counter()
    has_sire=Counter()
    out={}
    year={t:parse_year(v.get("生","")) for t,v in rows.items()}
    for title,r in sorted(rows.items()):
        parent_names=[]
        for field in ("父","母"):
            raw_field=r.get(field,"")
            item=canonical_title(raw_field)
            if raw_field and not item:
                removed[field+"_no_unambiguous_link"]+=1
            if item == title:
                item=None
                removed[field+"_self_parent"]+=1
            parent_names.append(item)
        sire,dam=parent_names
        if sire and dam and sire==dam:
            sire=dam=None
            removed["same_sire_and_dam_page"]+=1
        for field,parent in (("父",sire),("母",dam)):
            if parent and parent in rows:
                parent_year=year[parent]
                child_year=year[title]
                if parent_year and child_year and not 3<=child_year-parent_year<=45:
                    removed[field+"_implausible_parent_age"]+=1
                    if field=="父":
                        sire=None
                    else:
                        dam=None
        if sire:
            has_sire["sire_link"]+=1
        if dam:
            has_sire["dam_link"]+=1
        out[title]={
            "horse_id":PREFIX+title,"horse_name":title,
            "sire_id":PREFIX+sire if sire else "",
            "dam_id":PREFIX+dam if dam else ""
        }
    ped=RegistryPedigree(list(out.values()),cache_size=300000)
    meta={
        "article_titles":list(sorted(rows)),
        "japan_explicit_titles":[t for t,r in rows.items() if class_japan(r.get("国",""))],
        "meisho_titles":[t for t in rows if t.startswith("メイショウ")],
        "sample_years_count":sum(year[t] is not None for t in rows),
        "known_source_links":dict(has_sire),
        "link_rejections":dict(removed),
        "sire_links_to_article_with_infobox":sum(bool(r["sire_id"]) and
              r["sire_id"][len(PREFIX):] in rows for r in out.values()),
        "dam_links_to_article_with_infobox":sum(bool(r["dam_id"]) and
              r["dam_id"][len(PREFIX):] in rows for r in out.values()),
    }
    return ped,meta,out


def all_pairs(pedigree: RegistryPedigree, targets: list[str],
              meisho: set[str], *, max_pairs=20000000) -> dict:
    n=len(targets)
    n_pairs=n*(n-1)//2
    if n_pairs>max_pairs:
        return {"status":"HOLD_ALL_PAIR_BUDGET_EXCEEDED",
                "n_horses":n,"potential_pairs":n_pairs,"max_pairs":max_pairs}
    bins=Counter()
    positive=0
    both_meisho=0
    one_meisho=0
    positive_same_sire=0
    nonzero_individuals=set()
    for i,left in enumerate(targets):
        sire_l=pedigree.recorded[left][0]
        meisho_l=left in meisho
        for right in targets[i+1:]:
            value=pedigree.a(left,right)
            if value<=1e-12:
                continue
            positive+=1
            bins[f"{value:.6g}"]+=1
            nonzero_individuals.add(left)
            nonzero_individuals.add(right)
            n_m=meisho_l+int(right in meisho)
            if n_m==2:
                both_meisho+=1
            elif n_m==1:
                one_meisho+=1
            if sire_l and sire_l==pedigree.recorded[right][0]:
                positive_same_sire+=1
    return {
        "status":"EXACT_ALL_WITHIN_EXPLICIT_ARTICLE_COHORT_PARTIAL_PEDIGREE_A",
        "n_horses":n,"pairs_scored":n_pairs,
        "documented_nonzero_path_pairs":positive,
        "pairs_without_known_path_not_unrelated":n_pairs-positive,
        "horses_with_any_documented_path":len(nonzero_individuals),
        "documented_A_value_histogram":dict(sorted(
            bins.items(),key=lambda z:float(z[0]),reverse=True)),
        "positive_pairs_same_known_sire":positive_same_sire,
        "positive_pairs_meisho_to_meisho":both_meisho,
        "positive_pairs_meisho_to_other":one_meisho,
        "full_all_pairs_run_without_exporting_raw_wikipedia_articles":True,
    }


def analyze(input_file:Path, *, max_pairs=20000000) -> dict:
    raw=input_file.read_bytes()
    boxes=json.loads(raw)
    clock=time.monotonic()
    ped,meta,_=prepare_infoboxes(boxes)
    articles=[PREFIX+x for x in meta["article_titles"]]
    japan=[PREFIX+x for x in sorted(meta["japan_explicit_titles"])]
    meisho={PREFIX+x for x in meta["meisho_titles"]}
    global_stats,_=counts(ped,articles)
    japan_stats,_=counts(ped,japan)
    world_pairs=all_pairs(ped,articles,meisho,max_pairs=max_pairs)
    japan_pairs=all_pairs(ped,japan,meisho,max_pairs=max_pairs)
    return {
        "status":"REAL_JA_WIKIPEDIA_INFOBOXES_ANALYZED_NOT_ALL_JAPANESE_RACEHORSES",
        "source":"Japanese Wikipedia transclusions of Template:競走馬",
        "source_url":"https://ja.wikipedia.org/wiki/Template:競走馬",
        "upstream_data_builder":"https://github.com/Sheep-Meadow-Road-Games/open-horse-data",
        "license":"Japanese Wikipedia CC BY-SA; upstream software modified MIT with attribution",
        "attribution":"Sheep Meadow Road Games / Horse Racing Manager",
        "upstream_credit_url":"https://store.steampowered.com/app/2740170/Horse_Racing_Manager/",
        "input_sha256":hashlib.sha256(raw).hexdigest(),
        "grain":"distinct Japanese-language Wikipedia infobox article titles",
        "not_jra_or_nar_population":True,
        "japan_born_only_if_infobox_country_explicit":True,
        "parent_keys_are_unique_direct_japanese_wikipedia_page_links_not_names":True,
        "unknown_parent_article_is_assumed_unrelated_FOUNDER_for_partial_A_only":True,
        "data_quality": {
            "total_wikipedia_article_infoboxes":len(articles),
            "explicit_japan_country":len(japan),
            "meisho_name_in_title":len(meisho),
            "unique_documented_sire_article_links":meta["known_source_links"].get("sire_link",0),
            "unique_documented_dam_article_links":meta["known_source_links"].get("dam_link",0),
            "parent_links_to_same_infobox_pool":{
                "sire":meta["sire_links_to_article_with_infobox"],
                "dam":meta["dam_links_to_article_with_infobox"],
            },
            "recorded_birth_year_articles":meta["sample_years_count"],
            "rejected_parent_links":meta["link_rejections"],
        },
        "all_japanese_language_articles":{
            "cohort_counts":global_stats,
            "all_pairs":world_pairs,
        },
        "explicit_japan_country_articles":{
            "cohort_counts":japan_stats,
            "all_pairs":japan_pairs,
        },
        "analysis_runtime_seconds":round(time.monotonic()-clock,3),
        "limits":[
            "Article selection is highly non-random, prominent/successful horses more likely documented.",
            "Japanese-language Wikipedia covers both Japanese and foreign horses.",
            "Japanese-born subset requires explicit infobox country Japan; non-Japan-born horses racing in Japan are excluded.",
            "Pedigree edges are from one explicit wiki parent link only; without resolved ancestor pages relatedness is a lower-depth approximation.",
            "Zero partial A means no known path in this source, NOT genetic unrelatedness.",
            "O(N^2) pair sweep is limited to max_pairs; large authorized registry uses sparse queries and analytic sibling counts instead.",
            "No full JRA/NAR registry, historical starters, verified breeding data, physiological trait, heritability or betting prediction.",
        ],
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--infobox-json",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--max-pairs",type=int,default=20000000)
    opts=ap.parse_args()
    report=analyze(opts.infobox_json,max_pairs=opts.max_pairs)
    opts.summary.parent.mkdir(parents=True,exist_ok=True)
    opts.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
