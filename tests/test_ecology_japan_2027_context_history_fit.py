import sys
from pathlib import Path
import unittest
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2027_context_history_fit import *
from ecology_japan_2027_context_allocation_kernel import verify

T="2010-01-01T00:00:00+09:00"
C="2026-12-30T00:00:00+09:00"
def h(i):return "H:FICTIONAL_"+str(i)
def rr(i):return "R:FICTIONAL_"+str(i)

def fixture():
    hist=[];parents=[];registry=[]
    # Fictional horse cohorts: 4 information-depth bins; 60 sire groups.
    # Distinct IDs in each target year and 2 horses per sire/bin.
    serial=0
    def record(horse,yr,month,day,surface):
        nonlocal serial
        serial+=1
        stamp=f"{yr}-{month:02d}-{day:02d}T12:00:00+09:00"
        known=f"{yr}-{month:02d}-{day:02d}T15:00:00+09:00"
        hist.append({"race":rr(serial),"horse":horse,"start_at":stamp,
            "known_at":known,"surface":surface,"distance":1800,"circuit":"JRA"})
    for yr in DONOR_YEARS:
        for bin_,n in enumerate((0,2,5,9)):
            for j in range(120):
                horse=h(f"{yr}_{bin_}_{j}");sire=h(f"s{j%60}")
                parents.append({"horse":horse,"sire_state":"KNOWN","sire":sire,"known_at":T})
                for k in range(n):
                    record(horse,yr-1,5,k+1,"turf" if k%2==0 else "dirt")
                record(horse,yr,2,1,"turf" if j%2==0 else "dirt")
                if yr==2026 and j==0:
                    registry.append({"horse":horse,"sire_state":"KNOWN","sire":sire,
                        "prior_n":n+1,"history_state":"OBSERVED_HISTORY","registry_known_at":T,"parent_known_at":T})
    for j,state in enumerate(("KNOWN","UNKNOWN","CONFLICT","UNRESOLVED")):
        horse=h(f"new{j}");sire=h("s0") if state=="KNOWN" else ""
        registry.append({"horse":horse,"sire_state":state,"sire":sire,"prior_n":0,
                         "history_state":"NO_OBSERVED_HISTORY","registry_known_at":T,
                         "parent_known_at":T if state=="KNOWN" else ""})
    return hist,parents,registry

class HistoryFit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=fixture()
        cls.private,cls.receipt,cls.qa=fit(*cls.inputs,cutoff_jst=C,frozen_at_jst=C)
    def test_fitted_freeze(self):
        p,q,z=self.private,self.receipt,self.qa
        self.assertEqual(z["real_observations"],0)
        self.assertEqual(q["horses"],8);self.assertEqual(q["prediction_rows"],24)
        verify(p,q)
        self.assertNotIn("FICTIONAL_",str(z))
        for v in p["weights"].values():
            for w in v.values():
                self.assertTrue(all(a>=b for a,b in zip(w["monotone"],w["monotone"][1:])))
                self.assertTrue(all(b["informative_horses"]>=100 and b["informative_sires"]>=30 for b in w["support"]))
        new=[x for x in p["predictions"] if x["horse"]==h("new0")]
        self.assertTrue(all(abs(x["F"]-x["N"])>1e-8 for x in new))
        unknown=[x for x in p["predictions"] if x["horse"]==h("new1")]
        self.assertTrue(all(x["G"]==x["N"]==x["F"] for x in unknown))
    def test_validation_outcomes_cannot_fit_weights(self):
        hist,parents,reg=deepcopy(self.inputs)
        for x in hist:
            if x["start_at"].startswith("2026-02"):
                x["surface"]="dirt" if x["surface"]=="turf" else "turf"
        p,q,z=fit(hist,parents,reg,cutoff_jst=C,frozen_at_jst=C)
        self.assertEqual(p["weights"],self.private["weights"])
        self.assertNotEqual(z["history_sha256"],self.qa["history_sha256"])
        self.assertNotEqual(p["predictions"],self.private["predictions"])
    def test_future_late_and_count_guards(self):
        hist,parents,reg=deepcopy(self.inputs)
        hist[0]["known_at"]=C
        with self.assertRaisesRegex(ValueError,"HISTORY_TIME"):
            fit(hist,parents,reg,cutoff_jst=C,frozen_at_jst=C)
        hist,parents,reg=deepcopy(self.inputs)
        reg[0]["prior_n"]+=1
        with self.assertRaisesRegex(ValueError,"REGISTRY_HISTORY_COUNT_MISMATCH"):
            fit(hist,parents,reg,cutoff_jst=C,frozen_at_jst=C)
    def test_disjoint_chronology(self):
        hist,parents,reg=self.inputs
        hh,pp,_=validate(hist,parents,reg,time(C))
        p=make_panel(hh,pp,SEEDS[0],time(C))
        original=donor_profile(p,2025,0)
        mutated=[dict(x,residual=99.) if x["year"]>=2025 or x["half"]==0 else x for x in p]
        self.assertEqual(original,donor_profile(mutated,2025,0))
    def test_pooling_and_support(self):
        self.assertEqual(decreasing_projection([.8,.2,.6,.1],[1.,1.,1.,1.]),[.8,.4,.4,.1])
        with self.assertRaisesRegex(ValueError,"CALIBRATION_BIN_SUPPORT"):
            calibrate([{"year":2019,"half":1,"horse":h(1),"sire":h(2),"prior_n":0,"d":.2,"r":.1}],0)
if __name__=="__main__":unittest.main()
