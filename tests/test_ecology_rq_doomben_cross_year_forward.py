"""Fully fabricated longitudinal HORSES IDs: Doomben year-forward source test."""
from __future__ import annotations

from pathlib import Path
import json
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_doomben_cross_year_forward import (
    score,_scored_rows_private,evaluate,context,
    MIN_HORSES_WITH_YEAR_BRIDGE
)
from test_ecology_rq_doomben_2025_marker_extension import fake_soap,fake_gps


def fictional_year_rows(*,marker=150.,shared_horses=32,flip=False,
                        change_class=False):
    """Purely synthetic all-positive GPS fields; 4 dates in each year."""
    if shared_horses % 8:
        raise ValueError("Synthetic horses must divide into groups of eight")
    rng=random.Random(10455)
    records=[]
    for year in (2025,2026):
        for day in range(1,5):
            for race in range(1,shared_horses//8+1):
                offset=rng.uniform(-.2,.2)
                for i in range(8):
                    ident=(race-1)*8+i
                    own=(ident%8-3.5)*.065
                    if flip and year==2026:
                        own=-own
                    val=10.+offset+own+rng.gauss(0,.018)
                    records.append({
                        "day":f"{year}-06-{day:02d}",
                        "race_number":race,
                        "horse_id":f"FAKE-HORSE-ID-{ident:03d}",
                        "horse_name":f"FICTIONAL HORSE {ident:03d}",
                        "distance":"950 metres",
                        "first_marker_m":marker,
                        "first_section_sec":val,
                        "class":"FAKE A" if year==2025 or not change_class else "FAKE B",
                        "ground":"Good" if day%2 else "Soft",
                    })
    return records


class CrossYearHistoryTests(unittest.TestCase):
    def test_locked_2025_predicts_repeated_IDs_in_2026_more_than_other_horses(self):
        fake=fictional_year_rows()
        relative,readiness=prepare(fake,min_race_telemetry=4)
        scored,cover=_scored_rows_private(relative,150.,False)
        self.assertEqual(cover["cross_year_horses_scored_against_identical_other_history"],32)
        self.assertEqual(len(scored),128)
        self.assertEqual(cover["original_2025_dates_with_positive_timed_GPS_in_this_marker"],4)
        self.assertEqual(cover["original_2026_dates_with_positive_timed_GPS_in_this_marker"],4)
        self.assertTrue(cover["no_2026_values_used_to_fit_a_historical_profile"])
        result=score(relative,marker=150.,strict_class=False)
        self.assertEqual(result["status"],
            "EXPLORATORY_REAL_HORSES_ID_2025_TO_2026_TIMING_PERSISTENCE_ONLY")
        rmse=result["equal_original_HORSES_ID_weighted_2026_RMSE_seconds"]
        self.assertGreater(rmse["OTHER_minus_OWN_RMSE_gain_positive_own_better"],0)
        self.assertGreater(rmse["ZERO_minus_OWN_RMSE_gain_positive_own_better"],0)
        self.assertLess(rmse["historical_focal_HORSES_ID"],
                        rmse["historical_OTHER_HORSES_same_marker_and_distance"])
        self.assertTrue(result["no_confidence_interval_or_causal_p_value"])
        influence=result["posthoc_leave_one_horse_and_one_2026_date_out_influence"]
        by_id=influence["one_original_HORSES_ID"]
        self.assertEqual(by_id["attempted_deletions"],32)
        self.assertEqual(by_id["numerically_and_source_supported_deletions"],32)
        self.assertTrue(by_id["not_an_uncertainty_interval"])
        self.assertLessEqual(by_id["OTHER_minus_OWN_RMSE_gain_min_sec"],
                             by_id["OTHER_minus_OWN_RMSE_gain_max_sec"])
        self.assertEqual(influence["one_2026_source_date"]["attempted_deletions"],4)
        self.assertNotIn("FAKE-HORSE-ID",json.dumps(result))

    def test_synthetic_year_reversal_can_make_own_history_worse(self):
        relative,_=prepare(fictional_year_rows(flip=True))
        r=score(relative,marker=150.,strict_class=False)
        self.assertEqual(r["status"],
            "EXPLORATORY_REAL_HORSES_ID_2025_TO_2026_TIMING_PERSISTENCE_ONLY")
        rmse=r["equal_original_HORSES_ID_weighted_2026_RMSE_seconds"]
        self.assertLess(rmse["OTHER_minus_OWN_RMSE_gain_positive_own_better"],0)
        self.assertLess(rmse["ZERO_minus_OWN_RMSE_gain_positive_own_better"],0)
        influence=r["posthoc_leave_one_horse_and_one_2026_date_out_influence"]
        self.assertEqual(influence["one_original_HORSES_ID"]["attempted_deletions"],32)
        self.assertGreater(
            influence["one_original_HORSES_ID"]["deletions_where_other_horses_history_better"],
            0
        )
        # Explicitly allow failure of the biological-persistence hypothesis.

    def test_twenty_horses_gate_cannot_approve_sparse_200m_sample(self):
        relative,_=prepare(fictional_year_rows(marker=200.,shared_horses=16))
        r=score(relative,marker=200.,strict_class=False)
        self.assertEqual(r["status"],
                         "HOLD_TOO_FEW_YEAR_BRIDGE_HORSES_OR_FUTURE_OUTCOMES")
        self.assertEqual(r["source_support"][
            "cross_year_horses_scored_against_identical_other_history"],16)
        self.assertNotIn("equal_original_HORSES_ID_weighted_2026_RMSE_seconds",r)
        self.assertTrue(r["no_RMSE_or_anecdotal_2026_individual_values_published"])

    def test_strict_original_class_mismatch_is_hold_not_same_trait(self):
        relative,_=prepare(fictional_year_rows(change_class=True))
        common=score(relative,marker=150.,strict_class=False)
        strict=score(relative,marker=150.,strict_class=True)
        self.assertEqual(common["status"],
            "EXPLORATORY_REAL_HORSES_ID_2025_TO_2026_TIMING_PERSISTENCE_ONLY")
        self.assertEqual(strict["status"],
            "HOLD_TOO_FEW_YEAR_BRIDGE_HORSES_OR_FUTURE_OUTCOMES")
        self.assertEqual(strict["source_support"][
            "cross_year_horses_scored_against_identical_other_history"],0)

    def test_2026_outcome_cannot_leak_into_2025_prediction(self):
        rows,_=prepare(fictional_year_rows())
        before,_=_scored_rows_private(rows,150.,False)
        changed=[dict(x) for x in rows]
        for item in changed:
            if item["day"].startswith("2026"):
                item["relative_early_section_sec"]+=.4
        after,_=_scored_rows_private(changed,150.,False)
        self.assertEqual(len(before),len(after))
        self.assertEqual([r["own_prediction"] for r in before],
                         [r["own_prediction"] for r in after])
        self.assertEqual([r["other_prediction"] for r in before],
                         [r["other_prediction"] for r in after])
        self.assertNotEqual([r["observed"] for r in before],
                            [r["observed"] for r in after])

    def test_2025_young_horses_do_not_silently_become_2026_match_if_only_names(self):
        rows,_=prepare(fictional_year_rows())
        changed=[dict(x) for x in rows]
        for item in changed:
            if item["day"].startswith("2026"):
                item["horse_id"]="NEW-"+item["horse_id"]
                # Names are deliberately unchanged; ID is authoritative.
        r=score(changed,marker=150.,strict_class=False)
        self.assertEqual(r["status"],
            "HOLD_TOO_FEW_YEAR_BRIDGE_HORSES_OR_FUTURE_OUTCOMES")
        self.assertEqual(r["source_support"][
            "cross_year_horses_scored_against_identical_other_history"],0)

    def test_only_existing_2025_2026_locked_source_dates_are_requested(self):
        # Public-source fixture from existing ecological audit: only
        # 5 per marker and year, so scientific RMSE MUST be on HOLD.
        data=evaluate(soap=fake_soap,gps=fake_gps,source_error_mode="raise")
        self.assertEqual(data["status"],
            "POSTHOC_DOOMBEN_YEAR_FORWARD_DATA_SUPPORT_NOT_CAUSAL_H1_H2")
        self.assertEqual(len(data["original_source_dates_successful"]),42)
        self.assertEqual(data["original_source_dates_HOLD"],[])
        self.assertEqual(set(data["cross_year_score_by_first_GPS_marker_and_context"]),{
            "150m_same_distance","150m_same_distance_and_Class",
            "200m_same_distance","200m_same_distance_and_Class"
        })
        for result in data["cross_year_score_by_first_GPS_marker_and_context"].values():
            self.assertIn("HOLD",result["status"])
            self.assertTrue(result["race_relative_GPS_target_uses_measured_contemporaneous_rivals"])
        self.assertTrue(data["no_original_HORSES_ID_name_rider_trainer_licence_individual_GPS_or_prediction_output"])
        encoded=json.dumps(data)
        self.assertNotIn("FAKE HORSE",encoded)
        self.assertNotIn('"501"',encoded)

    def test_unapproved_marker_refused(self):
        rows,_=prepare(fictional_year_rows())
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED_ORIGINAL_GPS_MARKER"):
            score(rows,marker=250.,strict_class=False)


if __name__=="__main__":
    unittest.main()
