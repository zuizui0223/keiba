# Doomben original Thoroughbred first-marker repeatability: 2025-source extension

**Exploratory new-source design and real-data audit, 2026-10-15.**

Verified source workflows:
[initial official two-year audit 38674631028](https://github.com/zuizui0223/keiba/actions/runs/38674631028)
and [separate rerun 38674654236](https://github.com/zuizui0223/keiba/actions/runs/38674654236).
Both returned matching **observed identity/marker counts** and the same
conditional first-GPS interval ICC point estimates to numerical
optimizer precision.

**This is a new data-support and model-sensitivity observation,
not a preregistered biological effect, selection experiment,
genetic heritability, environmental H1 individual reaction norm,
H2 competition response or a wagering model.**

## Source and locked scientific target

Racing Queensland original public
[Thoroughbred Sectionals and Position Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
and official
[Open Data Web Services](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).
Names are matched conservatively within official event/race to
original `HORSES` numeric animal IDs; all-zero telemetry, same-day
duplicate horse names or multiple original-ID nominations are
excluded without coding them DNF.

Exactly **23 original 2025 Doomben CSV dates** were selected using the
earliest and latest official published CSV **per calendar month**,
with just one date where a month had only one; that source calendar was
[committed before reading these 2025 source HORSES IDs or fitting
2025 effects](ecology-rq-doomben-2025-marker-calendar-lock.md).
Previously locked **19 original 2026 Doomben dates** and original race
numbers 1–6 were unchanged. This follow-up was nevertheless
chosen after seeing positive source ICC at other tracks
and source-identification HOLD at 2026 Doomben:
**post-hoc source suitability, not a blinded biological replication**.

Original source acquisition: 42 dates requested;
**38/42 original date-specific SOAP/GPS source joins succeeded**.
The fixed date-level **HOLD** list was:
2025-01-22, 2025-05-28, 2025-08-27 and 2026-08-26.
No original race IDs, animals, first-section times or values are
inferred from an unreturned API response. The upstream API occasionally
terminates an incomplete chunked XML document, which is now
classified as an explicit date-level source HOLD rather than
read as a zero-count race.

Data publisher retains original rights; this public
research PR contains source SHA-256 fingerprints and
anonymous aggregates **only**, not original animal
names, HORSES IDs, rider/trainer licence values,
individual GPS timings, betting prices or predictions.

## First real cross-year repeat-availability results

All rows below are positive original *first-GPS-interval*
source records linked to genuine numeric `HORSES` IDs.
`first_marker_m` is the original GPS distance
marker, which is **not** the whole-race distance.
Race FE means a distinct intercept for every original race;
original HORSES ID is a Gaussian random intercept.
Fit unchanged source-restricted likelihood and
>=20 original IDs with repeated dated observations,
plus original minimum race/date/row support gates.

| Source scope | 2025 alone | 2025 + previously fixed 2026 |
| --- | ---: | ---: |
| Successful original source dates | **20/23** | **38/42** |
| All positive GPS original numeric-ID source candidates | **660** | **1,277** |
| Unique original source numeric HORSES IDs | **537** | **977** |
| HORSES IDs recurring on 2+ original dates (any marker) | **100** | **228** |
| Positive first-GPS records: 150m original marker | **242** | **419** |
| HORSES IDs recurring at 150m on 2+ dates | **25** | **60** |
| Timed 150m records surviving >=4 source GPS horses/race | **235** | **412** |
| Exploratory race-FE HORSES-ID 150m conditional ICC | **0.653589** | **0.180116** |
| Positive first-GPS records: 200m original marker | **218** | **423** |
| HORSES IDs recurring at 200m on 2+ dates | **19** | **42** |
| Timed 200m records surviving >=4 source GPS horses/race | **207** | **400** |
| Exploratory race-FE HORSES-ID 200m conditional ICC | **HOLD: 19 repeat IDs** | **0.412422** |

### Important scientific interpretation

**Repetition support improved.**
In the prior *2026-only* fixed Doomben study,
there were only **9** repeated numeric source
HORSES IDs at either 150m or 200m first marker,
so neither model was justified. Source-specific
2025/2026 extension has now passed the
unchanged repeat-ID gate at **both** markers.

**ICC model-dependence is substantial.**
The observed Doomben **150m** point estimate is
0.654 in 2025 alone but 0.180 in the pooled
2025+2026 source cohort. This difference
is **not** evidence for a year-caused biological
change in an individual horse, and the
numerical ICCs are not two independent
confidence intervals. Adding the 2026 date
cohort adds many different animal IDs,
competitor fields, race conditions,
possible source GPS measurement variation,
and within-year vs cross-year animal
repetitions. The Gaussian residual/error
variances and selection process may differ
across years.

**Different venues at a shared marker can now
be compared as technical source cohorts**
(Cannon Park 150m, Eagle Farm 200m, and
Doomben both exact markers). But this is
only an **instrumental/measurement-compatibility
gate**, not a valid confirmatory
same-biological-trait replication: the
different original site/year cohorts lack
verified equivalence of racing classes,
age, jockey, animal populations, common
recorded HORSES IDs across sites,
sensor error and final starter status.

**Numerical precision and 95% uncertainty
are NOT established here.** The original
Gaussian model is homoscedastic within
the source conditional design, but the
actual database has nonrandom
race nominations and GPS failures.
A positive source horse random intercept
can reflect stable trainer/rider management,
source selection and incomplete race
contexts. No independent all-starter
population ICC or causal source/year
comparison is estimated.

## Next source-identity reconciliation

The next narrow question is whether
the *same official numeric HORSES IDs*
have a **positive first-GPS 150m or 200m
measurement in both 2025 and 2026**,
and whether their original official race
distance and broad Class also agree.
This is a different and much stricter
criterion than merely fitting a pooled
random-intercept variance across many
largely distinct animals. Such an audit
must output anonymized COUNTS ONLY, not
original ID lists or signed effects for
tiny paired contexts.

The source code and tests now support
this additional gate in
[`scripts/ecology_rq_doomben_2025_marker_extension.py`](../scripts/ecology_rq_doomben_2025_marker_extension.py).
Any source failure remains HOLD.

## Reproduce

~~~bash
python -m unittest discover -s tests \
  -p 'test_ecology_rq_doomben_2025_marker_extension.py' -v

python scripts/ecology_rq_doomben_2025_marker_extension.py \
  --output tmp/rq-doomben-2025-2026-marker-readiness.json
~~~

Workflow:
[`.github/workflows/ecology-rq-doomben-2025-bridge.yml`](../.github/workflows/ecology-rq-doomben-2025-bridge.yml)
posts original-file fingerprints, date-level missing/HOLD
statuses and anonymous summary metrics only.

Original data source terms:
[Racing Queensland public open data](https://www.racingqueensland.com.au/about/reports-and-data/open-data).
As with all existing sections of PR #2,
**environmental reaction-norm H1 and
competitive-context H2 remain HOLD.**
