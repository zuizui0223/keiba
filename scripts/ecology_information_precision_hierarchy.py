#!/usr/bin/env python3
"""Biological vs market information precision: analytic hypothesis and evidence gate.

Actual observations are obtained ONLY from previously committed aggregate
evidence; this script never receives race-level horse IDs, genotypes or odds
series. Analytic Gaussian precision values are ILLUSTRATIVE, NOT fitted race
effect sizes, heritability, p values, probability of winning or profit.

Hypothesis: family-proxy information should have greater marginal predictive
value when a focal individual's own historical information is sparse or
outdated, if both signals are valid and conditionally informative.
Reject the false equivalence "kinship A/G = phenotype correlation" and
"relative performance prediction = additive genetic effect".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


INPUTS = {
    "integrated": "docs/evidence/integrated-ecology-kinship-genome-market-20261118.json",
    "factorial": "docs/evidence/japan-2026-own-kin-factorial-empirical-20261117.json",
    "strict": "docs/evidence/japan-2022-2024-joint-strict-strong-20261116.json",
    "market": "docs/evidence/market-9-race-empirical-structure-20261115.json",
}
MODEL_PARAMS = {
    # These are intentionally fictional dimensionless Gaussian assumptions.
    "prior_latent_variance": 1.0,
    "individual_measurement_noise_variance_per_observation": 1.5,
    "family_proxy_measurement_noise_variance_per_record": 1.0,
    "family_signal_loading_not_genetic_relatedness": 0.4,
    "family_information_age_decay_scale_days": 365.0,
    "family_proxy_observation_count": 4,
}
MODEL_TAG = "ANALYTIC_ONLY_GAUSSIAN_SIGNAL_PRECISION_NOT_ANIMAL_GENETICS"


def _finite_positive(name: str, value: float, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError("HOLD_BOOLEAN_IN_NUMERICAL_MODEL_" + name)
    try:
        x = float(value)
    except (ValueError, TypeError):
        raise ValueError("HOLD_NONNUMERIC_" + name) from None
    if not math.isfinite(x) or x < 0 or (x == 0 and not allow_zero):
        raise ValueError("HOLD_NONPOSITIVE_OR_NONFINITE_" + name)
    return x


def _count(name: str, value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("HOLD_INVALID_INFORMATION_COUNT_" + name)
    return value


def gaussian_information_value(
    *,
    n_own: int,
    n_family: int,
    kin_lag_days: float,
    prior_var: float,
    own_noise_per_observation: float,
    family_noise_per_record: float,
    family_loading: float,
    age_decay_scale_days: float,
) -> dict:
    """Closed-form ideal Gaussian conditional MSE/MI for a toy latent trait.

    O_k = theta + eps_k, eps ~ N(0, own_noise_per_observation).
    F_l = family_loading * theta + xi_l, with independent Gaussian noise
          variance family_noise_per_record * (1 + lag / decay_scale).
    If own observations or proxy observations are absent, omit that channel.
    Such conditional independence and loading are NOT estimates from horses.
    """
    n_own = _count("own", n_own)
    n_family = _count("family", n_family)
    lag = _finite_positive("kin_lag_days", kin_lag_days, allow_zero=True)
    tau2 = _finite_positive("prior_var", prior_var)
    v_o = _finite_positive("own_noise", own_noise_per_observation)
    v_f = _finite_positive("family_noise", family_noise_per_record)
    scale = _finite_positive("age_scale", age_decay_scale_days)
    if isinstance(family_loading, bool):
        raise ValueError("HOLD_BOOLEAN_FAMILY_LOADING")
    beta = float(family_loading)
    if not math.isfinite(beta):
        raise ValueError("HOLD_NONFINITE_FAMILY_LOADING")
    p_prior = 1.0 / tau2
    p_own = n_own / v_o
    effective_family_noise = v_f * (1 + lag / scale)
    p_family = beta * beta * n_family / effective_family_noise
    var_before = 1.0 / (p_prior + p_own)
    var_after = 1.0 / (p_prior + p_own + p_family)
    if not 0 < var_after <= var_before:
        raise ValueError("HOLD_GAUSSIAN_POSTERIOR_ORDER")
    return {
        "own_observation_count": n_own,
        "family_proxy_observation_count": n_family,
        "proxy_age_days": lag,
        "prior_precision": p_prior,
        "own_precision": p_own,
        "family_proxy_precision": p_family,
        "latent_variance_with_own_only": var_before,
        "latent_variance_with_own_plus_family_proxy": var_after,
        "ideal_variance_improvement": var_before - var_after,
        "ideal_conditional_information_nats": 0.5 * math.log(var_before / var_after),
        "no_source_relatedness_A_or_genomic_G_assumed": True,
    }


def conditional_gaussian_family_gain(
    *, prior_var: float, own_error_var: float, family_error_var: float,
    family_loading: float, correlated_measurement_errors: float = 0.0
) -> dict:
    """Exact Gaussian reduction including correlated OWN and FAMILY noise.

    O = theta + e_O; K = beta*theta + e_K; Cov(e_O,e_K)=c.
    The family observation may correlate with own information through
    management, measurement or shared contexts, without demonstrating genes.
    """
    tau2 = _finite_positive("prior", prior_var)
    vo = _finite_positive("own_error", own_error_var)
    vk = _finite_positive("family_error", family_error_var)
    if any(isinstance(x, bool) for x in (family_loading, correlated_measurement_errors)):
        raise ValueError("HOLD_BOOLEAN_GAUSSIAN_COVARIATE")
    beta = float(family_loading)
    c = float(correlated_measurement_errors)
    if not all(math.isfinite(x) for x in (beta, c)):
        raise ValueError("HOLD_NONFINITE_GAUSSIAN_COVARIATE")
    if c * c >= vo * vk:  # Positive definite measurement-error covariance.
        raise ValueError("HOLD_INVALID_CORRELATED_NOISE_COVARIANCE")
    var_o = tau2 + vo
    cov_o_k = beta * tau2 + c
    var_k = beta * beta * tau2 + vk
    variance_theta_given_o = tau2 - tau2 * tau2 / var_o
    covariance_theta_k_given_o = beta * tau2 - tau2 * cov_o_k / var_o
    variance_k_given_o = var_k - cov_o_k * cov_o_k / var_o
    if variance_k_given_o <= 0:
        raise ValueError("HOLD_GAUSSIAN_CONDITIONAL_VARIANCE")
    reduction = covariance_theta_k_given_o**2 / variance_k_given_o
    variance_theta_after = variance_theta_given_o - reduction
    if variance_theta_after < -1e-12:
        raise ValueError("HOLD_GAUSSIAN_NEGATIVE_POSTERIOR_VARIANCE")
    return {
        "family_and_own_error_covariance": c,
        "latent_variance_given_own": variance_theta_given_o,
        "latent_variance_given_own_and_family": max(0., variance_theta_after),
        "ideal_additional_family_variance_improvement": reduction,
        "conditional_family_loading_covariance": covariance_theta_k_given_o,
        "correlated_errors_may_represent_shared_context_NOT_genetic_proof": True,
    }


def _load_aggregate(root: Path, key: str) -> tuple[dict, str]:
    path = root / INPUTS[key]
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError("HOLD_SOURCE_AGGREGATE_NOT_AVAILABLE_" + key)
    raw = path.read_bytes()
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError("HOLD_SOURCE_EVIDENCE_NOT_JSON_OBJECT")
    return obj, hashlib.sha256(raw).hexdigest()


def _same(a, b, *, tol=1e-10):
    if not math.isclose(float(a), float(b), rel_tol=0, abs_tol=tol):
        raise ValueError("HOLD_PREVIOUSLY_REPORTED_AGGREGATE_SCORE_DRIFT")


def extract_real_evidence(root: Path) -> dict:
    """Independently recompute signs and descriptive contrasts; no refitting.

    One selected 2026 sample, a separate 2022-24 period, anonymous genomic
    individuals and single-receipt market prices have NONJOINABLE IDs and
    cannot be interpreted as four independent kinship replications.
    """
    integrated, hs = _load_aggregate(root, "integrated")
    factorial, hf = _load_aggregate(root, "factorial")
    strict, hq = _load_aggregate(root, "strict")
    market, hm = _load_aggregate(root, "market")

    if integrated.get("status") != "INTEGRATED_SCIENTIFIC_EVIDENCE_REGISTRY_NOT_NEW_EXPERIMENT":
        raise ValueError("HOLD_INTEGRATED_SOURCE_NOT_REVIEWED")
    if factorial.get("status") != "POSTHOC_2026_OWN_VS_KIN_HISTORY_FRESHNESS_FACTORIAL_NOT_CAUSAL":
        raise ValueError("HOLD_2026_FACTORIAL_NOT_POSTHOC")
    if market.get("status") != "REAL_ARCHIVED_ONE_TIME_MARKET_CROSS_SECTION_NO_KIN_TEST":
        raise ValueError("HOLD_MARKET_SOURCE_NOT_SINGLE_SNAPSHOT")
    q = strict.get("analysis_from_actual_successful_job_stdout", {})
    if q.get("status") != "POSTHOC_JOINT_STRICT_RACE_AND_STRONG_AGE_SEX_RECENCY_NOT_GENETIC_CAUSATION":
        raise ValueError("HOLD_STRICT_TEST_NOT_POSTHOC_SOURCE")
    if factorial["combined_from_successful_aggregated_job_stdout"]["same_2026_focals_and_dates"] != [480,232,259,42]:
        raise ValueError("HOLD_2026_EMPIRICAL_COHORT_DRIFT")
    obs = integrated["real_observations"]
    if obs["Japan_genomic_G"]["same_registered_horse_IDs_matched_to_racing_data"] is not False:
        raise ValueError("HOLD_JOINT_GENOTYPE_HORSE_ID_UNVERIFIED")
    if market.get("horse_bloodline_or_genotype_effect_estimated") is not False:
        raise ValueError("HOLD_UNSUPPORTED_MARKET_GENETIC_CAUSATION")
    if market.get("herding_time_evolution_observed") is not False:
        raise ValueError("HOLD_FALSE_MEASURED_MARKET_FEEDBACK")
    if integrated["implemented_but_not_empirically_proven"]["true_2027_forward_pre_race_predictions_submitted"] != 0:
        raise ValueError("HOLD_FUTURE_PRE_RACE_RESULTS_CHANGED")
    if market["race_count"] != 9 or market["horse_quote_rows"] != 117:
        raise ValueError("HOLD_MARKET_SAMPLE_DRIFT")
    by = factorial["combined_from_successful_aggregated_job_stdout"]["by_model"]
    extracted = {}
    for model in ("ordinary", "strong"):
        ss, fs, sf, ff = (by[model][key] for key in ("SS", "FS", "SF", "FF"))
        for k,v in (("SS",ss),("FS",fs),("SF",sf),("FF",ff)):
            _same(v["family_increment"], v["rmse_own"] - v["rmse_kin"])
        _same(ss["rmse_own"], sf["rmse_own"])
        _same(fs["rmse_own"], ff["rmse_own"])
        own_gain = ss["rmse_kin"] - fs["rmse_kin"]
        kin_only_gain = ss["rmse_kin"] - sf["rmse_kin"]
        kin_given_fresh_own = fs["rmse_kin"] - ff["rmse_kin"]
        _same(own_gain, factorial["combined_from_successful_aggregated_job_stdout"][
            "factorial_contrasts"][model]["refresh_own_given_stale_family"]["RMSE_improvement"])
        _same(kin_only_gain, factorial["combined_from_successful_aggregated_job_stdout"][
            "factorial_contrasts"][model]["refresh_family_given_stale_own"]["RMSE_improvement"])
        _same(kin_given_fresh_own, factorial["combined_from_successful_aggregated_job_stdout"][
            "factorial_contrasts"][model]["refresh_family_given_fresh_own"]["RMSE_improvement"])
        if not own_gain > 0 or not kin_only_gain > 0 or not kin_given_fresh_own > 0:
            raise ValueError("HOLD_REPORTED_FRESHNESS_DIRECTION_CHANGED")
        extracted[model] = {
            "updated_focal_own_history_only_RMSE_gain_with_family_fixed": own_gain,
            "updated_relative_history_only_RMSE_gain_with_own_fixed": kin_only_gain,
            "updated_family_given_updated_own_conditional_RMSE_gain": kin_given_fresh_own,
            "own_only_gain_to_family_only_gain_ratio_DESCRIPTIVE": own_gain/kin_only_gain,
            "full_updated_family_increment_over_updated_no_family_RMSE":
                ff["family_increment"],
            "full_updated_no_family_RMSE": ff["rmse_own"],
            "full_updated_with_family_RMSE": ff["rmse_kin"],
        }
    strict_data = q["strict_strong"]
    strict_2024 = q["strict_strong_yearly"]["2024"]
    _same(strict_data["M0_minus_kin_gain"],
          strict_data["RMSE_portable_no_kin"]-strict_data["RMSE_portable_kin"])
    _same(strict_2024["midpoint_minus_kin_gain"],
          strict_2024["RMSE_unchanged_midpoint"] - strict_2024["RMSE_portable_kin"])
    prior = obs["Japan_2022_2024"]
    _same(prior["gain"],prior["no_parent_RMSE"]-prior["with_parent_RMSE"])
    if not (prior["fake_parent_pair_shuffles"] == 19
            and prior["shuffles_exceeding_true_gain"] == 0
            and prior["min_attainable_one_sided_plus_one_p"] == 0.05):
        raise ValueError("HOLD_FALSE_CONFIRMATORY_PERMUTATION_P")
    if not (strict_2024["midpoint_minus_kin_gain"] < 0
            and extracted["ordinary"][
               "full_updated_family_increment_over_updated_no_family_RMSE"] < 0):
        raise ValueError("HOLD_RECORDED_NEGATIVE_RESULTS_NOT_PRESERVED")
    qmarket = market["races"]
    values = [r["field_size_adjusted_effective_fraction"] for r in qmarket]
    if len(qmarket) != 9 or any(not 0 < x <= 1 for x in values):
        raise ValueError("HOLD_MARKET_CONCENTRATION_INPUT_BAD")
    return {
        "status": "RECOMPUTED_FROM_PREVIOUSLY_COMMITTED_AGGREGATES_NOT_NEW_INDEPENDENT_EMPIRICS",
        "source_aggregate_SHA256": {
            "integrated": hs, "factorial": hf,
            "strict_race_outcome": hq, "market_snapshot": hm,
        },
        "Japan_2026_one_selected_posthoc_cohort": {
            "observed_horses":232,"observed_starts":480,
            "same_sample_original_source_2026_kin_increment":
                obs["Japan_2026_external_and_replay"]["original_source_separated_no_kin_RMSE"]-
                obs["Japan_2026_external_and_replay"]["original_source_separated_kin_RMSE"],
            "ordinary_and_strong_model_contrasts": extracted,
            "subgroup_and_model_selection_already_inspected": True,
            "family_freshness_comparison_does_NOT_establish_kin_deployable_value": True,
        },
        "Japan_2022_2024_separate_period": {
            "focal_horses":prior["later_source_horses"],
            "observed_starts":prior["observed_starts"],
            "portable_original_family_increment_RMSE":prior["gain"],
            "strict_race_with_strong_own_history_observed_starts":strict_data["rows"],
            "strict_race_with_strong_own_history_family_increment_RMSE":
                strict_data["M0_minus_kin_gain"],
            "strict_2024_midpoint_better_than_family_RMSE":
                strict_2024["midpoint_minus_kin_gain"] < 0,
            "parent_shuffled_controls":19,
            "controls_exceeding_true_increment":0,
            "minimum_one_sided_plus_one_p_no_confirmatory_test":0.05,
            "posthoc_reanalysis_same_period_not_independent_replication":True,
        },
        "market_real_cross_section_not_trajectory": {
            "race_count":market["race_count"],
            "horse_quotes":market["horse_quote_rows"],
            "min_field_normalized_effective_horses":min(values),
            "max_field_normalized_effective_horses":max(values),
            "min_top_favorite_normalized_inverse_odds_weight":
                min(r["relative_favorite_support"] for r in qmarket),
            "max_top_favorite_normalized_inverse_odds_weight":
                max(r["relative_favorite_support"] for r in qmarket),
            "time_trajectory_measured":False,
            "actual_votes_or_market_social_contagion_identified":False,
            "horse_genotype_or_pedigree_JOIN":False,
        },
        "genomic_G_coverage": {
            "anonymous_horses":obs["Japan_genomic_G"]["original_sample_horses"],
            "autosomal_QCed_SNPs":obs["Japan_genomic_G"]["post_QC_autosomal_SNPs"],
            "sample_pairs":obs["Japan_genomic_G"]["computed_sample_pairs"],
            "same_registered_horse_linked_to_race_performance":False,
        },
        "separate_phenotypes_and_studies_not_merged":True,
        "causal_genetics_or_2027_forecast_effect_NOT_established":True,
    }


def analytic_grid() -> dict:
    p = MODEL_PARAMS
    rows = []
    for n in (0, 1, 3, 10, 30):
        for age in (30, 365, 1460):
            rows.append(gaussian_information_value(
                n_own=n, n_family=p["family_proxy_observation_count"],
                kin_lag_days=age,
                prior_var=p["prior_latent_variance"],
                own_noise_per_observation=p[
                    "individual_measurement_noise_variance_per_observation"],
                family_noise_per_record=p[
                    "family_proxy_measurement_noise_variance_per_record"],
                family_loading=p["family_signal_loading_not_genetic_relatedness"],
                age_decay_scale_days=p[
                    "family_information_age_decay_scale_days"],
            ))
    # A second toy counterexample: K is a linear proxy of O plus
    # independent noise, so K has no additional information about theta.
    redundant = conditional_gaussian_family_gain(
        prior_var=1.0,own_error_var=1.0,family_error_var=1.0,
        family_loading=0.5,correlated_measurement_errors=0.5,
    )
    if not abs(redundant["ideal_additional_family_variance_improvement"]) < 1e-12:
        raise ValueError("HOLD_THEORETICAL_REDUNDANCY_COUNTEREXAMPLE_FAILED")
    return {
        "status": MODEL_TAG,
        "assumptions_explicitly_fictional": MODEL_PARAMS,
        "dimensionless_no_horse_OR_market_data_fitted": True,
        "Gaussian_conditional_precision_grid":rows,
        "correlated_noise_redundant_proxy_counterexample": redundant,
        "risk_reduction_is_for_latent_theta_NOT_observed_rank_RMSE": True,
        "family_signal_loading_is_NOT_pedigree_A_or_genomic_G": True,
        "conditional_information_nats_is_NOT_observed_market_information_flow": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    obj={
        "status":"OBSERVED_AGGREGATE_PARITY_PLUS_ANALYTIC_SYNTHETIC_INFORMATION_MODEL",
        "observational_evidence":extract_real_evidence(args.repo_root),
        "theoretical_counterfactual":analytic_grid(),
        "scientific_interpretation":{
            "real_2026_information_refresh_is_posthoc":True,
            "Bayesian_value_prediction_needs_new_future_2027_data":True,
            "human_odds_ABM_and_horse_performance_are_separate_processes":True,
            "valid_future_test_requires_true_published_at_history_and_IDs":True,
            "M2_must_beat_same_sample_M1_and_M0_before_operational_claim":True,
            "real_heritable_effect_or_MSTN_genotype_link_is_HOLD":True,
            "no_pools_ticket_shares_or_herding_estimated":True,
        },
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    # Only robust aggregate result, no full case-by-case source records.
    o=obj["observational_evidence"]
    print(json.dumps({
        "status":obj["status"],
        "source_aggregate_SHA256":o["source_aggregate_SHA256"],
        "Japan_2026_one_selected_posthoc_cohort":o["Japan_2026_one_selected_posthoc_cohort"],
        "Japan_2022_2024_separate_period":o["Japan_2022_2024_separate_period"],
        "market_real_cross_section_not_trajectory":o["market_real_cross_section_not_trajectory"],
        "toy_own0_recent_family_variance_gain":obj["theoretical_counterfactual"][
            "Gaussian_conditional_precision_grid"][0]["ideal_variance_improvement"],
        "toy_own10_recent_family_variance_gain":obj["theoretical_counterfactual"][
            "Gaussian_conditional_precision_grid"][9]["ideal_variance_improvement"],
        "toy_fully_redundant_family_variance_gain":obj["theoretical_counterfactual"][
            "correlated_noise_redundant_proxy_counterexample"][
                "ideal_additional_family_variance_improvement"],
        "not_an_empirical_market_or_genetic_effect":True,
    },indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
