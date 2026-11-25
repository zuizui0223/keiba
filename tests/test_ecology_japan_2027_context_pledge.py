from copy import deepcopy
import base64
import unittest
from test_ecology_japan_2027_context_history_fit import fixture, C, h
from ecology_japan_2027_context_pledge import *

CODE="a"*40
PARENT="b"*40
COMMIT="c"*40
RUN=123
def mock(pledge):
    path=filename(pledge)
    base="https://api.github.com/repos/"+REPO+"/"
    raw=canonical(pledge)
    urls={
        base+"actions/runs/"+str(RUN):{"id":RUN,"head_sha":COMMIT,"event":"push","run_attempt":1,
            "status":"completed","conclusion":"success","path":MOCK_WORKFLOW,
            "repository":{"full_name":REPO},"head_repository":{"full_name":REPO},
            "created_at":"2026-12-30T00:00:00Z"},
        base+"commits/"+COMMIT:{"sha":COMMIT,"parents":[{"sha":PARENT}],"files":[{"filename":path,"status":"added"}]},
        base+"compare/"+CODE+"..."+PARENT:{"status":"ahead","merge_base_commit":{"sha":CODE}},
        base+"contents/"+path+"?ref="+COMMIT:{"type":"file","encoding":"base64","path":path,
            "content":base64.b64encode(raw).decode(),"sha":blob_sha(raw)}}
    return urls,path

class Pledge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history,cls.parents,registry=fixture()
        cls.private,cls.receipt,cls.fitted=fit(cls.history,cls.parents,registry,cutoff_jst=C,frozen_at_jst=C)
        cls.pledge=build_pledge(cls.private,cls.receipt,cls.fitted,code_commit=CODE)
    def test_whitelist_and_replay(self):
        p=self.pledge
        self.assertEqual(set(p),PUBLIC_FIELDS)
        self.assertNotIn("H:FICTIONAL_",str(p));self.assertNotIn("R:FICTIONAL_",str(p))
        urls,path=mock(p)
        x=reopen(self.private,self.receipt,self.fitted,p,self.history,self.parents,
                 commit=COMMIT,run_id=RUN,relative_path=path,github_json_get=urls.__getitem__)
        self.assertFalse(x["external_attestation_verified"]);self.assertEqual(x["real_observations"],0)
    def test_bad_run_rejected(self):
        for k,v in [("event","workflow_dispatch"),("run_attempt",2),("created_at","2027-01-01T00:00:00Z"),
                    ("conclusion","failure"),("head_sha","d"*40)]:
            urls,path=mock(self.pledge);next(iter(urls.values()))[k]=v
            with self.assertRaises(ValueError):
                replay_original(self.pledge,commit=COMMIT,run_id=RUN,relative_path=path,github_json_get=urls.__getitem__)
    def test_modified_not_new_and_wrong_code(self):
        urls,path=mock(self.pledge);list(urls.values())[1]["files"][0]["status"]="modified"
        with self.assertRaisesRegex(ValueError,"NEW_FILE_ONLY"):
            replay_original(self.pledge,commit=COMMIT,run_id=RUN,relative_path=path,github_json_get=urls.__getitem__)
        urls,path=mock(self.pledge);list(urls.values())[2]["merge_base_commit"]["sha"]="d"*40
        with self.assertRaisesRegex(ValueError,"CODE_ANCESTRY"):
            replay_original(self.pledge,commit=COMMIT,run_id=RUN,relative_path=path,github_json_get=urls.__getitem__)
    def test_original_blob_and_input_drift(self):
        urls,path=mock(self.pledge);list(urls.values())[-1]["sha"]="d"*40
        with self.assertRaisesRegex(ValueError,"ORIGINAL_BLOB"):
            replay_original(self.pledge,commit=COMMIT,run_id=RUN,relative_path=path,github_json_get=urls.__getitem__)
        urls,path=mock(self.pledge);history=deepcopy(self.history);history[0]["surface"]="dirt" if history[0]["surface"]=="turf" else "turf"
        with self.assertRaisesRegex(ValueError,"INPUT_HASH_DRIFT"):
            reopen(self.private,self.receipt,self.fitted,self.pledge,history,self.parents,
                   commit=COMMIT,run_id=RUN,relative_path=path,github_json_get=urls.__getitem__)
    def test_end_to_end_score_includes_unknown_and_empty(self):
        urls,path=mock(self.pledge)
        rid="R:FICTIONAL_target";a=h("new0");b=h("new1")
        races=[{"race":rid,"start_at":"2027-01-02T12:00:00+09:00","surface":"turf",
                "distance":1800,"circuit":"JRA","declared_entries":2}]
        entries=[{"race":rid,"horse":x,"status":"STARTED"} for x in (a,b)]
        results=[{"race":rid,"horse":x,"rank":i,"known_at":"2027-01-02T15:00:00+09:00"} for i,x in enumerate((a,b),1)]
        z=replay_and_score(self.private,self.receipt,self.fitted,self.pledge,self.history,self.parents,races,entries,results,
                           commit=COMMIT,run_id=RUN,relative_path=path,github_json_get=urls.__getitem__,
                           scored_at_jst="2027-03-29T00:00:00+09:00")
        self.assertEqual(z["score"]["coverage"]["strict_observed_horses"],2)
        self.assertEqual(z["score"]["coverage"]["no_observed_candidate_start_horses"],6)
        self.assertEqual(z["score"]["results"][str(SEEDS[0])]["all"]["contrasts"]["N_minus_G"]["status"],"HOLD_LOW_SUPPORT")
        self.assertFalse(z["external_attestation_verified"])
        self.assertNotIn("H:FICTIONAL_",str(z))
if __name__=="__main__":unittest.main()
