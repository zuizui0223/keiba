"""Fictional original-SOAP/GPS tests for locked 12-date Cannon Park source audit."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_rq_2026_calendar_overlap import COHORT, NEW_DATES, compare, validate_cohort
from ecology_rq_multigoing_h1_preflight import audit_one_day
from ecology_rq_single_race_id_probe import parse_xml


def stub_soap(op, params, *, class_confounded=False, fail_day=None):
    days=list(COHORT)
    if op=="GetMeetingsForDate":
        day=params["meetingDate"]
        if day==fail_day:
            raise ValueError("HOLD_TEST_SOURCE_MISSING")
        i=days.index(day)
        body=(f'<Meetings><Meeting Id="{62000+i}">'
              f'<MeetingDate>{day}</MeetingDate>'
              '<TrackName>Ladbrokes Cannon Park</TrackName>'
              '<IsBarrierTrial>false</IsBarrierTrial></Meeting></Meetings>')
    elif op=="GetRacesForMeeting":
        i=int(params["meetingId"])-62000
        day=days[i]
        ground=COHORT[day][0]
        cl=("A" if ground=="Good" else "B") if class_confounded else "SameClass"
        body="<Races>"+"".join(
            f'<Race Id="{770000+i*100+n}">'
            f'<RaceNumber>{n}</RaceNumber>'
            f'<TrackRating>{ground} 5</TrackRating>'
            f'<Distance>950 metres</Distance><Class>{cl}</Class>'
            '</Race>'
            for n in range(1,9)
        )+"</Races>"
    elif op=="GetHorsesForRace":
        encoded=int(params["raceId"])-770000
        i,n=divmod(encoded,100)
        # "Recurring" IDs only for R1 and R2. Others unique by source day.
        hid=(101 if n==1 else 102 if n==2 else 800000+i*100+n)
        animal=("RepeatA" if n==1 else "RepeatB" if n==2
                else f"Day{i}R{n}")
        body=(f'<Horses><Horse Id="{hid}">'
              f'<HorseName>{animal}</HorseName>'
              '</Horse></Horses>')
    else:
        raise AssertionError(op)
    return parse_xml(body.encode("utf-8")), "https://www.racingqueensland.com.au/fake", "a"*64


def stub_gps(source: str):
    found={v[1]:day for day,v in COHORT.items()}
    day=found[source]
    i=list(COHORT).index(day)
    date=day[8:]+'/'+day[5:7]+'/'+day[:4]
    output=[]
    for n in range(1,9):
        name=("RepeatA" if n==1 else "RepeatB" if n==2
              else f"Day{i}R{n}")
        output += [
            f"Date,RaceNumber,{date} 12:00:00 AM;"
            f"FICTIONAL Ladbrokes Cannon Park;Race {n};00:00:56.000;F950",
            f"{date},{n},{name};1;150;19.2;00:00:10.25;"
            f"350;19.4;00:00:10.55",
        ]
    return ("\n".join(output)+"\n").encode("utf-8"), "https://www.racingqueensland.com.au/fake.csv"


class Calendar2026Tests(unittest.TestCase):
    def test_manifest_exact_dates_and_official_file_sources(self):
        validate_cohort()
        self.assertEqual(len(COHORT),12)
        self.assertEqual(len(NEW_DATES),7)
        self.assertEqual(list(COHORT),sorted(COHORT))
        self.assertEqual({v[0] for v in COHORT.values()},
                         {"Good","Soft","Heavy"})
        for date,(_,source) in COHORT.items():
            self.assertEqual(source,date.replace("-","")+"-cairns")

    def test_all_twelve_days_same_horse_with_rich_going_support(self):
        out=compare(soap=stub_soap,gps=stub_gps,warn_on_source_errors=False)
        self.assertEqual(out["status"],
                         "REAL_EQUINE_2026_CALENDAR_SOURCE_OVERLAP_NOT_H1_H2_EFFECT")
        self.assertEqual(len(out["temporal_cohort"]["source_dates_successful"]),12)
        self.assertEqual(out["temporal_cohort"]["source_dates_HOLD"],[])
        s=out["support"]
        self.assertEqual(s["positive_first_section_id_linked_candidate_rows"],96)
        self.assertEqual(s["stable_name_HORSES_IDs_on_two_or_more_original_dates"],2)
        self.assertEqual(s["stable_name_HORSES_IDs_with_both_Good_and_nonGood"],2)
        strict=s["same_official_distance_first_section_marker_and_class"]
        self.assertEqual(strict["horse_IDs_with_2plus_independent_dates_each_Good_and_wet"],2)
        self.assertFalse(out["actual_confirmed_starter_and_finish_status_verified"])
        self.assertFalse(out["ground_effect_or_random_slope_variance_fitted"])
        self.assertEqual(out["exploratory_early_pace_ID_persistence_NOT_H1_or_H2"]["status"],
                         "HOLD_INSUFFICIENT_POSITIVE_GPS_RACES_OR_DATES_FOR_PERSISTENCE")
        self.assertFalse(out["exploratory_early_pace_ID_persistence_NOT_H1_or_H2"]["independent_real_horse_effect_supported_H1"])
        self.assertTrue(out["individual_pace_repeatability_analysed_only_as_race_relative_first_interval"])
        dump=json.dumps(out)
        self.assertNotIn("RepeatA",dump)
        self.assertNotIn('"101"',dump)
        self.assertNotIn("Day11R",dump)

    def test_complete_ground_confounding_with_class_cannot_pass_strict(self):
        def req(op,params):
            return stub_soap(op,params,class_confounded=True)
        out=compare(soap=req,gps=stub_gps,warn_on_source_errors=False)
        self.assertEqual(out["support"]["stable_name_HORSES_IDs_with_both_Good_and_nonGood"],2)
        self.assertEqual(
            out["support"]["same_official_distance_and_first_section_marker"][
                "horse_IDs_with_2plus_independent_dates_each_Good_and_wet"],2)
        self.assertEqual(
            out["support"]["same_official_distance_first_section_marker_and_class"][
                "horse_IDs_with_2plus_independent_dates_each_Good_and_wet"],0)

    def test_race_level_soft_during_heavy_meeting_keeps_source_and_correct_going(self):
        def mixed_ground_soap(op, params):
            root,url,sha=stub_soap(op,params)
            if op=="GetRacesForMeeting" and params["meetingId"]==str(
                62000+list(COHORT).index("2026-03-12")
            ):
                # The original index page said Heavy, but one official
                # race can have the more precise Soft TrackRating.
                node=root.find("./Race")
                node.find("TrackRating").text="Soft 7"
            return root,url,sha
        out=compare(soap=mixed_ground_soap,gps=stub_gps)
        self.assertEqual(out["temporal_cohort"]["source_dates_HOLD"],[])
        self.assertEqual(
            out["temporal_cohort"]["source_dates_using_race_rating_different_from_meeting_page"],
            ["2026-03-12"],
        )
        day=out["date_scoped_source_manifest"]["2026-03-12"]
        self.assertEqual(day["official_race_ground_labels"],{"Soft":1,"Heavy":7})
        self.assertTrue(day["race_level_ground_was_used_not_page_rating"])
        self.assertEqual(day["candidate_ID_linked_positive_first_GPS_rows"],8)

    def test_unreachable_meeting_is_hold_not_zero_animal_response(self):
        def req(op,params):
            return stub_soap(op,params,fail_day="2026-04-04")
        out=compare(soap=req,gps=stub_gps)
        self.assertEqual(len(out["temporal_cohort"]["source_dates_successful"]),11)
        self.assertEqual(out["temporal_cohort"]["source_dates_HOLD"],["2026-04-04"])
        hold=out["date_scoped_source_manifest"]["2026-04-04"]
        self.assertEqual(hold["status"],"HOLD_DATE_SOURCE_NOT_RECONCILED")
        self.assertTrue(hold["not_counted_as_zero_participation"])
        self.assertGreater(out["support"]["positive_first_section_id_linked_candidate_rows"],0)

    def test_unknown_manifest_source_does_not_request_arbitrary_urls(self):
        with self.assertRaisesRegex(ValueError, "HOLD_UNAPPROVED_EXTERNAL_COHORT"):
            audit_one_day("2026-02-16", soap=stub_soap,gps=stub_gps,
                          locked_config={
                              "source":"20261111-cairns","ground_expected":"Heavy",
                              "races":tuple(range(1,9)),
                          })


if __name__ == "__main__":
    unittest.main()
