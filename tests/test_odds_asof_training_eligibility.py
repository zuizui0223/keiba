#!/usr/bin/env python3
"""Chronological evidence availability, not race-number pseudo-holdout."""
from copy import deepcopy
from datetime import datetime, timedelta
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from odds_asof_training_eligibility import (
    STATUS, audit, demo, training_graph, next_quote_training_graph,
)


class MarketOutcomeAsOfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observed = audit()

    def test_five_source_locked_real_races_zero_legal_prior_outcome_relations(self):
        r = self.observed
        self.assertEqual(r["status"], STATUS)
        self.assertEqual(r["meeting_date"], "2026-10-12")
        g = r["within_meeting_training_graph"]
        self.assertEqual(g["race_count"], 5)
        self.assertEqual(g["distinct_result_ids"], 5)
        self.assertEqual(g["available_training_relationships"], 0)
        self.assertEqual(g["targets_with_any_documented_prior_outcomes"], 0)
        self.assertEqual(g["targets_with_at_least_two_documented_training_outcomes"], 0)
        self.assertEqual(
            [len(x["known_prior_official_result_ids"]) for x in g["per_race"]],
            [0, 0, 0, 0, 0])
        self.assertTrue(r["all_five_forecast_features_available_before_any_of_five_races_started"])
        self.assertFalse(r["result_available_for_same_day_other_race_model_fit"])
        self.assertTrue(g["no_real_future_holdout_created"])

    def test_archived_1344_win_market_cannot_train_any_1327_snapshot(self):
        r=self.observed
        g=r["within_meeting_next_WIN_market_label_training_graph"]
        self.assertEqual(g["full_next_market_labels_available_in_archive"],1)
        self.assertEqual(g["frozen_market_candidate_count"],5)
        self.assertEqual(g["market_target_to_forecast_training_relations"],0)
        self.assertTrue(g["not_a_true_outcome_probability_or_betting_roi_test"])
        self.assertTrue(r["different_market_target_source_not_a_winner_label"])
        self.assertEqual(
            r["r8_next_market_quote_received_at"],
            "2026-10-12T13:44:55.575221+09:00")
        self.assertTrue(all(
            not x["next_market_label_ids_received_before_features"]
            for x in g["per_race"]))

    def test_synthetic_next_market_can_train_later_forecast_even_before_race_finishes(self):
        base=[
            {"race_id":"A","scheduled_post_jst":"2026-01-01T14:00+09:00",
             "quote_published_at":"2026-01-01T12:00+09:00",
             "last_required_feature_received_at":"2026-01-01T12:01+09:00",
             "feature_source_verified":True},
            {"race_id":"B","scheduled_post_jst":"2026-01-01T15:00+09:00",
             "quote_published_at":"2026-01-01T12:45+09:00",
             "last_required_feature_received_at":"2026-01-01T12:46+09:00",
             "feature_source_verified":True},
            {"race_id":"C","scheduled_post_jst":"2026-01-01T16:00+09:00",
             "quote_published_at":"2026-01-01T13:45+09:00",
             "last_required_feature_received_at":"2026-01-01T13:46+09:00",
             "feature_source_verified":True},
        ]
        later={
            "race_id":"A","scheduled_post_jst":"2026-01-01T14:00+09:00",
            "next_market_source_published_at":"2026-01-01T13:00+09:00",
            "next_market_received_at":"2026-01-01T13:01+09:00",
            "full_field_verified":True,
        }
        g=next_quote_training_graph(base,[later])
        self.assertEqual(g["market_target_to_forecast_training_relations"],1)
        self.assertEqual(
            {x["race_id"]:x["next_market_label_ids_received_before_features"]
             for x in g["per_race"]},
            {"A":[],"B":[],"C":["A"]})
        self.assertTrue(g["source_receiver_clock_overrides_race_number"])
        late=deepcopy(later)
        late["next_market_received_at"]="2026-01-01T14:01+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_NEXT_MARKET_LABEL"):
            next_quote_training_graph(base,[late])

    def test_actual_1327_receipts_are_before_1400_first_post(self):
        r = self.observed
        self.assertEqual(
            r["last_full_win_wide_market_received_at"],
            "2026-10-12T13:27:33.944454+09:00")
        self.assertEqual(
            r["earliest_scheduled_race_post"],
            "2026-10-12T14:00:00+09:00")
        self.assertAlmostEqual(
            r["minutes_between_last_market_receive_and_first_race_post"],
            32.4342591, delta=0.00001)
        self.assertEqual(
            r["official_result_verified_at_not_original_jra_publish_time"],
            "2026-10-12T23:46:27+09:00")
        self.assertTrue(any("not the first publication" in s for s in
                            r["scientific_interpretation"]))

    def test_synthetic_next_day_two_old_races_are_eligible(self):
        g = demo()
        self.assertEqual(g["race_count"], 3)
        self.assertEqual(g["available_training_relationships"], 2)
        self.assertEqual(
            {x["race_id"]: x["known_prior_official_result_ids"]
             for x in g["per_race"]},
            {"SYNTH-A": [], "SYNTH-B": [], "SYNTH-C": ["SYNTH-A", "SYNTH-B"]})
        self.assertEqual(g["targets_with_at_least_two_documented_training_outcomes"], 1)

    def test_you_cannot_use_r8_result_at_1327_to_train_r12_at_1327(self):
        # Race #8 has post=14:00. Even when its *official result* becomes
        # available by 14:20, race #12's quote was read at 13:27.
        old = {
            "race_id": "8", "scheduled_post_jst": "2026-10-12T14:00+09:00",
            "independent_official_result_verified_at": "2026-10-12T14:20+09:00",
            "official_source_verified": True,
        }
        x = training_graph([{
            "race_id": "12", "scheduled_post_jst": "2026-10-12T16:30+09:00",
            "quote_published_at": "2026-10-12T13:27+09:00",
            "last_required_feature_received_at": "2026-10-12T13:27:34+09:00",
            "feature_source_verified": True,
        }], [old])
        self.assertEqual(x["available_training_relationships"], 0)
        self.assertEqual(x["targets_with_any_documented_prior_outcomes"], 0)

    def test_prediction_input_order_cannot_create_extra_training(self):
        # Event time, never file row order, determines admissibility.
        a = demo()
        results = [
            {"race_id": "SYNTH-A", "scheduled_post_jst": "2026-01-01T14:00+09:00",
             "independent_official_result_verified_at": "2026-01-01T14:20+09:00",
             "official_source_verified": True},
            {"race_id": "SYNTH-B", "scheduled_post_jst": "2026-01-01T15:00+09:00",
             "independent_official_result_verified_at": "2026-01-01T15:20+09:00",
             "official_source_verified": True},
        ]
        predictions = []
        for x in a["per_race"]:
            predictions.append({
                "race_id": x["race_id"],
                "scheduled_post_jst": x["scheduled_post_at"],
                "quote_published_at": x["last_quote_source_published_at"],
                "last_required_feature_received_at": x["asof_last_feature_received_at"],
                "feature_source_verified": True,
            })
        b = training_graph(predictions[::-1], results[::-1])
        self.assertEqual(
            {x["race_id"]:x["known_prior_official_result_ids"] for x in b["per_race"]},
            {x["race_id"]:x["known_prior_official_result_ids"]
             for x in a["per_race"]},
        )

    def test_input_price_receipt_after_post_is_never_admissible(self):
        predictions = [{
            "race_id": "SYNTH-LATE",
            "quote_published_at": "2026-02-01T13:20+09:00",
            "last_required_feature_received_at": "2026-02-01T14:01+09:00",
            "scheduled_post_jst": "2026-02-01T14:00+09:00",
            "feature_source_verified": True,
        }]
        with self.assertRaisesRegex(ValueError, "HOLD_FEATURE_NOT_RECEIVED"):
            training_graph(predictions, [])
        predictions[0]["last_required_feature_received_at"] = (
            "2026-02-01T13:20+09:00")
        predictions[0]["quote_published_at"] = "2026-02-01T13:40+09:00"
        with self.assertRaisesRegex(ValueError, "HOLD_FEATURE_NOT_RECEIVED"):
            training_graph(predictions, [])

    def test_undocumented_official_result_cannot_be_used_even_if_earlier_race(self):
        # The public release time might have preceded archive verification,
        # but without that evidence the audit does not create it.
        g = demo()
        result = [{
            "race_id": "SYNTH-A",
            "scheduled_post_jst": "2026-01-01T14:00+09:00",
            "independent_official_result_verified_at": "2026-01-02T13:00+09:00",
            "official_source_verified": True,
        }]
        predictions = [{
            "race_id": "SYNTH-C",
            "quote_published_at": "2026-01-02T12:00+09:00",
            "last_required_feature_received_at": "2026-01-02T12:15+09:00",
            "scheduled_post_jst": "2026-01-02T15:00+09:00",
            "feature_source_verified": True,
        }]
        b = training_graph(predictions, result)
        self.assertEqual(b["available_training_relationships"], 0)

    def test_bad_result_provenance_duplicate_and_naive_clocks_hard_fail(self):
        result = {
            "race_id": "A", "scheduled_post_jst": "2026-01-01T14:00+09:00",
            "independent_official_result_verified_at": "2026-01-01T14:20+09:00",
            "official_source_verified": True,
        }
        forecast = {
            "race_id": "B", "scheduled_post_jst": "2026-01-02T14:00+09:00",
            "quote_published_at": "2026-01-02T12:00+09:00",
            "last_required_feature_received_at": "2026-01-02T12:01+09:00",
            "feature_source_verified": True,
        }
        invalid = deepcopy(result)
        invalid["official_source_verified"] = False
        with self.assertRaisesRegex(ValueError, "HOLD_UNVERIFIED_RESULT"):
            training_graph([forecast], [invalid])
        invalid = deepcopy(result)
        invalid["independent_official_result_verified_at"] = (
            "2026-01-01T13:59+09:00")
        with self.assertRaisesRegex(ValueError, "HOLD_RESULT_VERIFIED_BEFORE"):
            training_graph([forecast], [invalid])
        invalid = deepcopy(result)
        invalid["independent_official_result_verified_at"] = (
            "2026-01-01T14:20")
        with self.assertRaisesRegex(ValueError, "HOLD_NAIVE_TIMESTAMP"):
            training_graph([forecast], [invalid])
        with self.assertRaisesRegex(ValueError, "HOLD_DUPLICATE_OR_MISSING_RACE_ID"):
            training_graph([forecast, forecast], [result])

    def test_prediction_result_post_mismatch_hard_fails(self):
        forecast = {
            "race_id": "R", "scheduled_post_jst": "2026-01-01T15:00+09:00",
            "quote_published_at": "2026-01-01T13:00+09:00",
            "last_required_feature_received_at": "2026-01-01T13:01+09:00",
            "feature_source_verified": True,
        }
        result = {
            "race_id": "R", "scheduled_post_jst": "2026-01-01T14:00+09:00",
            "independent_official_result_verified_at": "2026-01-01T14:30+09:00",
            "official_source_verified": True,
        }
        with self.assertRaisesRegex(ValueError, "HOLD_POST_TIME_DISAGREES"):
            training_graph([forecast], [result])


if __name__ == "__main__":
    unittest.main()
