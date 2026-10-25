#!/usr/bin/env python3
"""Private capture -> locked card -> PR22 freeze -> next WIN score, no result."""
from __future__ import annotations
import copy
from datetime import datetime,timedelta
from itertools import combinations
import json
from pathlib import Path
import sys
import tempfile
import unittest

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_operator_winwide_capture as m

RACE="SYN_CAPTURE_KYOTO_20261031_R11"
DATE="2026-10-31"
PROVIDER="TEST_MANUAL_EXPORT_SOURCE"
SLOT="2026-10-31|京都|ファンタジーS"


def card():
    return {
        "schema":m.CARD_SCHEMA,
        "slot_id":SLOT,
        "race_id":RACE,
        "provider":PROVIDER,
        "race_number":11,
        "scheduled_post_jst":DATE+"T15:45:00+09:00",
        "race_distance_m":1400,
        "horse_numbers":list(range(1,7)),
        "source_card_url":"https://example.org/testing-only/card",
        "source_card_published_at_jst":DATE+"T09:10:00+09:00",
        "source_card_received_at_jst":DATE+"T09:40:00+09:00",
        "declared_final_entrant_list":True,
        "rights_reviewed_by_operator":False,
        "provenance":"synthetic_test",
    }


def win(hour,minute=0,scale=1.0):
    return {
        "schema":m.CAPTURE_SCHEMA,
        "race_id":RACE,
        "provider":PROVIDER,
        "market":"win",
        "source_updated_at_jst":DATE+f"T{hour:02d}:{minute:02d}:00+09:00",
        "source_url":"https://example.org/testing-only/win",
        "source_clock_declared_verified":True,
        "rights_reviewed_by_operator":False,
        "provenance":"synthetic_test",
        "odds_by_horse_number":{
            str(i):float((2*i+2)*(scale if i%2 else 1/scale))
            for i in range(1,7)},
    }


def wide(hour=11,minute=0):
    return {
        "schema":m.CAPTURE_SCHEMA,
        "race_id":RACE,
        "provider":PROVIDER,
        "market":"wide",
        "source_updated_at_jst":DATE+f"T{hour:02d}:{minute:02d}:00+09:00",
        "source_url":"https://example.org/testing-only/wide",
        "source_clock_declared_verified":True,
        "rights_reviewed_by_operator":False,
        "provenance":"synthetic_test",
        "pairs":[
            {"selection":[i,j],
             "odds_low":float(2+i+j),
             "odds_high":float(2+i+j+.5)}
            for i,j in combinations(range(1,7),2)
        ],
    }


@unittest.skipIf(np is None,"NumPy installed in dedicated physical-model CI")
class ManualCaptureChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)/"private"/"samples"

    def write(self,source,ts):
        return m.append_capture(self.dir,source,captured_at_jst=DATE+ts+"+09:00")

    def first_three(self):
        self.write(win(10), "T10:02:00")
        self.write(win(11,scale=1.1),"T11:01:00")
        self.write(wide(),"T11:02:00")

    def test_ledger_one_event_per_unique_published_market_update_and_sha_chain(self):
        self.first_three()
        e=m._read_ledger(self.dir)
        self.assertEqual(len(e),3)
        self.assertEqual(e[0]["previous_event_sha256"],"0"*64)
        self.assertEqual(e[1]["previous_event_sha256"],e[0]["event_sha256"])
        self.assertEqual(e[2]["previous_event_sha256"],e[1]["event_sha256"])
        self.assertEqual(len({e1["event_sha256"] for e1 in e}),3)
        for item in e:
            self.assertGreaterEqual(
                m._aware(item["captured_at_jst"]),
                m._aware(item["captured_source"]["source_updated_at_jst"]))

    def test_exact_local_first_three_to_integrated_physical_market_freeze(self):
        self.first_three()
        produced=m.freeze_private_from_ledger(
            self.dir,card(),freeze_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=50,horse_seed=43)
        f=produced["freeze"]
        self.assertEqual(produced["status"],
            "LOCAL_CAPTURE_TO_PR22_SHA_FREEZE_NOT_GITHUB_PRETARGET_PROOF")
        self.assertFalse(produced["remote_sha_comment_submitted"])
        p=f["payload"]
        self.assertEqual(len(p["candidate_predictions"]),12)
        self.assertEqual(p["horse_numbers"],list(range(1,7)))
        self.assertEqual(p["target_horizon_minutes"],15)
        self.assertEqual(p["target_window_minutes"],5)
        self.assertEqual(p["next_quote_min_published_at"],
                         DATE+"T11:15:00+09:00")
        self.assertEqual(p["next_quote_max_published_at"],
                         DATE+"T11:20:00+09:00")
        self.assertFalse(p["external_GitHub_server_preseal_verified"])
        self.assertEqual(p["source_provenance"],"synthetic_test")
        self.assertEqual(p["middle_WIDE_quote_received_at"],
                         DATE+"T11:02:00+09:00")
        self.assertAlmostEqual(sum(v["p"] for v in
            p["candidate_predictions"]["mid_WIN_persistence"]),1,places=12)

    def test_score_uses_separate_new_WIN_target_and_only_locally(self):
        self.first_three()
        f=m.freeze_private_from_ledger(
            self.dir,card(),freeze_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=50,horse_seed=43)["freeze"]
        # The target is received AFTER model freeze, not in its features.
        self.write(win(11,17,scale=1.3),"T11:18:00")
        out=m.score_private_from_ledger(
            self.dir,f,operator_declares_complete=True,
            scoring_at_jst=DATE+"T11:19:00+09:00")
        self.assertFalse(out["source_capture_stream_attested_independently"])
        scored=out["local_operator_capture_score"]
        self.assertEqual(scored["n_horses"],6)
        self.assertEqual(scored["status"],"LOCAL_SOURCE_SCOPED_NEXT_MARKET_SCORE_NOT_PROSPECTIVE_VERIFIED")
        self.assertEqual(scored["selected_first_eligible_source_published_at"],
                         DATE+"T11:17:00+09:00")
        self.assertEqual(len(scored["all_model_scores"]),12)
        self.assertFalse(scored["external_preseal_authenticated"])
        with self.assertRaisesRegex(ValueError,"OPERATOR_DID_NOT_DECLARED"):
            m.score_private_from_ledger(self.dir,f,operator_declares_complete=False)

    def test_alternative_published_target_not_substituted_when_window_missing(self):
        self.first_three()
        f=m.freeze_private_from_ledger(
            self.dir,card(),freeze_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=40)["freeze"]
        self.write(win(11,24,scale=1.12),"T11:25:00")
        report=m.score_private_from_ledger(
            self.dir,f,operator_declares_complete=True,
            scoring_at_jst=DATE+"T11:26:00+09:00")
        self.assertEqual(report["local_operator_capture_score"]["status"],
            "HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW")
        self.assertFalse(report["source_capture_stream_attested_independently"])

    def test_source_mutation_after_capture_invalidates_local_chain(self):
        self.first_three()
        first=sorted(self.dir.glob("*.json"))[0]
        d=json.loads(first.read_text(encoding="utf-8"))
        d["captured_source"]["odds_by_horse_number"]["1"]=99.
        first.write_text(json.dumps(d),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"HASH_OR_FILENAME"):
            m._read_ledger(self.dir)

    def test_duplicate_market_and_source_timestamp_never_appended(self):
        self.write(win(10),"T10:02:00")
        with self.assertRaisesRegex(ValueError,"DUPLICATE_SOURCE_UPDATE"):
            self.write(win(10),"T10:03:00")
        self.assertEqual(len(m._read_ledger(self.dir)),1)

    def test_invalid_capture_rights_future_clock_and_nonhttps_rejected(self):
        for case in ("future","rights","http","extra","mixed","duplicate_pairs"):
            with self.subTest(case=case):
                s=wide() if case=="duplicate_pairs" else win(10)
                if case=="future":
                    s["source_updated_at_jst"]=DATE+"T10:04:00+09:00"
                elif case=="rights":
                    s["rights_reviewed_by_operator"]=True
                elif case=="http":
                    s["source_url"]="http://example.org/not-https"
                elif case=="extra":
                    s["actual_winner"]=3
                elif case=="mixed":
                    s["market"]="place"
                elif case=="duplicate_pairs":
                    s["pairs"][1]=copy.deepcopy(s["pairs"][0])
                with self.assertRaises(ValueError):
                    self.write(s,"T10:03:00")

    def test_missing_half_WIDE_and_wrong_roster_halt_before_frozen_models(self):
        self.first_three()
        w=sorted(self.dir.glob("*.json"))[-1]
        data=json.loads(w.read_text(encoding="utf-8"))
        self.assertEqual(data["captured_source"]["market"],"wide")
        # Independent second ledger with incomplete WIDE is locally
        # captured but must never create a PR22 feature.
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"private"/"missing"
            m.append_capture(path,win(10),captured_at_jst=DATE+"T10:02:00+09:00")
            m.append_capture(path,win(11,scale=1.1),captured_at_jst=DATE+"T11:01:00+09:00")
            partial=wide()
            partial["pairs"].pop()
            m.append_capture(path,partial,captured_at_jst=DATE+"T11:02:00+09:00")
            with self.assertRaisesRegex(ValueError,"NOT_ALL_PAIRS"):
                m.prepare_feature_from_ledger(
                    path,card(),freeze_at_jst=DATE+"T11:03:00+09:00")

    def test_same_provider_minute_and_too_late_local_freeze_guard(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"private"/"unmatched"
            m.append_capture(p,win(10),captured_at_jst=DATE+"T10:02:00+09:00")
            m.append_capture(p,win(11),captured_at_jst=DATE+"T11:01:00+09:00")
            m.append_capture(p,wide(11,1),captured_at_jst=DATE+"T11:02:00+09:00")
            with self.assertRaisesRegex(ValueError,"SAME_SOURCE_MINUTE"):
                m.prepare_feature_from_ledger(
                    p,card(),freeze_at_jst=DATE+"T11:03:00+09:00")
        self.first_three()
        with self.assertRaisesRegex(ValueError,"TOO_LATE"):
            m.prepare_feature_from_ledger(
                self.dir,card(),freeze_at_jst=DATE+"T11:15:00+09:00")

    def test_first_complete_eligible_market_triple_cannot_be_selected_posthoc(self):
        self.first_three()
        self.write(win(11,4,scale=1.2),"T11:05:00")
        self.write(wide(11,4),"T11:06:00")
        frozen=m.prepare_feature_from_ledger(
            self.dir,card(),freeze_at_jst=DATE+"T11:08:00+09:00")
        self.assertEqual(
            frozen["middle_win"]["source_updated_at_jst"],
            DATE+"T11:00:00+09:00")
        self.assertEqual(
            frozen["middle_wide"]["source_updated_at_jst"],
            DATE+"T11:00:00+09:00")

    def test_not_final_card_or_unregistered_slot_cannot_support_real_capture(self):
        self.first_three()
        no=card()
        no["declared_final_entrant_list"]=False
        with self.assertRaisesRegex(ValueError,"NOT_DECLARED_FINAL"):
            m.prepare_feature_from_ledger(self.dir,no,
                freeze_at_jst=DATE+"T11:03:00+09:00")
        no=card()
        no["slot_id"]="2026-10-31|京都|OTHER"
        with self.assertRaisesRegex(ValueError,"UNREGISTERED"):
            m.prepare_feature_from_ledger(self.dir,no,
                freeze_at_jst=DATE+"T11:03:00+09:00")

    def test_predeclared_private_outputs_do_not_overwrite_source_or_freeze(self):
        fn=self.dir/"local_freeze.json"
        m._write_new_private(fn,{"status":"synthetic_local"})
        with self.assertRaises(FileExistsError):
            m._write_new_private(fn,{"status":"changed"})
        with self.assertRaisesRegex(ValueError,"GITIGNORED_PRIVATE"):
            m._write_new_private(Path(self.tmp.name)/"outside.json",{})


if __name__=="__main__":
    unittest.main()
