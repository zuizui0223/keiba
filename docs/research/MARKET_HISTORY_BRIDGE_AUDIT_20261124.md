# Market–individual-history bridge: source-clock and identity coverage audit (2026-11-24)

**Status: observed retrospective archive structure; registry identity / prospective history / genomic linkage HOLD.** Research-only extension of PR #76. Source revision `eb37e006d9f5622d3b0158789fd88e5cb40a023a`: all five Kyoto 2026-10-12 R8–R12 original card, history, TFW and wide files (20 pinned Git blobs). No race outcomes, payouts or stakes were used.

| Race | Horse rows | Complete pairs | Source update gap (min) | Unweighted node R² (in-sample) | Unambiguous candidate token | Conflict / missing |
|---|---:|---:|---:|---:|---:|---:|
| 8 | 11 | 55 | 0 | 0.552869 | 10 | 0 / 1 |
| 9 | 12 | 66 | 1 | 0.664882 | 11 | 1 / 0 |
| 10 | 10 | 45 | 0 | 0.760634 | 9 | 0 / 1 |
| 11 | 18 | 153 | 1 | 0.648332 | 18 | 0 / 0 |
| 12 | 16 | 120 | 0 | 0.546475 | 14 | 0 / 2 |

The exact source-update-minute subset (R8/R10/R12) has 37 horse rows, 220 pairs and race-mean in-sample R² **0.619993**. The one-minute subset (R9/R11) has 30 horse rows, 219 pairs and mean **0.656607**. This alignment sensitivity uses already inspected data (R8 uses the earlier 13:26 source pair), not a new independent date. The unweighted additive projection is not numerically interchangeable with earlier weighted or edge-holdout R². These descriptive 3/2 groups do not estimate a clock effect; a mismatch in stored update minutes is not required for additive structure.

All **67/67** original card rows match market TFW rows by race-local number and NFKC normalized name. All 67 history keys match the card number set, but the history source has no independent horse-name field. 66 rows have 198 listed runs in total, all dated before target day; one has no listed prior run. All latest dates agree with the maximum listed date (or null). History-check timestamps are Oct 13, **after** the races; six rows have career-count reconciliation notes. Zero independently verified pre-race history captures. Historical event dates are not publication or capture timestamps.

Original card Yahoo candidate coverage remains 30/67. Adding recognized individual horse URLs in history rows yields **62/67** unambiguous ten-digit token candidates; 29 have concordant original-card and history tokens, 28 show the same token under at least two distinct provider labels. **One R9 row has conflicting history tokens from JBIS and Yahoo, with no card candidate; four rows lack recognized tokens.** No majority-vote resolution, registry-ID promotion, or raw names/IDs output. The 62 unambiguous tokens are distinct in this cohort. Provider labels can reuse common underlying data, and URLs are not independently verified pages.

## Research implications and gates

This establishes a retrospective race-local linkage path, not a measured effect of individual history on market prices. Validate candidate identities via authorized sources and as-of captures; retain the intended 67-row denominator, the one conflict and four missing cases. Then test whether own-history recency and pedigree explain collective evaluation beyond shared race/condition effects. This dataset cannot test transfer across repeated horses or dates, social contagion, heritable behavior, selection, or a biological pair interaction. R8 is still the only documented aligned longitudinal contrast.

## Reproduction

The JS core was run on all 20 connector-fetched files and six synthetic URL/projection checks passed. The standalone Node replay checks input Git blob hashes, roster/name matching, source clock, complete pair sets, chronology, candidate conflicts, and exact saved row metrics. It can be run from the root with `node scripts/ecology_market_history_bridge_audit.mjs`. **Separate repository CI has not been verified.**

[Aggregate JSON](../evidence/market-history-bridge-audit-20261124.json) · [Replay code](../../scripts/ecology_market_history_bridge_audit.mjs).
