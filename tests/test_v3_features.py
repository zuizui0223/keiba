import unittest

from scripts.v3_features import normalize_class, horse_features, candidate_union


class V3FeatureTests(unittest.TestCase):
    def make_run(self, d, cls='1勝クラス', surface='dirt', distance=1200,
                 finish=4, margin=0.6):
        return {
            'date': d,
            'class': cls,
            'surface': surface,
            'distance_m': distance,
            'finish': finish,
            'beaten_margin_s': margin,
            'source_url': 'https://example.test/race',
        }

    def horse(self, number, odds, starts, runs, kyoto=None, kyoto_dist=None):
        return {
            'number': number,
            'name': f'H{number}',
            'win_odds': odds,
            'career_starts': starts,
            'recent_runs': runs,
            'kyoto_record': [0,0,0,0] if kyoto is None else kyoto,
            'kyoto_distance_record': kyoto_dist,
        }

    def race(self, horses):
        return {
            'date': '2026-10-12',
            'surface': 'dirt',
            'distance_m': 1200,
            'class': '1勝クラス',
            'horses': horses,
        }

    def test_normalize_class(self):
        self.assertEqual(normalize_class('3歳1勝クラス'), '1勝クラス')
        self.assertEqual(normalize_class('GII'), 'G2')
        self.assertEqual(normalize_class('G2'), 'G2')
        self.assertEqual(normalize_class('Listed'), 'L')

    def test_lightly_raced_recent_same_distance_winner_is_candidate(self):
        horses = [
            self.horse(i, float(i), 12, [self.make_run('2026-09-01')])
            for i in range(1, 8)
        ]
        horses[-1] = self.horse(
            7, 20.0, 3,
            [self.make_run('2026-08-02', cls='3歳未勝利', finish=1, margin=0.0)]
        )
        out = candidate_union(self.race(horses), market_top_n=5)
        row = next(r for r in out['candidates'] if r['number'] == 7)
        self.assertIn('recent_near_distance_win', row['reasons'])
        self.assertIn('lightly_raced_latest_good', row['reasons'])

    def test_recent_same_class_fourth_is_candidate_even_at_long_odds(self):
        horses = [
            self.horse(
                i, float(i), 12,
                [self.make_run('2026-09-01', finish=8, margin=1.2)]
            )
            for i in range(1, 8)
        ]
        horses[-1] = self.horse(
            7, 30.0, 7,
            [self.make_run('2026-07-04', distance=1000, finish=4, margin=0.6)]
        )
        out = candidate_union(self.race(horses), market_top_n=5)
        row = next(r for r in out['candidates'] if r['number'] == 7)
        self.assertIn('recent_same_class_good', row['reasons'])

    def test_layoff_is_uncertainty_not_exclusion(self):
        h = self.horse(
            1, 2.0, 9,
            [self.make_run('2025-10-25', finish=2, margin=0.3)]
        )
        f = horse_features(self.race([h]), h)
        self.assertTrue(f['long_layoff'])
        out = candidate_union(self.race([h]), market_top_n=1)
        self.assertEqual([c['number'] for c in out['candidates']], [1])
        self.assertIn('market_top_n', out['candidates'][0]['reasons'])

    def test_candidate_union_is_not_probability_model(self):
        horses = [
            self.horse(i, float(i), 10, [self.make_run('2026-09-01')])
            for i in range(1, 7)
        ]
        out = candidate_union(self.race(horses), market_top_n=5)
        self.assertFalse(out['probabilities_assigned'])
        self.assertEqual(
            out['candidate_order'], 'market_odds_baseline_only'
        )
        self.assertNotIn('win_probability', out['candidates'][0])


if __name__ == '__main__':
    unittest.main()
