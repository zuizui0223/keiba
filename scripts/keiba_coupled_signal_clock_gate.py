#!/usr/bin/env python3
"""Map a REAL declared information receipt to a hypothetical voter round.

No real JRA information-arrival or actual stake transactions are supplied
by this repository. Clock strings are local claims: ordering may be checked
but this code NEVER certifies their truth nor replaces third-party attestation.
This maps a signal to discrete rounds by START times, not by hindsight.
It creates no official bet prediction and never reads horse outcomes.

4 rounds begin at start_time + (k-1)*(end-start)/4. If horse information
is received just AFTER a round's start, it can influence only a LATER round.
After the fourth start, returned round 5 means no information used.
"""
from __future__ import annotations
import argparse
from datetime import timedelta
import json
from pathlib import Path
import math

from odds_threshold_regime_bridge import aware

CLOCK_SCHEMA="KEIBA_CAUSAL_HORSE_SIGNAL_AND_MARKET_RECEIPTS_V1"
STATUS="LOCAL_EVENT_ORDER_AND_ROUND_ASSIGNMENT_NOT_EXTERNALLY_ATTESTED"


def source_clock_to_voter_round(x, *, steps=4):
    if (not isinstance(x,dict) or x.get("schema")!=CLOCK_SCHEMA or
            type(steps) is not int or steps<2 or steps>60):
        raise ValueError("HOLD_INVALID_INFORMATION_CLOCK_CONTRACT")
    if x.get("externally_authenticated_by_third_party") is not False:
        raise ValueError("HOLD_SELF_ASSERTED_EXTERNAL_CLOCK_CERTIFICATION")
    required=(
        "first_win_quote_published_at",
        "first_win_quote_received_at",
        "later_win_quote_published_at",
        "later_win_quote_received_at",
        "local_forecast_created_at",
        "scheduled_post_at",
        "horse_signal_published_at",
        "horse_signal_received_at",
    )
    stamps={key:aware(x.get(key)) for key in required}
    a=stamps["first_win_quote_published_at"]
    b=stamps["first_win_quote_received_at"]
    c=stamps["later_win_quote_published_at"]
    d=stamps["later_win_quote_received_at"]
    e=stamps["local_forecast_created_at"]
    post=stamps["scheduled_post_at"]
    pub=stamps["horse_signal_published_at"]
    rec=stamps["horse_signal_received_at"]
    if not (a<=b<c<=d<=e<=post-timedelta(minutes=10)):
        raise ValueError("HOLD_UNVERIFIED_OR_OUT_OF_ORDER_QUOTE_RECEPTION_CLOCKS")
    if not pub<=rec:
        raise ValueError("HOLD_HORSE_SIGNAL_RECEPTION_PRECEDES_PUBLICATION")
    if rec>e:
        raise ValueError("HOLD_HORSE_SIGNAL_NOT_KNOWN_AT_LOCAL_FORECAST")
    duration=(d-b).total_seconds()
    if duration<=0:
        raise ValueError("HOLD_MISSING_CLOCKED_SIGNAL_INTERVAL")
    elapsed=(rec-b).total_seconds()
    if elapsed<=0:
        first_visible=1
    elif elapsed>=duration:
        first_visible=steps+1
    else:
        # ceil works for exact quarter/half timestamps: if signal arrived
        # at a round START it is visible in that round. Just after the
        # start, that round has already voted and it moves to the next.
        first_visible=1+math.ceil((elapsed/duration)*steps)
    if not 1<=first_visible<=steps+1:
        raise ValueError("HOLD_SIGNAL_ROUND_OUT_OF_RANGE")
    return {
        "status":STATUS,
        "signal_first_visible_voter_round":first_visible,
        "voter_rounds":steps,
        "signal_available_round_count":max(0,steps-first_visible+1),
        "signal_arrival_relative_to_first_quote_receipt":(
            "already_available" if first_visible==1 else
            "arrived_too_late_for_any_round" if first_visible==steps+1
            else "staged_after_initial_market"
        ),
        "market_quote_clock_order_locally_consistent":True,
        "horse_signal_publication_precedes_local_receipt":True,
        "independent_external_clock_validation":False,
        "actual_human_bet_timestamps_observed":False,
        "no_real_critical_price_or_biological_phase_identified":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--clock-panel",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    clocks=json.loads(args.clock_panel.read_text(encoding="utf-8"))
    out=source_clock_to_voter_round(clocks)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False))


if __name__=="__main__":
    main()
