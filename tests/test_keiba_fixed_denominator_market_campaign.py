#!/usr/bin/env python3
"""All 26 pre-registered source-locked JRA races stay in market denominator."""
from __future__ import annotations
from pathlib import Path
import copy
from itertools import combinations
import sys
import unittest

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_fixed_denominator_market_campaign as m


CUTOFF="2026-10-25T22:04:00+09:00"
POSTRACE="2026-10-31T16:00:00+09:00"
FIRST="2026-10-31|京都|ファンタジーS"
SECOND="2026-11-01|東京|天皇賞（秋）"


def first_receipt(stage="next_quote_local_scored", *, sha=None):
    if sha is None and stage in (
            "next_quote_local_scored","next_quote_window_missing",
            "local_SHA_frozen"):
        sha="a"*64
    return {
        "slot_id":FIRST,
        # Invented fixture race ID and source: never a real upcoming JRA ID.
        "official_race_id":"SYNTHETIC_JRA_2026_10_31",
        "scheduled_post_jst":"2026-10-31T15:40:00+09:00",
        "racecard_source_url":"https://example.org/synthetic-race-card",
        "racecard_received_at_jst":"2026-10-30T12:00:00+09:00",
        "quote_provider_name":"SYNTHETIC_PROVIDER_NEVER_REAL_JRA",
        "source_rights_checked_locally":True,
        "capture_stage":stage,
        "local_frozen_model_sha256":sha,
    }


def receipts(stage="next_quote_local_scored"):
    return {"schema":m.RECEIPT_SCHEMA,
            "entries":[first_receipt(stage)]}


def local_score(*, missing=False):
    if missing:
        return {
            "schema":m.SCORE_SCHEMA,
            "status":"HOLD_TARGET_NOT_OBSERVED_IN_LOCKED_TIME_WINDOW",
            "race_id":"SYNTHETIC_JRA_2026_10_31",
            "external_preseal_authenticated":False,
        }
    models={}
    for name in m.MODEL_BENCHMARKS:
        models[name]={"next_price_index_TV_pp": 10.0 if
                      name=="mid_WIN_persistence" else 7.0,
                      "next_price_index_KL_nats":0.025}
    for variant in m.SIGNAL_VARIANTS:
        for a in m.ARRIVALS:
            models[f"coupled_market_qmid_{variant}_round{a}"]={
                "next_price_index_TV_pp":8.0,
                "next_price_index_KL_nats":0.02,
            }
    assert len(models)==12
    return {
        "schema":m.SCORE_SCHEMA,"status":m.SCORE_STATUS,
        "race_id":"SYNTHETIC_JRA_2026_10_31",
        "scheduled_post_jst":"2026-10-31T15:40:00+09:00",
        "sealed_prediction_sha256":"a"*64,
        "selected_first_eligible_source_published_at":
            "2026-10-31T14:30:00+09:00",
        "selected_source_received_at":"2026-10-31T14:31:00+09:00",
        "external_preseal_authenticated":False,
        "capture_stream_independently_complete":False,
        "all_model_scores":models,
    }


@unittest.skipIf(np is None,"NumPy is installed only in numeric source-audit CI")
class CalendarSourceLockTests(unittest.TestCase):
    def test_exact_precommitted_roster_26_races_on_20_meeting_dates(self):
        calendar,coverage=m._locked_universe()
        self.assertEqual(len(calendar),26)
        self.assertEqual(len(coverage),26)
        self.assertEqual(len({e["scheduled_date_jst"] for e in calendar}),20)
        self.assertEqual(calendar[0]["slot_id"],m.EXPECTED_LEGACY_KIKKA)
        self.assertEqual(calendar[1]["slot_id"],FIRST)
        self.assertEqual(calendar[2]["slot_id"],SECOND)
        self.assertEqual(coverage[m.EXPECTED_LEGACY_KIKKA]["status"],
                         "preseal_sha_submitted_unverified")
        self.assertTrue(all(e["official_race_id"] is None and
                            e["source_reported_post_jst"] is None
                            for e in calendar[1:]))

    def test_calendar_SHA_detects_modified_or_deceptive_public_registry(self):
        with self.assertRaisesRegex(ValueError,"BLOB_DRIFT"):
            m._locked_json(ROOT,m.CALENDAR_PATH,"f"*40)
        with self.assertRaisesRegex(ValueError,"BLOB_DRIFT"):
            m._locked_json(ROOT,m.REGISTRY_PATH,"0"*40)

    def test_now_after_kikka_new_future_candidate_count_is_25(self):
        out=m.campaign(asof=CUTOFF)
        self.assertEqual(out["registered_flat_G1_G2_G3_slots_including_Kikka"],26)
        self.assertEqual(out["registered_meeting_dates"],20)
        self.assertEqual(
            out["registered_next_price_candidate_slots_excluding_old_Kikka"],25)
        self.assertEqual(out["future_registered_slots_after_asof_date"],25)
        self.assertEqual(
            out["official_post_and_race_id_unresolved_in_public_registry"],25)
        self.assertEqual(out["locally_scored_next_price_intervals_unattested"],0)
        self.assertEqual(out["new_independent_real_prospective_quote_trials_confirmed"],0)
        self.assertEqual(out["remotely_SHA_pre_next_price_verified_intervals"],0)
        self.assertTrue(out["prior_Kikka_M0_M2_SHA_and_v31_holdout_unchanged"])
        self.assertEqual(out["registered_slot_readiness"][0]["capture_state"],
                         "PRIOR_KIKKA_OUTCOME_PRESEAL_UNVERIFIED_NOT_NEXT_MARKET")
        self.assertEqual(out["registered_slot_readiness"][1]["slot_id"],FIRST)
        self.assertEqual(out["registered_slot_readiness"][2]["slot_id"],SECOND)
        self.assertEqual(out["registered_slot_readiness"][1]["capture_state"],
                         "UPCOMING_NO_VERIFIED_RACE_ID_POST_OR_WIN_WIDE_INPUT")
        self.assertFalse(out["minimum_60_races_8_dates_development_guard_met"])
        for model in m.MODEL_NAMES:
            self.assertIsNone(out["by_model_local_scores_not_prospective_certified"][
                model]["race_equal_delta_next_price_TV_vs_persistence_pp"])

    def test_after_uncollected_race_it_stays_denominator_not_success(self):
        out=m.campaign(asof="2026-11-02T21:00:00+09:00")
        ids={v["slot_id"]:v for v in out["registered_slot_readiness"]}
        self.assertEqual(ids[FIRST]["capture_state"],
                         "PAST_OR_DUE_UNCOLLECTED_FIXED_SLOT")
        self.assertEqual(ids[SECOND]["capture_state"],
                         "PAST_OR_DUE_UNCOLLECTED_FIXED_SLOT")
        self.assertEqual(len(out["registered_slot_readiness"]),26)
        self.assertEqual(out["locally_scored_next_price_intervals_unattested"],0)
        self.assertFalse(out["prospective_evaluation_certified"]
                         if "prospective_evaluation_certified" in out else False)

    def test_reject_naive_time_for_asof(self):
        with self.assertRaisesRegex(ValueError,"NAIVE"):
            m.campaign(asof="2026-10-25T22:04:00")


@unittest.skipIf(np is None,"NumPy numerical dependency")
class PrivateMetadataAndFutureCaptureTests(unittest.TestCase):
    def test_score_is_locally_counted_only_after_its_reported_receipt_time(self):
        report=m.campaign(asof=POSTRACE,local_receipts=receipts(),
                          private_scores=[local_score()])
        self.assertEqual(report["locally_scored_next_price_intervals_unattested"],1)
        self.assertEqual(report["new_independent_real_prospective_quote_trials_confirmed"],0)
        self.assertEqual(report["remotely_SHA_pre_next_price_verified_intervals"],0)
        self.assertEqual(report["registered_slot_readiness"][1]["capture_state"],
                         "LOCAL_PRICE_INDEX_SCORE_UNATTESTED")
        metric=report["by_model_local_scores_not_prospective_certified"][
            "mid_WIN_momentum_plus_WIDE_node_beta025"]
        self.assertAlmostEqual(
            metric["race_equal_delta_next_price_TV_vs_persistence_pp"],-3.0)
        self.assertAlmostEqual(
            metric["meeting_date_equal_delta_next_price_TV_pp"],-3.0)
        self.assertEqual(metric["locally_scored_distinct_real_market_intervals_not_authenticated"],1)

    def test_future_quoted_result_cannot_exist_at_prior_asof(self):
        with self.assertRaisesRegex(ValueError,"RECEIVED_AFTER_ASOF"):
            m.campaign(asof=CUTOFF,local_receipts=receipts(),
                       private_scores=[local_score()])
        with self.assertRaisesRegex(ValueError,"RECEIVED_AFTER_ASOF"):
            m.campaign(asof="2026-10-31T14:29:00+09:00",
                       local_receipts=receipts(),private_scores=[local_score()])

    def test_no_quote_in_frozen_target_window_stays_HOLD_but_only_after_post(self):
        meta=receipts(stage="next_quote_window_missing")
        with self.assertRaisesRegex(ValueError,"BEFORE_RACE_POST"):
            m.campaign(asof=CUTOFF,local_receipts=meta,
                       private_scores=[local_score(missing=True)])
        post=m.campaign(asof=POSTRACE,local_receipts=meta,
                        private_scores=[local_score(missing=True)])
        self.assertEqual(post["missing_locked_next_quote_target_intervals"],1)
        self.assertEqual(post["locally_scored_next_price_intervals_unattested"],0)
        self.assertEqual(post["registered_slot_readiness"][1]["capture_state"],
                         "TARGET_WINDOW_UNOBSERVED_NOT_REPLACED")

    def test_unregistered_score_and_same_race_duplicates_rejected(self):
        with self.assertRaisesRegex(ValueError,"NOT_PREDECLARED"):
            m.campaign(asof=POSTRACE,private_scores=[local_score()])
        with self.assertRaisesRegex(ValueError,"MULTIPLE"):
            m.campaign(asof=POSTRACE,local_receipts=receipts(),
                       private_scores=[local_score(),copy.deepcopy(local_score())])
        d=receipts()
        d["entries"].append(copy.deepcopy(d["entries"][0]))
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):
            m.campaign(asof=POSTRACE,local_receipts=d)

    def test_unknown_models_changed_sha_and_self_attested_remote_status_rejected(self):
        meta=receipts()
        sh=local_score()
        del sh["all_model_scores"]["coupled_market_qmid_horse_signal_round1"]
        sh["all_model_scores"]["FAKE_WINNER_MODEL"]={
            "next_price_index_TV_pp":0.0,
            "next_price_index_KL_nats":0.0}
        with self.assertRaisesRegex(ValueError,"UNIVERSE"):
            m.campaign(asof=POSTRACE,local_receipts=meta,private_scores=[sh])
        sh=local_score()
        sh["sealed_prediction_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SHA"):
            m.campaign(asof=POSTRACE,local_receipts=meta,private_scores=[sh])
        sh=local_score()
        sh["external_preseal_authenticated"]=True
        with self.assertRaisesRegex(ValueError,"SELF_CERTIFY"):
            m.campaign(asof=POSTRACE,local_receipts=meta,private_scores=[sh])
        sh=local_score()
        sh["all_model_scores"]["mid_WIN_persistence"][
            "next_price_index_TV_pp"]=-1
        with self.assertRaisesRegex(ValueError,"NONFINITE"):
            m.campaign(asof=POSTRACE,local_receipts=meta,private_scores=[sh])

    def test_unverified_rights_or_missing_card_cannot_freeze(self):
        meta=receipts(stage="local_SHA_frozen")
        meta["entries"][0]["source_rights_checked_locally"]=False
        with self.assertRaisesRegex(ValueError,"SOURCE_RIGHTS"):
            m.campaign(asof=CUTOFF,local_receipts=meta)
        meta=receipts(stage="local_SHA_frozen")
        meta["entries"][0]["official_race_id"]=None
        with self.assertRaisesRegex(ValueError,"PARTIAL"):
            m.campaign(asof=CUTOFF,local_receipts=meta)
        meta=receipts(stage="local_SHA_frozen")
        meta["entries"][0]["racecard_source_url"]="http://example.org/card"
        with self.assertRaisesRegex(ValueError,"HTTPS"):
            m.campaign(asof=CUTOFF,local_receipts=meta)

    def test_future_event_date_crosswalk_and_quote_stage_mismatch_rejected(self):
        meta=receipts(stage="next_quote_local_scored")
        meta["entries"][0]["scheduled_post_jst"]="2026-11-01T15:40:00+09:00"
        with self.assertRaisesRegex(ValueError,"EVENT_DATE_MISMATCH"):
            m.campaign(asof=POSTRACE,local_receipts=meta,
                       private_scores=[local_score()])
        meta=receipts(stage="local_SHA_frozen")
        with self.assertRaisesRegex(ValueError,"CAPTURE_STAGE"):
            m.campaign(asof=POSTRACE,local_receipts=meta,
                       private_scores=[local_score()])
        meta=receipts(stage="metadata_only")
        with self.assertRaisesRegex(ValueError,"WITHOUT_ELIGIBLE"):
            meta["entries"][0]["local_frozen_model_sha256"]="a"*64
            m.campaign(asof=CUTOFF,local_receipts=meta)

    def test_metadata_source_enumeration_cannot_change_denominator(self):
        meta=receipts(stage="metadata_only")
        meta["entries"][0]["local_frozen_model_sha256"]=None
        out=m.campaign(asof=CUTOFF,local_receipts=meta)
        self.assertEqual(len(out["registered_slot_readiness"]),26)
        self.assertEqual(out["registered_slot_readiness"][1]["capture_state"],
                         "PRIVATE_LOCAL_METADATA_ONLY")
        self.assertEqual(out["locally_scored_next_price_intervals_unattested"],0)
        self.assertEqual(out["new_independent_real_prospective_quote_trials_confirmed"],0)
        self.assertEqual(out["registered_slot_readiness"][2]["slot_id"],SECOND)


if __name__=="__main__":
    unittest.main()
