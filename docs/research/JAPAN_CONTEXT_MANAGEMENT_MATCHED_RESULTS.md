# Management-matched donor control: completed retrospective results (2026-11-24)

[Frozen protocol](JAPAN_CONTEXT_MANAGEMENT_MATCHED_PROTOCOL.md) · [successful workflow](https://github.com/zuizui0223/keiba/actions/runs/45367084420) · [stdout evidence](../evidence/japan-context-management-matched-20261124.json). Original commit `49c5f09fb582bee38fabd372787ebff709a43993`; PR82 primary reproduced. Synthetic tests, data gates and aggregate upload passed. Artifact metadata separately verified; full ZIP not independently extracted.

**Positive direction, primary strict other-parent contrast uncertain.** In 2021 main split, 716/7,276 horses (9.84%) matched; 80 sires and 154 trainers. Mean 1.254 pairs. Matched same-sire K improves M0 by 0.0047453546 MSE, sire [0.0011000820,0.0074523560], trainer [0.0016212503,0.0081310347]. K vs P gain 0.0041004328, both pointwise intervals include zero. All six matched year-seed point estimates favor same sire vs other parents, only two have both separate intervals positive. In the secondary raw-first-record matched stratum of main 2021, 209 horses: P−K +0.0142338164, sire [0.0052212611,0.0220871667], trainer [0.0045975781,0.0242242627]; all three 2021 seed sensitivities have both intervals positive in this stratum, but not all 2020 splits. This is selected, descriptive, not an interaction test or official debut. Full denominator keeps zero-support fallback; M0−K positive in all six, but P−K is uncertain. Same trainer/age/sex/year and count matching balances recorded conditions only, not farm, owner, deeper kinship or exposure decision. Complete ZIP not extracted; other support strata are not claimed.

| Seed | Year | Matched horses | M0 RMSE | K RMSE | P RMSE | P−K MSE | Sire CI | Trainer CI |
|---|---|---:|---:|---:|---:|---:|---|---|
| 20261124 | 2020 | 606 | 0.393417 | 0.382759 | 0.390266 | 0.005803037 | [0.000443917, 0.010033208] | [0.002211671, 0.009537524] |
| 20261124 | 2021 | 716 | 0.394657 | 0.388599 | 0.393840 | 0.004100433 | [-0.001798017, 0.008175473] | [-0.000721478, 0.008670469] |
| 20261125 | 2020 | 612 | 0.398243 | 0.387447 | 0.397101 | 0.007573910 | [0.002974273, 0.011324846] | [0.003211277, 0.012006480] |
| 20261125 | 2021 | 703 | 0.400952 | 0.398499 | 0.403653 | 0.004133943 | [-0.003924626, 0.010297459] | [-0.000550680, 0.008630011] |
| 20261126 | 2020 | 601 | 0.390141 | 0.381555 | 0.387201 | 0.004340445 | [-0.001831921, 0.008292227] | [-0.000123893, 0.008754231] |
| 20261126 | 2021 | 704 | 0.409089 | 0.405214 | 0.408326 | 0.002531492 | [-0.003344550, 0.006865450] | [-0.001721847, 0.006738790] |

All intervals conditional pointwise bootstrap sensitivities; distinct seeds and years share historical sources. No joint clustering, simultaneous inference, genetic causality, inherited physiological response, voluntary habitat choice, official debut, market or wagering claim. Preserve all unfavorable and support-limited findings. [Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45367084420/artifacts/14907552055) · sha256:a3a38362229306bd85cc12a5572b2a567d6ac7476dce1874abb0043416632915.
