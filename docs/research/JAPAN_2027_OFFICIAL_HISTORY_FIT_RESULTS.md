# JRA 2027: Point-in-time historical coefficient training — implementation validation

**2026-11-18 STATUS: SYNTHETIC TESTS PASS, REAL OFFICIAL-ID DATA UNAVAILABLE.**

A previous [2026 own/family freshness factorial](JAPAN_2026_OWN_KIN_FACTORIAL_RESULTS.md) established on a selected previously-active older-horse sample that newly published **own** history changes forecast quality much more than sibling-history updates. The original 2026 time-external family gain was not robust, and none of those post-hoc results establishes genetic inheritance. The next defensible question is whether a model fit before 2027 can outperform the simple midpoint and an own-history-only model on *future, truly unpublished* race results.

[PR #51's private pre-race forecast ledger](JAPAN_2027_POINT_IN_TIME_LEDGER.md) was missing actual M1/M2 historical training code. This branch supplies it.

## What the new trainer actually does

[Source code](../../scripts/ecology_japan_2027_official_historical_train.py) takes three **user-authorized local, private** CSVs, with the *same typed official horse and breeding identifier scheme* expected by the 2027 ledger: historical JRA entry snapshots (including pre-race known-on timestamps), complete official race-result observations (including result-known timestamps, course, jockey, trainer, surface and distance) and a parent-master table with separately timed parent-ID availability.

For every potential historical training race, it verifies complete 1..N classified finishers, one registered H: horse ID per entry, matching date/venue/surface/distance, published results after the start, a source-known parent ID record before the entry, and no post-cutoff records in the candidate predictors. Nonfinishers, gaps, ties, unreported race participants or inconsistent source IDs are **excluded as entire target races**, not given fictitious ranks or silently treated as random negative labels.

The trainer uses the exact PR #51 point-in-time feature function — identical fields in the actual forecast pipeline:

| Model | Features |
|---|---|
| M0 | Fixed normalized finish-rank midpoint 0.5 (no fitting) |
| M1 | 18 pretarget own performance, recency, current race context, age/sex and previously published course/jockey/trainer outcome features |
| M2 | All 18 M1 fields + 4 recorded shared-sire/dam *other-horse* history and relative-count fields |

The sire/dam history excludes the focal horse, uses within-surface and distance-bin peer average, and weights each other horse once per bin. An unknown parent is not treated as a common ancestral label. The trainer computes the **same scaler for every shared M1/M2 field**, so merely adding relatives does not change the standardization of the 18 ordinary features.

It fits a horse-equal-weighted linear ridge model with a **fixed alpha=100** and an unpenalized intercept; alpha and feature definitions are **not optimized using 2025–26 validation labels**. Both private coefficient sets are compatible with the PR #51 schema.

## Frozen temporal roles

| Time period | Use |
|---|---|
| 2018-01-01 to 2024-12-31 (JST) | Train coefficients; each entry uses only older result-known timestamps |
| 2025-01-01 through the actual time model is frozen, within 2026 | Historical temporal validation only; cannot re-optimize hyperparameters |
| 2027-01-01 through 2027-06-30 | **Future unseen evaluation target**, only after actual outcomes exist; NOT currently scored |

The code enforces **≥100 complete training starts from ≥30 horses and ≥30 days**, plus **≥50 complete validation starts from ≥20 horses and ≥15 dates**. Unmet support raises a HOLD. Public output includes the training/validation coverage, horse-equal-weight RMSE for M0/M1/M2 and separate one-way 399-draw horse and race-day cluster sensitivity *for the historical validation*, but no horse- or race-level records.

The fitted model JSON is **private**, with both coefficient vectors, means, standard deviations, training-through timestamp, and actual model-frozen timestamp. Its SHA256 is included in the public aggregate QA record and is the **same model file SHA** that the 2027 forecast commitment must use, creating a verifiable chain. That does **not** itself prove a future forecast was recorded before the race; the commitment must be independently timestamped **before the first start**.

## Synthetic tests verified (not real JRA findings)

[Successful 2026-11-18 GitHub Actions #44224429954](https://github.com/zuizui0223/keiba/actions/runs/44224429954), source commit 80f718663be773eac684e297502bd1cce9d356f7, uses entirely fictional IDs and race records. The fixed test generator constructs 40 training calendar days, 20 validation days, 42 fictional horse identities, and six horses per race.

Tests passed: **19 new historical model-training tests** + **24 pre-race forecast commitment/scorer tests** + **12 source-known-on and registration-ID tests** = **55 synthetic tests**. They cover complete race matching, parent-ID namespace conflicts, missing/late pedigree sources, duplication, future result-publication timestamps, chronological train vs validation split, exact M1/M2 common scalers, validation-label perturbation leaving training coefficients unchanged, private model digest and actual end-to-end software compatibility with the forecast-and-score ledger.

**None** of the fictional test results represents a horse's actual performance, genetic predictor value, an existing licensed dataset, or a 2027 forecast.

## Private execution, when permissions and data actually exist

Do not upload the source or fitted private model to public GitHub. These are illustrative command paths, not existing files:

~~~bash
python scripts/ecology_japan_2027_official_historical_train.py \
  --historical-entries /private/jra_official_historical_entries.csv \
  --historical-results /private/jra_official_historical_results.csv \
  --parent-master /private/authorized_parent_master.csv \
  --private-model-out /private/frozen_M1_M2_2027_model.json \
  --public-summary-out /private/M1_M2_historical_aggregate_qa.json
~~~

The input schemas match [the prior public contract](JAPAN_2027_POINT_IN_TIME_LEDGER.md), except that historical results additionally require source-certified turf/dirt, distance, venue, jockey and trainer IDs. Note that 2025–26 are historical validation periods, **not an independent 2027 test**.

Use the SHA256 of the resulting private model in PR #51's **freeze** command's public commitment, then store the individually predicted races **outside Git**. When results become available, run its **score** command on exactly those frozen predicted horses and races. For independent timing proof, publish the *aggregate commitment* through a time-audited public Git commit **before the race**. A SHA and a manually typed timestamp alone do not prove when predictions were made.

## Evidence classification / blockers

**Implemented:** model fitting with known-on filtering, chronological validation, common M1/M2 scaling, private coefficient hash, end-to-end future ledger software compatibility; all verified on synthetic input.

**Not performed / HOLD:** licensing and obtaining real JRA-VAN race and blood-registration parent data, training actual M1/M2 coefficients, externally confirming official source publication times, predicting any actual 2027 race, obtaining a full JRA+NAR pedigree relationship matrix A or ID-linked genomic G, and demonstrating heritability, genetics or betting returns. No authorized JRA-VAN / NAR credentials are embedded or requested by the source code, and no source or model rows are redistributed.

[Predeclared software contract](JAPAN_2027_OFFICIAL_HISTORY_FIT_PROTOCOL.md) · [synthetic-only provenance](../evidence/japan-2027-model-fit-synthetic-qa-20261118.json).
