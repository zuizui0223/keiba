# Doomben same-venue within-year histories: design fixed before new scores

**Protocol frozen on 2026-10-15 before looking at the new same-year
predictive scores. This is an exploratory post-hoc follow-up**. The
existing Cannon Park within-2026 positive result, the Doomben
2025→2026 negative result and the 2025-only marker-specific ICC
were already known. The comparison is NOT preregistered or causal.

## Motivation and exactly fixed source population

The current paper contrasts Cannon Park within-2026 chronological
prediction with Doomben 2025→2026 fixed-year prediction, confounding
venue, time horizon, horse cohort and rider-context eligibility.
A narrower falsification is possible without adding new sources:
evaluate **within Doomben** separately in **2025** and **2026**,
using the same source-bound GPS endpoint, history rule and equal-horse
loss metric as the Doomben 2025→2026 original-year study.

Use *exactly* its previously prelocked original **23 Doomben dates in
2025 and 19 in 2026**, official races 1–6; never add new dates to
rescue insufficient repeated IDs, or choose one date window based
on this new result. Use existing source-matched numeric HORSES ID,
source name consistency and >0 first GPS interval. A race needs
at least four positive original source GPS horses. Unavailable
source dates must remain recorded HOLD and cannot imply no animals
or zero true sectional time. The source may have four already
known unavailable dates (three in 2025 and one in 2026).

## Exact within-year predictive comparisons

For **each year separately (2025 and 2026)** and for original first
GPS marker **150m and 200m separately**, predict future source records
using only observations from strictly earlier dates **in that SAME
calendar year**. On each original date, compute predictions for
all races before including any of today's records in history.
Do not use a 2026 outcome to train 2025 or 2026 prior predictions
and do not use any 2025 observation to train a 2026 within-year
profile in this analysis.

Main original context = exact same original first GPS marker and
official race distance. A SECONDARY stricter sensitivity also
requires an exactly matched original race Class label. These Class
cohorts are not assumed nested in eligibility.

The focal historical source profile must contain at least
one strictly prior positive GPS original source observation
for the SAME original numeric HORSES ID in that context.
The other-horse benchmark must have at least **three
different** original source HORSES IDs observed strictly
earlier in the exact same context, excluding the focal
HORSES ID and all its original source rows entirely.
The zero benchmark predicts exactly 0 race-relative seconds.
Use identical fixed historical shrinkage **n/(n+2)**
on own and other profile means. Do not tune n or the
pseudo-count after scoring.

The observed relative source outcome is the individual first
GPS interval in seconds minus the mean first interval of OTHER
GPS-positive same-race horses. It is postrace and field-dependent,
NOT a raw speed, experimentally isolated behavior, final finish
time or a pre-race betting prediction.

Score own, other and zero models on exactly the SAME
eligible source future horse×race rows, with each
HORSES ID equally weighted: average future
squared errors within animal, average over animals,
then square root (RMSE in seconds). Gain = other minus own
RMSE (positive = own historical source profile is better).
Report equal-horse MAE only as an ancillary source descriptor.

## Numeric support gates and negative findings

Each exact calendar-year/marker/context cell must pass
**>=20 DISTINCT source HORSES IDs**, >=20 future rows,
**>=6 distinct observed future meeting dates**, and >=20
distinct horse-by-original-distance-marker contexts before
a numerical gain is reported. These are support heuristics
drawn from earlier chronology analyses, not statistical
power justification. If not met, give only dates, IDs,
rows and **HOLD**; DO NOT report an anecdotal positive or
negative result or impute missing cases.

The 2025→2026 historical outcome remains an independent
previously reported comparator (26 IDs/27 future rows;
other minus own −0.017225 s). It must NOT be pooled into
within-year scoring, and apparent differences between
same-year and cross-year gains are NOT an estimator of
time-dependent biological decay: focal individuals
and exposure windows can differ between target sets.

No post-hoc significance tests, causal year effects,
heritability or evolutionary selection should be asserted.
The final return must contain anonymous source counts,
HOLD codes and aggregate RMSE/MAE if supported,
plus original manifest hashes; no numeric HORSES IDs,
horse names, individual racing times, rider licences,
or individual prediction rows.

## Interpretation gates

- If 2025 same-course within-year own-history helps but
  2025→2026 own-history does not, the new fact is
  **context-dependent transfer under different exposure
  horizons/sample selection**, NOT intrinsic horse
  personality decay. Other horses' past history may
  change with original Class and source GPS composition.
- If 2025 within-year cannot pass 20 original-ID support,
  report HOLD, NOT lack of within-year predictability.
- If 2026 within-year is sparse (expected from the prior
  nine 150m-marker repeated IDs), report HOLD; never
  compare unsupported point errors with the 2025 result.
- H1 horse×ground reaction norms, H2 competitor effects,
  actual final starter/rider state, horse age, genetics,
  welfare, fitness and natural selection remain outside
  identified data scope.

Data provenance: Racing Queensland original Sectionals
and Open Data Web Services, exactly the previously
locked Doomben source calendar. Source eligibility
and fiscal rights remain subject to publisher conditions.
