#!/usr/bin/env python3
"""Time-stamped official-like normalized odds source gate; synthetic fixtures."""
import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_local_timeseries_preflight import (
    SCHEMA, STATUS_READY_SYN, STATUS_HOLD, audit, race_preflight,
    synthetic_demo,
)


class PrivateOddsPanelPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example=synthetic_demo(seed=123)

    def test_full_synthetic_60_races_ten_dates(self):
        r=audit(self.example)
        self.assertEqual(r["status"],STATUS_READY_SYN)
        self.assertEqual(r["unique_race_count"],60)
        self.assertEqual(r["distinct_meeting_dates"],10)
        self.assertEqual(r["full_prestart_verified_races"],60)
        self.assertEqual(r["raw_snapshots_in_input"],180)
        self.assertEqual(r["aggregate_passing_market_motion"]
                         ["total_horse_entries_in_passing_races"],720)
        self.assertFalse(r["real_future_race_win_and_top3_skill_estimated"])
        self.assertTrue(r["original_record_types_and_bytes_never_exported"])

    def test_too_few_races_holds_not_false_positive_skill(self):
        s=copy.deepcopy(self.example)
        s["races"]=s["races"][:6]
        v=audit(s)
        self.assertEqual(v["status"],STATUS_HOLD)
        self.assertEqual(v["distinct_meeting_dates"],1)
        self.assertEqual(v["full_prestart_verified_races"],6)

    def test_no_producer_clock_does_not_backfill_receipt_clock(self):
        s=copy.deepcopy(self.example)
        s["races"][0]["snapshots"][1]["producer_clock_verified"]=False
        r=audit(s)
        self.assertEqual(r["status"],STATUS_HOLD)
        self.assertEqual(r["full_prestart_verified_races"],59)
        self.assertEqual(r["failure_status_counts"],{
            "HOLD_SOURCE_CLOCKS_NOT_VERIFIED":1})

    def test_clock_order_and_late_snapshot_hard_fail(self):
        s=copy.deepcopy(self.example)
        s["races"][0]["snapshots"][1]["producer_quote_updated_at_jst"]=(
            "2026-01-01T13:30:00+09:00")
        with self.assertRaisesRegex(ValueError,"HOLD_PRESTART_PUBLICATION_TIME"):
            audit(s)
        s=copy.deepcopy(self.example)
        s["races"][0]["snapshots"][1]["producer_quote_updated_at_jst"]=(
            s["races"][0]["snapshots"][0]["producer_quote_updated_at_jst"])
        with self.assertRaisesRegex(ValueError,"HOLD_NONMONOTONE"):
            audit(s)
        s=copy.deepcopy(self.example)
        s["races"][0]["snapshots"][0]["received_at_jst"]=(
            "2025-12-30T12:00:00+09:00")
        with self.assertRaisesRegex(ValueError,"HOLD_PRESTART_PUBLICATION_TIME"):
            audit(s)

    def test_roster_changed_is_hold_not_imputation(self):
        s=copy.deepcopy(self.example)
        del s["races"][0]["snapshots"][1]["win_odds_by_horse"]["1"]
        r=audit(s)
        self.assertEqual(r["status"],STATUS_HOLD)
        self.assertEqual(r["failure_status_counts"],{"HOLD_HORSE_ROSTER_CHANGED":1})

    def test_wrong_market_and_duplicate_or_invalid_odds_rejected(self):
        s=copy.deepcopy(self.example)
        s["races"][0]["snapshots"][0]["bet_type"]="wide"
        with self.assertRaisesRegex(ValueError,"HOLD_MIXED_BET_EVENT"):
            audit(s)
        s=copy.deepcopy(self.example)
        s["races"][0]["snapshots"][0]["win_odds_by_horse"]["1"]=0.9
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_WIN_ODDS"):
            audit(s)
        s=copy.deepcopy(self.example)
        s["races"][1]["race_id"]=s["races"][0]["race_id"]
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_RACE"):
            audit(s)

    def test_self_attested_local_input_has_no_verified_license_claim(self):
        s=copy.deepcopy(self.example)
        s["origin"]="local_operator_authorized_normalized_export"
        s["normalized_record_family"]="JV_TS_O1_authorized_local_normalization"
        with self.assertRaisesRegex(ValueError,"HOLD_RESEARCH_ACCESS_NOT_SELF_ATTESTED"):
            audit(s)
        s["operator_confirmed_research_access"]=True
        v=audit(s)
        self.assertTrue(v["status"].startswith("LOCAL_SELF_ATTESTED"))
        self.assertTrue(v["operator_research_license_attestation_is_not_independent_legal_verification"])
        s["raw_records_redistributable"]=True
        with self.assertRaisesRegex(ValueError,"HOLD_RAW_RECORD"):
            audit(s)

    def test_no_horse_names_or_raw_market_prices_are_released(self):
        v=audit(self.example)
        z=str(v)
        self.assertNotIn("win_odds_by_horse",z)
        self.assertNotIn("horse_name",z)
        self.assertNotIn("official_top3",z)
        self.assertTrue(all(x["features_or_verified_outcomes_used"] is False
                            for x in v["per_race_aggregate_only"]))


if __name__=="__main__":
    unittest.main()
