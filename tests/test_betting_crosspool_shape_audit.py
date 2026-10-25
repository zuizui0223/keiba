"""Synthetic-only invariants for pre-race cross-pool market audit."""
import copy
from datetime import datetime, timedelta, timezone
import math
from itertools import combinations, permutations
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from betting_crosspool_shape_audit import (
    exact_pl, parse_snapshot, portfolio, sensitivity, ticket_hit, wide_market_shape
)

T = timezone(timedelta(hours=9))

def fake(n=5, tilted=True):
    names=list(range(1,n+1))
    horses={i:float(2+i) for i in names}
    m=exact_pl(horses,1)
    win=[{"number":i,"odds":horses[i]} for i in names]
    # Make the WIDE relative price proportional to a valid model pair index.
    wide=[{"numbers":list(pair),"odds_low":float(4/(m["wide"][pair]/3)),
           "odds_high":float(4/(m["wide"][pair]/3))+1}
          for pair in combinations(names,2)]
    if tilted:
        wide[0]["odds_low"]*=1.21
        wide[0]["odds_high"]*=1.21
    quin=[{"numbers":list(pair),"odds":float(3/m["quinella"][pair])}
          for pair in combinations(names,2)]
    trio=[{"numbers":list(triple),"odds":float(2/m["trio"][triple])}
          for triple in combinations(names,3)]
    groups={"win":win,"wide":wide,"quinella":quin,"trio":trio}
    return {"race_id":"SYNTHETIC-HOLD-TEST",
      "scheduled_post_jst":"2026-10-25T15:40:00+09:00",
      "markets":{kind:{"provider_url":"https://example.test/fiction",
                 "source_updated_at_jst":"2026-10-25T01:00:00+09:00",
                 "rows":v} for kind,v in groups.items()}}

class TestCrossPool(unittest.TestCase):
    def test_exact_probabilities_and_mass(self):
        m=exact_pl({i:float(i+2) for i in range(1,6)}, 1.0)
        self.assertEqual(len(m["ordered"]),60)
        self.assertAlmostEqual(sum(m["win"].values()),1)
        self.assertAlmostEqual(sum(m["top3"].values()),3)
        self.assertAlmostEqual(sum(m["wide"].values()),3)
        self.assertAlmostEqual(sum(m["quinella"].values()),1)
        self.assertAlmostEqual(sum(m["trio"].values()),1)

    def test_uniform_equivalence(self):
        m=exact_pl({i:5.0 for i in range(1,6)}, 1.0)
        self.assertAlmostEqual(m["win"][1],.2)
        self.assertAlmostEqual(m["top3"][1],.6)
        self.assertAlmostEqual(m["wide"][(1,2)],.3)
        self.assertAlmostEqual(m["quinella"][(1,2)],.1)
        self.assertAlmostEqual(m["trio"][(1,2,3)],.1)

    def test_permuted_horses_do_not_change_mass(self):
        a=exact_pl({1:2.0,2:4.0,3:8.0,4:16.0},1)
        b=exact_pl({14:16.0,13:8.0,12:4.0,11:2.0},1)
        self.assertAlmostEqual(a["win"][1],b["win"][11])
        self.assertAlmostEqual(a["wide"][(1,2)],b["wide"][(11,12)])
        self.assertAlmostEqual(a["trio"][(1,2,3)],b["trio"][(11,12,13)])

    def test_market_shape_exact_reference_without_tilt(self):
        x=parse_snapshot(fake(n=5,tilted=False))
        m=exact_pl(x["horses"],1)
        s=wide_market_shape(x,m)
        self.assertAlmostEqual(s["total_variation_between_relative_indices"],0,places=12)
        self.assertAlmostEqual(s["spearman_pair_rank"],1,places=12)

    def test_shape_with_one_pair_perturbation(self):
        x=parse_snapshot(fake(n=5,tilted=True))
        m=exact_pl(x["horses"],1)
        s=wide_market_shape(x,m)
        self.assertGreater(s["total_variation_between_relative_indices"],0)
        self.assertGreaterEqual(s["additive_horse_node_r2_descriptive"],0)
        self.assertLessEqual(s["additive_horse_node_r2_descriptive"],1)

    def test_unnamed_invalid_sources_blocked(self):
        for mutation in ("naive_time","after_post","missing_pair","dup_runner",
                         "dup_pair","bad_quote","missing_provenance","stale_top3"):
            doc=fake()
            if mutation=="naive_time":doc["markets"]["win"]["source_updated_at_jst"]="2026-10-25T01:00:00"
            if mutation=="after_post":doc["markets"]["win"]["source_updated_at_jst"]="2026-10-25T15:39:00+09:00"
            if mutation=="missing_pair":doc["markets"]["wide"]["rows"].pop()
            if mutation=="dup_runner":doc["markets"]["win"]["rows"][0]["number"]=2
            if mutation=="dup_pair":doc["markets"]["wide"]["rows"][0]["numbers"]=[1,3]
            if mutation=="bad_quote":doc["markets"]["wide"]["rows"][0]["odds_low"]=0
            if mutation=="missing_provenance":doc["markets"]["quinella"]["provider_url"]=""
            if mutation=="stale_top3":doc["markets"]["trio"]["rows"][0]["numbers"]=[1,1,2]
            with self.subTest(mutation=mutation):
                with self.assertRaises((ValueError,KeyError)):
                    parse_snapshot(doc)

    def test_nested_trio_cannot_expand_wide_anyhit(self):
        snapshot=parse_snapshot(fake(n=5))
        model=exact_pl(snapshot["horses"],1)
        a=[{"kind":"wide","numbers":[1,2],"yen":300}]
        b=[{"kind":"wide","numbers":[1,2],"yen":100},
           {"kind":"trio","numbers":[1,2,3],"yen":100},
           {"kind":"trio","numbers":[1,2,4],"yen":100}]
        x=portfolio(snapshot,model,a)
        y=portfolio(snapshot,model,b)
        self.assertAlmostEqual(x["model_prob_any_payout"],y["model_prob_any_payout"])

    def test_total_portfolio_return_linearity(self):
        snapshot=parse_snapshot(fake(n=5))
        model=exact_pl(snapshot["horses"],1)
        single=portfolio(snapshot,model,[{"kind":"wide","numbers":[1,2],"yen":300}])
        p=model["wide"][(1,2)]
        self.assertAlmostEqual(single["gross_multiplier_under_fixed_quote"],
                               p*snapshot["quotes"]["wide"][(1,2)][0])

    def test_trio_may_be_partial_but_cannot_be_empty(self):
        x=fake()
        x["markets"]["trio"]["rows"]=x["markets"]["trio"]["rows"][:4]
        snap=parse_snapshot(x)
        self.assertEqual(len(snap["quotes"]["trio"]),4)
        x["markets"]["trio"]["rows"]=[]
        with self.assertRaises(ValueError):parse_snapshot(x)

    def test_model_does_not_read_outcomes(self):
        x=fake()
        x["outcome_top3"]=[1,2,3]
        result=sensitivity(x,[0.75,1.0,1.25])
        self.assertEqual(result["status"],"PRE_RACE_EXPLORATORY_MARKET_ONLY_NOT_PROBABILITY_CALIBRATED")
        self.assertEqual(result["model_outcome_count"],60)
        self.assertEqual(result["quoted_pairs_full"],10)
        self.assertFalse(any("outcome_top3" in str(v) for v in result.values()))

    def test_complete_18_horse_space(self):
        d=fake(n=18)
        snap=parse_snapshot(d)
        self.assertEqual(len(snap["quotes"]["wide"]),153)
        self.assertEqual(len(snap["quotes"]["quinella"]),153)
        self.assertEqual(len(snap["quotes"]["trio"]),816)
        m=exact_pl(snap["horses"],1)
        self.assertEqual(len(m["ordered"]),4896)
        self.assertAlmostEqual(sum(m["wide"].values()),3.0)

    def test_exact_additive_node_fit(self):
        d=fake(n=6,tilted=False)
        x=parse_snapshot(d)
        model=exact_pl(x["horses"],1)
        weights={1:0.4,2:-0.2,3:0.0,4:0.2,5:-0.1,6:-0.3}
        for row in d["markets"]["wide"]["rows"]:
            i,j=row["numbers"]
            q=model["wide"][(i,j)]/3 * math.exp(weights[i]+weights[j])
            row["odds_low"]=2/q
            row["odds_high"]=row["odds_low"]*1.10
        s=wide_market_shape(parse_snapshot(d),model)
        self.assertAlmostEqual(s["additive_horse_node_r2_descriptive"],1,places=11)

    def test_invalid_plan_ticket_rejected(self):
        snap=parse_snapshot(fake())
        mod=exact_pl(snap["horses"],1)
        with self.assertRaises(ValueError):
            portfolio(snap,mod,[{"kind":"wide","numbers":[1,3],"yen":50}])

if __name__=="__main__":unittest.main()
