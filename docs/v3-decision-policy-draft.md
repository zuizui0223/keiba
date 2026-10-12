# v3 decision-policy draft after the 12R forward-test failure

Status: post-result design draft, **not validated**.

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
