"""Fictional-only triple-source 2026 identity / race denominator tests."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2026_triple_source import (
    event_key, match_hf_to_public_names, accepted_2026_races,
    MIN_HORSES, MIN_ROWS, MIN_DATES
)


def event(day, place, surface="turf"):
    return event_key(day,1600,surface,place)


class TripleSourceTests(unittest.TestCase):
    def test_two_pre2025_days_produce_ambiguous_name_free_identity(self):
        b={"A":("あかつき",{event("2023-04-01",1),event("2024-05-02",2)})}
        c={"あかつき":{event("2023-04-01",1),event("2024-05-02",2)}}
        link,qa=match_hf_to_public_names(b,c)
        self.assertEqual(link,{"あかつき":"A"})
        self.assertEqual(qa["two_day_horses"],1)

    def test_only_one_pre2025_date_is_not_identity(self):
        b={"A":("horse",{event("2023-04-01",1),event("2024-05-02",2)})}
        c={"horse":{event("2023-04-01",1),event("2024-05-02",3)}}
        link,qa=match_hf_to_public_names(b,c)
        self.assertFalse(link)
        self.assertEqual(qa["at_least_one_day"],1)

    def test_two_records_same_day_are_not_independent_anchors(self):
        b={"A":("horse",{event("2023-04-01",1),event("2023-04-01",2)})}
        c={"horse":{event("2023-04-01",1),event("2023-04-01",2)}}
        link,_=match_hf_to_public_names(b,c)
        self.assertFalse(link)

    def test_ambiguous_normalized_names_quarantined(self):
        b={
            "A":("horse",{event("2023-04-01",1),event("2024-05-02",2)}),
            "B":("horse",{event("2023-04-01",1),event("2024-05-02",2)})
        }
        c={"horse":{event("2023-04-01",1),event("2024-05-02",2)}}
        link,qa=match_hf_to_public_names(b,c)
        self.assertFalse(link)
        self.assertEqual(qa["ambiguous_normalized_names"],1)

    def test_surface_or_distance_conflict_blocks_event(self):
        a={event("2023-04-01",1)}
        b={event("2023-04-01",1,"dirt")}
        self.assertFalse(a.intersection(b))

    def test_two_clean_source_c_2026_races(self):
        data=[]
        for day,venue,race in [
            ("2026-03-01","東京","1"),("2026-03-08","京都","7")
        ]:
            for rank,name in [(1,"horsen1"),(2,"horsen2"),(3,"horsen3")]:
                data.append({
                    "year":2026,"day":pd.Timestamp(day),
                    "race_key":f"{day}|{venue}|{race}","rank":rank,
                    "normalized_name":name,"surf":"turf",
                    "distance":1600,"venue":venue
                })
        out,qa=accepted_2026_races(pd.DataFrame(data))
        self.assertEqual(qa["source_complete_races"],2)
        self.assertEqual(len(out),6)

    def test_incomplete_ranked_race_rejected(self):
        df=pd.DataFrame([
            {"year":2026,"day":pd.Timestamp("2026-01-01"),
             "race_key":"r","rank":1,"normalized_name":"a",
             "surf":"turf","distance":1600,"venue":"東京"},
            {"year":2026,"day":pd.Timestamp("2026-01-01"),
             "race_key":"r","rank":3,"normalized_name":"b",
             "surf":"turf","distance":1600,"venue":"東京"},
        ])
        out,qa=accepted_2026_races(df)
        self.assertTrue(out.empty)
        self.assertEqual(qa["incomplete_tied_or_gapped_results"],1)

    def test_duplicate_names_rejected_in_one_race(self):
        df=pd.DataFrame([
            {"year":2026,"day":pd.Timestamp("2026-01-01"),
             "race_key":"r","rank":1,"normalized_name":"horse",
             "surf":"turf","distance":1600,"venue":"東京"},
            {"year":2026,"day":pd.Timestamp("2026-01-01"),
             "race_key":"r","rank":2,"normalized_name":"horse",
             "surf":"turf","distance":1600,"venue":"東京"},
        ])
        out,qa=accepted_2026_races(df)
        self.assertTrue(out.empty)
        self.assertEqual(qa["duplicate_or_conflicting_race"],1)

    def test_future_2027_races_excluded(self):
        df=pd.DataFrame([
            {"year":2027,"day":pd.Timestamp("2027-01-01"),
             "race_key":"r","rank":1,"normalized_name":"a",
             "surf":"turf","distance":1600,"venue":"東京"},
            {"year":2027,"day":pd.Timestamp("2027-01-01"),
             "race_key":"r","rank":2,"normalized_name":"b",
             "surf":"turf","distance":1600,"venue":"東京"},
        ])
        out,_=accepted_2026_races(df)
        self.assertTrue(out.empty)

    def test_feasibility_gates_positive_and_conservative(self):
        self.assertGreaterEqual(MIN_HORSES,30)
        self.assertGreaterEqual(MIN_ROWS,100)
        self.assertGreaterEqual(MIN_DATES,30)

if __name__=="__main__":
    unittest.main()
