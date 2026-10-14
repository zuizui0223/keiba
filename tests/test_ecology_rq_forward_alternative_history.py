"""Fictional, explicitly sourced no-future leakage tests. NO real RQ animal rows."""
from __future__ import annotations

import copy
from datetime import date, timedelta
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_rider_switch_consistency import source_timed_panel
from ecology_rq_forward_alternative_history import (
    _paired_score, audit_other_horse_baselines,
    matched_source_rows_private,
)


def fake_annual_races(
    *,horses=40,days=12,seed=20261014,
    horse_signal=True,trainer_signal=False,retain_trainer=True,
    riders_change=True,
):
    """All IDs, jockeys, outcomes and trainer controls are FICTIONAL."""
    rng=random.Random(seed)
    ids=[f"FAKE-ANIMAL-{i:03d}" for i in range(horses)]
    animals={h:rng.gauss(0,.45) if horse_signal else 0. for h in ids}
    trainers={i:rng.gauss(0,.5) if trainer_signal else 0.
              for i in range(5)}
    result=[]
    for k in range(days):
        when=(date(2026,1,1)+timedelta(days=24*k)).isoformat()
        permutation=ids[:]
        rng.shuffle(permutation)
        for r in range(1,horses//8+1):
            race_shift=rng.gauss(0,.25)
            for h in permutation[(r-1)*8:r*8]:
                i=int(h.rsplit("-",1)[1])
                trainer=i%5
                rider=(i+3*k)%8 if riders_change else i
                result.append({
                    "horse_id":h,
                    "horse_name":f"FICTIONAL NAME {i:03d}",
                    "day":when,"race_number":r,
                    "distance":"1100 metres",
                    "first_marker_m":150.0,
                    "class":"FICTIONAL Group A",
                    "ground":"Good" if k%2 else "Soft",
                    "first_section_sec":10.+race_shift+animals[h]
                        +trainers[trainer]+rng.gauss(0,.06),
                    "trainer_license_id":(
                        str(10000+trainer) if retain_trainer else None),
                    "jockey_license_id":str(20000+rider),
                    "weight_kg":55.,
                })
    return result


class HorseVsOtherHorsesPastOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=fake_annual_races()
        cls.timed,_=source_timed_panel(cls.original)

    def test_planted_horse_identity_beats_past_other_horses_same_context(self):
        result=audit_other_horse_baselines(self.timed)
        entry=result["contexts"]["same_official_distance_and_exact_GPS_marker"]
        stats=entry["identical_scored_future_records"][
            "historical_other_horses_same_context"]
        self.assertEqual(stats["status"],
             "EXPLORATORY_IDENTICAL_FUTURE_HORSES_ROLE_CONTEXT_COMPARISON_ONLY")
        self.assertEqual(stats["distinct_original_HORSES_IDs"],40)
        self.assertGreater(stats["matched_chronological_future_source_rows"],100)
        self.assertGreater(stats["distinct_future_original_source_dates"],6)
        self.assertGreater(
            stats["past_other_horse_minus_focal_horse_RMSE_sec"],.04)
        self.assertTrue(stats["same_future_rows_for_each_compared_predictor"])
        self.assertTrue(result["no_original_horse_rider_trainer_ID_or_row_level_output"])
        self.assertTrue(result["not_starter_qualified_rider_verified_personality_heritability_or_H1_H2"])
        output=json.dumps(result)
        for forbidden in ("FAKE-ANIMAL","FICTIONAL NAME","FICTIONAL Group A",
                          '"horse_id"','"jockey_id"','"trainer_id"','"observed"'):
            self.assertNotIn(forbidden,output)

    def test_novel_documented_rider_is_actual_source_label_only(self):
        private,counts=matched_source_rows_private(self.timed)
        self.assertTrue(private)
        self.assertGreater(counts[
            "future_rows_with_prior_other_horse_same_jockey"],0)
        self.assertGreater(counts[
            "future_rows_with_prior_other_horse_same_trainer"],0)
        self.assertTrue(counts["prior_roles_are_documented_not_verified_actual_postrace"])
        self.assertTrue(counts["other_horse_role_controls_exclude_focal_HORSES_ID"])
        self.assertTrue(all(r["earlier_horse_observations"]>=1 for r in private))

    def test_trainer_only_planted_signal_is_not_identified_as_horse_genetics(self):
        true_trainer,_=source_timed_panel(fake_annual_races(
            horse_signal=False,trainer_signal=True))
        report=audit_other_horse_baselines(true_trainer)
        roles=report["contexts"]["same_official_distance_and_exact_GPS_marker"][
            "identical_scored_future_records"]
        trainer=roles["historical_other_horses_same_documented_trainer"]
        self.assertEqual(trainer["status"],
            "EXPLORATORY_IDENTICAL_FUTURE_HORSES_ROLE_CONTEXT_COMPARISON_ONLY")
        self.assertGreater(trainer["matched_chronological_future_source_rows"],100)
        self.assertLess(
            trainer["equal_HORSES_weighted_past_other_horse_baseline_RMSE_sec"],
            trainer["equal_HORSES_weighted_past_horse_RMSE_sec"])
        self.assertTrue(trainer[
            "post_hoc_selected_rider_model_not_CI_p_value_or_causal_decomposition"])

    def test_no_valid_trainer_licence_means_no_trainer_comparator(self):
        panel,_=source_timed_panel(fake_annual_races(retain_trainer=False))
        result=audit_other_horse_baselines(panel)
        cohorts=result["contexts"]["same_official_distance_and_exact_GPS_marker"][
            "identical_scored_future_records"]
        trainer=cohorts["historical_other_horses_same_documented_trainer"]
        self.assertEqual(trainer["matched_chronological_future_source_rows"],0)
        self.assertEqual(trainer["status"],
                         "HOLD_INSUFFICIENT_MATCHED_HORSE_AND_OTHER_HORSE_HISTORIES")
        self.assertNotIn("past_other_horse_minus_focal_horse_RMSE_sec",trainer)
        self.assertEqual(cohorts["historical_other_horses_same_context"][
            "status"],"EXPLORATORY_IDENTICAL_FUTURE_HORSES_ROLE_CONTEXT_COMPARISON_ONLY")

    def test_constant_rider_will_not_be_labeled_new_documented_rider(self):
        panel,_=source_timed_panel(fake_annual_races(riders_change=False))
        result=audit_other_horse_baselines(panel)
        ctx=result["contexts"]["same_official_distance_and_exact_GPS_marker"]
        self.assertEqual(ctx["source_readiness_counts_only"][
            "new_documented_jockey_future_rows_prior_to_alternative_baseline_gate"],0)
        vals=ctx["identical_scored_future_records"][
            "historical_other_horses_same_context"]
        self.assertEqual(vals["distinct_original_HORSES_IDs"],0)
        self.assertNotIn("equal_HORSES_weighted_past_horse_RMSE_sec",vals)

    def test_16_horses_held_even_if_the_sample_prediction_is_good(self):
        panel,_=source_timed_panel(fake_annual_races(horses=16))
        result=audit_other_horse_baselines(panel)
        for item in result["contexts"]["same_official_distance_and_exact_GPS_marker"][
                "identical_scored_future_records"].values():
            self.assertLessEqual(item["distinct_original_HORSES_IDs"],16)
            self.assertEqual(item["status"],
                             "HOLD_INSUFFICIENT_MATCHED_HORSE_AND_OTHER_HORSE_HISTORIES")
            self.assertNotIn("past_other_horse_minus_focal_horse_RMSE_sec",item)

    def test_reverse_input_order_cannot_inject_same_day_or_future_history(self):
        before=audit_other_horse_baselines(self.timed)
        after=audit_other_horse_baselines(list(reversed(self.timed)))
        b=before["contexts"]["same_official_distance_and_exact_GPS_marker"][
            "identical_scored_future_records"][
                "historical_other_horses_same_context"]
        a=after["contexts"]["same_official_distance_and_exact_GPS_marker"][
            "identical_scored_future_records"][
                "historical_other_horses_same_context"]
        self.assertEqual(b["matched_chronological_future_source_rows"],
                         a["matched_chronological_future_source_rows"])
        self.assertAlmostEqual(
            b["past_other_horse_minus_focal_horse_RMSE_sec"],
            a["past_other_horse_minus_focal_horse_RMSE_sec"],places=10)

    def test_current_future_y_does_not_change_past_scored_predictions(self):
        private,_=matched_source_rows_private(self.timed)
        latest=max(row["day"] for row in self.timed)
        shifted=copy.deepcopy(self.timed)
        for row in shifted:
            if row["day"]==latest:
                row["relative_seconds"]+=300.
        later,_=matched_source_rows_private(shifted)
        earlier1=[(r["horse_id"],r["day"],r["horse_prediction"],
                   r["context_prediction"],r["trainer_other_prediction"],
                   r["jockey_other_prediction"]) for r in private
                   if r["day"]<latest]
        earlier2=[(r["horse_id"],r["day"],r["horse_prediction"],
                   r["context_prediction"],r["trainer_other_prediction"],
                   r["jockey_other_prediction"]) for r in later
                   if r["day"]<latest]
        self.assertEqual(earlier1,earlier2)

    def test_focal_history_never_enters_its_other_horse_baseline(self):
        # No other HORSES ID can be the context predictor on this source.
        fake={
            "horse_id":"FAKE-SINGLE","distance":"1000 metres",
            "marker":200.0,"race_class":"FAKE CLASS",
            "race_number":1,"trainer_id":"100","horse_name":"FAKE-SINGLE",
        }
        timed=[
            {**fake,"day":"2026-01-01","relative_seconds":.7,"jockey_id":"101"},
            {**fake,"day":"2026-02-01","relative_seconds":.7,"jockey_id":"102"},
        ]
        private,counts=matched_source_rows_private(timed)
        self.assertEqual(len(private),1)
        self.assertIsNone(private[0]["context_prediction"])
        self.assertIsNone(private[0]["trainer_other_prediction"])
        self.assertIsNone(private[0]["jockey_other_prediction"])
        result=audit_other_horse_baselines(timed)
        s=result["contexts"]["same_official_distance_and_exact_GPS_marker"][
            "identical_scored_future_records"][
                "historical_other_horses_same_context"]
        self.assertEqual(s["status"],
                         "HOLD_INSUFFICIENT_MATCHED_HORSE_AND_OTHER_HORSE_HISTORIES")
        self.assertEqual(s["matched_chronological_future_source_rows"],0)

    def test_metadata_missing_does_not_affect_peer_mean_first_GPS_value(self):
        raw=fake_annual_races()
        baseline,_=source_timed_panel(raw)
        for row in raw:
            if int(row["horse_id"].split("-")[-1])%2:
                row["trainer_license_id"]=None
                row["jockey_license_id"]=None
        missing,_=source_timed_panel(raw)
        by_key=lambda panel:{
            (r["day"],r["horse_id"]):r["relative_seconds"] for r in panel
        }
        self.assertEqual(by_key(baseline),by_key(missing))

    def test_stricter_matching_original_class_can_withhold_support(self):
        raw=fake_annual_races()
        source_days=sorted({r["day"] for r in raw})
        for r in raw:
            r["class"]=("FAKE Class early" if r["day"]in source_days[:6]
                        else "FAKE Class late")
        panel,_=source_timed_panel(raw)
        z=audit_other_horse_baselines(panel)
        strict=z["contexts"]["also_same_original_race_Class"][
            "source_readiness_counts_only"]
        broad=z["contexts"]["same_official_distance_and_exact_GPS_marker"][
            "source_readiness_counts_only"]
        self.assertLess(strict[
            "new_documented_jockey_future_rows_prior_to_alternative_baseline_gate"],
            broad["new_documented_jockey_future_rows_prior_to_alternative_baseline_gate"])


if __name__=="__main__":
    unittest.main()
