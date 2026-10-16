# First-party Racing Queensland SOAP endpoint scope: assigned fields versus confirmed postrace outcomes

**Read-only source/specification audit, 2026-10-15.** This note
does not introduce original animal-level data or independently
verify any real starter, race finish, jockey switch or horse age.

## Authoritative first-party sources checked

- Official Racing Queensland [Open Data Web Services operation list](https://www.racingqueensland.com.au/OpenDataWebServices/).
- Official [Open Data Web Services Protocol & Interface Specification](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf),
  version 1.0 (09 January 2014), Sections 4.15 and 4.16,
  **printed pp. 27–28**, PDF viewer pp. 27–28.
- Official [Racing Queensland Open Data page](https://www.racingqueensland.com.au/about/reports-and-data/open-data),
  describing categories of agency-held racing information
  and showing original thoroughbred racing data as an
  openly licensed dataset category, subject to the
  applicable release/usage conditions.

The published protocol explicitly describes
GetHorsesForRace as returning a set of original
HORSES entity IDs, HorseName, Weight,
Jockey Id and its FullName, and Trainer Id and
its FullName. It describes Jockey and Trainer as
assigned to the horse in the race-source record.

The published GetHorseDetailsInRace schema,
whose parameters are RaceId and HorseId,
has the **same attributes** (one Horse rather
than a list of Horses).

Neither of these TWO specific documented SOAP
response schemas includes a structured final
starter indicator, original scratch / DNF status,
a reconciled final actual-rider-change log, an
individual certified finish time or a verified
GPS sampling/coverage denominator. It would be
incorrect to infer such information merely from
a horse's presence in these responses.

### Interpretation limitation

The absence of these attributes from two SOAP
schemas does **not** prove that Racing Queensland
does not publish results, scratchings, steward
reports, altered jockeys or finisher records
in OTHER data products, official pages or
separate files. Its open-data policy explicitly
mentions racing results, scratchings and
jockey alterations among agency data categories.
Other products must each be independently inspected,
their original dates and identities reconciled,
and reuse/redistribution rights checked.

**Therefore the current research program's
observed original Jockey/@Id and Trainer/@Id
values are source-assigned fields, not a
certified postrace causal treatment or validated
final actual jockey/trainer history.**
Source-row presence is not proof a nominated
animal actually started or finished the race.
First GPS duration is not the individual
certified full-race finish time.

A positive horse-ID-associated repeatability
or historical-prediction score remains a
source-conditionally associated observation.
Horse-by-ground H1, competitor-response H2,
genetic/innate personality, age decay and
confirmed effects of rider replacement are not
identified by these two SOAP operations.

## Data rights and reproducibility

Racing Queensland's original Open Data page
states that original Thoroughbred Racing Data
are available in multiple formats including
HTML, PDF, CSV, XML and limited web services,
with an open-licence indication on the table.
However, the original protocol specification
also reserves agency rights and describes
possible restrictions or charges for
commercial uses. The two statements are not
an unconditional permission to mirror raw
runner-level GPS/source records under any
circumstances.

For the present draft, publish only licensed
methods, original-source attribution,
anonymous counts/model summaries and
SHA256 source fingerprints. Any sharing of
raw named horse, licensed rider/trainer,
individual sectional or final outcome records
requires a specific rights review.

## Minimum source upgrade for causal/generalizable ecology

1. Verify a first-party historical list of
   **actual starters**, their official dates,
   number of starts, distance and race Class.
2. Independently confirm final **actual**
   jockey and trainer assignment and
   their changes since the original
   SOAP source nomination/acceptance.
3. Obtain certified individual finish status
   and elapsed time, versus mere first
   GPS-positive telemetry.
4. Account for GPS absence even in
   confirmed actual starters and preserve
   raw source edition/digest provenance.
5. Re-evaluate the pre-fixed repeated
   same-HORSES-ID and exact
   marker+distance+Class support gate
   before biological random slopes or
   temporal transfer interpretation.

*This is a technical verification of
public documentation, not a legal opinion
or an actual finish-status study.*
