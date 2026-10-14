# Gaussian race-FE horse ICC: conditional source-design Monte Carlo uncertainty

**Method audit design recorded 2026-10-14, AFTER initial positive original
Cannon Park and Eagle Farm ICC values were already known.** This is a
**post-hoc model-assumption sensitivity**, NOT preregistration, a population
confidence interval, external source replication, or a new H1/H2 result.

## Question

How variable would our original *race-fixed-effect Gaussian horse
random-intercept ICC estimator* be if the observed source ID × race
membership, positive-GPS coverage, timing marker, and the two fitted
variance components were truly the data-generating process?

Under the fitted homoscedastic Gaussian model:

    first_GPS_section_seconds_{i,r} = fixed_race_intercept_r
                                    + Normal_horse_effect_i(0, s_H²)
                                    + Normal_error_{i,r}(0, s_E²)

After the same orthonormal Helmert race-mean projection used by
the existing ecology_rq_race_fixed_icc.py, the covariance is:

    Cov(z) = s_E² I + s_H² (QZ)(QZ)^T

Only the source horse×race incidence/eigenvalues, **not the original
individual times**, are used to simulate conditional Gaussian draws
in the eigenbasis. Each simulated vector is re-fitted with the
**same restricted Gaussian likelihood** and zero-horse-variance
boundary convention used by the published point estimator.

Report at least 199 seeded simulated source-design replicates (prefer
399) and quantiles of their *re-estimated ICC points*, retaining
boundary-zero estimates. The lower/upper quantiles are a **parametric
sampling distribution**, not an empirically calibrated frequentist 95%
confidence interval, because the true source-generating model,
measurement error, selection, trainer–horse pairing, rider assignment,
and original date-level dependence have not been validated.

An independent set of simulations imposes **zero** horse random
variance while preserving the identical observed source race×horse
incidence matrix. This helps detect design-induced false ICC fits
under a narrow parametric null, but the fraction of null simulated
points exceeding observed ICC is NOT a valid source-population
or ecological hypothesis-test p value.

## Source scope for this diagnostic

1. Original 2026 Cannon Park 12 dates and Eagle Farm 12 dates; no added
   meeting dates selected based on this simulation's outcome.
2. Use the original positive first GPS section times, official
   source HORSES ID crosswalk and >=4 timed-GPS horses per race.
3. Within each track, report the pooled first-GPS interval as
   **one source-conditional model**, and separate original 150m,
   200m and 250m markers when enough repeated HORSES IDs pass the
   existing numerical gate.
4. Pooled Cannon and Eagle ICCs are **not** same-measurement
   biological replication: Cannon pooled includes 150m/250m
   whereas Eagle has mostly 200m initial markers. Even if the
   model-conditional sampling distributions overlap, do not upgrade
   cross-venue biological claims.
5. Never produce confidence claims from data with too few
   recurring HORSES IDs, too few independent dates or source races.
   Return explicit HOLD.
6. Hold numeric source labels, internal HORSES IDs, horse names,
   licence numbers, original raw XML and individual sectional
   measurements *in memory only*. GitHub artifacts contain summary
   statistics and source hashes only.

## Software falsification before biological discussion

Test on **wholly artificial** races:

- positive planted horse variance recovers positive ICC
  and a finite conditional simulation distribution;
- zero true horse effect should produce mostly low/null
  fitted ICCs, not a large spurious source repeatability;
- one added race-wide constant cancels exactly under
  race fixed-intercept projection;
- an insufficient source cohort must return HOLD,
  with no fabricated 0.0 result;
- all repeated calculations with the same seed must be
  reproducible within the CI environment;
- no original or synthetic horse identifiers appear in
  returned aggregate JSON;
- original likelihood point must match the independently
  computed eigenbasis likelihood to a small numeric tolerance.

**Interpretation:** this exercise only tests estimator uncertainty
**assuming** the restrictive fitted Gaussian model were true.
It does not fix source-field missingness, repeated rider allocations,
source licence errors, differing early section distances,
time-of-year confounding, or nonrandom racehorse selection.
The evidence status for individual H1 ground-reaction slopes and
H2 competition social context remains **HOLD**.
