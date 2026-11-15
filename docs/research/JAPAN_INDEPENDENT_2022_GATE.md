# 2022–2025 independent JRA source gate (2026-11-15)

**Goal:** After the earlier 2019–2021 retrospective family-history results, determine whether there is a defensible *untouched later period* with original horse IDs linked to an independently collected results source.

## Two inputs with different identity systems

1. Historic Kaggle archive `ayuser/horse-racing-in-japan`: 2010–2021, SHA256 `c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f`, has horse/parent identifiers and outcomes. Original redistribution license: **Unknown**.
2. `whitedogk/jra-condition-app` repository's public `jra-results-actual.csv`: source-described as JRA official HTML-derived 2016–2026, nearly half a million runner rows. It records horse **name** but no canonical horse ID or sire/dam ID. The published CSV has no independently verified redistribution license or coverage guarantee. [Source repository](https://github.com/whitedogk/jra-condition-app).

A race/result/name match is evidence about identity, not an official studbook crosswalk. **Do not infer genetic relationship from a name or a naming prefix.** Do not publish or merge raw source files into this repository.

## Strict pre-2022 identity anchors, without future-label leakage

Normalize only unambiguous ten JRA venue names (English and Japanese), turf/dirt, date, race number and integer distance; horse names use Unicode NFKC plus casefold, but **no fuzzy character-distance match**. The join key includes **race date × venue × race number × surface × distance × finish rank × exact normalized horse name**. A horse's old stable ID can be assigned to a newer source name only if:

- At least **two** matched race results on **different calendar dates in 2016–2021**;
- Both old name→ID and ID→name are unique throughout the old record; conflicts quarantined;
- Source-duplicate rows are counted but cannot create extra anchors;
- No source event, finishing position or result dated 2022 or later contributes to identifying an old horse.

Future eligible rows for **2022–2025** are reported separately. Names with fewer than two anchors are **UNKNOWN**, not a different horse or unobserved genetic relative. The source CSV may also include 2026, which is explicitly excluded.

Predeclared feasibility gate: **at least 100 two-event crosswalk horses and 100 eligible later rows** before declaring there are enough anchors to attempt a later-year model. Failing the threshold is **HOLD**, not a null genetic effect. Every source version is recorded by SHA256; never silently mix versions.

## Conditional next analysis, only if source gate passes

Use **only old-source pre-2022 history** to fit an age/sex/distance/course/surface and own-history baseline. Frozen pre-2022 parent relationships supply a second model with other known same-parent horses' earlier history, focal excluded. Train-and-freeze coefficients on pre-2022 races; apply without modifying them to the anchored **2022–2025** subset. This may be *out-of-source and out-of-period* but only for **surviving older horses with anchored past starts**, not current-year debutants or all Japan horses. Race-class, trainer and jockey feature families absent or incompatible between sources must be omitted or held as missing, **never assumed equivalent by name**. Compare models on the same classified-rank rows with full-race denominators; report year-by-year coverage, cohort selection, RMSE, baseline and negative controls.

No 2022+ outcomes are inspected to choose identity thresholds, model coefficients or model hyperparameters. If source schema and race overlap are insufficient, preserve the outcome data unused; do not retune the join based on future ranks.

## Evidence status

- Original 2019–2021 family-history benchmark is [PR #45](https://github.com/zuizui0223/keiba/pull/45), **not a 2022–2025 replication**.
- Current work first provides source feasibility counts and exact-ID anchor tests. Successful workflow execution does **not** itself prove an independent predictive gain.
- Studbook pedigree A, genomic G, hereditary/causal effects, present-day betting and nationwide JRA+NAR coverage are not established.

Raw third-party race rows stay transient on a private CI runner; only aggregate source audit JSON is stored with GitHub Actions.
