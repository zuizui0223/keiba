"""Synthetic cross-source event identity tests; no real runner rows."""
from __future__ import annotations
import sys
from pathlib import Path
import unittest
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_independent_source_gate import build_anchor_map


def old_rows():
    return pd.DataFrame([
      {"date":"2020-01-01","racecourse":"Tokyo","race_number":"1","track":"Turf","distance":"1600","place":"1","horse_name":"メイショウＡ","horse_id":"100"},
      {"date":"2021-01-02","racecourse":"Tokyo","race_number":"2","track":"Turf","distance":"1800","place":"2","horse_name":"メイショウＡ","horse_id":"100"},
      {"date":"2020-02-01","racecourse":"Kyoto","race_number":"1","track":"Dirt","distance":"1200","place":"1","horse_name":"シゲルB","horse_id":"200"},
      {"date":"2020-01-01","racecourse":"Tokyo","race_number":"1","track":"Turf","distance":"1600","place":"2","horse_name":"シゲルC","horse_id":"300"},
      {"date":"2021-01-02","racecourse":"Kyoto","race_number":"1","track":"Dirt","distance":"1200","place":"1","horse_name":"シゲルC","horse_id":"301"},
      {"date":"2021-01-02","racecourse":"Kyoto","race_number":"2","track":"Dirt","distance":"1200","place":"2","horse_name":"シゲルC","horse_id":"301"},
    ])


def new_rows():
    return pd.DataFrame([
      {"date":"2020-01-01","course":"東京","race":"1","surface":"芝","distance":"1600","finish":"1","horse":"メイショウA"},
      {"date":"2021-01-02","course":"東京","race":"2","surface":"芝","distance":"1800","finish":"2","horse":"メイショウA"},
      {"date":"2020-02-01","course":"京都","race":"1","surface":"ダート","distance":"1200","finish":"1","horse":"シゲルB"},
      {"date":"2020-01-01","course":"東京","race":"1","surface":"芝","distance":"1600","finish":"2","horse":"シゲルC"},
      {"date":"2021-01-02","course":"京都","race":"1","surface":"ダート","distance":"1200","finish":"1","horse":"シゲルC"},
      {"date":"2021-01-02","course":"京都","race":"2","surface":"ダート","distance":"1200","finish":"2","horse":"シゲルC"},
      {"date":"2022-03-01","course":"東京","race":"3","surface":"芝","distance":"1400","finish":"3","horse":"メイショウA"},
      {"date":"2023-03-01","course":"東京","race":"4","surface":"芝","distance":"1400","finish":"1","horse":"シゲルB"},
      {"date":"2023-03-01","course":"東京","race":"4","surface":"芝","distance":"1400","finish":"2","horse":"シゲルC"},
    ])


class IndependentSourceGateTests(unittest.TestCase):
    def test_two_independent_dates_required(self):
        mapping, report = build_anchor_map(old_rows(),new_rows())
        self.assertEqual(mapping, {"メイショウa":"100"})
        self.assertEqual(report["source_anchor_horses_two_plus"],1)
        self.assertEqual(report["future_2022_2025"]["anchored_rows"],1)
        self.assertEqual(report["future_2022_2025"]["distinct_anchored_horses"],1)
        self.assertEqual(report["future_2022_2025"]["total_rows_with_valid_keys"],3)

    def test_future_outcomes_cannot_change_identity_map(self):
        n=new_rows()
        original,_=build_anchor_map(old_rows(),n)
        n.loc[n.date>="2022","finish"]="1"
        altered,_=build_anchor_map(old_rows(),n)
        self.assertEqual(original,altered)

    def test_pre_2022_rank_mismatch_invalidates_an_anchor(self):
        n=new_rows()
        n.loc[n.date=="2020-01-01","finish"]="9"
        mapping,_=build_anchor_map(old_rows(),n)
        self.assertEqual(mapping,{})

    def test_duplicate_horse_names_with_different_ids_quarantined(self):
        o=old_rows()
        o.loc[o.horse_id=="200","horse_name"]="メイショウA"
        mapping,report=build_anchor_map(o,new_rows())
        self.assertEqual(mapping,{})
        self.assertGreater(report["source_old_names_with_conflicting_ids"],0)

    def test_only_post_2021_horse_is_not_falsely_linked(self):
        n=new_rows()
        n.loc[len(n)]=["2024-01-01","東京","1","芝","1600","1","ニュー馬"]
        mapping,report=build_anchor_map(old_rows(),n)
        self.assertNotIn("ニュー馬",mapping)
        self.assertEqual(report["future_2022_2025"]["anchored_rows"],1)

    def test_2026_records_are_excluded_from_2022_2025_window(self):
        n=new_rows()
        n.loc[len(n)]=["2026-04-01","東京","1","芝","1600","1","メイショウA"]
        _,report=build_anchor_map(old_rows(),n)
        self.assertEqual(report["future_2022_2025"]["anchored_rows"],1)
        self.assertEqual(report["source_new_year_counts"]["2026"],1)

    def test_non_integer_finishing_places_are_not_id_anchors(self):
        n=new_rows()
        n.loc[n.date=="2020-01-01","finish"]="1.5"
        mapping,_=build_anchor_map(old_rows(),n)
        self.assertEqual(mapping,{})


if __name__=="__main__":
    unittest.main()
