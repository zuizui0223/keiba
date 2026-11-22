"""Pure summary oracle tests; no new training or outcome selection."""
import copy
import unittest

from scripts.ticket_type_models import KINDS
from scripts.ticket_wide_sensitivity_summary import ALPHAS, POSITIONS, summarize


def fake_input(first):
    analyses = {}
    for position in POSITIONS:
        for alpha in ALPHAS:
            row = {
                kind: {
                    "brier_after_minus_PL": (0.01 if kind == "wide" else -0.02) * alpha,
                    "logloss_after_minus_PL": (0.015 if kind == "wide" else -0.03) * alpha,
                }
                for kind in KINDS
            }
            analyses[f"{position}:alpha={alpha:g}"] = {("scores" if first else "score"): row}
    return {
        "status": "RETROSPECTIVE_DEVELOPMENT_NO_PROSPECTIVE_SKILL_CLAIM"
        if first else "SECOND_DATE_RETROSPECTIVE_NOT_PROSPECTIVE",
        "pre_registered_before_outcome": False,
        "design_frozen_before_result": False,
        "races": [{"analyses": copy.deepcopy(analyses)} for _ in range(5 if first else 4)],
    }


class QuoteSensitivityTests(unittest.TestCase):
    def test_all_9_variants_per_date_without_selecting_winner(self):
        out = summarize(fake_input(True), fake_input(False))
        self.assertEqual(out["status"], "POSTHOC_SENSITIVITY_NOT_INDEPENDENT_EVIDENCE")
        self.assertFalse(out["hypothesis_test_p_value_produced"])
        self.assertEqual(out["race_count_by_date"], {"2026-10-12": 5, "2026-10-18": 4})
        self.assertEqual(set(out["ticket_types"]), set(KINDS))
        self.assertEqual(len(out["ticket_types"]["wide"]["alpha_price_grid"]["2026-10-18"]), 9)
        self.assertEqual(out["ticket_types"]["wide"]["n_positive_brier_change_configs_20261012"], 9)
        self.assertEqual(out["ticket_types"]["win"]["n_positive_brier_change_configs_20261012"], 0)
        self.assertTrue(out["ticket_types"]["wide"]["same_primary_direction_across_both_dates"])
        self.assertAlmostEqual(out["ticket_types"]["wide"]["primary_20261012_delta"], 0.005)

    def test_refuses_unfrozen_unsupported_evidence(self):
        a, b = fake_input(True), fake_input(False)
        a["pre_registered_before_outcome"] = True
        with self.assertRaises(ValueError):
            summarize(a, b)
        a = fake_input(True)
        b["races"].pop()
        with self.assertRaises(ValueError):
            summarize(a, b)


if __name__ == "__main__":
    unittest.main()
