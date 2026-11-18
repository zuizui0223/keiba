#!/usr/bin/env python3
"""Paired father-only / mother-only / available-parent pedigree sensitivity.

Uses the SAME licensed Japanese-Wikipedia article infobox snapshot for every
contrast. Describes information removed from a TRUNCATED source pedigree,
NOT biological paternal-vs-maternal genetic inheritance or heritability.
No animal-level measurements are republished.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import time

from ecology_japan_registry_pedigree import RegistryPedigree
from ecology_japan_wikipedia_large import PREFIX, parse_year, prepare_infoboxes


def strip_sex(graph: RegistryPedigree, keep: str) -> RegistryPedigree:
    if keep not in ("sire", "dam"):
        raise ValueError("HOLD_INVALID_PARENT_RESTRICTION")
    records=[]
    for h,(s,d) in graph.recorded.items():
        records.append({
            "horse_id":h,
            "horse_name":graph.names.get(h,""),
            "sire_id":s or "" if keep=="sire" else "",
            "dam_id":d or "" if keep=="dam" else "",
        })
    return RegistryPedigree(records,cache_size=250000)


def compare(full: RegistryPedigree, sire_only: RegistryPedigree,
            dam_only: RegistryPedigree, horses: list[str],
            *, max_pairs: int=20_000_000) -> dict:
    targets=sorted(horses)
    n=len(targets)
    pairs=n*(n-1)//2
    if pairs>max_pairs:
        return {"status":"HOLD_PAIR_BUDGET","n":n,"pairs_requested":pairs}
    near_thresholds=(0.5,0.25,0.125,0.0625)
    counter=Counter()
    total_full=total_sire=total_dam=total_gain=0.0
    max_negative=0.0
    for i,a in enumerate(targets):
        for b in targets[i+1:]:
            v=full.a(a,b)
            vs=sire_only.a(a,b)
            vd=dam_only.a(a,b)
            diff=v-vs
            if diff < -1e-9 or v < vd-1e-9:
                raise ValueError("HOLD_NONMONOTONIC_PEDIGREE_ABLATION")
            max_negative=min(max_negative,diff)
            total_full+=v
            total_sire+=vs
            total_dam+=vd
            total_gain+=max(0.0,diff)
            counter["full_documented_path"]+=v>1e-12
            counter["sire_documented_path"]+=vs>1e-12
            counter["dam_documented_path"]+=vd>1e-12
            counter["path_lost_if_mother_removed"]+=v>1e-12 and vs<=1e-12
            counter["A_increases_from_mother_links"]+=diff>1e-9
            counter["either_one_parent_graph_path"]+=vs>1e-12 or vd>1e-12
            for t in near_thresholds:
                tag=f"{t:.5g}"
                counter["full_A_at_least_"+tag]+=v>=t-1e-12
                counter["sire_A_at_least_"+tag]+=vs>=t-1e-12
                counter["dam_A_at_least_"+tag]+=vd>=t-1e-12
                counter["crosses_"+tag+"_when_mother_added"]+=v>=t-1e-12 and vs<t-1e-12
    return {
        "status":"SOURCE_CONDITIONAL_MATCHED_PAIRS_PARENT_LINK_ABLATION",
        "horses":n,
        "same_target_pairs":pairs,
        "counts":dict(counter),
        "sums_of_A_across_identical_pairs":{
            "both_available_parent_links":total_full,
            "sire_links_only":total_sire,
            "dam_links_only":total_dam,
            "increment_from_available_mother_links":total_gain,
        },
        "no_underlying_genetic_paternal_maternal_variance_estimated":True,
        "per_pair_genealogical_monotonicity_pass":max_negative>=-1e-9,
    }


def birth_cohort_quality(boxes: dict, full: RegistryPedigree) -> dict:
    groups=defaultdict(Counter)
    for title,box in boxes.items():
        year=parse_year(box.get("生",""))
        if year is None:
            group="unknown"
        else:
            group=f"{(year//10)*10}s"
        horse=PREFIX+title.replace("_"," ").strip()
        sire,dam=full.recorded[horse]
        g=groups[group]
        g["horses"]+=1
        g["verified_sire_page_link"]+=bool(sire)
        g["verified_dam_page_link"]+=bool(dam)
        g["both_parents"]+=bool(sire and dam)
        g["meisho_name"]+=title.startswith("メイショウ")
    return {
        k:dict(v) for k,v in sorted(groups.items())
    }


def analyze(input: Path,*,max_pairs:int=20_000_000,
            expected_source_sha:str|None=None) -> dict:
    start=time.monotonic()
    raw=input.read_bytes()
    digest=sha256(raw).hexdigest()
    boxes=json.loads(raw)
    full,meta,_=prepare_infoboxes(boxes)
    sire=strip_sex(full,"sire")
    dam=strip_sex(full,"dam")
    jp_titles=set(meta["japan_explicit_titles"])
    all_horses=[PREFIX+x for x in meta["article_titles"]]
    japan_horses=[PREFIX+x for x in sorted(jp_titles)]
    meisho_horses=[PREFIX+x for x in sorted(meta["meisho_titles"])]
    cohort={
        "all_language_articles":compare(full,sire,dam,all_horses,max_pairs=max_pairs),
        "japan_origin_infobox_articles":compare(full,sire,dam,japan_horses,max_pairs=max_pairs),
        "meisho_named_articles":compare(full,sire,dam,meisho_horses,max_pairs=max_pairs),
    }
    for key,r in cohort.items():
        if r["status"]!="SOURCE_CONDITIONAL_MATCHED_PAIRS_PARENT_LINK_ABLATION":
            raise ValueError("HOLD_INCOMPLETE_ABLATION_"+key)
        if r["counts"]["full_documented_path"] < r["counts"]["sire_documented_path"]:
            raise ValueError("HOLD_SIRE_ONLY_MORE_THAN_FULL")
        if r["counts"]["full_documented_path"] < r["counts"]["dam_documented_path"]:
            raise ValueError("HOLD_DAM_ONLY_MORE_THAN_FULL")
    return {
        "status":"REAL_JAPANESE_WIKIPEDIA_PARENTS_INFORMATION_SENSITIVITY_NOT_NATIONAL",
        "source":"Japanese Wikipedia Template:競走馬 CC BY-SA",
        "source_sha256":digest,
        "matches_previous_source_sha":(
            digest==expected_source_sha if expected_source_sha else None
        ),
        "upstream_fetcher_credit":"Sheep Meadow Road Games / Horse Racing Manager",
        "upstream_credit_url":"https://store.steampowered.com/app/2740170/Horse_Racing_Manager/",
        "source_horses":len(all_horses),
        "source_sire_links":meta["known_source_links"].get("sire_link",0),
        "source_dam_links":meta["known_source_links"].get("dam_link",0),
        "cohorts":cohort,
        "parent_data_completeness_by_foal_decade":birth_cohort_quality(boxes,full),
        "limits":[
            "Both sex-specific sensitivity graphs remove observed parent LINKS, not true biological parental inheritance.",
            "The three comparisons are made on identical within-cohort pairs; all are subject to source missingness.",
            "Wikipedia article existence selects notable horses and does not define all JRA/NAR runners.",
            "Unobserved maternal paths are not true unrelatedness; parent link ablation cannot correct missing mothers.",
            "No horse-specific output, genome data, random mating assumptions, heritability, or predictive race gains.",
        ],
        "calculation_seconds":round(time.monotonic()-start,3),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--infobox-json",type=Path,required=True)
    p.add_argument("--summary",type=Path,required=True)
    p.add_argument("--expected-source-sha")
    p.add_argument("--max-pairs",type=int,default=20_000_000)
    args=p.parse_args()
    result=analyze(args.infobox_json,
                   max_pairs=args.max_pairs,
                   expected_source_sha=args.expected_source_sha)
    args.summary.parent.mkdir(parents=True,exist_ok=True)
    args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
