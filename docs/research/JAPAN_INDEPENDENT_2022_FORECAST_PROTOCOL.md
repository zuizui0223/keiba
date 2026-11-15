# Independent 2022–2024 test of family-history race-rank prediction

**Freeze date:** 2026-11-15. **Scientific status:** out-of-period and second dataset/collection, but both archives may originate from overlapping upstream race-result websites. NOT a fresh prospectively measured official JRA/NAR cohort, genomic heritability or bettor profitability.

## Inputs and provenance

- Source A: ayuser/horse-racing-in-japan 2010–2021 archived ZIP SHA256 `c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f`. Source contains horse IDs, sire IDs, dam IDs and classified finish ranks. Original data redistribution licence **unknown**.
- Source B: Hugging Face KBlueLeaf/jp-racing-horse SQLite SHA256 `7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9`. Source's metadata labels Apache-2.0, underlying racing-content rights not independently confirmed. Horse history has **17 fields, not the 18 in current db.py documentation**; the full race calendar date is in **Race.rid→Race.date**, not at `Horse.races[17]`. This was diagnosed on 500 aggregate source rows; never silently impute a date from the 17th element (which is final sectional timing).

### Historical identity bridge

Exact Unicode NFKC+casefold name, with both source-side name→ID and ID→name uniqueness, plus **at least two distinct PRE-2022 race calendar dates** agreeing in **date, finishing rank and distance**. These are *independent matching events*, not a mere name match. 2022+ source results are never used to select matches.

Actual source gate: https://github.com/zuizui0223/keiba/actions/runs/43691860626

Identified 20,400 candidate cross-source horse pairs based on ≥2 separate historical matching dates; 23,014 have ≥1 matching earlier date. Candidates have 262,343 archived 2022–2025 source horse-history rows, distributed as 2022=126,040, 2023=84,775, 2024=44,690, 2025=6,838. These are *raw history counts*, before outcome eligibility filtering. 2025 source coverage ends 2025-03-27.

Not a canonical official studbook crosswalk, and cannot identify newly debuting 2022+ horses with no pre-2022 records. Excludes ambiguous labels; 5,531 new-source name labels map to multiple HF horse IDs, 875 old-source labels map to multiple original horse IDs. No fuzzy or genetic name matching.

## Model frozen before inspecting future outcomes

Only 2010–2021 original source is used for features and model training:
- Form annual training features for 2018, 2019, 2020, 2021; each target-year row uses horse and other horse histories dated before January 1 of its own year.
- Common baseline uses focal horse historical normalized mean and number of starts, same-surface/distance-bin historical mean and count, last 1 and 3 classified ranks, current turf/dirt and distance.
- Add source-A sire and dam ID shared other-horse histories as two additional numeric predictors. Each other horse contributes one mean residual per course-surface distance bin; focal excluded. Feature regression penalty `alpha=100` fixed for both models (equal-horse-weighted ridge).
- No current 2022+ outcome/label used to fit, tune or select predictors or normalize training input. The 2022–2024 outcomes are first read only for scoring. 2025 is partial and scored separately, excluded from primary 2022–24 pooled.
- Target normalized rank=(classified rank−1)/(declared field−1) on the independent source, using its `Horse.races[7]` declared horse count. The old source's normalized rank uses *classified finishers only*, so the two outcome measures are imperfectly aligned; report the discrepancy.
- Only source-invariant compatible features are included. HF race entry has no source-aligned historical trainer/jockey/race-class IDs; those richer features are not smuggled or guessed by string matching. Therefore compare within THIS portable family of two models, not as if it was PR45's identical rich model.
- Report middle-position 0.5 predictor, no-kin baseline, and +direct-family history on *identical held-out eligible rows*, 2022/2023/2024 independently, primary 2022–24 pooled, and partial 2025 only as separate exploratory check.
- Separate single-way bootstrap sensitivity groups: horse identity and race calendar day (not joint multiway or causal intervals). No cherry-picked named-family or course post-strata in first result.

## Required QA and HOLD gates

1. Source SHA and immutable original-ID mapping; archived parent ID uniqueness.
2. HF `race.rid` is unique, `Horse.races` events are linked via same `rid`. Reject distance/surface conflict against Race source table, rank/field outside valid bounds, missing dates and duplicates `(source race ID, source horse ID)`.
3. Preserve original named horse data in ephemeral runner only; no source individual rows, names or IDs in public artifact.
4. Do not label ranking prediction as a winning probability, GPS trajectory, animal-model additive genetic A/G, genotype-specific inheritance, or causal influence.
5. If too few qualifying anchors or target rows, explicitly HOLD. No lowering the two-event threshold to force results.
6. If source rights, date formats, or measured outcome-grain mismatch are unresolved, state them alongside any score.

Code: `scripts/ecology_japan_2022_independent_forward.py`. Tests: `tests/test_ecology_japan_2022_independent_forward.py`. Do not merge to production or change existing 2019–21 results pending independent source quality checks.
