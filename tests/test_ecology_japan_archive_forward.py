from pathlib import Path
import sys, unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ecology_japan_archive_forward import prepare_frame,make_features,fit_weights,predict

def races(day='2017-01-01',offset=0):
    rows=[]
    for i in range(6):
        rows.append(dict(date=day,racecourse='Tokyo',race_number='1',track='Turf',distance='1600',
            place=str(i+1),horse_id=str(100+i+offset),sire_id='10' if i<3 else '20',dam_id=str(40+i),
            horse_name=('メイショウ' if i%2==0 else 'OTHER')+str(i),trainer_id='T1' if i<3 else 'T2',age='3',sex='M'))
    return rows

class ArchiveForwardTests(unittest.TestCase):
    def test_parser_accepts_exact_ids_and_rank_outcome(self):
        d,qa=prepare_frame(pd.DataFrame(races()))
        self.assertEqual(len(d),6)
        self.assertEqual(d.horse.tolist(),[str(100+i) for i in range(6)])
        self.assertAlmostEqual(d.y.min(),0)
        self.assertAlmostEqual(d.y.max(),1)
        self.assertEqual(qa['valid_complete_races'],1)
    def test_duplicate_runner_is_rejected(self):
        r=races();r.append(r[0].copy())
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):
            prepare_frame(pd.DataFrame(r))
    def test_rank_gap_race_not_fabricated(self):
        r=races();r[3]['place']='DNF'
        d,qa=prepare_frame(pd.DataFrame(r))
        self.assertEqual(len(d),0)
        self.assertEqual(qa['incomplete_or_tied_races'],1)
    def test_first_observed_not_assumed_birth_or_debut(self):
        d,qa=prepare_frame(pd.DataFrame(races()+races('2018-01-01',100)))
        t=d[d.year<2018];f=d[d.year==2018]
        x=make_features(t,f)
        self.assertTrue(x.cold.all())
        self.assertTrue(x.kin_exposed.all())
        self.assertEqual(len(x),6)
    def test_same_day_and_future_training_are_rejected(self):
        d,_=prepare_frame(pd.DataFrame(races()))
        with self.assertRaisesRegex(ValueError,'TEMPORAL'):
            make_features(d,d)
    def test_future_labels_cannot_change_features_or_weights(self):
        d,_=prepare_frame(pd.DataFrame(races()+races('2018-01-01',100)))
        t=d[d.year<2018];f=d[d.year==2018].copy()
        x=make_features(t,f)
        f['y']=1-f.y
        y=make_features(t,f)
        for k in ['base','sire','dam','kin','trainer','name']:
            np.testing.assert_allclose(x[k],y[k])
    def test_focal_history_excluded_from_family_and_trainer(self):
        d,_=prepare_frame(pd.DataFrame(races()+races('2018-01-01')))
        train=d[d.year<2018];test=d[d.year==2018]
        x=make_features(train,test)
        target=x[x.horse=='100'].iloc[0]
        self.assertEqual(target.sire_relatives,2)
        self.assertEqual(target.dam_relatives,0)
        self.assertEqual(target.trainer_peers,2)
    def test_parent_missing_never_pooled_as_one_family(self):
        r=races()+races('2018-01-01',100)
        for v in r:v['sire_id']='';v['dam_id']=''
        d,_=prepare_frame(pd.DataFrame(r))
        x=make_features(d[d.year<2018],d[d.year==2018])
        self.assertFalse(x.kin_exposed.any())
        self.assertTrue(np.allclose(x.kin,0))
    def test_peer_features_equal_independent_scalar_reference(self):
        d,_=prepare_frame(pd.DataFrame(races()+races('2017-02-01')+races('2018-01-01',100)))
        h=d[d.year<2018];f=d[d.year==2018];x=make_features(h,f)
        target=x.iloc[0]
        others=h[(h.sire_id==target.sire_id)&(h.horse!=target.horse)]
        individual=others.groupby('horse',observed=True).y.mean().to_dict()
        expected=sum(v-.5 for v in individual.values())/(8+len(individual))
        self.assertAlmostEqual(target.sire,expected)
        self.assertEqual(target.sire_relatives,len(individual))
    def test_history_parent_conflict_cannot_make_a_relative(self):
        rows=races()+races('2017-02-01')+races('2018-01-01',100)
        rows[6]['sire_id']='CHANGED'
        d,_=prepare_frame(pd.DataFrame(rows))
        x=make_features(d[d.year<2018],d[d.year==2018])
        self.assertEqual(x.iloc[0].sire_relatives,2)
    def test_unverified_dataframe_cannot_receive_real_source_label(self):
        from ecology_japan_archive_forward import run_analysis
        rows=races('2017-01-01')+races('2018-01-01',100)+races('2019-01-01',200)
        result=run_analysis(pd.DataFrame(rows),years=(2019,))
        self.assertEqual(result['status'],'UNVERIFIED_INPUT_TEMPORAL_RANK_TEST')
        self.assertFalse(result['source']['archive_digest_verified'])
    def test_weights_train_on_validation_and_include_zero(self):
        d,_=prepare_frame(pd.DataFrame(races()+races('2018-01-01',100)))
        x=make_features(d[d.year<2018],d[d.year==2018])
        w=fit_weights(x);pred=predict(x,w)
        self.assertEqual(set(w),{'M0','M_sire','M_dam','M_kin','M_trainer','M_trainer_kin','M_name'})
        self.assertTrue(np.all((pred>=0)&(pred<=1)))
        self.assertTrue(np.allclose(pred[:,0],x.base))

if __name__=='__main__':unittest.main()
