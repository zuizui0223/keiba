"""Source probe is metadata-only, with no user-typed official roster claims."""
import hashlib
import unittest

from scripts.ticket_forward_jra_source_probe import (
    TARGETS, inspect_response, require_official,
)


class JraConnectivityMetadataTests(unittest.TestCase):
    def test_official_sources_only_and_known_nov23_anchors(self):
        self.assertEqual(len(TARGETS), 3)
        for url in TARGETS.values():
            require_official(url)
        for url in (
            "https://evil.example/JRADB/accessD.html",
            "http://www.jra.go.jp/keiba/calendar2026/2026/11/1123.html",
            "https://www.jra.go.jp.evil.example/keiba/calendar",
            "https://u:p@jra.jp/JRADB/accessD.html",
        ):
            with self.assertRaises(ValueError):
                require_official(url)

    def test_minimal_readonly_html_returns_hash_and_no_false_forward_status(self):
        html = b"""
        <html><body>
        <h1>2026 11/23 cards</h1>
        <a href="/JRADB/accessD.html?CNAME=pw01dde0103202603060120261123%2FEC">card</a>
        <a href="https://evil.example/JRADB/accessD.html?CNAME=forbidden">evil</a>
        </body></html>
        """
        url = "https://www.jra.go.jp/keiba/calendar2026/2026/11/1123.html"
        report = inspect_response(
            requested_url=url, response_url=url, content=html, http_status=200,
            recorded_at_utc="2026-11-22T14:00:00+00:00"
        )
        self.assertEqual(report["raw_sha256"], hashlib.sha256(html).hexdigest())
        self.assertTrue(report["raw_has_racedate_20261123"])
        self.assertEqual(report["html_a_jra_card_link_count"], 1)
        self.assertFalse(report["official_runner_count_verified"])
        self.assertFalse(report["source_updated_at_verified"])
        self.assertFalse(report["server_sealed_before_race"])

    def test_rejects_non_jra_redirect_empty_http_error_and_invalid_bytes(self):
        url = TARGETS["jra_program_nov23"]
        common = dict(requested_url=url, recorded_at_utc="2026-11-22T14:00:00+00:00")
        with self.assertRaises(ValueError):
            inspect_response(**common, response_url="https://evil.example", content=b"abc", http_status=200)
        with self.assertRaises(ValueError):
            inspect_response(**common, response_url=url, content=b"", http_status=200)
        with self.assertRaises(ValueError):
            inspect_response(**common, response_url=url, content=b"html", http_status=404)
        with self.assertRaises(ValueError):
            inspect_response(**common, response_url=url, content=b"X"*3_000_001, http_status=200)
        with self.assertRaises(ValueError):
            inspect_response(**common, response_url=url, content=b"\x81", http_status=200)


if __name__ == "__main__":
    unittest.main()
