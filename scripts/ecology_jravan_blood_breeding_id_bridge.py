#!/usr/bin/env python3
"""Source-safe TARGET/JRA-VAN pedigree CSV -> typed unique-ID pedigree bridge.

Original '血統登録番号' and '繁殖登録番号' are DIFFERENT namespaces.
Use only an explicitly supplied export, never scrape JRA/JBIS. Output remains
local and private; this is a static partial pedigree, NOT a race outcome panel.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

FIELDS=(
    "馬名","血統登録番号","繁殖登録番号","父繁殖登録番号","母繁殖登録番号"
)
REGEX=re.compile(r"^[A-Za-z0-9-]{2,30}$")


def encoding_of(path:Path)->str:
    for encoding in ("utf-8-sig","cp932"):
        try:
            with path.open(encoding=encoding,newline="") as fd:
                r=csv.reader(fd)
                _=next(r)
            return encoding
        except UnicodeDecodeError:
            pass
    raise ValueError("HOLD_UNREADABLE_JAPANESE_CSV_ENCODING")


def parse_id(value:str, *, blank_ok:bool=True)->str|None:
    value=(value or "").strip().replace(" ","")
    if not value or set(value)=={"0"}:
        if blank_ok:
            return None
        raise ValueError("HOLD_REQUIRED_STABLE_ID_MISSING")
    if not REGEX.fullmatch(value):
        raise ValueError("HOLD_INVALID_STABLE_REGISTRATION_ID")
    return value


def rows(path:Path,encoding:str):
    with path.open(encoding=encoding,newline="") as fd:
        reader=csv.DictReader(fd)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError("HOLD_MISSING_TARGET_CSV_FIELDS")
        for r in reader:
            yield r


def hash_file(path:Path)->str:
    obj=hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda:fd.read(1024*1024),b""):
            obj.update(chunk)
    return obj.hexdigest()


def transform(input_csv:Path,pedigree_output:Path,
              *, target_ids:Path|None=None)->dict:
    enc=encoding_of(input_csv)
    # Pass 1: independently identify every uniquely labeled breeding-registered
    # individual. Never resolve a parent by name or presume breeding ID is
    # equal to the child's blood registration ID.
    breed_to_blood={}
    blood_ids=set()
    n_source=0
    missing_blood=0
    aliases=Counter()
    for row in rows(input_csv,enc):
        n_source+=1
        blood=parse_id(row["血統登録番号"])
        breed=parse_id(row["繁殖登録番号"])
        if blood is None:
            missing_blood+=1
            continue
        blood_ids.add(blood)
        if breed:
            seen=breed_to_blood.get(breed)
            if seen is not None and seen!=blood:
                raise ValueError("HOLD_BREEDING_ID_LINKS_MULTIPLE_BLOOD_IDS")
            breed_to_blood[breed]=blood
        if row["馬名"].strip():
            aliases[blood]+=1
    if not blood_ids:
        raise ValueError("HOLD_ZERO_COMPLETE_HORSE_BLOOD_IDS")
    targets=None
    if target_ids:
        e=encoding_of(target_ids)
        with target_ids.open(encoding=e,newline="") as fd:
            rd=csv.DictReader(fd)
            if not rd.fieldnames or "血統登録番号" not in rd.fieldnames:
                raise ValueError("HOLD_TARGET_NOT_REGISTRY_BLOOD_IDS")
            target_list=[parse_id(r["血統登録番号"],blank_ok=False) for r in rd]
        targets=set(target_list)
        if len(target_list)!=len(targets):
            raise ValueError("HOLD_DUPLICATE_TARGET_HORSE_IDS")
        if not targets or not targets.issubset(blood_ids):
            raise ValueError("HOLD_TARGET_HAS_UNMATCHED_PEDIGREE_ID")
    else:
        # Without an official actual-horse registry list these are ALL
        # supplied pedigree-records; not asserted to be actual JRA/NAR starters.
        targets=blood_ids
    def parent_namespace(breeding_code:str|None)->str:
        if not breeding_code:
            return ""
        if breeding_code in breed_to_blood:
            return "H:"+breed_to_blood[breeding_code]
        return "B:"+breeding_code

    output={}
    parents_missing=Counter()
    parents_linked=Counter()
    n_name_mismatch=Counter()
    for row in rows(input_csv,enc):
        blood=parse_id(row["血統登録番号"])
        if blood is None:
            continue
        sire=parse_id(row["父繁殖登録番号"])
        dam=parse_id(row["母繁殖登録番号"])
        ps,pd=parent_namespace(sire),parent_namespace(dam)
        current=("H:"+blood,ps,pd)
        if current[0] in (ps,pd) or (ps and ps==pd):
            raise ValueError("HOLD_CONFLICTING_SELF_OR_SHARED_PARENT_REGISTRY_ID")
        if blood in output and output[blood]["parents"]!=(ps,pd):
            raise ValueError("HOLD_INCONSISTENT_DUPLICATE_REGISTRY_ROW")
        output[blood]={"parents":(ps,pd),"name":row.get("馬名","").strip()}
        for role,p,c in (("sire",ps,sire),("dam",pd,dam)):
            if c is None:
                parents_missing[role]+=1
            elif p.startswith("B:"):
                parents_missing[role+"_not_joined_to_registered_horse"]+=1
            else:
                parents_linked[role]+=1
    pedigree_output.parent.mkdir(parents=True,exist_ok=True)
    with pedigree_output.open("w",encoding="utf-8-sig",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=["horse_id","horse_name","sire_id","dam_id","is_target"])
        writer.writeheader()
        for blood,item in sorted(output.items()):
            sire,dam=item["parents"]
            writer.writerow({
                "horse_id":"H:"+blood,"horse_name":item["name"],
                "sire_id":sire,"dam_id":dam,
                "is_target":int(blood in targets),
            })
    return {
        "status":"PRIVATE_JRA_VAN_TARGET_CSV_NAMESPACE_BRIDGE_NOT_RACE_RESULTS",
        "source_file_sha256":hash_file(input_csv),
        "input_encoding":enc,
        "original_rows":n_source,"unique_stable_blood_ids":len(blood_ids),
        "source_rows_without_blood_id":missing_blood,
        "breeding_ids_uniquely_joined_to_horses":len(breed_to_blood),
        "explicit_target_cohort":target_ids is not None,
        "target_horses":len(targets),
        "source_registry_horse_ids_not_always_ACTUAL_JRA_NAR_STARTERS":True,
        "parent_linked_by_breeding_id":dict(parents_linked),
        "parent_missing_or_unmatched":dict(parents_missing),
        "cross_registry_name_matching_performed":False,
        "pedigree_output_is_private_not_GitHub_artifact":True,
        "no_data_license_clearance_implied":True,
    }


def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-export",type=Path,required=True)
    parser.add_argument("--out-private",type=Path,required=True)
    parser.add_argument("--official-target-ids",type=Path)
    parser.add_argument("--summary",type=Path,required=True)
    args=parser.parse_args()
    result=transform(args.target_export,args.out_private,
                     target_ids=args.official_target_ids)
    args.summary.parent.mkdir(parents=True,exist_ok=True)
    args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
