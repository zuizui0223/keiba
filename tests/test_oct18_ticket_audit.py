#!/usr/bin/env python3
"""Guardrail and arithmetic tests for the non-formal October 18 ticket audit."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.audit_20261018_tickets import audit, git_blob_sha, money, validate_snapshot
from scripts.v31_candidate_channels import market_channel

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/2026-10-18/ticket-odds-snapshot.json"
PICKS = ROOT / "data/2026-10-18/ticket-selections-and-form.json"
OUTPUT = ROOT / "reports/2026-10-18/ticket-audit.json"


class Oct18TicketAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_odds = SNAPSHOT.read_bytes()
        cls.raw_picks = PICKS.read_bytes()
        cls.odds = json.loads(cls.raw_odds)
        cls.picks = json.loads(cls.raw_picks)
        cls.report = audit(
            cls.odds, cls.picks, git_blob_sha(cls.raw_odds), git_blob_sha(cls.raw_picks)
        )

    def test_capture_precedes_all_races(self):
        races = validate_snapshot(self.odds)
        self.assertEqual(len(races), 9)
        self.assertTrue(all(len(r["horses"]) == r["runner_count"] for r in races.values()))

    def test_original_market_m_is_used_with_tie_expansion(self):
        byrace = {(r["venue"], r["race"]): r for r in self.odds["races"]}
        for row in self.report["races"]:
            got = market_channel(byrace[(row["venue"], row["race"])]["horses"])
            self.assertEqual(sorted(got), row["market_M"])
        kyoto_12 = next(r for r in self.report["races"] if r["venue"] == "京都" and r["race"] == 12)
        tokyo_12 = next(r for r in self.report["races"] if r["venue"] == "東京" and r["race"] == 12)
        self.assertEqual(kyoto_12["market_M"], [5, 8, 11, 12])
        self.assertEqual(tokyo_12["market_M"], [5, 9, 13, 14, 16])

    def test_fixed_ticket_count_and_budget(self):
        self.assertEqual(self.report["summary"]["ticket_count"], 12)
        self.assertEqual(self.report["summary"]["budget_yen"], 2000)
        self.assertEqual(self.report["summary"]["full_M_ticket_count"], 4)
        self.assertEqual(self.report["summary"]["not_full_M_ticket_count"], 8)
        self.assertEqual(sum(t["stake_yen"] for t in self.report["tickets"]), 2000)
        self.assertEqual(self.report["summary"]["total_loss_if_nothing_hits_yen"], -2000)

    def test_sample_quotes_and_portfolio_net(self):
        by_id = {t["id"]: t for t in self.report["tickets"]}
        k8 = by_id["K08-P08"]
        self.assertEqual((k8["odds_low"], k8["odds_high"]), (2.3, 3.4))
        self.assertEqual((k8["lower_payout_yen"], k8["upper_illustrative_payout_yen"]), (690, 1020))
        self.assertEqual(k8["portfolio_net_yen_if_only_this_ticket_hits_at_low_odds"], -1310)
        self.assertAlmostEqual(k8["break_even_hit_rate_pct_at_low_odds"], 43.5)
        k11 = by_id["K11-W0814"]
        self.assertEqual((k11["odds_low"], k11["odds_high"]), (7.8, 8.6))
        self.assertEqual(k11["lower_payout_yen"], 780)
        self.assertFalse(k11["in_M_all_horses"])
        self.assertEqual(money(3.3, 200), 660)

    def test_kyoto11_three_wides_cannot_all_hit(self):
        kyoto = next(r for r in self.report["races"] if r["venue"] == "京都" and r["race"] == 11)
        self.assertEqual(kyoto["top3_sets_enumerated"], 680)
        self.assertEqual(kyoto["max_simultaneous_tickets_hit"], 2)

    def test_no_false_calibration_or_holdout_claim(self):
        self.assertEqual(self.report["model_channels_calculated"], ["M_only_v31_market_channel"])
        self.assertIn("v3.1_union", self.report["not_calculated"])
        self.assertFalse(self.report["quote_age_from_upstream_known"])
        self.assertFalse(self.report["purchase_executed"])

    def test_no_future_or_postrace_capture(self):
        x = copy.deepcopy(self.odds)
        x["races"][0]["scheduled_post_jst"] = "2026-10-18T12:32:00+09:00"
        with self.assertRaisesRegex(ValueError, "not_eligible"):
            audit(x, self.picks)

    def test_unknown_ticket_quote_rejected(self):
        x = copy.deepcopy(self.odds)
        kyoto11 = next(r for r in x["races"] if r["venue"] == "京都" and r["race"] == 11)
        kyoto11["wide"] = [q for q in kyoto11["wide"] if q["horses"] != [8, 14]]
        with self.assertRaisesRegex(ValueError, "partial_wide_book"):
            audit(x, self.picks)

    def test_budget_mutation_rejected(self):
        x = copy.deepcopy(self.picks)
        x["tickets"][0]["stake_yen"] = 200
        with self.assertRaisesRegex(ValueError, "portfolio_conservation_failed"):
            audit(self.odds, x)

    def test_checked_in_json_matches_reproducible_math(self):
        self.assertEqual(json.loads(OUTPUT.read_text(encoding="utf-8")), self.report)


if __name__ == "__main__":
    unittest.main()
