"""Only fictional horse-ID cross-venue fixtures; never real animal identities."""
from __future__ import annotations

import json
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_rq_cannon_eagle_id_overlap import support,collect_cannon
from ecology_rq_2026_calendar_overlap import COHORT as CANNON_COHORT
from ecology_rq_eagle_farm_external_icc import DATES as EAGLE_DATES


def row(hid,name,day,marker=150.,distance="1200 metres",
        race_class="Class 1",race_no=1):
    return {
        "horse_id":hid,"horse_name":name,"day":day,
        "race_number":race_no,"first_marker_m":marker,
        "first_section_sec":10.54,
        "distance":distance,"class":race_class,"ground":"Good",
        "weight_kg":58., "jockey_license_id":"100","trainer_license_id":"201"
    }


class CrossVenueIdentitySupportTests(unittest.TestCase):
    def test_lock_reuses_two_already_frozen_venue_date_sets(self):
        self.assertEqual(len(CANNON_COHORT),12)
        self.assertEqual(len(EAGLE_DATES),12)
        self.assertEqual(CANNON_COHORT["2026-10-11"][1],"20261011-cairns")
        self.assertIn("2026-10-10",EAGLE_DATES)

    def test_matching_ID_is_not_automatically_comparable_initial_segment(self):
        c=[
            row("H1","repeat1","2026-05-15",marker=150.),
            row("H1","repeat1","2026-10-11",marker=150.),
            row("H2","repeat2","2026-05-29",marker=250.),
            row("H3","repeat3","2026-08-22",marker=150.),
            row("H4","repeat4","2026-08-29",marker=150.),
            row("C_ONLY","c","2026-04-09"),
        ]
        e=[
            row("H1","repeat1","2026-02-14",marker=150.),
            row("H1","repeat1","2026-10-03",marker=150.),
            row("H2","repeat2","2026-09-19",marker=200.),
            row("H3","CHANGED-NAME","2026-10-10",marker=150.),
            row("H4","repeat4","2026-08-29",marker=150.),
            row("E_ONLY","e","2026-06-13",marker=200.),
        ]
        s=support(c,e)
        self.assertEqual(s["numeric_original_HORSES_IDs_in_BOTH_venues_before_conflict_blocks"],4)
        self.assertEqual(s["original_HORSES_IDs_with_changed_name_across_venues_or_dates_BLOCKED"],1)
        self.assertEqual(s["original_HORSES_IDs_appearing_at_both_venues_on_same_date_BLOCKED"],1)
        self.assertEqual(s["distinct_same_name_safe_original_HORSES_IDs_observed_at_both_venues"],2)
        self.assertEqual(s["BOTH_venues_with_2plus_independent_dates_in_each"],1)
        self.assertEqual(s["BOTH_venues_with_1plus_identical_first_marker"],1)
        self.assertEqual(s["BOTH_venues_with_1plus_identical_marker_AND_official_distance"],1)
        self.assertEqual(s["BOTH_venues_with_1plus_identical_marker_distance_AND_official_class"],1)
        self.assertIn("AT_LEAST_ONE_MATCHED_SOURCE",s["scientific_decision"])
        self.assertFalse(s["shared_IDs_truly_confirmed_starters_or_finishers"])
        self.assertFalse(s["no_cross_site_behavioral_coefficient_fitted"] is False)
        blob=json.dumps(s)
        for ident in ("repeat1","repeat2","H1","H2","CHANGED-NAME"):
            self.assertNotIn('"'+ident+'"',blob)

    def test_shared_identity_without_matching_first_marker_is_hold(self):
        c=[row("A","a","2026-05-15",150.)]
        e=[row("A","a","2026-09-19",200.)]
        s=support(c,e)
        self.assertEqual(s["distinct_same_name_safe_original_HORSES_IDs_observed_at_both_venues"],1)
        self.assertEqual(s["BOTH_venues_with_1plus_identical_first_marker"],0)
        self.assertEqual(s["scientific_decision"],
                         "HOLD_NO_SAME_HORSE_IDENTICAL_MARKER_DISTANCE_CLASS_ACROSS_VENUES")
        self.assertFalse(s["no_confirmatory_p_value_or_genetic_or_adaptive_claim"] is False)

    def test_marker_matches_but_official_distance_or_class_differs(self):
        c=[row("X","x","2026-03-26",200.),
           row("Y","y","2026-03-26",200.)]
        e=[row("X","x","2026-08-29",200.,distance="1400 metres"),
           row("Y","y","2026-08-29",200.,race_class="Class 5")]
        s=support(c,e)
        self.assertEqual(s["BOTH_venues_with_1plus_identical_first_marker"],2)
        self.assertEqual(s["BOTH_venues_with_1plus_identical_marker_AND_official_distance"],1)
        self.assertEqual(s["BOTH_venues_with_1plus_identical_marker_distance_AND_official_class"],0)

    def test_reused_horse_ID_same_date_in_one_venue_is_blocked(self):
        c=[row("X","x","2026-08-29",150.,race_no=1),
           row("X","x","2026-08-29",150.,race_no=2)]
        with self.assertRaisesRegex(ValueError,"HOLD_CROSS_VENUE_DUPLICATE"):
            support(c,[])

    def test_unobserved_zero_first_section_is_never_assumed_absent_horse(self):
        c=[row("X","x","2026-08-29",150.)]
        c[0]["first_section_sec"]=0.
        with self.assertRaisesRegex(ValueError,"HOLD_CROSS_VENUE_GPS_UNOBSERVED"):
            support(c,[])

    def test_cannon_official_request_errors_are_HOLD_not_zero_population(self):
        def broken(op,params):
            raise TimeoutError("synthetic original SOAP timeout")
        rows,manifest=collect_cannon(soap=broken)
        self.assertEqual(rows,[])
        self.assertEqual(len(manifest),12)
        self.assertTrue(all(v["status"]=="HOLD_DATE_SOURCE_NOT_RECONCILED"
                            for v in manifest.values()))
        self.assertTrue(all(v["not_counted_as_zero_participation"]
                            for v in manifest.values()))


if __name__=="__main__":
    unittest.main()
