import sys
from pathlib import Path
import unittest
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2027_context_allocation_kernel import *

T="2026-12-30T00:00:00+09:00"
C="2026-12-31T00:00:00+09:00"
S="2027-01-02T12:00:00+09:00"
R="2027-01-02T14:00:00+09:00"
A="2027-03-29T00:00:00+09:00"
def h(i):return "H:FICTIONAL_"+str(i)
def race(i):return "R:FICTIONAL_"+str(i)

def fixture(n=4):
    registry=[];components=[]
    for i in range(n):
        known=i%4!=3
        registry.append({"horse":h(i),"sire_state":"KNOWN" if known else "UNKNOWN",
            "sire":h("s"+str(i%40)) if known else "","prior_n":0 if i%2==0 else 8,
            "history_state":"VERIFIED_UNRACED" if i%2==0 else "OBSERVED_HISTORY",
            "registry_known_at":T,"parent_known_at":T if known else ""})
        for seed in SEEDS:
            components.append({"horse":h(i),"seed":seed,"N":.4,"d":.2 if known else 0.,
                               "peer_n":4 if known else 0,"known_at":T})
    weights={str(seed):{str(k):{"monotone":[1.,.7,.4,.2],"pooled":.5,
        "support":[{"informative_horses":100,"informative_sires":30} for _ in BINS]} for k in (0,1)} for seed in SEEDS}
    return registry,components,weights

def freeze_fixture(n=4):
    return freeze(*fixture(n),cutoff_jst=C,frozen_at_jst=C)
def race_row(i,declared=2,surface="turf"):
    return {"race":race(i),"start_at":S,"surface":surface,"distance":1800,"circuit":"JRA","declared_entries":declared}
def entry(i,j,status="STARTED"):
    return {"race":race(i),"horse":h(j),"status":status}
def result(i,j,rank):
    return {"race":race(i),"horse":h(j),"rank":rank,"known_at":R}

class Kernel(unittest.TestCase):
    def test_frozen_all_horses_all_seeds(self):
        p,q=freeze_fixture()
        self.assertEqual(q["horses"],4)
        self.assertEqual(q["prediction_rows"],12)
        self.assertEqual(q["real_observations"],0)
        self.assertNotIn(h(0),str(q))
        z=[x for x in p["predictions"] if x["horse"]==h(3)]
        self.assertTrue(all(x["G"]==x["N"]==x["F"] for x in z))
        self.assertEqual(verify(p,q)[h(0)]["history_state"],"VERIFIED_UNRACED")
    def test_missing_and_duplicate_predictions(self):
        r,c,w=fixture()
        with self.assertRaisesRegex(ValueError,"PREDICTION_UNIVERSE"):
            freeze(r,c[:-1],w,cutoff_jst=C,frozen_at_jst=C)
        with self.assertRaisesRegex(ValueError,"DUPLICATE_KEY"):
            freeze(r,c+[c[0]],w,cutoff_jst=C,frozen_at_jst=C)
    def test_late_and_unknown_inputs(self):
        for field in ("registry_known_at","parent_known_at"):
            r,c,w=fixture();r[0][field]=C
            with self.assertRaises(ValueError):
                freeze(r,c,w,cutoff_jst=C,frozen_at_jst=C)
        r,c,w=fixture();c[0]["known_at"]=C
        with self.assertRaisesRegex(ValueError,"LATE_COMPONENT"):
            freeze(r,c,w,cutoff_jst=C,frozen_at_jst=C)
        r,c,w=fixture();r[3]["sire"]=h("s")
        with self.assertRaisesRegex(ValueError,"UNKNOWN_SHARED_PARENT"):
            freeze(r,c,w,cutoff_jst=C,frozen_at_jst=C)
        r,c,w=fixture();c[-1]["d"]=.1
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_NONZERO"):
            freeze(r,c,w,cutoff_jst=C,frozen_at_jst=C)
    def test_invalid_weights_and_nonfictional_id(self):
        r,c,w=fixture();w[str(SEEDS[0])]["0"]["monotone"]=[.1,.2,.1,0.]
        with self.assertRaisesRegex(ValueError,"WEIGHT_BOUNDS"):
            freeze(r,c,w,cutoff_jst=C,frozen_at_jst=C)
        r,c,w=fixture();w[str(SEEDS[0])]["0"]["support"][0]["informative_sires"]=29
        with self.assertRaisesRegex(ValueError,"CALIBRATION_SUPPORT"):
            freeze(r,c,w,cutoff_jst=C,frozen_at_jst=C)
        r,c,w=fixture();r[0]["horse"]="H:12345"
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_ID_ONLY"):
            freeze(r,c,w,cutoff_jst=C,frozen_at_jst=C)
    def test_commitment_mutation(self):
        p,q=freeze_fixture()
        for k in ("registry","components","weights","predictions"):
            a=deepcopy(p)
            if k=="registry":a[k][0]["prior_n"]=1
            elif k=="components":a[k][0]["N"]=.1
            elif k=="weights":a[k][str(SEEDS[0])]["0"]["pooled"]=.4
            else:a[k][0]["G"]=.9
            with self.assertRaises(ValueError):verify(a,q)
    def test_coverage_and_no_silent_imputation(self):
        p,q=freeze_fixture(6)
        races=[race_row(1,3),race_row(2,2,"dirt"),race_row(3,2)]
        entries=[entry(1,0),entry(1,3),entry(1,99,"WITHDRAWN"),
                 entry(2,0),entry(2,1),entry(3,2),entry(3,98)]
        results=[result(1,0,1),result(1,3,2),result(2,0,1)]
        s=score(p,q,races,entries,results,scored_at_jst=A)
        z=s["coverage"]
        self.assertEqual(z["strict_observed_horses"],2)
        self.assertEqual(z["strict_observed_starts"],2)
        self.assertEqual(z["observed_but_no_strict_start_horses"],2)
        self.assertEqual(z["no_observed_candidate_start_horses"],2)
        self.assertEqual(z["strict_with_additional_unresolved_observations_horses"],1)
        self.assertEqual(z["outside_universe_observed_horses"],2)
        self.assertEqual(z["race_status"],{"STRICT_COMPLETE":1,"INCOMPLETE_OR_UNCLASSIFIED":2})
        x=s["results"][str(SEEDS[0])]
        self.assertEqual(x["all"]["horses"],2)
        self.assertEqual(x["unknown_or_unresolved_sire"]["contrasts"]["N_minus_G"]["MSE_gain"],0.)
        self.assertEqual(x["all"]["contrasts"]["N_minus_G"]["status"],"HOLD_LOW_SUPPORT")
        self.assertNotIn(h(0),str(s))
    def test_score_bad_time_and_ranks(self):
        p,q=freeze_fixture()
        e=[entry(1,0),entry(1,1)]
        with self.assertRaisesRegex(ValueError,"PREWINDOW_SCORE"):
            score(p,q,[race_row(1)],e,[],scored_at_jst=R)
        bad=[result(1,0,1),result(1,1,1)]
        z=score(p,q,[race_row(1)],e,bad,scored_at_jst=A)
        self.assertEqual(z["coverage"]["strict_observed_horses"],0)
    def test_known_sire_support_not_inflated_by_missing(self):
        rows=[{"horse":h(i),"sire_state":"UNKNOWN","sire":""} for i in range(130)]
        z=interval(rows,[0.]*130,SEEDS[0])
        self.assertEqual(z["clusters"],130);self.assertEqual(z["known_sires"],0)
        self.assertEqual(z["status"],"HOLD_LOW_SUPPORT")
        rows=[{"horse":h(i),"sire_state":"KNOWN","sire":h("s"+str(i%35))} for i in range(140)]
        z=interval(rows,[.02]*140,SEEDS[0])
        self.assertEqual(z["status"],"DESCRIPTIVE")
        self.assertAlmostEqual(z["CI95_pointwise"][0],.02)
if __name__=="__main__":unittest.main()
