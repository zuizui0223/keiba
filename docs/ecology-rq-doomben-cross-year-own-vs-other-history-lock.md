# Doomben cross-year *same-horse* early-pacing test — locked before outcome scoring

**Locked on 2026-10-15, before evaluating the 2026 held-out
first-GPS relative timing scores against 2025 histories.** This
is a post-hoc *methodological follow-up* to the already observed
2025-only vs pooled 2025–26 Doomben ICC difference
(0.653589 versus 0.180116 for original 150m markers). It is
**not** a blind preregistered hypothesis, and data-source
access is still conditional on Racing Queensland availability.

Data and source dates **remain exactly the ones previously frozen**:
23 Doomben 2025 selected published meeting days, 19 Doomben
2026 meeting days, race numbers 1–6. See the frozen
[original 2025/26 calendar](ecology-rq-doomben-2025-marker-calendar-lock.md).
Do not search other dates, horses, trainers, class labels
or arbitrary GPS markers on the basis of the outcome.

## Important scientific distinction

A pooled source ICC differs from an *individual horse
across-year behavior* statistic. A 150m pooled ICC
can fall if many new horses enter the sample, residual
GPS error or racing context differs, or within-horse
consistency truly changes. It must **not** be called a
horse's developmental year effect without an actual
same-HORSES-ID 2025→2026 outcome comparison.

The previous source audit established **27** original
numeric HORSES IDs with a first 150m marker and
identical race distance across both years, and **16**
at the 200m marker/distance. Requiring matching
original race Class reduced these to **6 and 4**,
and zero ID had two original dates in *each* year
at either marker. These availability counts are
**already known**, not invented as a new finding.

## Frozen prospective-for-this-analysis *computational* design

Source: original Racing Queensland SOAP `HORSES/@Id`
and first original timed GPS interval. A record is
eligible only after the existing
`identity_overlap` cross-date name-consistency
gate and a race containing **at least 4** original
horses with positive GPS first timing.
Do not infer starters from nominee lists or
DNF from zero GPS values.

The outcome for this particular secondary
question is **race-relative initial sectional
time**, defined for each horse:

`d = focal first GPS seconds - mean(other GPS-timed horses' first seconds in the same official race)`.

This is not the absolute first section used
in the published Gaussian race-FE ICC, and
changes mechanically when rivals' measured
times change; the comparison cannot establish
causal social H2.

**Historical training = exclusively 2025 dates**.
**Future evaluation = exclusively 2026 dates**.
No 2026 observations enter the historical
predictor, even when an individual has multiple
2026 source starts. Use the original numerical
HORSES ID, the same exact initial marker and the
same exact official race distance. Exact Class
is a separately reported conservative sensitivity.

For a horse, use its 2025 mean historical
race-relative initial sectional time and
**fixed shrinkage `n/(n+2)`** learned from no
source outcomes. Compare on the identical
2026 rows with (a) zero race-relative timing
(no own-horse history) and (b) the 2025
historical mean among OTHER HORSES observed
at the same original marker/distance, excluding
the focal animal entirely and requiring at
least **3 different other original HORSES IDs**.
Apply the same fixed shrinkage to the other-horse
history as the focal history. Do not change
the comparator cohort after inspecting results.

Report:
- number of matched 2025/2026 original
  numeric HORSES IDs and 2026 evaluation rows;
- number of original race dates in each year;
- RMSE weighted equally by HORSES ID (each
  horse averages its own 2026 errors),
  zero/own/other predictions on identical
  rows, and the own-minus-other comparison;
- sign direction and changes under a stricter
  **exact original Race Class** matching
  condition, with no made-up missing class;
- descriptive per-horse signed errors or
  variance are never exported.

**Data-readiness gate:** at least 20 different
HORSES IDs with 2025 training AND 2026 outcome
records at the same marker and race distance,
at least 20 scored 2026 source observations
and at least 3 separate race dates in each
source year. The 200m group and Class-matched
groups may fail these thresholds and must
return an explicit **HOLD**, with no RMSE gain
or reported estimate. A positive gain will
not be upgraded to confirmatory significance.

Source sensitivity: report which original
meeting dates could not be retrieved and
per-source SHA-256 as already implemented.
No replacement dates, no raw horse names,
numeric IDs, individual GPS records or race
predictions in repository outputs.

## Primary biological decision gate

Even if same-ID 2025→2026 timing
persistence is observed, it cannot
be attributed to innate horse behavior
rather than aging, training, rider,
stable selection into race class,
GPS source changes or unobserved
final race outcomes. A source-level
persistence result may justify an
independent longer-term study,
**not** a developmental explanation for
the pooled 150m ICC difference.

Original ecological H1 individual
ground random slopes, H2 competitor
social response, adaptations, fitness,
heritable personality and betting
efficiency remain **HOLD**.

Publisher:
[Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data).
