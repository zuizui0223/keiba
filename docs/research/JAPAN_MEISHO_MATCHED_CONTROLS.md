# Japanese Meisho-name pedigree concentration versus matched Wikipedia controls (2026-11-14)

**Real source-conditional analysis completed. Not JRA/NAR census, genetic heritability, or race-performance prediction.**

## Biological question and design

Are real Japanese horse articles beginning with the **メイショウ** naming prefix systematically more genealogically close, even when compared to similarly documented horse articles from the same period? A name prefix is *not* a genetic pedigree or a historically verified single-owner cohort.

Implementation: scripts/ecology_japan_meisho_matched_null.py.
Fixed reproducibility log: https://github.com/zuizui0223/keiba/actions/runs/43588576130 .
Aggregate frozen evidence: ../evidence/japan-meisho-coverage-matched-kinship-20261114.json .

The observed cohort has **38 real Meisho-name Wikipedia article identities**, exactly **703 unordered pairs**. The random comparison uses **999** sets of exactly 38 non-Meisho-name horse articles, chosen without replacement within ten pre-specified exact matching strata of:
- birth decade as parsed from article infobox;
- explicit Japan flag in infobox country;
- availability of unambiguous sire article links;
- availability of unambiguous dam article links.

Source: Japanese Wikipedia horse infoboxes, CC BY-SA. Each of 999 control sets has identical coverage/period composition. The horse pedigree matrix is computed from document-linked parents as an incomplete additive pedigree numerator A; both the observed Meisho cohort and every control set are scored on the **same source graph** and comparable pair denominators. 999 control sets are simulation draws from the *real source's observed horses*, not invented horse performance phenotypes and not new biological observations.

## Reconciled real data and matched results

GitHub runner observed **5,879** distinct article horse identities, **38 Meisho-name** entries and **5,841 other names** in this current version. **This is one article more than the earlier 5,878-article fixed baseline.**

New source SHA256: 660a18d891c026390af6361fb463875cecef9f65cd421efa1b3d47cfe0fbd8c6.
Earlier fixed baseline SHA256: e4e25ba13754d8dc60a6160126b30c97641edea043c51be1c1120509d15c1a57.
The two versions **MUST NOT be treated as identical complete source snapshots**. Meisho-name observed pairs happen to retain the previous 311 documented paths, but that does not establish countrywide source invariance.

### All documented source parents, 703 pairs per group

| Measure | Observed real Meisho group | 999 matched real control sets, mean | 5th–95th percentile over 999 draws | Fraction of control draws >= Meisho |
| --- | ---: | ---: | ---: | ---: |
| Mean pairwise partial A | **0.0132771** | 0.0113370 | 0.006236–0.018438 | 0.2462 |
| Documented A>0 pairs | **311** | 376.75 | 300–465 | 0.9079 |
| Pairs A>=0.125 | **10** | 22.77 | 6–47 | 0.8829 |
| Pairs A>=0.25 | **10** | 5.99 | 2–12 | 0.1151 |

These metrics are NOT independent: a few close relatives can increase the mean even if many weak historical paths are absent. The frequency of arbitrary matched control selections above/below the observed group is a **descriptive reference diagnostic**, not a calibrated genetic p value, significance level or inferential confidence interval.

### Father-link-only sensitivity, same real group and identical 999 controls

| Measure | Meisho | Matched mean | Fraction of draws >= Meisho |
| --- | ---: | ---: | ---: |
| Mean pairwise partial A | 0.011083 | 0.009738 | 0.2853 |
| Documented A>0 pairs | 277 | 258.09 | 0.3554 |
| Pairs A>=0.125 | 7 | 21.71 | 0.9349 |
| Pairs A>=0.25 | 7 | 5.91 | 0.3483 |

The source-conditional result is **NOT a robust indication that Meisho is a special high-kinship breeding clan after matching ancestry documentation and period**. It also does not establish that Meisho horses have the same or different actual genetic diversity or that they are unrelated, because historic interbreeding, missing maternal ancestors, sex and breeding program selection are not controlled.

## Connection to the larger real pedigree screen

The prior source version contains **5,878** Wikipedia horse articles and **17,272,503** computed partial-A pairs. Removing only the 642 documented mother links removed 2,049,634 positive pedigree paths from the original graph. That extreme missingness makes this Meisho-group matched experiment **a source-specific contrast**, not a full pedigree result. Using the new 5,879-article source does not update or overwrite those fixed prior counts.

The directly audited 11 JBIS-ID profiles in JAPAN_MEISHO_DESIGN.md are separate, provenance-specified evidence of a few real maternal sibling links, not an assumed join onto 38 Wikipedia horse title IDs. No JRA/JBIS name-fuzzy crosswalk was performed.

## Next stringent tests for biological claims

1. Get licensable JRA/NAR original starter identities and breeding registry IDs including complete maternal ancestors and true historical horse owner/trainer/breeder assignment. The external published 346,744-horse Japanese study is literature, not data available in this repository.
2. Compare a verified Meisho-owned/name cohort to non-Meisho matches with **source-complete multi-generation pedigree**, ideally A/G, and verify owner/trainer and studbook identity before estimating any population clade-like concentration.
3. Only after that freeze real pre-race own-history/relative-history features, train horse-ABM/kin terms before outcome date, and evaluate future racing timing/rank accuracy with rival and odds models separately. Nothing in the current article-only matched analysis proves inherited pacing or betting gain.

### Credits and source rights

Public article data: Japanese Wikipedia, CC BY-SA. Upstream fetcher: **Sheep Meadow Road Games / Horse Racing Manager**, https://github.com/Sheep-Meadow-Road-Games/open-horse-data and required visible credit https://store.steampowered.com/app/2740170/Horse_Racing_Manager/ .
No third-party restricted bulk JRA/NAR/JBIS runner or raw copyrighted datasets were copied into this public repository.
