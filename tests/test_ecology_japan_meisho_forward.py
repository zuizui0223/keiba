"""Synthetic-only tests for Japan Meisho name/owner/pedigree forecast channels."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from ecology_pedigree_forward import Pedigree
from ecology_pedigree_stress import fabricate
from ecology_japan_meisho_forward import (
    analyze, frozen_features, load_race_asof, choose_weights,
)


def fake_input(directory: str):
    x,p=fabricate(Path(directory),"family_signal",101)
    with x.open(encoding="utf-8") as stream:
        rows=list(csv.DictReader(stream))
    for r in rows:
        family=int(r["horse_id"].split("-")[2])
        r["horse_name"]=("メイショウ架空-" if family%2==0 else "架空馬-")+r["horse_id"]
        r["owner_id"]=r["trainer_id"]
        r["owner_known_on"]="2000-01-01"
    with x.open("w",encoding="utf-8",newline="") as output:
        writer=csv.DictWriter(output,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return x,p


class JapanMeishoForwardTests(unittest.TestCase):
    def test_name_owner_and_kin_evaluated_on_same_future_rows(self):
        with tempfile.TemporaryDirectory() as d:
            x,p=fake_input(d)
            result=analyze(x,p,min_horses=10)
        self.assertEqual(result["status"],
                         "EXPLORATORY_OUT_OF_TIME_NAME_OWNER_KIN_SCORE_NOT_CAUSAL")
        r=result["results"]["all"]
        self.assertTrue(r["same_heldout_rows_all_models"])
        self.assertEqual(set(r["equal_horse_weight_RMSE_seconds"]),{
            "M0","M_name","M_owner","M_kin","M_owner_plus_kin"})
        self.assertGreater(result["heldout_context_supported_horses"],10)
        self.assertGreater(result["heldout_named_meisho_horses"],0)
        self.assertGreater(result["heldout_horses_with_related_training_history"],0)
        self.assertTrue(result["not_a_genetic_causal_test_or_heritability"])
        self.assertNotIn("SYNTH-HORSE",str(result))

    def test_future_or_same_day_owner_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            x,p=fake_input(d)
            with x.open(encoding="utf-8") as fd:
                rows=list(csv.DictReader(fd))
            rows[0]["owner_known_on"]=rows[0]["race_date"]
            with x.open("w",encoding="utf-8",newline="") as fd:
                writer=csv.DictWriter(fd,fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError,"NOT_KNOWN_BEFORE_RACE_DATE"):
                load_race_asof(x)

    def test_name_prefix_not_owner_and_not_kin(self):
        c=("FICTION","150","1200","Good","SYNTH")
        individuals=[
            ("A","GROUP-A",True,10),
            ("B","GROUP-B",True,12),
            ("C","GROUP-A",False,11),
            ("D","GROUP-C",False,9),
        ]
        train=[{
            "context":c,"horse":h,"race":f"R-{h}","day":date(2026,1,1),
            "owner":owner,"meisho":prefix,"y":y
        } for h,owner,prefix,y in individuals]
        target={
            "context":c,"horse":"NEW","race":"R-NEW","day":date(2026,1,3),
            "owner":"GROUP-A","meisho":True,"y":10.5
        }
        r=frozen_features(train,[target],Pedigree({}))[0]
        self.assertTrue(r["name_exposed"])
        self.assertTrue(r["owner_exposed"])
        self.assertFalse(r["kin_exposed"])
        self.assertNotEqual(r["name"],r["owner"])
        self.assertEqual(r["kin"],0.0)

    def test_owner_labels_on_historical_rows_are_not_backfilled_from_future(self):
        c=("FICTION","150","1200","Good","SYNTH")
        train=[
            {"context":c,"horse":f"H{i}","race":f"R{i}","day":date(2026,1,1),
             "owner":("OLD" if i<2 else "OTHER"),"meisho":i%2==0,"y":10+i}
            for i in range(5)
        ]
        focal={"context":c,"horse":"F","race":"RF","day":date(2026,1,10),
               "owner":"NEW","meisho":True,"y":10}
        before=frozen_features(train,[focal],Pedigree({}))[0]
        self.assertFalse(before["owner_exposed"])
        changed=[dict(r) for r in train]
        changed[0]["owner"]="NEW"
        after=frozen_features(changed,[focal],Pedigree({}))[0]
        self.assertTrue(after["owner_exposed"])
        self.assertEqual(before["name"],after["name"])

    def test_inner_weights_include_exactly_five_predeclared_models(self):
        sample=[{
            "horse":f"H{i}","y":float(i),"base":0.0,
            "name":.1*i,"owner":.2*i,"kin":.3*i
        } for i in range(6)]
        weights=choose_weights(sample)
        self.assertEqual(set(weights),{
            "M0","M_name","M_owner","M_kin","M_owner_plus_kin"})
        self.assertEqual(weights["M0"],(0.0,0.0,0.0))


if __name__=="__main__":
    unittest.main()
