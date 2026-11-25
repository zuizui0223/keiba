# Family-associated observed environment occupancy vs paired performance transfer

2026-11-24. Follow-up to PR80, frozen before seeing the new exposure scores. The alternative explanation for recurring sire × context differences is structured exposure: families may be preferentially entered in different environments, while individual response to an environment switch is much less portable. We test occupancy as a separate observed outcome, not genetically caused preference or a mediation estimate.

## Cohort and primary contrast

Use exact source A and original 2,092,836 starts / 90,962 horse parity; JRA turf/dirt 1600–1999m 2019–21 candidate 57,208 starts / 15,129 horses. Require recorded sire. Verify the no-date-thinning paired-surface count (3,031 horse-years) from PR80. Define occupancy per horse-year as the fraction of observed eligible starts on turf. Include turf-only, dirt-only, and dual-surface horses. Conditional on at least one eligible observed start; not prediction of race entry or an experimental choice.

At the start of each target year, compute an own-history turf fraction from all earlier eligible years, shrunk toward the horse-half-specific horse-equal population mean with fixed 5 pseudo-starts. Zero previous starts use the population prior. Sensitivity: replace that prior by last known historical trainer's equal-other-horse turf fraction, shrunk by 8 toward the population prior; subtract the focal horse and never use the target-year trainer to construct features. The current target fraction and count do not enter these baselines. Shared pre-year baseline records are not a fully independent external data source.

Use original PR80 horse-disjoint cross-fit and count-matched other-sire controls unchanged on the occupancy residual (observed minus baseline). M0 adds the earlier-year opposite-half global residual mean; M1 adds the earlier-year same-sire mean shrunk with n/(n+8) if >=3 unique training peers, otherwise fallback M0. P substitutes matched other-sire mean with same recipient shrinkage. All known-sire target horse-years scored, including fallback; match comparison on same matched subset. Score linear residual MSE, not a calibrated probability (adding back the offset gives identical squared error).

Primary: 2021, ordinary horse disjoint, seed 20261124, own-history baseline, all targets, MSE(M0)-MSE(M1). Other years/seeds and trainer-disjoint row-retained samples and last-trainer baseline are sensitivity. Pointwise whole-sire bootstrap with >=30 sires as PR80. These reuse the same source. Retain all negative and HOLD results. Report occupancy counts and prior support. Trainer-disjoint filtering changes the observed start fraction, so not an identical target population. If primary effect positive but sensitivities fail, interpret cautiously.

Compare conclusions with PR80 paired rank response, not raw MSE magnitudes (different targets and support). A positive exposure transfer and weak paired performance transfer would be consistent with structured environment assignment, not demonstrate that assignment explains PR78 or is causal. No new independent data, no genetic effect, no market or wagering claim.

[Code](../../scripts/ecology_japan_sire_context_exposure_transfer.py) · [Workflow](../../.github/workflows/ecology-japan-sire-context-exposure-transfer.yml).
