#!/usr/bin/env python3
"""Source-conditional, matched name-group kinship screen on real Wikipedia horses.

Meisho-name 38 horses are compared against fixed-size random sets matched
EXACTLY on article birth decade, country field Japan flag, and availability
of unambiguous sire and dam page links. No race outcomes, official JRA/NAR
registry membership, heritability or genetic selection is inferred.

The null is a DESCRIPTIVE coverage-matched selection diagnostic: Wiki article
selection, shared environments, owner allocations and historic birth-cohort
differences remain. Never label the fraction of sham samples >= observed A
a calibrated biological, association or causal p-value.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import random
from statistics import mean
import time

from ecology_japan_wikipedia_large import (
    PREFIX, class_japan, parse_year, prepare_infoboxes,
)
from ecology_japan_wikipedia_parent_ablation import strip_sex


def descriptor(title: str, box: dict, graph) -> tuple:
    when=parse_year(box.get("生",""))
    dec=str((when//10)*10) if when is not None else "missing"
    sire,dam=graph.recorded[PREFIX+title]
    return (dec,int(class_japan(box.get("国",""))),int(bool(sire)),int(bool(dam)))


def kin_stats(graph, ids: list[str]) -> dict:
    sum_a=0.0
    positive=near=strong=0
    n=len(ids)
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            value=graph.a(a,b)
            sum_a+=value
            positive+=(value>1e-12)
            near+=(value>=0.125-1e-12)
            strong+=(value>=0.25-1e-12)
    total=n*(n-1)//2
    return {
        "mean_partial_A":sum_a/total if total else None,
        "positive_known_path_pairs":positive,
        "A_at_least_0_125_pairs":near,
        "A_at_least_0_25_pairs":strong,
        "pairs":total,
    }


def percentile(values: list[float], fraction: float) -> float:
    ordered=sorted(values)
    if not ordered:
        raise ValueError("HOLD_EMPTY_PERMUTATION_RESULTS")
    return ordered[min(len(ordered)-1,max(0,int(fraction*(len(ordered)-1))))]


def summarize_observed_vs_shams(observed:dict,shams:list[dict]) -> dict:
    result={"observed":observed,"n_matched_random_sets":len(shams)}
    for metric in ("mean_partial_A","positive_known_path_pairs",
                   "A_at_least_0_125_pairs","A_at_least_0_25_pairs"):
        obs=observed[metric]
        distribution=[s[metric] for s in shams]
        result[metric+"_matched_reference"]={
            "observed":obs,
            "random_set_mean":mean(distribution),
            "random_set_5pct":percentile(distribution,0.05),
            "random_set_95pct":percentile(distribution,0.95),
            "fraction_random_sets_at_least_observed":
                sum(x>=obs for x in distribution)/len(distribution),
            "descriptive_diagnostic_NOT_a_genetic_p_value":True,
        }
    return result


def analyze(infobox_json:Path, *,
            n_random:int=499,
            seed:int=20261114,
            expected_sha:str|None=None,
            reference_sha:str|None=None) -> dict:
    if n_random<10 or n_random>4999:
        raise ValueError("HOLD_PERMUTATION_COUNT_OUT_OF_BOUNDS")
    t0=time.monotonic()
    raw=infobox_json.read_bytes()
    digest=sha256(raw).hexdigest()
    if expected_sha and digest!=expected_sha:
        return {
            "status":"HOLD_SOURCE_SHA_CHANGED_CANNOT_COMPARE_FIXED_BASELINE",
            "actual_source_sha256":digest,
            "expected_source_sha256":expected_sha,
            "matched_analysis_performed":False,
        }
    boxes=json.loads(raw)
    graph,meta,_=prepare_infoboxes(boxes)
    title_lookup={k.replace("_"," ").strip():v for k,v in boxes.items()}
    named=sorted(meta["meisho_titles"])
    other=sorted(set(title_lookup)-set(named))
    groups=defaultdict(list)
    for title in other:
        groups[descriptor(title,title_lookup[title],graph)].append(PREFIX+title)
    needed=Counter(descriptor(t,title_lookup[t],graph) for t in named)
    shortages=[{"source_stratum":str(key),"named_horses":count,
                "available_controls":len(groups.get(key,()))}
               for key,count in sorted(needed.items())
               if len(groups.get(key,()))<count]
    input_audit={
        "total_source_articles":len(meta["article_titles"]),
        "named_meisho_articles":len(named),
        "candidate_non_meisho_articles":len(other),
        "matched_strata_count":len(needed),
        "insufficient_strata":shortages,
        "matching":"EXACT [birth_decase, infobox_country_Japan, known_sire_page, known_dam_page]",
        "cohort_selected_by_name_NOT_ownership_or_registered_pedigree_family":True,
    }
    if len(named)<2:
        return {"status":"HOLD_TOO_FEW_MEISHO_NAME_ARTICLES",
                "source_sha256":digest,"audit":input_audit}
    if shortages:
        return {"status":"HOLD_INSUFFICIENT_EXACT_BIRTH_DECADE_AND_PARENTS_MATCHING_SUPPORT",
                "source_sha256":digest,"audit":input_audit,
                "biology_or_heritability_NOT_tested":True}
    full=graph
    sire=strip_sex(graph,"sire")
    ids=[PREFIX+t for t in named]
    observed={
        "both_available_parents":kin_stats(full,ids),
        "sire_only":kin_stats(sire,ids),
    }
    rng=random.Random(seed)
    sample_results={key:[] for key in observed}
    for _ in range(n_random):
        control=[]
        for key,n in sorted(needed.items()):
            control.extend(rng.sample(groups[key],n))
        control.sort()
        sample_results["both_available_parents"].append(kin_stats(full,control))
        sample_results["sire_only"].append(kin_stats(sire,control))
    comparisons={
        key:summarize_observed_vs_shams(observed[key],sample_results[key])
        for key in observed
    }
    for key in comparisons:
        if comparisons[key]["observed"]["pairs"]!=len(named)*(len(named)-1)//2:
            raise ValueError("HOLD_MEISHO_DENOMINATOR_CHANGED")
    return {
        "status":"SOURCE_CONDITIONAL_REAL_MEISHO_NAME_GROUP_MATCHED_PEDIGREE_DIAGNOSTIC",
        "source_sha256":digest,
        "expected_sha_matches":(digest==expected_sha if expected_sha else None),
        "historical_reference_source_sha":reference_sha,
        "matches_historical_reference_sha":(
            digest==reference_sha if reference_sha else None
        ),
        "source":"Japanese Wikipedia horse infoboxes CC BY-SA; selected article content",
        "credit":"Sheep Meadow Road Games / Horse Racing Manager",
        "credit_url":"https://store.steampowered.com/app/2740170/Horse_Racing_Manager/",
        "random_seed":seed,
        "random_control_groups":n_random,
        "selection_and_support":input_audit,
        "same_pair_count_all_models":True,
        "results":comparisons,
        "interpretation_boundaries":[
            "Do NOT call name prefix a family or infer owner identity from it.",
            "Matched random sets are not independent horse pedigrees or race outcomes.",
            "Exact birth decade and parent-link availability are matched but race, breeder, trainer and article selection are not.",
            "Many sire IDs are ancestors from outside the 5,878 source articles; missing mothers remain unknown founders.",
            "This is a DESCRIPTIVE Wikipedia coverage-conditioned name-group concentration test, NOT genetic causation, inherited pacing, significance or national prevalence.",
        ],
        "analysis_seconds":round(time.monotonic()-t0,3),
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--infobox-json",type=Path,required=True)
    p.add_argument("--summary",type=Path,required=True)
    p.add_argument("--n-random",type=int,default=499)
    p.add_argument("--seed",type=int,default=20261114)
    p.add_argument("--expected-sha")
    p.add_argument("--reference-sha")
    args=p.parse_args()
    result=analyze(args.infobox_json,n_random=args.n_random,seed=args.seed,
                   expected_sha=args.expected_sha,
                   reference_sha=args.reference_sha)
    args.summary.parent.mkdir(parents=True,exist_ok=True)
    args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
