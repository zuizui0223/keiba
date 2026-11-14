import sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ecology_japan_kin_controls import weights,history_features,parent_features,shuffle_parent_map,fit_linear,predict_linear,summarize

def fixture():
    rows=[]
    for yr in [2016,2017,2018]:
        for h in range(12):
            rows.append({'horse':str(h),'day':pd.Timestamp(yr,1,3),'year':yr,'y':h/11,'race':str(yr),
                'sire_id':'S'+str(h//3),'dam_id':'D'+str(h//2),'trainer_id':'T'+str(h//4),'jockey_id':'J'+str(h//4),
                'stratum':'JRA:turf:4','circuit':'JRA','surface':'turf','distance':1600.,'age':str(yr-2013),
                'sex':'M','going':'Good','race_class':'C1','course':'Tokyo','first_recorded':yr==2016,'prefix':'OTHER_UNMATCHED'})
    return pd.DataFrame(rows)

class StrongControlTests(unittest.TestCase):
    def test_equal_individual_weight_not_equal_starts(self):
        np.testing.assert_allclose(weights(pd.Series(['a','a','b'])),[.5,.5,1])
    def test_no_future_outcome_in_history_features(self):
        d=fixture();h=d[d.year<2018];f=d[d.year==2018].copy()
        x=history_features(h,f);f['y']=1-f.y;z=history_features(h,f)
        pd.testing.assert_frame_equal(x,z)
        self.assertNotIn('y',x.columns)
    def test_last3_and_last_result_reference(self):
        d=fixture();d.loc[(d.horse=='0')&(d.year==2016),'y']=.2;d.loc[(d.horse=='0')&(d.year==2017),'y']=.8
        x=history_features(d[d.year<2018],d[d.year==2018])
        self.assertAlmostEqual(x.iloc[0]['last1'],.8)
        self.assertAlmostEqual(x.iloc[0]['last3'],.5)
        self.assertEqual(x.iloc[0]['cold'],0)
    def test_unseen_horse_uses_midpoint_not_future_y(self):
        d=fixture();h=d[d.year<2018];f=d[d.year==2018].copy();f['horse']='new'+f.horse
        x=history_features(h,f)
        self.assertTrue((x.cold==1).all());self.assertTrue((x.last1==.5).all())
    def test_same_day_overlap_rejected(self):
        d=fixture()
        with self.assertRaisesRegex(ValueError,'TEMPORAL'):history_features(d,d)
    def test_focal_horse_excluded_from_kin(self):
        d=fixture();a=parent_features(d[d.year<2018],d[d.year==2018])
        expected=((1/11-.5)+(2/11-.5))/(8+2)
        self.assertAlmostEqual(a.iloc[0].sire_signal,expected)
    def test_unknown_parents_do_not_form_family(self):
        d=fixture();d['sire_id']='';d['dam_id']=''
        x=parent_features(d[d.year<2018],d[d.year==2018]);self.assertTrue(np.allclose(x,0))
    def test_parent_shuffling_preserves_pairs_and_is_outcome_blind(self):
        d=fixture();m=shuffle_parent_map(d,42);z=d.copy();z.y=1-z.y
        pd.testing.assert_frame_equal(m,shuffle_parent_map(z,42))
        original=d[['horse','sire_id','dam_id']].drop_duplicates()
        self.assertCountEqual(list(zip(m.sire_id,m.dam_id)),list(zip(original.sire_id,original.dam_id)))
        self.assertEqual(len(m),d.horse.nunique());self.assertGreater(int((m.sire_id!=original.set_index('horse').loc[m.index].sire_id).sum()),0)
    def test_model_preprocessing_uses_training_categories_and_values_only(self):
        x=pd.DataFrame({'num':np.arange(20,dtype=float),'cat':['a']*10+['b']*10});y=np.linspace(0,1,20)
        model=fit_linear(x,y,np.ones(20),alpha=0.00001)
        z=pd.DataFrame({'num':[5.],'cat':['unseen']})
        p=predict_linear(model,z)
        self.assertTrue(np.isfinite(p).all());self.assertEqual(p.shape,(1,))
        self.assertGreater(np.corrcoef(predict_linear(model,x),y)[0,1],.99)
    def test_no_truth_in_predictions_or_group_tuning(self):
        x=pd.DataFrame({'num':np.arange(10,dtype=float),'cat':['a']*10});y=np.linspace(0,1,10)
        m=fit_linear(x,y,np.ones(10),alpha=100)
        a=predict_linear(m,x);b=predict_linear(m,x.copy());np.testing.assert_allclose(a,b)
    def test_ridge_matches_direct_weighted_normal_equations(self):
        x=pd.DataFrame({'num':np.arange(8,dtype=float),'cat':['a']*8});y=np.linspace(.1,.9,8);w=np.arange(1,9,dtype=float)
        m=fit_linear(x,y,w,alpha=3)
        p=predict_linear(m,x)
        self.assertTrue(np.isfinite(p).all());self.assertTrue(((p>=0)&(p<=1)).all())
        self.assertEqual(m['uses_test_data'],False)
        z=(x['num'].to_numpy()-x['num'].mean())/x['num'].std(ddof=0)
        a=np.column_stack([np.ones(8),z]);ww=w/w.mean()
        expected=np.linalg.solve(a.T@(a*ww[:,None])+np.diag([0,3]),a.T@(y*ww))
        np.testing.assert_allclose(p,np.clip(a@expected,0,1),atol=1e-7)
    def test_metric_reconciles_zero_and_empty(self):
        d=fixture().iloc[:4];p={'strong':np.full(4,.5),'strong_kin':d.y.to_numpy()}
        r=summarize(d,p);self.assertGreater(r['gain_strong_to_kin'],0)
        self.assertEqual(summarize(d.iloc[:0],{k:v[:0] for k,v in p.items()})['rows'],0)

if __name__=='__main__':unittest.main()
