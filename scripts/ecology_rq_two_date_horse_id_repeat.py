#!/usr/bin/env python3
"""Two-date *official* Thoroughbred HORSES-ID recurrence feasibility audit.

Bounded to 2026-08-29 and 2026-10-11 Cannon Park, with only 4 selected
official races per date. Reads official meeting/race/HORSES SOAP responses
and exactly two original sectional CSVs. Never writes horse names,
race IDs, horse IDs, raw GPS rows or downloaded XML. Aggregate JSON only.

A recurring same official numeric HORSES ID over two dates establishes
source-record ID reuse, not biological effect, fitness, or necessarily a
confirmed start. The old data have no verified DNF/finish status or
individual official finishing time. H1/H2 remain explicitly HOLD.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from ecology_rq_single_race_id_probe import (
    identified_meeting, value, attr, xml_nodes, horse_candidates,
    request_xml,
)
from ecology_rq_thoroughbred_sectional_audit import (
    fetch_official, parse as parse_sectionals,
)
from ecology_rq_official_id_crosswalk import (
    canon_name, sections_in_memory,
)


SAMPLE = {
    "2026-08-29": {
        "venue": "Ladbrokes Cannon Park",
        "race_numbers": (2,3,4,5),
        "sectionals": "20260829-cairns",
    },
    "2026-10-11": {
        "venue": "Ladbrokes Cannon Park",
        "race_numbers": (2,3,5,6),
        "sectionals": "20261011-cairns",
    },
}
MAX_RACES_EACH_DATE = 4


def extract_selected_races(root, target: tuple[int,...]):
    candidates=xml_nodes(root,"Race")
    found={}
    for race in candidates:
        number=value(race,"RaceNumber","Number")
        if not number or not number.isdecimal():
            continue
        n=int(number)
        if n not in target:
            continue
        rid=attr(race,"Id")
        if n in found or not rid or not rid.isdecimal():
            raise ValueError("HOLD_DUPLICATE_OR_BAD_OFFICIAL_RACE_ID")
        found[n]={
            "race_id":rid, "ground":value(race,"TrackRating"),
            "official_distance":value(race,"Distance"),
            "class":value(race,"Class"),
        }
    if set(found)!=set(target):
        raise ValueError(
            f"HOLD_INCOMPLETE_SELECTED_OFFICIAL_RACE_SET:"
            f"expected={len(target)},observed={len(found)}"
        )
    return found, len(candidates)


def gps_index(sectionals_raw:bytes, day:str):
    parsed = parse_sectionals(sectionals_raw,"original official GPS, summary")
    if parsed["race_counts"]["source_dates"] != [day]:
        raise ValueError("HOLD_GPS_SOURCE_DATE_NOT_SAME_AS_OFFICIAL")
    all_rows=sections_in_memory(sectionals_raw)
    name_races=defaultdict(set)
    per_race=defaultdict(list)
    for item in all_rows:
        name_races[(day,item["name_normalized"])].add(
            item["race_number"]
        )
        per_race[item["race_number"]].append(item)
    ambiguous={
        name for (date,name),races in name_races.items()
        if date==day and len(races)>1
    }
    return per_race,ambiguous,parsed


def one_date(
    day:str, *,
    request_fn=request_xml,
    gps_fn=fetch_official,
) -> tuple[dict,dict]:
    if day not in SAMPLE:
        raise ValueError("HOLD_NON_ALLOWLISTED_EQUINE_DATE")
    cfg=SAMPLE[day]
    numbers=cfg["race_numbers"]
    if len(numbers)>MAX_RACES_EACH_DATE:
        raise ValueError("HOLD_TOO_MANY_OFFICIAL_RACES")
    meeting_xml,_,meeting_hash=request_fn(
        "GetMeetingsForDate",{"meetingDate":day})
    mid,_=identified_meeting(meeting_xml,day,cfg["venue"])
    races_xml,_,race_hash=request_fn(
        "GetRacesForMeeting",{"meetingId":mid})
    races,all_races_n=extract_selected_races(races_xml,numbers)
    raw,_=gps_fn(cfg["sectionals"])
    gps,blocked,readiness=gps_index(raw,day)
    rows=[]
    for number in numbers:
        official_horse_xml,_,hhash=request_fn(
            "GetHorsesForRace",{"raceId":races[number]["race_id"]})
        candidates,shape=horse_candidates(official_horse_xml)
        if len(candidates)<1 or shape["records_with_numeric_Id_and_named_value"]!=len(candidates):
            raise ValueError("HOLD_OFFICIAL_HORSE_IDS_OR_NAMES_MISSING")
        names=[canon_name(x["horse_name"]) for x in candidates]
        ids=[x["horse_id"] for x in candidates]
        if len(set(ids))!=len(ids) or len(set(names))!=len(names):
            raise ValueError("HOLD_OFFICIAL_DUPLICATE_NAME_OR_HORSE_ID_IN_ONE_RACE")
        gps_entries=gps.get(number,[])
        gps_names=[x["name_normalized"] for x in gps_entries]
        if len(set(gps_names))!=len(gps_names):
            raise ValueError("HOLD_DUPLICATE_GPS_NAME_SAME_RACE")
        by_gps={x["name_normalized"]:x for x in gps_entries}
        for name,hid in zip(names,ids):
            source=by_gps.get(name)
            rows.append({
                "horse_id":hid,"name":name,"race_number":number,
                "gps_exact_unique_name":bool(source and name not in blocked),
                "gps_positive":bool(source and source["gps_positive"] and name not in blocked),
                "gps_zero":bool(source and source["gps_all_zero"] and name not in blocked),
                "ambiguous_name_across_same_day_races":bool(name in blocked),
            })
    # Do not promote a HORSES ID appearing in multiple race nominations
    # on one date to a unique, verified start. Even a GPS all-zero entry
    # may be a nomination/scratch, not a completed race.
    occurrence=Counter(x["horse_id"] for x in rows)
    unique={
        x["horse_id"]:x for x in rows
        if occurrence[x["horse_id"]]==1
        and not x["ambiguous_name_across_same_day_races"]
        and x["gps_exact_unique_name"]
    }
    name_mismatch_in_same_id=0
    report={
        "day":day,
        "venue":cfg["venue"],
        "selected_race_count":len(races),
        "all_official_races_in_meeting":all_races_n,
        "source_sha256":{
            "meeting_xml":meeting_hash,
            "race_xml":race_hash,
            "gps_sectionals":hashlib.sha256(raw).hexdigest(),
        },
        "official_selected_race_metadata_groups":{
            "ground_labels":dict(Counter(
                races[number]["ground"] or "MISSING" for number in numbers)),
            "distances":dict(Counter(
                races[number]["official_distance"] or "MISSING"
                for number in numbers)),
            "classes":dict(Counter(
                races[number]["class"] or "MISSING" for number in numbers)),
        },
        "official_horse_rows_selected":len(rows),
        "distinct_official_horse_ids_in_selected_races":len(occurrence),
        "official_IDs_occurring_in_multiple_selected_races_same_day":sum(
            k>1 for k in occurrence.values()),
        "syntactically_matched_positive_gps":sum(x["gps_positive"] for x in rows),
        "syntactically_matched_zero_gps":sum(x["gps_zero"] for x in rows),
        "official_with_no_unique_gps_match":sum(
            not x["gps_exact_unique_name"] for x in rows),
        "day_wide_ambiguous_gps_names":len(blocked),
        "individually_linkable_official_id_gps_rows_this_date":len(unique),
        "gps_schema_horse_rows_whole_meeting":readiness["race_counts"]["horse_rows"],
        "gps_rows_republished":False,
    }
    return report,unique


def compare(
    *,
    request_fn=request_xml,
    gps_fn=fetch_official,
) -> dict:
    statuses={}
    ids={}
    for day in SAMPLE:
        statuses[day],ids[day]=one_date(
            day,request_fn=request_fn,gps_fn=gps_fn
        )
    earlier,later=tuple(SAMPLE)
    shared=set(ids[earlier])&set(ids[later])
    same_name={hid for hid in shared
               if ids[earlier][hid]["name"]==ids[later][hid]["name"]}
    mismatched=shared-same_name
    both_positive={hid for hid in same_name
                   if ids[earlier][hid]["gps_positive"] and
                   ids[later][hid]["gps_positive"]}
    with_zero={hid for hid in same_name
               if ids[earlier][hid]["gps_zero"] or ids[later][hid]["gps_zero"]}
    observed_dates=tuple(SAMPLE)
    return {
        "status":"REAL_HORSE_OFFICIAL_ID_RECURRENCE_AUDIT_H1_H2_HOLD",
        "source_publisher":"Racing Queensland",
        "cross_date": {
            "days":list(observed_dates),
            "both_same_official_horse_id_and_exact_name":len(same_name),
            "repeating_numeric_id_but_name_changed":len(mismatched),
            "repeated_official_ids_with_positive_gps_both_dates":len(both_positive),
            "repeated_official_ids_with_zero_gps_either_date":len(with_zero),
            "repetition_is_confirmed_finish_time_or_horse_reaction_norm":False,
            "selected_races_were_chosen_for_identity_feasibility_not_randomly":True,
        },
        "per_date":statuses,
        "api_calls_upper_bound":2*(2+MAX_RACES_EACH_DATE),
        "identity_values_or_raw_horse_names_exported":False,
        "source_gps_raw_records_exported":False,
        "track_ground_response_identifiable_after_two_dates":False,
        "competitor_interactions_identifiable_after_two_dates":False,
        "limits":[
            "Repeated official numeric HORSES ID across dates is source-level ID stability, not a completed ecological repeated-exposure panel.",
            "Only four deliberately selected races per date, so all-starter completeness and selection are not established.",
            "Some official horse lists can include nominated/scratched horses; all-zero GPS is not a DNF or zero speed.",
            "No official individual certified elapsed race time, first-call position, or complete contemporary opponent phenotypes are joined.",
            "No stable variation across two going conditions or controlled class/distance cohorts has been demonstrated.",
            "No individual IDs, names, raw measurements or financial betting information are published here.",
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    out=compare()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "per_date":out["per_date"],
        "cross_date":out["cross_date"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
