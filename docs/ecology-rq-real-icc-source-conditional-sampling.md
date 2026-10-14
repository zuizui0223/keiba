# Two genuine Thoroughbred venues: model-conditional Gaussian ICC sampling

**2026-10-14 original-data uncertainty/sensitivity result.**
Racing Queensland public-source data, two *previously fixed*
2026 source-cohort calendars. This method was developed
**after** the positive original observational ICC values
were known; it is a post-hoc parameter-assumption sensitivity
study and NOT a preregistered confirmatory horse experiment.

[Independent two-original-racecourse GitHub Actions #38501941730](https://github.com/zuizui0223/keiba/actions/runs/38501941730)
ran both venues with no source date missing.

Code:
- [Gaussian spectral-design simulations](../scripts/ecology_rq_icc_parametric_uncertainty.py)
- [Original two-venue source audit](../scripts/ecology_rq_source_icc_uncertainty_audit.py)
- [Prior method-definition note](ecology-rq-icc-conditional-simulation-protocol.md)
- [Prior Cannon original repeatability method](ecology-rq-real-horse-race-adjusted-icc.md)
- [Prior Eagle different-track source and strict marker mismatch](ecology-rq-eagle-farm-real-icc-cross-site-audit.md)

## Original source and scope

Source: [Racing Queensland Thoroughbred Sectionals and Position
Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals),
and official numeric HORSES ID via its
[Open Data Web Services](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).

Reused the originally locked twelve 2026 Cannon Park dates and
twelve 2026 Eagle Farm dates, with exactly the same numbered
race selections and original HORSES ID name/GPS positive timing
rules. All **12/12 original dates succeeded at both courses**
in this particular rerun. Each original meeting/race/GPS source
fingerprint was written **as anonymous SHA-256 digest only**.
No raw animal IDs, animal names, rider licence IDs,
individual time results, or source XML are published.

**Source snapshot drift:** previously frozen original-source
ICC estimates were Cannon Park **0.431738** and Eagle Farm
**0.452894**. The current fresh source responses yielded
**0.430147** and **0.453332**, respectively. The modest
differences may reflect changes to original vendor historical
data or record coverage; they **cannot** be interpreted as
true biological changes. Older original HORSES-list responses
were not always fingerprinted, so exact source-row causes
cannot be identified retrospectively. The current output
retains per-date hashes to make any later drift explicit.

## What was actually simulated

Using EXACTLY the observed original race×HORSES-ID incidence
matrix after the >=4 positive first GPS measurements/race gate:

    measured original first_GPS_seconds = fixed original_race_mean
        + independent Normal(0, fitted_horse_variance)
        + independent Normal(0, fitted_residual_variance)

Race intercepts are removed with the SAME
orthonormal within-race Helmert transform
as the empirical Gaussian race-FE restricted
likelihood (REML). The algorithm re-fits the
horse/residual variance ratio to each new
simulated contrast vector; the original ICC is
independently reproduced in the reduced spectral
likelihood before simulation is authorized.

- **299** model-conditional simulated data sets using
  the real design and observed fitted variance components;
  summarize the **re-estimated ICC point-estimator**
  distribution (including possible zero-boundary fits).
- **199** *parametric zero-horse-intercept* simulations
  on the same real source incidence matrix, using
  the estimated residual variance under a Gaussian
  zero-horse-effect model. A NULL-model reference,
  **not a real randomized race-entry experiment**.
- **149** fitted-model and **99** zero-horse simulations
  within each eligible exact first-GPS distance-marker
  category. Insufficient marker strata emit HOLD, not
  spurious zero horse repeatability.

### Main results (two different source cohorts)

| Genuine original RQ source cohort | Source-derived race-FE horse ICC | Conditional Gaussian 299-draw **2.5–97.5% estimator quantiles** | Under Gaussian zero-horse model, ICC 97.5% quantile |
| --- | ---: | ---: | ---: |
| Cannon Park, 12 source dates | **0.430147** | **0.313683–0.528432** | 0.100079 |
| Eagle Farm, 12 source dates | **0.453332** | **0.166828–0.708244** | 0.335444 |

Fitted Gaussian sampling means: **0.431122**
(Cannon) and **0.455200** (Eagle).
No numerical simulation optimizations failed.

Under the artificially zero-horse Gaussian model, the
point-estimator means were **0.022401** (Cannon)
and **0.061099** (Eagle). Both source
Gaussian zero-horse references produced 0/199
re-estimates at least as large as the original
source ICC (add-one reference fraction = 1/200).
**This is emphatically NOT an empirically valid
population/ecological p-value**: it ignores actual
source missingness, trainer/jockey selection,
date clustering, timing heteroskedasticity and
nonrandom entrants.

The fitted Gaussian sampling span is visibly
wider in Eagle Farm (0.5414 ICC units)
than Cannon Park (0.2147). Eagle's source
cohort had fewer repeat-ID animals at the
original GPS interval despite similar
numbers of source records. Even assuming
the restrictive Gaussian model, the apparent
numeric similarity of 0.430 versus 0.453
is too weak to declare a common biological
population parameter. They also measure
different first-section marker mixtures.

### Original first-GPS marker strata

| Site and first GPS section marker | Original source ICC | 149-draw fitted Gaussian 2.5–97.5% estimator quantiles | Scientific gate |
| --- | ---: | ---: | --- |
| Cannon Park 150m | 0.539528 | 0.321931–0.684309 | Model conditional only |
| Cannon Park 250m | 0.418787 | 0.248634–0.600394 | Model conditional only |
| Eagle Farm 200m | 0.527731 | 0.200194–0.786889 | Model conditional only |
| Eagle Farm 100m | n/a | n/a | **HOLD: insufficient original repeated horses / race-date support** |

**No first GPS marker has an identifiable ICC
for both sites.** Therefore even these marker-
specific conditional distributions are NOT
a valid same-trait replicated effect estimate.

The earlier Doomben third-track original
source audit also found only **9** repeated
original HORSES IDs at each of its 150m
and 200m first markers: both existing
source support gates remain HOLD, even
if many one-off animal rows exist.
See the [original third-source audit](ecology-rq-doomben-third-venue-original-marker-audit.md).

## Limitations: why the quantiles are not a validated 95% CI

These percentile endpoints describe **the distribution
of a re-estimated ICC given that the initially fitted
Gaussian variance-components model is exactly true**,
conditional on the current observed race×animal
GPS-positive source design. In particular:

- **Not** a confidence interval incorporating
  model misspecification, the original source
  selection mechanism, date-clustered
  performance variation or uncertainty
  in track-specific sensor calibration.
- **Not** a parametric correction for
  unobserved GPS intervals; source registration
  and animal exit/entry may affect who
  appears in the observed design.
- **Not** adjusted for horse age, final
  actual jockey/trainer, horse welfare
  or training history. Stable horse–trainer
  pairing can masquerade as animal variance.
- Same source operator, sensor processing
  and possibly overlapping horse identities,
  NOT independent genetics or ecology.
- No correctly matched source trait at
  both tracks due different first GPS
  markers, despite two positive pooled ICCs.
- No true H1 variation of *individual
  environment slopes* and no H2 effect of
  prior rival composition is identified.
- No heritability, natural selection,
  causality, personality, adaptation,
  betting advantage or profit is inferred.
- Current question was developed after
  seeing original results; neither a
  prospective independent sample nor
  multiple-comparison controlled
  hypothesis registration.

For appropriate statistical principles,
Nakagawa & Schielzeth (2010),
[DOI 10.1111/j.1469-185X.2010.00141.x](https://doi.org/10.1111/j.1469-185X.2010.00141.x)
and Stoffel et al. (2017), rptR:
[DOI 10.1111/2041-210X.12797](https://doi.org/10.1111/2041-210X.12797),
describe estimation of repeatability and
uncertainty under mixed-effects models.
A proper uncertainty interval additionally
requires defensible model specification
and validation, which is not yet available
in the source-covered racehorse cohorts.

## Reproduce from original, attribution-preserved source

~~~bash
# Synthetic/fictional model and source-HOLD tests first
python -m unittest discover -s tests \
  -p 'test_ecology_rq_icc_parametric_uncertainty.py' -v
python -m unittest discover -s tests \
  -p 'test_ecology_rq_source_icc_uncertainty_audit.py' -v

# Re-fetch exactly pre-locked original dates from Racing Queensland
python scripts/ecology_rq_source_icc_uncertainty_audit.py \
  --venue cannon --draws 299 --null-draws 199 \
  --output tmp/rq-cannon-model-conditional-uncertainty.json
python scripts/ecology_rq_source_icc_uncertainty_audit.py \
  --venue eagle --draws 299 --null-draws 199 \
  --output tmp/rq-eagle-model-conditional-uncertainty.json
~~~

[Independent paired matrix-run with original source
hashes and anonymous aggregate-only JSON artifacts](https://github.com/zuizui0223/keiba/actions/runs/38501941730).

**Scientific decision:** the source supports **exploratory
race-conditioned animal-ID repeatability** at each
site; its strength and precision remain
model-dependent. Biological same-trait
cross-venue replication, H1/H2, valid
population CI and causal/evolutionary
interpretations remain **HOLD**.
