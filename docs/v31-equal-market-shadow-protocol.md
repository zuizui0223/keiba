# v3.1 same-cardinality market shadow evaluation

**Status:** Descriptive comparator specified before the first prospective holdout race. It is not confirmatory, does not modify v3.1, and does not change PROMOTE / NO_PROMOTION.

## Why this comparison matters

The registered primary exact test compares added non-M horses against a **uniformly random subset of non-M horses**, holding the size fixed. But win odds carry ordering information among non-M horses as well, so beating random enlargement is not necessarily an improvement over simply including the next-most-popular horses.

## Fixed secondary procedure

After a race has a valid pre-result `freeze.json` and an independently stored official `result.json`:

1. Let K equal the exact size of the frozen v3.1 `union`.
2. Rank **all active horses by their frozen pre-race win odds**, from shortest to longest. For an exact tie, order numeric horse numbers ascending.
3. Take exactly K horses as `market_same_size`. Both lists therefore have equal capacity.
4. Compare winner coverage, top-three coverage, unique rescues, and per-race difference.
5. At the K-th odds cutoff, report the **minimum and maximum possible top-three hits** if tied horses could be exchanged, keeping all strictly shorter-priced horses selected. This exposes sensitivity to arbitrary tie-breaking.

Use the **same frozen odds** as M. Do not use final odds or modify the pre-result candidate set.

Implementation: `scripts/v31_equal_market_shadow.py`. The script fails closed for missing odds, duplicates, inconsistent race identity or candidate set, and stores input hashes. It only creates a separate result-after-race shadow file.

```bash
python -B scripts/v31_equal_market_shadow.py \
  --freeze holdout/v31/001/freeze.json \
  --result holdout/v31/001/result.json \
  --output holdout/v31/001/equal-market-shadow.json
```

## Reporting after 20 scored races

Report side-by-side total top-three hits, winner capture, per-race differences, unique rescues and boundary-tie sensitivity. Candidate count must match race by race.

This shadow comparison has **no preregistered formal p-value or promotion threshold**. It is descriptive only. Never use interim shadow outcomes to tune v3.1 or change its existing three-part promotion decision.

If v3.1 meets PROMOTE against equal-size random non-M addition but ties/loses against the equal-cardinality odds ranking, the supported claim is limited to **better-than-uniform-random rescue**, not evidence of additional information beyond market ranks.

## Development-only check: Kyoto 2026-10-12 R7-R12

Machine-readable data: `reports/2026-10-12/v31-equal-market-development.json`.

| Method | Candidates | Top-three hits |
| --- | ---: | ---: |
| M-only top quarter | 22 | 11/18 |
| Odds-ranked, same per-race size as v3.1 | 49 | 17/18 |
| v3.1 union | 49 | 18/18 |

R8 #7 レーヌマロン was the sole additional top-three horse captured by v3.1. Five of six races tied in top-three hits.

**These are in-sample development numbers.** The same races were available while v3.1 was designed. They are not prospective evidence of added predictive value.
