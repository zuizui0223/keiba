"""Strict morning-source drift categorization against already captured official cards."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.ticket_forward_nov23_morning_diff import compare

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/"docs/evidence/ticket-forward-20261123-program-staging.json"
PREVIOUS=ROOT/"docs/evidence/ticket-forward-20261123-jra-card-numbered-rows-20261122.json"


def fixture():
    staged=json.loads(STAGE.read_text(encoding="utf-8"))
    older=json.loads(PREVIOUS.read_text(encoding="utf-8"))
    current={
        "target_date":"2026-11-23",
        "races":[{
            "race_id":r["race_id"],
            "parse_status":"OFFICIAL_NUMBER_SEQUENCE_EXTRACTED",
            "strict_numbered_horse_rows":r["numbered_card_rows"],
            "raw_page_sha256":r["raw_page_sha256"],
        } for r in older["races"]],
    }
    odds={
        "date":"2026-11-23","page_count":2,
        "source_pages":{
            "win_place":{
                "status":"READ_ONLY_ODDS_STRUCTURE_NOT_FROZEN",
                "upstream_updated_at_jst_detected":["2026-11-23T05:45:00+09:00"],
                "num_html_tables":2,"sha256":"a"*64,"observed_at_utc":"2026-11-22T22:35:00+00:00",
            },
            "wide":{"status":"HOLD_ODDS_SOURCE_UNAVAILABLE_OR_UNRECOGNIZED"},
        },
    }
    return older,current,staged,odds


class MorningEvidenceTests(unittest.TestCase):
    def test_no_invented_source_drift_and_not_frozen(self):
        old,new,stage,odds=fixture()
        o=compare(old,new,stage,odds)
        self.assertEqual(o["status"],"MORNING_SOURCE_DRIFT_NOT_PROSPECTIVE_DAY_SEAL")
        self.assertEqual(o["morning_official_numbered_card_count"],24)
        self.assertEqual(o["numbered_count_changes"],[])
        self.assertEqual(o["changed_page_sha256_race_ids"],[])
        self.assertFalse(o["formal_pre_first_start_day_plan_sealed"])
        self.assertEqual(o["actual_forward_predictions"],0)
        self.assertEqual(o["early_market_source_readiness"]["wide"]["updated_at"],[])

    def test_change_in_count_distinguished_from_hash_only(self):
        old,new,stage,odds=fixture()
        new["races"][0]["strict_numbered_horse_rows"]-=1
        new["races"][1]["raw_page_sha256"]="f"*64
        out=compare(old,new,stage,odds)
        self.assertEqual(len(out["numbered_count_changes"]),1)
        self.assertEqual(len(out["changed_page_sha256_race_ids"]),1)
        self.assertEqual(out["changed_page_sha256_race_ids"][0],new["races"][1]["race_id"])
        self.assertFalse(out["official_active_scratch_status_verified"])

    def test_rejects_partial_day_or_date(self):
        old,new,stage,odds=fixture()
        new["races"].pop()
        with self.assertRaisesRegex(ValueError,"partial_or_wrong_day"):
            compare(old,new,stage,odds)
        old,new,stage,odds=fixture()
        odds["date"]="2026-10-18"
        with self.assertRaisesRegex(ValueError,"invalid_morning_comparison_source"):
            compare(old,new,stage,odds)

    def test_unparsable_card_excluded_without_inventing_row_count(self):
        old,new,stage,odds=fixture()
        new["races"][0]["parse_status"]="HOLD_CARD_FETCH_OR_PARSER"
        new["races"][0]["strict_numbered_horse_rows"]=None
        out=compare(old,new,stage,odds)
        self.assertEqual(len(out["unavailable_or_unparseable_races"]),1)
        self.assertEqual(out["morning_official_numbered_card_count"],23)
        self.assertEqual(out["actual_forward_predictions"],0)


if __name__=="__main__":
    unittest.main()
