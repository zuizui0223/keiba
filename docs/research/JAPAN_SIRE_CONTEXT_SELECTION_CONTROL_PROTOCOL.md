# Falsification of family-context resemblance by individual sorting and matched sire correspondence

2026-11-24, follow-up to PR78. Frozen before inspecting the new contrasts; not independent confirmation. Original source A and PR78 baseline/splits unchanged. Exact parity gates: 2,092,836 starts / 90,962 horses; diagnostic 57,208 starts / 15,129 horses; primary PR78 83 sires/174 sire-years/product 0.006530724376455479.

## Two separate diagnostics

1. **Within-horse contrast.** In each original split/year, require the same horse to have both turf and dirt records in 1600–1999m JRA. Mean residual by surface within horse, subtract, then center by half/year mean. Sire-year needs ≥3 paired horses in each half. Same equal-sire cross-half product as PR78, 999-draw sire bootstrap, HOLD interval if <30 sires. This tests whether resemblance persists after removing between-horse context sorting, but selects dual-surface runners and cannot eliminate within-horse temporal/context confounding. Report exact support even if too sparse. Never relax the minimum after viewing results.
2. **Correspondence placebo.** On original PR78 supported sire-years, form disjoint matched sire pairs with identical supported calendar years and all four within-year half/context horse counts within a factor of two. Greedy minimum squared log-count distance, deterministic hash tie break, no residuals used in matching. Compare actual same-sire cross-half product to swapping the B profiles between paired different sires. Equal year within pair, equal pair weighting; pair bootstrap 999 draws and HOLD interval below 20 pairs. This preserves counts/support, not genetic nonrelatedness or all environmental factors. Report matching attrition, true and placebo values and their difference, not randomization p-values.

Primary split for both is horse/day disjoint seed 20261124; other seeds and trainer-disjoint variants are sensitivity, not independent replication. Pointwise conditional intervals; no causal inference or claims of universally heritable reaction norms. Both diagnostics are new after the PR78 result, using same historical source. Record negative and HOLD outcomes; no betting models or ledgers changed.

[Code](../../scripts/ecology_japan_sire_context_selection_control.py) · [Workflow](../../.github/workflows/ecology-japan-sire-context-selection-control.yml).
