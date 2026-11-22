"""Real program facts and adversarial future-cohort HOLD checks for Nov23."""
import copy
import json
from pathlib import Path
import unittest

from scripts.ticket_forward_program_preflight import (
    HOLD_STATUS, TARGET_DATE, audit_preliminary_program,
)

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "docs/evidence/ticket-forward-20261123-program-staging.json"


class Nov23PublishedProgramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = json.loads(STAGING.read_text(encoding="utf-8"))

    def check_bad(self, mutator, error_message: str):
        other = copy.deepcopy(self.stage)
        mutator(other)
        with self.assertRaisesRegex(ValueError, error_message):
            audit_preliminary_program(other)

    def test_complete_24_race_program_is_only_provisional(self):
        result = audit_preliminary_program(self.stage)
        self.assertEqual(result["status"], HOLD_STATUS)
        self.assertEqual(result["program_full_day_rows"], 24)
        self.assertEqual(result["program_flat_rows"], 23)
        self.assertEqual(result["program_obstacle_rows"], 1)
        self.assertEqual(result["provisional_eligible_by_secondary_counts"], 23)
        self.assertEqual(result["official_entrant_counts_verified"], 0)
        self.assertEqual(result["market_snapshots_frozen"], 0)
        self.assertFalse(result["day_plan_pre_first_race_server_sealed"])
        self.assertEqual(result["future_prospective_scores"], 0)

    def test_first_ten_derived_not_result_chosen(self):
        result = audit_preliminary_program(self.stage)
        chosen = result["provisional_first_ten"]
        self.assertEqual(len(chosen), 10)
        self.assertEqual(chosen[0]["race_id"], "2026-11-23-FUKUSHIMA-01")
        self.assertEqual(chosen[-1]["race_id"], "2026-11-23-FUKUSHIMA-06")
        self.assertEqual(chosen[0]["scheduled_start_jst"], "2026-11-23T09:45:00+09:00")
        self.assertEqual(chosen[0]["nominal_forecast_window_start_jst"],
                         "2026-11-23T09:20:00+09:00")
        self.assertEqual(chosen[0]["nominal_forecast_window_end_jst"],
                         "2026-11-23T09:30:00+09:00")
        self.assertNotIn("2026-11-23-FUKUSHIMA-04",
                         [row["race_id"] for row in chosen])

    def test_missing_or_reordered_races_are_rejected(self):
        self.check_bad(lambda s: s["races"].pop(), "not_all_24_planned_races_present")
        self.check_bad(lambda s: s["races"].reverse(), "staging_rows_not_sorted")
        self.check_bad(lambda s: s["races"][0].update(
            race_id="2026-11-23-TOKYO-01"), "duplicate_or_mismatched_program_race")

    def test_official_card_claim_cannot_be_faked(self):
        self.check_bad(lambda s: s.update(
            official_card_count_confirmed=24), "stage_attempts_to_claim_real_frozen_data")
        self.check_bad(lambda s: s.update(
            day_plan_git_server_attested=True), "stage_attempts_to_claim_real_frozen_data")
        self.check_bad(lambda s: s["races"][0].update(
            official_current_card_runner_count=16), "unverified_official_card_claim")
        self.check_bad(lambda s: s["races"][0].update(
            confirmed_official_card_source_url="https://www.jra.go.jp/JRADB/accessD.html"),
            "unverified_official_card_claim")

    def test_source_clock_surface_or_unnumbered_counts_rejected(self):
        self.check_bad(lambda s: s["source"].update(
            secondary_runner_counts_url="https://example.com"), "source_provenance_not_separated")
        self.check_bad(lambda s: s["races"][0].update(
            scheduled_start_jst="2026-11-23T09:30:00+09:00"),
            "duplicate_or_mismatched_program_race")
        f4 = next(row for row in self.stage["races"]
                  if row["race_id"] == "2026-11-23-FUKUSHIMA-04")
        ix = self.stage["races"].index(f4)
        self.check_bad(lambda s: s["races"][ix].update(
            programmed_surface="芝"), "obstacle_flat_classification_mismatch")
        self.check_bad(lambda s: s["races"][0].update(
            third_party_displayed_runner_count=0), "missing_secondary_entrant_count")


if __name__ == "__main__":
    unittest.main()
