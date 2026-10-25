#!/usr/bin/env python3
"""Single observed three-time WIN market: no future quote/result into model."""
from __future__ import annotations
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
    import keiba_r8_threepoint_conditional_shadow as m


@unittest.skipIf(np is None,"Numerical dependency installed only in dedicated CI")
class MathematicalTests(unittest.TestCase):
    def test_complete_market_vectors_follow_one_horse_identity(self):
        q={i:1/(i+2) for i in range(1,8)}
        z=m._vector_from_proxy(q,sorted(q))
        self.assertEqual(len(z),7)
        self.assertAlmostEqual(sum(z),1,places=12)
        self.assertTrue(np.all(z>0))
        with self.assertRaisesRegex(ValueError,"ROSTER"):
            m._vector_from_proxy(q,[1,2,3,4,5,6,8])

    def test_nominal_proxy_assumption_dependent_and_infeasible_are_not_discoveries(self):
        def cell(feas,p):
            return {
                "hypothetical_exact_proxy_new_fraction_is_simplex_feasible":feas,
                "conditional_tail_TV_not_real_p_value":p}
        self.assertEqual(m._tail_class([cell(True,.01),cell(True,.8)])[
            "descriptive_exact_price_proxy_grid_status"],"ASSUMPTION_DEPENDENT")
        self.assertEqual(m._tail_class([cell(True,.01),cell(False,.9)])[
            "descriptive_exact_price_proxy_grid_status"],
            "ALL_FEASIBLE_ASSUMED_NOISE_MODELS_IN_TOP_FIVE_PERCENT_TAIL")
        self.assertEqual(m._tail_class([cell(True,.2),cell(True,.9)])[
            "descriptive_exact_price_proxy_grid_status"],
            "NO_FEASIBLE_ASSUMED_NOISE_MODEL_IN_TOP_FIVE_PERCENT_TAIL")
        self.assertEqual(m._tail_class([cell(False,.001)])[
            "descriptive_exact_price_proxy_grid_status"],
            "HOLD_NO_FEASIBLE_EXACT_PROXY_GRID_CELL")

    def test_score_held_target_does_not_reshape_preexisting_predictions(self):
        q=np.asarray([.29,.22,.18,.13,.09,.05,.04])
        original={"status":"PRETARGET","ids":list(range(1,8)),
                  "source_price_q0":q.copy(),
                  "source_price_qmid":q.copy(),
                  "nominal_cutoff":m.aware("2026-10-12T13:26:00+09:00"),
                  "first_source_published":m.aware("2026-10-12T12:21:00+09:00"),
                  "mid_received":m.aware("2026-10-12T13:27:00+09:00"),
                  "nominal_next_market_publication":m.aware(
                      "2026-10-12T13:44:00+09:00"),
                  "mid_original_displayed_win_prices":{
                    i:float(1/a) for i,a in enumerate(q,1)},
                  "candidate_indices":{
                    "mid_quote_persistence":q.copy(),
                    "alternate":m.vector(np.roll(q,1))}}
        # Later quote only changes the scoring, not the forecasts:
        nulls=m.generate_nulls(original,repetitions=120,seed=1)
        before={k:v.copy() for k,v in original["candidate_indices"].items()}
        target1={i:float(1/q[i-1]) for i in range(1,8)}
        target2={i:float(1/np.roll(q,1)[i-1]) for i in range(1,8)}
        a=m.score_source_only_forecasts(original,target1,nulls)
        b=m.score_source_only_forecasts(original,target2,nulls)
        self.assertAlmostEqual(a["candidate_forecast_scores"][
            "mid_quote_persistence"]["next_WIN_price_proxy_TV_pp"],0,places=11)
        self.assertGreater(b["candidate_forecast_scores"][
            "mid_quote_persistence"]["next_WIN_price_proxy_TV_pp"],1)
        for k in before:
            np.testing.assert_array_equal(original["candidate_indices"][k],
                                          before[k])
        self.assertTrue(a["future_race_outcome_or_positive_EV_inferred"] is False)
        self.assertEqual(len(a["null_condition_sensitivity"]),12)


@unittest.skipUnless(np is not None and (
    ROOT/"data/2026-10-12/r8_markets_latest.json").exists(),
    "Full locked source checkout and NumPy required")
class ArchivedR8Tests(unittest.TestCase):
    def test_build_pre_1344_never_opens_third_quote_or_official_result(self):
        with patch.object(m,"_locked",side_effect=AssertionError(
            "FUTURE_1344_PRICE_WOULD_LEAK")), patch(
            "odds_six_race_predictive_increment.verify_official_oct12",
            side_effect=AssertionError("POSTRACE_WINNER_WOULD_LEAK")):
            z=m.build_pre_1344_forecasts(horse_draws=40,seed=144)
        self.assertEqual(z["ids"],list(range(1,12)))
        self.assertEqual(len(z["candidate_indices"]),9)
        self.assertTrue(z["mid_wide_full_55_pair_source_already_checked"])
        self.assertFalse(z["horse_history_source_received_pre_cutoff_proven"])
        self.assertLess(z["mid_received"],z["nominal_next_market_publication"])
        for name,p in z["candidate_indices"].items():
            self.assertAlmostEqual(sum(p),1,places=12,msg=name)
        self.assertEqual(set(m.WIN_FORECASTS).issubset(z["candidate_indices"]),True)

    def test_same_one_real_quote_seed_replicates_are_not_new_market_data(self):
        from keiba_r8_threepoint_seed_noise import audit as seed_audit
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("NO_RACE_WINNERS_ALLOWED")):
            z=seed_audit(n_seeds=2,horse_draws=40,seed=100)
        self.assertEqual(z["independent_real_next_quote_targets"],1)
        self.assertEqual(z["artificial_horse_bettor_seed_repetitions"],2)
        self.assertFalse(z["real_bettor_vote_counts_or_JRA_race_outcomes_consumed"])
        for name in m.WIN_FORECASTS:
            item=z["by_fixed_candidate"][name]
            self.assertAlmostEqual(
                item["single_real_target_5seed_TV_max_pp"],
                item["single_real_target_5seed_TV_min_pp"],places=12)

    def test_locked_future_source_and_nulls_score_one_real_market(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("OFFICIAL_RESULT_LEAK")) as fn:
            z=m.audit(repetitions=120,horse_draws=40,seed=20261025)
            fn.assert_not_called()
        self.assertEqual(z["status"],
             "RETROSPECTIVE_NEXT_QUOTE_SINGLE_RACE_NOT_HOLDOUT")
        self.assertEqual(z["n_real_races"],1)
        self.assertEqual(z["n_horses"],11)
        self.assertEqual(len(z["candidate_forecast_scores"]),9)
        self.assertEqual(len(z["null_condition_sensitivity"]),12)
        self.assertGreater(z["previous_65minute_interval_TV_pp"],0)
        self.assertGreater(z["next_18minute_interval_TV_pp"],0)
        self.assertLessEqual(
            z["display_0_05_half_bin_conditional_lower_bound_TV_pp"],
            z["next_18minute_interval_TV_pp"])
        self.assertTrue(z["source_provider_same_all_three_quote_points"])
        self.assertTrue(z["historical_form_was_retrieved_after_2026_target"])
        self.assertTrue(z["same_source_price_and_horse_bettor_ABM_comparison_only"])
        self.assertFalse(z["market_criticality_or_information_arrival_inferred"])


if __name__=="__main__":
    unittest.main()
