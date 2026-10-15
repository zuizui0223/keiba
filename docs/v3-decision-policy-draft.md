# v3 decision-policy draft after the 12R forward-test failure

Status: post-result design draft, **not validated**. The data-completeness gate is implemented and currently fails closed on the frozen 2026-10-12 inputs.

## 1. Data-completeness gate before ranking

For every runner, store the latest N starts structurally:
- date;
- venue;
- class;
- surface;
- distance;
- finish;
- beaten margin;
- pace/position when available;
- jockey;
- source.

If the latest-start sequence is incomplete or stale, set `DATA_HOLD`. Missing evidence must not be treated as negative evidence.

This requirement is motivated directly by 12 ベラジオリン, whose frozen note omitted a later 2026-07-04 same-class 4th-place run.

## 2. Candidate generation as a union, not a single ranking cutoff

The broad candidate set should include the union of:
- baseline top-ranked runners;
- recent same/similar-distance winners;
- lightly raced 3-year-olds with a recent win or sharp improvement;
- recent same-class close finishes;
- market-supported horses;
- high-uncertainty upside cases that meet explicit criteria.

This would at least force 10 ビービーシナジー to be reviewed instead of discarded solely for class rise.

## 3. Separate mean prediction from uncertainty

Layoff, first course, first jockey, body-weight change and class rise should not be arbitrary negative points.

Output:
- central performance score;
- uncertainty score;
- reason codes.

Use uncertainty to decide whether to abstain or widen candidate coverage.

## 4. Transition features

Add explicit features for:
- age and starts count;
- recent improvement slope;
- first start after maiden win;
- same-distance recent win;
- class transition;
- recent speed/pace-adjusted figure once available.

A lightly raced 3-year-old class riser should not be treated like an exposed older horse moving up in class.

## 5. Ranking and ticket selection remain separate

Freeze horse probabilities/ranks first.
Then compare ticket markets **without changing the horse ranking because a different pair has attractive odds**.

If the horse model is uncertain, the system should say HOLD or keep multiple pairs; it should not manufacture confidence by choosing one high-paying pair.

## 6. Evaluation protocol

Do not use same-day post-race results both to tune and validate.

For each frozen version:
- freeze before a new race day;
- score winner rank;
- Recall@3 / Recall@5 / Recall@k;
- unordered Top-2 capture;
- NDCG or reciprocal rank;
- broad-set recall and candidate-set size together;
- actual proposed-ticket hit rate and ROI separately;
- compare against the market baseline.

Only after multiple independent races should a version be called improved.


## Implementation status (2026-10-13)

Implemented:
- `scripts/audit_recent_history.py` validates structured recent-run history before ranking.
- `tests/test_recent_history_gate.py` covers missing runs, stale source checks, lightly raced horses, future dates, and race-level fail-closed behavior.
- Local TDD verification: 9 focused tests pass. The TDD history includes the expected RED states before implementation: missing module, DATA_HOLD CLI returning 0, and latest-run/source mismatches not being detected.
- `reports/2026-10-12/v3-recent-history-gate-audit.json` records the current migration state.

Current frozen-input audit:
- Kyoto 7R-12R: 6 races, 83 runners.
- PASS: 0.
- DATA_HOLD: 83.
- All 83 currently predate the new structured schema and lack the fields required to PASS: `career_starts`, `history_checked_at_jst`, `history_source_url`, `source_latest_run_date`, and `recent_runs`.

This does **not** mean the old JSON is unusable as a historical record. It means v3 will not use it for a new ranking decision until recent-history data has been structurally refreshed.

Next migration requirement:
1. add `career_starts`;
2. store the latest 3 runs, or every career run when fewer than 3 starts exist;
3. include date, class, surface, distance, finish, beaten margin and source URL for each run;
4. record `history_checked_at_jst` at refresh time;
5. pass the data gate before ranking.


## 12R migration and candidate-union status (2026-10-13)

Structured-history migration is complete for Kyoto 12R in:
`data/2026-10-12/v3/kyoto_12.json`.

Independent reproduction of the data-gate rules returned:
- PASS: 16/16
- DATA_HOLD: 0/16

The original frozen `data/2026-10-12/kyoto_12.json` remains unchanged.

The margin schema now accepts either:
- numeric `beaten_margin_s`, or
- official text `beaten_margin_text` such as `アタマ` / `クビ`.

A first candidate-union implementation is in:
- `scripts/build_v3_candidate_union.py`
- `tests/test_v3_candidate_union.py`

Its 12R retrospective diagnostic is:
`reports/2026-10-12/v3-candidate-union-r12-diagnostic.json`.

With the frozen default parameters, the union selected 11/16 runners and retrospectively contained all official Top3. This is **not validation** because the rules were designed after seeing 12R. The important negative result is that the candidate set is too broad to count as a useful ranking system yet. No further threshold tuning should be done on 2026-10-12 results.


## Full migration completion and freeze (2026-10-13)

All Kyoto 7R-12R runners from 2026-10-12 have now been migrated into derived v3 inputs:
- 6 races
- 83 runners
- PASS: 83
- DATA_HOLD: 0

The fresh all-race verification is saved at:
`reports/2026-10-12/v3-gate-final-verification.json`.

The original frozen pre-race JSONs remain unchanged.

### Retrospective candidate-set comparison

Using the fixed v3 candidate-union parameters across all six races:

| candidate rule | selected / 83 | field coverage | Top3 hits / 18 | Top3 recall |
|---|---:|---:|---:|---:|
| market Top5 | 30 | 36.1% | 13 | 72.2% |
| v3 broad union | 54 | 65.1% | 17 | 94.4% |
| v3 reason_count >= 2 | 31 | 37.3% | 12 | 66.7% |

This is stored in `reports/2026-10-12/v3-candidate-union-cross-race.json`.

The broad union's higher recall comes with much wider coverage. At almost the same coverage as market Top5, the `reason_count >= 2` tier has lower retrospective recall. Therefore there is currently **no evidence that v3 adds predictive information over the market at comparable selectivity**.

The only Top3 slot missed by the broad union was 8R third-place runner 7 レーヌマロン. No rule or threshold is added to capture that horse after the fact.

### Frozen next-test version

`configs/v3-freeze-20261013.json` freezes:
- implementation blob SHAs;
- data-gate rules;
- candidate-union parameters;
- evaluation metrics;
- prohibition on further tuning with 2026-10-12 results.

The next legitimate performance test must use races from a different future race day. Until then, v3 remains **not validated**.


## Implementation status update (2026-10-15)

### Data migration

- Kyoto 7R–12R structured-history migration is complete: **83/83 runners PASS, 0 HOLD**.
- Original frozen pre-race JSON files are unchanged.
- For every runner, frozen `mark` and `notes` match the original inputs; sidecar/derived-history mismatches are zero.
- Source-latest-run synchronization and fail-closed DATA_HOLD remain mandatory.

### Broad candidate layer

Canonical implementation: `scripts/generate_v3_candidates.py`.

Retrospective diagnostic only:
- v3 union: 49 candidate slots, winners 6/6, Top3 16/18.
- old marked candidates: 38 slots, winners 5/6, Top3 15/18.
- market Top4: 24 slots, winners 5/6, Top3 12/18.

The union improves retrospective coverage but is less efficient per candidate slot. It is therefore frozen as a **broad screening layer**, not a ranking model. Do not tune it further on the October 12 races.

### Ranking-feature layer

`scripts/v3_ranking_features.py` now extracts descriptive candidate features without producing a score or predicted rank.

The frozen feature table is:
`reports/2026-10-12/v3-ranking-features.json`

It contains **49 candidate rows** and explicitly records:
- `ranking_produced=false`
- `target_fields_used=false`
- `official_results_joined=false`
- `ticket_selection_performed=false`

Features include market rank, career starts, days since latest run, recent wins/Top3, similar-distance form, same-class form, candidate-signal count and uncertainty flags.

### Validation boundary

The October 12 races were used to diagnose and design v3, so they are not out-of-sample validation.

The next legitimate validation must:
1. freeze the candidate generator and feature definitions before a future race set;
2. create any ranking/pruning rule without using those future outcomes;
3. compare against market baselines on multiple independent races;
4. track both recall and selectivity/candidate count;
5. evaluate ticket selection separately from horse ranking.

A container-level fresh test run of the exact GitHub branch could not be completed in the current environment because raw.githubusercontent.com DNS resolution failed. Local TDD runs were used during implementation, and GitHub-fetched data were independently recomputed for the 83-runner gate and candidate diagnostics.