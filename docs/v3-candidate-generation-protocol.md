# v3.0 candidate-generation protocol

Status: **frozen after the 2026-10-12 Kyoto R7-R12 post-race audit and before any future evaluation race**.

This protocol was designed after observing R7-R12, so those races are **development / in-sample diagnostics only**. They must not be used as prospective evidence that v3 works.

## Objective

v3.0 does not try to optimize exact finishing order yet.

Its first objective is narrower:

> reduce omission of plausible top-three horses without turning the candidate set into nearly the whole field.

Ranking, calibrated win probabilities, and expected value are separate future stages.

## Inputs

Only information available before post time may be used:

- pre-race win-market rank from a timestamped snapshot;
- age and career-start count;
- last three race results;
- class of those races;
- surface and distance;
- graded/listed status;
- same-course/same-distance record;
- layoff length;
- jockey/horse partnership only as metadata, not a standalone rescue channel.

No race result, final sectional, or post-race comment from the target race may enter candidate generation.

## Candidate channels

A horse enters the broad candidate set if it satisfies **at least one** channel.

### M — market baseline

Include the top quarter of the field by available pre-race win-market rank.

```
M_count = max(3, ceil(field_size * 0.25))
```

Use at most 5 horses for M:

```
M_count = min(5, M_count)
```

If multiple horses are tied at the M cutoff, include all horses tied at that cutoff even if this expands M above the nominal count or above 5; record the tie expansion.

If the available market quote is stale or cannot be timestamp-validated, M is marked unavailable rather than silently substituted with a later/final market.

### C — recent same-class / adjacent-distance form

Include if at least one of the last three starts:

- was on the same surface;
- was in the same class or a higher class;
- had distance within ±20% of the target distance;
- and finished 1st-4th **or** was beaten by no more than 0.5 seconds.

Long layoffs do not erase this channel; they add an uncertainty flag.

### U — young class-riser / sparse-career growth

Include if all are true:

- age 3;
- no more than 5 career starts before the target race;
- most recent start was a win;
- same surface;
- distance within ±20% of target.

This deliberately retains a lightly raced horse moving up in class. Promotion itself is not treated as a negative score.

### Q — quality transfer

Include if, within the last four starts:

- same surface;
- distance within ±20% of target;
- the horse won a Listed/graded race, or finished top three in a graded race.

This channel captures transferable class/finishing ability even when exact-distance history is sparse.

### K — course / adjacent-distance specialist

Include if pre-race history at the same venue and surface, using races within ±20% of the target distance, satisfies either:

- at least 2 wins; or
- at least 2 top-three finishes.

Exact-distance performance should still be reported separately. The wider band is used only to avoid treating nearby distances as unrelated when the venue/surface evidence is repeated.

K is a candidate-generation channel only. It must not automatically outrank recent same-class form.

## Uncertainty flags

These do **not** remove a horse from the broad set:

- layoff > 120 days;
- first run at venue;
- first run at exact distance;
- first ride by current jockey;
- body-weight change >= 10 kg;
- class rise.

They widen uncertainty and must be reported separately.

## No ticket-driven horse substitution

Candidate generation happens before ticket-price comparison.

After horses/pairs are selected, compare prices only for the **same target event**. A higher quote may change frame/quinella/wide/exacta construction, but must not replace a selected horse with a lower-ranked horse merely because another ticket looks more attractive.

This rule directly addresses the R9 and R10 ticket-conversion failures.

## v3.0 output

For each race save:

- channel membership M/C/U/Q/K for every horse;
- union broad set;
- field size and broad-set fraction;
- all uncertainty flags;
- source URLs and observation timestamps;
- a pre-result freeze SHA.

No manual additions after freeze.

## Prospective evaluation contract

Do not tune any threshold until at least **20 future races** have completed under this frozen protocol.

Report:

1. winner recall of broad set;
2. top-three recall;
3. broad-set fraction of field;
4. incremental top-three recall over M-only;
5. per-channel unique rescues;
6. market rank of misses;
7. residual classification for misses.

A broad-set recall gain is not useful if candidate fraction approaches 100%. Therefore report recall and coverage together.

## Ranking

v3.0 intentionally does **not** introduce a newly fitted numeric ranking score.

Until the candidate-generation stage has prospective evidence, ranking uses market order as a baseline and the other channels are reported as evidence tags. Kyoto/course/jockey evidence cannot manually jump a horse over several market ranks without a separately frozen rule.

## Change control

Any threshold change creates v3.1 or later and starts a new prospective evaluation window. Do not rewrite this file after seeing holdout results; add a new version instead.
