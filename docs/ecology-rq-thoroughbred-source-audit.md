# Racing Queensland thoroughbred GPS/sectional source — real-data audit

**Status: REAL THOROUGHBRED SECTIONAL DATA INSPECTED; H1/H2 EMPIRICAL TESTS ON HOLD.**
Date verified: **2026-10-13**. This note corrects the older status in which only
synthetic horse data (and an independent real-greyhound analogue) had been tested.

## Official source and independently executed code

Official index: https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals

Two **official, historical, named Thoroughbred** source CSVs were inspected and
independently parsed by GitHub Actions:
[run #38330158633](https://github.com/zuizui0223/keiba/actions/runs/38330158633).

- 2026-10-11, Ladbrokes Cannon Park:
  https://www.racingqueensland.com.au/RacingFile.ashx?path=/Sectional/20261011_Ladbrokes_Cannon_Park_T.csv
  - SHA-256: `2d24b5a01edf3fe8a6594b04557cbb6ad89f7ed8eebd87f64aa4face9ec0db84`
- 2026-10-10, Eagle Farm:
  https://www.racingqueensland.com.au/RacingFile.ashx?path=/Sectional/20261010_Eagle_Farm_T.csv
  - SHA-256: `ca3ccf1ac8a63cc8a67a3ffb58c62d51cd30264bb6d7a6f020ed8a0e8d76fc80`

Attribution: **Racing Queensland** (the official original publisher).
Review the primary-source conditions at
https://www.racingqueensland.com.au/about/reports-and-data/open-data
before research redistribution. Raw horse-level records have **NOT**
been added to this repository; this PR only contains a reproducible parser,
source links, aggregates and validation checks.

Code: [scripts/ecology_rq_thoroughbred_sectional_audit.py](../scripts/ecology_rq_thoroughbred_sectional_audit.py).
Independent tests: [tests/test_ecology_rq_thoroughbred_sectional_audit.py](../tests/test_ecology_rq_thoroughbred_sectional_audit.py).
CI: [.github/workflows/ecology-horse-sectionals-audit.yml](../.github/workflows/ecology-horse-sectionals-audit.yml).

## What the file actually contains

The files are **not ordinary rectangular CSV files**. Each race has a
`Date,RaceNumber,...` heading, whose third comma field contains five
semicolon-separated attributes: reporting date, venue description,
race title, a race-level clock-time-like measurement, and route code.
Horse rows then contain date, race number, and a semicolon-separated
horse-name / unnamed integer / sequence of triples:
`distance marker ; unknown numeric signal ; section-duration`.

The signal **resembles speed** but its exact units and interpretation
have not been independently verified. A route's final distance marker
must not be interpreted as the official event distance without a
race-level join. The clock-time-like race heading is **not an
individual horse's certified finish time**.

A relevant discrepancy illustrates the need for care: the official
Cairns race-1 result page lists a race time of about `0:55.06`,
while the CSV header for the corresponding named race reads
`00:00:57.263`. These are *different measures or sources* until
documented; do not treat them as identical or infer a focal horse's time
from the CSV header.

Official public Racing Queensland SOAP WSDL:
https://www.racingqueensland.com.au/OpenDataWebServices/Meetings.asmx?WSDL
and official PDF:
https://www.racingqueensland.com.au/rq-open-data-web-services.pdf .
The `GetHorsesForRace` specification exposes an internal `HORSES`
horse ID (along with race-specific horse, jockey and trainer fields).
However, **that ID is not present in the observed sectional CSV horse rows**,
and we have **not yet confirmed a lossless, unambiguous race-number +
horse-name + position-to-official-ID join**. The WSDL meeting/race ID
features are demonstrably available, but that does **not** prove a
historical, race-results-grade longitudinal panel exists in the SOAP
responses.

## Independent aggregate audit — frozen two official sources

| Official meeting | Race-header blocks | Horse-labelled rows | Positive section telemetry | All section values/time zero |
| --- | ---: | ---: | ---: | ---: |
| 2026-10-11 Ladbrokes Cannon Park | 8 | 76 | 68 | 8 |
| 2026-10-10 Eagle Farm | 10 | 121 | 94 | 27 |
| **Total** | **18** | **197** | **162** | **35** |

The parser separately counted:
- **4** horse names on the same Cannon Park day listed in multiple race
  headings where one row had all-zero sections and another had positive
  sections.
- **1** such name on the Eagle Farm day.
- Thus **5 same-day name repeats with mixed-zero telemetry** across
  the two meeting files. These may reflect duplicate/stale export
  entries or other source processing, not proven biological repeat
  starts. **They make the assumption "all-zero GPS means DNF" especially
  unsafe.**

The flags `all_zero_telemetry`, `partial_telemetry`, and
`complete_positive_telemetry` refer **only to timing measurement
presence**. A row with no positive timing evidence is **NOT**
confirmed as a nonfinisher, starter, withdrawal, disqualification,
or zero-speed animal. Never insert the 35 zero rows into a
`did_not_finish` outcome without independent official race-result
confirmation. A horse name is **not a unique permanent horse ID**.

The CI ran **10 dedicated parsing/identity/zero-telemetry tests**
successfully, and confirmed source hashes. Aggregate-only JSON
artifacts are attached to the workflow run.

## H1/H2 practical readiness

| Ecological requirement | Status | Reason |
| --- | --- | --- |
| Genuine horse GPS/sectional time data | **VERIFIED** | Official downloaded CSV, positive timing in 162 rows across the two meetings |
| Real local date, course, apparent race label | **PARTIAL / VERIFIED AS LABELS** | Date and race headings available, official race ID join not confirmed |
| Stable equine `horse_id` across years | **HOLD** | Official SOAP exposes a HORSES ID, sectional CSV has name only; crosswalk not established |
| Full real starter roster and DNF vs zero-telemetry code | **HOLD** | Some rows contain all-zero sections and duplicated same-day names |
| Individual, certified finish time | **HOLD** | CSV has sectional intervals; race heading time does not equal verified individual outcome |
| Comparable repeated ground/distance/class exposure within horse | **HOLD** | Two meetings are not a longitudinal repeated-exposure sample |
| Competitor's actual earlier-race style and contemporary complete rivals | **HOLD** | Sectional CSV lacks confirmed unique IDs, full rosters and early-position variables |
| H1/H2 ecological effect supported | **NO** | Scientific identification prerequisites not met |

## Precisely reproducible commands

~~~bash
python -m unittest discover -s tests -p 'test_ecology_rq_thoroughbred_sectional_audit.py' -v

python scripts/ecology_rq_thoroughbred_sectional_audit.py \
  --fetch-official 20261011-cairns --audit tmp/rq-cairns-aggregate.json

python scripts/ecology_rq_thoroughbred_sectional_audit.py \
  --fetch-official 20261010-eagle-farm --audit tmp/rq-eagle-farm-aggregate.json
~~~

Only two URLs are hard-allowlisted. The program reads bounded official
files, checks protocol/format/identity, does not infer DNF or individual
speed from zero, and publishes aggregate JSON only.

## Next study step (not yet done)

1. Take **one** archived official horse race and compare the
   `GetHorsesForRace` list (internal IDs) and the public racing-results
   roster against every named GPS row; explicitly flag one-to-many,
   mixed-telemetry duplicate, withdrawal and DNF cases rather than
   forcing a match.
2. Verify a **field-specific** reliable individual time and early
   position measurement. Use distance/time normalization only when
   official section distances and units are resolved.
3. Repeat for a carefully scoped cross-date sample with source-hash
   tracking; quantify official ID recurrence and within-horse
   environmental/competitor overlap. Do not bootstrap nonexistent
   historical individual starts from course aggregate records.
4. Keep the observational H1 individual reaction and H2 opponent
   interaction models on **HOLD** until a repeated-start, stable-ID,
   complete-results-equivalent panel is legitimately constructed.

**No horse biological discovery, prediction accuracy claim, bet advice,
causal competition effect or evolutionary adaptation is established by
this structural source audit.**
