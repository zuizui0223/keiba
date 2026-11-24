"""Source-identity and top-three parser oracles for official JRA results."""
import unittest

from scripts.ticket_forward_result_capture import parse_result_source

RACE_ID = "2026-11-28-TOKYO-11"
OFFICIAL_URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=synthetic"
SOURCE = """# レース結果2026年11月28日（土曜）5回東京7日 11レース

| 着順 | 枠 | 馬 番 | 馬名 |
| --- | --- | --- | --- |
| 1 |  | 9 | テスト甲 |
| 2 |  | 3 | テスト乙 |
| 3 |  | 2 | テスト丙 |
| 4 |  | 1 | テスト丁 |
""".encode("utf-8")


class JraResultCaptureTests(unittest.TestCase):
    def parse(self, **overrides):
        args = {"race_id": RACE_ID, "source_url": OFFICIAL_URL, "source_text": SOURCE}
        args.update(overrides)
        return parse_result_source(**args)

    def test_source_triple_correct_and_has_distinct_ranks(self):
        out = self.parse()
        self.assertEqual(out["top3"], [9, 3, 2])
        self.assertEqual(len(out["source_text_sha256"]), 64)
        self.assertFalse(out["original_page_authenticity_independently_verified"])

    def test_refuses_page_race_or_venue_mismatch(self):
        with self.assertRaisesRegex(ValueError, "identity_mismatch"):
            self.parse(race_id="2026-11-28-KYOTO-11")
        with self.assertRaisesRegex(ValueError, "identity_mismatch"):
            self.parse(race_id="2026-11-28-TOKYO-10")
        with self.assertRaisesRegex(ValueError, "identity_mismatch"):
            self.parse(race_id="2026-11-29-TOKYO-11")

    def test_refuses_duplicate_rank_missing_rank_duplicate_horse(self):
        missing = SOURCE.decode().replace("| 3 |  | 2 | テスト丙 |\n", "").encode()
        with self.assertRaisesRegex(ValueError, "top_three_not_complete"):
            self.parse(source_text=missing)
        duplicate = SOURCE.decode().replace("| 3 |  | 2 | テスト丙 |", "| 2 |  | 2 | テスト丙 |").encode()
        with self.assertRaisesRegex(ValueError, "duplicate_rank"):
            self.parse(source_text=duplicate)
        horse_same = SOURCE.decode().replace("| 3 |  | 2 | テスト丙 |", "| 3 |  | 9 | テスト丙 |").encode()
        with self.assertRaisesRegex(ValueError, "duplicate_horse"):
            self.parse(source_text=horse_same)

    def test_refuses_untrusted_hosts_or_unsupported_source_encoding(self):
        with self.assertRaisesRegex(ValueError, "not_official"):
            self.parse(source_url="https://fake-jra.example/JRADB/accessS.html")
        with self.assertRaisesRegex(ValueError, "not_official"):
            self.parse(source_url="https://www.jra.go.jp/example/summary")
        with self.assertRaisesRegex(ValueError, "non_utf8"):
            self.parse(source_text=b"\xff")
        with self.assertRaises(ValueError):
            self.parse(source_text=b"arbitrary ranking")


if __name__ == "__main__":
    unittest.main()
