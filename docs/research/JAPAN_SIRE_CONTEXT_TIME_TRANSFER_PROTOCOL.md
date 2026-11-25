# Temporal transfer of within-horse context differences (2026-11-24)

## Why this test

PR78 observed recurring sire-indexed context-specific differences, but PR79 found insufficient paired-horse support and unstable matched-other-sire correspondence. Rather than relaxing the original minimum or choosing a favorable split, use naturally disjoint calendar years. This is a **new retrospective analysis of previously inspected years**, not an untouched independent or prospective test.

## Fixed design

Same exact source A (2,092,836 starts; 90,962 horses), unchanged PR78 chronological own/trainer rank baseline and 57,208 JRA 1600–1999m turf/dirt candidate starts (15,129 horses). Verify denominators. A horse must contribute both surfaces within a calendar year; response is mean turf residual minus mean dirt residual. No calendar-day thinning. Hash horses globally into halves (same fixed seeds as PR78). Predict each half of 2021 from paired horses of the opposite half in 2019–20; the 2020 target with 2019 training is a separate sensitivity. Strict sensitivity also assigns recorded trainer IDs to halves and removes incompatible rows; no trainer crosses halves. Shared earlier baseline model, environmental exposure, and cross-fit dependence remain.

For each direction, average repeated training-year differences within horse, estimate a global mean m and a mean for each sire. M0=m. M1=m+n/(n+8)*(sire mean-m) for at least 3 different training horses, otherwise M1=M0. Zero is an additional calibration comparator. All paired known-sire target horses remain in the primary denominator, including unsupported families; report supported subset separately. Target contrasts are never used to estimate models or choose donor groups. Each paired target horse is scored once across the two directions.

Negative control P: form disjoint other-sire pairs using training counts only, maximum count ratio 2, fixed greedy minimum log-count distance with deterministic hash tie break. For matched targets replace true sire mean with partner sire mean while keeping recipient shrinkage identical. Score M0/M1/P on the same matched subset. No genomic unrelatedness or randomization claim.

Primary: horse-disjoint, seed 20261124, held 2021, all target horses, MSE(M0)-MSE(M1). Report supported/matched subsets, other seeds, 2020, and trainer-disjoint sensitivity regardless of sign. Whole-sire bootstrap, 999 draws, conditional pointwise interval only if >=30 target sires. No multiple-comparison or all-dependence inference. Treat absent support and nonpositive or unstable effects as limitations rather than selecting new primary. The target itself is conditional on having observations on both surfaces; this is not an operational future prediction of surface switching.

[Code](../../scripts/ecology_japan_sire_context_time_transfer.py) · [Workflow](../../.github/workflows/ecology-japan-sire-context-time-transfer.yml). No individual records, betting predictions or outcome-derived selection of the primary contrast published.
