# Locked 2026 Cannon Park sectional calendar cohort — source coverage, NOT hypothesis preregistration

Locked on **2026-10-13**, **before fetching the additional seven
source dates' official HORSES-ID/sectional overlap**, but **after**
the original five-meeting H1 design audit (20 races) and its 38-race
post-hoc sensitivity (showing zero >=2 Good / >=2 wet exact-class
individual contrasts).

This is a **predeclared source-coverage cohort for a feasibility
audit**, not a prospectively registered biological effect test.
No estimation of a ground-effect coefficient, random-slope
variance or social competition response is authorized by this
source-coverage note.

## Eligibility rule and fixed calendar

Include every **2026** `Ladbrokes Cannon Park` Thoroughbred
meeting through October 13, 2026 for which the [official Racing
Queensland Thoroughbred Sectionals index](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
lists an actual `*_Ladbrokes_Cannon_Park_T.csv` file.
Exclude barrier trials / `Cannon Park Night` and meetings
with position-map PDF only but no sectional CSV. All available
official race numbers **1–8** on each date are requested; missing
or unknown official race IDs are recorded as missing, not fabricated.

The official [Racing Queensland race meeting pages](https://www.racingqueensland.com.au/racing/full-calendar)
supply the categorical track ratings below; cross-check with
`GetRacesForMeeting` for *each* race and never assume uniformity
if a specific event has a different rating.

| Meeting date | Ground at original meeting | Cohort role | Original GPS file |
| --- | --- | --- | --- |
| 2026-02-16 | Heavy 8 | **New** | `20260216_Ladbrokes_Cannon_Park_T.csv` |
| 2026-03-12 | Heavy 8 | **New** | `20260312_Ladbrokes_Cannon_Park_T.csv` |
| 2026-03-26 | Heavy 9 | **New** | `20260326_Ladbrokes_Cannon_Park_T.csv` |
| 2026-04-04 | Heavy 10 | **New** | `20260404_Ladbrokes_Cannon_Park_T.csv` |
| 2026-04-09 | Soft 7 | **New** | `20260409_Ladbrokes_Cannon_Park_T.csv` |
| 2026-05-15 | Heavy 9 | Original cohort | `20260515_Ladbrokes_Cannon_Park_T.csv` |
| 2026-05-29 | Soft 5 | Original cohort | `20260529_Ladbrokes_Cannon_Park_T.csv` |
| 2026-07-23 | Soft 7 | **New** | `20260723_Ladbrokes_Cannon_Park_T.csv` |
| 2026-08-22 | Soft 6 | Original cohort | `20260822_Ladbrokes_Cannon_Park_T.csv` |
| 2026-08-28 | Good 4 | **New** | `20260828_Ladbrokes_Cannon_Park_T.csv` |
| 2026-08-29 | Good | Original cohort | `20260829_Ladbrokes_Cannon_Park_T.csv` |
| 2026-10-11 | Good | Original cohort | `20261011_Ladbrokes_Cannon_Park_T.csv` |

**Calendar count:** 12 dates total; seven new dates, five carried
forward. Dates and race-number selection do not depend on observed
first-section performance values or overlap estimates on the
additional seven meetings.

The 2026-02-09 and 2026-04-14 meeting name variants, if shown in
official calendars, are **not included** here because the official
sectional-CSV index reviewed for this cohort did not provide a
corresponding Cannon Park sectional CSV link. This audit does not
claim comprehensive coverage of all races at this venue.

## Predeclared data read and quality gate

- Source 1: official `GetMeetingsForDate` (exact real meeting
  date + venue, non-barrier-trial) => numeric Meeting Id.
- Source 2: `GetRacesForMeeting` => race numbers 1 through 8,
  numeric official Race Id, ground, class, scheduled distance.
- Source 3: `GetHorsesForRace` for *each actually returned*
  Race Id => source HORSES numeric individual ID and HorseName.
- Source 4: original official GPS sectional CSV for that **date**.
  Only a unique same-race exact normalized name and positive first
  interval time/signal qualifies as a *source-observed interval*.
- Exclude ambiguous same-day duplicate animal names and repeated
  official HORSES Ids in separate race lists; never guess that a
  nominee/zero-telemetry horse actually started or finished.
- Report source hashes and counts only, **no animal IDs/names or
  individual raw measurements** in GitHub output.
- A requested race missing from SOAP remains explicitly missing.
  A failed date is recorded as **HOLD** and excluded, not interpreted
  as zero horses or zero environmental response.

## Hierarchical overlap checks in fixed order

1. Source IDs with at least two records on **different race dates**.
2. IDs with at least one `Good` and one `Soft`/`Heavy`
   first positive section observation, no equality-of-ground spacing.
3. Same official race distance and same first measured section marker.
4. Same exact official race class *in addition* to (3).
5. Strict individual-stratum replication: at least **two Good and
   two non-Good** measurements in the same
   distance×first-marker×class stratum.
6. Separately report stricter **class + calendar-time support**
   and the number of independent horse IDs satisfying (5),
   not simply the number of duplicated strata.

These gates are *data-readiness/positivity screens*.
No biological effect-size sign test, likelihood model,
p-value, confidence interval, power claim or evolutionary
selection conclusion is part of this first expanded-source
audit. The original 20- and 38-race results remain archived
and are not replaced.

## Material unresolved sources of error

**Critical:** the SOAP HORSES listing is a declaration/nomination
list, not independently verified confirmed starters or race
finishers; the GPS rows have zeros and lack source-internal
horse IDs. The raw GPS first duration is not a verified
individual **full race finish time**. RaceClass can be coarse,
and the venue's rail, rider, class, distance and age/fitness
profiles may differ over the year. This means passing the
positivity thresholds could justify the *next level of
data construction*, never H1 being supported.

Source conditions and attribution:
[Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data),
[Original Sectionals index](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals).
