import sys
from pathlib import Path
import unittest
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from ecology_japan_2027_context_source_adapter import prepare,adapt_and_fit
from test_ecology_japan_2027_context_history_fit import fixture, h, T, C
from ecology_japan_2027_context_allocation_kernel import digest

CAP="2026-12-29T00:00:00+09:00"
DAY="2024-02-01T12:00:00+09:00"
KNOWN="2024-02-01T15:00:00+09:00"
LATER="2024-02-02T00:00:00+09:00"
def rr(i):return "R:FICTIONAL_"+str(i)
def reg(i,status="NOT_CERTIFIED"):
    return {"horse":h(i),"known_at":T,"unraced_status":status,
            "unraced_known_at":CAP if status=="VERIFIED_UNRACED" else ""}
def parent(i,s="KNOWN"):
    return {"horse":h(i),"sire_state":s,"sire":h("s") if s=="KNOWN" else "","known_at":T}
def race(i,n=2,surface="turf",distance=1800):
    return {"race":rr(i),"start_at":DAY,"known_at":DAY,"surface":surface,
            "distance":distance,"circuit":"JRA","declared_entries":n}
def entry(i,j,status="STARTED"):
    return {"race":rr(i),"horse":h(j),"status":status,"known_at":KNOWN}
def result(i,j,rank,known=KNOWN,status="CLASSIFIED"):
    return {"race":rr(i),"horse":h(j),"rank":rank,"status":status,"known_at":known}

def small():
    registry=[reg(0),reg(1),reg(2),reg(3,"VERIFIED_UNRACED")]
    parents=[parent(0),parent(1,"UNKNOWN"),parent(2,"UNRESOLVED"),parent(3)]
    races=[race(1),race(2)]
    entries=[entry(1,0),entry(1,1),entry(2,1),entry(2,2)]
    results=[result(1,0,1),result(1,1,2,LATER),result(2,1,1)]
    return registry,parents,races,entries,results
def run(x):
    return prepare(*x,captured_at_jst=CAP,cutoff_jst=C)
class Adapter(unittest.TestCase):
    def test_complete_and_partial_races(self):
        p,q=run(small())
        self.assertEqual(q["eligible_race_status"],{"STRICT_COMPLETE":1,"INCOMPLETE_OR_UNCLASSIFIED":1})
        self.assertEqual(q["strict_history_starts"],2)
        self.assertTrue(all(x["known_at"]==LATER for x in p["history"]))
        a={r["horse"]:r for r in p["registry"]}
        self.assertEqual(a[h(2)]["prior_n"],0)
        self.assertEqual(a[h(2)]["history_state"],"OBSERVED_HISTORY")
        self.assertEqual(a[h(3)]["history_state"],"VERIFIED_UNRACED")
        self.assertEqual(q["registry_horses_with_observed_eligible_start_but_no_strict_history"],1)
        self.assertEqual(q["prepared_sha256"],digest(p))
        self.assertNotIn("H:FICTIONAL_",str(q))
        self.assertNotIn("R:FICTIONAL_",str(q))
    def test_parent_version_change(self):
        z=list(small());z[1].append(dict(parent(0),known_at=KNOWN))
        p,q=run(z)
        self.assertEqual(next(x["known_at"] for x in p["parents"] if x["horse"]==h(0)),T)
        z[1].append(dict(parent(0),sire=h("s2"),known_at=LATER))
        with self.assertRaisesRegex(ValueError,"VERSIONED_PARENT_CHANGE"):run(z)
    def test_unraced_certificate_conflict_and_late_result(self):
        z=list(small());z[0][0]=reg(0,"VERIFIED_UNRACED")
        with self.assertRaisesRegex(ValueError,"UNRACED_CONTRADICTION"):run(z)
        z=list(small());z[4][0]["known_at"]=C
        with self.assertRaisesRegex(ValueError,"RESULT_TIME"):run(z)
    def test_missing_state_and_wrong_id(self):
        z=list(small());z[1]=z[1][1:]
        with self.assertRaisesRegex(ValueError,"MISSING_HISTORICAL_PARENT_STATE"):run(z)
        z=list(small());z[0][0]["horse"]="H:123456"
        with self.assertRaisesRegex(ValueError,"SYNTHETIC_ID_ONLY"):run(z)
    def test_actual_fictional_source_to_fit(self):
        # Pair original fictional starts into same-day same-surface races;
        # every race gets two fully classified entries, no generated extra
        # histories. This preserves all original individual start counts.
        hist,parents,registry=fixture()
        from collections import defaultdict
        g=defaultdict(list)
        for x in hist:g[(x["start_at"],x["surface"])].append(x)
        races=[];entries=[];results=[];i=0
        for (day,surface),rows in sorted(g.items()):
            self.assertEqual(len(rows)%2,0)
            for j in range(0,len(rows),2):
                i+=1;pair=rows[j:j+2];rid=rr(i)
                self.assertNotEqual(pair[0]["horse"],pair[1]["horse"])
                races.append({"race":rid,"start_at":day,"known_at":day,"surface":surface,
                              "distance":1800,"circuit":"JRA","declared_entries":2})
                for rank,x in enumerate(pair,1):
                    entries.append({"race":rid,"horse":x["horse"],"status":"STARTED","known_at":x["known_at"]})
                    results.append({"race":rid,"horse":x["horse"],"status":"CLASSIFIED","rank":rank,"known_at":x["known_at"]})
        raw_reg=[{"horse":x["horse"],"known_at":x["registry_known_at"],
                  "unraced_status":"NOT_CERTIFIED","unraced_known_at":""} for x in registry]
        have={x["horse"] for x in parents}
        parents=parents+[{"horse":x["horse"],"sire_state":x["sire_state"],"sire":x["sire"],"known_at":T}
                         for x in registry if x["horse"] not in have]
        p,q,z=adapt_and_fit(raw_reg,parents,races,entries,results,captured_at_jst=CAP,
                            cutoff_jst=C,frozen_at_jst=C)
        self.assertEqual(z["adapter"]["strict_history_starts"],len(hist))
        self.assertEqual(q["horses"],8);self.assertEqual(q["prediction_rows"],24)
        self.assertEqual(z["real_observations"],0)
        self.assertNotIn("H:FICTIONAL_",str(z));self.assertNotIn("R:FICTIONAL_",str(z))
if __name__=="__main__":unittest.main()
