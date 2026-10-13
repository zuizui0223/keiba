"""Hand-invented official-horse-ID crosswalk fixtures; no real individuals."""
from __future__ import annotations
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_official_id_crosswalk import (
    REQUIRED, audit, canon_name, official_roster_rows
)


def artificial_csv():
    return ("""Date,RaceNumber,11/10/2026 12:00:00 AM;FICTIONAL;Race 1;00:00:55.000;FAKE
11/10/2026,1,Alpha Horse;7;150;18.30;00:00:10.33;350;18.20;00:00:10.88
11/10/2026,1,Beta Horse;2;150;0;00:00:00.000;350;0;00:00:00.000
Date,RaceNumber,11/10/2026 12:00:00 AM;FICTIONAL;Race 2;00:00:57.000;FAKE
11/10/2026,2,Beta Horse;6;150;18.40;00:00:10.45;350;18.10;00:00:10.90
11/10/2026,2,Gamma Horse;4;150;18.60;00:00:10.45;350;18.50;00:00:10.80
""").encode("utf-8")


def roster():
    data=[
        ("1","FIRST-RACE","FAKE-A","Alpha Horse","started","finished"),
        ("1","FIRST-RACE","FAKE-B","Beta Horse","not_started","not_applicable"),
        ("2","SECOND-RACE","FAKE-B","Beta Horse","started","finished"),
        ("2","SECOND-RACE","FAKE-C","Gamma Horse","started","finished"),
    ]
    return [{
        "race_date":"2026-10-11","race_number":race,
        "official_race_id":rid,"official_horse_id":hid,
        "horse_name":name,"start_status":start,"finish_status":finish,
        "source_url":"https://example.org/fabricated-roster",
    } for race,rid,hid,name,start,finish in data]


def store_roster(tmp,rows):
    path=Path(tmp)/"invented-official-rows.csv"
    with path.open("w",newline="",encoding="utf-8") as fd:
        w=csv.DictWriter(fd,fieldnames=list(REQUIRED))
        w.writeheader();w.writerows(rows)
    return path


class OfficialIDCrosswalkTests(unittest.TestCase):
    def test_same_day_repeated_name_never_promoted_to_internal_id(self):
        with tempfile.TemporaryDirectory() as temp:
            official=official_roster_rows(store_roster(temp,roster()))
        result=audit(artificial_csv(),official)
        c=result["counts"]
        self.assertEqual(c["sectional_horse_rows"],4)
        self.assertEqual(c["same_day_names_in_multiple_race_headers"],1)
        self.assertEqual(c["blocked_same_day_duplicate_name"],2)
        self.assertEqual(c["unique_syntactic_official_name_matches"],2)
        self.assertEqual(c["matched_positive_gps"],2)
        self.assertTrue(result["ambiguous_identity_or_duplicate_contexts"])
        self.assertTrue(result["all_zero_gps_not_assumed_dnf"])
        self.assertTrue(result["unverified_name_and_number_were_not_upgraded_to_biological_ID"])
        self.assertNotIn("Alpha Horse",json.dumps(result))
        self.assertNotIn("FAKE-A",json.dumps(result))
        self.assertIn("HOLD",result["status"])

    def test_zero_sectional_matches_not_started_when_official_roster_says_so(self):
        # The zero GPS row has been moved into a single-race fixture.
        text=artificial_csv().decode("utf-8")
        text=text.split("Date,RaceNumber",2)
        only_race1=(text[0]+"Date,RaceNumber"+text[1]).encode("utf-8")
        subset=[row for row in roster() if row["race_number"]=="1"]
        with tempfile.TemporaryDirectory() as temp:
            official=official_roster_rows(store_roster(temp,subset))
        result=audit(only_race1,official)
        self.assertEqual(result["counts"]["matched_all_zero_gps"],1)
        self.assertEqual(result["counts"]["zero_gps_official_start_not_started"],1)
        self.assertEqual(result["counts"].get("match_official_finish_did_not_finish",0),0)
        self.assertFalse(result["ambiguous_identity_or_duplicate_contexts"])
        self.assertIn("HOLD",result["status"])

    def test_same_race_same_name_multiple_official_ids_is_not_auto_resolved(self):
        records=roster()
        records[0]["horse_name"]="Gamma Horse"
        records.append({
            **records[0],"official_horse_id":"DIFFERENT-GAMMA",
        })
        with tempfile.TemporaryDirectory() as temp:
            official=official_roster_rows(store_roster(temp,records))
        out=audit(artificial_csv(),official)
        self.assertGreater(out["counts"]["blocked_ambiguous_official_name_match"],0)
        self.assertTrue(out["ambiguous_identity_or_duplicate_contexts"])

    def test_invalid_roster_statuses_rejected(self):
        rows=roster()
        rows[0]["start_status"]="never-existed"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,"HOLD_ROSTER_PROVENANCE_OR_STATUS"):
                official_roster_rows(store_roster(temp,rows))

    def test_nonstarter_with_finish_contradiction_rejected(self):
        rows=roster()
        rows[1]["finish_status"]="finished"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,"HOLD_NONSTARTER_FINISH_STATUS"):
                official_roster_rows(store_roster(temp,rows))

    def test_no_invented_fuzzy_name_matches(self):
        rows=roster()
        rows[0]["horse_name"]="AlphaHorse"  # no space, must remain unmatched
        with tempfile.TemporaryDirectory() as temp:
            official=official_roster_rows(store_roster(temp,rows))
        out=audit(artificial_csv(),official)
        self.assertEqual(out["counts"]["not_matched_to_official_roster"],1)
        self.assertEqual(out["counts"]["unique_syntactic_official_name_matches"],1)

    def test_unicode_spaces_normalized_but_identity_not_validated(self):
        self.assertEqual(canon_name("  Alpha\u3000Horse  "), "alpha horse")
        self.assertNotEqual(canon_name("AlphaHorse"), "alpha horse")


if __name__=="__main__":
    unittest.main()
