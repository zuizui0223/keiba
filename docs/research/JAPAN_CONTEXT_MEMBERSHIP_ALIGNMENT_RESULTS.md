# Direct-source membership alignment: complete parity, inference HOLD

2026-11-26 JST. [Frozen protocol](JAPAN_CONTEXT_MEMBERSHIP_ALIGNMENT_PROTOCOL.md) · [successful source run](https://github.com/zuizui0223/keiba/actions/runs/45657243849) · [aggregate receipt](../evidence/japan-context-membership-alignment-20261126.json).

Source commit 0c438df5526fa7e5f540ff8d87a31ef010da44c3; synthetic, source hashes, venue, strict race/horse/rank denominators and common 527/115 sire gates passed. Direct group moments, Shapley components, annual/common H agree with all 18 reconstructed zero-vs-positive seed/year/profile conditions. This validates the aggregate recovery against the same underlying source records, not independent empirical replication. Artifact 15044466165, sha256:17f80147ef2e3829a5ed9b96a9c5ddcb03a29d5598e84d81c38084ec0642781d; metadata checked, full ZIP not independently extracted.

## Frozen support gates

Both partitions, all seeds/profiles: **HOLD_LOW_CELL_SUPPORT**. The rule requires at least 100 horses and 30 sires in every annual × membership × pre-2022 history cell, including 2024, and was frozen before the direct calculation. No intervals were computed.

| Partition | Year | Common low (horses/sires) | Common high | Complement low | Complement high |
|---|---:|---:|---:|---:|---:|
| zero_vs_positive | 2022 | 54/37 | 473/109 | 280/91 | 2204/189 |
| zero_vs_positive | 2023 | 54/37 | 473/109 | 120/65 | 941/144 |
| zero_vs_positive | 2024 | 54/37 | 473/109 | 46/36 | 170/69 |
| 0_to_3_vs_4_plus | 2022 | 288/83 | 239/84 | 1286/149 | 1198/162 |
| 0_to_3_vs_4_plus | 2023 | 288/83 | 239/84 | 530/121 | 531/121 |
| 0_to_3_vs_4_plus | 2024 | 288/83 | 239/84 | 146/64 | 70/41 |

The primary low-history common group has 54 horses. For the alternate 0–3 vs ≥4 partition all 2022 and 2023 cells meet the stated thresholds, but the 2024 high-history complement has only 70 horses. This is the reason all six alternate-partition conditions also HOLD. The frozen gate is not retrospectively relaxed.

## Point estimates only

H is the additional sample-optimal two-stratum scalar gain beyond the pooled sample-optimal scalar, with outcome-dependent weights. Total discrepancy = (annual H2023−H2022)−(common H2023−H2022). Alignment component change is the 2023−2022 difference in the Shapley A/E contribution to annual-minus-common H. The 2023 four-cell contrast is (complement low r−common low r)−(complement high r−common high r), with r=A/E. It is not an estimated causal interaction or a correlation.

| Seed | Partition | Profile | Total discrepancy | Alignment component change | Four-cell contrast 2023 | Status |
|---|---|---|---:|---:|---:|---|
| 20261124 | zero_vs_positive | fixed | 0.000990846 | 0.001008012 | 0.414225465 | HOLD |
| 20261124 | zero_vs_positive | refreshed | 0.000952361 | 0.000943672 | 0.437692637 | HOLD |
| 20261124 | 0_to_3_vs_4_plus | fixed | 0.001613185 | 0.001584744 | 0.207094591 | HOLD |
| 20261124 | 0_to_3_vs_4_plus | refreshed | 0.001771838 | 0.001730916 | 0.246473928 | HOLD |
| 20261125 | zero_vs_positive | fixed | 0.001147988 | 0.001168828 | 0.533888966 | HOLD |
| 20261125 | zero_vs_positive | refreshed | 0.001106979 | 0.001122105 | 0.589424348 | HOLD |
| 20261125 | 0_to_3_vs_4_plus | fixed | 0.001868782 | 0.001835568 | 0.164628450 | HOLD |
| 20261125 | 0_to_3_vs_4_plus | refreshed | 0.001925854 | 0.001885229 | 0.172241120 | HOLD |
| 20261126 | zero_vs_positive | fixed | 0.000979142 | 0.001008577 | 0.399275042 | HOLD |
| 20261126 | zero_vs_positive | refreshed | 0.000914849 | 0.000927826 | 0.408736633 | HOLD |
| 20261126 | 0_to_3_vs_4_plus | fixed | 0.001057075 | 0.001042833 | 0.191645806 | HOLD |
| 20261126 | 0_to_3_vs_4_plus | refreshed | 0.001133631 | 0.001109007 | 0.210003297 | HOLD |

All 12 point estimates for each of the three quantities are positive, but shared data/splits are not independent replicates. Primary fixed: total 0.000990846, alignment 0.001008012, four-cell 0.414225465. Refreshed primary split also reproduces the earlier descriptive 99.1% signed alignment component of the total change discrepancy. These are arithmetic contributions, not causal explanation fractions.

No confidence intervals or joint-positive conclusion for this study. Any shorter-window analysis after inspecting these support counts would be explicitly post-hoc and separate from this frozen primary; it cannot replace this HOLD. No new sources, registered population census, genetic effect, biological survival, causal selection or animal learning established. Keep the already supported fixed-correction own-update effect from PR88 as the manuscript's primary empirical result.
