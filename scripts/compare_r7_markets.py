#!/usr/bin/env python3
"""Descriptive price comparisons for equivalent 7R betting events.

This is a snapshot calculation, not an outcome model or a live arbitrage claim.
"""
import hashlib
from itertools import permutations
import json
from pathlib import Path


def equivalent_return(odds):
    return 1 / sum(1 / value for value in odds)


def main():
    path = Path("data/2026-10-12/r7_markets.json")
    raw = path.read_bytes()
    data = json.loads(raw)
    markets = {name: {tuple(q["selection"]): q["odds_low"] for q in m["quotes"]}
               for name, m in data["markets"].items()}
    for name, market in markets.items():
        assert len(market) == len(data["markets"][name]["quotes"]), "duplicate_quote"
        assert all(o >= 1 for o in market.values()), "invalid_odds"
    exclusive = {}
    for name in ("win", "frame", "quinella", "exacta"):
        assert len(markets[name]) == data["expected_full_market_sizes"][name]
        inverse_sum = sum(1 / o for o in markets[name].values())
        exclusive[name] = {"outcomes": len(markets[name]), "inverse_sum": inverse_sum,
            "continuous_equal_return_factor_if_every_outcome_bought": 1 / inverse_sum}
    # Each listed alternative is mutually exclusive; together they describe
    # exactly the same conditional event as the direct ticket, without ties.
    cases = [
        ("quinella_2_15", "quinella", (2, 15), "exacta", [(2, 15), (15, 2)]),
        ("trio_2_5_15", "trio", (2, 5, 15), "trifecta", list(permutations((2, 5, 15)))),
        ("frame_6_8", "frame", (6, 8), "quinella", [(11, 15), (11, 16), (12, 15), (12, 16)]),
    ]
    comparisons = []
    for label, direct, selection, alternate, outcomes in cases:
        direct_odds = markets[direct][selection]
        values = [markets[alternate][p] for p in outcomes]
        synthetic = equivalent_return(values)
        comparisons.append({"case": label, "direct_market": direct,
            "selection": selection, "direct_odds": direct_odds,
            "alternative_market": alternate, "alternative_selections": outcomes,
            "alternative_odds": values, "equal_return_synthetic_odds": synthetic,
            "direct_to_synthetic_gain": direct_odds / synthetic - 1,
            "same_update_time": data["markets"][direct]["updated_at_jst"] ==
                                data["markets"][alternate]["updated_at_jst"]})
    result = {"input_sha256": hashlib.sha256(raw).hexdigest(),
        "checked_at_utc": data["checked_at_utc"],
        "quote_counts": {k: len(v) for k, v in markets.items()},
        "exhaustive_exclusive_markets": exclusive,
        "equivalent_event_comparisons": comparisons,
        "same_frame_alternatives": [{"frame": f,
            "frame_odds": markets["frame"][(f, f)], "horse_pair": [2*f-1, 2*f],
            "quinella_odds": markets["quinella"][(2*f-1, 2*f)]} for f in range(1, 9)],
        "limitations": ["中間オッズの更新時刻が市場ごとに異なる。",
            "払戻均等配分は連続金額の理論値。100円単位の配分は別途検証が必要。",
            "3連複・3連単の取得は一部。全組合せの最適解を主張しない。",
            "複勝・ワイドは複数券が同時的中するため排他的市場の逆数和を適用しない。",
            "単一イベントの比較はそのイベントが起きた場合だけ。利益確定ではない。"]}
    output = Path("reports/2026-10-12/r7-price-comparison.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exclusive": exclusive, "comparisons": comparisons}, ensure_ascii=False))


if __name__ == "__main__":
    main()
