# Real Thoroughbred Good–Soft–Heavy H1 feasibility: expanded race coverage

**Exploratory expansion executed 2026-10-13. This is NOT a biological effect estimate.**

This memo is separate from the [frozen original 20-race
cohort](ecology-rq-real-h1-multigoing-feasibility.md). The original
scope was dates 2026-05-15 / 05-29 / 08-22 / 08-29 / 10-11 at
Cannon Park with race numbers `(1,2,3,8)` on each date.

**Expansion made after seeing the original overlap counts**:
inspect *all published official race numbers 1–8* on those
same five previously chosen meeting dates. This is a **post-hoc
data-readiness sensitivity**, not independent replication of an
environmental coefficient, and must never be rebranded as a
preregistered confirmatory result.

Original publisher: [Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
and the
[original Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).

Independently executed:
[GitHub Actions #38346571211](https://github.com/zuizui0223/keiba/actions/runs/38346571211);
script
[`ecology_rq_multigoing_h1_preflight.py`](../scripts/ecology_rq_multigoing_h1_preflight.py).
The CI artifact includes per-source SHA-256 hashes and summary
counts; **no names, numeric horse IDs, or runner-level time
records** are written into the repo or downloadable aggregates.

## Observed source-level sample coverage

| Official date | Going as reported by original SOAP | Verified race numbers | Internal HORSES ID × first-section GPS matched records |
| --- | --- | --- | ---: |
| 2026-05-15 | Heavy | 1–8 | 45 |
| 2026-05-29 | Soft | 1–8 | 51 |
| 2026-08-22 | Soft | 1–8 | 67 |
| 2026-08-29 | Good | 1–4, 6–8 | 64 |
| 2026-10-11 | Good | 1–6, 8 | 53 |
| **Total** | Heavy 45, Soft 118, Good 117 | **38 official races** | **280** |

The original SOAP index did **not** provide race 5 on
2026-08-29 or race 7 on 2026-10-11. These missing races
were reported explicitly; IDs, statuses and performances
were not guessed or imputed.

The race-level categorical classifications agreed with
meeting-page Good/Soft/Heavy labels for the observed
races. The research script does **not** assume equal
distance on a numeric going scale.

## Real individual-ID and competing-context support

| Gate | Original 20 races | Expanded 38 races |
| --- | ---: | ---: |
| Matched positive first-section records | 143 | 280 |
| Distinct official IDs after same-day ambiguity filtering | 107 | 194 |
| Official IDs recurring on two or more event dates | 26 | **65** |
| Recurring IDs observed in both Good and wet ground | 20 | **37** |
| Good-versus-Soft recurring IDs | 15 | 29 |
| Good-versus-Heavy recurring IDs | 8 | 14 |
| Horse ID with Good and wet at *same official distance and first section marker* | 10 | **17** |
| Horse ID with Good and wet at same distance, marker **and race class** | 1 | **2** |
| Same class/distance/marker with **at least 2 Good and 2 wet records** | **0** | **0** |

The Good–Soft and Good–Heavy groups overlap:
some IDs occur in both. Repeated official horse IDs
with positive GPS are **real source-level longitudinal
evidence**; they do **not** prove a complete actual-starter
or official finish-result panel.

The large attrition from 37 cross-ground IDs to only
2 class/distance/section-aligned IDs is an important
**design finding**: class/distance selection makes
simple apparent within-horse environmental slopes
hard to identify. Race `Class` in the source can be
a broad label such as `No class restrictions`; the
strict two-ID comparison is therefore an **upper bound**
on truly comparable biological contexts. Age/weight
conditions, jockey, weather, rail position and health
are not completely matched.

## Descriptive *artefact-risk* check — not a biological H1 test

In the **17** ID/first-marker/distance-matched
candidate comparisons (class *not* held constant),
the mean of per-ID non-Good minus Good first-section
durations was **−0.20824 s**; **15** stratum
differences were negative and **2** positive.

With original race class additionally held equal,
only **2** ID strata remained, with an
unweighted mean of **−0.255 s**, both negative.
Neither subset meets the **2 Good and 2 wet**
within-comparable-context design gate.
These underpowered and class/entry-confounded
numbers do **not** mean heavy ground makes
horses run faster, do **not** estimate behavioral
plasticity and do **not** support a causal effect.
They simply demonstrate how selective race
entries and different races can produce apparently
counterintuitive mean differences.

No hypothesis testing, cross-validated
reaction-norm variance, causal p-value, model
fit, power estimate or selection coefficient
was computed from the actual horse data.

## Scientific decision

**H1 still HOLD:** 37 genuine numeric horse IDs
have at least one positive GPS first-section
record on Good and non-Good conditions, but
**zero** horse×matched class/distance/section
strata have two independent observations in
each ground group. Age/weight/rail/course
conditions would further narrow comparability.
Requiring this evidence is not denying a true
biological response; it is protecting against
unsupported interpretation of an observational
slope.

**H2 still HOLD:** official
`GetHorsesForRace` lists are not verified
final starter rosters, some same-day
IDs are multiply listed, the CSV has zero
telemetry and no certified early position or
individual finish-result variables. Source
IDs alone cannot identify competition.

**Next empirical priority**: secure repeated
historical sources with verified outcomes and
stable HORSES IDs over longer periods;
choose future race dates based on pre-specified
**exposure overlap and race condition support**
(not postrace speed differences), and quantify
within-horse repeated Good-versus-wet
experiences conditional on class/distance,
jockey and other covariates. Pre-register
statistical power, correlated-race uncertainty,
selection sensitivity, and an independent
future-date holdout before claiming ecology.

## Reproduction (public data, private source records)

~~~bash
python -m unittest discover -s tests -p 'test_ecology_rq_multigoing_h1_preflight.py' -v

# Freeze and reproduce the original cohort
python scripts/ecology_rq_multigoing_h1_preflight.py \
  --scope focused_four \
  --output tmp/official-H1-focused.json

# Exploratory (post-hoc) source-coverage extension
python scripts/ecology_rq_multigoing_h1_preflight.py \
  --scope extended_eight \
  --output tmp/official-H1-extended.json
~~~

The program never exports numeric source HORSES
IDs, names, official raw XML, raw GPS horse rows,
betting returns, or identity-to-outcome predictions.

**Scientific conclusion from these two fixed
source-size audits is about research design,
not an adaptive behavioral difference.**
