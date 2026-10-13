# Eagle Farm: independently named venue for cross-site HORSES-ID ICC validation

**Locked source-coverage cohort on 2026-10-13, before ANY
Eagle Farm horse-ID recurrence or ICC fit on this cohort.**

This is a **prospective-in-workflow selection of official source
meeting dates**, NOT a preregistered ecological effect hypothesis.
The Cannon Park exploratory ICC = 0.431738, original 12-date
source audit, method and limitations were already known before
this source selection. Eagle Farm is a different
*Racing Queensland track*, not a new independent operator
or measurement technology.

Official sources:
- [Racing Queensland Thoroughbred Sectionals
and Position Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
- [Official RQ web service](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf)
  (\`GetMeetingsForDate\`, \`GetRacesForMeeting\`, \`GetHorsesForRace\`)

## Fixed original source dates

The official Sectionals index was inspected for files
\`YYYYMMDD_Eagle_Farm_T.csv\`; all the following original files
were present in the index, and the meeting API's exact
\`TrackName="Eagle Farm"\` was independently checked for
January 3, April 18, June 13, October 10.

The following spread across January–October 2026 was
**chosen for time/season coverage, not for horse names,
repeatability results, observed GPS timing or race-day
track ground effects**:

| Original source date | Exact allowlisted GPS CSV |
| --- | --- |
| 2026-01-03 | \`20260103_Eagle_Farm_T.csv\` |
| 2026-02-14 | \`20260214_Eagle_Farm_T.csv\` |
| 2026-03-07 | \`20260307_Eagle_Farm_T.csv\` |
| 2026-04-18 | \`20260418_Eagle_Farm_T.csv\` |
| 2026-05-02 | \`20260502_Eagle_Farm_T.csv\` |
| 2026-06-13 | \`20260613_Eagle_Farm_T.csv\` |
| 2026-07-25 | \`20260725_Eagle_Farm_T.csv\` |
| 2026-08-08 | \`20260808_Eagle_Farm_T.csv\` |
| 2026-08-29 | \`20260829_Eagle_Farm_T.csv\` |
| 2026-09-19 | \`20260919_Eagle_Farm_T.csv\` |
| 2026-10-03 | \`20261003_Eagle_Farm_T.csv\` |
| 2026-10-10 | \`20261010_Eagle_Farm_T.csv\` |

For **each** date, attempt numeric RQ Race Id for
official race numbers **1, 2, 3, 4, 5 and 6**.
Record any missing race IDs explicitly.
Do not guess missing races or change the dates based
on observed pace, between-animal variance or the
direction of a result.

## Original-data quality gates and target (defined before this run)

- Match a unique numerical original \`HORSES\` internal ID
  to a unique name in the same original Eagle Farm
  date+race-number sectional CSV.
- Exclude all-zero first GPS time/signal, invalid first
  distance marker, duplicate name in different
  original race blocks on the same meeting date and
  original HORSES IDs appearing on multiple race lists
  on the same date. These are **data completeness
  filters, not inferred non-starters**.
- Only races with **at least four** original horses
  having positive first interval observations are
  included. Report fraction lost by race and date.
- Use the **same mathematical outcome and fitting
  code as Cannon Park**:
  \`first_section_time_s = original race fixed
  intercept + original HORSES-ID random intercept
  + conditionally normal residual\`.
- Calculate race-adjusted Gaussian
  conditional ICC (point only), sensitivity
  for >=6 positive-GPS animals per race,
  and leave-one-entire-meeting-day-out
  estimates. If sufficient repeated IDs /
  race contrasts are absent, produce **HOLD**,
  not a default zero, forced estimate or
  hand-picked race set.
- First GPS distance marker may differ
  between races and tracks. Report
  \`100/150/200/250m\` section cohorts
  separately using the **original same code**
  with insufficient cohorts explicitly HOLD.
- **Between venues, ICCs are comparable as
  conditional model-point diagnostics only,
  not as fixed biological effect sizes.**
  Race surfaces, field structures, distances,
  measurement error, cohort selection,
  rider/age/trainer mixture and original
  telemetry completeness are not matched.
- The original \`GetHorsesForRace\` SOAP may
  return nominees rather than confirmed
  starters; there is no independently verified
  final results/finish time or exact individual
  behavior measure from these source records.
- No p-value or confidence interval is planned
  for this initial cross-site feasibility check;
  there are too few source-date clusters for
  naive independent-horse inference.
- Original individual names, HORSES IDs, jockey
  and trainer IDs, first-section records and
  predictions are never committed or emitted:
  original source file hashes and summary counts
  only, with Racing Queensland attribution.

### Scientific decision tree

If repeat-ID support is inadequate: **HOLD_INDEPENDENT_TRACK_ICC**.
If race-conditioned ICC is identifiable:
report numeric value *with sample size and
source-selection sensitivity*, comparing its
sign and numerical stability **without**
asserting independent confirmation of
innate personality, heritability, ground-response
H1 or competition effect H2.
No new source dates are allowed in the initial
fixed-cohort report after viewing the outcome.
Any follow-up expansion must be labelled as
**post-hoc exploratory** and kept separately.

Document/source license:
[Racing Queensland Open Data](https://www.racingqueensland.com.au/about/reports-and-data/open-data).
