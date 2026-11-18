"""Test market HHI and source time/ID guards; original market source is not genetic data."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_market_snapshot_structure import market_state,audit_snapshot,LOCKED_SOURCE_SHA

ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/"data/2026-10-18/ticket-odds-snapshot.json"

def fixture():
    return {"races":[
        {"race_id":"FAKE-01","venue":"TEST","race":1,
         "runner_count":3,"win_place_upstream_updated_at":None,
         "horses":[
           {"number":1,"name":"FAKE-A","win_odds":2},
           {"number":2,"name":"FAKE-B","win_odds":4},
           {"number":3,"name":"FAKE-C","win_odds":4},
         ]}]}

def write(tmp,data):
    p=Path(tmp)/"market.json"
    p.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    return p


class RealSnapshotMarketStructure(unittest.TestCase):
    def test_equal_inverse_odds_three_horses(self):
        h=[{"number":i,"win_odds":4.0} for i in (1,2,3)]
        m=market_state(h)
        self.assertAlmostEqual(m["relative_support_favorite"],1/3)
        self.assertAlmostEqual(m["effective_horses_simpson"],3.0)
        self.assertAlmostEqual(m["reciprocal_odds_sum"],.75)
        self.assertTrue(m["single_snapshot_only"])

    def test_unequal_inverse_odds_and_effective_field(self):
        m=market_state(fixture()["races"][0]["horses"])
        self.assertAlmostEqual(m["relative_support_favorite"],.5)
        self.assertAlmostEqual(m["relative_support_top3"],1.0)
        self.assertAlmostEqual(m["effective_horses_simpson"],8/3)

    def test_known_saved_real_source_has_nine_complete_price_rosters(self):
        s=audit_snapshot(SNAP)
        self.assertEqual(s["status"],
                         "OBSERVED_SINGLE_SNAPSHOT_MARKET_CONCENTRATION_NOT_GENETICS")
        self.assertEqual(s["data_quality"]["source_sha256"],LOCKED_SOURCE_SHA)
        self.assertEqual(s["data_quality"]["races"],9)
        self.assertEqual(s["data_quality"]["horse_price_rows"],117)
        self.assertEqual(s["data_quality"]["total_canonical_horse_ID_rows"],0)
        self.assertEqual(s["data_quality"]["total_meisho_named_horses"],0)
        self.assertFalse(s["genetic_market_effect_estimated"])
        self.assertFalse(s["herding_time_series_observed"])
        self.assertTrue(all(v["effective_horses_simpson"]<=v["horse_count"]+1e-10
                            for v in s["markets"]))

    def test_sha_change_does_not_accept_new_source_by_accident(self):
        with tempfile.TemporaryDirectory() as t:
            p=write(t,fixture())
            j=audit_snapshot(p)
            self.assertEqual(j["status"],"HOLD_SNAPSHOT_SHA_CHANGED")
            self.assertNotIn("markets",j)

    def test_nonidentical_roster_or_bad_odds_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            d=fixture()
            d["races"][0]["runner_count"]=4
            with self.assertRaisesRegex(ValueError,"INCOMPLETE_OR_INCONSISTENT_ROSTER"):
                audit_snapshot(write(t,d),require_sha=None)
            d=fixture()
            d["races"][0]["horses"][0]["win_odds"]=-1
            with self.assertRaisesRegex(ValueError,"INVALID_ODDS"):
                audit_snapshot(write(t,d),require_sha=None)

    def test_race_quote_update_does_not_fake_actual_time_series(self):
        with tempfile.TemporaryDirectory() as t:
            d=fixture()
            d["races"][0]["win_place_upstream_updated_at"]="2026-09-01T12:00:00+09:00"
            with self.assertRaisesRegex(ValueError,"UPSTREAM_TIMES_ABSENT"):
                audit_snapshot(write(t,d),require_sha=None)

    def test_separate_source_initial_share_vector_is_normalized(self):
        s,initial=audit_snapshot(SAP:=SNAP,include_share_vector=True)
        self.assertEqual(len(initial),9)
        self.assertEqual({x["race_id"] for x in initial},
                         {x["race_id"] for x in s["markets"]})
        for r in initial:
            self.assertAlmostEqual(sum(r["initial_relative_support"]),1.0)
            self.assertEqual(len(r["initial_relative_support"]),r["n"])

if __name__=="__main__":
    unittest.main()
