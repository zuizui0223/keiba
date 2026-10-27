#!/usr/bin/env python3
"""Predeclared paired A WIDE / B WIN-only q2 target, one original real race."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import tempfile
import unittest

try:
    import numpy as np
except ModuleNotFoundError:
    np=None

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
if np is not None:
    import keiba_dual_market_lane_audit as m
    import keiba_operator_winwide_capture as op
    import keiba_operator_cohort_bundle as A
    import keiba_win_only_shadow_lane as B
    from test_keiba_operator_winwide_capture import card,win,wide,DATE


@unittest.skipIf(np is None,"NumPy required by integrated horse/voter numerical model")
class DualMarketSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger=Path(self.tmp.name)/"private"/"chain"
        self.card=card()
        # CONTRACT-ONLY fixture: fake rights-reviewed source is still
        # synthetic and is NEVER remotely submitted as a real JRA result.
        self.card["provenance"]="authorized_private_local_export"
        self.card["rights_reviewed_by_operator"]=True

    def append(self,source,t):
        src=copy.deepcopy(source)
        src["provenance"]="authorized_private_local_export"
        src["rights_reviewed_by_operator"]=True
        return op.append_capture(self.ledger,src,
                                 captured_at_jst=DATE+t+"+09:00")

    def early(self,*,wide_available=True):
        self.append(win(10),"T10:02:00")
        self.append(win(11,scale=1.1),"T11:01:00")
        if wide_available:
            self.append(wide(),"T11:02:00")

    def freeze_A(self):
        return A.prepare_bundle(
            self.ledger,self.card,frozen_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=45,seed=33)

    def freeze_B(self):
        return B.prepare_win_only(
            self.ledger,self.card,frozen_at_jst=DATE+"T11:03:00+09:00",
            horse_draws=45,seed=33)

    def later(self,minute=17):
        self.append(win(11,minute,scale=1.3),
                    f"T11:{minute+1:02d}:00")

    def test_A_B_score_the_identical_q2_with_no_extra_race_units(self):
        self.early()
        bundle=self.freeze_A()
        b=self.freeze_B()
        self.later()
        report=m.compare_once(
            self.ledger,self.card,asof=DATE+"T11:21:00+09:00",
            lane_A_bundle=bundle,lane_B_freeze=b)
        self.assertTrue(report["lane_A_locally_scored"])
        self.assertTrue(report["lane_B_locally_scored"])
        self.assertEqual(report["one_operator_declared_race_not_two"],1)
        paired=report["within_race_A_B_paired_market_index_contrast"]
        self.assertEqual(paired["status"],
            "PAIRED_SAME_WIN_q0_qMID_q2_WITH_WIDE_SIGNAL_LOCAL_ONLY")
        self.assertEqual(paired["single_actual_source_race_declared"],1)
        self.assertTrue(report["full_WIDE_absence_cannot_be_imputed_by_lane_B"])
        self.assertFalse(report["any_external_GitHub_SHA_proof_actually_verified_by_this_script"])
        self.assertEqual(report["new_independently_proven_prospective_market_trials"],0)
        cohort=m.cohort([report])
        self.assertEqual(cohort["lane_A_full_WIDE_local_scores"],1)
        self.assertEqual(cohort["lane_B_WIN_only_local_scores"],1)
        self.assertEqual(cohort["same_q0_qmid_q2_paired_local_competitions"],1)
        self.assertEqual(cohort["unique_locally_scored_races_NOT_sum_of_A_and_B"],1)
        self.assertEqual(cohort["registered_grade_denominator"],26)
        self.assertEqual(cohort["registered_auxiliary_denominator"],64)
        self.assertEqual(cohort["certified_independent_new_JRA_market_trials"],0)

    def test_no_WIDE_B_only_works_but_A_remains_missing(self):
        self.early(wide_available=False)
        b=self.freeze_B()
        with self.assertRaisesRegex(ValueError,"NO_SAME_SOURCE_MINUTE"):
            self.freeze_A()
        self.later()
        r=m.compare_once(self.ledger,self.card,
                         asof=DATE+"T11:21:00+09:00",
                         lane_B_freeze=b)
        self.assertFalse(r["lane_A_locally_scored"])
        self.assertTrue(r["lane_B_locally_scored"])
        self.assertEqual(r["lane_A_complete_WIDE_status"],
                         "HOLD_FULL_WIDE_NOT_PRETARGET_FROZEN")
        self.assertIsNone(r["within_race_A_B_paired_market_index_contrast"])
        q=m.cohort([r])
        self.assertEqual(q["lane_A_missing_or_unfrozen"],1)
        self.assertEqual(q["lane_B_WIN_only_local_scores"],1)
        self.assertEqual(q["unique_locally_scored_races_NOT_sum_of_A_and_B"],1)

    def test_no_eligible_next_quote_keeps_both_lanes_missing_after_post(self):
        self.early()
        a=self.freeze_A()
        b=self.freeze_B()
        self.later(minute=24)
        report=m.compare_once(self.ledger,self.card,
                         asof=DATE+"T15:46:00+09:00",
                         lane_A_bundle=a,lane_B_freeze=b)
        self.assertFalse(report["lane_A_locally_scored"])
        self.assertFalse(report["lane_B_locally_scored"])
        self.assertEqual(report["one_operator_declared_race_not_two"],0)
        self.assertIsNone(report["within_race_A_B_paired_market_index_contrast"])
        cohort=m.cohort([report])
        self.assertEqual(cohort["distinct_operator_declared_real_race_IDs"],1)
        self.assertEqual(cohort["unique_locally_scored_races_NOT_sum_of_A_and_B"],0)

    def test_wrong_common_q0_qmid_or_q2_never_promoted_as_paired_info_gain(self):
        self.early()
        a=self.freeze_A()
        b=self.freeze_B()
        self.later()
        from odds_shadow_freeze_score import _seal
        changed=copy.deepcopy(b)
        changed["payload"]["source_first_WIN_published"]=(
            DATE+"T10:01:00+09:00")
        changed["seal_sha256_of_canonical_payload"]=_seal(changed["payload"])
        with self.assertRaisesRegex(ValueError,"DIFFERENT_SOURCE_Q0_QMID_OR_Q2"):
            m.compare_once(self.ledger,self.card,
                asof=DATE+"T11:21:00+09:00",
                lane_A_bundle=a,lane_B_freeze=changed)
        changed=copy.deepcopy(b)
        rows=changed["payload"]["fixed_next_quote_model_indices"][
            "WIN_mid_persistence"]
        rows[0]["p"]+=0.01
        rows[1]["p"]-=0.01
        changed["seal_sha256_of_canonical_payload"]=_seal(changed["payload"])
        with self.assertRaisesRegex(ValueError,"ORIGINAL_WIN_PRICE_VECTORS_NOT_IDENTICAL"):
            m.compare_once(self.ledger,self.card,
                asof=DATE+"T11:21:00+09:00",
                lane_A_bundle=a,lane_B_freeze=changed)

    def test_double_counted_real_race_and_slot_rejected_from_cohort(self):
        self.early()
        b=self.freeze_B()
        self.later()
        r=m.compare_once(self.ledger,self.card,
                         asof=DATE+"T11:21:00+09:00",
                         lane_B_freeze=b)
        with self.assertRaisesRegex(ValueError,"DUPLICATE_JRA_PHYSICAL_RACE"):
            m.cohort([r,copy.deepcopy(r)])
        other=copy.deepcopy(r)
        other["registered_primary_slot_id"]="2026-10-31|京都|R11"
        with self.assertRaisesRegex(ValueError,"DUPLICATE_JRA_PHYSICAL_RACE"):
            m.cohort([r,other])

    def test_incomplete_card_or_unsealed_A_cannot_fake_lanes(self):
        self.early()
        with self.assertRaisesRegex(ValueError,"NO_SOURCE_FROZEN"):
            m.compare_once(self.ledger,self.card,
                           asof=DATE+"T11:21:00+09:00")
        a=self.freeze_A()
        b=self.freeze_B()
        x=copy.deepcopy(self.card)
        x["race_id"]="FAKE_RACE"
        with self.assertRaises(ValueError):
            m.compare_once(self.ledger,x,
                           asof=DATE+"T11:21:00+09:00",
                           lane_A_bundle=a,lane_B_freeze=b)
        with self.assertRaisesRegex(ValueError,"NOT_A_TYPE_SAFE"):
            m.compare_once(self.ledger,self.card,
                           asof=DATE+"T11:21:00+09:00",
                           lane_B_freeze=a["freeze"])


if __name__=="__main__":
    unittest.main()
