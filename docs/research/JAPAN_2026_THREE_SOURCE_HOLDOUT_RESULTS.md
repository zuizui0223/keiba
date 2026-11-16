# 2026 third-source historical family prediction: previously positive effect did not reliably transfer

**Actual-source check completed, 2026-11-17 JST**. [GitHub Actions run #43897234479](https://github.com/zuizui0223/keiba/actions/runs/43897234479) **SUCCESS**, job 133404000470, code head ae152c83840a4b4a948f1ec4f8cfb135efc5edca; artifact 14240625433 (ZIP SHA256 dcf5b81df27cb75818a78f99aa98cc8e22982bd2dc722ec40c8fb5ce92fcaf05). The source and every numeric value are pinned in [aggregate evidence](../evidence/japan-2026-third-source-holdout-actual-20261117.json).

**Scientific classification**: previously unseen *family-model* outcome period (publicly available 2026 starts), different outcome-source release; retrospective out-of-period validation, not prospectively collected racing data. This **is not** official registry-verified individual identity or genetic inheritance.

## The sample was obtained without 2025/2026 rank-based identity matching

1. **Source A**, 2010–21 archive with focal/direct sire/dam IDs and original model training: SHA256 c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f.
2. **Source B**, 1990–2025/03 SQLite with a distinct ID space: SHA256 7c6717f6f081f957721396d1e0e7296b4be3eeaa2fe1a657b41a4b5358474be9. Reconstructed the prior **20,400** A↔B matches with >=2 dated, pre-2022 rank/distance anchors and unique normalized horse names.
3. **Source C**, JRA HTML-derived public root CSV in whitedogk/jra-condition-app: SHA256 ca14ff253018433e8e14bc583628f85ca909195d5e4edb42c6d1e2ade939ba6f. **137,860** valid flat turf/dirt observations, years 2023–2026. Source C has **no stable horse registry ID or sire/dam ID**; the README overstates coverage relative to the SHA-pinned file. Sources B↔C matched in a **second step using only 2023–2024** days/ranks/distances/surface and an exact unambiguous normalized name, with ≥2 independent matching days.
4. B↔C yielded **1,945** source-history-based candidate horses with two historical matching days (2,223 with at least one). These are **not official certified horse crosswalks**.
5. Source C contained **18,222** valid 2026 runner observations, with dates up to **2026-05-17 only**. Among its 2026 race results, **1,264 races / 17,864 classified runner observations** had unique horse names and full, consecutive ranked 1..N finishers. 25 races failed this source-complete test. The A↔B↔C chain yielded **232 older horses, 480 starts, 259 races across 42 distinct racing dates**; just 2.6% of the full source-C 2026 valid observation rows. Gate requiring ≥30 mapped horses, ≥100 starts and ≥30 dates passed.
6. Horse ID assignment and model coefficients were frozen without using 2025–26 finish ranks. Sources A and B may derive results from overlapping official JRA websites; they are **not independent biological samples**. The target cohort is *survivors already observed in 2021 and again in 2023–24*, excluding newly debuting racehorses or horses with broken source names.

## Results on the only new 2026 outcomes

Normalized rank \`y=(classified_finish-1)/(N_classified-1)\` is calculated within a complete, source-C race. Evaluation weights each focal horse equally, as in the earlier experiments. Training remains restricted to source A original 2018–21 targets with historical features from earlier years; last known individual and relatives' scores are **at least four calendar years old by 2026**.

| Frozen model on same 480 starts | 2026 RMSE (lower is better) | Conditional family gain |
|---|---:|---:|
| **Constant midpoint 0.5** | **0.312146279** | — |
| Original portable own-history no kin | 0.319681772 | — |
| Original portable own-history + same-parent histories | 0.320301606 | **−0.000619834** |
| Post-hoc stronger old-own-history no kin | 0.321518531 | — |
| Post-hoc stronger own-history + same-parent histories | 0.318074750 | **+0.003443780** |

**Main negative result:** the original portable family model **worsens** compared with the matched no-family baseline. With age/sex/recency enhanced own-history the family increment is positive but highly imprecise; **all fitted models lose to the fixed midpoint predictor**. Thus none of the models produced an operationally superior new-period forecast in the observed older-horse cohort.

Uncertainty (399 resamples, one-way clustering):
- Original kin gain: by horse ID **[−0.005077,+0.003033]** (232 clusters); by racing date **[−0.003878,+0.002868]** (42 clusters).
- Strong-history kin gain: by horse ID **[−0.000644,+0.007023]**; by racing date **[−0.000119,+0.007040]**. All intervals include zero. Distinct calendar days are only 42, so precision is poor.
- Relative to constant midpoint, **original +kin loses by RMSE 0.008155**; strong +kin loses by 0.005928. The source-C partial 2026 year cannot establish the full-year 2026 distribution.

## How this changes the research claim

Earlier 2022–24 (12,919 older matched horses; 255,484 starts) showed a tiny improvement +0.000322 with direct-parent other-horse history, robust to a separate strict-ranked source-B subset, a stronger old-history baseline and 19 *post-hoc* fake-family label permutations. Those sensitivity analyses all reuse the same 2022–24 period, so **they do not constitute four independent replications**.

The new year/source test **does not robustly replicate** a predictive benefit. It does not prove that family information has no value, either: only 232 older survivors from the historical sources reached 2026, and an unchanged pre-2022 history over a roughly 4+ year temporal gap is a particularly stale predictor. Results additionally differ by source C (JRA only) versus earlier mixed JRA/NAR. The failure may reflect temporal nonstationarity, aging and selective survival, source-definition differences, model aging, or true weakness of the signal. These mechanisms remain unresolved and should not be determined by post-hoc tuning to 2026 labels.

**Defensible conclusion**: historically same-parent relatives encode a small sample-conditional predictive association, but **there is no confirmed robust transfer to a new 2026 JRA outcome source**. The core idea remains a hypothesis, not a validated betting rule or demonstration of heritability.

## Highest priority after this result

1. **Stop modifying or retuning these exact 2026 results and calling the rerun an untouched holdout.** Preserve negative results, source SHA and temporal design.
2. Prospectively freeze separate *pre-race* prediction dates with **updated history through the day before each start**, including the last 1/3/10 races, current surface/distance/course, age/sex, licensed stable horse IDs and recorded sire/dam. For each historical row, calculate a true rolling cutoff and exclude focal current race outcomes. Use independent future weeks never seen during model selection.
3. Use authorized JRA-VAN RACE/RCOV **horse blood-registration numbers** in horse masters and SE records for stable IDs; use typed breeding-registration mapping for parent IDs. The existing private adapter \`scripts/ecology_jravan_blood_breeding_id_bridge.py\` does not obtain the source itself. NAR coverage requires separately verifiable access. No bulk JRA/JBIS copying or individual race rows in GitHub.
4. Only after ID crosswalk, phenotype and known-on histories are certified, evaluate pedigree A, genomic G and genetic-effect versus stable environmental/management effects in a sufficiently broad cohort. No current genetic causal effect, genome-linked race predictor, nationwide relatedness or profitable wagering result may be claimed.

Source upstream licensing is unresolved, so only anonymized totals and the run-digest are stored in public GitHub. No names, IDs, race-level labels or individual predictions were uploaded.
