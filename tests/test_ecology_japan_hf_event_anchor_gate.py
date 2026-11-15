"""Synthetic data identity crosswalk guard: no real horse rows."""
import json
import sys
from pathlib import Path
import unittest
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_hf_event_anchor_gate import anchor_name_histories


def race(day,rank=1,distance=1600):
    return ["r","01","0101","sun",1,distance,"good",16,3,57,500,0,rank,93,0,30,34,day]


def old():
    return pd.DataFrame([
       {"horse_id":"old-a","horse_name":"メイショウＡ","date":"2020-01-01","place":"1","distance":"1600M"},
       {"horse_id":"old-a","horse_name":"メイショウＡ","date":"2021-01-01","place":"2","distance":"1800M"},
       {"horse_id":"old-b","horse_name":"サトノB","date":"2021-01-02","place":"1","distance":"1600M"},
    ])


def current():
    return [
      ("new-1","メイショウA",json.dumps([[race("2020-01-01"),race("2021-01-01",2,1800),race("2022-01-01"),race("2023-01-01",2,1800)]])),
      ("new-2","サトノB",json.dumps([[race("2021-01-02"),race("2022-01-01")]])),
    ]


class TrueHistoryAnchorTests(unittest.TestCase):
    def test_exact_two_day_corrob_returns_only_one_ID_pair(self):
        matched,report=anchor_name_histories(old(),current())
        self.assertEqual(matched,{"new-1":"old-a"})
        self.assertEqual(report["two_event_anchor_horses"],1)
        self.assertEqual(report["independent_future_rows_on_anchors"],2)
        self.assertEqual(report["future_by_year"],{"2022":1,"2023":1})

    def test_future_rank_change_never_changes_identity_map(self):
        rows=current()
        before,_=anchor_name_histories(old(),rows)
        updated=json.loads(rows[0][2])
        updated[0][-1][12]=9
        rows[0]=(rows[0][0],rows[0][1],json.dumps(updated))
        after,_=anchor_name_histories(old(),rows)
        self.assertEqual(before,after)

    def test_duplicate_same_date_does_not_count_as_two_matches(self):
        fake=[("new-1","メイショウA",json.dumps([[race("2020-01-01"),race("2020-01-01")]]))]
        matched,_=anchor_name_histories(old(),fake)
        self.assertEqual(matched,{})

    def test_second_source_colliding_names_rejected(self):
        rows=current()
        rows.append(("another-id",rows[0][1],rows[0][2]))
        matched,report=anchor_name_histories(old(),rows)
        self.assertEqual(matched,{})
        self.assertEqual(report["new_names_with_multiple_ids"],1)

    def test_source_shape_diagnostics_do_not_leak_names_or_ids(self):
        matched,report=anchor_name_histories(old(),current())
        probe=report["source_shape_probe"]
        self.assertGreaterEqual(probe["candidate_histories_with_parsed_races"],1)
        self.assertGreaterEqual(probe["candidate_histories_with_pre2022_parsed_races"],1)
        self.assertGreaterEqual(probe["candidate_pre2022_dates_matching_old"],1)
        self.assertNotIn("メイショウ",str(probe))
        self.assertNotIn("old-a",str(probe))
        self.assertNotIn("new-1",str(probe))

    def test_first_source_colliding_names_rejected(self):
        rows=old()
        rows.loc[len(rows)]=["different","メイショウA","2019-01-01","1","1600M"]
        matched,report=anchor_name_histories(rows,current())
        self.assertEqual(matched,{})
        self.assertEqual(report["old_names_with_multiple_ids"],1)


if __name__=="__main__":
    unittest.main()
