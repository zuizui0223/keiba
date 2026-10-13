# Cross-venue official HORSES-ID overlap: a measurement/individuality gate

**2026-10-14; source audit extension to draft PR #2.**
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

Once the real 24-date coverage is verified, document the actual
aggregated overlap in this file and PR #2. If this overlap fails,
identify a next independent cohort or a **documented** common
first-GPS measurement rather than forcing model significance.
