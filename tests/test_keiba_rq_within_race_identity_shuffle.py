"""Permuting ONLY historical within-race labels on invented 24-horse GPS.

Same frozen own-history vs other-history eligibility, same future rows.
Tests require the pinned main horse ecology modules; are skipped if
those modules are not available in generic CI. Scientific CI pins
the exact original main-ecology commit before running them.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
PINNED_MAIN=False
try:
    from keiba_rq_within_race_identity_shuffle import (
        identity_history_shuffle, _forecast_historical,
        _remap_original_gps)
    from ecology_rq_forward_alternative_history import (
        matched_source_rows_private, _context)
    PINNED_MAIN=True
except ModuleNotFoundError as exc:
    if exc.name not in (
        "ecology_rq_forward_alternative_history",
        "ecology_rq_rider_forward_check",
        "ecology_rq_rider_switch_consistency",
        "ecology_rq_early_pace_repeatability",
        "ecology_rq_source_icc_uncertainty_audit",
        "ecology_rq_2026_calendar_overlap",
        "ecology_rq_single_race_id_probe",
    ):
        raise


def fake_timed():
    """All measured values, jockey IDs, horses and races are synthetic."""
    dates=[
       "2026-02-16","2026-03-12","2026-03-26","2026-04-04",
       "2026-04-09","2026-05-15","2026-05-29","2026-07-23",
       "2026-08-22","2026-08-28","2026-08-29","2026-10-11"
    ]
    horses=[f"NOT_A_REAL_HORSE_{i:02d}" for i in range(24)]
    out=[]
    for di,day in enumerate(dates):
        for i,h in enumerate(horses):
            val=.35*(i-11.5)/11.5+.012*((i+di)%3-1)
            # Centering is by all observed peers, not focal horse.
            out.append({
                "horse_id":h,"day":day,"race_number":4,
                "distance":"1400","marker":150.0,
                "race_class":"TOY_OPEN",
                "relative_seconds":val,
                "jockey_id":str(100+i*4+di%2),
                "trainer_id":str(200+i%5),
            })
    return out


@unittest.skipUnless(PINNED_MAIN,"Pinned main ecology source is only present in dedicated RQ CI")
class HistoricalHorseIdentityNullSyntheticTests(unittest.TestCase):
    def test_original_locked_profile_matches_same_future_denominator(self):
        rows=fake_timed()
        r=identity_history_shuffle(rows,permutations=49,seed=22)
        self.assertEqual(
            r["status"],
            "RETROSPECTIVE_SAME_RQ_SOURCE_WITHIN_RACE_HISTORY_IDENTITY_NULL")
        self.assertEqual(r["matched_chronological_future_source_rows"],24*11)
        self.assertEqual(r["distinct_original_HORSES_IDs"],24)
        self.assertGreater(
            r["null_mean_equal_horse_RMSE_seconds"],
            r["previously_locked_context_history_real_source_rmse_seconds"])
        self.assertTrue(r["same_GPS_field_context_and_future_denominator_in_all_nulls"])
        self.assertTrue(r["no_population_p_value_or_confidence_interval"])
        for label in ("NOT_A_REAL_HORSE_","first_section_seconds",
                      '"horse_id"',"jockey_id"):
            self.assertNotIn(label,str(r))
        again=identity_history_shuffle(rows,permutations=49,seed=22)
        self.assertEqual(again,r)

    def test_tight_race_class_source_returns_stable_original_chronological_profile(self):
        r=identity_history_shuffle(
            fake_timed(),strict_class=True,permutations=49,seed=22)
        self.assertEqual(r["matched_chronological_future_source_rows"],264)
        self.assertTrue(r["race_class_also_matched"])
        self.assertLess(r["previously_locked_context_history_real_source_rmse_seconds"],
                        r["null_mean_equal_horse_RMSE_seconds"])

    def test_future_test_date_relative_gps_cannot_reach_earlier_or_own_history_prediction(self):
        rows=fake_timed()
        cand,_=matched_source_rows_private(rows,strict_class=False)
        chosen=[r for r in cand if r["context_prediction"] is not None]
        unchanged={
            (r["day"],r["race_number"],r["horse_id"]):r["relative_seconds"]
            for r in rows
        }
        original=_forecast_historical(rows,chosen,False,unchanged)
        future_day=max(r["day"] for r in rows)
        mutated=dict(unchanged)
        for k in mutated:
            if k[0]==future_day:
                mutated[k]=mutated[k]+(1 if k[2].endswith("00") else 0)
        after=_forecast_historical(rows,chosen,False,mutated)
        for index,r in enumerate(chosen):
            if r["day"]<=future_day:
                self.assertEqual(original[index],after[index])

    def test_permutation_only_reshuffles_values_within_real_race(self):
        rows=fake_timed()
        mapped=_remap_original_gps(rows,random.Random(12))
        self.assertEqual(len(mapped),len(rows))
        for day in {r["day"] for r in rows}:
            a=sorted(float(r["relative_seconds"]) for r in rows
                     if r["day"]==day)
            b=sorted(v for k,v in mapped.items() if k[0]==day)
            self.assertEqual(a,b)

    def test_unidentifiable_old_eligibility_is_hold_not_false_support(self):
        rows=fake_timed()
        for r in rows:
            r["jockey_id"]="SAME_SOURCE_DECLARED_JOCKEY"
        result=identity_history_shuffle(rows,permutations=49)
        self.assertEqual(result["status"],
                         "HOLD_ORIGINAL_CONTEXT_DID_NOT_PASS_EVIDENCE_GATE")
        self.assertNotIn("null_mean_equal_horse_RMSE_seconds",result)

    def test_bad_design_or_duplicate_rows_cannot_pass(self):
        with self.assertRaises(ValueError):
            identity_history_shuffle(fake_timed(),permutations=8)
        rows=fake_timed()
        rows.append(rows[-1].copy())
        with self.assertRaises(ValueError):
            identity_history_shuffle(rows,permutations=49)


if __name__=="__main__":
    unittest.main()
