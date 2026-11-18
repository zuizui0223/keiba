# Source-B Race.horses denominator / identity audit (post-hoc)

**Date: 2026-11-16. Scientific status: exploratory quality / effect portability check, not preregistered evidence of heritability.**

## Why

The 2022–2024 external time-window score uses the archived older source's fully classified 1..N finishing ranks in model training, but the separate 1990–2025 SQLite Horse.races table contains a declared field size N that might include nonfinishers, ties or incomplete race results. Thus a positive 0.000322 RMSE gain can be confounded with a *change of response definition*. The **frozen 255,484-row/12,919-horse source-separated result is not to be updated, tuned or relabeled**, and 19 post-hoc parent-ID placebo comparisons remain separately recorded.

The dataset publisher's documented Race.horses schema contains each source horse ID and final ranking. The Horse.races schema contains race ID, declared field size and final ranking (actual published file has 17 fields rather than documented 18; calendar date comes from Race.date). This allows a stricter check based on **two different tables of the same later-source SQLite database**, not independent official data.

## Prespecified gate for this additional, post-hoc audit

1. SHA256 lock both source files and reproduce the **exact** original 2022–24 cohort and source-A-only model RMSE (no kin 0.31277751588017505, with kin 0.3124550620307501). Fail closed if anything differs more than 1e-8.
2. The old-source horse and later-source Horse.hid can be connected only by their already-fixed **two distinct identical pre-2022 historical races**. No post-2021 outcome is used to set horse identity or fit model coefficients.
3. For each selected later-source race, parse Race.horses as a list of [horse ID, final rank, ...] records. A STRICT_COMPLETE_CLASSIFIED_RACE has:
   - unique nonempty race horse IDs, integer finishing ranks 1..N exactly once, no ties or gaps, and N equals the independently reported Horse.races declared field size;
   - each focal horse's **new-source horse ID and rank** identical between its own Horse.races history and that Race.horses listing;
   - no missing or inconsistent Race.rid lookups.
   This is a *source-consistent complete-classified race*, not independent official certification of all starters.
4. Preserve the original fixed coefficient vectors (no retraining, no target-year lookup into predictors). Recalculate equal-horse-weighted RMSE and both single-way bootstrap intervals only for focal horses in strict races.
5. A separate **CLASSIFIED_PROXY** may use a race whose positive ranks form 1..m but m < declared N (including zero-rank nonfinishers). Only for focal horses individually confirmed by new-source horse ID and rank, use normalized rank (rank−1)/(m−1). This is an **incomplete-denominator proxy**, not proven official finisher counts; never pool with strict without labeling.
6. If source tables cannot be fully cross-validated, report HOLD, missing and conflict counts; do not weaken criteria to manufacture a positive effect. Report years separately and compare to the fixed midpoint baseline, not just with-kin vs no-kin.
7. No raw horse names, IDs, races, crosswalk, individual outcomes or predictions are published. All raw third-party data are transient on the CI runner, and the upstream racing-content rights are not independently verified.

## Interpretation gate

- If real-family gain remains positive and meaningful on strict complete races, the earlier apparent predictive value is **less likely to be driven entirely by denominator mismatch**. It still does not establish genetic inheritance, nor resolve why 2024 weakens.
- If strict races show no benefit or weak coverage, the original score remains historical but any claim of transportable family-history information should be weakened.
- A source-internal rank consistency check is **not** confirmation from a licensed official studbook.
- Later work will separately compare richer **pre-race** non-family history including age, sex and recency, using old-source pre-2022 features only; unavailable later-source race class, trainer and same-ID jockey cannot be manufactured.

Code: scripts/ecology_japan_2022_denominator_audit.py; synthetic tests: tests/test_ecology_japan_2022_denominator_audit.py.
