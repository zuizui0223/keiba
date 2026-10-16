"""Only fabricated Doomben source data, independent-track marker-bridge tests.

Does not use real animal identities, real GPS timing, rider, betting
or actual horse biological results; official source read happens in CI.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_doomben_third_venue_icc import (
    VENUE,DATES,RACE_NUMBERS,FILES,validate_lock,
    collect,evaluate,match_cannon_eagle,
)
from ecology_rq_single_race_id_probe import parse_xml
from ecology_rq_multigoing_h1_preflight import audit_one_day


def fake_soap(op,params,unique_on_each_date=False):
    if op=="GetMeetingsForDate":
        day=params["meetingDate"]
        index=DATES.index(day)
        xml=(f'<Meetings><Meeting Id="{85000+index}">'
             f'<MeetingDate>{day}</MeetingDate>'
             f'<TrackName>Doomben</TrackName>'
             f'<IsBarrierTrial>false</IsBarrierTrial></Meeting></Meetings>')
    elif op=="GetRacesForMeeting":
        index=int(params["meetingId"])-85000
        ground=("Good" if index%2 else "Soft 5")
        xml="<Races>"+"".join(
            f'<Race Id="{750000+index*100+race}">'
            f'<RaceNumber>{race}</RaceNumber>'
            f'<TrackRating>{ground}</TrackRating>'
            f'<Distance>{"1200" if race%2 else "1350"} metres</Distance>'
            f'<Class>FAKE CLASS {race}</Class></Race>'
            for race in RACE_NUMBERS
        )+"</Races>"
    elif op=="GetHorsesForRace":
        index,race=divmod(int(params["raceId"])-750000,100)
        xml="<Horses>"+"".join(
            f'<Horse Id="{(index*100000 if unique_on_each_date else 0)+race*100+i}">'
            f'<HorseName>FICTIONAL DOOMBEN {race}-{i}</HorseName>'
            f'<Weight>{54+i*.25:.1f}</Weight>'
            f'<Jockey Id="{450+i}"><FullName>FAKE RIDER</FullName></Jockey>'
            f'<Trainer Id="{550+(i%4)}"><FullName>FAKE TRAINER</FullName></Trainer>'
            f'</Horse>'
            for i in range(8)
        )+"</Horses>"
    else:
        raise AssertionError("Unallowed fake API operation")
    return parse_xml(xml.encode("utf-8")),"https://www.racingqueensland.com.au/mock","a"*64


def fake_gps(key):
    day=next(d for d,s in FILES.items() if s==key)
    index=DATES.index(day)
    dmy=f"{day[8:]}/{day[5:7]}/{day[:4]}"
    lines=[]
    for race in RACE_NUMBERS:
        marker=150 if race%2 else 200
        lines.append(
            f"Date,RaceNumber,{dmy} 12:00:00 AM;"
            f"2026-{day[5:7]}-{day[8:]} Doomben QLD - Professional;"
            f"FICTIONAL RACE {race};00:00:58.000;FAKE_ROUTE"
        )
        for i in range(8):
            r=random.Random(390+i*31+race*41+index*17)
            seconds=9.8+.08*i+.01*(index%3)+r.gauss(0,.03)
            lines.append(
                f"{dmy},{race},FICTIONAL DOOMBEN {race}-{i};{i+1};"
                f"{marker};19.5;00:00:{seconds:06.3f};"
                f"{marker+200};19.7;00:00:10.341"
            )
    return ("\n".join(lines)+"\n").encode(),"https://www.racingqueensland.com.au/fake.csv"


class DoombenThirdTrackTests(unittest.TestCase):
    def test_original_source_lock_dates_file_ids_and_exact_venue(self):
        validate_lock()
        self.assertEqual(len(DATES),19)
        self.assertEqual(tuple(sorted(DATES)),DATES)
        self.assertEqual(DATES[0],"2026-01-14")
        self.assertEqual(DATES[-1],"2026-10-05")
        self.assertEqual(FILES["2026-01-14"],"20260114-doomben")
        self.assertEqual(FILES["2026-10-05"],"20261005-doomben")
        self.assertEqual(RACE_NUMBERS,(1,2,3,4,5,6))
        with self.assertRaisesRegex(ValueError,"HOLD_INCORRECT_VENUE_WITHOUT_LOCKED"):
            audit_one_day("2026-10-05",venue="Doomben",soap=fake_soap,gps=fake_gps)

    def test_complete_fake_venue_both_markers_estimable_without_claiming_h1h2(self):
        outcome=evaluate(soap=fake_soap,gps=fake_gps,source_errors="raise")
        self.assertEqual(outcome["status"],
                         "DOOMBEN_THIRD_VENUE_ORIGINAL_SOURCE_MARKER_PILOT_NO_H1_H2")
        self.assertEqual(len(outcome["source_lock"]["dates_successfully_original_source_audited"]),19)
        self.assertEqual(outcome["original_numeric_HORSES_ID_source_support"][
            "original_ID_matched_positive_first_GPS_candidate_rows"],19*6*8)
        for source_date in DATES:
            snap=outcome["source_manifest"][source_date]
            self.assertEqual(snap["official_horse_rosters_hashed"],6)
            self.assertEqual(len(snap[
                "official_HORSES_roster_XML_sha256_combined_without_IDs"]),64)
            self.assertTrue(snap[
                "roster_snapshot_source_hashes_are_needed_to_identify_edition_changes"])
        self.assertEqual(outcome["original_numeric_HORSES_ID_source_support"][
            "horse_IDs_in_2plus_source_dates"],48)
        models=outcome["first_marker_150_and_200_original_race_FE_ICC"]
        for v in models.values():
            self.assertEqual(v["status"],"EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY")
            self.assertGreater(v["conditional_observational_ICC_point_estimate"],.1)
            self.assertEqual(v["source_rows"],19*3*8)
            self.assertEqual(v["original_races"],19*3)
        self.assertEqual(outcome["Cannon_Eagle_reference_marker_compatibility"][
            "matched_marker_numeric_comparisons_supported"],2)
        for value in outcome["first_marker_150_and_200_repeat_ID_identifiability"].values():
            self.assertEqual(value["HORSES_IDs_seen_at_least_twice_on_distinct_dates"],24)
            self.assertTrue(value["source_repeated_id_threshold_passed"])
            self.assertEqual(value["source_distinct_dates"],19)
        self.assertFalse(outcome["H1_ground_reaction_norm_variance_estimated"])
        self.assertFalse(outcome["H2_social_context_response_estimated"])
        self.assertTrue(outcome["raw_original_horse_names_IDs_or_individual_interval_exported"] is False)
        encoded=json.dumps(outcome)
        self.assertNotIn("FICTIONAL DOOMBEN",encoded)
        self.assertNotIn('"450"',encoded)
        self.assertNotIn("FAKE TRAINER",encoded)

    def test_no_repeated_biological_ids_returns_hold_not_a_zero_icc(self):
        def no_repeat_soap(op,params):
            return fake_soap(op,params,unique_on_each_date=True)
        out=evaluate(soap=no_repeat_soap,gps=fake_gps,source_errors="raise")
        models=out["first_marker_150_and_200_original_race_FE_ICC"]
        self.assertEqual(models["150.0"]["status"],
                         "HOLD_INSUFFICIENT_REPEATED_HORSES_OR_RACES_FOR_ICC")
        self.assertEqual(out["Cannon_Eagle_reference_marker_compatibility"][
            "matched_marker_numeric_comparisons_supported"],0)
        for value in out["first_marker_150_and_200_repeat_ID_identifiability"].values():
            self.assertEqual(value["HORSES_IDs_seen_at_least_twice_on_distinct_dates"],0)
            self.assertFalse(value["source_repeated_id_threshold_passed"])
        self.assertEqual(out["Cannon_Eagle_reference_marker_compatibility"][
            "status"],"HOLD_NO_SHARED_SOURCE_MARKER_WITH_NUMERIC_HORSE_ICC")

    def test_missing_original_source_date_never_equals_zero_horse_icc(self):
        def sometimes_missing(key):
            if key==FILES["2026-05-16"]:
                raise TimeoutError("fictional missing vendor GPS")
            return fake_gps(key)
        out=evaluate(soap=fake_soap,gps=sometimes_missing)
        self.assertEqual(out["status"],"HOLD_INCOMPLETE_LOCKED_DOOMBEN_SOURCE_DATES")
        self.assertEqual(out["source_lock"]["dates_source_HOLD"],["2026-05-16"])
        self.assertTrue(out["source_manifest"]["2026-05-16"][
            "not_counted_as_zero_participation"])
        self.assertEqual(out["source_manifest"]["2026-05-16"]["error_type"],
                         "TimeoutError")

    def test_source_key_cannot_be_substituted_by_other_track(self):
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED_EXTERNAL_COHORT"):
            audit_one_day(
                "2026-10-05",soap=fake_soap,gps=fake_gps,
                venue="Doomben",locked_config={
                    "source":"20261005-eagle-farm",
                    "ground_expected":"SOURCE_RACE_LEVEL",
                    "races":RACE_NUMBERS,
                }
            )


if __name__=="__main__":
    unittest.main()
