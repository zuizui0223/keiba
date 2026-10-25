#!/usr/bin/env python3
"""Strict provenance and independent-history placebo tests for coupled ABMs."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch
import copy
import hashlib
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
try:
    import numpy as np
except ImportError:
    np=None

if np is not None:
    import keiba_coupled_history_falsification as h
    import keiba_coupled_horse_market_pde as m


def fake_row():
    return {
        "race_id":"SYNTHETIC_RACE","race_no":8,
        "meeting_day":"2026-10-12",
        "first_odds": {i:float(i*2+2) for i in range(1,7)},
        "last_odds": {i:float(i*2+2)*1.08 for i in range(1,7)},
        "initial_quote_at":"2026-10-12T12:00:00+09:00",
        "latest_quote_at":"2026-10-12T13:00:00+09:00",
        "post_at":"2026-10-12T14:00:00+09:00",
    }


def fake_archive():
    return {
        "target_date":"2026-10-12","target_surface":"芝",
        "distance_m":2000,
        "rows":{
            i:{
                "name":f"HORSE{i}",
                "full_history_before_target":[
                    {"date":"2026-08-10","finish":i,
                     "distance_m":2000,"surface":"芝"},
                    {"date":"2026-05-09","finish":7-i,
                     "distance_m":1800,"surface":"芝"}]
            } for i in range(1,7)
        }
    }


@unittest.skipIf(np is None,"NumPy is required by numerical coupled ABM CI")
class HistoricalOnlyPureTest(unittest.TestCase):
    def test_history_only_field_whitelist_rejects_target_odds_or_label_leak(self):
        base=h.form_prior(fake_row(),fake_archive())
        changed=fake_archive()
        for num in changed["rows"]:
            changed["rows"][num]["result"] = {"win":num==3}
            changed["rows"][num]["odds"] = 1.1
            for r in changed["rows"][num]["full_history_before_target"]:
                r["popularity"] = 99999999
                r["target_future_top3"]= [1,2,3]
                r["payout"] = 9999
        derived=h.form_prior(fake_row(),changed)
        np.testing.assert_array_equal(base["prior"], derived["prior"])
        self.assertEqual(base["fields_used_in_past_records"],
                         ["date","finish","distance_m","surface"])

    def test_no_recent_past_runs_is_neutral_not_missing_horse(self):
        x=fake_archive()
        x["rows"][6]["full_history_before_target"]=[]
        p=h.form_prior(fake_row(),x)
        self.assertEqual(p["entrants_without_any_past_run"],1)
        self.assertAlmostEqual(sum(p["prior"]),1.,places=13)
        self.assertEqual(p["past_race_records_examined"],10)

    def test_current_and_future_run_hard_fail(self):
        for d in ("2026-10-12","2026-10-13"):
            z=fake_archive()
            z["rows"][1]["full_history_before_target"][0]["date"]=d
            with self.assertRaisesRegex(ValueError,"FUTURE_RUN_LEAKAGE"):
                h.form_prior(fake_row(),z)

    def test_incomplete_match_and_invalid_record_hard_fail(self):
        d=fake_archive()
        d["rows"].pop(1)
        with self.assertRaisesRegex(ValueError,"DIFFERENT_TARGET"):
            h.form_prior(fake_row(),d)
        d=fake_archive()
        d["rows"][3]["full_history_before_target"][0]["finish"]="1"
        with self.assertRaisesRegex(ValueError,"INVALID_PAST"):
            h.form_prior(fake_row(),d)

    def test_archived_source_sha_helper_detects_byte_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=root/"x.json"
            buf=b'{"a":1}\n'
            p.write_bytes(buf)
            v=hashlib.sha1(b"blob "+str(len(buf)).encode()+b"\0"+buf).hexdigest()
            self.assertEqual(h._read_git_sha(root,"x.json",v),{"a":1})
            p.write_bytes(b'{"a":2}\n')
            with self.assertRaisesRegex(ValueError,"SHA_DRIFT"):
                h._read_git_sha(root,"x.json",v)

    def test_horse_prior_is_used_by_physical_agents_not_initial_market(self):
        row=fake_row()
        form=h.form_prior(row,fake_archive())
        candidates=h.fixed_priors(row,form)
        self.assertEqual(set(candidates),set(h.ARMS))
        self.assertIsNone(candidates["market_proxy"])
        self.assertAlmostEqual(sum(candidates["history_only"]),1.)
        self.assertNotEqual(candidates["history_only"].tolist(),
                            candidates["history_shuffled"].tolist())
        base=m.couple_prestart(row, distance_m=1200, draws=80, seed=21)
        history=m.couple_prestart(row, distance_m=1200, draws=80, seed=21,
                                 horse_prior=candidates["history_only"])
        self.assertEqual(base["predictions"]["observed_M0"],
                         history["predictions"]["observed_M0"])
        self.assertEqual(base["horse_prior_source"],
                         "same_early_market_quote_proxy")
        self.assertEqual(history["horse_prior_source"],
                         "external_past_history_needs_source_clock")
        self.assertNotEqual(base["horse_signal"].tolist(),
                            history["horse_signal"].tolist())
        with self.assertRaisesRegex(ValueError,"PRIOR_ROSTER"):
            m.couple_prestart(row, distance_m=1200, draws=80,
                              horse_prior=[.4,.3,.2,.1,.05])

    def test_external_horse_prior_is_market_invariant_including_mc_smoothing(self):
        row=fake_row()
        independent_prior=h.form_prior(row,fake_archive())["prior"]
        run1=m.couple_prestart(row,distance_m=1200,draws=50,
                               seed=217,horse_prior=independent_prior)
        shifted=copy.deepcopy(row)
        shifted["first_odds"]={i:float(i*13+3) for i in row["first_odds"]}
        run2=m.couple_prestart(shifted,distance_m=1200,draws=50,
                               seed=217,horse_prior=independent_prior)
        # Shared historical physical prior must NOT borrow q0 even through
        # the fixed two-draw-equivalent Monte Carlo smoothing step.
        for kind in ("horse_P9_weak","horse_SDE_no_pack","horse_SDE_weak"):
            self.assertEqual(run1["predictions"][kind],
                             run2["predictions"][kind])
        np.testing.assert_array_equal(run1["horse_signal"],
                                      run2["horse_signal"])
        # But voters do start from the independently changing initial market.
        self.assertFalse(np.allclose(run1["initial_market_q"],
                                     run2["initial_market_q"]))

    def test_history_source_not_eligible_for_prestart_and_no_asof_promotion(self):
        with self.assertRaisesRegex(ValueError,"POSTRACE_RETRIEVED"):
            h.audit(prestart_only=True)
        with self.assertRaisesRegex(ValueError,"NO_AUTHENTIC"):
            h.audit(historical_source_asof_certified=True)


@unittest.skipIf(np is None or not (
    Path(__file__).resolve().parents[1]/
    "data/2026-10-12/v3-normalized-prerace-history.json").exists(),
    "Full archived source checkout and NumPy required")
class HistoricalRealSourceIntegrationTest(unittest.TestCase):
    def test_real_archived_all84_horses_with_original_name_identity_and_no_future(self):
        rows=h.load_source_locked_panels()
        lookup=h.history_map()
        self.assertEqual(len(rows),6)
        self.assertEqual(set(r["race_id"] for r in rows),set(lookup))
        totals=0
        no_history=0
        for row in rows:
            form=h.form_prior(row,lookup[row["race_id"]])
            totals+=len(form["horse_numbers"])
            no_history+=form["entrants_without_any_past_run"]
            self.assertTrue(form["all_run_dates_strictly_before_target"])
            self.assertFalse(form["certified_target_time_history_available"])
            self.assertAlmostEqual(sum(form["prior"]),1.,places=12)
        self.assertEqual(totals,84)
        self.assertEqual(no_history,1)

    def test_real_reconstruction_scores_are_separate_from_forward_validation(self):
        with patch("odds_six_race_predictive_increment.verify_official_oct12",
                   side_effect=AssertionError("NO_EARLY_TARGET_RESULT")) as mock:
            # Only the history mapping/form and physical ABM, never outcomes.
            row=h.load_source_locked_panels()[0]
            form=h.form_prior(row,h.history_map()[row["race_id"]])
            _=m.couple_prestart(row,distance_m=2000,draws=50,seed=33,
                                 horse_prior=form["prior"])
            mock.assert_not_called()
        report=h.audit(draws=60,seed=20261025)
        self.assertEqual(report["real_races"],6)
        self.assertEqual(report["real_meeting_dates"],2)
        self.assertEqual(report["horse_race_entries"],84)
        self.assertEqual(report["entrants_with_no_past_start"],1)
        self.assertEqual(set(report["mean_race_equal"]),set(h.ARMS))
        self.assertAlmostEqual(report["M0_late_market_reference"]["win_log_loss"],
                               1.696959293802405,places=8)
        self.assertEqual(report["prospective_model_readiness"],
                         "HOLD_UNPROVEN_HISTORY_CAPTURE_TIME")
        self.assertTrue(report["original_postrace_normalization_not_asof_proven"])
        self.assertEqual(report["by_meeting_date"]["2026-10-12"]["n_real_races"],5)
        self.assertEqual(report["by_meeting_date"]["2026-10-18"]["n_real_races"],1)
        self.assertTrue(report["meeting_date_bootstrap_not_claimed_with_2_dates"])
        self.assertIn("history_minus_shuffled_information_WIN_LL",
                      report["mean_date_equal_contrasts"])


if __name__=="__main__":
    unittest.main()
