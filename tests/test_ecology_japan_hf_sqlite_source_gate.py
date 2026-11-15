"""Fictional horse histories; tests contain no real horse identities."""
import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_hf_sqlite_source_gate import parse_horse_history,matched_event_dates,normalize_date


def fixture_result(day="2022-01-01",finish=2,meters=1600):
    return ["R","01","0101","sun",1,meters,"good",16,3,57,500,0,finish,93,0,30,34,day]


class IndependentlySourcedHistoryTests(unittest.TestCase):
    def test_wrapped_sqlite_race_history(self):
        rec=fixture_result()
        self.assertEqual(parse_horse_history(json.dumps([[rec],{"meta":"x"}])),
                         [("20220101",2,1600)])

    def test_nonfinisher_is_not_fabricated_as_classified_rank(self):
        rec=fixture_result(finish="DNF")
        self.assertEqual(parse_horse_history(json.dumps([[rec]])),[])

    def test_two_independent_historical_dates_required(self):
        earlier={("20200101",1,1600),("20210101",2,1800)}
        self.assertEqual(matched_event_dates(earlier,[("20200101",1,1600)]*2),1)
        self.assertEqual(matched_event_dates(earlier,list(earlier)),2)

    def test_output_contains_no_names_or_raw_horse_ids(self):
        rec=fixture_result(day="2024-01-01",finish=1)
        self.assertEqual(parse_horse_history(json.dumps([[rec]]))[0][0],"20240101")
        self.assertIsNone(normalize_date("not a date"))

if __name__=="__main__":unittest.main()
