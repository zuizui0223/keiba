"""Fictitious SOAP fixture for the RQ single-race identity feasibility probe."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ecology_rq_single_race_id_probe import (
    identified_meeting, identified_race, horse_candidates,
    candidate_gps_join, parse_xml, request_xml, run_single_day,
)


MEETINGS = b"""<?xml version="1.0"?>
<Meetings>
 <Meeting Id="130893">
  <MeetingDate>2026-10-11</MeetingDate>
  <TrackName>Ladbrokes Cannon Park</TrackName>
  <IsBarrierTrial>false</IsBarrierTrial>
 </Meeting>
 <Meeting Id="134252">
  <MeetingDate>2026-10-11</MeetingDate>
  <TrackName>Ladbrokes Cannon Park Night</TrackName>
  <IsBarrierTrial>true</IsBarrierTrial>
 </Meeting>
</Meetings>"""
RACES = b"""<?xml version="1.0"?>
<Races><Race Id="123451"><RaceNumber>1</RaceNumber>
 <RaceName>Fictional race 1</RaceName></Race>
 <Race Id="123452"><RaceNumber>2</RaceNumber></Race>
</Races>"""
HORSES = b"""<?xml version="1.0"?>
<Horses>
 <Horse Id="9001"><HorseName>Alpha Horse</HorseName></Horse>
 <Horse Id="9002"><Name>Beta Horse</Name></Horse>
</Horses>"""
GPS = b"""Date,RaceNumber,11/10/2026 12:00:00 AM;Ladbrokes Cannon Park QLD - Professional;Fictional Race 1;00:00:57.263;FAKE_TRACK
11/10/2026,1,Alpha Horse;7;150;18.30;00:00:10.33;350;18.20;00:00:10.88
11/10/2026,1,Beta Horse;2;150;0;00:00:00.000;350;0;00:00:00.000
"""


def stub_call(operation: str, params: dict[str,str]):
    expected = {
        "GetMeetingsForDate": ({"meetingDate":"2026-10-11"}, MEETINGS),
        "GetRacesForMeeting": ({"meetingId":"130893"}, RACES),
        "GetHorsesForRace": ({"raceId":"123451"}, HORSES),
    }
    if operation not in expected or params != expected[operation][0]:
        raise AssertionError(f"Unexpected official request {operation} with {params}")
    return parse_xml(expected[operation][1]), "https://www.racingqueensland.com.au/fictitious", "a"*64


class SingleRaceIdentityProbeTests(unittest.TestCase):
    def test_meeting_race_id_and_horse_name_mapping_stays_anonymous(self):
        report = run_single_day("2026-10-11", gps_raw=GPS, request_fn=stub_call)
        self.assertEqual(report["status"], "HOLD_RQ_OFFICIAL_ID_CROSSWALK_NOT_COMPLETE")
        self.assertTrue(report["api"]["meeting"]["meeting_id_found_and_validated"])
        self.assertTrue(report["api"]["race"]["race_id_found_and_validated"])
        self.assertEqual(report["api"]["horses"]["schema"]["records_with_numeric_Id_and_named_value"],2)
        counts = report["crosswalk"]["counts"]
        self.assertEqual(counts["unique_syntactic_official_name_matches"],2)
        self.assertEqual(counts["matched_all_zero_gps"],1)
        self.assertEqual(counts["matched_positive_gps"],1)
        self.assertEqual(counts["match_official_start_unknown"],2)
        one = report["crosswalk"]["one_race_exact_name_coverage"]
        self.assertEqual(one["official_horse_id_records"],2)
        self.assertEqual(one["gps_horse_rows_in_selected_race"],2)
        self.assertEqual(one["provisional_name_matches_excluding_same_day_ambiguity"],2)
        self.assertEqual(one["provisional_matched_with_positive_GPS"],1)
        self.assertEqual(one["provisional_matched_with_zero_GPS"],1)
        self.assertEqual(one["official_names_not_in_selected_GPS"],0)
        self.assertFalse(one["verified_individual_stable_across_different_dates"])
        import json
        output = json.dumps(report)
        self.assertNotIn("Alpha Horse", output)
        self.assertNotIn("Beta Horse", output)
        self.assertNotIn("9001", output)
        self.assertFalse(report["H1_real_horse_effect_supported"])
        self.assertFalse(report["H2_real_horse_effect_supported"])

    def test_race_number_unique_and_venue_does_not_select_trial(self):
        mid, shape = identified_meeting(parse_xml(MEETINGS), "2026-10-11", "Ladbrokes Cannon Park")
        self.assertEqual(mid, "130893")
        rid, shape = identified_race(parse_xml(RACES),1)
        self.assertEqual(rid,"123451")
        self.assertEqual(shape["rows"],2)
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EXACTLY_ONE_OFFICIAL_RACE"):
            identified_race(parse_xml(RACES),8)

    def test_one_race_and_one_horse_detail_schema_have_no_identity_values(self):
        race_detail = b"<RaceDetails><Race Id='123451'><Result>EXAMPLE-SECRET</Result><FinishTime>01:00.00</FinishTime></Race></RaceDetails>"
        horse_detail = b"<HorseDetails><Horse Id='9001'><Name>Alpha Horse</Name><HorseID>9001</HorseID><Status>UNKNOWN</Status></Horse></HorseDetails>"
        def stub(op, params):
            if op == "GetRaceDetails":
                self.assertEqual(params,{"raceId":"123451"})
                return parse_xml(race_detail), "https://www.racingqueensland.com.au/stub", "c"*64
            if op == "GetHorseDetailsInRace":
                self.assertEqual(params,{"raceId":"123451","horseId":"9001"})
                return parse_xml(horse_detail), "https://www.racingqueensland.com.au/stub", "d"*64
            return stub_call(op,params)
        r=run_single_day("2026-10-11",gps_raw=GPS,request_fn=stub,
                         inspect_details=True)
        self.assertEqual(set(r["detail_schema_audit"]),{
            "race_result_structure","one_horse_detail_structure"
        })
        import json
        summary=json.dumps(r)
        self.assertIn("FinishTime",summary)
        self.assertIn("HorseID",summary)
        self.assertNotIn("EXAMPLE-SECRET",summary)
        self.assertNotIn("Alpha Horse",summary)
        self.assertNotIn("9001",summary)
        self.assertNotIn("123451",summary)

    def test_missing_race_id_and_ambiguous_races_fail_closed(self):
        bad = RACES.replace(b'Id="123451"',b'Number="123451"')
        with self.assertRaisesRegex(ValueError,"HOLD_OFFICIAL_RACE_ID"):
            identified_race(parse_xml(bad),1)
        other = RACES.replace(b'<Race Id="123452"><RaceNumber>2',
                              b'<Race Id="123452"><RaceNumber>1')
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_EXACTLY_ONE_OFFICIAL_RACE"):
            identified_race(parse_xml(other),1)

    def test_horse_schema_unknown_does_not_guess(self):
        malformed = b'<Horses><Horse Id="9001"><Alias>Alpha Horse</Alias></Horse></Horses>'
        horses, shape = horse_candidates(parse_xml(malformed))
        self.assertEqual(shape["rows"],1)
        self.assertEqual(shape["records_with_numeric_Id_and_named_value"],0)
        self.assertIn("Alias",shape["direct_child_field_names"])
        def alternative_call(op, params):
            if op=="GetHorsesForRace":
                return parse_xml(malformed),"https://example.org/stub","b"*64
            return stub_call(op,params)
        report=run_single_day("2026-10-11",gps_raw=GPS,request_fn=alternative_call)
        self.assertEqual(report["crosswalk"]["status"],"HOLD_HORSE_SCHEMA_UNRESOLVED")

    def test_duplicate_same_day_name_blocks_one_to_one_promoting_identity(self):
        dup = GPS + b"""Date,RaceNumber,11/10/2026 12:00:00 AM;Ladbrokes Cannon Park QLD - Professional;Fictional Race 2;00:00:57.263;FAKE_TRACK
11/10/2026,2,Beta Horse;3;150;18.20;00:00:10.32;350;18.70;00:00:10.70
"""
        out = candidate_gps_join("2026-10-11",1,"123451",
                                 [{"horse_id":"9001","horse_name":"Alpha Horse"},
                                  {"horse_id":"9002","horse_name":"Beta Horse"}],dup)
        self.assertEqual(out["counts"]["blocked_same_day_duplicate_name"],2)
        self.assertEqual(out["counts"]["unique_syntactic_official_name_matches"],1)
        self.assertEqual(
            out["one_race_exact_name_coverage"]["provisional_name_matches_excluding_same_day_ambiguity"],1
        )
        self.assertEqual(out["status"],"HOLD_OFFICIAL_EQUIVALENCE_AND_LONGITUDINAL_VALIDATION")

    def test_reject_external_date_and_disallow_xml_entity_definitions(self):
        with self.assertRaisesRegex(ValueError,"HOLD_NOT_ALLOWLISTED"):
            run_single_day("2027-01-01",request_fn=stub_call)
        with self.assertRaisesRegex(ValueError,"HOLD_XML_DTD"):
            parse_xml(b'<!DOCTYPE foo [<!ENTITY x "abc">]><foo>&x;</foo>')

    def test_only_explicit_soap_ops_pass_allowlist(self):
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED"):
            request_xml("GetMeetingsForDate",{"raceId":"123"})
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED"):
            request_xml("DeleteHorse",{"horseId":"123"})


if __name__=="__main__":
    unittest.main()
