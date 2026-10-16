# Rider-change persistence audit: frozen post-hoc methods, not H1 or H2

**Design added 2026-10-14 to the ecological Draft PR #2, before fitting this rider-switch diagnostic on the original source records.** Previous positive Cannon Park first-GPS repeatability and ICC were already known, so this is explicitly **a post-hoc exploratory sensitivity**, NOT an independently preregistered hypothesis or confirmatory test.

## Question

For the **same official numeric HORSES ID**, and an identical official
race distance plus first GPS measurement marker, is the sign/magnitude
of its *race-relative early sectional time* more consistent across
different original meeting dates **when the documented source Jockey/@Id
licence changes** than would be expected under a simple reallocation
of observed first-GPS timing values within each original race?

A positive signal under a source-declared different rider cannot fully
be explained by **always observing an identical declared jockey**,
but it may still reflect stable trainer, rider selection, training,
unobserved fitness, age or nonrandom race entry. Jockey/@Id is a
nomination/source record and **not independently confirmed as the
post-race actual jockey**.

## Fixed source population and measurement

- Original first-party Racing Queensland source, **the previously frozen 12
  Cannon Park 2026 meeting dates** and requested race IDs 1–8.
  Do not add or drop source dates based on the estimated effect.
- Use the existing original SOAP HORSES ID and same-race-name GPS
  positive first-section join. Include source races with **>=4 positive
  GPS horse records**, irrespective of whether each peer has rider
  metadata. This keeps the **same timed-GPS peer baseline** for the
  documented-rider focal horses; a non-documented rider can still be
  part of the contemporaneous relative-timing denominator.
- The response is
  `first_GPS_section_sec(horse) - mean(first_GPS_section_sec(other
  positive-GPS horses in that race))`. It is **race-relative**
  seconds, not a verified full distance time or absolute speed.
- Make pairs across **different original meeting dates only**, with
  identical focal original HORSES ID, official race distance and exact
  first GPS marker. The main pair requires both source Jockey/@Id
  values valid and *different*. Compare same-rider pairs as a separate,
  descriptive subgroup on these same source/gating rules.
- Secondary stricter design adds equal official race Class; optional
  same documented Trainer/@Id in both records is a supplementary
  screen, not a trainer-causal identification.
- A 90-day within-year gap cut (<=90 versus >90 days) is a descriptive,
  fixed follow-up and cannot be called evidence of temporal-decay
  differences; the subset of horses can differ by gap.

## Unit of analysis and falsification

Aggregate *within each horse-by-distance-marker* pair products
`d_ir * d_is` in seconds squared, then **equally weight all distinct
horse-by-stratum groups** (avoids overweighting prolific horses).
Report IDs, stratum count, unique meeting dates, distinct date-pair
combinations and individual within-horse date pairs.

A main descriptive numeric mean pair product is **HOLD** unless all are
satisfied: at least **20 distinct eligible HORSES IDs**, 20 distinct
horse-strata, at least 6 contributing original meeting dates, and at
least 6 distinct meeting-date-pair combinations. These are
conservative design-support thresholds, not statistical power claims.
If the threshold fails, export only counts and an explicit HOLD;
do not report a numerical zero as the observed biological signal.

If the main switched-rider gate passes, permute **only** the
race-relative first-section outcomes among horse records **within
each original race** for 199 fixed-seed reference iterations, keeping
the observed HORSES IDs, horse-to-rider metadata association, race
conditions, field sizes, and source date assignments fixed. Report
the observed mean pair product and 5/50/95% null quantiles and an
*algorithmic upper-tail reference fraction*; it is **not** a valid
causal or confirmatory p-value (nonexchangeable entries,
nonnested repeated pairs, source missingness, post-hoc question).
Same-rider and Class-matched results are secondary, not effect
estimates of changing jockey.

This source analysis has no verified starter/finisher list, actual
rider assignments, GPS missingness model, biologically measured
personality, validated age/family data or random assignment.
H1 horse-by-ground random slopes, H2 competition interactions,
selection/adaptation/genetics, horse–jockey causation and wagering
predictions remain **HOLD / not analysed**.

## Output and privacy contract

The script and GitHub Actions workflow must export **anonymous counts,
mean summaries and HOLD codes only**. No original horse name, HORSES
ID, rider/trainer licence ID, source XML, row-level first-section
times, horse-specific results or betting advice. Use the already
documented original-source licence and attribution requirements.

Primary program: `scripts/ecology_rq_rider_switch_consistency.py`.
Synthetic-only test suite:
`tests/test_ecology_rq_rider_switch_consistency.py`.
Official source re-execution:
`.github/workflows/ecology-rq-rider-switch.yml`.

The only potentially supportable advance is a narrower
**source-conditional cross-rider persistence diagnostic**.
An observed effect with documented rider changes would reduce one
simple alternative explanation, NOT establish intrinsic biology.
