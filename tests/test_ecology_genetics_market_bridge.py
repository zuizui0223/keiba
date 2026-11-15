"""No live or real horse genomic / odds observations: synthetic source-guard tests."""
from __future__ import annotations

from datetime import date,timedelta
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_genetics_market_bridge import (
    _softmax, build_races, score, source_snapshot_readiness
)


def fixture(n_days=14, genotype=False):
    cards=[]
    quotes=[]
    for day in range(n_days):
        d=(date(2026,9,1)+timedelta(days=day)).isoformat()
        r_id=f"FICTIONAL-R-{day:02}"
        t0=d+"T10:00:00+09:00"
        t1=d+"T12:00:00+09:00"
        t2=d+"T13:00:00+09:00"
        start=d+"T14:00:00+09:00"
        k=[-1.,0.,1.]
        q0=_softmax([0.5*x for x in k])
        qm=q0  # No pre-terminal momentum, ONLY valid kin movement.
        qlast=_softmax([math.log(p)+0.5*x for p,x in zip(qm,k)])
        for i in range(3):
            horse=f"FAKE-{day}-{i}"
            card={
                "race_id":r_id,"horse_id":horse,"start_at":start,
                "feature_known_at":d+"T08:00:00+09:00",
                "kin_signal":str(k[i]),"distance_m":"1600",
            }
            if genotype:
                card["mstn_genotype"]=("TT","CT","CC")[i]
                card["mstn_assay_verified"]="true"
                card["genotype_known_at"]=d+"T08:00:00+09:00"
            cards.append(card)
            for t,p in [(t0,q0[i]),(t1,qm[i]),(t2,qlast[i])]:
                quotes.append({
                    "race_id":r_id,"horse_id":horse,"quote_at":t,
                    "win_odds":str(1/p),
                    "source_quote_time_verified":"true",
                })
    return cards,quotes


class GeneticsMarketBridgeTests(unittest.TestCase):
    def test_real_snapshot_missing_stable_ids_and_quote_times_is_hold(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"example.json"
            p.write_text(json.dumps({
                "races":[{"race_id":"X",
                    "horses":[{"name":"FAKE","win_odds":4.0}]}]
            }),encoding="utf-8")
            a=source_snapshot_readiness(p)
        self.assertEqual(a["status"],
                         "HOLD_NO_ID_LINKED_CERTIFIED_TIME_SERIES_FOR_GENEALOGY_MARKET")
        self.assertEqual(a["stable_horse_ID_rows"],0)
        self.assertEqual(a["saved_horse_price_rows"],1)
        self.assertTrue(a["source_name_only_pairing_not_authorized"])

    def test_complete_synthetic_market_kin_transfers_to_unseen_dates(self):
        cards,quotes=fixture()
        races,qa=build_races(cards,quotes)
        self.assertEqual(len(races),14)
        self.assertEqual(qa["eligible_races"],14)
        outcome=score(races)
        self.assertEqual(outcome["status"],
                         "MARKET_SUPPORT_TIMESERIES_OUT_OF_DATE_SCORE_NOT_CAUSAL")
        self.assertLess(outcome["models"]["M_market_plus_kin"]["mean_race_share_RMSE"],
                        outcome["models"]["M_penultimate_market_persistence"]["mean_race_share_RMSE"])
        self.assertLess(outcome["models"]["M_initial_kin"]["mean_race_share_RMSE"],
                        outcome["models"]["M_initial_uniform"]["mean_race_share_RMSE"])
        self.assertEqual(outcome["genotype_channel"],
                         "HOLD_NO_VERIFIED_ID_LINKED_MSTN_COHORT")
        self.assertTrue(outcome["no_races_from_same_calendar_day_cross_train_test"])
        self.assertNotIn("FAKE-",str(outcome))

    def test_known_MSTN_requires_assay_and_full_race_coverage(self):
        cards,quotes=fixture(genotype=True)
        races,qa=build_races(cards,quotes)
        outcome=score(races)
        self.assertEqual(outcome["genotype_channel"],"MEASURED_MSTN_COHORT_ONLY")
        self.assertIn("M_market_kin_MSTN",outcome["models"])
        cards[0]["mstn_assay_verified"]="false"
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_MSTN"):
            build_races(cards,quotes)

    def test_uncertified_timestamp_and_future_kin_rejected(self):
        cards,quotes=fixture()
        quotes[0]["source_quote_time_verified"]="false"
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_SOURCE_QUOTE"):
            build_races(cards,quotes)
        cards,quotes=fixture()
        cards[0]["feature_known_at"]=quotes[0]["quote_at"]
        with self.assertRaisesRegex(ValueError,"FUTURE_FEATURE"):
            build_races(cards,quotes)
        cards,quotes=fixture()
        quotes[0]["quote_at"]=cards[0]["start_at"]
        with self.assertRaisesRegex(ValueError,"POSTTIME"):
            build_races(cards,quotes)

    def test_snapshot_roster_must_be_identical_across_times(self):
        cards,quotes=fixture()
        quotes.pop(0)
        with self.assertRaisesRegex(ValueError,"NOT_COMPLETE_SAME_FIELD"):
            build_races(cards,quotes)
        cards,quotes=fixture()
        quotes[0]["horse_id"]="UNLINKED"
        with self.assertRaisesRegex(ValueError,"NO_STABLE_PEDIGREE_LINK"):
            build_races(cards,quotes)

    def test_missing_quote_or_no_evaluable_market_returns_hold(self):
        cards,quotes=fixture(n_days=3)
        races,_=build_races(cards,quotes)
        self.assertEqual(score(races)["status"],"HOLD_TOO_FEW_DISTINCT_RACE_DATES")
        cards,quotes=fixture()
        quotes=[q for q in quotes if "T13:00" not in q["quote_at"]]
        races,qa=build_races(cards,quotes)
        self.assertEqual(len(races),0)
        self.assertEqual(qa["rejected_by_reason"]
                         ["HOLD_NO_THREE_CERTIFIED_PRE_START_SNAPSHOTS"],14)

    def test_genotype_assay_after_earliest_quote_never_retrospectively_filled(self):
        cards,quotes=fixture(genotype=True)
        cards[0]["genotype_known_at"]=cards[0]["start_at"].replace("T14:00","T11:00")
        with self.assertRaisesRegex(ValueError,"GENOTYPE_AFTER_FIRST"):
            build_races(cards,quotes)

    def test_outcomes_are_never_inputs_to_market_only_model(self):
        cards,quotes=fixture()
        r,_=build_races(cards,quotes)
        baseline=score(r)
        cards[0]["actual_winner"]=cards[0]["horse_id"]
        r2,_=build_races(cards,quotes)
        self.assertEqual(baseline["models"],score(r2)["models"])

if __name__=="__main__":
    unittest.main()
