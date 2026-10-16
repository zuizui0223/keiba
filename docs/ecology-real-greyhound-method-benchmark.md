# First real-data benchmark for keiba ecology: Queensland greyhounds

**Frozen exploratory descriptive audit, 2026-10-13. NOT a Thoroughbred
horse analysis and NOT evidence supporting horse H1 or H2.**

Verified automated execution:
[GitHub Actions run #38325379268](https://github.com/zuizui0223/keiba/actions/runs/38325379268).
Software:
[scripts/ecology_greyhound_open_pilot.py](../scripts/ecology_greyhound_open_pilot.py).
The CI checks the exact Git *blob SHA-1*, downloads the fixed source revision
and publishes an **aggregated JSON artifact only**, not identifiable run rows.

## Citation and source permissions

- **Australian Racing Open Data (PandaVision), ODC-BY 1.0**,
  https://github.com/brucem1967/au-racing-open-data .
- Exact source repository commit:
  `4337848a4a3df181db3be2a75118c878270e0a58` (2026-10-12).
- Exact CSV Git blob:
  `8ef2f4c426e8f1f3e52830044d276ce57b03ba1f`.
- Source CSV path:
  `datasets/greyhound_sectionals_qld/greyhound_sectionals_qld.csv`.
- Publisher's dataset card:
  https://github.com/brucem1967/au-racing-open-data/tree/4337848a4a3df181db3be2a75118c878270e0a58/datasets/greyhound_sectionals_qld
- Upstream: Racing Queensland publicly released greyhound tracking. Their
  open-data policy says public site/web-service information is free for
  use without copyright restriction, with accuracy/availability limits,
  https://www.racingqueensland.com.au/about/reports-and-data/open-data .

This is **one third-party license at a pinned revision**. Do not silently
substitute latest data after a daily rebuild. Do not mix this result with
proprietary JRA-VAN or other restricted Japanese race data.

## Data actually inspected

| Audit metric | Verified value |
| --- | ---: |
| Reported dog–run rows | 25,679 |
| Distinct date × course × race labels | 6,021 |
| Different dog *names*, not guaranteed unique IDs | 3,603 |
| Source dates | 2025-10-01–2026-10-10 |
| Reported courses | 5 |
| First-50m times outside the exploratory range (2.4, 7.0) s | 7 |
| Empty 50m rail-offset values | 1,314 |
| Negative reported rail-offset values | 876 |
| Dog-name × course strata with >=2 inner and >=2 outer starts | 2,302 |
| Distinct dog names among those strata | 2,210 |

Negative rail offsets are flagged but **not** recoded to zero, used in
this model, or assumed to be errors. Published 50m splits ranged from
0.89 to 29.25 s, so an *exploratory after-inspection* plausibility
filter of 2.4–7.0 s was applied (strict bounds). This is not a
preregistered physiological limit.

A source key may have 1–11 rows; only 743 keys have exactly 8
published GPS rows and 10 keys have more than 8. These records do NOT
certify that the full opponent roster is recorded for every race.
Consequently, **direct competitor-composition H2 estimation is HOLD**.

Dog names are not guaranteed stable unique biological identifiers.
This may merge different animals sharing names, even though we
stratify by course. The data source itself specifically warns of this.

## Ecological analogue question

Can the *same named racing animal*, at the same venue, show different
early locomotor performance when starting in the inner (boxes 1–4)
versus outer (boxes 5–8) portion of the track?

- Outcome: **absolute GPS time to first 50 m**, seconds.
- Exposure: **assigned start box**, known before racing.
- Contrast: mean 50m split at outer boxes minus mean at inner boxes,
  separately for each dog name × venue.
- Only strata with >=2 recorded runs in each box category enter.
- Summary: arithmetic average of stratum differences, with a
  name-cluster bootstrap interval (1,000 seeded resamples) as a
  **descriptive stability diagnostic**, not valid causal uncertainty.
- Split at 80% of distinct recording dates (`2026-07-29`) for a
  chronological *descriptive* sensitivity analysis. The first
  versus last part can contain different dogs and is NOT an
  independent prospective prediction evaluation.

## Descriptive result (not causal)

| Comparison | Dog-name × venue strata | Outer minus inner mean 50m time | Descriptive dog-name-cluster 95% resampling interval |
| --- | ---: | ---: | ---: |
| All dated records | 2,302 | +0.01097 s | [+0.00823, +0.01340] s |
| Earlier 80% of dated observations | 1,250 | +0.01211 s | [+0.00819, +0.01603] s |
| Later 20% of dated observations | 814 | +0.01118 s | [+0.00706, +0.01550] s |
| q1-lakeside | 962 | +0.00765 s | [+0.00366, +0.01158] s |
| q-straight | 438 | +0.00558 s | [+0.00040, +0.01091] s |
| q2-parklands | 352 | +0.02019 s | [+0.01371, +0.02602] s |
| townsville | 378 | +0.01323 s | [+0.00779, +0.01901] s |
| rockhampton | 172 | +0.01949 s | [+0.01088, +0.02792] s |

The straight-track dataset also displays a small positive outer–inner
difference. Thus this does **not** identify greater bend distance,
cornering, drafting, or an adaptive response as the explanation.
Timing/venue/box assignment or unmeasured class and race length can
produce the same association. A ~11 ms mean difference is very small
and requires independent calibration of sensor reliability and
within-individual repeatability before a substantive effect claim.

**Do not report a hypothesis test or evolutionary discovery from a
bootstrap interval excluding zero**. The box dichotomy and split
quality cutoffs were chosen while inspecting these records, so the
estimates are explicitly exploratory.

## What this DID and DID NOT solve for horse ecology

**Solved in a separate racing species (technical feasibility):**
real repeated individual-labelled race performances; pre-start
environmental exposures; machine-readable missingness and outlier
audit; a pinned, attributed public source; a chronological
descriptive comparison; reproducibility beyond entirely synthetic tests.

**Still not solved:**
- Equine/Thoroughbred H1: this is **greyhound**, not horse data.
- Individual reaction norm variance: this simple contrast is not
  a fitted random-slope variance or age/class-controlled model.
- H2 social response: **no certified full contemporary starter roster**.
- Stable biological IDs: names may be reused.
- Causality: boxes are not shown to be randomized; race length,
  class/going, fatigue, dog age, time of day, track geometry and
  handler/trainer decisions are not jointly adjusted.
- Natural selection, indirect genetic effects, adaptive fitness or
  animal personality: not inferred.

## Next scientific gate

Use this as a transparent **methods reality check**, not as the
headline result of keiba. Target actual *horse* longitudinal data with
true stable horse IDs, complete starting fields, going, race condition
and per-run outcome/sectional data. The official Racing Queensland
[open-data program](https://www.racingqueensland.com.au/about/reports-and-data/open-data)
lists publicly available thoroughbred race data (including results and
sectionals); its precise **individual response fields** and longitudinal
stable IDs should be checked before designing an adapter.

For full equine H2, run separate completion and conditional-speed models
with horse/race clustering, independent chronological validation,
selection/missingness sensitivity and strict separation of
correlation from socially mediated causal response.
