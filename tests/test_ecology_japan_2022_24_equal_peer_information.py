"""Fictional end-to-end boundaries and matched-draw loss estimands."""
import hashlib
import json
from pathlib import Path
from statistics import NormalDist
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ecology_japan_2022_24_equal_peer_information as eq
import ecology_japan_2022_24_family_feature_ablation as ablation
import ecology_japan_2022_24_parent_performance_channels as channels


def fixture():
    panel = pd.DataFrame({"horse": ["a", "a", "b", "c", "d"], "race": list("pqrst"),
                          "day": pd.date_range("2022-01-01", periods=5),
                          "sire_id": ["1", "1", "2", "3", ""], "dam_id": ["a", "a", "b", "", ""],
                          "y": [0, 1, 1, 0, 1]})
    support = pd.DataFrame({"sire_relative_count": [7, 3, 2, 1, 0], "dam_relative_count": [5, 2, 1, 0, 0]})
    k = support.min(axis=1)
    full = {name: np.full(len(panel), .2 if name == "MD" else .5) for name in channels.FEATURES}
    losses = {"MS": np.array([np.full(len(panel), i % 2) for i in range(32)]),
              "MD": np.tile([0., .1, .3, .5, 1.], (32, 1))}
    return panel, full, losses, support, k


class EstimatorTests(unittest.TestCase):
    def test_period_weighting_paired_losses_and_matched_draw_precision(self):
        p, full, losses, support, k = fixture()
        r = eq.summarize_period(p, full, losses, support, k, draws=30, min_clusters=2)
        w = np.array([1/8, 1/8, 1/4, 1/4, 1/4])
        f = np.dot(w, (p.y-full["MD"])**2 - (p.y-full["MS"])**2)
        b = (losses["MD"] - losses["MS"]) @ w
        c = f - b
        self.assertEqual(tuple(eq.SEEDS), tuple(range(2026112200, 2026112232)))
        self.assertEqual(set(r["full_models"]), {"M0", *channels.FEATURES})
        self.assertAlmostEqual(r["balanced_models"]["MS"]["MSE"], .5)
        self.assertAlmostEqual(r["balanced_models"]["MS"]["RMSE"], np.sqrt(.5))
        contrasts = r["mean_MSE_contrasts"]
        self.assertAlmostEqual(contrasts["full_sire_advantage"], f)
        self.assertAlmostEqual(contrasts["change_in_sire_advantage"], contrasts["sire_loss_increase"] - contrasts["dam_loss_increase"])
        for term, oracle in [("balanced_sire_advantage", b), ("change_in_sire_advantage", c)]:
            self.assertAlmostEqual(contrasts[term], np.mean(oracle))
            np.testing.assert_allclose([draw[term] for draw in r["per_draw"]], oracle, rtol=0, atol=1e-14)
            self.assertEqual([draw["seed"] for draw in r["per_draw"]], list(eq.SEEDS))
            self.assertAlmostEqual(r["primary_uncertainty"][term]["mean_MSE_gain"], np.mean(oracle))
            expected = [oracle.mean(), oracle.std(ddof=1), oracle.std(ddof=1)/np.sqrt(32),
                        oracle.min(), oracle.max()]
            np.testing.assert_allclose([r["monte_carlo"][term][key] for key in ("mean","SD","MCSE","min","max")],
                                       expected, rtol=0, atol=1e-14)
        self.assertAlmostEqual(r["monte_carlo"]["balanced_sire_advantage"]["SD"], r["monte_carlo"]["change_in_sire_advantage"]["SD"])
        self.assertEqual(r["starts"], len(p))
        self.assertEqual(r["horses"], 4)

    def test_square_before_averaging(self):
        y = np.array([0., 1.])
        # Each individual fit yields one prediction vector. The ensemble would score .25.
        draws = [eq._squared_loss(y, v) for _ in range(16) for v in ([0., 1.], [1., 0.])]
        np.testing.assert_array_equal(np.mean(draws, axis=0), [.5, .5])
        for bad in ([np.nan, 1], [-.001, .5], [0, 1, .5]):
            with self.assertRaises(ValueError):
                eq._squared_loss(y, bad)

    def test_balanced_support_and_conditional_intervals(self):
        p, full, losses, support, k = fixture()
        r = eq.summarize_period(p, full, losses, support, k, draws=30, min_clusters=3)
        stats = r["support"]["balanced"]
        self.assertAlmostEqual(stats["mean_peer_count"], 5/8+2/8+1/4)
        for label, starts, share in [("0", 2, .5), ("1", 1, .25), ("2-4", 1, .125), ("5+", 1, .125)]:
            self.assertEqual(stats["bins"][label], {"starts": starts, "horse_equal_share": share})
        self.assertEqual(1-stats["bins"]["0"]["horse_equal_share"], r["support"]["joint_support"]["both"]["horse_equal_share"])
        for info in r["primary_uncertainty"].values():
            self.assertEqual(info["dam_bootstrap"]["status"], "HOLD_TOO_FEW_RECORDED_PARENT_GROUPS")
            self.assertEqual(info["sire_bootstrap"]["status"], "OK")
            center = info["mean_MSE_gain"]
            tw = info["two_way"]
            self.assertEqual(tw["status"], "OK")
            z = NormalDist().inv_cdf(1-.025/8)
            np.testing.assert_allclose(tw["CI95_bonferroni_8"], [center-z*tw["SE"], center+z*tw["SE"]])
            self.assertNotIn("CI95_bonferroni_12", tw)

    def test_malformed_draws_models_and_selected_support_rejected(self):
        p, full, loss, s, k = fixture()
        for bad in (loss["MS"][:-1], loss["MS"][:, :-1], np.full((32, 5), np.nan),
                    np.full((32,5), 1.1), np.full((32,5), -.1)):
            with self.assertRaises(ValueError):
                eq.summarize_period(p, full, {**loss, "MS": bad}, s, k)
        for args in [(p, {}, loss, s, k), (p, full, {"MS": loss["MS"]}, s, k),
                     (p, full, loss, s, k.iloc[::-1]), (p, full, loss, s, k+.2),
                     (p, full, loss, s, k+1), (p, full, loss, s, k*np.nan)]:
            with self.assertRaises(ValueError):
                eq.summarize_period(*args)

    def test_both_reference_hashes_checked_before_source_access(self):
        with tempfile.TemporaryDirectory() as d:
            ref = Path(d)/"ref.json"
            ref.write_text("{}")
            good = hashlib.sha256(ref.read_bytes()).hexdigest()
            for sha70, sha72 in [(good, "wrong"), ("wrong", good)]:
                with patch.multiple(eq, REFERENCE=ref, PARENT_REFERENCE=ref, REFERENCE_SHA=sha70,
                                    PARENT_REFERENCE_SHA=sha72), patch.object(ablation, "load_sources") as load:
                    with self.assertRaisesRegex(ValueError, "REFERENCE"):
                        eq.analyze(Path("fictional"), Path("fictional"))
                    load.assert_not_called()

    def test_fictional_runner_checks_both_legacy_periods_before_refitting_and_caches_blocks(self):
        rows = []
        for year in range(2017, 2025):
            for i, horse in enumerate(["a", "b", "c", "d"]):
                rows.append({"horse": horse, "race": f"r{year}", "day": pd.Timestamp(year, 6, 1),
                             "year": year, "surface": "turf", "distance": 1600, "stratum": "turf:4",
                             "sire_id": "s", "dam_id": f"m{i//2}", "circuit": "JRA",
                             "y": ((year+i) % 4)/3})
        data = pd.DataFrame(rows)
        old, future = data.loc[data.year.lt(2022)], data.loc[data.year.ge(2022)].reset_index(drop=True)
        raw = old.rename(columns={"horse":"horse_id", "day":"date"}).assign(age=4, sex="")
        pred, counts = channels._historical_predictions(raw, old, future)
        mask = future.horse.ne("d").to_numpy()
        strict = future[mask].reset_index(drop=True)
        qa = {"fictional_strict_starts": len(strict)}
        ref70 = {"strong_all_row_parity": ablation.canonical_parity_scores(
            ablation._scores(future, pred["M1"], pred["M2"])), "strict_source_qa": qa, "by_year": {}}
        ref72 = {"by_year": {}}
        strict_counts = counts.loc[mask].reset_index(drop=True)
        for label, p, f in channels._periods(strict, {k: v[mask] for k,v in pred.items()}):
            original = ablation.summarize_period(p, {k:f[k] for k in ablation.FEATURES})
            parent = channels.summarize_period(p, f, strict_counts.loc[p.index])
            for ref, stats in [(ref70, original), (ref72, parent)]:
                (ref if label == "pooled" else ref["by_year"])[label] = stats

        def run():
            with tempfile.TemporaryDirectory() as folder:
                files = [Path(folder)/name for name in ("a.json", "b.json")]
                for path, ref in zip(files, (ref70, ref72)):
                    path.write_text(json.dumps(ref))
                a, b = [hashlib.sha256(path.read_bytes()).hexdigest() for path in files]
                source = raw, old, future, {}, {"two_event_anchor_horses":4}, {}
                with patch.multiple(eq, REFERENCE=files[0], PARENT_REFERENCE=files[1],
                                    REFERENCE_SHA=a, PARENT_REFERENCE_SHA=b), \
                        patch.object(ablation, "load_sources", return_value=source), \
                        patch.object(ablation, "strict_mask_exact_horse_race", return_value=(mask, qa)):
                    return eq.analyze(Path("fictional.zip"), Path("fictional.db"))

        # Give the QA reference an independent object so corruption cannot alter the source.
        ref70["strict_source_qa"] = dict(qa)
        for endpoint, key in [(ref70["strong_all_row_parity"], "RMSE_M0_midpoint"),
                              (ref70["strict_source_qa"], "fictional_strict_starts"),
                              (ref70["by_year"]["2024"]["models"]["M1"], "MSE"),
                              (ref72["by_year"]["2024"]["models"]["M1"], "MSE")]:
            saved = endpoint[key]
            endpoint[key] += .01
            with patch.object(eq, "_draw_losses", side_effect=AssertionError("premature refit")):
                with self.assertRaisesRegex(ValueError, "PARITY"):
                    run()
            endpoint[key] = saved
        build = ablation._strong_features

        def wrong_training_count(history, context, meta):
            base = build(history, context, meta)
            if context.year.max() == 2019:
                base.loc[0, "dam_relative_count"] += 1
            return base

        with patch.object(ablation, "_strong_features", side_effect=wrong_training_count), \
                patch.object(eq, "_draw_losses", side_effect=AssertionError("premature refit")):
            with self.assertRaisesRegex(ValueError, "NATIVE_PEER_COUNT_PARITY"):
                run()

        with patch.object(eq, "prepare_peer_block", wraps=eq.prepare_peer_block) as prepare, \
                patch.object(eq, "_squared_loss", wraps=eq._squared_loss) as square, \
                patch.object(ablation, "_strong_features", wraps=ablation._strong_features) as bases, \
                patch.object(ablation, "fit_weighted_ridge", wraps=ablation.fit_weighted_ridge) as fits:
            result = run()
        self.assertEqual([call.kwargs["cutoff_year"] for call in prepare.call_args_list],
                         [2018,2019,2020,2021,2022])
        for call in prepare.call_args_list:
            self.assertEqual(list(call.args[1].columns), ablation.CONTEXT)
        self.assertEqual(bases.call_count, 5)
        for call in bases.call_args_list:
            self.assertEqual(list(call.args[1].columns), ablation.CONTEXT)
        self.assertEqual(square.call_count, 64)
        self.assertEqual(fits.call_count, 6+64)
        for i, call in enumerate(fits.call_args_list[-64:]):
            self.assertEqual(call.args[3], channels.FEATURES[("MS","MD")[i%2]])
            self.assertEqual(call.kwargs["alpha"], 100)
        self.assertEqual(result["pooled"]["starts"], len(strict))
        self.assertEqual(set(result["by_year"]), {"2022", "2023", "2024"})
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
