# Exact field decomposition: mean-rank coherence, not established opponent-shape gain

26 November 2026. [Protocol](JAPAN_FIELD_COHERENCE_DECOMPOSITION_PROTOCOL_20261126.md) · [successful source run](https://github.com/zuizui0223/keiba/actions/runs/45779380969) · [aggregate log receipt](../evidence/japan-field-coherence-decomposition-20261126.json).

All PR103 calibration grids, parameters, year and pooled RMSEs reproduced to 1e-10. Pooled 89,473 starts / 16,076 horses / 6,459 classified races. Arithmetic controls C and E are not calibrated probabilities. Exact decompositions passed.

| Model/weight | Closure | Guaranteed mean-bias term | Weighting cross term | Center to bounded linear | Linear to matched energy | Equal-energy shape | Raw-to-pair total |
|---|---:|---:|---:|---:|---:|---:|---:|
| own/race_equal | 0.004695995 | 0.004695995 | 0.000000000 | 0.000001106 | 0.000091553 | 0.000004494 | 0.004793147 |
| own/horse_equal | -0.002190256 | 0.005133484 | -0.007323740 | 0.000001100 | 0.000076608 | 0.000007920 | -0.002104628 |
| kin/race_equal | 0.004899171 | 0.004899171 | -0.000000000 | 0.000001947 | 0.000083405 | 0.000006522 | 0.004991046 |
| kin/horse_equal | -0.001828024 | 0.005294504 | -0.007122528 | 0.000001904 | 0.000066183 | 0.000005440 | -0.001754497 |

The no-kin equal-race closure is 0.004695995, about 98% of the raw-to-pair improvement. With the pairwise prediction energy matched, shape gain is 0.000004494, conditional 97.5% day interval [-0.000006933,0.000016022] and horse-axis interval [-0.000008499,0.000018395]. Kin shape likewise uncertain. Thus the earlier small nonlinear improvement mostly reflects changes in prediction energy, not an established gain from shape of the opponent-score distribution. The horse-equal weighting cross term is -0.007323740 (conditional horse-axis interval [-0.007860695,-0.006777507]) and reverses the positive mean-bias term. These are exact loss-accounting identities on the same observed scores, not causal participation effects. Centered unbounded diagnostics exceed [0,1] in 9/11 no-kin/kin rows; equal-energy diagnostics exceed in zero rows. Conditional single-axis intervals omit cross-cluster and fitting uncertainty. Preserve PR103's original evidence but narrow interpretation. PR104 remains adverse for fixed dyad residual correction. PR106 separately investigates a historical opponent-network common ability scale with first-meeting one-win comparisons. No raw data redistribution, no main merge.

Provenance: head 7a2b3b2a4d33a345b0abc2ae40849a5fd8843f2b; artifact 15097158538; sha256:921bf1cfb0d03509cf83c3309b96f63c0034240981b564b3f594f83eb18bcd67; metadata and upload-log parity, ZIP bytes not independently extracted.
