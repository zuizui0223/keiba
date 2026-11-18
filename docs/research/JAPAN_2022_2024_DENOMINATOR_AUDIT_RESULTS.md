# 2022–2024: independently matched Race.horses denominator audit

**Actual-source post-hoc sensitivity completed.** GitHub Actions **SUCCESS** [run 43892293154](https://github.com/zuizui0223/keiba/actions/runs/43892293154), job 133386438483, analysis commit 18927911a15c2f05261b0d83c1ee0ac1dedaba27, aggregate artifact **14237611481** SHA256 **1066827e51904a7f2fbfeca81e1453aeca7636efbd744887c892d182e230b8ed**.

Source lock: original archived 2010–21 dataset SHA256 c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f; independent 1990–2025 SQLite SHA256 7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9. Source A and B individual identities were matched only with at least two distinct **pre-2022** race results. No future outcomes used for model training or horse identity decisions.

## All race denominators, not cherry-picked successful races

The full frozen cohort has **255,484** runs, **12,919** horses, **36,955** races. Source-B Race.horses (ID and actual rank) was joined in memory against the same horse ID's Horse.races (race ID, declared field, rank); no individual records exported.

| Race outcome-audit class | Races |
|---|---:|
| **All classified 1..N, N matches declared runners, no rank ties** | **35,333** |
| Consecutive classified 1..m but m < declared N (proxy) | 1,050 |
| Tied/duplicated classified ranks | 569 |
| Gapped classified ranks | 3 |
| **All audited source races** | **36,955** |

**250,920** target rows match the exact new-source horse ID and rank and qualify for either strict or proxy; **4,564** target rows belong to races with nonqualifying or ambiguous rank structure. The **STRICT_COMPLETE** subset contains **244,147** runs, **12,887** horses, **35,333** races (95.56% of full rows). No target horse-level ID mismatch survived amongst eligible race tables under this audit; ineligible races are deliberately excluded rather than zero-weighted.

## Source-complete race sensitivity, original frozen coefficients

| Same cohort | RMSE no-family | RMSE + real same-parent history | Gain |
|---|---:|---:|---:|
| All original 255,484 source entries | 0.312777516 | 0.312455062 | **+0.000322454** |
| **Strict complete 244,147 entries** | **0.313543356** | **0.313218666** | **+0.000324690** |
| Proxy classified denominator, 250,920 entries | 0.313574922 | 0.313272787 | **+0.000302135** |

The strict gain has **399-draw, single-way horse-cluster 95% sensitivity** [+0.000127967, +0.000499485], and separate **calendar-day-cluster** [+0.000186290, +0.000466786]. These are not multiway, preregistered or causal intervals.

Strict subset year-by-year:

| Year | Strict rows | Gain no-parent minus parent | Strict +parent vs fixed midpoint |
|---|---:|---:|---:|
| 2022 | 120,381 | +0.000443513 | +0.011046858 |
| 2023 | 80,939 | +0.000251174 | +0.001372146 |
| 2024 | 42,827 | +0.000110518 | **−0.002300799** |

**Important:** 2024 still loses to a fixed midpoint predictor despite a positive relative parent-history increment. The increment is small; don't inflate this to a consistently superior general racing forecast. The proxy comparison also uses a **different target definition** (rank divided by observed consecutive classified ranks), so it is deliberately labeled separately and does not certify a true official finishing denominator for races with missing runners.

## Scientific conclusion and next gate

**Supported within this selected older-horse cohort:** the earlier small direct-parent other-horse-history gain persists when evaluating **only complete, source-self-consistent** race outcomes (about 95.6% of rows). The observed positive signal is not solely an artifact of including obviously incomplete or tied ranks.

**Still unresolved:** old-source rank denominator and later-source declared field size are not fully reconciled against official racing results; the two tables are from the **same** later dataset. Parent history can encode breeding-farm, selection and management context rather than additive genetics. Nothing here establishes the full-Japan JRA/NAR studbook kinship matrix A, linkage to anonymous 370-horse genotype G, causal inheritance or a betting edge.

The next step is a **separately labeled, post-hoc** stronger no-family benchmark with strictly pretarget age/sex and recency; this sensitivity must not change the locked old models or these source-audited results.

[Aggregate source- and run-pinned evidence](../evidence/japan-2022-2024-strict-race-denominator-20261116.json); [prior methodology freeze](JAPAN_2022_2024_DENOMINATOR_AUDIT_PROTOCOL.md).
