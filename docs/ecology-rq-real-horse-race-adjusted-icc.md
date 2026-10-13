# Real Thoroughbred early-pace individual repeatability: exact race-adjusted Gaussian ICC

**Original-source exploratory fitted model, 2026-10-13.**
[Independent GitHub Actions run 38350388785](https://github.com/zuizui0223/keiba/actions/runs/38350388785)
recovered the first *model-based variance decomposition* of an actual
early-sectional timing outcome in the 🐎 ecology research branch.

The result **does NOT** establish H1 heterogeneous ground reaction norms,
H2 an effect of the opponents' composition, causal animal behavior,
evolved behavioral personality, genetic heritability, fitness or
a wagering-related prediction.

## Provenance and population

Original source: Racing Queensland
[Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data),
its [official Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals),
and original \`GetMeetingsForDate\` → \`GetRacesForMeeting\` →
\`GetHorsesForRace\` horse-ID SOAP records.

The parent source calendar has **12 fixed 2026 Cannon Park
meeting dates**, covering Good/Soft/Heavy ratings (actual
per-race \`TrackRating\`, not the potentially different
whole-day headline category). One date, 2026-03-12,
was retained using its *individual race ratings* when
those differed from the headline rating.

To be eligible, each horse must have a unique genuine
numeric \`HORSES\` ID linked to a single original GPS
first section with **positive segment time and signal**;
ambiguous same-day duplicate names and horse IDs in
more than one listed race are excluded. A race needs
at least four such observed GPS horses.
**Positive GPS does not prove final official starter
or finisher status; 0 GPS is NOT coded as DNF.**

| Actual-source sample | >=4 GPS horses per race | >=6 GPS horses per race |
| --- | ---: | ---: |
| Dated source records in variance fit | 523 | 436 |
| Distinct races | 74 | 55 |
| Distinct source dates | 12 | 11 |
| Distinct numeric HORSES IDs in fit | 269 | 251 |
| IDs with 2+ observational rows | 139 | 112 |
| Independent race-contrast dimensions \`sum(n_r-1)\` | 449 | 381 |

These are **observational source-linked records**, not
randomly sampled racehorses. The sample is selected on
nomination coverage, first GPS telemetry presence,
race-date availability and exact name-to-ID matches.

## Estimand and model

The **absolute first GPS interval duration in seconds**
for original horse \`i\` in race \`r\` is modeled:

~~~text
first_section_sec(i,r) = alpha(r) + b(horse_i) + epsilon(i,r)

alpha(r)               = fixed intercept for EACH REAL RACE
b(horse_i)             ~ Normal(0, sigma_horse_squared)
epsilon(i,r)           ~ Normal(0, sigma_residual_squared)
b and epsilon assumed independent across labels
~~~

Race-level fixed intercepts absorb all effects
shared by animals *in the same race*: the particular
going, course/distance, race class, shared weather,
pace conditions and other common factors. They
do **not** remove horse-specific interactions,
jockey/rider, horse weight, age, training, injury,
entry selection, preferential rider assignment,
tracker properties or heteroskedastic noise.

The *conditional individual repeatability*
point estimate is:

~~~text
ICC_race_conditional =
    sigma_horse_squared /
    (sigma_horse_squared + sigma_residual_squared)
~~~

To avoid a numerically ill-conditioned large
dummy-variable model, the actual code
[\`ecology_rq_race_fixed_icc.py\`](../scripts/ecology_rq_race_fixed_icc.py)
projects each race's \`n\` first-section times onto
an orthonormal \`n−1\`-dimensional Helmert contrast.
All race-specific means are eliminated exactly.
The restricted Gaussian covariance of the
projected data is
\`sigma_e² I + sigma_h² (QZ)(QZ)'\`, with \`Z\` the
original horse-ID incidence matrix. Its eigenvalues
enter a one-dimensional profile REML objective for
the nonnegative horse/error variance ratio.

This is not the earlier *race-relative,
leave-one-out peer mean* endpoint. Here the
**focal's original absolute segment time** is
modeled, with explicit race fixed effects and a
horse random intercept. This design is invariant
(up to numerical optimizer tolerance) if *every
horse's* time in one race is uniformly shifted.
It avoids mistaking race-shared ground/distance
changes for an individual intercept difference.

## Actual observed results

| Point estimate | >=4 positive GPS/race | >=6 positive GPS/race |
| --- | ---: | ---: |
| Horse random-intercept variance | 0.0403995 sec² | 0.0407587 sec² |
| Residual variance | 0.0531745 sec² | 0.0564144 sec² |
| **Conditional ICC: horse fraction of modeled conditional variance** | **0.431738** | **0.419445** |
| Restricted profile objective improvement vs horse variance = 0 | 63.13 | 49.72 |

The profile objective difference is **NOT
an inferential likelihood-ratio p-value**, because
a variance parameter at 0 is a boundary problem
and the data violate untested sampling and
error assumptions. Neither a validated 95%
confidence/credible interval nor a power analysis
is supplied in this pilot.

### Leave-one-original-meeting-day-out stability

Fit the >=4 GPS/race model repeatedly,
omitting all original races on **one of the
12 source dates** in turn. All 12 re-fits
returned numerical ICC estimates.

**Range = 0.390814 to 0.499262** across these
12 observational perturbations.
This is a *stability range*, **NOT** a jackknife
standard error, a 95% interval, or independent
replication at other racecourses.

## Software falsification and auditability

[\`tests/test_ecology_rq_race_fixed_icc.py\`](../tests/test_ecology_rq_race_fixed_icc.py)
checks, on **deliberately fictitious horses**:

- a planted stable horse timing intercept produces
  a positive ICC and is recoverable after race means;
- when true horse differences are removed, the
  estimator does **not** create a large spurious ICC;
- adding a 15-second common shift to all original
  horse times in one race does **not** change
  the estimated individual random variance
  beyond optimizer tolerance;
- within-race shuffled horse identities destroy
  most invented animal-specific persistence;
- insufficient repeated HORSES ID support triggers
  explicit \`HOLD\`, not a fabricated zero or
  a numerical variance;
- the >=6 positive-GPS field threshold and
  one-meeting-deletion checks remain anonymous.

The complete research GitHub Actions suite
installs pinned-version-range NumPy/SciPy and
uses one BLAS thread per CI process to make
the eigenvalue/likelihood computation reproducible.
Original horse names, IDs, raw GPS, individual
prediction histories and race-level times are
**never committed**. Only source hashes and
aggregated metrics are published.

## Interpretation boundaries, NOT supported mechanisms

**Limited ecological observation:** These
original selected records are **consistent with
repeatable individual variation in first-section
timing even after race-common influences are
conditioned out**, in a Gaussian horse-level
random-intercept model. This is stronger than
the previous descriptive within-ID time
cross-products, but depends on additional
model assumptions.

**Not yet established:** whether this variance
fraction survives proper adjustment for
the horse's jockey, carried weight, age,
trainer, time between starts, selective race
entry, preferential racing class assignment,
source GPS missingness, **date-level dependence**
and different sensor error variances across
first-section distances. The two subsets are
not independent validation cohorts. The
12-date deletion range is not reliable
uncertainty calibration.

**Not an H1 slope:** A random horse
intercept does not mean horses have distinct
Good/Soft/Heavy performance responses.
The strict same-distance/first-marker/class
cohort still has **zero horse strata with
2+ Good and 2+ non-Good observations**.

**Not H2:** This ICC does not estimate
opponent running-style composition or a
social interaction. Our earlier race-relative
timing result can mathematically change
because other horses change their timings;
the race-fixed model addresses *race-common*
effects, not the causal effect of a particular
rival composition.

**Not personality, adaptation or heritability:**
The random-intercept variance incorporates
potentially stable extrinsic circumstances
and managed training. No genetic relatedness,
heritability, survival, reproductive fitness,
natural selection or physiological trait has
been analyzed.

### Scientific next gates

1. Independently establish official final
   starters, race-specific DNF/scratch and
   animal-specific finish/section-time
   measurement semantics with authoritative
   source provenance.
2. Attach valid original jockey/rider,
   carried weight, trainer and horse-age/rest
   covariates by official internal IDs;
   separate within-individual changes in
   these from the stable animal effect.
3. Inspect heteroskedastic residuals
   across first GPS interval lengths and
   racing class; run predeclared,
   independent-date replication and
   defensible horse/date clustered uncertainty
   or simulation-based variance
   calibration, including selection sensitivity.
4. Pre-register a prospective animal
   repeatability question and its thresholds
   **before** looking at the future data.
   Keep H1/H2 genuinely separate.

Method reference:
Nakagawa & Schielzeth (2010),
*Repeatability for Gaussian and non-Gaussian data:
a practical guide for biologists*,
[DOI 10.1111/j.1469-185X.2010.00141.x](https://doi.org/10.1111/j.1469-185X.2010.00141.x).
Their review discusses adjusted ICC, variance
partitioning, valid uncertainty and the
limits of individual repeatability estimates.
The present estimate remains **exploratory**
pending those additional controls.

## Reproduce the original aggregate results

~~~bash
# Synthetic tests with no external source identities
python -m unittest discover -s tests -p 'test_ecology_rq_race_fixed_icc.py' -v

# Real fixed 12-date official source, aggregate-only
python scripts/ecology_rq_2026_calendar_overlap.py \
  --output tmp/rq-2026-calendar-with-conditional-ICC.json
~~~

Public automated execution:
[GitHub Actions 38350388785](https://github.com/zuizui0223/keiba/actions/runs/38350388785).
