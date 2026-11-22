"""Recompute all provisional first-ten Nov23 selections against 24 official-card metadata rows.

This tests a result-blind *intent* that is allowed to be published the night
before racing. It MUST NOT be interpreted as official active-runner verification
or a formal prospective day-universe server seal.
"""
import copy
from datetime import datetime
import json
from pathlib import Path
import unittest

from scripts.ticket_forward_freeze import git_blob_sha1
from scripts.ticket_forward_jra_reconcile import reconcile

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "docs/evidence/ticket-forward-20261123-program-staging.json"
CARDS = ROOT / "docs/evidence/ticket-forward-20261123-jra-card-numbered-rows-20261122.json"
MANIFEST = ROOT / "docs/betting/ticket-forward-v1-manifest.json"
INTENT = ROOT / "docs/evidence/ticket-forward-20261123-prestart-intent.json"
RECEIPT = ROOT / "docs/evidence/ticket-forward-20261123-intent-receipt.json"


def check_intent(intent: dict, stage: dict, metadata: dict) -> dict:
    if (intent.get("status") != "PRE_FIRST_RACE_INTENT_NOT_FORMAL_SCHEDULE_OR_FORECAST"
            or intent.get("protocol") != "ticket-forward-v1"
            or intent.get("race_date") != "2026-11-23"
            or intent.get("formal_github_day_plan_receipt") is not False
            or intent.get("per_race_market_snapshots_frozen") != 0
            or intent.get("actual_start_list_verified_for_scratches") is not False
            or intent.get("true_prospective_scores") != 0):
        raise ValueError("intent_falsely_promoted_to_prospective")
    if (intent.get("manifest_git_blob_sha1") != git_blob_sha1(MANIFEST.read_bytes())
            or intent.get("source_git_blobs") != {
                "program_stage": git_blob_sha1(STAGE.read_bytes()),
                "official_numbered_rows_metadata": git_blob_sha1(CARDS.read_bytes()),
            }):
        raise ValueError("intent_does_not_match_pinned_inputs")
    measured = reconcile(stage, metadata)
    if (measured["status"] != "READ_ONLY_OFFICIAL_NUMBERED_ROWS_RECONCILED_NOT_FORMAL_FORWARD"
            or not measured["first_ten_race_ids_unchanged"]
            or measured["official_card_number_sequences_parsed"] != 24
            or intent.get("whole_day_card_pages") != 24
            or intent.get("eligible_flat_races_with_official_numbered_rows") != 23
            or intent.get("official_card_evidence_actions_run_id") !=
            metadata["observed_git_actions_run_id"]):
        raise ValueError("intent_source_coverage_invalid")
    expected = []
    raw = {r["race_id"]: r for r in metadata["races"]}
    for entry in measured["first_ten_with_numbered_card_rows"]:
        src = raw[entry["race_id"]]
        item = {
            "race_id": entry["race_id"],
            "venue": "福島" if "FUKUSHIMA" in entry["race_id"] else "東京",
            "race_number": int(entry["race_id"].split("-")[-1]),
            "scheduled_start_jst": entry["scheduled_start_jst"],
            "official_numbered_rows": entry["official_numbered_rows"],
            "secondary_count": entry["third_party_preliminary_count"],
            "official_card_url": src["official_card_url"],
            "official_card_sha256": src["raw_page_sha256"],
        }
        expected.append(item)
    if intent.get("selected_first_ten") != expected:
        raise ValueError("intent_first_ten_not_source_reproduced")
    return {
        "status": "INTENT_REPRODUCED_NO_FORMAL_FORWARD_PREDICTION",
        "selected_count": len(expected),
        "flat_eligible_numbered_races": 23,
        "official_card_numbered_pages": 24,
        "official_active_scratch_status_verified": False,
        "official_day_plan_server_sealed": False,
    }


class PreStartIntentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = json.loads(STAGE.read_text(encoding="utf-8"))
        cls.meta = json.loads(CARDS.read_text(encoding="utf-8"))
        cls.intent = json.loads(INTENT.read_text(encoding="utf-8"))
        cls.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_result_blind_ten_candidate_intent_matches_official_card_numbered_rows(self):
        r = check_intent(self.intent, self.stage, self.meta)
        self.assertEqual(r["selected_count"], 10)
        self.assertEqual(r["official_card_numbered_pages"], 24)
        self.assertFalse(r["official_active_scratch_status_verified"])

    def test_github_server_prestart_witness_is_only_candidate_intent(self):
        r = self.receipt
        self.assertEqual(r["status"], "GITHUB_SERVER_RECORDED_PRESTART_CANDIDATE_INTENT_NOT_FORMAL_DAY_SEAL")
        self.assertEqual(r["candidate_intent_count"], 10)
        self.assertEqual(r["candidate_intent_git_blob_sha1"], git_blob_sha1(INTENT.read_bytes()))
        self.assertEqual(r["candidate_intent_path"], str(INTENT.relative_to(ROOT)))
        self.assertEqual(r["github_actions_run_id"], 45031414549)
        self.assertEqual(r["source_commit_sha"], "9fb8e2a617d89a6b5c11869fd4c51d5f5013f7a5")
        created = datetime.fromisoformat(r["github_server_created_at_utc"].replace("Z", "+00:00"))
        first = datetime.fromisoformat(r["time_boundary"])
        self.assertLess(created, first)
        self.assertTrue(r["zero_forecast_outputs"])
        self.assertFalse(r["formal_full_day_source_capture_verified"])
        self.assertFalse(r["complete_market_odds_frozen"])
        self.assertEqual(r["actual_prospective_scored_races"], 0)

    def test_tamper_any_early_race_number_held(self):
        altered = copy.deepcopy(self.intent)
        altered["selected_first_ten"][1]["official_numbered_rows"] = 14
        with self.assertRaisesRegex(ValueError, "first_ten_not_source_reproduced"):
            check_intent(altered, self.stage, self.meta)

    def test_intent_cannot_promote_itself_or_claim_market_quotes(self):
        for key, value in [
            ("formal_github_day_plan_receipt", True),
            ("per_race_market_snapshots_frozen", 1),
            ("true_prospective_scores", 1),
        ]:
            altered = copy.deepcopy(self.intent)
            altered[key] = value
            with self.assertRaisesRegex(ValueError, "intent_falsely_promoted"):
                check_intent(altered, self.stage, self.meta)

    def test_manifest_or_source_hash_drift_rejected(self):
        altered = copy.deepcopy(self.intent)
        altered["manifest_git_blob_sha1"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "intent_does_not_match_pinned_inputs"):
            check_intent(altered, self.stage, self.meta)


if __name__ == "__main__":
    unittest.main()
