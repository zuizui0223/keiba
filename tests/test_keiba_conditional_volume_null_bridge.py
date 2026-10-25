#!/usr/bin/env python3
"""Conditional price-index null QA: no lookahead, feasibility, volume sensitivity."""
from __future__ import annotations

import copy
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
if np is not None:
    import keiba_conditional_volume_null_bridge as m


def synthetic_row():
    return {
      "race_id":"SYNTHETIC_R","race_no":8,"meeting_day":"2026-11-01",
      "first_odds":{i:float(3+2*i) for i in range(1,9)},
      "last_odds":{i:float(3+2*i)*(1.2 if i%2 else .95)
                   for i in range(1,9)},
      "initial_quote_at":"2026-11-01T10:00:00+09:00",
      "latest_quote_at":"2026-11-01T12:00:00+09:00",
      "post_at":"2026-11-01T15:40:00+09:00",
    }


def synthetic_history():
    return {
      "target_date":"2026-11-01",
      "target_surface":"芝","distance_m":1600,
      "rows":{i:{"full_history_before_target":[
          {"date":"2026-06-11","finish":i,
           "surface":"芝","distance_m":1800}
      ]} for i in range(1,9)}
    }


@unittest.skipIf(np is None,"Dedicated numerical workflow provides NumPy")
class ConditionalNullPureTests(unittest.TestCase):
    def test_simplex_lower_bound_and_genuine_flow_witness_algebra(self):
        q=m.vector([.4,.25,.15,.12,.08])
        b=np.asarray([0.,.5,.3,.2,0.])
        later=.6*q+.4*b
        self.assertAlmostEqual(
            m.transition_accounting_lower_bound(q,later),.4,places=12)
        w=m.transition_witness(q,later,.4)
        np.testing.assert_allclose(w,b,atol=1e-13)
        with self.assertRaisesRegex(ValueError,"NEGATIVE_HYPOTHETICAL"):
            m.transition_witness(q,later,.3)
        self.assertTrue(m.transition_accounting_lower_bound(q,later)<=1)

    def test_iid_stochastic_mass_and_paired_lambda_scale_without_future_quote(self):
        q=m.vector([.3,.2,.17,.13,.10,.07,.03])
        low=m.simulate_no_horse_information(
            q,new_fraction=.2,effective_new_votes=1000,
            repetitions=600,seed=33)
        high=m.simulate_no_horse_information(
            q,new_fraction=.8,effective_new_votes=1000,
            repetitions=600,seed=33)
        np.testing.assert_allclose(high["TV_pp"],low["TV_pp"]*4,
                                   rtol=1e-11,atol=1e-11)
        self.assertTrue(np.all(low["TV_pp"]>=0))
        self.assertEqual(len(low["max_abs_log_support_change"]),600)

    def test_overdispersed_null_has_broader_quote_shape_than_iid(self):
        q=m.vector([.35,.19,.15,.12,.09,.065,.035])
        iid=m.simulate_no_horse_information(
            q,new_fraction=.5,effective_new_votes=1000,
            repetitions=2400,seed=401)
        over=m.simulate_no_horse_information(
            q,new_fraction=.5,effective_new_votes=1000,
            concentration=80.,repetitions=2400,seed=401)
        self.assertGreater(np.mean(over["TV_pp"]),2*np.mean(iid["TV_pp"]))

    def test_null_calibrated_max_statistic_not_raw_hour_sensitive(self):
        q=m.vector([.30,.22,.16,.13,.10,.06,.03])
        alternative=m.vector([.32,.19,.15,.15,.11,.05,.03])
        null=m.simulate_no_horse_information(
            q,new_fraction=.5,effective_new_votes=300,
            repetitions=700,seed=23)
        a=m.null_calibration(null,q,alternative,hours=1,
                             new_fraction=.5,sample_count=300,
                             concentration=None)
        b=m.null_calibration(null,q,alternative,hours=22,
                             new_fraction=.5,sample_count=300,
                             concentration=None)
        self.assertAlmostEqual(
            a["conditional_tail_area_max_search_not_real_p_value"],
            b["conditional_tail_area_max_search_not_real_p_value"],
            places=12)
        self.assertAlmostEqual(
            a["observed_max_abs_log_support_per_hour"],
            b["observed_max_abs_log_support_per_hour"]*22,places=12)
        self.assertTrue(a["corrected_for_search_over_all_horses_in_one_race"])

    def test_independent_synthetic_calibration_not_empirical_pvalue(self):
        q=m.vector([.30,.2,.16,.13,.11,.065,.035])
        stats=m.heldout_null_false_alarm_check(
            q,new_fraction=.5,count=1000,repetitions=2000,seed=202)
        for k in ("false_alarm_max_statistic_in_independent_null_holdout",
                  "false_alarm_TV_in_independent_null_holdout"):
            self.assertGreater(stats[k],.01)
            self.assertLess(stats[k],.09)
        self.assertTrue(stats["not_a_real_market_type_I_error_estimate"])

    def test_hypothetical_decimal_bin_TV_lower_bound_is_conservative(self):
        a={i:float(2+i*2) for i in range(1,8)}
        b={i:float(2+i*2)*(1.18 if i%2 else .93)
           for i in range(1,8)}
        central,_=m._market_shape_statistics(
            [1/a[i] for i in sorted(a)],[1/b[i] for i in sorted(b)])
        low=m.quotation_TV_rounding_lower_bound(a,b)
        self.assertTrue(0<=low<=central+1e-10)
        self.assertEqual(m.quotation_TV_rounding_lower_bound(a,a),0)

    def test_q1_or_winner_mutation_cannot_change_nulls_or_physical_market_forecast(self):
        row=synthetic_row()
        q0=m.vector([1/row["first_odds"][i] for i in sorted(row["first_odds"])])
        original=m.simulate_no_horse_information(
            q0,new_fraction=.8,effective_new_votes=500,
            repetitions=150,seed=999)
        baseline=m._build_connected_preoutcome(
            row,synthetic_history(),draws=45,seed=101)
        changed=copy.deepcopy(row)
        changed["last_odds"]={i:float(i+15) for i in changed["last_odds"]}
        changed["official_top3"]=[3,4,7]
        changed["target_payout"]=999999
        after=m._build_connected_preoutcome(
            changed,synthetic_history(),draws=45,seed=101)
        repeated=m.simulate_no_horse_information(
            q0,new_fraction=.8,effective_new_votes=500,
            repetitions=150,seed=999)
        for k in original:
            np.testing.assert_array_equal(original[k],repeated[k])
        for arm in baseline:
            for a in baseline[arm]:
                np.testing.assert_array_equal(baseline[arm][a],after[arm][a])

    def test_price_proxy_feasibility_is_not_authorized_as_stake_volume(self):
        q=m.vector([.38,.21,.17,.13,.075,.035])
        other=m.vector([.20,.25,.20,.15,.12,.08])
        lo=m.transition_accounting_lower_bound(q,other)
        self.assertGreater(lo,0)
        null=m.simulate_no_horse_information(
            q,new_fraction=.2,effective_new_votes=100,
            repetitions=300,seed=80)
        result=m.null_calibration(
            null,q,other,hours=1,new_fraction=.2,
            sample_count=100,concentration=None)
        self.assertEqual(
            result["nominal_proxy_exact_cumulative_flow_feasible_at_assumed_lambda"],
            .2+1e-12>=lo)
        self.assertTrue(
            result["not_evidence_of_social_imitation_or_new_horse_information"])

    def test_bad_grid_rejected(self):
        q=m.vector([.4,.25,.15,.11,.09])
        with self.assertRaisesRegex(ValueError,"INVALID_PSEUDO_POOL"):
            m.simulate_no_horse_information(
                q,new_fraction=.3,effective_new_votes=0,repetitions=200)
        with self.assertRaisesRegex(ValueError,"INVALID_PSEUDO_POOL"):
            m.simulate_no_horse_information(
                q,new_fraction=1.1,effective_new_votes=100,repetitions=200)


@unittest.skipUnless(np is not None and (
    ROOT/"data/2026-10-12/v3-normalized-prerace-history.json").exists(),
    "Requires full real source-locked repo and NumPy")
class SourceLockedSixRaceChecks(unittest.TestCase):
    def test_real_quote_scoring_does_not_consume_any_official_finish(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("POSTRACE_WINNER_LEAK")) as fn:
            z=m.audit(repetitions=120,horse_draws=40,seed=20261025)
            fn.assert_not_called()
        self.assertEqual(z["archived_real_races"],6)
        self.assertEqual(z["distinct_source_meeting_dates"],2)
        self.assertEqual(z["horse_race_entries"],84)
        self.assertEqual(set(z["source_date_summaries"]),
                         {"2026-10-12","2026-10-18"})
        self.assertEqual(z["source_date_summaries"]["2026-10-12"]["real_races"],5)
        self.assertEqual(z["source_date_summaries"]["2026-10-18"]["real_races"],1)
        self.assertFalse(z["observed_exact_JRA_pool_shares_and_stake_flow_available"])
        self.assertEqual(z["real_social_contagion_or_market_criticality"],"HOLD")
        for race in z["by_real_race_without_raw_prices"]:
            self.assertEqual(len(race["price_index_null_sensitivity"]),12)
            self.assertGreaterEqual(
                race["central_observed_quote_proxy_TV_pp"],
                race["display_bin_only_TV_lower_bound_pp"])
            self.assertEqual(set(race["same_ABM_horse_to_bettor_smooth_candidates"]),
                             {"initial_market","past_form"})
            self.assertEqual(
                set(race["same_ABM_horse_to_bettor_smooth_candidates"]["past_form"]),
                {"1","3","5"})
        self.assertTrue(z["no_horse_outcomes_loaded_even_for_scoring"])


if __name__=="__main__":
    unittest.main()
