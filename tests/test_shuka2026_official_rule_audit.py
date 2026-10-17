"""Real official pre-race JRA histories; no race outcome, invented odds or numbers."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from shuka2026_official_rule_audit import (
    audit,blob_sha,SOURCE_FILE,MANIFEST,CLASSIFIER
)


class ShukaJRAOfficialPreDrawRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
        cls.manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.actual_blob=blob_sha(CLASSIFIER)
        cls.result=audit(cls.original,manifest=cls.manifest,
                         actual_classifier_blob_sha=cls.actual_blob)

    def test_really_frozen_classifier_sha_and_precise_dated_card(self):
        self.assertEqual(cls_sha:=self.actual_blob,
                         self.manifest["frozen_blobs"]["classifier"])
        self.assertEqual(self.result["horse_count"],17)
        self.assertIn("2026-10-18",self.result["race"])
        self.assertFalse(self.result["original_v31_thresholds_changed"])
        self.assertFalse(self.result["formal_v31_pre_result_15_to_25_minutes_freeze"])
        self.assertFalse(self.result["official_v31_market_plus_historical_full_union_completed"])

    def test_six_historical_nonmarket_rule_candidates(self):
        self.assertEqual(set(self.result["nonmarket_C1_or_U_or_rescue_names"]),{
            "カナルサンマルタン","ギャラボーグ","スウィートハピネス",
            "マスターソアラ","モンローウォーク","ラベルセーヌ",
        })
        self.assertEqual(self.result["counts_by_channel"]["C1"],1)
        self.assertEqual(self.result["counts_by_channel"]["U"],4)
        self.assertEqual(self.result["counts_by_channel"]["rescue"],1)
        self.assertEqual(self.result["counts_by_channel"][
            "nonmarket_C1_or_U_or_rescue"],6)

    def test_GI_rescue_Q1_without_kyoto_win_CANNOT_auto_join_union(self):
        by={x["horse_name"]:x for x in self.result["horse_records"]}
        for name in ("エンネ","ドリームコア","サムシングスイート",
                     "タイセイボーグ"):
            self.assertTrue(by[name]["Q1"])
            self.assertFalse(by[name]["K1"])
            self.assertFalse(by[name]["rescue"])
            self.assertFalse(by[name]["nonmarket_C1_or_U_or_rescue"])
            self.assertIsNone(by[name]["market_M"])
        self.assertTrue(by["スウィートハピネス"]["Q1"])
        self.assertTrue(by["スウィートハピネス"]["K1"])
        self.assertTrue(by["スウィートハピネス"]["rescue"])
        self.assertEqual(by["スウィートハピネス"]["K_prior_kyoto_band_wins"],2)
        self.assertEqual(by["スウィートハピネス"]["K_prior_kyoto_band_top3"],3)
        self.assertTrue(by["ギャラボーグ"]["C1"])

    def test_jra_ratings_do_not_automatically_insert_horses(self):
        by={x["horse_name"]:x for x in self.result["horse_records"]}
        self.assertEqual(by["ドリームコア"]["2026_JRA_pre_rating_NOT_a_model_input"],111)
        self.assertEqual(by["モンローウォーク"]["2026_JRA_pre_rating_NOT_a_model_input"],114)
        self.assertFalse(by["ドリームコア"]["nonmarket_C1_or_U_or_rescue"])
        self.assertTrue(by["モンローウォーク"]["nonmarket_C1_or_U_or_rescue"])

    def test_no_fabricated_betting_numbers_or_win_odds(self):
        for h in self.result["horse_records"]:
            self.assertIsNone(h["official_horse_number"])
            self.assertIsNone(h["market_M"])
            self.assertIsNone(h["full_union"])
            self.assertTrue(h["does_NOT_estimate_win_or_top3_probability"])
        self.assertTrue(self.result["avoid_treating_entry_order_as_betting_numbers"])

    def test_cancelled_past_race_is_not_faked_as_a_start(self):
        row=next(x for x in self.original["runners"]
                 if x["name"]=="サムシングスイート")
        self.assertNotIn("2026-04-26",[h["date"] for h in row["full_history_before_target"]])
        self.assertTrue(all(h["date"]<"2026-10-18" for h in row["full_history_before_target"]))

    def test_poisoned_future_leakage_or_fictional_betting_odds_fails_closed(self):
        q=copy.deepcopy(self.original)
        q["runners"][0]["full_history_before_target"][0]["date"]="2026-10-19"
        with self.assertRaises(ValueError):
            audit(q,manifest=self.manifest,actual_classifier_blob_sha=self.actual_blob)
        q=copy.deepcopy(self.original)
        q["runners"][0]["win_odds"]=2.2
        with self.assertRaisesRegex(ValueError,"HOLD_NO_FAKE_HORSE_NUMBER_OR_WIN_ODDS"):
            audit(q,manifest=self.manifest,actual_classifier_blob_sha=self.actual_blob)
        q=copy.deepcopy(self.original)
        q["runners"][0]["number"]=1
        with self.assertRaisesRegex(ValueError,"HOLD_NO_FAKE_HORSE_NUMBER_OR_WIN_ODDS"):
            audit(q,manifest=self.manifest,actual_classifier_blob_sha=self.actual_blob)

    def test_cannot_change_precommitted_v31_classifier_sha(self):
        with self.assertRaisesRegex(ValueError,"HOLD_LOCKED_V31_CLASSIFIER"):
            audit(self.original,manifest=self.manifest,actual_classifier_blob_sha="a"*40)

    def test_missing_profile_or_unknown_grade_is_scientific_HOLD(self):
        q=copy.deepcopy(self.original)
        q["runners"][2]["full_history_before_target"][0]["class_rank"]=None
        q["runners"][2]["last4"][0]["class_rank"]=None
        with self.assertRaisesRegex(ValueError,"HOLD_UNVERIFIED_ORIGINAL_PAST_RACE_CLASS"):
            audit(q,manifest=self.manifest,actual_classifier_blob_sha=self.actual_blob)
        q=copy.deepcopy(self.original)
        q["runners"].pop()
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_17"):
            audit(q,manifest=self.manifest,actual_classifier_blob_sha=self.actual_blob)


if __name__=="__main__":
    unittest.main()
