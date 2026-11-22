"""Exact fictional checks for the fixed parent-performance comparison."""
from pathlib import Path
from statistics import NormalDist
import json
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import ecology_japan_2022_24_family_feature_ablation as original
import ecology_japan_2022_24_parent_performance_channels as channels


def design():
    rng = np.random.default_rng(52)
    x = pd.DataFrame(rng.normal(size=(96, len(original.STRONG_KIN))), columns=original.STRONG_KIN)
    y = np.clip(.5 + .15*x.sire_kin_history - .10*x.dam_kin_history + .08*x.own_mean, 0, 1).to_numpy()
    return x, y, np.repeat(np.arange(24).astype(str), 4)


def panel():
    return pd.DataFrame({
        'horse': ['a', 'a', 'a', 'b', 'c', 'd'],
        'race': ['r1', 'r2', 'r3', 'r1', 'r2', 'r3'],
        'day': pd.to_datetime(['2022-01-01', '2022-02-01', '2022-03-01',
                               '2022-01-01', '2022-02-01', '2022-03-01']),
        'sire_id': ['s0', 's0', 's0', 's0', 's1', 's2'],
        'dam_id': ['m0', 'm0', 'm0', 'm1', 'm1', ''],
        'y': [0., .2, .4, .6, .8, 1.],
    })


def support():
    return pd.DataFrame({'sire_relative_count': [0, 0, 2, 5, 6, 0],
                         'dam_relative_count': [0, 2, 0, 1, 0, 0]})


def predictions(n=6):
    return {k: np.repeat(v, n) for k, v in
            {'M1': .5, 'MC': .4, 'MP': .6, 'M2': .7, 'MS': .6, 'MD': .5}.items()}


class ParentChannelTests(unittest.TestCase):
    def test_all_original_fits_and_predictions_match(self):
        x, y, h = design()
        old = original.predict_factorial(original.fit_factorial(x, y, h), x)
        new = channels.predict_factorial(channels.fit_factorial(x, y, h), x)
        self.assertEqual(set(new), {'M1', 'MC', 'MP', 'M2', 'MS', 'MD'})
        for name in old:
            np.testing.assert_allclose(new[name], old[name], rtol=0, atol=1e-14)

    def test_parent_subsets_keep_both_counts_and_original_order(self):
        for name, excluded in [('MS', 'dam_kin_history'), ('MD', 'sire_kin_history')]:
            expected = tuple(c for c in original.STRONG_KIN if c != excluded)
            self.assertEqual(tuple(channels.FEATURES[name]), expected)
            self.assertTrue(set(original.COUNTS).issubset(channels.FEATURES[name]))
            self.assertTrue(set(original.STRONG_NO_KIN).issubset(channels.FEATURES[name]))
            self.assertNotIn('sire_relative_count', channels.FEATURES[name])
            self.assertNotIn('dam_relative_count', channels.FEATURES[name])

    def test_excluded_side_cannot_change_predictions(self):
        x, y, h = design()
        models = channels.fit_factorial(x, y, h)
        base = channels.predict_factorial(models, x)
        for name, excluded in [('MS', 'dam_kin_history'), ('MD', 'sire_kin_history')]:
            changed = x.copy()
            changed[excluded] += 100
            actual = channels.predict_factorial(models, changed)
            np.testing.assert_allclose(actual[name], base[name], rtol=0, atol=1e-14)
            self.assertGreater(np.max(np.abs(actual['M2']-base['M2'])), .01)

    def test_excluded_side_cannot_change_refitted_coefficients(self):
        x, y, h = design()
        base = channels.fit_factorial(x, y, h)
        for name, excluded in [('MS', 'dam_kin_history'), ('MD', 'sire_kin_history')]:
            changed = x.copy()
            changed[excluded] = np.arange(len(x))**2
            actual = channels.fit_factorial(changed, y, h)
            np.testing.assert_allclose(actual[name]['coef'], base[name]['coef'], rtol=0, atol=1e-14)

    def test_hand_checked_signed_paths_and_direct_difference(self):
        pred = {k: np.array([v]) for k, v in
                {'M1': .5, 'MC': .75, 'MP': .5, 'M2': .375, 'MS': .625, 'MD': .5}.items()}
        r = channels.paired_loss_terms(np.array([.5]), pred)
        expected = {'combined_gain': 3/64, 'sire_alone': 3/64, 'dam_alone': 4/64,
                    'sire_given_dam': -1/64, 'dam_given_sire': 0., 'sire_minus_dam': -1/64}
        self.assertEqual(set(r), set(expected))
        for k, v in expected.items():
            self.assertAlmostEqual(r[k][0], v, places=14)
        self.assertEqual(r['combined_gain'][0], (r['sire_alone']+r['dam_given_sire'])[0])
        self.assertEqual(r['combined_gain'][0], (r['dam_alone']+r['sire_given_dam'])[0])
        self.assertNotEqual(r['combined_gain'][0], (r['sire_given_dam']+r['dam_given_sire'])[0])
        self.assertEqual(r['sire_minus_dam'][0], (r['sire_given_dam']-r['dam_given_sire'])[0])

    def test_equal_horse_scores_share_the_contrast_denominator(self):
        r = channels.summarize_period(panel(), predictions(), support(), draws=99, min_clusters=2)
        self.assertAlmostEqual(r['models']['M0']['MSE'], 7/60)
        self.assertAlmostEqual(r['models']['MC']['MSE'], 47/300)
        self.assertAlmostEqual(r['models']['M2']['MSE'], 29/300)
        self.assertAlmostEqual(r['loss_decomposition_MSE']['combined_gain'], .06)
        self.assertAlmostEqual(r['loss_decomposition_MSE']['sire_minus_dam'], .02)
        for name in ('sire_given_dam', 'dam_given_sire', 'sire_minus_dam'):
            self.assertAlmostEqual(r['primary_uncertainty'][name]['mean_MSE_gain'],
                                   r['loss_decomposition_MSE'][name])

    def test_replicating_one_horses_whole_history_preserves_means_and_support(self):
        p, s, pred = panel(), support(), predictions()
        before = channels.summarize_period(p, pred, s, draws=99, min_clusters=2)
        extra = p.iloc[:3].copy()
        extra['race'] = ['repeat1', 'repeat2', 'repeat3']
        after = channels.summarize_period(pd.concat([p, extra], ignore_index=True),
            {k: np.r_[v, v[:3]] for k, v in pred.items()}, pd.concat([s, s.iloc[:3]], ignore_index=True),
            draws=99, min_clusters=2)
        for name, score in before['models'].items():
            self.assertAlmostEqual(score['MSE'], after['models'][name]['MSE'])
        for name in before['loss_decomposition_MSE']:
            self.assertAlmostEqual(before['loss_decomposition_MSE'][name], after['loss_decomposition_MSE'][name])
        a, b = channels.support_summary(p, s), channels.support_summary(pd.concat([p, extra], ignore_index=True), pd.concat([s, s.iloc[:3]], ignore_index=True))
        for key in a['joint_support']:
            self.assertAlmostEqual(a['joint_support'][key]['horse_equal_share'], b['joint_support'][key]['horse_equal_share'])

    def test_two_way_interval_uses_twelve_comparisons(self):
        r = channels.paired_uncertainty(panel(), np.array([.1, .4, -.2, .3, .2, -.5]),
                                       draws=99, seed=11, min_clusters=2)
        theta, se = .025, .22942409783339382
        self.assertAlmostEqual(r['mean_MSE_gain'], theta)
        self.assertAlmostEqual(r['two_way']['SE'], se)
        self.assertNotIn('CI95_bonferroni_8', r['two_way'])
        for key, z in [('CI95', NormalDist().inv_cdf(.975)),
                       ('CI95_bonferroni_12', NormalDist().inv_cdf(1-.025/12))]:
            np.testing.assert_allclose(r['two_way'][key], [theta-z*se, theta+z*se], rtol=0, atol=1e-14)

    def test_low_known_parent_support_and_zero_variance_hold(self):
        r = channels.parent_bootstrap(panel(), np.zeros(6), 'dam', draws=99, min_clusters=3)
        self.assertEqual(r['recorded_parent_groups'], 2)
        self.assertEqual(r['clusters'], 3)
        self.assertEqual(r['status'], 'HOLD_TOO_FEW_RECORDED_PARENT_GROUPS')
        self.assertNotIn('CI95', r)
        r = channels.paired_uncertainty(panel(), np.zeros(6), draws=99, min_clusters=2)
        self.assertEqual(r['two_way']['status'], 'HOLD_NONPOSITIVE_VARIANCE')

    def test_each_parent_bootstrap_matches_separate_scalar_oracle(self):
        gain = np.array([.1, .4, -.2, .3, .2, -.5])
        # Horse means: a=.1, b=.3, c=.2, d=-.5. Different father/mother partitions.
        for parent, totals, sizes in [('sire', [.4, .2, -.5], [2, 1, 1]),
                                     ('dam', [.1, .5, -.5], [1, 2, 1])]:
            r = channels.parent_bootstrap(panel(), gain, parent, draws=99, seed=11, min_clusters=2)
            rng = np.random.default_rng(11)
            oracle = []
            for _ in range(99):
                ix = rng.integers(3, size=3)
                oracle.append(sum(totals[i] for i in ix)/sum(sizes[i] for i in ix))
            np.testing.assert_allclose(r['CI95'], np.quantile(oracle, [.025, .975]), rtol=0, atol=1e-14)

    def test_unknown_parent_singletons_do_not_collide_with_recorded_ids(self):
        p = panel()
        p.loc[p.horse.eq('a'), 'dam_id'] = 'd'
        gain = np.array([.1, .4, -.2, .3, .2, -.5])
        r = channels.parent_bootstrap(p, gain, 'dam', draws=99, seed=11, min_clusters=2)
        self.assertEqual(r['clusters'], 3)
        self.assertEqual(r['recorded_parent_groups'], 2)
        self.assertEqual(r['unknown_parent_singleton_horses'], 1)
        order = [5, 2, 0, 4, 1, 3]
        other = channels.parent_bootstrap(p.iloc[order], gain[order], 'dam', draws=99, seed=11, min_clusters=2)
        np.testing.assert_allclose(r['CI95'], other['CI95'], rtol=0, atol=1e-14)

    def test_joint_support_and_depth_use_period_horse_weights(self):
        r = channels.support_summary(panel(), support())
        expected = {'neither': (2, 1/3), 'sire_only': (2, 1/3),
                    'dam_only': (1, 1/12), 'both': (1, 1/4)}
        for key, (starts, mass) in expected.items():
            self.assertEqual(r['joint_support'][key]['starts'], starts)
            self.assertAlmostEqual(r['joint_support'][key]['horse_equal_share'], mass)
        self.assertAlmostEqual(sum(x['horse_equal_share'] for x in r['joint_support'].values()), 1.)
        self.assertAlmostEqual(r['by_parent']['sire']['mean_peer_count'], 35/12)
        self.assertAlmostEqual(r['by_parent']['dam']['mean_peer_count'], 5/12)
        for key, mass in {'0': 5/12, '1': 0., '2-4': 1/12, '5+': 1/2}.items():
            self.assertAlmostEqual(r['by_parent']['sire']['bins'][key]['horse_equal_share'], mass)
        self.assertEqual(r['parent_coverage']['dam']['unknown_parent_horses'], 1)
        self.assertEqual(r['parent_coverage']['dam']['known_parent_horses'], 3)

    def test_existing_peer_counts_exclude_self_and_repeat_starts_but_keep_neutral_siblings(self):
        h = pd.DataFrame({'horse':['a','b','b','c','d'], 'sire_id':['s']*5,
                          'dam_id':['m','m','m','m','other'],
                          'stratum':['turf:4','turf:4','turf:4','dirt:4','turf:4'],
                          'y':[.8,.2,.8,.1,.6], 'day':pd.date_range('2021-01-01',periods=5)})
        t = pd.DataFrame({'horse':['a','unseen','unknown'], 'sire_id':['s','empty',''],
                          'dam_id':['m','empty',''], 'stratum':['turf:4']*3,
                          'surface':['turf']*3,'distance':[1600]*3,
                          'day':pd.to_datetime(['2022-01-01']*3)})
        x = original.make_common_features(h, t)
        np.testing.assert_array_equal(x.sire_relative_count, [2,0,0])
        np.testing.assert_array_equal(x.dam_relative_count, [1,0,0])
        self.assertEqual(x.dam_kin_history.iloc[0], 0.)
        self.assertGreater(x.sire_kin_history.iloc[0], 0.)

    def test_invalid_support_or_nonzero_unknown_parent_support_is_rejected(self):
        for mutate in ('negative','fraction','nan','length','unknown','order'):
            s = support()
            if mutate=='negative':s.loc[0,'sire_relative_count']=-1
            elif mutate=='fraction':s=s.astype(float);s.loc[0,'sire_relative_count']=.5
            elif mutate=='nan':s.loc[0,'sire_relative_count']=np.nan
            elif mutate=='length':s=s.iloc[:-1]
            elif mutate=='order':s=s.iloc[::-1]
            else:s.loc[5,'dam_relative_count']=1
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):
                channels.support_summary(panel(),s)

    def test_duplicate_index_cannot_hide_reordered_support(self):
        p, s = panel(), support()
        p.index = s.index = [4, 8, 9, 4, 10, 11]
        swapped = s.iloc[[3, 1, 2, 0, 4, 5]]
        self.assertTrue(p.index.equals(swapped.index))
        with self.assertRaises(ValueError):
            channels.support_summary(p, swapped)

    def test_conflicting_parent_mapping_or_duplicate_rows_is_rejected(self):
        for mutate in ('dam','sire','duplicate','day'):
            p=panel()
            if mutate in ('dam','sire'):p.loc[1,mutate+'_id']='conflict'
            elif mutate=='duplicate':p.loc[1,['race','day']]=p.loc[0,['race','day']]
            else:p.loc[0,'day']=pd.NaT
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):
                channels.paired_uncertainty(p,np.zeros(6),draws=99,min_clusters=2)

    def test_invalid_or_missing_predictions_are_rejected(self):
        for bad in (np.repeat(np.nan,6), np.repeat(1.01,6), np.repeat(.5,5)):
            p=predictions();p['MD']=bad
            with self.assertRaises(ValueError):channels.paired_loss_terms(panel().y,p)
        p=predictions();del p['MS']
        with self.assertRaises(ValueError):channels.paired_loss_terms(panel().y,p)

    def test_reference_gate_rejects_missing_keys_and_changed_endpoints(self):
        for changed in ({'a':1.}, {'a':1.,'b':[2.01]}):
            with self.assertRaises(ValueError):channels._require_parity(changed,{'a':1.,'b':[2.]},'fixture')
        channels._require_parity({'a':1.,'b':[2.+1e-14]},{'a':1.,'b':[2.]},'fixture')

    def test_summary_is_finite_aggregate_only(self):
        p=panel();p['sire_id']='private_parent_label';p['dam_id']='private_mother_label'
        r=channels.summarize_period(p,predictions(),support(),draws=99,min_clusters=2)
        encoded=json.dumps(r,allow_nan=False)
        self.assertNotIn('private_parent_label',encoded)
        self.assertNotIn('private_mother_label',encoded)
        self.assertEqual(r['horses'],4)


if __name__=='__main__':
    unittest.main()
