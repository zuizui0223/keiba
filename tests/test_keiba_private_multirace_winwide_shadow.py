#!/usr/bin/env python3
"""Private future WIN/WIDE freeze -> separate target -> grouped score QA."""
from __future__ import annotations

import copy
from datetime import datetime,timedelta
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_private_multirace_winwide_shadow as m


def source():
    field=list(range(1,7))
    first={str(i):float(i*2+2) for i in field}
    mid={str(i):float(i*2+2)*(1.1 if i%2 else .97) for i in field}
    wide=[{"selection":[i,j],"odds_low":float(2+i+j),
           "odds_high":float(2+i+j+.5)}
          for i,j in combinations(field,2)]
    return {
        "schema":m.FEATURE_SCHEMA,
        "provenance":"synthetic_test",
        "operator_confirmed_research_rights":False,
        "race_id":"SYN_RACE_20261107_07",
        "scheduled_post_jst":"2026-11-07T15:00:00+09:00",
        "race_distance_m":1200,
        "provider":"TEST_PROVIDER",
        "model_coefficient_lock_at_jst":"2026-11-07T09:55:00+09:00",
        "local_forecast_created_at_jst":"2026-11-07T11:05:00+09:00",
        "horizon_minutes":18,"target_window_minutes":5,
        "first_win":{
            "market":"win","provider":"TEST_PROVIDER",
            "source_clock_verified":True,
            "source_updated_at_jst":"2026-11-07T10:00:00+09:00",
            "received_at_jst":"2026-11-07T10:02:00+09:00",
            "odds_by_horse_number":first,
        },
        "middle_win":{
            "market":"win","provider":"TEST_PROVIDER",
            "source_clock_verified":True,
            "source_updated_at_jst":"2026-11-07T11:00:00+09:00",
            "received_at_jst":"2026-11-07T11:02:00+09:00",
            "odds_by_horse_number":mid,
        },
        "middle_wide":{
            "market":"wide","provider":"TEST_PROVIDER",
            "source_clock_verified":True,
            "source_updated_at_jst":"2026-11-07T11:00:00+09:00",
            "received_at_jst":"2026-11-07T11:03:00+09:00",
            "pairs":wide,
        },
    }


def as_bytes(z):
    return json.dumps(z,ensure_ascii=False,sort_keys=True,
                      separators=(",",":")).encode("utf-8")


def target(feature,*,change=1.03,first_at="2026-11-07T11:18:00+09:00",
           extra=False):
    prices=feature["middle_win"]["odds_by_horse_number"]
    snapshots=[
        {"market":"win","provider":feature["provider"],
         "source_clock_verified":True,
         "source_updated_at_jst":first_at,
         "received_at_jst":(datetime.fromisoformat(first_at)+timedelta(minutes=2)).isoformat(),
         "odds_by_horse_number":{
             k:float(v*(change if int(k)%2 else 2-change))
             for k,v in prices.items()},
        }
    ]
    if extra:
        snapshots=[
            {"market":"win","provider":feature["provider"],
             "source_clock_verified":True,
             "source_updated_at_jst":"2026-11-07T11:15:00+09:00",
             "received_at_jst":"2026-11-07T11:16:00+09:00",
             "odds_by_horse_number":prices},
            *snapshots,
            {"market":"win","provider":feature["provider"],
             "source_clock_verified":True,
             "source_updated_at_jst":"2026-11-07T11:21:00+09:00",
             "received_at_jst":"2026-11-07T11:22:00+09:00",
             "odds_by_horse_number":{
                 k:float(v*(1.2 if int(k)%2 else .85))
                 for k,v in prices.items()},
            },
        ]
    return {
        "schema":m.TARGET_SCHEMA,
        "race_id":feature["race_id"],
        "provider":feature["provider"],
        "operator_declares_complete_capture_stream":True,
        "snapshots":snapshots,
    }


def history_fixture(feature):
    from keiba_independent_horse_asof_preflight import (
        HISTORY_SCHEMA,RECEIPT_SCHEMA)
    rows=[{
        "number":i,"name":f"HORSE{i}",
        "past_runs":[
            {"date":"2026-10-01","finish":7-i,
             "distance_m":1200,"surface":"芝"},
        ],
    } for i in range(1,7)]
    doc={"schema":HISTORY_SCHEMA,"race_id":feature["race_id"],
         "target_date":"2026-11-07","target_surface":"芝",
         "distance_m":1200,"horses":rows}
    raw=as_bytes(doc)
    receipt={
        "schema":RECEIPT_SCHEMA,
        "externally_attested":False,
        "operator_declares_rights_review":True,
        "original_source_sha256":sha256(raw).hexdigest(),
        "original_source_url":"https://example.org/authorized/history",
        "publisher_updated_at_jst":"2026-11-07T09:40:00+09:00",
        "source_received_at_jst":"2026-11-07T09:45:00+09:00",
        "declared_official_horse_names_by_number":{
            str(i):f"HORSE{i}" for i in range(1,7)},
    }
    return raw,receipt


@unittest.skipIf(np is None,"Dedicated numerical workflow installs NumPy")
class ShadowPureTests(unittest.TestCase):
    def test_no_horse_history_local_freeze_mass_and_model_universe(self):
        d=source()
        frozen=m.freeze_source_bytes(as_bytes(d),horse_draws=50,horse_seed=14)
        x=m.verify_freeze(frozen)
        self.assertEqual(x["schema"],m.FREEZE_SCHEMA)
        self.assertEqual(x["source_provenance"],"synthetic_test")
        self.assertFalse(x["external_GitHub_server_preseal_verified"])
        self.assertEqual(len(x["candidate_predictions"]),12)
        self.assertEqual(x["horse_numbers"],list(range(1,7)))
        self.assertTrue(frozen["SHA_only_existing_dispatch_inputs_NOT_SENT"][
            "seal_sha256"]==frozen["seal_sha256_of_canonical_payload"])
        for name,rows in x["candidate_predictions"].items():
            self.assertAlmostEqual(sum(a["p"] for a in rows),1,places=12,
                                   msg=name)
            self.assertTrue(all(a["p"]>0 for a in rows))
        for var in m.SIGNAL_VARIANTS:
            p=x["candidate_predictions"][
                f"coupled_market_qmid_{var}_round5"]
            self.assertEqual(
                p,x["candidate_predictions"][
                    "coupled_market_qmid_horse_signal_round5"])

    def test_horse_history_optional_aligned_and_replay_not_external_proof(self):
        d=source()
        raw,receipt=history_fixture(d)
        f=m.freeze_source_bytes(as_bytes(d),history_bytes=raw,
                                 history_receipt=receipt,
                                 horse_draws=50,horse_seed=15)
        payload=m.verify_freeze(f)
        self.assertEqual(len(payload["candidate_predictions"]),21)
        self.assertEqual(
            payload["optional_horse_history_sha256_local_only"],
            sha256(raw).hexdigest())
        self.assertEqual(f["external_prestart_proof_status"],
            "HOLD_WORKFLOW_NOT_INSTALLED_ON_DEFAULT_BRANCH_AND_NOT_DISPATCHED")
        for name in m.SIGNAL_VARIANTS:
            self.assertEqual(
                payload["candidate_predictions"][
                    f"coupled_authorized_past_form_{name}_round5"],
                payload["candidate_predictions"][
                    "coupled_authorized_past_form_horse_signal_round5"])
        bad=copy.deepcopy(receipt)
        bad["source_received_at_jst"]="2026-11-07T11:04:00+09:00"
        with self.assertRaisesRegex(ValueError,"HORSE_SOURCE_OR_QUOTE"):
            m.freeze_source_bytes(as_bytes(d),history_bytes=raw,
                                  history_receipt=bad,horse_draws=40)

    def test_different_future_market_cannot_change_freeze_or_prediction(self):
        d=source()
        f=m.freeze_source_bytes(as_bytes(d),horse_draws=50,horse_seed=144)
        sha=f["seal_sha256_of_canonical_payload"]
        a=m.score_target(f,target(d,change=1.01,extra=True))
        b=m.score_target(f,target(d,change=1.16))
        self.assertEqual(f["seal_sha256_of_canonical_payload"],sha)
        self.assertEqual(
            a["selected_first_eligible_source_published_at"],
            "2026-11-07T11:18:00+09:00")
        self.assertEqual(a["source_series_snapshot_count"],3)
        self.assertNotEqual(
            a["all_model_scores"]["mid_WIN_persistence"][
                "next_price_index_TV_pp"],
            b["all_model_scores"]["mid_WIN_persistence"][
                "next_price_index_TV_pp"])
        self.assertEqual(a["status"],m.SCORE_STATUS)
        self.assertFalse(a["external_preseal_authenticated"])
        self.assertFalse(a["capture_stream_independently_complete"])

    def test_unobserved_fixed_target_horizon_is_a_HOLD_not_free_choice(self):
        d=source()
        f=m.freeze_source_bytes(as_bytes(d),horse_draws=40,horse_seed=33)
        t=target(d,first_at="2026-11-07T11:24:00+09:00")
        x=m.score_target(f,t)
        self.assertEqual(x["status"],
            "HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW")
        self.assertFalse(x["external_preseal_authenticated"])

    def test_tampered_forecast_digest_rejected(self):
        d=source()
        f=m.freeze_source_bytes(as_bytes(d),horse_draws=40,horse_seed=33)
        f["payload"]["candidate_predictions"]["mid_WIN_persistence"][0]["p"]+=.01
        with self.assertRaisesRegex(ValueError,"HASH_OR_SCHEMA"):
            m.verify_freeze(f)

    def test_source_time_provider_rights_and_horse_roster_fail_closed(self):
        d=source()
        cases=[]
        future=copy.deepcopy(d)
        future["official_top3"]=[3,5,1]
        cases.append((future,"EXTRA_FUTURE_FIELDS"))
        stale=copy.deepcopy(d)
        stale["middle_wide"]["source_updated_at_jst"]=(
            "2026-11-07T10:59:00+09:00")
        cases.append((stale,"SOURCE_CLOCK"))
        bad_source=copy.deepcopy(d)
        bad_source["middle_win"]["provider"]="MIXED_PROVIDER"
        cases.append((bad_source,"PROVIDER"))
        late=copy.deepcopy(d)
        late["local_forecast_created_at_jst"]="2026-11-07T11:19:00+09:00"
        cases.append((late,"CLOCK"))
        missing=copy.deepcopy(d)
        missing["middle_wide"]["pairs"].pop()
        cases.append((missing,"ALL_PAIRS"))
        changed=copy.deepcopy(d)
        changed["middle_win"]["odds_by_horse_number"].pop("1")
        cases.append((changed,"ROSTER"))
        licensed=copy.deepcopy(d)
        licensed["provenance"]="authorized_private_local_export"
        cases.append((licensed,"RIGHTS"))
        for item,needle in cases:
            with self.subTest(needle=needle):
                with self.assertRaises(ValueError):
                    m.freeze_source_bytes(as_bytes(item),horse_draws=40)

    def test_next_target_provider_horse_time_drift_is_rejected(self):
        d=source()
        f=m.freeze_source_bytes(as_bytes(d),horse_draws=40,horse_seed=7)
        wrong=target(d)
        wrong["provider"]="OTHER_PROVIDER"
        with self.assertRaisesRegex(ValueError,"TARGET_STREAM"):
            m.score_target(f,wrong)
        changed=target(d)
        changed["snapshots"][0]["odds_by_horse_number"].pop("1")
        with self.assertRaisesRegex(ValueError,"HORSE_FIELD"):
            m.score_target(f,changed)
        time_travel=target(d)
        time_travel["snapshots"][0]["received_at_jst"]=(
            "2026-11-07T10:00:00+09:00")
        with self.assertRaisesRegex(ValueError,"RECEIVED_BEFORE_PUBLICATION"):
            m.score_target(f,time_travel)

    def test_authorized_future_private_export_and_too_late_received_quote(self):
        d=source()
        d["provenance"]="authorized_private_local_export"
        d["operator_confirmed_research_rights"]=True
        frozen=m.freeze_source_bytes(as_bytes(d),horse_draws=40,
                                     horse_seed=212)
        self.assertEqual(m.verify_freeze(frozen)["source_provenance"],
                         "authorized_private_local_export")
        later=target(d)
        later["snapshots"][0]["received_at_jst"]="2026-11-07T14:56:00+09:00"
        with self.assertRaisesRegex(ValueError,"TARGET_SNAPSHOT_CLOCK_TIME_TRAVEL"):
            m.score_target(frozen,later)

    def test_cohort_duplicate_and_missing_target_guard(self):
        d=source()
        freeze=m.freeze_source_bytes(as_bytes(d),horse_draws=40)
        scored=m.score_target(freeze,target(d))
        held=m.score_target(freeze,target(
            d,first_at="2026-11-07T11:24:00+09:00"))
        cohort=m.score_cohort([scored,held])
        self.assertEqual(cohort["scored_real_market_intervals"],1)
        self.assertEqual(cohort["missing_eligible_target_holds"],1)
        self.assertEqual(cohort["distinct_meeting_dates"],1)
        self.assertFalse(cohort["prospective_evaluation_certified"])
        self.assertTrue("mid_WIN_persistence" in
                        cohort["by_prespecified_model"])
        with self.assertRaisesRegex(ValueError,"DUPLICATE_ACTUAL"):
            m.score_cohort([scored,copy.deepcopy(scored)])
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_COHORT"):
            fake=copy.deepcopy(scored)
            fake["external_preseal_authenticated"]=True
            m.score_cohort([fake])


@unittest.skipUnless(np is not None and (
    ROOT/"data/2026-10-12/r8_markets_latest.json").exists(),
    "Source locked R8 archive is required only for historical replay smoke")
class HistoricalReplayTest(unittest.TestCase):
    def test_real_r8_separate_archive_replay_matches_prior_market_benchmarks(self):
        import keiba_private_forward_r8_replay as historical
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("NO_OFFICIAL_RESULT_LEAK")) as fn:
            report=historical.audit(horse_draws=60,seed=20261025)
            fn.assert_not_called()
        self.assertEqual(report["actual_source_races"],1)
        self.assertEqual(report["real_future_after_freeze_event_count"],0)
        self.assertEqual(report["n_market_models"],12)
        self.assertEqual(report["n_score_models"],12)
        score=report["scores"]
        self.assertAlmostEqual(score["mid_WIN_persistence"][
            "next_price_index_TV_pp"],9.656362948215287,places=9)
        self.assertAlmostEqual(score["mid_WIN_momentum"][
            "next_price_index_TV_pp"],8.180965354937559,places=9)
        self.assertAlmostEqual(score[
            "mid_WIN_momentum_plus_WIDE_node_beta025"][
                "next_price_index_TV_pp"],7.104113542634069,places=9)
        self.assertFalse(report["synthetic_duplicate_cohort"][
            "prospective_evaluation_certified"])


if __name__=="__main__":
    unittest.main()
