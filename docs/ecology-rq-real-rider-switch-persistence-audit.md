# Real-source documented-rider-change and early sectional persistence audit

**2026-10-14. Post-hoc exploratory observation, NOT a causal jockey effect, H1 reaction norm, H2 competitor effect, genetic personality or preregistered test.**

The source-eligibility and minimum support rules were fixed in
[the rider-switch design](ecology-rq-rider-switch-persistence-design.md)
before estimating this new rider-switch result, but the project already
knew the general Cannon Park horse-ID repeatability result.

Official source: [Racing Queensland Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and original same-race horse-name to numeric HORSES ID join from GetHorsesForRace.
Source population: previously locked 12 dates at Cannon Park during 2026,
race numbers 1–8 as available in official records.
Independent initial run: [GitHub Actions #38492841107](https://github.com/zuizui0223/keiba/actions/runs/38492841107)
(12 fictional validation tests and real-source calculation passed).

## What is actually measured

Within each observed GPS-positive race with at least four GPS-positive
horses, compute the focal horse's first-section time MINUS the mean first
sectional time of its other GPS-positive peers (seconds). An incomplete
jockey record among peers does NOT remove that horse from the peer average.
Link the same original HORSES ID across different original meeting dates,
holding official race distance and exact first GPS distance marker fixed.
Define the pair product between two relative time deviations in seconds
squared, then average within horse-by-distance-marker strata and give
each stratum equal weight.

The main set requires a *different* original Jockey/@Id on both
observations. This is the API's recorded/nominated jockey licence,
not independently verified final post-race rider assignment.

## Genuine original-source result (first RQ re-fetch)

| Quantity | Finding |
| --- | ---: |
| Source meetings | 12 / 12 |
| Original HORSES ID + positive first GPS candidates | 543 |
| GPS-positive rows retained at minimum four GPS horses/race | 519, 74 races |
| Retained rows with original numeric Jockey/@Id | 378 |
| Same horse, first GPS marker and race distance; different declared Jockey/@Id | 36 horses, 38 strata, 72 across-date pairs |
| Distinct meeting-date combinations in rider-switch pairs | 37 |
| **Changed-rider mean pair product** | **+0.063583 sec²** |
| Same declared jockey, descriptive comparison | 44 horses, 57 pairs, +0.057932 sec² |
| Different declared jockey with same known Trainer/@Id | 29 horses, 64 pairs, +0.070513 sec² |
| Different jockey plus same original race Class | 20 horses, 32 pairs, +0.069282 sec² |

The comparison of +0.063583 versus +0.057932 is NOT a causal effect
of changing a rider: the same- versus switched-rider subsets contain
different horses, and just 11 horse-by-context strata had both types
of within-animal pair. The stricter same-Class/same-jockey subgroup
has only 19 distinct source horse IDs and is HOLD under the fixed
20-ID minimum. Same-class/change-jockey+same-trainer has 16 IDs
and is also HOLD. No new genetic or ground-response claim follows.

In 199 seeded within-original-race *outcome* reassignments,
retaining the factual horse/rider labels and field/date membership,
the reference mean was **+0.001996 sec²** and the
5th/median/95th quantiles were **-0.023492 / +0.001769 / +0.030502 sec²**.
An exploratory upper-tail reference fraction was **1/200 = 0.005**.
This is **not a confirmatory p-value**: entries are nonrandom,
multiple pairs share animals, original roster status is incomplete,
rider assignments are unvalidated, and the question is post-hoc.
The positive result supports only source-conditional ID-associated
early relative timing persistence under *differently documented* riders.

Fixed time-lag description: within 90 days, 24 IDs/35 pairs/
+0.051879 sec²; over 90 days, 24 IDs/37 pairs/+0.080458 sec².
These are differently selected horse/context subsets: they
do not identify temporal stability or training-memory decay.

## Critical source snapshot discrepancy

Earlier archived Cannon Park analysis [#38411913010](https://github.com/zuizui0223/keiba/actions/runs/38411913010)
contained **548** original positive matched source candidates and
**523** timed rows retained after the race threshold. This rider
re-fetch has **543 / 519**. Comparing the saved per-date source
fingerprints from the earlier canonical original-source artifacts
showed identical **meeting XML, race XML and source GPS CSV SHA256
digests at all 12 dates**. Five specific source dates each had
one fewer matched candidate: February 16, March 26, April 9,
August 28 and October 11, 2026. The shared source auditing code
was not modified between the initial cross-venue source run and
this new rider analysis.

The earlier audits **did not retain a fingerprint of each
GetHorsesForRace response**, so source-roster updates or inconsistent
live roster returns remain possible but **unproven**. The new rider
script adds an anonymized per-date hash of all returned original
HORSES XML responses and records a flag when current candidate
counts differ from the original 548. It cannot retrospectively
recover missing historical XML hashes, or assert that earlier
horse-level records and the new 543-candidate sample are identical.

Thus **do not compare this rider-change persistence number as if it
used exactly the prior 548-record Cannon cohort**, and do not
interpret source candidate changes as changes in true starts,
DNF, population size or behavior.

## New same-source influence checks: all 12 dates and all 36 horses

After [the post-hoc deletion design was committed](ecology-rq-rider-switch-influence-design.md),
the new code performed all individual source-day and anonymous animal
influence calculations on a **fresh, complete 12/12 official-source read**:
[GitHub Actions #38498881524](https://github.com/zuizui0223/keiba/actions/runs/38498881524).
All 176 synthetic/QA tests passed in
[research CI #38498881472](https://github.com/zuizui0223/keiba/actions/runs/38498881472).

The identical source-conditional 543-candidate cohort was recovered
(519 first-GPS rows from 74 races after the >=4 timed GPS peer threshold,
378 rows with documented numeric Jockey/@Id).
The original changed-declared-jockey indicator remained
**36 HORSES IDs, 38 strata, 72 across-date pairs** and
**+0.0635832314 seconds squared**.

| Post-hoc deletion, preserving the already observed race-relative peer baseline | Result |
| --- | ---: |
| Original meeting-date deletions attempted | **12** |
| Date deletions still passing the same >=20-ID and remaining source support gates | **12/12** |
| Positive date-deletion mean pair products | **12/12** |
| Date-deletion minimum and maximum | **+0.045540 to +0.080127 sec²** |
| Original contributing HORSES-ID deletions attempted | **36** |
| Anonymous ID deletions passing the original source-support gates | **36/36** |
| Positive horse-deletion mean pair products | **36/36** |
| Anonymous horse-deletion minimum and maximum | **+0.049043 to +0.067635 sec²** |

**Largest sensitivity among dated sources:** Omitting the
2026-08-22 original meeting gave **+0.045540 sec²**;
omitting 2026-05-29 gave **+0.080127 sec²**.
Both retained positive descriptive results and passed the original
numeric support gate. These are the extrema after deleting a single
date, NOT a 95% confidence interval, independent sample validation
or causal experiment.

**Biological scope:** The signal was not carried solely by any one
original horse ID or any one meeting date in this observed cohort.
The removal of a horse's pair contributions keeps other horses'
contemporaneous GPS-peer reference fixed, specifically to avoid
changing other horses' dependent variables by definition.
No deleted individual's ID, date-specific individual trajectory
or pair-product contribution was exported.

### Rider documentation differs by source going

Among the **519 positive-GPS timed observations**,
valid numeric Jockey/@Id was present in **378 (72.8%)**.
The aggregate observed-source coverage by original race rating was:

| TrackRating | Timed rows | Numeric Jockey/@Id documented | Fraction |
| --- | ---: | ---: | ---: |
| Good | 180 | 120 | **66.7%** |
| Soft | 206 | 154 | **74.8%** |
| Heavy | 133 | 104 | **78.2%** |

This illustrates nonuniform source-rider documentation.
It is **conditional on observed positive GPS timing**, NOT
the completeness of true starters, and does not identify MCAR/MAR/MNAR
or biological differences among the missing horses.
The cross-rider analysis therefore remains a selected subset.

### Source availability and provenance: fail-closed, then full re-fetch

An intermediate official-source re-fetch
[run #38493337639](https://github.com/zuizui0223/keiba/actions/runs/38493337639)
succeeded in **3/12 dates only**; the other 9 dates raised
HTTP errors/timeouts. The script correctly reported
`HOLD_SOURCE_DATES_UNAVAILABLE_FOR_RIDER_SWITCH_INFERENCE`
with no partial biological estimate, even though the workflow
process finished green. This is a source-availability HOLD, not a zero
effect or a biological source-free result.

The later full re-fetch #38498881524 recovered **12/12** original
dates and the same positive 36-horse source-conditioned outcome.
For the three dates successfully read in BOTH of those recent runs
(2026-05-29, 2026-08-28 and 2026-08-29), the newly archived
**per-date aggregate original HORSES roster XML SHA256**, plus
meeting/race/GPS SHA256 and candidate row counts, all matched
exactly across runs. That demonstrates *recent partial source
snapshot reproducibility*, not retroactive verification of the
older 548-candidate original cohort: its horse-roster digests
were never captured.

The earlier **548 vs 543 candidate** discrepancy and the distinction
between documented nominated and actual postrace rider identity remain
unresolved. Thus even this successful all-deletions sensitivity
does **not** establish stable intrinsic animal personality, a jockey
cause, genetics, ecological ground responses H1 or competition H2.

## Biological inference boundary

The source-linked 36-horse repeated-rider-ID subgroup provides
additional descriptive support for identity-related early
race-relative timing persistence and rules out the simple statement
that *all* measured repetitions must have the same documented
jockey. It DOES NOT isolate an intrinsic horse trait from stable
trainer assignments, training/fitness, jockey selection,
source missingness, changes in competitor composition or sensor
error. The actual postrace riders, official final starters,
individual certified finish times and horse ages have not
been independently verified.

H1 environmental reaction-norm variance, H2 competitor social
interactions, adaptation, heritability and betting accuracy remain
unidentified. Report this as a **post-hoc source-conditioned
descriptive persistence diagnostic** only.

Method: scripts/ecology_rq_rider_switch_consistency.py.
Fictional tests: tests/test_ecology_rq_rider_switch_consistency.py.
CI: .github/workflows/ecology-rq-rider-switch.yml.
No original animal names, HORSES IDs, rider/trainer licence IDs
or per-horse interval times are published.
