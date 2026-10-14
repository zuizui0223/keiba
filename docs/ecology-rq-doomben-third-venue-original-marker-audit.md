# Third RQ Thoroughbred venue: Doomben 2026 original-source marker bridge

**Exploratory source-feasibility result, 2026-10-14.**
Initial genuine original-source execution:
[GitHub Actions #38499396097](https://github.com/zuizui0223/keiba/actions/runs/38499396097).
Protocol was committed BEFORE retrieving Doomben HORSES identities
or 19-date outcome values:
[immutable Doomben calendar and race-number source lock](ecology-rq-doomben-2026-third-venue-calendar-lock.md).

**Scientific decision: HOLD_NO_SHARED_SOURCE_MARKER_WITH_NUMERIC_HORSE_ICC.**
This is **not** evidence that individual early-pacing repeatability is
zero, that all racehorses are biologically identical, or that any
racecourse alters plasticity. It is an empirical source-design/
within-ID-repetition failure under the existing fixed model gates.

## Why the third racecourse was tested

The original 12-date Cannon Park sample gave a race-FE horse
random-intercept Gaussian ICC **0.431738** (pooled first
GPS segments), with separate numerically estimable
**150m ICC 0.547296** and **250m ICC 0.418787**.

The independently chosen 12-date Eagle Farm sample gave
pooled ICC **0.452894**, and **200m ICC 0.528346**,
but **no first GPS measurement marker was numerically
estimable at both venues**. Moreover only **2**
numeric original HORSES IDs appeared at both locked venues,
none with a common marker+original race distance.
Their similar pooled ICCs are **NOT a matched-trait
or same-animal replication**.

A source-schema inventory of a SINGLE Doomben GPS
file before locking the full cohort showed
**150m and 200m initial timing markers** in addition
to other route-specific distances. Doomben was
therefore chosen as a bridge between 150m Cannon
and 200m Eagle.

## Fixed cohort

Original source publisher:
[Racing Queensland Thoroughbred Sectionals and Position Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and official [RQ Open Data Web Services
protocol](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).

Exactly **19 original official Doomben CSV meeting dates**
spanning 2026-01-14 through 2026-10-05 were
preselected by the *earliest and latest
published Doomben source CSV per month*
(and October's single available date).
For each date, race numbers **1–6** were
attempted. No time series was enlarged
on the basis of measured ICC.

Data join: \`GetMeetingsForDate\` →
\`GetRacesForMeeting\` → \`GetHorsesForRace\`,
then unique original date/race exact
name to official positive first-section
GPS with original numeric HORSES IDs.
Duplicates, ambiguous same-day names
and all-zero sectional timing are
excluded without calling them DNFs
or proven scratches.

Original IDs, animal names, rider/trainer
licence IDs and times remain in memory.
Only race/date/marker counts, source
hashes, status and anonymous model
statistics enter the archived JSON.

## First original-source feasibility outcome

| Stage/quantity | Original-source observation |
| --- | ---: |
| Prelocked dates requested | 19 |
| Original meeting dates successfully processed | **18** |
| Original meeting date on source HOLD | **2026-08-26** |
| Positive first-GPS original HORSES-ID observations (across processed dates) | **617** |
| Different original HORSES IDs | **541** |
| Original IDs present on two or more dates across marker groups | **65** |
| HORSES IDs seen 4+ source dates/starts | **2** |
| 150m first-interval candidates | **177** |
| 150m original races | **24** |
| 150m distinct official HORSES IDs | **166** |
| 150m IDs recorded on 2+ source dates | **9** |
| 150m source meeting dates represented | **14** |
| 200m positive first-interval source candidates | **205** |
| 200m distinct official HORSES IDs | **195** |
| 200m IDs recorded on 2+ source dates | **9** |
| 200m source meeting dates represented | **14** |
| 200m candidates retained in >=4-timed-horse fields | **193** |
| 200m original races retained in model | **27** |
| Numerically supported ICC at either 150m or 200m | **NO: both HOLD** |
| Matched-marker numeric ICC bridge to either previous venue | **0** |

The full original Doomben first-marker frequency includes
110m, 150m, 200m, 215m, 220m, 230m, 240m,
250m, 260m and 270m. Although individual
HORSES IDs recur across dates in the
*pooled* original sample, there were
**only NINE** repeated original HORSES IDs
at each of the **exact 150m** and **200m**
first-marker strata across at least two dates,
below the existing **20-ID support gate**.
This is the specific quantitative reason the
ICC models return HOLD: 177 source 150m
records and 205 source 200m records are
mostly one-off individuals, not longitudinal
replication of the same animals.
The source collector never returns an
ICC=0 fallback if repeat support is absent.

### Upstream API failure (not absence of animals)

Original 2026-08-26 Doomben had a published
first-party sectional CSV with 8 race headers
and multiple positive GPS horse rows;
its exact original first-party calendar
\`GetMeetingsForDate\` returned a verified
Doomben meeting identifier.

However a read-only official call to
\`GetRacesForMeeting\` for that meeting
returned an **upstream SQL
string/binary truncation error** from
the Racing Queensland web service,
rather than a usable source \`<Races>\` XML
with numeric race IDs. This is a
**data-provider/API availability failure**;
it does not imply zero racehorses,
zero starts, zero variance, or a
legitimate scientific exclusion of
unfavorable outcomes.

The original aggregate error code for 2026-08-26
was `HOLD_NO_OFFICIAL_SELECTED_RACES`,
rather than a loss of GPS horse
recordings. A separate read-only
inspection of the official SOAP
`GetRacesForMeeting` endpoint showed
that it returned a text database
string/binary truncation error instead
of the expected XML race list.
No missing race was invented.

The full locked 19-date source cohort
is therefore **PARTIAL/HOLD**.
The program deliberately does **not**
guess official race identifiers from
races named in the GPS CSV, nor use
outcome-dependent replacement dates.
It records the source date as HOLD.

## Methods and limits

The same first GPS interval
\`first_section_sec(i,r)\` Gaussian
race fixed-intercept + original HORSES
random-intercept REML machinery as
the Cannon Park/Eagle Farm studies
was reused, including its preexisting
minimum repeated individual, race and
date support gates. A numerically
identifiable 150m/200m point was
**not fitted**.

The original first-section marker
may correspond to different route
and class cohorts across venues.
Even if a marker-specific ICC
becomes numerically estimable
later, numeric similarity alone
does not show genetic personality,
causal course effects or the same
individual animals followed between
tracks. The source is still a
single operator's GPS technology;
true final starter/finisher statuses,
jockey/weight assignment and age
remain partially unresolved.

**H1 wet-ground individual
reaction-norm slope variance:
NOT TESTED / HOLD.**
**H2 opponent-composition/social
interaction: NOT TESTED / HOLD.**
No fitness, natural selection, genetic
heritability or wagering prediction.

## Replication

~~~bash
python -m unittest discover -s tests -p 'test_ecology_rq_doomben_third_venue_icc.py' -v

python scripts/ecology_rq_doomben_third_venue_icc.py \
  --output tmp/rq-doomben-2026-third-venue-aggregate.json
~~~

The CI reads precisely 19 allowlisted
official source dates and 6 numbered
races/date, with original source hashes,
no individual source data published.
No additional dates may silently
replace the original API failure.
Source support counts are
**feasibility diagnostics, not
a hypothesis test**.


## Snapshot reproducibility improvement

In addition to the original Meeting, Race
and GPS CSV SHA-256 hashes, the audit
now computes a **combined anonymous hash
of every GetHorsesForRace original
roster XML response**, grouped by
original meeting date, plus the number
of original rosters hashed. This
prevents a future discrepancy from
being silently attributed to changed
animal biology if the upstream RQ
historical entrant list changes while
the GPS CSV remains byte-identical.
No numeric horse ID, race ID or
roster payload is exported.

The identity source may be updated by
the provider after the original event:
a cryptographic source fingerprint
provides repeatability of the **data
snapshot**, not evidence of valid
official starter or finisher status.
