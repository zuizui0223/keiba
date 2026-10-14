# Third-venue source cohort lock: Doomben 2026 first-GPS interval bridge

**Locked 2026-10-14, BEFORE original Doomben HORSES-ID recurrence,
fitted individual ICC, rider/role selection or horse-performance
statistics for the 19-date cohort were evaluated.**

This is a source-coverage and **measurement-compatibility** pilot,
not preregistration or a prospective confirmatory animal trait test.
Earlier Cannon Park and Eagle Farm ICC values, their measurement
mismatch, the 2-ID cross-venue overlap, and one 2026-10-05 Doomben
**CSV source-format/first-marker inventory only** were known in
advance. Do not retroactively label the source selection as
outcome-blinded if the broad research question was developed after
those earlier positive ICCs.

## Why a third track (and why Doomben)

The original [Racing Queensland Thoroughbred Sectionals index](https://www.racingqueensland.com.au/industry/thoroughbred/thoroughbred-sectionals)
lists real GPS CSVs for multiple Queensland racecourses.
The previous original-source experiments at Cannon Park and
Eagle Farm yielded positive pooled individual random-intercept
ICC point estimates, but there was **NO first-GPS marker
with enough repeat ID support at BOTH sites**:

- Cannon Park: supported 150m and 250m first markers;
- Eagle Farm: supported 200m first marker;
- Only 2 original HORSES IDs recur in both selected site cohorts,
  none with matched marker plus official distance.

One *source-layout screen only*, on the official Doomben
2026-10-05 sectional CSV, found original positive
first-interval markers of **110m, 150m, 200m and 260m**,
respectively 8, 17, 21 and 23 GPS-positive source rows.
This motivates a third track with potentially
**150m and 200m** source subsets. It does NOT
establish sufficient within-HORSES-ID repeatability
in either subset (the actual study test).

Doomben uses the same first-party RQ sensor/source pipeline
as Eagle Farm and Cannon Park and may involve overlapping
horse populations. It is **not** an independent sensor/vendor
replication and no shared individual trait can be inferred
merely from similar pooled ICCs.

## Deterministic exact source calendar, fixed before analyzing horse IDs

Source inclusion rule: for each month of 2026 from January
through October 5, include the **earliest AND latest
original Doomben Turf sectional CSV date** listed
in the official index. If only one source CSV is listed
in a month, use that one date.

This produces the following **19** specific, immutable
2026 original official Doomben dates:

| Month | Original source dates and exact filename suffix |
| --- | --- |
| January | 2026-01-14 / 2026-01-29 |
| February | 2026-02-07 / 2026-02-25 |
| March | 2026-03-04 / 2026-03-28 |
| April | 2026-04-01 / 2026-04-22 |
| May | 2026-05-16 / 2026-05-27 |
| June | 2026-06-03 / 2026-06-24 |
| July | 2026-07-11 / 2026-07-22 |
| August | 2026-08-01 / 2026-08-26 |
| September | 2026-09-12 / 2026-09-30 |
| October | 2026-10-05 |

Official file URL shape:
\`https://www.racingqueensland.com.au/RacingFile.ashx?path=/Sectional/YYYYMMDD_Doomben_T.csv\`

The exact source URLs are constrained to a separately coded
allowlist, not dynamically constructed from arbitrary input.
The official meeting API \`TrackName=Doomben\` was verified for
2026-01-14, 2026-03-28, 2026-06-24 and 2026-10-05
before the source lock, **without requesting any horse IDs or
individual outcomes from those meetings**.

Requested races are original numbers **1–6**, for every
selected meeting regardless of published score, field size,
race class, ground or original horse identity.
Unavailable official race numbers become explicitly
reported source-coverage gaps: never guessed or replaced.

## Analysis frozen before first original Doomben cohort fit

- Read \`GetMeetingsForDate\` → \`GetRacesForMeeting\`
  → \`GetHorsesForRace\` and the date-matched original
  first-party Doomben sectional CSV.
- Require a unique original HORSES numeric \`Id\`,
  normalized horse name identical *within the same
  official date and race*, positive original first
  GPS signal and time, and valid first GPS distance marker.
- Reject original name changes for one HORSES ID,
  same-day original ID appearing in multiple races,
  same-day GPS duplicate names, and all-zero section
  telemetry. No all-zero response is called DNF.
- Estimate the pre-existing **Gaussian absolute first-GPS
  time** race-FE + HORSES random-intercept conditional ICC.
  Preserve the existing >=4 and >=6 GPS-positive
  race thresholds, race-conditioned ID shuffle
  negative control, and delete-source-date stability.
- For first-section markers **150m** and **200m**,
  estimate separately using unchanged per-marker
  thresholds. Also report source size at marker
  110m, 250m, 260m or other as descriptive
  measurements but **NO ad hoc numeric H1 effects**.
- Before interpreting a cross-venue comparison, require
  separately numerical (non-HOLD) ICC at the **identical
  first GPS marker** at both study tracks. Note
  differences in field/class/race-distance populations
  and sensor residual variances. A matched marker
  alone does not make the sites causal/biologically exchangeable.
- Analyze source Weight, Jockey/@Id and Trainer/@Id
  completeness and allow an adjusted ICC **only** if
  the same-source cohort satisfies its predefined
  repeated-HORSES-ID and date coverage gates.
  Otherwise full adjustment must remain **HOLD**.
- Record the **one source-operator**, lack of
  independently verified final starter/finisher
  states, limitations of weight/jockey nominations,
  absence of animal age, source GPS dropout
  and absence of biological pedigree/genetics.

## Decision boundaries

- If 150m/200m repeated HORSES-ID source support fails:
  **HOLD_MATCHED_FIRST_SECTION_MARKER_ICC** rather than
  a numerical zero.
- If a marker-specific ICC succeeds, call it only a
  **third-track original-source observational
  repeatability point estimate**. It is not the
  same individual animal in two tracks unless
  separately linked by original numeric HORSES ID,
  matching name, and exact measurement context.
- No testing, prediction or purchasing of wagers,
  heritability, natural selection, adaptive horse
  personality, H1 ground-specific reaction slopes
  or H2 social competitor responses.
- **No raw identifiers, animal names, licensed
  rider/trainer identifiers, horse-level times,
  odds or predictions** in Github commits or
  published JSON. Only aggregate values,
  source-provenance URLs and source hashes.

The fixed dates may be used for a **technical
source-feasibility audit**. Future source-date
expansions must be labelled post-hoc and
kept separate rather than changing this
locked cohort in response to the ICC estimate.
