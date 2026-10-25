#!/usr/bin/env python3
"""Bet-type-wide per-unit payoff sensitivity, without arbitrary stake limits.

Input: local provenance-labelled normalized JSON, not an odds scraper.
Never reads finish results, selects stakes, or claims a calibrated probability.
The outputs are *conditional on hypothetical Plackett-Luce race models*.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from itertools import combinations
import json
import math
from pathlib import Path

from betting_crosspool_shape_audit import exact_pl

TYPES = ("win", "place", "frame", "wide", "quinella", "exacta", "trio", "trifecta")
FIELD_SIZE = {"frame": 2, "wide": 2, "quinella": 2,
              "exacta": 2, "trio": 3, "trifecta": 3}
UNORDERED = {"frame", "wide", "quinella", "trio"}
GAMMAS = (0.75, 1.0, 1.25)


def timestamp(value):
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() is None:
        raise ValueError("HOLD_TIMESTAMP_WITHOUT_OFFSET")
    return dt


def positive_odds(value):
    if type(value) not in (float, int) or not math.isfinite(value) or value <= 1:
        raise ValueError("HOLD_INVALID_INTERMEDIATE_ODDS")
    return float(value)


def key_of(kind, members):
    arity = FIELD_SIZE.get(kind, 1)
    if len(members) != arity or any(type(i) is not int for i in members):
        raise ValueError("HOLD_INVALID_MEMBERS")
    if len(set(members)) != len(members) and kind != "frame":
        raise ValueError("HOLD_REPEATED_HORSE")
    ordered = list(members) if kind not in UNORDERED else sorted(members)
    return ">".join(map(str, ordered)) if kind in ("exacta", "trifecta") else "-".join(map(str, ordered))


def probabilities(runners, win_prob):
    """Coherent 18x17x16 joint outcomes: all formats share the same race."""
    horse_ids = sorted(runners)
    pl = exact_pl({i: 1 / win_prob[i] for i in horse_ids}, 1.0)
    p = {
        "win": dict(pl["win"]), "place": dict(pl["top3"]),
        "wide": dict(pl["wide"]), "quinella": dict(pl["quinella"]),
        "trio": dict(pl["trio"]), "frame": {}, "exacta": {}, "trifecta": {},
    }
    for triple, mass in pl["ordered"].items():
        a, b, c = triple
        fr = tuple(sorted((runners[a]["frame"], runners[b]["frame"])))
        p["frame"][fr] = p["frame"].get(fr, 0.0) + mass
        ex = (a, b)
        p["exacta"][ex] = p["exacta"].get(ex, 0.0) + mass
        p["trifecta"][triple] = mass
    assert math.isclose(sum(p["win"].values()), 1, abs_tol=1e-10)
    assert math.isclose(sum(p["place"].values()), 3, abs_tol=1e-10)
    assert math.isclose(sum(p["wide"].values()), 3, abs_tol=1e-10)
    assert math.isclose(sum(p["quinella"].values()), 1, abs_tol=1e-10)
    assert math.isclose(sum(p["trio"].values()), 1, abs_tol=1e-10)
    assert math.isclose(sum(p["frame"].values()), 1, abs_tol=1e-10)
    return p


def normalize(weights):
    total = sum(weights.values())
    if total <= 0 or any(v <= 0 or not math.isfinite(v) for v in weights.values()):
        raise ValueError("HOLD_INVALID_MODEL_WEIGHTS")
    return {i: v / total for i, v in weights.items()}


def evaluate(doc, gamma_grid=GAMMAS):
    if doc.get("schema") != "PRESTART_ALL_BET_TYPES_LOCAL_QUOTES_V1":
        raise ValueError("HOLD_INPUT_SCHEMA")
    if not isinstance(doc.get("race_id"), str) or not doc["race_id"]:
        raise ValueError("HOLD_RACE_ID")
    post = timestamp(doc["scheduled_post_jst"])
    captured = timestamp(doc["page_observed_at_jst"])
    if captured >= post - timedelta(minutes=10):
        raise ValueError("HOLD_PRICE_LATE_OR_AFTER_START")
    rows = doc["runners"]
    runners = {}
    for row in rows:
        i = row["number"]
        if type(i) is not int or i < 1 or i in runners:
            raise ValueError("HOLD_DUPLICATE_OR_INVALID_STARTER")
        runners[i] = {
            "win_odds": positive_odds(row["win_odds"]),
            "place_low": positive_odds(row["place_low"]),
            "place_high": positive_odds(row["place_high"]),
            "frame": row["frame"],
        }
        if runners[i]["place_high"] < runners[i]["place_low"]:
            raise ValueError("HOLD_REVERSED_PLACE_RANGE")
        if type(row["frame"]) is not int or not 1 <= row["frame"] <= 8:
            raise ValueError("HOLD_BAD_FRAME")
    n = len(runners)
    if n < 4 or n > 30:
        raise ValueError("HOLD_UNEXPECTED_FIELD_SIZE")
    odds = {i: r["win_odds"] for i, r in runners.items()}
    forecasts = {
        f"market_gamma_{g:g}": normalize({i: odds[i] ** (-g) for i in odds})
        for g in gamma_grid
    }
    sealed = doc.get("original_sealed_M1_win_probs")
    if sealed is not None:
        sealed = {int(k): float(v) for k, v in sealed.items()}
        if set(sealed) != set(runners) or not math.isclose(sum(sealed.values()), 1, abs_tol=1e-10):
            raise ValueError("HOLD_BAD_ORIGINAL_SEAL_PROBABILITIES")
        forecasts["original_sealed_M1"] = normalize(sealed)
    pp = {name: probabilities(runners, values) for name, values in forecasts.items()}
    market_prices = {
        "win": [{"members": [i], "odds_low": odds[i]} for i in runners],
        "place": [{"members": [i], "odds_low": r["place_low"],
                   "odds_high": r["place_high"]} for i, r in runners.items()],
    }
    market_prices.update(doc.get("ticket_quotes") or {})
    if not set(TYPES).issubset(market_prices):
        raise ValueError("HOLD_MISSING_BET_TYPES")
    counts = {}
    table = []
    for kind in TYPES:
        seen = set()
        for quote in market_prices[kind]:
            members = quote["members"]
            normalized_key = key_of(kind, members)
            if normalized_key in seen:
                raise ValueError("HOLD_DUPLICATE_TICKET")
            seen.add(normalized_key)
            mk = tuple(int(i) for i in (sorted(members) if kind in UNORDERED else members))
            if kind == "frame":
                if any(i not in set(r["frame"] for r in runners.values()) for i in mk):
                    raise ValueError("HOLD_FRAME_NOT_IN_FIELD")
            elif any(i not in runners for i in mk):
                raise ValueError("HOLD_HORSE_NOT_IN_FIELD")
            low = positive_odds(quote["odds_low"])
            high = positive_odds(quote.get("odds_high", low))
            if high < low:
                raise ValueError("HOLD_REVERSED_QUOTE_RANGE")
            p_by_model = {m: probabilities_by_kind[kind].get(mk, 0.0)
                          for m, probabilities_by_kind in pp.items()}
            if any(p < 0 for p in p_by_model.values()):
                raise ValueError("HOLD_BAD_PROBABILITY")
            ev = {m: p * low for m, p in p_by_model.items()}
            base = ev.get("market_gamma_1", float("nan"))
            if not math.isfinite(base):
                raise ValueError("HOLD_MISSING_BASELINE_GAMMA_1")
            table.append({
                "type":kind, "selection":normalized_key,
                "source_odds_low":low, "source_odds_high":high,
                "break_even_probability":1/low,
                "p_by_model":p_by_model, "unit_expected_gross_by_model":ev,
                "min_model_unit_gross":min(ev.values()),
                "unit_gross_market_gamma_1":base
            })
        counts[kind] = len(seen)
    expected_pairs = math.comb(n, 2)
    if counts["wide"] != expected_pairs or counts["quinella"] != expected_pairs:
        raise ValueError("HOLD_INCOMPLETE_UNORDERED_PAIR_MARKETS")
    if counts["exacta"] != n*(n-1):
        raise ValueError("HOLD_INCOMPLETE_EXACTA_MARKET")
    results={}
    for kind in TYPES:
        sub = [x for x in table if x["type"] == kind]
        def compact(x):
            return {k:x[k] for k in ("selection", "source_odds_low",
                    "break_even_probability","unit_gross_market_gamma_1",
                    "min_model_unit_gross","p_by_model")}
        results[kind] = {
            "shown_tickets":len(sub),
            "model_positive_gamma_1":sum(x["unit_gross_market_gamma_1"]>1 for x in sub),
            "model_positive_all":sum(x["min_model_unit_gross"]>1 for x in sub),
            "top_baseline":[compact(x) for x in sorted(sub,key=lambda x:-x["unit_gross_market_gamma_1"])[:5]],
            "top_model_min":[compact(x) for x in sorted(sub,key=lambda x:-x["min_model_unit_gross"])[:5]],
        }
    return {
        "status":"PRESTART_HYPOTHETICAL_PL_ONLY_NOT_A_VALIDATED_EV",
        "race_id":doc["race_id"],
        "source_observed_at_jst":doc["page_observed_at_jst"],
        "source_timestamps_separately_verified":bool(doc.get("source_timestamps_separately_verified",False)),
        "original_sealed_M1_used":sealed is not None,
        "total_quoted_tickets":len(table),
        "coverage":counts,
        "proposed_amounts":None,
        "risk_warning":"No budget optimum exists without an objective, bankroll constraint, and calibrated true event probabilities.",
        "models":list(forecasts),
        "by_bet_type":results,
        "limitations":[
            "Observed web page time is not the same as every ticket-pool publication time.",
            "PLACE/WIDE upper-lower conditional payout bands are not uncertainty confidence intervals.",
            "TRIO and TRIFECTA can be top-K lists: model ranking is only within shown quotes.",
            "Every win horse has identical unit expected gross under normalized inverse-odds PL gamma=1.",
            "Positive model gross is not proof of positive real expected profit.",
            "No official finish results are used; frozen prospective forecasts remain unchanged."
        ],
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",type=Path,required=True,
                    help="Private normalized quotes; may contain non-redistributable raw prices")
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    result=evaluate(json.loads(a.input.read_text(encoding="utf-8")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"source_event_count":result["total_quoted_tickets"]}))


if __name__ == "__main__":
    main()
