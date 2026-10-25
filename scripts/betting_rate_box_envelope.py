#!/usr/bin/env python3
"""Exact Plackett-Luce rate-box envelopes for pre-start ticket sensitivity.

Assume rate_i = displayed_win_odds_i**(-gamma) * factor_i,
where factors lie independently in [1-delta, 1+delta].
For the event "all chosen horses finish in the first K", increasing any
chosen horse's rate or decreasing any outsider's rate cannot destroy a
previous success. Couple races using T_i=Exp(1)_i/rate_i: selected clocks
decrease and outsider clocks increase. Consequently, min/max probabilities
over the ENTIRE factor box occur at two specified corners, with no Monte
Carlo or exponential-time search over 2^n corners.

The gamma parameter is evaluated on a FINITE grid, not continuously.
Market prices, latent-rate boxes and probability model are all hypothetical
and do NOT establish a true positive expected betting return.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
from pathlib import Path

from betting_crosspool_shape_audit import exact_pl

KINDS = {"wide": 2, "quinella": 2, "trio": 3}


def _aware(value: str):
    ts = datetime.fromisoformat(value)
    if ts.utcoffset() is None:
        raise ValueError("HOLD_NAIVE_MARKET_TIME")
    return ts


def validate_inputs(win: dict, quotes: dict):
    if win.get("race_id") != quotes.get("race_id"):
        raise ValueError("HOLD_RACE_ID_MISMATCH")
    start = _aware(win["scheduled_post_jst"])
    update = _aware(win["source_updated_at_jst"])
    if not update < start - timedelta(minutes=10):
        raise ValueError("HOLD_LATE_WIN_QUOTES")
    if not str(win.get("source_url", "")).startswith("https://"):
        raise ValueError("HOLD_MISSING_PRICE_URL")
    horses = {}
    for row in win.get("horses", []):
        number, price = row.get("number"), row.get("win_odds")
        if (type(number) is not int or number in horses or number < 1
                or type(price) not in (float,int) or price <= 1
                or not math.isfinite(price)):
            raise ValueError("HOLD_INVALID_PRICE_OR_DUPLICATE_RUNNER")
        horses[number] = float(price)
    if len(horses) < 4 or len(horses) != win.get("runner_count"):
        raise ValueError("HOLD_INCOMPLETE_FIELD")
    if not isinstance(quotes.get("key_tickets"),list) or not quotes["key_tickets"]:
        raise ValueError("HOLD_NO_TICKETS")
    for row in quotes["key_tickets"]:
        kind = row.get("ticket_kind")
        members = row.get("members")
        low = row.get("low")
        high = row.get("high")
        if kind not in KINDS or not isinstance(members,list):
            raise ValueError("HOLD_INVALID_TICKET_TYPE")
        if (len(members) != KINDS[kind] or any(type(n) is not int or n not in horses
                                               for n in members)
                or len(set(members)) != len(members)):
            raise ValueError("HOLD_INVALID_TICKET_MEMBERS")
        if (type(low) not in (float,int) or type(high) not in (float,int)
                or not math.isfinite(low) or not math.isfinite(high)
                or low <= 1 or high < low):
            raise ValueError("HOLD_INVALID_TICKET_PRICE")
    return horses


def _p(horses: dict[int,float], kind: str, members: tuple[int,...],
       gamma: float, delta: float, side: str):
    if kind not in KINDS or len(members) != KINDS[kind]:
        raise ValueError("HOLD_INVALID_TICKET_EVENT")
    if (not 0 <= delta < 1 or not math.isfinite(delta) or gamma <= 0
            or not math.isfinite(gamma) or side not in ("min","base","max")):
        raise ValueError("HOLD_INVALID_SCENARIO")
    selected = set(members)
    rate = {}
    for number, price in horses.items():
        factor = (1 if side == "base" else
                  (1-delta if number in selected else 1+delta) if side=="min" else
                  (1+delta if number in selected else 1-delta))
        rate[number] = price ** (-gamma) * factor
    fake_prices = {number:1/value for number,value in rate.items()}
    model = exact_pl(fake_prices,1.0)
    return model[kind][tuple(sorted(members))]


def envelope(horses: dict[int,float], ticket: dict,
             gamma_grid: tuple[float,...], delta:float):
    if not gamma_grid:
        raise ValueError("HOLD_EMPTY_GAMMA_GRID")
    kind = ticket["ticket_kind"]
    members = tuple(ticket["members"])
    low = ticket["low"]
    by_gamma={}
    for gamma in gamma_grid:
        p_low = _p(horses,kind,members,gamma,delta,"min")
        p_center = _p(horses,kind,members,gamma,delta,"base")
        p_high = _p(horses,kind,members,gamma,delta,"max")
        if not p_low-1e-10 <= p_center <= p_high+1e-10:
            raise AssertionError("PL_MONOTONE_COUPLING_FAILED")
        by_gamma[f"{gamma:g}"] = {
            "probability_low":p_low, "probability_baseline":p_center,
            "probability_high":p_high,
            "p_times_intermediate_quote_low":low*p_low,
            "p_times_intermediate_quote_baseline":low*p_center,
            "p_times_intermediate_quote_high":low*p_high,
        }
    return {
        "min_model_gross_multiplier":min(v["p_times_intermediate_quote_low"] for v in by_gamma.values()),
        "max_model_gross_multiplier":max(v["p_times_intermediate_quote_high"] for v in by_gamma.values()),
        "by_gamma":by_gamma,
    }


def audit(win:dict, quotes:dict,
          gammas:tuple[float,...]=(0.75,1.,1.25),
          spreads:tuple[float,...]=(0.,0.1,0.2)):
    horses = validate_inputs(win,quotes)
    rows=[]
    for ticket in quotes["key_tickets"]:
        rows.append({
            "ticket_kind":ticket["ticket_kind"], "members":ticket["members"],
            "intermediate_price_low":ticket["low"],
            "scenario_by_rate_spread": {
                f"{delta:g}":envelope(horses,ticket,gammas,delta)
                for delta in spreads
            }
        })
    return {
        "status":"PRE_RACE_SYNTHETIC_UNCALIBRATED_NOT_PROFIT_EXPECTATION",
        "race_id":win["race_id"], "runner_count":len(horses),
        "source_win_update_jst":win["source_updated_at_jst"],
        "source_ticket_market_updates_jst":quotes.get("source_times_jst"),
        "gamma_finite_grid_not_fitted":list(gammas),
        "hypothetical_rate_box_spreads_not_fitted":list(spreads),
        "method":"Exact PL probability; exponential-race monotonicity gives two extreme rate-box corners at each gamma.",
        "tickets":rows,
        "limitations":[
            "The odds and payouts are intermediate; WIN and ticket pools have asynchronous timestamps.",
            "Rate box +/-10/20 percent is a chosen scenario, NOT a confidence interval or ground-effect estimate.",
            "Finite gamma grid does NOT establish the bound for all real gamma values.",
            "Positive model P x displayed odds is NOT a proven true positive betting expectation.",
            "Original 2026-10-24 externally sealed M0/M1/M2 prediction is unchanged.",
            "No target-race finish results are loaded."
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--win-json",type=Path,required=True)
    p.add_argument("--market-summary",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    w=json.loads(a.win_json.read_text(encoding="utf-8"))
    m=json.loads(a.market_summary.read_text(encoding="utf-8"))
    report=audit(w,m)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"tickets":len(report["tickets"])}))


if __name__=="__main__":
    main()
