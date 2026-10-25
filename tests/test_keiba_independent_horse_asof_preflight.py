#!/usr/bin/env python3
"""Offline future as-of horse-source contract: clock/roster/rights/HOLD gates."""
from __future__ import annotations
import copy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
try:
    import numpy as np
except ImportError:
    np=None
if np is not None:
    import keiba_independent_horse_asof_preflight as m


def fixtures():
    market={
        "race_id":"RACE-TEST-26",
        "meeting_day":"2026-11-01",
        "race_no":7,
        "first_odds":{i:float(2+i*2) for i in range(1,7)},
        "last_odds":{i:float(2+i*2)*1.05 for i in range(1,7)},
        "initial_quote_at":"2026-11-01T12:00:00+09:00",
        "initial_quote_received_at_jst":"2026-11-01T12:02:00+09:00",
        "latest_quote_at":"2026-11-01T13:00:00+09:00",
        "latest_quote_received_at_jst":"2026-11-01T13:02:00+09:00",
        "local_forecast_generated_at_jst":"2026-11-01T13:05:00+09:00",
        "post_at":"2026-11-01T15:00:00+09:00",
    }
    snapshot={
        "schema":m.HISTORY_SCHEMA,
        "race_id":"RACE-TEST-26","target_date":"2026-11-01",
        "target_surface":"芝","distance_m":1200,
        "horses":[{
            "number":i,"name":f"HORSE{i}",
            "past_runs":[{"date":"2026-10-10","finish":i,
                          "distance_m":1200,"surface":"芝"}]
        }for i in range(1,7)],
    }
    def encode(z):
        return json.dumps(z,sort_keys=True,separators=(",",":")).encode()
    raw=encode(snapshot)
    receipt={
        "schema":m.RECEIPT_SCHEMA,
        "externally_attested":False,
        "operator_declares_rights_review":True,
        "original_source_sha256":sha256(raw).hexdigest(),
        "original_source_url":"https://example.org/horses/past-2026-11-01",
        "publisher_updated_at_jst":"2026-11-01T11:40:00+09:00",
        "source_received_at_jst":"2026-11-01T11:45:00+09:00",
        "declared_official_horse_names_by_number":{
            str(i):f"HORSE{i}" for i in range(1,7)},
    }
    return market,snapshot,raw,receipt,encode


@unittest.skipIf(np is None,"NumPy required")
class LocalAsOfTests(unittest.TestCase):
    def test_good_clock_source_only_local_status_not_external_proof(self):
        row,src,raw,rec,encode=fixtures()
        report=m.verify_offline_source(raw,rec,row)
        self.assertEqual(report["status"],m.STATUS)
        self.assertFalse(report["independent_external_time_receipt_verified"])
        self.assertTrue(report["not_an_authentic_prospective_forecast"])
        self.assertEqual(report["history_records_examined"],6)
        self.assertAlmostEqual(sum(report["horse_history_prior"]),1.0)
        self.assertEqual(report["first_market_horse_numbers"],list(range(1,7)))

    def test_source_after_initial_market_is_invalid_even_if_before_post(self):
        row,src,raw,rec,encode=fixtures()
        bad=copy.deepcopy(rec)
        bad["source_received_at_jst"]="2026-11-01T12:30:00+09:00"
        with self.assertRaisesRegex(ValueError,"TIME_TRAVEL"):
            m.verify_offline_source(raw,bad,row)

    def test_market_published_and_acquired_clocks_cannot_time_travel(self):
        row,src,raw,rec,encode=fixtures()
        for field,clock in (
            ("initial_quote_received_at_jst","2026-11-01T13:12:00+09:00"),
            ("latest_quote_received_at_jst","2026-11-01T14:56:00+09:00"),
            ("local_forecast_generated_at_jst","2026-11-01T14:59:00+09:00"),
        ):
            bad=copy.deepcopy(row)
            bad[field]=clock
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError,"TIME_TRAVEL"):
                    m.verify_offline_source(raw,rec,bad)

    def test_claimed_external_attestation_cannot_self_authorize(self):
        row,src,raw,rec,encode=fixtures()
        bad=copy.deepcopy(rec)
        bad["externally_attested"]=True
        with self.assertRaisesRegex(ValueError,"SELF_ASSERTED_EXTERNAL"):
            m.verify_offline_source(raw,bad,row)

    def test_bad_rights_or_unauthorized_source_is_rejected(self):
        row,src,raw,rec,encode=fixtures()
        bad=copy.deepcopy(rec)
        bad["operator_declares_rights_review"]=False
        with self.assertRaisesRegex(ValueError,"RIGHTS"):
            m.verify_offline_source(raw,bad,row)
        bad=copy.deepcopy(rec)
        bad["original_source_url"]="http://example.org/a"
        with self.assertRaisesRegex(ValueError,"HTTPS"):
            m.verify_offline_source(raw,bad,row)

    def test_sha_tampering_and_wrong_horse_crosswalk_fail(self):
        row,src,raw,rec,encode=fixtures()
        mutated=copy.deepcopy(src)
        mutated["horses"][0]["past_runs"][0]["finish"]=6
        with self.assertRaisesRegex(ValueError,"SHA256"):
            m.verify_offline_source(encode(mutated),rec,row)
        bad=copy.deepcopy(rec)
        bad["declared_official_horse_names_by_number"]["3"]="WRONG"
        with self.assertRaisesRegex(ValueError,"CROSSWALK"):
            m.verify_offline_source(raw,bad,row)

    def test_same_day_or_future_horse_record_cannot_be_feature(self):
        row,src,raw,rec,encode=fixtures()
        for date in ("2026-11-01","2026-11-02"):
            mutated=copy.deepcopy(src)
            mutated["horses"][0]["past_runs"][0]["date"]=date
            changed=encode(mutated)
            r=copy.deepcopy(rec)
            r["original_source_sha256"]=sha256(changed).hexdigest()
            with self.assertRaisesRegex(ValueError,"FUTURE_HORSE"):
                m.verify_offline_source(changed,r,row)

    def test_roster_and_model_clock_fail_closed(self):
        row,src,raw,rec,encode=fixtures()
        bad=copy.deepcopy(row)
        bad["last_odds"].pop(1)
        with self.assertRaisesRegex(ValueError,"FULL_FIELD"):
            m.verify_offline_source(raw,rec,bad)
        bad=copy.deepcopy(row)
        bad["latest_quote_at"]=bad["post_at"]
        with self.assertRaisesRegex(ValueError,"TOO_LATE"):
            m.verify_offline_source(raw,rec,bad)

    def test_future_model_demo_uses_real_market_q0_separate_horse_history(self):
        row,src,raw,rec,encode=fixtures()
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("NO_OUTCOME_ALLOWED")):
            out=m.local_demo_coupling(raw,rec,row,draws=60,seed=122)
        self.assertEqual(out["status"],m.STATUS)
        self.assertTrue(out["no_target_outcome_read"])
        self.assertEqual(out["external_timestamp_authentication"],"HOLD")
        self.assertEqual(out["horse_prior_source"],
                         "external_past_history_needs_source_clock")
        self.assertEqual(set(out["model_predicted_event_probs"]),{
            "horse_P9_weak","horse_SDE_weak","market_mixed",
            "market_threshold_mixed","observed_M0"})
        for p in out["model_predicted_event_probs"].values():
            self.assertAlmostEqual(sum(p["win"]),1.0,places=11)
            self.assertAlmostEqual(sum(p["top3"]),3.0,places=11)


if __name__=="__main__":
    unittest.main()
