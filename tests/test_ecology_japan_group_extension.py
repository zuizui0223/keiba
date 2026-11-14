from pathlib import Path
import importlib.util, sys, unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(0,str(Path(__file__).parent))

class ExtensionTests(unittest.TestCase):
    def mod(self):
        self.assertIsNotNone(importlib.util.find_spec('ecology_japan_group_extension'),'extension module must exist')
        import ecology_japan_group_extension as m
        return m
    def test_longest_alias_not_ownership_or_fuzzy_match(self):
        m=self.mod()
        self.assertEqual(m.prefix_label('マイネルテスト'),'マイネル')
        self.assertEqual(m.prefix_label('マイネテスト'),'マイネ')
        self.assertEqual(m.prefix_label('MEINER Test'),'マイネル')
        self.assertEqual(m.prefix_label('Meisho Test'),'メイショウ')
        self.assertEqual(m.prefix_label('Ｔ．Ｍ． Test'),'テイエム')
        self.assertEqual(m.prefix_label('Winner'),'OTHER_UNMATCHED')
        self.assertEqual(m.prefix_label('テストメイショウ'),'OTHER_UNMATCHED')
        self.assertEqual(m.prefix_label(None),'OTHER_UNMATCHED')
    def test_source_id_groups_quarantine_conflicting_names(self):
        m=self.mod()
        source=pd.DataFrame({'horse_id':['1','1','2','3'],'horse_name':['メイショウ甲','ダノン甲','マイネル乙','無冠名'],'sire_id':['p','p','q','q'],'sire':['父p','父p','父q','父q']})
        mapping,audit,labels=m.source_labels(source)
        self.assertEqual(mapping['1'],'AMBIGUOUS_NAME_GROUP')
        self.assertEqual(mapping['2'],'マイネル')
        self.assertEqual(audit['conflicting_name_group_horses'],1)
        self.assertEqual(labels['p'],'父p')
    def test_training_sire_selection_uses_horses_not_starts_or_future(self):
        m=self.mod()
        d=pd.DataFrame({'horse':['a','a','a','b','c','d','e','f'],'sire_id':['S','S','S','T','T','U','U','U'],'year':[2018,2018,2018,2018,2018,2020,2020,2020]})
        self.assertEqual(m.select_sires(d,top_n=1),[('T',2)])
    def sample(self):
        f=pd.DataFrame({'horse':['a','a','b'],'race':['r1','r2','r3'],'day':['d1','d2','d3'],'sire_id':['s1','s1','s2'],'year':[2019,2020,2021], 'y':[0.,0.,.5],'circuit':['JRA','NAR','JRA'],'cold':[False,False,True],'first_recorded':[True,False,True]})
        p=np.tile(np.array([.2,.2,.5])[:,None],(1,7))
        return f,p
    def test_equal_horse_scores_and_null_not_fitted(self):
        m=self.mod();f,p=self.sample();r=m.scores(f,p)
        self.assertAlmostEqual(r['rmse']['neutral'],np.sqrt(.125))
        self.assertAlmostEqual(r['rmse']['M_kin'],np.sqrt(.02))
        self.assertEqual(r['horses'],2)
        self.assertGreater(r['gain_neutral_minus_kin'],0)
        self.assertAlmostEqual(r['gain_trainer_minus_joint'],0)
    def test_empty_subset_is_missing_not_successful_zero(self):
        m=self.mod();f,p=self.sample();r=m.scores(f.iloc[:0],p[:0])
        self.assertEqual(r['rows'],0);self.assertIsNone(r['rmse'])
    def test_bootstrap_direction_and_support(self):
        m=self.mod()
        n=40;f=pd.DataFrame({'horse':[f'H{i}' for i in range(n)],'day':[f'D{i}' for i in range(n)],'sire_id':[f'S{i}' for i in range(n)],'y':np.zeros(n)})
        p=np.full((n,7),.2)
        r=m.intervals(f,p,draws=29)
        for typ in ['sire','day']:
            self.assertAlmostEqual(r[typ]['neutral_minus_kin']['gain'],.3)
            np.testing.assert_allclose(r[typ]['neutral_minus_kin']['interval95'],[.3,.3])
            self.assertEqual(r[typ]['status'],'DESCRIPTIVE_POINTWISE_SINGLE_CLUSTER')
        small=m.intervals(f.iloc[:2],p[:2],draws=29)
        self.assertEqual(small['sire']['status'],'LOW_CLUSTER_SUPPORT')
    def test_predictive_scores_reject_wrong_rows(self):
        m=self.mod();f,p=self.sample()
        with self.assertRaisesRegex(ValueError,'ALIGNMENT'):m.scores(f,p[:1])
    def test_parent_pairs_do_not_pool_unknown_parent(self):
        m=self.mod()
        d=pd.DataFrame({'horse':['a','b','c','d'],'sire_id':['S','S','',''],'dam_id':['D','D','X','Y']})
        r=m.family_counts(d)
        self.assertEqual(r['shared_sire_pairs'],1)
        self.assertEqual(r['shared_dam_pairs'],1)
        self.assertEqual(r['full_sibling_pairs'],1)
        self.assertEqual(r['any_direct_shared_parent_pairs'],1)
    def test_original_reference_guard_detects_change(self):
        m=self.mod();f,p=self.sample()
        ref={'rows':3,'horses':2,'models':{name:{'equal_horse_RMSE':np.sqrt(.02)} for name in m.MODELS}}
        m.check_reference(f,p,ref)
        p[0,3]=.9
        with self.assertRaisesRegex(ValueError,'PRIMARY_SCORE'):m.check_reference(f,p,ref)

if __name__=='__main__':unittest.main()
