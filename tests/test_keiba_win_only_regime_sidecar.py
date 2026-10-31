#!/usr/bin/env python3
"""B+ same-source/same-target sidecar with original PR30 six frozen models."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
if np is not None:
    import keiba_win_only_regime_sidecar as b
    import keiba_win_only_shadow_lane as parent_mod
    import keiba_operator_winwide_capture as capture
    from test_keiba_operator_winwide_capture import card, win, DATE


@unittest.skipIf(np is None,"Original horse ABM/PDE/voter models require NumPy")
class WINRegimeSidecarTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger=Path(self.tmp.name)/"private"/"chain"
        self.card=card()
        capture.append_capture(self.ledger,win(10),
            captured_at_jst=DATE+"T10:02:00+09:00")
        capture.append_capture(self.ledger,win(11,scale=1.1),
            captured_at_jst=DATE+"T11:01:00+09:00")
        self.parent=parent_mod.prepare_win_only(
            self.ledger,self.card,frozen_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=45,seed=13)
        self.sidecar=b.freeze_companion(
            self.ledger,self.card,self.parent,
            freeze_at_jst=DATE+"T11:04:00+09:00")

    def target(self,minute=17,scale=1.2):
        capture.append_capture(self.ledger,win(11,minute,scale=scale),
            captured_at_jst=DATE+f"T11:{minute+1:02d}:00+09:00")

    def score(self,asof=None,complete=True):
        return b.score_companion(
            self.ledger,self.card,self.parent,self.sidecar,
            asof=asof or DATE+"T11:21:00+09:00",
            operator_declares_capture_complete=complete)

    def test_five_new_models_parent_six_untouched_same_roster_source_chain(self):
        p=b.verify_companion(self.sidecar)
        q=parent_mod.verify_win_only(self.parent)
        self.assertEqual(set(q["fixed_next_quote_model_indices"]),
                         set(parent_mod.MODEL_NAMES))
        self.assertEqual(set(p["sidecar_price_candidate_indices"]),
                         set(b.MODELS[:2]))
        self.assertEqual(set(p["sidecar_no_new_horse_signal_vote_paths"]),
                         set(b.MODELS[2:]))
        self.assertEqual(p["horse_numbers"],q["horse_numbers"])
        self.assertEqual(p["parent_original_six_model_freeze_SHA256"],
                         self.parent["seal_sha256_of_canonical_payload"])
        self.assertEqual(p["original_source_chain_head_SHA256"],
                         q["original_local_capture_chain_prefix_SHA256"])
        self.assertEqual(p["target_WIN_window_start"],
                         DATE+"T11:15:00+09:00")
        self.assertEqual(p["target_WIN_window_end"],
                         DATE+"T11:20:00+09:00")
        self.assertEqual(p["original_six_models_not_replaced"],
                         list(parent_mod.MODEL_NAMES))
        self.assertFalse(self.sidecar["external_pre_target_GitHub_SHA_proven"])
        self.assertEqual(set(p["code_file_SHA256"]),set(b.CODE_FILES))
        for row in p["sidecar_price_candidate_indices"].values():
            self.assertAlmostEqual(sum(x["p"] for x in row),1,places=12)
        for name, paths in p["sidecar_no_new_horse_signal_vote_paths"].items():
            self.assertEqual(len(paths),30)
            for rows in paths:
                self.assertEqual([x["n"] for x in rows],q["horse_numbers"])
                self.assertAlmostEqual(sum(x["p"] for x in rows),1,places=12)
            self.assertEqual(len(
                p["sidecar_no_new_horse_signal_hard_gate_counts"][name]),30)

    def test_smooth_hard_price_gains_match_inherited_source_clock_formula(self):
        p=self.sidecar["payload"]
        prices=b._first_two_full_win(
            self.ledger,self.card,
            frozen_at=p["sidecar_local_freeze_clock"])
        ids=p["horse_numbers"]
        a=b._normalize([1/prices["prices_first"][n] for n in ids])
        c=b._normalize([1/prices["prices_second"][n] for n in ids])
        h=(prices["second_t"]-prices["first_t"]).total_seconds()/3600
        rate=np.max(np.abs(np.log(c/a)))/h
        self.assertAlmostEqual(
            p["fixed_price_change_rate_log_index_per_hour"],rate)
        self.assertAlmostEqual(
            p["fixed_continuous_alpha"],rate/(rate+.1))
        self.assertEqual(p["fixed_hard_alpha"],
                         1.0 if rate>=.1 else 0.0)
        self.assertEqual(p["fixed_rate_scale_log_index_per_hour"],.1)
        self.assertEqual(p["fixed_target_horizon_minutes"],15)
        expected=b._project(c,np.log(c/a)*(.25/h),p["fixed_continuous_alpha"])
        observed=b._vector(p["sidecar_price_candidate_indices"][b.MODELS[0]],ids)
        np.testing.assert_allclose(observed,expected,atol=1e-12,rtol=0)

    def test_no_independent_horse_signal_or_future_target_enters_preseal(self):
        # Ensure 30 x 3 actual original PR19 market voters receive
        # arrival=5, qmid==signal, never a hypothetical horse output.
        calls=[]
        original=b.voter_path
        def witness(q,signal,**kwargs):
            self.assertTrue(np.array_equal(q,signal))
            self.assertEqual(kwargs["arrival"],5)
            calls.append(kwargs["policy"])
            return original(q,signal,**kwargs)
        with patch.object(b,"voter_path",side_effect=witness):
            frozen=b.freeze_companion(self.ledger,self.card,self.parent,
                  freeze_at_jst=DATE+"T11:04:00+09:00")
        self.assertEqual(len(calls),90)
        self.assertEqual(set(calls),{"fixed","smooth","hard"})
        self.assertEqual(frozen,self.sidecar)

    def test_next_WIN_score_all_11_on_exact_same_q2_as_parent(self):
        self.target(minute=17)
        original=parent_mod.score_win_only(
            self.ledger,self.card,self.parent,
            asof=DATE+"T11:21:00+09:00",
            operator_declares_capture_complete=True)
        result=self.score()
        self.assertEqual(result["status"],b.SCORED_STATUS)
        self.assertEqual(result["source_target_published"],
                         DATE+"T11:17:00+09:00")
        self.assertEqual(result["source_target_received"],
                         DATE+"T11:18:00+09:00")
        self.assertEqual(result["original_PR30_six_model_scores_unchanged"],
                         original["model_score_TV_KL"])
        self.assertEqual(set(result[
            "five_additional_companion_models_same_original_q2"]),
            set(b.MODELS))
        self.assertEqual(result["total_models_same_one_race"],11)
        self.assertEqual(result["independent_race_count_not_six_plus_five"],1)
        self.assertFalse(result["genuine_external_SHA_verification_of_both_freezes"])
        self.assertFalse(result["new_independently_proven_next_market_trial"])
        self.assertEqual(result["parent_original_six_model_SHA256"],
                         self.parent["seal_sha256_of_canonical_payload"])
        self.assertEqual(result["sidecar_local_SHA256"],
                         self.sidecar["sidecar_local_SHA256_not_remote_receipt"])
        for label,score in result[
                "five_additional_companion_models_same_original_q2"].items():
            if label in b.MODELS[:2]:
                self.assertGreaterEqual(score["TV_pp"],0)
                self.assertGreaterEqual(score["KL_later_target_vs_model_nats"],-1e-12)
            else:
                self.assertEqual(
                    score["synthetic_seed_count_NOT_independent_races"],30)

    def test_first_eligible_target_reused_and_cannot_select_better_one(self):
        self.target(minute=17,scale=1.05)
        self.target(minute=18,scale=2.0)
        a=self.score()
        self.assertEqual(a["source_target_published"],
                         DATE+"T11:17:00+09:00")

    def test_missing_next_quote_remains_HOLD_and_never_zero_loss(self):
        with self.assertRaisesRegex(ValueError,"WINDOW_NOT_CLOSED"):
            self.score(asof=DATE+"T11:16:00+09:00")
        with self.assertRaisesRegex(ValueError,"NO_FINAL_MISSING"):
            self.score(asof=DATE+"T11:21:00+09:00")
        r=self.score(asof=DATE+"T15:46:00+09:00")
        self.assertEqual(r["status"],b.MISSING_STATUS)
        self.assertFalse(r["one_original_market_target_observed"])
        self.assertTrue(r["unobserved_original_target_not_imputed"])
        self.assertNotIn("five_additional_companion_models_same_original_q2",r)

    def test_bad_parent_or_sidecar_sha_and_after_target_time_HOLD(self):
        forged=copy.deepcopy(self.sidecar)
        forged["payload"]["fixed_hard_alpha"]=9.
        with self.assertRaisesRegex(ValueError,"SHA_OR_PAYLOAD_CHANGED"):
            b.verify_companion(forged)
        forged=copy.deepcopy(self.sidecar)
        forged["external_pre_target_GitHub_SHA_proven"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_REMOTE_CLAIM"):
            b.verify_companion(forged)
        tampered=copy.deepcopy(self.parent)
        tampered["payload"]["model_seed"]=888
        with self.assertRaisesRegex(ValueError,"SHA_OR_SCHEMA"):
            b.freeze_companion(self.ledger,self.card,tampered,
                freeze_at_jst=DATE+"T11:04:00+09:00")
        with self.assertRaisesRegex(ValueError,"AFTER_TARGET"):
            b.freeze_companion(self.ledger,self.card,self.parent,
                freeze_at_jst=DATE+"T11:16:00+09:00")
        with self.assertRaisesRegex(ValueError,"BEFORE_PARENT"):
            b.freeze_companion(self.ledger,self.card,self.parent,
                freeze_at_jst=DATE+"T11:02:00+09:00")

    def test_original_capture_chain_and_card_changes_fail_closed(self):
        altered=copy.deepcopy(self.card)
        altered["race_distance_m"]=1800
        with self.assertRaisesRegex(ValueError,"PARENT_FINAL_CARD_CHANGED"):
            b.freeze_companion(self.ledger,altered,self.parent,
                freeze_at_jst=DATE+"T11:04:00+09:00")
        corrupt=copy.deepcopy(self.sidecar)
        corrupt["payload"]["parent_original_six_model_freeze_SHA256"]="a"*64
        corrupt["sidecar_local_SHA256_not_remote_receipt"]=b._seal(corrupt["payload"])
        self.target()
        with self.assertRaisesRegex(ValueError,"DIFFERENT_PARENT"):
            b.score_companion(self.ledger,self.card,self.parent,corrupt,
                asof=DATE+"T11:21:00+09:00",
                operator_declares_capture_complete=True)

    def test_mismatched_target_or_unconfirmed_capture_stays_HOLD(self):
        self.target()
        with self.assertRaisesRegex(ValueError,"COMPLETENESS_NOT_CONFIRMED"):
            self.score(complete=False)
        a=copy.deepcopy(self.sidecar)
        a["payload"]["code_file_SHA256"][
            "scripts/keiba_win_only_regime_sidecar.py"]="f"*64
        a["sidecar_local_SHA256_not_remote_receipt"]=b._seal(a["payload"])
        with self.assertRaisesRegex(ValueError,"CODE_CHANGED"):
            b.score_companion(self.ledger,self.card,self.parent,a,
                asof=DATE+"T11:21:00+09:00",
                operator_declares_capture_complete=True)


if __name__=="__main__":
    unittest.main()
