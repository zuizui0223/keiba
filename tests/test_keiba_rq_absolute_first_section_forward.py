"""Artificial 24-horse, 12-day ABSOLUTE GPS prediction and identity controls."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
PINNED_MAIN=False
try:
    from keiba_rq_absolute_first_section_forward import (
        absolute_first_section_forward_audit,
        _setup, _forecasts, _shuffle_abs_races)
    PINNED_MAIN=True
except ModuleNotFoundError as e:
    if e.name not in ("ecology_rq_forward_alternative_history",
                      "ecology_rq_rider_forward_check",
                      "ecology_rq_rider_switch_consistency",
                      "ecology_rq_early_pace_repeatability"):
        raise


def toy():
    dates=[
        "2026-02-16","2026-03-12","2026-03-26","2026-04-04",
        "2026-04-09","2026-05-15","2026-05-29","2026-07-23",
        "2026-08-22","2026-08-28","2026-08-29","2026-10-11"
    ]
    timed=[]
    original=[]
    for d,day in enumerate(dates):
        for h in range(24):
            horse=f"TOY_HORSE_{h:02d}"
            val=9.2+.045*d+.42*(h-11.5)/11.5+.014*((d+h*2)%3-1)
            timed.append({
                "day":day,"race_number":4,"horse_id":horse,
                "distance":"1400","marker":150.0,
                "race_class":"TOY_CLASS",
                "jockey_id":str(1000+h*100+d),
                "trainer_id":str(2000+h%5),
                "relative_seconds":val-9.2-.045*d
            })
            original.append({
                "day":day,"race_number":4,"horse_id":horse,
                "first_section_sec":val
            })
    return timed,original


@unittest.skipUnless(PINNED_MAIN,"Pinned main source must be included by scientific runner")
class AbsoluteFirstSectionSyntheticTests(unittest.TestCase):
    def test_absolute_earlier_horse_improves_and_is_not_relative_metric(self):
        timed,original=toy()
        r=absolute_first_section_forward_audit(
            timed,original,permutations=49,seed=4)
        self.assertEqual(r["matched_future_rows"],24*11)
        self.assertEqual(r["matched_distinct_horse_IDs"],24)
        self.assertEqual(r["status"],
                         "RETROSPECTIVE_ORIGINAL_SOURCE_ABSOLUTE_FIRST_GPS_FORWARD_IDENTITY_CHECK")
        self.assertLess(
            r["observed_original_horse_history_absolute_RMSE_seconds"],
            r["observed_original_other_horse_history_absolute_RMSE_seconds"])
        self.assertLess(
            r["observed_original_horse_history_absolute_RMSE_seconds"],
            r["null_mean_absolute_RMSE_seconds"])
        self.assertTrue(r["target_is_not_peer_relative"])
        self.assertTrue(r["context_and_future_target_population_fixed_across_nulls"])
        self.assertTrue(r["no_population_p_value_CI_or_biological_causality_inferred"])
        self.assertNotIn("TOY_HORSE_",str(r))
        self.assertEqual(
            r,
            absolute_first_section_forward_audit(
                timed,original,permutations=49,seed=4))

    def test_strict_original_class_still_has_same_locked_future_rows(self):
        timed,orig=toy()
        a=absolute_first_section_forward_audit(
            timed,orig,strict_class=False,permutations=49,seed=5)
        b=absolute_first_section_forward_audit(
            timed,orig,strict_class=True,permutations=49,seed=5)
        self.assertEqual(a["matched_future_rows"],b["matched_future_rows"])
        self.assertEqual(
            a["observed_original_horse_history_absolute_RMSE_seconds"],
            b["observed_original_horse_history_absolute_RMSE_seconds"])
        self.assertTrue(b["source_class_matched"])

    def test_future_absolute_time_does_not_reach_its_current_date_prediction(self):
        timed,original=toy()
        target,truth,_,elig=_setup(timed,original,False)
        earlier,_=_forecasts(timed,target,truth,truth,False)
        late=max(r["day"] for r in original)
        changed=dict(truth)
        for k in changed:
            if k[0]==late:
                changed[k]+=float((k[2].endswith("00")))*2.0
        after,_=_forecasts(timed,target,changed,changed,False)
        for row,a,b in zip(target,earlier,after):
            self.assertEqual(a,b)

    def test_historical_only_identity_shuffle_keeps_context_anchor(self):
        import random
        timed,original=toy()
        target,truth,races,_=_setup(timed,original,False)
        shuffled=_shuffle_abs_races(truth,races,random.Random(123))
        orig,_=_forecasts(timed,target,truth,truth,False)
        rand,anchor=_forecasts(timed,target,truth,shuffled,False)
        _,original_anchor=_forecasts(timed,target,truth,truth,False)
        self.assertEqual(anchor,original_anchor)
        self.assertNotEqual(rand,orig)
        self.assertEqual(len(shuffled),len(truth))

    def test_broken_history_or_missing_new_jockey_returns_hold(self):
        timed,original=toy()
        for r in timed:
            r["jockey_id"]="SAME_DECLARED_ID"
        r=absolute_first_section_forward_audit(
            timed,original,permutations=49)
        self.assertEqual(r["status"],
                         "HOLD_ORIGINAL_HORSE_HISTORY_EVIDENCE_GATE")
        self.assertNotIn(
            "observed_original_horse_history_absolute_RMSE_seconds",r)
        timed,original=toy()
        original.pop()
        with self.assertRaises(ValueError):
            absolute_first_section_forward_audit(
                timed,original,permutations=49)

    def test_invalid_inputs_and_duplicate_horse_date_fail(self):
        timed,original=toy()
        with self.assertRaises(ValueError):
            absolute_first_section_forward_audit(
                timed,original,permutations=5)
        timed.append(timed[0].copy())
        with self.assertRaises(ValueError):
            absolute_first_section_forward_audit(
                timed,original,permutations=49)


if __name__=="__main__":
    unittest.main()
