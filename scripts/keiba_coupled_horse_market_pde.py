#!/usr/bin/env python3
"""Coupled *synthetic* horse, voter, market, threshold and PDE mechanism.

Causal/as-of contract:
  EARLIEST SAVED WIN QUOTES (not opening odds)
       -> hypothetical horse ensembles (PR #9 first-passage plus SDE)
       -> bettors' synthetic pre-race signals -> cumulative vote dynamics
       -> market indices q(t) -> PR #13 M0/M1/M2/M3 coherent rankings.
  Independent official results enter only AFTER all forecasts exist.

The PDE is the uncrowded Brownian-position-residual closure of the SDE
horse component; it is NOT a nonlinear crowded-horse closure. No real
horse traits, actual bettor tickets/stakes, or positive ROI are fitted.
PR #10's presealed Kikka SHA and v3.1 holdout remain untouched.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from itertools import combinations

import numpy as np

from betting_abm_pde_sensitivity import scenario as legacy_horse_scenario
from betting_abm_pde_particle_bridge import compare_particle_density
from odds_coherent_hierarchy_rank_bridge import joint_rank_probability
from odds_threshold_regime_bridge import (
    ROOT, aware, market_features, forecast_prestart, exact_win_top3,
    load_source_locked_panels, score_forecast, normalize,
)

STATUS = "SYNTHETIC_COUPLED_ABM_PDE_AND_REAL_ODDS_ARCHIVE_NOT_CALIBRATED"
DIFFUSION_M2_PER_S = 0.25
INITIAL_POSITION_SD_M = 2.0
CROWD_PENALTY_MPS = 0.08
BETA_SIGNAL_BLEND = 0.5
MC_PRIOR_WEIGHT = 2.0  # early-market PL pseudo-sample; stops finite-MC zero log loss
MIXED_MODES = ("independent", "herding", "information", "mixed", "threshold_mixed")
REPORT_MODELS = ("observed_M0", "observed_M1", "observed_M2", "observed_M3",
                 "horse_P9_weak", "horse_SDE_no_pack", "horse_SDE_weak",
                 "market_independent", "market_herding",
                 "market_information", "market_mixed", "market_threshold_mixed")
SOURCE_MODELS = ("M0_latest", "M1_smooth", "M2_initial10",
                 "M3_initial10_speed010")


def vector(q):
    arr = np.asarray(q, dtype=float)
    if (arr.ndim != 1 or len(arr) < 5 or not np.all(np.isfinite(arr))
            or np.any(arr <= 0)):
        raise ValueError("HOLD_BAD_DISTRIBUTION")
    return arr / arr.sum()


def _rank(arrival):
    orders = np.argsort(arrival, axis=1)
    n = arrival.shape[1]
    return {"win": np.bincount(orders[:, 0], minlength=n) / len(orders),
            "top3": np.bincount(orders[:, :3].ravel(), minlength=n) / len(orders)}


def _finish_times(latent, pace, initial_x, noise, *,
                  distance_m, dt_s, crowd_mps):
    """Numerical first-passage SDE. Shared random inputs for paired scenarios.

    dX = (16.8 + .10*a + phase_pace - crowd)dt + sqrt(2D) dW.
    With crowd=0, R=X-v*t (and with the deterministic phase removed) is
    independent Brownian motion, as used by the companion PDE diagnostic.
    """
    if distance_m < 800 or dt_s <= 0 or crowd_mps < 0:
        raise ValueError("HOLD_BAD_PHYSICAL_PARAMETERS")
    n_steps, draws, n = noise.shape
    pos = initial_x.copy()
    arrival = np.full((draws, n), np.inf)
    nominal_s = distance_m / 16.8
    for s in range(n_steps):
        active = ~np.isfinite(arrival)
        if not np.any(active):
            break
        penalty = np.zeros_like(pos)
        if crowd_mps:
            order = np.argsort(np.where(active, pos, np.inf), axis=1,
                               kind="stable")
            sorted_pos = np.take_along_axis(np.where(active, pos, np.inf),
                                           order, axis=1)
            with np.errstate(invalid="ignore"):
                gap = sorted_pos[:, 1:] - sorted_pos[:, :-1]
            near = np.isfinite(gap) & (gap > 0) & (gap < 6)
            sorted_penalty = np.zeros_like(pos)
            sorted_penalty[:, :-1] = (crowd_mps *
                np.exp(-np.where(near, gap, 0.0) / 6) * near)
            np.put_along_axis(penalty, order, sorted_penalty, axis=1)
        phase = (s + 0.5) * dt_s / nominal_s
        speed = 16.8 + .10 * latent + pace * math.cos(2*math.pi*phase) - penalty
        if np.any(speed[active] <= 0):
            raise ValueError("HOLD_NONPOSITIVE_SIMULATED_SPEED")
        new_pos = pos + speed * dt_s + noise[s]
        hit = active & (new_pos >= distance_m)
        step_move = new_pos[hit] - pos[hit]
        arrival[hit] = s*dt_s + dt_s*(distance_m-pos[hit])/step_move
        pos[active] = new_pos[active]
    if not np.all(np.isfinite(arrival)):
        raise ValueError("HOLD_UNFINISHED_AGENTS")
    return arrival


def brownian_horse_ensemble(q0, distance_m, *, draws=400, seed=20261025,
                            diffusion=DIFFUSION_M2_PER_S, dt_s=2.0):
    """Alternative physically PDE-compatible horse motion model."""
    q0 = vector(q0)
    if draws < 40 or not (0 <= diffusion <= 10):
        raise ValueError("HOLD_BAD_BROWNIAN_ENSEMBLE")
    rng = np.random.default_rng(seed)
    n = len(q0)
    latent = np.log(q0)[None, :] + rng.gumbel(size=(draws, n))
    pace = rng.normal(0, .32, size=(draws, n))
    initial_x = rng.normal(0, INITIAL_POSITION_SD_M, size=(draws, n))
    n_steps = int(math.ceil(distance_m/(15*dt_s))) + 35
    noise = math.sqrt(2*diffusion*dt_s) * rng.standard_normal(
        (n_steps, draws, n))
    no_pack = _rank(_finish_times(latent, pace, initial_x, noise,
                                  distance_m=distance_m, dt_s=dt_s,
                                  crowd_mps=0.0))
    weak = _rank(_finish_times(latent, pace, initial_x, noise,
                               distance_m=distance_m, dt_s=dt_s,
                               crowd_mps=CROWD_PENALTY_MPS))
    for pred in (no_pack, weak):
        if not np.isclose(sum(pred["win"]), 1, atol=1e-9):
            raise ValueError("HOLD_SDE_WIN_MASS")
        if not np.isclose(sum(pred["top3"]), 3, atol=1e-9):
            raise ValueError("HOLD_SDE_TOP3_MASS")
    return {"no_pack": no_pack, "weak": weak,
            "physics": {"diffusion_m2_per_s": diffusion,
                        "initial_sd_m": INITIAL_POSITION_SD_M,
                        "crowd_weak_mps": CROWD_PENALTY_MPS,
                        "dt_s": dt_s, "draws": draws}}


def vote_market(q0, signal, *, mode, duration_hours, seed=20261025,
                steps=4, synthetic_prior_stakes=3000,
                synthetic_votes_per_step=250):
    """Independent categorical bettors with shared-uniform paired tally draws.

    Prices are normalized *proxy vote shares*, not recovered JRA pool stakes.
    Threshold mixing is a fixed, hypothetical endogenous response rule.
    """
    if mode not in MIXED_MODES or duration_hours <= 0 or steps < 2:
        raise ValueError("HOLD_INVALID_MARKET_MODE_OR_TIME")
    if synthetic_prior_stakes <= 0 or synthetic_votes_per_step < 0:
        raise ValueError("HOLD_BAD_SYNTHETIC_STAKES")
    q0 = vector(q0)
    signal = vector(signal)
    if len(q0) != len(signal):
        raise ValueError("HOLD_MARKET_HORSE_MISMATCH")
    rng = np.random.default_rng(seed)
    pool = q0 * synthetic_prior_stakes
    path = [q0.copy()]
    active_steps = 0
    for step in range(1, steps+1):
        current = vector(pool)
        elapsed_h = duration_hours * (step-1)/steps
        change_rate = (np.max(np.abs(np.log(current/q0))) / elapsed_h
                       if elapsed_h > 0 else 0.0)
        if mode == "independent":
            weights = q0
        elif mode == "herding":
            weights = current**1.25
        elif mode == "information":
            weights = signal
        else:
            herd_power = 0.75
            if mode == "threshold_mixed" and change_rate >= .10:
                herd_power = 1.50
                active_steps += 1
            weights = current**herd_power * signal**0.75
        # Inverse-CDF categorical choices using the SAME per-bettor
        # uniforms across counterfactual modes (when initialized with the
        # same seed). This isolates mechanism changes from voter MC noise.
        uniforms = rng.random(synthetic_votes_per_step)
        allocations = np.searchsorted(np.cumsum(vector(weights)),
                                      uniforms, side="right")
        votes = np.bincount(allocations, minlength=len(q0))
        pool = pool + votes
        path.append(vector(pool))
    end = path[-1]
    if not all(np.isclose(p.sum(), 1.0, atol=1e-12) for p in path):
        raise ValueError("HOLD_MARKET_SHARE_NOT_NORMALIZED")
    if not np.isclose(pool.sum(),
                      synthetic_prior_stakes + steps*synthetic_votes_per_step,
                      atol=1e-8):
        raise ValueError("HOLD_CUMULATIVE_POOL_ACCOUNTING_FAILED")
    return {"path": path, "final": end, "triggered_steps": active_steps,
            "initial_stakes_assumption": synthetic_prior_stakes,
            "new_vote_count_assumption": steps*synthetic_votes_per_step}


def _sde_prediction(raw):
    return {"win": [float(x) for x in raw["win"]],
            "top3": [float(x) for x in raw["top3"]]}


def _synthetic_odds_row(row, ids, q_latest):
    # 1/q is an exactly reversible *price proxy*, NOT a JRA payout quote.
    return {**row, "first_odds": {
                    i: float(1/q) for i, q in zip(ids, vector(
                        [1/row["first_odds"][i] for i in ids]))},
            "last_odds": {i: float(1/q) for i, q in zip(ids, q_latest)}}


def couple_prestart(row, *, distance_m, draws=400, seed=20261025,
                    votes_per_step=250, horse_prior=None):
    """The outcome never enters; late odds only enter an *audit sidecar*.

    Both physical ABMs are initialized from EARLY source quotes. Future
    sampled horse finish labels and archived later quotes are never used
    to generate bettor paths. They are not independent observed abilities.
    """
    features = market_features(row)
    ids = features["horse_numbers"]
    q0 = vector(features["early"])
    # When an independently recorded, past-only horse prior is provided,
    # initialize BOTH horse ensembles from it, but leave voter pool q0
    # at the actual archived early market. No realized finish is passed.
    # Caller is responsible for externally verifying the prior's as-of time.
    external_horse_prior = horse_prior is not None
    prior = vector(horse_prior) if external_horse_prior else q0
    if len(prior) != len(ids):
        raise ValueError("HOLD_INDEPENDENT_HORSE_PRIOR_ROSTER_MISMATCH")
    early_odds = ([float(1/x) for x in prior] if external_horse_prior
                  else [row["first_odds"][i] for i in ids])
    # Existing PR #9 agent model, imported unchanged.
    legacy = legacy_horse_scenario(
        early_odds, float(distance_m), draws=draws, seed=seed)
    legacy_prediction = {
        "win": [h["weak_win_pct"]/100 for h in legacy["horses"]],
        "top3": [h["weak_top3_pct"]/100 for h in legacy["horses"]]}
    sde = brownian_horse_ensemble(
        prior, distance_m, draws=draws, seed=seed + 1)
    # With only a few hundred MC runs a horse may have zero simulated wins.
    # Smooth with a *prestart-only*, fixed 2-draw equivalent PL prior.
    # Otherwise log loss is undefined for an unseen winning horse.
    pl_prior = exact_win_top3([float(v) for v in q0])
    def smooth_mc(raw):
        return {
            kind: [float((draws*float(v) + MC_PRIOR_WEIGHT*prior)
                         / (draws+MC_PRIOR_WEIGHT))
                   for v, prior in zip(raw[kind], pl_prior[kind])]
            for kind in ("win", "top3")}
    legacy_prediction = smooth_mc(legacy_prediction)
    no_pack_prediction = smooth_mc(_sde_prediction(sde["no_pack"]))
    weak_prediction = smooth_mc(_sde_prediction(sde["weak"]))
    # This is only a hypothetical prestart signal; it is NOT a learned
    # independent covariate. It enters ONCE, in bettors' information.
    signal = vector(BETA_SIGNAL_BLEND * np.asarray(legacy_prediction["win"])
                    + (1-BETA_SIGNAL_BLEND)*np.asarray(no_pack_prediction["win"]))
    predictions = {"horse_P9_weak": legacy_prediction,
                   "horse_SDE_no_pack": no_pack_prediction,
                   "horse_SDE_weak": weak_prediction}
    market = {}
    for mode in MIXED_MODES:
        out = vote_market(q0, signal, mode=mode,
                          duration_hours=features["hours"], seed=seed+300,
                          synthetic_votes_per_step=votes_per_step)
        market[mode] = out
        synthetic_row = _synthetic_odds_row(row, ids, out["final"])
        rankings = forecast_prestart(synthetic_row)["predictions"]
        predictions["market_"+mode] = rankings["M0_latest"]
        # Same synthetic price path also produces coherent M0-M3.
        # M1-M3 are auxiliary diagnostics, not repeated horse evidence.
        market[mode]["M0_to_M3"] = rankings
        # One ordered-finish distribution supplies ALL ticket-event types.
        # No independent, potentially incoherent pair/trio logits are used.
        joint = joint_rank_probability(
            synthetic_row["last_odds"], {i: 0.0 for i in ids},
            {p: 0.0 for p in combinations(ids, 2)})
        for j, horse in enumerate(ids):
            if not math.isclose(joint["win"][horse], rankings["M0_latest"]["win"][j],
                                abs_tol=1e-10):
                raise ValueError("HOLD_WIN_MARKET_AND_CROSSPOOL_NOT_COHERENT")
            if not math.isclose(joint["top3"][horse], rankings["M0_latest"]["top3"][j],
                                abs_tol=1e-10):
                raise ValueError("HOLD_TOP3_MARKET_AND_CROSSPOOL_NOT_COHERENT")
        market[mode]["joint_all_ticket_events"] = joint
        market[mode]["TV_to_archived_later_quote_pp"] = float(
            50*np.sum(np.abs(out["final"]-features["latest"])))
    actual = forecast_prestart(row)["predictions"]
    for n, source_key in zip(REPORT_MODELS[:4], SOURCE_MODELS):
        predictions[n] = actual[source_key]
    for pred in predictions.values():
        if not np.isclose(sum(pred["win"]), 1, atol=1e-8):
            raise ValueError("HOLD_COUPLED_WIN_MASS")
        if not np.isclose(sum(pred["top3"]), 3, atol=1e-8):
            raise ValueError("HOLD_COUPLED_TOP3_MASS")
    return {"predictions": predictions, "market_paths": market,
            "horse_signal": signal, "sde_physics": sde["physics"],
            "horse_pr9_status": legacy["status"],
            "horse_entries": len(ids),
            "initial_market_q": q0,
            "horse_physical_initial_prior": prior,
            "horse_prior_source": ("external_past_history_needs_source_clock"
                                   if external_horse_prior else
                                   "same_early_market_quote_proxy"),
            "diagnostic_only_later_market_q": np.asarray(features["latest"]),
            "event_probability_no_double_count": True,
            "not_an_independent_horse_ability_estimate": True}


def _source_distances(root):
    """Race distances come from source-locked PRESTART card metadata."""
    from odds_real_multirace_archive_audit import SOURCE_SHA, read_file
    distances = {}
    for num, (first, _) in SOURCE_SHA.items():
        original = read_file(root, first)
        distances[original["race_id"]] = original["distance_m"]
    distances["2608040711"] = 2000  # 秋華賞京都芝2000m (race-card metadata)
    return distances


def audit(root=ROOT, *, prestart_only=False, draws=250, seed=20261025):
    """One joint real-archive audit; official outcomes are held separately."""
    rows = load_source_locked_panels(root)
    distances = _source_distances(root)
    if len(rows) != 6 or set(distances) != {r["race_id"] for r in rows}:
        raise ValueError("HOLD_INCOMPLETE_SIX_RACE_JOINT_UNIVERSE")
    prepared = []
    for i, row in enumerate(rows):
        ready = couple_prestart(row, distance_m=distances[row["race_id"]],
                                draws=draws, seed=seed+i*1000)
        prepared.append((row, ready))
    # Same D and initial residual spread as horse SDE, but this diagnostic
    # is only its uncrowded independent Brownian residual projection.
    pde = compare_particle_density(
        particles=5000, seed=seed+999, dx=.5, dt=.04, duration=8.,
        drift=0., diffusion=DIFFUSION_M2_PER_S,
        initial_sd=INITIAL_POSITION_SD_M, half_width=50.)
    if not (abs(pde["pde_mass"]-1)<1e-9 and
            pde["kolmogorov_cdf_error"] < .06):
        raise ValueError("HOLD_SDE_PDE_INDEPENDENT_RESIDUAL_MISMATCH")
    out = {
        "status": STATUS,
        "cohort": {"races": len(rows), "meeting_dates": 2,
                   "horse_race_entries": sum(x["horse_entries"] for _, x in prepared),
                   "source_first_quotes_are_not_opening_odds": True},
        "horse_abm": {"actual_JRA_GPS_or_horse_parameters_fit": False,
                      "early_odds_proxy_used_for_latent_baseline": True,
                      "legacy_P9_reused_unmodified": True,
                      "synthetic_signal_mixture_from_two_ABMs": BETA_SIGNAL_BLEND,
                      "MC_prestart_PL_pseudocount_weight": MC_PRIOR_WEIGHT,
                      "real_horse_crowding_causal_effect_identified": False},
        "market_abm": {
            "synthetic_stakes_not_observed_actual_JRA_votes": True,
            "no_real_bettor_herding_identified": True,
            "mode_names": list(MIXED_MODES),
            "mean_TV_to_actual_later_quote_pp": {
                mode: mean(res["market_paths"][mode][
                    "TV_to_archived_later_quote_pp"] for _, res in prepared)
                for mode in MIXED_MODES},
            "threshold_triggered_steps_sum": sum(
                res["market_paths"]["threshold_mixed"]["triggered_steps"]
                for _, res in prepared)},
        "physics_SDE_to_PDE": {
            "shared_initial_sd_m": INITIAL_POSITION_SD_M,
            "shared_independent_diffusion_m2_per_s": DIFFUSION_M2_PER_S,
            "uncrowded_Brownian_residual_only_not_nonlinear_crowd_PDE": True,
            "pde_mass": pde["pde_mass"],
            "max_CDF_gap": pde["kolmogorov_cdf_error"],
            "out_of_domain_particles": pde["out_of_domain_particles"]},
        "rank_probability_masses_verified": True,
        "all_ticket_markets": {
            "sourced_from_same_ordered_finish_distribution": True,
            "win_mass": 1, "top2_inclusion_mass": 2, "top3_inclusion_mass": 3,
            "WIDE_both_Top3_mass": 3, "unordered_trio_mass": 1,
            "ordered_exacta_mass": 1, "ordered_trifecta_mass": 1,
            "actual_JRA_crosspool_quotes_used_for_fitting": False},
        "real_calibrated_forecast_advantage": "HOLD",
        "odds_threshold_phase_transition_claim": "HOLD",
        "wager_positive_expected_profit": "HOLD",
        "PR10_sha_and_v31_unchanged": True,
    }
    if prestart_only:
        out["status"] = "PRESTART_ONLY_SIMULATED_COUPLING_NO_JRA_OUTCOMES_LOADED"
        out["postrace"] = "NOT_COMPUTED"
        return out

    # SEALED FIREWALL: all historical forecasting distributions exist above.
    from odds_six_race_predictive_increment import (
        verify_official_oct12, verify_official_shuka)
    oct12, verified_at = verify_official_oct12(root)
    shuka = verify_official_shuka(root)
    date_rows = {}
    for row, res in prepared:
        if row["meeting_day"] == "2026-10-12":
            if verified_at <= aware(row["post_at"]):
                raise ValueError("HOLD_OUTCOME_BEFORE_POST")
            top3 = oct12["races"][str(row["race_no"])]["positions"]
        else:
            if shuka["verified_on_jst"] <= row["meeting_day"]:
                raise ValueError("HOLD_SHUKA_RESULT_BEFORE_POST")
            top3 = shuka["top3"]
        f = market_features(row)
        scores = {name: score_forecast(f, pred, top3)
                  for name, pred in res["predictions"].items()}
        trio = tuple(sorted(top3))
        actual_pairs = set(combinations(sorted(top3), 2))
        ticket_metrics = {}
        for mode in MIXED_MODES:
            joint = res["market_paths"][mode]["joint_all_ticket_events"]
            p_trio = joint["unordered_top3_trio"][trio]
            ticket_metrics[mode] = {
                "unordered_trio_log_loss": -math.log(p_trio),
                "WIDE_pair_Brier_mean_pairs": mean(
                    (p-int(edge in actual_pairs))**2
                    for edge,p in joint["both_top3_pair"].items())}
        # Observed market M0 uses the identical crosspool probability law,
        # but *not* real WIDE quotes. Actual JRA outcomes are used only here.
        ids = f["horse_numbers"]
        actual_late = {i: float(1/q) for i, q
                       in zip(ids, f["latest"])}
        actual_joint = joint_rank_probability(
            actual_late, {i:0.0 for i in ids},
            {p:0.0 for p in combinations(ids,2)})
        ticket_metrics["observed_M0"] = {
            "unordered_trio_log_loss": -math.log(
                actual_joint["unordered_top3_trio"][trio]),
            "WIDE_pair_Brier_mean_pairs": mean(
                (p-int(edge in actual_pairs))**2
                for edge,p in actual_joint["both_top3_pair"].items())}
        date_rows[row["race_id"]] = {
            "date": row["meeting_day"], "scores": scores,
            "ticket_scores": ticket_metrics}
    out["postrace"] = {
        "status": "RETROSPECTIVE_SIX_REAL_OUTCOMES_ONLY_NOT_PROSPECTIVE",
        "mean_race_equal_winner_log_loss": {
            name: mean(x["scores"][name]["win_log_loss"]
                       for x in date_rows.values()) for name in REPORT_MODELS},
        "mean_race_equal_Top3_brier": {
            name: mean(x["scores"][name]["top3_brier"]
                       for x in date_rows.values()) for name in REPORT_MODELS},
        "mean_date_equal_winner_logloss_delta_vs_observed_M0": {
            name: mean(mean(x["scores"][name]["win_log_loss"]-
                                x["scores"]["observed_M0"]["win_log_loss"]
                                for x in date_rows.values() if x["date"]==d)
                       for d in sorted({x["date"] for x in date_rows.values()}))
            for name in REPORT_MODELS if name != "observed_M0"},
        "mean_coherent_ticket_scores_race_equal": {
            name: {metric: mean(
                x["ticket_scores"][name][metric] for x in date_rows.values())
                for metric in ("unordered_trio_log_loss", "WIDE_pair_Brier_mean_pairs")}
            for name in ("observed_M0", *MIXED_MODES)},
        "WIDE_pairs_overlap_and_are_not_independent_races": True,
        "horses_and_pairs_not_independent_races": True,
        "no_parameter_tuning_to_any_of_six_actual_winners": True,
    }
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prestart-only", action="store_true")
    parser.add_argument("--draws", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--output", type=Path,
                        default=Path("tmp/coupled-horse-market-pde.json"))
    args = parser.parse_args()
    report = audit(prestart_only=args.prestart_only, draws=args.draws,
                   seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)
                           + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "races": report["cohort"]["races"],
                      "has_JRA_postrace_scores": not args.prestart_only,
                      "PDE_CDF_gap": report["physics_SDE_to_PDE"]["max_CDF_gap"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
