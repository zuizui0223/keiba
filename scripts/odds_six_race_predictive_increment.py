#!/usr/bin/env python3
"""Postrace pair scoring of archived early vs later win-odds forecasts.

6 historical races, 2 meeting dates:
  2026-10-12 Kyoto 8-12R have pre-race Yahoo full-field paired quotes and
  AFTER-the-race JRA official finish 1-3.
  2026-10-18 Kyoto 11R Shuka Sho has 4 pre-race full-field win snapshots and
  independently verified AFTER-the-race JRA finish 1-3.

Never re-fit a model to these 6 races or add them to frozen v3.1 holdout.
Pre-race models depend ONLY on archived odds and PL's mathematically exact
finish ranking probabilities; official outcome tables are loaded only AFTER
the forecasts exist. The two date cohorts have different horizons and quote
providers; contrast both race weighting and equal-meeting-date weighting.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha1
import json
import math
from pathlib import Path
from statistics import mean
from urllib.parse import urlparse

from odds_real_multirace_archive_audit import SOURCE_SHA, read_file, _one_race
from odds_threshold_forward_eval import order_probabilities
from shuka2026_odds_information_hierarchy import read_locked, load_snapshots

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_OCT12 = ROOT / "data/2026-10-12/official-results-final.json"
OFFICIAL_OCT12_BLOB_SHA = "fdcc70b78c64a50b8a0f566868b38b69ce2c6ff8"
OFFICIAL_SHUKA = ROOT / "docs/evidence/shuka2026-top3-20261023.json"
STATUS = "SIX_RACE_TWO_MEETING_DATES_RETROSPECTIVE_NO_HOLDOUT_OR_VALIDATED_WIN_RATE"
METRICS = ("win_categorical_log_loss", "win_multiclass_brier",
           "top3_binary_brier_mean_per_horse", "top3_binary_log_loss_mean_per_horse")


def _aware(ts):
    value = datetime.fromisoformat(ts)
    if value.utcoffset() is None:
        raise ValueError("HOLD_MISSING_OFFSET_TIMESTAMP")
    return value


def _load_official(root, path, expected_git_blob=None):
    raw = (Path(root) / path).read_bytes()
    if expected_git_blob and sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != expected_git_blob:
        raise ValueError("HOLD_OFFICIAL_RESULT_SOURCE_DRIFT")
    return json.loads(raw.decode("utf-8"))


def verify_official_oct12(root):
    official = _load_official(root, OFFICIAL_OCT12.relative_to(ROOT),
                              OFFICIAL_OCT12_BLOB_SHA)
    if (official.get("date") != "2026-10-12"
            or official.get("venue") != "京都"
            or official.get("status") != "official_top3_complete_7_to_12"):
        raise ValueError("HOLD_INCORRECT_OCT12_OFFICIAL_COHORT")
    verified_at = _aware(official["verified_at_jst"])
    for race_number in range(8, 13):
        outcome = official["races"][str(race_number)]
        if (outcome["source_type"] != "JRA_official"
                or not outcome["complete_top3"]
                or len(outcome["positions"]) != 3
                or len(set(outcome["positions"])) != 3
                or urlparse(outcome["source_url"]).hostname not in
                ("www.jra.go.jp", "app.jra.jp", "jra.jp")):
            raise ValueError("HOLD_UNVERIFIED_JRA_OFFICIAL_TOP3")
    return official, verified_at


def verify_official_shuka(root):
    official = _load_official(root, OFFICIAL_SHUKA.relative_to(ROOT))
    u = urlparse(official["source_url"])
    if (official.get("status") != "POSTRACE_OFFICIAL_JRA_TOP3_ONLY"
            or official.get("date") != "2026-10-18"
            or official.get("race_id") != "2608040711"
            or u.scheme != "https"
            or u.hostname not in ("www.jra.go.jp", "jra.jp", "app.jra.jp")
            or official.get("source_type") != "JRA_official"
            or len(official.get("top3", [])) != 3
            or len(set(official["top3"])) != 3
            or official["verified_on_jst"] <= "2026-10-18"):
        raise ValueError("HOLD_UNVERIFIED_SHUKA_JRA_TOP3")
    return official


def _odds_probabilities(price_by_number):
    if len(price_by_number) < 5:
        raise ValueError("HOLD_NOT_COMPLETE_FIELD")
    ids = sorted(price_by_number)
    if (len(ids) != len(set(ids)) or
            any(type(k) is not int or type(price_by_number[k]) not in (int, float)
                or not math.isfinite(price_by_number[k])
                or price_by_number[k] <= 1 for k in ids)):
        raise ValueError("HOLD_INVALID_WIN_QUOTE")
    win, top3 = order_probabilities([1/price_by_number[k] for k in ids])
    if not (math.isclose(sum(win), 1.0, abs_tol=1e-10)
            and math.isclose(sum(top3), 3.0, abs_tol=1e-10)):
        raise ValueError("HOLD_MASS_NOT_COHERENT")
    return {"numbers": ids, "win": win, "top3": top3}


def collect_pre_race_forecasts(root=ROOT):
    """The output of this function is deliberately outcome-free."""
    prepared = []
    for race_no in range(8, 13):
        a_spec, b_spec = SOURCE_SHA[race_no]
        a, b = read_file(root, a_spec), read_file(root, b_spec)
        _one_race(a, b, race_no)  # strict full-field & publication-time audit
        early = {h["number"]: h["win_odds"] for h in a["horses"]}
        late = {h["selection"][0]: h["odds_low"] for h in b["quotes"]["win"]}
        t0 = _aware(a["odds_updated_at_jst"])
        t1 = _aware(b["updated_at_jst"])
        start = _aware(a["start_jst"])
        if not t0 < t1 < start:
            raise ValueError("HOLD_TIME_TRAVEL_PRICE_FEATURES")
        prepared.append({
            "race_id": a["race_id"],
            "venue": "京都", "race_number": race_no,
            "meeting_day": "2026-10-12",
            "pre_race_clock": {"first":t0.isoformat(),"last":t1.isoformat(),
                               "post":start.isoformat()},
            "source_pair": "Yahoo/Yahoo; quoted publisher update minute may differ from receipt time",
            "early": _odds_probabilities(early),
            "later": _odds_probabilities(late),
        })
    shuka = load_snapshots(read_locked(root))
    a, b = shuka[0], shuka[-1]
    if not _aware(a["observed_at"]) < _aware(b["observed_at"]) < _aware("2026-10-18T15:40:00+09:00"):
        raise ValueError("HOLD_SHUKA_RACE_START_PAST_QUOTE")
    prepared.append({
        "race_id": "2608040711","venue":"京都","race_number":11,
        "meeting_day":"2026-10-18",
        "pre_race_clock":{"first":a["observed_at"],"last":b["observed_at"],
                          "post":"2026-10-18T15:40:00+09:00"},
        "source_pair":"Yahoo extraction start/JRA producer-reported win update; not synchronized source semantics",
        "early":_odds_probabilities(a["win"]),
        "later":_odds_probabilities(b["win"]),
    })
    if len({p["race_id"] for p in prepared}) != 6:
        raise ValueError("HOLD_DUPLICATED_RACE_COMPARISON")
    return prepared


def score_forecast(p, top3_numbers):
    """Proper score for one actual race; horse entries are not repeats."""
    ids = p["numbers"]
    if (len(top3_numbers)!=3 or len(set(top3_numbers))!=3
            or not set(top3_numbers).issubset(ids)):
        raise ValueError("HOLD_TOP3_MISSING_FROM_PRICE_FIELD")
    i = ids.index(top3_numbers[0])
    truth = set(top3_numbers)
    win = p["win"]
    top = p["top3"]
    return {
        "win_categorical_log_loss":-math.log(max(win[i],1e-12)),
        "win_multiclass_brier":sum(
            (win[j]-(1 if ids[j]==top3_numbers[0] else 0))**2
            for j in range(len(ids))),
        "top3_binary_brier_mean_per_horse":mean(
            (top[j]-(1 if ids[j] in truth else 0))**2
            for j in range(len(ids))),
        "top3_binary_log_loss_mean_per_horse":-mean(
            math.log(max(min(top[j],1-1e-12),1e-12))
            if ids[j] in truth else
            math.log(max(min(1-top[j],1-1e-12),1e-12))
            for j in range(len(ids))),
        "realized_winner_market_probability_pct":100*win[i],
    }


def score_against_outcomes(forecasts, official_oct12, official_shuka):
    outputs=[]
    for f in forecasts:
        day=f["meeting_day"]
        if day=="2026-10-12":
            outcome = official_oct12["races"][str(f["race_number"])]
            top3=outcome["positions"]
            src=outcome["source_url"]
        elif day=="2026-10-18":
            top3=official_shuka["top3"]
            src=official_shuka["source_url"]
        else:
            raise ValueError("HOLD_UNEXPECTED_MEETING_DAY")
        if f["early"]["numbers"] != f["later"]["numbers"]:
            raise ValueError("HOLD_CHANGED_PRICE_ROSTER")
        a=score_forecast(f["early"],top3)
        b=score_forecast(f["later"],top3)
        outputs.append({
            "race_id":f["race_id"],"meeting_day":day,
            "race_label":f["venue"]+str(f["race_number"])+"R",
            "runner_count":len(f["early"]["numbers"]),
            "outcome_top3_official_horse_numbers":list(top3),
            "jra_official_result_url":src,
            "quotes_first_last":f["pre_race_clock"],
            "quote_source_comparability":f["source_pair"],
            "early_score":a,"later_score":b,
            "late_minus_early_lower_is_better":{
                metric:b[metric]-a[metric] for metric in METRICS
            },
        })
    return outputs


def summarize_scored_races(races):
    if not races:
        raise ValueError("HOLD_NO_PAIRED_SCORING_RACES")
    days=sorted({r["meeting_day"] for r in races})
    def calc(rows):
        return {metric:{
            "early":mean(r["early_score"][metric] for r in rows),
            "later":mean(r["later_score"][metric] for r in rows),
            "late_minus_early":mean(
                r["late_minus_early_lower_is_better"][metric] for r in rows),
            "number_races_late_better":sum(
                r["late_minus_early_lower_is_better"][metric] < 0 for r in rows)
        } for metric in METRICS}
    by_day={day:{
        "actual_race_count":sum(r["meeting_day"]==day for r in races),
        "metrics":calc([r for r in races if r["meeting_day"]==day])
    } for day in days}
    equal_race=calc(races)
    date_equal = {metric:{
        "late_minus_early":mean(by_day[day]["metrics"][metric]["late_minus_early"]
                                for day in days)
    } for metric in METRICS}
    return {
        "status":STATUS,
        "total_independent_races":len(races),
        "distinct_meeting_dates":len(days),
        "distinct_horse_race_rows":sum(r["runner_count"] for r in races),
        "equal_race_weighting_descriptive":equal_race,
        "by_meeting_day":by_day,
        "equal_meeting_day_weighting_descriptive":date_equal,
        "direction_changes_under_meeting_day_vs_race_weighting_win_log_loss":
            (equal_race["win_categorical_log_loss"]["late_minus_early"]
             *date_equal["win_categorical_log_loss"]["late_minus_early"]<0),
        "scientific_limitations":[
            "The same calendar day supplies five of six races; two meeting-day clusters cannot support stable statistical inference.",
            "Kyoto Oct12 paired prices are about 51-69 minutes apart, while Shuka spans Oct17 daytime to Oct18 midday; the exposure windows are not exchangeable.",
            "Shuka crosses Yahoo extraction-start and JRA official source-update timestamp semantics; not an atomic provider-matched comparison.",
            "Win odds -> PL Top3 is a model assumption, not empirically calibrated place probability.",
            "Earlier/later score improvement is descriptive; outcomes were known when this retrospective comparison was designed.",
            "Do not optimize an odds threshold, model coefficients, ticket purchases or frozen v3.1 holdout on these historical outcomes.",
            "No horse-by-horse finish times, causal social behavior, intrarace GPS or actual return on investment is inferred.",
        ],
    }


def audit(root=ROOT):
    predictions=collect_pre_race_forecasts(root)
    # Only now read the official outcomes. Forecasts are a pure function of
    # previously archived pre-race quote data and locked model assumptions.
    oct12, verified_at=verify_official_oct12(root)
    shuka=verify_official_shuka(root)
    if any(_aware(v["pre_race_clock"]["post"])>=verified_at
           for v in predictions if v["meeting_day"]=="2026-10-12"):
        raise ValueError("HOLD_RESULTS_OBSERVED_BEFORE_START")
    scored=score_against_outcomes(predictions,oct12,shuka)
    summary=summarize_scored_races(scored)
    summary["pre_race_model"] = "Plackett-Luce normalized 1/win-odds ranking; exact marginal Top3."
    summary["source_pinning"]={
        "oct12_complete_JRA_results_git_blob":OFFICIAL_OCT12_BLOB_SHA,
        "shuka_official_JRA_link":shuka["source_url"],
    }
    summary["results"] = scored
    return summary


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,default=Path("tmp/odds-real-six-race-scores.json"))
    args=ap.parse_args()
    result=audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "races":result["total_independent_races"],
        "dates":result["distinct_meeting_dates"],
        "horse_entries":result["distinct_horse_race_rows"],
        "scores":result["equal_race_weighting_descriptive"],
        "equal_day_differences":result["equal_meeting_day_weighting_descriptive"],
        "sign_reversal_by_grouping":result[
            "direction_changes_under_meeting_day_vs_race_weighting_win_log_loss"],
    },ensure_ascii=False))


if __name__=="__main__":
    main()
