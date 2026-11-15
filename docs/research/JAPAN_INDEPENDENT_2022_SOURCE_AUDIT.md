# Japan horse pedigree forecasting: independent 2022+ source feasibility (2026-11-15)

**Status: no independently confirmed 2022+ predictive gain yet. Original 2019–2021 results are retrospective and remained unchanged.**

## Tested source 1: public JRA HTML-derived CSV without stable horse ID

Source: https://github.com/whitedogk/jra-condition-app

The repository README describes a wider 2016–2026 source, but the **actual CSV fetched during the audit** has SHA256 `ca14ff253018433e8e14bc583628f85ca909195d5e4edb42c6d1e2ade939ba6f`, **141,394 raw rows** and only years **2023, 2024, 2025, early 2026**. After explicit surface/distance/rank filtering, 137,808 source rows are eligible, and 119,602 rows are from 2023–2025.

The original Kaggle archive is SHA256 `c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f`. Original course/surface scope normalization gives **568,030** JRA source rows. A material parser defect was identified and fixed: distances were like `1600M`, not simply `1600`; the original initial zero eligible rows was a *parser error*, not evidence of no Japanese races. Eight source tests now cover this format. Names in the old archive are not canonical horse keys: **353 normalized horse-name labels map to multiple distinct old IDs**.

Since the new file's oldest year is **2023**, it contains **no 2016–2021 race outcomes**. It therefore cannot provide even one of the pre-2022 multi-event identity anchors needed to join a public name to an original pedigree ID. The 2022+ new records are **not** asserted to be genetically unrelated, and this absence must not be scored as predictive failure.

Evidence: https://github.com/zuizui0223/keiba/actions/runs/43690473932

## Tested source 2: long-running SQLite horse and race records

Source: https://huggingface.co/datasets/KBlueLeaf/jp-racing-horse

A real SQLite file with SHA256 `7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9` was downloaded transiently. It contains **236,232 horse rows**, **450,648 race rows**, dates **1990-01-05 through 2025-03-27**, and **51,835 race rows with years 2022–2025 inclusive**. Table schemas contain `horse.hid,name,races` and `race.rid,date,horses,place_id,distance`. Its source-level license label is Apache-2.0, but the *underlying racing records' reproduction rights are not independently audited*.

**Zero direct stable horse-ID matches** were found against the 91,255 original archive horse IDs with parseable race histories. This is evidence that the two public sources use distinct identifier namespaces; it is **NOT evidence of no shared real horses or no family structure**. No assumption that a numeric ID in one source equals a numeric ID in another is allowed.

Evidence: https://github.com/zuizui0223/keiba/actions/runs/43690611020

### Next strict check

Use **only pre-2022 results** from the source SQLite horse-specific race history to corroborate a candidate exact normalized name with at least **two independent race dates agreeing in date × distance × classified finish position**. Reject any normalized name mapped to multiple IDs in either source. Count later-year races only *after* this corroboration; no 2022+ outcome is used for identity or model selection. The source is heterogeneous and claims no official studbook ID; even two-event corroboration is evidence of an identity match, not a canonical ID certificate.

Only if an adequate anchored cohort exists may the frozen 2010–2021 pedigree/behavior histories be scored on *2022–2024* outcomes from an independent source, with **2025 partial through March 27** explicitly separate. Need actual two-source event coverage, age/sex/class/track/venue mapping, actual complete rank denominators and transparent unmatched-horse selection. Do not claim full Japanese coverage or prospective wagering validity.

## Ownership, limitations and research interpretation

- Every third-party raw file remains temporary and is not committed/uploaded; only aggregate evidence, code and source hashes are persisted.
- Source rights: old Kaggle redistribution licence **Unknown**; third-party JRA CSV licence **unverified**; HF dataset declares Apache-2.0 but its upstream racing rights remain unverified.
- Previous PR45: new contextual baseline showed source-conditional RMSE 0.304532 and +kin 0.303338 on 2019–2021. That is an already-inspected test window and **not an independent 2022+ validation**.
- A parent-ID or sire-history feature is not a multigeneration genomic relationship matrix, inherited causal effect, measured heritability, or betting advantage.

If the new source cannot pass exact identity and timing checks, keep **HOLD** and preserve the earlier retrospective claim at its actual evidence level. Do not relax matching solely because it produces more horses.
