"""A synthetic FIXED cohort checks future-meeting-date influence of two endpoints.

No actual horse names/section times are returned. Real-data run on the
12-date original Cannon archive is separately provenance gated.
"""
from __future__ import annotations

import math
from pathlib import Path
import sys
import unittest

try:
    import numpy
except ModuleNotFoundError:
    numpy=None

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
HAS_MAIN=False
if numpy is not None:
    try:
        from ecology_rq_rider_switch_consistency import source_timed_panel
        from keiba_rq_frozen_target_date_sensitivity import audit, _date_sensitivity
        HAS_MAIN=True
    except ModuleNotFoundError as e:
        if e.name not in (
           "ecology_rq_rider_switch_consistency",
           "ecology_rq_forward_alternative_history",
           "ecology_rq_early_pace_repeatability",
           "ecology_rq_2026_calendar_overlap",
           "ecology_rq_multigoing_h1_preflight",
           "ecology_rq_covariate_icc",
           "ecology_rq_race_fixed_icc"):
            raise


def toy_records():
    rows=[]
    # 24 stable horse IDs, exactly twelve distinct source dates.
    # Same future target is used for BOTH outcomes.
    for day in range(1,13):
        d=f"2026-10-{day:02d}"
        for k in range(24):
            h=f"FABRICATED_HORSE_{k:02d}"
            horse_effect=.33*math.sin(k*.49)
            day_effect=.18*math.sin(day*.72)
            seconds=11.+horse_effect+day_effect+.07*math.cos(.83*k+1.29*day)
            rows.append({
                "horse_id":h,"horse_name":h,
                "day":d,"race_number":3,"distance":"1400",
                "first_marker_m":150.,"first_section_sec":seconds,
                "class":"TOY_OPEN","ground":"Good",
                "jockey_license_id":str(1000+k+100*day),
                "trainer_license_id":str(3000+k),
            })
    return rows


@unittest.skipUnless(HAS_MAIN,"Fixed source RQ ecology dependencies are provided only in pinned main CI")
class FrozenRelativeAbsoluteDateSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=toy_records()
        cls.timed,_=source_timed_panel(cls.original,min_gps=4)

    def test_exact_same_frozen_population_and_distinct_endpoints(self):
        x=audit(self.timed,self.original,strict_class=False,draws=99,seed=44)
        self.assertEqual(x["status"],
                         "RETROSPECTIVE_FIXED_TARGET_DATE_CLUSTER_SENSITIVITY_ONLY")
        self.assertTrue(x["same_original_future_horses_and_dates_for_both_outcomes"])
        self.assertGreaterEqual(x["frozen_target_n_horses"],20)
        self.assertGreaterEqual(x["frozen_target_n_future_observations"],20)
        self.assertEqual(x["frozen_target_n_future_meeting_dates"],11)
        self.assertEqual(x["relative"]["full_equal_horse_RMSE"]["n_future_rows"],
                         x["absolute"]["full_equal_horse_RMSE"]["n_future_rows"])
        self.assertTrue(x["relative"]["full_denominator_not_changed_between_predictors"])
        self.assertTrue(x["absolute"]["full_denominator_not_changed_between_predictors"])
        self.assertTrue(x["absolute"]["these_are_not_future_meeting_outcomes_or_a_population_CI"])
        self.assertEqual(x["relative"]["historical_date_block_resamplings"],99)
        self.assertEqual(x["absolute"]["historical_date_block_resamplings"],99)
        self.assertEqual(x,audit(self.timed,self.original,strict_class=False,
                                 draws=99,seed=44))
        self.assertNotEqual(x["relative"]["full_equal_horse_RMSE"]["own_rmse"],
                            x["absolute"]["full_equal_horse_RMSE"]["own_rmse"])

    def test_original_class_treated_as_predeclared_sensitivity_not_selected(self):
        a=audit(self.timed,self.original,strict_class=False,draws=99,seed=45)
        b=audit(self.timed,self.original,strict_class=True,draws=99,seed=45)
        self.assertTrue(b["additional_original_class_matching"])
        # The constructed 24-horse toy has exactly one Class, so both
        # predefined endpoints legitimately coincide here.
        self.assertAlmostEqual(
            a["absolute"]["full_equal_horse_RMSE"]["other_minus_own_rmse"],
            b["absolute"]["full_equal_horse_RMSE"]["other_minus_own_rmse"])
        self.assertNotIn("FABRICATED_HORSE",str(a))

    def test_lodo_gate_retains_rejections_instead_of_claiming_significance(self):
        small=[]
        for day in range(9):
            for i in range(20):
                small.append({
                  "horse_id":f"TOY_{i}",
                  "day":f"2026-09-{day+1:02d}",
                  "relative":(.1,.1,.3),
                  "absolute":(11.,10.9,11.3),
                })
        out=_date_sensitivity(small,"absolute",draws=99,seed=22)
        self.assertEqual(out["attempted_future_date_deletions"],9)
        self.assertEqual(out["HOLD_deletions_below_original_threshold"],0)
        self.assertEqual(out["valid_deletions_positive_other_minus_own"],9)
        # One unique horse occurs on just the earliest original date.
        # Removing that date fails the old 20-ID gate; every other
        # date deletion still has this horse and can pass.
        small=[r for r in small
               if r["day"]=="2026-09-01" or r["horse_id"]!="TOY_19"]
        out=_date_sensitivity(small,"absolute",draws=99,seed=22)
        self.assertGreaterEqual(out["HOLD_deletions_below_original_threshold"],1)
        self.assertEqual(out["attempted_future_date_deletions"],9)
        self.assertEqual(
            out["valid_deletions_positive_other_minus_own"]+
            out["valid_deletions_negative_other_minus_own"],
            out["valid_deletions_original_minimum_evidence_support"])

    def test_short_future_cohort_or_outcome_leak_fails(self):
        from copy import deepcopy
        x=deepcopy(self.timed)
        reduced=[r for r in x if r["day"]<="2026-10-03"]
        o=audit(reduced,
                [r for r in self.original if r["day"]<="2026-10-03"],
                strict_class=False,draws=99)
        self.assertTrue(o["status"].startswith("HOLD_"))
        with self.assertRaises(ValueError):
            audit(self.timed,self.original,draws=3)


if __name__=="__main__":
    unittest.main()
