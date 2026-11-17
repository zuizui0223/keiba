# 2026 family-vs-own information freshness: actual-source four-condition factorial

**SUCCESS, 2026-11-17. Entirely POST-HOC explanatory sensitivity.** [GitHub Actions #44009989972](https://github.com/zuizui0223/keiba/actions/runs/44009989972), job 133794426168, source commit **80f42c163d2f964d84bce95bf67039c47a8187eb**; aggregate artifact **14295713998**, SHA256 **faad40e295301f55bdad3fbb5ecd6ddabca09f101205c0357d86c59470bb6d00**. Logged numeric aggregates and provider-release hashes are in the [permanent evidence JSON](../evidence/japan-2026-own-kin-factorial-empirical-20261117.json).

The frozen 2026 cohort was **232 previously raced horses, 480 starts, 259 races and 42 dates** (2026-01 through 2026-05-17); all were retained. A↔B identity still required two distinct matching **pre-2022** races and B↔C two dated matching **2023–2024** races. Source C history was used only if strictly **earlier calendar day** than the target race; no result publication time was independently verified. Source C's source snapshot and all original ridge coefficients were unchanged, and the four previous 2021-stale vs 2026 prior-day-replay RMSE pairs were reproduced within tolerance 1e−8 before accepting results. Synthetic tests verified correcting the focal-history attenuation on the four parent-specific features.

## Result: own history refresh is the dominant improvement

All four models use the same original source-A 2018–21 ridge training and the *same* test labels. Comparison is equal-focal-horse-weighted normalized rank RMSE; **lower is better**. The best simple fixed midpoint (0.5) reference has **RMSE 0.312146**.

| Condition | Focal own history | Recorded same-parent other-horse history | Ordinary +family RMSE | Enhanced own-history +family RMSE |
|---|---|---|---:|---:|
| **SS** | Frozen at 2021 | Frozen at 2021 | 0.320302 | 0.318075 |
| **FS** | Updated to prior calendar day | Frozen at 2021 | 0.276899 | 0.274929 |
| **SF** | Frozen at 2021 | Updated to prior calendar day | 0.318210 | 0.315925 |
| **FF** | Updated to prior calendar day | Updated to prior calendar day | **0.276427** | **0.274423** |

The no-family benchmark is determined exclusively by the own-history choice:
- Stale own-history: **0.319682** (ordinary), **0.321519** (enhanced), regardless of family-history freshness.
- Updated own-history: **0.274782** (ordinary), **0.274706** (enhanced), regardless of family-history freshness.

All updated-own-history fitted models beat the midpoint 0.312146 in this **already-inspected post-hoc sample**. Updating family alone while own history remains stale **does not** beat that midpoint (ordinary family RMSE 0.318210, enhanced 0.315925).

## Fixed-model paired comparisons, with one-way cluster sensitivity

Positive RMSE gain means improvement between the two listed conditions.

| Contrast | Ordinary +family RMSE gain | Enhanced +family RMSE gain |
|---|---:|---:|
| **Refresh own history, keep family stale (SS→FS)** | **+0.043402250** | **+0.043145547** |
| Refresh relatives, keep own stale (SS→SF) | +0.002091261 | +0.002149693 |
| Refresh relatives, **own already fresh** (FS→FF) | +0.000472459 | +0.000506616 |
| Refresh own history, family already fresh (SF→FF) | +0.041783448 | +0.041502470 |

The focal-history refresh effect is roughly **20–90 times larger** than the conditional family-history refresh effect, depending on which other factor is held fixed. These values are descriptive, conditional improvements on *one selected set* of 480 starts, not comparable to causal effect sizes or biological heritability.

For the **family refresh with already-updated own histories** (FS→FF), 399-draw one-way **horse-cluster** 95% resampling intervals are:
- Ordinary: **[+0.00012949,+0.00081878]**, with race-calendar-day interval [+0.00013346,+0.00077100].
- Enhanced: **[+0.00018118,+0.00084607]**, with race-day interval [+0.00017241,+0.00079113].

The intervals are conditional on a **post-hoc design chosen after viewing 2026 outcomes** and ignore joint two-way dependence and model selection. Do not report them as confirmatory evidence of family causal effects. The descriptive RMSE interaction (difference of differences) is +0.001618802 (ordinary), +0.001643077 (enhanced); **not a causal interaction parameter**.

## The crucial distinction: an updated family signal can still be unnecessary

Refreshing old family features to new family features modestly helps *within the same fixed family model*. But this does NOT establish that a family feature is worth including at all:

| Family-history benefit vs the corresponding NO-FAMILY model | Ordinary | Enhanced |
|---|---:|---:|
| **No refresh, SS** | −0.000620 | +0.003444 |
| **Own-only refresh, FS** | **−0.002117** | −0.000224 |
| **Family-only refresh, SF** | +0.001471 | +0.005593 |
| **Both refreshed, FF** | **−0.001644** | **+0.000283** |

The relevant deployed-type comparison is the last row, FF vs an updated own-history no-family model. In the original prior-day updated analysis, the **ordinary family increment was negative**, and the enhanced family increment +0.000283 had a 95% horse-cluster resampling interval **[−0.002333,+0.002639]**, including zero. These unfavorable incremental comparisons remain intact.

## Why selection and source timing matter

- **480/480 target starts** had at least one historic source-C own start from a prior day; **477/480** had a prior-day C result from a *different* recorded same-parent horse. This high prior-history coverage is partly **built into the historic cross-source event matching and established-runner selection**, not representative of a nationwide or newborn horse population.
- Parent history is other horses sharing an original sire or dam ID; **not** a full multigeneration pedigree A or genomic G.
- Parent-related model covariates include focal own-count attenuation 5/(5+n); the mixed-factorial algorithm reweights the family signal to match the selected own-history source before predicting. Without that correction, the factors would be accidentally entangled.
- The public later-source C has day but **not independently audited precise result-known timestamps**. The model strictly excludes all races on the target's calendar day and later; earlier-calendar-day status is not certified as already published before the bet.
- Both sources may share upstream racing websites; public record redistribution rights have not been independently verified. This is **JRA only** and limited to selected old runners through May 17, 2026.
- All original raw records and crosswalks were transient in GitHub Actions and removed before the aggregate artifact upload.

## Interpretation and next valid test

**Supported as a retrospective diagnostic:** the overwhelming model-skill gain over 2021-stale information comes from the **individual's own recent racing history**, while making relatives' information more recent offers much smaller conditional benefit. It does not show that a within-horse repeatability mechanism biologically caused the gain: source recency, historical selection, class matching and other source differences may be confounded.

**Not supported:** broad genetic effect or heritability, improved national kinship A, anonymous-sample G linked to these racers, profitable odds models, or stable future-period transfer of a parent-feature predictor. The original negative 2026 external-period result and the post-hoc updated 2026 result must both be reported.

**Next genuinely independent test:** the frozen 2027 official stable-ID + actual result-known-at-time protocol, with rolling pre-race history and M0/M1/M2 evaluated on previously unseen JRA races. The local official-ID known-on validator passed only fictional tests; actual licensed 2027 sources have **not** been acquired. Preserve the historical source hashes and avoid further retuning the already-inspected 2026 sample into a purported new holdout.

[Design and formulas](JAPAN_2026_OWN_KIN_FACTORIAL_PROTOCOL.md) | [Immutable aggregate provenance](../evidence/japan-2026-own-kin-factorial-empirical-20261117.json).
