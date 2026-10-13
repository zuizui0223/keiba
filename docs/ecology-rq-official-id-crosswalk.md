# Official HORSES-ID ↔ GPS-sectional identity crosswalk: conservative gate

Status: **SOFTWARE READY, REAL HORSE-ID CROSSWALK NOT YET VERIFIED**.
Added 2026-10-13 to prevent unverified equine biological IDs from silently
entering H1/H2. No live SOAP IDs or real official result roster has yet
been successfully joined to the real sectionals.

## What the schema really needs

The official Racing Queensland
[Open Data Web Services](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf)
describes `GetHorsesForRace`, returning an internal `HORSES` horse
identifier. Separately, the official
[Thoroughbred Sectionals and Position Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
download supplies date, race number, **horse name** and timing triples.
The latter does not visibly include the `HORSES` ID; its early
integer field has not been independently verified as a racecloth
or finish position.

Therefore linking records from these sources is an **identity
resolution problem**, not a safe direct join.

## Offline-only verification contract

`scripts/ecology_rq_official_id_crosswalk.py` reads one previously
downloaded official sectional CSV and an **independently verified**
official starter/result roster export. The local roster CSV needs
these exact columns:

| Column | Role |
| --- | --- |
| `race_date` | Genuine `YYYY-MM-DD`; must match GPS date |
| `race_number` | Genuine number within the same official race meeting |
| `official_race_id` | Authoritative original Racing Queensland race ID |
| `official_horse_id` | Original `HORSES` stable internal horse identifier |
| `horse_name` | For *provisional* within-race exact name matching only |
| `start_status` | One of `started`, `not_started`, `unknown` |
| `finish_status` | One of `finished`, `did_not_finish`, `not_applicable`, `unknown` |
| `source_url` | Exact HTTPS first-party evidence/provenance for that official roster row |

Note: the program cannot independently verify that a supplied local
file genuinely came from Racing Queensland or that an official finish
status was available. **Never invent these attributes from the GPS
source or an odds market.** If real official values are not accessible,
the correct status is **HOLD**, not data completion.

### One private, bounded command

~~~bash
python scripts/ecology_rq_official_id_crosswalk.py \
  --sectionals /private/rq/20261011_Ladbrokes_Cannon_Park_T.csv \
  --official-roster /private/rq/cairns_verified_official_starters.csv \
  --audit tmp/rq-identity-audit.json
~~~

Paths are examples, **not files already produced or a claim that the
roster exists**. The program uses no network, writes only aggregate
counts/flags and a sectional source SHA256, and keeps horse names
and internal IDs out of the public output.

The matching rule is **exact normalized horse name within a verified
date + race number**, only when both sides are unique. There is no
fuzzy name guessing or assignment of a raw sectional numeral to a
real horse ID. Names appearing in multiple race headings on the
same date are **blocked** rather than matched: this matters because
real source files contain 5 such ambiguous same-day names with
all-zero GPS in one heading and valid positive readings in another
(4 on 2026-10-11, 1 on 2026-10-10). These rows cannot be promoted
to reliable repeated biological observations.

A name successfully matched syntactically is only a **candidate**
official ID, not independent proof of a correct animal identity.
The status remains
`HOLD_OFFICIAL_EQUIVALENCE_AND_LONGITUDINAL_VALIDATION` until
external source verification, complete entrant rosters and
longitudinal recurrence checks have passed.

## Important interpretation limits

- **All-zero GPS is not DNF.** A separately verified official roster
  may reveal a nonstarter, finisher or other status; the telemetry
  does not.
- **A positive sectional does not establish a certified individual
  finish time.** The CSV race-level timing label differs from one
  official race-results time in the reviewed example.
- **Matching one race is not H1/H2 identification.** Need the same
  stable original horse IDs across *multiple* dates and varying
  going, distance, class and competitor composition, with
  race-specific provenance and strictly historical explanatory
  variables.
- The local `source_url` field is a provenance prompt, not proof
  of authorized redistribution.
- Any duplicate official ID+race, contradictory status, ambiguous
  within-race name or same-day repeated name must be rejected or
  held explicitly.

## Artificial validation

`tests/test_ecology_rq_official_id_crosswalk.py` uses entirely
fabricated official IDs and race headings. It verifies:

- same-day repeated names are **blocked**, not promoted;
- a GPS-zero row can be labelled `not_started` **only if** the
  separate fictional official roster explicitly says so;
- two official IDs with the same race/name do not receive an
  arbitrary tie-breaker;
- contradictory statuses and unsupported fuzzy matches are
  rejected;
- the aggregate output contains neither horse names nor official IDs.

The GitHub Actions `Ecological research QA` suite exercises these
tests. No biological H1/H2 result follows from passing software QA.
