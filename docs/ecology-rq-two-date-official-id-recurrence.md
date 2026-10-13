# Official two-date Thoroughbred identity recurrence — first validated longitudinal-source check

**Status: REAL EQUINE OFFICIAL-ID RECURRENCE VERIFIED; ECOLOGICAL H1/H2 STILL HOLD.**
Audit conducted 2026-10-13 using source dates 2026-08-29 and 2026-10-11,
both *Ladbrokes Cannon Park* (Cairns). Dates are genuine official
event dates, not the deliberately obscured Hong Kong sample dates.

Independent reproducible GitHub Actions execution:
[38333318382](https://github.com/zuizui0223/keiba/actions/runs/38333318382).
Source:
[Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
and its [Thoroughbred Sectionals](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).
The official SOAP endpoint has `Meeting Id`, `Race Id`,
and internal `Horse Id` attributes, as documented in the
[Open Data Web Services protocol](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).

## Scope of the explicitly bounded audit

- Earlier source 2026-08-29: 4 race numbers requested (2/3/4/5);
  **3 official race IDs were present** (2/3/4), while number 5 was
  absent from the public SOAP race list. The missing ID was **not
  fabricated or inferred**. Original GPS CSV SHA256:
  `6d5fdf8b9608fcd0f9adc17f341cec70a2dc4f3c525e2327d194989039817569`.
- Later source 2026-10-11: 4 race numbers requested (2/3/5/6),
  all 4 represented by official SOAP race IDs. Original GPS CSV
  SHA256:
  `2d24b5a01edf3fe8a6594b04557cbb6ad89f7ed8eebd87f64aa4face9ec0db84`.

| Feasibility indicator | Aug 29 | Oct 11 |
| --- | ---: | ---: |
| Selected races with verified numeric official race ID | 3 | 4 |
| API horse rows from selected races | 31 | 34 |
| Distinct numeric HORSES IDs | 31 | 33 |
| ID repeated in different selected races on the same day | 0 | 1 |
| One-to-one race/name match with positive GPS | 26 | 26 |
| One-to-one race/name match with all-zero GPS | 2 | 3 |
| API records without uniquely matched GPS | 3 | 5 |
| Official ID/GPS rows with unambiguous same-day name | 28 | 29 |
| Published GPS horse rows over the *whole meeting* | 94 | 76 |
| Track-rating category in all selected official races | Good | Good |

**Cross-date verification:** of the unambiguous, directly matched
official ID/GPS rows, **2 numeric internal HORSES IDs recurred with
the same normalized official horse name across both dates**.
Both repeated IDs had *positive recorded GPS telemetry on both dates*.
No name changes were found among these two ID repeats.

Crucially, this verifies a *source-record-level recurring official
animal ID* for a very small, deliberately selected subset. It is a
real equine repeated-record **feasibility finding**, not a causal,
evolutionary, or population-general biological discovery.
It does **not** prove that a particular zero-GPS nomination actually
started a race.

## Why H1 and H2 are still not identifiable

1. **No ground contrast:** the selected source races on both dates
   were all officially rated **Good**. No within-horse comparison
   between Good and non-Good ground is possible. H1 random-slope
   heterogeneity is **HOLD**.
2. **Only two repeated IDs:** these source-level repeated horses
   were identified by intentional two-date/selected-race sampling,
   not random population sampling. Even with environmental variation,
   they would be insufficient for a well-powered individual-slope
   distribution or reliable horse-by-opponent interaction.
3. **Nominations are not necessarily confirmed starters:** October's
   four selected official races included 34 horse list entries but
   only 33 distinct IDs. A horse ID appeared twice on the same
   calendar day in different race listings. This could reflect
   nominations/withdrawals and makes the `GetHorsesForRace` response
   unsuitable as an actual starter roster without result checks.
4. **GPS missingness vs finishing:** positive intervals are real
   published telemetry, but all-zero rows do not distinguish
   nonstart, scratch, DNF or sensor loss. No certified per-horse
   official finish time/position was joined.
5. **No pre-race historical opponent phenotype:** the GPS source
   contains repeated sectional distances and vendor signals,
   without validated units/first-call position and complete
   official starter confirmation. H2 remains **HOLD**.
6. **Current source selection is deliberately targeted:** race IDs
   absent from official API were never guessed; no evidence of
   comprehensive longitudinal coverage or individual random
   assignment follows.

## Reproduction without exporting horse identities

Script:
[`scripts/ecology_rq_two_date_horse_id_repeat.py`](../scripts/ecology_rq_two_date_horse_id_repeat.py).

~~~bash
python -m unittest discover -s tests -p 'test_ecology_rq_two_date_horse_id_repeat.py' -v
python scripts/ecology_rq_two_date_horse_id_repeat.py \
  --output tmp/rq-two-date-recurrence.json
~~~

The script calls only `GetMeetingsForDate`,
`GetRacesForMeeting`, and `GetHorsesForRace` for the
two dates and up to four selected races per day, plus one
official sectional CSV per date. No third-party mass crawl is
needed. Network response hashes, sources, method limits and
aggregate match/recurrence counts are recorded. Horse names,
numeric internal HORSES IDs and raw GPS data are **not**
written into the public repo or output artifact.

The two-date workflow includes a wholly fictional-ID unit test,
hash/provenance recording, an explicit missing-race-ID count,
and machine-readable scientific HOLDs. It runs independent
of the original one-race API check.

## Follow-up for a genuine animal ecology paper

- Identify a representative temporal cohort over multiple seasons
  and verify official IDs through a **complete, confirmed-starter
  + result** crosswalk, not just declared entrant lists.
- Quantify same-horse repeated starts under *two distinct going
  conditions*, preferably with repeated exposures within matched
  track/distance/class strata and jockey/age/rest covariates.
- Verify official individual time/sectional units and source
  availability timing. Partial data and source-panel missingness
  must be audited for conditioning on participation and finish.
- Only then test the individual reaction norm variance H1 and
  competitor context interaction H2, with preregistered null
  contrasts, race/horse dependence and forward replication.

**No real Thoroughbred H1/H2 coefficient has been estimated in
this two-date pilot.**
