"""Invented JRA-VAN TARGET CSV namespace and missing-data tests (no real rows)."""
from __future__ import annotations
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_jravan_blood_breeding_id_bridge import transform
from ecology_japan_registry_pedigree import RegistryPedigree,read_rows


HEADER=["馬名","血統登録番号","繁殖登録番号","父繁殖登録番号","母繁殖登録番号"]


def write_csv(path,rows,encoding="cp932",headers=HEADER):
    with path.open("w",encoding=encoding,newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=headers)
        writer.writeheader();writer.writerows(rows)


def data():
    return [
        dict(zip(HEADER,("父馬","0000002002","B-020","",""))),
        dict(zip(HEADER,("母馬","0000003003","B-030","",""))),
        dict(zip(HEADER,("子馬甲","0000001001","B-001","B-020","B-030"))),
        dict(zip(HEADER,("子馬乙","0000001004","","B-020","B-030"))),
        dict(zip(HEADER,("輸入馬","0000001005","","B-040",""))),
    ]


class JRAVANNamespaceTests(unittest.TestCase):
    def test_parent_join_uses_breeding_registration_not_same_string(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"target.csv";out=Path(td)/"private.csv"
            write_csv(src,data())
            result=transform(src,out)
            ped=RegistryPedigree(read_rows(out))
            self.assertEqual(result["target_horses"],5)
            self.assertEqual(result["input_encoding"],"cp932")
            self.assertEqual(ped.recorded["H:0000001001"],
                             ("H:0000002002","H:0000003003"))
            self.assertEqual(ped.recorded["H:0000001005"],("B:B-040",None))
            self.assertAlmostEqual(ped.a("H:0000001001","H:0000001004"),.5)
            self.assertEqual(result["parent_missing_or_unmatched"]["sire_not_joined_to_registered_horse"],1)
            self.assertFalse(result["cross_registry_name_matching_performed"])

    def test_explicit_target_ids_subset_excludes_breeding_only_horses(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"target.csv";out=Path(td)/"private.csv";targets=Path(td)/"starts.csv"
            write_csv(src,data())
            write_csv(targets,[{"血統登録番号":"0000001001"},{"血統登録番号":"0000001004"}],
                      headers=["血統登録番号"])
            result=transform(src,out,target_ids=targets)
            self.assertTrue(result["explicit_target_cohort"])
            self.assertEqual(result["target_horses"],2)

    def test_conflicting_breeding_id_rejected_not_same_name_heuristic(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"target.csv";out=Path(td)/"private.csv"
            dat=data()
            dat[1]["繁殖登録番号"]="B-020"  # two blood IDs claim one breeding ID
            write_csv(src,dat)
            with self.assertRaisesRegex(ValueError,"LINKS_MULTIPLE_BLOOD_IDS"):
                transform(src,out)

    def test_bad_parent_and_duplicate_conflict_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"target.csv";out=Path(td)/"private.csv"
            dat=data()
            dat[2]["父繁殖登録番号"]="B-001"
            write_csv(src,dat)
            with self.assertRaisesRegex(ValueError,"CONFLICTING_SELF"):
                transform(src,out)
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"target.csv";out=Path(td)/"private.csv"
            dat=data()
            dat.append({**dat[2],"父繁殖登録番号":"B-050"})
            write_csv(src,dat)
            with self.assertRaisesRegex(ValueError,"INCONSISTENT_DUPLICATE"):
                transform(src,out)


if __name__=="__main__":
    unittest.main()
