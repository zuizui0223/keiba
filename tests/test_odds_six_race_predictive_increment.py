#!/usr/bin/env python3
"""No-lookahead retrospective score tests: 6 races, only 2 days."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from odds_six_race_predictive_increment import (
    STATUS, OFFICIAL_OCT12, METRICS, _odds_probabilities,
    collect_pre_race_forecasts, score_forecast, score_against_outcomes,
    summarize_scored_races, audit, verify_official_oct12,
    verify_official_shuka,
)


class SixRealRaceForecastAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictions = collect_pre_race_forecasts()

    def test_all_six_pure_prerace_price_forecasts(self):
        a=self.predictions
        self.assertEqual(len(a),6)
        self.assertEqual([r["race_number"] for r in a[:5]],[8,9,10,11,12])
        self.assertEqual([r["meeting_day"] for r in a],[*["2026-10-12"]*5,"2026-10-18"])
        self.assertEqual([len(r["early"]["numbers"]) for r in a],[11,12,10,18,16,17])
        for row in a:
            self.assertNotIn("actual_top3", str(row))
            self.assertEqual(row["early"]["numbers"],row["later"]["numbers"])
            for key in ("early","later"):
                self.assertAlmostEqual(sum(row[key]["win"]),1,places=10)
                self.assertAlmostEqual(sum(row[key]["top3"]),3,places=10)

    def test_source_jra_postrace_labels_are_separate_and_locked(self):
        doc,verified=verify_official_oct12(ROOT)
        self.assertGreater(verified.year,2025)
        self.assertEqual([doc["races"][str(k)]["positions"] for k in range(8,13)],
                         [[9,1,7],[4,3,12],[5,2,9],[1,4,9],[10,12,9]])
        shuka=verify_official_shuka(ROOT)
        self.assertEqual(shuka["top3"],[8,1,13])
        self.assertEqual(shuka["source_type"],"JRA_official")

    def test_five_same_day_early_late_win_and_place_scores(self):
        r=audit()
        self.assertEqual(r["status"], STATUS)
        self.assertEqual(r["total_independent_races"],6)
        self.assertEqual(r["distinct_meeting_dates"],2)
        self.assertEqual(r["distinct_horse_race_rows"],84)
        a=r["by_meeting_day"]["2026-10-12"]["metrics"]
        self.assertAlmostEqual(a["win_categorical_log_loss"]["early"],
                               1.954229882347829, places=9)
        self.assertAlmostEqual(a["win_categorical_log_loss"]["later"],
                               1.921389738634519, places=9)
        self.assertAlmostEqual(a["top3_binary_brier_mean_per_horse"]["early"],
                               .1317799085002302, places=9)
        self.assertAlmostEqual(a["top3_binary_brier_mean_per_horse"]["later"],
                               .1299077756824236, places=9)
        self.assertEqual(a["win_categorical_log_loss"]["number_races_late_better"],4)
        self.assertEqual(a["top3_binary_brier_mean_per_horse"]["number_races_late_better"],4)

    def test_shuka_inverts_winner_information_despite_slight_top3_improvement(self):
        r=audit()
        a=r["by_meeting_day"]["2026-10-18"]["metrics"]
        self.assertAlmostEqual(a["win_categorical_log_loss"]["early"],
                               .45279344284000933, places=9)
        self.assertAlmostEqual(a["win_categorical_log_loss"]["later"],
                               .5748070696418344, places=9)
        self.assertGreater(a["win_categorical_log_loss"]["late_minus_early"],0)
        self.assertLess(
            a["top3_binary_brier_mean_per_horse"]["late_minus_early"],0)
        self.assertEqual(a["win_categorical_log_loss"]["number_races_late_better"],0)
        self.assertEqual(a["top3_binary_brier_mean_per_horse"]["number_races_late_better"],1)

    def test_result_changes_do_not_change_prepared_forecasts(self):
        oct12,_=verify_official_oct12(ROOT)
        shuka=verify_official_shuka(ROOT)
        immutable=deepcopy(self.predictions)
        outcomes=deepcopy(oct12)
        scored=score_against_outcomes(immutable,outcomes,shuka)
        outcomes["races"]["8"]["positions"]=[1,9,7]
        changed=score_against_outcomes(immutable,outcomes,shuka)
        self.assertEqual(self.predictions,immutable)
        self.assertNotEqual(scored[0]["early_score"],changed[0]["early_score"])
        self.assertEqual(scored[-1]["early_score"],changed[-1]["early_score"])

    def test_race_vs_meeting_date_weighting_reverses_win_sign(self):
        r=audit()
        self.assertTrue(
            r["direction_changes_under_meeting_day_vs_race_weighting_win_log_loss"])
        e=r["equal_race_weighting_descriptive"]["win_categorical_log_loss"]
        d=r["equal_meeting_day_weighting_descriptive"]["win_categorical_log_loss"]
        self.assertLess(e["late_minus_early"],0)
        self.assertGreater(d["late_minus_early"],0)
        self.assertEqual(e["number_races_late_better"],4)
        self.assertEqual(
            r["equal_race_weighting_descriptive"]
            ["top3_binary_brier_mean_per_horse"]["number_races_late_better"],5)
        self.assertEqual(set(r["equal_race_weighting_descriptive"]),set(METRICS))

    def test_invalid_podium_validation_and_mass(self):
        p=self.predictions[0]["early"]
        with self.assertRaisesRegex(ValueError,"HOLD_TOP3_MISSING_FROM_PRICE_FIELD"):
            score_forecast(p,[9,9,7])
        with self.assertRaisesRegex(ValueError,"HOLD_TOP3_MISSING_FROM_PRICE_FIELD"):
            score_forecast(p,[9,1,99])
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_COMPLETE_FIELD"):
            _odds_probabilities({1:2.0,2:3,3:4,4:5})
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_WIN_QUOTE"):
            _odds_probabilities({1:2,2:3,3:4,4:5,5:0.3})

    def test_official_20261012_modified_file_is_rejected_by_sha(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            target=root/"data/2026-10-12/official-results-final.json"
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(OFFICIAL_OCT12.read_bytes())
            verify_official_oct12(root)
            target.write_bytes(target.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"HOLD_OFFICIAL_RESULT_SOURCE_DRIFT"):
                verify_official_oct12(root)

    def test_no_promotion_to_v31_or_pooled_claim(self):
        r=audit()
        self.assertIn("NO_HOLDOUT",r["status"])
        self.assertEqual(len(r["results"]),6)
        self.assertTrue(any("two meeting-day clusters" in s for s in r[
            "scientific_limitations"]))
        self.assertTrue(any("Do not optimize" in s for s in r["scientific_limitations"]))
        self.assertEqual([x["meeting_day"] for x in r["results"]].count("2026-10-18"),1)


if __name__=="__main__":
    unittest.main()
