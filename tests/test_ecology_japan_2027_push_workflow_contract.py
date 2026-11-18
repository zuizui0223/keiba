"""Source-only audit of production GitHub Actions pre-race push attestation.

Never contacts GitHub or official JRA data; does not create a future pledge.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
PUSH=ROOT/".github/workflows/ecology-japan-2027-immutable-push-attestation.yml"


class ProductionPushGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=PUSH.read_text(encoding="utf-8")

    def test_strict_push_only_no_retroactive_manual_or_pr_trigger(self):
        s=self.source
        self.assertIn("\non:\n  push:\n",s)
        self.assertIn('docs/commitments/2027/*.json',s)
        self.assertNotRegex(s,r"(?m)^\s{2}(pull_request|workflow_dispatch|schedule):")

    def test_external_server_created_time_not_author_commit_timestamp(self):
        s=self.source
        self.assertIn("_fetch_current_run()",s)
        self.assertIn("attest_run(bundle,run,repo=repo,sha=sha)",s)
        self.assertIn("created_at",s)
        self.assertNotIn("git show --format=%at",s)
        self.assertNotIn("date --date",s)

    def test_only_new_opaque_files_in_exact_commit_allowlisted(self):
        s=self.source
        for v in (
            'fetch-depth: 0',
            'persist-credentials: false',
            'git","rev-parse","HEAD',
            'git","diff","--no-renames","--name-status',
            'status!="A"',
            'docs/commitments/2027/[a-f0-9]{32}',
            'HOLD_ATTEMPT_TO_REWRITE_EXISTING_OR_IDENTIFY_PLEDGE',
        ):
            self.assertIn(v,s,v)

    def test_no_write_scope_or_raw_jra_horse_data_download(self):
        s=self.source
        self.assertIn("contents: read",s)
        self.assertIn("actions: read",s)
        self.assertIn("GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}",s)
        self.assertNotIn("contents: write",s)
        self.assertNotIn("actions/upload-artifact",s)
        self.assertNotIn("jra-van.jp/",s)
        self.assertNotIn("JRA_VAN_PASSWORD",s)


if __name__=="__main__":
    unittest.main()
