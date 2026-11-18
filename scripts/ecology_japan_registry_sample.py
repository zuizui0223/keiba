#!/usr/bin/env python3
"""Run all-pair exact A queries within the 11 curated REAL registry examples.

This is a tiny, nonrepresentative JBIS-derived *factual* source demonstration,
not bulk JBIS copying and not all Japanese racehorses. Sire identifiers were
not independently linked, so known-sire coverage correctly stays at ZERO.
"""
from __future__ import annotations

import argparse
import csv
from itertools import combinations
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ecology_japan_registry_pedigree import analyze


def run(source: Path) -> dict:
    data=json.loads(source.read_text(encoding="utf-8"))
    if not data.get("scope","").startswith("PURPOSELY SELECTED"):
        raise ValueError("HOLD_SAMPLE_SELECTION_NOT_DISCLOSED")
    profiles=data["profiles"]
    with TemporaryDirectory() as td:
        source_csv=Path(td)/"parents.csv"
        pairs_csv=Path(td)/"queries.csv"
        all_results=Path(td)/"results.csv"
        with source_csv.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=["horse_id","horse_name","sire_id","dam_id"])
            writer.writeheader()
            for x in profiles:
                writer.writerow({
                    "horse_id":x["jbis_id"],
                    "horse_name":x["horse_name"],
                    "sire_id":"",  # NO verified canonical sire JBIS identifier
                    "dam_id":x.get("dam_jbis_id") or "",
                })
        with pairs_csv.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=["horse_id_1","horse_id_2"])
            writer.writeheader()
            for a,b in combinations(sorted(x["jbis_id"] for x in profiles),2):
                writer.writerow({"horse_id_1":a,"horse_id_2":b})
        summary=analyze(source_csv,pair_file=pairs_csv,pair_output=all_results)
    return {
        "status":"CURATED_11_REAL_JAPAN_HORSES_55_PAIRS_ONLY_NOT_ALL_JAPAN",
        "basis":"public profile facts manually checked in Nov 2026, not a licensed registry bulk export",
        "n_profiles":len(profiles),
        "partial_A_results":summary["statistics"],
        "verified_canonical_sire_ids":0,
        "unlinked_true_kinship_not_equivalent_to_zero":True,
        "not_official_countrywide_coverage":True,
        "not_horse_racing_performance_prediction":True,
        "relationship_matrix_saved_or_exported_publicly":False,
        "individual_profile_identifiers_only_in_checked_source_file":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profiles",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    opts=ap.parse_args()
    report=run(opts.profiles)
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
