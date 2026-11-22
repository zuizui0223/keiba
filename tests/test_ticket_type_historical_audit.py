import copy
import math
from pathlib import Path
import unittest

from scripts.ticket_type_historical_audit import (
    TARGET_RACES, direct_own_market, market_race, run_backtest, score_binary_events,
)
from scripts.ticket_type_models import _time


class HistoricalMarketAuditTests(unittest.TestCase):
    def test_real_pre_race_snapshots_and_exact_support(self):
        sha = {}
        expected = {
            8: (11, 990, 400), 9: (12, 1320, 400),
            10: (10, 720, 400), 11: (18, 4896, 400),
            12: (16, 3360, 400),
        }
        for race in TARGET_RACES:
            with self.subTest(race=race):
                data = market_race(race, sha)
                n, _, n_trifecta_quotes = expected[race]
                self.assertEqual(len(data["win_odds"]), n)
                self.assertEqual(len(data["frames"]), n)
                self.assertEqual(len(data["markets"]["trifecta"]), n_trifecta_quotes)
                self.assertLess(_time(data["receipt_as_of"]), _time(data["start_jst"]))
                self.assertTrue(all(o >= 1 for o in data["win_odds"].values()))
        self.assertTrue(all(len(digest) == 64 for digest in sha.values()))

    def test_audit_never_calls_any_fitted_horse_model(self):
        data = run_backtest()
        self.assertEqual([r["race_number"] for r in data["races"]], list(TARGET_RACES))
        self.assertEqual(set(data["by_ticket_type"]),
                         {"win", "place", "frame", "quinella", "wide", "exacta", "trio", "trifecta"})
        self.assertFalse(data["predictive_out_of_sample_validated"])
        self.assertFalse(data["probabilities_calibrated"])
        self.assertFalse(data["positive_EV_established"])
        self.assertEqual(data["races"][0]["actual_top3"], [9, 1, 7])
        self.assertEqual(data["races"][4]["actual_top3"], [10, 12, 9])
        for race in data["races"]:
            win = race["ticket_types"]["win"]
            self.assertEqual(win["possible"], race["runner_count"])
            self.assertEqual(win["quoted"], race["runner_count"])
            self.assertAlmostEqual(win["delta_brier_direct_minus_PL"], 0, places=12)
            self.assertEqual(win["direct_quote_status"], "AVAILABLE_UNCALIBRATED_PROXY")
            trifecta = race["ticket_types"]["trifecta"]
            self.assertEqual(trifecta["direct_quote_status"], "HOLD_INCOMPLETE_QUOTE_SET")
            self.assertIsNone(trifecta["direct_same_ticket_market"])
            self.assertTrue(0 < trifecta["PL_win_odds_only"]["brier_mean_per_ticket"] < 1)
        self.assertEqual(data["by_ticket_type"]["trifecta"]["races_with_complete_direct_market"], 0)

    def test_partial_and_duplicate_market_quotes_are_refused(self):
        base = [((1,), 2.0), ((2,), 4.0), ((3,), 6.0)]
        odds = [{"selection": list(k), "odds_low": o, "odds_high": o}
                for k, o in base]
        allkeys = {k for k, _ in base}
        full, status = direct_own_market(odds, "win", allkeys)
        self.assertEqual(status["status"], "AVAILABLE_UNCALIBRATED_PROXY")
        self.assertAlmostEqual(math.fsum(full.values()), 1)
        subset, status = direct_own_market(odds[:2], "win", allkeys)
        self.assertEqual(subset, {})
        self.assertEqual(status["status"], "HOLD_INCOMPLETE_QUOTE_SET")
        with self.assertRaises(ValueError):
            direct_own_market(odds + [copy.deepcopy(odds[0])], "win", allkeys)
        odds[0]["odds_high"] = 1.9
        with self.assertRaises(ValueError):
            direct_own_market(odds, "win", allkeys)

    def test_market_probabilities_not_automatically_calibrated(self):
        direct, meta = direct_own_market([
            {"selection": [1], "odds_low": 1, "odds_high": 1},
            {"selection": [2], "odds_low": 100, "odds_high": 100},
            {"selection": [3], "odds_low": 100, "odds_high": 100},
        ], "place", {(1,), (2,), (3,)})
        self.assertEqual(direct, {})
        self.assertEqual(meta["status"], "HOLD_IMPLIED_PROBABILITY_OVER_ONE")

    def test_binary_event_scores_correct_small_oracle(self):
        p = {(1,): 0.7, (2,): 0.3}
        out = score_binary_events(p, {(1,)})
        self.assertAlmostEqual(out["brier_mean_per_ticket"], 0.09)
        self.assertAlmostEqual(out["binary_log_loss_mean_per_ticket"], -math.log(.7))
        self.assertAlmostEqual(out["realized_winning_probability_sum"], .7)


if __name__ == "__main__":
    unittest.main()
