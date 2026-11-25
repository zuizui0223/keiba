# Information-weight boundaries and aggregation: a descriptive two-stratum analysis

2026-11-25. Derived from previously observed allocation aggregate moments (PR88) and earlier-A calibrated scores (PR87). **Not a new model fit, new dataset, forecast, confidence interval, or independent biological test.** This analysis formalizes a predictive loss boundary, not an odds threshold, animal decision threshold, or population phase transition.

## Exact identities

Let A = mean[(Y−B)d], E = mean[d²] > 0. For weight w in [0,1], gain G(w)=2wA−w²E. The unconstrained optimal scalar is r=A/E, the bounded optimum w*=clip(r,0,1). If A>0, strictly positive gain occurs for 0<w<2r within the permitted domain. If A≤0, no positive w can help in this sample. An observed sign change at w=1 can therefore occur without losing all aligned signal.

For a partition of the same evaluation horses into strata j, horse proportions p_j, moments A_j,E_j, and r_j=A_j/E_j, the pooled r equals the E-weighted average of r_j. The *unconstrained* stratified minus pooled optimum equals sum_j p_j E_j (r_j−r)^2. For the actual bounded weights subtract the extra clipping penalty:

    H = sum_j p_j E_j (r_j − r)^2
        − [sum_j p_j E_j (clip(r_j) − r_j)^2 − E(clip(r) − r)^2].

H is nonnegative by nested scalar model classes on the same data. It is the extra **sample-optimal** gain of allowing these two group-specific scalar weights rather than one common scalar; not the out-of-sample value of learning heterogeneous weights. The clipping term matters in one refreshed 2023 split. No extra fit of an unconstrained individual-level model is claimed.

## Actual aggregate calculation

Partition by presence versus absence of eligible source-A history before 2022. A horse with no eligible source-A history may gain its own history in 2022–24; this is not a contemporary cold-start or verified debut stratum. Within each seed/year/profile verify exact counts, weighted moment closure, full gain, stored optimum, clipping-corrected variance identity, and PR87 refreshed full-gain parity.

Primary split 20261124, refreshed own and donor profiles:

| Year | Horses without / with prior A | Pooled w* | Pooled boundary 2r | No prior A w* | Prior A w* | Pooled optimum | Two-stratum optimum | Extra two-stratum gain |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 334 / 2677 | 0.534 | 1.069 | 0.814 | 0.495 | 0.00812739 | 0.00843831 | 0.00031092 |
| 2023 | 174 / 1414 | 0.467 | 0.934 | 0.993 | 0.400 | 0.00551910 | 0.00641763 | 0.00089853 |
| 2024 | 100 / 643 | 0.304 | 0.608 | 0.431 | 0.285 | 0.00219631 | 0.00225368 | 0.00005737 |

In this primary calculation the two-stratum advantage peaks in 2023, then falls by 93.6% in 2024. All three seeds under both fixed and refreshed donor profiles have this ordering, with a duplicate 2022 condition. All six corresponding seed/profile sequences have a pooled boundary above one in 2022 and below one in both later years. The descriptive pattern suggests a possible transitional period when historical information depth differentiates useful weighting more strongly, followed by weaker family-signal alignment in both strata. Annual cohorts change; no causal age effect or formal temporal shape test. It is not an inferred universal hump-shaped law.

The no-prior-A group retains a higher sample-optimal scalar in all displayed conditions. Nevertheless, its 2024 full correction is negative in all three fixed-profile splits, and two of three refreshed splits; it is not guaranteed to benefit from full correction. The actual earlier-A-calibrated count gate has a positive 2024 point gain, but its primary interval includes zero. In the main 2024 refreshed comparison, this gate's gain (0.002282005) can exceed the two-stratum oracle (0.002253675), because it uses four current own-history count bins and different half-specific weights rather than these two pre-2022 groups. No contradiction or proof of generalization.

## Integration

This distinction adds a specific mathematical question to the multiscale information decoupling framework: are information sources losing residual alignment, over-weighted, or averaged across groups with different useful weights? Their effects on a common endpoint can be separated algebraically. The primary same-horse result still comes from PR88 and the direction control from PR92. This is a supplementary diagnostic, not a replacement for the prospectively testable calibration rule. The market and genomic datasets do not supply these same residual moments, and no cross-layer effect is estimated.

[Aggregate calculations](../evidence/information-weight-boundary-heterogeneity-20261125.json) · [replay script](../../scripts/ecology_information_weight_heterogeneity.mjs). Original [within-individual results](JAPAN_CONTEXT_WITHIN_INDIVIDUAL_RESULTS.md) · [calibration results](JAPAN_CONTEXT_INFORMATION_SUBSTITUTION_RESULTS.md). All 207 checks passed during construction; replay CI pending. No individual records copied.
