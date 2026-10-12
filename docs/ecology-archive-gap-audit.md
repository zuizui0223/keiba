# 2026-10-12 Kyoto archive: ecological identifiability audit

Status: **HOLD** — descriptive research-input audit, not an ecological hypothesis test.

## What is actually archived?

Source: the independently maintained `analysis/kyoto-20261012` branch
([README](https://github.com/zuizui0223/keiba/blob/analysis/kyoto-20261012/README.md),
[analysis design](https://github.com/zuizui0223/keiba/blob/analysis/kyoto-20261012/docs/analysis-design.md),
[seven race inputs](https://github.com/zuizui0223/keiba/tree/analysis/kyoto-20261012/data/2026-10-12)).

- Race scope: Kyoto 2026-10-12, 6–12R (7 races).
- Race-day roster records: 95 starters in seven separate `kyoto_06.json`–`kyoto_12.json` files.
- Race-level attributes currently recorded in those inputs: venue, race ID, start date/time, turf/dirt, distance, class. Horse entries include win odds, aggregate Kyoto finish counts and narrative historical evidence.
- This is a **single-day roster snapshot**, not a longitudinal table of the horses' own past starts. Postrace results exist in some other files but are not a complete horse×historical-start panel with ground condition, official individual times, pre-race running-style history and source permission.
- Prior Kyoto record arrays contain [1st, 2nd, 3rd, other] counts. Those counts cannot be inverted into the race-level exposures or contextual opponents needed for H1/H2.

## Explicit status table

| Measurement or test | Archive state | Decision |
| --- | --- | --- |
| Number of date-stamped race cards | 1 calendar day / 7 races | Insufficient for individual reaction norms |
| Horse identifiers consistently joining years and venues | Not supplied as normalized `horse_id` in the present roster JSON structure | Need authoritative historical identifiers |
| Repeated individual race starts with paired going and full timing | Not available as one-longitudinal-record-per-start | **H1 HOLD**: slope variation unidentifiable |
| Repeated *different* rival compositions for the same horse, with prior-race running style | Not available as a pre-race historical panel | **H2 HOLD**: rival-context interaction unidentifiable |
| Historical JRA performance vs betting odds distinction | Odds and aggregate records exist, but odds are not horse speed | No ecological effect can be inferred from win-market snapshots |
| Permissions for distributing raw multi-year records | Not established | No licensed-source bulk upload to a public repo |

**Interpretation:** There are zero *usable repeated-exposure measurements in the supplied structured archive*, not evidence that horses lack environment-dependent performance. Likewise, model-level fit/calibration or wager success on 2026-10-12 is not evidence for or against H1/H2.

## Progress on the computational side

The research branch now provides:
- a schema and a clock/source/roster-aware data auditor;
- strictly historical features for each horse and leave-one-out rivals;
- a diagnostic for repeated *within-horse variation* in opponent composition;
- an exploratory H1 random-intercept vs within-horse random-slope fitting pipeline with strictly time-forward evaluation;
- entirely fictional test records, with explicit no-empirical-claim safeguards.

This establishes technical feasibility on fabricated records only. The pilot H1 model is not yet a properly adjusted crossed-effects confirmatory model. Rights, repeated-start data, class/jockey history, racing condition and entry-selection adjustment remain essential.

## Next empirical milestone

1. Confirm data access rights **for a published scientific study**, including whether aggregate tables/figures and reproduction materials may be released.
2. Acquire authorized multi-year `horse_id × race_id` start records, including official finish times, race-level going, pre-race jockey/class, prior first-call position and timing/provenance. Do not pretend cross-race historical summaries are individual starts.
3. Run the audit, inspect cross-going overlap *within class, surface and venue*, and diagnose opponent composition changes within horses before fitting.
4. Use a simulation-based design-power analysis rather than interpreting the current engineering readiness threshold as a statistical sample-size justification.
5. After fitting, distinguish observational conditional performance from evolved adaptation, causal competition, heritability and animal personality.

### Prior benchmark and rights

Oda & Onogi (2024), *Journal of Animal Breeding and Genetics*, https://doi.org/10.1111/jbg.12822, already modelled Japanese Thoroughbred racing performance with mixed effects and race/age/jockey adjustments. This is why the new H1/H2 effects must be quantitatively compared against a serious baseline.

JRA-VAN Article 7: https://jra-van.jp/info/rule.html.
JRA-VAN developer notice (2026-07-06): https://developer.jra-van.jp/t/topic/899.
