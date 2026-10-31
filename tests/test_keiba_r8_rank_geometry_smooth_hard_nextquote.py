#!/usr/bin/env python3
"""R8 single real archival q2, source-before-target barrier and PR19 null."""
from __future__ import annotations
import copy
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
try:
    import numpy as np
except ModuleNotFoundError:
    np=None
if np is not None:
    import keiba_r8_rank_geometry_smooth_hard_nextquote as m


@unittest.skipIf(np is None,"NumPy required by original PR19 bidder and R8 parser")
class RealOneR8NextQuoteBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if np is None:
            return
        cls.frozen=m.freeze_1326_only(ROOT,n_seeds=5,seed=20261031)

    def test_honest_only_1221_and_1326_features_no_1344_target_read(self):
        with patch.object(m,"validate_later_quote",
                          side_effect=AssertionError("FUTURE_QUOTE_LEAK")):
            pre=m.freeze_1326_only(ROOT,n_seeds=3)
        self.assertTrue(pre["freeze_payload"][
            "no_target_quote_or_horse_finish_result_consulted_before_freeze"])
        self.assertFalse(pre["external_SHA_pre_target_attested"])
        self.assertTrue(pre["freeze_payload"][
            "retrospective_original_target_already_in_past_at_GitHub_PR_creation"])
        self.assertTrue(pre["freeze_payload"][
            "no_genuine_pretarget_SHA_commit_or_external_source_receipt"])

    def test_named_price_only_candidates_and_three_real_PR19_voter_rules(self):
        p=m.verify_freeze(self.frozen)
        self.assertEqual(set(p["fixed_market_only_candidates"]),set(m.MODEL_NAMES[:4]))
        self.assertEqual(set(p["no_information_original_PR19_vote_paths_by_seed"]),
                         set(m.MODEL_NAMES[4:]))
        self.assertEqual(len(p["forecast_indices_only_initial_and_middle_WIN"][
            "horse_numbers"]),11)
        self.assertEqual(p["predeclared_method_constants"][
            "horizon_minutes"],18)
        self.assertEqual(p["predeclared_method_constants"][
            "rate_threshold_log_index_per_hour"],.10)
        self.assertTrue(0<p["imposed_continuous_price_projection_gain"]<1)
        self.assertIn(p["imposed_hard_price_projection_gain"],(0.,1.))
        for rule,v in p["no_information_original_PR19_vote_paths_by_seed"].items():
            self.assertEqual(len(v),5)
            for seed_rows in v:
                self.assertEqual(len(seed_rows),11)
                self.assertAlmostEqual(sum(x["p"] for x in seed_rows),1,places=10)
        self.assertTrue(all(x==0 for key,v in p[
            "no_information_original_PR19_hard_gate_events_by_seed"].items()
            for x in v if key!="uninformed_PR19_hard_ABM"))

    def test_market_only_rank_forecasts_can_change_without_herding(self):
        p=m.verify_freeze(self.frozen)
        rows=p["fixed_market_only_candidates"]
        q=np.asarray([x["p"] for x in rows["WIN_latest_persistence"]])
        trend=np.asarray([x["p"] for x in rows["WIN_full_log_momentum_beta1"]])
        self.assertFalse(np.array_equal(q,trend))
        self.assertAlmostEqual(sum(trend),1,places=12)

    def test_forecast_parameters_and_sha_fail_closed(self):
        a=copy.deepcopy(self.frozen)
        a["freeze_payload"]["predeclared_method_constants"][
            "rate_threshold_log_index_per_hour"] = .5
        with self.assertRaisesRegex(ValueError,
                                     "HOLD_R8_RETROSPECTIVE_MODEL_SHA_TAMPERED"):
            m.verify_freeze(a)
        a=copy.deepcopy(self.frozen)
        a["external_SHA_pre_target_attested"]=True
        with self.assertRaisesRegex(ValueError,
                                     "HOLD_R8_INVALID_RETROSPECTIVE_FROZEN_SCHEMA"):
            m.verify_freeze(a)
        a=copy.deepcopy(self.frozen)
        a["freeze_payload"]["fixed_market_only_candidates"][
            "WIN_latest_persistence"][0]["p"]=-1.0
        a["local_replay_SHA256_not_pretarget"]=m._seal(a["freeze_payload"])
        with self.assertRaisesRegex(ValueError,
                                     "HOLD_R8_FROZEN_CANDIDATE_INVALID_SIMPLEX"):
            m.verify_freeze(a)

    def test_single_true_archived_1344_q2_scores_all_seven_models_not_results(self):
        score=m.score_original_later_quote(ROOT,frozen=self.frozen)
        self.assertEqual(score["independent_real_target_market_intervals"],1)
        self.assertEqual(score["independent_real_target_horse_races"],1)
        self.assertEqual(score["new_prospective_verified_target_intervals"],0)
        self.assertTrue(score[
            "old_2026_Oct12_target_was_known_long_before_current_GitHub_code"])
        self.assertFalse(score["actual_JRA_race_result_or_bettor_stakes_read"])
        self.assertFalse(score["real_horse_GPS_or_independent_horse_ability_used"])
        self.assertEqual(score["model_selection_or_criticality_from_one_target"],
                         "HOLD")
        self.assertEqual(set(score["by_predeclared_price_model"]),
                         set(m.MODEL_NAMES))
        self.assertEqual(score["target_price_rank_geometry"][
            "actually_reversed_pairs"],7)
        self.assertAlmostEqual(score["target_price_rank_geometry"][
            "actual_relative_index_TV_pp"],9.656362948215287,places=9)
        self.assertAlmostEqual(score["by_predeclared_price_model"][
            "WIN_latest_persistence"]["one_real_target_index_TV_pp"],
            9.656362948215287,places=9)
        for label in m.MODEL_NAMES[4:]:
            v=score["by_predeclared_price_model"][label]
            self.assertLessEqual(v[
                "min_one_target_TV_over_only_synthetic_seeds_pp"],
                v["mean_one_target_TV_over_only_synthetic_seeds_pp"])
            self.assertLessEqual(v[
                "mean_one_target_TV_over_only_synthetic_seeds_pp"],
                v["max_one_target_TV_over_only_synthetic_seeds_pp"])
            self.assertTrue(v[
                "artificial_seeds_are_not_new_independent_market_targets"])

    def test_market_index_log_brier_like_scores_not_horse_win_rates(self):
        u=np.array([.3,.2,.2,.2,.1])
        r=m._tilt(u,np.array([.4,.0,.0,-.1,-.1]),1.0)
        self.assertTrue(np.isclose(r.sum(),1))
        self.assertAlmostEqual(m._TV(u,u),0,places=12)
        self.assertAlmostEqual(m._KL(u,u),0,places=12)
        self.assertGreater(m._TV(u,r),0)
        self.assertGreater(m._KL(u,r),0)

    def test_wrong_roster_and_invalid_stochastic_parameters_hold(self):
        for a in (float("nan"),float("inf"),-1,0):
            with self.subTest(s=a):
                with self.assertRaisesRegex(ValueError,
                        "HOLD_R8_INVALID_PRICE_MOMENTUM_SHAPE"):
                    m._tilt(np.ones(5)/5,np.zeros(5),a)
        with self.assertRaisesRegex(ValueError,
                "HOLD_R8_INVALID_PREDECLARED_ARTIFICIAL_SEEDS"):
            m.freeze_1326_only(ROOT,n_seeds=1)
        with self.assertRaisesRegex(ValueError,
                "HOLD_R8_NOT_COMPLETE_POSITIVE_MARKET_VECTOR"):
            m._positive_simplex([1.0,2.0,-3.0,4.0,5.0])


if __name__=="__main__":
    unittest.main()
