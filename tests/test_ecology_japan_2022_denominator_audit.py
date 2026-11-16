"""Strict denominator audit synthetic tests only; never requires original race data."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_denominator_audit import (
    decode_race_horses, audit_race_entries
)

def race(horses, wrap=True):
    rows=[[str(hid),rank,1,1,55,490,0,97,35,0,"J1"]
          for hid,rank in horses]
    return json.dumps([rows] if wrap else rows)


class DenominatorAuditTests(unittest.TestCase):
    def test_source_outer_container_and_unwrapped_rows(self):
        for wrap in (True, False):
            v, status=decode_race_horses(race([("a",1),("b",2)],wrap))
            self.assertEqual(status,"OK")
            self.assertEqual(len(v),2)

    def test_strict_complete_all_classified_and_matches_declared(self):
        record, lookup=audit_race_entries(
            race([("h1",1),("h2",2),("h3",3)]),3
        )
        self.assertEqual(record["status"],"STRICT_COMPLETE_CLASSIFIED_RACE")
        self.assertEqual(record["classified_n"],3)
        self.assertEqual(lookup["h2"],2)

    def test_proxy_two_finishers_but_three_declared(self):
        record,_=audit_race_entries(
            race([("h1",1),("h2",2)]),3
        )
        self.assertEqual(record["status"],"CLASSIFIED_PROXY_INCOMPLETE_DECLARED")
        self.assertEqual(record["classified_n"],2)

    def test_proxy_rank_zero_counted_as_unclassified(self):
        record,_=audit_race_entries(
            race([("h1",1),("h2",2),("h3",0)]),3
        )
        self.assertEqual(record["status"],"CLASSIFIED_PROXY_INCOMPLETE_DECLARED")
        self.assertEqual(record["unclassified_rank_count"],1)

    def test_tied_and_gapped_ranks_never_pass(self):
        t,_=audit_race_entries(race([("h1",1),("h2",1)]),2)
        self.assertEqual(t["status"],"TIED_OR_DUPLICATED_RANKS")
        g,_=audit_race_entries(race([("h1",1),("h2",3)]),3)
        self.assertEqual(g["status"],"GAPPED_CLASSIFIED_RANKS")

    def test_race_horse_ids_must_be_unique(self):
        r,_=audit_race_entries(race([("x",1),("x",2)]),2)
        self.assertEqual(r["status"],"DUPLICATE_SOURCE_HORSE_ID")

    def test_no_false_full_when_declared_differs(self):
        r,_=audit_race_entries(race([("h1",1),("h2",2),("h3",3)]),2)
        self.assertEqual(r["status"],"ENTRY_COUNT_ABOVE_DECLARED")

    def test_bad_json_does_not_turn_into_valid_race(self):
        r,_=audit_race_entries("NOT_JSON",3)
        self.assertEqual(r["status"],"INVALID_RACE_HORSE_JSON")

    def test_non_integer_rank_rejected_not_rounded(self):
        r,_=audit_race_entries(race([("a",1),("b",2.5)]),2)
        self.assertEqual(r["status"],"INVALID_CLASSIFIED_RANK")

    def test_fewer_than_two_ranked_holds(self):
        r,_=audit_race_entries(race([("a",1),("b",0)]),2)
        self.assertEqual(r["status"],"TOO_FEW_OR_OUTSIDE_CLASSIFIED_RANKS")


if __name__=="__main__":
    unittest.main()
