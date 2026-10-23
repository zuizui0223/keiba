#!/usr/bin/env python3
"""Real archived odds cohort (one race is one unit, not each runner)."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from odds_real_multirace_archive_audit import (
    SOURCE_SHA, STATUS, audit, _one_race, read_file,
)
from shuka2026_odds_information_hierarchy import SOURCE as SHUKA_SOURCE


class RealMultipleRaceTimeSeriesAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=read_file(ROOT,SOURCE_SHA[8][0])
        cls.b=read_file(ROOT,SOURCE_SHA[8][1])

    def test_all_5_Oct12_plus_1_Shuka_completed_prestart(self):
        s=audit()
        self.assertEqual(s["status"],STATUS)
        self.assertEqual(s["distinct_real_races"],6)
        self.assertEqual(s["distinct_meeting_dates"],2)
        self.assertEqual(s["win_horse_entries_with_2_or_more_prestart_captures"],84)
        self.assertEqual(s["kyoto_20261012_total_runner_entries"],67)
        self.assertEqual(s["kyoto_20261012_horses_absolute_quote_move_ge20pct"],2)
        self.assertEqual(s["kyoto_20261012_top_five_membership_unchanged_races"],4)
        self.assertEqual(len(s["shuka_snapshot_adjacent_transitions"]),3)
        self.assertEqual(s["prediction_skill"],"HOLD_NO_RACE_BLOCKED_FUTURE_HOLDOUT")
        self.assertFalse(s["winning_probability_calibrated"])
        self.assertFalse(s["official_time_critical_update_clock_verified_for_all_sources"])

    def test_Oct12_actual_TV_not_pseudoreplication(self):
        rs=audit()["kyoto_20261012_races"]
        self.assertEqual([q["n_horses"] for q in rs],[11,12,10,18,16])
        for q,val in zip(rs,[5.3686,2.387,2.5717,.9126,1.718]):
            self.assertAlmostEqual(
                q["normalized_inverse_quote_total_variation_pp"],val,delta=.0003)
            self.assertTrue(q["twenty_percent_is_a_preexisting_monitoring_threshold_not_predictive"])
            self.assertGreater(q["minutes_between_displayed_update_times"],50)
            self.assertLess(q["minutes_between_displayed_update_times"],70)

    def test_initial_quote_bands_are_descriptive_only(self):
        x=audit()["kyoto_20261012_initial_odds_band_descriptive"]
        self.assertEqual([v["horse_entries"] for v in x],[7,26,23,11])
        self.assertEqual(sum(v["horses_over20pct"] for v in x),2)
        self.assertTrue(all(z["independent_sample_unit_is_race_not_horse"] for z in x))

    def test_full_field_roster_exactly_matched(self):
        s=_one_race(self.a,self.b,8)
        self.assertEqual(s["n_horses"],11)
        self.assertTrue(s["full_field_top_five_membership_unchanged"])
        self.assertEqual(s["horses_absolute_quote_move_ge20pct"],2)

    def test_change_early_quote_after_sealed_source_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            for points in SOURCE_SHA.values():
                for item in points:
                    target=path/item[0]
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(ROOT/item[0],target)
            for item in SHUKA_SOURCE.values():
                target=path/item[0]
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/item[0],target)
            self.assertEqual(audit(path)["distinct_real_races"],6)
            bad=path/SOURCE_SHA[8][0][0]
            bad.write_bytes(bad.read_bytes()+b"\n")
            with self.assertRaisesRegex(ValueError,"HOLD_UPSTREAM_SOURCE_DRIFT"):
                audit(path)

    def test_source_clock_and_missing_rows_fail_instead_of_imputing(self):
        early=copy.deepcopy(self.a)
        late=copy.deepcopy(self.b)
        early["start_jst"]="2026-10-12T13:20:00+09:00"
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_TIME_TRAVEL"):
            _one_race(early,late,8)
        early=copy.deepcopy(self.a)
        late=copy.deepcopy(self.b)
        late["quotes"]["win"].pop()
        with self.assertRaisesRegex(ValueError,"HOLD_INCOMPLETE_FULL_FIELD"):
            _one_race(early,late,8)
        late=copy.deepcopy(self.b)
        late["quotes"]["win"][0]["selection"]=[9,10]
        with self.assertRaisesRegex(ValueError,"HOLD_INCONSISTENT_WIN"):
            _one_race(self.a,late,8)

    def test_horses_cannot_be_duplicated_by_market_rank(self):
        late=copy.deepcopy(self.b)
        late["quotes"]["win"][1]["selection"] = late["quotes"]["win"][0]["selection"]
        with self.assertRaisesRegex(ValueError,"HOLD_DUPLICATE_LATE_HORSE"):
            _one_race(self.a,late,8)


if __name__=="__main__":
    unittest.main()
