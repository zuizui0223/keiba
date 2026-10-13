"""Entirely fictional five-date multigoing Thoroughbred-source overlap checks."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_multigoing_h1_preflight import (
    SELECTED, VENUE, audit_one_day, comparison, ground_class,
    first_section_table, selected_official_races
)
from ecology_rq_single_race_id_probe import parse_xml


def fake_req(op, params, class_confounded=False):
    if op=="GetMeetingsForDate":
        day=params["meetingDate"]
        ix=list(SELECTED).index(day)
        xml=(f'<Meetings><Meeting Id="{8000+ix}">'
             f'<MeetingDate>{day}</MeetingDate><TrackName>{VENUE}</TrackName>'
             '<IsBarrierTrial>false</IsBarrierTrial></Meeting></Meetings>')
    elif op=="GetRacesForMeeting":
        ix=int(params["meetingId"])-8000
        day=list(SELECTED)[ix]
        cfg=SELECTED[day]
        cl=("DifferentClass" if class_confounded and
            cfg["ground_expected"]!="Good" else "Maiden")
        xml="<Races>" + "".join(
            f'<Race Id="{90000+ix*100+n}"><RaceNumber>{n}</RaceNumber>'
            f'<TrackRating>{cfg["ground_expected"]} '
            f'{"9" if cfg["ground_expected"]=="Heavy" else "5"}</TrackRating>'
            f'<Distance>950 metres</Distance><Class>{cl}</Class></Race>'
            for n in cfg["races"]
        ) + "</Races>"
    elif op=="GetHorsesForRace":
        code=int(params["raceId"])-90000
        ix,n=divmod(code,100)
        day=list(SELECTED)[ix]
        horse_id=("101" if n==1 else "102" if n==2 else
                  str(10000+ix*100+n))
        name=("StableA" if n==1 else "StableB" if n==2 else
              f"Filler{ix}R{n}")
        xml=(f'<Horses><Horse Id="{horse_id}"><HorseName>'
             f'{name}</HorseName></Horse></Horses>')
    else:
        raise AssertionError(op)
    return parse_xml(xml.encode("utf-8")),"https://www.racingqueensland.com.au/fake","0"*64


def gps_fake(source, duplicate_same_day=False):
    days={cfg["source"]:day for day,cfg in SELECTED.items()}
    day=days[source]
    d,mo,year=day[8:10],day[5:7],day[:4]
    clock=f"{d}/{mo}/{year}"
    ix=list(SELECTED).index(day)
    lines=[]
    for n in SELECTED[day]["races"]:
        animal=("StableA" if n==1 else "StableB" if n==2 else
                f"Filler{ix}R{n}")
        lines.append(
            f"Date,RaceNumber,{clock} 12:00:00 AM;FICTIONAL {VENUE};"
            f"Race {n};00:00:56.000;FAKE_950_TRACK")
        lines.append(f"{clock},{n},{animal};1;150;19.0;"
                     f"00:00:10.{20+ix:02d};350;19.0;00:00:10.67")
        if duplicate_same_day and n==3:
            lines.append(f"{clock},{n},StableA;2;150;19.0;"
                         "00:00:10.24;350;19.0;00:00:10.56")
    return ("\n".join(lines)+"\n").encode("utf-8"),"https://www.racingqueensland.com.au/fake-GPS"


class MultiGoingTests(unittest.TestCase):
    def test_5_days_true_going_and_repeated_individual_id_design(self):
        out=comparison(soap=fake_req,gps=gps_fake)
        self.assertEqual(out["status"],
                         "REAL_EQUINE_MULTIGOING_FEASIBILITY_NOT_H1_H2_EVIDENCE")
        self.assertEqual(len(out["selected_dates"]),5)
        self.assertFalse(out["data_row_horse_ID_or_name_output"])
        self.assertFalse(out["fit_random_slope_H1"])
        self.assertFalse(out["fit_social_competition_H2"])
        s=out["within_horse_support"]
        self.assertEqual(s["recurrent_ids_with_both_Good_and_non_Good"],2)
        self.assertEqual(
            s["strict_horse_ID_matching_official_distance_first_section_marker_and_race_class"],2)
        self.assertEqual(s["strict_strata_with_at_least_two_good_AND_two_wet_starts"],2)
        self.assertEqual(s["contrast_types_with_at_least_one_repeat"]["good_vs_soft"],2)
        self.assertEqual(s["contrast_types_with_at_least_one_repeat"]["good_vs_heavy"],2)
        self.assertTrue(all(v["ground_disagreeing_with_page"]==0 for v in out["per_date"].values()))
        self.assertTrue(all(v["eligible_official_ID_matched_first_section_rows"]==4
                            for v in out["per_date"].values()))
        import json
        serialized=json.dumps(out)
        self.assertNotIn("StableA",serialized)
        self.assertNotIn('"101"',serialized)
        self.assertNotIn("Filler",serialized)

    def test_class_confounded_going_is_not_strictly_identifiable(self):
        def request(op,params):
            return fake_req(op,params,class_confounded=True)
        out=comparison(soap=request,gps=gps_fake)
        s=out["within_horse_support"]
        self.assertEqual(s["recurrent_ids_with_both_Good_and_non_Good"],2)
        self.assertEqual(
            s["strict_horse_ID_matching_official_distance_first_section_marker_and_race_class"],0)
        self.assertEqual(s["strict_strata_with_at_least_two_good_AND_two_wet_starts"],0)
        self.assertEqual(
            s["horse_ID_with_Good_nonGood_at_same_race_distance_and_first_section_marker"],2)

    def test_same_day_duplicate_gps_name_blocks_repeated_identity(self):
        def gps(src):
            return gps_fake(src,duplicate_same_day=True)
        out=comparison(soap=fake_req,gps=gps)
        self.assertGreater(
            out["per_date"]["2026-05-15"]["candidate_rows_with_same_day_duplicate_gps_name"],0)
        self.assertEqual(out["within_horse_support"]["recurrent_ids_with_both_Good_and_non_Good"],1)

    def test_declining_unapproved_dates_and_missing_races(self):
        with self.assertRaisesRegex(ValueError,"HOLD_DAY_NOT_IN_LOCKED"):
            audit_one_day("2023-05-01",soap=fake_req,gps=gps_fake)
        root=parse_xml(b"<Races><Race Id='9'><RaceNumber>7</RaceNumber></Race></Races>")
        with self.assertRaisesRegex(ValueError,"HOLD_NO_OFFICIAL_SELECTED_RACES"):
            selected_official_races(root,(1,2,3,8))
        root=parse_xml(b"<Races><Race Id='9'><RaceNumber>1</RaceNumber>"
                       b"<TrackRating>Soft 5</TrackRating></Race></Races>")
        d,n=selected_official_races(root,(1,2,3,8))
        self.assertEqual(set(d),{1})
        self.assertEqual(d[1]["ground"],"Soft")

    def test_going_not_treated_as_equally_spaced_numeric(self):
        self.assertEqual(ground_class("Heavy 9"),"Heavy")
        self.assertEqual(ground_class("Soft 6"),"Soft")
        self.assertEqual(ground_class("Good"),"Good")
        self.assertEqual(ground_class("Not-available"),"UNKNOWN")

    def test_first_segment_duration_is_not_the_entire_race(self):
        raw,_=gps_fake("20260515-cairns")
        d=first_section_table(raw,"2026-05-15")
        self.assertTrue(d[(1,"stablea")]["early_section_observed"])
        self.assertEqual(d[(1,"stablea")]["first_marker_m"],150)
        self.assertAlmostEqual(d[(1,"stablea")]["first_section_seconds"],10.20)


if __name__=="__main__":
    unittest.main()
