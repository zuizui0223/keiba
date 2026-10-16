# Cross-venue official HORSES-ID overlap: a measurement/individuality gate

**2026-10-14; source audit extension to draft PR #2.**


## Verified 24-date original-source aggregate (2026-10-14)

The first original official-source execution completed successfully:
[GitHub Actions run #38421064924](https://github.com/zuizui0223/keiba/actions/runs/38421064924).
This is the parallel source-ID-overlap implementation
(scripts/ecology_rq_cannon_eagle_id_overlap.py), not a new sample
chosen after looking at this result.

| Locked source metric | Cannon Park | Eagle Farm |
| --- | ---: | ---: |
| Original source meeting dates successfully audited | 12 / 12 | 12 / 12 |
| Eligible positive first-GPS source records | 548 | 391 |
| Distinct numeric official HORSES IDs | 280 | 339 |

Across both tracks, 617 unique official IDs were observed, and **2
IDs appeared in both venue cohorts**, with consistent names and no
same-calendar-date two-venue conflict. These counts were computed
in memory from each venue's original-source positive-GPS records,
not from a guessed name-only join. Of the two cross-venue shared IDs:

- **1** had at least one identical first-GPS measurement marker;
- **0** had both identical first marker AND official race distance;
- **0** had identical marker, distance AND official source class;
- **0** had two independent source dates on **each** track.

The narrow data conclusion is that very few IDs overlap and the
paired, properly matched-interval sample does **not** support a
cross-track within-individual comparison. This is NOT evidence
that biological repeatability is zero, or proof that site,
horse genotype, fitness, training or competition determines pace.
The previously estimated separately pooled track ICCs
(0.431738 / 0.452894) remain model- and measurement-conditioned;
do not report their similarity as a direct same-trait replication.


This document specifies an exploratory **data-feasibility** check.
It reports no cross-venue biological effect and does not reinterpret the
earlier Cannon Park / Eagle Farm ICC point estimates as replication.

## Why this audit comes before a stronger ecological claim

Race-adjusted first-GPS-interval ICC was numerically positive in
the separately analysed Cannon Park and Eagle Farm RQ source cohorts.
However, the observed interval markers differ between the fitted
samples, there is no same-marker ICC supported at both venues, and
the two samples have not been shown to contain the same horses.

The fundamental next question is whether **individual official
HORSES IDs actually recur across both locked tracks**. If not,
the pooled ICCs cannot be claimed to describe the same individuals
in two environments. If yes, a further gate asks whether those
same animals have positive initial GPS intervals at exactly the
same first-marker distance (and the same original race distance).

## Immutable source inclusion: no outcome-driven extension

This check uses ONLY the already documented, fixed dates/races:

- Cannon Park: 12 previously frozen 2026 meetings through
  2026-10-11, existing official race-number selection 1–8
  (docs/ecology-rq-2026-calendar-cohort-lock.md).
- Eagle Farm: 12 separately frozen 2026 meetings through
  2026-10-10, existing official race-number selection 1–6
  (docs/ecology-rq-eagle-farm-2026-independent-track-lock.md).

These source selections predate this particular ID-overlap result
and were not created based on cross-venue outcome inspection. They
are **NOT prospective preregistration** of a biological hypothesis.
No dates are appended because too few cross-venue animals are found.

Both venues use the same RQ data operator, so this is not an
independent sensor/vendor replication. Read the official
[Racing Queensland Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and [Open Data conditions](https://www.racingqueensland.com.au/about/reports-and-data/open-data).

## Verified original-source result: two linked horses, zero matched race contexts

The first end-to-end original public RQ read of both **previously
frozen 12-date** cohorts succeeded (24 out of 24 dates audited).
Independent real-source [GitHub Actions run #38421064924](https://github.com/zuizui0223/keiba/actions/runs/38421064924)
reported:

| Cross-venue source screen | Verified value |
| --- | ---: |
| Cannon Park positive GPS records linked to original HORSES IDs | **548** |
| Eagle Farm positive GPS records linked to original HORSES IDs | **391** |
| Distinct original HORSES IDs in Cannon Park | **280** |
| Distinct original HORSES IDs in Eagle Farm | **339** |
| Distinct numeric official HORSES IDs in both sites | **2** |
| Same official ID but conflicting normalized source name across the two sites | **0** |
| Same official ID recorded at both distant sites on the exact same calendar day | **0** |
| Safely recurring IDs with positive original GPS at both venues | **2** |
| Those shared IDs with any identical first measured GPS segment marker | **1** |
| Same shared ID with identical first marker AND race distance | **0** |
| Same shared ID with identical marker, distance AND original Class | **0** |
| Same shared ID with 2+ distinct original meeting dates in BOTH sites | **0** |

An independent implementation of the same locked
race/identity filters also produced two safely recurring
numeric official HORSES IDs, no common marker+distance+class
strata and 24 successful source dates. The research
branch was subsequently consolidated to **one maintained
source-of-truth implementation**,
\`scripts/ecology_rq_cross_venue_identity_support.py\`,
to avoid maintaining duplicate screens. That canonical
script also records **SHA-256 fingerprints** of both
venues' original official source responses in its
aggregate JSON without publishing individual animal
identities or records.

This finding is about **population/measurement overlap**.
Although both source-conditioned venue-specific Gaussian
race-FE horse ICC point estimates were positive
(Cannon Park 0.431738; Eagle Farm 0.452894),
the positive ICC models refer to **largely different
sets of horses and disjoint well-supported first
GPS interval marker cohorts**. Therefore the
similar-looking pooled ICC values are **NOT a
within-animal test of course-specific ecological
reaction or replication of a universal individual
trait**.

Nor does a count of two shared original IDs
establish how often the same horse travels
between tracks in the population: the
cohorts were small, purposively chosen source
subsets, nominatees are not guaranteed
actual starters, and GPS telemetry may be
missing in a nonrandom way. Source-record
absence is not a zero biological probability.

**Scientific decision: direct, source-matched
within-horse cross-venue comparison HOLD.**
This is a valid negative *feasibility result*,
not evidence for no environmental plasticity.

## Exact gates and interpretation

1. The existing date-specific SOAP GetMeetingsForDate,
   GetRacesForMeeting and GetHorsesForRace candidate lists
   are linked to unique, exact-name **positive** original first-GPS
   sectional records. Nominations and zero GPS do **not**
   establish actual race starts, withdrawals or DNF.
2. Within either venue, an official numeric HORSES ID associated
   with inconsistent normalized names is excluded in full.
3. Two tracks can be linked only by the **same official numeric
   HORSES ID with exactly the same normalized source name**.
   A matching name alone is NOT sufficient to join different IDs.
4. If the same ID has positive first-section records at **both
   distant tracks on the same calendar date**, it is removed
   from cross-site feasibility because the source identity/race
   cannot be reconciled; this does not diagnose the cause.
5. Counts are calculated for shared valid horse IDs, then for
   shared IDs with the **same original first distance marker**,
   then with identical official race distance, then identical
   source Class. Separately count IDs with at least two
   distinct source dates **per track** at the identical marker,
   and per track within the same marker+distance stratum.
6. Only counts/coverage/HOLD codes are emitted. Never export
   animal names, official animal IDs, rider/trainer licence IDs,
   raw individual first-section times, predictions or records.
7. Any failed original source date is logged as **HOLD source
   coverage**, never an absence of animals or biological
   non-response. Cross-site sample-size counts remain
   provisional until all 24 dates pass the source audit.

**Source-readiness decision:**
- No valid shared official IDs: HOLD_NO_VALID_SAME_HORSE_ID_ACROSS_TWO_VENUES.
- Shared IDs but no shared first GPS distance marker:
  HOLD_SHARED_HORSE_IDS_BUT_NO_IDENTICAL_FIRST_GPS_MARKER.
- Some same-ID same-marker telemetry:
  EXPLORATORY_CROSS_VENUE_ID_AND_MARKER_DATA_SUPPORT_ONLY;
  still NOT same segment calibration, official finish,
  environmental slope, competitor effect, or heritability.
- Missing source dates: top-level
  SOURCE_COHORT_INCOMPLETE_HOLD_CROSS_VENUE_INFERENCE,
  regardless of exploratory counts.

This audit purposely does **not** fit a new ICC, p-value,
confidence interval, horse-by-venue interaction or H1/H2 model.
A same marker does not by itself prove the two GPS files use
identical interval definitions or error characteristics.
The previously published pooled ICCs must retain their
separate, source-conditional interpretations.

## Reproducibility and next research gate

Code: scripts/ecology_rq_cross_venue_identity_support.py.
Fabricated-only unit tests:
tests/test_ecology_rq_cross_venue_identity_support.py.
Official aggregate-only action:
.github/workflows/ecology-rq-cross-venue-identity.yml.

    python -m unittest discover -s tests -p 'test_ecology_rq_cross_venue_identity_support.py' -v
    python scripts/ecology_rq_cross_venue_identity_support.py --output tmp/rq-cross-venue-horse-ID-support.json

The actual 24-date cohort yielded **two original-ID matches
but zero first-marker+official-distance source strata**.
Future scientifically defensible work needs a documented
common first-sectional measurement definition, consistent
race distance/classes, representative repeated animal-ID
coverage, complete starter/finish data, and independent
time/venue replication. Do not force model significance
or retroactively change the locked date selection.
