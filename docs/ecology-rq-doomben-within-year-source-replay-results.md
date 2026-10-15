# Doomben within-year horse-history result: original source availability reverses the inference gate

**Final scientific status (15 October 2026): HOLD — not a replicated biological effect.**
This is an observational read-only Racing Queensland (RQ) source
reproducibility audit, **not** a test of age-related behavioral decline,
heritability, environmental reaction-norm H1, social-competition H2,
or betting performance.

## Motivation and pre-scoring scope

Previous fixed 2026 Cannon Park source records suggested within-year
individual-profile persistence, whereas a locked Doomben 2025→2026
evaluation found the own-horse 2025 historical profile did not
improve 2026 race-relative early GPS timing against other-horse
history. These studies confound course, year, timing context and
entry/GPS observation selection.

The [within-Doomben, within-year source design](ecology-rq-doomben-within-year-history-design-lock.md)
was frozen **after** the earlier studies but **before** the new
same-year scores. It reused the previously locked **23 Doomben 2025
and 19 Doomben 2026** original meeting dates, races 1–6, and exact
**150m/200m** initial section marker plus official race distance.
Additional exact original Race Class comparisons were required
to be reported as separate sensitivity cohorts.

A horse's source-measured race-relative first GPS time means its
own positive first segment seconds **minus the mean of other
GPS-timed horses from the same original race**. Other horses'
measured outcomes influence this target arithmetically.
For each of 2025 and 2026 **separately**, only earlier dates in
the **same year** trained the own-horse/other-horse historical
profiles. Other-horse reference histories exclude the focal
HORSES ID. A fixed n/(n+2) shrinkage is used for both predictors.

Locked numerical support: ≥20 distinct HORSES IDs, ≥20
later source observations, ≥6 different scored dates and
≥20 horse-by-context strata. If any fail, report **HOLD**
without numeric RMSE, not a zero effect or a performance estimate.
All output here is anonymous and aggregate-only.

## Two independent first-party original-data executions

- [Run A: official source/within-year analysis #38696624349](https://github.com/zuizui0223/keiba/actions/runs/38696624349).
- [Run B: independent original-source rerun #38696711022](https://github.com/zuizui0223/keiba/actions/runs/38696711022).
- [Frozen replay-agreement CI #38697999341](https://github.com/zuizui0223/keiba/actions/runs/38697999341),
  using [the exact aggregate comparison script](../scripts/ecology_rq_doomben_same_year_source_replay_compare.py)
  and **seven fictional source-availability/privacy tests**.

Each run completed **37 of the same 42 locked source dates**, but
their failed dates were not identical:

| Original source date | Run A | Run B | Source-level reason |
| --- | --- | --- | --- |
| 2025-03-19 | Received and audited | **HOLD** | Incomplete/truncated HTTP response in B |
| 2025-07-12 | **HOLD** | Received and audited | Incomplete/truncated HTTP response in A |

Both runs also shared **four other source HOLD dates**:
2025-01-22, 2025-05-28, 2025-08-27 and 2026-08-26.

**Provenance verification:** all **36 source dates
successfully returned in BOTH runs** had the **same**
original meeting/race/GPS SHA256 values, the same
combined official HORSES roster SHA256, the same number
of horse-roster API responses, the same candidate
positive GPS records and original race identifiers.
Therefore no observed source-byte/identity changes
explain the difference in those shared dates.
The numerical eligibility difference is driven by
**intermittent source availability on the nonshared dates**,
not evidence of a biological 2025–26 effect.

## Biological and source-conditional scoring results

| Prelocked marker/year/context | Run A identities / later rows | Run A | Run B identities / later rows | Run B |
| --- | ---: | --- | ---: | --- |
| **2025 / first 150m / exact distance** | **21 / 21** | Exploratory own-history gain +0.028304 s | **17 / 18** | **HOLD** (below ≥20 ID gate) |
| 2025 / 150m / distance and Class | 16 / 16 | HOLD | 12 / 12 | HOLD |
| 2025 / 200m / distance | 13 / 13 | HOLD | 13 / 13 | HOLD |
| 2025 / 200m / distance and Class | 5 / 5 | HOLD | 5 / 5 | HOLD |
| 2026 / 150m / distance | 9 / 11 | HOLD | 9 / 11 | HOLD |
| 2026 / 150m / distance and Class | 7 / 8 | HOLD | 7 / 8 | HOLD |
| 2026 / 200m / distance | 7 / 8 | HOLD | 7 / 8 | HOLD |
| 2026 / 200m / distance and Class | 6 / 7 | HOLD | 6 / 7 | HOLD |

In the one supported Run A context only:
- Zero historical profile RMSE: **0.241816 s**.
- Other original horses' same-year historical profile:
  **0.243186 s**.
- The focal horse's same-year own profile:
  **0.214881 s**.
- OTHER minus OWN RMSE gain: **+0.028304 s**.

**The positive numerical contrast does NOT survive independent
source replay as an estimable contrast.** The second run has
insufficient original horses and future rows under the exact
same locked threshold and must not be treated as either
a zero or a negative own-history effect.

As a result, the single numerical same-year 2025 gain
may be retained in versioned exploratory audit logs but
**must not be promoted as a verified positive ecology result**
or included as a robust manuscript headline.

The 2025→2026 prior-year source evaluation was a separate
previously fixed sample: 26 shared IDs / 27 later
2026 observations, own-horse history RMSE 0.386131 s versus
other-horse history 0.368906 s (OTHER minus OWN
−0.017225 s). That negative sampled-cohort contrast
also changes sign under some single-ID/date omissions.
Neither pairing demonstrates a true temporal decline of
individual phenotype stability, since the included animals,
race conditions and observation histories are not matched.

## Additional post-result source-date-deletion check

The follow-on
[`ecology_rq_doomben_within_year_history.py`](../scripts/ecology_rq_doomben_within_year_history.py)
now explicitly re-fits the *already supported* original
year/marker/distance comparison after deleting each
original positive-GPS source date in turn, without
altering the locked support rules or prior-only timing
features. It counts re-fits satisfying all original gates
versus those reverting to HOLD and records the range
of differences **only for supported re-fits**.
It deliberately does not attempt numerical inference
for an original HOLD group.

This is a **post-hoc technical robustness diagnostic**,
not an effect-size confidence interval or new
prospective biological confirmation.

## Scientific decision

**Retain**: source-linked Thoroughbred early GPS timing
can show short-horizon individual-associated predictive
information in some selected cohorts; measuring persistence
at multiple time scales is a meaningful ecological question.

**Do not assert**: a replicated Doomben within-year gain,
an annual loss of identity-associated biology, adaptive
horse personality, stable genetic strategy, ground H1,
competitive-context H2, or a causal effect of rider/trainer.
These original sources cannot verify the full actual
starter/finisher roster or individual certified
race-finishing times; selective entries and missing
positive GPS/roster responses remain significant.

**Next methodological priority:** obtain or archive
lawfully usable *complete and immutable original source
snapshots*, with real event dates, final starters,
source identities, GPS measurement provenance and
full roster response hashes **before** setting a
numerical forward evaluation. Otherwise the set of
accessible source dates alone can decide whether
a scientific estimate may be reported.

All original sources and licensing terms:
[Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
and [Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).
No source HORSES IDs, animal names, trainer/rider licence
numbers, individual GPS measurements or personalized
predictions are published in this repository.
