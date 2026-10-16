# v2 decision policy

This policy separates horse ranking from ticket pricing.

## 1. Candidate generation
Use recent same-class form, similar distance/surface, direct head-to-head evidence, and only then course history to build a broad candidate set.

## 2. Ranking
Use market rank only as a baseline. Adjust mainly for:
- recent same-class performance;
- same/similar distance and surface;
- direct comparisons against today's rivals.

Use smaller adjustments for:
- Kyoto-only records when starts are few;
- jockey/course historical rates;
- first-time course/jockey effects.

Layoffs, large weight changes, first course/distance, and first jockey are uncertainty terms, not automatic negative points.

## 3. Ticket selection
Freeze the ranked horse set before comparing ticket prices. Compare win/place/frame/quinella/wide/exacta/trio/trifecta only within the same intended horse set/event. Do not jump from a higher-ranked horse to a lower-ranked horse solely because its payout looks attractive.

## 4. Live-action gate
Historical calculations and actionable candidates are separate. A live candidate must have:
- race/date/venue/market identity verified;
- runner/jockey/scratch status verified;
- quote display time verified and no more than 15 minutes old;
- current time earlier than the race-start-minus-2-minutes cutoff.

If any item is unknown, status is HOLD and the historical snapshot remains descriptive only.

## 5. Evaluation
After results are official, score separately:
- winner in pre-race Top 3;
- unordered Top-2 capture;
- actual Top-3 recall inside the broad candidate set;
- rank error of the winner;
- whether ticket selection preserved the horse ranking;
- realized return of the actually proposed ticket set;
- market rank vs model rank.

No post-result relabeling of marks.
