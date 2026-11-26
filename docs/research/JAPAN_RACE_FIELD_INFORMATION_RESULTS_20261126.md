# Horse full-field relative ranks: race-equal gains, horse-equal boundary

26 November 2026. [Frozen protocol](JAPAN_RACE_FIELD_INFORMATION_PROTOCOL_20261126.md) · [successful source run](https://github.com/zuizui0223/keiba/actions/runs/45778138898) · [aggregate log receipt](../evidence/japan-race-field-information-20261126.json).

Source SHA and all 2,092,836 prepared starts /90,962 horses reproduced. Fixed 2016–18 JRA fit, 2019 calibration, 2020–21 test. Both linear slopes 1 and pairwise slopes 4 selected on 2019. All field-coherent predictions have per-race mean 0.5 to numerical precision. 89,473 classified starts, 6,459 races, 16,076 horses, 215 dates in pooled test. This is a retrospective classified-finisher field, not an independently recorded race-entry list.

| Model | 2020 race-equal RMSE | 2021 race-equal RMSE | pooled race-equal RMSE | pooled horse-equal RMSE |
|---|---:|---:|---:|---:|
| neutral | 0.311560682 | 0.311785477 | 0.311673187 | 0.321987729 |
| own_raw | 0.305614871 | 0.304722802 | 0.305168817 | 0.299877697 |
| kin_raw | 0.304270082 | 0.303172372 | 0.303721298 | 0.297901702 |
| own_linear | 0.297629163 | 0.297117704 | 0.297373346 | 0.303505831 |
| kin_linear | 0.295839874 | 0.295245760 | 0.295542736 | 0.300951066 |
| own_pair | 0.297455450 | 0.296968347 | 0.297211809 | 0.303366546 |
| kin_pair | 0.295687384 | 0.295093893 | 0.295390557 | 0.300832047 |

| Primary contrast | pooled race-equal MSE gain | conditional date 97.5% interval |
|---|---:|---|
| nonlinear_beyond_linear_no_kin | 0.000096047 | [0.000071644, 0.000118513] |
| kin_given_pairwise_field | 0.001079278 | [0.000925987, 0.001232273] |

Both predeclared pooled contrasts positive; both conditional intervals exclude zero, also separately in 2020 and 2021. Main no-kin linear minus raw gain 0.0046971003 (descriptive), nonlinear beyond linear 0.0000960470 (about 2% of the full own-field vs raw improvement). Kin increment remains positive beyond both coherent representations; nonlinear contribution is small. Raw prediction mean deviates from 0.5 by 0.059985 average absolute race deviation. With equal-race/equal-start-within-race weighting, centering at 0.5 before any slope cap has an exact nonnegative squared-loss gain equal to squared mean-rank error; the substantial linear effect is therefore primarily a coherence/calibration question, not evidence of pairwise physical interference. A nonlinear field projection adds dependence on opponent score distribution, but changes scale and shape jointly. **Horse-equal RMSE worsens when either raw model is projected**, and the race-equal versus horse-equal estimands must remain separate. Pairwise logistic expected ranks do not establish a joint finish-order model, race tactics or causal competition. Conditional date intervals omit repeated horse/kin/trainer and fitting dependence. Source license unresolved; no raw records redistributed. PR104 repeated-dyad increment is a separate adverse result under a different endpoint, not a formal contrast. Next: exact centering/weighting decomposition and independent linear-vs-nonlinear robustness, and dyad correspondence versus excess weighting. No main merge.

Provenance: source head 13491edd38dea9a71ffa343e39f7cbccb62fb08a; artifact 15097421029; sha256:503d3d5e2882b8605a85f1d295aa1746d56df3e2e346861af19b73849e147d01; metadata and upload-log parity, ZIP bytes not independently extracted.
