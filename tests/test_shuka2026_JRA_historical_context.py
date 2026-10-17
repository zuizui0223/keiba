"""JRA 2026 historical-illustration audits, NOT new learned v3.1 thresholds."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from shuka2026_JRA_historical_context import (
    CONTEXT_PATH,context_stress
)


class JRA2026HistoricalRaceContextSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        cls.evaluated=context_stress(cls.original)

    def test_sources_exact_2026_jra_marginal_trends_and_17_runners(self):
        self.assertEqual(self.evaluated["official_seventeen_horse_count"],17)
        self.assertEqual(self.evaluated[
            "past_10_years_winner_counts_not_target_probabilities"],{
                "oaks_direct":7,"shion_stakes":3,"rose_stakes":0,
            })
        self.assertEqual(self.evaluated[
            "past_Kyoto_8_editions_previous_fourth_corner_position_by_finish"
        ]["front_four"]["first"],0)
        self.assertEqual(self.evaluated[
            "original_v31_hist_nonmarket_candidate_numbers"],[1,3,6,8,9,12])
        self.assertTrue(self.evaluated[
            "original_frozen_v31_model_code_or_thresholds_NOT_modified"])

    def test_most_relevant_horse_identity_contexts_explicitly_descriptive(self):
        z={r["JRA_official_horse_number"]:r
           for r in self.evaluated["horse_history_context_rows"]}
        self.assertEqual(z[8]["JRA_name"],"モンローウォーク")
        self.assertEqual(z[8]["latest_prior_race"],"ローズS")
        self.assertEqual(z[8]["latest_prior_race_fourth_corner"],2)
        self.assertEqual(z[8]["descriptive_context_label_NOT_a_win_probability"],
                         "ROSE_PRIOR_PATH_AND_PREVIOUS_RACE_FRONT4_STRESS")

        self.assertEqual(z[3]["JRA_name"],"マスターソアラ")
        self.assertEqual(z[3]["latest_prior_race_fourth_corner"],5)
        self.assertEqual(z[3]["descriptive_context_label_NOT_a_win_probability"],
                         "HISTORICALLY_COMPARABLE_SHION_PLUS_MIDFIELD")

        self.assertEqual(z[14]["JRA_name"],"サムシングスイート")
        self.assertEqual(z[14]["latest_prior_race_fourth_corner"],7)
        self.assertEqual(z[14]["descriptive_context_label_NOT_a_win_probability"],
                         "HISTORICALLY_COMPARABLE_SHION_PLUS_MIDFIELD")

        self.assertEqual(z[13]["JRA_name"],"ドリームコア")
        self.assertEqual(z[13]["latest_prior_race_fourth_corner"],3)
        self.assertEqual(z[13]["descriptive_context_label_NOT_a_win_probability"],
                         "SHION_TOP3_BUT_PREVIOUS_RACE_FRONT4")

    def test_cannot_read_context_as_win_probability_or_wager_value(self):
        q=self.evaluated
        self.assertTrue(q["not_added_to_model_rank_win_probabilities_or_M_market"])
        self.assertTrue(q["historical_zero_winners_DOES_NOT_imply_impossible_event"])
        self.assertTrue(q["historical_race_differences_not_a_randomized_effect"])
        self.assertTrue(q["source_historical_8_Kyoto_editions_not_national_independent_future_validation"])
        self.assertNotIn("predicted_win_probability",json.dumps(q))
        self.assertNotIn("expected_value",json.dumps(q))

    def test_false_trend_source_metadata_rejected(self):
        q=copy.deepcopy(self.original)
        q["JRA_previous_race_winner_counts_10years"]["rose_stakes"]=1
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_JRA_2026_GI_SOURCE"):
            context_stress(q)

    def test_changed_actual_horse_name_or_number_rejected(self):
        q=copy.deepcopy(self.original)
        q["official_17_recent_past_races"][7]["name"]="FAKE HORSE"
        with self.assertRaisesRegex(ValueError,"HOLD_CONTEXT_LAST_RACE_NAMES"):
            context_stress(q)
        q=copy.deepcopy(self.original)
        q["official_17_recent_past_races"][0]["official_number"]=2
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EXACT_OFFICIAL_SEVENTEEN"):
            context_stress(q)

    def test_unverified_previous_finish_position_rejected(self):
        for field,value in (
            ("last_race_finish",None),
            ("last_race_fourth_corner_position",0),
        ):
            q=copy.deepcopy(self.original)
            q["official_17_recent_past_races"][7][field]=value
            with self.assertRaisesRegex(ValueError,"HOLD_INVALID_LAST_RUN"):
                context_stress(q)


if __name__=="__main__":
    unittest.main()
