#!/usr/bin/env python3
"""Small, read-only official Racing Queensland SOAP/HTTP-GET horse-ID probe.

Verifies on one pre-allowlisted *historical* Queensland Thoroughbred race:
meeting-date -> meeting ID -> race ID -> list of HORSES internal horse IDs.
Tests a conservative in-memory name join to the official GPS sectionals.
Does not write any horse identities, names, raw API responses, or GPS rows.

This is an ID-compatibility audit, NEVER evidence for ecological H1/H2,
DNF status, all-horse completeness, individual finish time or causal effects.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from ecology_rq_thoroughbred_sectional_audit import (
    APPROVED, fetch_official, parse as parse_sectionals,
)
from ecology_rq_official_id_crosswalk import audit as audit_crosswalk, canon_name


HOST = "www.racingqueensland.com.au"
BASE = f"https://{HOST}/opendatawebservices/Meetings.asmx"
ALLOWED = {
    "2026-10-11": {
        "venue": "Ladbrokes Cannon Park",
        "race_number": 1,
        "gps_source": "20261011-cairns",
    },
}
MAX_XML = 600_000


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def xml_nodes(root: ET.Element, type_name: str) -> list[ET.Element]:
    return [
        item for item in root.iter()
        if local(item.tag).casefold() == type_name.casefold()
    ]


def attr(node: ET.Element, name: str) -> str | None:
    for k, value in node.attrib.items():
        if local(k).casefold() == name.casefold():
            return value.strip()
    return None


def value(node: ET.Element, *names: str) -> str | None:
    labels = {n.casefold() for n in names}
    for element in list(node):
        if local(element.tag).casefold() in labels:
            s = "".join(element.itertext()).strip()
            if s:
                return s
    return None


def safe_shape(nodes: list[ET.Element]) -> dict:
    """Report *field names*, not field values or individual identifiers."""
    return {
        "rows": len(nodes),
        "element_names": sorted({local(n.tag) for n in nodes}),
        "attribute_names": sorted({
            local(k) for n in nodes for k in n.attrib
        }),
        "direct_child_field_names": sorted({
            local(ch.tag) for n in nodes for ch in list(n)
        }),
    }


def parse_xml(raw: bytes) -> ET.Element:
    if not raw or len(raw) > MAX_XML:
        raise ValueError("HOLD_XML_EMPTY_OR_EXCEEDS_SIZE_LIMIT")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("HOLD_XML_DTD_OR_ENTITY_DECLARATION")
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("HOLD_SOAP_INVALID_XML") from exc


def request_xml(op: str, params: dict[str, str]) -> tuple[ET.Element, str, str]:
    allowed = {
        "GetMeetingsForDate": {"meetingDate"},
        "GetRacesForMeeting": {"meetingId"},
        "GetHorsesForRace": {"raceId"},
        "GetHorseDetailsInRace": {"raceId", "horseId"},
    }
    if op not in allowed or set(params) != allowed[op]:
        raise ValueError("HOLD_UNAPPROVED_SOAP_OPERATION_OR_PARAMETERS")
    if not all(str(x).strip() for x in params.values()):
        raise ValueError("HOLD_EMPTY_SOAP_PARAMETER")
    uri = f"{BASE}/{op}?{urlencode(params)}"
    with urlopen(Request(uri, headers={
        "User-Agent": "keiba-ecology/0.2 official-identity-feasibility-read-only",
        "Accept": "application/xml,text/xml,*/*",
    }), timeout=20) as response:
        parsed = urlparse(response.geturl())
        if parsed.scheme != "https" or parsed.hostname != HOST:
            raise ValueError("HOLD_UNEXPECTED_SOAP_REDIRECT")
        raw = response.read(MAX_XML + 1)
    root = parse_xml(raw)
    return root, uri, hashlib.sha256(raw).hexdigest()


def identified_meeting(root: ET.Element, day: str, venue: str) -> tuple[str, dict]:
    candidates = xml_nodes(root, "Meeting")
    selected = [
        n for n in candidates
        if value(n, "MeetingDate") == day
        and value(n, "TrackName") == venue
        and (value(n, "IsBarrierTrial") or "").casefold() == "false"
    ]
    if len(selected) != 1:
        raise ValueError(
            f"HOLD_NOT_EXACTLY_ONE_OFFICIAL_MEETING:matches={len(selected)}"
        )
    mid = attr(selected[0], "Id")
    if not mid or not mid.isdecimal():
        raise ValueError("HOLD_OFFICIAL_MEETING_ID_MISSING_OR_INVALID")
    return mid, safe_shape(candidates)


def identified_race(root: ET.Element, n: int) -> tuple[str, dict]:
    candidates = xml_nodes(root, "Race")
    matching = [
        race for race in candidates
        if (value(race, "RaceNumber") or value(race, "Number") or "").strip()
        == str(n)
    ]
    if len(matching) != 1:
        raise ValueError(
            f"HOLD_NOT_EXACTLY_ONE_OFFICIAL_RACE:matches={len(matching)}"
        )
    rid = attr(matching[0], "Id")
    if not rid or not rid.isdecimal():
        raise ValueError("HOLD_OFFICIAL_RACE_ID_MISSING_OR_INVALID")
    return rid, safe_shape(candidates)


def horse_candidates(root: ET.Element) -> tuple[list[dict], dict]:
    nodes = xml_nodes(root, "Horse")
    shape = safe_shape(nodes)
    found = []
    for node in nodes:
        hid = attr(node, "Id")
        name = value(node, "HorseName", "Name")
        if hid and hid.isdecimal() and name:
            found.append({
                "horse_id": hid,
                "horse_name": name,
            })
    shape["records_with_numeric_Id_and_named_value"] = len(found)
    shape["distinct_numeric_horse_ids"] = len({
        x["horse_id"] for x in found
    })
    shape["different_exact_horse_names"] = len({
        canon_name(x["horse_name"]) for x in found
    })
    return found, shape


def candidate_gps_join(
    race_date: str, race_number: int, race_id: str,
    horses: list[dict], raw: bytes,
) -> dict:
    # Only a candidate name match. The source API may list declared
    # entrants, not officially confirmed starters; statuses stay unknown.
    source = parse_sectionals(raw, "OFFICIAL RQ; summary only")
    if source["race_counts"]["source_dates"] != [race_date]:
        raise ValueError("HOLD_OFFICIAL_GPS_DATE_MISMATCH")
    ids = {x["horse_id"] for x in horses}
    if len(ids) != len(horses):
        raise ValueError("HOLD_DUPLICATE_OFFICIAL_HORSE_ID")
    roster = [{
        "race_date": race_date, "race_number": race_number,
        "official_race_id": race_id,
        "official_horse_id": h["horse_id"],
        "name_normalized": canon_name(h["horse_name"]),
        "start_status": "unknown",
        "finish_status": "unknown",
    } for h in horses]
    # Existing fail-closed crosswalk blocks names reused on the
    # same meeting day in another race heading.
    return audit_crosswalk(raw, roster)


def run_single_day(
    day: str, *, gps_raw: bytes | None = None,
    request_fn=request_xml,
) -> dict:
    if day not in ALLOWED:
        raise ValueError("HOLD_NOT_ALLOWLISTED_RESEARCH_DATE")
    cfg = ALLOWED[day]
    records = {"meeting": {}, "race": {}, "horses": {}}
    meeting_xml, meeting_url, meeting_hash = request_fn(
        "GetMeetingsForDate", {"meetingDate": day}
    )
    mid, meeting_shape = identified_meeting(
        meeting_xml, day, cfg["venue"]
    )
    records["meeting"] = {
        "source_url": meeting_url,
        "sha256": meeting_hash,
        "schema": meeting_shape,
        "meeting_id_found_and_validated": True,
    }
    race_xml, race_url, race_hash = request_fn(
        "GetRacesForMeeting", {"meetingId": mid}
    )
    rid, race_shape = identified_race(race_xml, cfg["race_number"])
    records["race"] = {
        "source_url": race_url,
        "sha256": race_hash,
        "schema": race_shape,
        "race_id_found_and_validated": True,
    }
    horse_xml, horse_url, horse_hash = request_fn(
        "GetHorsesForRace", {"raceId": rid}
    )
    horses, horse_shape = horse_candidates(horse_xml)
    records["horses"] = {
        "source_url": horse_url,
        "sha256": horse_hash,
        "schema": horse_shape,
        "stable_HORSES_ids_verified_across_dates": False,
        "true_starter_status_verified": False,
    }
    # Return HOLD even when IDs and names are found.
    result = {
        "status": "HOLD_RQ_OFFICIAL_ID_CROSSWALK_NOT_COMPLETE",
        "source_publisher": "Racing Queensland official web service",
        "meeting_date": day,
        "selected_venue": cfg["venue"],
        "race_number": cfg["race_number"],
        "api": records,
        "any_raw_names_or_horse_ids_output": False,
        "official_IDs_and_GPS_matching_not_guessed": True,
        "all_zero_sectionals_not_called_dnf": True,
        "H1_real_horse_effect_supported": False,
        "H2_real_horse_effect_supported": False,
        "limitations": [
            "Official HORSES attributes are not themselves proof of a repeated-start longitudinal panel.",
            "GetHorsesForRace may list nominees/runners rather than final verified starters.",
            "No canonical start_status or individual finish_time is inferred from GPS zeros.",
            "Only exact within-race names are provisionally matched; same-day duplicate names are blocked.",
            "Race/horse IDs are never published in output, only counts and SHA256.",
        ],
    }
    if not horses:
        result["crosswalk"] = {
            "status": "HOLD_HORSE_SCHEMA_UNRESOLVED",
            "reason": "No horse record with both valid numeric ID and Name/HorseName field",
        }
        return result
    if gps_raw is None:
        gps_raw, gps_url = fetch_official(cfg["gps_source"])
    else:
        from ecology_rq_thoroughbred_sectional_audit import official_url
        gps_url = official_url(cfg["gps_source"])
    candidate = candidate_gps_join(
        day, cfg["race_number"], rid, horses, gps_raw
    )
    result["crosswalk"] = {
        "source_url": gps_url,
        "source_sha256": hashlib.sha256(gps_raw).hexdigest(),
        "raw_horse_records_saved_to_git": False,
        **candidate,
    }
    # The underlying crosswalk method refuses to assign actual
    # biological ID from a name-only match.
    return result


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--date", choices=sorted(ALLOWED), default="2026-10-11")
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    report = run_single_day(args.date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    counts = report.get("crosswalk", {}).get("counts", {})
    print(json.dumps({
        "status": report["status"],
        "schema": {key: value["schema"] for key, value in report["api"].items()},
        "crosswalk_counts": counts,
        "crosswalk_status": report.get("crosswalk", {}).get("status"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
