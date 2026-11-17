#!/usr/bin/env python3
"""Privacy-safe 2027 official-ID known-on/source readiness preflight.

This validates *user-authorized private local CSV exports*, not live JRA access.
No raw licensed records, horse names/IDs, per-race decisions or predictions
are written to the output JSON. Future 2027 results do not yet exist here.

Known-on strict ordering: history result_known_at < entrant entry_known_at.
No use of a 2027 current race's finish or any same-time/delayed update.
Typed H:<blood registry ID> horse IDs differ from B:<breeding registry ID>.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path

JST = timedelta(hours=9)
ENTRY_REQUIRED = (
    "race_id", "horse_id", "race_start_at_jst", "entry_known_at_jst",
    "course_id", "surface", "distance_m", "sex", "age", "jockey_id",
    "trainer_id",
)
PARENT_REQUIRED = ("horse_id", "sire_id", "dam_id", "pedigree_master_known_at_jst")
HISTORY_REQUIRED = (
    "race_id", "horse_id", "race_start_at_jst", "result_known_at_jst",
    "finish_rank", "classified_field_size", "finish_status",
)


def local_jst(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise ValueError("HOLD_BAD_TIMESTAMP_FORMAT") from None
    if dt.tzinfo is None or dt.utcoffset() != JST:
        raise ValueError("HOLD_TIMESTAMP_NOT_EXPLICIT_JST_OFFSET")
    return dt


def typed_id(value: str, allowed: tuple[str,...], *, blank=False) -> str:
    s = str(value or "").strip()
    if blank and not s:
        return ""
    if not s or not any(s.startswith(p) and len(s)>len(p) for p in allowed):
        raise ValueError("HOLD_HORSE_OR_PARENT_IDENTIFIER_NAMESPACE")
    if ":" in s[s.find(":")+1:] or any(c.isspace() for c in s):
        raise ValueError("HOLD_MALFORMED_TYPED_HORSE_ID")
    if s.endswith(":0") or s.endswith(":UNKNOWN"):
        raise ValueError("HOLD_UNKNOWN_PARENT_NOT_A_SHARED_ID")
    return s


def read_csv(path:Path, required:tuple[str,...]) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fd:
        reader=csv.DictReader(fd)
        if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
            raise ValueError("HOLD_OFFICIAL_INPUT_SCHEMA_MISSING")
        rows=[{k:(v or "").strip() for k,v in row.items()} for row in reader]
    if not rows:
        raise ValueError("HOLD_OFFICIAL_INPUT_EMPTY")
    return rows


def prepare(entries:list[dict], parent_rows:list[dict], history:list[dict]):
    """Returns transient prepared input only; must NEVER be serialized."""
    known_parents={}
    for r in parent_rows:
        hid=typed_id(r["horse_id"],("H:",))
        sire=typed_id(r["sire_id"],("H:","B:"),blank=True)
        dam=typed_id(r["dam_id"],("H:","B:"),blank=True)
        if hid in (sire,dam) or (sire and dam and sire==dam):
            raise ValueError("HOLD_ILLOGICAL_OFFICIAL_PEDIGREE")
        when=local_jst(r["pedigree_master_known_at_jst"])
        if hid in known_parents:
            raise ValueError("HOLD_DUPLICATE_OFFICIAL_PEDIGREE_HORSE")
        known_parents[hid]=(sire,dam,when)
    entrants=[]
    seen=set()
    race_meta={}
    for e in entries:
        race=str(e["race_id"])
        if not race.startswith("JRA:"):
            raise ValueError("HOLD_NON_JRA_RACE_IN_PRIMARY_PANEL")
        horse=typed_id(e["horse_id"],("H:",))
        key=(race,horse)
        if key in seen:
            raise ValueError("HOLD_DUPLICATE_RACE_HORSE")
        seen.add(key)
        start=local_jst(e["race_start_at_jst"])
        cutoff=local_jst(e["entry_known_at_jst"])
        if cutoff>=start:
            raise ValueError("HOLD_ENTRY_SNAPSHOT_NOT_BEFORE_START")
        if not (datetime(2027,1,1,tzinfo=start.tzinfo)
                <= start < datetime(2027,7,1,tzinfo=start.tzinfo)):
            raise ValueError("HOLD_RACE_OUTSIDE_FROZEN_2027_H1")
        try:
            dist=int(e["distance_m"])
            age=int(e["age"])
        except (TypeError,ValueError):
            raise ValueError("HOLD_BAD_AGE_OR_DISTANCE") from None
        if not 600<=dist<=4000 or not 2<=age<=20:
            raise ValueError("HOLD_BAD_RACE_AGE_DISTANCE_RANGE")
        if e["surface"] not in ("turf","dirt"):
            raise ValueError("HOLD_BAD_SURFACE")
        metadata=(start,e["course_id"],e["surface"],dist)
        if race in race_meta and race_meta[race]!=metadata:
            raise ValueError("HOLD_INCONSISTENT_RACE_CONDITIONS")
        race_meta[race]=metadata
        if horse not in known_parents:
            raise ValueError("HOLD_HORSE_NOT_IN_OFFICIAL_PEDIGREE_MASTER")
        sire,dam,known=known_parents[horse]
        if known>=cutoff:
            raise ValueError("HOLD_PARENTS_NOT_KNOWN_AT_RACE_CUTOFF")
        entrants.append({
            "race":race,"horse":horse,"start":start,"cutoff":cutoff,
            "sire":sire,"dam":dam,"surface":e["surface"],
            "distance":dist,
        })
    histories=[]
    seen_h=set()
    for h in history:
        race=str(h["race_id"])
        horse=typed_id(h["horse_id"],("H:",))
        if (race,horse) in seen_h:
            raise ValueError("HOLD_DUPLICATE_HISTORY_RACE_HORSE")
        seen_h.add((race,horse))
        start=local_jst(h["race_start_at_jst"])
        known=local_jst(h["result_known_at_jst"])
        if known<start:
            raise ValueError("HOLD_RACE_RESULT_KNOWN_BEFORE_START")
        try:
            rank=int(h["finish_rank"])
            field=int(h["classified_field_size"])
        except (ValueError,TypeError):
            raise ValueError("HOLD_NONINTEGER_HISTORIC_RANK") from None
        if h["finish_status"]!="CLASSIFIED" or not 2<=field<=30 or not 1<=rank<=field:
            raise ValueError("HOLD_HISTORY_NOT_VALID_CLASSIFIED_RANK")
        histories.append({
            "horse":horse,"race":race,"start":start,"known":known,
            "y":(rank-1)/(field-1),
        })
    return entrants,known_parents,histories


def audit(entries:list[dict], parents:list[dict], history:list[dict]):
    entrants,known_parents,histories=prepare(entries,parents,history)
    timeline=defaultdict(list)
    for h in histories:
        timeline[h["horse"]].append(h)
    for h in timeline.values():
        h.sort(key=lambda x:x["known"])
    support=Counter()
    overlap=Counter()
    for row in entrants:
        cutoff=row["cutoff"]
        own=[h for h in timeline[row["horse"]] if h["known"]<cutoff]
        relatives=set()
        for horse,(sire,dam,known) in known_parents.items():
            if horse==row["horse"] or known>=cutoff:
                continue
            if ((row["sire"] and sire==row["sire"])
                    or (row["dam"] and dam==row["dam"])):
                relatives.add(horse)
        # Each different relative contributes one prior-history mean rather than
        # a large number of repeated starts. Missing parent IDs never match.
        prior={}
        for rel in relatives:
            used=[h["y"] for h in timeline[rel] if h["known"]<cutoff]
            if used:
                prior[rel]=sum(used)/len(used)
        support["entrant_rows"]+=1
        support["own_history_available"]+=bool(own)
        support["relatives_with_pretarget_history"]+=bool(prior)
        support["pretarget_own_observations"]+=len(own)
        support["pretarget_relatives_distinct"]+=len(prior)
        support["future_or_delayed_own_results_excluded"]+=sum(
            h["known"]>=cutoff for h in timeline[row["horse"]]
        )
        # A target's own start must never count as another family member.
        if row["horse"] in prior:
            raise ValueError("HOLD_FOCAL_AS_OWN_RELATIVE")
        overlap[row["race"]]+=1
    return {
        "status":"OFFICIAL_JRA_2027_H1_PRIVATE_INPUT_PREFLIGHT_ONLY_NO_FORECAST",
        "cohort":{"eligible_entered_horses":len(entrants),
                  "races":len(overlap),
                  "unique_horses":len({r["horse"] for r in entrants})},
        "historical_support":dict(support),
        "privacy_and_provenance":{
            "names_used_as_join_keys":False,
            "blood_vs_breeding_ID_namespaces_typed":True,
            "result_publication_before_entry_cutoff_required":True,
            "same_day_or_future_result_never_assumed_usable":True,
            "target_2027_outcomes_not_required_or_scored_here":True,
            "no_raw_horse_ids_names_or_race_rows_serialized":True,
            "official_license_and_source_permissions_not_verified_by_code":True,
        },
        "next_gate":"HOLD_ACTUAL_2027_OFFICIAL_RESULTS_AND_FROZEN_MODEL",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entries",type=Path,required=True)
    p.add_argument("--parents",type=Path,required=True)
    p.add_argument("--history",type=Path,required=True)
    p.add_argument("--out-aggregate",type=Path,required=True)
    a=p.parse_args()
    result=audit(read_csv(a.entries,ENTRY_REQUIRED),
                 read_csv(a.parents,PARENT_REQUIRED),
                 read_csv(a.history,HISTORY_REQUIRED))
    a.out_aggregate.parent.mkdir(parents=True,exist_ok=True)
    a.out_aggregate.write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8"
    )
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
