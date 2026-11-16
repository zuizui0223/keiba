# Post-hoc pre-2022 demographic and recency baseline for the 2022–24 family-history result

**Protocol committed 2026-11-16 after the previously observed positive family-history result and 19 false-family shuffles.** This is a *new, explicitly post-hoc sensitivity*, not a newly preregistered or untouched holdout.

## Research question

Does parent-sharing other-horse racing history add incremental information when stronger pre-existing focal-horse histories are included? Separate two same-source, pre-2022-fitted weighted ridge models (alpha fixed = 100):

- **Expanded no-kin baseline:** the original eight focal/track predictors + age derived from old-source race-year minus recorded age (strictly earlier than target cutoff), the old-source most recently recorded sex, days since the last old-source start, the mean of the last ten recorded classified ranks and the fraction of old starts recorded in JRA; encode explicit missing/age-conflict flags.
- **Expanded with family:** the expanded no-kin baseline **plus exactly the four original sire/dam other-horse history and relative-count features**; focal horse excluded by original algorithm.

No JRA/NAR race venue guess from the later-source place_id, no current 2022+ trainer/jockey/class mapping, no outcomes or prices after 2021 in feature engineering or ridge fitting. The source-A demographic covariates are available before cutoff and do not use source B birth/sex guesses. Explicitly mark that sex last recorded before 2022 can be stale after castration and age estimates can be missing/inconsistent.

## Immutable source and evaluation gate

- Source A archived 2010–2021 ZIP SHA256 c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f.
- Source B independent 1990–2025 SQLite SHA256 7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9.
- Same fixed two distinct pre-2022 matched source races for horse ID crosswalk. Holdout **12,919** unique horses and **255,484** starts in 2022–2024.
- Original no-family RMSE **0.31277751588017505**, with-family RMSE **0.3124550620307501** must reproduce to 1e-8 before running the expanded analysis. All scores from precisely the same rows, no prospective retuning.
- Train on original source targets 2018, 2019, 2020, 2021, each time only earlier years for histories, age/sex estimates and family features. For the 2022–24 holdout use 2010–21 only.
- Compare (1) expanded no-family vs original no-family, (2) expanded with-family vs expanded no-family, and (3) fixed midpoint 0.5. Evaluate pooled and each year; show horse-cluster and race-day-cluster one-way bootstrap sensitivity, not joint causal uncertainty.
- If the additional history fails or deteriorates, report it: it is not permitted to remove features after seeing outcomes, change ridge penalty or select years to make family features work.

## Interpretive limits

The newer source's normalized rank uses declared runners; old source ranks are consecutive classified finishers. A **separate strict-Race.horses denominator audit** tests sensitivity of the original model. Do not present the expanded-history result as a certified joint strict-denominator model until it is actually computed on that subgroup. Source B's underlying racing rights and the source A redistribution licence are not independently cleared. No official studbook A, genomic G, additive variance, genotype, MSTN or betting odds benefit is identified.

Code: scripts/ecology_japan_2022_strong_portable_baseline.py; tests: tests/test_ecology_japan_2022_strong_portable_baseline.py. All source rows and individual horse predictions are transient; published artifacts contain aggregates only.
