"""Synthetic tests for strict two-date gamma fitting. Never uses target race outcomes."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from betting_gamma_date_blocked import (
    GRID, STATUS, make_record, score_record, summarize, select_gamma, audit,
    source_json
)


def fictional_races():
    out=[]
    for day,count in (("2026-10-12",5),("2026-10-18",9)):
        for j in range(count):
            runners=[(i,2.0+0.7*i) for i in range(1,9)]
            winner=((j+2)%8)+1
            podium=[winner, ((winner+1)%8)+1,((winner+2)%8)+1]
            out.append(make_record(
                day,day+"-"+str(j),runners,podium,day+"T11:00:00+09:00"))
    return out


class GammaResearchTests(unittest.TestCase):
    def test_fixed_design_is_from_two_dates(self):
        self.assertEqual(len(GRID),37)
        self.assertAlmostEqual(GRID[0],0.5)
        self.assertAlmostEqual(GRID[-1],2.3)
        rows=fictional_races()
        self.assertEqual(len(rows),14)
        self.assertEqual({r["date"] for r in rows},{"2026-10-12","2026-10-18"})

    def test_winner_logloss_and_top3_calculation(self):
        r=make_record("2026-10-12","fake",
                      [(1,5.0),(2,5.0),(3,5.0),(4,5.0),(5,5.0)],
                      [1,2,3],"2026-10-12T10:00:00+09:00")
        s=score_record(r,1)
        self.assertAlmostEqual(s["winner_predicted_probability"],0.2)
        self.assertAlmostEqual(s["win_log_loss"],1.6094379124341)
        self.assertAlmostEqual(s["top3_brier_mean_horse"],0.24)

    def test_horse_label_permutation_invariance(self):
        r=fictional_races()[0]
        r2=copy.deepcopy(r)
        ren={i:i+100 for i in r["numbers"]}
        r2["numbers"]=[ren[i] for i in r["numbers"]]
        r2["top3"]=[ren[i] for i in r["top3"]]
        for gamma in (0.5,1,1.85,2.3):
            self.assertEqual(score_record(r,gamma),score_record(r2,gamma))

    def test_gamma_selection_uses_training_only(self):
        allr=fictional_races()
        original=audit(allr)
        modified=copy.deepcopy(allr)
        for r in modified:
            if r["date"]=="2026-10-18":
                r["top3"]=list(reversed(r["top3"]))
        new=audit(modified)
        self.assertEqual(original["training_winner_model"],new["training_winner_model"])
        self.assertEqual(original["training_top3_model"],new["training_top3_model"])
        self.assertEqual(original["n_independent_meeting_dates"],2)
        self.assertEqual(original["status"],STATUS)

    def test_today_outcome_data_is_not_part_of_this_pipeline(self):
        r=fictional_races()
        with self.assertRaises(ValueError):
            make_record("2026-10-25","today",[(i,2+i) for i in range(1,8)],
                        [1,2,3],"2026-10-25T13:00:00+09:00")

    def test_missing_past_data_or_duplicate_horse_rejected(self):
        rows=fictional_races()
        with self.assertRaises(ValueError):
            audit(rows[:13])
        with self.assertRaises(ValueError):
            make_record("2026-10-18","bad",[(1,4.1),(1,5.3),(2,6),(3,7),(4,8)],
                        [1,2,3],"2026-10-18T10:00:00+09:00")
        with self.assertRaises(ValueError):
            make_record("2026-10-18","bad",[(i,2+i) for i in range(1,8)],
                        [1,1,3],"2026-10-18T10:00:00+09:00")

    def test_hash_pin_fails_on_mutation(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            f=Path(directory)/"a.json"
            f.write_text('{"frozen":true}',encoding="utf-8")
            blob=f.read_bytes()
            expected=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
            self.assertEqual(source_json(f,expected),{"frozen":True})
            f.write_text('{"frozen":false}',encoding="utf-8")
            with self.assertRaises(ValueError):
                source_json(f,expected)

    def test_scores_not_probabilities_sold_as_returns(self):
        x=audit(fictional_races())
        self.assertTrue(x["refit_on_all_14_past_races_for_new_20261025_shadow"]["not_a_calibrated_probability_model"])
        self.assertIn("no real money",str(x).lower())
        self.assertNotIn("stake_optimum",x)
        self.assertEqual(len(x["historical_validation_race_deltas"]),9)


if __name__=="__main__":
    unittest.main()
