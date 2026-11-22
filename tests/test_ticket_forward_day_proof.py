"""Standalone synthetic oracle for pre-first-start GitHub day-universe sealing."""
import base64
from copy import deepcopy
from datetime import datetime, timedelta
import json
import unittest

from scripts.ticket_forward_day_proof import attest_day_plan, validate_day_evidence
from scripts.ticket_forward_freeze import REPO_ROOT, canonical, git_blob_sha1, sha256_bytes
from scripts.ticket_forward_universe import plan_day

DAY = "2026-11-28"
SOURCE_RAW = b"<html>synthetic complete 12-race official table (not a real source)</html>"


def schedule_fixture():
    start = datetime.fromisoformat(f"{DAY}T10:00:00+09:00")
    return {
        "schema_version": 1,
        "schedule_date": DAY,
        "captured_at_jst": f"{DAY}T09:30:00+09:00",
        "source_url": "https://www.jra.go.jp/keiba/calendar2026/2026/11/1128.html",
        "source_text_sha256": sha256_bytes(SOURCE_RAW),
        "races": [
            {
                "race_id": f"{DAY}-TOKYO-{i:02d}",
                "venue": "東京",
                "date": DAY,
                "race_number": i,
                "scheduled_start_jst": (start + timedelta(minutes=25 * (i-1))).isoformat(),
                "surface": "芝" if i % 2 else "ダ",
                "declared_runner_count": 12,
                "status": "RUNNING",
            }
            for i in range(1, 13)
        ],
    }


def evidence():
    manifest = json.loads(
        (REPO_ROOT / "docs/betting/ticket-forward-v1-manifest.json").read_text(encoding="utf-8")
    )
    schedule = schedule_fixture()
    raw = canonical(schedule)
    plan = plan_day(schedule, manifest, schedule_raw=raw)
    return (raw, SOURCE_RAW, canonical(plan), manifest)


class DaySealTests(unittest.TestCase):
    def test_recompute_support_and_hashes(self):
        raw, source, stored_plan, manifest = evidence()
        proof = validate_day_evidence(raw, source, stored_plan, manifest)
        self.assertEqual(proof["status"], "DAY_EVIDENCE_CONSISTENT_BUT_NOT_SERVER_ATTESTED")
        self.assertEqual(proof["planned_races"], 10)
        self.assertEqual(proof["schedule_races"], 12)
        self.assertEqual(proof["source_text_sha256"], sha256_bytes(source))
        self.assertEqual(proof["day_plan_file_sha256"], sha256_bytes(stored_plan))

    def test_reject_changed_source_or_posthoc_selection(self):
        raw, source, stored_plan, manifest = evidence()
        with self.assertRaisesRegex(ValueError, "source_sha_mismatch"):
            validate_day_evidence(raw, source + b"x", stored_plan, manifest)
        modified = json.loads(stored_plan)
        modified["included_first_ten"].pop()
        with self.assertRaisesRegex(ValueError, "not_reproducible"):
            validate_day_evidence(raw, source, canonical(modified), manifest)
        modified = json.loads(raw)
        modified["races"][0]["declared_runner_count"] = 8
        with self.assertRaisesRegex(ValueError, "raw_source_sha_mismatch|not_reproducible"):
            validate_day_evidence(canonical(modified), source, stored_plan, manifest)

    def test_github_server_created_and_all_three_blobs_required(self):
        raw, source, stored_plan, manifest = evidence()
        run_id = 123456
        path = f"holdout/ticket-forward-v1/{DAY}/day-plan.json"
        run = {
            "created_at": "2026-11-28T00:40:00Z",  # 09:40 JST
            "conclusion": "success",
            "event": "push",
            "repository": {"full_name": "zuizui0223/keiba"},
            "head_sha": "d" * 40,
        }
        file_bytes = {
            "day-plan.json": stored_plan,
            "day-schedule.json": raw,
            "day-schedule-source.txt": source,
        }
        def getter(url):
            if "/actions/runs/" in url:
                return run
            for name, payload in file_bytes.items():
                if f"/{name}?ref=" in url:
                    return {
                        "encoding": "base64",
                        "path": f"holdout/ticket-forward-v1/{DAY}/{name}",
                        "content": base64.b64encode(payload).decode("ascii"),
                        "sha": git_blob_sha1(payload),
                    }
            raise AssertionError(f"unrecognized API route {url}")
        kwargs = {"run_id": run_id, "plan_path": path, "getter": getter}
        sealed = attest_day_plan(raw, source, stored_plan, manifest, **kwargs)
        self.assertEqual(sealed["status"], "DAY_PLAN_SERVER_SEALED_PRE_FIRST_RACE")
        self.assertEqual(sealed["server_run_id"], run_id)
        self.assertEqual(sealed["git_head_sha"], "d" * 40)
        with self.assertRaises(ValueError):
            attest_day_plan(raw, source, stored_plan, manifest,
                run_id=run_id, plan_path=path.replace("day-plan", "plan"), getter=getter)
        late = dict(run, created_at="2026-11-28T01:01:00Z")
        with self.assertRaisesRegex(ValueError, "not_pre_first_race"):
            attest_day_plan(raw, source, stored_plan, manifest,
                run_id=run_id, plan_path=path,
                getter=lambda url: late if "/actions/runs/" in url else getter(url))
        early = dict(run, created_at="2026-11-28T00:29:00Z")
        with self.assertRaisesRegex(ValueError, "not_pre_first_race"):
            attest_day_plan(raw, source, stored_plan, manifest,
                run_id=run_id, plan_path=path,
                getter=lambda url: early if "/actions/runs/" in url else getter(url))
        def wrong_bytes(url):
            item = getter(url)
            if "/day-schedule-source.txt?ref=" in url:
                item["content"] = base64.b64encode(b"tampered").decode()
            return item
        with self.assertRaisesRegex(ValueError, "companion_does_not_match"):
            attest_day_plan(raw, source, stored_plan, manifest,
                run_id=run_id, plan_path=path, getter=wrong_bytes)

    def test_official_source_url_cannot_be_replaced_by_blog(self):
        raw, source, stored_plan, manifest = evidence()
        edited = json.loads(raw)
        edited["source_url"] = "https://somebody.example/races"
        with self.assertRaises(ValueError):
            validate_day_evidence(canonical(edited), source, stored_plan, manifest)


if __name__ == "__main__":
    unittest.main()
