# v3 frozen evaluation spec

Frozen after development on 2026-10-13. This specification is for the **next independent race-day evaluation** and must not be changed in response to those future outcomes.

## Scope

v3 currently produces:
1. a fail-closed data-quality decision;
2. a broad review candidate pool;
3. a bounded review shortlist.

It does **not** produce calibrated win probabilities, an exact horse ranking, expected value, or betting tickets.

## Data gate

Every runner must have:
- `career_starts`;
- `history_checked_at_jst`;
- `history_source_url`;
- `source_latest_run_date`;
- structured `recent_runs`.

Use the latest 3 runs, or all career runs if fewer than 3 starts exist.

Each run must include:
- date;
- class;
- surface;
- distance;
- finish;
- source;
- either numeric beaten margin, official margin text, or an explicit source-missing reason.

The saved latest run date must match the source-reported latest run date.

Any failed runner => race status `DATA_HOLD`; no candidate output.

## Broad candidate signals

A horse enters the broad candidate pool if at least one signal is present:

1. **market_top4**  
   Saved pre-race win odds rank 1-4. Odds are a market-support signal only, not a probability estimate.

2. **recent_similar_distance_win**  
   Any of the stored recent runs: same surface, distance within ±200 m, finish 1st.

3. **recent_similar_distance_close_finish**  
   Any stored recent run: same surface, distance within ±200 m, finish Top 3, and beaten margin <=0.5 sec or official close-margin text (ハナ/アタマ/クビ/同着).

4. **lightly_raced_latest_win**  
   Career starts <=8; latest run on same surface within ±400 m; finish 1st.

5. **lightly_raced_latest_close_form**  
   Career starts <=8; latest run on same surface within ±400 m; finish Top 4; beaten margin <=0.6 sec or official close-margin text.

Uncertainty flags are descriptive only:
- layoff >90 days;
- latest surface switch;
- latest distance shift >300 m.

They do not automatically remove a candidate.

## Bounded shortlist

Keep the saved-market Top 4 as baseline.

From non-baseline broad candidates add at most 3 upside runners.

Upside weights:
- recent_similar_distance_win = 3
- lightly_raced_latest_win = 3
- lightly_raced_latest_close_form = 2
- recent_similar_distance_close_finish = 1

Sort upside candidates by:
1. score descending;
2. market rank ascending;
3. horse number ascending.

Maximum shortlist size = 7.

This ordering is a **review shortlist**, not a calibrated horse ranking.

## Evaluation protocol

2026-10-12 is development/training data and is excluded from v3 validation.

For each future frozen race record:
- broad candidate count / field size;
- broad candidate Recall@3;
- shortlist count / field size;
- shortlist Recall@3;
- winner included in broad pool;
- winner included in shortlist;
- market Top4 Recall@3 baseline;
- old-system candidate recall when an old frozen prediction exists.

Report coverage together with candidate-set size; higher recall obtained by selecting more horses is not automatically better.

Do not tune this specification from individual future misses. Accumulate at least **30 frozen races across at least 3 race days** before making an improvement claim. Earlier readouts are descriptive interim checks only.

## Betting boundary

Horse review and ticket selection remain separate.

No betting recommendation may be generated from this v3 review pipeline until a separate, prospectively validated ticket-selection layer exists.
