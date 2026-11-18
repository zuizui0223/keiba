"""Fictional-only known-on audits: official 2027 private input contract."""
from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2027_official_knownon_preflight import (
    audit, local_jst, typed_id
)

START="2027-01-09T15:15:00+09:00"
CUTOFF="2027-01-08T18:00:00+09:00"
PREVIOUS="2026-12-24T15:30:00+09:00"
KNOWN="2026-12-24T17:00:00+09:00"
DELAYED="2027-01-09T17:00:00+09:00"


def input_data():
    entries=[]
    parents=[]
    for i in range(3):
        horse="H:"+str(100+i)
        entries.append({
            "race_id":"JRA:2027010901","horse_id":horse,
            "race_start_at_jst":START,"entry_known_at_jst":CUTOFF,
            "course_id":"KYOTO","surface":"turf","distance_m":"1600",
            "sex":"F" if i==2 else "M", "age":"5",
            "jockey_id":"J:"+str(i),"trainer_id":"T:"+str(i),
        })
        parents.append({
            "horse_id":horse,"sire_id":"B:77" if i<2 else "B:88",
            "dam_id":"B:"+str(i+1),"pedigree_master_known_at_jst":"2026-09-01T10:00:00+09:00",
        })
    history=[]
    for i in range(3):
        history.append({
            "race_id":"JRA:2026122401","horse_id":"H:"+str(100+i),
            "race_start_at_jst":PREVIOUS,"result_known_at_jst":KNOWN,
            "finish_rank":str(i+1),"classified_field_size":"3",
            "finish_status":"CLASSIFIED",
        })
    return entries,parents,history


class OfficialKnownOnTests(unittest.TestCase):
    def test_source_2027_preflight_accepts_typed_ids_without_predictions(self):
        e,p,h=input_data()
        a=audit(e,p,h)
        self.assertEqual(a["cohort"]["eligible_entered_horses"],3)
        self.assertEqual(a["historical_support"]["own_history_available"],3)
        self.assertEqual(a["historical_support"]["relatives_with_pretarget_history"],2)
        self.assertNotIn("H:100",str(a))
        self.assertEqual(a["next_gate"],"HOLD_ACTUAL_2027_OFFICIAL_RESULTS_AND_FROZEN_MODEL")

    def test_delayed_result_not_used_in_earlier_cutoff(self):
        e,p,h=input_data()
        h.append({
            "race_id":"JRA:2027010901","horse_id":"H:100",
            "race_start_at_jst":START,"result_known_at_jst":DELAYED,
            "finish_rank":"1","classified_field_size":"3",
            "finish_status":"CLASSIFIED",
        })
        a=audit(e,p,h)
        self.assertEqual(a["historical_support"]["pretarget_own_observations"],3)
        self.assertEqual(a["historical_support"]["future_or_delayed_own_results_excluded"],1)

    def test_absent_sire_must_not_be_a_family_label(self):
        e,p,h=input_data()
        for row in p:
            row["sire_id"]=""
        a=audit(e,p,h)
        self.assertEqual(a["historical_support"].get("relatives_with_pretarget_history",0),0)

    def test_parent_namespace_rejects_raw_name(self):
        e,p,h=input_data()
        p[0]["sire_id"]="Meisho Tabaru"
        with self.assertRaisesRegex(ValueError,"NAMESPACE"):
            audit(e,p,h)

    def test_disallow_same_horse_as_own_parent(self):
        e,p,h=input_data()
        p[0]["sire_id"]="H:100"
        with self.assertRaisesRegex(ValueError,"PEDIGREE"):
            audit(e,p,h)

    def test_disallow_parent_first_known_after_entry_cutoff(self):
        e,p,h=input_data()
        p[0]["pedigree_master_known_at_jst"]=START
        with self.assertRaisesRegex(ValueError,"PARENTS_NOT_KNOWN"):
            audit(e,p,h)

    def test_reject_duplicate_entered_horse(self):
        e,p,h=input_data()
        e.append(copy.deepcopy(e[0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE_RACE_HORSE"):
            audit(e,p,h)

    def test_entry_update_after_race_start_rejected(self):
        e,p,h=input_data()
        e[0]["entry_known_at_jst"]=DELAYED
        with self.assertRaisesRegex(ValueError,"ENTRY_SNAPSHOT_NOT_BEFORE"):
            audit(e,p,h)

    def test_result_publication_cannot_precede_race(self):
        e,p,h=input_data()
        h[0]["result_known_at_jst"]="2026-12-23T17:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"RESULT_KNOWN_BEFORE"):
            audit(e,p,h)

    def test_no_naive_timestamp_or_non_jst_timezone(self):
        for value in ("2027-01-09T15:15:00","2027-01-09T15:15:00+00:00"):
            with self.assertRaisesRegex(ValueError,"NOT_EXPLICIT_JST"):
                local_jst(value)

    def test_2026_target_race_is_not_in_frozen_2027_window(self):
        e,p,h=input_data()
        for row in e:
            row["race_start_at_jst"]="2026-10-01T15:00:00+09:00"
            row["entry_known_at_jst"]="2026-09-30T15:00:00+09:00"
        with self.assertRaisesRegex(ValueError,"OUTSIDE_FROZEN_2027"):
            audit(e,p,h)

    def test_same_parent_breeding_ids_and_blood_ids_never_equated(self):
        self.assertEqual(typed_id("B:123",("B:","H:")),"B:123")
        with self.assertRaisesRegex(ValueError,"NAMESPACE"):
            typed_id("B:123",("H:",))


if __name__=="__main__":
    unittest.main()
