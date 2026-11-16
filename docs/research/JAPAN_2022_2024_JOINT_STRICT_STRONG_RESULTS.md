# Japan 2022–2024: joint strict-classified race × strong pre-2022 own-history benchmark

**Status:** actual-source, post-hoc joint robustness **SUCCESS**. This is not a preregistered or independent new holdout, and no genetic causal effect is identified.

[Successful GitHub Actions #43894300320](https://github.com/zuizui0223/keiba/actions/runs/43894300320); job 133393559530; source commit acd8ee400ca6428c1d881cdafbccc979dc4a8c9b; aggregate-only artifact ID **14238242875**, ZIP digest SHA256 **dfc728698ebefdceeb807e9397bceedff1e27144aafdc97af3c3db3e57e9bdff**.

## Triple-parity quality gates: all passed

1. Only historically cross-matched horses from two or more **distinct pre-2022 identical old-source racing events** were included. Source releases fixed at SHA256 c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f (old 2010–21 ZIP) and 7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9 (later SQLite).
2. Locked original **255,484** test starts and **12,919** horses produced the unchanged original no-family RMSE **0.312777516** and real same-parent RMSE **0.312455062**.
3. The newly expanded historical age/sex/recency no-family RMSE **0.311692673**, expanded real-parent RMSE **0.311432823**, and the same full cohort were reproduced.
4. The independent-source Race.horses rank must match the *same new horse ID and rank* in its Horse.races list and have consecutive ranks 1..N exactly matching declared N. The independently audited **244,147** strict starts / **12,887** horses / **35,333** races were reproduced. On that subgroup the untouched original no-family RMSE **0.313543356** and +real-parent RMSE **0.313218666** also reproduced.
5. Only then did the analysis score fixed expanded age/sex/recency coefficients on **that identical strict subset**.

No future race outcome influenced source ID matching, model coefficients, history feature creation, pedigree linking or cohort tuning. Both SQLite tables are **same-source** quality controls, not independently certified official races. This is **post-hoc after viewing positive effects twice**.

## Main new result: same rows, same response, same expanded controls

| Prediction on the 244,147 strict starts | Individual-horse-weighted normalized-rank RMSE |
|---|---:|
| Frozen original no-family | 0.313543356 |
| Frozen original with same-parent history | 0.313218666 |
| **Expanded old-source age/sex/recency no-family** | **0.312429448** |
| **Expanded old-source age/sex/recency + same-parent history** | **0.312167869** |
| Simple fixed midpoint 0.5 | 0.321744142 |

- **Improvement from augmenting own-horse pretarget history (no family): +0.001113908** RMSE versus original no-family.
- **Additional improvement attributable to the source-recorded actual same-parent other-horse histories under these predictors: +0.000261580**, about 0.084% of expanded no-family RMSE.
- Horse-cluster 399-resample one-way 95% sensitivity interval **[+0.000077019, +0.000438797]**, separate race-calendar-day cluster interval **[+0.000121521, +0.000394440]**. These intervals are exploratory conditional sensitivity, **not** evidence of genetic heritability, a joint two-way bootstrap or preregistered discovery.

| Calendar year | Strict starts | RMSE expanded without family | RMSE expanded +family | Incremental gain | Expanded +family minus fixed midpoint benefit |
|---|---:|---:|---:|---:|---:|
| 2022 | 120,381 | 0.310059507 | 0.309804310 | +0.000255196 | +0.012327849 |
| 2023 | 80,939 | 0.317894126 | 0.317566350 | +0.000327776 | +0.002885313 |
| **2024** | **42,827** | **0.319865727** | **0.319256714** | **+0.000609012** | **−0.001197930** |

**Important negative operational result:** in 2024 the +family expanded model still performs worse than a fixed 0.5 prediction (0.319257 versus 0.318059), even though the incremental family information is positive relative to expanded no-family. A family-information advantage is **not a uniformly good forecasting strategy**.

## Meaning and limitations

**What is supported:** For the *selected previously raced Japanese horses* that have two earlier historical cross-source matching events, the identities of relatives sharing a recorded direct sire/dam provide **small additional race-rank prediction information** beyond own historical performance, age estimated from pre-2022 source, sex last known before 2022, and elapsed time since the last documented start. Both source-rank completeness and covariate enrichment were checked together.

**What is not supported:** A causal genetic mechanism, additive genetic variance/heritability, actual genomic G/IBD, full multi-generation relationship A for all JRA/NAR horses, a stable out-of-period result for new debutants, horse social behavior, an odds-market threshold or profitable wagers. Recorded sire/dam IDs also carry farm management, trainer, owner and selective breeding structure; a placebo permutation of parent pairs within approximate birth cohorts cannot remove all these alternative pathways.

The model source-A and source-B race records may share original racing websites. The later source's metadata license label does not by itself clear third-party race-record rights. No source horse IDs, name lists, full original races, genotype mapping or individual predictions are distributed. Additional class/trainer/jockey covariates are not assigned from unverified cross-source numeric keys.

### Next primary test

Stop treating increasingly re-used 2022–24 post-hoc sensitivity as independent evidence. The defensible next increment is a genuinely future-time, unseen registered-horse cohort with audited official ID and fully aligned pre-race training/racing covariates. Distinguish retained older starters vs new debutants. Use a source-certified pedigree if the scientific target is genetic relatedness or heritability, not just family predictive information.

[Immutable aggregate evidence JSON](../evidence/japan-2022-2024-joint-strict-strong-20261116.json) | [locked joint design](JAPAN_2022_2024_JOINT_STRICT_STRONG_PROTOCOL.md).
