# When does individual history predict early pacing? Context-limited temporal consistency in source-identified Thoroughbreds

**Manuscript draft v1 — 15 October 2026. NOT SUBMITTED.**
Evidence is original-source observational and source-version dependent.
No title/abstract wording here licenses statements about intrinsic animal
personality, genetics, causal jockey effects, H1 or H2. This manuscript
explicitly retains a nonconfirming year-forward result.

## Abstract

Repeated individual differences in animal behaviour can predict future
phenotypes, yet the predictive value of individual identity may depend on
time, sampling and behavioural context. We examined source-identified
Thoroughbreds using historical public racing and first-GPS-sectional
records from Racing Queensland. We distinguished three questions:
whether horse identity was associated with repeatable early timing;
whether the horse's prior measurements improved chronological prediction
within a racecourse; and whether this advantage persisted when an earlier
calendar year was used to predict the next year at another racecourse.
In a fixed Cannon Park 2026 cohort, a race-fixed Gaussian model yielded
a horse-ID conditional intraclass correlation of approximately 0.43.
Among 36 horses and 46 subsequently observed, context-matched records
with a source-documented rider not previously recorded for that horse,
the focal horse's strictly earlier race-relative first-GPS time history
reduced equal-horse-weighted root-mean-square error (RMSE) to 0.256 s
compared with 0.298 s for an unpersonalized zero-relative-time baseline
and 0.303 s for an identically matched earlier history of other horses.
Conversely, using fixed 2025 Doomben histories to predict 2026
same-HORSES-ID early timing did not reproduce this advantage. For
26 horses and 27 scored 2026 records at the 150-m initial marker
and an identical official race distance, own-horse history RMSE
was 0.386 s, versus 0.369 s for the historical other-horse
reference. In post-hoc influence checks, removing one horse
or 2026 source date reversed the sign in one of 26 and one
of 10 comparisons, respectively. Source class, participating
animals, timing contexts and data availability differ across
the evaluations; four locked Doomben source dates were unavailable,
and matching Class left only six animals. Thus these findings show
*within-source individual-history predictability alongside limited
transfer between distinct observed cohorts*, not a causal decline
in behavioural stability with age or season. A distinction between
observational individual signatures and their external generalization
is essential before inferring stable intrinsic personality.

**Keywords:** repeatability; individual variation; behavioural ecology;
longitudinal prediction; telemetry; horse; measurement selection;
external validation.

## 1. Introduction

Consistent differences among individuals are a central subject of
behavioural ecology, but the biological meaning of repeatability
depends on what has been repeatedly measured, which individuals
were sampled and which shared contexts are statistically controlled.
Bell, Hankison & Laskowski (2009) synthesized behavioural
repeatability across empirical studies, while Dingemanse &
Dochtermann (2013) outlined how mixed-effects models distinguish
between-individual intercept variation from within-individual and
environment-dependent variation. Nakagawa & Schielzeth (2010)
and Stoffel et al. (2017) likewise emphasize measurement- and
model-specific repeatability estimates. These principles caution
against treating an estimated individual intercept as a mechanism,
such as genetically based temperament or behavioural plasticity.

An alternative and practically testable question is whether the
information attached to an individual identity adds predictive
value to a genuinely later behavioural observation, after
considering the historical information available from other
individuals in a comparable environment. A predictor can
be source-conditionally useful even when the underlying
between-individual variance remains confounded with shared
training, selective participation or imperfect measurement.
Moreover, within-cohort predictability need not transfer to
a different year or racing cohort, even when an individual
identifier is preserved.

Historical Thoroughbred racing records offer repeated numerical
identifiers, dated competitions, initial GPS measurements and
heterogeneous track conditions. They are also an unusually
nonrandom observational system. Race entry, horse training,
rider assignments and sensor coverage can all select which
individuals have observable outcomes. The first GPS interval
is a performance endpoint rather than an experimentally isolated
behavioural decision; a contemporaneous race-relative contrast
depends mechanically on the horses with recorded telemetry.
The dataset therefore provides a useful, but restricted,
setting to study *individual-associated prediction*.

We asked three progressively stricter questions. First, is
early sectional timing associated with the same source horse
identifier across source-recorded races? Second, within a
fixed racecourse-year cohort, does an earlier individual
history improve prediction of later race-relative early
timing versus zero and context-/rider-/trainer-matched
histories from other horses? Third, does a horse's preceding
year's matched history outperform other horses' histories
when the next year's source records are held out in full?
We deliberately retain both favorable and unfavorable
results and avoid claiming that the third analysis identifies
temporal biological change, because the contrasts are not a
factorial experiment separating site, year and source Class.

## 2. Materials and methods

### 2.1. Original sources and locked cohorts

The data source was Racing Queensland's public Thoroughbred
Sectionals and Open Data Web Services. Original dated
GPS first-interval records were linked in memory to numeric
HORSES identifiers returned by the original public race
roster operation. A join was permitted only with a unique
normalized name within the same officially identified
race; ambiguous source identities and all-zero/invalid
sectional durations were discarded rather than interpreted
as confirmed nonstarters or did-not-finish outcomes.

Cannon Park: twelve previously fixed 2026 meeting dates,
official races 1–8 as available. A refreshed complete
12-date source snapshot contained 543 numeric-HORSES-ID /
positive first-GPS candidate rows; 519 observations
were retained in 74 original races with at least
four positively timed GPS horses. Numeric source
Jockey/@Id was documented for 378 of these observations.
The source is NOT the 548-candidate historical snapshot;
their five-record discrepancy is addressed below.

Doomben: a separately fixed 23-date 2025 cohort and
19-date 2026 cohort, original races 1–6. Original SOAP
race or roster data could be linked on 38 of the 42
locked dates. Four dates were unavailable: 22 January,
28 May and 27 August 2025, and 26 August 2026.
They remained source-HOLD and were not replaced,
imputed or treated as absent horses. These
source cohorts were selected for retrospective
original-source feasibility, not random or
representative racehorse sampling.

### 2.2. Two related but different responses

For the race-conditional ICC analysis, we used the
**absolute elapsed duration in seconds to the original
first positive GPS sectional marker** for focal horse
i in official race r:

    y_ir = alpha_r + b_i + epsilon_ir

where alpha_r is an unrestricted fixed race intercept,
b_i is a Gaussian random intercept associated with
the source numeric horse identifier, and epsilon_ir
is Gaussian residual error. A Helmert projection
removed each race intercept and the variance
components were estimated by a restricted-likelihood
profile. The conditional model ICC is

    Var(b_i) / [Var(b_i) + Var(epsilon_ir)] .

This conditional ratio is an **observational model-based
variance partition**, not heritability or intrinsic
personality. Marker-specific subgroup ICCs were held
unless at least 20 original horse IDs had repeated
recordings and the existing races/dates gates were met.

For longitudinal prediction, the distinct response was
**race-relative early sectional timing**, constructed
among the positively GPS-observed runners:

    d_ir = y_ir - mean_{j != i, observed in race r}(y_jr).

A negative value corresponds to a shorter first GPS
interval than the other observed GPS runners in that race.
The peer reference is not the complete verified field
of actual starters and may vary with source availability.
This endpoint can therefore shift because *other
measured horses* change, independently of any focal
horse's absolute pace. Consequently, it cannot
identify H2 social interaction.

### 2.3. Strictly earlier histories and comparative benchmarks

Historical prediction used only observations dated
strictly earlier than each scored Cannon Park date.
For a focal horse, historical records had to match the
official race distance and first GPS measurement marker.
The predictor was a source-historical mean `m_i`,
shrunk deterministically to `n/(n+2) * m_i`
where n is the number of prior records within that
identical context. The shrinkage was reused from an
existing historical method, not optimized on the
future outcomes.

The primary Cannon scored cohort required at least
one prior context-matched observation with a
valid source Jockey/@Id, and a current Jockey/@Id
not documented in that horse's earlier context-matched
source records. Incomplete prior licence fields
mean that this is a difference in *documented*
source riders, not proof of a newly assigned actual
jockey or an experimental rider switch.

Benchmarks used on identical future observations
were (i) a no-individual-history prediction of zero
relative seconds; (ii) the fixed-shrinkage prior
relative timing average of OTHER original horse IDs
under the same official distance and GPS marker,
explicitly excluding all focal-horse rows; and
(iii) in smaller paired eligibility sets, OTHER
horses sharing the current source-documented
trainer or jockey under the same measurement context.
Each paired result used the same future observations
for its own versus comparator models.

The principal error measure was RMSE weighted
**equally across scored original horse IDs**:
the average of each horse's mean squared future
error was square-rooted. This avoids giving more
weight solely to horses with many scored future
records. Other summaries of MAE or row-weighted
RMSE are descriptive. Minimum numerical support
required 20 different horse IDs, 20 scored future
records, six future source dates and 20 matched
horse-by-measurement contexts; otherwise numeric
gains were suppressed as HOLD.

### 2.4. Year-forward Doomben evaluation

We evaluated 2025 Doomben history against 2026
Doomben positive-GPS records without updating any
horse profile with 2026 observations, even if the
same original horse ID reappeared several times
in the evaluation year. All candidates needed
the same numeric HORSES ID, identical first-GPS
marker (150 or 200 m) and exact original
official race distance across years. Historical
other-horse comparison required at least three
distinct alternative HORSES IDs at the same
marker/distance, excluding the focal entirely.
An exact source Class match was a separate
pre-scoring sensitivity.

Before inspecting these year-forward errors, a
minimum of 20 original IDs with matched history
and evaluation records, 20 scored 2026 outcomes
and three dates per year was fixed. The comparison
was not selected to maximize apparent differences.
The protocol was developed after earlier favorable
Cannon and pooled Doomben ICC outcomes, and is
therefore retrospective/post-hoc, not preregistered.

### 2.5. Influence, source-edition and privacy checks

For Cannon changed-source-jockey pair products,
single original meeting dates and single original
horse IDs were removed in turn. For the
year-forward Doomben 150-m comparison, the
source scoring pipeline performed 26 single-horse
deletions and 10 single-2026-source-date deletions,
with the same fixed support gate applied to
each re-fit. The resulting ranges describe
*influence*, not 95% confidence intervals.

Original vendor data can change between historical
fetches. The Cannon October 13 snapshot contained
548 original positive GPS/HORSES-ID joins, but the
October 14 snapshot contained 543. Each of five
dates differed by one join; original meeting XML,
race XML and GPS CSV SHA256 fingerprints matched
for all 12 dates. Earlier HORSES-roster XML
response digests were not preserved, and code
also changed, so the precise cause is unidentified.
The later 543-candidate edition was subsequently
independently replayed for all 12 dates,
matching four source response digest groups
and per-date candidate counts.

All individual horse names, original horse IDs,
jockey/trainer licence IDs, horse-specific
times/predictions and raw XML remained in memory;
published materials include only code, synthetic
unit tests, aggregate values and source digests.
Publisher reuse/attribution terms must be
reviewed before submission or derived-data release.

## 3. Results

### 3.1. Source-conditional horse-ID repeatability

In the most recent model-conditional Cannon
source snapshot, the race-fixed horse-ID
Gaussian ICC was 0.430147.
On 299 re-simulated data sets generated
under the fitted Gaussian source incidence
and variance components, 2.5–97.5% percentiles
of re-estimated conditional ICCs were
0.313683–0.528432. These are model-conditional
estimator distributions, NOT validated
population confidence intervals.

An independent Eagle Farm source-date cohort
produced a pooled race-conditional ICC
of 0.453332 with corresponding fitted Gaussian
re-estimated percentiles of 0.166828–0.708244.
This does NOT replicate the same trait:
the supported Cannon original GPS marker
subgroups predominantly used 150/250 m,
whereas Eagle Farm's estimable subgroup
primarily used 200 m. The prelocked
2026 Doomben 150/200-m subsets each had
only nine distinct-date repeated HORSES
IDs and did not satisfy the per-marker
model gate.

In Doomben source data spanning 2025 and
2026, a pooled initial 150-m marker ICC
also shifted from a fitted 2025-only
0.653589 to a combined-year 0.180116.
This comparison includes different
horses and observed race contexts and
cannot quantify within-horse aging
or a within-individual shift.

### 3.2. Within-cohort evidence of individual-associated temporal consistency

The Cannon changed-source-jockey analysis
included 36 horse IDs, 38 identical
distance/marker strata and 72
different-date pairs, with an
equal-stratum mean pair product
of +0.063583 s². Its value stayed
positive after all 12 single-meeting
deletions (+0.045540 to +0.080127 s²)
and all 36 anonymous single-horse
deletions (+0.049043 to +0.067635 s²).
These are not independent date/horse
replications and were evaluated
post hoc.

In the chronological prediction
analysis of 36 horse IDs and 46 later
source observations, the equal-horse
RMSE fell from 0.297676 s (zero
reference) to 0.255809 s
(shrunk horse-specific history).
The other-horse matched-context
history RMSE was 0.303195 s,
making the focal horse's
history 0.047386 s better in
this selected future cohort.
Among 23 horse IDs/31 later records
with an alternative same-source-trainer
other-horse history, the matched
own-history and other-history
RMSEs were 0.223217 and 0.293963 s.
For a separate 32-ID/39-record
same-source-jockey benchmark,
the analogous errors were
0.246934 and 0.301783 s.
These subset differences do
not estimate rider or trainer
causation; the cohorts are not
identical across benchmark types.

### 3.3. Non-transfer in a year-forward matched-individual source cohort

For Doomben 2025 histories matched
to original 2026 observations
at the 150-m first GPS marker
and identical official race
distance, 26 HORSES IDs generated
27 scored 2026 positive-GPS
rows. On these same 2026
observations, RMSE from the
individual 2025 history was
**0.386131 s**, larger than
the other-horse 2025 history
**0.368906 s** and zero
reference **0.368844 s**.
Thus the fixed own-horse
history did NOT improve
prediction in this cohort
(OTHER minus OWN = **−0.017225 s**).
The source-Class-matched
150-m analysis had only six
IDs/six observations and
was held as insufficient,
as were 200-m cohorts
(13 IDs/14 records without
Class, three IDs/three
records with Class).

In 26 leave-one-horse
analyses, other-horse
history remained better
in **25**, whereas the
focal history became
better in **one**
(range of OTHER−OWN
RMSE across deletions
−0.027772 to +0.007524 s).
Among ten leave-one-2026-date
analyses, other-horse
history remained better
in **nine**, and focal
history became better
in **one**
(range −0.031433 to
+0.014650 s).
These ranges include
a sign reversal and must
not be mistaken for a
confidence interval or
proof of consistent failure.
Four previously fixed source
dates could not be retrieved.

## 4. Discussion

### 4.1. Predictive individuality is a conditional property of the observed system

The primary empirical result is
that individual identity carried
useful information for *later*
race-relative early pacing
within one 2026 Cannon Park
source cohort. The result was
not limited to simple random
reassignment of horse identities,
and alternative historical
context- and role-matched
benchmarks did not reproduce
the same prediction accuracy
on their scored observations.
Nevertheless, animal identity
in an observational racing
system bundles stable training
history, selection into race
classes, physiology, underlying
ability, GPS measurement
properties and possibly
actual rider assignment.
A horse-ID signal is therefore
not synonymous with
innate personality.

### 4.2. Cross-year failure constrains the scope of the claim, not the mechanism

A stronger hypothesis might
state that historical source
individual identity predicts
relative early pacing robustly
across calendar years and
study contexts. In the
observed Doomben 2025→2026
evaluation, the fixed
horse-specific history
did not outperform other
source horses or zero.
This challenges that stronger
claim and should be reported
alongside the positive
Cannon observation, even
though the Doomben effect
is small and sensitive to
one animal/date deletion.

However, **the comparison does
not identify a temporal
decay parameter**.
The Cannon test updates
horse profiles using earlier
dates within 2026; Doomben
freezes all profiles at
2025, changes course and
observed animal/context
composition, permits
source Class changes and
has upstream unavailable
dates. All these dimensions
differ simultaneously.
Even at the same 150-m
GPS marker and race distance,
shared-class matched
year-forward animal
replication was only six.
It would thus be unjustified
to conclude that individual
personality vanished, that
year-to-year plasticity
increased or that season,
training, age or ground
caused the difference.

This pattern instead
separates two ecological
questions: does stable
identity improve
prediction *somewhere*,
and under what sampling
and environmental
conditions is that
predictability transferable?
The first currently
has bounded affirmative
source-conditional evidence;
the second remains unresolved
mechanistically.

### 4.3. Measurement selection and incomplete exposure histories matter

Only GPS-positive,
name-linked source
records enter the
timing analysis. The
selection process can
depend on race distance,
track, source publication,
sensor function, actual
starts, trainer, class
and condition.
Rider identifiers are
incomplete and are
not confirmed final
race-rider assignments.
Temporal measurement
availability and race
entry are not randomized;
missing GPS records
cannot be coded as
zero pace or nonfinishers.

Moreover, an absolute
first sectional time
and a race-relative
first sectional deviation
have different estimands.
The latter is a contrast
to the measured peer
subset: rival composition
affects the reference
mechanically. It is
therefore particularly
important not to
reinterpret this
association as a
causal social-response
parameter.

### 4.4. What a decisive next ecological test would need

A stronger study would
sample confirmed actual
starters in a new,
independently source-fixed
cohort with age,
verified final rider
and trainer assignment,
regular calibrated
sensor observations,
and genuine repeated
same-horse exposures
within fixed distance/
GPS marker and Class
across source years.
Testing environmental
reaction norms would
add repeated horse
measurements across
distinct ground
conditions, ideally
at least two repeated
exposures under each
condition before any
random-slope inference.
A competition-context
analysis would need
observed opponent
identities and an
absolute focal
performance endpoint
with an explicit
selection/missingness
model.

A prospective
study should report
its complete original
data-inclusion flow,
both positive and
negative model scores,
and date-/animal-
clustered uncertainty,
rather than
repeatedly selecting
calendar windows
with favorable estimates.

## 5. Conclusion

Source-linked Thoroughbreds
displayed within-cohort
individual-history
predictability of
race-relative early
GPS timing in one
fixed racecourse-year,
but a separate
matched-identity
year-forward cohort
did not show
a generalizable
advantage of each
horse's earlier
year's record.
The contrast
cautions against
conflating observed
individual-associated
repeatability with
stable, transferable
intrinsic personality.
Causal ecology of
ground reactions,
social competition
and heritability
remain untested.

## Figure captions and source-backed display

**Figure 1. Conditional advantage and non-transfer of individual
pacing history in different source cohorts.** RMSE (seconds) is
weighted equally across source-identified horse IDs and is
calculated on identical scored future records *within* each
panel. Panel A: historical source Cannon Park 2026 earlier dates
to later dates, 36 original horse IDs/46 future observations.
Panel B: Doomben fixed 2025 original histories predicting 2026
positive-GPS observations, 26 original horse IDs/27 future
observations. Lower RMSE indicates more accurate prediction
of the focal horse's race-relative first-GPS duration
for the specified source-conditional target. No source
Class or genuine rider/horse annual effect was randomized;
the panels differ in course, timing window, population
and source observation availability. Their RMSE
difference does **not** identify a causal year, age
or context effect. In Doomben, Class-matching allowed
only six shared horse IDs and four previously locked
source dates were unavailable. Figure provenance:
[generated figure CI and SVG artifact](https://github.com/zuizui0223/keiba/actions/runs/38679488650);
[anonymized pinned evidence](evidence/rq-racehorse-temporal-generalization-20261015.json);
[deterministic figure generator](../scripts/ecology_rq_manuscript_temporal_figure.py).

**Figure 2, planned:** historical source provenance
and missingness/eligibility flow for the 543-current vs
548-older original Cannon candidate matches and Doomben
38/42 successfully sourced dates. Do not imply a
biological disappearance of source records.

**Figure 3, planned:** within-Cannon positive source-date
and horse-ID deletion ranges versus Doomben
year-forward influence checks. Graph as sensitivity
ranges, **never** 95% confidence intervals.

## References

Bell AM, Hankison SJ, Laskowski KL (2009).
The repeatability of behaviour: a meta-analysis.
*Animal Behaviour* 77:771–783.
https://doi.org/10.1016/j.anbehav.2008.12.022

Dingemanse NJ, Dochtermann NA (2013).
Quantifying individual variation in behaviour:
mixed-effect modelling approaches.
*Journal of Animal Ecology* 82:39–54.
https://doi.org/10.1111/1365-2656.12013

Nakagawa S, Schielzeth H (2010).
Repeatability for Gaussian and non-Gaussian data:
a practical guide for biologists.
*Biological Reviews* 85:935–956.
https://doi.org/10.1111/j.1469-185X.2010.00141.x

Stoffel MA, Nakagawa S, Schielzeth H (2017).
rptR: repeatability estimation and variance
decomposition by generalized linear
mixed-effects models.
*Methods in Ecology and Evolution* 8:1639–1644.
https://doi.org/10.1111/2041-210X.12797

Racing Queensland. Thoroughbred Sectionals
and Position Maps / Open Data Web Services
(original first-party sources,
accessed for original frozen
date cohorts in 2026).
https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals
https://www.racingqueensland.com.au/rq-open-data-web-services.pdf

## Reproducibility and claim-audit materials

- docs/ecology-racehorse-individuality-manuscript-outline.md
- docs/ecology-rq-rider-change-forward-validation-results.md
- docs/ecology-rq-forward-other-horse-comparator-results.md
- docs/ecology-rq-doomben-2025-to-2026-year-forward-results.md
- docs/ecology-rq-doomben-cross-year-own-vs-other-history-lock.md
- docs/ecology-rq-cannon-original-source-drift-20261014.md
- docs/ecology-rq-real-icc-source-conditional-sampling.md
- GitHub Actions original source execution 38563275612
- GitHub Actions year-forward source execution 38678720302

**Manuscript status:** coherent full first draft,
not approved for journal submission.
Required: complete rights check,
verifiable independent source data,
appropriately qualified uncertainty,
and author/affiliation/contribution review.
