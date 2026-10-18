#!/usr/bin/env python3
"""Reproducible, non-formal audit of the 2026-10-18 conversational tickets.

Only market-channel M from the pre-existing v3.1 classifier is run.
C1/U/Q1/K1, full v3.1 union, calibrated probabilities and expected value
are NOT calculated. No target results, odds fetching, or purchases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

from scripts.v31_candidate_channels import market_channel

DATE = "2026-10-18"
INPUT_SNAPSHOT = Path("data/2026-10-18/ticket-odds-snapshot.json")
INPUT_SELECTIONS = Path("data/2026-10-18/ticket-selections-and-form.json")
JSON_REPORT = Path("reports/2026-10-18/ticket-audit.json")
MD_REPORT = Path("reports/2026-10-18/ticket-audit.md")


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def parse_time(value: str) -> datetime:
    date = datetime.fromisoformat(value)
    if date.tzinfo is None or date.utcoffset() is None:
        raise ValueError("timezone_required")
    return date


def money(odds: float, stake: int) -> int:
    return int(Decimal(str(odds)) * Decimal(stake))


def validate_snapshot(snapshot: dict) -> dict:
    if snapshot.get("status") != "exploratory_market_snapshot_not_v31_holdout":
        raise ValueError("wrong_snapshot_status")
    if snapshot.get("quote_source") != "Yahoo!競馬 intermediary displayed 中間オッズ":
        raise ValueError("wrong_quote_source")
    if snapshot.get("upstream_quote_updated_at_jst") is not None:
        raise ValueError("unexpected_upstream_time")
    begin = parse_time(snapshot["observed_window_start_jst"])
    end = parse_time(snapshot["observed_window_end_jst"])
    if begin > end or begin.date().isoformat() != DATE:
        raise ValueError("invalid_capture_window")
    by_race = {}
    for race in snapshot["races"]:
        key = (race["venue"], race["race"])
        if key in by_race:
            raise ValueError("duplicate_race")
        if race["date"] != DATE or not race["race_id"].endswith(f"{race['race']:02d}"):
            raise ValueError("mismatched_race_identity")
        if parse_time(race["scheduled_post_jst"]) <= end + timedelta(minutes=2):
            raise ValueError("not_eligible_for_new_bet_at_capture")
        horses = race["horses"]
        if len(horses) != race["runner_count"] or len(horses) < 3:
            raise ValueError("incorrect_runner_count")
        numbers = [h["number"] for h in horses]
        if len(set(numbers)) != len(numbers) or len(set(h["popularity"] for h in horses)) != len(horses):
            raise ValueError("duplicate_runner_or_popularity")
        if any(h["win_odds"] < 1 or h["place_odds_low"] < 1 or
               h["place_odds_high"] < h["place_odds_low"] or
               not math.isfinite(h["win_odds"]) for h in horses):
            raise ValueError("invalid_win_or_place_odds")
        if not race["source_win_place_url"].startswith("https://sports.yahoo.co.jp/keiba/race/odds/tfw/"):
            raise ValueError("unsupported_source")
        seen_pairs = set()
        for quote in race["wide"]:
            pair = tuple(quote["horses"])
            if pair in seen_pairs or tuple(sorted(pair)) != pair or len(pair) != 2:
                raise ValueError("duplicate_or_disordered_wide")
            if not set(pair) <= set(numbers) or quote["odds_low"] < 1 or quote["odds_high"] < quote["odds_low"]:
                raise ValueError("invalid_wide")
            seen_pairs.add(pair)
        if race["source_wide_url"] and len(seen_pairs) != math.comb(len(numbers), 2):
            raise ValueError("partial_wide_book")
        by_race[key] = race
    return by_race


def audit(snapshot: dict, selections: dict, snapshot_blob_sha: str | None = None,
          selections_blob_sha: str | None = None) -> dict:
    by_race = validate_snapshot(snapshot)
    if selections.get("status") != "exploratory_human_selected_tickets_not_v31_model_output":
        raise ValueError("wrong_picks_status")
    if selections.get("purchase_executed") is not False:
        raise ValueError("purchase_status_invalid")
    ticket_rows = []
    seen_ids = set()
    total = 0
    for ticket in selections["tickets"]:
        if ticket["id"] in seen_ids:
            raise ValueError("duplicate_ticket_id")
        seen_ids.add(ticket["id"])
        key = (ticket["venue"], ticket["race"])
        if key not in by_race:
            raise ValueError("no_race_for_ticket")
        race = by_race[key]
        horses = {h["number"]: h for h in race["horses"]}
        selection = ticket["selection"]
        kind = ticket["kind"]
        if kind not in ("place", "wide") or len(selection) != (1 if kind == "place" else 2):
            raise ValueError("invalid_ticket_kind_or_size")
        if len(set(selection)) != len(selection) or list(sorted(selection)) != selection:
            raise ValueError("duplicate_or_unsorted_selection")
        if not set(selection) <= set(horses):
            raise ValueError("unlisted_horse")
        stake = ticket["stake_yen"]
        if not isinstance(stake, int) or stake < 100 or stake % 100:
            raise ValueError("invalid_stake")
        total += stake
        if kind == "place":
            quote = horses[selection[0]]
            low, high = quote["place_odds_low"], quote["place_odds_high"]
            odds_url = race["source_win_place_url"]
        else:
            matches = [q for q in race["wide"] if q["horses"] == selection]
            if len(matches) != 1:
                raise ValueError("missing_wide_quote")
            low, high = matches[0]["odds_low"], matches[0]["odds_high"]
            odds_url = race["source_wide_url"]
        m = market_channel(race["horses"])
        low_payout = money(low, stake)
        ticket_rows.append({
            "id": ticket["id"], "venue": ticket["venue"], "race": ticket["race"],
            "kind": kind, "selection": selection, "stake_yen": stake,
            "popularity_by_selection": [horses[n]["popularity"] for n in selection],
            "in_M_all_horses": set(selection) <= m,
            "odds_low": low, "odds_high": high,
            "lower_payout_yen": low_payout, "upper_illustrative_payout_yen": money(high, stake),
            "break_even_hit_rate_pct_at_low_odds": round(100 / low, 1),
            "form_basis": ticket["form_basis"], "form_source": ticket["form_source"],
            "odds_source": odds_url
        })
    if total != selections["advertised_stake_yen"] or total != 2000 or len(ticket_rows) != 12:
        raise ValueError("portfolio_conservation_failed")
    for row in ticket_rows:
        row["portfolio_net_yen_if_only_this_ticket_hits_at_low_odds"] = row["lower_payout_yen"] - total

    race_rows = []
    for race in snapshot["races"]:
        included = [t for t in ticket_rows if (t["venue"], t["race"]) == (race["venue"], race["race"])]
        full_M = market_channel(race["horses"])
        ordered = sorted(race["horses"], key=lambda h: (h["win_odds"], h["number"]))
        selected_N = min(len(ordered), min(5, max(3, math.ceil(len(ordered) * 0.25))))
        cutoff = ordered[selected_N - 1]["win_odds"]
        if {h["number"] for h in ordered if h["win_odds"] <= cutoff} != full_M:
            raise ValueError("market_channel_contract_drift")
        min_positive = None
        max_paid = max_hits = 0
        combos = 0
        for top3 in combinations([h["number"] for h in race["horses"]], 3):
            top = set(top3)
            paid = [t for t in included if
                    (t["kind"] == "place" and t["selection"][0] in top) or
                    (t["kind"] == "wide" and set(t["selection"]) <= top)]
            payout = sum(t["lower_payout_yen"] for t in paid)
            max_paid = max(max_paid, payout)
            max_hits = max(max_hits, len(paid))
            if payout > 0:
                min_positive = payout if min_positive is None else min(min_positive, payout)
            combos += 1
        race_rows.append({
            "venue": race["venue"], "race": race["race"], "race_name": race["race_name"],
            "scheduled_post_jst": race["scheduled_post_jst"], "runner_count": len(race["horses"]),
            "win_book_inverse_odds_sum": round(sum(1 / h["win_odds"] for h in race["horses"]), 4),
            "market_M_nominal_count": selected_N, "market_M_cutoff_odds": cutoff,
            "market_M": sorted(full_M), "ticket_ids": [t["id"] for t in included],
            "top3_sets_enumerated": combos,
            "max_simultaneous_tickets_hit": max_hits,
            "min_positive_lower_payout_yen": min_positive,
            "max_lower_payout_yen": max_paid,
        })
    return {
        "schema_version": 1,
        "calculated_by": "scripts/audit_20261018_tickets.py",
        "date": DATE,
        "as_of_jst": snapshot["observed_window_end_jst"],
        "data_kind": "exploratory_intermediary_market_snapshot",
        "input_blob_sha": {"odds": snapshot_blob_sha, "selections": selections_blob_sha},
        "model_channels_calculated": ["M_only_v31_market_channel"],
        "not_calculated": ["C1", "U", "Q1", "K1", "v3.1_union", "predicted_probabilities", "expected_value", "actual_profit", "formal_holdout"],
        "quote_age_from_upstream_known": False,
        "purchase_executed": False,
        "summary": {
            "ticket_count": len(ticket_rows), "budget_yen": total,
            "full_M_ticket_count": sum(t["in_M_all_horses"] for t in ticket_rows),
            "not_full_M_ticket_count": sum(not t["in_M_all_horses"] for t in ticket_rows),
            "total_loss_if_nothing_hits_yen": -total,
            "upper_bound_of_combined_per_race_lower_odds_scenario_payout_yen": sum(r["max_lower_payout_yen"] for r in race_rows)
        },
        "tickets": ticket_rows, "races": race_rows
    }


def make_markdown(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# 2026-10-18 中間オッズ・投票案再現監査（非正式・探索的）", "",
        "## 判定", "",
        "- 以前の12点・2,000円案は対話中の定性的選択で、v3.1全チャネルのモデル計算結果ではなかった。",
        "- 今回、保存した全出走馬の単勝・複勝とワイド価格に対し、既存の v31_candidate_channels.market_channel（Mだけ）を実行した。",
        "- C1/U/Q1/K1、full union、勝率・EV・利益の推定は未実行。予想優位・正の期待値を意味しない。",
        "- 正式v3.1 holdoutには不適格。取得元はJRA公式JRADBではなくYahoo!競馬、中間オッズの元更新時刻も未検証。",
        "- 本ファイルは過去の提案の事後監査であり、現時点の新規購入を推奨するものではない。",
        "", "## 入力・出所", "",
        "- オッズスナップショット: data/2026-10-18/ticket-odds-snapshot.json",
        "- 人手選択と近走根拠: data/2026-10-18/ticket-selections-and-form.json",
        "- オッズ取得窓終了 (JST): " + report["as_of_jst"],
        "- odds Git blob: " + str(report["input_blob_sha"]["odds"]),
        "- picks Git blob: " + str(report["input_blob_sha"]["selections"]),
        "", "## 再計算結果", "",
        f"- {s['ticket_count']}点、総額{s['budget_yen']:,}円。Mに全対象馬が含まれる券は{s['full_M_ticket_count']}点、含まれない券は{s['not_full_M_ticket_count']}点。",
        f"- 全て不的中の場合は{s['total_loss_if_nothing_hits_yen']:,}円。各レースの3着内集合を全列挙したが、**それらを等確率とは仮定しない**。",
        "- 損益分岐的中率は 1 / 中間オッズ下限であり、推定的中率ではない。",
        "- 単券が当たっても、合計2,000円の回収とは限らない。馬券を重ねると的中事象も相関する。",
        "", "| レース | 券種・馬番 | 金額 | 価格下限–上限 | 下限払戻 | 損益分岐（下限） | 全馬M内 |", "|---|---|---:|---:|---:|---:|---|"
    ]
    for t in report["tickets"]:
        mark = "○" if t["in_M_all_horses"] else "×"
        kind = "複勝" if t["kind"] == "place" else "ワイド"
        sel = "–".join(f"{n:02d}" for n in t["selection"])
        lines.append(f"| {t['venue']}{t['race']}R | {kind} {sel} | {t['stake_yen']}円 | {t['odds_low']:.1f}–{t['odds_high']:.1f}倍 | {t['lower_payout_yen']}円 | {t['break_even_hit_rate_pct_at_low_odds']:.1f}% | {mark} |")
    lines.extend(["", "## v3.1 市場Mチャネル（9レースに限定）", "",
                  "| レース | 頭数 | M候補 | Mカットオフ（単勝） | 3着以内組合せ | 最大同時的中点数 |",
                  "|---|---:|---|---:|---:|---:|"])
    for r in report["races"]:
        sel = ",".join(str(x) for x in r["market_M"])
        lines.append(f"| {r['venue']}{r['race']}R | {r['runner_count']} | {sel} | {r['market_M_cutoff_odds']:.1f}倍 | {r['top3_sets_enumerated']} | {r['max_simultaneous_tickets_hit']} |")
    lines += ["", "## 個別選択の根拠（人手判断。定量モデルの特徴量スコアではない）", ""]
    for t in report["tickets"]:
        lines.append(f"- {t['venue']}{t['race']}R {t['id']}: {t['form_basis']} [JBIS出馬表]({t['form_source']}) / [中間オッズ]({t['odds_source']})")
    lines += ["", "## 再現手順", "",
              "python -m scripts.audit_20261018_tickets",
              "python -m unittest tests.test_oct18_ticket_audit -v",
              "", "出力: reports/2026-10-18/ticket-audit.json と本書。販売締切・取消・返還・同着特殊払戻・確定オッズ・将来結果の不確実性は対象外。",
              "試算で使った価格は取得時刻の中間表示であり購入価格を確定しない。", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=INPUT_SNAPSHOT)
    parser.add_argument("--selections", type=Path, default=INPUT_SELECTIONS)
    parser.add_argument("--json-output", type=Path, default=JSON_REPORT)
    parser.add_argument("--md-output", type=Path, default=MD_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw_snap = args.snapshot.read_bytes()
    raw_picks = args.selections.read_bytes()
    report = audit(json.loads(raw_snap), json.loads(raw_picks), git_blob_sha(raw_snap), git_blob_sha(raw_picks))
    j = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    md = make_markdown(report)
    if args.check:
        if json.loads(args.json_output.read_text(encoding="utf-8")) != report:
            raise SystemExit("FAIL: stored JSON audit disagrees with inputs")
        if args.md_output.read_text(encoding="utf-8") != md:
            raise SystemExit("FAIL: stored markdown audit disagrees with inputs")
        print("PASS: audit inputs and both stored reports match")
    else:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(j, encoding="utf-8")
        args.md_output.write_text(md, encoding="utf-8")
        print(f"tickets={report['summary']['ticket_count']}; budget={report['summary']['budget_yen']}; M_full={report['summary']['full_M_ticket_count']}")


if __name__ == "__main__":
    main()
