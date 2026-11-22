"""Strict synthetic pre-post gates and independent GitHub-server receipt checks."""
import base64
import copy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import unittest

from scripts.ticket_forward_freeze import (
    REPO_ROOT, _attest_github_run, canonical, freeze_forecast, git_blob_sha1,
    score_frozen, validate_capture, validate_manifest, verify_forecast_integrity,
    sha256_bytes,
)

SOURCE_PAGES = {
    "win": b"<html>synthetic pre-race win source</html>",
    "wide": b"<html>synthetic pre-race wide source</html>",
}

MANIFEST_PATH = REPO_ROOT / "docs/betting/ticket-forward-v1-manifest.json"
FORECAST_ASOF = "2026-11-28T14:40:00+09:00"
POST_TIME = "2026-11-28T15:00:00+09:00"
RESULT_SOURCE = """# レース結果2026年11月28日（土曜）5回東京7日 11レース

| 着順 | 枠 | 馬 番 | 馬名 | タイム |
| --- | --- | --- | --- | --- |
| 1 |  | 9 | 架空甲 | 1:33.5 |
| 2 |  | 2 | 架空乙 | 1:33.6 |
| 3 |  | 3 | 架空丙 | 1:33.7 |
| 4 |  | 1 | 架空丁 | 1:34.1 |
""".encode("utf-8")


def make_capture():
    nums = list(range(1, 10))
    return {
        "schema_version": 1,
        "race": {
            "race_id": "2026-11-28-TOKYO-11",
            "date": "2026-11-28", "venue": "東京", "race_number": 11,
            "scheduled_start_jst": POST_TIME,
            "horses": [{"number": n, "frame": min(n, 8)} for n in nums],
        },
        "markets": {
            "win": {
                "source_url": "https://www.jra.go.jp/JRADB/accessO.html?synthetic=yes",
                "observed_at_jst": "2026-11-28T14:39:05+09:00",
                "updated_at_jst": "2026-11-28T14:36:00+09:00",
                "updated_time_basis": "source_visible",
                "raw_page_sha256": sha256_bytes(SOURCE_PAGES["win"]),
                "quotes": [
                    {"selection": [n], "odds_low": 2.5 + n, "odds_high": 2.5 + n}
                    for n in nums
                ],
            },
            "wide": {
                "source_url": "https://www.jra.go.jp/JRADB/accessO.html?synthetic_wide=yes",
                "observed_at_jst": "2026-11-28T14:39:10+09:00",
                "updated_at_jst": "2026-11-28T14:37:00+09:00",
                "updated_time_basis": "source_visible",
                "raw_page_sha256": sha256_bytes(SOURCE_PAGES["wide"]),
                "quotes": [
                    {"selection": [i, j],
                     "odds_low": 6.0+i+j,
                     "odds_high": 6.5+i+j}
                    for i in nums for j in nums if i < j
                ],
            },
        },
    }


def make_result():
    return {
        "race_id": "2026-11-28-TOKYO-11",
        "observed_at_jst": "2026-11-28T15:35:00+09:00",
        "source_url": "https://jra.jp/JRADB/accessS.html?synthetic=yes",
        "source_text_sha256": sha256_bytes(RESULT_SOURCE),
        "top3": [9, 2, 3],
    }


class FutureEightTicketProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def freeze(self, capture=None, asof=FORECAST_ASOF):
        c = make_capture() if capture is None else capture
        return freeze_forecast(c, self.manifest, asof,
                               capture_raw=canonical(c), source_pages=SOURCE_PAGES)

    def test_manifest_pins_actual_source_blobs_and_controls(self):
        validate_manifest(self.manifest)
        self.assertEqual(self.manifest["holdout_attempts"], 30)
        self.assertEqual(self.manifest["primary_loss"], "ordered_top3_log_loss")
        m = copy.deepcopy(self.manifest)
        m["wide_alpha"] = 0.65
        with self.assertRaises(ValueError):
            validate_manifest(m)
        m = copy.deepcopy(self.manifest)
        m["pinned_source_git_blob_sha1"]["scripts/ticket_type_models.py"] = "0"*40
        with self.assertRaises(ValueError):
            validate_manifest(m)

    def test_freeze_contains_immutable_complete_order_distribution(self):
        out = self.freeze()
        self.assertEqual(out["status"], "PRE_RACE_CANDIDATE_UNATTESTED")
        self.assertEqual(len(out["ordered_top3_probs"]), 9*8*7)
        self.assertAlmostEqual(math.fsum(row[3] for row in out["ordered_top3_probs"]), 1)
        self.assertAlmostEqual(math.fsum(row[4] for row in out["ordered_top3_probs"]), 1)
        verify_forecast_integrity(out, self.manifest)
        self.assertNotIn("top3", out)
        self.assertEqual(len(out["integrity_sha256"]), 64)
        self.assertEqual(out["race_id"], "2026-11-28-TOKYO-11")

    def test_rejects_any_target_result_in_forecast_capture(self):
        c = make_capture()
        c["race"]["top3"] = [1, 2, 3]
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["wide"]["quotes"][0]["payouts"] = {"win": 1000}
        with self.assertRaises(ValueError):
            self.freeze(c)

    def test_raw_source_evidence_must_reproduce_captured_digest(self):
        c = make_capture()
        with self.assertRaises(ValueError):
            freeze_forecast(c, self.manifest, FORECAST_ASOF,
                            capture_raw=canonical(c),
                            source_pages={"win": b"changed", "wide": SOURCE_PAGES["wide"]})
        with self.assertRaises(ValueError):
            freeze_forecast(c, self.manifest, FORECAST_ASOF,
                            capture_raw=canonical(c), source_pages={})

    def test_fixed_post_window_and_no_future_market(self):
        with self.assertRaises(ValueError):
            self.freeze(asof="2026-11-28T14:50:00+09:00")
        with self.assertRaises(ValueError):
            self.freeze(asof="2026-11-28T14:30:00+09:00")
        with self.assertRaises(ValueError):
            self.freeze(asof="2026-11-28T15:10:00+09:00")
        c = make_capture()
        c["markets"]["win"]["observed_at_jst"] = "2026-11-28T14:42:00+09:00"
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["win"]["updated_at_jst"] = "2026-11-28T14:42:00+09:00"
        with self.assertRaises(ValueError):
            self.freeze(c)

    def test_holds_stale_unknown_origin_and_async_prices(self):
        c = make_capture()
        c["markets"]["wide"]["updated_time_basis"] = "receipt_inferred"
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["wide"]["updated_at_jst"] = "2026-11-28T14:20:00+09:00"
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["wide"]["observed_at_jst"] = "2026-11-28T14:36:00+09:00"
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["wide"]["raw_page_sha256"] = None
        with self.assertRaises(ValueError):
            self.freeze(c)

    def test_holds_incomplete_duplicate_or_invalid_odds_and_field(self):
        c = make_capture()
        c["markets"]["wide"]["quotes"].pop()
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["wide"]["quotes"][-1]["selection"] = [1,2]
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["win"]["quotes"][0]["odds_low"] = 0
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["race"]["horses"].pop()
        with self.assertRaises(ValueError):
            self.freeze(c)
        c = make_capture()
        c["markets"]["wide"]["source_url"] = "https://not-a-jra-source.example/odds"
        with self.assertRaises(ValueError):
            self.freeze(c)

    def test_manifest_earliest_date_excludes_archived_development(self):
        c = make_capture()
        c["race"]["date"] = "2026-10-18"
        c["race"]["scheduled_start_jst"] = "2026-10-18T15:00:00+09:00"
        with self.assertRaises(ValueError):
            self.freeze(c)

    def test_checksum_tamper_is_detected_even_if_one_number_changes(self):
        out = self.freeze()
        out["ordered_top3_probs"][0][3] += 0.000001
        with self.assertRaises(ValueError):
            verify_forecast_integrity(out, self.manifest)

    def test_scoring_is_postresult_and_has_all_eight_proper_scores(self):
        out = self.freeze()
        result = make_result()
        scored = score_frozen(
            out, self.manifest, result,
            forecast_raw=(json.dumps(out, ensure_ascii=False, sort_keys=True)+"\n").encode(),
            result_raw=canonical(result), result_source_raw=RESULT_SOURCE,
        )
        self.assertEqual(scored["status"], "SCORED_BUT_PROSPECTIVE_STATUS_UNVERIFIED")
        self.assertIsNone(scored["server_attestation"])
        self.assertEqual(len(scored["ticket_type_brier"]), 8)
        self.assertTrue(math.isfinite(scored["primary_delta_wide_minus_win_ordered_log_loss"]))
        self.assertTrue(all(math.isfinite(r["delta_wide_minus_win"])
                            for r in scored["ticket_type_brier"].values()))

    def test_scoring_refuses_result_text_that_disagrees_with_top3(self):
        frozen = self.freeze()
        result = make_result()
        result["top3"] = [2, 9, 3]
        with self.assertRaisesRegex(ValueError, "source_and_result_file_disagree"):
            score_frozen(frozen, self.manifest, result,
                         forecast_raw=canonical(frozen), result_raw=canonical(result),
                         result_source_raw=RESULT_SOURCE)
        result = make_result()
        with self.assertRaisesRegex(ValueError, "source_and_result_file_disagree"):
            score_frozen(frozen, self.manifest, result,
                         forecast_raw=canonical(frozen), result_raw=canonical(result),
                         result_source_raw=RESULT_SOURCE + b"manipulated")

    def test_refuse_mismatched_or_early_result(self):
        out = self.freeze()
        result = make_result()
        result["race_id"] = "wrong_race"
        with self.assertRaises(ValueError):
            score_frozen(out, self.manifest, result,
                         forecast_raw=canonical(out), result_raw=canonical(result), result_source_raw=RESULT_SOURCE)
        result = make_result()
        result["observed_at_jst"] = "2026-11-28T14:40:00+09:00"
        with self.assertRaises(ValueError):
            score_frozen(out, self.manifest, result,
                         forecast_raw=canonical(out), result_raw=canonical(result), result_source_raw=RESULT_SOURCE)
        result = make_result()
        result["top3"] = [9, 9, 2]
        with self.assertRaises(ValueError):
            score_frozen(out, self.manifest, result,
                         forecast_raw=canonical(out), result_raw=canonical(result), result_source_raw=RESULT_SOURCE)

    def test_github_server_created_pre_post_and_exact_bytes_are_required(self):
        frozen = self.freeze()
        payload = canonical(frozen)
        result = make_result()
        github_sha = "e"*40
        path = "holdout/ticket-forward-v1/2026-11-28-TOKYO-11/forecast.json"
        run = {
            "event": "pull_request", "conclusion": "success",
            "repository": {"full_name": "zuizui0223/keiba"},
            "created_at": "2026-11-28T05:41:00Z",
            "head_sha": github_sha,
        }
        file_info = {
            "encoding": "base64", "path": path,
            "content": base64.b64encode(payload).decode(),
            "sha": git_blob_sha1(payload),
        }
        source_files = {
            "forecast.json": payload,
            "capture.json": canonical(make_capture()),
            "win-source.txt": SOURCE_PAGES["win"],
            "wide-source.txt": SOURCE_PAGES["wide"],
        }
        def getter(url):
            if "/actions/runs/" in url:
                return run
            for name, content in source_files.items():
                if f"/{name}?ref=" in url:
                    return {
                        "encoding": "base64", "path": path.replace("forecast.json", name),
                        "content": base64.b64encode(content).decode(),
                        "sha": git_blob_sha1(content),
                    }
            raise ValueError("unknown_test_url")
        args = {"owner_repo": "zuizui0223/keiba", "run_id": 123, "committed_path": path}
        verified = _attest_github_run(payload, frozen, getter=getter, **args)
        self.assertEqual(verified["status"], "GITHUB_SERVER_PREPOST_RECEIPT_VERIFIED")
        scored = score_frozen(frozen, self.manifest, result,
                              forecast_raw=payload, result_raw=canonical(result), result_source_raw=RESULT_SOURCE,
                              github_receipt=args, github_getter=getter)
        self.assertEqual(scored["status"], "SCORED_PROSPECTIVE_SERVER_SEALED")
        changed = dict(run, created_at="2026-11-28T06:00:00Z")
        with self.assertRaises(ValueError):
            _attest_github_run(payload, frozen, getter=lambda u: changed if "/actions/runs/" in u else file_info,
                               **args)
        changed = dict(file_info, content=base64.b64encode(payload+b" ").decode())
        with self.assertRaises(ValueError):
            _attest_github_run(payload, frozen, getter=lambda u: run if "/actions/runs/" in u else changed,
                               **args)
        with self.assertRaises(ValueError):
            _attest_github_run(payload, frozen,
                getter=lambda u: {
                    "encoding": "base64", "path": path.replace("forecast.json", "win-source.txt"),
                    "content": base64.b64encode(b"tampered").decode(), "sha": git_blob_sha1(b"tampered"),
                } if "/win-source.txt?ref=" in u else getter(u), **args)
        with self.assertRaises(ValueError):
            _attest_github_run(payload, frozen, owner_repo="evil/repo", run_id=123,
                               committed_path=path, getter=getter)
        with self.assertRaises(ValueError):
            _attest_github_run(payload, frozen, getter=getter,
                               owner_repo="zuizui0223/keiba", run_id=123,
                               committed_path="holdout/ticket-forward-v1/../other/forecast.json")


if __name__ == "__main__":
    unittest.main()
