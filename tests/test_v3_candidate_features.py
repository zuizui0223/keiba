import unittest

from scripts.v3_candidate_features import build_candidate_features, class_group


class CandidateFeatureTests(unittest.TestCase):
    def race(self):
        return {
            "race": 12,
            "date": "2026-10-12",
            "surface": "dirt",
            "distance_m": 1200,
            "class": "3歳以上1勝クラス",
            "horses": [
                {"number":1,"name":"Market","win_odds":2.0,"career_starts":10,"source_latest_run_date":"2026-09-01","recent_runs":[{"date":"2026-09-01","class":"1勝クラス","surface":"dirt","distance_m":1400,"finish":8,"beaten_margin_s":1.2,"source_url":"x"}]},
                {"number":2,"name":"SameDistWinner","win_odds":20.0,"career_starts":7,"source_latest_run_date":"2026-08-01","recent_runs":[{"date":"2026-08-01","class":"3歳未勝利","surface":"dirt","distance_m":1200,"finish":1,"beaten_margin_s":0.0,"source_url":"x"}]},
                {"number":3,"name":"SameClassClose","win_odds":30.0,"career_starts":12,"source_latest_run_date":"2026-09-15","recent_runs":[{"date":"2026-09-15","class":"1勝クラス","surface":"dirt","distance_m":1000,"finish":4,"beaten_margin_s":0.6,"source_url":"x"}]},
                {"number":4,"name":"LightlyRaced","win_odds":40.0,"career_starts":4,"source_latest_run_date":"2026-05-01","recent_runs":[{"date":"2026-05-01","class":"未勝利","surface":"turf","distance_m":1600,"finish":1,"beaten_margin_s":0.0,"source_url":"x"}]},
                {"number":5,"name":"NoFlag","win_odds":50.0,"career_starts":12,"source_latest_run_date":"2026-03-01","recent_runs":[{"date":"2026-03-01","class":"1勝クラス","surface":"dirt","distance_m":1800,"finish":10,"beaten_margin_s":2.0,"source_url":"x"}]},
            ],
        }

    def test_class_group_normalizes_win_class_labels(self):
        self.assertEqual(class_group("3歳以上1勝クラス"), "1win")
        self.assertEqual(class_group("3歳1勝クラス"), "1win")
        self.assertEqual(class_group("2勝クラス"), "2win")

    def test_candidate_union_keeps_distinct_evidence_paths(self):
        out = build_candidate_features(self.race(), market_top_n=1)
        rows = {r["number"]: r for r in out["horses"]}
        self.assertIn("market_top_n", rows[1]["candidate_reasons"])
        self.assertIn("recent_same_distance_win", rows[2]["candidate_reasons"])
        self.assertIn("recent_same_class_close", rows[3]["candidate_reasons"])
        self.assertIn("lightly_raced_recent_win", rows[4]["candidate_reasons"])
        self.assertFalse(rows[5]["candidate"])

    def test_long_layoff_is_uncertainty_not_candidate_exclusion(self):
        out = build_candidate_features(self.race(), market_top_n=1,
                                       long_layoff_days=120)
        rows = {r["number"]: r for r in out["horses"]}
        self.assertIn("long_layoff", rows[4]["uncertainty_flags"])
        self.assertTrue(rows[4]["candidate"])

    def test_candidate_set_is_sorted_for_stable_output(self):
        out = build_candidate_features(self.race(), market_top_n=1)
        self.assertEqual([r["number"] for r in out["horses"]], [1,2,3,4,5])
        self.assertEqual(out["candidate_numbers"], [1,2,3,4])


if __name__ == "__main__":
    unittest.main()
