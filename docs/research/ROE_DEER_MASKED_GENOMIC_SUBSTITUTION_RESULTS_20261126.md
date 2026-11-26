# Wild roe deer: masked genomic information substitution — observed results

26 November 2026 JST. [Frozen protocol](ROE_DEER_MASKED_GENOMIC_SUBSTITUTION_PROTOCOL_20261126.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45758728558) · [aggregate log receipt](../evidence/roe-deer-masked-genomic-substitution-20261126.json).

The fixed, recorded-genome correction improved prediction of the same held-out POH observation when zero own observations were revealed, and its incremental squared-loss value declined when three other observations were revealed. This is an independent-species and distinct-dataset analogue of the horse allocation fixed-correction decomposition, not a chronological forecast or a causal genetic replication. 228 eligible deer from 256 deer/2,288 cells, 334 labeled genomic rows. Source file hashes match PR97; archive container bytes differ. Shifted minimum eigenvalue 0.9392097188, ridge 1. No target is used in its own donor fit/history. The two fold predictions are mutually dependent through the donor sets.

| Seed | Gain 0 | Gain 1 | Gain 3 | Change 3−0 | conditional 97.5% interval gain 0 | conditional 97.5% interval change |
|---|---:|---:|---:|---:|---|---|
| 20261124 | 0.004345391 | 0.002939229 | 0.001335061 | -0.003010330 | [0.000832691, 0.008008971] | [-0.005078585, -0.001318788] |
| 20261125 | 0.005937772 | 0.003946904 | 0.001812725 | -0.004125046 | [0.001677204, 0.009658836] | [-0.005764498, -0.002577394] |
| 20261126 | 0.004448323 | 0.003106987 | 0.001389844 | -0.003058479 | [0.000413470, 0.008631557] | [-0.004817593, -0.001417369] |

Primary no-own/family RMSE: 0.271163/0.263029 (depth 0), 0.233489/0.227108 (depth 1), 0.202135/0.198805 (depth 3). Incremental gain drops 69.3% on the same 228 targets. Fixed-correction identity holds; clipped sensitivity retains positive gain and decline. All three split/mask sensitivities have the expected signs and conditional intervals. Actual genomic labeling beats 199/199 sex-blocked label shuffles for both directional contrasts in each split (descriptive plus-one tail 0.005; exchangeability not established). These are not three independent replications. The intervals condition on fitted predictions and ignore cross-fold, genetic and spatial dependence. Do not infer heritability, time decay, learning, genetic causation, or independence from shared space.

## Next distinct falsification

A second endpoint (SPEED) in the same Dryad release can test whether the record-depth pattern generalizes from habitat use to locomotion; it is not another independent population. Freeze the endpoint and masks without looking at SPEED values. For POH, test a donor-only observed road-distance covariate sensitivity with explicit semantics and check whether the correction survives. Spatially blocked or independent donor/focal inference remains a priority before population-level claims. The 2022 revision selection and actual chronology remain HOLD. Keep the horse PR96 support HOLD and all adverse evidence in the synthesis. No pooled effect or main merge here.

Receipt provenance: run head `981bbacbc54fbb00ed50c323f6347655fcf3c426`, artifact 15088569247; digest matches upload log and artifact API. Full ZIP bytes not independently extracted. Source and result JSON are preserved from the successful job log, no raw animal IDs, observations, or matrices.
