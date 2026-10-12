"""Two-part outcome checks: all records are fictional and never empirical."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_demo_competitors import fabricate_competition
from ecology_h2_outcome_loss_stress import inject_nonfinishing
from ecology_h2_two_part import (
    starter_completion_panel,make_features,run,
)
from ecology_panel import REQUIRED, load_panel, lagged_features
from ecology_h1_pilot import split_dates


def save(folder, rows):
    path=Path(folder)/"fictional-horses.csv"
    with path.open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(REQUIRED)+["first_call_position"])
        writer.writeheader();writer.writerows(rows)
    return path


def fabricated_with_dnf(days=100,seed=512):
    rows=fabricate_competition(n_days=days,n_horses=48,runners=12,
                                seed=seed,interaction=-0.9)
    return inject_nonfinishing(rows,"random",seed=seed+31)


class TwoPartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample=fabricated_with_dnf(days=100)

    def test_both_outcomes_keep_all_starters(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows=lagged_features(load_panel(save(tmp,self.sample)))
        whole,diagnostic=starter_completion_panel(rows)
        self.assertGreater(diagnostic["did_not_finish_count"],10)
        self.assertEqual(diagnostic["all_history_eligible_starts"],len(whole))
        self.assertEqual(int((whole["finished"]==0).sum()),
                         diagnostic["did_not_finish_count"])
        self.assertTrue(diagnostic["full_roster_without_postrace_time_filter"])
        self.assertTrue(diagnostic["no_zero_speed_imputation"])
        self.assertEqual(diagnostic["finished_but_timing_unavailable"],0)

    def test_two_part_model_runs_on_generated_dnf(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=run(save(tmp,self.sample),permit_synthetic_demo=True)
        self.assertEqual(report["status"],"SYNTHETIC_TWO_PART_H2_DEMO_ONLY")
        self.assertTrue(report["no_causal_or_empirical_claim"])
        self.assertLess(report["date_split"]["train_max_date"],
                        report["date_split"]["test_start_date"])
        self.assertGreaterEqual(report["date_split"]["training_DNF"],12)
        self.assertGreaterEqual(report["date_split"]["future_DNF"],3)
        self.assertEqual(report["part_A_completion"]["outcome"],
                         "binary FINISHED vs DID_NOT_FINISH among actual starters")
        self.assertTrue(report["part_A_completion"]["baseline"]["preprocessing"]["all_explanatory_values_pre_race_historical"])
        self.assertFalse(report["part_A_completion"]["style_by_rival_competition_interaction"]["fitted_coefficient_is_causal_or_confirmatory"])
        self.assertTrue(report["part_B_speed_conditional_on_timed_finish"]["never_impute_a_nonfinisher_full_distance_speed"])
        self.assertEqual(report["part_B_speed_conditional_on_timed_finish"]["scientific_selection_hold"],
                         "HOLD_POTENTIALLY_INFORMATIVE_SPEED_MISSINGNESS")

    def test_no_dnf_means_completion_inference_hold(self):
        rows=fabricate_competition(n_days=65,n_horses=36,runners=12,seed=512)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"HOLD_TOO_FEW_COMPLETION_EVENTS"):
                run(save(tmp,rows),permit_synthetic_demo=True)

    def test_train_centres_independent_of_test_race_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=lagged_features(load_panel(save(tmp,self.sample)))
        allstarts,_=starter_completion_panel(data)
        tr,te,_=split_dates(allstarts)
        _,_,before=make_features(tr,te,True)
        changed=te.copy()
        changed["finished"]=1-changed["finished"]
        _,_,after=make_features(tr,changed,True)
        self.assertEqual(before,after)
        self.assertLess(tr["date"].max(),te["date"].min())

    def test_finish_with_missing_time_is_not_dnf(self):
        altered=[dict(r) for r in self.sample]
        for r in altered:
            if r["race_id"]=="FAKE-COMP-R0045" and r["finish_status"]=="finished":
                r["finish_time_s"]=""
                break
        with tempfile.TemporaryDirectory() as tmp:
            lagged=lagged_features(load_panel(save(tmp,altered)))
        _,diag=starter_completion_panel(lagged)
        self.assertEqual(diag["finished_but_timing_unavailable"],1)


if __name__=="__main__":
    unittest.main()
