# 2025 Doomben original GPS year-extension calendar lock

**Scope locked 2026-10-15 (before fetching any of the selected 2025 Doomben HORSES identities / individual first GPS times in the follow-up).**

This is explicitly **post-hoc measurement-feasibility follow-up** to the
2026 Doomben third-venue pilot, whose 150m and 200m marker cohorts
both failed the >=20 repeatedly observed original HORSES-ID gate.
It is **NOT** preregistration, an independent data-driven discovery,
an ecological horse personality test, H1 ground reaction-norm support
or H2 rival-context effect.

Official publisher and file source:
[Racing Queensland Thoroughbred Sectionals and Position Maps](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals),
and [RQ original SOAP open-data documentation](https://www.racingqueensland.com.au/rq-open-data-web-services.pdf).

## Deterministic selection BEFORE the new individual histories

From the original RQ public sectionals index, select the **earliest
and latest published Doomben turf sectional CSV per calendar month
in 2025**. Months with only one public source CSV contribute that
single source date. The index had **39 original Doomben 2025
sectional CSV dates**; this rule selects **23 dated files**:

| Original month | Frozen source CSV dates |
| --- | --- |
| January | 2025-01-22, 2025-01-27 |
| February | 2025-02-01, 2025-02-26 |
| March | 2025-03-19 |
| April | 2025-04-01, 2025-04-23 |
| May | 2025-05-17, 2025-05-28 |
| June | 2025-06-04, 2025-06-25 |
| July | 2025-07-12, 2025-07-30 |
| August | 2025-08-06, 2025-08-27 |
| September | 2025-09-06, 2025-09-17 |
| October | 2025-10-04, 2025-10-29 |
| November | 2025-11-15, 2025-11-29 |
| December | 2025-12-06, 2025-12-12 |

Each approved source filename follows exactly
`YYYYMMDD_Doomben_T.csv` at the official RQ endpoint.
Read only official race numbers **1–6** from each meeting.
An unreturned race ID or upstream SOAP error is a
separate `HOLD`, not a record of zero starts or no effect.

The source calendar was selected by **file availability and date**,
not by original horse IDs, timings, coefficients, source jockeys,
race going, race class, race winners or the direction of the prior ICC.
There is **no replacement-date rule** when a source URL or SOAP
response fails: preserve a per-date `HOLD` and count coverage.

## Exact predeclared research-data support questions

1. How many numeric original source `HORSES` IDs recur on at least two
   distinct 2025 source dates in identical first-GPS marker groups
   **150m** and **200m**?
2. Do those repeated IDs also recur after adding the previously fixed
   **19 selected 2026 Doomben dates**, with separate source coverage,
   source hashes, and original date/horse name consistency checking?
3. Do original 150m or 200m sections pass the **unchanged existing
   `race_fixed_reml`** minimum positivity gates: >=20 repeat IDs,
   >=12 source races, >=6 source dates, >=80 positive timed source
   rows, >=4 timed GPS horses per race?
4. If and ONLY if the unchanged gate passes, report a source-only
   Gaussian race-fixed-effect HORSES-ID ICC point estimate and its
   sensitivity with >=6 GPS horses per race, with no p-value,
   empirical confidence interval, outcome selection correction or
   genetic/causal claim.
5. Preserve exact same-section marker checks separately.
   **150m at Cannon** and **200m at Eagle** are *previously
   fitted reference sites*, not matched individual horses or
   independent GPS vendors. A model for source timing at
   different first markers is NOT a matched-trait replication.

## Original source/data quality gates

- Always join official `GetMeetingsForDate`,
  `GetRacesForMeeting`, `GetHorsesForRace` numeric IDs to
  uniquely named positive first-GPS entries in the **same real
  date/race**; retain original race-level TrackRating, Class,
  Distance and first-marker distance.
- Block name changes under a source HORSES ID and same-day names/IDs
  listed for more than one race; all-zero or missing GPS is never a DNF.
- Record original meeting/race/GPS SHA-256, plus an aggregate
  original HORSES-roster response fingerprint per meeting.
- Return **aggregate counts/HOLD codes only**. No horse names, HORSES
  numbers, rider/trainer licences, original GPS measurements, odds,
  race predictions, or raw source response documents in GitHub.
- **Source-snapshot caveat:** Earlier Cannon Park 548 vs 543 linked
  candidate counts were not reconcilable without the old original
  HORSES-list response hashes. New Doomben 2025 original rosters must
  therefore be fingerprinted and source-locked before using their
  ICC comparisons for scientific interpretation.
- Model dependence, nonrandom nominations, jockey/trainer/age,
  stable training assignments, source missingness, marker-specific
  measurement units, class differences and true final starters/results
  remain unverified.

## Scientific status

This is a **measurement harmonization + independent year source-coverage
audit**, following a recognized insufficiency. It cannot establish
a universal animal trait across racecourses, inherited personality,
recovery from wet tracks, H1 individual reaction norms, H2 social
plasticity, welfare, natural selection or a betting advantage.

The existing 2026 Doomben cohort is NOT modified or silently replaced.
The 2025 cohort and any combined 2025/2026 analyses must be labelled
post-hoc source-data expansion and report missing original source
dates separately.
