# Why the annual intermediate-year heterogeneity peak disappears under fixed membership

2026-11-26 · Aggregate arithmetic of PR88/95 and the preceding two-stratum analysis. No new dataset, raw-data fit, inferential interval, or causal result. The original common-cohort primary remains HOLD because the zero-prior-history stratum has 54 horses (<100). The goal is to describe the numerical discrepancy, not rescue the peak hypothesis.

## Recover common-cohort moments without individual records

For groups 0/1 (zero versus positive eligible pre-2022 history), let p_j be the observed horse fraction, A_j=mean[(Y−B)d], E_j=mean[d²]>0, r_j=A_j/E_j and w_j=clip(r_j,0,1). Let A,E be pooled moments and S the archived group-specific optimum. Group 1 has an interior optimum and w_0 differs from w_1 in every archived condition. From A_1=w_1 E_1 and weighted moments,

    S = 2 w_0 A − w_0² E + (w_0−w_1)² p_1 E_1.

Recover p_1 E_1=[S−2w_0 A+w_0² E]/(w_0−w_1)²; recover remaining weighted moments by subtraction and divide by group fractions. This handles the clipped group-0 weight in 2022. Gate positive energy, interior group-1 weight and non-negligible weight difference. Validate archived common H, pooled moments, earlier-year transferred weights on both later years (separately stored scores), and fixed common group energy. Complement moments use exact count-weighted subtraction of the common subset from each annual cohort. No individual rows recovered.

## Decomposition of the annual versus common H difference

H is the gain of separately optimized bounded group weights over one optimized bounded pooled weight. Define H(p,E,r). Replace the common-cohort vectors p (group proportions), E (mean correction energy), and r (alignment per unit correction energy) with those of the full annual cohort in all six orders; average marginal changes (Shapley). This partitions the difference including interactions. The hybrids are arithmetic, not realized cohorts. r is an unconstrained scalar optimal weight, not a correlation or biological mechanism.

Primary seed 20261124, refreshed profiles, zero vs positive history:

| Year | Annual H | Common H | Annual−common | Proportion | Energy | Alignment per energy |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 0.000310924 | 0.000579785 | -0.000268861 | 0.000030712 | -0.000018622 | -0.000280952 |
| 2023 | 0.000898531 | 0.000215032 | 0.000683500 | 0.000032262 | -0.000011482 | 0.000662720 |
| 2024 | 0.000057366 | 0.000054161 | 0.000003205 | 0.000013196 | -0.000004583 | -0.000005408 |

In 2023 annual H exceeds common H by 0.000683500. The alignment-per-energy contribution is 0.000662720 (96.96% of the signed difference). No-prior-A proportions are 10.25% (common) and 10.96% (annual). All six seed/profile sequences have a positive 2023 difference dominated by alignment per energy in absolute component magnitude.

The 2022→23 annual H rise is 0.000587608; common H change -0.000364754. Their discrepancy 0.000952361 is partitioned into proportions 0.000001549, energy 0.000007139, alignment per energy 0.000943672 (99.09% of signed discrepancy).

| Seed | Profile | Annual minus common change (22→23) | Proportions | Energy | Alignment / energy | Signed alignment share |
|---|---|---:|---:|---:|---:|---:|
| 20261124 | fixed | 0.000990846 | 0.000006558 | -0.000023725 | 0.001008012 | 101.73% |
| 20261124 | refreshed | 0.000952361 | 0.000001549 | 0.000007139 | 0.000943672 | 99.09% |
| 20261125 | fixed | 0.001147988 | 0.000011682 | -0.000032523 | 0.001168828 | 101.82% |
| 20261125 | refreshed | 0.001106979 | 0.000006948 | -0.000022074 | 0.001122105 | 101.37% |
| 20261126 | fixed | 0.000979142 | -0.000000492 | -0.000028943 | 0.001008577 | 103.01% |
| 20261126 | refreshed | 0.000914849 | -0.000005966 | -0.000007011 | 0.000927826 | 101.42% |

## Within-stratum observational composition

The complement is annual horses not observed in all three eligible years, not verified retired/deceased/new horses. In 2023, primary refreshed profile:

| Group | Common n | Common r | Complement n | Complement r | Annual r |
|---|---:|---:|---:|---:|---:|
| No pre-2022 eligible history | 54 | 0.7309 | 120 | 1.1156 | 0.9934 |
| Prior eligible history | 473 | 0.4348 | 941 | 0.3818 | 0.3995 |

The annual peak is not merely a difference in the proportions of historical-count groups. Differences in conditional alignment-per-energy between observation sets dominate the arithmetic comparison. This does not identify causal membership, survival, learning or adaptation: the common restriction conditions on future observations and H is nonlinear. No new uncertainty for reconstructed moments or Shapley terms. Signed shares may exceed 100% when terms cancel. Shared sources and split sensitivities are not independent replicates.

[Numeric receipt](../evidence/information-heterogeneity-membership-mechanics-20261126.json) · [Replay](../../scripts/ecology_information_heterogeneity_membership.mjs) · [PR95 result](JAPAN_CONTEXT_TRANSITIONAL_HETEROGENEITY_RESULTS.md). 1170 arithmetic and support checks during construction; replay CI pending. Original files and main unchanged.
