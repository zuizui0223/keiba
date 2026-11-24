"""Oracle tests for coherent pair-residual transfer (stdlib only)."""
import math
from pathlib import Path
import unittest

from scripts.ticket_type_models import KINDS, predict_tickets
from scripts.ticket_type_historical_audit import market_race
from scripts.ticket_wide_cross_market import (
    EXPLORATORY_ALPHAS, PRIMARY_ALPHA, market_quote_time_guard,
    tilt_wide_joint, run_audit,
)


def uniform_nine():
    strengths = {n: 1.0 for n in range(1, 10)}
    frames = {n: (n if n <= 8 else 8) for n in strengths}
    quotes = [
        {"selection": [i, j], "odds_low": 20.0, "odds_high": 20.0}
        for i in strengths for j in strengths if i < j
    ]
    return strengths, frames, quotes


class WideTransferTests(unittest.TestCase):
    def test_alpha_zero_exactly_reproduces_all_eight_marginals(self):
        strengths, frames, quotes = uniform_nine()
        prior = predict_tickets(strengths, frames)
        out = tilt_wide_joint(strengths, frames, quotes, alpha=0)
        self.assertEqual(out["status"], "AVAILABLE_UNCALIBRATED_POSTHOC_DEVELOPMENT")
        self.assertEqual(set(out["ticket_types"]), set(KINDS))
        for kind in KINDS:
            self.assertEqual(set(out["ticket_types"][kind]), set(prior[kind]))
            self.assertLess(max(abs(out["ticket_types"][kind][key] - p)
                                for key, p in prior[kind].items()), 1e-12)
        self.assertAlmostEqual(out["kl_posterior_vs_prior_nats"], 0, places=12)

    def test_identical_uniform_wide_and_pl_never_change_model(self):
        strengths, frames, quotes = uniform_nine()
        base = predict_tickets(strengths, frames)
        out = tilt_wide_joint(strengths, frames, quotes, alpha=1)
        for kind in KINDS:
            self.assertTrue(all(math.isclose(out["ticket_types"][kind][key], p, abs_tol=1e-12)
                                for key, p in base[kind].items()))
        self.assertAlmostEqual(out["mean_abs_wide_market_pair_log_lift"], 0, places=12)

    def test_specific_pair_price_lift_propagates_to_other_ticket_types(self):
        strengths, frames, quotes = uniform_nine()
        for quote in quotes:
            if quote["selection"] == [1, 2]:
                quote["odds_low"] = quote["odds_high"] = 1.0
            else:
                quote["odds_low"] = quote["odds_high"] = 10.0
        base = predict_tickets(strengths, frames)
        tilt = tilt_wide_joint(strengths, frames, quotes, alpha=0.5)
        after = tilt["ticket_types"]
        self.assertGreater(after["wide"][(1, 2)], base["wide"][(1, 2)])
        self.assertGreater(after["quinella"][(1, 2)], base["quinella"][(1, 2)])
        self.assertGreater(after["trio"][(1, 2, 3)], base["trio"][(1, 2, 3)])
        for kind in KINDS:
            self.assertAlmostEqual(sum(after[kind].values()), 3 if kind in ("wide", "place") else 1, places=10)
        self.assertGreater(tilt["kl_posterior_vs_prior_nats"], 0)

    def test_missing_or_duplicated_price_is_fail_closed(self):
        strengths, frames, quotes = uniform_nine()
        out = tilt_wide_joint(strengths, frames, quotes[:-1])
        self.assertEqual(out["status"], "HOLD_INCOMPLETE_QUOTE_SET")
        self.assertIsNone(out["ticket_types"])
        with self.assertRaises(ValueError):
            tilt_wide_joint(strengths, frames, quotes + [dict(quotes[0])])
        with self.assertRaises(ValueError):
            tilt_wide_joint(strengths, frames, quotes, alpha=-0.1)
        with self.assertRaises(ValueError):
            tilt_wide_joint(strengths, frames, quotes, alpha=2)
        with self.assertRaises(ValueError):
            tilt_wide_joint(strengths, frames, quotes, odds_position="fake")

    def test_two_market_receipts_must_be_synchronous_and_pre_race(self):
        snapshot = {
            "market_observation_times": {
                "win": "2026-10-12T13:43:00+09:00",
                "wide": "2026-10-12T13:44:00+09:00",
            },
            "receipt_as_of": "2026-10-12T13:45:00+09:00",
            "start_jst": "2026-10-12T14:00:00+09:00",
        }
        self.assertEqual(market_quote_time_guard(snapshot), 60)
        snapshot["market_observation_times"]["wide"] = "2026-10-12T13:46:00+09:00"
        with self.assertRaises(ValueError):
            market_quote_time_guard(snapshot)
        snapshot["market_observation_times"]["wide"] = "2026-10-12T13:20:00+09:00"
        with self.assertRaises(ValueError):
            market_quote_time_guard(snapshot)

    def test_real_observation_timestamps_from_archived_five_races(self):
        for race in (8, 9, 10, 11, 12):
            with self.subTest(race=race):
                source = market_race(race, {})
                self.assertEqual(set(source["market_observation_times"]), set(KINDS))
                self.assertLess(market_quote_time_guard(source), 90)

    def test_all_alphas_and_quote_positions_are_reported_and_not_optimised(self):
        out = run_audit()
        self.assertFalse(out["pre_registered_before_outcome"])
        self.assertFalse(out["independent_period_validation"])
        self.assertFalse(out["positive_expected_value_established"])
        self.assertFalse(out["market_probabilities_calibrated"])
        self.assertEqual(out["primary_posthoc_alpha"], PRIMARY_ALPHA)
        self.assertEqual(len(out["races"]), 5)
        self.assertEqual(set(out["primary_equal_race_summary"]), set(KINDS))
        for race in out["races"]:
            self.assertEqual(len(race["analyses"]), 3 * len(EXPLORATORY_ALPHAS))
            for price in ("low", "geometric", "high"):
                for kind in KINDS:
                    no_tilt = race["analyses"][f"{price}:alpha=0"]["scores"][kind]
                    self.assertAlmostEqual(no_tilt["brier_after_minus_PL"], 0, places=11)
        self.assertTrue(all(len(v) == 64 for v in out["input_file_sha256"].values()))


if __name__ == "__main__":
    unittest.main()
