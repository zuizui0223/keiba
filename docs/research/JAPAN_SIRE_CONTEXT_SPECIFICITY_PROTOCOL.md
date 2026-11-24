# A necessary mechanism test: does a sire's residual context profile recur across independent observation subsets?

2026-11-24. New retrospective diagnostic, complementary to PR #77 (information diversity). It does not change that primary test. All effects are HOLD before real output.

## Motivation

If relatives' observations have a shared context component, a family-level reaction profile may recur across disjoint sets of horses and dates. That component could represent a transferable biological response, breeding/training practice, or other context-specific selection rather than mere noise. Thus a broad peer portfolio has two possible effects: reduces correlated error, but can dilute relevant context-specific signal. A positive result alone cannot tell these apart.

## Frozen primary statistic

Source A exactly SHA-pinned, original 2,092,836 starts/90,962 horses. Use JRA 1600–1999 m turf vs dirt, calendar years 2019, 2020, 2021. This specific pair is selected on substantive grounds, without observing new contrast results. Fit own-history + pre-target age/sex/recency + historical trainer-context peer (excluding focal) ridge alpha=100 on earlier JRA target-year blocks from 2016 onward; each block's features use only the years before it. The outcome is relative rank. Record annual M1-type vs 0.5 RMSE. This is not the PR77 portable M2 or a new untouched cohort.

For each fixed seed, hash horse identity and calendar day independently into two halves globally. Retain only starts with both labels agreeing. Strict sensitivity also requires a known recorded trainer assigned to the same half by independent hash. Thus no same horse, race-day, or (strict only) recorded trainer crosses the halves. Same fitted model/history, common trainers (primary), farms, and distant kin can still induce dependencies. Exposure is nonrandom.

In each half/year/context, first average residuals within each horse; subtract population horse-equal context mean. For each recorded sire/year with >=3 distinct horses in each of the four half x context cells, calculate delta_A = mean(r_A,turf) - mean(r_A,dirt), delta_B analogously. Primary: equal-sire mean of delta_A*delta_B (average within sire across supported years), seed 20261124, horse/day disjoint. Report support and whole-sire bootstrap pointwise sensitivity (999 draws; HOLD if fewer than 30 sires). Two other fixed seeds and trainer-disjoint results are sensitivity, not independent replications. No seed chosen based on effect. Show all year estimates and losses.

The product equals the sum of the two same-context cross-half products minus the two crossed-context products. A positive replicated difference is consistent with context-specific residual resemblance after family common offsets cancel. It is not a causal reaction norm: different horses enter contexts, and residual calibration, shared management and selection can produce a similar pattern. A non-positive or uncertain result leaves mechanism unestablished. Do not estimate genetic heritability, competition intensity or a universal information-diversity effect. Never use same-race relative ranks to claim physical competition.

## Execution and privacy

[Code](../../scripts/ecology_japan_sire_context_specificity.py) and [source-locked runner](../../.github/workflows/ecology-japan-sire-context-specificity.yml). Only aggregate diagnostics are emitted. Synthetic tests cover family offset cancellation, exact contrast algebra, four-cell support, row order and identity-disjoint splits. The data are temporary, redistribution rights and as-of publication times are not certified. No betting or PR77 scores/parameters changed.
