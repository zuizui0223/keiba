"""H2 competition-context tests on deliberately fictional changing-field races."""
import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ecology_panel import REQUIRED, audit, lagged_features, load_panel
from ecology_demo_competitors import fabricate_competition
from ecology_h2_pilot import (
    competition_frame, freeze_scaling, horse_context_support, run, split_dates,
)


def to_csv(folder, rows):
    output=Path(folder)/"FAKE-competition.csv"
    with output.open("w",encoding="utf-8",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(REQUIRED)+["first_call_position"])
        writer.writeheader()
        writer.writerows(rows)
    return output


class H2PilotTests(unittest.TestCase):
    def test_turnover_creates_within_horse_contexts(self):
        rows=fabricate_competition(n_days=65,n_horses=36,seed=512)
        with tempfile.TemporaryDirectory() as tmp:
            prepared=load_panel(to_csv(tmp,rows))
            enriched=lagged_features(prepared)
        diag=audit(prepared,enriched)
        self.assertEqual(diag["status"],"SYNTHETIC_ONLY")
        self.assertEqual(diag["unique_races"],65)
        self.assertGreater(diag["h2_horses_with_4plus_races_and_2plus_distinct_opponent_style_contexts"],15)
        frame=competition_frame(enriched)
        train,test,_=split_dates(frame)
        self.assertGreater(horse_context_support(train),8)
        self.assertLess(train["date"].max(),test["date"].min())

    def test_full_pre_race_coverage_required(self):
        rows=fabricate_competition(n_days=35,n_horses=24)
        with tempfile.TemporaryDirectory() as tmp:
            enriched=lagged_features(load_panel(to_csv(tmp,rows)))
        frame=competition_frame(enriched)
        race_id=frame["race_id"].iloc[-1]
        # Remove historical measurement on one eligible horse; whole race must go.
        tampered=[{**r} for r in enriched]
        for row in tampered:
            if row["race_id"]==race_id:
                row["prior_front_runner_score"]=None
                break
        modified=competition_frame(tampered)
        self.assertNotIn(race_id,set(modified["race_id"]))

    def test_training_centering_never_looks_at_test_dates(self):
        rows=fabricate_competition(n_days=45,n_horses=30)
        with tempfile.TemporaryDirectory() as tmp:
            enriched=lagged_features(load_panel(to_csv(tmp,rows)))
        df=competition_frame(enriched)
        tr,te,_=split_dates(df)
        original_tr, original_te, means=freeze_scaling(tr,te)
        altered=te.copy()
        altered["other_front_runner_share"]=0.99
        altered["prior_front_runner_score"]=0.01
        _,changed,means_changed=freeze_scaling(tr,altered)
        self.assertEqual(means,means_changed)
        self.assertTrue((original_tr["opponent_c"].values ==
                         freeze_scaling(tr,altered)[0]["opponent_c"].values).all())
        self.assertNotEqual(float(original_te["opponent_c"].mean()),
                            float(changed["opponent_c"].mean()))

    def test_only_synthetic_demo_allowed(self):
        rows=fabricate_competition(n_days=35,n_horses=24)
        with tempfile.TemporaryDirectory() as tmp:
            path=to_csv(tmp,rows)
            with self.assertRaisesRegex(ValueError,"synthetic-only panel"):
                run(path)
            rows[0]["source_license"]="research-approved"
            with self.assertRaisesRegex(ValueError,"mixed fabricated/real"):
                run(to_csv(tmp,rows),permit_synthetic_demo=True)

    def test_fits_and_separates_prediction_from_inference(self):
        rows=fabricate_competition(n_days=65,n_horses=36,seed=512,interaction=-0.9)
        with tempfile.TemporaryDirectory() as tmp:
            result=run(to_csv(tmp,rows),permit_synthetic_demo=True)
        self.assertEqual(result["status"],"SYNTHETIC_H2_SMOKE_ONLY")
        self.assertTrue(result["m0"]["converged"])
        self.assertTrue(result["m1"]["converged"])
        self.assertGreater(result["h2_overlap"]["future_test_races"],3)
        self.assertLess(result["h2_overlap"]["train_max_date"],
                        result["h2_overlap"]["test_start_date"])
        self.assertTrue(result["preprocessing"]["leave_one_out_opponents"])
        self.assertFalse(result["m1"]["beta_valid_clustered_ci_or_causal_pvalue"])
        self.assertEqual(len(result["forward_test"]["race_block_bootstrap_95pct_interval"]),2)
        self.assertLess(result["m1"]["style_by_opponent_context_beta_point_estimate"],0)


if __name__=="__main__":
    unittest.main()
