"""Invented Eagle Farm original API/sectional fixtures; no real horse rows."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_eagle_farm_external_icc import (
    VENUE,DATES,RACE_NUMBERS,EXPECTED_ORIGINAL_FILES,
    validate_source_lock,collect,identity_overlap,compare,
    cross_venue_marker_identifiability,
)
from ecology_rq_multigoing_h1_preflight import audit_one_day
from ecology_rq_single_race_id_probe import parse_xml


def fake_soap(op,params):
    if op=="GetMeetingsForDate":
        d=params["meetingDate"]
        n=DATES.index(d)
        xml=(f'<Meetings><Meeting Id="{27000+n}">'
             f'<MeetingDate>{d}</MeetingDate>'
             f'<TrackName>Eagle Farm</TrackName>'
             f'<IsBarrierTrial>false</IsBarrierTrial></Meeting></Meetings>')
    elif op=="GetRacesForMeeting":
        d=DATES[int(params["meetingId"])-27000]
        n=DATES.index(d)
        # 4 of 6 fixed races: missing 5 & 6 MUST NOT be invented.
        xml="<Races>"+"".join(
            f'<Race Id="{300000+n*100+r}">'
            f'<RaceNumber>{r}</RaceNumber>'
            f'<TrackRating>{"Good" if n%2 else "Soft 5"}</TrackRating>'
            f'<Distance>{"1000" if r%2 else "1200"} metres</Distance>'
            f'<Class>Invented Class {r}</Class></Race>'
            for r in range(1,5)
        )+"</Races>"
    elif op=="GetHorsesForRace":
        ident=int(params["raceId"])-300000
        n,r=divmod(ident,100)
        xml="<Horses>"+"".join(
            f'<Horse Id="{90000+r*100+i}">'
            f'<HorseName>FAKE-EAGLE-HORSE-R{r}-N{i}</HorseName>'
            f'<Weight>{54+i*.5:.1f}</Weight>'
            f'<Jockey Id="{40000+i}"><FullName>FICTIONAL Rider</FullName></Jockey>'
            f'<Trainer Id="{50000+(i%3)}"><FullName>FICTIONAL Trainer</FullName></Trainer>'
            f'</Horse>'
            for i in range(6)
        )+"</Horses>"
    else:
        raise AssertionError("Unexpected fake official request "+op)
    return parse_xml(xml.encode()),"https://www.racingqueensland.com.au/fake","e"*64


def fake_gps(source):
    d=next(k for k,v in EXPECTED_ORIGINAL_FILES.items() if v==source)
    ordinal=DATES.index(d)
    ddmm=f"{d[8:10]}/{d[5:7]}/{d[:4]}"
    rows=[]
    for r in range(1,5):
        marker=150 if r%2 else 250
        rows.append(
            f'Date,RaceNumber,{ddmm} 12:00:00 AM;'
            f'Eagle Farm QLD Fake Venue {d};Invented race {r};'
            f'00:00:55.000;FAKE_ROUTE'
        )
        for i in range(6):
            rng=random.Random(20261013+r*10000+i*100+ordinal)
            first=10.0+.12*i+.0015*ordinal+rng.gauss(0,.055)
            second=10.6+rng.gauss(0,.1)
            rows.append(
                f'{ddmm},{r},FAKE-EAGLE-HORSE-R{r}-N{i};{i+1};'
                f'{marker};19.5;00:00:{first:06.3f};'
                f'{marker+200};19.3;00:00:{second:06.3f}'
            )
    return ("\n".join(rows)+"\n").encode(),"https://www.racingqueensland.com.au/fake_original.csv"


class ExternalSiteLockTests(unittest.TestCase):
    def test_exact_twelve_meetings_six_source_races_before_outcomes(self):
        validate_source_lock()
        self.assertEqual(len(DATES),12)
        self.assertEqual(RACE_NUMBERS,(1,2,3,4,5,6))
        self.assertEqual(VENUE,"Eagle Farm")
        self.assertEqual(DATES,tuple(sorted(DATES)))
        self.assertEqual(EXPECTED_ORIGINAL_FILES["2026-01-03"],
                         "20260103-eagle-farm")
        self.assertEqual(EXPECTED_ORIGINAL_FILES["2026-10-10"],
                         "20261010-eagle-farm")

    def test_same_original_source_identity_linking_across_new_venue(self):
        rows,manifest=collect(soap=fake_soap,gps=fake_gps,on_source_error="raise")
        self.assertEqual(len(rows),12*4*6)
        self.assertEqual(len(manifest),12)
        self.assertTrue(all(s["status"]=="SOURCE_EAGLE_FARM_OFFICIAL_IDS_AND_GPS_AUDITED"
                            for s in manifest.values()))
        self.assertEqual(manifest["2026-01-03"]["official_race_numbers_not_in_API"],
                         [5,6])
        self.assertEqual(manifest["2026-01-03"]["source_HORSES_IDs_listed_in_multiple_races_same_date"],0)
        clean,ids=identity_overlap(rows)
        self.assertEqual(len(clean),12*4*6)
        self.assertEqual(ids["distinct_original_IDs_after_name_identity_screen"],24)
        self.assertEqual(ids["horse_IDs_in_2plus_source_dates"],24)
        self.assertEqual(ids["HORSES_IDs_with_4plus_source_starts"],24)
        self.assertTrue(ids["not_confirmed_complete_entrant_or_finisher_population"])

    def test_external_original_source_model_runs_but_no_h1_or_h2(self):
        result=compare(soap=fake_soap,gps=fake_gps,on_source_error="raise")
        self.assertTrue(result["locked_source_design"]["cohort_was_fixed_before_Eagle_Farm_original_HORSES_ID_or_ICC_read"])
        self.assertEqual(len(result["locked_source_design"]["original_dates_successfully_audited"]),12)
        self.assertEqual(result["independent_venue_original_ID_support"]["original_ID_matched_positive_first_GPS_candidate_rows"],288)
        icc=result["conditional_ICC_at_Eagle_Farm_existing_race_FE_implementation"]
        point=icc["all_races_at_least_four_timed_horses"]
        self.assertEqual(point["status"],"EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY")
        self.assertGreater(point["conditional_observational_ICC_point_estimate"],.15)
        self.assertEqual(point["original_races"],48)
        self.assertEqual(point["original_date_clusters"],12)
        self.assertFalse(result["ecological_H1_ground_reaction_norm_var_supported"])
        self.assertFalse(result["ecological_H2_competitor_social_interaction_supported"])
        self.assertTrue(icc["not_H1_or_H2_or_causal_or_heritability"])
        gate=result["different_venue_same_first_GPS_marker_ICC_identifiability"]
        self.assertIn(gate["status"],{
            "HOLD_NO_SHARED_FIRST_SECTION_MARKER_WITH_ESTIMABLE_ICC",
            "EXPLORATORY_SAME_FIRST_MARKER_VENUE_ICC_COMPARABLE",
        })
        self.assertFalse(
            gate["pooled_Cannon_vs_Eagle_ICC_can_establish_universal_horse_trait"])
        self.assertFalse(result["actual_starter_DNF_and_individual_official_finish_verified"])
        s=json.dumps(result)
        self.assertNotIn("FAKE-EAGLE-HORSE",s)
        self.assertNotIn('"90100"',s)
        self.assertNotIn('"40000"',s)

    def test_cross_venue_marker_mismatch_blocks_universal_icc_claim(self):
        # Cannon can estimate 150m and 250m source marker ICC, but not
        # 100m or 200m. Eagle has ONLY a valid 200m model here.
        fake={
            "first_section_marker_sensitivity":{
                "200.0":{
                    "status":"EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY",
                    "source_rows":300,
                },
                "100.0":{"status":"HOLD_INSUFFICIENT_REPEATED_HORSES_OR_RACES_FOR_ICC",
                         "source_rows":30},
            }
        }
        gate=cross_venue_marker_identifiability(fake)
        self.assertEqual(gate["status"],
                         "HOLD_NO_SHARED_FIRST_SECTION_MARKER_WITH_ESTIMABLE_ICC")
        self.assertEqual(gate["first_markers_with_estimable_ICC_at_both_venues"],[])
        self.assertFalse(gate["pooled_Cannon_vs_Eagle_ICC_can_establish_universal_horse_trait"])
        self.assertFalse(gate["original_source_markers_screened"]["200.0"][
            "identical_first_section_marker_model_estimable_at_both_venues"])
        # Only if Eagle also has supported 150m source data does an
        # identical-marker *numeric* comparison become possible; even
        # that does not prove site effects or heritability.
        fake["first_section_marker_sensitivity"]["150.0"]={
            "status":"EXPLORATORY_RACE_ADJUSTED_GAUSSIAN_ICC_POINT_ONLY",
            "source_rows":220,
        }
        allowed=cross_venue_marker_identifiability(fake)
        self.assertEqual(allowed["first_markers_with_estimable_ICC_at_both_venues"],
                         ["150.0"])
        self.assertFalse(allowed["pooled_Cannon_vs_Eagle_ICC_can_establish_universal_horse_trait"])

    def test_wrong_venue_or_disallowed_filename_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"HOLD_INCORRECT_VENUE_WITHOUT_LOCKED"):
            audit_one_day("2026-10-10",soap=fake_soap,gps=fake_gps,
                          venue="Eagle Farm")
        with self.assertRaisesRegex(ValueError,"HOLD_UNAPPROVED_EXTERNAL_COHORT"):
            audit_one_day(
                "2026-10-10",soap=fake_soap,gps=fake_gps,
                venue="Eagle Farm",locked_config={
                    "source":"20261010-cairns",
                    "ground_expected":"SOURCE_RACE_LEVEL",
                    "races":RACE_NUMBERS,
                }
            )

    def test_unavailable_original_source_date_is_not_zero_animal_icc(self):
        def missing(source):
            if source==EXPECTED_ORIGINAL_FILES["2026-07-25"]:
                raise TimeoutError("synthetic unavailable original GPS")
            return fake_gps(source)
        rows,manifest=collect(soap=fake_soap,gps=missing)
        self.assertEqual(len(rows),11*4*6)
        self.assertEqual(manifest["2026-07-25"]["status"],
                         "HOLD_DATE_SOURCE_NOT_RECONCILED")
        self.assertTrue(manifest["2026-07-25"]["not_counted_as_zero_participation"])

    def test_changed_name_same_official_numeric_ID_is_blocked(self):
        rows,_=collect(soap=fake_soap,gps=fake_gps,on_source_error="raise")
        altered=[dict(r) for r in rows]
        altered[0]["horse_name"]="DIFFERENT_NAME_REUSED_ID"
        cleaned,diag=identity_overlap(altered)
        self.assertEqual(diag["HORSES_IDs_with_different_names_across_dates_blocked"],1)
        self.assertEqual(len(cleaned),len(rows)-12)


if __name__=="__main__":
    unittest.main()
