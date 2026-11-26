# Roe deer SPEED endpoint: useful genomic information substitution not established

26 November 2026. [Frozen protocol](ROE_DEER_SPEED_SUBSTITUTION_PROTOCOL_20261126.md) · [successful source run](https://github.com/zuizui0223/keiba/actions/runs/45759333457) · [aggregate log receipt](../evidence/roe-deer-speed-substitution-20261126.json).

All source file hashes match the 2020 release; 1,856 valid records, 205 deer, 1,848 distinct candidate cells (8 duplicate rows collapsed), 183 eligible deer. Identical POH-model parameters, no outcome retuning, untransformed recorded SPEED units. Source archive bytes differ, file content parity passed. The fixed genomic correction has positive zero-depth point gain and a negative 3−0 contrast in all three shared-data splits, but all three gain-0 conditional 97.5% intervals include zero, and the primary contrast interval also includes zero. The predeclared directional joint criterion is not met. **HOLD useful substitution on SPEED.**

All MSE differences below are in recorded SPEED squared units × 10^6.

| Seed | Gain 0 | Gain 1 | Gain 3 | Change 3−0 | 97.5% conditional gain 0 | 97.5% conditional change | label tail gain / change |
|---|---:|---:|---:|---:|---|---|---|
| 20261124 | 80.619 | 79.605 | 54.154 | -26.465 | [-112.681, 321.384] | [-113.146, 43.489] | 0.1 / 0.24 |
| 20261125 | 4.992 | -42.994 | -93.346 | -98.337 | [-203.300, 192.632] | [-195.837, -17.533] | 0.24 / 0.005 |
| 20261126 | 60.854 | 30.469 | -17.673 | -78.527 | [-126.229, 271.794] | [-142.722, -14.848] | 0.11 / 0.015 |

Primary RMSE without/with genome: 0.085397/0.084924, 0.083515/0.083037, 0.082544/0.082215 at depths 0/1/3. The negative increment at depth 3 in the two sensitivity splits is retained. Conditional intervals do not include all genomic, spatial, donor-fit or cross-fold dependence; label-exchangeability is unestablished. No causal genetic inference, chronology, independent population, or formal contrast of trait effects. The POH result remains the positive independent-species analogue of the horse result; SPEED is an uncertain boundary, not a second replication. Different endpoint membership, masks, units and baseline signal preclude direct raw-MSE contrast. Next test POH sensitivity to recorded road distance (potentially concurrent; not a causal environmental control), then an exact shared-individual/period trait comparison only if adequate support. No raw data redistributed.

Provenance: source head 5a584eb28e6c29af4547b19b7f212a24ff644c29; artifact 15088604725; sha256:30813b36373250775bbde28de490ef62ede5ec9f17fbbc233b1f3ca249c7b04d; metadata and upload-log parity, not independent ZIP extraction. The run's successful status is a computational result, not scientific acceptance.
