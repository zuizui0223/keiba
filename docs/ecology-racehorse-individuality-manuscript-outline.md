# Ecological individuality in Thoroughbred early pacing: manuscript claim map

**Draft research synthesis, 2026-10-15.** This document reports existing
verified original-source results; it does not claim a new experiment,
an independent external replication, a biological genetic personality
effect, or prospective preregistration.

## Working title

**Individual-associated consistency in race-relative early pacing:
longitudinal evidence and the limits of observational attribution**

## Primary question and inference ladder

Does the same officially identified racehorse retain information about
its relative early pacing across races, even when the source-nominated
rider changes? And can this information be distinguished from a
generic matched race context or historical records of other horses
associated with the same nominated trainer or rider?

The defensible primary claim is **source-conditional horse-ID-associated
temporal consistency in initial GPS pacing**, not intrinsic personality.

### Evidence A — source-linked repeated identity

In the previously fixed 2026 Cannon Park source cohort,
race-conditioned horse-ID repeatability is positive under a
Gaussian random-horse / fixed-race model. Current-source
ICC about 0.430, with 299 fitted-model Gaussian simulations
yielding a 0.314–0.528 re-estimated ICC quantile range.
This is **not** a validated population confidence interval.
Eagle Farm also gives a positive source-conditional pooled ICC
about 0.453, but uses different GPS marker distributions;
the two numbers are NOT matched-trait cross-site replication.
Doomben does not meet the repeated-animal source threshold
for a marker-specific ICC.

### Evidence B — changed documented rider, same horse/context

Cannon Park: 36 official HORSES IDs, 38 horse-by-distance-marker
strata and 72 different-date pairs with different source
Jockey/@Id. Mean pair product of race-relative early GPS
time deviations +0.063583 seconds squared. All 12/12
single-meeting deletions and 36/36 anonymous single-horse
deletions remain positive under the original support gates.
This cannot establish the final actual race rider.

### Evidence C — strictly chronological forecast

Among 36 HORSES IDs and 46 later observations, the focal
horse's strictly earlier, fixed-shrinkage historical relative
GPS profile improves equal-horse-weighted RMSE from
0.297676 (zero-personalization baseline) to 0.255809 seconds,
about a 14.1% reduction. This is a retrospective
*postrace-field-relative* outcome, not a pre-race prediction
or independent source validation.

### Evidence D — alternative past histories

On the same 36 IDs / 46 future observations, the focal horse
profile RMSE 0.255809 s beats the earlier OTHER-horse
same-distance/same-GPS-marker historical benchmark
RMSE 0.303195 s, a difference of 0.047386 s.
Other-horse historical benchmarks restricted to the same
source-documented trainer (23 IDs/31 later records) or
source-documented jockey (32 IDs/39 records) also have
larger errors than the focal horse's profile *on each
respective matched subset*. These different subsets
are not causal contrasts. The stricter Class-matched
comparison (20 IDs/22 records) lies at the exact
minimum support boundary and is secondary.

## Crucial source edition boundary

An older Cannon Park 2026 12-date source artifact has 548
HORSES-ID-positive-GPS candidate joins; later source
snapshots have 543. On exactly five dates, the later
source join count is one smaller. All 12 meeting XML,
race XML and GPS CSV SHA256 digests match across the
two archived editions, but original per-race HORSES
roster response hashes were not archived for the
older run, and analysis code also changed.

Therefore, the cause is **HOLD**: roster update versus
joining/parser revision cannot be distinguished.
The later 543-row edition IS independently reproducible
across 12 dates with all four original upstream
response types and per-date join counts matching the
permanently pinned source manifest. The source version
problem is not an ecological effect.

## Methods for paper

- Retrospective, observational, single primary course;
  original official Racing Queensland race/horse roster
  and positive first-GPS sectional joins.
- Fixed original Cannon Park 12 dates and official race
  selection; race-relative response = focal first GPS
  interval time minus mean of other GPS-positive horses
  in the same race. Include races with at least four
  GPS-positive observations.
- Link same numeric HORSES ID only with unique normalized
  official same-race horse name; avoid guessed name-only
  matches and invalid/zero GPS observations.
- Original Jockey/@Id and Trainer/@Id reflect source
  documentation, not independently verified final
  race-day assignment. Their missingness is nonuniform.
- Within-horse historical profiles use only strictly
  earlier dates in the identical official race distance
  and first GPS marker context; deterministic n/(n+2)
  shrinkage toward zero, no tuned hyperparameters.
- Compare equal-HORSES-ID-weighted RMSE on the same
  future rows to zero, other horses' matched-context
  histories, and other horses with matching documented
  jockey/trainer. Apply minimum 20 IDs, 20 future rows,
  6 dates, 20 context strata; insufficient strata HOLD.
- Do not present post-hoc model-conditional Gaussian
  simulation quantiles as robust 95% confidence intervals,
  or same-cohort forward scores as independent external
  validation.

## Candidate manuscript abstract

Individual consistency in animal movement can reflect
stable organismal differences, but repeated observations
also combine individual history with environmental
context, nonrandom participation and measurement
selection. We evaluated race-relative early GPS
sectional timing in retrospectively linked
Thoroughbred records from a fixed twelve-meeting
Cannon Park source cohort. Race-conditioned
horse-ID repeatability was positive under a
Gaussian variance-component model. Among
36 horses with different source-documented rider
identifiers across matched early-section contexts,
within-horse timing deviations were positively
associated across dates and remained positive
after each single-meeting and single-horse deletion.
In a strictly chronological evaluation of
46 later observations, the horse's own earlier
timing profile reduced equal-horse-weighted
prediction error relative to both a zero
individual-history baseline and the historical
profile of other horses under the same
measurement context. These findings indicate
that source-linked individual history carries
information about subsequent race-relative
early pacing beyond a generic race-context
average. However, the data do not isolate
intrinsic behavioral personality from training,
selection, actual rider assignment or sensor
coverage. Cross-venue measurements lack a
shared sufficiently repeated GPS interval,
and historical source roster editions differ.
We therefore interpret the results as
observational, measurement-conditional
individual-associated temporal consistency
rather than causal or evolutionary evidence
of stable intrinsic temperament.

## Suggested figures and tables

- Figure 1: original source lineage and eligibility
  flow, including the 548-to-543 snapshot caveat.
- Figure 2: time-ordered same-horse versus zero and
  other-horse matched-context RMSE; equal-horse weights.
- Figure 3: 12 leave-date and 36 leave-horse
  aggregate influence ranges (not confidence intervals).
- Table 1: source coverage, GPS marker and documented
  rider/trainer missingness.
- Table 2: same-Class and role-specific matched
  benchmarks, with insufficient groups marked HOLD.

## Required independent validation before stronger claims

1. Rights-cleared, source-pinned independent future
   longitudinal horse cohort with at least two genuinely
   repeated same-marker/distance observations per horse.
2. Official verified final starter and actual jockey
   assignment; age, trainer and race-condition histories.
3. Defined population of all starters and documented GPS
   missingness, including non-random availability.
4. Pre-fixed identical prediction, no new threshold tuning,
   date-grouped uncertainty and independent source
   reproducibility checks.

No evidence currently identifies H1 horse-by-ground
reaction-norm variance, H2 causal opponent interactions,
genetics, heritability, selection or adaptation.
No individual horse predictions or betting guidance
are produced.

## Audit trail

- docs/ecology-rq-real-icc-source-conditional-sampling.md
- docs/ecology-rq-real-rider-switch-persistence-audit.md
- docs/ecology-rq-rider-change-forward-validation-results.md
- docs/ecology-rq-forward-other-horse-comparator-results.md
- docs/ecology-rq-cannon-original-source-drift-20261014.md
- docs/evidence/rq-cannon-original-source-fingerprints-20261014.json
