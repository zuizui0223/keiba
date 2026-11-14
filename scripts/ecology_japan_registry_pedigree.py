#!/usr/bin/env python3
"""Exact partial-pedigree numerator relatedness, scalable to a full registry export.

Authorized source CSV: horse_id,sire_id,dam_id[,horse_name]; no name-matching.
Optional target-cohort IDs separate Japanese registered racehorses from
non-Japanese/sire/dam ancestors. O(N) per-horse summaries; sparse pair
queries only. The code never claims an unknown genealogy equals true zero.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import csv
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path


def read_rows(path: Path) -> list[dict[str,str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        if not rd.fieldnames or not {"horse_id","sire_id","dam_id"}.issubset(rd.fieldnames):
            raise ValueError("HOLD_REQUIRED_HORSE_PARENT_ID_COLUMNS")
        out = [{k:(v or "").strip() for k,v in row.items()} for row in rd]
    if not out:
        raise ValueError("HOLD_EMPTY_PEDIGREE_INPUT")
    return out


class RegistryPedigree:
    """Tabular A recurrence for known pedigree: unknown parents are founders."""

    def __init__(self, rows: list[dict[str,str]], cache_size: int = 200000):
        self.recorded: dict[str,tuple[str|None,str|None]] = {}
        self.names: dict[str,str] = {}
        for row in rows:
            horse = row["horse_id"]
            sire, dam = row["sire_id"] or None, row["dam_id"] or None
            if not horse or horse in self.recorded:
                raise ValueError("HOLD_EMPTY_OR_DUPLICATE_HORSE_ID")
            if horse == sire or horse == dam or (sire and sire == dam):
                raise ValueError("HOLD_BAD_PARENT_REFERENCE")
            self.recorded[horse] = (sire, dam)
            self.names[horse] = row.get("horse_name","")
        self.parents = self.recorded.copy()
        self.parent_ref_missing = set()
        for sire, dam in self.recorded.values():
            for parent in (sire, dam):
                if parent and parent not in self.parents:
                    self.parents[parent] = (None,None)
                    self.parent_ref_missing.add(parent)
        descendants = defaultdict(list)
        indegree: dict[str,int] = {}
        for horse, (sire, dam) in self.parents.items():
            anc = {p for p in (sire, dam) if p}
            indegree[horse] = len(anc)
            for parent in anc:
                descendants[parent].append(horse)
        queue = deque(sorted(x for x, d in indegree.items() if d == 0))
        rank = {}
        while queue:
            horse = queue.popleft()
            rank[horse] = len(rank)
            for child in descendants.get(horse,()):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if len(rank) != len(self.parents):
            raise ValueError("HOLD_PEDIGREE_CYCLE")
        self.rank = rank
        if cache_size < 0:
            raise ValueError("HOLD_NEGATIVE_CACHE")
        self._a = lru_cache(maxsize=cache_size)(self._rel)

    def _rel(self, left: str|None, right: str|None) -> float:
        if not left or not right or left not in self.rank or right not in self.rank:
            return 0.0
        if left == right:
            sire, dam = self.parents[left]
            return 1.0 + 0.5 * self._a(sire,dam)
        if self.rank[left] < self.rank[right]:
            left,right = right,left
        sire,dam = self.parents[left]
        return 0.5 * (self._a(sire,right) + self._a(dam,right))

    def a(self, horse1: str, horse2: str) -> float:
        if horse1 not in self.recorded or horse2 not in self.recorded:
            raise ValueError("HOLD_QUERY_ID_NOT_IN_REGISTERED_INPUT")
        val = self._a(horse1,horse2)
        if not math.isfinite(val) or val < 0:
            raise ValueError("HOLD_NONFINITE_PEDIGREE_NUMERATOR")
        return val

    def f(self, horse: str) -> float:
        """Partial-pedigree F. F=0 DOES NOT prove not inbred."""
        return self.a(horse,horse)-1.0

    def quality(self, horse: str) -> dict:
        if horse not in self.recorded:
            raise ValueError("HOLD_UNKNOWN_HORSE")
        sire, dam = self.recorded[horse]
        return {
            "known_sire": bool(sire),
            "known_dam": bool(dam),
            "sire_explicitly_recorded": sire in self.recorded if sire else False,
            "dam_explicitly_recorded": dam in self.recorded if dam else False,
        }


def target_ids(path: Path|None, ped: RegistryPedigree) -> list[str]:
    if path is None:
        return sorted(ped.recorded)
    with path.open(encoding="utf-8-sig", newline="") as fd:
        reader = csv.DictReader(fd)
        if not reader.fieldnames or "horse_id" not in reader.fieldnames:
            raise ValueError("HOLD_MISSING_TARGET_ID_COLUMN")
        found = [r["horse_id"].strip() for r in reader]
    if not found or any(not x or x not in ped.recorded for x in found):
        raise ValueError("HOLD_TARGET_IDS_UNMATCHED_IN_PEDIGREE")
    if len(found) != len(set(found)):
        raise ValueError("HOLD_DUPLICATE_TARGET_IDS")
    return sorted(found)


def _choose2(n: int) -> int:
    return n*(n-1)//2


def counts(ped: RegistryPedigree, target: list[str]) -> tuple[dict, dict]:
    # All family counts refer to the TARGET cohort only.
    sire_groups = Counter()
    dam_groups = Counter()
    both_groups = Counter()
    sire_dams = defaultdict(Counter)
    dam_sires = defaultdict(Counter)
    children = Counter()
    for horse in target:
        sire,dam = ped.recorded[horse]
        if sire:
            sire_groups[sire]+=1
            if dam:
                sire_dams[sire][dam]+=1
            children[sire]+=1
        if dam:
            dam_groups[dam]+=1
            if sire:
                dam_sires[dam][sire]+=1
            children[dam]+=1
        if sire and dam:
            both_groups[(sire,dam)]+=1
    maternal_conf = sum(_choose2(sum(v.values()))-
                        sum(_choose2(x) for x in v.values())
                        for v in dam_sires.values())
    paternal_conf = sum(_choose2(sum(v.values()))-
                        sum(_choose2(x) for x in v.values())
                        for v in sire_dams.values())
    stats = {
        "target_horses":len(target),
        "pedigree_record_rows":len(ped.recorded),
        "linked_parent_placeholders_not_in_source":len(ped.parent_ref_missing),
        "target_known_sire":sum(bool(ped.recorded[x][0]) for x in target),
        "target_known_dam":sum(bool(ped.recorded[x][1]) for x in target),
        "target_both_parents":sum(all(ped.recorded[x]) for x in target),
        "distinct_sire_ids_with_target_offspring":len(sire_groups),
        "distinct_dam_ids_with_target_offspring":len(dam_groups),
        "shared_sire_target_pairs_including_unknown_other_parent":sum(
            _choose2(n) for n in sire_groups.values()),
        "shared_dam_target_pairs_including_unknown_other_parent":sum(
            _choose2(n) for n in dam_groups.values()),
        "full_sibling_pairs_both_verified_parents":sum(
            _choose2(n) for n in both_groups.values()),
        "confirmed_paternal_half_pairs_both_dams_known_distinct":paternal_conf,
        "confirmed_maternal_half_pairs_both_sires_known_distinct":maternal_conf,
        "largest_one_sire_target_cohort":max(sire_groups.values(),default=0),
        "largest_one_dam_target_cohort":max(dam_groups.values(),default=0),
        "the_rest_are_not_proved_unrelated":True,
        "all_pair_dense_matrix_NOT_computed":True,
    }
    aux = {
        "sire_groups":sire_groups, "dam_groups":dam_groups,
        "both_groups":both_groups, "sire_dams":sire_dams,
        "dam_sires":dam_sires, "children":children,
    }
    return stats,aux


def per_horse(ped: RegistryPedigree, target: list[str], aux, outfile: Path) -> dict:
    outfile.parent.mkdir(parents=True, exist_ok=True)
    fields=["horse_id","horse_name","known_sire","known_dam",
            "partial_F","shared_sire_other_targets","shared_dam_other_targets",
            "full_siblings_documented","paternal_half_confirmed",
            "maternal_half_confirmed","documented_offspring_in_target"]
    positives = 0
    total = 0.0
    max_f = 0.0
    with outfile.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        for horse in target:
            sire,dam = ped.recorded[horse]
            f_i=ped.f(horse)
            total += f_i
            positives += f_i>1e-12
            max_f=max(max_f,f_i)
            full=aux["both_groups"][(sire,dam)]-1 if sire and dam else 0
            phalf=(sum(n for d,n in aux["sire_dams"][sire].items()
                       if d!=dam) if sire and dam else 0)
            mhalf=(sum(n for s,n in aux["dam_sires"][dam].items()
                       if s!=sire) if sire and dam else 0)
            writer.writerow({
                "horse_id":horse,"horse_name":ped.names[horse],
                "known_sire":int(bool(sire)),"known_dam":int(bool(dam)),
                "partial_F":f"{f_i:.10g}",
                "shared_sire_other_targets":aux["sire_groups"][sire]-1 if sire else 0,
                "shared_dam_other_targets":aux["dam_groups"][dam]-1 if dam else 0,
                "full_siblings_documented":full,
                "paternal_half_confirmed":phalf,
                "maternal_half_confirmed":mhalf,
                "documented_offspring_in_target":aux["children"][horse],
            })
    return {"partial_F_positive_horses":positives,
            "partial_F_mean":total/max(1,len(target)),
            "partial_F_max":max_f,
            "partial_F_zero_is_NOT_proof_no_inbreeding":True}


def pair_queries(ped: RegistryPedigree, infile: Path, outfile: Path) -> dict:
    with infile.open(encoding="utf-8-sig",newline="") as fd:
        reader=csv.DictReader(fd)
        if not reader.fieldnames or not {"horse_id_1","horse_id_2"}.issubset(reader.fieldnames):
            raise ValueError("HOLD_REQUIRED_PAIR_QUERY_COLUMNS")
        pairs=[(r["horse_id_1"].strip(),r["horse_id_2"].strip()) for r in reader]
    if not pairs:
        raise ValueError("HOLD_EMPTY_PAIR_QUERY")
    outfile.parent.mkdir(parents=True, exist_ok=True)
    positives=0
    with outfile.open("w",encoding="utf-8",newline="") as fd:
        writer=csv.writer(fd)
        writer.writerow(["horse_id_1","horse_id_2","partial_numerator_A",
                         "pedigree_coefficient_r","status"])
        for a,b in pairs:
            val=ped.a(a,b)
            positives+=val>0
            # Relationship coefficient r_ij = Aij / sqrt(Aii Ajj).
            # The numerator A itself is the additive expected kin coefficient.
            normalized=val / math.sqrt(ped.a(a,a)*ped.a(b,b))
            writer.writerow([a,b,f"{val:.10g}",f"{normalized:.10g}",
                  "PATH_IN_DOCUMENTED_PEDIGREE" if val>0 else
                  "NO_PATH_IN_TRUNCATED_PEDIGREE_NOT_UNRELATED"])
    return {"pair_queries":len(pairs),"documented_positive_pairs":positives,
            "zero_paths_not_proven_genetically_unrelated":True}


def analyze(ped_file: Path, target_file: Path|None=None,
            per_horse_file: Path|None=None, pair_file: Path|None=None,
            pair_output: Path|None=None, cache_size: int=200000) -> dict:
    if (pair_file is None) != (pair_output is None):
        raise ValueError("HOLD_PAIR_INPUT_OUTPUT_MUST_BOTH_BE_SET")
    ped=RegistryPedigree(read_rows(ped_file),cache_size=cache_size)
    targets=target_ids(target_file,ped)
    stats,aux=counts(ped,targets)
    if per_horse_file:
        stats.update(per_horse(ped,targets,aux,per_horse_file))
    if pair_file:
        stats.update(pair_queries(ped,pair_file,pair_output))
    return {
        "status":"COMPUTED_FOR_SUPPLIED_REGISTERED_PEDIGREE_NOT_ALL_JAPAN_UNLESS_COMPLETE_SOURCE",
        "input_sha256":hashlib.sha256(ped_file.read_bytes()).hexdigest(),
        "target_cohort_explicit":target_file is not None,
        "target_source_completeness_verified_by_code":False,
        "statistics":stats,
        "family_relationship_definition":"Aij expected additive pedigree numerator; r_ij=Aij/sqrt(Aii*Ajj)",
        "unknown_parent_handling":"blank = unrelated computational founder only; absent name/ID is not proven unrelated",
        "source_identity_policy":"identifiers only, never infer same individual by name",
        "no_automatic_third_party_bulk_scraping":True,
        "row_level_outputs_explicitly_optional_private":True,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pedigree",type=Path,required=True)
    parser.add_argument("--target-ids",type=Path)
    parser.add_argument("--summary",type=Path,required=True)
    parser.add_argument("--per-horse",type=Path)
    parser.add_argument("--pairs",type=Path)
    parser.add_argument("--pair-output",type=Path)
    parser.add_argument("--cache-size",type=int,default=200000)
    args=parser.parse_args()
    result=analyze(args.pedigree,args.target_ids,args.per_horse,args.pairs,
                   args.pair_output,args.cache_size)
    args.summary.parent.mkdir(parents=True,exist_ok=True)
    args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                            encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
