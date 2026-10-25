"""Synthetic no-result tests for privately reproducible gamma-shadow SHA."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from betting_gamma_shadow_preseal_20261025 import (
    build,canonical_bytes,exact_model,sha256,source_validation,GAMMA_WIN,GAMMA_TOP3
)


def fake():
    return {
      "schema":"KEIBA_KIKKA_LOCAL_PRICE_VECTOR_V1",
      "race_id":"2026-10-25-KYOTO-11",
      "source_url":"https://sports.yahoo.co.jp/keiba/race/odds/tfw/2608040911?ninki=1",
      "source_page_retrieved_at_jst":"2026-10-25T13:02:10+09:00",
      "provider_publication_clock_verified":False,
      "not_opening_or_final_odds":True,
      "runner_count":18,
      "odds_by_number":{str(i):2.0+.5*i for i in range(1,19)},
    }


class KikkaGammaShadowTests(unittest.TestCase):
    def test_all_18_and_816_outcome_mass(self):
        payload=build(fake())
        self.assertEqual(payload["chosen_gamma_win"],1.85)
        self.assertEqual(payload["chosen_gamma_top3"],1.7)
        for model in payload["scored_models"].values():
            self.assertEqual(len(model["win"]),18)
            self.assertEqual(len(model["top3"]),18)
            self.assertEqual(len(model["unordered_trio"]),816)
            self.assertAlmostEqual(sum(x["p"] for x in model["win"]),1)
            self.assertAlmostEqual(sum(x["p"] for x in model["top2"]),2)
            self.assertAlmostEqual(sum(x["p"] for x in model["top3"]),3)
            self.assertAlmostEqual(sum(x["p"] for x in model["unordered_trio"]),1)

    def test_digest_canonical(self):
        a={"x":1,"y":{"b":2,"a":3}}
        b={"y":{"a":3,"b":2},"x":1}
        self.assertEqual(canonical_bytes(a),canonical_bytes(b))
        self.assertEqual(sha256(a),sha256(b))
        self.assertEqual(sha256(build(fake())),sha256(build(fake())))
        self.assertEqual(len(sha256(build(fake()))),64)

    def test_source_quote_mutation_detectable_by_sha(self):
        a=fake()
        initial=sha256(build(a))
        b=copy.deepcopy(a)
        b["odds_by_number"]["8"]*=1.1
        self.assertNotEqual(initial,sha256(build(b)))

    def test_clock_must_precede_cutoff(self):
        for ts in ("2026-10-25T15:35:00+09:00","2026-10-25T13:02:10",
                   "2026-10-26T13:02:10+09:00"):
            x=fake()
            x["source_page_retrieved_at_jst"]=ts
            with self.subTest(ts=ts),self.assertRaises(ValueError):
                build(x)

    def test_reject_unverified_market_roster_and_price_changes(self):
        for mode in ("missing","bad_quote","wrong_race","wrong_link","purported_clock"):
            x=fake()
            if mode=="missing":del x["odds_by_number"]["18"]
            if mode=="bad_quote":x["odds_by_number"]["2"]=0
            if mode=="wrong_race":x["race_id"]="OTHER-RACE"
            if mode=="wrong_link":x["source_url"]="https://example.com"
            if mode=="purported_clock":x["provider_publication_clock_verified"]=True
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                build(x)

    def test_outcome_is_never_a_forecast_input(self):
        x=fake()
        x["winner"]=8
        with self.assertRaises(ValueError):
            build(x)
        x=fake()
        x["official_result"]=[8,10,2]
        with self.assertRaises(ValueError):
            build(x)

    def test_label_permutation_horse_odds(self):
        odds=source_validation(fake())
        shuffled={i:odds[19-i] for i in odds}
        p=exact_model(odds,1.85)
        q=exact_model(shuffled,1.85)
        # Opposite horse-label assignment preserves unordered trio mass.
        self.assertAlmostEqual(sum(x["p"] for x in p["unordered_trio"]),1)
        self.assertAlmostEqual(sum(x["p"] for x in q["unordered_trio"]),1)
        self.assertAlmostEqual(p["win"][0]["p"],q["win"][-1]["p"])


if __name__=="__main__":
    unittest.main()
