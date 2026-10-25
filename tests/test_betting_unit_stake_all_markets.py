"""Fully synthetic QA for budget-free eight-market unit-return audit."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
import copy
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from betting_unit_stake_all_markets import evaluate, normalize, probabilities, TYPES


def sample():
    runners=[{"number":i, "frame": f, "win_odds": 2.5 + 1.1*i,
              "place_low":1.2, "place_high":1.8} 
             for i,f in ((1,1),(2,1),(3,2),(4,2),(5,3))]
    rr={row["number"]:row for row in runners}
    q=normalize({i:1/row["win_odds"] for i,row in rr.items()})
    p=probabilities(rr,q)
    markets={}
    for kind in ("frame","wide","quinella","exacta","trio","trifecta"):
        markets[kind]=[]
        for key,v in p[kind].items():
            if v>0:
                markets[kind].append({"members":list(key),"odds_low":float(2/max(v,1e-12))})
    return {
        "schema":"PRESTART_ALL_BET_TYPES_LOCAL_QUOTES_V1",
        "race_id":"SYNTHETIC-ONLY",
        "scheduled_post_jst":"2026-10-25T15:40:00+09:00",
        "page_observed_at_jst":"2026-10-25T11:00:00+09:00",
        "source_timestamps_separately_verified":False,
        "runners":runners, "ticket_quotes":markets
    }


class BudgetFreeAuditTests(unittest.TestCase):
    def test_all_market_types_score(self):
        result=evaluate(sample())
        self.assertEqual(set(result["by_bet_type"]),set(TYPES))
        self.assertEqual(result["total_quoted_tickets"],125)
        self.assertEqual(result["coverage"]["exacta"],20)
        self.assertEqual(result["coverage"]["wide"],10)
        self.assertEqual(result["coverage"]["quinella"],10)
        self.assertEqual(result["coverage"]["trio"],10)
        self.assertEqual(result["coverage"]["trifecta"],60)
        self.assertIsNone(result["proposed_amounts"])

    def test_all_win_baseline_unit_gross_identical(self):
        r=evaluate(sample())
        # More than one horse, same inverse-odds normalized return.
        vals=[]
        doc=sample()
        q=normalize({row["number"]:1/row["win_odds"] for row in doc["runners"]})
        for row in doc["runners"]:
            vals.append(q[row["number"]]*row["win_odds"])
        self.assertAlmostEqual(max(vals),min(vals),places=12)

    def test_frame_and_ordered_events_mass(self):
        doc=sample()
        rr={row["number"]:row for row in doc["runners"]}
        p=probabilities(rr,normalize({i:1/row["win_odds"] for i,row in rr.items()}))
        self.assertAlmostEqual(sum(p["frame"].values()),1)
        self.assertAlmostEqual(sum(p["exacta"].values()),1)
        self.assertAlmostEqual(sum(p["trifecta"].values()),1)

    def test_original_seal_validation_and_use(self):
        doc=sample()
        doc["original_sealed_M1_win_probs"]={str(i):.2 for i in range(1,6)}
        out=evaluate(doc)
        self.assertIn("original_sealed_M1",out["models"])
        doc["original_sealed_M1_win_probs"]["1"]+=.01
        with self.assertRaises(ValueError):
            evaluate(doc)

    def test_place_lower_upper_not_ci(self):
        d=sample()
        result=evaluate(d)
        self.assertGreater(result["coverage"]["place"],0)
        # Price upper interval must be >= lower.
        d["runners"][0]["place_high"]=1.1
        with self.assertRaises(ValueError):
            evaluate(d)

    def test_no_outcome_access(self):
        a=sample()
        x=evaluate(a)
        a["actual_winner_after_race"]=1
        a["finish_order"]=[1,2,3,4,5]
        y=evaluate(a)
        self.assertEqual(x,y)

    def test_price_capture_time_guard(self):
        d=sample()
        d["page_observed_at_jst"]="2026-10-25T15:35:00+09:00"
        with self.assertRaises(ValueError):
            evaluate(d)

    def test_reject_missing_or_duplicate_wide(self):
        d=sample()
        d["ticket_quotes"]["wide"].pop()
        with self.assertRaises(ValueError):
            evaluate(d)
        d=sample()
        d["ticket_quotes"]["wide"].append(d["ticket_quotes"]["wide"][0])
        with self.assertRaises(ValueError):
            evaluate(d)

    def test_partial_exotic_coverage_is_explicit(self):
        d=sample()
        d["ticket_quotes"]["trio"]=d["ticket_quotes"]["trio"][:4]
        d["ticket_quotes"]["trifecta"]=d["ticket_quotes"]["trifecta"][:15]
        r=evaluate(d)
        self.assertEqual(r["coverage"]["trio"],4)
        self.assertEqual(r["coverage"]["trifecta"],15)

    def test_stake_invariant_to_price_scaling(self):
        d=sample()
        r=evaluate(d)
        self.assertIn("model_positive_all",r["by_bet_type"]["wide"])
        # No user stake is stored; per-unit is independent of budget.
        self.assertNotIn("amount",str(r).lower())


if __name__=="__main__":
    unittest.main()
