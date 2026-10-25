"""Artificial-input tests for exact pre-start PL rate-box envelope; no race outcomes."""
import copy
from itertools import combinations, permutations, product
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from betting_rate_box_envelope import validate_inputs, _p, envelope, audit


def fixture():
    odds = {1:2.8,2:3.5,3:7.1,4:12.9,5:23.7}
    win = {
        "race_id":"SYNTHETIC-DO-NOT-BET",
        "scheduled_post_jst":"2026-10-25T15:40:00+09:00",
        "source_updated_at_jst":"2026-10-25T09:30:00+09:00",
        "source_url":"https://example.org/fake",
        "runner_count":5,
        "horses":[{"number":n,"win_odds":o} for n,o in odds.items()]
    }
    prices = {
        "race_id":win["race_id"],
        "source_times_jst":{"win":"09:30","wide":"09:25","quinella":"09:20","trio":"09:22"},
        "key_tickets":[
          {"ticket_kind":"wide","members":[1,2],"low":2.8,"high":3.1},
          {"ticket_kind":"quinella","members":[1,2],"low":4.3,"high":4.3},
          {"ticket_kind":"trio","members":[1,2,3],"low":13.5,"high":13.5}
        ]
    }
    return win,prices,odds


def manual_event(weights, kind, selected):
    # Independent rank-order expansion, not calling production exact_pl.
    total=sum(weights.values())
    ans=0.
    for a,b,c in permutations(weights,3):
        pr=(weights[a]/total
            *weights[b]/(total-weights[a])
            *weights[c]/(total-weights[a]-weights[b]))
        if kind=="trio":
            hit=set((a,b,c))==set(selected)
        elif kind=="quinella":
            hit=set((a,b))==set(selected)
        elif kind=="wide":
            hit=set(selected).issubset((a,b,c))
        else:
            raise ValueError(kind)
        if hit:
            ans+=pr
    return ans


class TestPLBox(unittest.TestCase):
    def test_exact_vs_independently_enumerated_pl(self):
        win,prices,odds=fixture()
        for kind,selected in (("wide",(1,3)),("quinella",(1,3)),
                              ("trio",(1,3,5))):
            for gamma in (0.75,1.,1.25):
                for delta in (0.,0.1,0.2):
                    for side in ("min","base","max"):
                        rates={}
                        for h,od in odds.items():
                            factor=(1 if side=="base" else
                                1-delta if (side=="min") == (h in selected) else 1+delta)
                            rates[h]=od**(-gamma)*factor
                        actual=manual_event(rates,kind,selected)
                        predicted=_p(odds,kind,selected,gamma,delta,side)
                        self.assertAlmostEqual(predicted,actual,places=11)

    def test_global_box_corners_exhaustively(self):
        win,prices,odds=fixture()
        for kind,selected in (("wide",(1,3)),("quinella",(1,3)),
                              ("trio",(1,3,5))):
            delta=.2
            extreme_min=_p(odds,kind,selected,1.,delta,"min")
            extreme_max=_p(odds,kind,selected,1.,delta,"max")
            for factors in product((1-delta,1+delta),repeat=len(odds)):
                rates={k:odds[k]**-1*f for k,f in zip(odds,factors)}
                intermediate=manual_event(rates,kind,selected)
                self.assertLessEqual(extreme_min-1e-11,intermediate)
                self.assertLessEqual(intermediate,extreme_max+1e-11)

    def test_label_permutation_invariance(self):
        _,_,odds=fixture()
        remap={1:20,2:14,3:7,4:8,5:2}
        mapped={remap[k]:v for k,v in odds.items()}
        for kind,selected in (("wide",(1,3)),("quinella",(1,3)),("trio",(1,3,5))):
            mapped_selected=tuple(remap[h] for h in selected)
            for case in ("min","base","max"):
                a=_p(odds,kind,selected,1.25,.2,case)
                b=_p(mapped,kind,mapped_selected,1.25,.2,case)
                self.assertAlmostEqual(a,b,places=11)

    def test_envelope_has_ordered_bounds(self):
        win,prices,odds=fixture()
        for ticket in prices["key_tickets"]:
            report=envelope(odds,ticket,(0.75,1.,1.25),.2)
            self.assertLessEqual(report["min_model_gross_multiplier"],
                                 report["max_model_gross_multiplier"])
            for v in report["by_gamma"].values():
                self.assertLessEqual(v["probability_low"],v["probability_baseline"])
                self.assertLessEqual(v["probability_baseline"],v["probability_high"])

    def test_input_guards(self):
        changes={
            "missing_url":lambda w,p: w.update(source_url="http://bad.test/"),
            "date_after_start":lambda w,p:w.update(source_updated_at_jst="2026-10-25T15:39:00+09:00"),
            "timezone_missing":lambda w,p:w.update(source_updated_at_jst="2026-10-25T09:30:00"),
            "roster_incomplete":lambda w,p:w["horses"].pop(),
            "duplicate":lambda w,p:w["horses"][0].update(number=2),
            "changed_id":lambda w,p:p.update(race_id="CHANGED"),
            "repeated_ticket_horse":lambda w,p:p["key_tickets"][0].update(members=[1,1]),
            "invalid_odds":lambda w,p:w["horses"][0].update(win_odds=float("nan")),
            "negative_quote":lambda w,p:p["key_tickets"][0].update(low=-2.),
            "bad_kind":lambda w,p:p["key_tickets"][0].update(ticket_kind="slot")
        }
        for name,edit in changes.items():
            w,p,_=fixture()
            edit(w,p)
            with self.subTest(name=name),self.assertRaises((ValueError,KeyError,TypeError)):
                validate_inputs(w,p)

    def test_does_not_use_future_outcome(self):
        win,prices,_=fixture()
        a=audit(win,prices)
        win["official_result_after_start"]=[1,2,3]
        prices["winner"]=1
        b=audit(win,prices)
        self.assertEqual(a,b)
        self.assertEqual(a["runner_count"],5)
        self.assertEqual(len(a["tickets"]),3)
        self.assertNotIn("official_result",str(a))

    def test_changes_in_payout_do_not_change_probability(self):
        win,p,_=fixture()
        a=audit(win,p)
        p2=copy.deepcopy(p)
        p2["key_tickets"][0]["low"]*=1.05
        b=audit(win,p2)
        arow=a["tickets"][0]["scenario_by_rate_spread"]["0.1"]["by_gamma"]["1"]
        brow=b["tickets"][0]["scenario_by_rate_spread"]["0.1"]["by_gamma"]["1"]
        self.assertAlmostEqual(arow["probability_low"],brow["probability_low"])
        self.assertNotAlmostEqual(arow["p_times_intermediate_quote_low"],
                                  brow["p_times_intermediate_quote_low"])

if __name__=="__main__":
    unittest.main()
