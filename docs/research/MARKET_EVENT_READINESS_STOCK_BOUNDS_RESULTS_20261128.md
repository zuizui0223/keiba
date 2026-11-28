# Actual publication clock HOLD; conditional continuous stock-growth lower bounds

28 November 2026 JST. [Frozen protocol](MARKET_EVENT_READINESS_STOCK_BOUNDS_PROTOCOL_20261128.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/46113669434) · [aggregate receipt](../evidence/market-event-readiness-stock-bounds-20261128.json).

20 pinned source blobs, full PR126 aggregate parity, event-clock and continuous feasibility tests passed. Explicit structured field and TFW header scan found no body-weight publication fields or total stock fields. Scope is the 20 pinned files, not a claim that no external sources exist. All seven races HOLD_NO_VERIFIED_EVENT_CLOCK. Scheduled post minus 60 minutes is only a nominal diagnostic: one bracket (R8, before 39 min, after 26 min, span 65 min), zero brackets within 10 min each side. Zero actual verified event brackets. No empirical information-arrival effect.

## Conditional partial identification, not observed volume

Assume ordinary single-winner payout factor .8, displayed quote truncation to .1, no exceptional minimum or premium, cancellations/refunds/revisions, stable complete positive roster and nondecreasing accumulated selection mass. Earlier/later share intervals [.8/(o+.1), .8/o] constrained by simplex. Compute infimum g>=1 such that some earlier p and later q satisfy g*q_i>=p_i. This is a continuous closure relaxation, not integer ticket reconstruction or certified intermediate quote convention. The algorithm constructs a feasible continuous witness at g just above its boundary. Point normalized reciprocal proxy ratio is a different estimand.

| Race/interval | Minutes | Conditional lower bound on stock ratio | Minimum fraction of later stock newly accumulated | Point proxy ratio |
|---|---:|---:|---:|---:|
| R7 12:29–13:03 | 34 | 1.319588 | 0.242187 | 1.335722 |
| R8 12:21–13:26 | 65 | 1.216374 | 0.177885 | 1.223767 |
| R8 13:26–13:44 | 18 | 1.401914 | 0.286689 | 1.413676 |
| R9 12:32–13:26 | 54 | 1.124467 | 0.110690 | 1.131780 |
| R10 12:18–13:27 | 69 | 1.161616 | 0.139130 | 1.171547 |
| R11 12:27–13:26 | 59 | 1.075724 | 0.070393 | 1.074389 |
| R12 12:36–13:27 | 51 | 1.081871 | 0.075676 | 1.087385 |

All seven intervals conditionally feasible; stock ratio lower bounds 1.075724–1.401914, not measured stock ratios. In this archive all continuous simplex-constrained bounds coincide with the simpler coordinate lower bounds to 1e-9; do not claim additional tightening from joint constraints here. Numerical tolerances cause tiny (<1.3e-10) differences at closure boundaries. No finite upper bound follows: once feasible, scaling later total mass upwards preserves nondecreasing selection mass. Without true total stock, an interval's aggregate new-arrival composition is not identified. Do not compare these bounds as observed arrival intensity or causal effects. No actual news timing, participant data, independent dates or calibration.

## Acquisition gate

Official JRA-VAN schedule https://jra-van.jp/dlb/ddata.html gives typical timing only. O1 0B41 timestamped quotes and aggregate ticket totals candidate source; staff https://developer.jra-van.jp/t/topic/119 confirms total by ticket type available but intermediate per-selection ticket counts not provided in 0B20. Staff https://developer.jra-van.jp/t/topic/1153 explicitly does not guarantee completeness and gives approximately one-year availability. WH has a published-minute field in unofficial specification reference https://ht-0328.github.io/jvdata-store/reference/WH/ ; confirm against authorized current SDK and capture promptly, do not infer old actual event times from ordinary schedule. Payout rate source https://www.jra.go.jp/faq/pop03/1_17.html?newwindow=true; exceptional cases https://www.jra.go.jp/kouza/plus10/ . No licensed data or actual WH record obtained. Future event study must distinguish provider minute label and local first receipt, exclude same-minute ambiguity and simultaneous updates, retain all missing/failed cases, use independent date blocks and predeclared sham windows. Require authorized exports and research rights; no public raw redistribution. No betting advice, outcome inference, main merge or frozen ledger edits.

Artifact 15251175398, sha256:7f8e79c5b2fd43bd3012b2a66f2c330150e69adaac79d199cbba65576acfd8f1; metadata and upload log match, ZIP bytes not independently extracted.
