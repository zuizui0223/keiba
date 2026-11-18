#!/usr/bin/env python3
"""Observed market CONCENTRATION in saved 2026 Japanese win-odds snapshots.

This is an actual single-receipt-time study of archived intermediary quotes.
No official source update time, canonical horse/pedigree IDs, betting volume,
historical price trajectory, genotype, or winning-probability calibration exists.
Never label support shares as actual ticket shares or realised win chances.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

LOCKED_SOURCE_SHA = "5423270f25ce79cd393116ab944dc3fe5d709a67ed169711d3e1eb93bef77e8e"


def market_state(horses: list[dict]) -> dict:
    if len(horses)<3:
        raise ValueError("HOLD_RACE_FIELD_TOO_SMALL")
    numbers = [h.get("number") for h in horses]
    if any(x is None for x in numbers) or len(numbers)!=len(set(numbers)):
        raise ValueError("HOLD_UNKNOWN_OR_DUPLICATE_HORSE_NUMBERS")
    odds = []
    for h in horses:
        try:
            value=float(h.get("win_odds"))
        except (ValueError,TypeError) as exc:
            raise ValueError("HOLD_MISSING_OR_NONNUMERIC_ODDS") from exc
        if not math.isfinite(value) or value<=1.0:
            raise ValueError("HOLD_INVALID_ODDS")
        odds.append(value)
    inverse=[1/x for x in odds]
    overround=sum(inverse)
    if not math.isfinite(overround) or overround<=0:
        raise ValueError("HOLD_ODDS_INVERSE_SUM")
    q=[x/overround for x in inverse]
    H=sum(x*x for x in q)
    shannon=-sum(x*math.log(x) for x in q)
    ranked=sorted(q,reverse=True)
    return {
        "horse_count":len(q),
        "reciprocal_odds_sum":overround,
        "relative_support_favorite":ranked[0],
        "relative_support_top3":sum(ranked[:3]),
        "HHI_normalized_support":H,
        "effective_horses_simpson":1/H,
        "effective_horses_shannon":math.exp(shannon),
        "effective_fraction_of_actual_field":1/(len(q)*H),
        "single_snapshot_only":True,
    }


def audit_snapshot(path:Path, *, require_sha:str|None=LOCKED_SOURCE_SHA,
                   include_share_vector:bool=False):
    raw=path.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if require_sha is not None and sha!=require_sha:
        return {
            "status":"HOLD_SNAPSHOT_SHA_CHANGED",
            "observed_sha256":sha,"expected_sha256":require_sha,
            "no_market_effect_calculated":True,
        }
    source=json.loads(raw)
    races=source.get("races")
    if not isinstance(races,list) or not races:
        raise ValueError("HOLD_NO_RACE_QUOTES")
    seen_races=set()
    rows=[]
    preview=[]
    for r in races:
        race=r.get("race_id")
        if not race or race in seen_races:
            raise ValueError("HOLD_DUPLICATE_OR_MISSING_RACE_ID")
        seen_races.add(race)
        horses=r.get("horses")
        if not isinstance(horses,list) or r.get("runner_count")!=len(horses):
            raise ValueError("HOLD_INCOMPLETE_OR_INCONSISTENT_ROSTER")
        m=market_state(horses)
        m["race_id"]=race
        m["venue"]=r.get("venue")
        m["race_no"]=r.get("race")
        m["source_horse_ID_count"]=sum(bool(x.get("horse_id")) for x in horses)
        m["source_sire_ID_count"]=sum(bool(x.get("sire_id")) for x in horses)
        m["source_dam_ID_count"]=sum(bool(x.get("dam_id")) for x in horses)
        m["horses_with_meisho_prefix"]=sum(
            str(x.get("name","")).startswith("メイショウ") for x in horses
        )
        if r.get("win_place_upstream_updated_at") or r.get("upstream_quote_updated_at"):
            raise ValueError("HOLD_AUDIT_ASSUMES_SOURCE_UPSTREAM_TIMES_ABSENT")
        if include_share_vector:
            # For ABM initialization only; values ordered by supplied
            # HORSE NUMBER, never used to infer horse names or genetic data.
            ordered=sorted(horses,key=lambda x:int(x["number"]))
            inv=[1.0/float(x["win_odds"]) for x in ordered]
            p=sum(inv)
            preview.append({
                "race_id":race,"n":len(ordered),
                "initial_relative_support":[x/p for x in inv],
            })
        rows.append(m)
    metrics=("relative_support_favorite","relative_support_top3",
             "effective_horses_simpson","effective_fraction_of_actual_field",
             "reciprocal_odds_sum")
    summary={
        "source_sha256":sha,
        "races":len(rows),
        "horse_price_rows":sum(x["horse_count"] for x in rows),
        "min_field_size":min(x["horse_count"] for x in rows),
        "max_field_size":max(x["horse_count"] for x in rows),
        **{key+"_across_races_mean":statistics.mean(x[key] for x in rows)
           for key in metrics},
        "total_meisho_named_horses":sum(x["horses_with_meisho_prefix"] for x in rows),
        "total_canonical_horse_ID_rows":sum(x["source_horse_ID_count"] for x in rows),
        "total_sire_ID_rows":sum(x["source_sire_ID_count"] for x in rows),
        "total_dam_ID_rows":sum(x["source_dam_ID_count"] for x in rows),
    }
    result={
        "status":"OBSERVED_SINGLE_SNAPSHOT_MARKET_CONCENTRATION_NOT_GENETICS",
        "source":"2026-10-18 Yahoo intermediary quote saved in keiba repo",
        "source_receipt_window":(
            source.get("observed_window_start_jst"),
            source.get("observed_window_end_jst")),
        "upstream_quote_update_time_verified":False,
        "data_quality":summary,
        "markets":rows,
        "genetic_market_effect_estimated":False,
        "herding_time_series_observed":False,
        "market_support_is_normalized_inverse_odds_not_tickets":True,
        "takeout_not_estimated_from_inverse_odds_sum":True,
        "actual_win_probabilities_not_calibrated":True,
        "relative_price_concentration_only":True,
    }
    if include_share_vector:
        # Privacy & scope: public price rows already archived, but
        # unnecessary row-level share vectors are ONLY ephemeral in memory
        # for seeded original model simulations. Never export them.
        return result,preview
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=audit_snapshot(args.snapshot)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
