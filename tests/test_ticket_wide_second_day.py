"""Four 2026-10-18 JRA-result comparisons with full archived win and wide boards."""
import copy
import json
from pathlib import Path
import unittest

from scripts.ticket_type_models import KINDS, _time
from scripts.ticket_wide_second_day import (
    OFFICIAL_TOP3_PATH, SAVED_SNAPSHOT_PATH, eligible_four_market_only,
    extract_eligible_snapshot, run_second_date, score_one
)


class OtherDayMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(SAVED_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        cls.official = json.loads(OFFICIAL_TOP3_PATH.read_text(encoding="utf-8"))

    def test_four_included_by_quotes_only_and_five_missing_wide_held(self):
        eligible, summary = eligible_four_market_only(self.raw)
        self.assertEqual(summary["total_races"], 9)
        self.assertEqual(summary["included"], 4)
        self.assertEqual(len(summary["excluded"]), 5)
        self.assertEqual(
            {r["race_id"] for r in eligible},
            {"2608040711", "2605040711", "2604040210", "2604040211"}
        )
        self.assertEqual([r["runner_count"] for r in eligible], [17, 13, 18, 10])
        for r in eligible:
            self.assertFalse(r["quote_update_timestamp_verified"])
            self.assertEqual(len(r["wide_quotes"]), r["runner_count"] * (r["runner_count"] - 1) // 2)
            self.assertLess(_time(r["received_end"]), _time(r["start_jst"]))

    def test_official_top3_only_for_later_scoring(self):
        included, _ = eligible_four_market_only(self.raw)
        official = {r["race_id"]: r for r in self.official["official_results"]}
        self.assertEqual(set(official), {r["race_id"] for r in included})
        self.assertEqual(official["2608040711"]["top3"], [8, 1, 13])
        self.assertEqual(official["2605040711"]["top3"], [9, 11, 6])
        self.assertEqual(official["2604040210"]["top3"], [16, 15, 9])
        self.assertEqual(official["2604040211"]["top3"], [3, 1, 5])
        self.assertTrue(all(x["source_type"] == "JRA_official" for x in official.values()))

    def test_shuffled_or_duplicate_wide_board_is_rejected(self):
        chosen = next(r for r in self.raw["races"] if r["race_id"] == "2608040711")
        fewer = copy.deepcopy(chosen)
        fewer["wide"].pop()
        self.assertIsNone(extract_eligible_snapshot(self.raw, fewer))
        bad = copy.deepcopy(chosen)
        bad["wide"][-1]["horses"] = bad["wide"][0]["horses"]
        with self.assertRaises(ValueError):
            extract_eligible_snapshot(self.raw, bad)
        bad = copy.deepcopy(chosen)
        bad["wide"][0]["odds_low"] = 50
        bad["wide"][0]["odds_high"] = 5
        with self.assertRaises(ValueError):
            extract_eligible_snapshot(self.raw, bad)

    def test_claimed_receipt_after_start_must_fail(self):
        invalid = copy.deepcopy(self.raw)
        invalid["observed_window_end_jst"] = "2026-10-18T17:00:00+09:00"
        with self.assertRaises(ValueError):
            eligible_four_market_only(invalid)

    def test_scoring_report_remains_retrospective_and_alpha_zero_identity(self):
        data = run_second_date()
        self.assertEqual(data["status"], "SECOND_DATE_RETROSPECTIVE_NOT_PROSPECTIVE")
        self.assertFalse(data["design_frozen_before_result"])
        self.assertFalse(data["quote_upstream_times_verified"])
        self.assertFalse(data["positive_expected_value_established"])
        self.assertTrue(data["independent_date_after_initial_source"])
        self.assertEqual(len(data["races"]), 4)
        self.assertEqual(set(data["primary_summary"]), set(KINDS))
        self.assertEqual(len(data["source_sha256"]), 2)
        for r in data["races"]:
            self.assertEqual(len(r["analyses"]), 12)
            for market in ("low", "geometric", "high"):
                for kind in KINDS:
                    delta = r["analyses"][f"{market}:alpha=0"]["score"][kind]["brier_after_minus_PL"]
                    self.assertAlmostEqual(delta, 0.0, places=11)
        self.assertTrue(all(len(v) == 64 for v in data["source_sha256"].values()))


if __name__ == "__main__":
    unittest.main()
