# Forward-only historical horse profile under a newly recorded source jockey

**Methods committed 2026-10-14 before examining the new forward-only error metric.**
This is an **exploratory / post-hoc** question that follows already
observed positive original Cannon Park HORSES-ID repeatability and
cross-jockey pair-product results. It is NOT a confirmatory experiment
or new independent racing population.

## Question

Within the already frozen twelve 2026 Cannon Park original meeting
dates, can a horse's **strictly earlier** race-relative initial
GPS timing profile forecast its **later** relative initial GPS timing
when the later original source records a *new* Jockey/@Id that has
not appeared for that horse in its previous **matched-context**
source records? The target is biological/observational persistence,
not betting, returns, rank, or a proven jockey effect.

**Do not enlarge the calendar, switch the time split based on
outcomes, use same-date/future horse values, or read other racecourses.**

## Source and data filter

- Reuse the existing rider-switch script's source_timed_panel,
  built on the previously locked 12 Cannon Park meeting dates,
  Races 1–8 as actually available, with >=4 GPS-positive
  horses/race, original numeric HORSES ID and exact same-race
  horse-name join. Invalid or zero GPS signals are unavailable,
  never a DNF or biological zero.
- Outcome: horse's first GPS sectional time minus the **mean first
  sectional time of all other GPS-positive horses in the same
  original race**, in seconds. Its target *requires the completed
  race and the realized GPS peer sample*; do not call it
  prospective pre-race speed, racing rank or betting prediction.
- Historic context: **same official race distance AND exact first
  GPS distance marker**; repeat as a stricter secondary screen
  also requiring same official Class label. No class/marker
  interpolation. All horse dates must be strictly earlier
  than the test date.
- At each original date, compute predictions first, then add
  all eligible observations from that date to history. This
  prevents same-day/future leakage even when multiple races
  are listed.
- Prior horse profile: mean of ALL earlier GPS-positive
  race-relative initial intervals in the matched stratum,
  shrunk deterministically by **n/(n+2)**. This is the
  previously used unoptimized fixed shrinkage in
  ecology_rq_early_pace_repeatability.py. No new tuning on
  test outcomes.
- New documented rider test gate: current source Jockey/@Id
  must be a valid numeric licence; at least ONE prior dated
  observation of the same HORSES ID and stratum has a valid
  numeric licence; and current Jockey/@Id must not equal
  ANY prior *documented* licence in that stratum. If there
  were past records with missing rider licences, absence of
  the current ID from the *known* list does NOT prove the
  actual rider is novel; explicitly describe this as
  "not previously documented in matched prior records."
  This is NOT confirmation of the final post-race rider.
- Comparator: predict **zero** race-relative initial
  seconds, the source field-centered non-personalized
  benchmark. Score only matched eligible future records;
  do not score unobserved horses as zero.

## Score and support rules

For each eligible later horse-record, accumulate absolute and
squared errors for past-profile and zero baseline. Primary
error target is **equal-horse-weighted RMSE**, taking the
mean of each horse's future-record mean squared error before
taking the square root of the average across horses. Report
secondary equal-horse MAE and event-weighted RMSE
for transparency; do not optimize shrinkage against tests.

**Minimum quantitative gate** (source feasibility rather than
precalculated statistical power): >=20 different HORSES IDs,
>=20 eligible future horse-records, >=6 distinct source dates
with scored future records, and >=20 distinct horse-by-marker
contexts. If any fail, return HOLD with counts but NO numeric
gain/loss; a failure of data availability is not a null
biological effect.

- Positive RMSE reduction (zero baseline minus historical
  profile RMSE) indicates greater out-of-date descriptive
  persistence under this source/matched-context selection,
  not a trait mechanism or real-time predictive product.
- Zero/negative RMSE reduction is an informative exploratory
  stress result, NOT proof animals lack individuality.
- For an additional data-availability check, report matched
  scored rows with the same previously documented current rider
  separately, WITHOUT presenting between-subgroup differences
  as the causal effect of changing rider.
- Report separately the stricter same-Class sensitivity and
  the subset with valid previously matched original
  Trainer/@Id; this is not causal trainer adjustment.
- Never infer a valid p value or 95% CI from pooled
  future records; animal/meeting dependence and missingness
  preclude simple iid intervals here.

## Provenance and privacy

The official RQ source can change its historical SOAP horse
roster and with it the matched observations. Save the existing
per-day source meeting/race/GPS digests and newly captured
per-date HORSES roster XML aggregate SHA256. Require all
original 12 source dates to be successfully retrieved before
a final real data result; an HTTP error/timeout is an
explicit source-read HOLD.

Never publish raw original horse names, HORSES IDs,
jockey/trainer licence IDs, individual first GPS times,
dated individual predictions, wagers or odds; output only
safe aggregate population counts, errors if support gates pass,
HOLD flags and source hashes.

This study cannot establish actual jockey switches,
intrinsic physiological personality, genetics,
heritability, ground reaction norm (H1), causal social
competitor effects (H2) or fitness/adaptation.
