"""Original JRA runner-number source join vs v3.1 frozen historical channels."""
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
from shuka2026_bind_draw_numbers import join_draw,DRAW_FILE


class StrictActualShukaNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw=json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
        manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.baseline=audit(raw,manifest=manifest,
                           actual_classifier_blob_sha=blob_sha(CLASSIFIER))
        cls.draw=json.loads(DRAW_FILE.read_text(encoding="utf-8"))
        cls.out=join_draw(cls.baseline,cls.draw)

    def test_exact_17_official_numbers_and_original_names_match(self):
        self.assertTrue(self.out["official_17_horse_numbers_confirmed"])
        self.assertEqual(len(self.out["horse_records"]),17)
        self.assertEqual([x["official_horse_number"] for x in
            self.out["horse_records"]],list(range(1,18)))
        self.assertEqual(set(x["horse_name"] for x in self.out["horse_records"]),
                         set(x["horse_name"] for x in self.baseline["horse_records"]))

    def test_correct_6_historical_candidates_match_current_official_numbers(self):
        self.assertEqual(self.out[
            "official_nonmarket_v31_candidate_numbers_NOT_RANKING"],[1,3,6,8,9,12])
        by={x["official_horse_number"]:x for x in self.out["horse_records"]}
        self.assertEqual(by[8]["horse_name"],"モンローウォーク")
        self.assertEqual(by[13]["horse_name"],"ドリームコア")
        self.assertFalse(by[13]["nonmarket_C1_or_U_or_rescue"])
        self.assertEqual(by[3]["horse_name"],"マスターソアラ")
        self.assertTrue(by[1]["C1"])
        self.assertTrue(by[9]["rescue"])

    def test_no_odds_imputed_when_exact_draw_known(self):
        self.assertTrue(self.out["actual_live_market_M_still_HOLD"])
        self.assertIsNone(self.out["market_plus_historical_v31_complete_union"])
        self.assertFalse(self.out["real_timestamped_pre_race_win_odds_captured"])
        for x in self.out["horse_records"]:
            self.assertIsNone(x["market_M"])
            self.assertIsNone(x["full_union"])
            self.assertTrue(x["does_NOT_estimate_win_or_top3_probability"])

    def test_fabricated_conflicting_draw_cannot_change_horse_identity(self):
        fake=copy.deepcopy(self.draw)
        fake["JRA_official_horse_number_by_name"][0]["horse_name"]="FAKE HORSE"
        with self.assertRaisesRegex(ValueError,"HOLD_OFFICIAL_JRA_DRAW_NAMES"):
            join_draw(self.baseline,fake)
        fake=copy.deepcopy(self.draw)
        fake["JRA_official_horse_number_by_name"][0]["official_horse_number"]=2
        with self.assertRaisesRegex(ValueError,"HOLD_MISSING_OR_DUPLICATED_FINAL"):
            join_draw(self.baseline,fake)

    def test_cannot_claim_market_or_profitable_prediction(self):
        fake=copy.deepcopy(self.draw)
        fake["actual_timestamped_win_odds_captured"]=True
        with self.assertRaisesRegex(ValueError,"HOLD_JRA_OFFICIAL_DRAW_OR_MARKET"):
            join_draw(self.baseline,fake)
        self.assertTrue(self.out["draw_join_not_a_race_probability_or_expected_value"])


if __name__=="__main__":
    unittest.main()
