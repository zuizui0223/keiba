# Repeated competition: fixed dyad correction is detrimental

26 November 2026. [Frozen protocol](JAPAN_COMPETITION_DYADS_PROTOCOL_20261126.md) · [successful source run](https://github.com/zuizui0223/keiba/actions/runs/45778143527) · [aggregate receipt](../evidence/japan-competition-dyads-20261126.json).

All archive SHA, prepared source counts, candidate scope, pair orientation, chronological donor and fallback gates passed. Logistic coefficients trained on 2017–18; older same-band/surface history only. Target 2020/21 127,085/123,210 pair observations. N baseline includes individual broad/context ranks, sire context and counts. H adds historical horse residual means; D adds fixed dyad residual mean shrinkage k/(k+3). The primary 2021 comparison of D versus H on supported rematches is adverse, not evidence for useful pair-specific transfer.

| Year / support | Pair observations | Distinct dyads | Race days | H Brier | D Brier | H−D gain | Conditional day 95% interval |
|---|---:|---:|---:|---:|---:|---:|---|
| 2020 / all | 127085 | 120719 | 109 | 0.238599 | 0.239016 | -0.000417 | [-0.000542, -0.000293] |
| 2020 / one_or_more | 3588 | 3056 | 109 | 0.231538 | 0.245803 | -0.014265 | [-0.020090, -0.008764] |
| 2020 / two_or_more | 474 | 372 | 98 | 0.226856 | 0.233170 | -0.006314 | HOLD support |
| 2021 / all | 123210 | 117120 | 106 | 0.239119 | 0.239386 | -0.000267 | [-0.000416, -0.000115] |
| 2021 / one_or_more | 4022 | 3440 | 106 | 0.229670 | 0.238895 | -0.009225 | [-0.014224, -0.004067] |
| 2021 / two_or_more | 724 | 593 | 96 | 0.235237 | 0.249440 | -0.014204 | [-0.026216, -0.002241] |

Only 2.82% (2020) and 3.26% (2021) of target pair observations had at least one same-surface prior meeting in the designated donor years. All six point gains from adding D are negative; five supported day-block intervals exclude zero. The 2020 >=2-meeting subgroup fails the frozen 500-dyad gate. Unclipped differences retain the adverse sign. The correction harms held-out performance under this specific fitted model and selected rematch population. A negative gain can reflect noisy estimates, residual misalignment, or excessive correction magnitude; not proof that competitors do not interact or that there is no pair-specific signal. Day resampling is conditional on fitted predictions and ignores shared horse/kin/management dependence. No genetic, physiological, race tactics, causal or prospective inference. No wagers.

**Next discriminating question:** decompose the unbounded signed increment into 2 E[(Y−H)d] − E[d²], test residual correspondence separately from magnitude, and calibrate one nonnegative weight on 2020 only for a retrospective 2021 transfer sensitivity (2021 has already been inspected; no untouched confirmation). Retain zero or adverse calibration. Preserve the original full-weight primary, do not promote sample-optimal weights.

Provenance: source commit acf6a4d16abf3287db39c2e3946864b9180aa116, run 45778143527, artifact 15097156568, sha256:d9e783da3c1a29032c753ccc9520fd89bc566f2c1455d95cf0c1088b59d0b4e1. Aggregate from completed job log and artifact metadata; no independent ZIP extraction or raw redistribution.
