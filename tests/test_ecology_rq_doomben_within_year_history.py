"""Only invented horses and source snapshots: within-year Doomben history tests."""
from __future__ import annotations

import copy
from datetime import date,timedelta
import json
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from ecology_rq_early_pace_repeatability import prepare
from ecology_rq_doomben_within_year_history import (
    analyze,score_private,scoring_summary,evaluate,
    original_date_deletion_support_sensitivity,
)
from ecology_rq_doomben_2025_marker_extension import LOCKED_DATES
from test_ecology_rq_doomben_2025_marker_extension import fake_soap,fake_gps


def fictional_annual_records(*,ids=32,source_days=8,flip_2026=False,
                             no_individual=False,changing_class=False,
                             year_2026_marker=150.):
    """All IDs/identities are fictional. Preserve one same-day start per horse."""
    if ids%8:
        raise ValueError("Synthetic horse population must divide by eight.")
    rng=random.Random(9021)
    effects={i:(rng.gauss(0,.5) if not no_individual else 0.)
             for i in range(ids)}
    out=[]
    for year in (2025,2026):
        for day_index in range(source_days):
            when=(date(year,1,3)+timedelta(days=28*day_index)).isoformat()
            horses=list(range(ids))
            rng.shuffle(horses)
            for race_number in range(1,ids//8+1):
                random_race_mean=rng.gauss(0,1.)
                for ident in horses[(race_number-1)*8:race_number*8]:
                    effect=effects[ident]
                    if flip_2026 and year==2026:
                        effect=-effect
                    cls=("SYNTH CLASS A" if day_index<4 else "SYNTH CLASS B"
                         ) if changing_class else "SYNTH CLASS A"
                    out.append({
                        "day":when,"race_number":race_number,
                        "horse_id":f"FAKE-ANIMAL-{ident:03d}",
                        "horse_name":f"FICTIONAL-HORSE-{ident:03d}",
                        "distance":"1100 metres","class":cls,
                        "ground":"Good",
                        "first_marker_m":(year_2026_marker if year==2026 else 150.),
                        "first_section_sec":
                            10.+random_race_mean+effect+rng.gauss(0,.08),
                    })
    return out


class SameCourseWithinYear(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.realistic,_=prepare(fictional_annual_records())

    def test_planted_identity_yields_positive_same_year_signal_in_each_year(self):
        for year in ("2025","2026"):
            score=scoring_summary(self.realistic,year=year,
                                  marker=150.,strict_class=False)
            self.assertEqual(score["status"],
                "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")
            cov=score["comparison_population"]
            self.assertEqual(cov["scored_anonymous_distinct_original_HORSES_IDs"],32)
            self.assertEqual(cov["scored_anonymous_original_future_rows"],224)
            self.assertEqual(cov["distinct_future_original_meeting_dates_scored"],7)
            self.assertGreater(score["equal_horse_RMSE_seconds"][
                "OTHER_minus_OWN_positive_horse_history_better"],.05)
            self.assertTrue(score["not_an_independent_cohort_or_valid_population_CI"])
            r=json.dumps(score)
            self.assertNotIn("FAKE-ANIMAL-",r)
            self.assertNotIn("FICTIONAL-HORSE-",r)

    def test_crossyear_behavior_reversal_does_not_make_same_year_change_causal(self):
        data,_=prepare(fictional_annual_records(flip_2026=True))
        for year in ("2025","2026"):
            score=scoring_summary(data,year=year,marker=150.,strict_class=False)
            self.assertEqual(score["status"],
                "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")
            self.assertGreater(
                score["equal_horse_RMSE_seconds"][
                    "OTHER_minus_OWN_positive_horse_history_better"],0)
            self.assertTrue(score["not_a_causal_year_trainer_jockey_ground_or_evolution_effect"])

    def test_no_horse_signal_does_not_force_positive_advantage(self):
        data,_=prepare(fictional_annual_records(no_individual=True))
        x=scoring_summary(data,year="2025",marker=150.,strict_class=False)
        self.assertEqual(x["status"],
            "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")
        self.assertLess(abs(x["equal_horse_RMSE_seconds"][
            "OTHER_minus_OWN_positive_horse_history_better"]),.07)

    def test_small_repeated_cohort_HOLD_not_zero_effect(self):
        rows,_=prepare(fictional_annual_records(ids=16))
        out=scoring_summary(rows,year="2025",marker=150.,strict_class=False)
        self.assertEqual(out["status"],
            "HOLD_TOO_FEW_WITHIN_YEAR_REPEATED_HORSES_FUTURE_ROWS_OR_DATES")
        self.assertEqual(out["comparison_population"][
            "scored_anonymous_distinct_original_HORSES_IDs"],16)
        self.assertNotIn("equal_horse_RMSE_seconds",out)

    def test_source_date_deletion_reveals_borderline_positive_result_is_fragile(self):
        # 7 fictional dates -> 6 different post-history evaluation dates:
        # exactly meets the previously locked 6-date support requirement.
        # Removing ANY original date makes it fail (only 5 dated
        # future comparisons), without changing the effect or scoring rule.
        data,_=prepare(fictional_annual_records(source_days=7))
        original=scoring_summary(
            data,year="2025",marker=150.,strict_class=False)
        self.assertEqual(
            original["status"],
            "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")
        diagnostic=original_date_deletion_support_sensitivity(
            data,year="2025",marker=150.,strict_class=False,
            baseline=original)
        self.assertEqual(diagnostic["original_source_dates_with_positive_GPS_for_marker"],7)
        self.assertEqual(diagnostic["delete_one_original_date_refits_attempted"],7)
        self.assertEqual(diagnostic["refits_returning_HOLD_after_one_date_missing"],7)
        self.assertEqual(diagnostic["refits_passing_PREVIOUSLY_FROZEN_minimum_support"],0)
        self.assertNotIn("valid_refit_OTHER_minus_OWN_gain_min_sec",diagnostic)
        self.assertTrue(diagnostic["not_an_independent_prospective_validation"])

    def test_unsupported_source_data_is_not_rescored_for_positive_signal(self):
        data,_=prepare(fictional_annual_records(ids=16))
        d=original_date_deletion_support_sensitivity(
            data,year="2025",marker=150.,strict_class=False)
        self.assertEqual(
            d["status"],"HOLD_ORIGINAL_YEAR_MARKER_CONTEXT_ALREADY_UNSUPPORTED")
        self.assertFalse(d["recalculation_on_unsupported_original_data"])

    def test_too_few_original_future_dates_HOLD(self):
        data,_=prepare(fictional_annual_records(source_days=4))
        s=scoring_summary(data,year="2025",marker=150.,strict_class=False)
        self.assertEqual(s["comparison_population"][
            "distinct_future_original_meeting_dates_scored"],3)
        self.assertEqual(s["status"],
            "HOLD_TOO_FEW_WITHIN_YEAR_REPEATED_HORSES_FUTURE_ROWS_OR_DATES")
        self.assertNotIn("equal_horse_RMSE_seconds",s)

    def test_source_class_change_restarts_history_not_assumed_nested_HOLD(self):
        data,_=prepare(fictional_annual_records(changing_class=True))
        broad=scoring_summary(data,year="2025",marker=150.,strict_class=False)
        strict=scoring_summary(data,year="2025",marker=150.,strict_class=True)
        self.assertEqual(broad["status"],
            "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")
        # After a class change, the first new-Class date has no matching
        # horse history, but there are enough later new-Class dates that
        # strict-Class scoring still meets the predeclared support gate.
        self.assertEqual(strict["status"],
            "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")
        self.assertEqual(strict["comparison_population"][
            "distinct_future_original_meeting_dates_scored"],6)
        self.assertEqual(broad["comparison_population"][
            "distinct_future_original_meeting_dates_scored"],7)
        self.assertLess(strict["comparison_population"][
            "scored_anonymous_original_future_rows"],
            broad["comparison_population"]["scored_anonymous_original_future_rows"])

    def test_2025_and_2026_are_never_combined_into_one_historical_profile(self):
        data,_=prepare(fictional_annual_records(year_2026_marker=200.))
        a=scoring_summary(data,year="2025",marker=150.,strict_class=False)
        b=scoring_summary(data,year="2026",marker=150.,strict_class=False)
        c=scoring_summary(data,year="2026",marker=200.,strict_class=False)
        self.assertEqual(a["status"],
            "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")
        self.assertEqual(b["status"],
            "HOLD_TOO_FEW_WITHIN_YEAR_REPEATED_HORSES_FUTURE_ROWS_OR_DATES")
        self.assertEqual(b["comparison_population"][
            "original_positive_timed_GPS_rows_for_marker"],0)
        self.assertEqual(c["status"],
            "EXPLORATORY_SAME_VENUE_WITHIN_YEAR_SOURCE_ID_HISTORY_ONLY")

    def test_future_scores_cannot_change_past_history_predictions(self):
        a,_=score_private(self.realistic,year="2025",marker=150.,strict_class=False)
        changed=copy.deepcopy(self.realistic)
        finalday=max(r["day"] for r in changed if r["day"].startswith("2025"))
        for r in changed:
            if r["day"]==finalday:
                r["relative_early_section_sec"]+=.88
        b,_=score_private(changed,year="2025",marker=150.,strict_class=False)
        first=[(r["horse_id"],r["day"],r["own"],r["other"])
               for r in a if r["day"]<finalday]
        second=[(r["horse_id"],r["day"],r["own"],r["other"])
                for r in b if r["day"]<finalday]
        self.assertEqual(first,second)
        self.assertNotEqual(a,b)

    def test_future_2026_records_cannot_affect_2025_score(self):
        data=scoring_summary(self.realistic,year="2025",marker=150.,strict_class=False)
        changed=copy.deepcopy(self.realistic)
        for r in changed:
            if r["day"].startswith("2026"):
                r["relative_early_section_sec"]+=500
        future=scoring_summary(changed,year="2025",marker=150.,strict_class=False)
        self.assertEqual(data,future)

    def test_input_order_reversal_is_invariant(self):
        before=scoring_summary(self.realistic,year="2025",marker=150.,strict_class=False)
        after=scoring_summary(list(reversed(self.realistic)),
                              year="2025",marker=150.,strict_class=False)
        self.assertEqual(before,after)

    def test_only_prelocked_42_original_source_dates_and_safe_aggregation(self):
        all_keys=list(LOCKED_DATES)
        data=analyze(self.realistic,source_dates=all_keys,source_HOLD_dates=[],
                     source_manifests={})
        self.assertEqual(len(data["comparisons_by_year_marker_context"]),8)
        self.assertEqual(data["original_source_calendar"]["fixed_2025_date_count"],23)
        self.assertEqual(data["original_source_calendar"]["fixed_2026_date_count"],19)
        self.assertTrue(data["no_individual_horse_names_IDs_role_IDs_section_times_or_predictions_exported"])
        serialized=json.dumps(data)
        self.assertNotIn("FAKE-ANIMAL",serialized)
        self.assertNotIn("FICTIONAL-HORSE",serialized)
        self.assertNotIn('"horse_id"',serialized)

    def test_missing_locked_date_never_becomes_zero_GPS(self):
        dates=list(LOCKED_DATES)
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EXACTLY_PREVIOUSLY_LOCKED"):
            analyze(self.realistic,source_dates=dates[:-1],
                    source_HOLD_dates=[],source_manifests={})

    def test_unsupported_year_and_marker_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED"):
            score_private(self.realistic,year="2027",marker=150.,strict_class=False)
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED"):
            score_private(self.realistic,year="2025",marker=250.,strict_class=False)

    def test_original_source_adapter_does_not_invent_missing_records(self):
        result=evaluate(soap=fake_soap,gps=fake_gps,source_error_mode="raise")
        self.assertEqual(result["original_source_calendar"][
            "original_locked_source_dates_successful"],42)
        self.assertEqual(result["original_source_calendar"][
            "original_source_HOLD_dates"],[])
        self.assertTrue(result["not_preregistered_annual_personality_decay_or_betting"])
        for result in result["comparisons_by_year_marker_context"].values():
            self.assertEqual(result["status"],
                "HOLD_TOO_FEW_WITHIN_YEAR_REPEATED_HORSES_FUTURE_ROWS_OR_DATES")
            self.assertNotIn("equal_horse_RMSE_seconds",result)


if __name__=="__main__":
    unittest.main()
