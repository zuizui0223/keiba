#!/usr/bin/env python3
"""Original 64 slots -> first 16 JRA programme-only observation checkpoints."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
try:
    import numpy as np
except ModuleNotFoundError:
    np=None
if np is not None:
    import keiba_week1_licensed_capture_plan as plan


@unittest.skipIf(np is None,"Upstream fixed JRA cohort requires numeric CI")
class TwoUpcomingProgrammeTests(unittest.TestCase):
    def test_16_source_scoped_slots_zero_collected_outcomes_or_racecard(self):
        d=plan.plan_week1(asof="2026-10-26T01:14:00+09:00")
        self.assertEqual(d["predeclared_slots_in_first_two_dates"],16)
        self.assertEqual(d["first_two_auxiliary_dates_captured_as_scheduling_ideas"],2)
        self.assertEqual(d["possible_overlap_with_prior_26_graded_race_calendar"],2)
        self.assertEqual(len(d["slots"]),16)
        self.assertEqual(len({x["auxiliary_slot_id"] for x in d["slots"]}),16)
        self.assertEqual(d["actually_authenticated_SHA_pre_next_price"],0)
        self.assertEqual(d["observed_next_market_targets"],0)
        self.assertEqual(d["actual_full_field_win_wide_quote_snapshots_collected"],0)
        self.assertTrue(d["2026_oct31_and_nov01_race_programme_only_not_final_start_list"])

    def test_preliminary_JRA_post_clock_checkpoints_not_assumed_actual_updates(self):
        d=plan.plan_week1()
        slots={x["auxiliary_slot_id"]:x for x in d["slots"]}
        ky=slots["2026-10-31|京都|R11"]
        tok=slots["2026-11-01|東京|R11"]
        self.assertEqual(ky["planned_post_time_not_authoritative"],
                         "2026-10-31T15:45:00+09:00")
        self.assertEqual(tok["planned_post_time_not_authoritative"],
                         "2026-11-01T15:40:00+09:00")
        self.assertEqual(ky["programme_distance_m_not_verified_final"],1400)
        self.assertEqual(tok["programme_distance_m_not_verified_final"],2000)
        self.assertEqual(ky["candidate_first_full_WIN_observation_jst"],
                         "2026-10-31T14:05:00+09:00")
        self.assertEqual(ky["candidate_middle_WIN_and_WIDE_observation_jst"],
                         "2026-10-31T14:40:00+09:00")
        self.assertEqual(ky["target_start_only_after_actual_middle_update_minutes"],15)
        self.assertEqual(ky["target_end_only_after_actual_middle_update_minutes"],20)
        self.assertTrue(all(not x["confirmed_official_card_or_runner_numbers_available"]
                            for x in d["slots"]))
        self.assertTrue(all(not x["authorized_provider_WIN_WIDE_captured"]
                            for x in d["slots"]))

    def test_tentative_not_official_schedule_and_grade_overlap_deduplicated(self):
        d=plan.plan_week1()
        overlapping=[x for x in d["slots"]
                     if x["possible_grade_calendar_overlap_slots"]]
        self.assertEqual(len(overlapping),2)
        self.assertEqual(overlapping[0]["possible_grade_calendar_overlap_slots"],
                         ["2026-10-31|京都|ファンタジーS"])
        self.assertEqual(overlapping[1]["possible_grade_calendar_overlap_slots"],
                         ["2026-11-01|東京|天皇賞（秋）"])
        self.assertTrue(all("jra.jp/keiba/calendar2026/" in x["programme_source_url"]
                            for x in d["slots"]))
        self.assertFalse(d["no_actual_scheduled_future_background_fetch"] is False)

    def test_race_number_or_venue_source_drift_blocks_programme_use(self):
        with patch.dict(plan.PROGRAMME_PAGES["2026-11-01"]["races"],
                        {11:("15:40",2600,"芝")}):
            x=plan.plan_week1()
            self.assertEqual(
                next(s for s in x["slots"]
                     if s["auxiliary_slot_id"]=="2026-11-01|東京|R11")[
                    "programme_distance_m_not_verified_final"],2600)
            self.assertEqual(x["observed_next_market_targets"],0)
        with patch.dict(plan.PROGRAMME_PAGES,
                        {"2026-11-01":{"venue":"京都",
                          "official_preliminary_source_url":
                          "https://jra.jp/keiba/calendar2026/2026/11/1101.html",
                          "races":plan.PROGRAMME_PAGES["2026-11-01"]["races"]}}):
            with self.assertRaisesRegex(ValueError,"NONPREREGISTERED"):
                plan.plan_week1()


if __name__=="__main__":
    unittest.main()
