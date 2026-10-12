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
| earliest_feature_available_jst | ISO-8601/null | Crucial for backtesting pre-race availability |
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
