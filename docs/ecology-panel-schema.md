# Ecological panel specification (proposal only)

Unit of observation: **one horse per official race start**. Never collapse horse records prematurely; never infer historical individual starts from aggregate win-place-show counts.

## Required table (CSV/Parquet; one row per horse_id × race_id)

| Field | Type | Definition / leak control |
| --- | --- | --- |
| race_id | string | Official unique race identifier |
| horse_id | string | Stable official horse identifier, never name-only |
| race_date_jst | YYYY-MM-DD | Date race was run |
| race_start_jst | ISO-8601 with timezone | Temporal cutoff for features |
| venue | string | Official racecourse |
| course_surface | enum | turf / dirt (separate strata) |
| course_distance_m | integer | Official race distance |
| track_going | category | Ground condition **announced before start** |
| weather_at_start | string/null | Verified historical observation with time/source |
| class_pre | string | Competition class known before start |
| jockey_id | string/null | Pre-race announced jockey, retain changes |
| field_size | integer | Confirmed runners, not originally entered headcount |
| gate | integer/null | Official draw |
| assigned_weight_kg | number/null | Declared carrying weight before race |
| age_at_start | number/null | Horse age as of start |
| prior_rest_days | integer/null | From prior official start strictly before date |
| prior_front_runner_score | number/null | Historical positional profile from previous starts only |
| other_front_runner_share | number/null | Other entrants' historical profiles; leave-one-out |
| prior_opponent_strength | number/null | Strength of other entrants estimated only from earlier records |
| finishing_position | integer/null | Postrace outcome, null for nonfinisher/cancellation |
| finish_time_s | number/null | Postrace individual elapsed time, when available |
| finish_status | enum | finished / did_not_finish / withdrawn / excluded / other |
| source_url | string | Authorized record provenance |
| source_observed_at_jst | ISO-8601/null | When data was retrieved |
| feature_available_at_jst | ISO-8601/null | Crucial for backtesting pre-race availability |
| source_license | string/null | Reuse rights; never presume redistribution permitted |

## Constraints and checks

- Unique (race_id, horse_id); race-level variables identical within race_id.
- Horse IDs link across venues/years; race results never appear in pre-race features.
- Track_going may be categorical; avoid treating Good/Soft etc. as equally spaced metric without justification.
- Historical running style defined from starts strictly before target event and preferably adjusted for venue, distance and jockey; do not use in-race passage positions from the target event.
- Report missing-by-source, missing-by-condition, and overlap of horse exposures across conditions. A horse with one environment condition has no empirically identifiable within-horse slope.
- The historical start time used for each feature must not exceed target race_start_jst; use earlier cutoffs when official announcement times matter.
- Race results and race times are post-race outcomes. Do not fit ecological tests on betting odds as a substitute for performance.
- Do not commit licensed or redistributed race records without source approval.

## Existing files as pilot provenance

The existing analysis/kyoto-20261012 branch has approximately 95 starters across one Kyoto race card (6–12R), and stores per-horse course-level aggregates with sourced snapshots. It is useful to bootstrap identities/source procedures, **not sufficient to estimate environmental reaction norms**.


## Implemented v0 CSV contract (2026-10-12)

The first executable auditor is `scripts/ecology_panel.py`. It uses precisely
these required columns (unimplemented additional fields above remain valuable
for the full research design):

`race_id,horse_id,race_date_jst,race_start_jst,venue,course_surface,course_distance_m,track_going,class_pre,jockey_id,field_size,finish_status,finishing_position,finish_time_s,source_url,source_license,feature_available_at_jst`

Optional current column: `first_call_position`; also accepts
`age_at_start` and `prior_rest_days`. For `track_going` it currently
recognizes exactly `良`, `稍重`, `重`, `不良`. All race predictors and
their latest relevant availability time must precede `race_start_jst`.
`finish_status` is `finished`, `did_not_finish` or `pending`.
`finish_time_s` and `finishing_position` are postrace *outcomes*,
not permitted pre-race predictors.

`source_license` should say `synthetic` only for knowingly fabricated
records. `unknown`, `uncleared`, and `restricted` force a rights HOLD.
A provider data contract must be checked independently; an arbitrary string
here is not a real legal authorization.

The auditor requires unique horse×race keys, consistent within-race
metadata, no duplicate horse racing on the same day and explicit missingness.
A full roster is required to compute competition-composition predictors.
 For H2, repeated starts **against different opposing fields** are a separate
 identification requirement: many repeats with the same opponents are not
 informative. The auditor calculates a within-horse composition-variation
 count and flags a conservative context-overlap HOLD when absent.
`first_call_position` is **postrace** data and is incorporated only from
previous calendar dates. Features are not constructed using any outcomes from
the target day. The `--features` output carries a
`lagged_feature_rule` watermark and must not be mistaken for observed
causal interactions.

H1 smoke-model requires complete official-finish-time rosters; this is a
possible source of selection bias. The model *never* treats missing time as 0.
The conservative 30-horse cross-going and 15-day readiness threshold is an
engineering threshold, **not** a power calculation or biological finding.
