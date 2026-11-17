# 2026 own-history vs family-history freshness: four-condition factorial audit

**Design date 2026-11-17; fully POST-HOC.** This experiment was specified after inspecting both the negative original 2026 outcome and the favorable update of own racing history in PR #49. It is a diagnostic decomposition, not a preregistered test, new holdout, estimate of genetic causality, or evidence of wagering profit.

## Scientific question

The previously observed source-C 2026 cohort (232 horses, 480 starts, 259 races, 42 dates through 2026-05-17) gave:

- 2021-frozen ordinary no-family RMSE **0.3196817723**, +direct-family RMSE **0.3203016064**.
- Prior-calendar-day updated ordinary no-family **0.2747824094**, +family **0.2764268977**.
- 2021-frozen stronger own-history no-family **0.3215185306**, +family **0.3180747502**.
- Prior-day updated stronger own-history no-family **0.2747056231**, +family **0.2744225871**.

The huge change could come from the focal horse's own racing information, the relatives' racing information, or their interaction. The previous work updated BOTH feature families simultaneously. Here we vary them independently, **holding the old source-A fitted ridge coefficients unchanged**.

## Four immutable conditions and prediction targets

| Code | Focal horse own-history features | Recorded same-sire/same-dam OTHER-horse features |
|---|---|---|
| **SS** | Source A records to 2021 | Source A records to 2021 |
| **FS** | Source A + source C up to **day before** focal 2026 target | Source A to 2021 |
| **SF** | Source A to 2021 | Source A + source C up to **day before** focal target |
| **FF** | Source A + source C up to **day before** target | Same updated history |

Compute both ordinary portable ridge models and the stronger source-A age/sex/recency-enhanced models, each with original 2018–2021 training and ridge alpha=100. No 2026 labels determine horse identity or training hyperparameters.

**Source SHA locks:** original 2010–21 race/parent archive c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f; 1990–2025/03 intermediate identity SQLite 7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9; 2023–2026/05 public source-C JRA results CSV ca14ff253018433e8e14bc583628f85ca909195d5e4edb42c6d1e2ade939ba6f.

**Identity gate:** 20,400 source A↔B matching candidate horses from ≥2 PRE-2022 race dates, and 1,945 source B↔C candidates with ≥2 2023–2024 matching race dates and exact normalized name. These are **not officially certified studbook IDs**. All 2025 and 2026 result labels are excluded from horse identity decisions. Source C's full-ranked 1..N race results are the only new historical inputs; any result on the target day or later is excluded, even if it was from an earlier race. No verified timestamp to minute resolution is available.

**Model parity hard gates:** reproduce 2021-frozen ordinary and strong 2026 RMSE from PR #48 (tolerance 1e−8), and reproduce both prior-day FF 2026 RMSE from PR #49 (tolerance 1e−8). Validate the same fixed 480 target rows/232 horse IDs/259 races/42 dates and 1,945 historic bridge IDs. The focused source-A horse/family subset must preserve every original feature to 1e−10.

## Correct decomposition of kin features

Original additional sibling features use **focal own-start count** attenuation 5/(5+n_own), even though their peer score and peer count are family-history quantities. Blindly copying family features from an updated model into a stale-own model would accidentally mix stale and fresh own information.

To isolate the family signal, take same-sire/same-dam relative mean/count signals from the selected family-history source, and reapply the own-start attenuation corresponding to the selected focal own-history source:

    mixed_kin_signal = family_source_signal * (5 + n_own,family_source) / (5 + n_own,selected_own_source)

The family-relative log counts copy from the chosen family source. All other features, including stronger age/sex/recency and focal own-history fields, copy from the chosen own-history source. SS and FF must reproduce the entire original feature vectors, and both no-family predictions must be identical across family-source choices for the same own-source state.

## Comparisons

Report on **identical 480 target starts**: all four ordinary and strong with-family RMSE, their matched no-family RMSE and fixed midpoint; refreshing own with stale relatives (SS→FS); refreshing relatives with stale own (SS→SF); refreshing relatives with fresh own (FS→FF); and refreshing own with fresh relatives (SF→FF).

Report descriptive RMSE difference-in-differences, **not causal interaction**, and separate one-way 399-draw horse and calendar-day bootstrap intervals for each contrast. Record how many focal starts have genuinely earlier-calendar-day source-C own histories vs other same-parent histories (both / neither). Never treat missing histories as biologically unrelated horses.

A negative updated-family effect must remain visible. These are **post-hoc**, not independent biological replications. Parent identity is confounded by breeding farm, owner, stable, selection, and genes and is not complete pedigree matrix A or genomic G.

## Critical limitations

Race source rank denominators and nonfinisher coverage can differ, and all archives may share upstream JRA records with underlying redistribution rights unverified. Source C has calendar-day rather than certified publication-time information, so the replay is not a live betting-time data feed.

For a defensible prospective result use authorized official JRA horse registration IDs, 2027 actual entrant snapshots and result-known timestamps, and the separately frozen 2027 official-ID rolling protocol. Genetic inheritance, national kinship and odds profits remain HOLD.
