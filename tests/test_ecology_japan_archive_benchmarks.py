from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ecology_japan_archive_benchmarks import midrank_score,cluster_comparison
class MidrankBenchmarkTests(unittest.TestCase):
    def test_constant_is_half_without_using_any_test_outcome_to_fit(self):
        y=np.array([0.,.2,.4,.6,.8,1.]);ids=['a','b','c','d','e','f']
        r=midrank_score(y,ids)
        self.assertAlmostEqual(r['RMSE'],float(np.sqrt(np.mean((y-.5)**2))))
        self.assertAlmostEqual(r['MAE'],.3)
    def test_horses_not_starts_have_equal_weights(self):
        r=midrank_score(np.array([0.,0.,.5]),['a','a','b'])
        self.assertAlmostEqual(r['RMSE'],np.sqrt(.125))
    def test_pairwise_cluster_intervals_have_direct_direction(self):
        y=np.array([0.,0.,1.,1.]);p=np.array([.2,.2,.8,.8]);groups=['a','a','b','b']
        r=cluster_comparison(y,p,groups,groups,B=19)
        self.assertAlmostEqual(r['midrank_minus_model_RMSE'],.3)
        np.testing.assert_allclose(r['percentile_95_interval'],[.3,.3])
if __name__=='__main__':unittest.main()
