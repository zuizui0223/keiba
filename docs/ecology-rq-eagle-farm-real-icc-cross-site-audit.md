# Eagle Farm: first out-of-racecourse real Thoroughbred ICC source check

**Original-source observational analysis, 2026-10-13.**
**Evidence class: explanatory / feasibility check, not an independent
confirmatory trait replication, and not H1 or H2.**

Independent first-party re-executions:
- [Eagle Farm 12-source-date model, run 38411272196](https://github.com/zuizui0223/keiba/actions/runs/38411272196);
- [Strict first-section-marker identifiability and source-complete
  adjusted ICC HOLD, run 38412012692](https://github.com/zuizui0223/keiba/actions/runs/38412012692);
- [Original Cannon Park race-adjusted ICC,
  methods and uncertainties](ecology-rq-real-horse-race-adjusted-icc.md).

Source publisher: [Racing Queensland Thoroughbred Sectionals
and Position Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and [original official RQ web service
documentation](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).
Racing Queensland's position maps derive from GPS observations and
come with an explicit informational-accuracy/reliance limitation.
No raw source animal names, HORSES IDs, licences, timings, or
individual-level predictions are written in this research repository
or public aggregate JSON artifacts.

## Design was locked BEFORE reading original Eagle Farm horse identities

Eagle Farm is a **different track from Cannon Park**, but from
the SAME operator and public GPS processing pipeline, with potentially
overlapping horse populations. See
[the dated independent-venue calendar lock](ecology-rq-eagle-farm-2026-independent-track-lock.md).

Exactly **12 specified Eagle Farm original source dates** spread
across 2026-01-03 through 2026-10-10, and official race numbers
1–6 per selected date, were locked before the new Eagle Farm
horse identities or timings were fitted. All 12 dates
returned valid official source and GPS; official race numbers missing
from the API, if any, were not guessed.

This source selection is **not preregistration of a new
scientific effect**: earlier positive Cannon Park individual
ICC and H1 insufficiency had already been seen.

## Genuine source sample, primary exploratory mixed model

| RQ Eagle Farm original-source metric | Result |
| --- | ---: |
| Original meeting dates read from RQ | **12 / 12** |
| Unique same-date same-race original HORSES-ID + positive first GPS segment candidates | **391** |
| Different official numeric HORSES IDs among those records | **339** |
| Original HORSES IDs observed at least twice on different dates | **48** |
| ID-name changes across 2026 source records, blocked | **0** |
| Races with >=4 positive GPS HORSES IDs | **51** |
| GPS HORSES-ID records in >=4-timed source race cohort | **382** |
| Different HORSES IDs in fitted race-FE cohort | **333** |
| IDs with at least 2 GPS records in fitted cohort | **45** |
| Observations in races with >=6 timed horses | **342 (42 races)** |

The same **absolute first GPS sectional time** model from
Cannon Park was applied, rather than a race-relative score:

~~~text
first_GPS_section_sec_ir =
  fixed_intercept_for_original_RQ_race(r)
  + Gaussian_random_intercept_for_original_HORSES_ID(i)
  + residual_error_ir

conditional_ICC = Var(horse_ID_intercept) /
                  (Var(horse_ID_intercept) + Var(error))
~~~

Numerics: exact orthonormal elimination of race fixed
means followed by eigenprofile Gaussian restricted likelihood
(REML); same source and hold rules as the prior Cannon Park
code. These models have **not** validated final starter
rosters, individual certified finishing times, ages,
nonrandom entries, jockey/rider or source data missingness.

| Exploratory model statistic | Eagle Farm |
| --- | ---: |
| Original race-FE conditional HORSES-ID ICC point estimate, >=4 timed GPS/race | **0.452894** |
| Sensitivity restricted to >=6 timed GPS/race | **0.441609** |
| 12 source dates, delete one original meeting at a time | **0.331549–0.563767** |
| Mean ICC after 99 within-original-race HORSES-ID label shuffles | **0.045556** |
| Horse-ID label shuffle reference 5th/median/95th percentiles | **0 / 0 / 0.228087** |

99 identity-label shuffles retain actual
racing fields and individual recorded GPS values but
reassign labels within original races. This
is an **observational negative-control reference**,
not an experimental treatment, confirmatory
p-value, age-adjusted ICC or a causal answer.
The delete-meeting range is **not a confidence interval**.

**Narrow source observation:** Under the same
race-FE Gaussian assumptions at a second track,
the original HORSES ID component was **positive
and the point estimate was above zero**, including
a stricter source GPS coverage filter. This is
consistent with nonzero source-recorded animal ID
repeatability. It is not evidence for a common
mechanism, personality, heritability, adaptation
or a social/ground interaction.

## Critical limit: the first measured GPS DISTANCE is different

This is the most important source-comparability finding.
The initial GPS segment is not the same observed animal
trait across the two independently selected tracks:

| First measured GPS marker | Cannon Park fitted source sample | Eagle Farm original positive source rows | Can estimate a matched-marker ICC at BOTH tracks? |
| --- | ---: | ---: | --- |
| 100m | 32, too few repeated IDs/races, **HOLD** | 46, **HOLD** | **NO** |
| 150m | 209, numeric ICC **0.547296** | 0 | **NO** |
| 200m | 56, too few repeated IDs/races, **HOLD** | 297 raw candidates (293 after minimum race coverage), numeric ICC **0.528346** | **NO** |
| 250m | 226, numeric ICC **0.418787** | 0 | **NO** |

The Eagle Farm original source also includes **205m,
206m, 212m, 215m, 220m and 225m** first-marker records
that the original historical Cannon marker-focused comparisons
did not test.

**Decision: \`HOLD_NO_SHARED_FIRST_SECTION_MARKER_WITH_ESTIMABLE_ICC\`.**
Although pooled Cannon Park and Eagle Farm
race-FE ICC point estimates are respectively
**0.431738 and 0.452894**, no initial GPS
marker has adequate numeric support in
*both* cohorts. Treat their numeric
proximity as source-method transferability
only, **not** verification of the same
biological early-pace trait or a universal
racehorse repeatability parameter.

The source-measurement gate is implemented
and unit-tested in
[\`ecology_rq_eagle_farm_external_icc.py\`](../scripts/ecology_rq_eagle_farm_external_icc.py).

## Source nuisance covariate attrition: adjusted ICC on HOLD

| Eagle Farm source role/weight inclusion stage | Original HORSES-ID/GPS rows |
| --- | ---: |
| Original positive-GPS ID-linked candidates | **391** |
| Original source Weight, Jockey licence and Trainer licence all present | **179** |
| Also >=4 such complete source rows in the same original race | **108** |
| Kept for the attempted adjusted ICC comparison | **27.6%** |

After the fully documented per-race fields gate,
only **21 races from 10 source dates** remain.
Completeness differs strongly by source ground:

| Race TrackRating | Original positive-GPS source rows | Retained source-complete source rows | Retained fraction |
| --- | ---: | ---: | ---: |
| Good | 97 | 31 | **32.0%** |
| Soft | 213 | 45 | **21.1%** |
| Heavy | 81 | 32 | **39.5%** |

An early software iteration could numerically
optimize a very large apparent horse ICC from
this drastically reduced and sparsely
repeated source population **even when its
baseline horse variance was not identifiable**.
Such a numeric result is **not** biological
support and is deliberately **suppressed**.

The revised
[\`ecology_rq_covariate_icc.py\`](../scripts/ecology_rq_covariate_icc.py)
requires a numerically identifiable same-source
baseline **and at least 20 repeated official
HORSES IDs plus 8 source dates** for
a nuisance-adjusted horse ICC. When a
baseline is on scientific HOLD, all heavier
adjustment results are **HOLD rather than
implicitly accepted as high ICCs**.

The independently reproduced output
[run 38412012692](https://github.com/zuizui0223/keiba/actions/runs/38412012692)
correctly suppresses all four source-complete
numeric ICC values, rather than reporting
false apparent adjusted/individual variance.

This is a **methodological safety correction**,
not evidence for lack of persistent animal
differences at Eagle Farm.

## Scientific follow-up decision

**Supported with strict limitation:** a positive
observational RQ source-ID random-intercept
signal for early GPS timing exists at two
separate tracks, under a common operator's
source and statistical model. An exploratory
horse-identity shuffle reference reduces
the modeled source-ID variance.

**Not established:**
- Same measured *first sectional distance*
  with adequate repeated IDs at both sites:
  the strict cross-site comparison remains HOLD.
- Date/horse clustered valid confidence interval,
  independent operator, replicated rider,
  age, weight/trainer/source covariate controls.
- True final official starter/finisher status,
  certified individual full-distance time,
  fitness/selection or sensor calibration.
- Heritable animal personality, any H1
  ground-response random slope, or any H2
  competitor-response/social plasticity.

**High-value next source choice:** a second
official venue with adequate repeated
HORSES IDs and the **same 150m, 200m or 250m
initial GPS marker**, or a deliberately
harmonized and independently validated
early-segment measurement. Do not add dates
to this frozen Eagle Farm cohort based on
observed ICC values; record follow-up as
separately exploratory.

### Reproduce on first-party public source, outputs aggregate-only

~~~bash
python -m unittest discover -s tests -p 'test_ecology_rq_eagle_farm_external_icc.py' -v

python scripts/ecology_rq_eagle_farm_external_icc.py \
  --output tmp/rq-eagle-farm-2026-venue-external-ICC.json
~~~

No source horse names, horse/rider/trainer licence
numbers, GPS runner rows, or individual predictions
are written to any public repo asset.


## New source-format follow-up: Doomben attempted the first-marker bridge (2026-10-14)

A **third original Racing Queensland racecourse,
Doomben**, was chosen because a *pre-lock source
format screen* had shown original 150m
and 200m initial GPS marker categories.
A fixed 19-date/6-races-per-date
cohort was committed before inspecting
animal IDs or fitted ICCs.

The [original independent
Doomben audit](ecology-rq-doomben-third-venue-original-marker-audit.md)
found **only nine** HORSES IDs
observed on separate dates at the
exact 150m marker, and **nine**
at the exact 200m marker. Despite
177 and 205 original positive
marker records, respectively, neither
cohort meets the existing >=20
repeated-ID requirement.

Therefore **the Doomben 150m
comparison with Cannon Park 150m,
and the Doomben 200m comparison
with Eagle Farm 200m, both remain HOLD**.
This result reinforces the importance
of individual repeat exposures and
measurement compatibility, not a
biological zero or site effect.
