import unittest
from copy import deepcopy
from datetime import datetime

from scripts.v3_ranking_features import build_ranking_features


class RankingFeatureTests(unittest.TestCase):
    def race(self):
        return {
            "race":12,"date":"2026-10-12","surface":"dirt",
            "distance_m":1200,"class":"1勝クラス","horses":[
                {"number":1,"name":"A","win_odds":2.0,"career_starts":5,
                 "source_latest_run_date":"2026-09-20","recent_runs":[
                    {"date":"2026-09-20","class":"1勝クラス","surface":"dirt","distance_m":1200,"finish":2,"beaten_margin_s":0.2,"source_url":"x"},
                    {"date":"2026-08-20","class":"1勝クラス","surface":"dirt","distance_m":1400,"finish":1,"beaten_margin_s":0.0,"source_url":"x"},
                    {"date":"2026-07-20","class":"未勝利","surface":"dirt","distance_m":1200,"finish":1,"beaten_margin_s":0.0,"source_url":"x"}]},
                {"number":2,"name":"B","win_odds":50.0,"career_starts":12,
                 "source_latest_run_date":"2026-06-01","recent_runs":[
                    {"date":"2026-06-01","class":"1勝クラス","surface":"turf","distance_m":1800,"finish":9,"beaten_margin_s":1.2,"source_url":"x"},
                    {"date":"2026-05-01","class":"1勝クラス","surface":"turf","distance_m":1600,"finish":8,"beaten_margin_s":1.0,"source_url":"x"},
                    {"date":"2026-04-01","class":"1勝クラス","surface":"turf","distance_m":1600,"finish":10,"beaten_margin_s":1.5,"source_url":"x"}]},
                {"number":3,"name":"C","win_odds":3.0,"career_starts":10,"source_latest_run_date":"2026-09-01","recent_runs":[{"date":"2026-09-01","class":"1勝クラス","surface":"turf","distance_m":1800,"finish":9,"beaten_margin_s":1.2,"source_url":"x"}]},
                {"number":4,"name":"D","win_odds":4.0,"career_starts":10,"source_latest_run_date":"2026-09-01","recent_runs":[{"date":"2026-09-01","class":"1勝クラス","surface":"turf","distance_m":1800,"finish":9,"beaten_margin_s":1.2,"source_url":"x"}]},
                {"number":5,"name":"E","win_odds":5.0,"career_starts":10,"source_latest_run_date":"2026-09-01","recent_runs":[{"date":"2026-09-01","class":"1勝クラス","surface":"turf","distance_m":1800,"finish":9,"beaten_margin_s":1.2,"source_url":"x"}]},
                {"number":6,"name":"F","win_odds":6.0,"career_starts":10,"source_latest_run_date":"2026-09-01","recent_runs":[{"date":"2026-09-01","class":"1勝クラス","surface":"turf","distance_m":1800,"finish":9,"beaten_margin_s":1.2,"source_url":"x"}]}
            ]
        }

    def as_of(self):
        return datetime.fromisoformat("2026-10-12T10:00:00+09:00")

    def test_only_candidates_are_emitted(self):
        out = build_ranking_features(self.race(), self.as_of())
        numbers = [row["number"] for row in out["rows"]]
        self.assertIn(1, numbers)
        self.assertNotIn(2, numbers)

    def test_features_are_descriptive_without_score_or_rank_output(self):
        row = next(
            row for row in build_ranking_features(self.race(), self.as_of())["rows"]
            if row["number"] == 1
        )
        self.assertEqual(row["market_rank"], 1)
        self.assertEqual(row["recent_wins"], 2)
        self.assertEqual(row["recent_top3"], 3)
        self.assertEqual(row["best_similar_finish"], 1)
        self.assertEqual(row["days_since_latest_run"], 22)
        self.assertGreaterEqual(row["candidate_signal_count"], 1)
        self.assertNotIn("score", row)
        self.assertNotIn("predicted_rank", row)

    def test_result_fields_do_not_change_features(self):
        base = self.race()
        first = build_ranking_features(base, self.as_of())
        leaked = deepcopy(base)
        leaked["official_result"] = [2,1]
        leaked["winner"] = 2
        second = build_ranking_features(leaked, self.as_of())
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
