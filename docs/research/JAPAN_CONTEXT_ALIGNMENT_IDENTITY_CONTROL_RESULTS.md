# Recorded-sire identity alignment: completed retrospective direction control

2026-11-25. **The historical same-sire correction aligns with later own-history updates more than the equal-magnitude, count-matched other-sire direction control in the primary middle band.** [Frozen protocol](JAPAN_CONTEXT_ALIGNMENT_IDENTITY_CONTROL_PROTOCOL.md) · [successful run](https://github.com/zuizui0223/keiba/actions/runs/45387457638) · [stdout receipt](../evidence/japan-context-alignment-identity-control-20261124.json). Source commit `9f55532aea63835ab2e8f0d2e82bef80c437443e`. Synthetic, source, venue, strict and PR89 parity checks passed. Artifact metadata checked, ZIP not independently extracted.

| Band | Seed | All horses | Matched nonzero horses | Sires | True cosine | Equal-magnitude swap cosine | Primary-style alignment difference | Pointwise sire interval |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 1200-1599 | 20261124 | 531 | 490 | 107 | 0.285263636 | 0.006557195 | 0.014268990 | [0.006567606, 0.021727863] |
| 1200-1599 | 20261125 | 531 | 514 | 107 | 0.283372635 | 0.005072869 | 0.014538174 | [0.005347396, 0.026118931] |
| 1200-1599 | 20261126 | 531 | 492 | 109 | 0.291046285 | 0.023773496 | 0.014074272 | [0.004712919, 0.024066771] |
| 1600-1999 | 20261124 | 599 | 565 | 109 | 0.271923228 | 0.065916342 | 0.012457150 | [0.004122848, 0.023532985] |
| 1600-1999 | 20261125 | 599 | 559 | 113 | 0.236664465 | -0.069898647 | 0.017765598 | [0.007019623, 0.030721013] |
| 1600-1999 | 20261126 | 599 | 565 | 110 | 0.241354438 | -0.057557020 | 0.017196010 | [0.006941159, 0.030744215] |
| 2000-2399 | 20261124 | 267 | 239 | 54 | 0.097342156 | -0.029450191 | 0.002520668 | [-0.002687715, 0.009621337] |
| 2000-2399 | 20261125 | 267 | 233 | 56 | 0.190203088 | -0.151544266 | 0.007336559 | [0.000285677, 0.017541503] |
| 2000-2399 | 20261126 | 267 | 246 | 55 | 0.151627437 | -0.096985643 | 0.005388989 | [0.000168567, 0.013733727] |

Primary 1600–1999m, seed 20261124: 565 of 599 horses, 109 sires; 221 signs differ. True and magnitude-preserving swap correction RMS both 0.174856989; cosine 0.271923228 vs 0.065916342. True own-update term −0.016443083 vs swap −0.003985933; difference +0.012457150 [0.004122848,0.023532985]. Raw count-matched other-sire contrast +0.014359667 [0.005826308,0.024144190]. All nine equal-magnitude contrasts positive, 8/9 pointwise intervals positive; raw 7/9. Three shorter and three middle-band intervals positive; long-band main interval crosses zero. No formal comparison of band effects or independence of these sensitivities.

## Do not mistake identity alignment for useful predictive gain

| Band | Seed | 2022 true gain | 2024 true gain | 2024 true vs magnitude-matched swap | 2024 true-gain pointwise interval |
|---|---|---:|---:|---:|---|
| 1200-1599 | 20261124 | 0.010022166 | -0.009839685 | 0.006250195 | [-0.017427549, -0.002508929] |
| 1200-1599 | 20261125 | 0.010184666 | -0.011656369 | 0.005667606 | [-0.019411004, -0.004142670] |
| 1200-1599 | 20261126 | 0.008231242 | -0.009757695 | 0.017786939 | [-0.017919033, -0.002359362] |
| 1600-1999 | 20261124 | 0.011018244 | -0.015500799 | 0.016201898 | [-0.023207402, -0.006573491] |
| 1600-1999 | 20261125 | 0.006618423 | -0.014798119 | 0.020431000 | [-0.024284654, -0.005727563] |
| 1600-1999 | 20261126 | 0.008233690 | -0.016759175 | 0.020525170 | [-0.025719789, -0.007200327] |
| 2000-2399 | 20261124 | -0.001079060 | -0.004836858 | 0.002900035 | [-0.008324835, -0.000558373] |
| 2000-2399 | 20261125 | 0.002747347 | -0.003691403 | 0.009716926 | [-0.007468099, 0.000622430] |
| 2000-2399 | 20261126 | 0.001834252 | -0.002430073 | 0.005831356 | [-0.006935325, 0.001895281] |

All nine 2024 true full correction gains negative, 7/9 pointwise intervals negative. Main 2024 true gain −0.015500799 [−0.023207402,−0.006573491], equal-magnitude swap gain −0.031702696: beating an adverse comparator does not imply improvement beyond own history. No 2022 matched-subset true-gain interval wholly positive. This is a deliberately selected common cohort, not the PR81 or PR86 entire target cohort. Primary alignment uses prior B updates only, not the evaluated 2024 surface fraction; inclusion still conditions on 2024 observations.

Interpretation: recorded-sire correspondence contributes to the alignment of the two predictive inputs. This supports information-overlap as a predictive mechanism under the specified control. A different recorded sire need not be genomically unrelated, and shared management or earlier observational selection remain. Equal-magnitude swap uses the true correction magnitude; it is a diagnostic not a deployable alternative predictor. Reused archives, dependent seeds/bands, conditional pointwise sire intervals, no simultaneous inference or prospective validation. No animal learning, genetic adaptation, heritability, fitness, choice or betting claim. Anonymous aggregates only.

[Aggregate artifact](https://github.com/zuizui0223/keiba/actions/runs/45387457638/artifacts/14915909441) · sha256:bb9def96f12dc370ff5ada3c883a3fd5dddbee9d9856eae61b70d4f1d963484b.
