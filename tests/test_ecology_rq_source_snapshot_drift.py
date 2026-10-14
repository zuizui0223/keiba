"""Wholly fabricated source audit snapshots; no actual original identities."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_source_snapshot_drift import (
    DAYS,KEYS,audit
)


def fictional_archives():
    early={"date_scoped_source_manifest":{}, "support":{}}
    late={
        "source_manifest_original_SHA256_no_individuals":{},
        "source_snapshot_candidate_count_audit":{},
    }
    for i,day in enumerate(DAYS):
        prior=40+i
        recent=prior-int(i in {0,2,4,9,11})
        h={
            "meeting_xml_sha256":format(i+1,"064x"),
            "race_xml_sha256":format(i+101,"064x"),
            "gps_csv_sha256":format(i+1001,"064x"),
        }
        early["date_scoped_source_manifest"][day]={
            "status":"SOURCE_DATE_READ_AND_ID_GPS_MATCHED",
            "candidate_ID_linked_positive_first_GPS_rows":prior,
            "source_hashes":dict(h),
            # Malicious unrelated content should NEVER be materialized.
            "raw_horse_name":"PRIVATE SECRET NAME",
        }
        late["source_manifest_original_SHA256_no_individuals"][day]={
            "status":"SOURCE_ORIGINAL_ID_GPS_AND_DECLARED_RIDER_AUDITED",
            "first_GPS_matched_original_source_rows":recent,
            "original_source_SHA256":dict(h),
            "original_HORSES_roster_XML_sha256_aggregate":
                format(i+10001,"064x"),
            "official_original_HORSES_roster_races_hashed":8,
            "user_specific_gambling_hint":"DO NOT EMIT",
        }
    early["support"]["positive_first_section_id_linked_candidate_rows"]=sum(
        x["candidate_ID_linked_positive_first_GPS_rows"]
        for x in early["date_scoped_source_manifest"].values()
    )
    late["source_snapshot_candidate_count_audit"][
        "now_original_Cannon_candidate_rows"]=sum(
        x["first_GPS_matched_original_source_rows"]
        for x in late["source_manifest_original_SHA256_no_individuals"].values()
    )
    return early,late


class SourceSnapshotDriftTests(unittest.TestCase):
    def test_five_changed_original_join_counts_do_not_imply_GPS_change(self):
        old,new=fictional_archives()
        report=audit(old,new)
        self.assertEqual(report["source_join_candidate_change_later_minus_earlier"],-5)
        self.assertEqual(
            report["source_dates_with_changed_candidate_count"],
            [DAYS[i] for i in (0,2,4,9,11)]
        )
        self.assertEqual(report["status"],
            "HOLD_SAME_ORIGINAL_3_SOURCES_DIFFERENT_JOIN_COUNTS_ROSTER_OR_CODE_UNRESOLVED")
        support=report["source_component_equality_counts"]
        self.assertEqual(support["source_meetings_checked"],12)
        self.assertEqual(support["meeting_XML_unchanged"],12)
        self.assertEqual(support["races_XML_unchanged"],12)
        self.assertEqual(support["GPS_CSV_unchanged"],12)
        self.assertEqual(support["dates_with_original_source_byte_change"],0)
        self.assertEqual(support["dates_with_join_count_change"],5)
        self.assertFalse(
            report["GetHorsesForRace_comparable_earlier_response_hashes_available"])
        self.assertTrue(
            report["different_source_parser_code_versions_cannot_be_ruled_out"])
        self.assertFalse(report["any_ecological_H1_or_H2_claim_permitted_from_drift"])
        content=json.dumps(report)
        self.assertNotIn("PRIVATE SECRET NAME",content)
        self.assertNotIn("DO NOT EMIT",content)

    def test_first_party_GPS_bytes_changed_must_be_separate_hold(self):
        old,new=fictional_archives()
        new["source_manifest_original_SHA256_no_individuals"][DAYS[0]][
            "original_source_SHA256"]["gps_csv_sha256"]="f"*64
        v=audit(old,new)
        self.assertEqual(v["status"],
                         "HOLD_ORIGINAL_MEETING_RACE_OR_GPS_SOURCE_BYTES_CHANGED")
        self.assertEqual(
            v["source_component_equality_counts"][
                "dates_with_original_source_byte_change"],1)
        self.assertEqual(v["source_component_equality_counts"]["GPS_CSV_unchanged"],11)

    def test_equal_counts_and_equal_three_documents_do_not_prove_roster_stable(self):
        old,new=fictional_archives()
        for d in DAYS:
            new["source_manifest_original_SHA256_no_individuals"][d][
                "first_GPS_matched_original_source_rows"] = (
                old["date_scoped_source_manifest"][d][
                    "candidate_ID_linked_positive_first_GPS_rows"]
            )
        new["source_snapshot_candidate_count_audit"][
            "now_original_Cannon_candidate_rows"]=old["support"][
                "positive_first_section_id_linked_candidate_rows"]
        v=audit(old,new)
        self.assertEqual(
            v["status"],
            "SOURCE_THREE_COMPONENTS_AND_JOIN_COUNTS_STABLE_ROSTER_PREVIOUSLY_UNHASHED")
        self.assertFalse(v["source_join_count_stability_proves_same_horse_identity_membership"])

    def test_fake_missing_source_date_blocks_misleading_difference(self):
        old,new=fictional_archives()
        del old["date_scoped_source_manifest"][DAYS[0]]
        with self.assertRaisesRegex(ValueError,"HOLD_SOURCE_CALENDARS"):
            audit(old,new)

    def test_forged_digest_never_accepted_as_original_provenance(self):
        old,new=fictional_archives()
        new["source_manifest_original_SHA256_no_individuals"][DAYS[0]][
            "original_HORSES_roster_XML_sha256_aggregate"]="unverified"
        with self.assertRaisesRegex(ValueError,"HOLD_INVALID_SOURCE_SHA256"):
            audit(old,new)

    def test_inconsistent_total_counts_cannot_support_audit(self):
        old,new=fictional_archives()
        old["support"]["positive_first_section_id_linked_candidate_rows"]+=7
        with self.assertRaisesRegex(ValueError,"HOLD_ARCHIVED_TOTAL"):
            audit(old,new)

    def test_do_not_guess_cause_when_new_roster_hash_exists_only_on_new_run(self):
        old,new=fictional_archives()
        v=audit(old,new)
        entry=v["per_original_meeting_day"][DAYS[0]]
        self.assertIsNone(entry["earlier_horse_roster_SHA256"])
        self.assertFalse(
            entry["is_horse_roster_byte_change_identifiable_from_both_snapshots"])
        self.assertEqual(len(entry["later_horse_roster_combined_SHA256"]),64)
        self.assertTrue(v["original_horse_nomination_roster_changes_cannot_be_ruled_out"])


if __name__=="__main__":
    unittest.main()
