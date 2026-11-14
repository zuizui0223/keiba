#!/usr/bin/env python3
"""Small, human-source-cited Japanese Meisho registry linkage audit.

No data scraping and no prediction. A name prefix and current owner are
NOT genetic relationships or historical pre-race owner facts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import re

from ecology_pedigree_forward import Pedigree

ID = re.compile(r"^[0-9]{10}$")
JBIS_BASE = "https://www.jbis.or.jp/horse/"
PREFIX = "メイショウ"


def _validate(payload: dict) -> dict[str, dict]:
    if not payload.get("profiles"):
        raise ValueError("HOLD_NO_MANUALLY_VERIFIED_PROFILES")
    if payload.get("scope", "").startswith("PURPOSELY SELECTED") is False:
        raise ValueError("HOLD_INSUFFICIENT_SELECTION_DISCLOSURE")
    if not payload.get("snapshot_recorded_on"):
        raise ValueError("HOLD_NO_SNAPSHOT_DATE")
    index: dict[str, dict] = {}
    for row in payload["profiles"]:
        identifier = row["jbis_id"]
        if not isinstance(identifier, str) or not ID.fullmatch(identifier) or identifier in index:
            raise ValueError("HOLD_INVALID_OR_DUPLICATE_JBIS_ID")
        if row.get("profile_url") != JBIS_BASE + identifier + "/":
            raise ValueError("HOLD_SOURCE_URL_DOES_NOT_MATCH_STABLE_ID")
        for key in ("horse_name", "sire_label", "dam_label"):
            if not row.get(key):
                raise ValueError("HOLD_INCOMPLETE_MANUAL_PARENT_NAME")
        if not row.get("displayed_owner") or not row.get("displayed_trainer"):
            raise ValueError("HOLD_INCOMPLETE_PROFILE_SNAPSHOT")
        dam = row.get("dam_jbis_id")
        if dam is not None and (not isinstance(dam, str) or not ID.fullmatch(dam) or dam == identifier):
            raise ValueError("HOLD_INVALID_MOTHER_REFERENCE")
        index[identifier] = row
    for row in index.values():
        dam = row.get("dam_jbis_id")
        if dam is not None:
            if dam not in index:
                raise ValueError("HOLD_MOTHER_NOT_IN_FIXED_PROFILE_SET")
            if index[dam]["horse_name"] != row["dam_label"]:
                raise ValueError("HOLD_MOTHER_NAME_AND_ID_DISAGREE")
    return index


def summarize(payload: dict) -> dict:
    records = _validate(payload)
    # Sire canonical IDs are deliberately NOT inferred from name labels.
    pedigree = Pedigree({
        pid: (None, r.get("dam_jbis_id")) for pid, r in records.items()
    })
    parentage, documented_links = [], []
    same_prefix_pairs = 0
    for (ida, a), (idb, b) in combinations(sorted(records.items()), 2):
        fa, fb = a["horse_name"].startswith(PREFIX), b["horse_name"].startswith(PREFIX)
        if fa and fb:
            same_prefix_pairs += 1
        linked = pedigree.relationship(ida, idb)
        if linked > 0:
            documented_links.append({
                "pair": sorted([a["horse_name"], b["horse_name"]]),
                "documented_dam_only_A": round(linked, 6),
                "same_name_prefix": fa == fb,
                "same_displayed_owner": a["displayed_owner"] == b["displayed_owner"],
            })
        dam = a.get("dam_jbis_id")
        if dam is not None and dam == b.get("dam_jbis_id"):
            # Different verified sire labels => confirmed different sires
            # in these curated pages, but aliases must not be generalized.
            if a["sire_label"] == b["sire_label"]:
                raise ValueError("HOLD_FULL_SIB_OR_SIRE_ALIAS_REQUIRES_DIRECT_VERIFICATION")
            parentage.append({
                "pair": sorted([a["horse_name"], b["horse_name"]]),
                "mother": records[dam]["horse_name"],
                "same_name_prefix": fa == fb,
                "same_displayed_owner": a["displayed_owner"] == b["displayed_owner"],
                "minimal_pedigree_expected_A": round(linked, 6),
            })
    counts = Counter(
        {"profiles":len(records),"names_with_meisho_prefix":sum(
            r["horse_name"].startswith(PREFIX) for r in records.values()),
         "other_name_profiles":sum(
            not r["horse_name"].startswith(PREFIX) for r in records.values()),
         "distinct_displayed_owners":len({r["displayed_owner"] for r in records.values()}),
         "distinct_displayed_sires":len({r["sire_label"] for r in records.values()}),
         "manually_linked_dams":sum(bool(r.get("dam_jbis_id")) for r in records.values()),
         "same_meisho_name_pairs":same_prefix_pairs,
         "same_dam_different_sire_pairs":len(parentage),
         "same_dam_pairs_with_name_prefix_difference":sum(not p["same_name_prefix"] for p in parentage),
         "same_dam_pairs_with_displayed_owner_difference":sum(not p["same_displayed_owner"] for p in parentage),
         "documented_nonzero_dam_path_pairs":len(documented_links),
         "owner_disagreement_within_meisho_named_profiles":len({
             r["displayed_owner"] for r in records.values()
             if r["horse_name"].startswith(PREFIX)})>1,
        }
    )
    return {
        "status": "REAL_PUBLIC_PEDIGREE_FACTS_AUDITED_NOT_PREDICTIVE_RESULT",
        "evidence_class": "HAND_VERIFIED_SMALL_NONREPRESENTATIVE_JBIS_SAMPLE",
        "metadata_snapshot_on": payload["snapshot_recorded_on"],
        "counts": dict(counts),
        "known_shared_dam_different_sire_examples": parentage,
        "documented_dam_path_relationships": documented_links,
        "denominators_are_SELECTED_PROFILES_not_all_JAPAN_or_all_MEISHO": True,
        "unlinked_pairs_are_NOT_classified_as_genetically_unrelated": True,
        "displayed_owner_labels_are_NOT_historical_race_owner_ids": True,
        "known_parent_crosswalk_is_dam_only_no_verified_sire_ID": True,
        "expected_A_is_partial_pedigree_under_unrelated_unknown_founders": True,
        "racing_dates_or_outcomes_in_input": False,
        "real_future_prediction_or_heritability_estimated": False,
        "licensed_race_history_required_for_prediction": True,
        "no_automated_scraping": True,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profiles", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = summarize(json.loads(args.profiles.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
