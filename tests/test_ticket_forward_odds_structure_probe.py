"""Strict non-actionable odds-source readiness probes; do not certify a real market."""
import hashlib
import unittest

from scripts.ticket_forward_odds_structure_probe import TARGETS, inspect_html, strict_target_url


class TicketForwardOddsReadinessTests(unittest.TestCase):
    def test_fukushima_win_table_with_explicit_update_is_only_metadata(self):
        source = """<html><body><h1>2026年11月23日 福島1R 中間オッズ</h1>
        <table><tr><th>枠番</th><th>馬番</th><th>馬名</th><th>単勝</th></tr>
        <tr><td>1</td><td>1</td><td>馬A</td><td>6.1</td></tr>
        <tr><td>1</td><td>2</td><td>馬B</td><td>104.2</td></tr></table>
        <p>2026/11/23 05:38 更新</p></body></html>""".encode("utf-8")
        summary=inspect_html(TARGETS["win_place"],source,"2026-11-22T22:29:00+00:00")
        self.assertEqual(summary["sha256"],hashlib.sha256(source).hexdigest())
        self.assertEqual(summary["num_html_tables"],1)
        self.assertEqual(summary["upstream_updated_at_jst_detected"],["2026-11-23T05:38:00+09:00"])
        self.assertEqual(summary["tables"][0]["rows"],3)
        self.assertTrue(summary["race_date_evidence_detected"])
        self.assertFalse(summary["win_market_verified_complete"])
        self.assertFalse(summary["wide_market_verified_complete"])
        self.assertEqual(summary["prospective_prediction_count"],0)

    def test_update_format_and_source_validation_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"unsupported_odds_page"):
            strict_target_url("https://sports.yahoo.co.jp/keiba/race/odds/tfw/2603030602?ninki=0")
        with self.assertRaisesRegex(ValueError,"unsupported_odds_page"):
            strict_target_url("http://sports.yahoo.co.jp/keiba/race/odds/tfw/2603030601?ninki=0")
        with self.assertRaisesRegex(ValueError,"invalid_odds_page_bytes"):
            inspect_html(TARGETS["wide"],b"","2026-11-22T22:30:00+00:00")
        with self.assertRaisesRegex(ValueError,"unrecognized_odds_page_encoding"):
            inspect_html(TARGETS["wide"],b"\xff","2026-11-22T22:30:00+00:00")

    def test_no_synthetic_prices_become_forward_criteria(self):
        text=b"<html><h1>Tomorrow race</h1><table><tr><th>1</th></tr><tr><td>3.4</td></tr></table></html>"
        output=inspect_html(TARGETS["wide"],text,"2026-11-22T22:30:00+00:00")
        self.assertEqual(output["upstream_updated_at_jst_detected"],[])
        self.assertFalse(output["race_date_evidence_detected"])
        self.assertFalse(output["market_as_of_within_prepost_window"])
        self.assertFalse(output["wide_market_verified_complete"])


if __name__=="__main__":
    unittest.main()
