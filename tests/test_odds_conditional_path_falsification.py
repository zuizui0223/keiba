#!/usr/bin/env python3
"""No-leakage same-latest-odds different-middle-path synthetic stress suite."""
import copy
from datetime import datetime, timedelta
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from odds_conditional_path_falsification import (
    STATUS, MECHANISMS, attach_fictional_results, evaluate, generate,
    path_feature, prepare_before_results, _select_model, _prob_win,
    _uncertainty,
)
from odds_threshold_forward_eval import order_probabilities


class SameEndpointCounterfactualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=attach_fictional_results(
            generate(mechanism="smooth_path_signal",seed=104,dates=18,
                     twin_pairs_per_date=8,horses=12,signal_beta=2.0),
            seed=105)

    def test_same_early_and_latest_quotes_but_opposite_middle_paths(self):
        f=prepare_before_results(self.data["rows"])
        self.assertEqual(len(f),288)
        for i in range(0,len(f),2):
            a,b=f[i:i+2]
            self.assertEqual(a["early_q"],b["early_q"])
            self.assertEqual(a["latest_q"],b["latest_q"])
            self.assertNotEqual(a["curvature"],b["curvature"])
            self.assertTrue(
                all(abs(x+y)<1e-9 for x,y in zip(a["curvature"],b["curvature"])))
            self.assertGreater(
                a["middle_race_centered_deviation_sd"],0.0)
        self.assertNotIn("synthetic_top3",str(f))

    def test_time_weighted_mid_residual_zero_if_geo_path(self):
        t0=datetime.fromisoformat("2026-01-01T12:00:00+09:00")
        t1=t0+timedelta(minutes=90)
        t2=t0+timedelta(minutes=150)
        q0=[.1,.2,.25,.2,.15,.1]
        q2=[.15,.3,.05,.1,.2,.2]
        u=(t1-t0)/(t2-t0)
        baseline=[q0[i]**(1-u)*q2[i]**u for i in range(len(q0))]
        mid=[z/sum(baseline) for z in baseline]
        v=path_feature(q0,mid,q2,*[x.isoformat() for x in (t0,t1,t2)])
        self.assertTrue(all(abs(z)<1e-10 for z in v))

    def test_earliest_and_latest_alone_cannot_distinguish_twins(self):
        f=prepare_before_results(self.data["rows"])
        for i in range(0,20,2):
            a,b=f[i:i+2]
            p1=_prob_win(a["latest_q"],a["curvature"],0.0,None,a["initial_win_odds"])
            p2=_prob_win(b["latest_q"],b["curvature"],0.0,None,b["initial_win_odds"])
            self.assertEqual(p1,p2)
            q1,t1=order_probabilities(p1)
            q2,t2=order_probabilities(p2)
            self.assertEqual(q1,q2)
            self.assertEqual(t1,t2)
            self.assertAlmostEqual(sum(t1),3)

    def test_chronological_future_cannot_choose_coefficients(self):
        r1=evaluate(self.data,repetitions=100,seed=314)
        revised=copy.deepcopy(self.data)
        cutoff=r1["training_max_date"]
        for row in revised["rows"]:
            if row["post_jst"][:10] > cutoff:
                values=row["synthetic_top3"]
                others=[i for i in range(1,13) if i not in values][:3]
                row["synthetic_top3"]=others
        r2=evaluate(revised,repetitions=100,seed=314)
        self.assertEqual(r1["selected_only_with_past_results"],
                         r2["selected_only_with_past_results"])
        self.assertNotEqual(r1["future_mean_scores"],r2["future_mean_scores"])
        self.assertLess(r1["training_max_date"],r1["future_min_date"])

    def test_both_source_time_and_result_time_leakage_refused(self):
        late=copy.deepcopy(self.data)
        row=late["rows"][0]
        row["snapshots"][-1]["published_at_jst"]=row["post_jst"]
        with self.assertRaisesRegex(ValueError,"HOLD_PRICE_AFTER_ALLOWED_CUTOFF"):
            evaluate(late,repetitions=100)
        late=copy.deepcopy(self.data)
        row=late["rows"][0]
        row["official_result_recorded_at_jst"]=row["post_jst"]
        with self.assertRaisesRegex(ValueError,"HOLD_SYNTHETIC_OUTCOME_NOT_POSTRACE"):
            evaluate(late,repetitions=100)

    def test_changed_latest_breaks_exact_endpoint_pair_gate(self):
        changed=copy.deepcopy(self.data)
        changed["rows"][1]["snapshots"][-1]["odds"]["1"]*=1.2
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EXACT_IDENTICAL_ENDPOINT_TWINS"):
            evaluate(changed,repetitions=100)

    def test_outcome_generation_is_null_or_planted_not_real(self):
        for mech in MECHANISMS:
            rows=attach_fictional_results(generate(
                mechanism=mech,seed=115,dates=12,twin_pairs_per_date=3),seed=112)
            self.assertEqual(rows["status"],"FABRICATED_MATCHED_ENDPOINT_RACES_NO_JRA_DATA")
            report=evaluate(rows,repetitions=100,seed=115)
            self.assertEqual(report["status"],STATUS)
            self.assertFalse(report["real_race_data_used"])
            self.assertEqual(report["training_date_count"],8)
            self.assertEqual(report["future_date_count"],4)
            self.assertTrue(report["generated_twin_cases_identical_initial_and_latest"])
            self.assertEqual(len(report["future_mean_scores"]),4)
            self.assertEqual(len(report["paired_day_bootstrap_synthetic_only"]),3)

    def test_without_synthetic_watermark_refuses_data(self):
        fake=copy.deepcopy(self.data)
        fake["status"]="JRA_ORIGINAL_ODDS_DATA"
        with self.assertRaisesRegex(ValueError,"HOLD_NO_REAL_DATA_ALLOWED"):
            evaluate(fake,repetitions=100)

    def test_future_day_bootstrap_uses_day_blocks_and_is_deterministic(self):
        r=evaluate(self.data,repetitions=250,seed=555)
        s=evaluate(self.data,repetitions=250,seed=555)
        self.assertEqual(r,s)
        item=r["paired_day_bootstrap_synthetic_only"][
            "train_selected_smooth"]["win_log_loss"]
        self.assertTrue(item["not_a_real_market_ci_or_identified_threshold"])
        self.assertEqual(item["independent_resample_unit"],"fictional_meeting_day")
        self.assertEqual(len(item["synthetic_date_block_bootstrap_95pct"]),2)
        self.assertLessEqual(*item["synthetic_date_block_bootstrap_95pct"])


if __name__=="__main__":
    unittest.main()
