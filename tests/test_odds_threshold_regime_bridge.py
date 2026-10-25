#!/usr/bin/env python3
"""Numerical and provenance regressions for the new *unfitted* threshold audit."""
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import odds_threshold_regime_bridge as m


def row(*, duration_h=1.0, first=None, last=None):
    from datetime import datetime, timedelta, timezone
    if first is None:
        first = {1: 3.0, 2: 7.0, 3: 11.0, 4: 15.0, 5: 22.0, 6: 40.0}
    if last is None:
        last = {1: 3.0, 2: 8.0, 3: 9.0, 4: 15.5, 5: 27.0, 6: 36.0}
    start = datetime(2026, 10, 12, 11, 0, tzinfo=timezone(timedelta(hours=9)))
    return {"first_odds": first, "last_odds": last,
            "initial_quote_at": start.isoformat(),
            "latest_quote_at": (start+timedelta(hours=duration_h)).isoformat(),
            "post_at": (start+timedelta(days=1)).isoformat(),
            "race_id": "TEST_20261012", "race_no": 8,
            "meeting_day": "2026-10-12", "source_scope": "SYNTHETIC"}


class ThresholdPureMathTest(unittest.TestCase):
    def test_probability_mass_all_models(self):
        models = m.forecast_prestart(row())
        self.assertEqual(tuple(models["predictions"]), m.MODEL_NAMES)
        for prediction in models["predictions"].values():
            self.assertAlmostEqual(sum(prediction["win"]), 1.0, places=11)
            self.assertAlmostEqual(sum(prediction["top3"]), 3.0, places=11)
            self.assertTrue(all(0 < p < 1 for p in prediction["win"]))
            self.assertTrue(all(0 < p < 1 for p in prediction["top3"]))

    def test_M0_M1_M2_exact_historical_compatibility(self):
        f = m.market_features(row())
        for name, beta, cutoff in (("M0_latest", 0, None),
                                   ("M1_smooth", .25, None),
                                   ("M2_initial10", .25, 10.0)):
            expected = m.normalize([
                q*math.exp(beta*math.log(q/p) *
                           (cutoff is None or o >= cutoff))
                for q, p, o in zip(f["latest"], f["early"], f["initial_odds"])
            ])
            observed = m.forecast_prestart(row())["predictions"][name]["win"]
            for a, b in zip(expected, observed):
                self.assertAlmostEqual(a, b, places=14)

    def test_M3_gates_are_subset_of_M2_and_clock_normalized(self):
        short = m.forecast_prestart(row(duration_h=1.0))
        long = m.forecast_prestart(row(duration_h=10.0))
        g2 = short["gates"]["M2_initial10"]
        g3 = short["gates"]["M3_initial10_speed010"]
        self.assertTrue(any(g3))
        self.assertTrue(all(not a or b for a, b in zip(g3, g2)))
        self.assertGreater(sum(g3), sum(long["gates"]["M3_initial10_speed010"]))

    def test_flat_relative_market_never_passes_speed_gate(self):
        first = {i: float(i+5) for i in range(1, 7)}
        last = {i: 2*v for i, v in first.items()}
        output = m.forecast_prestart(row(first=first, last=last))
        self.assertFalse(any(output["gates"]["M3_initial10_speed010"]))
        self.assertEqual(output["predictions"]["M3_initial10_speed010"]["win"],
                         output["predictions"]["M0_latest"]["win"])

    def test_no_unexpected_features_from_outcome_columns(self):
        base = row()
        with_fake_result = {**base, "top3": [1, 2, 3], "winner": 2,
                            "payout": 900000, "future_market_quote": 1.1}
        self.assertEqual(m.forecast_prestart(base), m.forecast_prestart(with_fake_result))

    def test_timing_and_roster_gates(self):
        bad = row()
        bad["latest_quote_at"] = bad["post_at"]
        with self.assertRaisesRegex(ValueError, "TOO_LATE"):
            m.forecast_prestart(bad)
        bad = row()
        bad["latest_quote_at"] = "2026-10-12T12:00:00"
        with self.assertRaisesRegex(ValueError, "NAIVE"):
            m.forecast_prestart(bad)
        bad = row()
        bad["last_odds"] = {1: 4.0, 2: 6.0}
        with self.assertRaisesRegex(ValueError, "FULL_FIELD"):
            m.forecast_prestart(bad)

    def test_score_top3_validates_runner_and_is_race_level(self):
        out = m.forecast_prestart(row())
        f, p = out["features"], out["predictions"]["M0_latest"]
        good = m.score_forecast(f, p, [1, 2, 3])
        self.assertGreater(good["win_log_loss"], 0)
        self.assertGreater(good["top3_brier"], 0)
        with self.assertRaisesRegex(ValueError, "FINISH"):
            m.score_forecast(f, p, [1, 2, 99])

    def test_prestart_mode_never_requests_postrace_labels(self):
        specimen = row()
        with patch.object(m, "load_source_locked_panels", return_value=[specimen]*6), \
             patch.object(m, "real_three_point_regime", return_value={"synthetic": True}), \
             patch.object(m, "_score_history", side_effect=AssertionError("LABEL_LEAK")):
            report = m.audit(prestart_only=True)
        self.assertEqual(report["status"], "PRESTART_ONLY_NO_OFFICIAL_OUTCOMES_READ")
        self.assertEqual(report["postrace_scores"], "NOT_COMPUTED")
        self.assertFalse(report["qualified_for_forward_threshold_inference"])
        self.assertTrue(report["no_outcome_based_threshold_selection"])
        self.assertNotIn("mean_postrace_scores_race_equal", report)

    def test_zero_difference_models_no_claim(self):
        specimen = row(first={i: float(6+i) for i in range(1, 7)},
                       last={i: float(6+i) for i in range(1, 7)})
        f = m.forecast_prestart(specimen)
        self.assertAlmostEqual(f["KL_M0_to_model"]["M3_initial10_speed010"], 0)
        self.assertEqual(f["predictions"]["M0_latest"]["win"],
                         f["predictions"]["M3_initial10_speed010"]["win"])

    def test_grid_fixed_and_information_threshold_distinct(self):
        self.assertEqual(m.INITIAL_ODDS_GRID, (5., 10., 20., 50.))
        self.assertEqual(m.SPEED_GRID, (.05, .10, .20))
        self.assertEqual(m.INFORMATION_KL_STRATUM_CUTOFF, .005)
        self.assertNotEqual(m.SPEED_LOG_PER_HOUR_CUTOFF, m.INFORMATION_KL_STRATUM_CUTOFF)

    def test_exact_pl_equals_hand_enumeration_for_five_horses(self):
        w = [3, 2, 1, 4, 1]
        computed = m.exact_win_top3(w)
        p = m.normalize(w)
        for i in range(5):
            brute = 0.0
            for a in range(5):
                for b in range(5):
                    for c in range(5):
                        if len({a, b, c}) == 3 and i in (a, b, c):
                            brute += p[a]*p[b]/(1-p[a])*p[c]/(1-p[a]-p[b])
            self.assertAlmostEqual(computed["top3"][i], brute, places=12)


if __name__ == "__main__":
    unittest.main()

# In GitHub CI, the exact original source archives are present; this test is
# skipped only for a standalone copy of the pure-math module in a scratch dir.
class ThresholdSourceLockedIntegrationTest(unittest.TestCase):
    @unittest.skipUnless((m.ROOT / "data/2026-10-12/kyoto_08.json").exists(),
                         "Requires full archived keiba repository checkout")
    def test_real_six_race_contract_and_negative_result(self):
        report = m.audit()
        self.assertEqual(report["races"], 6)
        self.assertEqual(report["horse_entries"], 84)
        self.assertEqual(report["meeting_dates"], 2)
        self.assertEqual(report["high_KL_M1_races"], 0)
        self.assertEqual(report["race_count_lower_win_log_loss_than_M0"]["M3_initial10_speed010"], 1)
        self.assertFalse(report["qualified_for_forward_threshold_inference"])
        self.assertTrue(report["no_outcome_based_threshold_selection"])
        scores = report["mean_postrace_scores_race_equal"]
        self.assertAlmostEqual(scores["M0_latest"]["win_log_loss"], 1.696959293802405, places=7)
        self.assertAlmostEqual(scores["M1_smooth"]["win_log_loss"], 1.696681573413395, places=7)
        self.assertAlmostEqual(scores["M2_initial10"]["win_log_loss"], 1.698632399258879, places=7)
        self.assertAlmostEqual(scores["M3_initial10_speed010"]["win_log_loss"], 1.697686248432792, places=7)
        self.assertAlmostEqual(report["three_time_single_race"]["segments"][0]["mean_abs_log_change_per_hour"], .095861118449424, places=7)
        self.assertAlmostEqual(report["three_time_single_race"]["segments"][1]["mean_abs_log_change_per_hour"], .632758482039174, places=7)
        self.assertEqual(sum(r["M3_gated_entries"] for r in report["per_race"]), 5)
