"""Fully invented two-date RQ HORSES-ID recurrence software check.

Actual equine observations are fetched separately by the bounded CI
workflow. Here every XML ID, label and GPS row is deliberately fictional.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from ecology_rq_two_date_horse_id_repeat import (
    SAMPLE, compare, extract_selected_races, one_date
)
from ecology_rq_single_race_id_probe import parse_xml


RACE_IDS={}
for di,day in enumerate(SAMPLE):
    for num in SAMPLE[day]["race_numbers"]:
        RACE_IDS[str(700000+di*1000+num)]=(day,num)


def fake_req(op,params):
    if op=="GetMeetingsForDate":
        day=params["meetingDate"]
        mid="600001" if day=="2026-08-29" else "600002"
        text=(f'<Meetings><Meeting Id="{mid}">'
              f'<MeetingDate>{day}</MeetingDate>'
              f'<TrackName>Ladbrokes Cannon Park</TrackName>'
              f'<IsBarrierTrial>false</IsBarrierTrial></Meeting></Meetings>')
    elif op=="GetRacesForMeeting":
        di=0 if params["meetingId"]=="600001" else 1
        day=list(SAMPLE)[di]
        text="<Races>"+ "".join(
            f'<Race Id="{700000+di*1000+n}"><RaceNumber>{n}</RaceNumber>'
            f'<TrackRating>Good</TrackRating><Distance>950 metres</Distance>'
            f'<Class>Maiden</Class></Race>'
            for n in SAMPLE[day]["race_numbers"]
        ) + "</Races>"
    elif op=="GetHorsesForRace":
        day,n=RACE_IDS[params["raceId"]]
        # One identical official HORSES Id across 6 weeks:
        # Aug29 race 2 and Oct11 race 2.
        h_id="500" if n==2 else str(900000+int(day[-2:])*100+n)
        name="Repeat Horse" if n==2 else f"Other Horse {day} {n}"
        text=f'<Horses><Horse Id="{h_id}"><HorseName>{name}</HorseName></Horse></Horses>'
    else:
        raise AssertionError(op)
    return parse_xml(text.encode()),"https://www.racingqueensland.com.au/fictional","x"*64


def fake_gps(which:str):
    date=("29/08/2026" if which=="20260829-cairns"
          else "11/10/2026")
    day="2026-08-29" if which=="20260829-cairns" else "2026-10-11"
    data=[]
    for n in SAMPLE[day]["race_numbers"]:
        name="Repeat Horse" if n==2 else f"Other Horse {day} {n}"
        data += [
            f"Date,RaceNumber,{date} 12:00:00 AM;FICTIONAL;Race {n};00:00:57.000;FAKE_ROUTE",
            f"{date},{n},{name};1;150;18.3;00:00:10.50;350;18.6;00:00:10.33",
        ]
    return ("\n".join(data)+"\n").encode(),"https://www.racingqueensland.com.au/fictional-source"


class TwoDateHorseIdTests(unittest.TestCase):
    def test_stable_numeric_HORSES_id_reappears_on_two_original_dates(self):
        output=compare(request_fn=fake_req,gps_fn=fake_gps)
        self.assertEqual(output["status"],"REAL_HORSE_OFFICIAL_ID_RECURRENCE_AUDIT_H1_H2_HOLD")
        x=output["cross_date"]
        self.assertEqual(x["both_same_official_horse_id_and_exact_name"],1)
        self.assertEqual(x["repeated_official_ids_with_positive_gps_both_dates"],1)
        self.assertEqual(x["repeating_numeric_id_but_name_changed"],0)
        self.assertFalse(output["identity_values_or_raw_horse_names_exported"])
        self.assertFalse(x["repetition_is_confirmed_finish_time_or_horse_reaction_norm"])
        self.assertFalse(output["track_ground_response_identifiable_after_two_dates"])
        self.assertFalse(output["competitor_interactions_identifiable_after_two_dates"])
        import json
        report=json.dumps(output)
        self.assertNotIn("Repeat Horse",report)
        self.assertNotIn('"500"',report)

    def test_fixed_source_race_count_per_day_and_going_label(self):
        output,_=one_date("2026-08-29",request_fn=fake_req,gps_fn=fake_gps)
        self.assertEqual(output["selected_race_count"],4)
        self.assertEqual(output["official_selected_race_numbers_missing_from_API"],[])
        self.assertTrue(output["not_extrapolating_missing_race_IDs"])
        self.assertEqual(output["syntactically_matched_positive_gps"],4)
        self.assertEqual(output["official_with_no_unique_gps_match"],0)
        self.assertEqual(output["official_selected_race_metadata_groups"]["ground_labels"],{"Good":4})

    def test_missing_official_race_id_and_excess_requested_races_are_holds(self):
        root=ET.fromstring(b'<Races><Race Id="123"><RaceNumber>1</RaceNumber></Race></Races>')
        with self.assertRaisesRegex(ValueError,"HOLD_NO_SELECTED_RACE"):
            extract_selected_races(root,(2,3,4,5))
        partial, n=extract_selected_races(root,(1,2,3,4))
        self.assertEqual(set(partial),{1})
        self.assertEqual(n,1)
        with self.assertRaisesRegex(ValueError,"HOLD_NON_ALLOWLISTED"):
            one_date("2025-01-01",request_fn=fake_req,gps_fn=fake_gps)

    def test_unknown_horse_id_does_not_fake_identity_link(self):
        def fake_bad_req(op,params):
            if op=="GetHorsesForRace":
                return parse_xml(b'<Horses><Horse><HorseName>Unknown</HorseName></Horse></Horses>'),"https://www.racingqueensland.com.au/mock","x"*64
            return fake_req(op,params)
        with self.assertRaisesRegex(ValueError,"HOLD_OFFICIAL_HORSE_IDS"):
            compare(request_fn=fake_bad_req,gps_fn=fake_gps)


if __name__ == "__main__":
    unittest.main()
