import unittest
from datetime import date

from scripts.evaluate_frozen_v3 import validate_test_date, score_candidate_set


class FrozenV3EvaluationTests(unittest.TestCase):
    def test_same_day_as_freeze_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'not_out_of_sample'):
            validate_test_date('2026-10-13', '2026-10-13T10:19:54+09:00')

    def test_pre_freeze_day_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'not_out_of_sample'):
            validate_test_date('2026-10-12', '2026-10-13T10:19:54+09:00')

    def test_future_day_is_allowed(self):
        self.assertEqual(
            validate_test_date('2026-10-14', '2026-10-13T10:19:54+09:00'),
            date(2026, 10, 14),
        )

    def test_candidate_scoring_separates_coverage_and_recall(self):
        out = score_candidate_set([1, 3, 5], [1, 2, 3], field_size=10)
        self.assertEqual(out['selected'], 3)
        self.assertAlmostEqual(out['coverage'], 0.3)
        self.assertEqual(out['top3_hits'], 2)
        self.assertAlmostEqual(out['top3_recall'], 2 / 3)

    def test_duplicate_candidates_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_candidate'):
            score_candidate_set([1, 1, 3], [1, 2, 3], field_size=10)


if __name__ == '__main__':
    unittest.main()
