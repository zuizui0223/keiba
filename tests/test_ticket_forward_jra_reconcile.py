"""Quality gate for JRA 24-card numbered-row metadata vs third-party staging."""
import copy
import json
from pathlib import Path
import unittest

from scripts.ticket_forward_jra_reconcile import reconcile

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/"docs/evidence/ticket-forward-20261123-program-staging.json"
META=ROOT/"docs/evidence/ticket-forward-20261123-jra-card-numbered-rows-20261122.json"


class JraOfficialCardReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage=json.loads(STAGE.read_text())
        cls.metadata=json.loads(META.read_text())

    def test_real_source_hash_metadata_keeps_prospective_0(self):
        report=reconcile(self.stage,self.metadata)
        self.assertEqual(report["official_card_number_sequences_parsed"],24)
        self.assertEqual(report["flat_candidate_count_by_numbered_rows"],23)
        self.assertEqual(report["scheduled_races"],24)
        self.assertTrue(report["first_ten_race_ids_unchanged"])
        self.assertEqual(len(report["official_vs_secondary_count_discrepancies"]),3)
        self.assertEqual(
            [r["race_id"] for r in report["official_vs_secondary_count_discrepancies"]],
            ["2026-11-23-TOKYO-01","2026-11-23-TOKYO-04","2026-11-23-TOKYO-06"],
        )
        self.assertEqual(report["source_actions_run_id"],45030215026)
        self.assertFalse(report["has_server_sealed_whole_day_forecast_universe"])
        self.assertFalse(report["has_verified_current_active_runners_after_scratches"])
        self.assertTrue(report["do_not_promote_to_formal_day_plan"])
        self.assertEqual(report["prospective_predictions"],0)
        self.assertEqual(report["actual_market_price_snapshots"],0)
        chosen=report["first_ten_with_numbered_card_rows"]
        self.assertEqual(len(chosen),10)
        tokyo1=next(r for r in chosen if r["race_id"]=="2026-11-23-TOKYO-01")
        self.assertEqual(tokyo1["official_numbered_rows"],13)
        self.assertEqual(tokyo1["third_party_preliminary_count"],14)

    def test_missing_or_changed_source_is_not_silently_backfilled(self):
        bad=copy.deepcopy(self.metadata)
        bad["races"].pop()
        with self.assertRaisesRegex(ValueError,"incomplete_JRA_card_metadata"):
            reconcile(self.stage,bad)
        bad=copy.deepcopy(self.metadata)
        bad["races"][0]["official_card_url"] = "https://example.com/horse"
        with self.assertRaises(ValueError):
            reconcile(self.stage,bad)
        bad=copy.deepcopy(self.metadata)
        bad["races"][0]["numbered_card_rows"]=17
        with self.assertRaisesRegex(ValueError,"unverified_or_invalid_JRA_numbered_rows"):
            reconcile(self.stage,bad)
        bad=copy.deepcopy(self.metadata)
        bad["races"][0]["raw_page_sha256"]="not a hash"
        with self.assertRaisesRegex(ValueError,"unverified_or_invalid_JRA_numbered_rows"):
            reconcile(self.stage,bad)

    def test_cannot_promote_to_prospective_seal_or_claim_scratch_check(self):
        bad=copy.deepcopy(self.metadata)
        bad["official_day_schedule_server_sealed"]=True
        with self.assertRaisesRegex(ValueError,"claims_unobserved_prospective"):
            reconcile(self.stage,bad)
        bad=copy.deepcopy(self.metadata)
        bad["races"][0]["official_active_runner_count_independently_verified"]=True
        with self.assertRaisesRegex(ValueError,"unverified_or_invalid"):
            reconcile(self.stage,bad)


if __name__=="__main__":
    unittest.main()
