# Independent 2022–2024 Japanese race-rank holdout: recovered actual results (2026-11-16 audit)

**Status:** source-separated, out-of-period *association* for **family racing histories**; not pedigree (A), genomic (G), additive genetic heritability, causal genetics, betting edge, or a national JRA/NAR census. This file records an already successful action, **not a new rerun or newly tuned model**.

## Verified execution and source identity

- GitHub Actions **SUCCESS** [run #43693232874](https://github.com/zuizui0223/keiba/actions/runs/43693232874), workflow `Japan 2022+ independent SQLite horse-ID crosscheck`, head `4bbb295f01e29af445aec2d4659749b4570f4111`; job ID `132748074793`.
- Run's ZIP artifact `japan-independent-2022-sqlite-metadata-only`, ID `14153256321`, SHA256 `497eaf0ada05982ae7802c8f1d0379947eb2748d99b19824445cfacfde83ca8e`. The workflow keeps only aggregate JSON; its artifact is transient (expiry 2026-11-22), but the aggregate log and [permanent extracted numeric summary](../evidence/japan-independent-2022-2024-actual-holdout-20261115.json) identify the source.
- Source A, 2010–21: `ayuser/horse-racing-in-japan`, archived ZIP SHA256 `c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f`. Parent and stable horse IDs come only from this source.
- Source B, 1990–2025/03: `KBlueLeaf/jp-racing-horse`, SQLite SHA256 `7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9`. This source provides *outcome* data, not authenticated official pedigree IDs.
- **20,400** cross-source horse identity candidates passed exact normalized names plus at least two distinct **pre-2022** matching race dates, classified ranks and distances. The eligible 2022–24 group is much narrower: **12,919** distinct horses. No 2022+ finish was used to construct the crosswalk or train coefficients.

## Empirical performance (individual-horse-equal-weighted RMSE, lower is better)

| Holdout | Rows | No parent-history RMSE | With parent-history RMSE | Gain = no-kin minus kin | Fixed 0.5 RMSE |
|---|---:|---:|---:|---:|---:|
| **2022–24 pooled (primary)** | **255,484** | **0.312778** | **0.312455** | **+0.000322** | **0.320977** |
| 2022 | 126,031 | 0.310913 | 0.310441 | +0.000472 | 0.321527 |
| 2023 | 84,768 | 0.318433 | 0.318221 | +0.000212 | 0.319608 |
| 2024 | 44,685 | 0.319725 | 0.319656 | +0.000069 | **0.317212** |
| 2025 partial (**exploratory only**) | 6,837 | **0.315055** | 0.315415 | **−0.000360** | **0.312319** |

The primary 2022–24 improvement is `0.000322 / 0.312778 ≈ 0.103%` relative RMSE reduction, **small in magnitude**. Relative to the fixed 0.5 prediction, the pooled portable +parent-history model improves RMSE by `0.008522`, but this is not proof of added family-history value; the **correct incremental comparator is the matched no-parent-history model**. By 2024, both trained models were worse than 0.5; do not call the kin model a universally useful prediction rule. In 2025 partial data, the family-history feature set deteriorated.

The run's **399-draw single-way** bootstrap for the primary gain yielded:
- horse-identity clusters: `+0.0001170 to +0.0005079` (12,919 clusters);
- race-calendar-day clusters: `+0.0001889 to +0.0004595` (1,067 clusters).

Both intervals exclude zero **conditional on this model, link rule and sample**. They are not multiway clusters, post-selection corrected intervals, a heritability estimate, or evidence of genetic causality.

The run's identity gate reported **262,343** raw linked 2022–25 history rows. The eligible scored counts sum to **262,321** (22 excluded). The 2025 series is incomplete through March 27 and does not contribute to the primary result. Source row counts do not imply the same denominator across years or full JRA/NAR coverage.

## What was frozen vs. what was not

Code `scripts/ecology_japan_2022_independent_forward.py` fitted equal-horse-weighted ridge models on source A only, with target years 2018–21 each using earlier-year history. Ridge alpha 100; same focal past-performance, turf/dirt, distance and context predictors in both models. The additional model receives direct **sire/dam-sharing other-horse race histories**, excluding the focal horse. Those are not full multigeneration relatedness coefficients; relationship strength within a family is not estimated.

Old-source ranked outcomes are relative to **classified finishers in complete untied races**; source B's target rank uses `Horse.races[7]` declared field size. The historical 2019–21 results were already inspected when this portable modeling specification was built, so the 2022–24 check is **retrospective out-of-period**, not prospective preregistration. The source datasets may share upstream websites. The source-B horse ID match is historical-event corroboration, *not official registry identity*. The selected cohort is older previously active survivors; **new 2022+ debutants are excluded**. Model histories are frozen through 2021 (no rolling refresh). The original archive's redistribution rights are unknown; the HF dataset's Apache-2.0 label does **not** independently certify the source racing records' rights. Raw records, names and horse-level predictions were not uploaded.

## Decision and next falsification

1. Preserve the actual pooled positive **small effect**, while explicitly reporting year-wise attenuation and 2025 reversal. Do not overwrite the earlier PR46 draft's source-audit HOLD history; distinguish the initial schema error from this later successful run.
2. Add a **separate, labeled post-hoc robustness analysis** if resources permit: same source/held-out rows, within-birth-cohort parent-ID permutations that retain pedigree missingness, and a strong no-parent baseline with comparable available features. This should not change the frozen published values.
3. For nationally comprehensive genetic relatedness and true pre-race prediction, require permitted official JRA/NAR registry IDs, multi-generation sire/dam records, dated racing records and independent validation. The 5,878-horse Wikipedia pedigree (A), 370 anonymous genomic samples (G), and 12,919-horse parent-history prediction **must not be silently joined by horse name**.

**Interpretation:** family members' earlier observable performance contains a modest, time-decaying predictive signal *in this selected cohort*. It does not establish an inherited performance mechanism or a profitable market strategy.
