"""Absolute-speed H2 checks on wholly fictional horses and races."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_demo_competitors import fabricate_competition
from ecology_panel import REQUIRED, load_panel, lagged_features
from ecology_h2_pilot import competition_frame
from ecology_h2_absolute_speed import frame_with_individual_speed, run
from ecology_h2_absolute_stress import stress


def panel(temp,rows):
    path=Path(temp)/"fictional.csv"
    with path.open("w",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,fieldnames=list(REQUIRED)+["first_call_position"])
        w.writeheader()
        w.writerows(rows)
    return path


class H2AbsoluteSpeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake=fabricate_competition(n_days=65,n_horses=36,seed=512,
                                       interaction=-0.9)

    def test_rival_outcome_can_change_focal_z_but_not_focal_raw_speed(self):
        before=[dict(v) for v in self.fake]
        changed=[dict(v) for v in before]
        race="FAKE-COMP-R0045"
        focal=next(v for v in before if v["race_id"]==race)
        rival=next(v for v in changed
                   if v["race_id"]==race and v["horse_id"]!=focal["horse_id"])
        rival["finish_time_s"]=str(float(rival["finish_time_s"])*1.3)
        with tempfile.TemporaryDirectory() as tmp:
            f0=lagged_features(load_panel(panel(tmp,before)))
            f1=lagged_features(load_panel(panel(tmp,changed)))
        raw0=frame_with_individual_speed(f0,"turf")
        raw1=frame_with_individual_speed(f1,"turf")
        key=lambda df:df[(df["race_id"]==race)&
                         (df["horse_id"]==focal["horse_id"])].iloc[0]
        self.assertAlmostEqual(float(key(raw0)["speed_mps"]),
                               float(key(raw1)["speed_mps"]))
        # Opponents' contemporaneous speeds enter the rival-centred z score.
        self.assertNotAlmostEqual(float(key(raw0)["y"]),float(key(raw1)["y"]))

    def test_nonfinisher_is_still_a_rival_but_not_zero_speed(self):
        changed=[dict(v) for v in self.fake]
        race_id="FAKE-COMP-R0045"
        nonfinish=next(r for r in changed if r["race_id"]==race_id)
        nonfinish["finish_status"]="did_not_finish"
        nonfinish["finishing_position"]=""
        nonfinish["finish_time_s"]=""
        with tempfile.TemporaryDirectory() as tmp:
            baseline=lagged_features(load_panel(panel(tmp,self.fake)))
            edited=lagged_features(load_panel(panel(tmp,changed)))
        rb={r["horse_id"]:r for r in baseline if r["race_id"]==race_id}
        re={r["horse_id"]:r for r in edited if r["race_id"]==race_id}
        for horse in rb:
            self.assertEqual(rb[horse]["other_front_runner_share"],
                             re[horse]["other_front_runner_share"])
        frame=frame_with_individual_speed(edited,"turf")
        self.assertEqual(int((frame["race_id"]==race_id).sum()),11)
        self.assertNotIn(nonfinish["horse_id"],
                         set(frame.loc[frame["race_id"]==race_id,"horse_id"]))
        audit=frame.attrs["selection_audit"]
        self.assertEqual(audit["nonfinisher_starts_in_retained_races"],1)
        self.assertEqual(audit["observed_speed_loss_count"],1)
        self.assertGreater(audit["races_with_some_missing_focal_speeds"],0)
        self.assertFalse(audit["unobserved_speed_is_zero"])
        self.assertEqual(audit["missingness_status"],
                         "OBSERVATIONAL_SELECTION_RISK_UNRESOLVED")
        # The regression remains runnable and propagates an explicit hold
        # on interpreting population ecology from observed finishers alone.
        with tempfile.TemporaryDirectory() as tmp:
            report=run(panel(tmp,changed),permit_synthetic_demo=True)
        self.assertEqual(report["empirical_missingness_decision"],
                         "HOLD_POTENTIALLY_INFORMATIVE_SPEED_MISSINGNESS")
        self.assertEqual(report["outcome_selection_audit"]["nonfinisher_starts_in_retained_races"],1)

    def test_one_missing_result_time_does_not_drop_twelve_horse_race(self):
        changed=[dict(v) for v in self.fake]
        selected=next(r for r in changed if r["race_id"]=="FAKE-COMP-R0045")
        selected["finish_time_s"]=""
        with tempfile.TemporaryDirectory() as tmp:
            feats=lagged_features(load_panel(panel(tmp,changed)))
        frame=frame_with_individual_speed(feats,"turf")
        self.assertEqual(int((frame["race_id"]=="FAKE-COMP-R0045").sum()),11)
        self.assertEqual(frame.attrs["selection_audit"]["finished_but_missing_time_starts"],1)

    def test_incomplete_entry_roster_must_not_look_like_no_rivals(self):
        reduced=[dict(v) for v in self.fake]
        chosen=next(r for r in reduced if r["race_id"]=="FAKE-COMP-R0045")
        reduced.remove(chosen)
        with tempfile.TemporaryDirectory() as tmp:
            enriched=lagged_features(load_panel(panel(tmp,reduced)))
        frame=frame_with_individual_speed(enriched,"turf")
        self.assertNotIn("FAKE-COMP-R0045",set(frame["race_id"]))
        self.assertGreater(frame.attrs["selection_audit"]["excluded_races_by_reason"]["incomplete_entry_roster"],0)

    def test_ground_condition_dependent_nonfinishing_is_recorded(self):
        altered=[dict(v) for v in self.fake]
        # Artificial informative loss occurs only in non-good going.
        for day in (41,43,45,47,49):
            day_race=f"FAKE-COMP-R{day:04d}"
            target=next(r for r in altered if r["race_id"]==day_race)
            target["finish_status"]="did_not_finish"
            target["finishing_position"]=""
            target["finish_time_s"]=""
        with tempfile.TemporaryDirectory() as tmp:
            feats=lagged_features(load_panel(panel(tmp,altered)))
        report=frame_with_individual_speed(feats,"turf").attrs["selection_audit"]
        by=report["timed_fraction_by_going"]
        self.assertLess(by["非良"]["timed_outcome_fraction"],
                        by["良"]["timed_outcome_fraction"])
        self.assertEqual(report["nonfinisher_starts_in_retained_races"],5)

    def test_uses_raw_mps_training_with_crossed_race_and_horse_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=run(panel(tmp,self.fake),permit_synthetic_demo=True)
        self.assertEqual(report["status"],"SYNTHETIC_ABSOLUTE_SPEED_H2_DEMO_ONLY")
        self.assertTrue(report["relative_outcome_avoided_in_training"])
        self.assertTrue(report["train_before_test"])
        self.assertGreaterEqual(report["support_horses_with_repeated_rival_contexts"],8)
        self.assertEqual(set(report["models"]),{"other_horses_only","whole_field"})
        for result in report["models"].values():
            self.assertTrue(result["M0"]["horse_and_race_effects_both_controlled"])
            self.assertTrue(result["M1"]["race_context_main_effect_omitted_as_collinear"])
            self.assertEqual(len(result["M1"]["two_way_cluster_nominal_interval"]),2)
            self.assertFalse(result["M1"]["interval_is_causal_or_confirmatory"])
            self.assertEqual(result["future_within_race_speed_mps_test"]["metric_units"],
                             "m/s within-race speed deviation")
            self.assertTrue(np.isfinite(
                result["M1"]["beta_raw_speed_mps_per_style_context_product"]))

    def test_null_and_confounding_checks_report_holds_not_biological_claims(self):
        trials=stress(seeds=(512,))
        self.assertEqual(trials["status"],"SYNTHETIC_ABSOLUTE_SPEED_STRESS_ONLY")
        self.assertEqual(len(trials["trials"]),3)
        self.assertEqual(set(trials["summary"]),{
            "null_random_entry","planted_opponent_interaction","confounded_null"
        })
        for row in trials["trials"]:
            self.assertIn(row["status"],(
                "SYNTHETIC_ABSOLUTE_MODEL_STRESS_ONLY",
                "HOLD_DESIGN_OR_COVARIANCE",
            ))
        self.assertIn("engineering/design test",trials["interpretation"])

    def test_cannot_run_synthetic_panel_without_explicit_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"synthetic"):
                run(panel(tmp,self.fake),permit_synthetic_demo=False)


if __name__=="__main__":
    unittest.main()
