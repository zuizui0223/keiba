#!/usr/bin/env python3
"""Prospective eight-ticket forecast freezer and post-result scorer (stdlib only).

A forecast is a *candidate* until independently attested by a GitHub Actions
server-created run containing the identical forecast bytes before post time.
No forecast is ever a purchase recommendation, calibrated model or proof of EV.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
from itertools import permutations
import json
import math
from pathlib import Path
import re
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

try:
    from scripts.ticket_type_models import KINDS, _time, event_selection, predict_tickets
    from scripts.ticket_wide_cross_market import tilt_wide_joint
    from scripts.ticket_forward_result_capture import parse_result_source
except ModuleNotFoundError:
    from ticket_type_models import KINDS, _time, event_selection, predict_tickets
    from ticket_wide_cross_market import tilt_wide_joint
    from ticket_forward_result_capture import parse_result_source

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "ticket-forward-v1"
DATA_STATUSES = {"READY", "HOLD_INCOMPLETE_ODDS", "HOLD_STALE_OR_UNVERIFIED", "HOLD_ROSTER"}
FORBIDDEN_INPUT_KEYS = frozenset({
    "finish", "finishing_order", "result", "results", "payout", "payouts",
    "top3", "winner", "actual_top3", "actual_winner", "final_odds",
})
OFFICIAL_HOSTS = frozenset({"www.jra.go.jp", "jra.go.jp", "jra.jp", "app.jra.jp", "sp.jra.jp"})
SECONDARY_HOSTS = frozenset({"sports.yahoo.co.jp"})
RESULT_HOSTS = OFFICIAL_HOSTS


def canonical(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def valid_hex(value: str, length: int = 64) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", value))


def _http_host(url: str, hosts: frozenset[str]) -> str:
    if not isinstance(url, str):
        raise ValueError("missing_source_url")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port:
        raise ValueError("untrusted_source_url")
    return parsed.hostname


def _jst(value: str) -> datetime:
    result = _time(value)
    if result.utcoffset() != timedelta(hours=9):
        raise ValueError("timestamp_not_explicit_JST")
    return result


def _no_outcomes(obj: object):
    if isinstance(obj, list):
        for item in obj:
            _no_outcomes(item)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in FORBIDDEN_INPUT_KEYS:
                raise ValueError("post_result_key_in_forecast")
            _no_outcomes(value)


def _run_files_match(manifest: dict, repo_root: Path):
    expected = manifest["pinned_source_git_blob_sha1"]
    if set(expected) != {
        "scripts/ticket_type_models.py",
        "scripts/ticket_wide_cross_market.py",
        "scripts/ticket_type_historical_audit.py",
    }:
        raise ValueError("incomplete_pinned_code_set")
    for path, digest in expected.items():
        if not valid_hex(digest, 40):
            raise ValueError("invalid_pinned_git_sha")
        actual = git_blob_sha1((repo_root / path).read_bytes())
        if actual != digest:
            raise ValueError(f"model_code_changed_since_manifest:{path}")


def validate_manifest(manifest: dict, *, repo_root: Path = REPO_ROOT):
    if (manifest.get("schema_version") != 1 or manifest.get("version") != VERSION or
            manifest.get("market_sources") != ["win", "wide"] or
            manifest.get("min_runners") != 9 or manifest.get("max_runners") != 18 or
            manifest.get("start_eligible_on_or_after_jst_date") != "2026-11-23" or
            manifest.get("forecast_lead_minutes") != [15, 25] or
            manifest.get("source_updated_max_age_minutes") != 10 or
            manifest.get("source_receipt_max_age_minutes") != 5 or
            manifest.get("win_wide_receipt_gap_seconds") != 90 or
            manifest.get("wide_alpha") != 0.5 or
            manifest.get("wide_quote_midpoint") != "geometric" or
            manifest.get("primary_loss") != "ordered_top3_log_loss" or
            manifest.get("holdout_attempts") != 30 or
            manifest.get("max_attempts_per_race_date") != 10):
        raise ValueError("unapproved_forward_manifest")
    _run_files_match(manifest, repo_root)


def _source_quotes(market: dict, kind: str, freeze: datetime, start: datetime, manifest: dict):
    if not isinstance(market, dict):
        raise ValueError(f"missing_{kind}_market")
    _http_host(market["source_url"], OFFICIAL_HOSTS | SECONDARY_HOSTS)
    observed, updated = _jst(market["observed_at_jst"]), _jst(market["updated_at_jst"])
    if not updated <= observed <= freeze < start:
        raise ValueError(f"{kind}_quote_timestamp_invalid")
    if freeze - observed > timedelta(minutes=manifest["source_receipt_max_age_minutes"]):
        raise ValueError(f"{kind}_market_receipt_stale")
    if freeze - updated > timedelta(minutes=manifest["source_updated_max_age_minutes"]):
        raise ValueError(f"{kind}_market_update_stale")
    if market.get("updated_time_basis") != "source_visible":
        raise ValueError(f"{kind}_market_update_not_source_verified")
    if not valid_hex(market.get("raw_page_sha256")):
        raise ValueError(f"{kind}_missing_raw_evidence_sha256")
    if not isinstance(market.get("quotes"), list):
        raise ValueError(f"{kind}_market_quotes_missing")
    return observed, updated


def validate_capture(capture: dict, manifest: dict, as_of_jst: str) -> tuple[dict, dict[int, float], dict[int, int], list[dict]]:
    _no_outcomes(capture)
    if set(capture) != {"schema_version", "race", "markets"} or capture["schema_version"] != 1:
        raise ValueError("capture_schema_unapproved")
    race, markets = capture["race"], capture["markets"]
    if set(race) != {"race_id", "date", "venue", "race_number", "scheduled_start_jst", "horses"}:
        raise ValueError("race_fields_unapproved")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{7,79}", race["race_id"]):
        raise ValueError("invalid_race_id")
    start, asof = _jst(race["scheduled_start_jst"]), _jst(as_of_jst)
    if (race["date"] != start.date().isoformat() or
            race["date"] < manifest["start_eligible_on_or_after_jst_date"] or
            not isinstance(race["venue"], str) or not race["venue"] or
            type(race["race_number"]) is not int or not 1 <= race["race_number"] <= 12):
        raise ValueError("invalid_race_or_future_date")
    lead = (start - asof).total_seconds() / 60
    if not manifest["forecast_lead_minutes"][0] <= lead <= manifest["forecast_lead_minutes"][1]:
        raise ValueError("forecast_outside_fixed_prepost_window")
    if set(markets) != {"win", "wide"}:
        raise ValueError("market_roster_incomplete")
    observed = {}
    for kind, market in markets.items():
        observed[kind], _ = _source_quotes(market, kind, asof, start, manifest)
    if abs((observed["win"] - observed["wide"]).total_seconds()) > manifest["win_wide_receipt_gap_seconds"]:
        raise ValueError("cross_market_receipts_not_synchronous")
    horses = race["horses"]
    if not isinstance(horses, list) or not manifest["min_runners"] <= len(horses) <= manifest["max_runners"]:
        raise ValueError("field_size_ineligible")
    frames = {}
    for h in horses:
        if set(h) != {"number", "frame"} or type(h["number"]) is not int or type(h["frame"]) is not int:
            raise ValueError("invalid_horse_schema")
        n, f = h["number"], h["frame"]
        if not 1 <= n <= 18 or not 1 <= f <= 8 or n in frames:
            raise ValueError("invalid_duplicate_horse")
        frames[n] = f
    odds = {}
    for q in markets["win"]["quotes"]:
        if set(q) != {"selection", "odds_low", "odds_high"}:
            raise ValueError("win_quote_schema_invalid")
        ids = q["selection"]
        if len(ids) != 1 or type(ids[0]) is not int or ids[0] in odds:
            raise ValueError("invalid_win_quote_selection")
        low, high = q["odds_low"], q["odds_high"]
        if (isinstance(low, bool) or isinstance(high, bool) or
                not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or
                not math.isfinite(low) or not math.isfinite(high) or low < 1 or low != high):
            raise ValueError("invalid_win_quote_odds")
        odds[ids[0]] = float(low)
    if set(odds) != set(frames):
        raise ValueError("field_win_market_mismatch")
    wide = markets["wide"]["quotes"]
    if len(wide) != len(odds) * (len(odds) - 1) // 2:
        raise ValueError("incomplete_wide_market")
    seen_pairs = set()
    for q in wide:
        if set(q) != {"selection", "odds_low", "odds_high"}:
            raise ValueError("wide_quote_schema_invalid")
        pair = q["selection"]
        if (len(pair) != 2 or any(type(n) is not int for n in pair) or
                pair[0] == pair[1] or not set(pair) <= set(odds)):
            raise ValueError("wide_quote_selection_invalid")
        key = tuple(sorted(pair))
        if key in seen_pairs:
            raise ValueError("duplicate_wide_selection")
        seen_pairs.add(key)
        low, high = q["odds_low"], q["odds_high"]
        if (isinstance(low, bool) or isinstance(high, bool) or
                not isinstance(low, (int, float)) or not isinstance(high, (int, float)) or
                not math.isfinite(low) or not math.isfinite(high) or
                low < 1 or high < low):
            raise ValueError("invalid_wide_quote_odds")
    if len(seen_pairs) != len(wide):
        raise ValueError("incomplete_pair_roster")
    return race, odds, frames, wide


def freeze_forecast(capture: dict, manifest: dict, as_of_jst: str,
                    *, capture_raw: bytes, source_pages: dict[str, bytes],
                    repo_root: Path = REPO_ROOT) -> dict:
    validate_manifest(manifest, repo_root=repo_root)
    race, odds, frames, wide = validate_capture(capture, manifest, as_of_jst)
    if not isinstance(source_pages, dict) or set(source_pages) != {"win", "wide"}:
        raise ValueError("missing_archived_source_page_bytes")
    for kind in ("win", "wide"):
        raw = source_pages[kind]
        if not isinstance(raw, bytes) or not raw or sha256_bytes(raw) != capture["markets"][kind]["raw_page_sha256"]:
            raise ValueError(f"source_page_sha256_mismatch:{kind}")
    strength = {n: 1.0 / odd for n, odd in odds.items()}
    base = predict_tickets(strength, frames)
    tilt = tilt_wide_joint(strength, frames, wide,
                           alpha=manifest["wide_alpha"],
                           odds_position=manifest["wide_quote_midpoint"])
    if tilt["ticket_types"] is None or set(base) != set(KINDS):
        raise ValueError("HOLD_NO_COHERENT_TICKET_PREDICTIONS")
    triples = []
    for order in permutations(sorted(odds), 3):
        p0 = base["trifecta"][order]
        p1 = tilt["ticket_types"]["trifecta"][order]
        if min(p0, p1) <= 0:
            raise ValueError("zero_probability")
        triples.append([*order, p0, p1])
    if not math.isclose(math.fsum(r[3] for r in triples), 1, abs_tol=1e-10) or not math.isclose(
            math.fsum(r[4] for r in triples), 1, abs_tol=1e-10):
        raise ValueError("probabilities_not_normalized")
    out = {
        "schema_version": 1, "version": VERSION, "status": "PRE_RACE_CANDIDATE_UNATTESTED",
        "race_id": race["race_id"], "race_date": race["date"],
        "venue": race["venue"], "race_number": race["race_number"],
        "scheduled_start_jst": race["scheduled_start_jst"],
        "forecast_as_of_jst": as_of_jst,
        "capture_sha256": sha256_bytes(capture_raw),
        "manifest_sha256": sha256_bytes(canonical(manifest)),
        "source_evidence": {kind: {
            "raw_page_sha256": capture["markets"][kind]["raw_page_sha256"],
            "source_url": capture["markets"][kind]["source_url"],
            "observed_at_jst": capture["markets"][kind]["observed_at_jst"],
            "updated_at_jst": capture["markets"][kind]["updated_at_jst"],
        } for kind in ("win", "wide")},
        "runner_frames": {str(n): frames[n] for n in sorted(frames)},
        "model_codes_git_blob_sha1": manifest["pinned_source_git_blob_sha1"],
        "baseline": "win_only_PL",
        "alternative": "wide_pair_tilt_alpha_0.5_geometric",
        "ordered_top3_probs": triples,
        "usage_note": "No outcome, no final odds, no placed bets; server attestation pending",
    }
    out["integrity_sha256"] = sha256_bytes(canonical(out))
    return out


def verify_forecast_integrity(forecast: dict, manifest: dict, repo_root: Path = REPO_ROOT) -> None:
    validate_manifest(manifest, repo_root=repo_root)
    if (forecast.get("version") != VERSION or forecast.get("schema_version") != 1 or
            forecast.get("status") != "PRE_RACE_CANDIDATE_UNATTESTED" or
            forecast.get("manifest_sha256") != sha256_bytes(canonical(manifest)) or
            forecast.get("model_codes_git_blob_sha1") != manifest["pinned_source_git_blob_sha1"]):
        raise ValueError("wrong_forecast_version_or_manifest")
    payload = dict(forecast)
    checksum = payload.pop("integrity_sha256", None)
    if not valid_hex(checksum) or checksum != sha256_bytes(canonical(payload)):
        raise ValueError("frozen_forecast_checksum_mismatch")
    frames = {int(k): v for k, v in forecast["runner_frames"].items()}
    triples = forecast["ordered_top3_probs"]
    expected = set(permutations(sorted(frames), 3))
    if len(triples) != len(expected):
        raise ValueError("frozen_top3_support_size_mismatch")
    seen = set()
    for row in triples:
        if not isinstance(row, list) or len(row) != 5:
            raise ValueError("invalid_frozen_row")
        i, j, k, p0, p1 = row
        key = (i, j, k)
        if key not in expected or key in seen or any(
            isinstance(p, bool) or not isinstance(p, (int, float)) or
            not math.isfinite(p) or not 0 < p < 1 for p in (p0, p1)
        ):
            raise ValueError("invalid_or_duplicate_frozen_prediction")
        seen.add(key)
    if not all(math.isclose(math.fsum(row[ix] for row in triples), 1, abs_tol=1e-10)
               for ix in (3, 4)):
        raise ValueError("frozen_probability_normalization_failure")


def _attest_github_run(forecast_raw: bytes, forecast: dict, *,
                       owner_repo: str, run_id: int, committed_path: str,
                       getter=None) -> dict:
    """Read public GitHub server event time + its exact git-head file bytes.

    Security: run.created_at is GitHub server time, not user-supplied timestamp;
    same head SHA must expose identical forecast contents under dedicated path.
    Caller must still independently audit fidelity of archived market source.
    """
    if owner_repo != "zuizui0223/keiba" or type(run_id) is not int or run_id < 1:
        raise ValueError("untrusted_github_receipt")
    prefix = "holdout/ticket-forward-v1/"
    if (not isinstance(committed_path, str) or not committed_path.startswith(prefix) or
            not committed_path.endswith("/forecast.json") or
            ".." in committed_path or "//" in committed_path):
        raise ValueError("invalid_forecast_commit_path")
    if getter is None:
        def getter(url):
            with urlopen(Request(url, headers={"Accept": "application/vnd.github+json",
                                              "User-Agent": "keiba-ticket-forward-audit"}),
                         timeout=15) as response:
                return json.loads(response.read())
    run = getter(f"https://api.github.com/repos/{owner_repo}/actions/runs/{run_id}")
    start = _jst(forecast["scheduled_start_jst"])
    created = _time(run["created_at"])
    if (run.get("event") not in {"push", "workflow_dispatch", "pull_request"} or
            run.get("conclusion") != "success" or
            run.get("repository", {}).get("full_name") != owner_repo or
            not _jst(forecast["forecast_as_of_jst"]) <= created < start or
            not isinstance(run.get("head_sha"), str) or not valid_hex(run["head_sha"], 40)):
        raise ValueError("github_receipt_not_successful_before_post")
    commit_sha = run["head_sha"]
    file_data = getter(
        f"https://api.github.com/repos/{owner_repo}/contents/"
        f"{quote(committed_path, safe='/')}?ref={commit_sha}"
    )
    if file_data.get("encoding") != "base64" or file_data.get("path") != committed_path:
        raise ValueError("github_commit_does_not_contain_frozen_file")
    actual = base64.b64decode(file_data["content"], validate=False)
    if actual != forecast_raw or file_data.get("sha") != git_blob_sha1(forecast_raw):
        raise ValueError("github_seal_forecast_bytes_mismatch")
    base_dir = committed_path[: -len("forecast.json")]
    companion_hashes = {
        "capture.json": forecast["capture_sha256"],
        "win-source.txt": forecast["source_evidence"]["win"]["raw_page_sha256"],
        "wide-source.txt": forecast["source_evidence"]["wide"]["raw_page_sha256"],
    }
    for filename, digest in companion_hashes.items():
        companion_path = base_dir + filename
        companion = getter(
            f"https://api.github.com/repos/{owner_repo}/contents/"
            f"{quote(companion_path, safe='/')}?ref={commit_sha}"
        )
        if companion.get("encoding") != "base64" or companion.get("path") != companion_path:
            raise ValueError(f"github_seal_companion_missing:{filename}")
        payload = base64.b64decode(companion["content"], validate=False)
        if sha256_bytes(payload) != digest or companion.get("sha") != git_blob_sha1(payload):
            raise ValueError(f"github_seal_companion_sha_mismatch:{filename}")
    return {
        "status": "GITHUB_SERVER_PREPOST_RECEIPT_VERIFIED",
        "github_actions_run_id": run_id, "server_created_at": run["created_at"],
        "git_head_sha": commit_sha, "committed_path": committed_path,
        "forecast_file_sha256": sha256_bytes(forecast_raw),
        "note": "market source authenticity and upstream timestamp still need source audit",
    }


def score_frozen(forecast: dict, manifest: dict, result: dict, *,
                 forecast_raw: bytes, result_raw: bytes, result_source_raw: bytes,
                 repo_root: Path = REPO_ROOT, github_receipt: dict | None = None,
                 github_getter=None) -> dict:
    verify_forecast_integrity(forecast, manifest, repo_root)
    if (set(result) != {"race_id", "observed_at_jst", "source_url", "source_text_sha256", "top3"} or
            result["race_id"] != forecast["race_id"]):
        raise ValueError("result_schema_or_race_mismatch")
    _http_host(result["source_url"], RESULT_HOSTS)
    if not valid_hex(result["source_text_sha256"]):
        raise ValueError("official_result_missing_raw_evidence")
    parsed_source = parse_result_source(
        race_id=result["race_id"],
        source_url=result["source_url"],
        source_text=result_source_raw,
    )
    if (parsed_source["source_text_sha256"] != result["source_text_sha256"] or
            parsed_source["top3"] != result["top3"]):
        raise ValueError("official_result_source_and_result_file_disagree")
    if not _jst(result["observed_at_jst"]) > _jst(forecast["scheduled_start_jst"]):
        raise ValueError("result_observed_before_start")
    top3 = result["top3"]
    frames = {int(k): v for k, v in forecast["runner_frames"].items()}
    if (not isinstance(top3, list) or len(top3) != 3 or
            any(type(n) is not int for n in top3) or
            len(set(top3)) != 3 or not set(top3) <= set(frames)):
        raise ValueError("invalid_result_top3_no_dead_heat_support")
    distribution = {"win_only_PL": {}, "wide_pair_tilt": {}}
    for row in forecast["ordered_top3_probs"]:
        k = tuple(row[:3])
        distribution["win_only_PL"][k] = row[3]
        distribution["wide_pair_tilt"][k] = row[4]
    ordered = tuple(top3)
    ordered_scores = {}
    all_types = {}
    for model, joint in distribution.items():
        ordered_scores[model] = -math.log(joint[ordered])
        per_type = {}
        for kind in KINDS:
            prob = {}
            for finish, mass in joint.items():
                for sel in event_selection(kind, finish, frames):
                    prob[sel] = prob.get(sel, 0.) + mass
            winners = set(event_selection(kind, ordered, frames))
            proper_brier = math.fsum(
                (p - float(sel in winners)) ** 2 for sel, p in prob.items()
            ) / len(prob)
            per_type[kind] = {
                "ticket_count": len(prob),
                "winning_ticket_count": len(winners),
                "brier_per_ticket": proper_brier,
            }
        all_types[model] = per_type
    verified = None
    if github_receipt is not None:
        verified = _attest_github_run(
            forecast_raw, forecast, owner_repo=github_receipt["owner_repo"],
            run_id=github_receipt["run_id"],
            committed_path=github_receipt["committed_path"],
            getter=github_getter,
        )
    return {
        "schema_version": 1, "version": VERSION,
        "status": "SCORED_PROSPECTIVE_SERVER_SEALED" if verified else "SCORED_BUT_PROSPECTIVE_STATUS_UNVERIFIED",
        "race_id": forecast["race_id"], "race_date": forecast["race_date"],
        "forecast_sha256": sha256_bytes(forecast_raw),
        "result_source_sha256": result["source_text_sha256"],
        "result_source_parse_status": parsed_source["status"],
        "result_source_authenticity_independently_verified": False,
        "result_file_sha256": sha256_bytes(result_raw),
        "server_attestation": verified,
        "ordered_top3_log_loss": ordered_scores,
        "primary_delta_wide_minus_win_ordered_log_loss":
            ordered_scores["wide_pair_tilt"] - ordered_scores["win_only_PL"],
        "ticket_type_brier": {
            kind: {
                "win_only_PL": all_types["win_only_PL"][kind]["brier_per_ticket"],
                "wide_pair_tilt": all_types["wide_pair_tilt"][kind]["brier_per_ticket"],
                "delta_wide_minus_win":
                    all_types["wide_pair_tilt"][kind]["brier_per_ticket"] -
                    all_types["win_only_PL"][kind]["brier_per_ticket"],
            } for kind in KINDS
        },
        "note": "Single race report; no positive EV, betting return or model calibration implied",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="command", required=True)
    freeze = modes.add_parser("freeze")
    freeze.add_argument("--capture", type=Path, required=True)
    freeze.add_argument("--manifest", type=Path, required=True)
    freeze.add_argument("--as-of-jst", required=True)
    freeze.add_argument("--win-source-page", type=Path, required=True)
    freeze.add_argument("--wide-source-page", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    score = modes.add_parser("score")
    score.add_argument("--forecast", type=Path, required=True)
    score.add_argument("--result", type=Path, required=True)
    score.add_argument("--result-source-text", type=Path, required=True)
    score.add_argument("--manifest", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--github-run-id", type=int)
    score.add_argument("--github-committed-path")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_bytes())
        if args.command == "freeze":
            capture_raw = args.capture.read_bytes()
            data = freeze_forecast(
                json.loads(capture_raw), manifest, args.as_of_jst,
                capture_raw=capture_raw,
                source_pages={
                    "win": args.win_source_page.read_bytes(),
                    "wide": args.wide_source_page.read_bytes(),
                },
            )
        else:
            f_raw, r_raw = args.forecast.read_bytes(), args.result.read_bytes()
            if bool(args.github_run_id) != bool(args.github_committed_path):
                raise ValueError("github_attestation_requires_run_and_path")
            receipt = ({
                "owner_repo": "zuizui0223/keiba", "run_id": args.github_run_id,
                "committed_path": args.github_committed_path,
            } if args.github_run_id else None)
            data = score_frozen(json.loads(f_raw), manifest, json.loads(r_raw),
                                forecast_raw=f_raw, result_raw=r_raw,
                                result_source_raw=args.result_source_text.read_bytes(),
                                github_receipt=receipt)
    except (ValueError, KeyError, TypeError, OSError, OverflowError, ZeroDivisionError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                     sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"race_id": data["race_id"], "status": data["status"],
                      "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
