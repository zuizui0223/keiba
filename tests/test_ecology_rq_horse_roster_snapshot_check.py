"""Fully fake source-SHA replay and permanent-archive fixture validation."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import ecology_rq_horse_roster_snapshot_check as mod


def artificial_frozen_manifest():
    records={}
    for i,date in enumerate(mod.DAYS):
        n=45 if i<11 else 48
        raw_roster_sha=format(i+1001,"064x")
        combined=hashlib.sha256(
            f"{987654+i}:{raw_roster_sha}\n".encode("ascii")
        ).hexdigest()
        records[date]={
            "verified_positive_first_GPS_HORSES_ID_matches":n,
            "meeting_XML_SHA256":format(i+101,"064x"),
            "race_XML_SHA256":format(i+201,"064x"),
            "gps_CSV_SHA256":format(i+301,"064x"),
            "combined_original_GetHorsesForRace_roster_SHA256":combined,
            "number_of_original_HORSES_roster_responses_hashed":1,
        }
    return {
        "schema":mod.SCHEMA,
        "source_snapshot_run_id":38501390778,
        "date_count":12,
        "source_positive_ID_GPS_total":543,
        "per_date":records,
        "raw_private_original_horse_name":"DO NOT EMIT SOURCE NAME",
    }


def artificial_archived(baseline):
    manifest={}
    for day,row in baseline["per_date"].items():
        manifest[day]={
            "status":"SOURCE_ORIGINAL_ID_GPS_AND_DECLARED_RIDER_AUDITED",
            "first_GPS_matched_original_source_rows":
                row["verified_positive_first_GPS_HORSES_ID_matches"],
            "original_source_SHA256":{
                "meeting_xml_sha256":row["meeting_XML_SHA256"],
                "race_xml_sha256":row["race_XML_SHA256"],
                "gps_csv_sha256":row["gps_CSV_SHA256"],
            },
            "original_HORSES_roster_XML_sha256_aggregate":
                row["combined_original_GetHorsesForRace_roster_SHA256"],
            "official_original_HORSES_roster_races_hashed":1,
        }
    return {"source_manifest_original_SHA256_no_individuals":manifest}


def artificial_current(baseline,scope="affected_five_plus_control"):
    dates=(*mod.AFFECTED_DATES,mod.STABLE_CONTROL_DATE) if (
        scope=="affected_five_plus_control") else mod.DAYS
    return {day:{
        **row,"status":"SOURCE_DATE_READ_AND_JOIN_AUDITED",
    } for day,row in baseline["per_date"].items() if day in dates}


class SourceRecheckTests(unittest.TestCase):
    def test_permanent_baseline_uses_exact_twelve_anonymous_original_dates(self):
        base=artificial_frozen_manifest()
        self.assertEqual(len(mod.validate_baseline(base)),12)
        self.assertEqual(base["source_positive_ID_GPS_total"],543)
        self.assertEqual(len(mod.AFFECTED_DATES),5)
        self.assertNotIn(mod.STABLE_CONTROL_DATE,mod.AFFECTED_DATES)
        invalid=copy.deepcopy(base)
        invalid["per_date"][mod.DAYS[0]]["gps_CSV_SHA256"]="fake"
        with self.assertRaisesRegex(ValueError,"HOLD_MALFORMED_ANONYMOUS_SOURCE_DIGEST"):
            mod.validate_baseline(invalid)

    def test_frozen_fixture_compares_against_actual_artifact_shaped_json(self):
        base=artificial_frozen_manifest()
        r=mod.check_original_archive(base,artificial_archived(base))
        self.assertEqual(r["status"],
          "VERIFIED_PERMANENT_FINGERPRINT_FIXTURE_AGAINST_ORIGINAL_ARCHIVED_JSON")
        self.assertEqual(r["source_components_checked_per_day"],4)
        modified=artificial_archived(base)
        modified["source_manifest_original_SHA256_no_individuals"][mod.DAYS[1]][
            "original_HORSES_roster_XML_sha256_aggregate"]="f"*64
        with self.assertRaisesRegex(ValueError,"HOLD_PERMANENT_HASH_FIXTURE_DIFFERS"):
            mod.check_original_archive(base,modified)

    def test_same_source_roster_gps_and_join_counts_are_reported_as_snapshot_only(self):
        base=artificial_frozen_manifest()
        d=mod.compare_live_to_baseline(base,artificial_current(base))
        self.assertEqual(
            d["status"],
            "SOURCE_SNAPSHOT_REPLAY_MATCHES_20261014_FOUR_ORIGINAL_COMPONENTS",
        )
        self.assertEqual(
            d["source_component_status_counts"][
                "dates_fully_matching_frozen_source_and_count"],6)
        self.assertTrue(d["does_not_reconstruct_earlier_original_548_row_roster"])
        self.assertTrue(d["not_H1_H2_heritability_personality_competition_evidence"])
        self.assertNotIn("DO NOT EMIT SOURCE NAME",json.dumps(d))

    def test_source_roster_byte_change_is_not_called_a_biological_effect(self):
        base=artificial_frozen_manifest()
        current=artificial_current(base)
        current[mod.DAYS[0]][
            "combined_original_GetHorsesForRace_roster_SHA256"]="e"*64
        d=mod.compare_live_to_baseline(base,current)
        self.assertEqual(d["status"],
                         "HOLD_RQ_SOURCE_ROSTER_OR_OTHER_ORIGINAL_RESPONSE_DRIFTED")
        entry=d["per_date_anonymous_comparison"][mod.DAYS[0]]
        self.assertFalse(
            entry["source_bytes_match_exact_20261014_by_component"][
                "combined_original_GetHorsesForRace_roster_SHA256"])
        self.assertTrue(d["same_bytes_do_not_verify_actual_starter_status_or_biological_response"])

    def test_source_bytes_same_but_horse_join_rule_changed_is_hold(self):
        base=artificial_frozen_manifest()
        current=artificial_current(base)
        current[mod.DAYS[0]][
            "verified_positive_first_GPS_HORSES_ID_matches"]-=1
        d=mod.compare_live_to_baseline(base,current)
        self.assertEqual(d["status"],
                         "HOLD_RQ_ORIGINAL_BYTES_STABLE_BUT_MATCHING_RULE_CHANGED")
        self.assertEqual(d["source_component_status_counts"][
            "dates_with_same_bytes_but_join_count_changed"],1)

    def test_source_unavailable_is_a_hold_not_zero_record(self):
        base=artificial_frozen_manifest()
        current=artificial_current(base)
        current[mod.DAYS[0]]={
            "status":"HOLD_UNRECONCILED_OFFICIAL_SOURCE_DATE",
            "error_category":"ValueError",
        }
        out=mod.compare_live_to_baseline(base,current)
        self.assertEqual(out["status"],"HOLD_SOME_ORIGINAL_SOURCE_DATES_NOT_RETRIEVED")
        self.assertTrue(out["per_date_anonymous_comparison"][mod.DAYS[0]][
            "unretrieved_is_not_zero_horses"])

    def test_only_locked_dates_permitted_and_missing_live_status_refused(self):
        base=artificial_frozen_manifest()
        with self.assertRaisesRegex(ValueError,"HOLD_REPLAY_SCOPE"):
            mod.compare_live_to_baseline(base,{},scope="choose_winners")
        with self.assertRaisesRegex(ValueError,"HOLD_UNEXPECTED_LIVE_SOURCE_DATE_SET"):
            mod.compare_live_to_baseline(base,{})

    def test_synthetic_live_fetch_does_not_export_ids_names_from_mocked_source(self):
        baseline=artificial_frozen_manifest()
        digest_by_date={}
        def fake_soap(op,params):
            assert op=="GetHorsesForRace"
            day=digest_by_date["day"]
            i=mod.DAYS.index(day)
            assert params["raceId"]==str(987654+i)
            return None, "https://www.racingqueensland.com.au/fake",format(i+1001,"064x")
        def fake_audit(day,*,soap,gps,venue,locked_config,race_selection):
            digest_by_date["day"]=day
            i=mod.DAYS.index(day)
            soap("GetHorsesForRace",{"raceId":str(987654+i)})
            b=baseline["per_date"][day]
            return {
                "source_hashes":{
                    "meeting_xml_sha256":b["meeting_XML_SHA256"],
                    "race_xml_sha256":b["race_XML_SHA256"],
                    "gps_csv_sha256":b["gps_CSV_SHA256"],
                }
            },[{"horse_id":"FAKE-PRIVATE-NUMERIC-ID"}]*b[
                "verified_positive_first_GPS_HORSES_ID_matches"]
        with patch.object(mod,"audit_one_day",fake_audit):
            live=mod.fetch_live(soap=fake_soap,gps=lambda _:None)
        d=mod.compare_live_to_baseline(baseline,live)
        self.assertEqual(d["status"],
            "SOURCE_SNAPSHOT_REPLAY_MATCHES_20261014_FOUR_ORIGINAL_COMPONENTS")
        self.assertNotIn("FAKE-PRIVATE-NUMERIC-ID",json.dumps(d))


if __name__=="__main__":
    unittest.main()
