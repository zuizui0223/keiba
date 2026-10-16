# When does individual history predict early pacing? Context-limited temporal consistency in source-identified Thoroughbreds

**Manuscript draft v1 — 15 October 2026. NOT SUBMITTED.**
Evidence is original-source observational and source-version dependent.
No title/abstract wording here licenses statements about intrinsic animal
personality, genetics, causal jockey effects, H1 or H2. This manuscript
explicitly retains a nonconfirming year-forward result.

## Abstract

Repeatable individual differences can predict future animal performance,
but the portability of individual historical signatures may depend on
observational context, elapsed time and source completeness. We
reconciled original Racing Queensland horse identifiers with positive
initial GPS sectional timings and compared strictly earlier focal-horse
histories to historical profiles of other horses with the same first-GPS
measurement marker and official race distance. Within a fixed
Cannon Park 2026 cohort, the own-horse history reduced equally
horse-weighted later race-relative time prediction RMSE to 0.256 s,
versus 0.303 s for other horses' context-matched history, across
36 horses and 46 later observations. Within Doomben 2025, two
re-fetches of 38/42 originally fixed dates gave identical aggregate
scores for 23 horses and 24 subsequent observations at the 150-m
first GPS marker: own-history RMSE was 0.211 s versus 0.241 s
for other-horse history. However, alternative original-source
re-fetches obtained different meeting dates, reducing the
eligible sample to 21 or 17 horses and causing one run to
fail the predeclared minimum support threshold. Moreover,
fixed Doomben 2025 horse histories did not outperform
other horses' histories in 2026, with RMSE 0.386 s versus
0.369 s in 26 matched horses and 27 later recordings.
The latter result changed sign under one individual/date
deletion, while a common source-Class requirement retained
only six horses. An independently checked original source ID/date audit
subsequently found **zero horses** with at least two
distinct observed dates in 2025 AND at least one
observed date in 2026 at the same 150-m initial
GPS marker and race distance: the 23 within-2025
and 26 year-forward scored horses were disjoint.
The contrasts therefore cannot identify
time-decay, aging, intrinsic personality,
H1 environment response or H2 social mechanism. Horse-ID-associated
historical performance can be predictively useful within
a selected source context, but its transfer and even
numerical estimability depend on observational support.

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

Racing Queensland's official Open Data Web Services
Protocol & Interface Specification (v1.0,
sections 4.15–4.16, printed pp. 27–28)
describes GetHorsesForRace and GetHorseDetailsInRace
responses as a horse ID and name, source Weight,
assigned Jockey/@Id and Trainer/@Id, with
no structured final verified starter flag,
actual postrace rider-change record, certified
focal finish time or positive-GPS measurement
denominator in these TWO SOAP schemas.
Other first-party products MAY supply results,
scratchings and jockey changes but were not
independently reconciled in this analysis.
Thus the source assigned-Jockey identifiers
used here are not a validated intervention
on actual jockey identity. See
[source-schema validation and provenance
boundary](ecology-rq-official-soap-vs-final-starters-jockey-data-scope.md).

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

### 2.6. Additional same-Doomben within-year and source-availability test

To reduce the contrast between different
racecourses, we carried out a further
**post-hoc, pre-score-locked** comparison
separately inside original Doomben 2025
and 2026 source-date cohorts.
No previously fixed dates, races,
150/200-m initial marker or official
race distance was changed. Each
individual's historical mean used only
earlier source dates in the SAME
calendar year, and other-horse
histories excluded the focal HORSES ID.
The n/(n+2) shrinkage and equal-horse
RMSE were unchanged. The new
numeric support gate required at least
20 distinct original HORSES IDs,
20 scored later records, six
different later source dates and
20 horse-by-context strata; a
Class-matched secondary check was
also fixed in advance.

Two read-only GitHub Actions reran
all 23 fixed 2025 dates and 19
fixed 2026 dates independently.
We then compared their *previously
archived anonymous aggregate outputs*
rather than selecting the most
favorable source retrieval.
Across dates successfully downloaded
in both runs, original meeting,
race, GPS and HORSES-roster
SHA256 digests, official race counts
and GPS-ID join counts were
required to match exactly.
Missing source dates remained HOLD.
A numeric estimate passing
the cutoff in only one original
source replay could not be
treated as replicated support.
This checks source availability,
not an experimentally randomized
source-missingness mechanism.

### 2.7. Same-individual temporal support gate

An additional pre-scoring-locked but explicitly
post-hoc audit used the same 42 original Doomben
dates to ask whether **the same horse and exact
150-m marker/distance** was scored in BOTH the
within-2025 and 2025-trained/2026-heldout
predictive evaluation. A separate, outcome-blind
method used only the original HORSES ID and
source observation dates, marker, distance and
optional Class; no GPS outcome value was
accessed for its incidence calculations.
The predeclared gate required at least
20 shared original horse IDs and
20 scored observations in each horizon,
plus sufficient separate meeting dates.
An absent matched population returns HOLD,
not an estimated temporal effect.
[Methods/source provenance](ecology-rq-doomben-matched-individual-timescale-overlap-lock.md).

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

### 3.4. Same-venue within-year Doomben history, and its source-availability limits

A supplementary analysis reused
the exactly prelocked Doomben
2025/2026 date cohorts and
150-m/200-m initial GPS markers.
Within each year separately,
only strictly earlier dates
trained source-identified horse
or other-horse histories under
the same original marker/distance.
No 2025 observation entered
a 2026 within-year training
profile or vice versa.

The first read-only source
run successfully obtained
37/42 fixed dates. At
the 2025 150-m original
GPS marker with identical
race distance, **21 horse
IDs and 21 later GPS
records** passed the
minimum 20-ID source
support gate. The
historical own-horse RMSE
was **0.214881 s**,
compared with **0.243186 s**
for earlier other-horse
history and **0.241816 s**
for the zero baseline;
OTHER−OWN = **+0.028304 s**.

An independent second run
also successfully read
37/42 dates, but a
different original
2025 meeting was missing.
It retained only **17
HORSES IDs and 18
later records** and
correctly returned HOLD
without a numerical RMSE.
The first run read
2025-03-19 but not
2025-07-12, while the
second did the reverse;
both failed with original
incomplete/truncated
HTTP responses on their
unavailable date. All
**36 common successful
meeting dates** had
matching source meeting,
race, GPS and complete
HORSES-roster SHA256
digests and exactly
matching source join
counts. This is
sampling/access
instability, not
a biological change.

Two additional independently
executed original-source
re-fetches each successfully
read **38/42 original dates**
(including BOTH key 2025
dates). Their anonymous
aggregate JSON output bytes
were **SHA256-identical**.
In both runs, the
2025 150-m matched-distance
cohort held **23
HORSES IDs and 24
later records**. RMSE
was **0.211065 s**
for each focal horse's
strictly earlier history,
**0.240692 s** for
other horses' matched
past history, and
**0.239390 s** for the
zero benchmark
(OTHER−OWN = **+0.029627 s**).
Thus a positive
**source-conditional numerical**
comparison was reproduced
when both key dates were
accessible, but it was
not **source-availability
invariant** and is
not an independent
biological replication.

All 2026 within-year
Doomben 150-m and
200-m original contexts
remained below the
fixed support gate:
respectively **9 IDs /
11 later observations**
and **7 IDs / 8
later observations**.
Even in the first
2025 run, exact
Race Class matching
retained only **16**
IDs, while the second
retained **12**;
2025 200-m without
Class retained **13**.
Those original contexts
were HOLD, not null
biological effects.

The 2025→2026
year-forward Doomben
analysis evaluated a
different set of 26
identities and
source histories; it
cannot be treated as
a paired contrast
against this
within-2025 result
to infer annual
behavioral decay.
Full original
data provenance,
all non-confirming
source runs and
sample-based limitations:
[within-Doomben source-replay
audit](ecology-rq-doomben-within-year-source-replay-results.md),
[pinned anonymous
source evidence](evidence/rq-doomben-same-year-rerun-availability-20261015.json)
and [source
replay CI](https://github.com/zuizui0223/keiba/actions/runs/38697999341).

### 3.5. The two temporal prediction populations are fully disjoint

An original 38/42-date Doomben re-fetch included
**1,277** numeric HORSES-ID/positive initial
GPS source candidate records, **977** unique
original IDs and **228** original IDs observed
on multiple dates when markers/distances were
pooled. No horse ID was rejected for
inconsistent names.

At the **exact initial 150-m marker and
official race distance**, the independently
computed **outcome-blind ID/date incidence**
was:

| Fixed source repetition rule | Without Class | Also exact Class |
| --- | ---: | ---: |
| At least two different observed dates in 2025 | **23** | 17 |
| At least one date in each of 2025 and 2026 | **26** | 6 |
| **At least two 2025 dates AND one 2026 date, same individual and context** | **0** | **0** |
| At least two dates in BOTH calendar years | **0** | **0** |

The actual two scored source populations
likewise contained **23 within-2025
horses and 26 2025-trained/2026-scored
horses but zero original HORSES IDs in
their intersection**, even before matching
context. Both strict and broad comparisons
therefore returned the predeclared
**scientific HOLD** without computing an
unsupported paired-horizon RMSE contrast.

This is a **source repetition/identifiability
failure**: the two observed positive and
negative scores describe different animals,
not a within-animal change across years.
The independent source-incidence calculation
did not use prediction error or GPS timings.
[Original-source overlap analysis
and interpretation](ecology-rq-doomben-matched-timescale-overlap-real-results.md)
([verified first official data run
#38703717378](https://github.com/zuizui0223/keiba/actions/runs/38703717378)).

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

The new same-Doomben
within-year control
strengthens this caution:
a marginally supported
positive 2025 within-year
score was lost as an
estimable result when
a different fixed 2025
meeting had a truncated
source response. The
common 36 successful
original source dates
were byte-identical
under multiple independent
SHA256 components and
source-join counts. A
source-retrieval failure
can therefore determine
whether an apparent
individual-history effect
is even eligible to be
reported. It cannot
tell us whether the
horse itself altered
its behavior across
months or years.

More fundamentally, the direct Doomben
source-incidence test showed **zero
eligible same-HORSES-ID animals**
with an exact 150-m marker/distance
history measured at least twice in
2025 and at least once in 2026.
The two historical-score groups
are **disjoint, not the same animals
followed at two horizons**.
The contrast between their group-level
RMSE values therefore cannot be
interpreted as within-animal change,
independently of whether its
individual numerical scores have been
computationally reproduced.

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

The [meta-analysis of behavioural repeatability by Bell,
Hankison & Laskowski (2009)](https://doi.org/10.1016/j.anbehav.2008.12.022)
found that the length of the interval between
observations can modify apparent repeatability,
with the direction of its initial analysis
sensitive to two unusually influential
studies. This provides biological motivation
for explicit time-horizon tests, not evidence
that a one-year period caused a change in
these particular horses. More fundamentally,
[Dingemanse & Dochtermann (2013)](https://doi.org/10.1111/1365-2656.12013)
distinguish individual differences in reaction-norm
intercepts from context variation and
**pseudo-repeatability** arising when observed
conditions covary with individual identity.
Here, every conditional ICC and source-identified
prediction advantage could still incorporate
nonrandom training, selection, race Class or
GPS sensing. Neither temporal transfer failure
nor an ICC contrast alone establishes a
within-horse change in behaviour or physiology.

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

Even public original-source availability
can be unstable across repeated retrievals:
the same Doomben within-year code yielded
a marginal 2025 numerical own-history
advantage in one source run and a HOLD in
another. The 36 overlapping original
source snapshots were byte-fingerprint
concordant; an incomplete or truncated
HTTP response for a different 2025
meeting in each run changed the
eligible HORSES-ID count.
A numerical result conditional on the
retrieved source subset must therefore
not be mistaken for replication
of the same biological cohort.
An immutable lawful source cache,
documented original roster response
hashes and prespecified completeness
requirements are prerequisites for
a stronger external prediction test.

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
Within Doomben 2025,
two original-source
38-date reruns
reproduced a positive
individual-history
numerical advantage,
but another rerun
lost the 20-horse
support threshold
through an incomplete
upstream source response.
The conditional
advantage was therefore
reproducible for one
source snapshot, not
independent of source
availability.
The same-venue Doomben source
lacks even a single original horse
ID observed on >=2 dates in 2025
and again in 2026 with identical
150-m first marker and race distance.
The sign contrast arises from
**different animal populations**,
not an experimentally observed
within-horse change. The contrast
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
[generated figure CI and SVG artifact](https://github.com/zuizui0223/keiba/actions/runs/38679786636);
[anonymized pinned evidence](evidence/rq-racehorse-temporal-generalization-20261015.json);
[deterministic figure generator](../scripts/ecology_rq_manuscript_temporal_figure.py).

**Table 3. Doomben same-course source replay
availability and individual-history score support.**
Run A: 2025 150m exact-distance
21 IDs/21 future records,
OTHER−OWN gain +0.028304 s;
Run B: 17 IDs/18 records, HOLD.
All 36 jointly successful dates
have matching original source
hashes and matching GPS-ID
join counts. The two
source-specific available
dates are 2025-03-19
and 2025-07-12;
each was unavailable in
the opposite source run.
No claim of individual
within-year decay follows.
Evidence: [independent source
comparison](https://github.com/zuizui0223/keiba/actions/runs/38697999341);
[source and inference audit](ecology-rq-doomben-within-year-source-replay-results.md).

**Figure 2. Nonoverlapping original-source horse-ID sampling
populations prohibit an individual time-horizon effect.**
Under the first 150-m GPS marker and exact original
race distance at Doomben, 23 individual source
HORSES IDs had two or more distinct source dates
within 2025, and 26 IDs had at least one source
date in each of 2025 and 2026. The intersection
of these eligibility sets was **zero IDs**.
The same-Class screen also returned zero
between its 17 within-2025 repeats and six
year-shared horses. These are **disjoint
source-observable eligibility sets, not
experimental year treatment groups**.
Across original first GPS markers,
977 unique source IDs were observed and 228
had at least two source dates, but
matching marker, distance and exposure
was not available across both horizons.
Only 38/42 locked source dates were
accessible. The figure depicts
source support, not an inferred
biological absence of personality or
an age-related behavioral response.
Two original source-run anonymous aggregates
were fully SHA256 identical.
Figure code: [anonymous deterministic
Figure 2 generator](../scripts/ecology_rq_manuscript_source_overlap_figure.py);
[full scientific HOLD audit](ecology-rq-doomben-matched-timescale-overlap-real-results.md);
[verified SVG and CI
#38705465632](https://github.com/zuizui0223/keiba/actions/runs/38705465632).

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

The following are aggregate-only and code/source-provenance
records; none includes individual HORSES IDs,
jockey/trainer licence IDs, named race performances
or individual telemetry.

- [Complete pre-submission claim map](ecology-racehorse-individuality-manuscript-outline.md)
- [Within-2026 Cannon forward score](ecology-rq-rider-change-forward-validation-results.md)
- [Focal-horse versus other-horses source context](ecology-rq-forward-other-horse-comparator-results.md)
- [2025→2026 Doomben held-out source score](ecology-rq-doomben-2025-to-2026-year-forward-results.md)
- [Original Doomben within-year fixed sample and source availability](ecology-rq-doomben-within-year-source-replay-results.md)
- [Critical same-HORSES-ID two-timescale overlap audit](ecology-rq-doomben-matched-timescale-overlap-real-results.md)
- [Pinned anonymous 2-run exact zero source overlap](evidence/rq-doomben-identical-horse-timescale-overlap-20261015.json)
- [Figure 2 source renderer](../scripts/ecology_rq_manuscript_source_overlap_figure.py)
- [Racing Queensland official assigned versus postrace fields](ecology-rq-official-soap-vs-final-starters-jockey-data-scope.md)
- [Historical Cannon source snapshot changes](ecology-rq-cannon-original-source-drift-20261014.md)
- [Parametric Gaussian ICC limitations](ecology-rq-real-icc-source-conditional-sampling.md)
- [Official same-horse time-horizon incidence run A](https://github.com/zuizui0223/keiba/actions/runs/38703717378)
- [Official same-horse time-horizon incidence run B](https://github.com/zuizui0223/keiba/actions/runs/38703784178)
- [Full scientific source-positive forward cohort run](https://github.com/zuizui0223/keiba/actions/runs/38563275612)
- [Year-forward original source cohort run](https://github.com/zuizui0223/keiba/actions/runs/38678720302)

**Manuscript status:** coherent full first draft,
not approved for journal submission.
Required: complete rights check,
verifiable independent source data,
appropriately qualified uncertainty,
and author/affiliation/contribution review.
