"""Fictional 2022 model-usage calibration / 2023-24 score transfer tests."""
from __future__ import annotations

import copy
import unittest
from datetime import datetime
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2022_trained_family_gate import (
    CANDIDATES,STATUS,EXPECTED_YEARS,gate_mask,rule_name,
    switch_prediction,year_fixed_comparison,
    select_rule_with_2022_only,_support,
)

def fictional(year=2022):
    # 1200 starts, 200 horse IDs and 120 race days; records are artificial.
    rows=[]
    for i in range(1200):
        own="0-3" if i%2==0 else "16+"
        rows.append({
            "horse":"H:SYN"+str(i%200),
            "race":"JRA:SYN_"+str(year)+"_"+str(i//10),
            "day":pd.Timestamp(year=year,month=1,day=1)+pd.Timedelta(days=i//10),
            "year":year,
            "y":0.2 if own=="0-3" else 0.5
        })
    t=pd.DataFrame(rows)
    ctx=pd.DataFrame({
        "own_record_count_bin":["0-3" if i%2==0 else "16+"
                                for i in range(len(rows))],
        "other_same_parent_horse_count_bin":["5+_peers"]*len(rows),
    })
    p0=np.full(len(rows),0.5,dtype=float)
    # Kin predicts low-own group exactly, but damages high-own group.
    p1=np.full(len(rows),0.2,dtype=float)
    return t,ctx,p0,p1


class YearTransferGateTests(unittest.TestCase):
    def test_candidate_grid_fixed_no_future_label_sensitive_thresholds(self):
        self.assertEqual(len(CANDIDATES),12)
        self.assertEqual(CANDIDATES[0],(0,1))
        self.assertEqual(CANDIDATES[-1],(3,3))
        self.assertEqual(tuple(EXPECTED_YEARS),(2022,2023,2024))
        self.assertTrue(STATUS.startswith("POSTHOC_"))

    def test_all_baseline_gates_and_no_peer_cannot_trigger(self):
        _,ctx,_,_=fictional()
        self.assertEqual(gate_mask(ctx,"never_family").sum(),0)
        self.assertEqual(gate_mask(ctx,"always_family").sum(),1200)
        self.assertEqual(gate_mask(ctx,(0,1)).sum(),600)
        ctx.iloc[:,"1"]=None if False else ctx.iloc[:,1]
        ctx.loc[0,"other_same_parent_horse_count_bin"]="no_recorded_peer"
        self.assertFalse(gate_mask(ctx,(0,1))[0])

    def test_source_binned_focal_history_rules_reject_undocumented_group(self):
        _,ctx,_,_=fictional()
        ctx.loc[0,"own_record_count_bin"]="official_maiden"
        with self.assertRaisesRegex(ValueError,"UNKNOWN_PAST_ONLY_INFORMATION_BIN"):
            gate_mask(ctx,(0,1))

    def test_choose_rule_on_2022_synthetic_labels_only(self):
        t,ctx,p0,p1=fictional()
        rule,qa=select_rule_with_2022_only(t,ctx,p0,p1)
        self.assertIsInstance(rule,tuple)
        self.assertEqual(rule[0],0)
        self.assertEqual(qa["selection_candidate_count_total"],14)
        self.assertFalse(qa["selection_uses_2023_or_2024_labels"])
        self.assertIn(qa["selected_rule_name"],
                      qa["all_2022_candidate_results_including_unfavorable"])
        self.assertTrue(_support(t,gate_mask(ctx,rule))["starts"]>=500)

    def test_2023_and_2024_labels_cannot_reselect_2022_gate(self):
        t,ctx,p0,p1=fictional()
        rule,info=select_rule_with_2022_only(t,ctx,p0,p1)
        t23,ctx23,q0,q1=fictional(2023)
        t24,ctx24,z0,z1=fictional(2024)
        before=(
            year_fixed_comparison(t23,q0,q1,gate_mask(ctx23,rule)),
            year_fixed_comparison(t24,z0,z1,gate_mask(ctx24,rule)),
        )
        # Reverse targets of ALL future years. 2022 choice cannot change,
        # though scored performance must change.
        t23["y"]=1-t23["y"]
        t24["y"]=1-t24["y"]
        newrule,_=select_rule_with_2022_only(t,ctx,p0,p1)
        after=(
            year_fixed_comparison(t23,q0,q1,gate_mask(ctx23,newrule)),
            year_fixed_comparison(t24,z0,z1,gate_mask(ctx24,newrule))
        )
        self.assertEqual(rule,newrule)
        self.assertNotEqual(
            before[0]["RMSE_2022_chosen_gate"],
            after[0]["RMSE_2022_chosen_gate"])
        self.assertNotEqual(
            before[1]["M1_minus_selected_gate_RMSE_gain"],
            after[1]["M1_minus_selected_gate_RMSE_gain"])

    def test_2022_only_validation_rejects_future_year_leakage(self):
        t,ctx,p0,p1=fictional()
        t.loc[1,"year"]=2023
        with self.assertRaisesRegex(ValueError,"NON2022_YEAR"):
            select_rule_with_2022_only(t,ctx,p0,p1)

    def test_missing_support_candidate_holds_not_overfit(self):
        t,ctx,p0,p1=fictional()
        ctx["other_same_parent_horse_count_bin"]="no_recorded_peer"
        rule,qa=select_rule_with_2022_only(t,ctx,p0,p1)
        self.assertEqual(rule,"never_family")
        self.assertEqual(qa["selection_candidate_count_supported"],2)
        self.assertTrue(all(v["status"]=="HOLD_GATE_2022_SELECTED_GROUP_LOW_SUPPORT"
                            for k,v in qa["all_2022_candidate_results_including_unfavorable"].items()
                            if k not in ("never_family","always_family")))

    def test_gated_2022_synthetic_can_beat_both_fixed_variants(self):
        t,ctx,p0,p1=fictional()
        rule,_=select_rule_with_2022_only(t,ctx,p0,p1)
        score=year_fixed_comparison(t,p0,p1,gate_mask(ctx,rule))
        self.assertTrue(score["selected_gate_better_than_M1_M2_midpoint_all"])
        self.assertGreater(score["M1_minus_selected_gate_RMSE_gain"],0)
        self.assertGreater(score["always_family_minus_selected_gate_RMSE_gain"],0)

    def test_low_support_not_a_new_positive_independent_trial(self):
        t,ctx,p0,p1=fictional()
        for r in ("never_family","always_family"):
            self.assertEqual(len(gate_mask(ctx,r)),len(t))
        self.assertEqual(_support(t,gate_mask(ctx,"never_family"))["starts"],0)
        with self.assertRaisesRegex(ValueError,"LOW_SUPPORT"):
            select_rule_with_2022_only(
                t.iloc[:25].copy(),ctx.iloc[:25].copy(),
                p0[:25],p1[:25])

    def test_prohibit_unregistered_gate_and_predictions_without_finite_values(self):
        _,ctx,p0,p1=fictional()
        with self.assertRaisesRegex(ValueError,"UNDECLARED_PARENT_INFORMATION_GATE"):
            gate_mask(ctx,(3,0))
        with self.assertRaisesRegex(ValueError,"GATE_FORECAST_OUT_OF_RANGE"):
            switch_prediction([1.2],[.5],[True])
        with self.assertRaisesRegex(ValueError,"GATE_PREDICTION_VECTOR_PARITY"):
            switch_prediction([.5],[.5,.6],[True])

    def test_score_always_never_parity_and_identity(self):
        t,ctx,p0,p1=fictional()
        base=year_fixed_comparison(t,p0,p1,gate_mask(ctx,"never_family"))
        alt=year_fixed_comparison(t,p0,p1,gate_mask(ctx,"always_family"))
        self.assertAlmostEqual(base["RMSE_2022_chosen_gate"],base["RMSE_own_M1"])
        self.assertAlmostEqual(alt["RMSE_2022_chosen_gate"],
                               alt["RMSE_always_family_M2"])
        self.assertEqual(base["starts"],1200)
        self.assertGreaterEqual(base["race_days"],100)


if __name__=="__main__":
    unittest.main()
