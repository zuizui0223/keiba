# 2026 day-lagged rolling-source C history vs 2021-frozen forecast

**Protocol and all comparisons recorded 2026-11-17 AFTER seeing the original 2026 negative outcome. Strictly POST-HOC.** This is an explanatory stress test of stale information, NOT an independent confirmation, a licensed official race feed, or a new 2026/2027 holdout.

## Fixed sample, sources, no new ID tuning

The initial three-source study used A=original 2010–21 family/race archive, B=1990–2025/03 SQLite (ID witness), C=public 2023–2026 JRA results CSV. All three original SHA-256s, A→B pre-2022 two-event match, B→C exactly two 2023–24 dated race matches and full-ranked 2026 eligible C races are unchanged. Expect exactly **232 focal older horses / 480 2026 starts / 259 races / 42 dates**. Require exact original frozen RMSE values (see prior evidence), or hard HOLD.

This new script reuses the prior transient name-ID bridge in memory only. It does NOT relax historic matching, use 2025 or 2026 outcomes to choose horse identity, or merge unnamed parent IDs. No names, horse IDs, race rows, pseudo-pedigrees or individual predictions may leave the runner.

## Three scenarios, all on identical heldout 480 starts

1. **Original frozen-2021 history**: own and family features from A only, exact previous results **ordinary no-family 0.319681772293503 / +family 0.32030160640717165** and **strong no-family 0.3215185305911288 / +family 0.3180747501712852**.
2. **History through 2025-12-31 only**: A + source-C 2023–25 complete ranked races for the pre-2025-anchored identities. Never use C or B 2025 to change identity; all source-C history must be linked through the same historic ID bridge and source-A sire/dam reference. Recalculate original own and same-family prior-performance features but use **exact original source-A model coefficients**, with no hyperparameter or training update.
3. **Daily rolling prior days in 2026**: A + C complete ranked racing history from 2023 through the **calendar day before each 2026 target** (including earlier 2026 days). No same-day target or other racing result; source C has day but no verified publication time, so strictly earlier *date*, never same-day. Hold coefficients, model features, 2026 rows and source hashes fixed.

For each of 2 and 3, recompute both **ordinary** (8 own-history predictors, +4 parent-history features) and **strong** (same plus pre-2022-derived estimated age/sex, source-A/C last 10, race recency and historical-JRA share). Pooled RMSE (equal horse weights), per January/February/March/April/May support, fixed midpoint 0.5, and separate horse-/race-day clustered 399-resample intervals are reported. No sample selection based on the result. Source C only through **May 17, 2026**, not the whole year.

**Parity gate:** The baseline source-A-only full-sample predictions must match original #48 RMSE to 1e-8, and a source-A-only focal-family-filtered history must reproduce all original feature columns to 1e-10. Violation means HARD_HOLD even if a rolling score looks favorable.

## Questions and interpretation

- Does replacing 2021-stale history with verified pre-2026 history improve the no-family model? Does adding same-parent history improve further? Are either better than midpoint?
- Distinguish proportion of 2026 focal horses with C 2025 history and 2026 strictly prior-day histories, and distinct C parent-matched family-history contributors. Report coverage, not just gains.
- A positive rolling benefit may arise from **recency, different source's target definition, changed information coverage or sample selection**. It does **not** show that staleness caused the original negative result, heritability or useful live pre-race predictions.
- Pre-2022 training and 2026 results are already inspected, so these are explicit **post-hoc explanations**; the 2026 original failure remains the scientific out-of-time outcome. Do not overwrite PR #48's failure or claim a newly untouched independent test.
- The public C data is a snapshot with no verified `result_known_at` or race time. Excluding same-day races is a safety approximation, not a verified known-on public information stream. Official 2027 time-stamped model remains HOLD.

No JRA/JBIS bulk scraping. Only SHA-verified existing public files on transient CI runner, automatically removed. Source licensing remains unverified and aggregate-only JSON is published.
