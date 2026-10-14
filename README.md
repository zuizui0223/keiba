# keiba — ecological individuality & competitive context

## 2026-10-14: how uncertain are the original horse ICCs under the Gaussian model?

A post-hoc, **model-conditional sampling sensitivity** was completed
on **both previously source-locked racecourses** using the exact
original Racing Queensland race×horse ID observation design.
All **12/12 source dates** were fetched for both Cannon Park
and Eagle Farm, with 299 fitted-Gaussian and 199
zero-horse-variance Gaussian simulations per venue.

| Original site | Fresh source race-FE horse ICC point | Conditional Gaussian re-estimated ICC 2.5–97.5% quantiles |
| --- | ---: | ---: |
| Cannon Park | **0.430147** | **0.313683–0.528432** |
| Eagle Farm | **0.453332** | **0.166828–0.708244** |

These are **NOT validated population 95% confidence intervals**.
They are distributions of re-estimated ICC points when the
fitted Gaussian horse/random-effect model, observed horse×race
coverage, and constant error variance are assumed literally
true. Actual source dropout, nonrandom race entry, shared
trainers, age/weight/jockey confounding and meeting-date
dependence are **not corrected**. Eagle's broader interval
shows materially weaker conditional source precision despite
a numerically similar point estimate.

The original GPS section marker is **NOT the same measured
first-segment trait** between the tracks. On the latest source
snapshot, marker-specific ICC and conditional model quantiles
were Cannon 150m **0.539528** (0.321931–0.684309),
Cannon 250m **0.418787** (0.248634–0.600394),
and Eagle 200m **0.527731** (0.200194–0.786889).
Eagle 100m and other nonidentified cross-track matched-marker
cohorts remain **HOLD**; Doomben 150/200m also lacks
the necessary recurring horse IDs.

**Data snapshot warning:** fresh ICC values differ slightly
from previous source reports (0.431738 Cannon, 0.452894
Eagle). Per-original-meeting source hashes are retained;
changes in data-provider historic entrant lists must
never be interpreted as animal biology.

[Reproducible original-source simulation and scientific
limitations](docs/ecology-rq-real-icc-source-conditional-sampling.md),
[post-hoc source-design protocol](docs/ecology-rq-icc-conditional-simulation-protocol.md),
and [successful paired GitHub Actions source audit
#38501941730](https://github.com/zuizui0223/keiba/actions/runs/38501941730).

This is *additional uncertainty information*, not
a H1 random environmental slope, H2 social interaction,
heritable animal personality, natural selection,
or population-wide horse-specific biological finding.


## 2026-10-14: strictly earlier horse records predict later timing with new documented rider

A fresh, **12/12 official-date** Cannon Park source re-read passed
a newly frozen exploratory **chronological, past-only** data gate.
For **36 numeric HORSES IDs / 46 later GPS-timed horse records**
with an original `Jockey/@Id` not previously documented for
that horse within the identical original race-distance and first-GPS
marker context, the equal-horse RMSE of the later
**race-relative first-sectional timing** changed from
**0.297676 seconds** (zero horse profile) to **0.255809 seconds**
(fixed n/(n+2) shrunken historical horse profile), an error
reduction of **0.041867 seconds or approximately 14.1%**.

This is a positive *retrospective out-of-time* repeatability
observation, **not** independent source validation or pre-race
wagering. The evaluation target is defined using the realized
post-race GPS-timed peers; the official licence is a
source-nominated rider, **not a verified final jockey**.

Stricter same-Class comparisons also gave positive reduction
(20 original IDs / 22 later records; +0.049712 seconds),
but the sample exactly meets the minimum support gate. The
main same-declared-trainer subgroup (29 IDs / 39 later
records) showed +0.043919 seconds. These *different*
subsamples do **not** identify a jockey or trainer cause.

The original 543-candidate current source snapshot is still
**five records smaller** than the historical 548-record
candidate cohort; earlier RQ horse-roster SOAP hashes were not
saved, so the reason is unresolved. Individual intrinsic
personality, genetics, adaptation, environmental H1
reaction norms and competitive-interaction H2 remain
**unsupported**.

See the [real-source forward-only validation results](docs/ecology-rq-rider-change-forward-validation-results.md),
[pre-result analysis lock](docs/ecology-rq-rider-change-forward-validation-lock.md),
[successful official-source execution](https://github.com/zuizui0223/keiba/actions/runs/38501390778),
and [192-test ecological QA](https://github.com/zuizui0223/keiba/actions/runs/38501390724).

**研究の中心：競走馬の個体差・環境反応規範・競争相手の構成が、相対的な競走成績をどう変えるか。**

This repository is being developed as a reproducible observational research program at the intersection of **individual ecology, phenotypic plasticity, competitive interactions and equine performance science**. The causal/environmental H1 and competition H2 hypotheses are **proposed and not empirically supported**. A separate, narrower **exploratory real-horse finding on individual consistency of race-relative early timing** has now been reproduced, with substantial selection and measurement limitations (see below).

## 2026-10-14: Third-track exact-marker repeatability audit — scientifically HOLD

The official first-party Racing Queensland Doomben
Turf sectional CSV index provides early intervals
starting at **150m and 200m**: candidate identical
first-marker comparisons to Cannon Park (150m)
and Eagle Farm (200m). To avoid selecting favorable
results, the **earliest and latest original Doomben
CSV meeting per month** were source-locked before
reading original 2026 horse IDs or ICCs:
**19 original meeting dates, races 1–6 per date**.

[Real original-source GitHub Actions #38499396097](https://github.com/zuizui0223/keiba/actions/runs/38499396097)
successfully processed **18/19 dates**,
linking **617** positive first-GPS HORSES-ID
observations, 541 distinct official IDs,
and 65 IDs repeated on >=2 dates
*irrespective of section marker*.

**The critical result is a negative
data-identifiability decision, NOT zero animal
repeatability:**

- **150m:** 177 original rows in 24
  race fields, but only **9** official
  HORSES IDs observed on 2+ different
  dates at that exact first marker.
- **200m:** 205 original positive marker
  records (193 after minimum race GPS
  filter), with only **9** IDs repeated
  on 2+ dates at that marker.
- The pre-existing race-FE horse Gaussian
  ICC requires >=20 repeated IDs:
  **both marker-matched ICCs return
  HOLD**, NOT zero.
- 2026-08-26 is a documented upstream
  **GetRacesForMeeting source failure**:
  the official RQ web service returned a
  SQL text-truncation error, not a valid
  race-ID XML roster. We did not guess
  missing race IDs or replace the fixed
  source date.

Thus Cannon Park ICC 0.432 and Eagle
Farm ICC 0.453 remain **separate,
marker-heterogeneous observational
model estimates**, NOT a reproduced
same-individual, same-interval biological
trait. A third venue with some 150m/200m
measurement records is **not** sufficient:
it must have enough *repeated same-ID
animals within each measurement condition*.

[Full Doomben method and frozen
source failure/support audit](docs/ecology-rq-doomben-third-venue-original-marker-audit.md);
[source-date inclusion locked before this
fit](docs/ecology-rq-doomben-2026-third-venue-calendar-lock.md).

**H1 wet-ground random slope, H2
social context interaction, heritability,
adaptation and wagering claims remain HOLD.**

## 2026-10-14: Does early relative pacing persist with another declared jockey?

**New exploratory REAL horse-ID source observation:** in the already locked
12-date Cannon Park 2026 cohort, the same official HORSES ID had
matched original race distance and first GPS marker but **a different
source-declared Jockey/@Id** in **36 horses, 38 animal-by-marker strata,
72 different-date observation pairs**. The equally weighted within-horse
pair-product of original race-relative first-GPS timing deviations was
**+0.063583 seconds²**, versus a mean of **+0.001996 seconds²** under
199 seeded *within-race outcome reassignments*. This is not an
exchangeable randomized experiment, a confirmatory p-value, or
a causal estimate of changing riders. The **actual postrace jockey**,
finishing state, rider selection, trainer/horse confounding and
true biological personality remain unverified.

**Important source snapshot limitation:** this run had **543** original
GPS-positive ID matches (519 after the >=4 timed-peers gate);
the earlier official Cannon analysis had **548** (523 after gate).
Earlier meeting/race/GPS files had the same hashes, but earlier
original GetHorsesForRace rider/animal roster response hashes were
**not archived**, so the five-record difference cannot be assigned
a verified biological or data-provider cause. A subsequent source
retry obtained only **3 of 12 dates** and was correctly marked
**scientifically HOLD**, despite the successful CI process.
Never treat absent source responses as zero animal effects.

A **post-hoc leave-one-meeting-date and anonymous leave-one-horse
influence audit** has now independently re-read **all 12 source dates**,
and all 176 synthetic/QA tests passed. The original changed-rider
mean pair product remained **+0.063583 sec²**. All **12/12** single
meeting-date deletions stayed numerically supported and positive
(range **+0.045540 to +0.080127 sec²**), as did all **36/36**
anonymous single-animal deletions (**+0.049043 to +0.067635 sec²**).
These ranges are **NOT 95% uncertainty intervals**, independent
new cohorts or evidence of causal/innate horse personality.
The earlier incomplete 3/12-source retry was an availability HOLD,
not an empirical negative result. The difference between the
original 548 and new 543 candidate matches remains unresolved.

See the [rider-change real-source observational audit](docs/ecology-rq-real-rider-switch-persistence-audit.md),
[date/horse deletion criteria](docs/ecology-rq-rider-switch-influence-design.md),
[full 12/12 official source sensitivity re-run](https://github.com/zuizui0223/keiba/actions/runs/38498881524),
and [first original rider-change run](https://github.com/zuizui0223/keiba/actions/runs/38492841107).
Environmental H1/H2, horse intrinsic personality, genetics and
wagering effects remain unsupported.

## 2026-10-14: Same original horse across Cannon Park and Eagle Farm?

The two previously locked 2026 venue cohorts were joined **by the
original numeric HORSES ID**, not by matching horse names or by a
modelled prediction. The bounded source audit independently read
**12 Cannon Park dates + 12 Eagle Farm dates**, with 548 and
391 original positive-GPS source records respectively.

Only **two original HORSES IDs** had positive source GPS at
both venues under conservative identity guards.
**One** of those had any identical first GPS marker at both
venues; **zero** had both an identical first marker and
the same official race distance/class. **Zero** IDs had
2+ dated measurements at each venue.

**Ecological interpretation:** The similar pooled race-FE
ICC point estimates (Cannon 0.432 and Eagle 0.453)
reflect mostly different observed animals and different
first-GPS interval measurement contexts. It would be
**incorrect** to describe them as a repeated-measures
test of the same horses' response to different tracks,
a universal behavior trait, an H1 environmental reaction
norm or an H2 social competition effect.

The restricted-source audit is documented in
[official cross-venue identity/measurement overlap](docs/ecology-rq-cross-venue-identity-support.md),
with [source-backed independent GitHub Actions
execution](https://github.com/zuizui0223/keiba/actions/runs/38421064924).
The current canonical code is
`scripts/ecology_rq_cross_venue_identity_support.py`,
using only the prelocked original 24 meeting dates.
**All biological cross-venue effect claims remain HOLD.**

## 2026-10-13 second racecourse: Eagle Farm source-ID ICC, but marker comparison HOLD

**One new real-data milestone with a substantive limitation:**
The original RQ SOAP HORSES-ID/early-GPS source joined **391**
Eagle Farm horse-labelled positive first-section records
across **12 different 2026 meeting dates** in a
[cohort locked before its new animal outcomes were inspected](docs/ecology-rq-eagle-farm-2026-independent-track-lock.md).
**48 HORSES IDs recurred across original dates**.

Using EXACTLY the same race-fixed Gaussian
horse random-intercept variance model as Cannon Park:
- Eagle Farm: 382 timed candidate observations in 51 races,
  45 repeated HORSES IDs, **conditional ICC 0.452894**.
  With >=6 positive GPS horses/race: ICC **0.441609**
  (342 observations, 42 races).
- Across 12 leave-one-meeting-day-out fits:
  **0.331549–0.563767**. This is **not** a confidence
  interval.
- Race-conditioned 99 horse-ID shuffles: mean
  **ICC 0.045556**, an observational null reference,
  **not** causal randomization.
- Historical Cannon Park (different venue,
  same publisher) pooled ICC was **0.431738**.

**CRITICAL: no original GPS first-distance marker
has an estimable individual ICC at BOTH tracks.**
Cannon Park's numerically supported 150m and
250m cohorts have **0 observations at Eagle Farm**;
Eagle Farm's 200m cohort has numeric **ICC 0.528346**,
but Cannon's 200m cohort had only 56 source rows and
failed the model-repeatability gate. The cross-site
same-segment scientific decision therefore is
**HOLD_NO_SHARED_FIRST_SECTION_MARKER_WITH_ESTIMABLE_ICC**.
The proximity of pooled 0.432/0.453 does not
demonstrate a universal horse behavior trait.

**IMPORTANT source-completeness limitation:** Only
108 of Eagle Farm's original 391 matched GPS
candidate rows survive complete Weight/Jockey/Trainer
fields plus >=4 complete horses/race. Those
108 rows contain **only 3 repeatedly observed HORSES
IDs**, much less than the 20-ID support gate.
Any superficially high fixed-nuisance adjusted
ICC is scientifically unidentifiable here.
The code now **suppresses those numeric adjusted
models and records HOLD**, instead of mistaking
a numerical optimizer output for animal variation.

The findings are source-conditional and exploratory.
No confirmed actual starter/finisher roster,
individual certified finish time, biological age,
heritable personality, environmental random-slope
H1 or competitive-context H2 has been established.

See [independent-track real-data
audit and interpretation](docs/ecology-rq-eagle-farm-real-icc-cross-site-audit.md),
[Eagle Farm locked cohort](docs/ecology-rq-eagle-farm-2026-independent-track-lock.md),
and [first-party CI run](https://github.com/zuizui0223/keiba/actions/runs/38412116293).
The matching-marker gate and adjustment support
tests are in
\`scripts/ecology_rq_eagle_farm_external_icc.py\`
and \`scripts/ecology_rq_covariate_icc.py\`.

~~~bash
python scripts/ecology_rq_eagle_farm_external_icc.py \
  --output tmp/independent-eagle-farm-source-ICC.json
~~~

## New 2026-10-13 selection and source-day stability tests

**The source-conditioned horse variance signal remains exploratory.**
The official `Weight`, `Jockey/@Id` and `Trainer/@Id`
complete-case sample has 279 horse×race observations,
**49.1% fewer than the original 548 positive-GPS
candidate records**. Its observed first-GPS
measurement selection was explicitly tested:

- In 68 original races with >=4 timed-GPS
  horses and a mixture of complete and
  incomplete role/weight records
  (**491 observations**), the equal-race
  mean first-GPS timing contrast was
  **−0.02355 seconds** (documentation-complete
  minus documentation-incomplete).
- 499 source-metadata-label shuffles *within
  each race* gave a two-sided algorithmic
  reference fraction **0.416**. This is
  **not** a calibrated missingness p value;
  it does NOT prove source outcome data are
  MCAR or validate unobserved racehorses'
  GPS/finishing times.

**Source-date stability gave a bigger warning.**
In the 11 original meeting dates represented
by the 279 complete-case rows, deleting
one entire source meeting at a time produced
ICC **0.429–0.551** (race-FE baseline)
and **0.385–0.577** (fully source-role
adjusted). The *difference* between adjusted
and baseline ICC ranged **−0.0789 to
+0.0340**, lowering ICC in 8 of 11
refits but **raising it in 3**.

Therefore the initial same-record adjustment
`0.503 → 0.487` is **NOT** a
date-stable reduction that can safely be
attributed to jockey/trainer/weight,
and stable horse–trainer assignments remain
a major identity confounder. These are
stability ranges, **not 95% confidence
intervals** or prospective tests.

Full original-data evidence:
[Weight/Jockey/Trainer adjusted ICC and
date-deletion caveats](docs/ecology-rq-real-horse-weight-jockey-trainer-adjusted-icc.md),
[source-metadata missingness and timing
negative control](docs/ecology-rq-source-role-missingness-vs-early-gps.md).

## First original-source Weight/Jockey/Trainer-adjusted horse ICC

The official Racing Queensland `GetHorsesForRace` response
documents `Weight` and original `Jockey/@Id`/
`Trainer/@Id` licence identifiers. These have now been
parsed without fuzzy names or guessed individual ages and
compared in a **same-source-cohort** race fixed-effects /
Gaussian random HORSES-ID model.

Original 548 positive first-GPS+HORSES-ID records:
**337** contained complete original weight/rider/trainer
attributes; only **279** remained after requiring >=4
attribute-complete timed horses in the same race
(54 races, 11 dates, 164 HORSES IDs).

In precisely those same 279 observations:
- race-FE + horse random intercept ICC **0.503005**
- + published registered riding weight ICC **0.509202**
- + jockey original licence fixed nuisance ICC **0.513500**
- + trainer original licence fixed nuisance ICC **0.487447**

**This is NOT evidence that jockey or trainer are
unimportant**: there are 148 source observations
missing numeric jockey licences, 63 further
missing trainer licences, and only 1 horse in
the final cohort has multiple different
trainer licences. The attrition from the
original positive GPS cohort is **49.1%**,
varying by original race TrackRating:
Good retained **47.8%**, Soft **56.9%**,
Heavy **45.9%**. At least one original
source meeting lost all observations
under the required complete-field gate.

The original **0.432** was fit to a
*different 523-record source population* and
cannot be compared directly with the complete
279-record fit. The matching-cohort ICC
shift **0.503 → 0.487** is a *descriptive
model dependence*, not a causal share,
calibrated interval, or an adjusted
intrinsic-horse genetic variance.

[Original-data numerical/source audit and
model specification](docs/ecology-rq-real-horse-weight-jockey-trainer-adjusted-icc.md).
The scientific claims for age-controlled
individual personality, ground-response H1,
social context H2, fitness and heritability
remain **HOLD**.

## New 2026-10-13 real-horse conditional mixed-model ICC (exploratory)

A **Gaussian random horse intercept with exact race
fixed effects**, fitted by within-race orthonormal
contrasts (restricted likelihood) to the
**original absolute first GPS sectional seconds**
rather than the race-relative peer outcome,
produced an **observational conditional ICC point
estimate of 0.431738** (523 original horse×race
observations, 74 races, 269 unique HORSES IDs,
139 repeated in 2+ races).

When only races with >=6 valid timed GPS
horses were kept, the point estimate was
**0.419445** (436 observations, 55 races).
Deleting one entire 2026 source meeting
at a time gave ICC estimates **0.390814–0.499262**;
this is **NOT** a confidence interval.

Under **99 within-race HORSES-ID shuffles**,
the shuffled ICC averaged **0.016736**,
compared with the original **0.431738**.
This is a computational negative-control
reference, **not** a randomized causal test.

Segment-marker stratification yielded
**0.547296** for first marker 150m (209 source
observations) and **0.418787** for 250m
(226 observations). Subsets at markers
100m/200m did not meet the source
repeatability gate. Different marker/route
cohorts and heteroskedasticity can create
different ICCs; pooled values should not
be treated as a universal equine parameter.

The result adds **model-based evidence
consistent with repeatable individual
variation**, but **not** a validated
population-level ICC confidence interval,
biological personality/heritability,
causal response, ground H1 reaction
slope or H2 social competition effect.
Jockey/rider, weight, age, training,
nominations, GPS dropout and date-clustered
uncertainty remain unresolved.

See [exact REML model, source hashes,
99 shuffled-identity negative controls,
marker-specific robustness and HOLD gates](docs/ecology-rq-real-horse-race-adjusted-icc.md).
Reproduce via the locked 12-date aggregated
original-source pipeline:

~~~bash
python scripts/ecology_rq_2026_calendar_overlap.py \
  --output tmp/rq-conditional-ICC-and-negative-controls.json
~~~

## Evidence update: exploratory real Thoroughbred individuality (2026-10-13)

From the **original Racing Queensland numeric HORSES IDs**
and 12 original Cannon Park meeting dates, 523 source
horse×race first GPS intervals were eligible in 74
races with >=4 positive GPS readings. Horse identity
recurred over different dates.

**New, narrower result: early race-relative time differs
consistently among recorded individuals in this
observational sample.** Among 99 HORSES IDs with repeated
early GPS readings at the same official race distance
and first distance marker, the equal-stratum mean
within-horse pair product was **+0.051925 s²** compared
with **+0.001735 s²** across 299 within-race identity
shuffles. Matching the original broad race class as
well retained 50 IDs and a mean pair product
**+0.035633 s²** versus a shuffled mean **+0.001136 s²**.

A past-identity historical profile improved later-date
retrospective relative-time RMSE from **0.3332 to
0.2878 seconds** in 54 held-out records, and from
**0.2826 to 0.2570 seconds** among 20 class-matched
records. **These are exploratory descriptive
associations, not corrected causal p-values, true
random-intercept ICC, a blinded independent cohort or
evidence of evolved behavioral personality.**

This response explicitly depends on observed *other
horses' contemporaneous first-section times*; it is
**relative early pacing consistency**, not absolute
locomotor speed nor causal social behavior. Source
starter status, missing telemetry, age, jockey, race
selection and training effects remain potentially
confounded. **H1 heterogeneous Good/Soft/Heavy
reaction norms and H2 competitor-interaction effects
remain scientifically HOLD.**

See the [complete frozen real-source result,
method and limitations](docs/ecology-rq-real-early-pacing-repeatability.md).
Reproduce the 12-date aggregator with the same
source-time-ordered, within-race-permutation benchmark:

~~~bash
python scripts/ecology_rq_2026_calendar_overlap.py \
  --output tmp/cannon-park-2026-12-dates.json
~~~

Reference for standard adjusted repeatability methodology:
Nakagawa & Schielzeth (2010),
https://doi.org/10.1111/j.1469-185X.2010.00141.x.

## Research questions

1. **Individual reaction norms:** do horses differ in how their performances change with ground condition, after controlling for course, distance, age, class and jockey?
2. **Biotic context:** does a horse's historically measured running-style profile interact with the pre-race composition of opponents?
3. **Specialization** (exploratory): is environmental performance specialization associated with a robustness trade-off, after correcting for selective race entry?

Read:
- [Ecological research design: hypotheses, alternatives, models, falsification criteria](docs/ecology-research-plan.md)
- [Longitudinal horse–race panel specification and leakage checks](docs/ecology-panel-schema.md)
- [Actual Kyoto 2026-10-12 archive: explicit H1/H2 data-gap audit](docs/ecology-archive-gap-audit.md)
- [Versioned H2 null and confounded-null simulation audit](docs/ecology-h2-simulation-audit.md)
- [Why race-standardized speed can mimic social interactions](docs/ecology-h2-absolute-outcome.md)
- [Versioned raw-speed horse+race FE falsification audit](docs/ecology-h2-absolute-stress-audit.md)
- [Data-source licensing and longitudinal field-coverage audit](docs/ecology-data-source-feasibility.md)
- [Why nonfinishers and missing speeds require a selection audit](docs/ecology-h2-outcome-selection.md)
- [Completion and speed as different H2 biological outcomes](docs/ecology-h2-two-part.md)
- [First real-data test in a separate racing species: Queensland greyhound GPS records](docs/ecology-real-greyhound-method-benchmark.md)
- [Official Thoroughbred sectional CSV: two independently audited race meetings](docs/ecology-rq-thoroughbred-source-audit.md)
- [Official HORSES internal ID recurrence: two Cannon Park dates, source-verified](docs/ecology-rq-two-date-official-id-recurrence.md)
- [First exploratory real-horse result: repeatable relative early sectional timing](docs/ecology-rq-real-early-pacing-repeatability.md)
- [Race-adjusted mixed-model ICC 0.432 on absolute first GPS time (exploratory, model-dependent)](docs/ecology-rq-real-horse-race-adjusted-icc.md)
- [Official riding Weight, Jockey & Trainer licence adjustment: same-source cohort and missingness](docs/ecology-rq-real-horse-weight-jockey-trainer-adjusted-icc.md)
- [Eagle Farm different-track source ICC and original first-section marker compatibility HOLD](docs/ecology-rq-eagle-farm-real-icc-cross-site-audit.md)
- [Eagle Farm dated twelve-meeting source cohort locked before animal ID inspection](docs/ecology-rq-eagle-farm-2026-independent-track-lock.md)
- [Real race-controlled documentation missingness vs first GPS timing: 68 mixed fields](docs/ecology-rq-source-role-missingness-vs-early-gps.md)
- [Original 20-race Good/Soft/Heavy real-horse H1 identifiability audit](docs/ecology-rq-real-h1-multigoing-feasibility.md)
- [Exploratory 38-race expansion: why ground-reaction norms remain unidentified](docs/ecology-rq-real-h1-multigoing-expanded-audit.md)
- [Fail-closed official HORSES-ID to sectional name crosswalk protocol](docs/ecology-rq-official-id-crosswalk.md)
- [H2 methods, negative controls, scope and interpretability](docs/ecology-h2-methods.md)

## Real Thoroughbred observation/identifiability (2026-10-13)

**Real official horses now confirmed:** in five separate
Ladbrokes Cannon Park meetings spanning Good, Soft and Heavy
ground, the original `HORSES` IDs have been linked
to first-positive-section GPS observations using conservative
same-day duplicate/identity controls.

The first, preserved fixed sample (20 official race numbers)
yielded 143 linked observations; 26 IDs repeated across
meeting dates and 20 IDs were seen in both Good and non-Good.
After matching race distance and the first-section marker,
10 IDs were comparable; with original race class also
matched, only 1 remained. **None** provided >=2 Good
and >=2 non-Good measures within the same strict stratum.

An explicitly labelled **exploratory post-hoc extension**
to the same five dates, requesting race numbers 1–8,
recovered **38 official race IDs**, 280 positive-GPS
ID-linked observations, **65** repeatedly observed numeric
HORSES IDs, and **37** with Good and Soft/Heavy observations.
Only **17** were comparable at the same race distance/first
marker; **2** when class was also matched; **0** reached
the original >=2 Good and >=2 wet within-stratum gate.
Even those "matched class" cases can differ in age/weight
restrictions, jockey and course preparation. A simple
wet-minus-Good difference is not a causal/environmental
reaction norm.

Therefore **a real animal ID and an environmental
contrast now exist, but H1 random-slope variance is
still NOT estimable at the required support; H2 also
remains scientifically HOLD** because official finish
outcomes, confirmed starters and historical rival
phenotypes are unavailable in the joined source.
See [fixed 20-race audit](docs/ecology-rq-real-h1-multigoing-feasibility.md),
[38-race sensitivity](docs/ecology-rq-real-h1-multigoing-expanded-audit.md),
and [source-level ID limitations](docs/ecology-rq-two-date-official-id-recurrence.md).

Reproduce **aggregate-only**, with no raw horse files committed:

~~~bash
python scripts/ecology_rq_multigoing_h1_preflight.py \
  --scope focused_four --output tmp/rq-H1-fixed.json

python scripts/ecology_rq_multigoing_h1_preflight.py \
  --scope extended_eight --output tmp/rq-H1-expanded.json
~~~

Original open-data publisher: Racing Queensland; no
JRA-VAN/NAR betting data were used for these audits.

## Current evidence / not yet done

- Present on the separate experimental branch [analysis/kyoto-20261012](https://github.com/zuizui0223/keiba/tree/analysis/kyoto-20261012): a single Kyoto race-day card with descriptive horse histories, source/time-stamped odds snapshots, market-comparison scripts and reproducibility checks.
- **Not yet present from actual races**: a licensed multi-year horse–race panel, complete official finish times, validated historical running-style profiles, or independently replicated effects. **Artificial test data** can run both H1 and H2 exploratory models with chronological evaluation.
- One-day win/place/third summaries cannot establish reaction norms, adaptive specialization, animal personality, natural selection, competition causality, or expected wagering returns.

## Research vs decision support

Ecological outputs will focus on conditional performance curves, horse-level slope variation, opponent-context interactions and uncertainty, with temporal validation and explicit competing explanations.

Historical odds/ticket analysis and betting decision support belong to the [separate Kyoto draft PR](https://github.com/zuizui0223/keiba/pull/1). They will not count as ecological evidence. No bet placing or financial return claims are made here.

## Literature anchors

- Dingemanse et al. 2010, behavioural reaction norms: https://doi.org/10.1016/j.tree.2009.07.013
- van de Pol 2012, random-regression design: https://doi.org/10.1111/j.2041-210X.2011.00160.x
- Maeda et al. 2012, track conditions and times: https://doi.org/10.1016/j.jevs.2012.02.012
- Oda et al. 2024, Japanese Thoroughbred performance and mixed models: https://doi.org/10.1111/jbg.12822

Already-published mixed-model and track-condition studies mean this is **not** a novelty claim. The proposed competition × individual-environment interaction and robust longitudinal validation require literature review and independent verification.


## Reproduce the research pipeline (fabricated data only)

The executable prototype requires Python 3.12+, NumPy, pandas, SciPy and statsmodels.
It is **not** a confirmed ecological model and has **no connection to betting**.

```bash
python -m pip install 'numpy>=1.26,<3' 'pandas>=2,<3' 'scipy>=1.11,<2' 'statsmodels>=0.14,<0.15'
python scripts/ecology_demo_data.py --output tmp/fabricated.csv
python scripts/ecology_panel.py --input tmp/fabricated.csv --audit tmp/audit.json --features tmp/lagged.csv
python scripts/ecology_h1_pilot.py --input tmp/fabricated.csv --surface turf --permit-synthetic-demo --output tmp/h1-synthetic.json
python -m unittest discover -s tests -p 'test_ecology_*.py' -v
```

The artificial rows carry `source_license=synthetic`, and fitting is refused without
`--permit-synthetic-demo`; that flag refuses any non-synthetic rows. A successfully
fitted model on invented data is an **implementation smoke test**, not a research result.

For authorized real records, first prepare one CSV row per historical horse×race
start according to the [schema](docs/ecology-panel-schema.md), then run
`ecology_panel.py`. The full cross-going repeated exposure and rights gates must
pass before `ecology_h1_pilot.py` will run without demo mode.

Current H1 pilot uses *race-centred z-speed*, estimated after complete finish-time
rosters are available, a horse random intercept, and optionally a horse random
**within-individual ground-response slope**. Horse exposure means are estimated from
training dates only; train/test races are chronologically separated. It omits
several confounder adjustments (jockey, age, class changes, selective race entry),
cannot establish physiological plasticity, and reports no validated ecological
effect. An exploratory H2 interaction pilot is implemented separately; confirmatory causal analyses are not yet fitted.

**Data rights:** JRA-VAN's standard Article 7 is restrictive about public
redistribution. Do not add real licensed extracts to this repository before
obtaining appropriate permissions:
https://jra-van.jp/info/rule.html and
https://developer.jra-van.jp/t/topic/899.


## H2: changing-competitor-field exploratory model (fabricated only)

A second **independent** demo constructs new rivals across dates and fits
an own-style × historical-other-front-runner-composition interaction:

```bash
python scripts/ecology_demo_competitors.py --output tmp/competitors-FAKE.csv --days 65 --horses 36 --runners 12
python scripts/ecology_panel.py --input tmp/competitors-FAKE.csv --audit tmp/h2-audit.json --features tmp/h2-lagged.csv
python scripts/ecology_h2_pilot.py --input tmp/competitors-FAKE.csv --output tmp/h2-pilot.json --surface turf --permit-synthetic-demo
```

The two competing models contain identical baseline historical form and
opponent-strength predictors, with the interaction term added only in H2.
Horse intercepts are partially pooled, train/test is date-ordered, and all
feature centering learns from training dates only. Both models are compared
using future race-relative speed prediction errors.

**Never interpret these simulated coefficients as findings about real horses.**
The dynamic-field generator deliberately inserts a known interaction to
exercise the code. The model lacks a robust causal identification strategy,
horse/race crossed uncertainty, and a formal source-licensed data cohort.
Read [H2 methods](docs/ecology-h2-methods.md) before interpreting outputs.

Previously known science must be distinguished from our proposal:
Spence et al. (2012), DOI
[10.1098/rsbl.2011.1120](https://doi.org/10.1098/rsbl.2011.1120),
reported pacing and aerodynamic drafting associations from
44,803 tracked runners across 3,357 races. Merely observing a competitive
effect or front-runner performance is **not** an original ecological discovery.


## Ecological social-interaction falsification tests (research branch)

The next-level pilot treats changing opponents as a repeated **social
environment** rather than another betting odds feature.

- [Within-horse rival context, fixed effects and two-way clustered SE](scripts/ecology_h2_within_between.py)
- [Three fabricated mechanisms: null, planted interaction, confounded null](scripts/ecology_h2_falsification.py)
- [Methodological limits, real-data prerequisites and published ecological theory](docs/ecology-h2-methods.md)

Reproduce the strictly synthetic falsification pipeline:

```bash
python scripts/ecology_demo_competitors.py --output tmp/competitors-FAKE.csv --days 65 --horses 36 --runners 12
python scripts/ecology_h2_within_between.py --input tmp/competitors-FAKE.csv --output tmp/h2-within.json --permit-synthetic-demo
python scripts/ecology_h2_falsification.py --output tmp/h2-stress.json --seeds 512 911
```

**This is not a full social animal model**: see van de Pol & Wright (2009,
https://doi.org/10.1016/j.anbehav.2008.11.006) and Martin & Jaeggi
(2022, https://doi.org/10.1111/jeb.13900). The current pipeline does
not estimate heritability, fitness, social selection or causal social
plasticity. Its null and confounded-null scenarios are checks for
software/design weakness, not actual observations. Real results remain
unavailable until authorized multi-year racing records are assembled.


## H2 primary outcome safeguard: raw individual speed

**Important identification improvement.** The previously implemented
race-centred z-speed response can change if an opponent changes speed,
even while the focal horse's speed remains fixed. This creates a
mathematical rival effect in the outcome, not necessarily social plasticity.

The more defensible **exploratory primary H2 model** now fits focal
individual speed (m/s) with **crossed horse and race fixed effects**,
style×going controls and focal style×within-horse rival-context interaction.
Comparison with the old z-speed model is a mandatory sensitivity check.

```bash
python scripts/ecology_h2_absolute_speed.py --input tmp/competitors-FAKE.csv --output tmp/h2-absolute.json --permit-synthetic-demo
python scripts/ecology_h2_absolute_stress.py --output tmp/h2-absolute-stress.json --seeds 512 911
```

In a two-seed-per-scenario **synthetic-only** stress audit, the
deliberately confounded zero-effect case produced a nominal zero-
excluding interaction interval in **1/2** leave-one-out runs using
z-speed, and **0/2** using raw speed plus horse/race effects.
These are merely six illustrative fictional datasets per model and
**not** validated false-positive rates, statistical power, or
observations from real horses. See [frozen audit and complete limitations](docs/ecology-h2-absolute-stress-audit.md).


## 2026-10-12 update: whole entrant exposure, observed speed selection

The raw-speed H2 model has been corrected to retain **every confirmed
starting horse as a rival**, even if that horse later does not finish.
The speed regression uses only positive observed individual finishing
times and does **not** impute nonfinishers as 0 m/s. Previously, one
unobserved time could remove an entire race. New audits separate:

- Full **starting field** completeness from available **past style/
  ability history** and available **postrace speed**.
- Nonfinishers versus horses reported as finished without a usable time.
- Timed-outcome fractions by track going, focal pre-race running style,
  and pre-race rival style composition.

The model now writes `outcome_selection_audit` and, if any otherwise
eligible horse's speed is unobserved, explicitly records
`HOLD_POTENTIALLY_INFORMATIVE_SPEED_MISSINGNESS`. This is a *warning*,
not an automated correction for informative censoring or a new
biological finding.

Reproduce the missing-outcome stress, on fake horses only:

```bash
python scripts/ecology_h2_outcome_loss_stress.py \
  --output tmp/h2-outcome-loss-stress.json --seed 512
```

Methods and outstanding bias: [H2 starter/outcome selection](docs/ecology-h2-outcome-selection.md).

## Route to actual longitudinal data: offline compatibility screen

The Kaggle
[Horse Racing in HK](https://www.kaggle.com/datasets/gdaley/hkracing)
publisher lists horse IDs, race IDs, first sectional position, ground
condition and individual times in `races.csv`/`runs.csv`, potentially
enabling long-term ecological contrasts. Its race dates are expressly
**obscured**, and the claimed CC0 label does not independently confirm
rights from the originating race-results provider.

`ecology_hk_preflight.py` can inspect lawfully obtained **local**
CSV files and emit aggregate join/overlap/coverage statistics. It does
not download, republish horse rows, guess source timestamps, relabel
ground types or feed a fitted H1/H2 model.

```bash
python scripts/ecology_hk_preflight.py \
  --races /private/hk/races.csv \
  --runs /private/hk/runs.csv \
  --audit tmp/hk-readiness.json
```

The output status is **HOLD_SOURCE_RIGHTS_AND_OBSCURED_DATES** until
external provenance and study-use permissions are established.


## October 13: completion and performance are distinct ecological outcomes

The experimental H2 pathway now contains a **two-part observational
sensitivity model** rather than treating nonfinishing as a zero-speed
performance:

1. Binomial completion among ALL confirmed race starters, using
   previous horse ability, previous running style and previous rival
   composition. Compare baseline with a horse-style × rival-style
   interaction on later race dates. Sparse DNF events cause explicit HOLD.
2. Individual raw speed conditional on observed finishing times, with
   horse/race fixed effects and the previously introduced loss-to-
   observation warning. A DNF does **not** have a full-distance speed.

Both stages remain **exploratory**, fitted independently rather than a
joint likelihood, and cannot attribute injuries or nonfinishing to
social competition. Reproduce exclusively on invented horse IDs:

~~~bash
python scripts/ecology_demo_completion.py --output tmp/fictional-with-DNF.csv --days 100 --horses 48 --runners 12 --seed 512 --loss random
python scripts/ecology_h2_two_part.py --input tmp/fictional-with-DNF.csv --output tmp/h2-two-part.json --permit-synthetic-demo
~~~

A synthetic QA run created 1,200 fictional horse starts and 26
artificial DNF records; this is an **implementation result, not a
biological observation**. See the
[full two-part definition](docs/ecology-h2-two-part.md).

### Data suitability has a new within-condition gate

The offline Hong Kong CSV preflight now also reports whether the same
horse has **at least two starts in each of two ground conditions
within the same venue, surface, distance and class**. A general
"many records + mixed ground" count is insufficient: if every poor
ground race is a higher class, H1 environment effects cannot be
identified separately. It flags repeated nominally obscured dates
without inventing an ordering.

**Actual Thoroughbred horse data access is still HOLD.** A separate,
properly attributed *real greyhound* benchmark now checks repeated
start-box exposure and early split timing; it neither tests horse H1/H2
nor supplies complete rival fields for causal competition analysis.


## First real animal-data benchmark (not racehorse evidence)

Unlike the synthetic H1/H2 demonstrations, the new
[Queensland greyhound repeat-exposure benchmark](docs/ecology-real-greyhound-method-benchmark.md)
was **independently reproduced on genuinely published GPS running data**
in [GitHub Actions run #38325379268](https://github.com/zuizui0223/keiba/actions/runs/38325379268).

The pinned 2026-10-12 public ODC-BY source from **Australian Racing Open
Data (PandaVision)** contains 25,679 published runs over 6,021
date × venue × race labels. A dog name is *not necessarily a unique
stable biological identifier*.

Exploratory individual-name × venue contrast: 2,302 strata each with
>=2 starts from boxes 1–4 and >=2 from boxes 5–8. Mean first-50m
split at outer boxes minus inner boxes = **+0.01097 seconds**,
descriptive name-cluster-resampling interval
**[+0.00823, +0.01340] seconds** (1,000 draws).

This is **not an effect of natural selection, not causal lane geometry,
not physiological plasticity, and NOT A HORSE RESEARCH RESULT**.
The straight-track venue also shows a positive association, timing
and start-box choices are not randomized, and race class/distance/
weather may be confounded. The source contains incomplete/variable
GPS coverage, with no certified full opponent rosters, so true
horse-style × rival-composition H2 cannot be inferred.

Reproduce exactly the pinned open-data version, with its Git blob
verification and mandated attribution:

~~~bash
python scripts/ecology_greyhound_open_pilot.py \
  --fetch-pinned --require-pinned \
  --output tmp/greyhound-audit-20261012.json
~~~

The script downloads ODC-BY source values for local analysis but
publishes **aggregate JSON only**, not runner-level records.

**Actual Thoroughbred sectional source now verified:** Racing Queensland's
official downloadable horse GPS sectional CSVs for 2026-10-10 Eagle Farm
and 2026-10-11 Cannon Park were independently retrieved and audited.
See [the frozen horse source audit](docs/ecology-rq-thoroughbred-source-audit.md).
They provide dated per-named-horse sectional intervals but **not**
verified stable `HORSES` IDs, certified individual finish times, actual
starters/DNF status or complete competitor histories. Thus genuine
equine observations exist, but H1/H2 ecological model results remain
**HOLD**, pending a conservative official ID/results crosswalk.

The official [Open Data Web Services](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf)
document describes `GetHorsesForRace` and an internal horse ID,
not yet joined to sectional CSV horse names. This is not proof that
a long-term horse-level panel has been assembled.


## 2026-10-13: two verified official horse sectional files

[Official published Thoroughbred sectional measurements](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
were accessed for exactly two historical dates. A new standard-library parser,
`scripts/ecology_rq_thoroughbred_sectional_audit.py`, reads the
unusual semicolon-packed rows, checks the race headers and timestamps,
and reports **aggregate-only** counts.

GitHub Actions [source audit run #38330158633](https://github.com/zuizui0223/keiba/actions/runs/38330158633)
successfully retrieved and hashed 197 horse-labelled CSV rows across
18 race-header blocks; 162 had some positive sectional telemetry and
35 had all-zero values. **These are not 35 confirmed nonfinishers.**
Indeed five horse *names* appeared on the same date in two separate
race headers, with zero telemetry in one and positive telemetry in
another. No automatic DNF or shared biological identity is inferred.

~~~bash
python scripts/ecology_rq_thoroughbred_sectional_audit.py \
  --fetch-official 20261011-cairns \
  --audit tmp/cairns-official-sectionals-audit.json
python scripts/ecology_rq_thoroughbred_sectional_audit.py \
  --fetch-official 20261010-eagle-farm \
  --audit tmp/eagle-farm-official-sectionals-audit.json
~~~

The source publisher is Racing Queensland (subject to its original
terms); raw horse-level files are not copied to this repository. The
sectional numeric signal's units, official horse IDs, full starter
status and individual finish times have **not yet been confirmed**.
Consequently **no actual equine environmental or social-effect
coefficient has been estimated**. See [source identity and telemetry
audit](docs/ecology-rq-thoroughbred-source-audit.md).


### Conservative official horse-ID crosswalk

The new `scripts/ecology_rq_official_id_crosswalk.py` checks one
locally supplied **verified official race roster** against the
independently validated official sectionals, without downloading
or publishing raw horse records. It refuses to guess identifiers
from a CSV horse name or an unnamed integer field, and marks
ambiguous same-day repeat names as unresolved. Its output remains
**HOLD_OFFICIAL_EQUIVALENCE_AND_LONGITUDINAL_VALIDATION**, even when
a name matches syntactically, because the official roster and
longitudinal biological identity must be validated separately.

[Required source fields, synthetic tests and usage](docs/ecology-rq-official-id-crosswalk.md).
**Updated 2026-10-13:** the official API and the original GPS CSV
have now been compared for one actual race (**11/11** exact name matches
with original HORSES Ids) and for two same-venue dates (**2** source-
level recurring internal HORSES IDs with positive GPS each date).
These are source-verifiable individual-history feasibility checks, but
the verified actual-starter roster, official individual finish-time
join and environment-conditional repeated population panel remain
**HOLD**. See the [reproducible two-date identity audit](docs/ecology-rq-two-date-official-id-recurrence.md).


## Official equine ID recurrence has now passed a small real-data gate

The **verified original-source** comparison of Cannon Park
(2026-08-29 and 2026-10-11) found **two** official internal HORSES IDs
with the same exact horse name across these dates and positive original
GPS timing on both days. A bounded small-race audit produced this
count without committing any horse-level records; see
[GitHub Actions source-ID recurrence run #38333318382](https://github.com/zuizui0223/keiba/actions/runs/38333318382)
and the [frozen proof and caveats](docs/ecology-rq-two-date-official-id-recurrence.md).

Both sets of selected official races were rated **Good**; this
source-backed linkage is *not* an H1 ground reaction-norm result.
It also does not prove full actual-starter rosters, historical
opponent behaviors or H2 social plasticity. Racing Queensland SOAP
`GetRaceDetails` and `GetHorseDetailsInRace` schema checks
revealed only race metadata and a horse's name/jockey/trainer/weight,
not certified individual result times or placings. The missing
result/track-contrast pieces remain the scientific priority.

~~~bash
python scripts/ecology_rq_two_date_horse_id_repeat.py \
  --output tmp/rq-two-date-id-recurrence.json
~~~

The JSON contains aggregate counts and source hashes only; **no names,
numeric HORSES IDs, or bulk original GPS source rows are published**.
