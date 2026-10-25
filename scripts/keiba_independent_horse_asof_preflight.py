#!/usr/bin/env python3
"""Offline gate for an independently sourced horse-history input to coupled ABM.

This accepts local source/receipt/market snapshots but NEVER authenticates
the claimed reception timestamp against an external trusted server.
Therefore output is always LOCAL_CLOCK_CHECK_ONLY_NOT_PROSPECTIVE_EVIDENCE.
An authenticated GitHub server or third-party pre-event time receipt and
independent source-rights audit are separate future requirements.

Unlike the six archived Oct 12/18 reconstructions, such a source would
have to be recorded BEFORE THE EARLIEST market quote used as q0. Otherwise
the horse signal would be used by synthetic bettors before it existed.
"""
from __future__ import annotations
import argparse
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlparse

from odds_threshold_regime_bridge import aware, market_features
from keiba_coupled_history_falsification import form_prior
from keiba_coupled_horse_market_pde import couple_prestart

HISTORY_SCHEMA = "KEIBA_INDEPENDENT_PAST_HORSE_SOURCE_V1"
RECEIPT_SCHEMA = "KEIBA_LOCAL_HORSE_HISTORY_RECEIPT_V1"
STATUS = "CLOCK_ORDER_CHECKED_LOCAL_SOURCE_NOT_EXTERNALLY_AUTHENTICATED"


def _positive_ids(d):
    if not isinstance(d, dict) or len(d) < 5:
        raise ValueError("HOLD_MISSING_RUNNER_NUMBER_MAPPING")
    try:
        ids = [int(k) for k in d]
    except (ValueError,TypeError):
        raise ValueError("HOLD_BAD_RUNNER_NUMBER_KEY")
    if (len(ids) != len(set(ids)) or any(x<=0 for x in ids)
            or any(str(x) not in d for x in ids)):
        raise ValueError("HOLD_DUPLICATE_OR_NONCANONICAL_RUNNER_NUMBER")
    return sorted(ids)


def _url(u):
    x=urlparse(str(u))
    if x.scheme!="https" or not x.hostname:
        raise ValueError("HOLD_SOURCE_HTTPS_URL_REQUIRED")
    return x.geturl()


def verify_offline_source(source_bytes: bytes, receipt: dict, market_row: dict):
    """Only emits an intrinsically UNATTESTED local-source result.

    market_row first & last quotes must both have exact source time and
    be available before the scheduled race. The independent horse source
    must have been locally captured before or at FIRST market timestamp,
    not merely before post time.
    """
    if not isinstance(source_bytes,bytes) or not isinstance(receipt,dict):
        raise ValueError("HOLD_INVALID_SOURCE_BYTES_OR_RECEIPT")
    if receipt.get("schema")!=RECEIPT_SCHEMA:
        raise ValueError("HOLD_WRONG_LOCAL_RECEIPT_SCHEMA")
    if receipt.get("externally_attested") is not False:
        raise ValueError("HOLD_SELF_ASSERTED_EXTERNAL_ATTESTATION_IS_NOT_PROOF")
    if receipt.get("operator_declares_rights_review") is not True:
        raise ValueError("HOLD_SOURCE_RIGHTS_NOT_REVIEWED_BY_OPERATOR")
    digest=sha256(source_bytes).hexdigest()
    if receipt.get("original_source_sha256")!=digest:
        raise ValueError("HOLD_SOURCE_CONTENT_SHA256_MISMATCH")
    _url(receipt.get("original_source_url"))
    source=json.loads(source_bytes.decode("utf-8"))
    if source.get("schema")!=HISTORY_SCHEMA:
        raise ValueError("HOLD_HORSE_SOURCE_WRONG_SCHEMA")
    f=market_features(market_row)
    if (source.get("race_id")!=market_row["race_id"] or
            source.get("target_date")!=market_row["meeting_day"]):
        raise ValueError("HOLD_SOURCE_RACE_DATE_MISMATCH")
    capture=aware(receipt.get("source_received_at_jst"))
    upstream=aware(receipt.get("publisher_updated_at_jst"))
    earliest=aware(market_row["initial_quote_at"])
    first_received=aware(market_row.get("initial_quote_received_at_jst"))
    latest=aware(market_row["latest_quote_at"])
    later_received=aware(market_row.get("latest_quote_received_at_jst"))
    frozen_locally=aware(market_row.get("local_forecast_generated_at_jst"))
    post=aware(market_row["post_at"])
    # Publication clocks and OUR acquisition clocks are separate. All
    # source declarations are still LOCAL and not independent proof.
    # Both historical signal AND first market source must be available
    # before the simulated bettor path begins, without time travel.
    if not (upstream<=capture<=earliest<=first_received<
            latest<=later_received<=frozen_locally<=post-timedelta(minutes=10)):
        raise ValueError("HOLD_HORSE_SOURCE_OR_QUOTE_RECEPTION_TIME_TRAVEL")
    official_name_map=receipt.get("declared_official_horse_names_by_number")
    ids=_positive_ids(official_name_map)
    if ids!=f["horse_numbers"]:
        raise ValueError("HOLD_SOURCE_OFFICIAL_ROSTER_DOES_NOT_MATCH_MARKET")
    if (not isinstance(source.get("horses"),list) or
            len(source["horses"])!=len(ids)):
        raise ValueError("HOLD_INCOMPLETE_INDEPENDENT_HORSE_FORM_SOURCE")
    out={}
    for h in source["horses"]:
        n=h.get("number")
        if type(n) is not int or n not in ids or n in out:
            raise ValueError("HOLD_DUPLICATE_OR_MISSING_HORSE_IN_SOURCE")
        if (not isinstance(h.get("name"),str) or
                h["name"]!=official_name_map[str(n)]):
            raise ValueError("HOLD_HORSE_NUMBER_NAME_CROSSWALK_MISMATCH")
        runs=h.get("past_runs")
        if not isinstance(runs,list):
            raise ValueError("HOLD_MISSING_HORSE_RUNS")
        for p in runs:
            if not isinstance(p,dict) or not all(
                    k in p for k in ("date","finish","distance_m","surface")):
                raise ValueError("HOLD_PAST_RUN_MISSING_REQUIRED_FIELDS")
            if date.fromisoformat(p["date"])>=date.fromisoformat(
                    source["target_date"]):
                raise ValueError("HOLD_CURRENT_OR_FUTURE_HORSE_RACE_RESULT")
        out[n]={"full_history_before_target":runs}
    if set(out)!=set(ids):
        raise ValueError("HOLD_NOT_ALL_MARKET_HORSES_PRESENT")
    if (type(source.get("distance_m")) is not int or
        source["distance_m"]<800 or
        source.get("target_surface") not in ("芝","ダ","障")):
        raise ValueError("HOLD_BAD_HORSE_RACE_ENVIRONMENT")
    archive={"target_date":source["target_date"],
             "target_surface":source["target_surface"],
             "distance_m":source["distance_m"],"rows":out}
    form=form_prior(market_row,archive)
    return {
        "status":STATUS,
        "race_id":source["race_id"],
        "checked_first_market_timestamp":market_row["initial_quote_at"],
        "first_market_received_at":market_row["initial_quote_received_at_jst"],
        "latest_market_received_at":market_row["latest_quote_received_at_jst"],
        "local_forecast_generated_at":market_row["local_forecast_generated_at_jst"],
        "local_source_received_at":receipt["source_received_at_jst"],
        "first_market_horse_numbers":ids,
        "horse_history_prior":form["prior"],
        "source_sha256":digest,
        "independent_external_time_receipt_verified":False,
        "real_provider_rights_independently_verified":False,
        "no_official_podium_or_postrace_label_consumed":True,
        "not_an_authentic_prospective_forecast":True,
        "prior_calibrated_from_real_winner_outcomes":False,
        "history_records_examined":form["past_race_records_examined"],
        "source_data_not_suitable_for_public_redistribution_by_this_tool":True,
    }


def local_demo_coupling(source_bytes, receipt, market_row, *, draws=60,
                        seed=20261025):
    checked=verify_offline_source(source_bytes,receipt,market_row)
    sim=couple_prestart(
        market_row, distance_m=json.loads(source_bytes)["distance_m"],
        draws=draws, seed=seed, horse_prior=checked["horse_history_prior"])
    from numpy import isclose
    for key,p in sim["predictions"].items():
        if not isclose(sum(p["win"]),1,atol=1e-9):
            raise ValueError("HOLD_LOCAL_COHERENT_WIN_PROBABILITY_MASS")
        if not isclose(sum(p["top3"]),3,atol=1e-9):
            raise ValueError("HOLD_LOCAL_COHERENT_TOP3_MASS")
    return {
        "status":STATUS,
        "race_id":checked["race_id"],
        "local_history_sha256":checked["source_sha256"],
        "prestart_input_clock_consistent_if_user_receipts_truthful":True,
        "external_timestamp_authentication":"HOLD",
        "real_data_rights_independently_audited":False,
        "not_validated_win_probability_or_wager_return":True,
        "no_target_outcome_read":True,
        "horse_prior_source":sim["horse_prior_source"],
        "model_predicted_event_probs":{
            k:sim["predictions"][k] for k in (
                "horse_P9_weak","horse_SDE_weak","market_mixed",
                "market_threshold_mixed","observed_M0")},
        "horse_numbers":checked["first_market_horse_numbers"],
        "scientific_warning":
            "Local self-reported reception timestamps and source SHA are "
            "not independent external proof of a prospective prediction.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--history-source",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--market-panel",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--draws",type=int,default=60)
    args=p.parse_args()
    market=json.loads(args.market_panel.read_text(encoding="utf-8"))
    # JSON string keys are converted to canonical horse number ints in the
    # pre-existing paired-quote market schema, but not in names crosswalk.
    for market_key in ("first_odds","last_odds"):
        prices=market[market_key]
        if (not isinstance(prices,dict) or len(prices)!=len(set(prices))
                or any(not str(i).isdecimal() or str(int(i))!=str(i)
                       for i in prices)):
            raise ValueError("HOLD_NONCANONICAL_MARKET_PANEL_HORSE_IDS")
        market[market_key]={int(i):v for i,v in prices.items()}
    result=local_demo_coupling(
        args.history_source.read_bytes(),
        json.loads(args.receipt.read_text(encoding="utf-8")),
        market,draws=args.draws)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({"status":result["status"],
                      "race_id":result["race_id"],
                      "forecast_is_externally_authenticated":False},
                     ensure_ascii=False))


if __name__=="__main__":
    main()
