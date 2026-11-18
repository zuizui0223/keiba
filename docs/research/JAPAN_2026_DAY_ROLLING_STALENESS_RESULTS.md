# Racing information freshness vs recorded family history: 2026 post-hoc replay

**2026-11-17 UTC/JST result: actual-source analysis SUCCESS, but fully POST-HOC.** The original partial-2026 out-of-period prediction failed to beat fixed normalized midpoint; we explicitly keep that negative result and test only one explanatory mechanism using **the same 232 horses / 480 starts**.

[GitHub Actions run #44007279933](https://github.com/zuizui0223/keiba/actions/runs/44007279933) succeeded on commit 48ee00f8c10e8d6fc6aed40ffeed2075032a5452, job 133785550303. The aggregate-only artifact **14294719430**, ZIP digest SHA256 **11324361180b1c5e30b78c82fb96bd0eb6e908817dadeeb672de08e4d7ad2e3d**, is traceable from the [permanent logged aggregate evidence JSON](../evidence/japan-2026-posthoc-day-rolling-staleness-20261117.json). No raw horse names, IDs, race records or individual predictions were copied to GitHub.

## Fixed design and source reconstruction

Sources were locked to their prior full SHA256 releases:
- A (original 2010–21 race and parent archive): c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f.
- B (1990–2025/03 historical identity-witness SQLite): 7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9.
- C (public 2023–2026/05 JRA HTML-derived results CSV): ca14ff253018433e8e14bc583628f85ca909195d5e4edb42c6d1e2ade939ba6f.

B↔C horse identity relied exclusively on exact names and two dated rank/condition matches in **2023–24**; A↔B relied on two **pre-2022** races. No 2025 or 2026 result was used to choose horse identity. The existing **1,945** A↔B↔C historical IDs, **232** older 2026 focal horses, **480** starts / **259** races / **42** distinct calendar days were preserved exactly. Both 2021-stale original ordinary and strong model score pairs reproduced to 1e−8; a focal + shared-parent-relevant subset of A preserved all original features to 1e−10. Source A had 2,092,836 original rows; the prechecked lossless restricted family context had 688,571 rows.

The original source-A trained coefficients and ridge α=100 were **not retuned**. Source C historical races with complete and unique 1..N classified ranks were added only for the already-anchored individuals. For each target, historical features use source C from:
- Scenario 1: **none after 2021** (original stale model).
- Scenario 2: **up to 2025-12-31**, fixed for all 2026 starts.
- Scenario 3: **strictly earlier calendar date** than each 2026 target, including older 2026 results but excluding all same-day results, regardless of race time.

Because C has no independently verified result-publication timestamp, scenario 3 is **calendar-day-lagged**, not a certified live pre-race known-on replay. Both historical sources and the heldout source may derive from common JRA upstream. The outcomes and this post-hoc feature proposal were already observed. These results cannot become an untouched independent test simply by filtering dates.

## Main results: equal-focal-horse-weighted normalized rank RMSE

**Lower is better.** The source C target is a complete-classified-rank result, not a probability or a wager.

| Historical information for prediction | Ordinary no-family | Ordinary + same-parent other-horse history | Strong own-history no-family | Strong + family |
|---|---:|---:|---:|---:|
| Constant midpoint benchmark | 0.312146 | 0.312146 | 0.312146 | 0.312146 |
| **Only through source A, 2021 (unchanged old result)** | 0.319682 | 0.320302 | 0.321519 | 0.318075 |
| Add verified-source-C historical races through **2025-12-31** | **0.276847** | 0.278462 | 0.276846 | **0.276429** |
| Update C history through **prior calendar day of each 2026 start** | **0.274782** | 0.276427 | 0.274706 | **0.274423** |

The ordinary **no-family** predictor improved by **0.044899 RMSE units** (relative reduction ~14.05%) between the stale A-only and day-lagged versions. Most of this (0.042834 of 0.044899 units) is already achieved by adding **2023–25** C histories; adding prior 2026 calendar days contributes another 0.002065.

The strong no-family predictor improved by **0.046813 units** between stale and day-lagged history. Crucially, the **family increment on 2026 with day-lagged current history is not robust**:

| Family-history addition, using updated information | ΔRMSE = no-family RMSE − with-family RMSE | One-way horse-bootstrap 95% sensitivity |
|---|---:|---|
| Ordinary, through 2025 | **−0.001615** (deteriorates) | [−0.004253, +0.000749] |
| Ordinary, prior day 2026 | **−0.001644** (deteriorates) | [−0.004240, +0.000711] |
| Strong, through 2025 | **+0.000417** (tiny) | [−0.002303, +0.002950] |
| Strong, prior day 2026 | **+0.000283** (tiny) | [−0.002333, +0.002639] |

All listed intervals include zero. Therefore the updated own-history signal is large but **no reliable incremental same-parent-history forecast value has been demonstrated for 2026**.

Unlike the original stale-run 2026 models, **all refreshed models beat the fixed 0.5 benchmark** on this selected sample. This is a positive post-hoc diagnostic of **available racing-history information**, not an independent, commercially deployable result.

## Information coverage and what changed

- The most recent source-A race for a 2026 target was a median **1,562 days (≈4.28 years)** earlier; interquartile range 1,525–1,610 days.
- **226 of 232** focal horses already had a linked 2025 source-C race record, covering **467 of 480** 2026 focal starts.
- Source C supplied **13,149** pre-2026 complete-race history rows among 1,655 focal-or-family-relevant, historically anchored horses; **2,220** of those rows were from 2025. It supplied earlier-calendar-day 2026 histories only where actually available.
- All C source-day race results are from complete 1..N classified races after source QA. C cannot certify the true list of official nonfinishers, first publication times, or changed source records.

## What is biologically supported

**Conditional association:** a horse's **recently observed own racing performance** greatly improves the fit of previously trained models for this selected previously active 2026 cohort compared with models forced to use 4-year-old historical records. Historical predictions are sensitive to information freshness and scope. Even fully updated, the record-shared **sire/dam relative** effect remains small, noisy or negative.

**Not supported:** the fresh own-history gain is proof that temporal decay alone *caused* the original failure (the source, outcome coverage and available individual information change together). It does not establish additive genetic variance, heritability, biological kinship A, identity-linked genomic G, or public-odds/betting advantages. The 2026 test was already inspected before this diagnostic and cannot be reframed as a new discovery holdout.

## Decision and next valid test

Preserve both observations: **a 2026 frozen-2021 model fails to transfer**, and **a non-causally motivated rolling historical update strongly improves the same post-hoc sample**. Frame the new ecological/evolutionary hypothesis as the *temporal availability of reliable individual vs familial information*, rather than as an established "kinship gene" predictor.

For a genuinely prospective conclusion, use the separately frozen [2027 official blood-ID, result known-on, and rolling history protocol](JAPAN_2027_OFFICIAL_ID_ROLLING_FORECAST_PROTOCOL.md) and its [private known-on validator](JAPAN_2027_PRIVATE_KNOWNON_VALIDATOR.md). The validator's 12 fictional tests passed; there are **no licensed JRA/NAR 2027 outcomes** here and no current national pedigree completion. Never train on inspected 2026 results and then claim 2026 as a new untouched validation. External provider licensing remains unresolved.
