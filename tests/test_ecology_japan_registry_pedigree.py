"""Algebraic relationship and scale guards for Japanese nationwide pedigree export.

Uses a tiny manually curated registry sample and invented stress horses.
No JRA/NAR records or complete nationwide registry are being fabricated.
"""
from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ecology_japan_registry_pedigree import (
    RegistryPedigree, analyze, counts, per_horse, pair_queries,
)

SAMPLE = ROOT / "docs/evidence/japan-meisho-manual-profile-snapshot-20261114.json"


def save(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def materialize_sample(directory: str):
    payload=json.loads(SAMPLE.read_text(encoding="utf-8"))
    records=[{
        "horse_id":r["jbis_id"],
        "horse_name":r["horse_name"],
        "sire_id":"",  # NOT a verified canonical sire identifier.
        "dam_id":r.get("dam_jbis_id") or "",
    } for r in payload["profiles"]]
    pedigree = Path(directory)/"partial_registry.csv"
    pairs = Path(directory)/"candidate_pairs.csv"
    save(pedigree, records, ["horse_id","horse_name","sire_id","dam_id"])
    ordered=sorted(x["horse_id"] for x in records)
    save(pairs, [
        {"horse_id_1":a,"horse_id_2":b}
        for a,b in itertools.combinations(ordered,2)
    ], ["horse_id_1","horse_id_2"])
    return pedigree,pairs


class RegistryRelationshipTests(unittest.TestCase):
    def test_full_half_parent_and_inbred_coefficients(self):
        p=RegistryPedigree([
            {"horse_id":"S","sire_id":"","dam_id":""},
            {"horse_id":"D","sire_id":"","dam_id":""},
            {"horse_id":"D2","sire_id":"","dam_id":""},
            {"horse_id":"A","sire_id":"S","dam_id":"D"},
            {"horse_id":"B","sire_id":"S","dam_id":"D"},
            {"horse_id":"H","sire_id":"S","dam_id":"D2"},
            {"horse_id":"IN","sire_id":"A","dam_id":"B"},
        ])
        self.assertAlmostEqual(p.a("A","B"),0.5)
        self.assertAlmostEqual(p.a("A","H"),0.25)
        self.assertAlmostEqual(p.a("S","A"),0.5)
        self.assertAlmostEqual(p.f("IN"),0.25)
        self.assertAlmostEqual(p.a("IN","S"),0.5)
        self.assertAlmostEqual(p.a("IN","IN"),1.25)
        self.assertAlmostEqual(p.a("B","A"),p.a("A","B"))

    def test_selected_meisho_11_have_13_documented_maternal_paths(self):
        with tempfile.TemporaryDirectory() as d:
            path,pairs = materialize_sample(d)
            out=Path(d)/"queries.csv"
            individual=Path(d)/"all.csv"
            result=analyze(path,per_horse_file=individual,
                           pair_file=pairs,pair_output=out)
            entries=list(csv.DictReader(out.open(encoding="utf-8")))
        summary=result["statistics"]
        self.assertEqual(summary["target_horses"],11)
        self.assertEqual(summary["target_known_sire"],0)
        self.assertEqual(summary["target_known_dam"],6)
        self.assertEqual(summary["shared_dam_target_pairs_including_unknown_other_parent"],3)
        self.assertEqual(summary["confirmed_maternal_half_pairs_both_sires_known_distinct"],0)
        self.assertEqual(summary["pair_queries"],55)
        self.assertEqual(summary["documented_positive_pairs"],13)
        self.assertTrue(result["target_source_completeness_verified_by_code"] is False)
        positives=[x for x in entries if float(x["partial_numerator_A"])>0]
        self.assertEqual(len(positives),13)
        values={frozenset((x["horse_id_1"],x["horse_id_2"])):float(x["partial_numerator_A"])
                for x in entries}
        self.assertAlmostEqual(values[frozenset(("0001335651","0001267813"))],0.25)
        self.assertAlmostEqual(values[frozenset(("0001335651","0001046777"))],0.125)
        self.assertEqual(
            next(x["status"] for x in entries
                 if {x["horse_id_1"],x["horse_id_2"]}=={"0000760084","0001335651"}),
            "NO_PATH_IN_TRUNCATED_PEDIGREE_NOT_UNRELATED",
        )

    def test_unknown_father_and_mother_never_counted_as_shared(self):
        p=RegistryPedigree([
            {"horse_id":"A","sire_id":"","dam_id":""},
            {"horse_id":"B","sire_id":"","dam_id":""},
            {"horse_id":"C","sire_id":"S","dam_id":""},
            {"horse_id":"D","sire_id":"S","dam_id":""},
        ])
        self.assertEqual(p.a("A","B"),0)
        self.assertAlmostEqual(p.a("C","D"),0.25)
        summary,_=counts(p,sorted(p.recorded))
        self.assertEqual(summary["shared_sire_target_pairs_including_unknown_other_parent"],1)
        self.assertEqual(summary["confirmed_paternal_half_pairs_both_dams_known_distinct"],0)
        self.assertEqual(summary["linked_parent_placeholders_not_in_source"],1)

    def test_full_sibling_counts_and_distinct_other_parent_half_counts(self):
        records=[
            {"horse_id":"A","sire_id":"S","dam_id":"D"},
            {"horse_id":"B","sire_id":"S","dam_id":"D"},
            {"horse_id":"C","sire_id":"S","dam_id":"D2"},
            {"horse_id":"E","sire_id":"S2","dam_id":"D"},
        ]
        graph=RegistryPedigree(records)
        stats,aux=counts(graph,sorted(graph.recorded))
        self.assertEqual(stats["full_sibling_pairs_both_verified_parents"],1)
        self.assertEqual(stats["confirmed_paternal_half_pairs_both_dams_known_distinct"],2)
        self.assertEqual(stats["confirmed_maternal_half_pairs_both_sires_known_distinct"],2)
        with tempfile.TemporaryDirectory() as d:
            report=per_horse(graph,sorted(graph.recorded),aux,Path(d)/"detail.csv")
            rows=list(csv.DictReader((Path(d)/"detail.csv").open()))
        a=next(x for x in rows if x["horse_id"]=="A")
        self.assertEqual(int(a["full_siblings_documented"]),1)
        self.assertEqual(int(a["paternal_half_confirmed"]),1)
        self.assertEqual(int(a["maternal_half_confirmed"]),1)
        self.assertEqual(report["partial_F_positive_horses"],0)

    def test_invalid_loops_and_duplicates_rejected(self):
        with self.assertRaisesRegex(ValueError,"CYCLE"):
            RegistryPedigree([
                {"horse_id":"A","sire_id":"B","dam_id":""},
                {"horse_id":"B","sire_id":"A","dam_id":""},
            ])
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            RegistryPedigree([
                {"horse_id":"A","sire_id":"","dam_id":""},
                {"horse_id":"A","sire_id":"","dam_id":""},
            ])

    def test_large_paternal_sib_group_is_aggregated_not_quadratic(self):
        n=3000
        rows=[
            {"horse_id":f"H{i:05d}","sire_id":"S","dam_id":""}
            for i in range(n)
        ]
        graph=RegistryPedigree(rows)
        stats,_=counts(graph,sorted(graph.recorded))
        self.assertEqual(stats["target_horses"],n)
        self.assertEqual(stats["shared_sire_target_pairs_including_unknown_other_parent"],
                         n*(n-1)//2)
        self.assertEqual(stats["confirmed_paternal_half_pairs_both_dams_known_distinct"],0)
        self.assertEqual(stats["linked_parent_placeholders_not_in_source"],1)
        self.assertTrue(stats["all_pair_dense_matrix_NOT_computed"])

    def test_explicit_cohort_never_automatically_includes_external_ancestors(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"all.csv"
            targets=Path(d)/"targets.csv"
            save(path,[
                {"horse_id":"FOREIGN-S","sire_id":"","dam_id":""},
                {"horse_id":"JP-A","sire_id":"FOREIGN-S","dam_id":""},
                {"horse_id":"JP-B","sire_id":"FOREIGN-S","dam_id":""},
            ],["horse_id","sire_id","dam_id"])
            save(targets,[{"horse_id":"JP-A"},{"horse_id":"JP-B"}],["horse_id"])
            rep=analyze(path,target_file=targets)
        self.assertEqual(rep["statistics"]["target_horses"],2)
        self.assertEqual(rep["statistics"]["pedigree_record_rows"],3)
        self.assertEqual(rep["statistics"]["shared_sire_target_pairs_including_unknown_other_parent"],1)
        self.assertTrue(rep["target_cohort_explicit"])


if __name__ == "__main__":
    unittest.main()
