# v3 candidate-generator freeze

Frozen after retrospective diagnostic: 2026-10-13.

## Exact implementation

- `scripts/generate_v3_candidates.py`
- Git blob: `060b0cef7de1b185258fa3698233151d32760a87`

The module creates a **broad candidate union only**. It does not rank horses and does not choose betting tickets.

Current signals:
- saved market Top 4;
- recent same/similar-distance win;
- recent same/similar-distance close Top-3 finish;
- lightly raced latest win with a wider distance window;
- lightly raced latest close form with a wider distance window.

Layoff and condition shifts are uncertainty flags, not automatic exclusion rules.

## Retrospective diagnostic

Using the fully migrated 2026-10-12 Kyoto 7R-12R inputs:

- winner captured: 6/6;
- mean Top-3 recall: 88.9%;
- full Top-3 capture: 4/6 races;
- average candidate count: 8.17;
- average field coverage: 58.2%;
- Top-3 hits / candidate slots: 16/49 = 32.7%.

Baselines on the same races:
- old marked candidates: winner 5/6, mean Top-3 recall 83.3%, 15/38 Top-3 hits per candidate slot;
- market Top 4: winner 5/6, mean Top-3 recall 66.7%, 12/24 Top-3 hits per candidate slot.

The v3 union therefore has higher recall but substantially lower selectivity.

## Interpretation

This is **not validation**. The rules were designed after reviewing failures from the same race day, including 12R. Tuning candidate thresholds again on these six races would increase same-sample overfitting.

The implementation above is now frozen for the next forward test. Any change to thresholds or signals creates a new version and must not be scored as the same v3 freeze.

## Forward-test requirements

On a future race set, before results:
1. pass the v3 recent-history data gate;
2. record the exact candidate set and generator blob SHA;
3. record market Top-4 baseline;
4. do not modify the generator after seeing results;
5. score winner capture, Recall@3, candidate-set size, field share, and Top-3 hits per candidate slot;
6. only call the generator improved if it beats the baseline across multiple independent races without simply expanding coverage.


## Forward-freeze implementation

Added:
- `scripts/freeze_v3_forward_test.py`
- `tests/test_freeze_v3_forward_test.py`

The freeze manifest:
- rejects freezes at or after race-start minus 2 minutes;
- rejects any `DATA_HOLD` input;
- records the migrated data blob SHA and candidate-generator blob SHA;
- records the candidate set and saved market Top-4 baseline;
- sets `result_attached=false` and does not perform ranking or ticket selection.

Focused TDD verification for this component: 3 tests pass after the expected RED import failure before implementation.

### Anti-replay check

The post-race-migrated Kyoto 12R data was intentionally tested against a hypothetical 2026-10-12 16:00 freeze. All 16 histories have `history_checked_at_jst` on 2026-10-13, so the data gate returns `future_history_check` and blocks the freeze.

This is desired behavior: post-result data repair cannot be presented later as if it had been available before the race.
