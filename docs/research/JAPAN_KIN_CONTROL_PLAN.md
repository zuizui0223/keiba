# Same-target strong baseline and shuffled-parent controls (2026-11-14)

This extension is exploratory sensitivity of PR45, not new untouched validation. All 2019–2021 outcomes were examined previously. Preserve existing analyses and do not overwrite their scores.

## Fixed decisions before this run

- Use original source SHA256 c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f and identical eligible rows. Replay all original annual scores against japan-group-primary-lock-20261114.json before scoring new models.
- New baseline is weighted ridge regression, alpha=100, fixed rather than tuned against 2019–2021 outcomes. Each horse has equal total loss weight. Fit annual feature records from 2016 through Y-1; test Y=2019,2020,2021.
- Histories for every annual feature record are frozen before January 1 of that feature year: overall/context means and counts, last1/3/10 and preceding365-day summaries, time since last start, trainer/jockey prior peer means. Also use reported age, sex, course, going, race class, surface, circuit and distance. Trainer/jockey means exclude the focal horse. No odds, current finish time, current rank, prizes or finishing-field predictors.
- Numeric transformations and categorical vocabulary fit only on training years. Categorical levels with fewer than20 training rows or outside the256 most common levels are grouped as other. Previously unseen test levels map to other.
- True-parent models add only leave-focal-out sire/dam peer signals and cold-start/history-support interactions. Distinct other horses receive one historical mean per context. Not a multigeneration A or genomic G.
- Three negative controls permute the complete father/mother pair together between horse IDs within birth-estimate five-year bin and first observed JRA/NAR circuit. Seeds20261114,20261115,20261116. The mapping is outcome-blind but conditioned on the entire retrospectively observed source roster. Both historical and future parent labels receive the same stable mapping. Control models are fitted on prior years just like the real-parent model.
- These three shuffles are diagnostics, not a calibrated permutation p-value or proof of genetic causality.
- Report every previously declared38 prefix group and20 sire groups, including small and unhelpful ones. No group-specific tuning. Sire groups selected by pre2019 offspring counts, not predictive results.
- Separate sire-family and date bootstrap sensitivity intervals; not joint multiway intervals, population generalization, or multiplicity-adjusted subgroup tests.

## Source and limits

The public archive's redistribution licence is Unknown. Raw records and individual predictions must remain transient and be deleted after scoring. Only source hashes, code and aggregate counts/metrics are uploaded. Source parent/trainer and race-condition metadata lack independently verified historic publication times. Target selection is conditional on retained classified finishing ranks. No genuine prospective claim, nationwide census, causal genetic effect, heritability, current-race betting or profit.

## Verification

New12 tests: temporal boundary; target-outcome invariance; last3 scalar reference; unseen horse midpoint; focal exclusion; blank parents; parent-pair count preservation and outcome blindness; training-only preprocessing; independently solved weighted ridge reference; metric empty cases. Preserve existing code/tests and verify original-source cohort equality. Added files only on the PR45 branch.
