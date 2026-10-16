import unittest
from compare_prerace_rankings import compare_rankings

class CompareRankingsTests(unittest.TestCase):
    def test_v2_improvement_metrics(self):
        result = [16, 1, 14]
        old = [14, 1, 6]
        v2 = [16, 1, 14]
        out = compare_rankings(result, old, v2)
        self.assertIsNone(out["old"]["winner_rank"])
        self.assertEqual(out["v2"]["winner_rank"], 1)
        self.assertFalse(out["old"]["top2_exact_unordered"])
        self.assertTrue(out["v2"]["top2_exact_unordered"])
        self.assertAlmostEqual(out["old"]["top3_recall"], 2/3)
        self.assertEqual(out["v2"]["top3_recall"], 1.0)

    def test_rank_is_one_based_and_absent_is_none(self):
        out = compare_rankings([14, 1, 16], [14, 1, 6], [16, 1, 14])
        self.assertEqual(out["old"]["winner_rank"], 1)
        self.assertEqual(out["v2"]["winner_rank"], 3)

if __name__ == "__main__":
    unittest.main()
