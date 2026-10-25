#!/usr/bin/env python3
"""Eight future dates × eight flat-race numbers = 64 fixed proposed slots."""
from __future__ import annotations
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
    import keiba_secondary_64_market_slots as m


@unittest.skipIf(np is None,"NumPy-dependent upstream shared registry")
class Auxiliary64Registration(unittest.TestCase):
    def test_64_exact_unique_future_slots_on_eight_declared_dates(self):
        o=m.audit(asof="2026-10-25T23:18:00+09:00")
        self.assertEqual(o["predeclared_auxiliary_slots"],64)
        self.assertEqual(o["predeclared_distinct_meeting_dates"],8)
        self.assertEqual(len(o["slots"]),64)
        self.assertEqual(len({s["slot_id"] for s in o["slots"]}),64)
        self.assertEqual(o["race_numbers_in_each_date"],list(range(5,13)))
        self.assertEqual([tuple(x.values()) for x in
                          o["dates_and_selected_venues"]],
                         list(m.EXPLICIT_FIRST_8_DAY_VENUE))
        self.assertTrue(all(s["status"]=="UPCOMING_AUXILIARY_SLOT_UNACQUIRED"
                            for s in o["slots"]))

    def test_source_lock_calendar_26_cannot_be_rewritten_as_64(self):
        source=m.defined_slots()
        self.assertEqual(source[0]["slot_id"],"2026-10-31|京都|R05")
        self.assertEqual(source[7]["slot_id"],"2026-10-31|京都|R12")
        self.assertEqual(source[8]["slot_id"],"2026-11-01|東京|R05")
        self.assertEqual(source[-1]["slot_id"],"2026-11-22|京都|R12")
        self.assertTrue(all(s["source_calendar_git_blob_sha"]==
                            m.CALENDAR_GIT_BLOB_SHA for s in source))
        self.assertFalse(any(s["is_verified_official_race_ID_or_post_time"]
                             for s in source))
        self.assertFalse(any(s["counted_as_new_prospective_scored_trial"]
                             for s in source))

    def test_no_real_market_acquisitions_or_remote_commitments_are_invented(self):
        r=m.audit(asof="2026-10-25T23:18:00+09:00")
        self.assertTrue(r["old_26_race_calendar_unchanged"])
        self.assertEqual(r["auxiliary_real_future_market_targets_collected"],0)
        self.assertEqual(r["auxiliary_source_and_target_remote_Sha_authenticated"],0)
        self.assertEqual(r["future_independent_races_only_after_actual_proven_capture"],0)
        self.assertFalse(r["observed_60race_8date_development_guard_met"])
        self.assertTrue(r["nominal_60race_8date_development_slot_capacity"])
        self.assertTrue(r["cannot_pool_with_grade_26_without_deduplicating_race_ids"])

    def test_after_start_data_missing_remains_in_original_denominator(self):
        r=m.audit(asof="2026-11-15T18:00:00+09:00")
        self.assertEqual(len(r["slots"]),64)
        self.assertEqual(sum(s["status"]==
                            "PAST_UNCOLLECTED_DO_NOT_DROP_FROM_DENOMINATOR"
                             for s in r["slots"]),40)
        self.assertEqual(sum(s["status"]=="UPCOMING_AUXILIARY_SLOT_UNACQUIRED"
                             for s in r["slots"]),16)
        self.assertEqual(sum(s["status"]==
            "SAME_DATE_UNVERIFIED_POST_DO_NOT_DECIDE_IF_CLOSED"
            for s in r["slots"]),8)
        self.assertEqual(r["auxiliary_real_future_market_targets_collected"],0)

    def test_same_day_without_actual_post_clock_not_assumed_completed(self):
        r=m.audit(asof="2026-10-31T09:00:00+09:00")
        today=[s for s in r["slots"]
               if s["scheduled_date_jst"]=="2026-10-31"]
        self.assertEqual(len(today),8)
        self.assertTrue(all(s["status"]==
            "SAME_DATE_UNVERIFIED_POST_DO_NOT_DECIDE_IF_CLOSED"
            for s in today))

    def test_grade_calendar_changed_selection_causes_hard_stop(self):
        with patch.object(m,"EXPLICIT_FIRST_8_DAY_VENUE",
                          (("2026-10-31","東京"),)+m.EXPLICIT_FIRST_8_DAY_VENUE[1:]):
            with self.assertRaisesRegex(ValueError,"SELECTION_CHANGED"):
                m.defined_slots()


if __name__=="__main__":
    unittest.main()
