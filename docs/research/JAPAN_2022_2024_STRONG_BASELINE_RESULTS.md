# 2022–2024 portable stronger pre-race history: family-history incremental RMSE

**Actual-source run SUCCESS:** [GitHub Actions #43893149680](https://github.com/zuizui0223/keiba/actions/runs/43893149680), job **133389441870**, commit **2644d7d959a8d6930bb39e32dc9339a66f1b425c**, ZIP artifact **14237956921**, SHA256 **4e478bd82028feab3d1353634908bbd49120515f9b91960197402e9a7aff76da**.

**Explicitly post-hoc:** these extra features were chosen after the previous small positive family-history result was known. They are an additional sensitivity check on **the same** second-source 2022–24 period, not new external replication or a preregistered holdout. The source A and B SHA256, historical two-event crosswalk and original scores were locked and reproduced before analysis.

## Model definitions and input availability

The source-A-only history gives age inferred from first documented racing-year minus historical recorded age, sex last recorded before the target cutoff, elapsed time since the last *precutoff* start, mean rank across the last ten starts and fraction of source-A historical starts in the JRA circuit. Explicit age-unknown/conflict and sex-unknown indicators are included. Exactly the same age/sex/recency features enter the no-family and with-family ridge models. The latter adds only the four original same-sire/dam other-horse history features; **no target's own race result enters its relatives' historical score**. Ridge alpha fixed 100 and original 2018–21 old-source training cohorts maintained.

In the 2022–24 selected cohort, old-source history suffices to infer both age and last-known sex for **100%** of scored rows. In the earlier annual training targets, these are available only for **about 83%** because some horses lack a recorded prior start. This itself is a **cohort selection shift**: the later-source evaluation excludes horses without two matched pre-2022 history events. It limits transportability, not a reason to discard missing rows.

Current rider, trainer, race class and exact venue cannot be joined between the original archived IDs and the later SQLite by unverified source labels. Horse sex last known before 2022 may become stale, especially if castrated later. The later-source target rank is still normalized by the declared runner count; the strict complete-race audit was performed **separately** on the frozen original model.

## Empirical results on same 255,484 starts and 12,919 selected horses

| Frozen/extended model | Equal-horse-weighted RMSE |
|---|---:|
| Original no-family | 0.312777516 |
| Original +parent history | 0.312455062 |
| **Expanded age/sex/recency no-family** | **0.311692673** |
| **Expanded no-family +parent history** | **0.311432823** |

- Expanded own-history features improve the no-family RMSE by **0.001084843**, about **3.4 times** the original standalone family-history increment of 0.000322454.
- Within the expanded models, the **additional recorded family-history gain is +0.000259849**, roughly 0.083% of the new no-family RMSE. Thus the family-history association is **attenuated but remains positive**.
- One-way 399-draw horse-cluster sensitivity 95% interval **[+0.000059321,+0.000451078]**, separate race-calendar-day interval **[+0.000126750,+0.000391791]**. Neither interval proves inheritance or is a multilevel joint cluster inference.

| Year | Expanded no-kin RMSE | Expanded +family RMSE | Family increment | Fixed midpoint RMSE |
|---|---:|---:|---:|---:|
| 2022 | 0.309452714 | 0.309163044 | +0.000289670 | 0.321526961 |
| 2023 | 0.317022990 | 0.316731807 | +0.000291183 | 0.319608023 |
| 2024 | 0.319104177 | 0.318542487 | +0.000561690 | **0.317212146** |

The 2024 family *increment* becomes larger than in the original portable model, but **both expanded models still lose to a flat midpoint baseline that year**. This is a practical performance failure, not grounds to claim that using family data reliably produces better forecasts. No 2025 partial-year outcome entered the expanded primary evaluation.

## Interpretation

**Supported:** adding age, last-known sex and simple individual racing-history recency **improves predictive performance** more than adding family history alone. Conditional on these features, matching the *actual* sire/dam other-horse histories still yields a **small additional reduction** in normalized-rank RMSE for these selected previously active horses.

**Not supported:** heritability, additive genetic breeding values, causal sire/maternal inheritance, full multi-generation A, individual genomic G, official nationwide coverage, price informativeness, odds market dynamics or betting returns. The data come from related racing-record sources with unverified upstream rights and a historical event-match crosswalk, not an official studbook.

**Most important remaining tests:** (1) Evaluate these exact **expanded** coefficients on the *same strict-complete-race subset* verified in a separate source-denominator audit, (2) stronger pre-race trainer/class/venue controls where stable IDs can be legally obtained, and (3) truly unseen future runs with fully audited race-and-pedigree identifiers. Avoid treating a post-hoc exploratory model as prospective confirmation.

[Source- and run-pinned aggregate evidence](../evidence/japan-2022-2024-strong-prehistory-20261116.json) · [post-hoc feature protocol](JAPAN_2022_2024_STRONG_BASELINE_PROTOCOL.md).
