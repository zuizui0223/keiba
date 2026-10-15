"""Entirely fictional 2025/2026 Doomben source and marker feasibility tests."""
from __future__ import annotations

import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_doomben_2025_marker_extension import (
    DATES_2025,PREVIOUS_2026_DATES,LOCKED_DATES,
    verify_lock, collect, evaluate, summarize, cross_year_id_overlap
)
from ecology_rq_single_race_id_probe import parse_xml


def fake_soap(operation,params,omit=None,name_changed_year=False):
    if operation=="GetMeetingsForDate":
        day=params["meetingDate"]
        if day==omit:
            raise TimeoutError("FICTIONAL_NETWORK_INTERRUPTION")
        ix=LOCKED_DATES.index(day)
        xml=(f'<Meetings><Meeting Id="{87000+ix}">'
             f'<MeetingDate>{day}</MeetingDate><TrackName>Doomben</TrackName>'
             '<IsBarrierTrial>false</IsBarrierTrial></Meeting></Meetings>')
    elif operation=="GetRacesForMeeting":
        ix=int(params["meetingId"])-87000
        xml="<Races>"+"".join(
            f'<Race Id="{700000+ix*100+n}">'
            f'<RaceNumber>{n}</RaceNumber><TrackRating>Good 4</TrackRating>'
            f'<Distance>{1200 if n==1 else 1350} metres</Distance>'
            '<Class>FICTIONAL MAIDEN</Class></Race>'
            for n in (1,2)
        )+"</Races>"
    elif operation=="GetHorsesForRace":
        key=int(params["raceId"])-700000
        ix,n=divmod(key,100)
        day=LOCKED_DATES[ix]
        xml="<Horses>"+"".join(
            f'<Horse Id="{n*100+i}">'
            f'<HorseName>{"ONE NAME" if name_changed_year and day[:4]=="2025" and n==1 and i==0 else f"FAKE HORSE {n}-{i}"}</HorseName>'
            f'<Weight>{54+i:.1f}</Weight>'
            f'<Jockey Id="{400+i}"><FullName>FICTIONAL RIDER</FullName></Jockey>'
            f'<Trainer Id="{500+i}"><FullName>FICTIONAL TRAINER</FullName></Trainer>'
            '</Horse>'
            for i in range(5)
        )+"</Horses>"
    else:
        raise AssertionError(operation)
    return parse_xml(xml.encode("utf-8")),"https://www.racingqueensland.com.au/FICTIONAL","a"*64


def fake_gps(source,naming_changed=False):
    day=source[:4]+"-"+source[4:6]+"-"+source[6:8]
    dmy=day[8:] + "/" + day[5:7] + "/" + day[:4]
    content=[]
    for n in (1,2):
        marker=150 if n==1 else 200
        content.append(
            f"Date,RaceNumber,{dmy} 12:00:00 AM;"
            f"{day} Doomben FICTIONAL - Professional;"
            f"FICTIONAL RACE {n};00:00:59.500;FAKE_ROUTE"
        )
        for i in range(5):
            name=("ONE NAME" if naming_changed and day[:4]=="2025" and n==1 and i==0
                  else f"FAKE HORSE {n}-{i}")
            duration=10+.05*i+.002*int(day[-2:])
            content.append(
                f"{dmy},{n},{name};{i+1};{marker};18.5;"
                f"00:00:{duration:06.3f};{marker+200};18.8;00:00:10.433"
            )
    return ("\n".join(content)+"\n").encode(),"https://www.racingqueensland.com.au/FICTIONAL"


class DoombenYearExtensionTests(unittest.TestCase):
    def test_exact_prelocked_monthly_source_dates(self):
        verify_lock()
        self.assertEqual(len(DATES_2025),23)
        self.assertEqual(len(PREVIOUS_2026_DATES),19)
        self.assertEqual(len(LOCKED_DATES),42)
        self.assertEqual(DATES_2025[0],"2025-01-22")
        self.assertEqual(DATES_2025[-1],"2025-12-12")
        self.assertEqual(PREVIOUS_2026_DATES[0],"2026-01-14")

    def test_all_fake_2025_and_2026_ids_are_anonymous_and_holds_if_only_five_repeat_per_marker(self):
        result=evaluate(soap=fake_soap,gps=fake_gps,on_error="raise")
        self.assertEqual(result["status"],
                         "POSTHOC_DOOMBEN_2025_2026_FIRST_MARKER_SOURCE_FEASIBILITY_COMPLETE")
        lock=result["locked_source_design"]
        self.assertEqual(len(lock["source_dates_successfully_audited"]),42)
        self.assertEqual(lock["source_dates_on_HOLD"],[])
        for period,count in (
            ("2025_ONLY_first_marker_source_models",230),
            ("2025_AND_2026_first_marker_source_models",420),
        ):
            p=result[period]
            self.assertEqual(p["source_id_linkage"]["original_ID_matched_positive_first_GPS_candidate_rows"],count)
            self.assertEqual(set(p["source_marker_repeated_IDs"]),{"150.0","200.0"})
            for marker in ("150.0","200.0"):
                support=p["source_marker_repeated_IDs"][marker]
                self.assertEqual(support["HORSES_IDs_seen_at_least_twice_on_distinct_dates"],5)
                self.assertFalse(support["source_repeated_id_threshold_passed"])
                self.assertEqual(p["first_marker_race_FE_Gaussian_horse_ICC"][marker]["status"],
                                 "HOLD_INSUFFICIENT_REPEATED_HORSES_OR_RACES_FOR_ICC")
                self.assertFalse(p["prior_Cannon150_Eagle200_reference_gates"][
                    "reference_venue_marker_comparisons"]["Cannon Park" if marker=="150.0" else "Eagle Farm"
                ]["Doomben_numerical_ICC_support_at_identical_marker"])
        shared=result["same_original_HORSES_IDs_crossing_2025_and_2026_after_identity_gate"]
        self.assertEqual(shared["status"],
                         "EXPLORATORY_SAME_ORIGINAL_HORSES_ID_ACROSS_2025_2026_SOURCES")
        self.assertEqual(shared["same_original_numeric_IDs_appearing_in_both_2025_and_2026"],10)
        for marker in ("150.0","200.0"):
            m=shared["marker_exact_and_race_context_cross_year_recurrence"][marker]
            self.assertEqual(m["original_HORSES_IDs_with_this_marker_on_2025_and_2026_dates"],5)
            self.assertEqual(m["source_IDs_with_same_marker_and_same_official_race_distance_both_years"],5)
            self.assertEqual(m["source_IDs_with_same_marker_distance_and_original_Class_both_years"],5)
            self.assertEqual(m["source_IDs_with_2plus_different_dates_in_EACH_year_same_marker"],5)
        st=json.dumps(result)
        self.assertNotIn("FAKE HORSE",st)
        self.assertNotIn('"501"',st)
        self.assertNotIn('"101"',st)
        self.assertNotIn("FICTIONAL RIDER",st)
        self.assertTrue(result["no_source_HORSES_ID_names_rider_trainer_licences_or_raw_GPS_published"])

    def test_original_source_unavailable_is_hold_not_zero_timing(self):
        def broken_api(op,params):
            return fake_soap(op,params,omit="2025-04-23")
        result=evaluate(soap=broken_api,gps=fake_gps)
        self.assertEqual(result["status"],
                         "POSTHOC_DOOMBEN_2025_2026_FIRST_MARKER_SOURCE_FEASIBILITY_PARTIAL_HOLD")
        self.assertEqual(result["locked_source_design"]["source_dates_on_HOLD"],["2025-04-23"])
        self.assertTrue(result["per_original_date_source_fingerprints_and_anonymous_coverage"][
            "2025-04-23"]["not_counted_as_zero_participation"])
        self.assertEqual(result["2025_ONLY_first_marker_source_models"][
            "source_id_linkage"]["original_ID_matched_positive_first_GPS_candidate_rows"],220)

    def test_truncated_official_chunked_XML_is_a_source_HOLD_not_zero(self):
        from http.client import IncompleteRead
        def transient_upstream_failure(op,params):
            if op=="GetMeetingsForDate" and params["meetingDate"]=="2025-03-19":
                raise IncompleteRead(b"<Meetings>",9)
            return fake_soap(op,params)
        result=evaluate(soap=transient_upstream_failure,gps=fake_gps)
        missed=result["per_original_date_source_fingerprints_and_anonymous_coverage"]["2025-03-19"]
        self.assertEqual(missed["status"],"HOLD_DATE_SOURCE_NOT_RECONCILED")
        self.assertEqual(
            missed["error_code"],
            "HOLD_INCOMPLETE_OR_TRUNCATED_OFFICIAL_HTTP_RESPONSE")
        self.assertTrue(missed["not_counted_as_zero_participation"])
        self.assertIn("2025-03-19",result["locked_source_design"]["source_dates_on_HOLD"])
        self.assertEqual(result["2025_ONLY_first_marker_source_models"][
            "source_id_linkage"]["original_ID_matched_positive_first_GPS_candidate_rows"],220)

    def test_changed_original_name_under_same_numeric_id_is_blocked(self):
        def changed_soap(op,params):
            return fake_soap(op,params,name_changed_year=True)
        def changed_gps(key):
            return fake_gps(key,naming_changed=True)
        result=evaluate(soap=changed_soap,gps=changed_gps)
        prior=result["2025_ONLY_first_marker_source_models"]["source_id_linkage"]
        combined=result["2025_AND_2026_first_marker_source_models"]["source_id_linkage"]
        self.assertEqual(prior["HORSES_IDs_with_different_names_across_dates_blocked"],0)
        self.assertEqual(combined["HORSES_IDs_with_different_names_across_dates_blocked"],1)
        self.assertEqual(combined["rows_after_original_ID_name_identity_consistency"],378)
        self.assertEqual(
            result["same_original_HORSES_IDs_crossing_2025_and_2026_after_identity_gate"]["same_original_numeric_IDs_appearing_in_both_2025_and_2026"],9)
        self.assertTrue(result["not_direct_Cannon_Eagle_Doomben_biological_replication"])

    def test_empty_2026_records_hold_cross_year_sample_instead_of_zero(self):
        rows,manifest=collect(soap=fake_soap,gps=fake_gps)
        only_2025=[r for r in rows if r["day"].startswith("2025-")]
        check=cross_year_id_overlap(only_2025)
        self.assertEqual(check["status"],
                         "HOLD_ONE_OR_BOTH_ORIGINAL_SOURCE_YEARS_EMPTY")
        self.assertTrue(check["not_proof_of_zero_real_horse_cross_year_overlap"])
        self.assertNotIn("same_original_numeric_IDs_appearing_in_both_2025_and_2026",check)

    def test_no_horse_rows_in_source_data_is_hold_not_fake_zero_icc(self):
        p=summarize([],period_label="fictional-2025")
        self.assertEqual(p["status"],"HOLD_NO_ORIGINAL_ID_MATCHED_POSITIVE_GPS_IN_PERIOD")
        self.assertFalse(p["individual_original_data_exported"])


if __name__=="__main__":
    unittest.main()
