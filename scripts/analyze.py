#!/usr/bin/env python3
"""Reproduce descriptive course statistics and conditional ticket arithmetic.

No learning, race-result lookup, live scraping, purchase, or outcome probabilities.
"""
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
CARD = {6: (12, "turf", 1200), 7: (16, "dirt", 1900),
        8: (11, "turf", 2000), 9: (12, "dirt", 1800),
        10: (10, "turf", 1800), 11: (18, "turf", 1400),
        12: (16, "dirt", 1200)}


def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone_required: " + value)
    return result.astimezone(JST)


def record_summary(record):
    if record is None:
        return {"starts": None, "wins": None, "top3": None,
                "win_rate": None, "top3_rate": None}
    if (len(record) != 4 or any(type(x) is not int or x < 0 for x in record)):
        raise ValueError("invalid_course_record")
    starts = sum(record)
    top3 = sum(record[:3])
    return {"starts": starts, "wins": record[0], "top3": top3,
            "win_rate": record[0] / starts if starts else None,
            "top3_rate": top3 / starts if starts else None}


def validate(race, as_of):
    start = timestamp(race["start_jst"])
    observed = timestamp(race["odds_observed_at_jst"])
    updated = timestamp(race["odds_updated_at_jst"])
    if observed > as_of:
        raise ValueError("future_observation: " + race["race_id"])
    if updated > observed or updated >= start:
        raise ValueError("invalid_quote_time: " + race["race_id"])
    number = race["race"]
    if (race["date"] != "2026-10-12" or race["venue"] != "京都"
            or race["race_id"] != f"26080405{number:02d}"
            or start.date().isoformat() != race["date"]):
        raise ValueError("card_identity_mismatch")
    size, surface, distance = CARD[number]
    if (race["surface"], race["distance_m"]) != (surface, distance):
        raise ValueError("course_identity_mismatch")
    numbers = [h["number"] for h in race["horses"]]
    if sorted(numbers) != list(range(1, size + 1)):
        raise ValueError("roster_incomplete_or_duplicate")
    for horse in race["horses"]:
        if not math.isfinite(horse["win_odds"]) or horse["win_odds"] < 1:
            raise ValueError("invalid_win_odds")
        course = record_summary(horse["kyoto_record"])
        same_distance = record_summary(horse["kyoto_distance_record"])
        if same_distance["starts"] is not None:
            if (course["starts"] is None or same_distance["starts"] > course["starts"]
                    or any(d > c for d, c in zip(horse["kyoto_distance_record"],
                                                horse["kyoto_record"]))):
                raise ValueError("distance_exceeds_course")
        if not horse["evidence_urls"]:
            raise ValueError("missing_horse_evidence")
    pairs = set()
    for ticket in race["tickets"]:
        pair = tuple(sorted(ticket["horses"]))
        if (ticket["type"] != "wide" or len(pair) != 2 or len(set(pair)) != 2
                or not set(pair).issubset(numbers) or pair in pairs):
            raise ValueError("invalid_or_duplicate_ticket")
        pairs.add(pair)
        low, high = ticket["odds_low"], ticket["odds_high"]
        if not all(math.isfinite(v) for v in (low, high)) or not 1 <= low <= high:
            raise ValueError("invalid_wide_odds")
        quote_time = timestamp(ticket["updated_at_jst"])
        if quote_time > observed or quote_time >= start:
            raise ValueError("invalid_ticket_time")


def payout(odds, stake):
    return int(Decimal(str(odds)) * Decimal(stake))


def race_scenarios(race, tickets, stake):
    """Enumerate distinct top-three sets; no equal-likelihood assumption."""
    pairs = [set(t["horses"]) for t in tickets]
    axes = set.intersection(*pairs)
    scenarios = []
    for top3 in combinations([h["number"] for h in race["horses"]], 3):
        top = set(top3)
        winners = [t for t in tickets if set(t["horses"]).issubset(top)]
        scenarios.append((len(winners), sum(payout(t["odds_low"], stake)
                                           for t in winners), axes.issubset(top)))
    positive = [value for count, value, _ in scenarios if count]
    absent = [value for _, value, axis_present in scenarios if not axis_present]
    return {"race": race["race"], "stake_yen": len(tickets) * stake,
            "common_axes": sorted(axes),
            "distinct_top3_sets_enumerated": len(scenarios),
            "max_simultaneous_winners": max(n for n, _, _ in scenarios),
            "min_low_return_if_any_hit_yen": min(positive) if positive else 0,
            "max_low_return_scenario_yen": max(value for _, value, _ in scenarios),
            "axis_absent_max_return_yen": max(absent) if absent else None,
            "probabilities_assigned": False}


def portfolio(races, as_of, stake, priority_only=False, max_age_minutes=15):
    active = [r for r in races
              if as_of < timestamp(r["start_jst"]) - timedelta(minutes=2)]
    selected = [(r, t) for r in active for t in r["tickets"]
                if not priority_only or t["priority"]]
    total = len(selected) * stake
    rows = []
    for race, ticket in selected:
        age = (as_of - timestamp(ticket["updated_at_jst"])).total_seconds() / 60
        low_return = payout(ticket["odds_low"], stake)
        rows.append({"race": race["race"], "horses": sorted(ticket["horses"]),
                     "stake_yen": stake, "odds_low": ticket["odds_low"],
                     "odds_high": ticket["odds_high"],
                     "updated_at_jst": ticket["updated_at_jst"],
                     "quote_age_minutes": round(age, 2),
                     "needs_quote_refresh": age > max_age_minutes,
                     "payout_low_yen": low_return,
                     "only_this_hit_net_yen": low_return - total,
                     "break_even_hit_probability": float(Decimal(1) /
                                                          Decimal(str(ticket["odds_low"]))),
                     "source_url": ticket["source_url"]})
    risks = []
    for race in active:
        tickets = [t for r, t in selected if r["race"] == race["race"]]
        if tickets:
            risks.append(race_scenarios(race, tickets, stake))
    return {"ticket_count": len(rows), "stake_yen": total, "tickets": rows,
            "race_scenarios": risks, "purchase_executed": False}


def build_report(data, as_of, stake, max_age_minutes):
    races, manifest = [], []
    for path in sorted(data.glob("kyoto_*.json")):
        raw = path.read_bytes()
        race = json.loads(raw)
        validate(race, as_of)
        for horse in race["horses"]:
            horse["course_summary"] = record_summary(horse["kyoto_record"])
            horse["distance_summary"] = record_summary(horse["kyoto_distance_record"])
        race["before_analysis_cutoff"] = (as_of < timestamp(race["start_jst"])
                                            - timedelta(minutes=2))
        races.append(race)
        manifest.append({"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
    if sorted(r["race"] for r in races) != list(CARD):
        raise ValueError("expected_frozen_races_6_through_12")
    return {"analysis_at_jst": as_of.isoformat(), "scope": "2026-10-12 京都6〜12R",
            "method": "descriptive_history_and_conditional_ticket_arithmetic",
            "calibrated_prediction_model": False,
            "horse_count": sum(len(r["horses"]) for r in races),
            "stake_per_ticket_yen": stake, "max_quote_age_minutes": max_age_minutes,
            "source_manifest": manifest, "races": races,
            "portfolios": {"all": portfolio(races, as_of, stake, False, max_age_minutes),
                           "priority": portfolio(races, as_of, stake, True, max_age_minutes)}}


def safe(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def record_text(record):
    return "未確認/未出走（注記参照）" if record is None else "-".join(map(str, record))


def markdown(report):
    lines = ["# 京都競馬：実績・オッズ・買い目の分析", "",
             f"分析時刻：{report['analysis_at_jst']}。対象95頭、6〜12R。", "",
             "京都の過去好走率は今日の的中確率ではありません。印は会話での定性判断を保存したもので、学習済みモデルの出力ではありません。", "",
             "このスクリプトは保存済み入力を計算します。現在のオッズの自動取得や購入は行いません。", "",
             "## 優先買い目の収支", ""]
    for key, title in (("priority", "優先候補"), ("all", "全レースの候補")):
        p = report["portfolios"][key]
        lines.extend([f"### {title}", "",
                      f"{p['ticket_count']}点 × {report['stake_per_ticket_yen']}円 = {p['stake_yen']}円。発走2分前以降のレースは除外。", "",
                      "| R | ワイド | 中間オッズ | 更新JST | 要再確認 | 必要的中率 | 下限払戻 | この1点だけ的中した全体収支 |",
                      "|---|---|---|---|---|---|---|---|"])
        for t in p["tickets"]:
            pair = "-".join(map(str, t["horses"]))
            lines.append(f"| {t['race']} | {pair} | {t['odds_low']}–{t['odds_high']} | "
                         f"{timestamp(t['updated_at_jst']).strftime('%H:%M')} | "
                         f"{'要更新' if t['needs_quote_refresh'] else '15分以内'} | "
                         f"{100*t['break_even_hit_probability']:.1f}% | "
                         f"{t['payout_low_yen']}円 | {t['only_this_hit_net_yen']:+}円 |")
        lines.extend(["", "必要的中率 = 1 ÷ オッズ下限。これは当該1券を繰り返す仮定での損益分岐点で、実際にその確率を達成できるという推定ではありません。", ""])
    lines.extend(["## 同じ軸への集中", "",
                  "通常の同着なしの3着以内を列挙し、券の同時的中可能性を確認しました。各着順を等確率とは仮定していません。", "",
                  "| R | 共通する馬番 | 同時的中できる最大点数 | 購入額 | 1点以上的中した場合の最小払戻試算 |",
                  "|---|---|---|---|---|"])
    for r in report["portfolios"]["priority"]["race_scenarios"]:
        lines.append(f"| {r['race']} | {','.join(map(str,r['common_axes']))} | "
                     f"{r['max_simultaneous_winners']} | {r['stake_yen']}円 | "
                     f"{r['min_low_return_if_any_hit_yen']}円 |")
    lines.extend(["", "11Rの3券はすべて9番が軸。9番が3着以内に入らなければ3券とも外れ、9番が入っても同時的中は最大2券です。", "",
                  "## レース別の全頭比較", "",
                  "成績は1着-2着-3着-4着以下。京都通算は当該レースの芝またはダートのみ。同距離は確認できた履歴だけを集計し、未知は0戦に置き換えません。", ""])
    for race in report["races"]:
        lines.extend([f"### {race['race']}R {race['class']} {race['distance_m']}m", "",
                      f"発走予定：{timestamp(race['start_jst']).strftime('%H:%M')}、単勝更新："
                      f"{timestamp(race['odds_updated_at_jst']).strftime('%H:%M')}、取得：{race['odds_observed_at_jst']}。", "",
                      "| 印 | 馬番・馬名 | 単勝 | 京都通算 | 京都3着以内 | 京都同距離 | 根拠・留保 |",
                      "|---|---|---|---|---|---|---|"])
        for h in race["horses"]:
            stat = h["course_summary"]
            rate = (f"{stat['top3']}/{stat['starts']} ({100*stat['top3_rate']:.1f}%)"
                    if stat["top3_rate"] is not None else "算出しない")
            lines.append(f"| {h['mark']} | {h['number']} {safe(h['name'])} | {h['win_odds']} | "
                         f"{record_text(h['kyoto_record'])} | {rate} | "
                         f"{record_text(h['kyoto_distance_record'])} | {safe(' '.join(h['notes']))} |")
        lines.extend(["", "根拠：", ""])
        for source in race["sources"]:
            lines.append(f"- [{source['kind']}]({source['url']})")
        lines.append("")
        for key in ("data_notes", "analysis_notes"):
            value = race.get(key, [])
            if isinstance(value, str):
                value = [value]
            lines.extend(str(note) for note in value)
        lines.append("")
    lines.extend(["## 再現と限界", "",
                  "入力ファイルごとのSHA-256はanalysis.jsonに記録。分析時刻と1点当たり金額を固定すると同じ結果を再現できます。", "",
                  "下限払戻は表示中間オッズを固定した条件付き計算で、最終払戻を保証しません。オッズの下落、取消、返還、同着の特殊払戻は別途確認が必要です。買い目の評価を、未検証の利益予測に置き換えません。", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/2026-10-12"))
    parser.add_argument("--output", type=Path, default=Path("reports/2026-10-12"))
    parser.add_argument("--as-of", required=True, help="Timezone-aware ISO timestamp")
    parser.add_argument("--stake", type=int, default=100)
    parser.add_argument("--max-quote-age-minutes", type=int, default=15)
    args = parser.parse_args()
    try:
        if args.stake <= 0 or args.stake % 100 or args.max_quote_age_minutes <= 0:
            raise ValueError("invalid_stake_or_quote_age")
        report = build_report(args.data, timestamp(args.as_of), args.stake,
                              args.max_quote_age_minutes)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "analysis.json").write_text(json.dumps(report, ensure_ascii=False,
                                                           indent=2) + "\n", encoding="utf-8")
        (args.output / "report.md").write_text(markdown(report), encoding="utf-8")
        print(json.dumps({"horses": report["horse_count"],
                          "all_stake_yen": report["portfolios"]["all"]["stake_yen"],
                          "priority_stake_yen": report["portfolios"]["priority"]["stake_yen"],
                          "output": str(args.output)}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
