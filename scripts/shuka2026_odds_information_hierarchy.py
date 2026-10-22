#!/usr/bin/env python3
"""Shuka Sho odds-path information hierarchy audit + fictional voter ABM.

All observed data are archival pre-race 2026-10-17/18 odds in the
separate analysis/shuka-20261018-official-form branch. The EARLIEST
CAPTURE IS NOT OPENING ODDS. Direct quote times are not always
publisher-updated times. The pair pool is not synchronized with the
win pool. This script does not use results or optimize wagers.

Use:
 python scripts/shuka2026_odds_information_hierarchy.py \
     --output tmp/shuka-odds-hierarchy.json

Status is descriptive / synthetic only; neither feedback causality
nor a predictive threshold can be identified from one race.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha1
from itertools import combinations, permutations
import json
import math
from pathlib import Path
import random
from statistics import mean, pstdev

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {
    "early": (
        "data/2026-10-17/shuka2026-sportsnavi-intermediate-win-odds.json",
        "4bd49e1bf6de7e5d0dda4ff92c972b30adfc21ad"),
    "sat": (
        "data/2026-10-17/shuka2026-sportsnavi-multipool-intermediate-1537.json",
        "6ce23925ec11c165ba3d2f892fd9d5b2fe731a47"),
    "morning": (
        "data/2026-10-18/shuka2026-JRA-official-win-plus-multipool-morning.json",
        "fac2d8132d49a30838320b70c5c43f5429398cc2"),
    "noon": (
        "data/2026-10-18/shuka2026-JRA-all-bet-pools-and-superset-20261018.json",
        "22b36f86573823f1184515196663161c42e8b2f2"),
}
STATUS = "ONE_RACE_DESCRIPTIVE_AND_SYNTHETIC_ABM_ONLY"
POST = datetime.fromisoformat("2026-10-18T15:40:00+09:00")
BANDS = ((0, 5, "<5x"), (5, 15, "5-15x"),
         (15, 50, "15-50x"), (50, math.inf, ">=50x"))


def git_blob_sha(raw: bytes):
    return sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def read_locked(root=ROOT):
    result = {}
    for key, (relpath, required_sha) in SOURCE.items():
        raw = (Path(root) / relpath).read_bytes()
        current_sha = git_blob_sha(raw)
        if current_sha != required_sha:
            raise ValueError("HOLD_CHANGED_ARCHIVED_SOURCE:" + key)
        result[key] = json.loads(raw.decode("utf-8"))
    return result


def _validate_quote_vector(rows):
    prices = {}
    for number, price in rows:
        if (type(number) is not int or not 1 <= number <= 17
                or type(price) not in (int, float)
                or not math.isfinite(price) or price <= 1
                or number in prices):
            raise ValueError("HOLD_DUPLICATED_OR_INVALID_WIN_QUOTE")
        prices[number] = float(price)
    if set(prices) != set(range(1, 18)):
        raise ValueError("HOLD_MISSING_FULL_17_HORSE_WIN_VECTOR")
    return prices


def _pair_key(numbers):
    if not isinstance(numbers, list) or len(numbers) != 2:
        raise ValueError("HOLD_PAIR_ID_INVALID")
    a, b = numbers
    if type(a) is not int or type(b) is not int or a == b or not (
            1 <= a <= 17 and 1 <= b <= 17):
        raise ValueError("HOLD_PAIR_ID_DUPLICATE_OR_INVALID")
    return (min(a, b), max(a, b))


def _validate_pair_quotes(rows):
    pairs = {}
    for numbers, price in rows:
        key = _pair_key(numbers)
        if (type(price) not in (int, float) or price <= 1
                or not math.isfinite(price) or key in pairs):
            raise ValueError("HOLD_DUPLICATED_OR_INVALID_WIDE_PAIR")
        pairs[key] = float(price)
    expected = set(combinations(range(1, 18), 2))
    if set(pairs) != expected:
        raise ValueError("HOLD_INCOMPLETE_136_WIDE_PAIR_QUOTE_GRID")
    return pairs


def load_snapshots(data):
    if set(data) != set(SOURCE):
        raise ValueError("HOLD_MISSING_REQUIRED_ARCHIVED_SNAPSHOTS")
    a, b, c, d = (data[k] for k in ("early", "sat", "morning", "noon"))
    if a.get("target_race_date") != "2026-10-18" or "2026-10-18" not in str(b["event"]):
        raise ValueError("HOLD_WRONG_RACE")
    if c["event"]["race_id"] != "2026-10-18-KYOTO-11" or d["event"]["field_size"] != 17:
        raise ValueError("HOLD_WRONG_EVENT_OR_FIELD_SIZE")
    snapshots = [
        {
            "label": "sat_1437", "provider": "SportsNavi/Yahoo",
            "timestamp_kind": "extraction_started_not_source_quote_update",
            "observed_at": a["observation_started_at_jst"],
            "win": _validate_quote_vector(
                [(q["number"], q["win_odds"]) for q in a["horses"]]),
        },
        {
            "label": "sat_1537", "provider": "SportsNavi/Yahoo",
            "timestamp_kind": "extraction_started_not_source_quote_update",
            "observed_at": b["observation_started_jst"],
            "win": _validate_quote_vector(
                [(q["horse_number"], q["win_odds"]) for q in b["win_prices_all_17"]]),
            "wide": _validate_pair_quotes(
                [(q["horse_numbers"], q["quoted_odds_min"]) for q in b["wide_pair_all_136"]]),
            "wide_timestamp_kind": "unverified_publisher_update_independent_pool",
        },
        {
            "label": "sun_1142", "provider": "JRA official win + separate SportsNavi wide",
            "timestamp_kind": "JRA_first_party_explicit_win_update_only",
            "observed_at": c["first_party_JRA_win"]["publisher_explicit_update_timestamp_jst"],
            "win": _validate_quote_vector(
                [(q["horse_number"], q["official_displayed_win_odds"])
                 for q in c["first_party_JRA_win"]["displayed_official_win_prices_all_17"]]),
            "wide": _validate_pair_quotes(
                [(q["horse_numbers"], q["payout_odds_low"])
                 for q in c["separately_refreshed_SportsNavi"]["wide_odds_all_136"]]),
            "wide_timestamp_kind": "unverified_publisher_update_independent_pool",
        },
        {
            "label": "sun_1218", "provider": "JRA official win + separate SportsNavi wide",
            "timestamp_kind": "JRA_first_party_explicit_win_update_only",
            "observed_at": d["official_jra_win_published_at_jst"],
            "win": _validate_quote_vector(
                [(q["number"], q["win_odds"]) for q in d["official_JRA_win_all17"]]),
            "wide": _validate_pair_quotes(
                [(q["numbers"], q["odds"]) for q in d["wide_all136_grid"]]
            ) if "wide_all136_grid" in d else _validate_pair_quotes(
                [(q["numbers"], q["odds"]) for q in d["wide_all136"]]),
            "wide_timestamp_kind": "unverified_publisher_update_independent_pool",
        },
    ]
    last = None
    for s in snapshots:
        current = datetime.fromisoformat(s["observed_at"])
        if current.utcoffset() is None or current >= POST or (last is not None and current <= last):
            raise ValueError("HOLD_NOT_CHRONOLOGICAL_PRE_RACE_SNAPSHOT")
        last = current
    return snapshots


def share(prices: dict[int, float]) -> dict[int, float]:
    vals = {k: 1.0 / v for k, v in prices.items()}
    total = sum(vals.values())
    return {k: vals[k] / total for k in sorted(vals)}


def effective_count(probabilities):
    return math.exp(-sum(x * math.log(x) for x in probabilities))


def win_snapshot_summary(s):
    q = share(s["win"])
    rank = sorted(q, key=lambda h: (s["win"][h], h))
    return {
        "label": s["label"],
        "provider": s["provider"],
        "timestamp": s["observed_at"],
        "timestamp_kind": s["timestamp_kind"],
        "inverse_win_odds_sum_not_probability": sum(1/o for o in s["win"].values()),
        "effective_number_from_normalized_inverse_odds": effective_count(q.values()),
        "favorite": rank[0],
        "favorite_relative_weight_pct_not_win_probability": q[rank[0]] * 100,
        "market_top5_horse_numbers": rank[:5],
    }


def band_summaries(before, after):
    bins = []
    for low, high, name in BANDS:
        included = [h for h in sorted(before["win"]) if low <= before["win"][h] < high]
        changes = [(after["win"][h]/before["win"][h]-1)*100 for h in included]
        bins.append({
            "prior_odds_band": name,
            "n_horses": len(included),
            "absolute_quote_change_ge_20pct_count":
                sum(abs(c) >= 20 for c in changes),
            "mean_absolute_quote_change_pct":
                mean(abs(c) for c in changes) if changes else None,
            "not_a_predictive_threshold": True,
        })
    return bins


def adjacent_summary(first, second):
    q0, q1 = share(first["win"]), share(second["win"])
    horses = sorted(q0)
    rank0 = sorted(horses, key=lambda h: (first["win"][h], h))
    rank1 = sorted(horses, key=lambda h: (second["win"][h], h))
    percent = {h: (second["win"][h]/first["win"][h]-1)*100 for h in horses}
    common = [math.log(q1[h]/q0[h]) for h in horses]
    centered = [x-mean(common) for x in common]
    changes = [{
        "horse": h,
        "before_quote": first["win"][h],
        "after_quote": second["win"][h],
        "odds_pct_change": percent[h],
        "relative_share_delta_pp": (q1[h]-q0[h])*100,
        "rank_before": rank0.index(h)+1,
        "rank_after": rank1.index(h)+1,
    } for h in horses]
    return {
        "from": first["label"], "to": second["label"],
        "mixed_provider_or_timestamp_semantics":
            first["provider"] != second["provider"],
        "timepoints_not_transaction_timestamps": True,
        "relative_share_total_variation_pp":
            50 * sum(abs(q1[h]-q0[h]) for h in horses),
        "changed_horse_ordinal_positions_with_fixed_tie_break":
            sum(rank0.index(h) != rank1.index(h) for h in horses),
        "different_20pct_or_more_quote_horses":
            sum(abs(percent[h]) >= 20 for h in horses),
        "idiosyncratic_centered_log_quote_movement_sd":
            pstdev(centered),
        "market_top5_membership_unchanged":
            set(rank0[:5]) == set(rank1[:5]),
        "prior_quote_bands": band_summaries(first, second),
        "largest_absolute_relative_share_movements": sorted(
            changes, key=lambda z: -abs(z["relative_share_delta_pp"]))[:5],
    }


def pl_pair_top3_index(win):
    """PL probability of BOTH horses Top-3 divided by 3.

    There are exactly three successful pairs for every unordered Top-3
    outcome, so the 136 normalized model pair weights sum to exactly one.
    """
    ids = sorted(win)
    w = {h: 1/win[h] for h in ids}
    total = sum(w.values())
    output = {}
    for a, b in combinations(ids, 2):
        prob = 0.0
        for c in ids:
            if c in (a, b):
                continue
            for i, j, k in permutations((a, b, c)):
                prob += ((w[i]/total) *
                         (w[j]/(total-w[i])) *
                         (w[k]/(total-w[i]-w[j])))
        output[(a, b)] = prob/3
    if not math.isclose(sum(output.values()), 1, abs_tol=1e-11):
        raise ValueError("HOLD_PL_PAIR_DISTRIBUTION_NOT_NORMALIZED")
    return output


def wide_snapshot_summary(s):
    if "wide" not in s:
        raise ValueError("HOLD_NO_PAIR_POOL")
    qwin = share(s["win"])
    raw = {k: 1/v for k, v in s["wide"].items()}
    mass = sum(raw.values())
    pair_index = {k: v/mass for k, v in raw.items()}
    pl_index = pl_pair_top3_index(s["win"])
    top_wide = sorted(s["wide"], key=lambda k: (s["wide"][k], k))
    keypairs = ((8, 14), (3, 8), (8, 13), (8, 9))
    details = {}
    for pair in keypairs:
        odds = s["wide"][pair]
        details[f"{pair[0]}-{pair[1]}"] = {
            "wide_lower_quote": odds,
            "wide_quote_relative_inverse_weight_not_event_probability": pair_index[pair],
            "win_PL_both_top3_model_probability": pl_index[pair]*3,
            "log_wide_relative_weight_over_normalized_win_PL_pair_index":
                math.log(pair_index[pair]/pl_index[pair]),
            "wide_rank_among_136_lower_quote": top_wide.index(pair)+1,
        }
    return {
        "time": s["label"],
        "pair_count": len(s["wide"]),
        "wide_quote_timestamp_kind": s["wide_timestamp_kind"],
        "pair_weight_normalization_only_not_joint_probability": True,
        "wide_events_not_mutually_exclusive": True,
        "highlighted_pairs": details,
    }


def cross_pool_signs(snaps):
    early, late = snaps[1], snaps[3]
    refpair = (8, 14)
    controlpair = (3, 8)
    win14 = (late["win"][14]/early["win"][14]-1)*100
    wide14 = (late["wide"][refpair]/early["wide"][refpair]-1)*100
    rel_early = ((1/early["wide"][refpair]) /
                 (1/early["wide"][controlpair]))
    rel_late = ((1/late["wide"][refpair]) /
                (1/late["wide"][controlpair]))
    wp = wide_snapshot_summary(early)["highlighted_pairs"]
    wq = wide_snapshot_summary(late)["highlighted_pairs"]
    residual_change = (
        wq["8-14"]["log_wide_relative_weight_over_normalized_win_PL_pair_index"]
        -wp["8-14"]["log_wide_relative_weight_over_normalized_win_PL_pair_index"])
    return {
        "comparison": "sat_1537_to_sun_1218_distinct_win_and_wide_sources",
        "horse_14_win_quote_change_pct": win14,
        "wide_8_14_lower_quote_change_pct": wide14,
        "horse_14_stronger_in_win_but_pair_8_14_weaker_in_wide":
            (win14 < 0 and wide14 > 0),
        "pair_8_14_relative_weight_over_3_8_before": rel_early,
        "pair_8_14_relative_weight_over_3_8_after": rel_late,
        "relative_wide_pair_ranking_reversal": rel_early > 1 and rel_late < 1,
        "8_14_cross_pool_log_residual_change_vs_PL_reference": residual_change,
        "normalization_and_event_family_differ_warning":
            "Inverse lower wide quote normalized over 136 overlapping events is only a price-weight index. It is not an event likelihood.",
        "no_proof_of_timestamp_lags":
            "Win and wide pools have unknown atomically matched producer update times.",
        "no_proof_of_bettor_information_causality": True,
    }


def _unitize(values):
    s = sum(values)
    if s <= 0 or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("invalid_voter_weights")
    return [v/s for v in values]


def synthetic_bettor_abm(q0, *, repeats=100, seed=20261023,
                         steps=32, bets_per_step=80,
                         prior_votes=1500, gamma=1.25):
    """Synthetic dynamic pari-mutuel-like vote-share mechanism.

    These are VOTER agents, not racing-horse motion. The arbitrary
    'signal' is a fixed tilt of INITIAL MARKET RANKS 5 and 8, NOT derived
    from actual later market quotes or race results.
    """
    q = list(q0)
    if (len(q) < 9 or min(q) <= 0 or not math.isclose(sum(q), 1, abs_tol=1e-8)
            or repeats < 2 or steps < 4 or bets_per_step < 1
            or prior_votes < 1 or gamma <= 0):
        raise ValueError("INVALID_SYNTHETIC_MARKET_ABM_SETUP")
    order = sorted(range(len(q)), key=lambda i: -q[i])
    fav, fifth, eighth = order[0], order[4], order[7]
    private_signal = q[:]
    private_signal[fav] *= 0.80
    private_signal[fifth] *= 1.8
    private_signal[eighth] *= 1.5
    private_signal = _unitize(private_signal)
    result = {}
    scenarios = {
        "herding_only": lambda t: 0.0,
        "information_only": lambda t: 1.0,
        "hierarchical_early_herding_late_information":
            lambda t: 0.10 if t < steps//2 else 0.75,
    }
    for mode, info_share in scenarios.items():
        terminal, favorite, fifth_horse = [], [], []
        for rep in range(repeats):
            rng = random.Random(seed + 103*rep)
            cumulative = [x*prior_votes for x in q]
            for t in range(steps):
                before = _unitize(cumulative)
                imitation = _unitize([x**gamma for x in before])
                a = info_share(t)
                choices = _unitize([
                    (1-a)*imitation[i] + a*private_signal[i]
                    for i in range(len(q))
                ])
                for chosen in rng.choices(range(len(q)), weights=choices,
                                          k=bets_per_step):
                    cumulative[chosen] += 1
            end = _unitize(cumulative)
            terminal.append(50*sum(abs(end[i]-q[i]) for i in range(len(q))))
            favorite.append(end[fav])
            fifth_horse.append(end[fifth])
        result[mode] = {
            "independent_synthetic_paths": repeats,
            "mean_relative_share_turnover_pp": mean(terminal),
            "mean_favorite_relative_weight_pct": 100*mean(favorite),
            "mean_initial_fifth_rank_runner_relative_weight_pct":
                100*mean(fifth_horse),
        }
    return {
        "status": "SYNTHETIC_BETTOR_BEHAVIOR_MODEL_NOT_ESTIMATED_FROM_MARKET_OR_OUTCOMES",
        "initial_share_from_archived_win_quote": True,
        "simulated_random_bettor_paths_not_actual_races": repeats,
        "steps": steps, "bets_per_step": bets_per_step,
        "prior_votes_arbitrary": prior_votes,
        "herding_exponent_gamma_arbitrary": gamma,
        "private_signal": "synthetic rank-5 and rank-8 tilts, rank-1 weakening; no actual observations or win result",
        "arbitrary_signal_rank5": fifth+1,
        "results": result,
        "causal_identification": "HOLD: odds trajectories alone cannot separately identify herding, heterogeneous private signals and mechanical accumulation.",
    }


def audit(root=ROOT, *, paths=100, seed=20261023):
    raw = read_locked(root)
    snaps = load_snapshots(raw)
    snapshot_overview = [win_snapshot_summary(s) for s in snaps]
    intervals = [adjacent_summary(snaps[i], snaps[i+1])
                 for i in range(len(snaps)-1)]
    wide = [wide_snapshot_summary(s) for s in snaps[1:]]
    q_initial = share(snaps[0]["win"])
    abm = synthetic_bettor_abm(
        list(q_initial.values()), repeats=paths, seed=seed)
    return {
        "status": STATUS,
        "race": "2026-10-18 Kyoto 11R Shuka Sho",
        "early_quote_is_not_opening_odds": True,
        "snapshot_count": len(snaps),
        "source_git_blob_shas": {
            k: sha for k, (_, sha) in SOURCE.items()},
        "snapshots": snapshot_overview,
        "transitions": intervals,
        "wide_market_windows": wide,
        "cross_pool_non_synchrony": cross_pool_signs(snaps),
        "voter_ABM": abm,
        "hypotheses": {
            "H0_market_path_independent_conditional_on_final_odds":
                "Requires independent multiple actual races and time-aligned final/pre-race information; cannot test with this sample.",
            "H1_initial_popularity_feedback":
                "Later odds partly depend on previously shown odds (herding/anchoring), as distinct from new private information and deterministic cumulative pool accounting.",
            "H2_rank_dependent_threshold":
                "At a prespecified earlier-odds or market-concentration threshold, a later odds path adds forecast skill; HOLD with one race and no prospective split.",
            "H3_cross_pool_non_synchrony":
                "Win and wide pair relative price movements diverge even after adjusting for win-only joint-top3 PL benchmark; descriptive, clocks unaligned.",
            "H4_temporal_information_hierarchy":
                "Fast price feedback plus slow public signals and late private information can have different effects; requires micro-timestamped panel.",
        },
        "inference_gates": {
            "initial_odds_anchor_causal_effect": "HOLD_CONFOUNDING_MARKET_FEEDBACK_VS_NEW_INFORMATION",
            "forecast_skill_threshold": "HOLD_NO_INDEPENDENT_RACE_LEVEL_PROSPECTIVE_HOLDOUT",
            "within_bettor_update_timing": "HOLD_NO_TRANSACTION_TIMESTAMPS",
            "cross_pool_atomically_aligned": False,
            "backtest_outcomes_used_in_model_fitting": False,
            "old_v31_thresholds_modified": False,
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paths", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261023)
    ap.add_argument("--output", type=Path,
                    default=Path("tmp/shuka-odds-information-hierarchy.json"))
    args = ap.parse_args()
    obj = audit(paths=args.paths, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "status": obj["status"],
        "transitions": [{
            "from": t["from"], "to": t["to"],
            "turnover_pp": t["relative_share_total_variation_pp"],
            "changed_horses_over_20pct": t["different_20pct_or_more_quote_horses"],
        } for t in obj["transitions"]],
        "pair_8_14_divergence": obj["cross_pool_non_synchrony"]
        ["horse_14_stronger_in_win_but_pair_8_14_weaker_in_wide"],
        "forecast_threshold": obj["inference_gates"]["forecast_skill_threshold"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
